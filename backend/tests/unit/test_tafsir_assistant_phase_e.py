"""
Phase E — Tafsir Assistant Upgrade Tests

Tests for the supervised tafsir assistant fields added to GroundedResponse:
  - answer_mode set correctly per question intent
  - ai_summary_disclaimer always True
  - disagreement_warning set when scholarly sources disagree
  - fields serialized correctly in to_dict()
  - mode determination helper works correctly
  - disclaimer cannot be suppressed by pipeline logic
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Optional

from app.rag.types import GroundedResponse, Citation
from app.rag.pipeline import RAGPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(**kwargs) -> GroundedResponse:
    """Build a minimal valid GroundedResponse for testing Phase E fields."""
    defaults = dict(
        answer="Test answer.",
        citations=[],
        confidence=0.8,
        intent="verse_meaning",
        processing_time_ms=100,
    )
    defaults.update(kwargs)
    return GroundedResponse(**defaults)


def _make_pipeline() -> RAGPipeline:
    """Create a RAGPipeline instance without DB dependencies."""
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.session = MagicMock()
    pipeline.retriever = MagicMock()
    pipeline.validator = MagicMock()
    from app.core.config import settings
    pipeline.settings = settings
    return pipeline


# ---------------------------------------------------------------------------
# 1. Default field values on GroundedResponse
# ---------------------------------------------------------------------------

class TestGroundedResponseDefaults:
    def test_answer_mode_defaults_to_tafsir_summary(self):
        r = _make_response()
        assert r.answer_mode == "tafsir_summary"

    def test_ai_summary_disclaimer_defaults_to_true(self):
        r = _make_response()
        assert r.ai_summary_disclaimer is True

    def test_disagreement_warning_defaults_to_none(self):
        r = _make_response()
        assert r.disagreement_warning is None

    def test_can_set_answer_mode(self):
        r = _make_response(answer_mode="tafsir_comparison")
        assert r.answer_mode == "tafsir_comparison"

    def test_can_set_disagreement_warning(self):
        r = _make_response(disagreement_warning="Scholars differ on this.")
        assert r.disagreement_warning == "Scholars differ on this."


# ---------------------------------------------------------------------------
# 2. to_dict() serialization includes Phase E fields
# ---------------------------------------------------------------------------

class TestToDict:
    def test_answer_mode_in_to_dict(self):
        r = _make_response(answer_mode="thematic")
        d = r.to_dict()
        assert d["answer_mode"] == "thematic"

    def test_ai_summary_disclaimer_in_to_dict(self):
        r = _make_response()
        d = r.to_dict()
        assert d["ai_summary_disclaimer"] is True

    def test_disagreement_warning_none_in_to_dict(self):
        r = _make_response()
        d = r.to_dict()
        assert d["disagreement_warning"] is None

    def test_disagreement_warning_value_in_to_dict(self):
        r = _make_response(disagreement_warning="Scholars disagree.")
        d = r.to_dict()
        assert d["disagreement_warning"] == "Scholars disagree."

    def test_all_three_fields_present_in_to_dict(self):
        r = _make_response()
        d = r.to_dict()
        assert "answer_mode" in d
        assert "ai_summary_disclaimer" in d
        assert "disagreement_warning" in d


# ---------------------------------------------------------------------------
# 3. _determine_answer_mode() — mode mapping
# ---------------------------------------------------------------------------

class TestDetermineAnswerMode:
    def test_tafsir_question_returns_tafsir_summary(self):
        pipeline = _make_pipeline()
        mode, _ = pipeline._determine_answer_mode(
            question="What is the tafsir of 2:255?",
            scholarly_consensus=None,
            tafsir_by_source={},
        )
        assert mode == "tafsir_summary"

    def test_scientific_miracle_returns_needs_scholar_review(self):
        pipeline = _make_pipeline()
        mode, _ = pipeline._determine_answer_mode(
            question="Does this verse prove the Big Bang theory?",
            scholarly_consensus=None,
            tafsir_by_source={},
        )
        assert mode == "needs_scholar_review"

    def test_thematic_question_returns_thematic(self):
        pipeline = _make_pipeline()
        mode, _ = pipeline._determine_answer_mode(
            question="Show me verses about patience in the Quran.",
            scholarly_consensus=None,
            tafsir_by_source={},
        )
        assert mode == "thematic"

    def test_vocabulary_question_returns_vocabulary(self):
        pipeline = _make_pipeline()
        mode, _ = pipeline._determine_answer_mode(
            question="What is the meaning of the word 'taqwa'?",
            scholarly_consensus=None,
            tafsir_by_source={},
        )
        assert mode == "vocabulary"

    def test_multiple_sources_upgrades_to_tafsir_comparison(self):
        pipeline = _make_pipeline()
        # Use a general question — "general_question" intent → "simple_explanation"
        # With 2+ sources this upgrades to "tafsir_comparison"
        mode, _ = pipeline._determine_answer_mode(
            question="What does Surah Al-Baqarah verse 1 say?",
            scholarly_consensus=None,
            tafsir_by_source={"ibn_kathir": [], "tabari": []},  # 2 sources
        )
        assert mode == "tafsir_comparison"

    def test_single_source_stays_simple_or_tafsir(self):
        pipeline = _make_pipeline()
        # Single source — no upgrade
        mode, _ = pipeline._determine_answer_mode(
            question="What does Surah Al-Baqarah verse 1 say?",
            scholarly_consensus=None,
            tafsir_by_source={"ibn_kathir": []},  # 1 source
        )
        assert mode in ("tafsir_summary", "simple_explanation")  # either is valid

    def test_thematic_with_multiple_sources_stays_thematic(self):
        # thematic intent is not upgraded to comparison
        pipeline = _make_pipeline()
        mode, _ = pipeline._determine_answer_mode(
            question="What does the Quran say about prayer?",
            scholarly_consensus=None,
            tafsir_by_source={"ibn_kathir": [], "tabari": []},
        )
        assert mode == "thematic"


# ---------------------------------------------------------------------------
# 4. _determine_answer_mode() — disagreement detection
# ---------------------------------------------------------------------------

class TestDisagreementWarning:
    def test_no_disagreement_when_consensus_none(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="What is the tafsir of this verse?",
            scholarly_consensus=None,
            tafsir_by_source={},
        )
        assert warning is None

    def test_disagreement_detected_from_dispute_signal(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="Explain this verse.",
            scholarly_consensus="Scholars dispute the interpretation here.",
            tafsir_by_source={},
        )
        assert warning is not None
        assert len(warning) > 10

    def test_disagreement_detected_from_differ_signal(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="What does this ayah mean?",
            scholarly_consensus="Views differ on this ruling.",
            tafsir_by_source={},
        )
        assert warning is not None

    def test_disagreement_detected_arabic_signal(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="ما معنى هذه الآية؟",
            scholarly_consensus="اختلف العلماء في معنى هذه الآية.",
            tafsir_by_source={},
        )
        assert warning is not None

    def test_no_disagreement_for_clear_consensus(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="What is the meaning?",
            scholarly_consensus="All major scholars agree on this meaning.",
            tafsir_by_source={},
        )
        assert warning is None

    def test_disagreement_warning_contains_bilingual_text(self):
        pipeline = _make_pipeline()
        _, warning = pipeline._determine_answer_mode(
            question="Explain this verse.",
            scholarly_consensus="Scholars disagree on the scope.",
            tafsir_by_source={},
        )
        assert warning is not None
        # Warning contains both English and Arabic text
        assert "scholars" in warning.lower() or "views" in warning.lower()
        assert "العلماء" in warning or "اختلف" in warning


# ---------------------------------------------------------------------------
# 5. ai_summary_disclaimer is always True
# ---------------------------------------------------------------------------

class TestAISummaryDisclaimerImmutability:
    def test_disclaimer_true_by_default(self):
        r = _make_response()
        assert r.ai_summary_disclaimer is True

    def test_disclaimer_in_serialized_output(self):
        r = _make_response()
        assert r.to_dict()["ai_summary_disclaimer"] is True

    def test_disclaimer_true_for_all_modes(self):
        modes = [
            "simple_explanation", "tafsir_summary", "tafsir_comparison",
            "vocabulary", "thematic", "needs_scholar_review",
        ]
        for mode in modes:
            r = _make_response(answer_mode=mode)
            assert r.ai_summary_disclaimer is True, f"Failed for mode: {mode}"


# ---------------------------------------------------------------------------
# 6. All valid answer modes are accepted
# ---------------------------------------------------------------------------

class TestValidAnswerModes:
    VALID_MODES = [
        "simple_explanation",
        "tafsir_summary",
        "tafsir_comparison",
        "vocabulary",
        "thematic",
        "needs_scholar_review",
    ]

    def test_all_modes_can_be_set(self):
        for mode in self.VALID_MODES:
            r = _make_response(answer_mode=mode)
            assert r.answer_mode == mode

    def test_all_modes_serialize(self):
        for mode in self.VALID_MODES:
            r = _make_response(answer_mode=mode)
            d = r.to_dict()
            assert d["answer_mode"] == mode


# ---------------------------------------------------------------------------
# 7. Mode determination intent map covers all classifier intents
# ---------------------------------------------------------------------------

class TestIntentToModeCoverage:
    ALL_CLASSIFIER_INTENTS = [
        "scientific_miracle_claim", "thematic_tafsir", "vocabulary_meaning",
        "munasabah", "tafsir_summary", "irab", "morphology", "qiraat",
        "story", "similarity", "general_question", "fatwa_like",
        "unsupported", "needs_clarification",
    ]

    def test_all_classifier_intents_have_a_mode(self):
        pipeline = _make_pipeline()
        for intent in self.ALL_CLASSIFIER_INTENTS:
            mode = pipeline._CLASSIFIER_INTENT_TO_MODE.get(intent)
            assert mode is not None, f"No mode mapping for intent: {intent}"

    def test_all_mapped_modes_are_valid(self):
        pipeline = _make_pipeline()
        valid_modes = {
            "simple_explanation", "tafsir_summary", "tafsir_comparison",
            "vocabulary", "thematic", "needs_scholar_review",
        }
        for intent, mode in pipeline._CLASSIFIER_INTENT_TO_MODE.items():
            assert mode in valid_modes, f"Invalid mode '{mode}' for intent '{intent}'"


# ---------------------------------------------------------------------------
# 8. Pydantic API model has Phase E fields
# ---------------------------------------------------------------------------

class TestPydanticModelFields:
    def test_pydantic_model_has_answer_mode(self):
        from app.api.routes.rag import GroundedResponse as PydanticGR
        assert "answer_mode" in PydanticGR.model_fields

    def test_pydantic_model_has_ai_summary_disclaimer(self):
        from app.api.routes.rag import GroundedResponse as PydanticGR
        assert "ai_summary_disclaimer" in PydanticGR.model_fields

    def test_pydantic_model_has_disagreement_warning(self):
        from app.api.routes.rag import GroundedResponse as PydanticGR
        assert "disagreement_warning" in PydanticGR.model_fields

    def test_pydantic_answer_mode_default(self):
        from app.api.routes.rag import GroundedResponse as PydanticGR
        field = PydanticGR.model_fields["answer_mode"]
        assert field.default == "tafsir_summary"

    def test_pydantic_ai_summary_disclaimer_default_true(self):
        from app.api.routes.rag import GroundedResponse as PydanticGR
        field = PydanticGR.model_fields["ai_summary_disclaimer"]
        assert field.default is True
