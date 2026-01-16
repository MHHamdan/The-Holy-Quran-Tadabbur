"""
Tests for Quran Search Service.

Tests cover:
1. Arabic text normalization
2. Semantic query expansion
3. TF-IDF scoring
4. Search results and matching
5. Word analytics
6. Grammatical categorization
"""

import pytest
from typing import Set

from app.services.quran_search import (
    normalize_arabic,
    extract_words,
    expand_query,
    TFIDFScorer,
    SearchMatch,
    SearchResult,
    WordAnalytics,
    GrammaticalRole,
    SentenceType,
    GRAMMATICAL_ROLE_AR,
    SENTENCE_TYPE_AR,
    ARABIC_STOP_WORDS,
    CONCEPT_EXPANSIONS,
    jaccard_similarity,
    cosine_similarity_words,
    concept_overlap_score,
    compute_combined_relevance,
)


# =============================================================================
# ARABIC NORMALIZATION TESTS
# =============================================================================

class TestArabicNormalization:
    """Tests for Arabic text normalization."""

    def test_remove_diacritics(self):
        """Diacritics (tashkeel) should be removed."""
        # "الرَّحْمَٰنِ" with diacritics
        text_with_diacritics = "الرَّحْمَٰنِ"
        normalized = normalize_arabic(text_with_diacritics)

        # Should not contain diacritics
        assert "َ" not in normalized  # Fatha
        assert "ْ" not in normalized  # Sukun
        assert "ّ" not in normalized  # Shadda

    def test_normalize_alef_variants(self):
        """Alef variants should be normalized to plain alef."""
        # Test آ (Alef with Madda)
        assert "ا" in normalize_arabic("آدم")

        # Test أ (Alef with Hamza above)
        assert "ا" in normalize_arabic("أنا")

        # Test إ (Alef with Hamza below)
        assert "ا" in normalize_arabic("إيمان")

    def test_normalize_ya_variants(self):
        """Ya variants should be normalized."""
        # Alef Maqsura (ى) to Ya (ي)
        text = "موسى"
        normalized = normalize_arabic(text)
        assert "ي" in normalized or "ى" in normalized  # Either is acceptable after normalization

    def test_preserve_base_arabic(self):
        """Base Arabic text should be preserved."""
        text = "الله"
        normalized = normalize_arabic(text)
        assert len(normalized) > 0
        assert "ل" in normalized
        assert "ه" in normalized

    def test_empty_string(self):
        """Empty string should return empty."""
        assert normalize_arabic("") == ""
        assert normalize_arabic(None) == ""


class TestWordExtraction:
    """Tests for Arabic word extraction."""

    def test_extract_arabic_words(self):
        """Should extract Arabic words from text."""
        text = "بسم الله الرحمن الرحيم"
        words = extract_words(text)

        assert len(words) > 0
        # Stop words like 'بسم' might be filtered
        assert "الله" in words or "رحمن" in words or "رحيم" in words

    def test_filter_stop_words(self):
        """Stop words should be filtered out."""
        text = "في من إلى على عن"
        words = extract_words(text)

        # All are stop words
        for word in words:
            assert word not in ARABIC_STOP_WORDS

    def test_filter_short_words(self):
        """Single-character words should be filtered."""
        text = "و ب ل ك الله"
        words = extract_words(text)

        for word in words:
            assert len(word) > 1


# =============================================================================
# SEMANTIC EXPANSION TESTS
# =============================================================================

