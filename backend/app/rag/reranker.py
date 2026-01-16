"""
Cross-Encoder Reranker for RAG Retrieval.

Uses a cross-encoder model to rerank retrieved chunks based on
semantic relevance to the query. Cross-encoders process query-document
pairs together, providing more accurate relevance scores than bi-encoders.

MODELS (in order of preference):
- Primary: cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, multilingual)
- Arabic: amberoad/bert-multilingual-passage-reranking-msmarco
- Fallback: Simple keyword overlap scoring

OPTIMIZATIONS:
- GPU acceleration with automatic device selection
- Batch processing for throughput
- Model warmup for consistent latency
- Configurable model selection
- Prometheus metrics integration

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
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)


class RerankerModel(str, Enum):
    """Available reranker models."""
    MS_MARCO_MINILM = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MS_MARCO_DISTILBERT = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
    MULTILINGUAL_MSMARCO = "amberoad/bert-multilingual-passage-reranking-msmarco"
    ARABIC_BERT = "aubmindlab/bert-base-arabertv02"  # For Arabic-specific fine-tuning


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
_cross_encoder = None
_model_load_attempted = False
_reranker_stats = RerankerStats()
_model_lock = threading.Lock()


# Configuration with environment variable overrides
RERANKER_CONFIG = {
    "enabled": os.getenv("RERANKER_ENABLED", "true").lower() == "true",
    "use_cross_encoder": os.getenv("RERANKER_USE_CROSS_ENCODER", "true").lower() == "true",
    "model": os.getenv("RERANKER_MODEL", RerankerModel.MS_MARCO_MINILM.value),
    "max_input_length": int(os.getenv("RERANKER_MAX_INPUT_LENGTH", "512")),
    "batch_size": int(os.getenv("RERANKER_BATCH_SIZE", "32")),
    "warmup_on_load": os.getenv("RERANKER_WARMUP", "true").lower() == "true",
    "use_fp16": os.getenv("RERANKER_USE_FP16", "true").lower() == "true",  # Half precision for GPU
    "fallback_weight": float(os.getenv("RERANKER_FALLBACK_WEIGHT", "0.3")),  # Weight for keyword overlap
}


def get_reranker_stats() -> RerankerStats:
    """Get reranker statistics singleton."""
    return _reranker_stats


def _detect_device() -> str:
    """Detect best available device (CUDA > MPS > CPU)."""
    try:
        import torch
        if torch.cuda.is_available():
            # Check CUDA memory
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"CUDA available with {gpu_mem:.1f}GB memory")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Apple MPS available")
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _warmup_model(cross_encoder, device: str) -> bool:
    """
    Warmup model with sample queries for consistent latency.

    First inference is typically slower due to JIT compilation,
    memory allocation, etc. Warmup ensures consistent performance.
    """
    try:
        warmup_pairs = [
            ["What is patience in Islam?", "Patience (sabr) is a virtue in Islam..."],
            ["Tell me about Moses", "Prophet Musa (Moses) was sent to Pharaoh..."],
            ["ما معنى الصبر", "الصبر من أعظم الفضائل في الإسلام..."],
        ]

        logger.info(f"Warming up cross-encoder on {device}...")
        start = time.perf_counter()

        # Run warmup inference
        _ = cross_encoder.predict(warmup_pairs)

        warmup_time = (time.perf_counter() - start) * 1000
        logger.info(f"Cross-encoder warmup complete in {warmup_time:.1f}ms")

        return True
    except Exception as e:
        logger.warning(f"Warmup failed: {e}")
        return False


def get_cross_encoder(force_reload: bool = False):
    """
    Lazy-load the cross-encoder model with GPU optimization.

    Features:
    - Automatic device selection (CUDA > MPS > CPU)
    - Half-precision (FP16) for GPU inference
    - Model warmup for consistent latency
    - Thread-safe loading
    """
    global _cross_encoder, _model_load_attempted, _reranker_stats

    with _model_lock:
        if _model_load_attempted and not force_reload:
            return _cross_encoder

        _model_load_attempted = True

        try:
            import torch
            from sentence_transformers import CrossEncoder

            # Detect best device
            device = _detect_device()
            _reranker_stats.gpu_available = device in ("cuda", "mps")

            model_name = RERANKER_CONFIG["model"]
            logger.info(f"Loading cross-encoder model: {model_name} on {device}")

            # Load model
            _cross_encoder = CrossEncoder(model_name, device=device)

            # Enable half-precision on GPU for faster inference
            if device == "cuda" and RERANKER_CONFIG["use_fp16"]:
                try:
                    _cross_encoder.model.half()
                    logger.info("Enabled FP16 (half-precision) for GPU inference")
                except Exception as e:
                    logger.warning(f"Could not enable FP16: {e}")

            _reranker_stats.model_loaded = True
            _reranker_stats.model_name = model_name

            # Warmup if configured
            if RERANKER_CONFIG["warmup_on_load"]:
                _reranker_stats.warmup_complete = _warmup_model(_cross_encoder, device)

            logger.info(f"Cross-encoder model loaded successfully on {device}")
            return _cross_encoder

        except ImportError as e:
            logger.warning(f"sentence-transformers not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            return None


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

    # Try cross-encoder if enabled
    if use_cross_encoder and RERANKER_CONFIG["use_cross_encoder"]:
        cross_encoder = get_cross_encoder()

        if cross_encoder is not None:
            try:
                result = _rerank_with_cross_encoder(query, chunks, top_k, cross_encoder)
                latency_ms = (time.perf_counter() - start_time) * 1000
                result[1].latency_ms = latency_ms

                # Record metrics
                _reranker_stats.record_request(latency_ms, "cross_encoder", len(chunks))
                _record_prometheus_metrics(latency_ms, "cross_encoder", len(chunks))

                return result
            except Exception as e:
                logger.warning(f"Cross-encoder reranking failed, using fallback: {e}")

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
    cross_encoder,
) -> Tuple[List, RerankResult]:
    """
    Rerank using cross-encoder model with batch processing.

    Creates query-document pairs and computes relevance scores.
    Uses batched inference for better GPU utilization.
    """
    import torch

    max_input_length = RERANKER_CONFIG["max_input_length"]
    batch_size = RERANKER_CONFIG["batch_size"]

    # Prepare query-document pairs
    pairs = []
    valid_indices = []

    for i, chunk in enumerate(chunks):
        # Use the most relevant content field
        text = chunk.content or chunk.content_en or chunk.content_ar or ""
        if text:
            # Truncate to max input length
            pairs.append([query, text[:max_input_length]])
            valid_indices.append(i)

    if not pairs:
        return chunks[:top_k], RerankResult(
            reranked=False,
            method="cross_encoder",
            scores=[0.0] * len(chunks[:top_k]),
            model_used=RERANKER_CONFIG["model"]
        )

    # Batch inference for better GPU utilization
    all_scores = []
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]

        with torch.no_grad():
            batch_scores = cross_encoder.predict(batch, show_progress_bar=False)

        if hasattr(batch_scores, 'tolist'):
            batch_scores = batch_scores.tolist()

        all_scores.extend(batch_scores)

    # Map scores back to chunks
    chunk_scores = [0.0] * len(chunks)
    for idx, score in zip(valid_indices, all_scores):
        chunk_scores[idx] = float(score)

    # Pair chunks with scores and sort
    scored_chunks = list(zip(chunks, chunk_scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    # Extract reranked chunks and scores
    reranked_chunks = [chunk for chunk, _ in scored_chunks[:top_k]]
    raw_scores = [score for _, score in scored_chunks[:top_k]]

    # Normalize scores to 0-1 range using sigmoid
    # Cross-encoder outputs raw logits that can be negative
    import math
    def sigmoid(x):
        """Convert logit to probability 0-1."""
        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0

    reranked_scores = [sigmoid(score) for score in raw_scores]

    # Update relevance scores in chunks with normalized scores
    for i, chunk in enumerate(reranked_chunks):
        chunk.relevance_score = float(reranked_scores[i])

    device = _detect_device()
    logger.info(f"Cross-encoder reranked {len(chunks)} chunks on {device}, top raw score: {raw_scores[0]:.3f}, normalized: {reranked_scores[0]:.3f}")

    return reranked_chunks, RerankResult(
        reranked=True,
        method="cross_encoder",
        scores=reranked_scores,
        model_used=RERANKER_CONFIG["model"],
        device=device
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
    Check if reranker is available and what method will be used.

    Returns dict with:
    - available: bool
    - method: str ("cross_encoder", "keyword_overlap")
    - model: str (model name if cross-encoder)
    - device: str ("cuda", "mps", or "cpu")
    - stats: dict (performance statistics)
    """
    cross_encoder = get_cross_encoder()
    stats = _reranker_stats.to_dict()

    if cross_encoder is not None:
        device = _detect_device()
        return {
            "available": True,
            "method": "cross_encoder",
            "model": RERANKER_CONFIG["model"],
            "device": device,
            "config": {
                "max_input_length": RERANKER_CONFIG["max_input_length"],
                "batch_size": RERANKER_CONFIG["batch_size"],
                "use_fp16": RERANKER_CONFIG["use_fp16"],
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


def preload_model():
    """
    Preload model at application startup.

    Call this during app initialization to avoid cold-start latency
    on the first reranking request.
    """
    logger.info("Preloading cross-encoder model...")
    encoder = get_cross_encoder()
    if encoder:
        logger.info("Cross-encoder model preloaded successfully")
    else:
        logger.warning("Cross-encoder model not available, will use fallback")
