"""
Semantic verse similarity — index coverage tests.

GET /quran/similarity/semantic/{sura}/{aya} used to rank against a 500-verse
sample taken without an ORDER BY, so it scored roughly 8% of the Quran skewed
to the earliest surahs: 112:1 (al-Ikhlas) matched only against surahs 1-3 and
23. It now queries the Qdrant `quran_verses` collection, which holds all 6,236
verses embedded with multilingual-e5-large.

The underlying cause was that verse_embedding_service.find_similar_to_verse
looked a point up by `sura_no * 1000 + aya_no` while index_verses() keys points
on the database verse id, so it never resolved and returned [] — silently,
since callers read an empty list as "nothing similar" rather than as a failure.

Requires a seeded DB and a populated Qdrant index.

Tests cover:
  1.  Endpoint responds and reports its coverage
  2.  Full coverage considers every indexed verse, not a sample
  3.  Results reach beyond the early surahs the sample was biased toward
  4.  Self is excluded from its own similarity results
  5.  min_similarity is respected
  6.  limit is respected
  7.  Unknown verses 404
  8.  Service-level lookup resolves by payload, not a derived point id
  9.  Coverage is declared so sampled and full rankings are distinguishable
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.verse_embedding_service import get_verse_embedding_service

pytestmark = pytest.mark.asyncio(loop_scope="session")

# al-Ikhlas 112:1 sits near the end of the mushaf, so under the old sampling
# it could never be matched against its own neighbourhood.
IKHLAS = (112, 1)
QAF = (50, 16)


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


def _url(ref, **params):
    s, a = ref
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/api/v1/quran/similarity/semantic/{s}/{a}" + (f"?{query}" if query else "")


class TestServiceLookup:
    async def test_find_similar_resolves_by_payload(self):
        """The point-id guess never matched; a payload filter must."""
        svc = get_verse_embedding_service()
        results = await svc.find_similar_to_verse(
            sura_no=IKHLAS[0], aya_no=IKHLAS[1], limit=5, min_score=0.1
        )
        assert results, "index lookup returned nothing — point lookup is broken again"

    async def test_service_excludes_source_verse(self):
        svc = get_verse_embedding_service()
        results = await svc.find_similar_to_verse(
            sura_no=IKHLAS[0], aya_no=IKHLAS[1], limit=5, min_score=0.1
        )
        assert all(
            not (r.sura_no == IKHLAS[0] and r.aya_no == IKHLAS[1]) for r in results
        )

    async def test_service_returns_scores_in_range(self):
        svc = get_verse_embedding_service()
        results = await svc.find_similar_to_verse(
            sura_no=QAF[0], aya_no=QAF[1], limit=5, min_score=0.1
        )
        assert all(0.0 <= r.similarity_score <= 1.0 for r in results)


class TestEndpointCoverage:
    async def test_responds_ok(self, client: AsyncClient):
        r = await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))
        assert r.status_code == 200

    async def test_declares_coverage(self, client: AsyncClient):
        """Sampled and full rankings are not comparable, so the API says which."""
        r = await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))
        assert r.json()["coverage"] in {"full", "partial"}

    async def test_full_coverage_uses_whole_index(self, client: AsyncClient):
        body = (await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))).json()
        if body["coverage"] != "full":
            pytest.skip("Qdrant verse index unavailable")
        assert body["candidates_considered"] > 6000, (
            f"only {body['candidates_considered']} candidates — index not being used"
        )

    async def test_reaches_beyond_early_surahs(self, client: AsyncClient):
        """The old sample returned only surahs 1-3 and 23 for this verse."""
        body = (await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))).json()
        if body["coverage"] != "full":
            pytest.skip("Qdrant verse index unavailable")
        surahs = {r["sura_no"] for r in body["results"]}
        assert surahs - {1, 2, 3}, f"results still confined to early surahs: {surahs}"

    async def test_reports_the_indexed_model(self, client: AsyncClient):
        body = (await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))).json()
        if body["coverage"] != "full":
            pytest.skip("Qdrant verse index unavailable")
        assert "e5-large" in body["model_info"]["model_name"]

    async def test_excludes_source_verse(self, client: AsyncClient):
        body = (await client.get(_url(IKHLAS, limit=6, min_similarity=0.1))).json()
        assert all(r["reference"] != "112:1" for r in body["results"])

    async def test_respects_limit(self, client: AsyncClient):
        body = (await client.get(_url(QAF, limit=3, min_similarity=0.1))).json()
        assert len(body["results"]) <= 3

    async def test_respects_min_similarity(self, client: AsyncClient):
        body = (await client.get(_url(QAF, limit=10, min_similarity=0.5))).json()
        assert all(r["semantic_similarity"] >= 0.5 for r in body["results"])

    async def test_results_sorted_descending(self, client: AsyncClient):
        body = (await client.get(_url(QAF, limit=6, min_similarity=0.1))).json()
        scores = [r["semantic_similarity"] for r in body["results"]]
        assert scores == sorted(scores, reverse=True)

    async def test_unknown_verse_404s(self, client: AsyncClient):
        r = await client.get(_url((2, 9999), limit=5))
        assert r.status_code == 404

    async def test_source_verse_echoed(self, client: AsyncClient):
        body = (await client.get(_url(IKHLAS, limit=3, min_similarity=0.1))).json()
        assert body["source_verse"]["reference"] == "112:1"
        assert body["source_verse"]["text"]
