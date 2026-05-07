"""
Phase K — Scientific Miracle Safety Tests

Tests for:
1. Strengthened classifier patterns (scientific_miracle_claim intent)
2. QuranAnswerGuard definitive-claim hard-block
3. Guard caution labels for soft scientific content
4. Guard pass-through for non-scientific answers
"""
import pytest

from app.safety.quran_question_classifier import QuranQuestionClassifier
from app.safety.quran_answer_guard import QuranAnswerGuard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def classifier():
    return QuranQuestionClassifier()


@pytest.fixture
def guard():
    return QuranAnswerGuard()


# ---------------------------------------------------------------------------
# Classifier — scientific_miracle_claim detection
# ---------------------------------------------------------------------------

class TestClassifierScientificPatterns:
    """New patterns added in Phase K must trigger scientific_miracle_claim."""

    @pytest.mark.parametrize("query", [
        "Does the Quran prove the big bang theory?",
        "does the quran prove modern science?",
        "expanding universe in the Quran?",
        "mountains as pegs in surah Al-Naba",
        "Does this verse prove modern physics?",
        "quran mentions embryology",
        "science proves the Quran",
        "scientifically proven by the Quran",
        "scientific miracle of surah yaseen",
    ])
    def test_english_patterns_classify_as_scientific(self, classifier, query):
        result = classifier.classify(query)
        assert result.intent == "scientific_miracle_claim", (
            f"Expected scientific_miracle_claim for: {query!r}, got {result.intent!r}"
        )

    @pytest.mark.parametrize("query", [
        "هل القرآن يثبت نظرية الانفجار الكبير؟",
        "علم الأجنة في القرآن",
        "توسع الكون في القرآن",
        "الجبال أوتاد في سورة النبأ",
        "الإعجاز العلمي في القرآن",
        "يثبت العلم صحة القرآن",
    ])
    def test_arabic_patterns_classify_as_scientific(self, classifier, query):
        result = classifier.classify(query)
        assert result.intent == "scientific_miracle_claim", (
            f"Expected scientific_miracle_claim for: {query!r}, got {result.intent!r}"
        )

    def test_scientific_intent_is_allowed_to_generate_with_caution(self, classifier):
        result = classifier.classify("Does the Quran prove the big bang?")
        assert result.intent == "scientific_miracle_claim"
        # scientific queries are allowed through (with caution) — not hard-blocked like fatwa
        assert result.allowed_to_generate is True

    def test_regular_tafsir_not_misclassified(self, classifier):
        result = classifier.classify("What does Ibn Kathir say about Surah Al-Fatiha?")
        assert result.intent != "scientific_miracle_claim"

    def test_fatwa_not_misclassified_as_scientific(self, classifier):
        result = classifier.classify("Is it halal to eat shrimp?")
        assert result.intent == "fatwa_like"
        assert result.allowed_to_generate is False


# ---------------------------------------------------------------------------
# Guard — definitive scientific claim hard-block (Phase K)
# ---------------------------------------------------------------------------

VALID_SOURCE = "ibn_kathir_ar"


class TestGuardDefinitiveScientificClaimHardBlock:
    """Definitive scientific claim phrases must be hard-blocked."""

    @pytest.mark.parametrize("phrase", [
        "This verse proves modern science definitively.",
        "The Quran definitively refers to the expanding universe.",
        "The Quran definitively means that mountains are pegs.",
        "Science has confirmed the tafsir of this verse.",
        "This proves the big bang theory from the Quran.",
        "This verse proves the theory of evolution.",
        "The Quran definitively proves modern physics.",
        "Quran has proven the existence of dark matter.",
        "This proves modern science beyond doubt.",
    ])
    def test_definitive_claim_hard_blocked(self, guard, phrase):
        result = guard.validate(
            answer_text=f"According to this verse, {phrase}",
            source_ids=[VALID_SOURCE],
            intent="scientific_miracle_claim",
        )
        assert result.passed is False, f"Should hard-block: {phrase!r}"
        assert result.hard_block_reason is not None
        assert "definitive" in result.hard_block_reason.lower() or "blocked" in result.hard_block_reason.lower() or "definitively" in result.hard_block_reason.lower() or "claim" in result.hard_block_reason.lower()

    @pytest.mark.parametrize("phrase", [
        "تثبت هذه الآية نظرية التطور.",
        "يثبت القرآن نظرية الانفجار الكبير.",
        "أثبت العلم صحة تفسير هذه الآية.",
        "هذه الآية تثبت صحة النظرية العلمية.",
        "القرآن يثبت نظرية الكم.",
    ])
    def test_arabic_definitive_claim_hard_blocked(self, guard, phrase):
        result = guard.validate(
            answer_text=phrase,
            source_ids=[VALID_SOURCE],
            intent="scientific_miracle_claim",
        )
        assert result.passed is False, f"Should hard-block Arabic phrase: {phrase!r}"


# ---------------------------------------------------------------------------
# Guard — soft scientific content: caution labels (not hard-block)
# ---------------------------------------------------------------------------

class TestGuardSoftScientificCaution:
    """Scientific content without definitive phrases → pass with labels."""

    def test_scientific_reflection_gets_caution_labels(self, guard):
        result = guard.validate(
            answer_text=(
                "Some contemporary scholars have noted that the description of the sky "
                "being expanded in this verse resonates with modern astronomy's expanding universe."
            ),
            source_ids=[VALID_SOURCE],
            intent="scientific_miracle_claim",
        )
        assert result.passed is True
        assert "scientific_reflection_needs_review" in result.required_labels
        assert "needs_scholarly_and_scientific_review" in result.required_labels
        assert "contemporary_reflection_not_tafsir" in result.required_labels
        assert len(result.warnings) >= 1

    def test_scientific_keyword_in_text_triggers_caution(self, guard):
        result = guard.validate(
            answer_text=(
                "This is a tafsir_summary. Some note the verse mentions embryology stages."
            ),
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True
        assert "scientific_reflection_needs_review" in result.required_labels

    def test_caution_warning_is_bilingual(self, guard):
        result = guard.validate(
            answer_text="This is about the big bang mentioned in the verse.",
            source_ids=[VALID_SOURCE],
            intent="scientific_miracle_claim",
        )
        assert result.passed is True
        # At least one English and one Arabic warning
        assert any("specialized" in w for w in result.warnings)
        assert any("مراجعة" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Guard — non-scientific answers unaffected
# ---------------------------------------------------------------------------

class TestGuardNonScientificUnaffected:
    """Normal tafsir answers must not receive scientific caution labels."""

    def test_plain_tafsir_no_scientific_labels(self, guard):
        result = guard.validate(
            answer_text=(
                "Ibn Kathir explains in Surah 2:255 that the Throne Verse "
                "describes Allah's sovereignty and eternal watchfulness."
            ),
            source_ids=[VALID_SOURCE],
            intent="tafsir_summary",
        )
        assert result.passed is True
        assert "scientific_reflection_needs_review" not in result.required_labels
        assert len(result.warnings) == 0

    def test_no_source_still_hard_blocks(self, guard):
        result = guard.validate(
            answer_text="A simple answer about patience in the Quran.",
            source_ids=[],
            intent="tafsir_summary",
        )
        assert result.passed is False
        assert "no source" in result.hard_block_reason.lower() or "citation" in result.hard_block_reason.lower()
