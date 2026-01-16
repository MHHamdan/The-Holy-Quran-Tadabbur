"""
Semantic Embeddings Service for Quranic Verses.

Provides contextual embeddings using transformer models for:
1. Deep semantic similarity beyond word overlap
2. Contextual understanding of verse meanings
3. Cross-lingual semantic matching

Arabic: خدمة التضمينات الدلالية للآيات القرآنية
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Embedding model configuration
EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "fallback_model": "sentence-transformers/all-MiniLM-L6-v2",
    "max_sequence_length": 512,
    "embedding_dimension": 384,
    "batch_size": 32,
}

# Semantic similarity thresholds
SIMILARITY_THRESHOLDS = {
    "very_high": 0.85,
    "high": 0.70,
    "moderate": 0.50,
    "low": 0.30,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SemanticMatch:
    """A semantic similarity match."""
    verse_id: int
    sura_no: int
    aya_no: int
    reference: str
    text: str
    similarity_score: float
    confidence: str  # "very_high", "high", "moderate", "low"
    semantic_themes: List[str]


@dataclass
class EmbeddingResult:
    """Result of embedding computation."""
    text: str
    embedding: np.ndarray
    model_used: str
    processing_time_ms: float


# =============================================================================
# SEMANTIC EMBEDDING SERVICE
# =============================================================================

class SemanticEmbeddingService:
    """
    Service for computing and comparing semantic embeddings of Quranic verses.

    Uses transformer models to capture contextual meaning beyond word overlap.
    Falls back to TF-IDF weighted embeddings if transformer models unavailable.
    """

    def __init__(self):
        self._model = None
        self._model_name = None
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize the embedding model.

        Returns True if a transformer model is loaded, False if using fallback.
        """
        if self._initialized:
            return self._model is not None

        try:
            # Try to load sentence-transformers
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(EMBEDDING_CONFIG["model_name"])
                self._model_name = EMBEDDING_CONFIG["model_name"]
                logger.info(f"Loaded primary embedding model: {self._model_name}")
            except Exception as e:
                logger.warning(f"Failed to load primary model: {e}")
                try:
                    self._model = SentenceTransformer(EMBEDDING_CONFIG["fallback_model"])
                    self._model_name = EMBEDDING_CONFIG["fallback_model"]
                    logger.info(f"Loaded fallback model: {self._model_name}")
                except Exception as e2:
                    logger.error(f"Failed to load fallback model: {e2}")
                    self._model = None

        except ImportError:
            logger.warning("sentence-transformers not installed, using TF-IDF fallback")
            self._model = None

        self._initialized = True
        return self._model is not None

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    async def compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for a text.

        Uses transformer model if available, otherwise TF-IDF fallback.
        """
        cache_key = self._get_cache_key(text)

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        if not self._initialized:
            await self.initialize()

        if self._model is not None:
            # Use transformer model
            embedding = self._model.encode(text, convert_to_numpy=True)
        else:
            # Use TF-IDF fallback
            embedding = self._compute_tfidf_embedding(text)

        self._embedding_cache[cache_key] = embedding
        return embedding

    async def compute_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Compute embeddings for multiple texts efficiently."""
        if not self._initialized:
            await self.initialize()

        # Check cache first
        results = []
        texts_to_compute = []
        indices_to_compute = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                results.append((i, self._embedding_cache[cache_key]))
            else:
                texts_to_compute.append(text)
                indices_to_compute.append(i)

        # Compute new embeddings
        if texts_to_compute:
            if self._model is not None:
                new_embeddings = self._model.encode(
                    texts_to_compute,
                    convert_to_numpy=True,
                    batch_size=EMBEDDING_CONFIG["batch_size"],
                    show_progress_bar=False,
                )
            else:
                new_embeddings = [
                    self._compute_tfidf_embedding(t)
                    for t in texts_to_compute
                ]

            # Cache and add to results
            for idx, (orig_idx, text) in enumerate(zip(indices_to_compute, texts_to_compute)):
                embedding = new_embeddings[idx] if isinstance(new_embeddings, list) else new_embeddings[idx]
                cache_key = self._get_cache_key(text)
                self._embedding_cache[cache_key] = embedding
                results.append((orig_idx, embedding))

        # Sort by original index and return embeddings
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    def _compute_tfidf_embedding(self, text: str) -> np.ndarray:
        """
        Compute TF-IDF based embedding as fallback.

        Uses a fixed vocabulary of important Quranic terms.
        """
        from app.services.quran_search import normalize_arabic, extract_words
        from app.services.advanced_similarity import CONTEXTUAL_SIGNIFICANCE

        words = extract_words(text)

        # Create embedding from significant words
        embedding = np.zeros(EMBEDDING_CONFIG["embedding_dimension"])

        if not words:
            return embedding

        # Use word positions and significance to create embedding
        for i, word in enumerate(words):
            normalized = normalize_arabic(word)
            significance = CONTEXTUAL_SIGNIFICANCE.get(normalized, 1.0)

            # Hash word to position in embedding
            word_hash = int(hashlib.md5(normalized.encode('utf-8')).hexdigest(), 16)
            positions = [
                word_hash % EMBEDDING_CONFIG["embedding_dimension"],
                (word_hash * 7) % EMBEDDING_CONFIG["embedding_dimension"],
                (word_hash * 13) % EMBEDDING_CONFIG["embedding_dimension"],
            ]

            for pos in positions:
                embedding[pos] += significance * (1.0 / (i + 1))  # Position decay

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    async def compute_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """Compute semantic similarity between two texts."""
        emb1 = await self.compute_embedding(text1)
        emb2 = await self.compute_embedding(text2)

        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    async def find_similar_by_embedding(
        self,
        query_text: str,
        candidate_texts: List[Tuple[int, str]],  # (verse_id, text)
        top_k: int = 20,
        min_similarity: float = 0.3,
    ) -> List[Tuple[int, float]]:
        """
        Find most similar texts to query using embeddings.

        Args:
            query_text: The source text
            candidate_texts: List of (verse_id, text) tuples
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold

        Returns:
            List of (verse_id, similarity_score) tuples
        """
        query_embedding = await self.compute_embedding(query_text)

        # Compute embeddings for candidates
        candidate_embeddings = await self.compute_embeddings_batch(
            [text for _, text in candidate_texts]
        )

        # Compute similarities
        similarities = []
        for (verse_id, _), emb in zip(candidate_texts, candidate_embeddings):
            sim = float(np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            ))
            if sim >= min_similarity:
                similarities.append((verse_id, sim))

        # Sort and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_confidence_level(self, similarity: float) -> str:
        """Get confidence level string from similarity score."""
        if similarity >= SIMILARITY_THRESHOLDS["very_high"]:
            return "very_high"
        elif similarity >= SIMILARITY_THRESHOLDS["high"]:
            return "high"
        elif similarity >= SIMILARITY_THRESHOLDS["moderate"]:
            return "moderate"
        else:
            return "low"

    async def analyze_semantic_themes(
        self,
        text: str,
        theme_embeddings: Optional[Dict[str, np.ndarray]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Analyze which themes are semantically present in text.

        Returns list of (theme_id, relevance_score) tuples.
        """
        from app.services.advanced_similarity import EXTENDED_THEME_KEYWORDS

        text_embedding = await self.compute_embedding(text)

        # Compute theme embeddings if not provided
        if theme_embeddings is None:
            theme_embeddings = {}
            for theme_id, keywords in EXTENDED_THEME_KEYWORDS.items():
                theme_text = " ".join(keywords)
                theme_embeddings[theme_id] = await self.compute_embedding(theme_text)

        # Compute similarity with each theme
        theme_scores = []
        for theme_id, theme_emb in theme_embeddings.items():
            sim = float(np.dot(text_embedding, theme_emb) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(theme_emb)
            ))
            if sim > 0.2:  # Minimum threshold
                theme_scores.append((theme_id, sim))

        theme_scores.sort(key=lambda x: x[1], reverse=True)
        return theme_scores[:5]  # Top 5 themes

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_name": self._model_name or "tfidf_fallback",
            "initialized": self._initialized,
            "using_transformer": self._model is not None,
            "cache_size": len(self._embedding_cache),
            "embedding_dimension": EMBEDDING_CONFIG["embedding_dimension"],
        }

    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()


# =============================================================================
# CONTEXTUAL SIMILARITY ENHANCER
# =============================================================================

class ContextualSimilarityEnhancer:
    """
    Enhances similarity scores using contextual understanding.

    Combines multiple signals:
    1. Semantic embeddings
    2. Thematic alignment
    3. Structural patterns
    4. Cross-reference awareness
    """

    def __init__(self, embedding_service: SemanticEmbeddingService):
        self.embedding_service = embedding_service
        self._theme_embeddings: Optional[Dict[str, np.ndarray]] = None

    async def _get_theme_embeddings(self) -> Dict[str, np.ndarray]:
        """Get or compute theme embeddings."""
        if self._theme_embeddings is None:
            from app.services.advanced_similarity import EXTENDED_THEME_KEYWORDS

            self._theme_embeddings = {}
            for theme_id, keywords in EXTENDED_THEME_KEYWORDS.items():
                theme_text = " ".join(keywords)
                self._theme_embeddings[theme_id] = await self.embedding_service.compute_embedding(theme_text)

        return self._theme_embeddings

    async def compute_enhanced_similarity(
        self,
        source_text: str,
        target_text: str,
        source_sura: int,
        target_sura: int,
        source_aya: int,
        target_aya: int,
        base_scores: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute enhanced similarity with multiple contextual signals.

        Returns a comprehensive similarity analysis.
        """
        # Semantic embedding similarity
        semantic_sim = await self.embedding_service.compute_similarity(source_text, target_text)

        # Theme analysis for both texts
        theme_embeddings = await self._get_theme_embeddings()
        source_themes = await self.embedding_service.analyze_semantic_themes(
            source_text, theme_embeddings
        )
        target_themes = await self.embedding_service.analyze_semantic_themes(
            target_text, theme_embeddings
        )

        # Compute theme overlap
        source_theme_ids = {t[0] for t in source_themes}
        target_theme_ids = {t[0] for t in target_themes}
        shared_themes = source_theme_ids & target_theme_ids

        theme_overlap = len(shared_themes) / max(len(source_theme_ids | target_theme_ids), 1)

        # Structural similarity (same sura, nearby verses)
        structural_sim = 0.0
        if source_sura == target_sura:
            structural_sim = 0.3
            verse_distance = abs(source_aya - target_aya)
            if verse_distance <= 5:
                structural_sim += 0.2 * (1 - verse_distance / 5)

        # Combine scores
        combined_score = (
            semantic_sim * 0.40 +
            theme_overlap * 0.30 +
            structural_sim * 0.10 +
            (base_scores.get("combined", 0.0) * 0.20 if base_scores else 0.0)
        )

        return {
            "semantic_similarity": round(semantic_sim, 4),
            "theme_overlap": round(theme_overlap, 4),
            "structural_similarity": round(structural_sim, 4),
            "combined_enhanced": round(combined_score, 4),
            "confidence": self.embedding_service.get_confidence_level(combined_score),
            "source_themes": [{"theme": t[0], "score": round(t[1], 3)} for t in source_themes[:3]],
            "target_themes": [{"theme": t[0], "score": round(t[1], 3)} for t in target_themes[:3]],
            "shared_themes": list(shared_themes),
        }


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

semantic_embedding_service = SemanticEmbeddingService()
contextual_enhancer = ContextualSimilarityEnhancer(semantic_embedding_service)
