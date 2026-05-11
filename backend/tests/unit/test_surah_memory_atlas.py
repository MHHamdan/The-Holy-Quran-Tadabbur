"""
Surah Memory Atlas — Validation Tests

Tests the generated surahMemoryAtlas.json against verified Quran data
and validates all structural/content requirements.

These tests run against the static generated file; no API calls needed.
"""
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
ATLAS_PATH = os.path.join(ROOT, 'frontend/src/data/generated/surahMemoryAtlas.json')
QURAN_PATH = os.path.join(ROOT, 'data/raw/quran_uthmani.json')
SOURCE_REGISTRY_PATH = os.path.join(ROOT, 'frontend/src/data/sourceRegistry.ts')


@pytest.fixture(scope='module')
def atlas():
    assert os.path.exists(ATLAS_PATH), f'Atlas file not found: {ATLAS_PATH}'
    with open(ATLAS_PATH) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def quran_data():
    assert os.path.exists(QURAN_PATH), f'Quran file not found: {QURAN_PATH}'
    with open(QURAN_PATH) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def ground_truth(quran_data):
    """Build per-surah ground truth from verified Quran data."""
    surahs = {}
    for ayah in quran_data:
        s = ayah['sura_no']
        if s not in surahs:
            surahs[s] = {
                'ayah_count': 0,
                'pages': set(),
                'juzs': set(),
                'first_ayah_text': None,
                'last_ayah_text': None,
                'ayahs': {},
            }
        surahs[s]['ayah_count'] += 1
        if ayah.get('page'):
            surahs[s]['pages'].add(ayah['page'])
        if ayah.get('jozz'):
            surahs[s]['juzs'].add(ayah['jozz'])
        surahs[s]['ayahs'][ayah['aya_no']] = ayah['aya_text']

    for s in surahs:
        count = surahs[s]['ayah_count']
        surahs[s]['first_ayah_text'] = surahs[s]['ayahs'].get(1)
        surahs[s]['last_ayah_text'] = surahs[s]['ayahs'].get(count)

    return surahs


@pytest.fixture(scope='module')
def known_source_ids():
    assert os.path.exists(SOURCE_REGISTRY_PATH)
    with open(SOURCE_REGISTRY_PATH) as f:
        content = f.read()
    return set(re.findall(r"sourceId:\s*'([^']+)'", content))


@pytest.fixture(scope='module')
def surahs(atlas):
    return atlas['surahs']


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------

def test_atlas_has_required_top_level_fields(atlas):
    assert 'version' in atlas
    assert 'generatedAt' in atlas
    assert 'totalSurahs' in atlas
    assert 'surahs' in atlas
    assert isinstance(atlas['surahs'], list)


def test_atlas_has_exactly_114_surahs(surahs):
    assert len(surahs) == 114, f'Expected 114 surahs, got {len(surahs)}'


def test_total_surahs_matches_list_length(atlas, surahs):
    assert atlas['totalSurahs'] == len(surahs)


def test_surah_numbers_are_1_to_114(surahs):
    numbers = [s['surahNumber'] for s in surahs]
    assert sorted(numbers) == list(range(1, 115))


def test_no_duplicate_surah_numbers(surahs):
    numbers = [s['surahNumber'] for s in surahs]
    assert len(numbers) == len(set(numbers))


# ---------------------------------------------------------------------------
# Required field presence
# ---------------------------------------------------------------------------

def test_all_surahs_have_arabic_name(surahs):
    for s in surahs:
        assert s.get('nameArabic'), f'Surah {s["surahNumber"]}: missing nameArabic'


def test_all_surahs_have_transliteration(surahs):
    for s in surahs:
        assert s.get('nameTransliteration'), f'Surah {s["surahNumber"]}: missing nameTransliteration'


def test_all_surahs_have_ayah_count_positive(surahs):
    for s in surahs:
        assert s['ayahCount'] > 0, f'Surah {s["surahNumber"]}: ayahCount must be > 0'


# ---------------------------------------------------------------------------
# Revelation type
# ---------------------------------------------------------------------------

VALID_REVELATION_TYPES = {'makki', 'madani', 'unknown'}

def test_all_revelation_types_valid(surahs):
    for s in surahs:
        assert s['revelationType'] in VALID_REVELATION_TYPES, \
            f'Surah {s["surahNumber"]}: invalid revelationType "{s["revelationType"]}"'