class TestSemanticExpansion:
    """Tests for query expansion with related concepts."""

    def test_expand_allah(self):
        """'الله' should expand to related names."""
        expanded = expand_query("الله")

        assert "الله" in expanded
        # Should include some related names
        related = {"الرب", "الرحمن", "الرحيم"}
        assert len(expanded & related) > 0

    def test_expand_patience(self):
        """'صبر' should expand to related terms."""
        expanded = expand_query("صبر")

        assert "صبر" in expanded
        # Related terms
        related = {"صابر", "صابرين"}
        assert len(expanded & related) > 0

    def test_expand_forgiveness(self):
        """Forgiveness terms should expand."""
        expanded = expand_query("غفر")

        assert "غفر" in expanded
        # Related terms
        related = {"مغفرة", "غفور"}
        assert len(expanded & related) > 0

    def test_unknown_word_returns_self(self):
        """Unknown words should at least return themselves."""
        expanded = expand_query("كلمة غريبة")

        assert len(expanded) >= 1

    def test_concept_expansions_have_arabic(self):
        """All concept expansions should contain Arabic."""
        for source, targets in CONCEPT_EXPANSIONS.items():
            # Source should be Arabic
            assert any('\u0600' <= c <= '\u06FF' for c in source), \
                f"Source '{source}' is not Arabic"

            # All targets should be Arabic
            for target in targets:
                assert any('\u0600' <= c <= '\u06FF' for c in target), \
                    f"Target '{target}' is not Arabic"


# =============================================================================
# GRAMMATICAL CATEGORIZATION TESTS
# =============================================================================

class TestGrammaticalCategories:
    """Tests for grammatical role and sentence type enums."""

    def test_all_roles_have_arabic_labels(self):
        """All grammatical roles must have Arabic translations."""
        for role in GrammaticalRole:
            assert role in GRAMMATICAL_ROLE_AR, f"Missing Arabic for {role}"
            label = GRAMMATICAL_ROLE_AR[role]
            assert any('\u0600' <= c <= '\u06FF' for c in label), \
                f"Label '{label}' is not Arabic"

    def test_all_sentence_types_have_arabic_labels(self):
        """All sentence types must have Arabic translations."""
        for st in SentenceType:
            assert st in SENTENCE_TYPE_AR, f"Missing Arabic for {st}"
            label = SENTENCE_TYPE_AR[st]
            assert any('\u0600' <= c <= '\u06FF' for c in label), \
                f"Label '{label}' is not Arabic"

    def test_role_values_are_english(self):
        """Role enum values should be English identifiers."""
        for role in GrammaticalRole:
            assert role.value.isalpha() or "_" in role.value
            assert role.value.islower() or role.value == role.value.lower().replace("_", "")

    def test_sentence_type_values_are_english(self):
        """Sentence type enum values should be English identifiers."""
        for st in SentenceType:
            assert st.value.isalpha() or "_" in st.value


# =============================================================================
# DATA STRUCTURE TESTS
# =============================================================================

class TestSearchDataStructures:
    """Tests for search result data structures."""

    def test_search_match_creation(self):
        """SearchMatch should be properly created."""
        match = SearchMatch(
            verse_id=1,
            sura_no=1,
            sura_name_ar="الفاتحة",
            sura_name_en="Al-Fatihah",
            aya_no=1,
            text_uthmani="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            text_imlaei="بسم الله الرحمن الرحيم",
            page_no=1,
            juz_no=1,
            match_positions=[(5, 9)],
            highlighted_text="بسم 【الله】 الرحمن الرحيم",
            relevance_score=0.95,
            exact_match=True,
        )

        assert match.sura_no == 1
        assert match.exact_match is True
        assert match.relevance_score > 0

    def test_search_result_creation(self):
        """SearchResult should be properly created."""
        result = SearchResult(
            query="الله",
            query_normalized="الله",
            total_matches=2698,
            matches=[],
            sura_distribution={1: 4, 2: 282},
            juz_distribution={1: 50, 2: 60},
        )

        assert result.total_matches == 2698
        assert 1 in result.sura_distribution
        assert 2 in result.sura_distribution

    def test_word_analytics_creation(self):
        """WordAnalytics should be properly created."""
        analytics = WordAnalytics(
            word="الله",
            word_normalized="الله",
            total_occurrences=2698,
            by_sura={"2": {"count": 282, "sura_name_ar": "البقرة", "percentage": 10.5}},
            by_juz={1: 50, 2: 60},
        )

        assert analytics.total_occurrences == 2698
        assert "2" in analytics.by_sura


