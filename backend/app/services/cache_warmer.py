"""
Cache Warming Service for Pre-populating Frequently Accessed Content.

Pre-loads cache with popular Quranic content to improve first-request latency:
- Popular surahs (Al-Fatiha, last 10 surahs)
- Frequently accessed tafseer
- Common search queries

Can be run on startup or scheduled periodically.

Arabic: خدمة تسخين الذاكرة المؤقتة
"""
import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WarmingResult:
    """Result of cache warming operation."""
    started_at: datetime
    completed_at: datetime
    total_items: int
    success_count: int
    error_count: int
    errors: List[str]
    duration_ms: int

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total_items if self.total_items > 0 else 0.0


# Popular content to warm
POPULAR_SURAHS = [1, 2, 36, 55, 67, 78, 103, 108, 110, 112, 113, 114]  # Fatiha, Baqarah, Ya-Sin, etc.
POPULAR_VERSES = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),  # Al-Fatiha
    (2, 255),  # Ayat al-Kursi
    (2, 256),  # La ikraha fi'd-din
    (2, 285), (2, 286),  # Last verses of Baqarah
    (112, 1), (112, 2), (112, 3), (112, 4),  # Al-Ikhlas
    (113, 1), (113, 2), (113, 3), (113, 4), (113, 5),  # Al-Falaq
    (114, 1), (114, 2), (114, 3), (114, 4), (114, 5), (114, 6),  # An-Nas
]
DEFAULT_EDITIONS = ["ar.muyassar", "en.sahih"]


