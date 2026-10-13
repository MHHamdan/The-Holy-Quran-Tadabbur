"""
Hizb quarters and sajdah verses (data/manifests/quran_structure_markers.json).

The markers come from Tanzil's metadata reconciled with the Madinah Mushaf
text the app displays. These tests pin that reconciliation: every rub
el-hizb mark (U+06DE) printed in the stored Uthmani text is a quarter start,
and the sajdah list is exactly the verses carrying the sajdah mark (U+06E9).
"""
import json
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKERS = json.loads((REPO_ROOT / "data" / "manifests" / "quran_structure_markers.json").read_text(encoding="utf-8"))
QURAN = json.loads((REPO_ROOT / "assets" / "hafs_smart_v8.json").read_text(encoding="utf-8"))
RUB_EL_HIZB, SAJDAH = "۞", "۩"


def _verses_with(mark: str) -> set[tuple[int, int]]:
    return {(int(v["sura_no"]), int(v["aya_no"])) for v in QURAN if mark in v["aya_text"]}


class TestManifest:
    def test_240_quarters_in_mushaf_order(self):
        order = {(int(v["sura_no"]), int(v["aya_no"])): i for i, v in enumerate(QURAN)}
        quarters = [tuple(q) for q in MARKERS["hizb_quarters"]]
        assert len(quarters) == len(set(quarters)) == 240
        assert quarters[0] == (1, 1)
        assert [order[q] for q in quarters] == sorted(order[q] for q in quarters)

    def test_every_printed_rub_el_hizb_mark_starts_a_quarter(self):
        assert _verses_with(RUB_EL_HIZB) <= {tuple(q) for q in MARKERS["hizb_quarters"]}

    def test_madinah_mushaf_wins_over_tanzil(self):
        quarters = {tuple(q) for q in MARKERS["hizb_quarters"]}
        assert (15, 49) in quarters and (15, 50) not in quarters

    def test_sajdahs_match_the_printed_marks(self):
        listed = {(s["sura"], s["aya"]) for s in MARKERS["sajdahs"]}
        assert listed == _verses_with(SAJDAH)
        assert len(listed) == 15
        assert {s["type"] for s in MARKERS["sajdahs"]} == {"recommended", "obligatory"}

    def test_attribution_present(self):
        assert MARKERS["license"] == "Creative Commons Attribution 3.0"
        assert "tanzil.net" in MARKERS["attribution"]


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
@pytest.mark.requires_data("verse_markers")
class TestApi:
    async def test_markers_on_verses(self, client):
        r = await client.get("/api/v1/quran/verses/96/19")
        v = r.json()
        assert v["sajda_type"] == "obligatory"
        assert (v["hizb_no"], v["rub_no"]) == (60, 239)

    async def test_quarter_boundary(self, client):
        r = await client.get("/api/v1/quran/verses/2/1/30")
        verses = {v["aya_no"]: v for v in r.json()}
        assert verses[25]["rub_no"] == 1 and verses[26]["rub_no"] == 2
        assert [a for a, v in verses.items() if v["quarter_start"]] == [26]
        assert all(v["sajda_type"] is None for v in verses.values())

    async def test_madinah_quarter_start_flagged(self, client):
        r = await client.get("/api/v1/quran/verses/15/48/50")
        assert [v["aya_no"] for v in r.json() if v["quarter_start"]] == [49]