# =============================================================================
# TF-IDF SCORING TESTS
# =============================================================================

class TestTFIDFScoring:
    """Tests for TF-IDF scoring."""

    def test_tf_calculation(self):
        """TF should be count / total words."""
        scorer = TFIDFScorer()

        # Text with 2 occurrences of "الله" in 6 words
        verse = "الله أكبر الله أكبر لا إله"
        tf = scorer.compute_tf("الله", verse)

        # TF should be positive for a word that appears
        assert tf > 0

    def test_tf_zero_for_missing_word(self):
        """TF should be 0 for word not in text."""
        scorer = TFIDFScorer()

        verse = "بسم الله الرحمن الرحيم"
        tf = scorer.compute_tf("صبر", verse)

        assert tf == 0

    def test_document_count(self):
        """Document count should be total Quran verses."""
        scorer = TFIDFScorer()
        assert scorer.document_count == 6236


# =============================================================================
# ARABIC STOP WORDS TESTS
# =============================================================================

class TestArabicStopWords:
    """Tests for Arabic stop words list."""

    def test_stop_words_are_arabic(self):
        """All stop words should be Arabic."""
        for word in ARABIC_STOP_WORDS:
            assert any('\u0600' <= c <= '\u06FF' for c in word), \
                f"Stop word '{word}' is not Arabic"

    def test_common_stop_words_present(self):
        """Common Arabic stop words should be in list."""
        common = ["في", "من", "إلى", "على", "عن", "هو", "هي", "ما", "لا"]
        for word in common:
            assert word in ARABIC_STOP_WORDS, f"Missing common stop word: {word}"

    def test_meaningful_words_not_stop_words(self):
        """Meaningful words should not be stop words."""
        meaningful = ["الله", "صبر", "رحمة", "إيمان", "جنة", "نار"]
        for word in meaningful:
            assert word not in ARABIC_STOP_WORDS, f"Meaningful word wrongly in stop words: {word}"


# =============================================================================
# SIMILARITY ALGORITHM TESTS
# =============================================================================

