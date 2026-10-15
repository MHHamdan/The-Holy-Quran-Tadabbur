"""/rag route hardening: admin-only cache endpoints, no exception text in
follow-up/expand errors, the broken agentic endpoint is gone."""
import json
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import rag as rag_routes
from app.db.database import get_async_session
from app.main import app
from app.services.conversation_service import get_conversation_service


class MemoryCache:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        v = self.store.get(key)
        return json.loads(v) if v is not None else None

    async def set(self, key, value, ttl=None):
        self.store[key] = json.dumps(value)
        return True

    async def delete(self, key):
        self.store.pop(key, None)
        return True


@pytest.fixture
async def client(monkeypatch):
    monkeypatch.setattr(get_conversation_service(), "_cache", MemoryCache())

    async def _no_db():
        yield SimpleNamespace()

    app.dependency_overrides[get_async_session] = _no_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_async_session, None)


async def test_cache_clear_requires_admin_key(client):
    r = await client.delete("/api/v1/rag/cache/clear")
    assert r.status_code in (401, 403, 503)


async def test_cache_stats_requires_admin_key(client):
    r = await client.get("/api/v1/rag/cache/stats")
    assert r.status_code in (401, 403, 503)


async def test_agentic_endpoint_is_removed(client):
    r = await client.post("/api/v1/rag/ask/agentic", json={"question": "What is patience?"})
    assert r.status_code in (404, 405)


@pytest.mark.parametrize("path,body", [
    ("/api/v1/rag/ask/followup", {"question": "And what about the next verse?"}),
    ("/api/v1/rag/ask/expand", {"topic": "patience in hardship"}),
])
async def test_followup_and_expand_errors_hide_exception_text(client, monkeypatch, path, body):
    session = await get_conversation_service().create_session("en", [])

    class Exploding:
        def __init__(self, *_a, **_k):
            pass

        async def query(self, **_k):
            raise ValueError("secret detail /internal/path")

    monkeypatch.setattr(rag_routes, "RAGPipeline", Exploding)
    r = await client.post(path, json={**body, "session_id": session.session_id, "language": "en"})
    assert r.status_code == 500
    assert "secret detail" not in r.text and "/internal/path" not in r.text
    payload = r.json()
    assert payload["error_id"] and payload["message_ar"] and payload["message_en"]
