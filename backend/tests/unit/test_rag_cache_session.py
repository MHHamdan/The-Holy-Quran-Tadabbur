"""
/rag/ask response cache must never leak one user's session to another.

The pipeline, the response cache and the conversation store are replaced by
in-memory fakes, so this runs offline (no DB, Redis or Hugging Face).
"""
import json
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import rag as rag_routes
from app.db.database import get_async_session
from app.main import app
from app.rag.types import Citation, GroundedResponse
from app.services.conversation_service import get_conversation_service


class MemoryCache:
    """Minimal async stand-in for RedisCache (get/set/delete)."""

    def __init__(self):
        self.store = {}
        self.sets = 0

    async def get(self, key):
        value = self.store.get(key)
        return json.loads(value) if value is not None else None

    async def set(self, key, value, ttl=None):
        self.sets += 1
        self.store[key] = json.dumps(value)
        return True

    async def delete(self, key):
        self.store.pop(key, None)
        return True


class FakePipeline:
    calls = []

    def __init__(self, session, llm=None):
        self.llm_provider = "fake"

    async def query(self, **kwargs):
        FakePipeline.calls.append(kwargs)
        return GroundedResponse(
            answer="Allah alone is worshipped [Al-Muyassar, 2:255].",
            citations=[Citation(
                chunk_id="muyassar_ar:2:255", source_id="muyassar_ar", source_name="Al-Muyassar",
                source_name_ar="التفسير الميسر", verse_reference="2:255", excerpt="x",
                relevance_score=0.9,
            )],
            confidence=0.9,
            answer_kind="ai_synthesis",
            session_id=kwargs.get("session_id"),
        )


@pytest.fixture
async def client(monkeypatch):
    response_cache = MemoryCache()
    conv = get_conversation_service()
    monkeypatch.setattr(conv, "_cache", MemoryCache())
    monkeypatch.setattr(rag_routes, "get_rag_cache", lambda: response_cache)
    monkeypatch.setattr(rag_routes, "RAGPipeline", FakePipeline)
    FakePipeline.calls = []

    async def _no_db():
        yield SimpleNamespace()

    app.dependency_overrides[get_async_session] = _no_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            c.response_cache = response_cache
            yield c
    finally:
        app.dependency_overrides.pop(get_async_session, None)


QUESTION = {"question": "What is the meaning of Ayat al-Kursi?", "language": "en"}


async def test_cache_hit_gets_its_own_session(client):
    first = (await client.post("/api/v1/rag/ask", json=QUESTION)).json()
    second = (await client.post("/api/v1/rag/ask", json=QUESTION)).json()

    assert first["cached"] is False and second["cached"] is True
    assert len(FakePipeline.calls) == 1
    assert first["session_id"] and second["session_id"]
    assert first["session_id"] != second["session_id"]
    assert first["request_id"] != second["request_id"]

    s1 = (await client.get(f"/api/v1/rag/sessions/{first['session_id']}")).json()["session"]
    s2 = (await client.get(f"/api/v1/rag/sessions/{second['session_id']}")).json()["session"]
    assert s1["message_count"] == 2 and s2["message_count"] == 2


async def test_cached_copy_has_no_per_request_ids(client):
    await client.post("/api/v1/rag/ask", json=QUESTION)
    (stored,) = [json.loads(v) for v in client.response_cache.store.values()]
    assert "session_id" not in stored and "request_id" not in stored and "error_id" not in stored


async def test_follow_up_with_context_is_neither_served_from_nor_stored_in_cache(client):
    first = (await client.post("/api/v1/rag/ask", json=QUESTION)).json()
    sets_before = client.response_cache.sets
    again = (await client.post(
        "/api/v1/rag/ask", json={**QUESTION, "session_id": first["session_id"]},
    )).json()
    assert again["cached"] is False
    assert again["session_id"] == first["session_id"]
    assert FakePipeline.calls[-1]["conversation_context"]
    assert client.response_cache.sets == sets_before
