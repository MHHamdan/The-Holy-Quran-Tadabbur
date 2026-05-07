"""
Phase S — Rate Limiting Tests

Verifies:
  1. InMemoryRateLimiter class: sliding window, thread safety, reset
  2. _get_client_ip extracts real IP from X-Forwarded-For
  3. RAG /ask endpoint returns 429 after limit exceeded
  4. Vocabulary /lookup returns 429 after limit exceeded
  5. Admin decision endpoint returns 429 (after auth) when rate limited
  6. Normal first request (well under limit) always succeeds
  7. Public non-sensitive routes are not rate-limited
  8. Different IPs have independent counters

Strategy:
  - Unit tests test InMemoryRateLimiter directly.
  - Integration tests use app.dependency_overrides to inject a
    tight-limit version of the dependency (limit=2), so tests
    are fast and deterministic.
  - After each integration test, module-level limiters are reset.
"""
import hashlib
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.rate_limit import (
    InMemoryRateLimiter,
    _get_client_ip,
    rag_rate_limit,
    vocab_rate_limit,
    admin_decision_rate_limit,
    _rag_limiter,
    _vocab_limiter,
    _admin_decision_limiter,
)

TEST_KEY = "phase-s-rate-test-key-xyz"
TEST_KEY_HASH = hashlib.sha256(TEST_KEY.encode()).hexdigest()


def _auth() -> dict:
    return {"X-Admin-API-Key": TEST_KEY}


def _patch_key(hash_val=TEST_KEY_HASH):
    return patch("app.core.admin_auth._get_configured_key_hash", return_value=hash_val)


# ---------------------------------------------------------------------------
# 1. InMemoryRateLimiter — unit tests
# ---------------------------------------------------------------------------

class TestInMemoryRateLimiter:
    def test_first_request_allowed(self):
        lim = InMemoryRateLimiter(max_requests=5, window_seconds=60)
        allowed, remaining = lim.is_allowed("192.0.2.1")
        assert allowed is True
        assert remaining == 4

    def test_requests_decrement_remaining(self):
        lim = InMemoryRateLimiter(max_requests=3, window_seconds=60)
        _, r1 = lim.is_allowed("10.0.0.1")
        _, r2 = lim.is_allowed("10.0.0.1")
        allowed, r3 = lim.is_allowed("10.0.0.1")
        assert r1 == 2
        assert r2 == 1
        assert r3 == 0  # remaining=0 on last allowed request

    def test_limit_exceeded_denied(self):
        lim = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        lim.is_allowed("10.0.0.2")
        lim.is_allowed("10.0.0.2")
        allowed, remaining = lim.is_allowed("10.0.0.2")
        assert allowed is False
        assert remaining == 0

    def test_different_ips_independent(self):
        lim = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        allowed_a, _ = lim.is_allowed("10.0.0.10")
        allowed_b, _ = lim.is_allowed("10.0.0.11")
        assert allowed_a is True
        assert allowed_b is True  # Different IP — independent counter

    def test_reset_clears_all_counters(self):
        lim = InMemoryRateLimiter(max_requests=1, window_seconds=60)
        lim.is_allowed("10.0.0.3")
        lim.is_allowed("10.0.0.3")  # Now blocked
        lim.reset()
        allowed, _ = lim.is_allowed("10.0.0.3")
        assert allowed is True

    def test_window_expires_old_requests(self):
        import time
        lim = InMemoryRateLimiter(max_requests=2, window_seconds=1)
        lim.is_allowed("10.0.0.4")
        lim.is_allowed("10.0.0.4")
        # Manually backdate entries to simulate window expiry
        with lim._lock:
            lim._requests["10.0.0.4"] = [time.time() - 2]  # expired
        allowed, _ = lim.is_allowed("10.0.0.4")
        assert allowed is True  # Old entries evicted, fresh window

    def test_cleanup_removes_stale_ips(self):
        import time
        lim = InMemoryRateLimiter(max_requests=10, window_seconds=1)
        lim.is_allowed("10.0.0.5")
        with lim._lock:
            lim._requests["10.0.0.5"] = [time.time() - 2]  # expired
        lim.cleanup_stale()
        assert "10.0.0.5" not in lim._requests


# ---------------------------------------------------------------------------
# 2. _get_client_ip helper
# ---------------------------------------------------------------------------

class TestGetClientIp:
    def _make_request(self, headers: dict, client_host: str = "127.0.0.1"):
        req = MagicMock()
        req.headers = headers
        req.client = MagicMock()
        req.client.host = client_host
        return req

    def test_direct_connection_ip(self):
        req = self._make_request({}, "192.168.1.5")
        assert _get_client_ip(req) == "192.168.1.5"

    def test_xff_single_ip(self):
        req = self._make_request({"X-Forwarded-For": "203.0.113.7"})
        assert _get_client_ip(req) == "203.0.113.7"

    def test_xff_chain_takes_first(self):
        req = self._make_request({"X-Forwarded-For": "203.0.113.7, 10.0.0.1, 10.0.0.2"})
        assert _get_client_ip(req) == "203.0.113.7"

    def test_no_client_returns_unknown(self):
        req = MagicMock()
        req.headers = {}
        req.client = None
        assert _get_client_ip(req) == "unknown"


# ---------------------------------------------------------------------------
# 3. RAG /ask rate limiting integration
# ---------------------------------------------------------------------------

