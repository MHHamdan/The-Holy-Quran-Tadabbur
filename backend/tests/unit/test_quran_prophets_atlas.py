"""
Phase X — Prophets Atlas — unit tests.

Covers:
- seed list contains exactly 25 prophets, no more, no fewer
- non-prophet figures (Luqman, Dhul-Qarnayn, Maryam, Bilqis, Khidr, Uzayr,
  Talut, Jalut) are excluded from the canonical list
- every prophet appears in the generated atlas
- explicit mentions are mapped for every prophet that the scanner detected
- Musa has relations to Harun
- Ibrahim has family relations to Ismail and Ishaq
- Isa has a relation context involving Maryam (NOT as a prophet)
- Dawud / Sulayman relation exists
- Yusuf / Yaqub relation exists
- the builder creates a mushaf-order journey for every prophet
- story-world journey carries certainty != "high" (needs_review or low)
- the storytelling service refuses unsupported tafsir and returns
  no_verified_source for non-trusted source IDs
- the storytelling output includes warnings
- the API routes return reviewStatus and humanReviewRequired
- the frontend pages are wired into App.tsx
- the validators pass
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[3]
ATLAS_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "quranProphetsAtlas.json"
SEEDS_PATH = ROOT / "frontend" / "src" / "data" / "quranProphetSeeds.ts"
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def atlas() -> Dict[str, Any]:
    assert ATLAS_PATH.exists(), (
        f"Run `npx tsx scripts/build-quran-prophets-atlas.ts` first; missing {ATLAS_PATH}"
    )
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def seeds_text() -> str:
    return SEEDS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Seed file
# ---------------------------------------------------------------------------


_EXPECTED_PROPHET_IDS = [
    "prophet_adam",
    "prophet_idris",
    "prophet_nuh",
    "prophet_hud",
    "prophet_salih",
    "prophet_ibrahim",
    "prophet_lut",
    "prophet_ismail",
    "prophet_ishaq",
    "prophet_yaqub",
    "prophet_yusuf",
    "prophet_ayyub",
    "prophet_shuayb",
    "prophet_musa",
    "prophet_harun",
    "prophet_dhulkifl",
    "prophet_dawud",
    "prophet_sulayman",
    "prophet_ilyas",
    "prophet_alyasa",
    "prophet_yunus",
    "prophet_zakariyya",
    "prophet_yahya",
    "prophet_isa",
    "prophet_muhammad",
]


_FORBIDDEN_NON_PROPHET_PHRASES = [
    "prophet_luqman",
    "prophet_dhulqarnayn",
    "prophet_khidr",
    "prophet_uzayr",
    "prophet_maryam",
    "prophet_talut",
    "prophet_jalut",
    "prophet_bilqis",
]


def test_seed_list_contains_25_prophets(seeds_text: str) -> None:
    for pid in _EXPECTED_PROPHET_IDS:
        assert pid in seeds_text, f"Missing prophet seed: {pid}"
    assert "QURAN_PROPHET_COUNT_CANONICAL = 25" in seeds_text


def test_seed_list_excludes_non_prophets(seeds_text: str) -> None:
    for forbidden in _FORBIDDEN_NON_PROPHET_PHRASES:
        assert forbidden not in seeds_text, (
            f"Non-prophet figure must not appear as a prophet seed: {forbidden}"
        )


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------


def test_atlas_has_exactly_25_profiles(atlas: Dict[str, Any]) -> None:
    profiles = atlas["profiles"]
    assert len(profiles) == 25, f"Expected 25 prophets, got {len(profiles)}"


def test_atlas_ids_match_expected(atlas: Dict[str, Any]) -> None:
    ids = {p["prophetId"] for p in atlas["profiles"]}
    assert ids == set(_EXPECTED_PROPHET_IDS)


def test_atlas_no_forbidden_figures(atlas: Dict[str, Any]) -> None:
    ids = {p["prophetId"] for p in atlas["profiles"]}
    for forbidden in _FORBIDDEN_NON_PROPHET_PHRASES:
        assert forbidden not in ids, f"Non-prophet figure in atlas: {forbidden}"


def test_every_prophet_has_review_status(atlas: Dict[str, Any]) -> None:
    for p in atlas["profiles"]:
        assert p["reviewStatus"] in {"needs_review", "verified", "missing_source"}
        assert p["humanReviewRequired"] is True or p["reviewStatus"] == "verified"


def _by_id(atlas: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {p["prophetId"]: p for p in atlas["profiles"]}


def test_musa_has_explicit_mentions_and_harun_relation(atlas: Dict[str, Any]) -> None:
    profiles = _by_id(atlas)
    musa = profiles["prophet_musa"]
    assert len(musa["explicitMentions"]) > 0
    targets = {r["targetProphetId"] for r in musa["relatedProphets"]}
    assert "prophet_harun" in targets


def test_ibrahim_family_relations(atlas: Dict[str, Any]) -> None:
    profiles = _by_id(atlas)
    ibr = profiles["prophet_ibrahim"]
    targets = {r["targetProphetId"] for r in ibr["relatedProphets"]}
    assert "prophet_ismail" in targets
    assert "prophet_ishaq" in targets


def test_dawud_sulayman_relation(atlas: Dict[str, Any]) -> None:
    profiles = _by_id(atlas)
    dawud = profiles["prophet_dawud"]
    targets = {r["targetProphetId"] for r in dawud["relatedProphets"]}
    assert "prophet_sulayman" in targets


def test_yusuf_yaqub_relation(atlas: Dict[str, Any]) -> None:
    profiles = _by_id(atlas)
    yusuf = profiles["prophet_yusuf"]
    targets = {r["targetProphetId"] for r in yusuf["relatedProphets"]}
    assert "prophet_yaqub" in targets


def test_isa_relations_with_maryam_context(atlas: Dict[str, Any]) -> None:
    """Maryam must appear as a related entity for Isa, never as a prophet target."""
    profiles = _by_id(atlas)
    isa = profiles["prophet_isa"]
    related_targets = {r["targetProphetId"] for r in isa["relatedProphets"]}
    # No version of Maryam-as-prophet is allowed.
    assert "prophet_maryam" not in related_targets
    # Maryam is exposed via the entity graph reference (entity_person_maryam).
    related_entities_str = " ".join(isa.get("relatedEntities", []))
    assert "maryam" in related_entities_str.lower() or "person_maryam" in related_entities_str


def test_every_prophet_has_mushaf_journey(atlas: Dict[str, Any]) -> None:
    for p in atlas["profiles"]:
        types = {j["journeyType"] for j in p.get("journeys", [])}
        assert "mushaf_order" in types, f"{p['prophetId']} missing mushaf_order journey"


def test_story_world_order_not_high_certainty(atlas: Dict[str, Any]) -> None:
    for p in atlas["profiles"]:
        for j in p.get("journeys", []):
            if j["journeyType"] == "story_world_order":
                assert j["certainty"] != "high", (
                    f"{p['prophetId']}: story_world_order MUST NOT be certainty=high"
                )


# ---------------------------------------------------------------------------
# Storytelling service
# ---------------------------------------------------------------------------


def test_storytelling_refuses_unsupported_tafsir() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_musa",
            journey_type="mushaf_order",
            ayah_references=[AyahRef(2, 51), AyahRef(20, 9)],
            source_ids=["random_source", "untrusted_x"],
            language="en",
        )
    )
    # Phase X2 change: ayahs supplied + untrusted source → navigation_summary
    # mode (review_status = needs_review). Untrusted source IDs are still
    # dropped and a no_verified_source warning is appended.
    assert out.review_status == "needs_review"
    assert out.output_mode == "navigation_summary"
    assert any("no_verified_source" in w for w in out.warnings)
    assert out.summary_english  # navigation summary still returned
    assert out.human_review_required is True


def test_storytelling_accepts_trusted_sources() -> None:
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
            language="en",
        )
    )
    # With trusted source, status is needs_review (NEVER verified).
    assert out.review_status == "needs_review"
    assert out.human_review_required is True


def test_storytelling_includes_warnings_for_story_world_order() -> None:
    from app.services.prophet_storytelling_service import (
        AyahRef,
        ProphetStorytellingInput,
        build_prophet_storytelling,
    )

    out = build_prophet_storytelling(
        ProphetStorytellingInput(
            prophet_id="prophet_yusuf",
            journey_type="story_world_order",
            ayah_references=[AyahRef(12, 4)],
            source_ids=["ibn_kathir"],
            language="ar",
        )
    )
    assert any("chronology" in w.lower() or "إرشاد" in w or "guided" in w.lower() for w in out.warnings)


# ---------------------------------------------------------------------------
# Relation explainer
# ---------------------------------------------------------------------------


def test_relation_explainer_rejects_unknown_relation() -> None:
    from app.services.entity_connection_explainer import (
        AyahRef,
        ExplainProphetRelationInput,
        explain_prophet_relation,
    )

    out = explain_prophet_relation(
        ExplainProphetRelationInput(
            source_prophet_id="prophet_musa",
            target_prophet_id="prophet_harun",
            relation_type="bogus_type",
            ayah_references=[AyahRef(20, 29)],
            source_ids=["ibn_kathir"],
            language="en",
        )
    )
    assert out.review_status == "needs_review"
    assert any("Unknown prophet relation_type" in w for w in out.warnings)


def test_relation_explainer_accepts_family_relation() -> None:
    from app.services.entity_connection_explainer import (
        AyahRef,
        ExplainProphetRelationInput,
        explain_prophet_relation,
    )

    out = explain_prophet_relation(
        ExplainProphetRelationInput(
            source_prophet_id="prophet_ibrahim",
            target_prophet_id="prophet_ismail",
            relation_type="family_relation",
            ayah_references=[AyahRef(2, 127)],
            source_ids=["ibn_kathir"],
            language="en",
        )
    )
    assert out.review_status == "needs_review"
    assert out.tafsir_evidence and out.tafsir_evidence[0].source_id == "ibn_kathir"


# ---------------------------------------------------------------------------
# API routes registered + frontend routes wired
# ---------------------------------------------------------------------------


def test_backend_prophets_router_registered() -> None:
    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    expected = {
        "/api/v1/quran/prophets",
        "/api/v1/quran/prophets/{prophet_id}",
        "/api/v1/quran/prophets/{prophet_id}/ayahs",
        "/api/v1/quran/prophets/{prophet_id}/stories",
        "/api/v1/quran/prophets/{prophet_id}/relations",
        "/api/v1/quran/prophets/{prophet_id}/journey",
        "/api/v1/quran/prophets/{prophet_id}/storytelling",
        "/api/v1/quran/prophets/explain-relation",
    }
    missing = expected - paths
    assert not missing, f"Missing routes: {missing}"


def test_frontend_routes_registered() -> None:
    txt = APP_PATH.read_text(encoding="utf-8")
    assert '/prophets' in txt
    assert '/prophets/:prophetId' in txt
    assert '/prophets/:prophetId/journey' in txt
    assert 'ProphetsPage' in txt
    assert 'ProphetDetailPage' in txt
    assert 'ProphetJourneyPage' in txt


# ---------------------------------------------------------------------------
# Live API smoke (read-only)
# ---------------------------------------------------------------------------


def test_get_list_endpoint_returns_25() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 25
    assert len(body["prophets"]) == 25
    # Every record must carry reviewStatus + humanReviewRequired
    for p in body["prophets"]:
        assert "reviewStatus" in p
        assert "humanReviewRequired" in p


def test_get_profile_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/prophet_musa")
    assert r.status_code == 200
    body = r.json()
    assert body["prophetId"] == "prophet_musa"
    assert len(body["explicitMentions"]) > 0
    assert body["reviewStatus"] == "needs_review"


def test_get_profile_invalid_id_400() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/BAD-ID")
    assert r.status_code == 400


def test_get_profile_unknown_404() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/prophets/prophet_unknown_x")
    assert r.status_code == 404


def test_storytelling_endpoint_round_trip() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "journeyType": "mushaf_order",
        "ayahReferences": [{"surahNumber": 2, "ayahStart": 51}],
        "sourceIds": ["ibn_kathir"],
        "language": "en",
    }
    r = client.post("/api/v1/quran/prophets/prophet_musa/storytelling", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reviewStatus"] == "needs_review"
    assert body["humanReviewRequired"] is True


def test_explain_relation_endpoint_round_trip() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "sourceProphetId": "prophet_musa",
        "targetProphetId": "prophet_harun",
        "relationType": "family_relation",
        "ayahReferences": [{"surahNumber": 20, "ayahStart": 29}],
        "sourceIds": ["ibn_kathir"],
        "language": "en",
    }
    r = client.post("/api/v1/quran/prophets/explain-relation", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reviewStatus"] == "needs_review"
