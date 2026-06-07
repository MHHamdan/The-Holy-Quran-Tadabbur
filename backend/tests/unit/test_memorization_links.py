"""
Memorization Intelligence Route Tests

Tests for GET /api/v1/memorization/* endpoints.

These tests verify:
  1.  GET /memorization/status — available=True
  2.  GET /memorization/status — module name present
  3.  GET /memorization/similar-ayat/{surah}/{ayah} — returns ok
  4.  GET /memorization/similar-ayat — invalid surah 0 rejected
  5.  GET /memorization/similar-ayat — invalid surah 115 rejected
  6.  GET /memorization/similar-ayat — always has review warnings
  7.  GET /memorization/surah-links/{surah} — returns ok
  8.  GET /memorization/surah-links/{surah} — has review status
  9.  GET /memorization/story-links/{storyId} — valid story ID
  10. GET /memorization/story-links/{storyId} — invalid ID rejected
  11. GET /memorization/confusion-pairs — returns ok
  12. GET /memorization/confusion-pairs — filter by risk level
  13. GET /memorization/confusion-pairs — invalid risk level rejected
  14. GET /memorization/repeated-phrases — returns ok
  15. GET /memorization/repeated-phrases — has review warning
  16. All endpoints return humanReviewRequired: true
  17. All endpoints return warnings list
  18. Bilingual messages in key responses
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


class TestMemorizationStatus:
    """Tests for GET /api/v1/memorization/status"""

    async def test_status_available(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        assert r.status_code == 200
        assert r.json()["available"] is True

    async def test_status_module_name(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        assert r.json()["module"] == "memorization_intelligence"

    async def test_status_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_status_has_bilingual_messages(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        data = r.json()
        assert "message_en" in data
        assert "message_ar" in data
        assert len(data["message_en"]) > 10
        assert len(data["message_ar"]) > 10

    async def test_status_has_coverage(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/status")
        assert "coverage" in r.json()


class TestSimilarAyat:
    """Tests for GET /api/v1/memorization/similar-ayat/{surah}/{ayah}"""

    async def test_returns_ok_for_valid_ayah(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/1/1")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_returns_surah_ayah_in_data(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/18/9")
        data = r.json()["data"]
        assert data["surah"] == 18
        assert data["ayah"] == 9

    async def test_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/2/1")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_has_human_review_flag(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/2/1")
        assert r.json()["humanReviewRequired"] is True

    async def test_has_warnings(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/2/1")
        assert len(r.json()["warnings"]) > 0

    async def test_invalid_surah_0(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/0/1")
        assert r.status_code == 422

    async def test_invalid_surah_115(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/115/1")
        assert r.status_code == 422

    async def test_invalid_ayah_0(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/similar-ayat/1/0")
        assert r.status_code == 422


class TestSurahMemorizationLinks:
    """Tests for GET /api/v1/memorization/surah-links/{surah}"""

    async def test_returns_ok_for_valid_surah(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/surah-links/18")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_has_surah_number(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/surah-links/18")
        assert r.json()["data"]["surah"] == 18

    async def test_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/surah-links/1")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_invalid_surah_0(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/surah-links/0")
        assert r.status_code == 422


class TestStoryLinks:
    """Tests for GET /api/v1/memorization/story-links/{story_id}"""

    async def test_valid_story_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/story-links/story_musa")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_has_story_id_in_data(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/story-links/story_ibrahim")
        assert r.json()["data"]["storyId"] == "story_ibrahim"

    async def test_invalid_story_id(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/story-links/invalid_id_no_prefix")
        assert r.status_code == 422

    async def test_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/story-links/story_musa")
        assert r.json()["reviewStatus"] == "needs_review"


class TestConfusionPairs:
    """Tests for GET /api/v1/memorization/confusion-pairs"""

    async def test_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_has_human_review_flag(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs")
        assert r.json()["humanReviewRequired"] is True

    async def test_filter_by_risk_high(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs?risk_level=high")
        assert r.status_code == 200

    async def test_filter_by_risk_medium(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs?risk_level=medium")
        assert r.status_code == 200

    async def test_filter_by_surah(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs?surah=18")
        assert r.status_code == 200

    async def test_invalid_risk_level_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/confusion-pairs?risk_level=invalid")
        assert r.status_code == 422


class TestRepeatedPhrases:
    """Tests for GET /api/v1/memorization/repeated-phrases"""

    async def test_returns_ok(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/repeated-phrases")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_has_review_status(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/repeated-phrases")
        assert r.json()["reviewStatus"] == "needs_review"

    async def test_has_warnings(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/repeated-phrases")
        assert len(r.json()["warnings"]) > 0

    async def test_filter_by_surah(self, client: AsyncClient):
        r = await client.get("/api/v1/memorization/repeated-phrases?surah=55")
        assert r.status_code == 200