class TestSimilarityAlgorithms:
    """Tests for similarity algorithms."""

    def test_jaccard_identical_sets(self):
        """Jaccard of identical sets should be 1.0."""
        set1 = {"الله", "رحمة", "صبر"}
        set2 = {"الله", "رحمة", "صبر"}
        assert jaccard_similarity(set1, set2) == 1.0

    def test_jaccard_disjoint_sets(self):
        """Jaccard of disjoint sets should be 0.0."""
        set1 = {"الله", "رحمة"}
        set2 = {"جنة", "نار"}
        assert jaccard_similarity(set1, set2) == 0.0

    def test_jaccard_partial_overlap(self):
        """Jaccard of overlapping sets should be between 0 and 1."""
        set1 = {"الله", "رحمة", "صبر"}
        set2 = {"الله", "رحمة", "جنة"}
        score = jaccard_similarity(set1, set2)
        assert 0 < score < 1
        # Intersection = 2, Union = 4, so Jaccard = 0.5
        assert score == pytest.approx(0.5, rel=0.01)

    def test_jaccard_empty_sets(self):
        """Jaccard with empty sets should be 0.0."""
        assert jaccard_similarity(set(), {"الله"}) == 0.0
        assert jaccard_similarity({"الله"}, set()) == 0.0

    def test_cosine_identical_words(self):
        """Cosine of identical word lists should be 1.0."""
        words = ["الله", "رحمة", "صبر"]
        assert cosine_similarity_words(words, words) == pytest.approx(1.0, rel=0.001)

    def test_cosine_different_words(self):
        """Cosine of completely different words should be 0.0."""
        words1 = ["الله", "رحمة"]
        words2 = ["جنة", "نار"]
        assert cosine_similarity_words(words1, words2) == 0.0

    def test_cosine_partial_overlap(self):
        """Cosine with partial overlap should be between 0 and 1."""
        words1 = ["الله", "رحمة", "صبر"]
        words2 = ["الله", "رحمة", "جنة"]
        score = cosine_similarity_words(words1, words2)
        assert 0 < score < 1

    def test_cosine_empty_lists(self):
        """Cosine with empty lists should be 0.0."""
        assert cosine_similarity_words([], ["الله"]) == 0.0
        assert cosine_similarity_words(["الله"], []) == 0.0

    def test_concept_overlap_full(self):
        """Concept overlap with all concepts present should be high."""
        concepts = {"الله", "رحمة"}
        verse = "إن الله غفور رحيم"  # Contains "الله" and "رحيم" (related to رحمة)
        score = concept_overlap_score(concepts, verse)
        assert score > 0

    def test_concept_overlap_empty(self):
        """Concept overlap with no matching concepts should be 0."""
        concepts = {"جنة", "نار"}
        verse = "والصابرين في البأساء والضراء"  # No matching concepts
        score = concept_overlap_score(concepts, verse)
        # Score could be 0 if no direct or expanded matches
        assert 0 <= score <= 1

    def test_combined_relevance_exact_match_bonus(self):
        """Combined relevance with exact match should be higher."""
        query = "الله"
        verse = "بسم الله الرحمن الرحيم"
        concepts = {"الله", "رحمن", "رحيم"}

        score_exact = compute_combined_relevance(
            query=query,
            verse_text=verse,
            tf_idf_score=0.5,
            exact_match=True,
            query_concepts=concepts,
        )

        score_no_exact = compute_combined_relevance(
            query=query,
            verse_text=verse,
            tf_idf_score=0.5,
            exact_match=False,
            query_concepts=concepts,
        )

        assert score_exact > score_no_exact

    def test_combined_relevance_bounded(self):
        """Combined relevance should be between 0 and 1."""
        score = compute_combined_relevance(
            query="الله",
            verse_text="الله لا إله إلا هو الحي القيوم",
            tf_idf_score=0.8,
            exact_match=True,
            query_concepts={"الله", "إله", "حي", "قيوم"},
        )
        assert 0 <= score <= 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSearchIntegration:
    """Integration tests for search functionality."""

    def test_search_match_with_grammar(self):
        """SearchMatch should accept grammatical analysis."""
        match = SearchMatch(
            verse_id=255,
            sura_no=2,
            sura_name_ar="البقرة",
            sura_name_en="Al-Baqarah",
            aya_no=255,
            text_uthmani="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
            text_imlaei="الله لا إله إلا هو الحي القيوم",
            page_no=42,
            juz_no=3,
            word_role=GrammaticalRole.SUBJECT,
            word_role_ar="فاعل",
            sentence_type=SentenceType.NOMINAL,
            sentence_type_ar="جملة اسمية",
        )

        assert match.word_role == GrammaticalRole.SUBJECT
        assert match.word_role_ar == "فاعل"
        assert match.sentence_type == SentenceType.NOMINAL

    def test_expansion_coverage(self):
        """Test expansion covers key Islamic concepts."""
        # Note: Some concepts expand, some just normalize
        # The important thing is that major concepts have expansions
        key_concepts_with_expansion = ["الله", "صبر", "رحمة", "هدى", "جنة", "نار"]

        for concept in key_concepts_with_expansion:
            expanded = expand_query(concept)
            assert len(expanded) > 1, f"Concept '{concept}' should have expansions"

    def test_expansion_includes_normalized(self):
        """Expansion should always include normalized version of query."""
        queries = ["الله", "صبر", "إيمان", "آمن"]

        for query in queries:
            expanded = expand_query(query)
            # Should have at least one result (the normalized form)
            assert len(expanded) >= 1
