"""
Grammar Static Fallback Tests

Tests for the static morphology fallback when Ollama is unavailable.
"""
import pytest
from app.services.grammar_fallback import (
    get_static_analysis,
    get_static_verse_count,
    get_available_static_verses,
    STATIC_VERSES,
)
from app.models.grammar import (
    POSTag,
    GrammaticalRole,
    SentenceType,
    CaseEnding,
)


class TestStaticFallbackData:
    """Tests for static fallback data structure."""

    def test_static_verses_not_empty(self):
        """Static verses dictionary should not be empty."""
        assert len(STATIC_VERSES) > 0

    def test_static_verse_count(self):
        """get_static_verse_count returns correct count."""
        count = get_static_verse_count()
        assert count == len(STATIC_VERSES)
        assert count >= 8  # At least the 8 known verses

    def test_available_static_verses(self):
        """get_available_static_verses returns list of verse refs."""
        verses = get_available_static_verses()
        assert isinstance(verses, list)
        assert len(verses) == len(STATIC_VERSES)
        assert "1:1" in verses
        assert "1:2" in verses
        assert "2:255" in verses

    def test_required_verses_present(self):
        """Required popular verses should be in static data."""
        required = ["1:1", "1:2", "2:255", "112:1", "112:2"]
        for ref in required:
            assert ref in STATIC_VERSES, f"Missing required verse: {ref}"


class TestStaticAnalysisLookup:
    """Tests for looking up static analysis."""

    def test_get_by_verse_reference(self):
        """Can get analysis by verse reference."""
        result = get_static_analysis("", "1:1")
        assert result is not None
        assert result.verse_reference == "1:1"
        assert "بِسْمِ" in result.text

    def test_get_by_text_matching(self):
        """Can get analysis by matching text."""
        result = get_static_analysis("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", None)
        assert result is not None
        assert result.verse_reference == "1:1"

    def test_nonexistent_verse_returns_none(self):
        """Non-existent verse returns None."""
        result = get_static_analysis("", "99:99")
        assert result is None

    def test_nonexistent_text_returns_none(self):
        """Non-existent text returns None."""
        result = get_static_analysis("هذا نص غير موجود", None)
        assert result is None


class TestBismillahAnalysis:
    """Tests for Al-Fatiha 1:1 analysis."""

    def test_fatiha_1_1_structure(self):
        """1:1 has correct overall structure."""
        result = get_static_analysis("", "1:1")
        assert result is not None
        assert result.verse_reference == "1:1"
        assert result.sentence_type == SentenceType.SEMI
        assert result.source == "static"
        assert result.overall_confidence >= 0.9

    def test_fatiha_1_1_tokens(self):
        """1:1 has correct token count and structure."""
        result = get_static_analysis("", "1:1")
        assert result is not None
        assert len(result.tokens) == 4

        # First token: بسم
        t0 = result.tokens[0]
        assert t0.word == "بِسْمِ"
        assert t0.pos == POSTag.PARTICLE_PREP
        assert t0.role == GrammaticalRole.JARR_MAJRUR
        assert t0.case_ending == CaseEnding.KASRA
        assert t0.root == "س م و"

        # Second token: الله
        t1 = result.tokens[1]
        assert t1.word == "اللَّهِ"
        assert t1.pos == POSTag.NOUN_PROPER
        assert t1.role == GrammaticalRole.MUDAF_ILAYH


class TestAlhamdulillahAnalysis:
    """Tests for Al-Fatiha 1:2 analysis."""

    def test_fatiha_1_2_structure(self):
        """1:2 has correct overall structure."""
        result = get_static_analysis("", "1:2")
        assert result is not None
        assert result.verse_reference == "1:2"
        assert result.sentence_type == SentenceType.NOMINAL
        assert len(result.tokens) == 4

    def test_fatiha_1_2_alhamd(self):
        """1:2 Al-Hamd is correctly analyzed."""
        result = get_static_analysis("", "1:2")
        assert result is not None

        t0 = result.tokens[0]
        assert t0.word == "الْحَمْدُ"
        assert t0.pos == POSTag.NOUN
        assert t0.role == GrammaticalRole.MUBTADA
        assert t0.case_ending == CaseEnding.DAMMA
        assert t0.root == "ح م د"


