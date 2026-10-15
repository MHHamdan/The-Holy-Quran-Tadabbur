"""
/api/v1/duas serves verbatim Qur'an excerpts with attribution, and no
unsourced Arabic explanation.

The catalogue is generated from frontend/src/data/quranicDuas.ts. Its Arabic
must be byte-exact Tanzil Uthmani text, one segment per verse of the stated
range (3:26-27 and 5:83-84 used to claim two verses for one segment), and the
66 hand-written Arabic 'explanations' (meaningAr) are gone: the app shows
al-Tafsir al-Muyassar from the tafsir API with its source instead.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes import duas as duas_route
from app.main import app

ROOT = Path(__file__).resolve().parents[3]
TANZIL = ROOT / "data" / "raw" / "quran_tanzil.json"


@pytest.fixture(scope="module")
def client():
    duas_route._duas_limiter.reset()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def verses():
    data = json.loads(TANZIL.read_text(encoding="utf-8"))
    return {(v["sura_no"], v["aya_no"]): v["aya_text"] for v in data["verses"]}


def test_list_serves_all_with_attribution(client):
    r = client.get("/api/v1/duas")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["duas"]) >= 66
    assert "Tanzil" in body["quran_text_attribution"] and "tanzil.net" in body["quran_text_attribution"]
    assert all("meaningAr" not in d for d in body["duas"])


def test_every_excerpt_is_verbatim_for_its_range(client, verses):
    for d in client.get("/api/v1/duas").json()["duas"]:
        last = d["ayahEnd"] or d["ayah"]
        segments = d["excerptUthmani"].split(" ۝ ")
        assert len(segments) == last - d["ayah"] + 1, d["id"]
        for i, seg in enumerate(segments):
            verse = verses[(d["surah"], d["ayah"] + i)]
            assert seg and seg in verse, f"{d['id']} segment {i + 1}"
            at = verse.index(seg)
            assert at == 0 or verse[at - 1] == " ", d["id"]
            end = at + len(seg)
            assert end == len(verse) or verse[end] == " ", d["id"]


def test_fixed_ranges(client):
    by_id = {d["id"]: d for d in client.get("/api/v1/duas").json()["duas"]}
    assert by_id["dua_imran_sovereignty"]["ayahEnd"] is None
    assert by_id["dua_gospel_believers"]["ayahEnd"] is None


def test_filters_still_work(client):
    r = client.get("/api/v1/duas", params={"category": "prophets"})
    assert r.status_code == 200 and r.json()["count"] > 0
    assert all(d["category"] == "prophets" for d in r.json()["duas"])
    r = client.get("/api/v1/duas", params={"q": "guidance"})
    assert r.status_code == 200 and r.json()["count"] > 0


def test_mutated_diacritic_would_be_caught(client, verses):
    """The verbatim rule is strict: one changed mark breaks the match."""
    FATHA, KASRA = "َ", "ِ"
    for d in client.get("/api/v1/duas").json()["duas"][:10]:
        seg = d["excerptUthmani"].split(" ۝ ")[0]
        if FATHA not in seg:
            continue
        verse = verses[(d["surah"], d["ayah"])]
        assert seg in verse
        assert seg.replace(FATHA, KASRA, 1) not in verse, d["id"]
