"""
The canonical Qur'an text is Tanzil's, verbatim, and it is the same Mushaf
the app showed before.

- data/raw/quran_tanzil.json must equal the verbatim Tanzil XML files verse
  for verse (text and Bismillah), and carry Tanzil's copyright block.
- Compared with the previous KFGQPC text, every verse has the same letters
  once encoding conventions are normalised; the only differences allowed are
  the five documented in data/manifests/quran_hafs.json.
- The database and API serve exactly that text.
"""
import json
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
TANZIL = ROOT / "data" / "raw" / "tanzil"
DERIVED = json.loads((ROOT / "data" / "raw" / "quran_tanzil.json").read_text(encoding="utf-8"))
VERSES = {(v["sura_no"], v["aya_no"]): v for v in DERIVED["verses"]}

# Same words, written differently by the two corpora (spacing / encoding).
KNOWN_ENCODING_DIFFERENCES = {(2, 181), (8, 6), (13, 37), (12, 39), (12, 41)}


def _xml(name: str) -> dict:
    out = {}
    for sura in ET.parse(TANZIL / name).getroot().iter("sura"):
        for aya in sura.iter("aya"):
            out[(int(sura.get("index")), int(aya.get("index")))] = (aya.get("text"), aya.get("bismillah"))
    return out


def _skeleton(text: str) -> str:
    """Letters only: no diacritics or Quranic annotation marks, one alef/ya/waw form."""
    text = "".join(
        ch for ch in text.replace("﻿", "")
        if not unicodedata.category(ch).startswith("M") and ch != "ـ" and not 0x06D6 <= ord(ch) <= 0x06ED
    ).replace("ءا", "ا")  # after stripping marks: KFGQPC's hamza + alef = Tanzil's alef madda
    for a, b in [("ٱ", "ا"), ("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ئ", "ي"), ("ؤ", "و"), ("ة", "ه")]:
        text = text.replace(a, b)
    return " ".join(text.split())


class TestDerivedFile:
    def test_verbatim_uthmani_and_bismillah(self):
        source = _xml("quran-uthmani.xml")
        assert len(source) == len(VERSES) == 6236
        for key, (text, bismillah) in source.items():
            assert VERSES[key]["aya_text"] == text, key
            assert VERSES[key]["bismillah"] == bismillah, key

    def test_verbatim_simple(self):
        for key, (text, bismillah) in _xml("quran-simple.xml").items():
            assert VERSES[key]["aya_text_emlaey"] == text, key
            assert VERSES[key]["bismillah_emlaey"] == bismillah, key

    def test_copyright_block_travels(self):
        for edition in ("uthmani", "simple"):
            block = DERIVED["copyright"][edition]
            assert "Tanzil Project" in block and "Creative Commons Attribution 3.0" in block
            assert "CHANGING IT IS NOT ALLOWED" in block

    def test_bismillah_on_112_surah_openings(self):
        with_b = {k for k, v in VERSES.items() if v["bismillah"]}
        assert with_b == {(s, 1) for s in range(2, 115) if s != 9}


class TestSameMushafAsBefore:
    def test_letters_match_previous_text(self):
        previous = json.loads((ROOT / "assets" / "hafs_smart_v8.json").read_text(encoding="utf-8"))
        differing = set()
        for v in previous:
            key = (int(v["sura_no"]), int(v["aya_no"]))
            old = v["aya_text"].replace("﻿", "")
            if key[1] == 1 and key[0] not in (1, 9):
                old = " ".join(old.split()[4:])  # KFGQPC inlined the Bismillah
            if _skeleton(old) != _skeleton(VERSES[key]["aya_text"]):
                differing.add(key)
        assert differing == KNOWN_ENCODING_DIFFERENCES

    def test_pages_and_juz_unchanged(self):
        previous = json.loads((ROOT / "assets" / "hafs_smart_v8.json").read_text(encoding="utf-8"))
        for v in previous:
            new = VERSES[(int(v["sura_no"]), int(v["aya_no"]))]
            assert (new["page"], new["jozz"]) == (int(v["page"]), int(v["jozz"]))


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
class TestServed:
    async def test_api_serves_tanzil_text_and_attribution(self, client):
        r = await client.get("/api/v1/quran/suras/2")
        verses = r.json()
        for v in verses:
            assert v["text_uthmani"] == VERSES[(2, v["aya_no"])]["aya_text"]
            assert v["text_imlaei"] == VERSES[(2, v["aya_no"])]["aya_text_emlaey"]
            assert "tanzil.net" in v["source_authority_en"]
        assert verses[0]["bismillah_uthmani"] == VERSES[(2, 1)]["bismillah"]
        assert all(v["bismillah_uthmani"] is None for v in verses[1:])

    async def test_no_bismillah_on_fatiha_and_tawbah(self, client):
        for sura in (1, 9):
            v = (await client.get(f"/api/v1/quran/verses/{sura}/1")).json()
            assert v["bismillah_uthmani"] is None and v["bismillah_imlaei"] is None
