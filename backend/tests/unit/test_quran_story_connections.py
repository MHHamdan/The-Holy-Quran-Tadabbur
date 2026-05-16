"""
Whole-Quran Story Connection Atlas — validation tests.

Validates the generated scan + connection-graph outputs and the seed
dictionaries used to produce them.

These tests run against the static generated JSON files; no API calls and no
Quran-text mutation.
"""
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SCAN_PATH = os.path.join(ROOT, 'frontend/src/data/generated/quranStoryConnections.json')
GRAPH_PATH = os.path.join(ROOT, 'frontend/src/data/generated/quranStoryConnectionGraph.json')
SEEDS_PATH = os.path.join(ROOT, 'frontend/src/data/quranStoryEntitySeeds.ts')
CHRONO_PATH = os.path.join(ROOT, 'frontend/src/data/quranStoryChronologySeeds.ts')
QURAN_PATH = os.path.join(ROOT, 'data/raw/quran_uthmani.json')
APP_PATH = os.path.join(ROOT, 'frontend/src/App.tsx')


@pytest.fixture(scope='module')
def scan():
    assert os.path.exists(SCAN_PATH), f'Run scan-quran-story-connections.ts first; missing {SCAN_PATH}'
    with open(SCAN_PATH) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def graph():
    assert os.path.exists(GRAPH_PATH), f'Run build-quran-story-connection-graph.ts first; missing {GRAPH_PATH}'
    with open(GRAPH_PATH) as f:
        return json.load(f)


