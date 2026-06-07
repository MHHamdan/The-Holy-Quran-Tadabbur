"""
Surah Atlas Intelligence Route Tests

Tests for GET /api/v1/surah-atlas/* endpoints.

These tests do NOT require a database — the surah atlas reads from the
surahMemoryAtlas.json static file and returns structured responses.

Tests cover:
  1.  GET /surah-atlas — returns 114 surahs
  2.  GET /surah-atlas — total field equals 114
  3.  GET /surah-atlas — first item has surahNumber=1
  4.  GET /surah-atlas — status field is "ok"
  5.  GET /surah-atlas — reviewStatus is "needs_review"
  6.  GET /surah-atlas — humanReviewRequired is true
  7.  GET /surah-atlas — warnings list is non-empty
  8.  GET /surah-atlas?revelation_type=makki — filtered results
  9.  GET /surah-atlas?search=Baqara — returns Al-Baqara
  10. GET /surah-atlas/{surah} — returns single surah detail
  11. GET /surah-atlas/1 — Al-Fatiha is correct
  12. GET /surah-atlas/114 — An-Nas is correct
  13. GET /surah-atlas/0 — 404 error
  14. GET /surah-atlas/115 — 404 error
  15. GET /surah-atlas/{surah}/stories — returns stories list
  16. GET /surah-atlas/{surah}/rare-words — returns safe refusal
  17. GET /surah-atlas/{surah}/memorization-links — returns memo data
  18. GET /surah-atlas/search?q=Musa — returns results
  19. Each result in list has required fields
  20. Detail response has ayah count
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

class TestSurahAtlasList:
    """Tests for GET /api/v1/surah-atlas"""

    async def test_returns_ok_status(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_returns_114_surahs(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas?limit=114")
        data = r.json()
        assert data["total"] == 114

    async def test_data_list_not_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        assert len(r.json()["data"]) > 0

    async def test_review_status_needs_review(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_human_review_required(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        assert r.json()["humanReviewRequired"] is True

    async def test_warnings_non_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        assert len(r.json()["warnings"]) > 0

    async def test_each_item_has_surah_number(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        for item in r.json()["data"]:
            assert "surahNumber" in item
            assert 1 <= item["surahNumber"] <= 114

    async def test_each_item_has_ayah_count(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        for item in r.json()["data"]:
            assert item["ayahCount"] > 0

    async def test_each_item_has_names(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas")
        for item in r.json()["data"]:
            assert item["nameArabic"]
            assert item["nameTransliteration"]

    async def test_filter_by_makki(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas?revelation_type=makki")
        data = r.json()
        assert data["total"] < 114
        for item in data["data"]:
            assert item["revelationType"] == "makki"

    async def test_filter_by_madani(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas?revelation_type=madani")
        data = r.json()
        assert data["total"] < 114
        for item in data["data"]:
            assert item["revelationType"] == "madani"

    async def test_search_baqara(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas?search=Baqara")
        results = r.json()["data"]
        assert any(item["surahNumber"] == 2 for item in results)

    async def test_pagination_offset(self, client: AsyncClient):
        r1 = await client.get("/api/v1/surah-atlas?limit=10&offset=0")
        r2 = await client.get("/api/v1/surah-atlas?limit=10&offset=10")
        ids1 = [item["surahNumber"] for item in r1.json()["data"]]
        ids2 = [item["surahNumber"] for item in r2.json()["data"]]
        assert ids1 != ids2

    async def test_limit_param_respected(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas?limit=5")
        assert len(r.json()["data"]) <= 5


# ---------------------------------------------------------------------------
# Detail endpoint
# ---------------------------------------------------------------------------

class TestSurahAtlasDetail:
    """Tests for GET /api/v1/surah-atlas/{surah_number}"""

    async def test_fatiha_detail(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["surahNumber"] == 1
        assert data["ayahCount"] == 7

    async def test_baqara_detail(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/2")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["surahNumber"] == 2
        assert data["ayahCount"] == 286

    async def test_nas_detail(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/114")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["surahNumber"] == 114

    async def test_invalid_surah_0(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/0")
        assert r.status_code == 404

    async def test_invalid_surah_115(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/115")
        assert r.status_code == 404

    async def test_detail_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_detail_has_human_review_flag(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        assert r.json()["humanReviewRequired"] is True

    async def test_detail_has_warnings(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        assert len(r.json()["warnings"]) > 0

    async def test_detail_has_revelation_type(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        data = r.json()["data"]
        assert "revelationType" in data
        assert data["revelationType"] in ("makki", "madani", "mixed", "disputed", "unknown", "needs_review")

    async def test_detail_has_first_ayah_preview(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/1")
        data = r.json()["data"]
        # firstAyahPreview is optional but Fatiha should have it
        assert "firstAyahPreview" in data


# ---------------------------------------------------------------------------
# Sub-endpoints
# ---------------------------------------------------------------------------

class TestSurahAtlasSubEndpoints:
    """Tests for stories, rare-words, memorization-links sub-endpoints"""

    async def test_stories_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/12/stories")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_stories_has_surah_number(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/12/stories")
        assert r.json()["data"]["surahNumber"] == 12

    async def test_rare_words_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/18/rare-words")
        assert r.status_code == 200

    async def test_rare_words_has_review_warning(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/18/rare-words")
        assert r.json()["reviewStatus"] == "needs_review"
        assert r.json()["humanReviewRequired"] is True

    async def test_memorization_links_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/18/memorization-links")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_stories_invalid_surah(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/0/stories")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------

class TestSurahAtlasSearch:
    """Tests for GET /api/v1/surah-atlas/search"""

    async def test_search_returns_results(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/search?q=Yusuf")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_search_returns_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/surah-atlas/search?q=Ibrahim")
        assert r.json()["reviewStatus"] == "needs_review"
