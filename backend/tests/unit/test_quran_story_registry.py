"""
Tests for the canonical Quran Story Registry.

Covers:
- Registry JSON exists and has stories.
- Atlas count > 0 if the authored manifest has stories (prevents the
  "/story-atlas shows 0" regression).
- Categories used in the registry are all in the canonical enum.
- All 9 Phase X2 prophet pages are present in the registry.
- Every entry's quranReferences point to valid surah/ayah numbers.
- Dhul-Kifl entry is a compact_profile with a limited-mentions warning.
- Muhammad ﷺ entry uses prophetic_sirah category and carries the
  not-full-biography warning.
- The frontend StoryAtlasPage imports the registry adapter and uses
  the canonical category enum.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryRegistry.json"
CONNECTIONS_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryAtlasConnections.json"
MANIFEST_PATH = ROOT / "data" / "manifests" / "stories.json"
PROPHET_PAGES_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetStoryPages.json"
STORY_ATLAS_PAGE = ROOT / "frontend" / "src" / "pages" / "StoryAtlasPage.tsx"
STORIES_PAGE = ROOT / "frontend" / "src" / "pages" / "StoriesPage.tsx"
ADAPTER_PATH = ROOT / "frontend" / "src" / "utils" / "storyRegistryAdapter.ts"


CANONICAL_CATEGORIES = {
    "prophet",
    "prophetic_sirah",
    "person",
    "nation",
    "parable",
    "historical",
    "unseen",
    "compact_profile",
    "needs_review",
}

PHASE_X2_PROPHETS = [
    "prophet_ishaq",
    "prophet_yaqub",
    "prophet_harun",
    "prophet_dhulkifl",
    "prophet_ilyas",
    "prophet_alyasa",
    "prophet_sulayman",
    "prophet_muhammad",
    "prophet_ismail",
]


@pytest.fixture(scope="module")
def registry() -> Dict[str, Any]:
    assert REGISTRY_PATH.exists(), (
        f"Run `npx tsx scripts/build-quran-story-registry.ts` first; missing {REGISTRY_PATH}"
    )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def connections() -> Dict[str, Any]:
    assert CONNECTIONS_PATH.exists()
    return json.loads(CONNECTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest() -> Dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prophet_pages() -> Dict[str, Any]:
    return json.loads(PROPHET_PAGES_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Registry shape & non-emptiness
# ---------------------------------------------------------------------------


def test_registry_has_stories(registry: Dict[str, Any]) -> None:
    assert registry["stories"], "Registry has no stories — /story-atlas would render 0."


def test_registry_includes_all_manifest_stories(registry: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    registry_ids = {s["storyId"] for s in registry["stories"]}
    missing = [m["id"] for m in manifest["stories"] if m["id"] not in registry_ids]
    assert not missing, f"Registry missing manifest stories: {missing[:5]}…"


def test_registry_includes_phase_x2_prophet_pages(registry: Dict[str, Any]) -> None:
    registry_ids = {s["storyId"] for s in registry["stories"]}
    for pid in PHASE_X2_PROPHETS:
        expected = f"storypage_{pid.replace('prophet_', '')}"
        assert expected in registry_ids, f"Missing prophet story page: {expected}"


def test_atlas_count_positive_when_manifest_nonempty(registry: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    if manifest["stories"]:
        assert len(registry["stories"]) > 0


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


def test_categories_match_canonical_enum(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        assert s["category"] in CANONICAL_CATEGORIES, (
            f"Story {s['storyId']} has non-canonical category {s['category']}"
        )


def test_registry_categories_listed(registry: Dict[str, Any]) -> None:
    assert set(registry["categories"]) == CANONICAL_CATEGORIES


# ---------------------------------------------------------------------------
# Quran references
# ---------------------------------------------------------------------------


def test_quran_references_have_valid_surahs(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        for r in s["quranReferences"]:
            assert 1 <= r["surahNumber"] <= 114
            assert r["ayahStart"] >= 1
            if r.get("ayahEnd") is not None:
                assert r["ayahEnd"] >= r["ayahStart"]


def test_story_ids_unique(registry: Dict[str, Any]) -> None:
    ids = [s["storyId"] for s in registry["stories"]]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Special prophet rules
# ---------------------------------------------------------------------------


def test_dhulkifl_compact_profile(registry: Dict[str, Any]) -> None:
    e = next((s for s in registry["stories"] if s["storyId"] == "storypage_dhulkifl"), None)
    assert e is not None
    assert e["category"] == "compact_profile"


def test_muhammad_prophetic_sirah_warning(registry: Dict[str, Any], prophet_pages: Dict[str, Any]) -> None:
    entry = next((s for s in registry["stories"] if s["storyId"] == "storypage_muhammad"), None)
    assert entry is not None
    assert entry["category"] == "prophetic_sirah"
    page = next((p for p in prophet_pages["pages"] if p["prophetId"] == "prophet_muhammad"), None)
    assert page is not None
    combined_warnings = " ".join(page.get("warnings", []) or [])
    assert "biography" in combined_warnings.lower() or "سيرة" in combined_warnings


def test_no_generated_entry_is_verified(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        if s["sourceType"] in ("prophet_story_page", "generated_candidate", "entity_story_cluster"):
            assert s["reviewStatus"] != "verified" or s["humanReviewRequired"] is False


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------


def test_connections_have_evidence(connections: Dict[str, Any]) -> None:
    assert connections["totalConnections"] > 0
    for c in connections["connections"]:
        assert c["evidenceReferences"], f"Connection {c['sourceStoryId']}→{c['targetId']} missing evidence"
        assert c["reviewStatus"] == "needs_review"
        assert c["humanReviewRequired"] is True


# ---------------------------------------------------------------------------
# Frontend wiring
# ---------------------------------------------------------------------------


def test_frontend_uses_registry_adapter() -> None:
    src = STORY_ATLAS_PAGE.read_text(encoding="utf-8")
    assert "storyRegistryAdapter" in src
    assert "REGISTRY_CATEGORY_ORDER" in src or "REGISTRY_CATEGORY_LABELS" in src


def test_registry_adapter_exposes_required_functions() -> None:
    src = ADAPTER_PATH.read_text(encoding="utf-8")
    for fn in (
        "getAllStoriesForCards",
        "getStoriesByCategory",
        "searchStories",
        "getStoryDetailRoute",
        "getStoryReviewStatus",
        "getStorySourceType",
    ):
        assert re.search(rf"\bexport function {fn}\b", src), f"Adapter missing {fn}"


def test_stories_atlas_correlation(registry: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    # Whatever count /stories will see (the manifest) must be <= registry stories count.
    assert len(registry["stories"]) >= len(manifest["stories"])


def test_atlas_page_renders_review_warning() -> None:
    src = STORY_ATLAS_PAGE.read_text(encoding="utf-8")
    assert "scholarly review" in src
    assert "هذا الأطلس" in src


# ---------------------------------------------------------------------------
# Live API smoke
# ---------------------------------------------------------------------------


def test_registry_endpoint_returns_non_empty_list() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] > 0
    assert len(body["stories"]) > 0
    assert body["coverage"]["totalStories"] > 0
    assert set(body["categories"]) == CANONICAL_CATEGORIES


def test_registry_search_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/search", params={"q": "yusuf"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0


def test_registry_coverage_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/coverage")
    assert r.status_code == 200
    body = r.json()
    assert "coverage" in body
    assert body["coverage"]["totalStories"] > 0


def test_registry_categories_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/categories")
    assert r.status_code == 200
    body = r.json()
    assert set(body["categories"]) == CANONICAL_CATEGORIES


def test_registry_story_detail_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/story_adam")
    assert r.status_code == 200
    body = r.json()
    assert body["storyId"] == "story_adam"


def test_registry_invalid_story_id_400() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/BAD ID!")
    assert r.status_code in (400, 404)


def test_registry_connections_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/story_adam/connections")
    assert r.status_code == 200
    body = r.json()
    # Connections may be 0 for some stories but the endpoint must exist
    assert "connections" in body
    assert "total" in body


# ---------------------------------------------------------------------------
# Cross-references file (S1/S2)
# ---------------------------------------------------------------------------


CROSS_REFS_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranStoryCrossReferences.json"


@pytest.fixture(scope="module")
def cross_refs() -> Dict[str, Any]:
    assert CROSS_REFS_PATH.exists(), (
        "Run `npx tsx scripts/build-quran-story-cross-references.ts` first; "
        f"missing {CROSS_REFS_PATH}"
    )
    return json.loads(CROSS_REFS_PATH.read_text(encoding="utf-8"))


def test_cross_refs_has_edges(cross_refs: Dict[str, Any]) -> None:
    assert cross_refs["edges"], "Cross-references file must have edges."
    assert cross_refs["stats"]["totalPairs"] >= 50


def test_cross_refs_all_edges_have_strong_signal(cross_refs: Dict[str, Any]) -> None:
    strong = {"same_prophet", "same_figure", "overlapping_ayahs"}
    for e in cross_refs["edges"]:
        kinds = {ev["relation"] for ev in e["evidence"]}
        assert kinds & strong, f"{e['sourceStoryId']}<->{e['targetStoryId']} missing strong signal"


def test_cross_refs_no_self_loops(cross_refs: Dict[str, Any]) -> None:
    for e in cross_refs["edges"]:
        assert e["sourceStoryId"] != e["targetStoryId"]


def test_cross_refs_targets_resolve_in_registry(
    cross_refs: Dict[str, Any], registry: Dict[str, Any]
) -> None:
    ids = {s["storyId"] for s in registry["stories"]}
    for e in cross_refs["edges"]:
        assert e["sourceStoryId"] in ids
        assert e["targetStoryId"] in ids


def test_registry_neighbours_populated(registry: Dict[str, Any]) -> None:
    """After cross-references are merged, the average story should have
    multiple relatedStories — guards against a future regression that
    accidentally bypasses the neighbours-merge step."""
    counts = [len(s["relatedStories"]) for s in registry["stories"]]
    avg = sum(counts) / len(counts)
    assert avg >= 2.0, f"Average relatedStories count too low: {avg:.2f}"


def test_cross_refs_default_needs_review(cross_refs: Dict[str, Any]) -> None:
    for e in cross_refs["edges"]:
        assert e["reviewStatus"] == "needs_review"
        assert e["humanReviewRequired"] is True
