"""
Fast Similarity Search Service for Quranic Verses.

Uses pre-computed vectors and numpy for O(1) lookup with caching.
Target: <100ms response time.

Arabic: خدمة البحث السريع عن التشابه في الآيات القرآنية
"""

import logging
import hashlib
import json
import time
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import math

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse
from app.services.quran_text_utils import (
    preprocess_for_similarity,
    is_bismillah_verse,
    is_first_verse_with_bismillah,
)
from app.services.quran_search import normalize_arabic, extract_words

logger = logging.getLogger(__name__)


@dataclass
class FastSimilarityResult:
    """Fast similarity search result."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    text_imlaei: str
    reference: str
    similarity_score: float
    shared_words: List[str]


class FastSimilarityService:
    """
    High-performance similarity search using pre-computed vectors.

    Features:
    - Pre-computed TF-IDF vectors in memory
    - Numpy vectorized cosine similarity (milliseconds)
    - LRU caching for repeated queries
    - Bismillah exclusion built-in
    """

    # Class-level cache for singleton pattern
    _instance = None
    _initialized = False
    _verses_data: List[Dict] = []
    _tfidf_matrix: Optional[np.ndarray] = None
    _vocabulary: Dict[str, int] = {}
    _idf_values: Dict[str, float] = {}
    _verse_index: Dict[Tuple[int, int], int] = {}  # (sura, aya) -> index
    _result_cache: Dict[str, Tuple[float, Any]] = {}  # cache with timestamps
    _cache_ttl = 300  # 5 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls, session: AsyncSession) -> bool:
        """
        Initialize the service with pre-computed vectors.
        Call once at application startup.
        """
        if cls._initialized:
            return True

        start_time = time.time()
        logger.info("Initializing FastSimilarityService...")

        try:
            # Load all verses
            result = await session.execute(select(QuranVerse))
            verses = result.scalars().all()

            cls._verses_data = []
            processed_texts = []

            for verse in verses:
                # Skip pure Bismillah verses
                if is_bismillah_verse(verse.text_imlaei):
                    continue

                # Preprocess text (remove Bismillah from first verses)
                processed_text = preprocess_for_similarity(
                    verse.text_imlaei,
                    sura_no=verse.sura_no,
                    aya_no=verse.aya_no,
                    exclude_bismillah=True
                )

                # Skip if very little content after preprocessing
                if is_first_verse_with_bismillah(verse.sura_no, verse.aya_no):
                    if len(processed_text.strip().split()) < 2:
                        continue

                verse_data = {
                    'id': verse.id,
                    'sura_no': verse.sura_no,
                    'sura_name_ar': verse.sura_name_ar,
                    'sura_name_en': verse.sura_name_en,
                    'aya_no': verse.aya_no,
                    'text_uthmani': verse.text_uthmani,
                    'text_imlaei': verse.text_imlaei,
                    'processed_text': processed_text,
                }

                cls._verses_data.append(verse_data)
                processed_texts.append(processed_text)
                cls._verse_index[(verse.sura_no, verse.aya_no)] = len(cls._verses_data) - 1

            # Build vocabulary and compute IDF
            doc_freq = Counter()
            all_words = []

            for text in processed_texts:
                words = set(extract_words(text))
                all_words.append(words)
                for word in words:
                    doc_freq[word] += 1

            num_docs = len(processed_texts)
            cls._vocabulary = {}
            cls._idf_values = {}

            for idx, (word, freq) in enumerate(doc_freq.items()):
                cls._vocabulary[word] = idx
                cls._idf_values[word] = math.log(num_docs / (freq + 1)) + 1

            vocab_size = len(cls._vocabulary)

            # Build TF-IDF matrix (sparse representation using numpy)
            logger.info(f"Building TF-IDF matrix: {num_docs} docs x {vocab_size} vocab")
            cls._tfidf_matrix = np.zeros((num_docs, vocab_size), dtype=np.float32)

            for doc_idx, (text, words) in enumerate(zip(processed_texts, all_words)):
                word_counts = Counter(extract_words(text))
                total_words = sum(word_counts.values())

                for word, count in word_counts.items():
                    if word in cls._vocabulary:
                        word_idx = cls._vocabulary[word]
                        tf = count / total_words
                        idf = cls._idf_values[word]
                        cls._tfidf_matrix[doc_idx, word_idx] = tf * idf

            # Normalize vectors for faster cosine similarity
            norms = np.linalg.norm(cls._tfidf_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            cls._tfidf_matrix = cls._tfidf_matrix / norms

            cls._initialized = True
            elapsed = time.time() - start_time
            logger.info(f"FastSimilarityService initialized in {elapsed:.2f}s with {num_docs} verses")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize FastSimilarityService: {e}")
            return False

    @classmethod
    def _get_cache_key(cls, sura_no: int, aya_no: int, top_k: int) -> str:
        """Generate cache key for a query."""
        return f"sim:{sura_no}:{aya_no}:{top_k}"

    @classmethod
    def _check_cache(cls, cache_key: str) -> Optional[Any]:
        """Check if result is in cache and not expired."""
        if cache_key in cls._result_cache:
            timestamp, result = cls._result_cache[cache_key]
            if time.time() - timestamp < cls._cache_ttl:
                return result
            else:
                del cls._result_cache[cache_key]
        return None

    @classmethod
    def _set_cache(cls, cache_key: str, result: Any):
        """Store result in cache."""
        cls._result_cache[cache_key] = (time.time(), result)

        # Limit cache size (LRU-like cleanup)
        if len(cls._result_cache) > 1000:
            # Remove oldest entries
            sorted_keys = sorted(cls._result_cache.keys(),
                               key=lambda k: cls._result_cache[k][0])
            for key in sorted_keys[:200]:
                del cls._result_cache[key]

    async def find_similar(
        self,
        sura_no: int,
        aya_no: int,
        top_k: int = 20,
        min_score: float = 0.1,
        exclude_same_sura: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Find similar verses using pre-computed vectors.

        Args:
            sura_no: Source verse sura number
            aya_no: Source verse aya number
            top_k: Maximum results
            min_score: Minimum similarity threshold
            exclude_same_sura: Exclude verses from same sura
            session: Database session (for initialization if needed)

        Returns:
            Dict with search results and metadata
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._get_cache_key(sura_no, aya_no, top_k)
        cached = self._check_cache(cache_key)
        if cached:
            cached['from_cache'] = True
            cached['search_time_ms'] = round((time.time() - start_time) * 1000, 2)
            return cached

        # Initialize if needed
        if not self._initialized and session:
            await self.initialize(session)

        if not self._initialized:
            return {
                'error': 'Service not initialized',
                'matches': [],
                'search_time_ms': 0,
            }

        # Get source verse index
        source_idx = self._verse_index.get((sura_no, aya_no))
        if source_idx is None:
            return {
                'error': f'Verse {sura_no}:{aya_no} not found',
                'matches': [],
                'search_time_ms': 0,
            }

        source_data = self._verses_data[source_idx]
        source_vector = self._tfidf_matrix[source_idx]

        # Compute cosine similarities (vectorized - very fast!)
        # Since vectors are normalized, dot product = cosine similarity
        similarities = np.dot(self._tfidf_matrix, source_vector)

        # Set self-similarity to -1 to exclude
        similarities[source_idx] = -1

        # Apply same-sura filter if needed
        if exclude_same_sura:
            for idx, v in enumerate(self._verses_data):
                if v['sura_no'] == sura_no:
                    similarities[idx] = -1

        # Get top-k indices
        # Use argpartition for O(n) instead of full sort O(n log n)
        k = min(top_k * 2, len(similarities))  # Get extra for filtering
        top_indices = np.argpartition(similarities, -k)[-k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        # Build results
        source_words = set(extract_words(source_data['processed_text']))
        matches = []

        for idx in top_indices:
            score = float(similarities[idx])
            if score < min_score:
                break

            verse = self._verses_data[idx]
            verse_words = set(extract_words(verse['processed_text']))
            shared = list(source_words & verse_words)[:10]

            # Use processed text (without Bismillah) for display if it's a first verse
            display_text = verse['text_uthmani']
            if is_first_verse_with_bismillah(verse['sura_no'], verse['aya_no']):
                # Remove Bismillah from display text
                display_text = preprocess_for_similarity(
                    verse['text_uthmani'],
                    sura_no=verse['sura_no'],
                    aya_no=verse['aya_no'],
                    exclude_bismillah=True
                )

            matches.append(FastSimilarityResult(
                verse_id=verse['id'],
                sura_no=verse['sura_no'],
                sura_name_ar=verse['sura_name_ar'],
                sura_name_en=verse['sura_name_en'],
                aya_no=verse['aya_no'],
                text_uthmani=display_text,  # Show text without Bismillah for first verses
                text_imlaei=verse['processed_text'],  # Always show processed text
                reference=f"{verse['sura_no']}:{verse['aya_no']}",
                similarity_score=round(score, 4),
                shared_words=shared,
            ))

            if len(matches) >= top_k:
                break

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # Remove Bismillah from source verse display if it's a first verse
        source_display_text = source_data['text_uthmani']
        if is_first_verse_with_bismillah(source_data['sura_no'], source_data['aya_no']):
            source_display_text = preprocess_for_similarity(
                source_data['text_uthmani'],
                sura_no=source_data['sura_no'],
                aya_no=source_data['aya_no'],
                exclude_bismillah=True
            )

        result = {
            'source_verse': {
                'sura_no': source_data['sura_no'],
                'sura_name_ar': source_data['sura_name_ar'],
                'sura_name_en': source_data['sura_name_en'],
                'aya_no': source_data['aya_no'],
                'text_uthmani': source_display_text,  # Show text without Bismillah
                'text_original': source_data['text_uthmani'],  # Keep original for reference
                'reference': f"{source_data['sura_no']}:{source_data['aya_no']}",
            },
            'total_similar': len(matches),
            'matches': [
                {
                    'verse_id': m.verse_id,
                    'sura_no': m.sura_no,
                    'sura_name_ar': m.sura_name_ar,
                    'sura_name_en': m.sura_name_en,
                    'aya_no': m.aya_no,
                    'text_uthmani': m.text_uthmani,
                    'text_imlaei': m.text_imlaei,
                    'reference': m.reference,
                    'similarity_score': m.similarity_score,
                    'shared_words': m.shared_words,
                }
                for m in matches
            ],
            'search_time_ms': elapsed_ms,
            'from_cache': False,
        }

        # Cache the result
        self._set_cache(cache_key, result)

        return result

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if service is initialized."""
        return cls._initialized

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'initialized': cls._initialized,
            'verses_count': len(cls._verses_data),
            'vocabulary_size': len(cls._vocabulary),
            'cache_entries': len(cls._result_cache),
            'matrix_shape': cls._tfidf_matrix.shape if cls._tfidf_matrix is not None else None,
        }


# Singleton instance
_fast_similarity_service: Optional[FastSimilarityService] = None


def get_fast_similarity_service() -> FastSimilarityService:
    """Get fast similarity service singleton."""
    global _fast_similarity_service
    if _fast_similarity_service is None:
        _fast_similarity_service = FastSimilarityService()
    return _fast_similarity_service
