"""
Redis Cache Backend for Distributed Caching.

Provides L2 caching layer that complements the in-memory L1 cache.
Enables cache sharing across multiple backend instances.

Features:
- Automatic serialization/deserialization
- Connection pooling
- Graceful degradation on Redis unavailability
- TTL support with automatic expiration
- Key prefixing for namespace isolation

Arabic: خدمة التخزين المؤقت الموزع باستخدام Redis
"""
import json
import logging
import asyncio
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed. Use: pip install redis")


@dataclass
class RedisStats:
    """Redis cache statistics."""
    connected: bool = False
    hits: int = 0
    misses: int = 0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class RedisCache:
    """
    Redis cache backend for distributed caching.

    Implements async operations with automatic reconnection
    and graceful degradation when Redis is unavailable.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "tadabbur:",
        default_ttl: int = 3600,
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        retry_on_error: bool = True,
    ):
        self.url = url
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.retry_on_error = retry_on_error

        self._client: Optional[Any] = None
        self._pool: Optional[Any] = None
        self._connected = False
        self._stats = RedisStats()
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Establish connection to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not available")
            return False

        if self._connected and self._client:
            return True

        async with self._lock:
            if self._connected and self._client:
                return True

            try:
                self._client = aioredis.from_url(
                    self.url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_timeout,
                    retry_on_timeout=self.retry_on_error,
                    max_connections=self.max_connections,
                )

                # Test connection
                await self._client.ping()
                self._connected = True
                self._stats.connected = True
                logger.info(f"Connected to Redis at {self.url}")
                return True

            except Exception as e:
                self._stats.errors += 1
                self._stats.last_error = str(e)
                self._stats.last_error_time = datetime.utcnow()
                logger.error(f"Failed to connect to Redis: {e}")
                return False

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
            self._stats.connected = False

    def _make_key(self, key: str) -> str:
        """Generate prefixed key."""
        return f"{self.key_prefix}{key}"

    def _serialize(self, value: Any) -> str:
        """Serialize value for storage."""
        return json.dumps(value, default=str, ensure_ascii=False)

    def _deserialize(self, data: str) -> Any:
        """Deserialize stored value."""
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self._connected:
            if not await self.connect():
                self._stats.misses += 1
                return None

        try:
            full_key = self._make_key(key)
            data = await self._client.get(full_key)

            if data is None:
                self._stats.misses += 1
                return None

            self._stats.hits += 1
            return self._deserialize(data)

        except Exception as e:
            self._stats.errors += 1
            self._stats.misses += 1
            self._stats.last_error = str(e)
            self._stats.last_error_time = datetime.utcnow()
            logger.error(f"Redis GET error for key {key}: {e}")
            self._connected = False
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in Redis with optional TTL."""
        if not self._connected:
            if not await self.connect():
                return False

        try:
            full_key = self._make_key(key)
            serialized = self._serialize(value)
            expire = ttl or self.default_ttl

            await self._client.setex(full_key, expire, serialized)
            return True

        except Exception as e:
            self._stats.errors += 1
            self._stats.last_error = str(e)
            self._stats.last_error_time = datetime.utcnow()
            logger.error(f"Redis SET error for key {key}: {e}")
            self._connected = False
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._connected:
            if not await self.connect():
                return False

        try:
            full_key = self._make_key(key)
            result = await self._client.delete(full_key)
            return result > 0

        except Exception as e:
            self._stats.errors += 1
            self._stats.last_error = str(e)
            logger.error(f"Redis DELETE error for key {key}: {e}")
            self._connected = False
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._connected:
            if not await self.connect():
                return False

        try:
            full_key = self._make_key(key)
            return await self._client.exists(full_key) > 0

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            self._connected = False
            return False

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once."""
        if not keys:
            return {}

        if not self._connected:
            if not await self.connect():
                self._stats.misses += len(keys)
                return {}

        try:
            full_keys = [self._make_key(k) for k in keys]
            values = await self._client.mget(full_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
                    self._stats.hits += 1
                else:
                    self._stats.misses += 1

            return result

        except Exception as e:
            self._stats.errors += 1
            self._stats.misses += len(keys)
            logger.error(f"Redis MGET error: {e}")
            self._connected = False
            return {}

    async def mset(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set multiple keys at once."""
        if not items:
            return True

        if not self._connected:
            if not await self.connect():
                return False

        try:
            expire = ttl or self.default_ttl
            pipe = self._client.pipeline()

            for key, value in items.items():
                full_key = self._make_key(key)
                serialized = self._serialize(value)
                pipe.setex(full_key, expire, serialized)

            await pipe.execute()
            return True

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Redis MSET error: {e}")
            self._connected = False
            return False

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys matching a prefix."""
        if not self._connected:
            if not await self.connect():
                return 0

        try:
            pattern = self._make_key(f"{prefix}*")
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += await self._client.delete(*keys)
                if cursor == 0:
                    break

            return deleted

        except Exception as e:
            self._stats.errors += 1
            logger.error(f"Redis CLEAR_PREFIX error: {e}")
            self._connected = False
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health and return stats."""
        healthy = False
        latency_ms = 0

        if self._connected or await self.connect():
            try:
                start = asyncio.get_event_loop().time()
                await self._client.ping()
                latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
                healthy = True
            except Exception as e:
                self._stats.last_error = str(e)
                self._connected = False

        return {
            "healthy": healthy,
            "connected": self._connected,
            "url": self.url.split("@")[-1] if "@" in self.url else self.url,
            "latency_ms": latency_ms,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": round(self._stats.hit_rate * 100, 2),
            "errors": self._stats.errors,
            "last_error": self._stats.last_error,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "connected": self._connected,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": round(self._stats.hit_rate * 100, 2),
            "errors": self._stats.errors,
            "last_error": self._stats.last_error,
            "last_error_time": self._stats.last_error_time.isoformat() if self._stats.last_error_time else None,
        }


