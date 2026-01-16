"""
Caching and Performance Optimization Service.

Provides caching strategies for:
1. Frequently searched terms and results
2. Commonly accessed verses and Tafsir
3. User preferences and recommendations
4. Embedding computations
5. Query result caching

Arabic: خدمة التخزين المؤقت وتحسين الأداء
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class CacheStrategy(str, Enum):
    """Cache eviction strategies."""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    TTL = "ttl"           # Time To Live
    HYBRID = "hybrid"     # Combination


class CacheType(str, Enum):
    """Types of cached content."""
    SEARCH_RESULTS = "search_results"
    VERSE_DATA = "verse_data"
    TAFSIR_DATA = "tafsir_data"
    EMBEDDINGS = "embeddings"
    USER_PREFS = "user_prefs"
    RECOMMENDATIONS = "recommendations"
    THEMES = "themes"
    AGGREGATIONS = "aggregations"


# Default TTL for different cache types (in seconds)
DEFAULT_TTL = {
    CacheType.SEARCH_RESULTS: 3600,      # 1 hour
    CacheType.VERSE_DATA: 86400,         # 24 hours
    CacheType.TAFSIR_DATA: 86400,        # 24 hours
    CacheType.EMBEDDINGS: 604800,        # 7 days
    CacheType.USER_PREFS: 1800,          # 30 minutes
    CacheType.RECOMMENDATIONS: 900,       # 15 minutes
    CacheType.THEMES: 43200,             # 12 hours
    CacheType.AGGREGATIONS: 3600,        # 1 hour
}

# Maximum cache sizes
MAX_CACHE_SIZES = {
    CacheType.SEARCH_RESULTS: 10000,
    CacheType.VERSE_DATA: 7000,           # All verses
    CacheType.TAFSIR_DATA: 5000,
    CacheType.EMBEDDINGS: 20000,
    CacheType.USER_PREFS: 10000,
    CacheType.RECOMMENDATIONS: 5000,
    CacheType.THEMES: 500,
    CacheType.AGGREGATIONS: 1000,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)

    @property
    def age_seconds(self) -> int:
        """Get age of entry in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())


@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int = 0
    total_size_bytes: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_cleanups: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# =============================================================================
# LRU CACHE IMPLEMENTATION
# =============================================================================