@pytest.fixture(scope='module')
def seeds_text():
    with open(SEEDS_PATH, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture(scope='module')
def chrono_text():
    with open(CHRONO_PATH, 'r', encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Scan output
# ---------------------------------------------------------------------------

def test_scan_covers_all_114_surahs(scan):
    assert scan['scannedSurahs'] == 114
    assert len(scan['surahs']) == 114
    surah_numbers = sorted(s['surahNumber'] for s in scan['surahs'])
    assert surah_numbers == list(range(1, 115))


def test_scan_no_quran_text_embedded(scan):
    raw = json.dumps(scan, ensure_ascii=False)
    for forbidden in ('aya_text', 'text_uthmani', 'arabicText'):
        assert f'"{forbidden}"' not in raw, f'Field "{forbidden}" leaked into scan output'


def test_scan_detects_key_prophets(scan):
    """Musa, Ibrahim, Maryam, Yusuf, Nuh should all appear across multiple surahs."""
    ent_by_id = {e['entityId']: e for e in scan['entityIndex']}
    multi_surah = {}
    for eid, entry in ent_by_id.items():
        multi_surah[eid] = len({o['surahNumber'] for o in entry['occurrences']})

    # Musa is mentioned in dozens of surahs; require at least 20 to catch
    # regressions if normalisation breaks.
    assert multi_surah.get('entity_prophet_musa', 0) >= 20, f"musa surah count={multi_surah.get('entity_prophet_musa')}"
    assert multi_surah.get('entity_prophet_ibrahim', 0) >= 15
    assert multi_surah.get('entity_prophet_nuh', 0) >= 15
    assert multi_surah.get('entity_prophet_yusuf', 0) >= 1
    assert multi_surah.get('entity_person_maryam', 0) >= 5
    assert multi_surah.get('entity_person_firawn', 0) >= 15


def test_scan_entity_ids_match_seeds(scan, seeds_text):
    seed_ids = set(re.findall(r"entityId: '([a-z_0-9]+)'", seeds_text))
    assert seed_ids, 'No entity IDs parsed from seeds file'
    for ent in scan['entityIndex']:
        assert ent['entityId'] in seed_ids, f'Entity {ent["entityId"]} not in seeds'


def test_scan_occurrences_valid_ayah_refs(scan):
    """Every ayah ref must be inside 1..ayahs-per-surah."""
    quran = json.load(open(QURAN_PATH, encoding='utf-8'))
    per_surah_max = {}
    for ayah in quran:
        s = ayah['sura_no']
        per_surah_max[s] = max(per_surah_max.get(s, 0), ayah['aya_no'])
    for ent in scan['entityIndex']:
        for occ in ent['occurrences']:
            assert 1 <= occ['surahNumber'] <= 114
            assert 1 <= occ['ayahStart'] <= per_surah_max[occ['surahNumber']]


def test_scan_cross_surah_links_min(scan):
    """At least 20 cross-surah links should exist — proves the cross-surah
    aggregation actually runs and is not empty."""
    assert len(scan['crossSurahLinks']) >= 20
    for cs in scan['crossSurahLinks']:
        assert len(cs['surahNumbers']) >= 2
        assert cs['reviewStatus'] == 'needs_review'


def test_scan_unmapped_candidates_listed(scan):
    """The scan should surface unmapped cluster candidates so reviewers know
    what to look at."""
    assert isinstance(scan['unmappedClusterCandidateIds'], list)


# ---------------------------------------------------------------------------
# Graph output
# ---------------------------------------------------------------------------

def test_graph_node_edge_counts_consistent(graph):
    assert graph['nodeCount'] == len(graph['nodes'])
    assert graph['edgeCount'] == len(graph['edges'])
    assert graph['nodeCount'] > 0
    assert graph['edgeCount'] > 0


def test_graph_every_edge_has_evidence(graph):
    for edge in graph['edges']:
        assert edge['evidenceReferences'], f'Edge {edge["edgeId"]} missing evidence'
        for ev in edge['evidenceReferences']:
            assert ev.get('sourceIds'), f'Edge {edge["edgeId"]} evidence missing sourceIds'
            assert all(isinstance(s, str) and s for s in ev['sourceIds'])


def test_graph_endpoint_integrity(graph):
    node_ids = {n['id'] for n in graph['nodes']}
    for edge in graph['edges']:
        assert edge['sourceNodeId'] in node_ids, f"src {edge['sourceNodeId']} missing"
        assert edge['targetNodeId'] in node_ids, f"tgt {edge['targetNodeId']} missing"


def test_graph_no_quran_text_embedded(graph):
    raw = json.dumps(graph, ensure_ascii=False)
    for forbidden in ('aya_text', 'text_uthmani', 'arabicText'):
        assert f'"{forbidden}"' not in raw


def test_graph_no_verified_without_review(graph):
    """No 'verified' edge may have humanReviewRequired=true or be backed only
    by needs_review evidence."""
    for edge in graph['edges']:
        if edge['reviewStatus'] == 'verified':
            assert edge['humanReviewRequired'] is False
            assert any(ev.get('evidenceType') != 'needs_review' for ev in edge['evidenceReferences'])


def test_graph_contains_chronology_nodes(graph):
    """At least the broad chronology bands should be present as nodes."""
    types = [n['type'] for n in graph['nodes']]
    assert types.count('chronology_group') >= 5


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------

def test_seeds_contain_critical_entities(seeds_text):
    """The seed dictionary must enumerate prophets, persons, peoples, animals,
    places, and objects/events covered by the implementation plan."""
    must_have = [
        # prophets
        "'entity_prophet_musa'", "'entity_prophet_ibrahim'", "'entity_prophet_yusuf'",
        "'entity_prophet_nuh'", "'entity_prophet_isa'", "'entity_prophet_muhammad'",
        # persons
        "'entity_person_maryam'", "'entity_person_firawn'", "'entity_person_qarun'",
        # peoples
        "'entity_people_bani_israel'", "'entity_people_aad'", "'entity_people_thamud'",
        # animals
        "'entity_animal_baqarah'", "'entity_animal_naqah'", "'entity_animal_hoopoe'",
        # places
        "'entity_place_makkah'", "'entity_place_egypt'", "'entity_place_sinai'",
        # objects / events
        "'entity_object_ark'", "'entity_event_flood'", "'entity_event_fire_ibrahim'",
    ]
    missing = [m for m in must_have if m not in seeds_text]
    assert not missing, f'Missing seeds: {missing}'


def test_seeds_no_quran_text_block(seeds_text):
    """No multi-line Arabic Quran text should be embedded — only short labels."""
    # heuristic: reject any line with more than 60 contiguous Arabic chars
    for line in seeds_text.splitlines():
        arabic_run = re.search(r'[؀-ۿ]{60,}', line)
        assert arabic_run is None, f'Line embeds large Arabic block: {line[:80]}'


# ---------------------------------------------------------------------------
# Chronology
# ---------------------------------------------------------------------------

def test_chronology_has_story_world_groups(chrono_text):
    must_have = ['chrono_primordial', 'chrono_patriarchs', 'chrono_israelite', 'chrono_late_israelite']
    for m in must_have:
        assert m in chrono_text, f'Chronology missing group {m}'


def test_chronology_revelation_disclaimer_present(chrono_text):
    assert 'هذا الترتيب تقريبي' in chrono_text
    assert 'requires review' in chrono_text


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

def test_story_atlas_connections_route_registered():
    """The /story-atlas/connections route must be wired into App.tsx."""
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        text = f.read()
    assert 'StoryAtlasConnectionsPage' in text
    assert '/story-atlas/connections' in text


# ---------------------------------------------------------------------------
# Quran integrity (light cross-check)
# ---------------------------------------------------------------------------

def test_quran_data_not_modified():
    """Ensure the canonical Quran data still has 6236 ayahs and 114 surahs."""
    quran = json.load(open(QURAN_PATH, encoding='utf-8'))
    assert len(quran) == 6236
    assert len({a['sura_no'] for a in quran}) == 114
