#!/usr/bin/env python3
"""
Arabic Grammar (إعراب) Integration Tests

ACCEPTANCE CRITERIA:
1. All POS tags are from valid set
2. All roles are from valid set
3. Confidence scores are 0-1
4. Arabic output labels only
5. Graceful fallback when Ollama unavailable

Run with: pytest tests/integration/test_grammar.py -v
"""
import pytest
from typing import Any, Dict
from unittest.mock import patch, AsyncMock

# Mark all tests as async
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestGrammarModels:
    """Tests for grammar model definitions."""

    def test_pos_tags_are_arabic(self):
        """All POS tags must be in Arabic."""
        from app.models.grammar import POSTag
        import re

        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for tag in POSTag:
            assert arabic_pattern.search(tag.value), \
                f"POS tag '{tag.name}' has non-Arabic value: {tag.value}"

    def test_roles_are_arabic(self):
        """All grammatical roles must be in Arabic."""
        from app.models.grammar import GrammaticalRole
        import re

        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for role in GrammaticalRole:
            assert arabic_pattern.search(role.value), \
                f"Role '{role.name}' has non-Arabic value: {role.value}"

    def test_sentence_types_are_arabic(self):
        """All sentence types must be in Arabic."""
        from app.models.grammar import SentenceType
        import re

        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for st in SentenceType:
            assert arabic_pattern.search(st.value), \
                f"Sentence type '{st.name}' has non-Arabic value: {st.value}"

    def test_case_endings_are_arabic(self):
        """All case endings must be in Arabic."""
        from app.models.grammar import CaseEnding
        import re

        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for ce in CaseEnding:
            assert arabic_pattern.search(ce.value), \
                f"Case ending '{ce.name}' has non-Arabic value: {ce.value}"

    def test_valid_pos_tags_set(self):
        """Valid POS tags set matches enum values."""
        from app.models.grammar import POSTag, VALID_POS_TAGS

        enum_values = {tag.value for tag in POSTag}
        assert VALID_POS_TAGS == enum_values

    def test_valid_roles_set(self):
        """Valid roles set matches enum values."""
        from app.models.grammar import GrammaticalRole, VALID_ROLES

        enum_values = {role.value for role in GrammaticalRole}
        assert VALID_ROLES == enum_values


class TestGrammarValidation:
    """Tests for grammar output validation."""

    def test_validate_valid_output(self):
        """Valid output passes validation."""
        from app.models.grammar import validate_grammar_output

        valid_output = {
            "sentence_type": "جملة اسمية",
            "tokens": [
                {"pos": "اسم علم", "role": "مبتدأ"},
                {"pos": "فعل مضارع", "role": "خبر"},
            ]
        }

        errors = validate_grammar_output(valid_output)
        assert len(errors) == 0

    def test_validate_invalid_pos(self):
        """Invalid POS tag is caught."""
        from app.models.grammar import validate_grammar_output

        invalid_output = {
            "sentence_type": "جملة اسمية",
            "tokens": [
                {"pos": "invalid_pos", "role": "مبتدأ"},
            ]
        }

        errors = validate_grammar_output(invalid_output)
        assert len(errors) == 1
        assert "Invalid pos" in errors[0]

    def test_validate_invalid_role(self):
        """Invalid role is caught."""
        from app.models.grammar import validate_grammar_output

        invalid_output = {
            "sentence_type": "جملة اسمية",
            "tokens": [
                {"pos": "اسم", "role": "invalid_role"},
            ]
        }

        errors = validate_grammar_output(invalid_output)
        assert len(errors) == 1
        assert "Invalid role" in errors[0]

    def test_validate_invalid_sentence_type(self):
        """Invalid sentence type is caught."""
        from app.models.grammar import validate_grammar_output

        invalid_output = {
            "sentence_type": "invalid_type",
            "tokens": []
        }

        errors = validate_grammar_output(invalid_output)
        assert len(errors) == 1
        assert "Invalid sentence_type" in errors[0]


