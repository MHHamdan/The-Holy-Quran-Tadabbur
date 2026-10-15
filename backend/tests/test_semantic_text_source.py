"""
Semantic search and similar-verse results must carry the canonical verse text
from quran_verses, never the copy stored in the Qdrant payload.

A full scroll of the Qdrant collection found the payload text different from
the Tanzil text in the database for 4,885 of 6,236 verses. These tests feed a
fake Qdrant whose payload text is the string "STALE" and check that every text
field in the response is byte-equal to the database row.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, tuple_

from app.main import app
from app.db import database
from app.models.quran import QuranVerse
from app.services import verse_embedding_service as ves

pytestmark = pytest.mark.asyncio(loop_scope="session")

HITS = [(40, 66, 0.91), (2, 124, 0.88), (1, 1, 0.80), (3, 33, 0.75)]


class _Resp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


class _FakeQdrant:
    """Stands in for httpx.AsyncClient inside verse_embedding_service."""

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kw):
        return _Resp({"result": {"points_count": 6236, "vectors_count": 6236, "status": "green"}})

    async def put(self, url, **kw):
        return _Resp({"status": "ok"})

    async def post(self, url, json=None, **kw):
        if url.endswith("/points/scroll"):
            return _Resp({"result": {"points": [{"id": 1, "vector": [0.1] * 4}]}})
        # /points/search — payload deliberately stale
        return _Resp({
            "status": "ok",
            "result": [
                {
                    "score": score,
                    "payload": {
                        "sura_no": s,
                        "aya_no": a,
                        "verse_id": 999999,
                        "text_uthmani": "STALE",
                        "text_imlaei": "STALE",
                    },
                }
                for s, a, score in HITS
            ],
        })


@pytest.fixture
def fake_qdrant(monkeypatch):
    monkeypatch.setattr(ves.httpx, "AsyncClient", _FakeQdrant)
    svc = ves.get_verse_embedding_service()
    monkeypatch.setattr(svc, "_collection_ready", True)
    monkeypatch.setattr(svc, "compute_embedding", lambda text, kind="query": [0.1] * 4)
    yield svc


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _db_rows(refs):
    async with database.AsyncSessionLocal() as s:
        rows = (await s.execute(
            select(QuranVerse).where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(refs))
        )).scalars().all()
    return {(r.sura_no, r.aya_no): r for r in rows}


async def test_find_similar_text_comes_from_db(fake_qdrant):
    results = await fake_qdrant.find_similar_to_verse(2, 255, limit=10, min_score=0.1)
    assert results, "expected hydrated results"
    db = await _db_rows([(r.sura_no, r.aya_no) for r in results])
    for r in results:
        row = db[(r.sura_no, r.aya_no)]
        assert r.text_uthmani == row.text_uthmani
        assert r.text_imlaei == row.text_imlaei
        assert r.verse_id == row.id
        assert "STALE" not in (r.text_uthmani, r.text_imlaei)
    # 1:1 is the Bismillah and is excluded
    assert (1, 1) not in {(r.sura_no, r.aya_no) for r in results}


async def test_semantic_search_text_comes_from_db(fake_qdrant):
    results = await fake_qdrant.semantic_search("patience", limit=10, min_score=0.1)
    assert results
    db = await _db_rows([(r.sura_no, r.aya_no) for r in results])
    for r in results:
        assert r.text_uthmani == db[(r.sura_no, r.aya_no)].text_uthmani


async def test_similar_endpoint_is_byte_equal_to_db(fake_qdrant, client):
    r = await client.get("/api/v1/quran/search/similar/2/124?min_score=0.1")
    assert r.status_code == 200
    items = r.json()["similar_verses"]
    assert items
    db = await _db_rows([(v["sura_no"], v["aya_no"]) for v in items])
    for v in items:
        row = db[(v["sura_no"], v["aya_no"])]
        assert v["text_uthmani"] == row.text_uthmani
        assert v["text_imlaei"] == row.text_imlaei


async def test_index_payload_carries_no_verse_text(monkeypatch):
    """index_verses() must not write verse text into the Qdrant payload."""
    sent = {}

    class _Capture(_FakeQdrant):
        async def put(self, url, json=None, **kw):
            if url.endswith("/points"):
                sent["points"] = json["points"]
            return _Resp({"status": "ok"})

    class _Model:
        async def aencode(self, texts):
            import numpy as np
            return [np.zeros(4) for _ in texts]

    monkeypatch.setattr(ves.httpx, "AsyncClient", _Capture)
    svc = ves.VerseEmbeddingService()
    svc._collection_ready = True
    monkeypatch.setattr(svc, "_get_model", lambda: _Model())
    await svc.index_verses([{"id": 8, "sura_no": 2, "aya_no": 1, "text_uthmani": "x", "text_imlaei": "y"}])
    payload = sent["points"][0]["payload"]
    assert "text_uthmani" not in payload and "text_imlaei" not in payload
