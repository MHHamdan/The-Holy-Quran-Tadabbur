"""
Phase F — Quranic Vocabulary Module Tests

Verifies safe-refusal behavior: the vocabulary endpoint must NEVER generate
word meanings from AI alone — it returns a structured refusal until verified
lexical data is integrated.

Tests cover:
  1. /vocabulary/lookup returns status="no_verified_source"
  2. /vocabulary/lookup always includes bilingual safe-refusal messages
  3. /vocabulary/status reports module as unavailable
  4. /vocabulary/status lists planned sources
  5. Response schema fields are correct
  6. Source fields (source_id, root, meaning_en, meaning_ar) are absent in placeholder
  7. Example_verses is empty in placeholder
  8. Any word returns the same safe refusal (no AI-generated meanings)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. /vocabulary/lookup — basic safe-refusal
# ---------------------------------------------------------------------------

class TestVocabularyLookup:
    def test_lookup_returns_200(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        assert r.status_code == 200

    def test_lookup_status_is_no_verified_source(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "تقوى"})
        assert r.json()["status"] == "no_verified_source"

    def test_lookup_echoes_word(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "رحمة"})
        assert r.json()["word"] == "رحمة"

    def test_lookup_english_word(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "mercy"})
        assert r.status_code == 200
        assert r.json()["status"] == "no_verified_source"

    def test_any_word_returns_safe_refusal(self):
        for word in ["صبر", "حكمة", "نور", "إيمان", "كفر"]:
            r = client.get("/api/v1/vocabulary/lookup", params={"word": word})
            assert r.json()["status"] == "no_verified_source", f"Expected refusal for: {word}"


# ---------------------------------------------------------------------------
# 2. Safe-refusal messages are present and bilingual
# ---------------------------------------------------------------------------

class TestSafeRefusalMessages:
    def test_message_en_is_present(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        data = r.json()
        assert "message_en" in data
        assert len(data["message_en"]) > 20

    def test_message_ar_is_present(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        data = r.json()
        assert "message_ar" in data
        assert len(data["message_ar"]) > 20

    def test_message_en_mentions_verified_source(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        msg = r.json()["message_en"].lower()
        assert "verified" in msg or "source" in msg

    def test_message_ar_mentions_verified_source(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        msg = r.json()["message_ar"]
        assert "موثوق" in msg or "مصدر" in msg

    def test_message_en_does_not_contain_ai_meaning(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "أحد"})
        msg = r.json()["message_en"].lower()
        assert "meaning_en" not in msg
        assert "the word means" not in msg

    def test_message_ar_mentions_classical_lexicon(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "أحد"})
        msg = r.json()["message_ar"]
        assert "لسان" in msg or "مفردات" in msg or "معجم" in msg


# ---------------------------------------------------------------------------
# 3. Source fields absent in placeholder
# ---------------------------------------------------------------------------

class TestPlaceholderFieldAbsence:
    def test_source_id_is_null(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert r.json()["source_id"] is None

    def test_root_is_null(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert r.json()["root"] is None

    def test_meaning_en_is_null(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert r.json()["meaning_en"] is None

    def test_meaning_ar_is_null(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert r.json()["meaning_ar"] is None

    def test_example_verses_is_empty(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert r.json()["example_verses"] == []


# ---------------------------------------------------------------------------
# 4. /vocabulary/status endpoint
# ---------------------------------------------------------------------------

class TestVocabularyStatus:
    def test_status_returns_200(self):
        r = client.get("/api/v1/vocabulary/status")
        assert r.status_code == 200

    def test_module_name_is_vocabulary(self):
        r = client.get("/api/v1/vocabulary/status")
        assert r.json()["module"] == "vocabulary"

    def test_available_is_false(self):
        r = client.get("/api/v1/vocabulary/status")
        assert r.json()["available"] is False

    def test_planned_sources_not_empty(self):
        r = client.get("/api/v1/vocabulary/status")
        assert len(r.json()["planned_sources"]) > 0

    def test_planned_sources_include_lisan(self):
        r = client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("lisan" in s for s in sources)

    def test_planned_sources_include_mufradat(self):
        r = client.get("/api/v1/vocabulary/status")
        sources = r.json()["planned_sources"]
        assert any("mufradat" in s for s in sources)

    def test_status_has_bilingual_messages(self):
        r = client.get("/api/v1/vocabulary/status")
        data = r.json()
        assert "message_en" in data and len(data["message_en"]) > 10
        assert "message_ar" in data and len(data["message_ar"]) > 10

    def test_reason_field_present(self):
        r = client.get("/api/v1/vocabulary/status")
        assert "reason" in r.json()
        assert len(r.json()["reason"]) > 5


# ---------------------------------------------------------------------------
# 5. Response schema completeness
# ---------------------------------------------------------------------------

class TestResponseSchema:
    LOOKUP_REQUIRED_FIELDS = {"word", "status", "message_en", "message_ar", "example_verses"}
    STATUS_REQUIRED_FIELDS = {"module", "available", "reason", "planned_sources", "message_en", "message_ar"}

    def test_lookup_has_all_required_fields(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "علم"})
        data = r.json()
        for field in self.LOOKUP_REQUIRED_FIELDS:
            assert field in data, f"Missing field: {field}"

    def test_status_has_all_required_fields(self):
        r = client.get("/api/v1/vocabulary/status")
        data = r.json()
        for field in self.STATUS_REQUIRED_FIELDS:
            assert field in data, f"Missing field: {field}"

    def test_lookup_word_param_required(self):
        r = client.get("/api/v1/vocabulary/lookup")
        assert r.status_code == 422

    def test_planned_sources_is_list(self):
        r = client.get("/api/v1/vocabulary/status")
        assert isinstance(r.json()["planned_sources"], list)

    def test_example_verses_is_list(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "نور"})
        assert isinstance(r.json()["example_verses"], list)