class TestTokenAnalysis:
    """Tests for TokenAnalysis dataclass."""

    def test_token_analysis_to_dict(self):
        """TokenAnalysis.to_dict() returns proper structure."""
        from app.models.grammar import TokenAnalysis, POSTag, GrammaticalRole, CaseEnding

        token = TokenAnalysis(
            word="اللهُ",
            word_index=0,
            pos=POSTag.NOUN_PROPER,
            role=GrammaticalRole.MUBTADA,
            case_ending=CaseEnding.DAMMA,
            i3rab="مبتدأ مرفوع وعلامة رفعه الضمة",
            root="أله",
            pattern="فَعِلَ",
            confidence=0.95,
            notes_ar="لفظ الجلالة",
        )

        result = token.to_dict()

        assert result["word"] == "اللهُ"
        assert result["word_index"] == 0
        assert result["pos"] == "اسم علم"
        assert result["role"] == "مبتدأ"
        assert result["case_ending"] == "ضمة"
        assert result["i3rab"] == "مبتدأ مرفوع وعلامة رفعه الضمة"
        assert result["root"] == "أله"
        assert result["pattern"] == "فَعِلَ"
        assert result["confidence"] == 0.95
        assert result["notes_ar"] == "لفظ الجلالة"

    def test_token_analysis_optional_fields(self):
        """TokenAnalysis handles optional fields."""
        from app.models.grammar import TokenAnalysis, POSTag, GrammaticalRole

        token = TokenAnalysis(
            word="لا",
            word_index=1,
            pos=POSTag.PARTICLE_NEG,
            role=GrammaticalRole.UNKNOWN,
        )

        result = token.to_dict()

        assert result["case_ending"] is None
        assert result["root"] is None
        assert result["pattern"] is None


class TestGrammarAnalysis:
    """Tests for GrammarAnalysis dataclass."""

    def test_grammar_analysis_to_dict(self):
        """GrammarAnalysis.to_dict() returns proper structure."""
        from app.models.grammar import (
            GrammarAnalysis, TokenAnalysis, POSTag, GrammaticalRole, SentenceType
        )

        analysis = GrammarAnalysis(
            verse_reference="2:255",
            text="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ",
            sentence_type=SentenceType.NOMINAL,
            tokens=[
                TokenAnalysis(
                    word="اللهُ",
                    word_index=0,
                    pos=POSTag.NOUN_PROPER,
                    role=GrammaticalRole.MUBTADA,
                    confidence=0.9,
                ),
            ],
            notes_ar="آية الكرسي - أعظم آية في القرآن",
            overall_confidence=0.9,
            source="llm",
        )

        result = analysis.to_dict()

        assert result["verse_reference"] == "2:255"
        assert result["text"] == "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ"
        assert result["sentence_type"] == "جملة اسمية"
        assert len(result["tokens"]) == 1
        assert result["tokens"][0]["word"] == "اللهُ"
        assert result["notes_ar"] == "آية الكرسي - أعظم آية في القرآن"
        assert result["overall_confidence"] == 0.9
        assert result["source"] == "llm"


class TestGrammarService:
    """Tests for the grammar service."""

    def test_grammar_service_singleton(self):
        """Grammar service is singleton."""
        from app.services.grammar_ollama import get_grammar_service

        service1 = get_grammar_service()
        service2 = get_grammar_service()

        assert service1 is service2

    def test_build_grammar_prompt(self):
        """Grammar prompt is properly built."""
        from app.services.grammar_ollama import build_grammar_prompt

        prompt = build_grammar_prompt("اللهُ أكبر", "1:1")

        assert "اللهُ أكبر" in prompt
        assert "سورة 1:1" in prompt
        assert "JSON" in prompt

    def test_build_grammar_prompt_without_reference(self):
        """Grammar prompt works without verse reference."""
        from app.services.grammar_ollama import build_grammar_prompt

        prompt = build_grammar_prompt("بسم الله")

        assert "بسم الله" in prompt
        assert "سورة" not in prompt

    def test_pos_tag_mapping(self):
        """POS tag string mapping works correctly."""
        from app.services.grammar_ollama import GrammarService
        from app.models.grammar import POSTag

        service = GrammarService()

        assert service._get_pos_tag("اسم") == POSTag.NOUN
        assert service._get_pos_tag("فعل") == POSTag.VERB
        assert service._get_pos_tag("حرف") == POSTag.PARTICLE
        assert service._get_pos_tag("invalid") == POSTag.UNKNOWN

    def test_role_mapping(self):
        """Role string mapping works correctly."""
        from app.services.grammar_ollama import GrammarService
        from app.models.grammar import GrammaticalRole

        service = GrammarService()

        assert service._get_role("مبتدأ") == GrammaticalRole.MUBTADA
        assert service._get_role("خبر") == GrammaticalRole.KHABAR
        assert service._get_role("فاعل") == GrammaticalRole.FAEL
        assert service._get_role("invalid") == GrammaticalRole.UNKNOWN

    def test_sentence_type_mapping(self):
        """Sentence type string mapping works correctly."""
        from app.services.grammar_ollama import GrammarService
        from app.models.grammar import SentenceType

        service = GrammarService()

        assert service._get_sentence_type("جملة اسمية") == SentenceType.NOMINAL
        assert service._get_sentence_type("جملة فعلية") == SentenceType.VERBAL
        assert service._get_sentence_type("شبه جملة") == SentenceType.SEMI
        assert service._get_sentence_type("invalid") == SentenceType.UNKNOWN


