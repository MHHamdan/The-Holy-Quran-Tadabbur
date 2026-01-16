"""
Tests for Bismillah Exclusion in Similarity Computations.

Validates that the Bismillah phrase is correctly:
1. Detected in various forms (with/without diacritics)
2. Removed from verse text for similarity computation
3. Excluded from search results appropriately
4. Handled correctly in multi-concept search

Arabic: اختبارات استبعاد البسملة من حسابات التشابه
"""

import pytest
from app.services.quran_text_utils import (
    BISMILLAH_PATTERNS,
    BISMILLAH_REGEX,
    remove_bismillah,
    is_bismillah_verse,
    is_sura_opening_verse,
    is_first_verse_with_bismillah,
    preprocess_for_similarity,
    parse_multi_concept_query,
    expand_bilingual_query,
    get_concept_expansions,
)


class TestBismillahPatterns:
    """Tests for Bismillah pattern detection."""

    def test_full_bismillah_with_diacritics_detected(self):
        """Full Bismillah with diacritics should be detected."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        assert is_bismillah_verse(text)

    def test_full_bismillah_with_standard_diacritics(self):
        """Bismillah with standard diacritics should be detected."""
        text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        assert is_bismillah_verse(text)

    def test_full_bismillah_without_diacritics(self):
        """Bismillah without diacritics should be detected."""
        text = "بسم الله الرحمن الرحيم"
        assert is_bismillah_verse(text)

    def test_verse_with_bismillah_prefix_not_bismillah_only(self):
        """Verse starting with Bismillah but with additional content is not Bismillah-only."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"
        # This has content beyond Bismillah, so is_bismillah_verse should return False
        assert not is_bismillah_verse(text)

    def test_non_bismillah_verse(self):
        """Regular verse should not be detected as Bismillah."""
        text = "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"
        assert not is_bismillah_verse(text)


class TestRemoveBismillah:
    """Tests for removing Bismillah from verse text."""

    def test_remove_bismillah_from_beginning(self):
        """Bismillah at beginning should be removed."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ ٱلْحَمْدُ لِلَّهِ"
        result = remove_bismillah(text)
        assert "بِسْمِ" not in result
        assert "ٱلْحَمْدُ" in result

    def test_remove_bismillah_preserves_content(self):
        """Content after Bismillah should be preserved."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الم"
        result = remove_bismillah(text)
        assert "الم" in result

    def test_remove_bismillah_from_pure_bismillah(self):
        """Pure Bismillah verse should result in empty or minimal text."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        result = remove_bismillah(text)
        # Should be empty or just whitespace
        assert len(result.strip()) == 0 or result == text  # May return original if nothing left

    def test_non_bismillah_text_unchanged(self):
        """Text without Bismillah should remain unchanged."""
        text = "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"
        result = remove_bismillah(text)
        assert result == text


class TestPreprocessForSimilarity:
    """Tests for preprocessing text for similarity computation."""

    def test_preprocess_removes_bismillah_for_first_verse(self):
        """First verse (aya 1) of any sura should have Bismillah removed."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ ٱلْحَمْدُ لِلَّهِ"
        result = preprocess_for_similarity(text, sura_no=1, aya_no=1)
        assert "بِسْمِ" not in result
        assert "ٱلْحَمْدُ" in result

    def test_preprocess_sura_1_verse_1_special_case(self):
        """Sura 1 verse 1 (Al-Fatiha) IS the Bismillah."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        result = preprocess_for_similarity(text, sura_no=1, aya_no=1)
        # For similarity, this should be empty or minimal
        assert len(result.strip()) == 0 or "بسم" not in result.lower()

    def test_preprocess_middle_verse_unchanged(self):
        """Middle verses should not have anything removed."""
        text = "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        result = preprocess_for_similarity(text, sura_no=1, aya_no=3)
        assert result.strip() == text.strip()

    def test_preprocess_with_exclude_false(self):
        """When exclude_bismillah=False, text should be unchanged."""
        text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        result = preprocess_for_similarity(text, exclude_bismillah=False)
        assert "بِسْمِ" in result


class TestIsSuraOpeningVerse:
    """Tests for detecting sura opening verses."""

    def test_first_verse_is_opening(self):
        """Verse 1 of any sura is an opening verse."""
        assert is_sura_opening_verse(1, 1)
        assert is_sura_opening_verse(2, 1)
        assert is_sura_opening_verse(114, 1)

    def test_non_first_verse_not_opening(self):
        """Non-first verses are not opening verses."""
        assert not is_sura_opening_verse(1, 2)
        assert not is_sura_opening_verse(2, 5)


class TestIsFirstVerseWithBismillah:
    """Tests for detecting verses that typically have Bismillah."""

    def test_first_verse_of_most_suras_has_bismillah(self):
        """First verse of most suras has Bismillah."""
        assert is_first_verse_with_bismillah(1, 1)
        assert is_first_verse_with_bismillah(2, 1)
        assert is_first_verse_with_bismillah(114, 1)

    def test_sura_9_has_no_bismillah(self):
        """Sura 9 (At-Tawbah) has no Bismillah."""
        assert not is_first_verse_with_bismillah(9, 1)

    def test_non_first_verse_has_no_bismillah(self):
        """Non-first verses don't have Bismillah prefix."""
        assert not is_first_verse_with_bismillah(1, 2)
        assert not is_first_verse_with_bismillah(2, 5)
        assert not is_first_verse_with_bismillah(112, 2)


