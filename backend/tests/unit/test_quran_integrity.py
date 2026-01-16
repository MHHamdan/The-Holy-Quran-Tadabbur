#!/usr/bin/env python3
"""
Quran Canonical Integrity Tests

Ensures the Quran data in the database matches canonical specifications:
1. Exactly 114 surahs
2. Exactly 6236 verses total
3. Correct verse counts per surah
4. Uthmani text integrity (if stored)

These tests verify that no accidental modifications have been made to Quran text.

Run with: pytest tests/unit/test_quran_integrity.py -v
"""

import pytest
import sys
import os
from typing import Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text as sql_text
from sqlalchemy.orm import Session


# =============================================================================
# CANONICAL CONSTANTS (from Tanzil / Standard Uthmani)
# =============================================================================

# Total verses in the Quran (standard count, excluding Bismillah in Al-Fatiha numbering)
QURAN_TOTAL_VERSES = 6236

# Total surahs
QURAN_TOTAL_SURAHS = 114

# Verse counts per surah (1-indexed, surah 1 = index 0)
QURAN_VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,    # 1-10
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,     # 11-20
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,        # 21-30
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,          # 31-40
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,           # 41-50
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,           # 51-60
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,           # 61-70
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,           # 71-80
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,           # 81-90
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,                # 91-100
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,                    # 101-110
    5, 4, 5, 6                                         # 111-114
]

# Surah names (Arabic) for reference
SURAH_NAMES_AR = {
    1: "الفاتحة",
    2: "البقرة",
    3: "آل عمران",
    112: "الإخلاص",
    113: "الفلق",
    114: "الناس",
}

# Expected source metadata
EXPECTED_SOURCE = "tanzil"
EXPECTED_QURAN_TYPE = "uthmani"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def db_session():
    """Create database session."""
    db_url = os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")
    engine = create_engine(db_url)
    with Session(engine) as session:
        yield session


# =============================================================================
# TEST 1: SURAH COUNT
# =============================================================================

class TestSurahCount:
    """Tests for correct number of surahs."""

    def test_exactly_114_surahs(self, db_session):
        """
        The Quran must have exactly 114 surahs.

        Arabic: القرآن يجب أن يحتوي على 114 سورة بالضبط
        """
        result = db_session.execute(sql_text(
            "SELECT COUNT(DISTINCT sura_no) FROM quran_verses"
        ))
        surah_count = result.scalar()

        assert surah_count == QURAN_TOTAL_SURAHS, \
            f"Expected {QURAN_TOTAL_SURAHS} surahs, found {surah_count}"

    def test_surah_numbers_1_to_114(self, db_session):
        """Surah numbers must be consecutive from 1 to 114."""
        result = db_session.execute(sql_text(
            "SELECT DISTINCT sura_no FROM quran_verses ORDER BY sura_no"
        ))
        surah_numbers = [row[0] for row in result]

        expected = list(range(1, 115))
        assert surah_numbers == expected, \
            f"Surah numbers not consecutive: missing {set(expected) - set(surah_numbers)}"


# =============================================================================
# TEST 2: VERSE COUNT
# =============================================================================

