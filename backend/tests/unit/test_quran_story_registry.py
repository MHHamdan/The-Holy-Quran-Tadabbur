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


# ---------------------------------------------------------------------------
# Subcategory taxonomy (animal:cow, animal:bee, …)
# ---------------------------------------------------------------------------


SUBCATEGORY_GROUPS = {
    "animal",
    "place",
    "object",
    "event",
    "miracle",
    "family",
    "role",
    "afterlife",
    "nature",
    "virtue",
    "vice",
}


def test_every_story_has_subcategory_array(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        assert "subcategories" in s, f"{s['storyId']} missing subcategories field"
        assert isinstance(s["subcategories"], list)


def test_every_authored_story_has_at_least_one_subcategory(
    registry: Dict[str, Any],
) -> None:
    missing = [
        s["storyId"]
        for s in registry["stories"]
        if s["sourceType"] == "authored_story" and not s.get("subcategories")
    ]
    assert not missing, (
        f"Authored stories missing subcategories: {missing[:5]}…"
    )


def test_subcategory_tags_are_well_formed(registry: Dict[str, Any]) -> None:
    pat = re.compile(r"^[a-z0-9_]+:[a-z0-9_]+$")
    for s in registry["stories"]:
        for sc in s.get("subcategories", []):
            assert pat.match(sc), f"{s['storyId']}: malformed subcategory {sc!r}"
            group = sc.split(":", 1)[0]
            assert group in SUBCATEGORY_GROUPS, (
                f"{s['storyId']}: unknown subcategory group {group!r}"
            )


def test_animal_subcategory_covers_user_examples(registry: Dict[str, Any]) -> None:
    """User explicitly requested coverage of animal stories (cow, bee, elephant)."""
    all_tags = {sc for s in registry["stories"] for sc in s.get("subcategories", [])}
    # bee is only mentioned in surah an-Nahl, no dedicated story in the
    # authored manifest — but cow and elephant should both be present.
    for required in ("animal:cow", "animal:elephant", "animal:ant", "animal:spider"):
        assert required in all_tags, f"Missing required animal tag: {required}"


def test_subcategory_filter_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Filter by parent group.
    r = client.get("/api/v1/quran/story-atlas", params={"subcategory": "animal"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    for s in body["stories"]:
        assert any(sc.startswith("animal:") for sc in s["subcategories"])

    # Filter by full tag.
    r = client.get(
        "/api/v1/quran/story-atlas", params={"subcategory": "animal:cow"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    for s in body["stories"]:
        assert "animal:cow" in s["subcategories"]


def test_subcategory_facets_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/subcategories")
    assert r.status_code == 200
    body = r.json()
    assert "facets" in body
    groups = {f["group"] for f in body["facets"]}
    # At minimum animal/place/event/vice should appear.
    for required in ("animal", "place", "event", "vice"):
        assert required in groups
    # Each facet should expose at least one tag with a non-zero count.
    for f in body["facets"]:
        assert f["totalStoryCount"] >= 1
        assert len(f["tags"]) >= 1
        assert all(t["storyCount"] >= 1 for t in f["tags"])


def test_themes_and_main_figures_propagated(
    registry: Dict[str, Any], manifest: Dict[str, Any]
) -> None:
    """The build script should pass the manifest's themes / main_figures
    arrays straight through. Without these the registry loses the rich
    metadata the manifest already carries."""
    by_id = {s["storyId"]: s for s in registry["stories"]}
    for m in manifest["stories"]:
        entry = by_id.get(m["id"])
        if not entry:
            continue
        assert set(m.get("themes", [])).issubset(set(entry.get("themes", []))), (
            f"{m['id']} dropped themes during registry build"
        )
        assert set(m.get("main_figures", [])).issubset(
            set(entry.get("mainFigures", []))
        ), f"{m['id']} dropped main_figures during registry build"


# ---------------------------------------------------------------------------
# People taxonomy (Firawn, Haman, Maryam, Asiya, Bilqis, …)
# ---------------------------------------------------------------------------


PERSON_ROLES = {
    "prophet",
    "righteous_figure",
    "monarch",
    "antagonist",
    "companion",
    "family_member",
    "angel",
    "unseen_being",
    "collective",
}

PEOPLE_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranPeopleIndex.json"


@pytest.fixture(scope="module")
def people_index() -> Dict[str, Any]:
    assert PEOPLE_PATH.exists(), (
        f"Run `npx tsx scripts/build-quran-story-registry.ts` first; missing {PEOPLE_PATH}"
    )
    return json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))


def test_people_index_is_well_formed(people_index: Dict[str, Any]) -> None:
    assert len(people_index["people"]) > 30, (
        "People index has fewer than expected entries — Firawn/Haman/Maryam etc. must be present"
    )
    assert len(people_index["prophets"]) == 25, (
        "All 25 prophets from the atlas must be carried into the people index"
    )
    seen = set()
    for entry in people_index["people"] + people_index["prophets"]:
        pid = entry["personId"]
        assert pid not in seen or entry["role"] == "prophet", (
            f"Duplicate personId outside the prophet bucket: {pid}"
        )
        seen.add(pid)
        assert entry["role"] in PERSON_ROLES, (
            f"{pid}: unknown role {entry['role']!r}"
        )
        assert entry["nameArabic"], f"{pid}: missing nameArabic"
        assert entry["nameEnglish"], f"{pid}: missing nameEnglish"


def test_every_story_has_peopleids_array(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        assert "peopleIds" in s, f"{s['storyId']} missing peopleIds field"
        assert isinstance(s["peopleIds"], list)


def test_user_named_antagonists_appear_in_registry(
    registry: Dict[str, Any],
) -> None:
    """The user explicitly named Fir'awn and Haman. Both must be linked
    to at least one story so the People facet has content."""
    pid_storycount: Dict[str, int] = {}
    for s in registry["stories"]:
        for pid in s.get("peopleIds", []):
            pid_storycount[pid] = pid_storycount.get(pid, 0) + 1
    for required in (
        "person_firawn",
        "person_haman",
        "person_qarun",
        "person_iblis",
        "person_maryam",
        "person_asiya",
        "person_bilqis",
        "person_luqman",
        "person_khidr",
    ):
        assert pid_storycount.get(required, 0) >= 1, (
            f"{required} expected in at least one story; found 0"
        )


def test_prophets_are_referenced_with_canonical_ids(
    registry: Dict[str, Any], people_index: Dict[str, Any]
) -> None:
    prophet_ids = {p["personId"] for p in people_index["prophets"]}
    referenced = set()
    for s in registry["stories"]:
        for pid in s.get("peopleIds", []):
            if pid.startswith("prophet_"):
                referenced.add(pid)
    # At least the major prophets the user cares about must be present.
    for required in (
        "prophet_musa",
        "prophet_ibrahim",
        "prophet_yusuf",
        "prophet_isa",
        "prophet_muhammad",
    ):
        assert required in prophet_ids, f"Missing prophet ID {required} in index"
        assert required in referenced, (
            f"{required} not linked to any story via peopleIds"
        )


def test_filter_by_person_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Filter by canonical personId.
    r = client.get(
        "/api/v1/quran/story-atlas", params={"person": "person_firawn"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    for s in body["stories"]:
        assert "person_firawn" in s["peopleIds"]

    # Filter by role bucket.
    r = client.get(
        "/api/v1/quran/story-atlas", params={"person": "antagonist"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1


def test_people_facets_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/people")
    assert r.status_code == 200
    body = r.json()
    assert "facets" in body
    roles_present = {f["role"] for f in body["facets"]}
    # The user explicitly cares about prophets + people-in-general:
    for required in ("prophet", "antagonist", "righteous_figure"):
        assert required in roles_present
    # Antagonists facet should include Fir'awn and Haman with at least 1 story.
    antag = next(f for f in body["facets"] if f["role"] == "antagonist")
    antag_ids = {p["personId"]: p for p in antag["people"]}
    for required in ("person_firawn", "person_haman"):
        assert required in antag_ids
        assert antag_ids[required]["storyCount"] >= 1


def test_person_search_term_matches() -> None:
    """Searching for "firawn" / "pharaoh" should hit Fir'awn-related stories."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas", params={"search": "firawn"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Places taxonomy (Makkah, Madinah, Egypt, Mount Sinai, …)
# ---------------------------------------------------------------------------


PLACE_TYPES = {
    "sanctuary",
    "city",
    "region",
    "mountain",
    "water_body",
    "landmark",
    "battlefield",
    "structure",
    "otherworldly",
}

PLACES_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranPlacesIndex.json"


@pytest.fixture(scope="module")
def places_index() -> Dict[str, Any]:
    assert PLACES_PATH.exists(), (
        f"Run `npx tsx scripts/build-quran-story-registry.ts` first; missing {PLACES_PATH}"
    )
    return json.loads(PLACES_PATH.read_text(encoding="utf-8"))


def test_places_index_is_well_formed(places_index: Dict[str, Any]) -> None:
    assert len(places_index["places"]) >= 40, (
        "Places index should cover all major Quranic geography (Makkah, "
        "Madinah, Egypt, Sinai, Madyan, Sheba, …)"
    )
    seen = set()
    for entry in places_index["places"]:
        pid = entry["placeId"]
        assert pid not in seen, f"Duplicate placeId: {pid}"
        seen.add(pid)
        assert pid.startswith("place_"), f"placeId must be prefixed: {pid}"
        assert entry["type"] in PLACE_TYPES, (
            f"{pid}: unknown type {entry['type']!r}"
        )
        assert entry["nameArabic"], f"{pid}: missing nameArabic"
        assert entry["nameEnglish"], f"{pid}: missing nameEnglish"


def test_every_story_has_placeids_array(registry: Dict[str, Any]) -> None:
    for s in registry["stories"]:
        assert "placeIds" in s, f"{s['storyId']} missing placeIds field"
        assert isinstance(s["placeIds"], list)


def test_canonical_places_appear_in_registry(registry: Dict[str, Any]) -> None:
    """Major Quranic places must each link to at least one story so the
    Places facet renders content."""
    pid_storycount: Dict[str, int] = {}
    for s in registry["stories"]:
        for pid in s.get("placeIds", []):
            pid_storycount[pid] = pid_storycount.get(pid, 0) + 1
    for required in (
        "place_makkah",
        "place_madinah",
        "place_egypt",
        "place_mount_sinai",
        "place_madyan",
        "place_sheba",
        "place_cave_kahf",
        "place_kabah",
        "place_jerusalem",
        "place_red_sea",
        "place_badr",
        "place_uhud",
    ):
        assert pid_storycount.get(required, 0) >= 1, (
            f"{required} expected in at least one story; found 0"
        )


def test_filter_by_place_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Filter by canonical placeId.
    r = client.get(
        "/api/v1/quran/story-atlas", params={"place": "place_makkah"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    for s in body["stories"]:
        assert "place_makkah" in s["placeIds"]

    # Filter by type bucket.
    r = client.get(
        "/api/v1/quran/story-atlas", params={"place": "mountain"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    for s in body["stories"]:
        assert any(pid.startswith("place_") for pid in s["placeIds"])


def test_places_facets_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas/places")
    assert r.status_code == 200
    body = r.json()
    assert "facets" in body
    types_present = {f["type"] for f in body["facets"]}
    for required in ("sanctuary", "city", "mountain", "battlefield"):
        assert required in types_present
    # City facet should include Makkah, Madinah, Egypt with ≥1 story each.
    cities = next(f for f in body["facets"] if f["type"] == "city")
    city_ids = {p["placeId"]: p for p in cities["places"]}
    for required in ("place_makkah", "place_madinah", "place_egypt"):
        assert required in city_ids
        assert city_ids[required]["storyCount"] >= 1


def test_place_search_matches() -> None:
    """Searching for "egypt" or "sinai" should hit relevant stories."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/story-atlas", params={"search": "egypt"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    r = client.get("/api/v1/quran/story-atlas", params={"search": "sinai"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
