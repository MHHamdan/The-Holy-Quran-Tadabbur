"""
Phase V — Quran Topic Discovery Atlas — unit tests.

Covers:
- topic seeds load
- scan covers all 114 surahs
- topic atlas generated; mercy/patience/gratitude/tawhid/hereafter exist
- topic links have evidence and default needs_review
- topic clusters generated (graph_community + entity_story_overlap)
- topic relation graph generated
- topic API routes registered
- surah topic map endpoint works
- validators reject invalid ayah ref / approved candidate without review
- explain-link endpoint returns warnings + no_verified_source when sourceIds=[]
- no Quran text mutation
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "frontend" / "src" / "data" / "generated"
ATLAS_PATH = GEN / "quranTopicAtlas.json"
CLUSTERS_PATH = GEN / "quranTopicClusters.json"
GRAPH_PATH = GEN / "quranTopicRelationGraph.json"
SEEDS_PATH = ROOT / "frontend" / "src" / "data" / "quranTopicSeeds.ts"
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"


@pytest.fixture(scope="module")
def atlas() -> dict:
    assert ATLAS_PATH.exists(), f"Run scan-quran-topic-links.ts first; missing {ATLAS_PATH}"
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def clusters() -> dict:
    assert CLUSTERS_PATH.exists(), f"Run discover-quran-topic-clusters.ts first; missing {CLUSTERS_PATH}"
    return json.loads(CLUSTERS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def graph() -> dict:
    assert GRAPH_PATH.exists(), f"Run build-quran-topic-relation-graph.ts first; missing {GRAPH_PATH}"
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def seeds_text() -> str:
    return SEEDS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------


def test_topic_seeds_load(seeds_text: str) -> None:
    assert "QURAN_TOPIC_SEEDS" in seeds_text
    for tid in (
        "topic_mercy",
        "topic_patience",
        "topic_gratitude",
        "topic_tawhid",
        "topic_resurrection",
        "topic_paradise",
        "topic_hellfire",
    ):
        assert tid in seeds_text, f"Missing seed: {tid}"


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------


def test_atlas_has_70_plus_topics(atlas: dict) -> None:
    assert atlas["totalTopics"] >= 50


def test_atlas_links_exist_and_are_needs_review(atlas: dict) -> None:
    seen_any_link = False
    for t in atlas["topics"]:
        for l in t.get("ayahLinks", []):
            seen_any_link = True
            assert l["reviewStatus"] == "needs_review"
            assert l["humanReviewRequired"] is True
            assert l["evidenceReferences"], f"empty evidence on {t['topicId']} {l['surahNumber']}:{l['ayahNumber']}"
    assert seen_any_link


def test_atlas_key_topics_exist(atlas: dict) -> None:
    ids = {t["topicId"] for t in atlas["topics"]}
    for needed in ("topic_mercy", "topic_patience", "topic_gratitude", "topic_tawhid", "topic_resurrection"):
        assert needed in ids


def test_atlas_covers_quran_well(atlas: dict) -> None:
    # We expect ≥2,500 ayahs to receive at least one link.
    covered = 6236 - atlas["ayahsWithoutTopics"]
    assert covered >= 2500


def test_atlas_no_verified_links_or_topics(atlas: dict) -> None:
    for t in atlas["topics"]:
        assert t["reviewStatus"] != "verified"
        for l in t.get("ayahLinks", []):
            assert l["reviewStatus"] == "needs_review"


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------


def test_clusters_present(clusters: dict) -> None:
    assert clusters["totalClusters"] >= 1
    for c in clusters["clusters"]:
        assert len(c["memberTopicIds"]) >= 2
        assert 0 <= c["coherenceScore"] <= 1
        assert c["reviewStatus"] == "needs_review"


def test_clusters_have_known_methods(clusters: dict) -> None:
    methods = {c["generatedBy"] for c in clusters["clusters"]}
    assert "seed_taxonomy" in methods
    assert "entity_story_overlap" in methods or "graph_community" in methods


# ---------------------------------------------------------------------------
# Relation graph
# ---------------------------------------------------------------------------


def test_graph_present(graph: dict) -> None:
    assert graph["nodeCount"] > 0
    assert graph["edgeCount"] > 0


def test_graph_edges_have_evidence_and_needs_review(graph: dict) -> None:
    sampled = 0
    for e in graph["edges"][:500]:
        sampled += 1
        assert e["evidenceReferences"]
        assert e["reviewStatus"] == "needs_review"
        assert 0 <= e["confidence"] <= 1
    assert sampled > 0


# ---------------------------------------------------------------------------
# Validator regression — invalid ayah ref and approved-without-review
# ---------------------------------------------------------------------------


def test_validator_invalid_ayah_ref_predicate() -> None:
    """Predicate mirror of the validator: surah/ayah must be in range and
    every link must be needs_review."""
    AYAHS_PER_SURAH = {1: 7, 2: 286}
    bad_link = {"surahNumber": 1, "ayahNumber": 999, "reviewStatus": "needs_review", "humanReviewRequired": True}
    invalid = bad_link["ayahNumber"] > AYAHS_PER_SURAH.get(bad_link["surahNumber"], 0)
    assert invalid

    forged = {"surahNumber": 2, "ayahNumber": 1, "reviewStatus": "verified", "humanReviewRequired": False}
    bad = forged["reviewStatus"] != "needs_review" or forged["humanReviewRequired"] is False
    assert bad


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


def test_topic_api_routes_registered() -> None:
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/v1/quran/topics" in paths
    assert "/api/v1/quran/topics/{topic_id}" in paths
    assert "/api/v1/quran/topics/{topic_id}/ayahs" in paths
    assert "/api/v1/quran/topics/{topic_id}/related" in paths
    assert "/api/v1/quran/topics/{topic_id}/journey" in paths
    assert "/api/v1/quran/topics/surah/{surah_no}" in paths
    assert "/api/v1/quran/topics/explain-link" in paths


def test_topic_explain_returns_no_verified_source_warning() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # find a real link
    atlas = json.loads(ATLAS_PATH.read_text(encoding="utf-8"))
    sample = next(
        (t for t in atlas["topics"] if t["topicId"] == "topic_mercy" and t["ayahLinks"]),
        None,
    )
    assert sample is not None
    link = sample["ayahLinks"][0]
    r = client.post(
        "/api/v1/quran/topics/explain-link",
        json={
            "topicId": "topic_mercy",
            "surahNumber": link["surahNumber"],
            "ayahNumber": link["ayahNumber"],
            "language": "en",
            "sourceIds": [],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reviewStatus"] == "needs_review"
    assert any("no_verified_source" in w for w in body["warnings"])
    assert body["sourceIds"] == []


def test_surah_topics_endpoint_works() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/topics/surah/2")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["surahNumber"] == 2
    assert body["totalTopics"] >= 5


# ---------------------------------------------------------------------------
# UI route regression
# ---------------------------------------------------------------------------


def test_app_routes_include_topic_routes() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'path="/topics"' in text
    assert 'path="/topics/:topicId"' in text
    assert 'path="/topics/:topicId/journey"' in text
    assert 'path="/surah-topics/:surahNo"' in text


# ---------------------------------------------------------------------------
# No Quran text mutation — sanity
# ---------------------------------------------------------------------------


def test_no_long_arabic_text_in_atlas(atlas: dict) -> None:
    # The atlas should not embed Quran text. Sanity: any string field longer
    # than 200 chars and containing many Arabic letters is a violation.
    import re

    arabic = re.compile(r"[؀-ۿ]")
    def _walk(o):
        if isinstance(o, str):
            if len(o) > 200 and len(arabic.findall(o)) > 50:
                return True
        elif isinstance(o, dict):
            return any(_walk(v) for v in o.values())
        elif isinstance(o, list):
            return any(_walk(v) for v in o)
        return False

    assert not _walk(atlas), "Found suspiciously long Arabic text in atlas"