class TestVerseCount:
    """Tests for correct total verse count."""

    def test_exactly_6236_verses(self, db_session):
        """
        The Quran must have exactly 6236 verses.

        Arabic: القرآن يجب أن يحتوي على 6236 آية بالضبط
        """
        result = db_session.execute(sql_text(
            "SELECT COUNT(*) FROM quran_verses"
        ))
        verse_count = result.scalar()

        assert verse_count == QURAN_TOTAL_VERSES, \
            f"Expected {QURAN_TOTAL_VERSES} verses, found {verse_count}"

    def test_verse_counts_per_surah(self, db_session):
        """Each surah must have the correct number of verses."""
        result = db_session.execute(sql_text("""
            SELECT sura_no, COUNT(*) as verse_count
            FROM quran_verses
            GROUP BY sura_no
            ORDER BY sura_no
        """))

        mismatches = []
        for row in result:
            sura_no = row[0]
            actual_count = row[1]
            expected_count = QURAN_VERSE_COUNTS[sura_no - 1]

            if actual_count != expected_count:
                mismatches.append({
                    'sura': sura_no,
                    'expected': expected_count,
                    'actual': actual_count,
                })

        assert len(mismatches) == 0, \
            f"Verse count mismatches: {mismatches[:5]}"

    def test_al_fatiha_has_7_verses(self, db_session):
        """Al-Fatiha (Surah 1) must have exactly 7 verses."""
        result = db_session.execute(sql_text(
            "SELECT COUNT(*) FROM quran_verses WHERE sura_no = 1"
        ))
        count = result.scalar()

        assert count == 7, f"Al-Fatiha has {count} verses, expected 7"

    def test_al_baqarah_has_286_verses(self, db_session):
        """Al-Baqarah (Surah 2) must have exactly 286 verses."""
        result = db_session.execute(sql_text(
            "SELECT COUNT(*) FROM quran_verses WHERE sura_no = 2"
        ))
        count = result.scalar()

        assert count == 286, f"Al-Baqarah has {count} verses, expected 286"

    def test_an_nas_has_6_verses(self, db_session):
        """An-Nas (Surah 114) must have exactly 6 verses."""
        result = db_session.execute(sql_text(
            "SELECT COUNT(*) FROM quran_verses WHERE sura_no = 114"
        ))
        count = result.scalar()

        assert count == 6, f"An-Nas has {count} verses, expected 6"


# =============================================================================
# TEST 3: VERSE NUMBERING
# =============================================================================

class TestVerseNumbering:
    """Tests for correct verse numbering within surahs."""

    def test_verses_start_at_1(self, db_session):
        """Every surah must start at verse 1."""
        result = db_session.execute(sql_text("""
            SELECT sura_no, MIN(aya_no) as first_verse
            FROM quran_verses
            GROUP BY sura_no
            HAVING MIN(aya_no) != 1
        """))

        bad_surahs = list(result)
        assert len(bad_surahs) == 0, \
            f"Surahs not starting at verse 1: {bad_surahs}"

    def test_verses_are_consecutive(self, db_session):
        """Verses within each surah must be consecutive."""
        # Check for gaps in verse numbering
        result = db_session.execute(sql_text("""
            WITH verse_gaps AS (
                SELECT
                    sura_no,
                    aya_no,
                    LAG(aya_no) OVER (PARTITION BY sura_no ORDER BY aya_no) as prev_aya
                FROM quran_verses
            )
            SELECT sura_no, aya_no, prev_aya
            FROM verse_gaps
            WHERE prev_aya IS NOT NULL AND aya_no != prev_aya + 1
        """))

        gaps = list(result)
        assert len(gaps) == 0, \
            f"Found gaps in verse numbering: {gaps[:5]}"

    def test_no_duplicate_verses(self, db_session):
        """No duplicate (sura, aya) pairs should exist."""
        result = db_session.execute(sql_text("""
            SELECT sura_no, aya_no, COUNT(*) as cnt
            FROM quran_verses
            GROUP BY sura_no, aya_no
            HAVING COUNT(*) > 1
        """))

        duplicates = list(result)
        assert len(duplicates) == 0, \
            f"Found duplicate verses: {duplicates}"


# =============================================================================
# TEST 4: TEXT INTEGRITY (if Uthmani text stored)
# =============================================================================

class TestTextIntegrity:
    """Tests for Quran text integrity."""

    def test_all_verses_have_arabic_text(self, db_session):
        """All verses must have Arabic text."""
        result = db_session.execute(sql_text("""
            SELECT COUNT(*) FROM quran_verses
            WHERE text_uthmani IS NULL OR LENGTH(TRIM(text_uthmani)) = 0
        """))
        empty_count = result.scalar()

        assert empty_count == 0, \
            f"{empty_count} verses have empty Arabic text"

    def test_arabic_text_contains_arabic(self, db_session):
        """Arabic text must contain Arabic characters."""
        # Check a sample of verses
        result = db_session.execute(sql_text("""
            SELECT sura_no, aya_no, text_uthmani
            FROM quran_verses
            WHERE sura_no IN (1, 2, 112, 114)
            ORDER BY sura_no, aya_no
            LIMIT 20
        """))

        non_arabic = []
        for row in result:
            text = row[2]
            if text:
                # Check for Arabic character range
                has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
                if not has_arabic:
                    non_arabic.append((row[0], row[1]))

        assert len(non_arabic) == 0, \
            f"Verses without Arabic characters: {non_arabic}"

    def test_bismillah_present_in_al_fatiha(self, db_session):
        """Al-Fatiha verse 1 should contain Bismillah."""
        result = db_session.execute(sql_text("""
            SELECT text_uthmani FROM quran_verses
            WHERE sura_no = 1 AND aya_no = 1
        """))
        row = result.fetchone()

        assert row is not None, "Al-Fatiha verse 1 not found"
        text = row[0]

        # Bismillah should contain "بسم" and "الله" and "الرحمن" and "الرحيم"
        assert "بسم" in text or "بِسْمِ" in text, \
            f"Al-Fatiha 1:1 missing Bismillah: {text[:50]}"


