"""
Phase 7 — Hallucination Guard Tests

Tests for QuranAnswerGuard: ayah reference validation, source ID trust,
fatwa blocking, scientific miracle labeling, and translation labeling.

Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
           Prof. Dr. Abdulrahman Al-Shehri
"""
import pytest

from app.safety.quran_answer_guard import (
    QuranAnswerGuard,
    GuardResult,
    AyahRef,
    SURAH_AYAH_COUNTS,
    TOTAL_SURAHS,
)
from app.rag.source_validator import TRUSTED_SOURCE_IDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def guard() -> QuranAnswerGuard:
    return QuranAnswerGuard()


VALID_SOURCE = next(iter(TRUSTED_SOURCE_IDS))  # any trusted source ID


# ---------------------------------------------------------------------------
# 1. Ayah reference parsing
# ---------------------------------------------------------------------------

class TestAyahRefParsing:
    def test_parses_simple_ref(self, guard):
        refs = guard.parse_ayah_refs("See 2:255 for the Throne Verse.")
        assert len(refs) == 1
        assert refs[0].surah == 2
        assert refs[0].ayah_start == 255

    def test_parses_range_ref(self, guard):
        refs = guard.parse_ayah_refs("Verses 2:1-5 discuss this topic.")
        assert len(refs) == 1
        assert refs[0].ayah_end == 5

    def test_parses_multiple_refs(self, guard):
        refs = guard.parse_ayah_refs("See 1:1 and 114:1 for boundary surahs.")
        assert len(refs) == 2

    def test_no_refs_returns_empty(self, guard):
        refs = guard.parse_ayah_refs("No verse reference here.")
        assert refs == []


# ---------------------------------------------------------------------------
# 2. Individual ayah reference validation
# ---------------------------------------------------------------------------

class TestIsValidAyahRef:
    def test_first_ayah_first_surah(self, guard):
        assert guard.is_valid_ayah_ref(1, 1) is True

    def test_last_ayah_last_surah(self, guard):
        # Surah 114 has 6 ayahs
        assert guard.is_valid_ayah_ref(114, 6) is True

    def test_al_baqarah_286(self, guard):
        # Surah 2 has 286 ayahs
        assert guard.is_valid_ayah_ref(2, 286) is True

    def test_surah_zero_is_invalid(self, guard):
        assert guard.is_valid_ayah_ref(0, 1) is False

    def test_surah_115_is_invalid(self, guard):
        assert guard.is_valid_ayah_ref(115, 1) is False

    def test_ayah_zero_is_invalid(self, guard):
        assert guard.is_valid_ayah_ref(1, 0) is False

    def test_ayah_beyond_surah_max_is_invalid(self, guard):
        # Surah 1 has 7 ayahs; 8 is beyond max
        assert guard.is_valid_ayah_ref(1, 8) is False

    def test_al_baqarah_287_is_invalid(self, guard):
        # Surah 2 has 286 ayahs; 287 does not exist
        assert guard.is_valid_ayah_ref(2, 287) is False

    def test_surah_114_ayah_7_is_invalid(self, guard):
        # Surah 114 has 6 ayahs; 7 does not exist
        assert guard.is_valid_ayah_ref(114, 7) is False

    def test_all_surah_counts_positive(self):
        for count in SURAH_AYAH_COUNTS:
            assert count > 0

    def test_total_surahs_is_114(self):
        assert TOTAL_SURAHS == 114

    def test_total_ayahs_is_6236(self):
        assert sum(SURAH_AYAH_COUNTS) == 6236


# ---------------------------------------------------------------------------
# 3. validate() — invented ayah reference → hard block
# ---------------------------------------------------------------------------

