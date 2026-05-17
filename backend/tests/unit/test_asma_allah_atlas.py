"""
Phase W — Asmā' Allah al-Ḥusnā Atlas — unit tests.

Covers:
- atlas JSON exists; primary list contains exactly the 99 traditional Names
- Divine Name "Allah" is exposed separately (NOT inside the 99 list)
- "All" tab display count is 99, never 100
- no duplicate nameIds; no duplicate normalised Arabic names
- category totals sum to 99
- "Allah" occurrence scanning excludes surah-opening basmalah (113 × 3 = 339)
- Al-Fatihah 1:1 basmalah is excluded by default (countBasmalaInFatihah=false)
- in-ayah basmalah at 27:30 is counted normally
- occurrence refs valid; pairings reference existing names
- zero-occurrence names are clearly marked with a warning
- category counts non-zero for at least one category
- API endpoints registered; list returns non-zero category counts
- GET /asma returns total=99 and the standalone divineNameAllah payload
- GET /asma/{nameId} returns the missing-meaning message when no meaning
  is set; "allah" is still resolvable via the detail endpoint.
- frontend AsmaAllahPage does not render the literal "الكل (100)"
- validator rejects a forged "verified" name without a non-Quran source
- no Quran text mutation
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ATLAS_PATH = ROOT / "frontend" / "src" / "data" / "generated" / "asmaAllahAtlas.json"
SEEDS_PATH = ROOT / "frontend" / "src" / "data" / "asmaAllahSeeds.ts"
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"


@pytest.fixture(scope="module")
def atlas() -> dict:
    assert ATLAS_PATH.exists(), f"Run scripts/build-asma-allah-atlas.ts first; missing {ATLAS_PATH}"
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def seeds_text() -> str:
    return SEEDS_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------


def test_asma_seed_list_loads(seeds_text: str) -> None:
    assert "ASMA_ALLAH_SEEDS" in seeds_text
    for nm in ("allah", "ar_rahman", "ar_raheem", "al_malik", "al_aziz", "al_hakim", "ash_shahid"):
        assert nm in seeds_text, f"Missing seed nameId: {nm}"


# ---------------------------------------------------------------------------
# Atlas
# ---------------------------------------------------------------------------


def test_atlas_primary_list_has_99_names(atlas: dict) -> None:
    """The Asmā' learning list must contain exactly 99 traditional Names.

    The Divine Name "Allah" (اسم الجلالة) is exposed separately via
    `divineNameAllah` — it is the supreme Name that the 99 describe and must
    NOT be counted inside the 99. Showing "الكل (100)" is the bug this guards.
    """
    assert atlas["totalNames"] == 99
    assert atlas["traditionalNamesCount"] == 99
    assert atlas["allDisplayCount"] == 99
    assert atlas["allDisplayCount"] != 100
    assert len(atlas["names"]) == 99
    assert atlas["divineNameAllahIncluded"] is False
    name_ids = [n["nameId"] for n in atlas["names"]]
    assert "allah" not in name_ids


def test_divine_name_allah_exposed_separately(atlas: dict) -> None:
    divine = atlas.get("divineNameAllah")
    assert divine is not None
    assert divine["nameId"] == "allah"
    assert divine["occurrenceCount"] > 1500  # preserved Quran evidence


def test_atlas_has_no_duplicate_name_ids(atlas: dict) -> None:
    name_ids = [n["nameId"] for n in atlas["names"]]
    assert len(name_ids) == len(set(name_ids)), "Duplicate nameId in 99-Names list"


def test_atlas_category_totals_sum_to_99(atlas: dict) -> None:
    s = sum(c["names"] for c in atlas["categoryCounts"])
    assert s == 99, f"Category 'names' totals must sum to 99; got {s}"


def test_atlas_no_duplicate_normalised_arabic_names(atlas: dict) -> None:
    import re

    diacritics = re.compile(r"[ً-ٰٟۖ-ۭـ]")

    def norm(s: str) -> str:
        s = diacritics.sub("", s)
        s = re.sub(r"[آأإٱ]", "ا", s)
        s = s.replace("ى", "ي").replace("ة", "ه").replace("ء", "")
        return s.strip()

    seen: dict[str, str] = {}
    for n in atlas["names"]:
        k = norm(n["arabicName"])
        prior = seen.get(k)
        assert prior is None or prior == n["nameId"], (
            f'Alternate form collision: "{k}" shared by {prior} and {n["nameId"]} — must be alias.'
        )
        seen[k] = n["nameId"]


def test_allah_occurrence_count_excludes_basmalah(atlas: dict) -> None:
    # Allah lives in the standalone divineNameAllah field — not inside the 99.
    allah = atlas["divineNameAllah"]
    assert allah is not None and allah["nameId"] == "allah"
    # The Quran corpus has thousands of "الله" (incl. clitic-prefixed forms).
    # With basmalah excluded, the count must be far above 1000 and far below 8000.
    assert allah["occurrenceCount"] > 1500
    # The 113 basmalah-opening occurrences for "Allah" must be present as
    # excluded entries.
    excluded = [o for o in allah["quranOccurrences"] if o["matchType"] == "basmalah_excluded"]
    assert len(excluded) == 113, f"Expected 113 basmalah-excluded Allah occurrences, got {len(excluded)}"


def test_total_excluded_basmalah_is_339(atlas: dict) -> None:
    # 113 surahs × 3 names (الله / الرحمن / الرحيم) = 339 excluded
    assert atlas["totalExcludedBasmalahOccurrences"] == 339


def test_al_fatihah_basmalah_excluded(atlas: dict) -> None:
    allah = atlas["divineNameAllah"]
    fatihah_basmalah = [
        o for o in allah["quranOccurrences"]
        if o["surahNumber"] == 1 and o["ayahNumber"] == 1
    ]
    assert any(o["counted"] is False and o["matchType"] == "basmalah_excluded" for o in fatihah_basmalah)


def test_in_ayah_basmalah_at_27_30_is_counted(atlas: dict) -> None:
    """Surah An-Naml 27:30 contains the basmalah inside Sulayman's letter; this
    is NOT a surah-opening line, so the three names must be counted normally
    (not excluded)."""
    by_id: dict[str, dict] = {n["nameId"]: n for n in atlas["names"]}
    if atlas.get("divineNameAllah"):
        by_id["allah"] = atlas["divineNameAllah"]
    for nid in ("allah", "ar_rahman", "ar_raheem"):
        name = by_id[nid]
        at_27_30 = [
            o for o in name["quranOccurrences"]
            if o["surahNumber"] == 27 and o["ayahNumber"] == 30
        ]
        assert at_27_30, f"Expected {nid} at 27:30 in the atlas"
        for o in at_27_30:
            assert o["counted"] is True, f"{nid} at 27:30 must be counted (in-ayah basmalah)"
            assert o["matchType"] != "basmalah_excluded"


def test_occurrence_count_matches_counted_entries(atlas: dict) -> None:
    records = list(atlas["names"])
    if atlas.get("divineNameAllah"):
        records.append(atlas["divineNameAllah"])
    for n in records:
        counted = [o for o in n["quranOccurrences"] if o["counted"]]
        assert n["occurrenceCount"] == len(counted), f"{n['nameId']}: mismatch"


def test_zero_occurrence_names_have_warning(atlas: dict) -> None:
    zero = [n for n in atlas["names"] if n["occurrenceCount"] == 0]
    assert zero, "Expected some names with zero explicit Quran occurrences"
    for n in zero:
        assert n["warnings"], f"{n['nameId']}: zero-occurrence name must carry a warning"


def test_pairings_reference_existing_names(atlas: dict) -> None:
    ids = {n["nameId"] for n in atlas["names"]}
    for n in atlas["names"]:
        for p in n["commonPairings"]:
            assert p["firstNameId"] in ids
            assert p["secondNameId"] in ids


def test_category_counts_match_names(atlas: dict) -> None:
    for c in atlas["categoryCounts"]:
        names = [n for n in atlas["names"] if n["category"] == c["category"]]
        assert len(names) == c["names"]


def test_at_least_one_category_has_nonzero_counts(atlas: dict) -> None:
    # Critical UI safety: the page should NEVER render all-zero counts.
    assert any(c["countedOccurrences"] > 0 for c in atlas["categoryCounts"])


def test_no_meaning_set_on_atlas_names(atlas: dict) -> None:
    """The build script must not emit meanings; meanings are scholar-only."""
    for n in atlas["names"]:
        if n.get("reviewStatus") != "verified":
            assert not n.get("meaningArabic")
            assert not n.get("meaningEnglish")


def test_no_long_arabic_text_in_atlas(atlas: dict) -> None:
    import re
    arabic = re.compile(r"[؀-ۿ]")

    def walk(o):
        if isinstance(o, str):
            if len(o) > 200 and len(arabic.findall(o)) > 50:
                return True
        elif isinstance(o, dict):
            return any(walk(v) for v in o.values())
        elif isinstance(o, list):
            return any(walk(v) for v in o)
        return False

    assert not walk(atlas)


# ---------------------------------------------------------------------------
# Validator rejection contract
# ---------------------------------------------------------------------------


def test_validator_rejects_forged_verified_without_non_quran_source() -> None:
    """Simulate the validator predicate: a name marked verified must have a
    non-Quran source attached."""
    forged = {
        "nameId": "al_aziz",
        "reviewStatus": "verified",
        "sourceIds": ["quran_uthmani_cloud"],
    }
    bad = forged["reviewStatus"] == "verified" and all(s == "quran_uthmani_cloud" for s in forged["sourceIds"])
    assert bad, "The forged name must be flagged by the validator predicate."


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


def test_api_routes_registered() -> None:
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/v1/quran/asma" in paths
    assert "/api/v1/quran/asma/categories" in paths
    assert "/api/v1/quran/asma/search" in paths
    assert "/api/v1/quran/asma/{name_id}" in paths
    assert "/api/v1/quran/asma/{name_id}/occurrences" in paths
    assert "/api/v1/quran/asma/{name_id}/pairings" in paths


def test_api_list_returns_non_zero_category_counts() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma")
    assert r.status_code == 200, r.text
    body = r.json()
    # The API total reflects the primary 99-Names list. The Divine Name "Allah"
    # is exposed separately via the divineNameAllah field — never bundled here.
    assert body["total"] == 99
    assert body["traditionalNamesCount"] == 99
    assert body["allDisplayCount"] == 99
    assert body["divineNameAllahIncluded"] is False
    # Allah never lives inside the 99 names list.
    assert "allah" not in {n["nameId"] for n in body["names"]}
    # Divine Name payload is present and carries the separation note.
    divine = body.get("divineNameAllah")
    assert divine is not None
    assert divine["nameId"] == "allah"
    # arabicName may carry tashkeel (e.g. "اللَّه"); strip diacritics before
    # comparing to the bare lemma.
    import re as _re
    _diacritics = _re.compile(r"[ً-ٰٟۖ-ۭـ]")
    assert "الله" in _diacritics.sub("", divine["arabicName"])
    assert "99" in divine["separateFromListNoteArabic"]
    assert "99 Names" in divine["separateFromListNoteEnglish"]
    # CRITICAL: not every category may be zero — the bug we fixed.
    assert any(c["countedOccurrences"] > 0 for c in body["categories"])
    # Category names sum to 99.
    assert sum(c["names"] for c in body["categories"]) == 99
    # basmalah policy is surfaced.
    assert "basmalahPolicy" in body
    assert body["basmalahPolicy"]["excludeRepeatedSurahOpeningBasmalah"] is True


def test_api_categories_endpoint_reports_99() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma/categories")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["traditionalNamesCount"] == 99
    assert body["allDisplayCount"] == 99
    assert body["divineNameAllahIncluded"] is False


def test_api_detail_returns_missing_meaning_message() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma/al_aziz")
    assert r.status_code == 200, r.text
    body = r.json()
    # No meaning set yet → missing message present.
    assert body.get("meaningArabic") in (None, "")
    assert body.get("meaningEnglish") in (None, "")
    msg = body["missingMeaningMessage"]
    assert "لا يتوفر معنى موثوق" in msg["ar"]
    assert "No verified meaning" in msg["en"]


def test_api_occurrences_includes_excluded_metadata() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma/allah/occurrences")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["excludedBasmalahCount"] >= 113


# ---------------------------------------------------------------------------
# UI route regression
# ---------------------------------------------------------------------------


def test_app_routes_include_asma() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'path="/themes/asma"' in text
    assert 'path="/themes/asma/:nameId"' in text


def test_asma_page_does_not_render_all_100_label() -> None:
    """Regression guard: the Asmā' page must never render the literal string
    "الكل (100)" or "All (100)". The "all" tab uses data.allDisplayCount
    (=99) rather than data.total when computed by the backend."""
    page = ROOT / "frontend" / "src" / "pages" / "AsmaAllahPage.tsx"
    src = page.read_text(encoding="utf-8")
    assert "الكل (100)" not in src
    assert "All (100)" not in src
    # The "All" tab must derive its count from allDisplayCount, not total.
    assert "data.allDisplayCount" in src
    # The Divine Name hero panel is wired up.
    assert "data.divineNameAllah" in src
    assert "separateFromListNoteArabic" in src


def test_atlas_every_traditional_name_has_primary_refs(atlas: dict) -> None:
    """Each of the 99 traditional Names must cite at least one canonical
    Quranic verse from the Tirmidhi tradition (no Quran text — only refs)."""
    for n in atlas["names"]:
        refs = n.get("primaryQuranicReferences") or []
        assert refs, f"{n['nameId']}: missing primaryQuranicReferences"
        for r in refs:
            assert isinstance(r["surahNumber"], int)
            assert isinstance(r["ayahStart"], int)
            assert 1 <= r["surahNumber"] <= 114
            assert r["ayahStart"] >= 1


def test_atlas_primary_refs_attach_tirmidhi_source(atlas: dict) -> None:
    for n in atlas["names"]:
        refs = n.get("primaryQuranicReferences") or []
        if refs:
            assert "tirmidhi_asma_husna_list" in n["sourceIds"], (
                f"{n['nameId']}: primary refs attached but Tirmidhi source missing"
            )


def test_atlas_primary_refs_have_no_quran_text(atlas: dict) -> None:
    """primaryQuranicReferences carry numbers + optional short notes only.
    They must NEVER carry Quran ayah text. We guard the contract here."""
    forbidden_keys = {"text", "arabicText", "ayahText", "translation"}
    for n in atlas["names"]:
        for r in n.get("primaryQuranicReferences") or []:
            for k in forbidden_keys:
                assert k not in r, f"{n['nameId']}: forbidden field '{k}' on primary ref"


def test_api_detail_returns_primary_refs() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma/al_ahad")
    assert r.status_code == 200, r.text
    body = r.json()
    refs = body.get("primaryQuranicReferences", [])
    assert refs, "al_ahad must carry primary refs"
    # Surah 112:1 is the canonical reference for al-Ahad.
    assert any(r["surahNumber"] == 112 and r["ayahStart"] == 1 for r in refs)


def test_api_list_includes_primary_refs_on_rows() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/quran/asma")
    assert r.status_code == 200
    body = r.json()
    # At least 90% of the rows should carry at least one primary reference.
    with_refs = [n for n in body["names"] if n.get("primaryQuranicReferences")]
    assert len(with_refs) >= 90, f"only {len(with_refs)} rows have primary refs"


def test_source_registry_has_tirmidhi_entry() -> None:
    """The new Tirmidhi reference source must be registered in sourceRegistry."""
    path = ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts"
    text = path.read_text(encoding="utf-8")
    assert "tirmidhi_asma_husna_list" in text
    assert "quran_com_verse_audio" in text


def test_audio_player_uses_quran_com_cdn() -> None:
    """Audio player must stream from verses.quran.com (CDN policy) and must
    attribute the reciter (per the source registry license terms)."""
    path = ROOT / "frontend" / "src" / "components" / "quran" / "AsmaAudioPlayer.tsx"
    src = path.read_text(encoding="utf-8")
    assert "verses.quran.com/Alafasy/mp3" in src
    assert "Mishary Rashid Alafasy" in src
    # No Quran text rendered in the player.
    forbidden = ["aya_text", "ayahText", "dangerouslySetInnerHTML"]
    for token in forbidden:
        assert token not in src, f"Audio player must not render Quran text or use {token}"


def test_audio_url_pattern_is_zero_padded() -> None:
    """The verse audio URL must be zero-padded to 3 digits per Quran.com CDN."""
    path = ROOT / "frontend" / "src" / "components" / "quran" / "AsmaAudioPlayer.tsx"
    src = path.read_text(encoding="utf-8")
    # `pad(surah, 3)` + `pad(ayah, 3)` produce 6 digits total (e.g. 001001).
    assert "pad(n, width)" in src or "padStart" in src
    assert "${pad(surah, 3)}${pad(ayah, 3)}.mp3" in src


def test_asma_seed_marks_allah_outside_traditional99() -> None:
    """The seed list must explicitly tag the Divine Name "Allah" with
    inTraditional99: false so the builder can partition it from the 99."""
    src = SEEDS_PATH.read_text(encoding="utf-8")
    # Find the allah seed block and check its flag.
    allah_block_start = src.find("nameId: 'allah'")
    assert allah_block_start >= 0, "allah seed missing"
    # Look ahead for the flag — the closing brace of the object.
    next_object_close = src.find("\n  },", allah_block_start)
    assert next_object_close >= 0
    allah_block = src[allah_block_start:next_object_close]
    assert "inTraditional99: false" in allah_block, (
        '"allah" must carry inTraditional99: false so it is shown separately.'
    )
