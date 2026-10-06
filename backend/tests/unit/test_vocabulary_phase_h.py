"""
Phase H — Quranic Vocabulary Live-DB Tests

Uses the real PostgreSQL database via httpx.AsyncClient + ASGITransport so that
asyncpg runs in the same event loop as the tests — avoiding the "Future attached
to a different loop" error that occurs with starlette's sync TestClient.

The seed data loaded by scripts/seed_vocabulary_qac.py must be present for
the "found" tests to pass.  Tests that check safe-refusal behaviour use words
that are guaranteed not to be in the seed data.

Tests cover:
  1.  GET /vocabulary/lookup — found path (seeded word)
  2.  GET /vocabulary/lookup — not-found path (safe refusal)
  3.  GET /vocabulary/lookup — response schema completeness
  4.  GET /vocabulary/by-ref — found path (seeded position)
  5.  GET /vocabulary/by-ref — not-found path
  6.  GET /vocabulary/by-ref — input validation (sura=0, pos=0)
  7.  GET /vocabulary/status — available=True with seeded data
  8.  GET /vocabulary/status — entry_count > 0
  9.  GET /vocabulary/sources — QAC listed as available
  10. GET /vocabulary/sources — all classical sources present
  11. GET /vocabulary/sources — total matches list length
  12. Found response has source attribution
  13. Not-found response has bilingual messages
  14. Root field present for seeded words that have roots
  15. POS tag field present for seeded words
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.rate_limit import vocab_rate_limit

# All tests share one event loop to prevent asyncpg "different loop" errors.
pytestmark = pytest.mark.asyncio(loop_scope="session")

# ---------------------------------------------------------------------------
# Override rate limit so tests run without throttling
# ---------------------------------------------------------------------------

async def _no_rate_limit() -> None:
    return None


app.dependency_overrides[vocab_rate_limit] = _no_rate_limit


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# Known seeded positions (from scripts/seed_vocabulary_qac.py _SEED list)
_FATIHA_1_1 = {"sura": 1, "aya": 1, "pos": 1}   # بِسْمِ  — root سمو
_FATIHA_1_2 = {"sura": 1, "aya": 1, "pos": 2}   # ٱللَّهِ — root أله
_IKHLAS_2_2 = {"sura": 112, "aya": 2, "pos": 2} # ٱلصَّمَدُ — root صمد
_UNSEED_WORD = "غريبةجداً"   # definitely not in seed

# ---------------------------------------------------------------------------
# 1–3. /vocabulary/lookup
# ---------------------------------------------------------------------------

class TestVocabularyLookup:
    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_seeded_word_found(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        assert r.status_code == 200
        assert r.json()["status"] == "found"

    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_seeded_word_has_root(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        body = r.json()
        assert body["root"] == "رحم"

    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_seeded_word_has_meaning_en(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        assert r.json()["meaning_en"]

    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_seeded_word_message_is_empty(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        body = r.json()
        assert body["message_en"] == ""
        assert body["message_ar"] == ""

    async def test_lookup_not_found_returns_safe_refusal(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        body = r.json()
        assert r.status_code == 200
        assert body["status"] == "no_verified_source"
        assert body["message_en"]
        assert body["message_ar"]

    async def test_lookup_not_found_nulls(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        body = r.json()
        assert body["root"] is None
        assert body["meaning_en"] is None
        assert body["example_verses"] == []

    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_source_attribution(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        body = r.json()
        assert body["source_id"] == "quranic_arabic_corpus"
        assert "Quranic Arabic Corpus" in (body.get("source_title_en") or "")

    @pytest.mark.requires_data("vocabulary")
    async def test_lookup_example_verses_contains_ref(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        body = r.json()
        assert len(body["example_verses"]) > 0
        assert "1:1" in body["example_verses"]

    async def test_lookup_schema_complete(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "ٱلرَّحْمَٰنِ"})
        body = r.json()
        for field in ["word", "status", "message_en", "message_ar",
                      "source_id", "root", "meaning_en", "example_verses"]:
            assert field in body, f"Missing field: {field}"

    async def test_lookup_word_required(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup")
        assert r.status_code == 422

    async def test_lookup_safeguard_no_ai_meaning(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        msg = r.json()["message_en"].lower()
        assert "ai" in msg or "generated" in msg or "verified" in msg


# ---------------------------------------------------------------------------
# 4–6. /vocabulary/by-ref
# ---------------------------------------------------------------------------

class TestVocabularyByRef:
    @pytest.mark.requires_data("vocabulary")
    async def test_by_ref_found(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref", params=_FATIHA_1_1)
        assert r.status_code == 200
        assert r.json()["status"] == "found"

    @pytest.mark.requires_data("vocabulary")
    async def test_by_ref_allah_word(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref", params=_FATIHA_1_2)
        body = r.json()
        assert body["status"] == "found"
        assert body["root"] == "أله"
        assert body["meaning_en"] == "Allah"

    @pytest.mark.requires_data("vocabulary")
    async def test_by_ref_samad_word(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref", params=_IKHLAS_2_2)
        body = r.json()
        assert body["status"] == "found"
        assert body["root"] == "صمد"

    async def test_by_ref_not_found(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref",
                             params={"sura": 114, "aya": 6, "pos": 99})
        assert r.status_code == 200
        assert r.json()["status"] == "no_verified_source"

    async def test_by_ref_sura_zero_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref",
                             params={"sura": 0, "aya": 1, "pos": 1})
        assert r.status_code == 422

    async def test_by_ref_pos_zero_rejected(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref",
                             params={"sura": 1, "aya": 1, "pos": 0})
        assert r.status_code == 422

    @pytest.mark.requires_data("vocabulary")
    async def test_by_ref_pos_tag_present(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/by-ref", params=_FATIHA_1_2)
        assert r.json().get("pos_tag")


# ---------------------------------------------------------------------------
# 7–8. /vocabulary/status
# ---------------------------------------------------------------------------

class TestVocabularyStatus:
    async def test_status_200(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/status")
        assert r.status_code == 200

    @pytest.mark.requires_data("vocabulary")
    async def test_status_available_true(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/status")
        assert r.json()["available"] is True

    @pytest.mark.requires_data("vocabulary")
    async def test_status_entry_count_positive(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/status")
        assert r.json()["entry_count"] > 0

    async def test_status_planned_sources_present(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert len(sources) >= 5
        assert "quranic_arabic_corpus" in sources
        assert "lisan_al_arab" in sources

    async def test_status_reason_field(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/status")
        reason = r.json()["reason"]
        assert len(reason) > 5
        # Should mention entry count
        assert "entries" in reason.lower() or "loaded" in reason.lower()


# ---------------------------------------------------------------------------
# 9–11. /vocabulary/sources
# ---------------------------------------------------------------------------

class TestVocabularySources:
    async def test_sources_200(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/sources")
        assert r.status_code == 200

    async def test_qac_is_available(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/sources")
        qac = next(s for s in r.json()["sources"] if s["source_id"] == "quranic_arabic_corpus")
        assert qac["status"] == "available"

    async def test_classical_sources_present(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = {s["source_id"] for s in r.json()["sources"]}
        assert "mufradat_al_raghib" in ids
        assert "lisan_al_arab" in ids
        assert "al_nihaya_ibn_al_athir" in ids
        assert "qamus_al_muhit" in ids

    async def test_total_matches_list(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/sources")
        body = r.json()
        assert body["total"] == len(body["sources"])

    async def test_all_sources_have_required_fields(self, client: AsyncClient):
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            for field in ["source_id", "title_en", "title_ar", "license", "status"]:
                assert field in src, f"{src.get('source_id')} missing {field}"
