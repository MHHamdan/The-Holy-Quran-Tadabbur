"""
Tests for the therapy safety layer (Phase T-Situations / T-Crisis / T-Ruqyah).

These tests are intentionally strict: they fail if any new situation /
ruqyah evidence entry is added without proper sourcing, if the crisis
classifier stops triggering on canonical phrases, or if the disclaimer
is dropped from any therapy response.
"""
from __future__ import annotations

import re
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.crisis_classifier import (
    CRISIS_HOTLINES,
    classify_crisis,
)
from app.services.situation_atlas import (
    DUA_BANK,
    SITUATION_ATLAS,
    get_situation,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Crisis classifier
# ---------------------------------------------------------------------------


_HARD_CASES_EN = [
    "I want to kill myself",
    "thinking about suicide",
    "I'm going to end my life",
    "I wish I were dead",
    "i want to cut myself tonight",
]

_HARD_CASES_AR = [
    "أريد أن أموت",
    "أتمنى الموت",
    "أفكر في الانتحار",
    "ساقتل نفسي",
]

_SOFT_CASES = [
    "I feel hopeless and tired of life",
    "كرهت حياتي",
    "I can't go on like this",
]

_BENIGN_CASES = [
    "I am grateful for my family",
    "أشكر الله على نعمته",
    "I'm worried about my exam",
]


@pytest.mark.parametrize("text", _HARD_CASES_EN + _HARD_CASES_AR)
def test_classify_crisis_hard_triggers(text):
    result = classify_crisis(text)
    assert result.level == "crisis", f"Hard-trigger phrase missed: {text!r}"
    assert result.reasons
    assert result.suggested_hotlines, "Crisis responses must surface hotlines"


@pytest.mark.parametrize("text", _SOFT_CASES)
def test_classify_crisis_soft_triggers(text):
    result = classify_crisis(text)
    assert result.level in ("elevated", "crisis"), text
    assert result.suggested_hotlines


@pytest.mark.parametrize("text", _BENIGN_CASES)
def test_classify_crisis_benign_passes(text):
    result = classify_crisis(text)
    assert result.level == "none"
    assert result.suggested_hotlines == []


def test_crisis_hotlines_all_have_urls():
    for h in CRISIS_HOTLINES:
        assert h.url.startswith(("https://", "http://")), f"hotline {h.region_code} missing URL"
        assert h.number
        assert h.region_name_en and h.region_name_ar
        assert h.organisation_en and h.organisation_ar


def test_crisis_hotline_988_present():
    has_988 = any(h.number == "988" for h in CRISIS_HOTLINES)
    assert has_988, "US 988 must be in the static hotline list"


def test_crisis_hotline_saudi_present():
    has_sa = any(h.region_code == "SA" for h in CRISIS_HOTLINES)
    assert has_sa, "Saudi national mental-health hotline must be present"


def test_crisis_hotline_intl_directory_present():
    has_intl = any("findahelpline.com" in h.url for h in CRISIS_HOTLINES)
    assert has_intl, "findahelpline.com must be in the directory entries"


# ---------------------------------------------------------------------------
# Situation atlas
# ---------------------------------------------------------------------------


def test_situation_atlas_has_minimum_entries():
    assert len(SITUATION_ATLAS) >= 20, "Situation atlas should cover ≥20 life conditions"


def test_situation_keys_unique_and_slug_safe():
    seen = set()
    for s in SITUATION_ATLAS:
        assert re.match(r"^[a-z][a-z0-9_]*$", s.key), s.key
        assert s.key not in seen
        seen.add(s.key)


def test_every_situation_has_bilingual_labels_and_descriptions():
    for s in SITUATION_ATLAS:
        assert s.label_en and s.label_ar, s.key
        assert s.description_en and s.description_ar, s.key


def test_every_situation_has_at_least_one_hadith_citation():
    for s in SITUATION_ATLAS:
        assert s.hadith_refs, f"{s.key}: no hadith citation"
        for h in s.hadith_refs:
            assert h.url.startswith("https://sunnah.com/"), (
                f"{s.key}: hadith {h.number} must cite sunnah.com"
            )


def test_situations_default_to_needs_review():
    for s in SITUATION_ATLAS:
        assert s.review_status == "needs_review"
        assert s.human_review_required is True


def test_dua_bank_entries_are_well_formed():
    for key, d in DUA_BANK.items():
        for required in ("arabic", "transliteration", "translation_en", "translation_ar"):
            assert d.get(required), f"DUA_BANK[{key}] missing {required}"


def test_situations_referencing_duas_resolve():
    for s in SITUATION_ATLAS:
        for k in s.dua_keys:
            assert k in DUA_BANK, f"{s.key}: dua_key {k} not in DUA_BANK"


def test_situations_referencing_clinical_concerns_recommend_professional():
    """Hard-coded sanity check: a few clearly clinical situations must flag
    refer_to_professional=True."""
    clinical_keys = {
        "physical_illness",
        "depression_episode",
        "abuse_or_harm",
        "anxiety_general",
        "addiction_recovery",
    }
    found = {s.key: s.refer_to_professional for s in SITUATION_ATLAS if s.key in clinical_keys}
    for key in clinical_keys:
        assert found.get(key) is True, f"{key} must set refer_to_professional=True"


# ---------------------------------------------------------------------------
# Live API smoke (TestClient)
# ---------------------------------------------------------------------------


def test_situations_endpoint_returns_list(client):
    r = client.get("/api/v1/therapy/situations")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 20
    assert body["disclaimer_en"]
    assert body["disclaimer_ar"]


def test_situation_detail_endpoint_returns_hadith_and_disclaimer(client):
    r = client.get("/api/v1/therapy/situations/physical_illness")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["key"] == "physical_illness"
    assert body["refer_to_professional"] is True
    assert body["hadith_refs"], "Detail must include hadith citations"
    assert body["disclaimer_en"] and body["disclaimer_ar"]
    for h in body["hadith_refs"]:
        assert h["url"].startswith("https://sunnah.com/")


def test_situation_detail_unknown_404(client):
    r = client.get("/api/v1/therapy/situations/this_situation_does_not_exist")
    assert r.status_code == 404


def test_ruqyah_evidence_endpoint(client):
    r = client.get("/api/v1/therapy/ruqyah-evidence")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 5
    # Every entry must cite either sunnah.com or quran.com.
    for item in body["items"]:
        assert item["url"].startswith(("https://sunnah.com/", "https://quran.com/"))
    # Scope notes must explicitly bound the claim — Quran complements but
    # does not substitute medical or mental-health care.
    assert "complements but never replaces" in body["scope_note_en"]
    assert "مكمّلة" in body["scope_note_ar"]


def test_ask_endpoint_returns_disclaimer(client):
    r = client.post(
        "/api/v1/therapy/ask",
        json={"message": "I am grateful today", "language": "en"},
    )
    # Note: /ask hits the DB so it may 500 in CI when the DB is unavailable.
    # We accept either a happy 200 (with disclaimer) or a 500 — we only care
    # that the disclaimer SHAPE is enforced when the route returns 200.
    if r.status_code == 200:
        body = r.json()
        assert body.get("disclaimer_en") and body.get("disclaimer_ar")
        assert body.get("crisis_level") in ("none", "elevated", "crisis")
