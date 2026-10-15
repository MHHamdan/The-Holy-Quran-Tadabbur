"""
Dhikr session API (WS1: duas-api-dhikr-api-untested).

The write path uses a fake session so the shared database's community
counters are never touched; /stats is read-only.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.routes import adhkar
from app.db.database import get_async_session
from app.main import app


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, obj):
        obj.id = 4242


@pytest.fixture
def fake_db():
    fake = _FakeSession()

    async def _dep():
        yield fake

    app.dependency_overrides[get_async_session] = _dep
    adhkar._dhikr_limiter.reset()
    yield fake
    app.dependency_overrides.pop(get_async_session, None)
    adhkar._dhikr_limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)


def _body(**kw):
    body = {"session_date": "2026-10-14", "category": "morning",
            "total_dhikr_completed": 3, "total_count": 133, "duration_seconds": 600}
    body.update(kw)
    return body


def test_record_session(client, fake_db):
    r = client.post("/api/v1/dhikr/sessions", json=_body())
    assert r.status_code == 201
    assert r.json() == {"id": 4242, "session_date": "2026-10-14", "category": "morning",
                        "total_dhikr_completed": 3, "total_count": 133, "duration_seconds": 600}
    assert len(fake_db.added) == 1


@pytest.mark.parametrize("override", [
    {"total_count": 10_001},          # realistic per-session bound
    {"total_count": -1},
    {"session_date": "14/10/2026"},
    {"total_dhikr_completed": 501},
    {"duration_seconds": 86_401},
    {"category": "x" * 51},
])
def test_invalid_sessions_are_rejected(client, fake_db, override):
    assert client.post("/api/v1/dhikr/sessions", json=_body(**override)).status_code == 422
    assert fake_db.added == []


def test_total_count_upper_bound_is_accepted(client, fake_db):
    assert client.post("/api/v1/dhikr/sessions", json=_body(total_count=10_000)).status_code == 201


def test_session_writes_are_rate_limited(client, fake_db):
    codes = [client.post("/api/v1/dhikr/sessions", json=_body()).status_code for _ in range(21)]
    assert codes[:20] == [201] * 20
    assert codes[20] == 429
    assert len(fake_db.added) == 20


def test_stats_shape(client):
    r = client.get("/api/v1/dhikr/stats")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"sessions_today", "counts_today", "sessions_alltime", "date"}
    assert all(isinstance(body[k], int) and body[k] >= 0
               for k in ("sessions_today", "counts_today", "sessions_alltime"))