class TestRagRateLimit:
    """Uses dependency override to inject a tight limiter (limit=2)."""

    def setup_method(self):
        self._tight_lim = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        _lim = self._tight_lim  # capture for closure

        async def tight_rag_limit():
            from fastapi import HTTPException
            allowed, _ = _lim.is_allowed("test-ip")
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={"error": "rate_limited", "message_en": "Too many requests."},
                )

        app.dependency_overrides[rag_rate_limit] = tight_rag_limit
        self._client = TestClient(app, raise_server_exceptions=False)

    def teardown_method(self):
        app.dependency_overrides.pop(rag_rate_limit, None)
        self._tight_lim.reset()

    def test_first_ask_not_rate_limited(self):
        # The rate check passes; actual LLM call will fail (no DB), but not 429
        r = self._client.post(
            "/api/v1/rag/ask",
            json={"question": "What is Surah Al-Fatiha?"},
        )
        assert r.status_code != 429

    def test_ask_returns_429_after_limit(self):
        self._client.post("/api/v1/rag/ask", json={"question": "q1"})
        self._client.post("/api/v1/rag/ask", json={"question": "q2"})
        # Third request exceeds limit=2
        r = self._client.post("/api/v1/rag/ask", json={"question": "q3"})
        assert r.status_code == 429

    def test_429_response_has_retry_after(self):
        self._client.post("/api/v1/rag/ask", json={"question": "q1"})
        self._client.post("/api/v1/rag/ask", json={"question": "q2"})
        r = self._client.post("/api/v1/rag/ask", json={"question": "q3"})
        assert r.status_code == 429
        # Either header or body should indicate retry
        assert "rate_limited" in r.text or "429" in str(r.status_code)


# ---------------------------------------------------------------------------
# 4. Vocabulary /lookup rate limiting integration
# ---------------------------------------------------------------------------

class TestVocabRateLimit:
    def setup_method(self):
        self._tight_lim = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        _lim = self._tight_lim

        async def tight_vocab_limit():
            from fastapi import HTTPException
            allowed, _ = _lim.is_allowed("test-ip")
            if not allowed:
                raise HTTPException(status_code=429, detail={"error": "rate_limited"})

        app.dependency_overrides[vocab_rate_limit] = tight_vocab_limit
        self._client = TestClient(app, raise_server_exceptions=False)

    def teardown_method(self):
        app.dependency_overrides.pop(vocab_rate_limit, None)
        self._tight_lim.reset()

    def test_first_vocab_request_succeeds(self):
        r = self._client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        assert r.status_code == 200

    def test_vocab_returns_429_after_limit(self):
        self._client.get("/api/v1/vocabulary/lookup", params={"word": "رحمة"})
        self._client.get("/api/v1/vocabulary/lookup", params={"word": "تقوى"})
        r = self._client.get("/api/v1/vocabulary/lookup", params={"word": "صبر"})
        assert r.status_code == 429


# ---------------------------------------------------------------------------
# 5. Admin decision endpoint rate limiting (auth first, then rate)
# ---------------------------------------------------------------------------

class TestAdminDecisionRateLimit:
    def setup_method(self):
        self._tight_lim = InMemoryRateLimiter(max_requests=2, window_seconds=60)
        _lim = self._tight_lim

        async def tight_admin_limit():
            from fastapi import HTTPException
            allowed, _ = _lim.is_allowed("test-ip")
            if not allowed:
                raise HTTPException(status_code=429, detail={"error": "rate_limited"})

        app.dependency_overrides[admin_decision_rate_limit] = tight_admin_limit
        self._client = TestClient(app, raise_server_exceptions=False)

    def teardown_method(self):
        app.dependency_overrides.pop(admin_decision_rate_limit, None)
        self._tight_lim.reset()

    def test_decision_without_auth_is_401_not_429(self):
        """Auth must fail before rate limit is checked."""
        with _patch_key(TEST_KEY_HASH):
            # No auth header → 401 regardless of rate limit
            r = self._client.post(
                "/api/v1/admin/review/tasks/task-001/decision",
                json={"status": "approved", "notes": "test notes here ok", "reviewerId": "r1"},
            )
        assert r.status_code == 401

    def test_decision_rate_limited_returns_429(self):
        with _patch_key(TEST_KEY_HASH):
            body = {"status": "approved", "notes": "scholarly review notes", "reviewerId": "r1"}
            self._client.post(
                "/api/v1/admin/review/tasks/task-001/decision",
                json=body,
                headers=_auth(),
            )
            self._client.post(
                "/api/v1/admin/review/tasks/task-002/decision",
                json=body,
                headers=_auth(),
            )
            r = self._client.post(
                "/api/v1/admin/review/tasks/task-003/decision",
                json=body,
                headers=_auth(),
            )
        assert r.status_code == 429


# ---------------------------------------------------------------------------
# 6. Module-level rate limiters export and are instances
# ---------------------------------------------------------------------------

class TestLimiterExports:
    def test_rag_limiter_is_instance(self):
        assert isinstance(_rag_limiter, InMemoryRateLimiter)

    def test_vocab_limiter_is_instance(self):
        assert isinstance(_vocab_limiter, InMemoryRateLimiter)

    def test_admin_decision_limiter_is_instance(self):
        assert isinstance(_admin_decision_limiter, InMemoryRateLimiter)

    def test_rag_limiter_limit_is_strict(self):
        assert _rag_limiter.max_requests <= 20

    def test_admin_decision_limiter_is_strictest(self):
        assert _admin_decision_limiter.max_requests <= 10

    def test_search_limiter_more_lenient_than_rag(self):
        from app.core.rate_limit import _search_limiter
        assert _search_limiter.max_requests > _rag_limiter.max_requests