class TestAyatAlKursiAnalysis:
    """Tests for Ayat Al-Kursi 2:255 analysis."""

    def test_ayat_kursi_structure(self):
        """2:255 has correct overall structure."""
        result = get_static_analysis("", "2:255")
        assert result is not None
        assert result.verse_reference == "2:255"
        assert result.sentence_type == SentenceType.NOMINAL
        assert len(result.tokens) >= 6

    def test_ayat_kursi_allah(self):
        """2:255 Allah is correctly analyzed."""
        result = get_static_analysis("", "2:255")
        assert result is not None

        t0 = result.tokens[0]
        assert t0.word == "اللَّهُ"
        assert t0.pos == POSTag.NOUN_PROPER
        assert t0.role == GrammaticalRole.MUBTADA
        assert t0.case_ending == CaseEnding.DAMMA

    def test_ayat_kursi_la_nafiya(self):
        """2:255 لا النافية is correctly analyzed."""
        result = get_static_analysis("", "2:255")
        assert result is not None

        t1 = result.tokens[1]
        assert t1.word == "لَا"
        assert t1.pos == POSTag.PARTICLE_NEG
        assert "لا النافية للجنس" in t1.i3rab


class TestIkhlasAnalysis:
    """Tests for Surah Al-Ikhlas analysis."""

    def test_ikhlas_112_1_structure(self):
        """112:1 has correct overall structure."""
        result = get_static_analysis("", "112:1")
        assert result is not None
        assert result.verse_reference == "112:1"
        assert result.sentence_type == SentenceType.VERBAL
        assert len(result.tokens) == 4

    def test_ikhlas_112_1_qul(self):
        """112:1 قل is correctly analyzed."""
        result = get_static_analysis("", "112:1")
        assert result is not None

        t0 = result.tokens[0]
        assert t0.word == "قُلْ"
        assert t0.pos == POSTag.VERB_IMPERATIVE
        assert t0.case_ending == CaseEnding.SUKUN
        assert t0.root == "ق و ل"

    def test_ikhlas_112_2_structure(self):
        """112:2 has correct overall structure."""
        result = get_static_analysis("", "112:2")
        assert result is not None
        assert result.verse_reference == "112:2"
        assert result.sentence_type == SentenceType.NOMINAL
        assert len(result.tokens) == 2


class TestMuraqabatAnalysis:
    """Tests for mystery letters and special verses."""

    def test_yasin_mystery_letters(self):
        """36:1 Ya-Sin mystery letters are handled."""
        result = get_static_analysis("", "36:1")
        assert result is not None
        assert result.sentence_type == SentenceType.UNKNOWN
        assert len(result.tokens) == 1
        assert result.tokens[0].pos == POSTag.UNKNOWN
        assert "حروف مقطعة" in result.tokens[0].i3rab


class TestConfidenceScores:
    """Tests for confidence score correctness."""

    def test_overall_confidence_reasonable(self):
        """Overall confidence should be reasonable."""
        for ref in get_available_static_verses():
            result = get_static_analysis("", ref)
            assert result is not None
            assert 0.0 <= result.overall_confidence <= 1.0

    def test_token_confidence_reasonable(self):
        """Token confidence should be reasonable."""
        for ref in get_available_static_verses():
            result = get_static_analysis("", ref)
            assert result is not None
            for token in result.tokens:
                assert 0.0 <= token.confidence <= 1.0


class TestArabicContent:
    """Tests for Arabic content correctness."""

    def test_pos_tags_are_arabic(self):
        """All POS tags should be in Arabic."""
        import re
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for ref in get_available_static_verses():
            result = get_static_analysis("", ref)
            assert result is not None
            for token in result.tokens:
                # UNKNOWN is allowed to not have Arabic
                if token.pos != POSTag.UNKNOWN:
                    assert arabic_pattern.search(token.pos.value), \
                        f"Non-Arabic POS tag in {ref}: {token.pos.value}"

    def test_roles_are_arabic(self):
        """All roles should be in Arabic."""
        import re
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')

        for ref in get_available_static_verses():
            result = get_static_analysis("", ref)
            assert result is not None
            for token in result.tokens:
                if token.role != GrammaticalRole.UNKNOWN:
                    assert arabic_pattern.search(token.role.value), \
                        f"Non-Arabic role in {ref}: {token.role.value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
