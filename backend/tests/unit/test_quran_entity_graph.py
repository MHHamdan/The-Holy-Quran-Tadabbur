"""
Entity-Centered Quran Narrative GraphRAG — unit tests.

Covers:
- seed dictionary loads from quranEntitySeeds.ts (text scan)
- scan output includes Maryam with explicit name mentions
- scan output detects Isa-son-of-Maryam family pattern
- relation builder creates Maryam–Isa relation with evidence
- relation builder creates Maryam–Zakariyya relation
- journey builder returns mushaf order
- journey builder marks story_world as needs_review
- journey builder warns on revelation order when seed is missing
- explainer refuses (no_verified_source) when no trusted source is supplied
- explainer attaches trusted sources when given
- no Quran text embedded in mention output
- UI routes are wired in App.tsx
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "frontend" / "src" / "data" / "generated"
MENTIONS_PATH = GEN / "quranEntityMentions.json"
RELATIONS_PATH = GEN / "quranEntityRelations.json"
JOURNEYS_PATH = GEN / "quranEntityJourneys.json"
SEEDS_PATH = ROOT / "frontend" / "src" / "data" / "quranEntitySeeds.ts"
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"


@pytest.fixture(scope="module")
def mentions() -> dict:
    assert MENTIONS_PATH.exists(), f"Run scan-quran-entity-mentions.ts first; missing {MENTIONS_PATH}"
    return json.loads(MENTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def relations() -> dict:
    assert RELATIONS_PATH.exists(), f"Run build-quran-entity-relations.ts first; missing {RELATIONS_PATH}"
    return json.loads(RELATIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def journeys() -> dict:
    assert JOURNEYS_PATH.exists(), f"Run build-quran-entity-journeys.ts first; missing {JOURNEYS_PATH}"
    return json.loads(JOURNEYS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def seeds_text() -> str:
    return SEEDS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Seed dictionary
# ---------------------------------------------------------------------------


def test_seeds_export_combined_constant(seeds_text: str) -> None:
    assert "QURAN_ENTITY_SEEDS" in seeds_text


def test_maryam_seed_has_expected_aliases(seeds_text: str) -> None:
    assert "entity_person_maryam" in seeds_text
    # The required aliases per spec
    assert "مريم" in seeds_text
    assert "ابن مريم" in seeds_text
    assert "Mary mother of Jesus" in seeds_text


def test_seeds_default_unreviewed(seeds_text: str) -> None:
    assert "reviewedDictionary: false" in seeds_text


# ---------------------------------------------------------------------------
# Scan output
# ---------------------------------------------------------------------------


def test_scan_covers_all_surahs(mentions: dict) -> None:
    assert mentions["scannedSurahs"] == 114


def test_scan_finds_maryam_explicit_mentions(mentions: dict) -> None:
    maryam = next(e for e in mentions["entities"] if e["entityId"] == "entity_person_maryam")
    explicit = [m for m in maryam["mentions"] if m["mentionType"] == "explicit_name"]
    assert len(explicit) >= 25, f"Expected ≥25 explicit Maryam mentions, got {len(explicit)}"


def test_scan_finds_isa_via_explicit_or_alias(mentions: dict) -> None:
    isa = next(e for e in mentions["entities"] if e["entityId"] == "entity_prophet_isa")
    # Isa is named ~25 times directly; we accept >=15 explicit_name OR alias matches
    primary = [m for m in isa["mentions"] if m["mentionType"] in ("explicit_name", "alias")]
    assert len(primary) >= 15


def test_scan_mentions_carry_review_metadata(mentions: dict) -> None:
    for e in mentions["entities"][:5]:
        for m in e["mentions"][:5]:
            assert "reviewStatus" in m and m["reviewStatus"]
            assert m["humanReviewRequired"] is True


def test_scan_does_not_embed_quran_text(mentions: dict) -> None:
    # We only allow a short normalised surface form. Disallow any text longer
    # than 80 chars or containing newlines (Quran ayahs are much longer).
    for e in mentions["entities"]:
        for m in e["mentions"]:
            mt = m.get("matchedText", "") or ""
            assert len(mt) <= 80
            assert "\n" not in mt


def test_scan_sources_are_known(mentions: dict) -> None:
    # Every mention sources from quran_uthmani_cloud (registered in sourceRegistry).
    for e in mentions["entities"]:
        for m in e["mentions"]:
            assert m["sourceIds"], f"{e['entityId']} {m['surahNumber']}:{m['ayahNumber']} missing sourceIds"
            assert "quran_uthmani_cloud" in m["sourceIds"]


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


def test_relations_total_positive(relations: dict) -> None:
    assert relations["totalRelations"] > 100


def test_every_relation_has_evidence(relations: dict) -> None:
    for r in relations["relations"]:
        assert r["evidenceReferences"], f"Empty evidence on {r['sourceEntityId']}->{r['targetEntityId']}"


def test_relations_default_needs_review(relations: dict) -> None:
    for r in relations["relations"]:
        assert r["reviewStatus"] == "needs_review"
        assert r["humanReviewRequired"] is True


def test_maryam_isa_relation_exists(relations: dict) -> None:
    rels = [
        r
        for r in relations["relations"]
        if r["sourceEntityId"] == "entity_person_maryam" and r["targetEntityId"] == "entity_prophet_isa"
    ]
    types = {r["relationType"] for r in rels}
    assert "mother_of" in types
    assert "mentioned_with" in types
    assert "theological_discussion" in types


def test_maryam_zakariyya_relation_exists(relations: dict) -> None:
    rels = [
        r
        for r in relations["relations"]
        if {r["sourceEntityId"], r["targetEntityId"]}
        == {"entity_person_maryam", "entity_prophet_zakariyya"}
    ]
    types = {r["relationType"] for r in rels}
    # Either side: family_of or guardian_of must appear
    assert "family_of" in types or "guardian_of" in types


# ---------------------------------------------------------------------------
# Journeys
# ---------------------------------------------------------------------------


def test_journey_has_mushaf_order(journeys: dict) -> None:
    maryam = journeys["journeys"]["entity_person_maryam"]
    assert "mushaf_order" in maryam
    assert maryam["mushaf_order"]["sections"], "Maryam mushaf journey is empty"
    # certainty for mushaf is by construction "high"
    assert maryam["mushaf_order"]["certainty"] == "high"


def test_story_world_journey_is_needs_review(journeys: dict) -> None:
    maryam = journeys["journeys"]["entity_person_maryam"]
    sw = maryam["story_world"]
    assert sw["reviewStatus"] == "needs_review"
    assert sw["certainty"] != "high"


def test_revelation_journey_warns_when_uncertain(journeys: dict) -> None:
    maryam = journeys["journeys"]["entity_person_maryam"]
    rev = maryam["revelation_order"]
    # Most surahs lack a revelation-order seed → certainty should be disputed
    assert rev["certainty"] in ("disputed", "low", "medium")
    assert any("revelation-order" in w.lower() or "lack" in w.lower() for w in rev["warnings"])


def test_thematic_journey_has_at_least_5_sections_for_maryam(journeys: dict) -> None:
    th = journeys["journeys"]["entity_person_maryam"]["thematic_order"]
    assert len(th["sections"]) >= 5


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------


def test_explainer_no_verified_source_when_empty():
    from app.services.entity_connection_explainer import (
        AyahRef,
        ExplainConnectionInput,
        explain_connection,
    )

    out = explain_connection(
        ExplainConnectionInput(
            entity_id="entity_person_maryam",
            source_reference=AyahRef(19, 16),
            target_reference=AyahRef(3, 42),
            relation_types=["mentioned_with"],
            source_ids=[],
            language="en",
        )
    )
    assert out.review_status == "needs_review"
    assert any("no_verified_source" in w for w in out.warnings)
    assert out.tafsir_evidence == []


def test_explainer_filters_untrusted_sources():
    from app.services.entity_connection_explainer import (
        AyahRef,
        ExplainConnectionInput,
        explain_connection,
    )

    out = explain_connection(
        ExplainConnectionInput(
            entity_id="entity_person_maryam",
            source_reference=AyahRef(19, 16),
            target_reference=AyahRef(3, 42),
            relation_types=["theological_discussion"],
            source_ids=["random_blog", "ibn_kathir_ar"],
            language="en",
        )
    )
    sids = {e.source_id for e in out.tafsir_evidence}
    assert "random_blog" not in sids
    assert "ibn_kathir_ar" in sids
    assert any("Theological-clarification" in w for w in out.warnings)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


def test_app_has_entity_routes() -> None:
    # Entity routes were consolidated into /concepts in 221f552.
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'path="/concepts"' in text
    assert 'path="/concepts/:conceptId"' in text


# ---------------------------------------------------------------------------
# API smoke (route registration)
# ---------------------------------------------------------------------------


def test_api_routes_registered() -> None:
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/v1/quran/entities" in paths
    assert "/api/v1/quran/entities/{entity_id}" in paths
    assert "/api/v1/quran/entities/{entity_id}/mentions" in paths
    assert "/api/v1/quran/entities/{entity_id}/relations" in paths
    assert "/api/v1/quran/entities/{entity_id}/journey" in paths
    assert "/api/v1/quran/entities/explain-connection" in paths


# ---------------------------------------------------------------------------
# Sanity: ensure no path-traversal escape in entity_id
# ---------------------------------------------------------------------------


def test_entity_id_pattern_rejects_traversal():
    from app.api.routes.entities import _ENTITY_ID_RE

    assert _ENTITY_ID_RE.match("entity_person_maryam")
    assert not _ENTITY_ID_RE.match("../etc/passwd")
    assert not _ENTITY_ID_RE.match("entity_../passwd")
    assert not _ENTITY_ID_RE.match("Entity_With_Caps")
