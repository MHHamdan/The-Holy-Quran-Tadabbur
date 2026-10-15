"""
Theme review flags (themes-mostly-empty).

- Theme segments are never seeded / discovered as verified.
- The Al-Ikhlas "one-third of the Quran" summary (a hadith claim with no
  hadith citation) is withheld from the API pending owner review.
"""
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

BACKEND = Path(__file__).resolve().parents[2]


def test_seed_themes_never_marks_verified():
    src = (BACKEND / "scripts" / "ingest" / "seed_themes.py").read_text(encoding="utf-8")
    assert "is_verified=True" not in src


def test_discovery_inserts_unverified():
    src = (BACKEND / "scripts" / "ingest" / "discover_theme_segments_quran_wide.py").read_text(encoding="utf-8")
    assert ":is_core, FALSE," in src


def test_public_summary_withholds_ikhlas_claim():
    from app.api.routes.themes import _public_summary

    assert _public_summary("theme_tawheed:112:1-4", "Surah Al-Ikhlas equals one-third of the Quran") == ""
    assert _public_summary("theme_sabr:3:200", "text") == "text"
    assert _public_summary("x", None) == ""


@pytest_asyncio.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio(loop_scope="session")
async def test_api_withholds_ikhlas_summary(client: AsyncClient):
    r = await client.get("/api/v1/themes/theme_tawheed/segments")
    if r.status_code == 404:
        pytest.skip("themes not seeded")
    assert r.status_code == 200
    for seg in r.json()["segments"]:
        assert "one-third" not in (seg["summary_en"] or "")
        assert "ثلث القرآن" not in (seg["summary_ar"] or "")
        assert seg["is_verified"] is False


# ---------------------------------------------------------------------------
# Every endpoint that serves theme-segment free text must withhold the
# unsourced hadith claims (Al-Ikhlas "one-third of the Quran", Ayat al-Kursi
# "greatest verse"). Real tafsir chunk text (tafsir_entries) is sourced and is
# not checked here.
# ---------------------------------------------------------------------------

_BANNED = ("ثلث القرآن", "one-third", "أعظم آية", "greatest verse")


def _assert_clean(payload, where: str):
    import json

    blob = json.dumps(payload, ensure_ascii=False).lower()
    for phrase in _BANNED:
        assert phrase.lower() not in blob, f"{where} still serves {phrase!r}"


def test_withheld_ids_cover_both_claims():
    from app.api.routes.themes import SUMMARY_WITHHELD_SEGMENT_IDS, _public_title

    assert {"theme_tawheed:112:1-4", "theme_tawheed:2:255"} <= SUMMARY_WITHHELD_SEGMENT_IDS
    assert _public_title("theme_tawheed:2:255", "Ayat al-Kursi - The Greatest Verse", "en") == "Ayat al-Kursi"
    assert _public_title("theme_sabr:3:200", "t", "en") == "t"


@pytest.mark.asyncio(loop_scope="session")
async def test_withheld_claims_absent_from_every_theme_endpoint(client: AsyncClient):
    base = "/api/v1/themes/theme_tawheed"
    r = await client.get(f"{base}/segments", params={"limit": 200})
    if r.status_code == 404:
        pytest.skip("themes not seeded")
    assert r.status_code == 200
    seg_ids = {s["id"] for s in r.json()["segments"]}
    _assert_clean(r.json(), "/segments")

    for sid in ("theme_tawheed:112:1-4", "theme_tawheed:2:255"):
        if sid not in seg_ids:
            continue
        ev = await client.get(f"{base}/segments/{sid}/evidence")
        assert ev.status_code == 200
        _assert_clean(ev.json(), f"/segments/{sid}/evidence")

    for path, params in (
        (f"{base}/timeline", {}),
        (f"{base}/graph", {"language": "en"}),
        (f"{base}/graph", {"language": "ar"}),
        (f"{base}/cross-connections", {}),
        ("/api/v1/themes/by-ayah/112/1", {}),
        ("/api/v1/themes/by-ayah/2/255", {}),
    ):
        resp = await client.get(path, params=params)
        assert resp.status_code == 200, path
        _assert_clean(resp.json(), path)

    tafsir = await client.get(f"{base}/tafsir", params={"limit": 50})
    assert tafsir.status_code == 200
    for seg in tafsir.json()["segments"]:
        segment_fields = {k: v for k, v in seg.items() if k not in ("tafsir_entries", "verses")}
        _assert_clean(segment_fields, "/tafsir")
