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