def test_al_fatiha_is_makki(surahs):
    s1 = next(s for s in surahs if s['surahNumber'] == 1)
    assert s1['revelationType'] == 'makki'


def test_al_baqara_is_madani(surahs):
    s2 = next(s for s in surahs if s['surahNumber'] == 2)
    assert s2['revelationType'] == 'madani'


# ---------------------------------------------------------------------------
# Length category
# ---------------------------------------------------------------------------

VALID_LENGTHS = {'short', 'medium', 'long', 'very_long'}

def test_all_length_categories_valid(surahs):
    for s in surahs:
        assert s['lengthCategory'] in VALID_LENGTHS


def test_length_category_matches_ayah_count(surahs):
    for s in surahs:
        n = s['ayahCount']
        expected = (
            'short' if n <= 20
            else 'medium' if n <= 80
            else 'long' if n <= 180
            else 'very_long'
        )
        assert s['lengthCategory'] == expected, \
            f'Surah {s["surahNumber"]}: lengthCategory mismatch (ayahs={n}, expected={expected}, got={s["lengthCategory"]})'


# ---------------------------------------------------------------------------
# Quran position
# ---------------------------------------------------------------------------

VALID_POSITIONS = {'beginning', 'early', 'middle', 'late', 'ending'}

def test_all_positions_valid(surahs):
    for s in surahs:
        assert s['quranPosition'] in VALID_POSITIONS


def test_position_matches_surah_number(surahs):
    for s in surahs:
        n = s['surahNumber']
        expected = (
            'beginning' if n <= 10
            else 'early' if n <= 30
            else 'middle' if n <= 70
            else 'late' if n <= 100
            else 'ending'
        )
        assert s['quranPosition'] == expected, \
            f'Surah {s["surahNumber"]}: position mismatch (expected={expected}, got={s["quranPosition"]})'


# ---------------------------------------------------------------------------
# Ayah count matches ground truth
# ---------------------------------------------------------------------------

def test_ayah_counts_match_quran_data(surahs, ground_truth):
    for s in surahs:
        gt = ground_truth[s['surahNumber']]
        assert s['ayahCount'] == gt['ayah_count'], \
            f'Surah {s["surahNumber"]}: ayahCount {s["ayahCount"]} != Quran data {gt["ayah_count"]}'


# ---------------------------------------------------------------------------
# Page range matches ground truth
# ---------------------------------------------------------------------------

def test_page_ranges_match_quran_data(surahs, ground_truth):
    for s in surahs:
        gt = ground_truth[s['surahNumber']]
        if not gt['pages']:
            continue
        expected_start = min(gt['pages'])
        expected_end = max(gt['pages'])
        assert s['pageStart'] == expected_start, \
            f'Surah {s["surahNumber"]}: pageStart {s["pageStart"]} != {expected_start}'
        assert s['pageEnd'] == expected_end, \
            f'Surah {s["surahNumber"]}: pageEnd {s["pageEnd"]} != {expected_end}'


def test_no_impossible_page_values(surahs):
    for s in surahs:
        assert s['pageStart'] > 0
        assert s['pageEnd'] >= s['pageStart']
        assert s['pageEnd'] <= 604  # Mushaf Al-Madinah has 604 pages


# ---------------------------------------------------------------------------
# Juz range matches ground truth
# ---------------------------------------------------------------------------

def test_juz_ranges_match_quran_data(surahs, ground_truth):
    for s in surahs:
        gt = ground_truth[s['surahNumber']]
        if not gt['juzs']:
            continue
        expected_start = min(gt['juzs'])
        expected_end = max(gt['juzs'])
        assert s['juzStart'] == expected_start
        assert s['juzEnd'] == expected_end


def test_no_impossible_juz_values(surahs):
    for s in surahs:
        assert 1 <= s['juzStart'] <= 30
        assert 1 <= s['juzEnd'] <= 30
        assert s['juzEnd'] >= s['juzStart']


# ---------------------------------------------------------------------------
# Ayah references
# ---------------------------------------------------------------------------

def test_first_ayah_refs_are_valid(surahs):
    for s in surahs:
        expected = f'{s["surahNumber"]}:1'
        assert s['firstAyahRef'] == expected, \
            f'Surah {s["surahNumber"]}: firstAyahRef "{s["firstAyahRef"]}" != "{expected}"'


