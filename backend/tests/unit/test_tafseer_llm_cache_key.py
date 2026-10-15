"""
/tafseer/llm/* take identifiers only and key the shared cache on every input.

Before: the client sent verse_text/tafsir_text (unbounded, unchecked) and the
cache key was md5 of truncated text without language or source, so one
anonymous request could poison the answer other readers got, and ar/en or
different sources collided. Now the server loads the verse and the tafsir
passage itself, refuses when no enabled licensed passage exists, and the key is
sha256 over all fields plus the model id.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.routes import tafseer
from app.core.rate_limit import _rag_limiter
from app.main import app

VERSE = "verse-text-from-db"
TAFSIR = "tafsir-text-from-db"


class _DictCache:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, **_):
        self.store[key] = value


@pytest.fixture
def cache(monkeypatch):
    c = _DictCache()
    monkeypatch.setattr(tafseer, "get_hybrid_cache", lambda: c)
    return c


@pytest.fixture
def grounding(monkeypatch):
    calls = []

    async def fake(session, sura, aya, source_id):
        calls.append((sura, aya, source_id))
        if source_id == "tabari_ar" and (sura, aya) == (1, 1):
            return None  # no enabled passage for this source/verse
        return f"{VERSE} {sura}:{aya}", f"{TAFSIR} {source_id}"

    monkeypatch.setattr(tafseer, "_load_grounding", fake)
    return calls


@pytest.fixture
def llm(monkeypatch):
    calls = []

    async def summarize(tafsir_text, verse_text, language):
        calls.append(("summary", verse_text, tafsir_text, language))
        return f"summary in {language}"

    async def explain(word, verse_text, context, language):
        calls.append(("explain", word, verse_text, context, language))
        return "explanation"

    async def answer(question, verse_text, tafsir_text, language):
        calls.append(("answer", question, verse_text, tafsir_text, language))
        return "answer"

    svc = tafseer.tafsir_llm_service
    monkeypatch.setattr(svc, "summarize_tafsir", summarize)
    monkeypatch.setattr(svc, "explain_word", explain)
    monkeypatch.setattr(svc, "answer_question", answer)
    return calls


@pytest_asyncio.fixture
async def client():
    _rag_limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    _rag_limiter.reset()


BASE = {"sura": 112, "aya": 1, "source_id": "muyassar_ar", "language": "ar"}


class TestCacheKey:
    def test_every_field_changes_the_key(self):
        k = tafseer._llm_cache_key
        base = dict(sura=2, aya=255, source_id="muyassar_ar", language="ar", tafsir_sha="x")
        ref = k("summary", **base)
        assert ref.startswith("llm:summary:v2:")
        for field, other in [("sura", 3), ("aya", 256), ("source_id", "tabari_ar"),
                             ("language", "en"), ("tafsir_sha", "y")]:
            assert k("summary", **{**base, field: other}) != ref, field
        assert k("explain", **base) != ref

    def test_long_questions_are_not_truncated(self):
        k = tafseer._llm_cache_key
        q1 = "a" * 60 + "1"
        q2 = "a" * 60 + "2"
        assert k("answer", question=q1) != k("answer", question=q2)

    def test_model_id_is_part_of_the_key(self, monkeypatch):
        k1 = tafseer._llm_cache_key("summary", sura=1)
        monkeypatch.setattr(tafseer.settings, "hf_llm_model", "other/model")
        assert tafseer._llm_cache_key("summary", sura=1) != k1


@pytest.mark.asyncio
class TestRequests:
    @pytest.mark.parametrize("path,extra", [
        ("summarize", {"verse_text": "anything"}),
        ("summarize", {"tafsir_text": "anything"}),
        ("explain-word", {"word": "الصمد", "verse_text": "test"}),
        ("explain-word", {"word": "الصمد", "context": "x"}),
        ("answer", {"question": "q", "tafsir_text": "x"}),
    ])
    async def test_client_supplied_text_is_rejected(self, client, cache, grounding, llm, path, extra):
        r = await client.post(f"/api/v1/tafseer/llm/{path}", json={**BASE, **extra})
        assert r.status_code == 422
        assert not llm

    @pytest.mark.parametrize("bad", [
        {"source_id": "random_blog"}, {"language": "fr"}, {"sura": 115}, {"aya": 0},
    ])
    async def test_invalid_identifiers_rejected(self, client, cache, grounding, llm, bad):
        r = await client.post("/api/v1/tafseer/llm/summarize", json={**BASE, **bad})
        assert r.status_code == 422

    async def test_word_and_question_are_bounded(self, client, cache, grounding, llm):
        r = await client.post("/api/v1/tafseer/llm/explain-word", json={**BASE, "word": "x" * 65})
        assert r.status_code == 422
        r = await client.post("/api/v1/tafseer/llm/answer", json={**BASE, "question": "x" * 501})
        assert r.status_code == 422

    async def test_server_loads_text_and_language_source_miss_separately(
        self, client, cache, grounding, llm
    ):
        for body in (BASE, BASE, {**BASE, "language": "en"}, {**BASE, "source_id": "ibn_kathir_ar"}):
            r = await client.post("/api/v1/tafseer/llm/summarize", json=body)
            assert r.status_code == 200 and r.json()["ok"] is True
        # Second identical call hit the cache; language and source each missed.
        assert len(llm) == 3
        assert llm[0][1] == f"{VERSE} 112:1" and llm[0][2] == f"{TAFSIR} muyassar_ar"
        assert {c[3] for c in llm} == {"ar", "en"}

    async def test_word_explanation_uses_server_text(self, client, cache, grounding, llm):
        r = await client.post("/api/v1/tafseer/llm/explain-word",
                              json={**BASE, "aya": 2, "word": " الصمد "})
        assert r.json()["ok"] is True
        kind, word, verse, context, _ = llm[0]
        assert (kind, word, verse, context) == ("explain", "الصمد", f"{VERSE} 112:2", f"{TAFSIR} muyassar_ar")

    async def test_refuses_without_enabled_passage(self, client, cache, grounding, llm):
        r = await client.post("/api/v1/tafseer/llm/answer",
                              json={"sura": 1, "aya": 1, "source_id": "tabari_ar",
                                    "language": "en", "question": "What does it mean?"})
        body = r.json()
        assert body["ok"] is False and body["error_code"] == "NO_VERIFIED_SOURCE"
        assert body["error"] and not llm and not cache.store

    async def test_rate_limited(self, client, cache, grounding, llm):
        codes = [
            (await client.post("/api/v1/tafseer/llm/summarize", json=BASE)).status_code
            for _ in range(21)
        ]
        assert codes[:20] == [200] * 20 and codes[20] == 429


@pytest.mark.asyncio
async def test_errors_do_not_echo_exceptions(monkeypatch, grounding):
    async def boom(**_):
        raise RuntimeError("internal detail hf_secret_value")

    monkeypatch.setattr(tafseer.tafsir_llm_service, "explain_word", boom)
    monkeypatch.setattr(tafseer, "get_hybrid_cache", lambda: SimpleNamespace(
        get=AsyncMock(return_value=None), set=AsyncMock()))
    req = tafseer.LLMExplainWordRequest(**BASE, word="الصمد")
    r = await tafseer.explain_word(req, session=None)
    assert r.ok is False and "internal detail" not in (r.error or "")


@pytest.mark.asyncio
async def test_load_grounding_reads_canonical_tables():
    """Real DB: verse text comes from quran_verses, context from tafseer_chunks."""
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            got = await tafseer._load_grounding(session, 112, 1, "muyassar_ar")
        except Exception as e:  # pragma: no cover - no DB in this environment
            pytest.skip(f"database unavailable: {type(e).__name__}")
        if got is None:
            pytest.skip("muyassar_ar not seeded")
        verse, tafsir_text = got
        assert verse and tafsir_text
        assert await tafseer._load_grounding(session, 112, 1, "no_such_source") is None
