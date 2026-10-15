"""The readers' surah -> first page / first juz tables match the canonical text.

frontend/src/components/reader/surahNavigation.ts holds 114-entry tables used
by the mushaf surah selector and the surah index. They must equal the `page`
and `jozz` fields of each surah's first ayah in data/raw/quran_tanzil.json.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TANZIL = ROOT / "data" / "raw" / "quran_tanzil.json"
TS = ROOT / "frontend" / "src" / "components" / "reader" / "surahNavigation.ts"


def _ts_table(name: str) -> list:
    src = TS.read_text(encoding="utf-8")
    m = re.search(rf"export const {name}: readonly number\[\] = \[(.*?)\];", src, re.S)
    assert m, name
    return [int(x) for x in re.findall(r"\d+", re.sub(r"//.*", "", m.group(1)))]


def _canonical():
    if not TANZIL.exists():
        pytest.skip("data/raw/quran_tanzil.json not present")
    first_page, first_juz = {}, {}
    for v in json.loads(TANZIL.read_text(encoding="utf-8"))["verses"]:
        s = int(v["sura_no"])
        first_page.setdefault(s, int(v["page"]))
        first_juz.setdefault(s, int(v["jozz"]))
    return [first_page[i] for i in range(1, 115)], [first_juz[i] for i in range(1, 115)]


def test_surah_first_page_matches_canonical():
    pages, _ = _canonical()
    assert _ts_table("SURAH_FIRST_PAGE") == pages
    assert pages[17] == 293  # Al-Kahf


def test_surah_first_juz_matches_canonical():
    _, juz = _canonical()
    assert _ts_table("SURAH_FIRST_JUZ") == juz