def test_last_ayah_refs_are_valid(surahs):
    for s in surahs:
        expected = f'{s["surahNumber"]}:{s["ayahCount"]}'
        assert s['lastAyahRef'] == expected


# ---------------------------------------------------------------------------
# Ayah previews match ground truth
# ---------------------------------------------------------------------------

def test_first_ayah_previews_match_quran_data(surahs, ground_truth):
    for s in surahs:
        if s.get('firstAyahPreview') is None:
            continue
        gt = ground_truth[s['surahNumber']]
        assert s['firstAyahPreview'] == gt['first_ayah_text'], \
            f'Surah {s["surahNumber"]}: firstAyahPreview does not match Quran data'


def test_last_ayah_previews_match_quran_data(surahs, ground_truth):
    for s in surahs:
        if s.get('lastAyahPreview') is None:
            continue
        gt = ground_truth[s['surahNumber']]
        assert s['lastAyahPreview'] == gt['last_ayah_text'], \
            f'Surah {s["surahNumber"]}: lastAyahPreview does not match Quran data'


# ---------------------------------------------------------------------------
# Source IDs
# ---------------------------------------------------------------------------

def test_all_source_ids_are_known(surahs, known_source_ids):
    for s in surahs:
        for sid in s.get('sourceIds', []):
            assert sid in known_source_ids, \
                f'Surah {s["surahNumber"]}: unknown sourceId "{sid}"'


def test_all_surahs_have_at_least_one_source(surahs):
    for s in surahs:
        assert len(s.get('sourceIds', [])) >= 1, \
            f'Surah {s["surahNumber"]}: no sourceIds'


# ---------------------------------------------------------------------------
# Review status
# ---------------------------------------------------------------------------

VALID_STATUSES = {'verified', 'needs_review', 'missing_metadata'}

def test_all_review_statuses_valid(surahs):
    for s in surahs:
        assert s['reviewStatus'] in VALID_STATUSES, \
            f'Surah {s["surahNumber"]}: invalid reviewStatus "{s["reviewStatus"]}"'


# ---------------------------------------------------------------------------
# Array fields
# ---------------------------------------------------------------------------

def test_array_fields_are_arrays(surahs):
    for s in surahs:
        n = s['surahNumber']
        assert isinstance(s['mainTopicsArabic'], list), f'Surah {n}: mainTopicsArabic not a list'
        assert isinstance(s['mainTopicsEnglish'], list), f'Surah {n}: mainTopicsEnglish not a list'
        assert isinstance(s['relatedStories'], list), f'Surah {n}: relatedStories not a list'
        assert isinstance(s['relatedThemes'], list), f'Surah {n}: relatedThemes not a list'
        assert isinstance(s['sourceIds'], list), f'Surah {n}: sourceIds not a list'


# ---------------------------------------------------------------------------
# Missing metadata safety
# ---------------------------------------------------------------------------

def test_no_topics_or_clues_claimed_as_verified(surahs):
    """Topics and clues are not yet sourced — they must be absent or empty."""
    for s in surahs:
        assert s['mainTopicsArabic'] == [], \
            f'Surah {s["surahNumber"]}: mainTopicsArabic should be empty until sourced'
        assert s['mainTopicsEnglish'] == [], \
            f'Surah {s["surahNumber"]}: mainTopicsEnglish should be empty until sourced'


# ---------------------------------------------------------------------------
# Known values sanity check
# ---------------------------------------------------------------------------

def test_al_baqara_has_286_ayahs(surahs):
    s2 = next(s for s in surahs if s['surahNumber'] == 2)
    assert s2['ayahCount'] == 286


def test_al_ikhlas_has_4_ayahs(surahs):
    s112 = next(s for s in surahs if s['surahNumber'] == 112)
    assert s112['ayahCount'] == 4


def test_al_baqara_spans_juz_1_to_3(surahs):
    s2 = next(s for s in surahs if s['surahNumber'] == 2)
    assert s2['juzStart'] == 1
    assert s2['juzEnd'] == 3


def test_al_fatiha_is_on_page_1(surahs):
    s1 = next(s for s in surahs if s['surahNumber'] == 1)
    assert s1['pageStart'] == 1
    assert s1['pageEnd'] == 1


def test_all_114_surahs_have_english_name(surahs):
    for s in surahs:
        assert s.get('nameEnglish'), f'Surah {s["surahNumber"]}: missing English name'
