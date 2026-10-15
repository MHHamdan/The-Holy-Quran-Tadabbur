"""
'Similar verses' endpoints return results instead of silently falling back.

/quran/semantic/similar raised AttributeError on result.search_method (the
SimilaritySearchResult has no such field), logged "Similarity service error"
and returned [] for every verse. The frontend also sent top_k=60 (422 at
le=50) and exclude_same_sura (ignored; the parameter was cross_sura).

/quran/search/similar uses the stored verse vectors, needs no query
embedding (works without HF) and returns the shape the search and
similarity pages read.
"""
import logging

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_semantic_similar_returns_results(client, caplog):
    caplog.set_level(logging.ERROR)
    r = await client.get("/api/v1/quran/semantic/similar/2/255?top_k=60&exclude_same_sura=true")
    assert r.status_code == 200
    body = r.json()
    assert body["search_method"] != "fallback"
    assert body["similar_verses"], "no similar verses"
    assert all(v["sura_no"] != 2 for v in body["similar_verses"])
    assert "Similarity service error" not in caplog.text


async def test_semantic_similar_accepts_top_k_100(client):
    r = await client.get("/api/v1/quran/semantic/similar/2/255?top_k=100")
    assert r.status_code == 200
    refs = [v["reference"] for v in r.json()["similar_verses"]]
    assert "2:255" not in refs


async def test_search_similar_unknown_verse_404(client):
    r = await client.get("/api/v1/quran/search/similar/1/8")
    assert r.status_code == 404


@pytest.mark.requires_data("verse_vector:2:153")
async def test_search_similar_from_stored_vectors(client):
    r = await client.get("/api/v1/quran/search/similar/2/153?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["source_verse"]["reference"] == "2:153"
    assert len(body["similar_verses"]) >= 5
    v = body["similar_verses"][0]
    # the shape SearchPage / SimilarityPage read
    for key in ("sura_name_ar", "sura_name_en", "semantic_score", "text_uthmani", "connection_type"):
        assert key in v
    assert body["total_found"] == len(body["similar_verses"])


async def test_search_semantic_degrades_without_hf(client):
    """HF is cleared in ordinary tests: keyword results with a degraded flag, not 503."""
    r = await client.get("/api/v1/quran/search/semantic?query=patience")
    assert r.status_code == 200
    body = r.json()
    assert body["degraded"] == "ai_unavailable"
    assert body["message_ar"] and body["message_en"]
    assert body["total"] > 0


async def test_graph_semantic_reports_degraded(client):
    r = await client.get("/api/v1/graph/search/semantic?q=patience&limit=2")
    assert r.status_code == 200
    assert r.json()["degraded"] == "ai_unavailable"
