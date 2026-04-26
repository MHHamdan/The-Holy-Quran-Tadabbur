"""
Unit tests for Arabic text normalization in Tasmeeʿ feature.

Tests cover:
1. Diacritic removal (tashkeel)
2. Alef normalization
3. Yaa/Alif-maqsura normalization
4. Ta marbuta normalization
5. Tatweel removal
6. Tokenization
7. Word similarity calculation
"""

import pytest
from app.stt.arabic_normalizer import (
    remove_diacritics,
    normalize_alef,
    normalize_yaa,
    normalize_ta_marbuta,
    remove_tatweel,
    normalize_arabic,
    normalize_for_matching,
    tokenize_arabic,
    tokenize_with_positions,
    word_similarity,
    find_best_match,
    get_quran_words,
    ArabicNormalizer,
    NormalizedWord,
)


class TestDiacriticRemoval:
    """Test diacritic (tashkeel) removal."""

    def test_remove_fatha(self):
        """Test removal of fatha (فَ -> ف)."""
        assert remove_diacritics("بَسْمِ") == "بسم"

    def test_remove_kasra(self):
        """Test removal of kasra (بِ -> ب)."""
        assert remove_diacritics("بِسْمِ") == "بسم"

    def test_remove_damma(self):
        """Test removal of damma (بُ -> ب)."""
        assert remove_diacritics("رَبُّكَ") == "ربك"

    def test_remove_sukun(self):
        """Test removal of sukun (بْ -> ب). Note: remove_diacritics strips diacritics only; alef variants are unchanged."""
        assert remove_diacritics("اقْرَأْ") == "اقرأ"

    def test_remove_shadda(self):
        """Test removal of shadda (رَبَّ -> رب)."""
        assert remove_diacritics("رَبَّكَ") == "ربك"

    def test_remove_tanween(self):
        """Test removal of tanween (ًٌٍ)."""
        assert remove_diacritics("كِتَابًا") == "كتابا"
        assert remove_diacritics("كِتَابٌ") == "كتاب"
        assert remove_diacritics("كِتَابٍ") == "كتاب"

    def test_full_verse_diacritics(self):
        """Test diacritic removal on full verse."""
        verse = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        expected = "بسم الله الرحمن الرحيم"
        assert remove_diacritics(verse) == expected

    def test_empty_string(self):
        """Test with empty string."""
        assert remove_diacritics("") == ""

    def test_no_diacritics(self):
        """Test string without diacritics."""
        text = "بسم الله"
        assert remove_diacritics(text) == text


class TestAlefNormalization:
    """Test alef variant normalization."""

    def test_alef_with_hamza_above(self):
        """أ -> ا"""
        assert normalize_alef("أحمد") == "احمد"

    def test_alef_with_hamza_below(self):
        """إ -> ا"""
        assert normalize_alef("إبراهيم") == "ابراهيم"

    def test_alef_with_madda(self):
        """آ -> ا"""
        assert normalize_alef("آدم") == "ادم"
        assert normalize_alef("القرآن") == "القران"

    def test_alef_wasla(self):
        """ٱ -> ا (normalize_alef only replaces alef variants; diacritics remain)"""
        assert normalize_alef("ٱلْحَمْدُ") == "الْحَمْدُ"

    def test_mixed_alefs(self):
        """Test text with multiple alef variants."""
        text = "آدم وإبراهيم وأحمد"
        expected = "ادم وابراهيم واحمد"
        assert normalize_alef(text) == expected

    def test_plain_alef_unchanged(self):
        """Plain alef should remain unchanged."""
        assert normalize_alef("الله") == "الله"


class TestYaaNormalization:
    """Test yaa and alif-maqsura normalization."""

    def test_alif_maqsura_to_yaa(self):
        """ى -> ي"""
        assert normalize_yaa("موسى") == "موسي"
        assert normalize_yaa("عيسى") == "عيسي"

    def test_farsi_yeh_to_yaa(self):
        """ی -> ي (Farsi yeh)"""
        assert normalize_yaa("می") == "مي"

    def test_mixed_yaa_forms(self):
        """Test with multiple yaa forms."""
        text = "موسى وعيسى والهدى"
        expected = "موسي وعيسي والهدي"
        assert normalize_yaa(text) == expected

    def test_plain_yaa_unchanged(self):
        """Plain yaa should remain unchanged."""
        assert normalize_yaa("يوم") == "يوم"


