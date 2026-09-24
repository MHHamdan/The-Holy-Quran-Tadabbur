"""
Story verse-coverage and Duʿā catalogue tests.

Covers two fixes:

A. Story.total_verses is an unmaintained column that was 0 for every seeded
   story, so the API now derives the figure from the story's segments. The
   count must be the union of the covered (sura, aya) pairs, because segments
   of the same story overlap routinely — Badr covers 8:5-14 and again 8:9-12,
   which naive summing reports as 19 verses instead of 15.

B. The Duʿā catalogue used to be a hand-copied Python list that drifted to 21
   of 66 entries and duplicated Quranic Arabic as string literals. It is now
   generated into backend/app/data/duas.json, so the shipped file is checked
   for shape, completeness and reference validity.

Tests:
  1.  A single-ayah segment covers one verse
  2.  An inclusive range covers every verse in it
  3.  A null aya_end is treated as a single ayah
  4.  A reversed range is normalised rather than dropped
  5.  A null sura contributes nothing
  6.  Overlapping segments in one sura are not double-counted
  7.  The same ayah number in different suras stays distinct
  8.  Derived counts win over a stale stored column
  9.  A stored count is kept when nothing can be derived
  10. Zero is returned when neither source has a figure
  11. The generated Duʿā catalogue exists and parses
  12. The catalogue holds every curated entry
  13. Duʿā ids are unique
  14. Every Duʿā carries an in-range Quranic reference
  15. Every Duʿā exposes the fields the API serves
"""
import json
from pathlib import Path

import pytest

from app.api.routes.duas import _DUAS, _DUAS_PATH
from app.api.routes.stories import _resolve_total_verses, _segment_verse_keys


# --- A. verse coverage ------------------------------------------------------

def test_single_ayah_segment_covers_one_verse():
    assert _segment_verse_keys(2, 255, 255) == {(2, 255)}


def test_range_is_inclusive_of_both_ends():
    assert _segment_verse_keys(8, 5, 8) == {(8, 5), (8, 6), (8, 7), (8, 8)}


def test_missing_aya_end_is_a_single_ayah():
    assert _segment_verse_keys(112, 1, None) == {(112, 1)}


def test_reversed_range_is_normalised():
    assert _segment_verse_keys(3, 127, 123) == _segment_verse_keys(3, 123, 127)


def test_missing_sura_contributes_nothing():
    assert _segment_verse_keys(None, 1, 5) == set()
    assert _segment_verse_keys(2, None, None) == set()


def test_overlapping_segments_are_not_double_counted():
    """Badr: 8:5-14 and 8:9-12 overlap; the union is 10 verses, not 14."""
    covered = _segment_verse_keys(8, 5, 14) | _segment_verse_keys(8, 9, 12)
    assert len(covered) == 10


def test_same_ayah_number_in_different_suras_stays_distinct():
    covered = _segment_verse_keys(2, 30, 30) | _segment_verse_keys(7, 30, 30)
    assert len(covered) == 2


# --- A. stored vs derived ---------------------------------------------------

def test_derived_count_overrides_stale_stored_column():
    assert _resolve_total_verses(0, 15) == 15
    assert _resolve_total_verses(99, 15) == 15


def test_stored_count_is_kept_when_nothing_is_derived():
    assert _resolve_total_verses(12, 0) == 12
    assert _resolve_total_verses(12, None) == 12


def test_zero_when_neither_source_has_a_figure():
    assert _resolve_total_verses(None, None) == 0
    assert _resolve_total_verses(0, 0) == 0


# --- B. generated Duʿā catalogue -------------------------------------------

def test_generated_catalogue_exists_and_parses():
    assert Path(_DUAS_PATH).is_file(), f"missing generated catalogue: {_DUAS_PATH}"
    payload = json.loads(Path(_DUAS_PATH).read_text(encoding="utf-8"))
    assert payload["count"] == len(payload["duas"])


def test_catalogue_holds_every_curated_entry():
    """Guards the 21-of-66 drift that the hand-maintained list had."""
    assert len(_DUAS) >= 66


def test_dua_ids_are_unique():
    ids = [dua["id"] for dua in _DUAS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("field", [
    "id", "surah", "ayah", "category",
    "titleEn", "titleAr", "surahNameEn", "surahNameAr",
    "meaningEn", "meaningAr", "occasions", "tags",
])
def test_every_dua_exposes_the_served_fields(field):
    missing = [dua.get("id", "<no id>") for dua in _DUAS if field not in dua]
    assert not missing, f"duas missing {field!r}: {missing[:5]}"


def test_every_dua_has_an_in_range_quranic_reference():
    for dua in _DUAS:
        assert 1 <= dua["surah"] <= 114, f"{dua['id']}: surah {dua['surah']}"
        assert dua["ayah"] >= 1, f"{dua['id']}: ayah {dua['ayah']}"
        end = dua.get("ayahEnd")
        if end is not None:
            assert end >= dua["ayah"], f"{dua['id']}: ayahEnd precedes ayah"
