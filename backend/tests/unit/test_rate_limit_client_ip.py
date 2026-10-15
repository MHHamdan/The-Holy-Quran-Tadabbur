"""
Rate-limit keying and memory bounds (WS1, findings devops-xff-ratelimit-bypass,
security-ratelimit-xff-spoof, backend-ratelimit-xff-spoof).

  - A client-supplied X-Forwarded-For must not change the rate-limit bucket.
  - Expired keys are swept, so rotating client IPs cannot grow memory forever.
  - RATE_LIMIT_BACKEND=redis shares one count across workers and falls back to
    the in-process limiter when Redis fails (the limit is never lifted).
  - Log lines for exceeded limits never contain the client IP.
"""
import logging

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.rate_limit import (
    InMemoryRateLimiter,
    _SWEEP_EVERY,
    _stt_limiter,
    _vocab_limiter,
    stt_rate_limit,
    vocab_rate_limit,
)


def _app(dep) -> FastAPI:
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(dep)])
    async def limited():
        return {"ok": True}

    return app


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_BACKEND", raising=False)
    _vocab_limiter.reset()
    _stt_limiter.reset()
    yield
    _vocab_limiter.reset()
    _stt_limiter.reset()


def test_rotating_x_forwarded_for_does_not_bypass_the_limit():
    client = TestClient(_app(vocab_rate_limit))
    codes = [
        client.get("/limited", headers={"X-Forwarded-For": f"198.51.100.{i}"}).status_code
        for i in range(70)
    ]
    assert codes[:60] == [200] * 60
    assert codes[60:] == [429] * 10


def test_spoofed_x_forwarded_for_shares_the_peer_bucket():
    client = TestClient(_app(vocab_rate_limit))
    client.get("/limited", headers={"X-Forwarded-For": "203.0.113.9"})
    client.get("/limited")
    # Only the ASGI peer ("testclient") is ever used as a key.
    assert set(_vocab_limiter._requests) == {"testclient"}
    assert len(_vocab_limiter._requests["testclient"]) == 2


def test_429_is_bilingual_and_has_retry_after():
    client = TestClient(_app(stt_rate_limit))
    for _ in range(_stt_limiter.max_requests):
        assert client.get("/limited").status_code == 200
    r = client.get("/limited")
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"
    detail = r.json()["detail"]
    assert detail["message_ar"] and detail["message_en"]


def test_stt_limit_is_ten_per_minute():
    assert _stt_limiter.max_requests == 10
    assert _stt_limiter.window_seconds == 60


def test_expired_keys_are_swept_after_10k_distinct_clients():
    now = [1_000_000.0]
    lim = InMemoryRateLimiter(max_requests=5, window_seconds=60, clock=lambda: now[0])
    for i in range(10_000):
        lim.is_allowed(f"10.{i // 65536}.{(i // 256) % 256}.{i % 256}")
    assert len(lim._requests) <= 10_000

    now[0] += 61  # every key is now outside the window
    for _ in range(_SWEEP_EVERY):
        lim.is_allowed("192.0.2.1")
    # Only the active key survives the periodic sweep.
    assert set(lim._requests) == {"192.0.2.1"}

    now[0] += 61
    lim.cleanup_stale()
    assert len(lim._requests) == 0


def test_denied_requests_do_not_extend_the_window():
    now = [0.0]
    lim = InMemoryRateLimiter(max_requests=2, window_seconds=60, clock=lambda: now[0])
    assert lim.is_allowed("a")[0] and lim.is_allowed("a")[0]
    assert lim.is_allowed("a") == (False, 0)
    now[0] = 61
    assert lim.is_allowed("a")[0] is True


def test_exceeded_limit_log_has_no_client_ip(caplog):
    client = TestClient(_app(stt_rate_limit))
    with caplog.at_level(logging.WARNING, logger="app.core.rate_limit"):
        for _ in range(_stt_limiter.max_requests + 1):
            client.get("/limited")
    text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "STT rate limit exceeded" in text
    assert "testclient" not in text and "IP" not in text


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

class _FakePipeline:
    def __init__(self, store):
        self.store = store
        self.ops = []

    def incr(self, key):
        self.ops.append(("incr", key))

    def expire(self, key, ttl):
        self.ops.append(("expire", key, ttl))

    async def execute(self):
        out = []
        for op in self.ops:
            if op[0] == "incr":
                self.store[op[1]] = self.store.get(op[1], 0) + 1
                out.append(self.store[op[1]])
            else:
                out.append(True)
        return out


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def pipeline(self):
        return _FakePipeline(self.store)


class _BrokenRedis:
    def pipeline(self):
        raise ConnectionError("redis down")


def test_redis_backend_shares_count_across_workers(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
    fake = _FakeRedis()
    monkeypatch.setattr(rate_limit._shared, "_client", fake)
    monkeypatch.setattr(rate_limit._shared, "_down_until", 0.0)

    client = TestClient(_app(stt_rate_limit))
    codes = [client.get("/limited").status_code for _ in range(12)]
    assert codes == [200] * 10 + [429] * 2
    # The count lived in Redis, not in the per-process limiter.
    assert _stt_limiter._requests == {}
    (key,) = fake.store
    assert ":rl:stt:testclient:" in key


def test_redis_failure_falls_back_to_in_process_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setattr(rate_limit._shared, "_client", _BrokenRedis())
    monkeypatch.setattr(rate_limit._shared, "_down_until", 0.0)

    client = TestClient(_app(stt_rate_limit))
    codes = [client.get("/limited").status_code for _ in range(11)]
    assert codes == [200] * 10 + [429]
    monkeypatch.setattr(rate_limit._shared, "_down_until", 0.0)


def test_reset_all_limiters_covers_router_limiters():
    from app.api.routes import adhkar

    adhkar._dhikr_limiter.is_allowed("x")
    rate_limit.reset_all_limiters()
    assert adhkar._dhikr_limiter._requests == {}