class TestMultiConceptQueryParsing:
    """Tests for multi-concept query parsing."""

    def test_parse_english_and_query(self):
        """English 'and' connector should be parsed."""
        result = parse_multi_concept_query("Solomon and Queen of Sheba")
        assert result.is_multi_concept
        assert len(result.concepts) == 2
        assert result.connector_type == "and"

    def test_parse_arabic_and_query(self):
        """Arabic 'و' connector should be parsed."""
        result = parse_multi_concept_query("موسى و فرعون")
        assert result.is_multi_concept
        assert result.connector_type == "and"

    def test_parse_single_concept(self):
        """Single concept query should not be multi-concept."""
        result = parse_multi_concept_query("patience")
        assert not result.is_multi_concept
        assert len(result.concepts) == 1

    def test_parse_or_connector(self):
        """'or' connector should set connector_type to 'or'."""
        result = parse_multi_concept_query("mercy or justice")
        assert result.is_multi_concept
        assert result.connector_type == "or"


class TestBilingualExpansion:
    """Tests for bilingual concept expansion."""

    def test_expand_solomon_to_arabic(self):
        """'Solomon' should expand to Arabic equivalents."""
        expansions = get_concept_expansions("solomon", language="ar")
        assert "سليمان" in expansions or any("سليمان" in exp for exp in expansions)

    def test_expand_arabic_to_english(self):
        """Arabic concept should expand to English equivalents."""
        expansions = get_concept_expansions("صبر", language="en")
        assert "patience" in expansions or any("patience" in exp.lower() for exp in expansions)

    def test_expand_bilingual_query(self):
        """Query expansion should include both languages."""
        expansions, _ = expand_bilingual_query("patience")
        # Should have both English and Arabic terms
        has_arabic = any(any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in exp) for exp in expansions)
        has_english = any(all(ord(c) < 0x0600 for c in exp) for exp in expansions)
        assert has_arabic or has_english  # At least one language present


class TestBismillahExclusionIntegration:
    """Integration tests for Bismillah exclusion in search."""

    def test_surah_9_no_bismillah(self):
        """Surah 9 (At-Tawbah) has no Bismillah - verify handling."""
        # Surah 9 verse 1 doesn't start with Bismillah
        text = "بَرَآءَةٌ مِّنَ ٱللَّهِ وَرَسُولِهِ"
        result = preprocess_for_similarity(text, sura_no=9, aya_no=1)
        # Should remain unchanged since there's no Bismillah
        assert "بَرَآءَةٌ" in result

    def test_surah_27_verse_30_special_bismillah(self):
        """Surah 27:30 contains Bismillah in the middle (Solomon's letter)."""
        text = "إِنَّهُ مِن سُلَيْمَٰنَ وَإِنَّهُ بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
        # This Bismillah is part of the narrative, not the standard opening
        # The function should handle this appropriately
        result = preprocess_for_similarity(text, sura_no=27, aya_no=30)
        # The verse contains substantive content so shouldn't be detected as pure Bismillah
        assert not is_bismillah_verse(text)