class TestTaMarbutaNormalization:
    """Test ta marbuta to ha normalization."""

    def test_ta_marbuta_to_ha(self):
        """ة -> ه"""
        assert normalize_ta_marbuta("رحمة") == "رحمه"
        assert normalize_ta_marbuta("نعمة") == "نعمه"

    def test_multiple_ta_marbuta(self):
        """Test multiple ta marbutas."""
        text = "رحمة ونعمة"
        expected = "رحمه ونعمه"
        assert normalize_ta_marbuta(text) == expected

    def test_ta_marbuta_unchanged_ha(self):
        """Existing ha should remain unchanged."""
        assert normalize_ta_marbuta("الله") == "الله"


class TestTatweelRemoval:
    """Test tatweel (kashida) removal."""

    def test_remove_tatweel(self):
        """Test kashida removal."""
        assert remove_tatweel("اللـــه") == "الله"
        assert remove_tatweel("محـمـد") == "محمد"

    def test_no_tatweel(self):
        """Test string without tatweel."""
        text = "الله"
        assert remove_tatweel(text) == text


class TestFullNormalization:
    """Test complete normalization pipeline."""

    def test_normalize_arabic_default(self):
        """Test default normalization settings."""
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        result = normalize_arabic(text)
        assert "ِ" not in result  # No kasra
        assert "ْ" not in result  # No sukun
        assert "َ" not in result  # No fatha

    def test_normalize_for_matching(self):
        """Test normalization for matching."""
        text1 = "بِسْمِ اللَّهِ"
        text2 = "بسم الله"
        assert normalize_for_matching(text1) == normalize_for_matching(text2)

    def test_normalize_preserves_content(self):
        """Normalization should preserve semantic content."""
        original = "الرَّحْمَٰنِ الرَّحِيمِ"
        normalized = normalize_for_matching(original)
        assert "رحمن" in normalized
        assert "رحيم" in normalized

    def test_normalize_arabic_custom_flags(self):
        """Test normalization with custom flags."""
        text = "رحمة"
        # With ta marbuta normalization
        result_with_ta = normalize_arabic(text, normalize_ta_marbuta_flag=True)
        assert result_with_ta == "رحمه"

        # Without ta marbuta normalization
        result_without_ta = normalize_arabic(text, normalize_ta_marbuta_flag=False)
        assert result_without_ta == "رحمة"


class TestTokenization:
    """Test Arabic text tokenization."""

    def test_simple_tokenization(self):
        """Test basic tokenization."""
        text = "بسم الله الرحمن الرحيم"
        tokens = tokenize_arabic(text)
        assert len(tokens) == 4
        assert tokens[0] == "بسم"
        assert tokens[3] == "الرحيم"

    def test_tokenization_with_diacritics(self):
        """Test tokenization removes diacritics."""
        text = "بِسْمِ اللَّهِ"
        tokens = tokenize_arabic(text, normalize=True)
        assert tokens[0] == "بسم"
        assert tokens[1] == "الله"

    def test_tokenization_without_normalization(self):
        """Test tokenization preserves diacritics when normalize=False."""
        text = "بِسْمِ اللَّهِ"
        tokens = tokenize_arabic(text, normalize=False)
        assert "ِ" in tokens[0]  # Kasra preserved

    def test_tokenize_with_positions(self):
        """Test tokenization with position info."""
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ"
        words = tokenize_with_positions(text)

        assert len(words) == 3
        assert words[0].original == "بِسْمِ"
        assert words[0].normalized == "بسم"
        assert words[0].position == 0
        assert words[2].position == 2

    def test_tokenize_empty_string(self):
        """Test tokenization of empty string."""
        assert tokenize_arabic("") == []
        assert tokenize_with_positions("") == []


class TestWordSimilarity:
    """Test word similarity calculation."""

    def test_identical_words(self):
        """Identical words should have similarity 1.0."""
        assert word_similarity("الله", "الله") == 1.0

    def test_completely_different_words(self):
        """Different words should have low similarity."""
        sim = word_similarity("الله", "محمد")
        assert sim < 0.5

    def test_similar_words(self):
        """Similar words should have high similarity."""
        # One character difference
        sim = word_similarity("رحمن", "رحيم")
        assert sim >= 0.5

    def test_empty_word(self):
        """Empty word should have zero similarity."""
        assert word_similarity("", "الله") == 0.0
        assert word_similarity("الله", "") == 0.0

    def test_similarity_is_symmetric(self):
        """Similarity should be symmetric."""
        word1, word2 = "الرحمن", "الرحيم"
        assert word_similarity(word1, word2) == word_similarity(word2, word1)


