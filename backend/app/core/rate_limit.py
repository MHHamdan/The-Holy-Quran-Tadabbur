"""
Per-client rate limiting for sensitive endpoints.

Design:
  - Per-client-IP, 60-second window.
  - The client IP is ``request.client.host`` ONLY. Uvicorn's
    ``--proxy-headers --forwarded-allow-ips <proxy CIDR>`` already rewrites it
    from X-Forwarded-For when (and only when) the TCP peer is a trusted proxy.
    Reading X-Forwarded-For here would let any caller pick its own bucket.
  - Two backends:
      * in-process sliding window (always available, used in development and
        tests, and as the fallback whenever Redis is unreachable);
      * Redis fixed window (INCR + EXPIRE per limiter:ip:window), enabled with
        RATE_LIMIT_BACKEND=redis so that every uvicorn worker shares one count.
  - Returns HTTP 429 with a bilingual message on limit exceeded.
  - Exports named FastAPI dependency functions so callers can override
    them in tests via app.dependency_overrides.
  - Logs never carry the client IP (see the in-app privacy policy).

Per-endpoint limits (conservative defaults; adjust via constructor):
  Endpoint              Limit      Rationale
  RAG /ask, LLM routes  20/min     LLM call is expensive; prevents cost abuse
  Speech-to-text        10/min     Each call spends HF STT credit
  Admin /decision       10/min     Write operation; extra-strict
  Search                60/min     Read-only; generous enough for UI typeahead
  Vocabulary            60/min     No LLM call; lenient
"""

import logging
import os
import time
from threading import Lock
from typing import Callable, Optional

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

_RETRY_AFTER_SECONDS = 60
# Sweep expired keys after this many is_allowed() calls, so one-off client IPs
# do not accumulate as permanent dict keys.
_SWEEP_EVERY = 1000
# After a Redis failure, use the in-process fallback for this long before
# trying Redis again (avoids paying a connection timeout on every request).
_REDIS_RETRY_SECONDS = 30.0


def _get_client_ip(request: Request) -> str:
    """
    The client IP as seen by the ASGI server.

    Deliberately ignores X-Forwarded-For / X-Real-IP: those headers are
    client-controlled unless a trusted proxy rewrote them, and uvicorn's
    proxy-headers middleware has already applied the trusted ones to
    ``request.client``.
    """
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class InMemoryRateLimiter:
    """
    Sliding-window, per-IP rate limiter (in-process state).

    Thread-safe. Expired keys are swept every ``_SWEEP_EVERY`` calls, so the
    number of stored keys is bounded by the number of clients active within
    one window (plus at most ``_SWEEP_EVERY`` stale ones).
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int = 60,
        name: Optional[str] = None,
        clock: Optional[Callable[[], float]] = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name or f"limiter{id(self)}"
        self._clock = clock or time.time
        self._requests: dict[str, list[float]] = {}
        self._lock = Lock()
        self._calls = 0
        _ALL_LIMITERS.append(self)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check and record a request for key (typically client IP).

        Returns:
            (allowed, remaining): allowed=True if under limit,
            remaining=requests_left_in_window (0 when denied).
        """
        now = self._clock()
        cutoff = now - self.window_seconds

        with self._lock:
            self._calls += 1
            if self._calls % _SWEEP_EVERY == 0:
                self._sweep_locked(cutoff)

            recent = [ts for ts in self._requests.get(key, ()) if ts > cutoff]
            count = len(recent)
            if count >= self.max_requests:
                self._requests[key] = recent
                return False, 0

            recent.append(now)
            self._requests[key] = recent
            return True, self.max_requests - count - 1

    def reset(self) -> None:
        """Clear all counters — for testing only."""
        with self._lock:
            self._requests.clear()
            self._calls = 0

    def _sweep_locked(self, cutoff: float) -> None:
        stale = [k for k, tss in self._requests.items() if not tss or tss[-1] <= cutoff]
        for k in stale:
            del self._requests[k]

    def cleanup_stale(self) -> None:
        """Remove keys with no activity inside the current window."""
        cutoff = self._clock() - self.window_seconds
        with self._lock:
            self._sweep_locked(cutoff)


# Every limiter created in this process (module-level and per-router ones), so
# tests can reset them all with reset_all_limiters().
_ALL_LIMITERS: list[InMemoryRateLimiter] = []


def reset_all_limiters() -> None:
    """Reset every limiter in this process — for tests."""
    for lim in list(_ALL_LIMITERS):
        lim.reset()


# ---------------------------------------------------------------------------
# Shared (Redis) backend
# ---------------------------------------------------------------------------