class TestInventedAyahRejected:
    def test_invented_surah_blocked(self, guard):
        result = guard.validate(
            answer_text="This verse 999:1 proves the claim.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert result.hard_block_reason is not None
        assert "999:1" in result.hard_block_reason or result.invalid_refs

    def test_invented_ayah_beyond_max_blocked(self, guard):
        # Surah 1 has 7 ayahs; 8 is invalid
        result = guard.validate(
            answer_text="See Surah 1:8 for this ruling.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert result.invalid_refs or "invalid" in (result.hard_block_reason or "").lower()

    def test_valid_ref_passes(self, guard):
        result = guard.validate(
            answer_text="The Throne Verse is 2:255.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True

    def test_al_fatiha_boundary_passes(self, guard):
        result = guard.validate(
            answer_text="Surah Al-Fatiha spans 1:1 to 1:7.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True


# ---------------------------------------------------------------------------
# 4. validate() — invented / unknown source → hard block
# ---------------------------------------------------------------------------

class TestInventedSourceRejected:
    def test_unknown_source_id_blocked(self, guard):
        result = guard.validate(
            answer_text="According to verified scholarship, this ayah means...",
            source_ids=["made_up_scholar_xyz"],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert result.invalid_source_ids == ["made_up_scholar_xyz"]

    def test_empty_source_list_blocked(self, guard):
        result = guard.validate(
            answer_text="Some explanation here.",
            source_ids=[],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert "no source citations" in (result.hard_block_reason or "").lower()

    def test_trusted_source_passes(self, guard):
        result = guard.validate(
            answer_text="No verse references here; just a note.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True

    def test_mix_of_valid_and_invalid_sources_blocked(self, guard):
        result = guard.validate(
            answer_text="Some explanation.",
            source_ids=[VALID_SOURCE, "totally_fake_source_abc"],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert "totally_fake_source_abc" in result.invalid_source_ids


# ---------------------------------------------------------------------------
# 5. validate() — fatwa-like intent or content → hard block
# ---------------------------------------------------------------------------

class TestFatwaBlocked:
    def test_fatwa_intent_blocked(self, guard):
        result = guard.validate(
            answer_text="Based on Islamic jurisprudence, this action is permissible.",
            source_ids=[VALID_SOURCE],
            intent="fatwa_like",
        )
        assert result.passed is False
        assert result.hard_block_reason is not None
        block = result.hard_block_reason.lower()
        assert "fatwa" in block or "ruling" in block or "scholar" in block

    def test_fatwa_keyword_in_text_blocked(self, guard):
        result = guard.validate(
            answer_text="Is it halal to invest in this company?",
            source_ids=[VALID_SOURCE],
            intent="general_question",
        )
        assert result.passed is False

    def test_arabic_fatwa_keyword_blocked(self, guard):
        result = guard.validate(
            answer_text="هل يجوز ذلك في الإسلام؟",
            source_ids=[VALID_SOURCE],
            intent="general_question",
        )
        assert result.passed is False

    def test_tafsir_summary_not_blocked_as_fatwa(self, guard):
        result = guard.validate(
            answer_text="Ibn Kathir explains the meaning of taqwa in this ayah.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True


# ---------------------------------------------------------------------------
# 6. validate() — scientific miracle claim → warning + labels, not block
# ---------------------------------------------------------------------------

class TestScientificMiracleCaution:
    def test_scientific_miracle_intent_adds_labels(self, guard):
        result = guard.validate(
            answer_text="This ayah discusses the creation of the universe.",
            source_ids=[VALID_SOURCE],
            intent="scientific_miracle_claim",
        )
        assert result.passed is True
        assert "needs_scholarly_and_scientific_review" in result.required_labels
        assert "contemporary_reflection_not_tafsir" in result.required_labels

    def test_scientific_miracle_keyword_adds_warning(self, guard):
        result = guard.validate(
            answer_text="Modern science confirms what this ayah mentioned about embryology.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True
        assert len(result.warnings) >= 1
        # Warning should mention scholarly and scientific review
        combined = " ".join(result.warnings).lower()
        assert "scientific" in combined or "علمي" in combined

    def test_arabic_miracle_keyword_triggers_caution(self, guard):
        result = guard.validate(
            answer_text="يدل هذا على الإعجاز العلمي للقرآن الكريم.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True
        assert any("review" in w.lower() or "مراجعة" in w for w in result.warnings)

    def test_normal_tafsir_has_no_miracle_labels(self, guard):
        result = guard.validate(
            answer_text="This surah emphasizes the importance of prayer and gratitude.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True
        assert "needs_scholarly_and_scientific_review" not in result.required_labels


# ---------------------------------------------------------------------------
# 7. validate() — translation must carry a label
# ---------------------------------------------------------------------------

class TestTranslationLabeled:
    def test_translation_flag_adds_label(self, guard):
        result = guard.validate(
            answer_text="In the name of Allah, the Most Gracious, the Most Merciful.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
            is_translation=True,
        )
        assert result.passed is True
        assert "translation_not_quran_text" in result.required_labels

    def test_non_translation_has_no_translation_label(self, guard):
        result = guard.validate(
            answer_text="Ibn Kathir's commentary on this passage.",
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
            is_translation=False,
        )
        assert result.passed is True
        assert "translation_not_quran_text" not in result.required_labels


# ---------------------------------------------------------------------------
# 8. Missing citation entirely → hard block
# ---------------------------------------------------------------------------

class TestMissingCitationBlocked:
    def test_no_sources_hard_blocks(self, guard):
        result = guard.validate(
            answer_text="The verse is about patience and gratitude.",
            source_ids=[],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert result.hard_block_reason is not None


# ---------------------------------------------------------------------------
# 9. Module-level singleton is accessible
# ---------------------------------------------------------------------------

class TestModuleSingleton:
    def test_singleton_importable(self):
        from app.safety.quran_answer_guard import quran_answer_guard
        assert quran_answer_guard is not None

    def test_singleton_is_guard_instance(self):
        from app.safety.quran_answer_guard import quran_answer_guard
        assert isinstance(quran_answer_guard, QuranAnswerGuard)


# ---------------------------------------------------------------------------
# 10. AyahRef.is_valid property
# ---------------------------------------------------------------------------

class TestAyahRefIsValid:
    def test_valid_range_ref(self):
        ref = AyahRef(surah=2, ayah_start=1, ayah_end=5, raw="2:1-5")
        assert ref.is_valid is True

    def test_invalid_range_end_beyond_max(self):
        # Surah 114 has 6 ayahs; end=7 is invalid
        ref = AyahRef(surah=114, ayah_start=1, ayah_end=7, raw="114:1-7")
        assert ref.is_valid is False

    def test_invalid_range_end_less_than_start(self):
        ref = AyahRef(surah=2, ayah_start=10, ayah_end=5, raw="2:10-5")
        assert ref.is_valid is False

    def test_valid_single_ayah(self):
        ref = AyahRef(surah=36, ayah_start=1, raw="36:1")
        assert ref.is_valid is True