class TestFindBestMatch:
    """Test finding best matching word from candidates."""

    def test_exact_match(self):
        """Should find exact match."""
        candidates = ["بسم", "الله", "الرحمن", "الرحيم"]
        idx, score = find_best_match("الله", candidates)
        assert idx == 1
        assert score == 1.0

    def test_no_match_below_threshold(self):
        """Should return None if no match above threshold."""
        candidates = ["بسم", "الله"]
        idx, score = find_best_match("محمد", candidates, threshold=0.9)
        assert idx is None
        assert score == 0.0

    def test_best_partial_match(self):
        """Should find best partial match."""
        candidates = ["رحمن", "رحيم", "عظيم"]
        idx, score = find_best_match("رحمان", candidates, threshold=0.7)
        assert idx == 0  # رحمن is closest to رحمان


class TestGetQuranWords:
    """Test Quran word extraction."""

    def test_simple_verse(self):
        """Test extracting words from simple verse."""
        verse = "الحمد لله رب العالمين"
        words = get_quran_words(verse)
        assert len(words) == 4
        assert words[0].normalized == "الحمد"
        assert words[3].normalized == "العالمين"

    def test_verse_with_diacritics(self):
        """Test with diacritics."""
        verse = "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        words = get_quran_words(verse)
        assert len(words) == 4
        assert words[0].normalized == "الحمد"


class TestArabicNormalizerClass:
    """Test ArabicNormalizer class interface."""

    def test_default_normalizer(self):
        """Test normalizer with default settings."""
        normalizer = ArabicNormalizer()
        text = "بِسْمِ اللَّهِ"
        result = normalizer.normalize(text)
        assert "ِ" not in result

    def test_custom_normalizer(self):
        """Test normalizer with custom settings."""
        normalizer = ArabicNormalizer(
            remove_diacritics=True,
            normalize_ta_marbuta=True,
        )
        assert normalizer.normalize("رحمة") == "رحمه"

    def test_normalizer_tokenize(self):
        """Test normalizer tokenize method."""
        normalizer = ArabicNormalizer()
        tokens = normalizer.tokenize("بسم الله الرحمن")
        assert len(tokens) == 3

    def test_normalizer_tokenize_with_info(self):
        """Test normalizer tokenize_with_info method."""
        normalizer = ArabicNormalizer()
        words = normalizer.tokenize_with_info("بسم الله")
        assert all(isinstance(w, NormalizedWord) for w in words)


class TestNormalizedWordEquality:
    """Test NormalizedWord equality and hashing."""

    def test_equal_normalized_words(self):
        """Words with same normalized form should be equal."""
        w1 = NormalizedWord(original="بِسْمِ", normalized="بسم", position=0)
        w2 = NormalizedWord(original="بسم", normalized="بسم", position=1)
        assert w1 == w2

    def test_string_equality(self):
        """NormalizedWord should compare with string."""
        w = NormalizedWord(original="بِسْمِ", normalized="بسم", position=0)
        assert w == "بسم"

    def test_hashable(self):
        """NormalizedWord should be hashable."""
        w1 = NormalizedWord(original="بِسْمِ", normalized="بسم", position=0)
        w2 = NormalizedWord(original="بسم", normalized="بسم", position=1)
        s = {w1, w2}
        assert len(s) == 1  # Same normalized form


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_numbers_mixed_with_arabic(self):
        """Test handling of numbers."""
        text = "سورة البقرة 255"
        result = normalize_arabic(text, remove_non_arabic_flag=True)
        assert "255" not in result

    def test_punctuation_removal(self):
        """Test punctuation handling."""
        text = "الحمد لله، رب العالمين!"
        result = normalize_arabic(text, remove_non_arabic_flag=True)
        assert "،" not in result
        assert "!" not in result

    def test_multiple_spaces(self):
        """Test multiple space normalization."""
        text = "الحمد   لله     رب"
        result = normalize_arabic(text)
        assert "   " not in result
        assert result == "الحمد لله رب"

    def test_leading_trailing_spaces(self):
        """Test space trimming."""
        text = "  الحمد لله  "
        result = normalize_arabic(text)
        assert result == "الحمد لله"

    def test_unicode_normalization(self):
        """Test Unicode NFC normalization consistency."""
        # Same character can have different Unicode representations
        text1 = "الله"
        text2 = "الله"  # May have different composition
        assert normalize_for_matching(text1) == normalize_for_matching(text2)