class _RedisWindow:
    """Fixed-window counter in Redis shared by all workers.

    Any Redis error makes the caller fall back to the in-process limiter for
    ``_REDIS_RETRY_SECONDS``; the limit is never silently lifted.
    """

    def __init__(self) -> None:
        self._client = None
        self._down_until = 0.0

    def enabled(self) -> bool:
        return os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower() == "redis"

    def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis
            from app.core.config import settings

            url = os.getenv("RATE_LIMIT_REDIS_URL") or settings.redis_url
            self._client = aioredis.from_url(
                url, socket_timeout=0.5, socket_connect_timeout=0.5
            )
        return self._client

    async def is_allowed(self, limiter: InMemoryRateLimiter, ip: str) -> Optional[bool]:
        """True/False from Redis, or None when Redis is unavailable."""
        if time.monotonic() < self._down_until:
            return None
        try:
            from app.core.config import settings

            window = int(time.time() // limiter.window_seconds)
            key = f"{settings.redis_key_prefix}rl:{limiter.name}:{ip}:{window}"
            client = self._get_client()
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, limiter.window_seconds + 1)
            count, _ = await pipe.execute()
            return int(count) <= limiter.max_requests
        except Exception as exc:  # pragma: no cover - exercised via fallback test
            self._down_until = time.monotonic() + _REDIS_RETRY_SECONDS
            logger.warning(
                "Rate limiter: Redis unavailable (%s); using in-process limits for %.0fs",
                type(exc).__name__, _REDIS_RETRY_SECONDS,
            )
            return None


_shared = _RedisWindow()


async def enforce(limiter: InMemoryRateLimiter, request: Request, label: str) -> None:
    """Count one request against ``limiter`` and raise 429 when over the limit."""
    ip = _get_client_ip(request)
    allowed: Optional[bool] = None
    if _shared.enabled():
        allowed = await _shared.is_allowed(limiter, ip)
    if allowed is None:
        allowed, _ = limiter.is_allowed(ip)
    if not allowed:
        # No client IP in the log line (privacy policy).
        logger.warning("%s rate limit exceeded", label)
        raise _make_429_response(request)


# ---------------------------------------------------------------------------
# Module-level limiter instances
# These are singletons per process; tests can swap them via
# app.dependency_overrides or call .reset() between tests.
# ---------------------------------------------------------------------------

_rag_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60, name="rag")
_search_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60, name="search")
_vocab_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60, name="vocab")
_admin_decision_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60, name="admin_decision")
_feedback_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60, name="feedback")
_therapy_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60, name="therapy")
_stt_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60, name="stt")


def _make_429_response(request: Request) -> HTTPException:
    return HTTPException(
        status_code=429,
        headers={"Retry-After": str(_RETRY_AFTER_SECONDS)},
        detail={
            "error": "rate_limited",
            "message_en": (
                "Too many requests. Please wait before trying again. "
                f"Retry after {_RETRY_AFTER_SECONDS} seconds."
            ),
            "message_ar": (
                "تم تجاوز حد الطلبات المسموح به. "
                f"يرجى الانتظار {_RETRY_AFTER_SECONDS} ثانية ثم المحاولة مجدداً."
            ),
            "retry_after_seconds": _RETRY_AFTER_SECONDS,
        },
    )


# ---------------------------------------------------------------------------
# Named dependency functions — import and use with Depends()
# They can be overridden in tests via app.dependency_overrides.
# ---------------------------------------------------------------------------

async def rag_rate_limit(request: Request) -> None:
    """
    Dependency: limit RAG /ask and other LLM-backed endpoints to 20 requests/min per IP.

    Strict because each call may invoke an LLM (cost + latency).
    """
    await enforce(_rag_limiter, request, "RAG")


async def search_rate_limit(request: Request) -> None:
    """
    Dependency: limit search endpoints to 60 requests/min per IP.

    Moderate — search is read-only and used heavily by the UI typeahead.
    """
    await enforce(_search_limiter, request, "Search")


async def vocab_rate_limit(request: Request) -> None:
    """
    Dependency: limit vocabulary lookup to 60 requests/min per IP.

    Lenient — vocabulary lookups make no LLM call.
    """
    await enforce(_vocab_limiter, request, "Vocab")


async def feedback_rate_limit(request: Request) -> None:
    """
    Dependency: limit feedback submissions to 10 requests/min per IP.

    Prevents spam submissions while staying generous enough for legitimate use.
    """
    await enforce(_feedback_limiter, request, "Feedback")


async def therapy_rate_limit(request: Request) -> None:
    """
    Dependency: limit therapy/emotional-support endpoints to 20 requests/min per IP.

    Matches RAG limit — each call may involve DB queries and session writes.
    """
    await enforce(_therapy_limiter, request, "Therapy")


async def stt_rate_limit(request: Request) -> None:
    """
    Dependency: limit speech-to-text (Tasmee) calls to 10 requests/min per IP.

    Each call spends Hugging Face speech-recognition credit.
    """
    await enforce(_stt_limiter, request, "STT")


async def admin_decision_rate_limit(request: Request) -> None:
    """
    Dependency: limit admin review decisions to 10 requests/min per IP.

    Strict — write operation that persists to disk; prevents bulk automation.
    Auth check (require_admin_api_key) still runs first regardless.
    """
    await enforce(_admin_decision_limiter, request, "Admin decision")
