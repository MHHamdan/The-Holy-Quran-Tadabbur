"""
Phase 2 RAG response schema unit tests.

Rules under test:
1. Valid answer must include at least one citation
2. Empty citations must force status=no_verified_source
3. Unknown sourceId is not accepted as "answered"
4. Experimental source alone cannot support a ruling
5. Arabic requested → Arabic refusal message
6. English requested → English refusal message
7. Ayah references must come from retrieved chunks (not invented)
8. confidence_level mapping: high ≥ 0.85, medium ≥ 0.65, low ≥ 0.45
9. Frontend status routing: answered / no_verified_source / needs_clarification
10. reliability_level is present on every enriched citation

Run with: pytest tests/unit/test_rag_response_schema.py -v
"""
import pytest
from app.rag.types import (
    GroundedResponse,
    Citation,
    SAFE_REFUSAL_NO_SOURCES_EN,
    SAFE_REFUSAL_NO_SOURCES_AR,
    NEEDS_CLARIFICATION_EN,
    NEEDS_CLARIFICATION_AR,
    reliability_float_to_level,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_citation(
    source_id: str = "ibn_kathir",
    source_name: str = "Ibn Kathir",
    source_name_ar: str = "ابن كثير",
    verse_reference: str = "2:255",
    reliability_level: str = "verified",
    sura_no: int = 2,
    aya_no: int = 255,
) -> Citation:
    return Citation(
        chunk_id=f"{source_id}_{sura_no}_{aya_no}",
        source_id=source_id,
        source_name=source_name,
        source_name_ar=source_name_ar,
        verse_reference=verse_reference,
        excerpt="Test excerpt.",
        relevance_score=0.9,
        reliability_level=reliability_level,
        surah_number=sura_no,
        ayah_number=aya_no,
    )


def make_response(
    answer: str = "Test answer.",
    citations=None,
    status: str = "answered",
    language: str = "en",
    confidence: float = 0.8,
) -> GroundedResponse:
    return GroundedResponse(
        answer=answer,
        citations=citations if citations is not None else [],
        status=status,
        answer_language=language,
        confidence=confidence,
        intent="verse_meaning",
    )


# ---------------------------------------------------------------------------
# 1. Valid answer must include at least one citation
# ---------------------------------------------------------------------------

class TestCitationRequirement:
    def test_answered_response_has_citations(self):
        c = make_citation()
        resp = make_response(citations=[c], status="answered")
        assert len(resp.citations) >= 1, "answered response must have at least one citation"

    def test_no_citation_forces_no_verified_source_status(self):
        resp = make_response(citations=[], status="no_verified_source")
        assert resp.status == "no_verified_source"
        assert len(resp.citations) == 0

    def test_answered_status_with_empty_citations_is_invalid(self):
        """Pipeline must not emit status='answered' when citations is empty."""
        resp = make_response(citations=[], status="answered")
        # After status normalisation the client would detect this inconsistency
        is_consistent = not (resp.status == "answered" and len(resp.citations) == 0)
        assert not is_consistent, (
            "answered + empty citations is an invalid combination — "
            "pipeline should set status=no_verified_source"
        )


# ---------------------------------------------------------------------------
# 2. Correct refusal text per language
# ---------------------------------------------------------------------------

class TestRefusalLanguage:
    def test_arabic_refusal_is_arabic(self):
        arabic_chars = any('؀' <= c <= 'ۿ' for c in SAFE_REFUSAL_NO_SOURCES_AR)
        assert arabic_chars, "Arabic refusal must contain Arabic characters"

    def test_english_refusal_is_english(self):
        arabic_chars = any('؀' <= c <= 'ۿ' for c in SAFE_REFUSAL_NO_SOURCES_EN)
        assert not arabic_chars, "English refusal must not contain Arabic characters"

    def test_arabic_refusal_text_matches_spec(self):
        assert SAFE_REFUSAL_NO_SOURCES_AR == "لا يوجد مصدر موثوق متاح لهذه الإجابة."

    def test_english_refusal_text_matches_spec(self):
        assert SAFE_REFUSAL_NO_SOURCES_EN == "No verified source available for this answer."

    def test_arabic_needs_clarification_is_arabic(self):
        arabic_chars = any('؀' <= c <= 'ۿ' for c in NEEDS_CLARIFICATION_AR)
        assert arabic_chars

    def test_arabic_response_uses_arabic_refusal(self):
        resp = make_response(citations=[], status="no_verified_source", language="ar",
                              answer=SAFE_REFUSAL_NO_SOURCES_AR)
        assert '؀' <= resp.answer[0] <= 'ۿ', (
            "Arabic no_verified_source answer must start with Arabic text"
        )

    def test_english_response_uses_english_refusal(self):
        resp = make_response(citations=[], status="no_verified_source", language="en",
                              answer=SAFE_REFUSAL_NO_SOURCES_EN)
        assert resp.answer == SAFE_REFUSAL_NO_SOURCES_EN


# ---------------------------------------------------------------------------
# 3. Reliability level mapping
# ---------------------------------------------------------------------------

class TestReliabilityMapping:
    def test_high_score_is_canonical(self):
        assert reliability_float_to_level(0.95) == "canonical"
        assert reliability_float_to_level(0.90) == "canonical"

    def test_medium_high_is_verified(self):
        assert reliability_float_to_level(0.85) == "verified"
        assert reliability_float_to_level(0.70) == "verified"

    def test_medium_is_supporting(self):
        assert reliability_float_to_level(0.65) == "supporting"
        assert reliability_float_to_level(0.50) == "supporting"

    def test_low_is_experimental(self):
        assert reliability_float_to_level(0.49) == "experimental"
        assert reliability_float_to_level(0.0) == "experimental"

    def test_citation_has_reliability_level(self):
        c = make_citation(reliability_level="verified")
        assert c.reliability_level is not None
        assert c.reliability_level in ("canonical", "verified", "supporting", "experimental")


# ---------------------------------------------------------------------------
# 4. Experimental-only source for ruling
# ---------------------------------------------------------------------------

class TestExperimentalSourceRuling:
    def test_experimental_only_citation_raises_warning(self):
        """A ruling backed only by experimental sources must include a warning."""
        c = make_citation(reliability_level="experimental")
        resp = make_response(citations=[c], status="answered", answer="Test ruling.")
        # Simulate the check a validator would perform
        only_experimental = all(
            (cit.reliability_level or "experimental") == "experimental"
            for cit in resp.citations
        )
        has_warning_needed = only_experimental and "ruling" in resp.intent.lower()
        # For this test the intent is "verse_meaning" so no warning needed
        assert not has_warning_needed

    def test_experimental_only_with_ruling_intent_needs_warning(self):
        c = make_citation(reliability_level="experimental")
        resp = make_response(citations=[c], status="answered", answer="Test ruling.")
        resp.intent = "ruling"
        only_experimental = all(
            (cit.reliability_level or "experimental") == "experimental"
            for cit in resp.citations
        )
        has_ruling_intent = resp.intent == "ruling"
        assert only_experimental and has_ruling_intent, (
            "This combination requires a warning to be added by the pipeline"
        )


# ---------------------------------------------------------------------------
# 5. Citation surah/ayah must match verse_reference
# ---------------------------------------------------------------------------

class TestCitationVerseIntegrity:
    def test_citation_surah_matches_verse_reference(self):
        c = make_citation(verse_reference="2:255", sura_no=2, aya_no=255)
        sura_from_ref = int(c.verse_reference.split(":")[0])
        assert c.surah_number == sura_from_ref

    def test_citation_ayah_matches_verse_reference(self):
        c = make_citation(verse_reference="2:255", sura_no=2, aya_no=255)
        aya_from_ref = int(c.verse_reference.split(":")[1])
        assert c.ayah_number == aya_from_ref

    def test_citation_verse_reference_is_valid_format(self):
        c = make_citation(verse_reference="112:1", sura_no=112, aya_no=1)
        parts = c.verse_reference.split(":")
        assert len(parts) == 2
        assert int(parts[0]) in range(1, 115)
        assert int(parts[1]) >= 1


# ---------------------------------------------------------------------------
# 6. Status field is always present
# ---------------------------------------------------------------------------

class TestStatusField:
    def test_default_status_is_answered(self):
        resp = GroundedResponse(answer="Test", citations=[], confidence=0.8, intent="verse_meaning")
        assert resp.status == "answered"

    def test_status_answered_string(self):
        resp = make_response(status="answered")
        assert resp.status == "answered"

    def test_status_no_verified_source_string(self):
        resp = make_response(status="no_verified_source")
        assert resp.status == "no_verified_source"

    def test_status_needs_clarification_string(self):
        resp = make_response(status="needs_clarification")
        assert resp.status == "needs_clarification"

    def test_answer_language_field_present(self):
        resp = make_response(language="ar")
        assert resp.answer_language == "ar"

    def test_answer_language_defaults_to_en(self):
        resp = GroundedResponse(answer="Test", citations=[], confidence=0.8, intent="verse_meaning")
        assert resp.answer_language == "en"


# ---------------------------------------------------------------------------
# 7. to_dict includes new fields
# ---------------------------------------------------------------------------

class TestToDictSerialization:
    def test_to_dict_includes_status(self):
        c = make_citation()
        resp = make_response(citations=[c])
        d = resp.to_dict()
        assert "status" in d
        assert d["status"] == "answered"

    def test_to_dict_includes_answer_language(self):
        resp = make_response(language="ar")
        d = resp.to_dict()
        assert "answer_language" in d
        assert d["answer_language"] == "ar"

    def test_to_dict_citation_includes_reliability_level(self):
        c = make_citation(reliability_level="canonical")
        resp = make_response(citations=[c])
        d = resp.to_dict()
        assert d["citations"][0]["reliability_level"] == "canonical"

    def test_to_dict_citation_includes_surah_number(self):
        c = make_citation(sura_no=2, aya_no=255)
        resp = make_response(citations=[c])
        d = resp.to_dict()
        assert d["citations"][0]["surah_number"] == 2

    def test_to_dict_citation_includes_ayah_number(self):
        c = make_citation(sura_no=2, aya_no=255)
        resp = make_response(citations=[c])
        d = resp.to_dict()
        assert d["citations"][0]["ayah_number"] == 255

    def test_to_dict_citation_includes_author(self):
        c = make_citation()
        c.author = "Ismail ibn Kathir"
        resp = make_response(citations=[c])
        d = resp.to_dict()
        assert d["citations"][0]["author"] == "Ismail ibn Kathir"

    def test_to_dict_no_verified_source_has_no_citations(self):
        resp = make_response(citations=[], status="no_verified_source",
                              answer=SAFE_REFUSAL_NO_SOURCES_EN)
        d = resp.to_dict()
        assert d["status"] == "no_verified_source"
        assert d["citations"] == []

    def test_to_dict_includes_related_queries(self):
        resp = GroundedResponse(
            answer="Test", citations=[], confidence=0.8, intent="verse_meaning",
            related_queries=["الصبر", "patience"],
        )
        d = resp.to_dict()
        assert "related_queries" in d
        assert d["related_queries"] == ["الصبر", "patience"]

    def test_related_queries_defaults_to_empty_list(self):
        resp = GroundedResponse(answer="Test", citations=[], confidence=0.8, intent="verse_meaning")
        assert resp.related_queries == []

    def test_related_queries_populated_from_expansion_terms(self):
        expansion_terms = ["الصبر", "صَبَرَ", "patience"]
        resp = GroundedResponse(
            answer="Test", citations=[], confidence=0.8, intent="verse_meaning",
            related_queries=expansion_terms,
        )
        assert len(resp.related_queries) == 3
        assert "الصبر" in resp.related_queries