# =============================================================================
# TEST 5: NO MODIFICATION GUARD
# =============================================================================

class TestNoModification:
    """Tests to ensure Quran text hasn't been modified."""

    def test_text_not_truncated(self, db_session):
        """Verse texts should not be truncated (reasonable length check)."""
        # Shortest verses are about 10 characters, longest are 500+
        result = db_session.execute(sql_text("""
            SELECT sura_no, aya_no, LENGTH(text_uthmani) as len
            FROM quran_verses
            WHERE LENGTH(text_uthmani) < 5
        """))

        too_short = list(result)
        assert len(too_short) == 0, \
            f"Suspiciously short verses (possible truncation): {too_short}"

    def test_known_verse_content_ayat_kursi(self, db_session):
        """Ayat al-Kursi (2:255) should contain key phrases."""
        result = db_session.execute(sql_text("""
            SELECT text_uthmani FROM quran_verses
            WHERE sura_no = 2 AND aya_no = 255
        """))
        row = result.fetchone()

        assert row is not None, "Ayat al-Kursi (2:255) not found"
        text = row[0]

        # Key phrases that must be present (simplified roots/core letters)
        # Using core consonants that appear in any spelling variant
        key_patterns = [
            "إل",      # Part of إله (god)
            "حي",      # Living (الحي)
            "قيوم",    # Self-subsisting (القيوم)
            "كرسي",    # Throne (كرسي)
        ]

        # Normalize text by removing common diacritics and special chars
        import unicodedata
        def normalize(s):
            # Remove diacritics (marks)
            return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

        text_norm = normalize(text)

        for pattern in key_patterns:
            pattern_norm = normalize(pattern)
            assert pattern_norm in text_norm, \
                f"Ayat al-Kursi missing key pattern: {pattern}"

    def test_known_verse_content_ikhlas(self, db_session):
        """Surah Al-Ikhlas (112:1) should contain 'قُلْ هُوَ اللَّهُ أَحَدٌ'."""
        result = db_session.execute(sql_text("""
            SELECT text_uthmani FROM quran_verses
            WHERE sura_no = 112 AND aya_no = 1
        """))
        row = result.fetchone()

        assert row is not None, "Al-Ikhlas 112:1 not found"
        text = row[0]

        # Must contain "أحد" (one)
        assert "أَحَدٌ" in text or "احد" in text.replace("ٌ", "").replace("َ", ""), \
            f"Al-Ikhlas 112:1 missing 'أحد': {text}"


# =============================================================================
# CONSTANT VERIFICATION
# =============================================================================

class TestConstantsCorrect:
    """Verify our constants are correct."""

    def test_verse_counts_sum_to_6236(self):
        """QURAN_VERSE_COUNTS should sum to 6236."""
        total = sum(QURAN_VERSE_COUNTS)
        assert total == QURAN_TOTAL_VERSES, \
            f"QURAN_VERSE_COUNTS sums to {total}, expected {QURAN_TOTAL_VERSES}"

    def test_verse_counts_has_114_entries(self):
        """QURAN_VERSE_COUNTS should have 114 entries."""
        assert len(QURAN_VERSE_COUNTS) == QURAN_TOTAL_SURAHS, \
            f"QURAN_VERSE_COUNTS has {len(QURAN_VERSE_COUNTS)} entries, expected {QURAN_TOTAL_SURAHS}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
