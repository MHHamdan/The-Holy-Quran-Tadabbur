"""
English translations come from the licensed QuranEnc copies, never alquran.cloud.

alquran.cloud serves Tanzil's copies of English translations, which are
non-commercial only. en.sahih / en.hilali must be answered from the
translations table; other English editions are refused without a network call.
"""
import pytest

from app.rag.source_validator import TRUSTED_SOURCE_IDS
from app.services import tafseer_api
from app.services.tafseer_api import LICENSED_DB_EDITIONS, AlQuranCloudClient


@pytest.fixture
def no_network(monkeypatch):
    """Any HTTP call fails the test."""
    class Boom:
        def __init__(self, *a, **k):
            raise AssertionError("alquran.cloud must not be called for English editions")
    monkeypatch.setattr(tafseer_api.httpx, "AsyncClient", Boom)


def test_only_licensed_english_ids_are_trusted():
    english = {s for s in TRUSTED_SOURCE_IDS if s.startswith("alquran_cloud_en.")}
    assert english == {f"alquran_cloud_{e}" for e in LICENSED_DB_EDITIONS}


@pytest.mark.asyncio
async def test_unlicensed_english_edition_refused_without_network(no_network):
    client = AlQuranCloudClient()
    resp = await client.get_tafseer(2, 255, ["en.pickthall", "en.yusufali"])
    assert resp.tafasir == [] and not resp.success
    assert await client.get_surah_tafseer(1, "en.yusufali") == []


@pytest.mark.asyncio
@pytest.mark.requires_data("translations")
async def test_sahih_served_from_quranenc_copy(no_network):
    client = AlQuranCloudClient()
    resp = await client.get_tafseer(2, 255, ["en.sahih"])
    assert resp.success
    verse = resp.tafasir[0]
    assert verse.text.startswith("Allāh - there is no deity except Him")
    assert "QuranEnc" in verse.edition_name and " v" in verse.edition_name


@pytest.mark.asyncio
@pytest.mark.requires_data("translations")
async def test_surah_from_db(no_network):
    verses = await AlQuranCloudClient().get_surah_tafseer(112, "en.hilali")
    assert [v.ayah for v in verses] == [1, 2, 3, 4]
