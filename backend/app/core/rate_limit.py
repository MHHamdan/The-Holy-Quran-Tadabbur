"""
In-memory sliding-window rate limiter for sensitive endpoints.

Design:
  - Per-client-IP, sliding 60-second window.
  - Thread-safe: uses threading.Lock (FastAPI's default sync code path).
  - Returns HTTP 429 with bilingual message on limit exceeded.
  - Exports named FastAPI dependency functions so callers can override
    them in tests via app.dependency_overrides.

Production deployment note:
  This implementation is correct for a SINGLE-PROCESS deployment.
  If you run multiple uvicorn workers (--workers N) or deploy behind
  multiple instances, rate-limit state is NOT shared between processes.
  For distributed rate limiting, use:
    - Redis + a library such as fastapi-limiter or slowapi
    - AWS API Gateway / Cloudflare / nginx limit_req module

Per-endpoint limits (conservative defaults; adjust via constructor):
  Endpoint              Limit      Rationale
  RAG /ask              20/min     LLM call is expensive; prevents cost abuse
  Admin /decision       10/min     Write operation; extra-strict
  Search                60/min     Read-only; generous enough for UI typeahead
  Vocabulary            60/min     Safe-refusal only; lenient
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from typing import Optional

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

_RETRY_AFTER_SECONDS = 60


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP.

    Respects X-Forwarded-For when behind a reverse proxy.
    Falls back to the direct connection IP.

    SECURITY NOTE: Only trust X-Forwarded-For if your deployment is
    guaranteed to run behind a trusted proxy (nginx, AWS ALB, Cloudflare).
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # Take the first (leftmost) IP — the original client
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class InMemoryRateLimiter:
    """
    Sliding-window, per-IP rate limiter.

    Thread-safe for single-process use.
    Not suitable for multi-process/distributed deployments without Redis.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check and record a request for key (typically client IP).

        Returns:
            (allowed, remaining): allowed=True if under limit,
            remaining=requests_left_in_window (0 when denied).
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Evict expired timestamps
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]

            count = len(self._requests[key])
            if count >= self.max_requests:
                return False, 0

            self._requests[key].append(now)
            return True, self.max_requests - count - 1

    def reset(self) -> None:
        """Clear all counters — for testing only."""
        with self._lock:
            self._requests.clear()

    def cleanup_stale(self) -> None:
        """Remove IPs with no recent activity (housekeeping)."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            stale = [
                ip for ip, tss in self._requests.items()
                if not tss or all(ts <= cutoff for ts in tss)
            ]
            for ip in stale:
                del self._requests[ip]


# ---------------------------------------------------------------------------
# Module-level limiter instances
# These are singletons per process; tests can swap them via
# app.dependency_overrides or call .reset() between tests.
# ---------------------------------------------------------------------------

_rag_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)
_search_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60)
_vocab_limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60)
_admin_decision_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
_feedback_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
_therapy_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)


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
    Dependency: limit RAG /ask endpoints to 20 requests/min per IP.

    Strict because each call may invoke an LLM (cost + latency).
    """
    ip = _get_client_ip(request)
    allowed, remaining = _rag_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("RAG rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


async def search_rate_limit(request: Request) -> None:
    """
    Dependency: limit search endpoints to 60 requests/min per IP.

    Moderate — search is read-only and used heavily by the UI typeahead.
    """
    ip = _get_client_ip(request)
    allowed, remaining = _search_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Search rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


async def vocab_rate_limit(request: Request) -> None:
    """
    Dependency: limit vocabulary lookup to 60 requests/min per IP.

    Lenient — vocabulary currently returns a safe-refusal (no LLM call).
    """
    ip = _get_client_ip(request)
    allowed, remaining = _vocab_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Vocab rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


async def feedback_rate_limit(request: Request) -> None:
    """
    Dependency: limit feedback submissions to 10 requests/min per IP.

    Prevents spam submissions while staying generous enough for legitimate use.
    """
    ip = _get_client_ip(request)
    allowed, remaining = _feedback_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Feedback rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


async def therapy_rate_limit(request: Request) -> None:
    """
    Dependency: limit therapy/emotional-support endpoints to 20 requests/min per IP.

    Matches RAG limit — each call may involve DB queries and session writes.
    """
    ip = _get_client_ip(request)
    allowed, remaining = _therapy_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Therapy rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


async def admin_decision_rate_limit(request: Request) -> None:
    """
    Dependency: limit admin review decisions to 10 requests/min per IP.

    Strict — write operation that persists to disk; prevents bulk automation.
    Auth check (require_admin_api_key) still runs first regardless.
    """
    ip = _get_client_ip(request)
    allowed, remaining = _admin_decision_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Admin decision rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)