class LRUCache:
    """
    Least Recently Used cache implementation.

    Features:
    - O(1) get and set operations
    - Automatic eviction of least recently used items
    - TTL support
    - Size tracking
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if key not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key]

        # Check expiration
        if entry.is_expired:
            del self._cache[key]
            self._stats.expired_cleanups += 1
            self._stats.misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        self._stats.hits += 1

        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        cache_type: CacheType = CacheType.SEARCH_RESULTS,
        ttl: Optional[int] = None,
    ) -> None:
        """Set item in cache."""
        # Evict if at capacity
        while len(self._cache) >= self._max_size:
            self._evict_lru()

        # Estimate size
        try:
            size_bytes = len(json.dumps(value, default=str))
        except:
            size_bytes = 1000  # Default estimate

        entry = CacheEntry(
            key=key,
            value=value,
            cache_type=cache_type,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            ttl_seconds=ttl or self._default_ttl,
            size_bytes=size_bytes,
        )

        self._cache[key] = entry
        self._stats.total_entries = len(self._cache)
        self._stats.total_size_bytes += size_bytes

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._stats.evictions += 1
            self._stats.total_size_bytes -= entry.size_bytes

    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.total_entries = len(self._cache)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._stats = CacheStats()

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            self.delete(key)
            self._stats.expired_cleanups += 1

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "total_entries": self._stats.total_entries,
            "total_size_mb": round(self._stats.total_size_bytes / (1024 * 1024), 2),
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": round(self._stats.hit_rate * 100, 2),
            "evictions": self._stats.evictions,
            "expired_cleanups": self._stats.expired_cleanups,
            "max_size": self._max_size,
        }


# =============================================================================
# CACHE SERVICE
# =============================================================================

class CacheService:
    """
    Centralized caching service for the application.

    Features:
    - Multiple cache types with different TTLs
    - Automatic cleanup of expired entries
    - Cache warming for frequently accessed data
    - Statistics and monitoring
    """

    def __init__(self):
        # Initialize caches for different types
        self._caches: Dict[CacheType, LRUCache] = {}

        for cache_type in CacheType:
            max_size = MAX_CACHE_SIZES.get(cache_type, 1000)
            default_ttl = DEFAULT_TTL.get(cache_type, 3600)
            self._caches[cache_type] = LRUCache(max_size, default_ttl)

        # Query index for fast lookups
        self._query_index: Dict[str, List[str]] = {}

        # Warm cache flag
        self._warmed = False

    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = [prefix] + [str(a) for a in args]
        key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get_cached(
        self,
        cache_type: CacheType,
        key: str,
    ) -> Optional[Any]:
        """Get item from cache."""
        cache = self._caches.get(cache_type)
        if cache:
            return cache.get(key)
        return None

    async def set_cached(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set item in cache."""
        cache = self._caches.get(cache_type)
        if cache:
            cache.set(key, value, cache_type, ttl)

    async def get_or_compute(
        self,
        cache_type: CacheType,
        key: str,
        compute_fn: Callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute if not cached."""
        # Try cache first
        cached = await self.get_cached(cache_type, key)
        if cached is not None:
            return cached

        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Cache the result
        await self.set_cached(cache_type, key, value, ttl)

        return value

    async def cache_search_result(
        self,
        query: str,
        results: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Cache a search result."""
        key = self._get_cache_key("search", query.lower().strip())
        await self.set_cached(CacheType.SEARCH_RESULTS, key, results, ttl)

        # Index by query terms for partial matching
        terms = query.lower().split()
        for term in terms:
            if term not in self._query_index:
                self._query_index[term] = []
            if key not in self._query_index[term]:
                self._query_index[term].append(key)

    async def get_cached_search(
        self,
        query: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached search result."""
        key = self._get_cache_key("search", query.lower().strip())
        return await self.get_cached(CacheType.SEARCH_RESULTS, key)

    async def cache_verse(
        self,
        sura_no: int,
        aya_no: int,
        verse_data: Dict[str, Any],
    ) -> None:
        """Cache verse data."""
        key = f"verse:{sura_no}:{aya_no}"
        await self.set_cached(CacheType.VERSE_DATA, key, verse_data)

    async def get_cached_verse(
        self,
        sura_no: int,
        aya_no: int,
    ) -> Optional[Dict[str, Any]]:
        """Get cached verse data."""
        key = f"verse:{sura_no}:{aya_no}"
        return await self.get_cached(CacheType.VERSE_DATA, key)

    async def cache_tafsir(
        self,
        sura_no: int,
        aya_no: int,
        source_id: str,
        tafsir_data: Dict[str, Any],
    ) -> None:
        """Cache Tafsir data."""
        key = f"tafsir:{sura_no}:{aya_no}:{source_id}"
        await self.set_cached(CacheType.TAFSIR_DATA, key, tafsir_data)

    async def get_cached_tafsir(
        self,
        sura_no: int,
        aya_no: int,
        source_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached Tafsir data."""
        key = f"tafsir:{sura_no}:{aya_no}:{source_id}"
        return await self.get_cached(CacheType.TAFSIR_DATA, key)

    async def cache_embedding(
        self,
        text: str,
        embedding: Any,
    ) -> None:
        """Cache computed embedding."""
        key = hashlib.md5(text.encode()).hexdigest()
        await self.set_cached(CacheType.EMBEDDINGS, key, embedding)

    async def get_cached_embedding(
        self,
        text: str,
    ) -> Optional[Any]:
        """Get cached embedding."""
        key = hashlib.md5(text.encode()).hexdigest()
        return await self.get_cached(CacheType.EMBEDDINGS, key)

    async def cache_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """Cache user preferences."""
        key = f"prefs:{user_id}"
        await self.set_cached(CacheType.USER_PREFS, key, preferences)

    async def get_cached_user_preferences(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached user preferences."""
        key = f"prefs:{user_id}"
        return await self.get_cached(CacheType.USER_PREFS, key)

    async def cache_recommendations(
        self,
        user_id: str,
        recommendations: Dict[str, Any],
    ) -> None:
        """Cache user recommendations."""
        key = f"recs:{user_id}"
        await self.set_cached(CacheType.RECOMMENDATIONS, key, recommendations)

    async def get_cached_recommendations(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached user recommendations."""
        key = f"recs:{user_id}"
        return await self.get_cached(CacheType.RECOMMENDATIONS, key)

    async def invalidate_user_cache(
        self,
        user_id: str,
    ) -> None:
        """Invalidate all caches for a user."""
        prefs_cache = self._caches.get(CacheType.USER_PREFS)
        recs_cache = self._caches.get(CacheType.RECOMMENDATIONS)

        if prefs_cache:
            prefs_cache.delete(f"prefs:{user_id}")
        if recs_cache:
            recs_cache.delete(f"recs:{user_id}")

    async def cleanup_all_expired(self) -> Dict[str, int]:
        """Cleanup expired entries from all caches."""
        results = {}

        for cache_type, cache in self._caches.items():
            cleaned = cache.cleanup_expired()
            results[cache_type.value] = cleaned

        return results

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}

        for cache_type, cache in self._caches.items():
            stats[cache_type.value] = cache.get_stats()

        # Aggregate totals
        total_entries = sum(s["total_entries"] for s in stats.values())
        total_hits = sum(s["hits"] for s in stats.values())
        total_misses = sum(s["misses"] for s in stats.values())

        return {
            "caches": stats,
            "totals": {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "overall_hit_rate": round(
                    total_hits / (total_hits + total_misses) * 100
                    if (total_hits + total_misses) > 0 else 0,
                    2
                ),
            },
            "query_index_size": len(self._query_index),
        }

    async def warm_cache(
        self,
        session: Any,
    ) -> Dict[str, int]:
        """
        Pre-warm cache with frequently accessed data.

        Arabic: تسخين الذاكرة المؤقتة بالبيانات المستخدمة بكثرة
        """
        if self._warmed:
            return {"status": "already_warmed"}

        warmed = {}

        try:
            from app.models.quran import QuranVerse
            from sqlalchemy import select

            # Cache all verses from Al-Fatiha (most accessed)
            result = await session.execute(
                select(QuranVerse).where(QuranVerse.sura_no == 1)
            )
            fatiha_verses = result.scalars().all()

            for verse in fatiha_verses:
                await self.cache_verse(
                    verse.sura_no,
                    verse.aya_no,
                    {
                        "id": verse.id,
                        "sura_no": verse.sura_no,
                        "aya_no": verse.aya_no,
                        "text_uthmani": verse.text_uthmani,
                    }
                )

            warmed["fatiha_verses"] = len(fatiha_verses)

            # Cache popular short suras
            short_suras = [112, 113, 114, 108, 110]
            count = 0
            for sura_no in short_suras:
                result = await session.execute(
                    select(QuranVerse).where(QuranVerse.sura_no == sura_no)
                )
                verses = result.scalars().all()
                for verse in verses:
                    await self.cache_verse(
                        verse.sura_no,
                        verse.aya_no,
                        {
                            "id": verse.id,
                            "sura_no": verse.sura_no,
                            "aya_no": verse.aya_no,
                            "text_uthmani": verse.text_uthmani,
                        }
                    )
                    count += 1

            warmed["short_suras_verses"] = count

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            warmed["error"] = str(e)

        self._warmed = True
        return warmed

    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in self._caches.values():
            cache.clear()
        self._query_index.clear()
        self._warmed = False


# =============================================================================
# REDIS CACHE LAYER (L2 - Distributed)
# =============================================================================

class RedisCacheLayer:
    """
    Redis-based distributed cache layer (L2).

    Provides:
    - Distributed caching across multiple instances
    - Persistent cache across restarts
    - Larger storage capacity
    - TTL-based expiration

    Arabic: طبقة التخزين المؤقت الموزعة باستخدام Redis
    """

    def __init__(self, redis_url: str, key_prefix: str = "tadabbur:"):
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._client = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if self._connected:
            return True

        try:
            import redis.asyncio as redis
            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {self._redis_url}")
            return True
        except ImportError:
            logger.warning("redis package not installed, Redis cache disabled")
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            return False

    def _make_key(self, cache_type: CacheType, key: str) -> str:
        """Create namespaced Redis key."""
        return f"{self._key_prefix}{cache_type.value}:{key}"

    async def get(self, cache_type: CacheType, key: str) -> Optional[Any]:
        """Get item from Redis."""
        if not self._connected:
            return None

        try:
            redis_key = self._make_key(cache_type, key)
            data = await self._client.get(redis_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Redis get error: {e}")
            return None

    async def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> bool:
        """Set item in Redis with TTL."""
        if not self._connected:
            return False

        try:
            redis_key = self._make_key(cache_type, key)
            data = json.dumps(value, default=str)
            await self._client.setex(redis_key, ttl, data)
            return True
        except Exception as e:
            logger.debug(f"Redis set error: {e}")
            return False

    async def delete(self, cache_type: CacheType, key: str) -> bool:
        """Delete item from Redis."""
        if not self._connected:
            return False

        try:
            redis_key = self._make_key(cache_type, key)
            await self._client.delete(redis_key)
            return True
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._connected:
            return {"connected": False}

        try:
            info = await self._client.info("memory")
            keyspace = await self._client.info("keyspace")

            # Count keys by type
            key_counts = {}
            for cache_type in CacheType:
                pattern = self._make_key(cache_type, "*")
                keys = await self._client.keys(pattern)
                key_counts[cache_type.value] = len(keys)

            return {
                "connected": True,
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "peak_memory_mb": round(info.get("used_memory_peak", 0) / (1024 * 1024), 2),
                "keys_by_type": key_counts,
                "total_keys": sum(key_counts.values()),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"connected": True, "error": str(e)}

    async def clear_by_type(self, cache_type: CacheType) -> int:
        """Clear all keys for a cache type."""
        if not self._connected:
            return 0

        try:
            pattern = self._make_key(cache_type, "*")
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False


# =============================================================================
# HYBRID CACHE SERVICE (L1 + L2)
# =============================================================================

class HybridCacheService:
    """
    Hybrid caching service with L1 (in-memory) and L2 (Redis) layers.

    Features:
    - L1: Fast in-memory LRU cache for hot data
    - L2: Redis distributed cache for persistence and sharing
    - Write-through to L2, read-through from L1 then L2
    - Automatic failover to L1 if L2 unavailable

    Arabic: خدمة التخزين المؤقت الهجينة
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "tadabbur:",
        l1_max_size: int = 10000,
        l1_ttl: int = 300,
    ):
        # L1: In-memory cache (existing CacheService)
        self._l1 = CacheService()

        # L2: Redis cache layer
        self._l2 = RedisCacheLayer(redis_url, key_prefix)
        self._l2_enabled = False

        # Configuration
        self._l1_ttl = l1_ttl  # Shorter TTL for L1

        # Stats
        self._l1_hits = 0
        self._l2_hits = 0
        self._misses = 0

    async def initialize(self) -> bool:
        """Initialize hybrid cache (connect to Redis)."""
        from app.core.config import settings

        if settings.feature_redis_cache:
            self._l2_enabled = await self._l2.connect()

        return self._l2_enabled

    async def get(
        self,
        cache_type: CacheType,
        key: str,
    ) -> Optional[Any]:
        """
        Get from cache (L1 first, then L2).

        Read-through: If found in L2 but not L1, populate L1.
        """
        # Try L1 first
        value = await self._l1.get_cached(cache_type, key)
        if value is not None:
            self._l1_hits += 1
            return value

        # Try L2 if enabled
        if self._l2_enabled:
            value = await self._l2.get(cache_type, key)
            if value is not None:
                self._l2_hits += 1
                # Populate L1 for future requests
                await self._l1.set_cached(cache_type, key, value, self._l1_ttl)
                return value

        self._misses += 1
        return None

    async def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: int = None,
    ) -> None:
        """
        Set in cache (write-through to both layers).
        """
        if ttl is None:
            ttl = DEFAULT_TTL.get(cache_type, 3600)

        # Write to L1 with shorter TTL
        await self._l1.set_cached(cache_type, key, value, min(ttl, self._l1_ttl))

        # Write to L2 if enabled
        if self._l2_enabled:
            await self._l2.set(cache_type, key, value, ttl)

    async def delete(
        self,
        cache_type: CacheType,
        key: str,
    ) -> None:
        """Delete from both cache layers."""
        # Delete from L1
        cache = self._l1._caches.get(cache_type)
        if cache:
            cache.delete(key)

        # Delete from L2
        if self._l2_enabled:
            await self._l2.delete(cache_type, key)

    async def get_or_compute(
        self,
        cache_type: CacheType,
        key: str,
        compute_fn: Callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute if not cached."""
        # Try cache first
        value = await self.get(cache_type, key)
        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Cache the result
        await self.set(cache_type, key, value, ttl)

        return value

    # Convenience methods (delegating to underlying services)
    async def cache_search_result(self, query: str, results: Dict[str, Any], ttl: int = None):
        key = hashlib.md5(query.lower().strip().encode()).hexdigest()
        await self.set(CacheType.SEARCH_RESULTS, key, results, ttl)

    async def get_cached_search(self, query: str) -> Optional[Dict[str, Any]]:
        key = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return await self.get(CacheType.SEARCH_RESULTS, key)

    async def cache_verse(self, sura_no: int, aya_no: int, verse_data: Dict[str, Any]):
        key = f"verse:{sura_no}:{aya_no}"
        await self.set(CacheType.VERSE_DATA, key, verse_data)

    async def get_cached_verse(self, sura_no: int, aya_no: int) -> Optional[Dict[str, Any]]:
        key = f"verse:{sura_no}:{aya_no}"
        return await self.get(CacheType.VERSE_DATA, key)

    async def cache_concept_highlights(
        self,
        concept_ids: str,
        page_no: Optional[int],
        sura_no: Optional[int],
        highlights: Dict[str, Any],
    ):
        """Cache concept highlight results."""
        key = f"highlights:{concept_ids}:p{page_no or 0}:s{sura_no or 0}"
        await self.set(CacheType.SEARCH_RESULTS, key, highlights, 1800)  # 30 min TTL

    async def get_cached_concept_highlights(
        self,
        concept_ids: str,
        page_no: Optional[int],
        sura_no: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """Get cached concept highlights."""
        key = f"highlights:{concept_ids}:p{page_no or 0}:s{sura_no or 0}"
        return await self.get(CacheType.SEARCH_RESULTS, key)

    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        total_requests = self._l1_hits + self._l2_hits + self._misses

        stats = {
            "l1": self._l1.get_all_stats(),
            "l2_enabled": self._l2_enabled,
            "hybrid_stats": {
                "l1_hits": self._l1_hits,
                "l2_hits": self._l2_hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "l1_hit_rate": round(self._l1_hits / total_requests * 100, 2) if total_requests > 0 else 0,
                "overall_hit_rate": round((self._l1_hits + self._l2_hits) / total_requests * 100, 2) if total_requests > 0 else 0,
            },
        }

        return stats

    async def get_full_stats(self) -> Dict[str, Any]:
        """Get full stats including Redis."""
        stats = self.get_stats()
        if self._l2_enabled:
            stats["l2"] = await self._l2.get_stats()
        return stats

    async def warm_cache(self, session: Any) -> Dict[str, int]:
        """Warm both cache layers."""
        return await self._l1.warm_cache(session)

    async def close(self):
        """Close connections."""
        if self._l2_enabled:
            await self._l2.close()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Legacy in-memory cache service
cache_service = CacheService()

# Hybrid cache service (L1 + L2 Redis)
_hybrid_cache: Optional[HybridCacheService] = None


async def get_hybrid_cache() -> HybridCacheService:
    """Get or create hybrid cache service."""
    global _hybrid_cache

    if _hybrid_cache is None:
        from app.core.config import settings

        _hybrid_cache = HybridCacheService(
            redis_url=settings.redis_url,
            key_prefix=settings.redis_key_prefix,
            l1_max_size=settings.redis_l1_max_size,
            l1_ttl=settings.redis_l1_ttl,
        )
        await _hybrid_cache.initialize()

    return _hybrid_cache
