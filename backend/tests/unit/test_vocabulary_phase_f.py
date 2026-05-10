"""
Phase F — Quranic Vocabulary Module Tests (updated for Phase H live DB)

Verifies safe-refusal behavior and the authenticated Sunni sources catalogue.
The vocabulary endpoint must NEVER generate word meanings from AI alone.

Tests updated for Phase H: module is now live with QAC data.  Safe-refusal
tests use words that are definitely not in the seed data.

Uses httpx.AsyncClient + ASGITransport (same loop as asyncpg engine) to avoid
the "Future attached to a different loop" errors from sync TestClient.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.rate_limit import vocab_rate_limit

pytestmark = pytest.mark.asyncio(loop_scope="session")

_UNSEED_WORD = "غريبةجداً"   # definitely not in the seed data


async def _no_rate_limit() -> None:
    return None


app.dependency_overrides[vocab_rate_limit] = _no_rate_limit


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# 1. /vocabulary/lookup — basic behavior
# ---------------------------------------------------------------------------

class TestVocabularyLookup:
    async def test_lookup_returns_200(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        assert r.status_code == 200

    async def test_lookup_status_is_no_verified_source(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["status"] == "no_verified_source"

    async def test_lookup_echoes_word(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["word"] == _UNSEED_WORD

    async def test_lookup_english_word(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": "mercy"})
        assert r.status_code == 200
        assert r.json()["status"] == "no_verified_source"

    async def test_unseen_words_return_safe_refusal(self, client):
        for word in ["إشكالية", "مستشفى", "برتقال"]:
            r = await client.get("/api/v1/vocabulary/lookup", params={"word": word})
            assert r.json()["status"] == "no_verified_source", f"Expected refusal for: {word}"


# ---------------------------------------------------------------------------
# 2. Safe-refusal messages are present and bilingual
# ---------------------------------------------------------------------------

class TestSafeRefusalMessages:
    async def test_message_en_is_present(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        data = r.json()
        assert "message_en" in data
        assert len(data["message_en"]) > 20

    async def test_message_ar_is_present(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        data = r.json()
        assert "message_ar" in data
        assert len(data["message_ar"]) > 20

    async def test_message_en_mentions_verified_source(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        msg = r.json()["message_en"].lower()
        assert "verified" in msg or "source" in msg

    async def test_message_ar_mentions_verified_source(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        msg = r.json()["message_ar"]
        assert "موثوق" in msg or "مصدر" in msg

    async def test_message_en_does_not_contain_ai_meaning(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        msg = r.json()["message_en"].lower()
        assert "meaning_en" not in msg
        assert "the word means" not in msg

    async def test_message_ar_mentions_classical_lexicon(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        msg = r.json()["message_ar"]
        assert "لسان" in msg or "مفردات" in msg or "معجم" in msg


# ---------------------------------------------------------------------------
# 3. Not-found response has null optional fields
# ---------------------------------------------------------------------------

class TestNotFoundFieldAbsence:
    async def test_source_id_is_null(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["source_id"] is None

    async def test_root_is_null(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["root"] is None

    async def test_meaning_en_is_null(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["meaning_en"] is None

    async def test_meaning_ar_is_null(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["meaning_ar"] is None

    async def test_example_verses_is_empty(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert r.json()["example_verses"] == []


# ---------------------------------------------------------------------------
# 4. /vocabulary/status endpoint
# ---------------------------------------------------------------------------

class TestVocabularyStatus:
    async def test_status_returns_200(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert r.status_code == 200

    async def test_module_name_is_vocabulary(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert r.json()["module"] == "vocabulary"

    async def test_available_field_is_boolean(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert isinstance(r.json()["available"], bool)

    async def test_planned_sources_not_empty(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert len(r.json()["planned_sources"]) > 0

    async def test_planned_sources_include_lisan(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("lisan" in s for s in sources)

    async def test_planned_sources_include_mufradat(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("mufradat" in s for s in sources)

    async def test_planned_sources_include_ibn_qutaybah(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("qutaybah" in s for s in sources)

    async def test_planned_sources_include_al_nihaya(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("nihaya" in s for s in sources)

    async def test_planned_sources_include_lanes_lexicon(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("lanes" in s for s in sources)

    async def test_planned_sources_include_quranic_corpus(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("corpus" in s for s in sources)

    async def test_planned_sources_count_at_least_five(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert len(r.json()["planned_sources"]) >= 5

    async def test_status_has_bilingual_message_fields(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        data = r.json()
        assert "message_en" in data
        assert "message_ar" in data

    async def test_reason_field_present(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert "reason" in r.json()
        assert len(r.json()["reason"]) > 5


# ---------------------------------------------------------------------------
# 5. Response schema completeness
# ---------------------------------------------------------------------------

class TestResponseSchema:
    LOOKUP_REQUIRED_FIELDS = {"word", "status", "message_en", "message_ar", "example_verses"}
    STATUS_REQUIRED_FIELDS = {
        "module", "available", "reason", "planned_sources",
        "message_en", "message_ar", "entry_count",
    }

    async def test_lookup_has_all_required_fields(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        data = r.json()
        for field in self.LOOKUP_REQUIRED_FIELDS:
            assert field in data, f"Missing field: {field}"

    async def test_status_has_all_required_fields(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        data = r.json()
        for field in self.STATUS_REQUIRED_FIELDS:
            assert field in data, f"Missing field: {field}"

    async def test_lookup_word_param_required(self, client):
        r = await client.get("/api/v1/vocabulary/lookup")
        assert r.status_code == 422

    async def test_planned_sources_is_list(self, client):
        r = await client.get("/api/v1/vocabulary/status")
        assert isinstance(r.json()["planned_sources"], list)

    async def test_example_verses_is_list(self, client):
        r = await client.get("/api/v1/vocabulary/lookup", params={"word": _UNSEED_WORD})
        assert isinstance(r.json()["example_verses"], list)


# ---------------------------------------------------------------------------
# 6. /vocabulary/sources — authenticated Sunni lexicon catalogue
# ---------------------------------------------------------------------------

class TestVocabularySources:
    REQUIRED_SOURCE_FIELDS = {
        "source_id", "title_ar", "title_en",
        "author_ar", "author_en",
        "era_ar", "era_en",
        "focus_ar", "focus_en",
        "category", "license", "status",
    }

    async def test_sources_returns_200(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        assert r.status_code == 200

    async def test_sources_has_required_envelope_fields(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        data = r.json()
        assert "sources" in data
        assert "total" in data
        assert "message_en" in data
        assert "message_ar" in data

    async def test_sources_list_not_empty(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        assert len(r.json()["sources"]) > 0

    async def test_sources_total_matches_list_length(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        data = r.json()
        assert data["total"] == len(data["sources"])

    async def test_sources_count_at_least_five(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        assert r.json()["total"] >= 5

    async def test_each_source_has_required_fields(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            for field in self.REQUIRED_SOURCE_FIELDS:
                assert field in src, f"Source '{src.get('source_id', '?')}' missing field: {field}"

    async def test_includes_mufradat_al_raghib(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "mufradat_al_raghib" in ids

    async def test_includes_lisan_al_arab(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "lisan_al_arab" in ids

    async def test_includes_ibn_qutaybah(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "gharib_al_quran_ibn_qutaybah" in ids

    async def test_includes_al_nihaya(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "al_nihaya_ibn_al_athir" in ids

    async def test_includes_qamus_al_muhit(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "qamus_al_muhit" in ids

    async def test_includes_lanes_lexicon(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "lanes_lexicon" in ids

    async def test_includes_quranic_arabic_corpus(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        ids = [s["source_id"] for s in r.json()["sources"]]
        assert "quranic_arabic_corpus" in ids

    async def test_all_sources_have_valid_status(self, client):
        valid_statuses = {"planned", "integrating", "available"}
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            assert src["status"] in valid_statuses, \
                f"Source '{src['source_id']}' has unexpected status: {src['status']}"

    async def test_arabic_sources_have_arabic_titles(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            if src["category"] == "arabic":
                assert src["title_ar"], f"Source '{src['source_id']}' missing Arabic title"
                assert src["author_ar"], f"Source '{src['source_id']}' missing Arabic author"

    async def test_volumes_field_on_lisan_al_arab(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        lisan = next(s for s in r.json()["sources"] if s["source_id"] == "lisan_al_arab")
        assert lisan.get("volumes") == 20

    async def test_volumes_field_on_lanes_lexicon(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        lanes = next(s for s in r.json()["sources"] if s["source_id"] == "lanes_lexicon")
        assert lanes.get("volumes") == 8

    async def test_categories_are_valid(self, client):
        valid = {"arabic", "english", "digital"}
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            assert src["category"] in valid, \
                f"Source '{src['source_id']}' has invalid category: {src['category']}"

    async def test_all_sources_have_bilingual_content(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        for src in r.json()["sources"]:
            assert len(src["title_ar"]) > 3, f"'{src['source_id']}' has weak Arabic title"
            assert len(src["title_en"]) > 3, f"'{src['source_id']}' has weak English title"
            assert len(src["focus_ar"]) > 10, f"'{src['source_id']}' has weak Arabic focus"
            assert len(src["focus_en"]) > 10, f"'{src['source_id']}' has weak English focus"

    async def test_mufradat_is_public_domain(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        mufradat = next(s for s in r.json()["sources"] if s["source_id"] == "mufradat_al_raghib")
        assert "public domain" in mufradat["license"].lower()

    async def test_corpus_has_open_license(self, client):
        r = await client.get("/api/v1/vocabulary/sources")
        corpus = next(s for s in r.json()["sources"] if s["source_id"] == "quranic_arabic_corpus")
        assert "gpl" in corpus["license"].lower() or "open" in corpus["license"].lower()
