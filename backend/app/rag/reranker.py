"""
Reranker for RAG retrieval (Hugging Face hosted cross-encoder).

A cross-encoder scores each (query, passage) pair jointly, which is more
accurate than bi-encoder similarity alone. The model runs on Hugging Face
Inference Providers (``HF_RERANKER_MODEL``, default ``BAAI/bge-reranker-v2-m3``
— multilingual, handles Arabic and English); nothing is loaded locally and no
GPU is needed.

If the HF call fails (no token, quota, outage) the deterministic hybrid
keyword-overlap + BM25 scorer below is used instead.

FLOW:
1. Bi-encoder (embedding model) retrieves candidate chunks
2. Cross-encoder reranks candidates by computing relevance scores
3. Top-k highest scoring chunks are returned

Arabic: معيد ترتيب النتائج باستخدام الترميز المتقاطع
"""
import logging
import time
import os
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import re
import threading

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Result of reranking operation."""
    reranked: bool
    method: str  # "cross_encoder", "keyword_overlap", "none"
    scores: List[float]
    latency_ms: float = 0.0
    model_used: Optional[str] = None
    device: str = "cpu"


@dataclass
class RerankerStats:
    """Statistics for reranker performance monitoring."""
    total_requests: int = 0
    cross_encoder_requests: int = 0
    fallback_requests: int = 0
    total_chunks_processed: int = 0
    avg_latency_ms: float = 0.0
    gpu_available: bool = False
    model_loaded: bool = False
    model_name: Optional[str] = None
    warmup_complete: bool = False
    _latencies: List[float] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_request(self, latency_ms: float, method: str, chunk_count: int):
        """Thread-safe request recording."""
        with self._lock:
            self.total_requests += 1
            self.total_chunks_processed += chunk_count
            self._latencies.append(latency_ms)

            # Keep only last 1000 latencies for rolling average
            if len(self._latencies) > 1000:
                self._latencies = self._latencies[-1000:]

            self.avg_latency_ms = sum(self._latencies) / len(self._latencies)

            if method == "cross_encoder":
                self.cross_encoder_requests += 1
            else:
                self.fallback_requests += 1

    def to_dict(self) -> Dict[str, Any]:
        """Export stats as dictionary."""
        return {
            "total_requests": self.total_requests,
            "cross_encoder_requests": self.cross_encoder_requests,
            "fallback_requests": self.fallback_requests,
            "total_chunks_processed": self.total_chunks_processed,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "gpu_available": self.gpu_available,
            "model_loaded": self.model_loaded,
            "model_name": self.model_name,
            "warmup_complete": self.warmup_complete,
        }


# Global state
_reranker_stats = RerankerStats()


def _reranker_model() -> str:
    from app.core.config import settings
    return os.getenv("RERANKER_MODEL") or settings.hf_reranker_model


# Configuration with environment variable overrides
RERANKER_CONFIG = {
    "enabled": os.getenv("RERANKER_ENABLED", "true").lower() == "true",
    "use_cross_encoder": os.getenv("RERANKER_USE_CROSS_ENCODER", "true").lower() == "true",
    "max_input_length": int(os.getenv("RERANKER_MAX_INPUT_LENGTH", "512")),
    "batch_size": int(os.getenv("RERANKER_BATCH_SIZE", "32")),
    "fallback_weight": float(os.getenv("RERANKER_FALLBACK_WEIGHT", "0.3")),  # Weight for keyword overlap
}


def get_reranker_stats() -> RerankerStats:
    """Get reranker statistics singleton."""
    return _reranker_stats


def _hf_rerank_scores(query: str, passages: List[str]) -> List[float]:
    """
    Score (query, passage) pairs with the hosted cross-encoder.

    Returns one relevance probability (0–1) per passage, in input order.
    Raises HFInferenceError on any upstream failure.
    """
    from app.ai.hf_client import HFErrorKind, HFInferenceError, classify_exception

    model = _reranker_model()
    scores: List[float] = []
    size = RERANKER_CONFIG["batch_size"]
    for start in range(0, len(passages), size):
        batch = passages[start:start + size]
        payload = [{"text": query, "text_pair": p} for p in batch]
        try:
            out = _post_pairs(model, payload)
        except Exception as exc:  # noqa: BLE001
            raise classify_exception(exc, "rerank") from None
        batch_scores = _parse_rerank_output(out, len(batch))
        if batch_scores is None:
            raise HFInferenceError(HFErrorKind.MALFORMED, "rerank")
        scores.extend(batch_scores)
    return scores


HF_INFERENCE_BASE = "https://router.huggingface.co/hf-inference/models"


def _post_pairs(model: str, payload: list):
    """
    POST (text, text_pair) inputs to the hf-inference text-classification
    endpoint. huggingface_hub's typed client has no pair-input helper, so
    this one request is made with httpx directly.
    """
    import httpx
    from app.ai.hf_client import require_hf_token
    from app.core.config import settings

    response = httpx.post(
        f"{HF_INFERENCE_BASE}/{model}",
        headers={"Authorization": f"Bearer {require_hf_token('rerank')}"},
        json={"inputs": payload},
        timeout=settings.hf_timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def _parse_rerank_output(out, expected: int) -> Optional[List[float]]:
    """
    Accept the shapes hf-inference returns for pair classification:
    ``[[{"label","score"}, ...]]`` (one list per pair or one wrapping list),
    or ``[{"label","score"}, ...]``.
    """
    if isinstance(out, (bytes, str)):
        import json
        out = json.loads(out)
    if isinstance(out, list) and len(out) == 1 and isinstance(out[0], list) and expected != 1:
        out = out[0]
    if not isinstance(out, list) or len(out) != expected:
        return None
    scores = []
    for item in out:
        if isinstance(item, list):
            item = item[0] if item else None
        if not isinstance(item, dict) or "score" not in item:
            return None
        scores.append(float(item["score"]))
    return scores


def compute_keyword_overlap_score(query: str, text: str) -> float:
    """
    Fallback scoring using keyword overlap with Arabic support.

    Returns a score between 0 and 1 based on how many query
    terms appear in the text.
    """
    if not query or not text:
        return 0.0

    # Normalize and tokenize
    query_lower = query.lower()
    text_lower = text.lower()

    # Extract words (handles both Arabic and English)
    query_words = set(re.findall(r'[\w\u0600-\u06FF]+', query_lower))
    text_words = set(re.findall(r'[\w\u0600-\u06FF]+', text_lower))

    if not query_words:
        return 0.0

    # Calculate overlap
    overlap = len(query_words & text_words)
    score = overlap / len(query_words)

    # Boost for exact phrase matches
    if query_lower in text_lower:
        score = min(1.0, score + 0.3)

    # Boost for Arabic root matches (simplified)
    arabic_query_words = [w for w in query_words if re.match(r'[\u0600-\u06FF]', w)]
    if arabic_query_words:
        # Check for partial Arabic word matches (root-like matching)
        for qw in arabic_query_words:
            if len(qw) >= 3:
                root = qw[:3]  # Simplified 3-letter root
                for tw in text_words:
                    if root in tw:
                        score = min(1.0, score + 0.1)
                        break

    return score


def compute_bm25_score(query: str, text: str, k1: float = 1.5, b: float = 0.75) -> float:
    """
    BM25-style scoring for better keyword matching.

    More sophisticated than simple overlap, considers term frequency
    and document length.
    """
    if not query or not text:
        return 0.0

    query_words = re.findall(r'[\w\u0600-\u06FF]+', query.lower())
    text_words = re.findall(r'[\w\u0600-\u06FF]+', text.lower())

    if not query_words or not text_words:
        return 0.0

    # Calculate term frequencies
    text_tf = {}
    for word in text_words:
        text_tf[word] = text_tf.get(word, 0) + 1

    avg_doc_len = 200  # Approximate average document length
    doc_len = len(text_words)

    score = 0.0
    for term in set(query_words):
        if term in text_tf:
            tf = text_tf[term]
            # BM25 term score
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
            score += numerator / denominator

    # Normalize to 0-1 range
    max_score = len(set(query_words)) * (k1 + 1)
    return min(1.0, score / max_score) if max_score > 0 else 0.0


def rerank_chunks(
    query: str,
    chunks: List,  # List[RetrievedChunk]
    top_k: int = 8,
    use_cross_encoder: bool = True,
) -> Tuple[List, RerankResult]:
    """
    Rerank retrieved chunks using cross-encoder or fallback.

    Args:
        query: The user's search query
        chunks: List of RetrievedChunk objects from initial retrieval
        top_k: Number of top results to return
        use_cross_encoder: Whether to try using cross-encoder (fallback if fails)

    Returns:
        Tuple of (reranked_chunks, RerankResult metadata)
    """
    start_time = time.perf_counter()

    if not chunks:
        return [], RerankResult(reranked=False, method="none", scores=[])

    # Try the hosted cross-encoder if enabled and HF is configured
    from app.ai.hf_client import hf_configured

    if use_cross_encoder and RERANKER_CONFIG["use_cross_encoder"] and hf_configured():
        try:
            result = _rerank_with_cross_encoder(query, chunks, top_k)
            latency_ms = (time.perf_counter() - start_time) * 1000
            result[1].latency_ms = latency_ms

            # Record metrics
            _reranker_stats.record_request(latency_ms, "cross_encoder", len(chunks))
            _record_prometheus_metrics(latency_ms, "cross_encoder", len(chunks))

            return result
        except Exception as e:
            logger.warning(f"HF reranking failed, using fallback: {e}")

    # Fallback to hybrid keyword/BM25 scoring
    result = _rerank_with_hybrid_fallback(query, chunks, top_k)
    latency_ms = (time.perf_counter() - start_time) * 1000
    result[1].latency_ms = latency_ms

    # Record metrics
    _reranker_stats.record_request(latency_ms, "keyword_overlap", len(chunks))
    _record_prometheus_metrics(latency_ms, "keyword_overlap", len(chunks))

    return result


def _record_prometheus_metrics(latency_ms: float, method: str, chunk_count: int):
    """Record metrics to Prometheus if available."""
    try:
        from app.services.metrics import get_metrics
        metrics = get_metrics()
        metrics.record_rerank(method=method, latency=latency_ms / 1000)
    except Exception:
        pass  # Metrics not available


def _rerank_with_cross_encoder(
    query: str,
    chunks: List,
    top_k: int,
) -> Tuple[List, RerankResult]:
    """Rerank with the HF-hosted cross-encoder (scores are probabilities 0–1)."""
    max_input_length = RERANKER_CONFIG["max_input_length"]

    passages, valid_indices = [], []
    for i, chunk in enumerate(chunks):
        text = chunk.content or chunk.content_en or chunk.content_ar or ""
        if text:
            passages.append(text[:max_input_length])
            valid_indices.append(i)

    model = _reranker_model()
    if not passages:
        return chunks[:top_k], RerankResult(
            reranked=False, method="cross_encoder",
            scores=[0.0] * len(chunks[:top_k]), model_used=model,
        )

    scores = _hf_rerank_scores(query, passages)

    chunk_scores = [0.0] * len(chunks)
    for idx, score in zip(valid_indices, scores):
        chunk_scores[idx] = float(score)

    scored_chunks = sorted(zip(chunks, chunk_scores), key=lambda x: x[1], reverse=True)
    reranked_chunks = [chunk for chunk, _ in scored_chunks[:top_k]]
    reranked_scores = [score for _, score in scored_chunks[:top_k]]

    for chunk, score in zip(reranked_chunks, reranked_scores):
        chunk.relevance_score = float(score)

    logger.info(
        "HF reranker scored %d chunks, top score %.3f", len(chunks),
        reranked_scores[0] if reranked_scores else 0.0,
    )
    return reranked_chunks, RerankResult(
        reranked=True,
        method="cross_encoder",
        scores=reranked_scores,
        model_used=model,
        device="huggingface",
    )


def _rerank_with_hybrid_fallback(
    query: str,
    chunks: List,
    top_k: int,
) -> Tuple[List, RerankResult]:
    """
    Fallback reranking using hybrid keyword overlap + BM25 scoring.
    """
    fallback_weight = RERANKER_CONFIG["fallback_weight"]
    scored_chunks = []

    for chunk in chunks:
        text = chunk.content or chunk.content_en or chunk.content_ar or ""

        # Compute multiple scores
        keyword_score = compute_keyword_overlap_score(query, text)
        bm25_score = compute_bm25_score(query, text)

        # Combine scores: original relevance + keyword + BM25
        combined_score = (
            (1 - fallback_weight) * chunk.relevance_score +
            fallback_weight * 0.5 * keyword_score +
            fallback_weight * 0.5 * bm25_score
        )
        scored_chunks.append((chunk, combined_score))

    # Sort by combined score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    # Extract results
    reranked_chunks = [chunk for chunk, _ in scored_chunks[:top_k]]
    reranked_scores = [score for _, score in scored_chunks[:top_k]]

    # Update relevance scores
    for i, chunk in enumerate(reranked_chunks):
        chunk.relevance_score = float(reranked_scores[i])

    logger.info(f"Hybrid fallback reranked {len(chunks)} chunks")

    return reranked_chunks, RerankResult(
        reranked=True,
        method="keyword_overlap",
        scores=reranked_scores,
        device="cpu"
    )


# Legacy alias for backward compatibility
_rerank_with_keyword_overlap = _rerank_with_hybrid_fallback


def is_reranker_available() -> dict:
    """
    Report which reranking method will be used. Makes no network call.
    """
    from app.ai.hf_client import hf_configured

    stats = _reranker_stats.to_dict()
    if RERANKER_CONFIG["use_cross_encoder"] and hf_configured():
        return {
            "available": True,
            "method": "cross_encoder",
            "model": _reranker_model(),
            "device": "huggingface",
            "config": {
                "max_input_length": RERANKER_CONFIG["max_input_length"],
                "batch_size": RERANKER_CONFIG["batch_size"],
            },
            "stats": stats,
        }

    return {
        "available": True,
        "method": "keyword_overlap",
        "model": None,
        "device": "cpu",
        "stats": stats,
    }