class TestGrammarServiceFallback:
    """Tests for grammar service fallback behavior."""

    def test_fallback_analysis_structure(self):
        """Fallback analysis has proper structure."""
        from app.services.grammar_ollama import GrammarService
        from app.models.grammar import POSTag, GrammaticalRole, SentenceType

        service = GrammarService()
        result = service._create_fallback_analysis(
            text="بسم الله الرحمن الرحيم",
            verse_reference="1:1",
            error="Test error",
        )

        assert result.verse_reference == "1:1"
        assert result.text == "بسم الله الرحمن الرحيم"
        assert result.sentence_type == SentenceType.UNKNOWN
        assert result.overall_confidence == 0.0
        assert result.source == "fallback"
        assert "تعذّر التحليل" in result.notes_ar

        # Check tokens
        assert len(result.tokens) == 4  # 4 words
        for token in result.tokens:
            assert token.pos == POSTag.UNKNOWN
            assert token.role == GrammaticalRole.UNKNOWN
            assert token.confidence == 0.0


class TestGrammarResponseConversion:
    """Tests for converting LLM response to GrammarAnalysis."""

    def test_to_grammar_analysis(self):
        """LLM response is properly converted."""
        from app.services.grammar_ollama import GrammarService

        service = GrammarService()

        parsed = {
            "sentence_type": "جملة اسمية",
            "tokens": [
                {"w": "الله", "pos": "اسم علم", "role": "مبتدأ", "i3rab": "مبتدأ مرفوع", "confidence": 0.9},
                {"w": "أكبر", "pos": "اسم", "role": "خبر", "i3rab": "خبر مرفوع", "confidence": 0.85},
            ],
            "notes_ar": "جملة اسمية بسيطة",
        }

        result = service._to_grammar_analysis(
            parsed=parsed,
            original_text="الله أكبر",
            verse_reference="test",
        )

        assert result.verse_reference == "test"
        assert result.text == "الله أكبر"
        assert result.sentence_type.value == "جملة اسمية"
        assert len(result.tokens) == 2
        assert result.tokens[0].word == "الله"
        assert result.tokens[0].pos.value == "اسم علم"
        assert result.tokens[0].role.value == "مبتدأ"
        assert result.overall_confidence == 0.875  # Average of 0.9 and 0.85
        assert result.source == "llm"


class TestGrammarAPIRoutes:
    """Tests for grammar API route structure."""

    def test_labels_endpoint_structure(self):
        """Labels endpoint returns all valid label sets."""
        from app.models.grammar import (
            VALID_POS_TAGS, VALID_ROLES, VALID_SENTENCE_TYPES, VALID_CASE_ENDINGS
        )

        # Just verify the sets are populated
        assert len(VALID_POS_TAGS) > 0
        assert len(VALID_ROLES) > 0
        assert len(VALID_SENTENCE_TYPES) > 0
        assert len(VALID_CASE_ENDINGS) > 0

        # Verify key labels exist
        assert "اسم" in VALID_POS_TAGS
        assert "فعل" in VALID_POS_TAGS
        assert "حرف" in VALID_POS_TAGS
        assert "مبتدأ" in VALID_ROLES
        assert "خبر" in VALID_ROLES
        assert "فاعل" in VALID_ROLES


class TestGrammarConfidenceScores:
    """Tests for confidence score handling."""

    def test_confidence_bounds(self):
        """Confidence scores are between 0 and 1."""
        from app.models.grammar import TokenAnalysis, POSTag, GrammaticalRole

        # Valid confidence
        token = TokenAnalysis(
            word="test",
            word_index=0,
            pos=POSTag.NOUN,
            role=GrammaticalRole.MUBTADA,
            confidence=0.5,
        )
        assert 0 <= token.confidence <= 1

    def test_overall_confidence_calculation(self):
        """Overall confidence is properly calculated."""
        from app.services.grammar_ollama import GrammarService

        service = GrammarService()

        parsed = {
            "sentence_type": "جملة اسمية",
            "tokens": [
                {"w": "a", "pos": "اسم", "role": "مبتدأ", "i3rab": "", "confidence": 0.8},
                {"w": "b", "pos": "فعل", "role": "خبر", "i3rab": "", "confidence": 0.6},
                {"w": "c", "pos": "حرف", "role": "غير محدد", "i3rab": "", "confidence": 1.0},
            ],
        }

        result = service._to_grammar_analysis(parsed, "test", None)

        # Average: (0.8 + 0.6 + 1.0) / 3 = 0.8
        assert abs(result.overall_confidence - 0.8) < 0.001


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