class CacheWarmer:
    """
    Service to warm caches with frequently accessed content.

    Reduces cold-start latency by pre-loading popular verses,
    tafseer, and grammar analysis into the cache.
    """

    def __init__(self):
        self._tafseer_client = None
        self._cache = None
        self._last_warming: WarmingResult = None

    async def _init_clients(self):
        """Initialize API clients."""
        if self._tafseer_client is None:
            from app.services.tafseer_api import get_tafseer_client
            self._tafseer_client = get_tafseer_client()

        if self._cache is None:
            try:
                from app.services.redis_cache import get_hybrid_cache
                self._cache = get_hybrid_cache()
            except Exception as e:
                logger.warning(f"Failed to get hybrid cache: {e}")

    async def warm_tafseer_editions(self) -> Dict[str, int]:
        """Pre-fetch tafseer edition list."""
        await self._init_clients()
        result = {"editions": 0, "errors": 0}

        try:
            editions = await self._tafseer_client.get_editions()
            result["editions"] = len(editions)
            logger.info(f"Warmed {len(editions)} tafseer editions")
        except Exception as e:
            result["errors"] = 1
            logger.error(f"Failed to warm tafseer editions: {e}")

        return result

    async def warm_popular_verses(
        self,
        editions: List[str] = None,
    ) -> Dict[str, int]:
        """Pre-fetch tafseer for popular verses."""
        await self._init_clients()
        editions = editions or DEFAULT_EDITIONS

        result = {"verses": 0, "tafasir": 0, "errors": 0}
        errors = []

        for surah, ayah in POPULAR_VERSES:
            try:
                response = await self._tafseer_client.get_tafseer(surah, ayah, editions)
                if response.success:
                    result["verses"] += 1
                    result["tafasir"] += len(response.tafasir)
                else:
                    result["errors"] += 1
                    errors.append(f"Verse {surah}:{ayah} - {response.error}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                result["errors"] += 1
                errors.append(f"Verse {surah}:{ayah} - {str(e)}")

        logger.info(
            f"Warmed {result['verses']} popular verses with {result['tafasir']} tafseer entries"
        )
        return result

    async def warm_popular_surahs(
        self,
        edition: str = "ar.muyassar",
    ) -> Dict[str, int]:
        """Pre-fetch tafseer for entire popular surahs."""
        await self._init_clients()

        result = {"surahs": 0, "verses": 0, "errors": 0}

        # Only warm short surahs to avoid huge cache entries
        short_surahs = [s for s in POPULAR_SURAHS if s >= 78]  # Juz Amma

        for surah in short_surahs:
            try:
                verses = await self._tafseer_client.get_surah_tafseer(surah, edition)
                if verses:
                    result["surahs"] += 1
                    result["verses"] += len(verses)
                else:
                    result["errors"] += 1

                await asyncio.sleep(0.2)

            except Exception as e:
                result["errors"] += 1
                logger.error(f"Failed to warm surah {surah}: {e}")

        logger.info(
            f"Warmed {result['surahs']} surahs with {result['verses']} verses"
        )
        return result

    async def warm_all(
        self,
        include_full_surahs: bool = False,
    ) -> WarmingResult:
        """
        Warm all caches with popular content.

        Args:
            include_full_surahs: Also warm full surah tafseer (slower)

        Returns:
            WarmingResult with statistics
        """
        started_at = datetime.utcnow()
        import time
        start = time.perf_counter()

        total_items = 0
        success_count = 0
        error_count = 0
        errors = []

        logger.info("Starting cache warming...")

        # Warm editions
        editions_result = await self.warm_tafseer_editions()
        total_items += 1
        if editions_result["errors"] == 0:
            success_count += 1
        else:
            error_count += 1
            errors.append("Failed to warm editions")

        # Warm popular verses
        verses_result = await self.warm_popular_verses()
        total_items += len(POPULAR_VERSES)
        success_count += verses_result["verses"]
        error_count += verses_result["errors"]

        # Optionally warm full surahs
        if include_full_surahs:
            surahs_result = await self.warm_popular_surahs()
            total_items += len([s for s in POPULAR_SURAHS if s >= 78])
            success_count += surahs_result["surahs"]
            error_count += surahs_result["errors"]

        completed_at = datetime.utcnow()
        duration_ms = int((time.perf_counter() - start) * 1000)

        self._last_warming = WarmingResult(
            started_at=started_at,
            completed_at=completed_at,
            total_items=total_items,
            success_count=success_count,
            error_count=error_count,
            errors=errors[:10],  # Keep only first 10 errors
            duration_ms=duration_ms,
        )

        logger.info(
            f"Cache warming completed: {success_count}/{total_items} items "
            f"in {duration_ms}ms ({self._last_warming.success_rate*100:.1f}% success)"
        )

        return self._last_warming

    def get_last_warming_result(self) -> Dict[str, Any]:
        """Get result of last warming operation."""
        if not self._last_warming:
            return {"status": "never_run"}

        return {
            "status": "completed",
            "started_at": self._last_warming.started_at.isoformat(),
            "completed_at": self._last_warming.completed_at.isoformat(),
            "total_items": self._last_warming.total_items,
            "success_count": self._last_warming.success_count,
            "error_count": self._last_warming.error_count,
            "success_rate": round(self._last_warming.success_rate * 100, 2),
            "duration_ms": self._last_warming.duration_ms,
            "errors": self._last_warming.errors,
        }


# Popular RAG questions to pre-cache
POPULAR_RAG_QUESTIONS = {
    "en": [
        "What is the meaning of Ayat al-Kursi (2:255)?",
        "What is the meaning of Surah Al-Fatiha?",
        "What does the Quran say about patience (sabr)?",
        "What is taqwa in Islam?",
        "What does the Quran say about mercy?",
        "Tell me about the story of Prophet Musa",
        "What is the story of Prophet Yusuf?",
        "What does the Quran say about prayer?",
        "What is the concept of tawakkul?",
        "What does the Quran say about gratitude?",
    ],
    "ar": [
        "ما معنى آية الكرسي؟",
        "ما معنى سورة الفاتحة؟",
        "ماذا يقول القرآن عن الصبر؟",
        "ما هي التقوى في الإسلام؟",
        "أخبرني عن قصة موسى عليه السلام",
        "ما قصة يوسف عليه السلام؟",
    ],
}


class RAGCacheWarmer:
    """
    Warms the RAG response cache with popular questions.

    This is separate from tafseer caching and handles full
    RAG pipeline responses (answer + citations).
    """

    def __init__(self, session):
        self.session = session

    async def warm_rag_cache(
        self,
        languages: List[str] = None,
        max_questions: int = None,
    ) -> Dict[str, Any]:
        """
        Warm RAG cache with popular questions.

        Args:
            languages: Languages to warm (default: ['en', 'ar'])
            max_questions: Max questions per language (None = all)

        Returns:
            Dictionary with warming statistics
        """
        from app.api.routes.rag import get_rag_cache, make_rag_cache_key
        from pydantic import BaseModel, Field

        languages = languages or ["en", "ar"]
        rag_cache = get_rag_cache()

        result = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        # Create AskRequest class locally to avoid circular import
        class AskRequest(BaseModel):
            question: str
            language: str = "en"
            include_scholarly_debate: bool = True
            preferred_sources: List[str] = Field(default_factory=list)
            max_sources: int = 5

        for lang in languages:
            questions = POPULAR_RAG_QUESTIONS.get(lang, [])
            if max_questions:
                questions = questions[:max_questions]

            for question in questions:
                result["total"] += 1

                # Check if already cached
                request = AskRequest(question=question, language=lang)
                cache_key = make_rag_cache_key(request)

                try:
                    cached = await rag_cache.get(cache_key)
                    if cached:
                        result["skipped"] += 1
                        logger.debug(f"RAG cache warm: skipped (cached): {question[:40]}...")
                        continue
                except Exception as e:
                    logger.warning(f"Cache check failed: {e}")

                # Generate response via RAG pipeline
                try:
                    from app.rag.pipeline import RAGPipeline

                    pipeline = RAGPipeline(self.session)
                    response = await pipeline.query(
                        question=question,
                        language=lang,
                        include_scholarly_debate=True,
                        preferred_sources=[],
                        max_sources=5,
                    )

                    # Cache if confidence is acceptable
                    if response.confidence >= 0.3:
                        response_dict = response.to_dict()
                        response_dict["cached"] = False
                        response_dict["pre_warmed"] = True

                        await rag_cache.set(cache_key, response_dict, ttl=3600)
                        result["success"] += 1
                        logger.info(f"RAG cache warm: stored: {question[:40]}... (conf={response.confidence:.2f})")
                    else:
                        result["failed"] += 1
                        result["errors"].append(f"Low confidence: {question[:40]}...")

                except Exception as e:
                    result["failed"] += 1
                    result["errors"].append(f"Error: {str(e)[:50]}")
                    logger.error(f"RAG cache warm failed: {e}")

                # Small delay
                await asyncio.sleep(1.0)

        return result


# Singleton instance
_warmer_instance: CacheWarmer = None


def get_cache_warmer() -> CacheWarmer:
    """Get the cache warmer singleton instance."""
    global _warmer_instance
    if _warmer_instance is None:
        _warmer_instance = CacheWarmer()
    return _warmer_instance


async def run_cache_warming(include_full_surahs: bool = False) -> WarmingResult:
    """Convenience function to run cache warming."""
    warmer = get_cache_warmer()
    return await warmer.warm_all(include_full_surahs=include_full_surahs)


async def warm_rag_cache(session, **kwargs) -> Dict[str, Any]:
    """Convenience function to warm RAG cache."""
    warmer = RAGCacheWarmer(session)
    return await warmer.warm_rag_cache(**kwargs)
