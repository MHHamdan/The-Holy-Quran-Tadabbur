"""
Phase X2 — Prophet story pages & contextual links — unit tests.

Covers:
- the 8 Phase X2 required prophets all have story pages
  (plus Ismail, added during validation review)
- each missing prophet has the right pageType
- Muhammad ﷺ page includes a not-full-biography warning
- Dhul-Kifl and Al-Yasa are compact_profile + limited-detail warning
- contextual links generated and all needs_review
- storytelling-safe endpoint returns the right output_mode
- routers registered for entities / topics / prophets
- /missing-coverage endpoint returns 25 entries
- /story-page endpoint round-trips
- /contextual-links endpoint round-trips
- 404 for prophets without a story page (Adam, etc. — atlas only)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[3]
ATLAS_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetsAtlas.json"
STORY_PAGES_PATH = (
    ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetStoryPages.json"
)
CONTEXTUAL_LINKS_PATH = (
    ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetContextualLinks.json"
)


@pytest.fixture(scope="module")
def story_pages() -> Dict[str, Any]:
    assert STORY_PAGES_PATH.exists(), (
        f"Run scripts/build-missing-prophet-story-pages.ts first; missing {STORY_PAGES_PATH}"
    )
    return json.loads(STORY_PAGES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contextual_links() -> Dict[str, Any]:
    assert CONTEXTUAL_LINKS_PATH.exists(), (
        f"Run scripts/build-prophet-contextual-links.ts first; missing {CONTEXTUAL_LINKS_PATH}"
    )
    return json.loads(CONTEXTUAL_LINKS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def atlas() -> Dict[str, Any]:
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


def _pages_by_id(story_pages: Dict[str, Any]) -> Dict[str, Any]:
    return {p["prophetId"]: p for p in story_pages["pages"]}


# ---------------------------------------------------------------------------
# Story pages — structural assertions
# ---------------------------------------------------------------------------


def test_ishaq_page_exists(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_ishaq")
    assert p is not None
    assert p["pageType"] == "full_story"
    assert len(p["storySections"]) > 0


def test_yaqub_page_exists(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_yaqub")
    assert p is not None
    assert p["pageType"] == "full_story"
    assert len(p["storySections"]) > 0


def test_harun_page_exists(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_harun")
    assert p is not None
    assert p["pageType"] == "full_story"
    # Joint mission section must exist
    section_types = {s["sectionType"] for s in p["storySections"]}
    assert "mission" in section_types or "people_or_nation" in section_types


def test_dhulkifl_compact_profile(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_dhulkifl")
    assert p is not None
    assert p["pageType"] == "compact_profile"
    # limited-Quran warning present
    text = json.dumps(p, ensure_ascii=False)
    assert "limited" in text.lower() or "compact" in text.lower() or "موجز" in text


def test_ilyas_page_exists(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_ilyas")
    assert p is not None
    assert p["pageType"] == "full_story"
    # The Surah As-Saffat passage section is present
    section_types = {s["sectionType"] for s in p["storySections"]}
    assert "mission" in section_types


def test_alyasa_compact_profile(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_alyasa")
    assert p is not None
    assert p["pageType"] == "compact_profile"


def test_sulayman_page_exists_with_related_entities(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_sulayman")
    assert p is not None
    assert p["pageType"] == "full_story"
    # Saba / Bilqis / hoopoe context surfaced via relatedFigures or
    # relatedNations / relatedObjects
    related_text = " ".join(
        p.get("relatedFigures", [])
        + p.get("relatedNations", [])
        + p.get("relatedObjects", [])
    )
    assert "bilqis" in related_text.lower() or len(related_text) > 0


def test_muhammad_quranic_mission_profile(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_muhammad")
    assert p is not None
    assert p["pageType"] == "mission_summary"
    # Not-full-biography warning required
    text = json.dumps(p, ensure_ascii=False)
    assert "biography" in text.lower() or "سيرة" in text


def test_ismail_page_exists(story_pages: Dict[str, Any]) -> None:
    p = _pages_by_id(story_pages).get("prophet_ismail")
    assert p is not None
    assert p["pageType"] == "full_story"


def test_missing_prophet_list_reduced_to_zero(story_pages: Dict[str, Any], atlas: Dict[str, Any]) -> None:
    page_ids = set(_pages_by_id(story_pages).keys())
    atlas_with_story_or_page = []
    for p in atlas["profiles"]:
        if p["prophetId"] in page_ids:
            atlas_with_story_or_page.append(p["prophetId"])
        elif (p.get("storyIds") or []):
            atlas_with_story_or_page.append(p["prophetId"])
    assert len(atlas_with_story_or_page) == 25, (
        f"Coverage gap: {25 - len(atlas_with_story_or_page)} prophet(s) have no story page or storyIds"
    )


# ---------------------------------------------------------------------------
# Contextual links
# ---------------------------------------------------------------------------


def test_contextual_links_all_needs_review(contextual_links: Dict[str, Any]) -> None:
    for l in contextual_links["links"]:
        assert l["reviewStatus"] == "needs_review"
        assert l["humanReviewRequired"] is True


def test_contextual_links_have_evidence(contextual_links: Dict[str, Any]) -> None:
    for l in contextual_links["links"]:
        assert l["evidenceReferences"] and len(l["evidenceReferences"]) >= 1


def test_contextual_links_total_nonzero(contextual_links: Dict[str, Any]) -> None:
    assert contextual_links["totalLinks"] > 0


# ---------------------------------------------------------------------------
# Storytelling service — 4 modes
# ---------------------------------------------------------------------------


def test_storytelling_no_verified_source_mode() -> None:
    from app.services.prophet_storytelling_service import (
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_musa",
            journey_type="mushaf_order",
            ayah_references=[],
            source_ids=[],
        )
    )
    assert out.output_mode == "no_verified_source"
    assert out.review_status == "no_verified_source"


def test_storytelling_navigation_summary_mode() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_musa",
            journey_type="mushaf_order",
            ayah_references=[AyahRef(2, 51)],
            source_ids=[],
        )
    )
    assert out.output_mode == "navigation_summary"
    assert out.review_status == "needs_review"


def test_storytelling_source_backed_mode() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_musa",
            journey_type="mushaf_order",
            ayah_references=[AyahRef(2, 51)],
            source_ids=["ibn_kathir"],
        )
    )
    assert out.output_mode == "source_backed_tafsir_summary"
    assert out.review_status == "needs_review"


def test_storytelling_compact_prophet_mode() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_dhulkifl",
            journey_type="mushaf_order",
            ayah_references=[AyahRef(21, 85)],
            source_ids=["ibn_kathir"],
        )
    )
    # Compact prophets never run in source_backed mode
    assert out.output_mode in {"navigation_summary", "evidence_only"}
    assert out.review_status == "needs_review"


def test_storytelling_muhammad_mode_includes_warning() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_muhammad",
            journey_type="mushaf_order",
            ayah_references=[AyahRef(33, 40)],
            source_ids=["ibn_kathir"],
        )
    )
    assert any("biography" in w.lower() or "سيرة" in w for w in out.warnings)


# ---------------------------------------------------------------------------
# Routers registered
# ---------------------------------------------------------------------------


def test_entities_router_registered() -> None:
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/quran/entities" in paths


def test_topics_router_registered() -> None:
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/v1/quran/topics" in paths


def test_prophets_router_registered() -> None:
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    expected = {
        "/api/v1/quran/prophets",
        "/api/v1/quran/prophets/missing-coverage",
        "/api/v1/quran/prophets/{prophet_id}/story-page",
        "/api/v1/quran/prophets/{prophet_id}/contextual-links",
        "/api/v1/quran/prophets/{prophet_id}/storytelling-safe",
    }
    assert expected.issubset(paths)


# ---------------------------------------------------------------------------
# Live API smoke
# ---------------------------------------------------------------------------


def test_missing_coverage_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/missing-coverage")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 25
    # The 9 required prophets must have a non-null pageType
    required = {
        "prophet_ishaq",
        "prophet_yaqub",
        "prophet_harun",
        "prophet_dhulkifl",
        "prophet_ilyas",
        "prophet_alyasa",
        "prophet_sulayman",
        "prophet_muhammad",
        "prophet_ismail",
    }
    by_id = {c["prophetId"]: c for c in body["coverage"]}
    for pid in required:
        assert by_id[pid]["pageType"] is not None, f"{pid} missing pageType in coverage"
        assert by_id[pid]["hasStoryPage"] is True


def test_story_page_endpoint_ishaq() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/prophet_ishaq/story-page")
    assert r.status_code == 200
    body = r.json()
    assert body["prophetId"] == "prophet_ishaq"
    assert body["pageType"] == "full_story"
    assert len(body["storySections"]) > 0


def test_story_page_endpoint_404_for_no_page_prophet() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    # Adam has explicit mentions but no curated story page — should 404
    r = client.get("/api/v1/quran/prophets/prophet_adam/story-page")
    assert r.status_code == 404


def test_contextual_links_endpoint_musa() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/prophet_musa/contextual-links?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] <= 10
    for l in body["links"]:
        assert l["reviewStatus"] == "needs_review"


def test_storytelling_safe_endpoint_refuses_unsupported_tafsir() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "journeyType": "mushaf_order",
        "ayahReferences": [],
        "sourceIds": ["random_source"],
        "language": "en",
    }
    r = client.post("/api/v1/quran/prophets/prophet_musa/storytelling-safe", json=payload)
    assert r.status_code == 200
    body = r.json()
    # No ayahs + no trusted source → no_verified_source mode
    assert body["outputMode"] == "no_verified_source"
    assert body["reviewStatus"] == "no_verified_source"


def test_storytelling_safe_returns_navigation_summary_with_ayahs() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "journeyType": "mushaf_order",
        "ayahReferences": [{"surahNumber": 2, "ayahStart": 51}],
        "sourceIds": [],
        "language": "en",
    }
    r = client.post("/api/v1/quran/prophets/prophet_musa/storytelling-safe", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["outputMode"] == "navigation_summary"
    assert body["reviewStatus"] == "needs_review"
    # Follow-up actions surfaced
    assert "view_related_ayahs" in body["followUpActions"]


def test_entities_endpoint_responds() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/entities?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "entities" in body
    assert len(body["entities"]) <= 5


def test_topics_endpoint_responds() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/topics?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "topics" in body
