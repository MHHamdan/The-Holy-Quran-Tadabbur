"""
Health/readiness probes (WS1: backend-ready-and-qdrant-health,
hf-health-qdrant-readiness-path).
"""
import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import health
from app.db.database import get_async_session
from app.main import app


class _Session:
    def __init__(self, behaviour):
        self.behaviour = behaviour

    async def execute(self, *_a, **_k):
        if self.behaviour == "raise":
            raise ConnectionError("db down")
        if self.behaviour == "hang":
            await asyncio.sleep(10)
        return None


def _override(behaviour):
    async def _dep():
        yield _Session(behaviour)

    return _dep


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.pop(get_async_session, None)


def test_ready_is_200_when_db_answers(client):
    app.dependency_overrides[get_async_session] = _override("ok")
    r = client.get("/ready")
    assert r.status_code == 200 and r.json() == {"status": "ready"}


def test_ready_is_503_when_db_raises(client):
    app.dependency_overrides[get_async_session] = _override("raise")
    r = client.get("/ready")
    assert r.status_code == 503 and r.json() == {"status": "not_ready"}


def test_ready_is_503_when_db_hangs(client, monkeypatch):
    monkeypatch.setattr(health, "READY_DB_TIMEOUT_SECONDS", 0.05)
    app.dependency_overrides[get_async_session] = _override("hang")
    r = client.get("/ready")
    assert r.status_code == 503


def _mock_client(routes):
    def handler(request):
        return httpx.Response(routes.get(request.url.path, 404))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("routes,expected", [
    ({"/readyz": 200}, (True, 200)),
    ({"/healthz": 200}, (True, 200)),          # older Qdrant without /readyz
    ({"/readyz": 503}, (False, 503)),
    ({}, (False, 404)),
])
def test_qdrant_probe_uses_readyz_then_healthz(routes, expected):
    async def run():
        async with _mock_client(routes) as c:
            return await health._qdrant_ready(c)

    assert asyncio.run(run()) == expected


def test_qdrant_probe_never_uses_readiness_path():
    import inspect

    assert '"/readiness"' not in inspect.getsource(health) and "/readiness\"" not in inspect.getsource(health)