# =============================================================================
# HYBRID CACHE (L1 + L2)
# =============================================================================

class HybridCache:
    """
    Two-tier cache combining in-memory L1 with Redis L2.

    - L1 (in-memory): Fast, per-instance, limited size
    - L2 (Redis): Distributed, shared across instances, larger capacity

    Read path: L1 -> L2 -> compute
    Write path: Write-through to both L1 and L2

    Arabic: ذاكرة مؤقتة هجينة متعددة المستويات
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        l1_max_size: int = 10000,
        l1_default_ttl: int = 300,      # 5 minutes for L1
        l2_default_ttl: int = 3600,     # 1 hour for L2
        key_prefix: str = "tadabbur:",
        enable_redis: bool = True,
    ):
        from app.services.cache_service import LRUCache

        self.l1 = LRUCache(max_size=l1_max_size, default_ttl=l1_default_ttl)
        self.l2: Optional[RedisCache] = None
        self.l2_default_ttl = l2_default_ttl
        self.enable_redis = enable_redis

        if enable_redis and REDIS_AVAILABLE:
            self.l2 = RedisCache(
                url=redis_url,
                key_prefix=key_prefix,
                default_ttl=l2_default_ttl,
            )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 first, then L2).

        If found in L2 but not L1, populate L1.
        """
        # Try L1 first
        value = self.l1.get(key)
        if value is not None:
            return value

        # Try L2
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                # Populate L1
                self.l1.set(key, value)
                return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in both L1 and L2 (write-through).
        """
        # Write to L1
        self.l1.set(key, value, ttl=l1_ttl)

        # Write to L2 (async, don't wait)
        if self.l2:
            asyncio.create_task(self.l2.set(key, value, ttl=l2_ttl))

    async def delete(self, key: str) -> None:
        """Delete from both L1 and L2."""
        self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)

    async def get_or_compute(
        self,
        key: str,
        compute_fn,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute if not found."""
        # Try cache
        value = await self.get(key)
        if value is not None:
            return value

        # Compute
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Cache result
        await self.set(key, value, l1_ttl, l2_ttl)

        return value

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        stats = {
            "l1": self.l1.get_stats(),
            "l2": self.l2.get_stats() if self.l2 else {"enabled": False},
            "redis_available": REDIS_AVAILABLE,
        }

        # Calculate combined hit rate
        l1_hits = stats["l1"]["hits"]
        l1_misses = stats["l1"]["misses"]
        l2_hits = stats["l2"].get("hits", 0) if self.l2 else 0

        total_requests = l1_hits + l1_misses
        total_hits = l1_hits + l2_hits

        stats["combined"] = {
            "total_requests": total_requests,
            "l1_hit_rate": stats["l1"]["hit_rate"],
            "l2_hit_rate": stats["l2"].get("hit_rate", 0) if self.l2 else 0,
            "effective_hit_rate": round(
                total_hits / total_requests * 100 if total_requests > 0 else 0, 2
            ),
        }

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all cache tiers."""
        health = {
            "l1": {
                "healthy": True,
                "entries": self.l1.get_stats()["total_entries"],
            },
            "l2": await self.l2.health_check() if self.l2 else {"enabled": False},
        }

        health["overall_healthy"] = health["l1"]["healthy"] and (
            not self.l2 or health["l2"].get("healthy", False)
        )

        return health


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_hybrid_cache: Optional[HybridCache] = None


def get_hybrid_cache() -> HybridCache:
    """Get the singleton hybrid cache instance."""
    global _hybrid_cache

    if _hybrid_cache is None:
        from app.core.config import settings

        _hybrid_cache = HybridCache(
            redis_url=settings.redis_url,
            enable_redis=settings.feature_redis_cache,
            key_prefix="tadabbur:",
        )

    return _hybrid_cache


async def init_cache() -> bool:
    """Initialize the cache (connect to Redis if enabled)."""
    cache = get_hybrid_cache()
    if cache.l2:
        return await cache.l2.connect()
    return True
