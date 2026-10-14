#!/usr/bin/env python3
"""
Build data/raw/quran_tanzil.json, the canonical Qur'an text of the app, from
the verbatim Tanzil files in data/raw/tanzil/.

Why Tanzil: its licence (CC BY 3.0) explicitly allows use "in any website or
application" with attribution and a link to tanzil.net, verbatim only. The
previous source (KFGQPC's Hafs text, assets/hafs_smart_v8.json, byte-identical
to data/raw/quran_uthmani.json) grants no redistribution rights. Verse-by-verse
comparison shows the two are the same Mushaf: identical letters in all 6,236
verses apart from encoding conventions (backend/tests/test_quran_text_source.py).

Nothing is edited. Each verse's text, and the Bismillah Tanzil gives for the
first verse of 112 surahs, is copied verbatim. Page and juz numbers come from
Tanzil's metadata (CC BY 3.0). Surah names: "سورة " + Tanzil's Arabic name, and
Tanzil's transliterated name. The Tanzil copyright block travels in the output
as its licence requires.

Usage: python scripts/build_quran_tanzil.py   (writes data/raw/quran_tanzil.json)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "tanzil"
OUT = ROOT / "data" / "raw" / "quran_tanzil.json"


def copyright_block(xml_path: Path) -> str:
    text = xml_path.read_text(encoding="utf-8")
    return text[text.index("<!--") + 4 : text.index("-->")].strip("\n")


def load_ayas(xml_path: Path) -> dict[tuple[int, int], tuple[str, str | None]]:
    out = {}
    for sura in ET.parse(xml_path).getroot().iter("sura"):
        for aya in sura.iter("aya"):
            out[(int(sura.get("index")), int(aya.get("index")))] = (aya.get("text"), aya.get("bismillah"))
    return out


def metadata_table(src: str, name: str) -> list[list[str]]:
    body = src[src.index(f"QuranData.{name} = [") :]
    body = body[: body.index("];")]
    body = "\n".join(line for line in body.split("\n") if not line.strip().startswith("//"))
    return [[x.strip().strip("'\"") for x in m.split(",")] for m in re.findall(r"\[([^\[\]]+)\]", body)]


def main() -> int:
    uthmani = load_ayas(SRC / "quran-uthmani.xml")
    simple = load_ayas(SRC / "quran-simple.xml")
    meta_src = (SRC / "quran-data.js").read_text(encoding="utf-8")
    suras = metadata_table(meta_src, "Sura")  # [start, ayas, order, rukus, name, tname, ename, type]
    page_starts = [(int(s), int(a)) for s, a in metadata_table(meta_src, "Page")]
    juz_starts = [(int(s), int(a)) for s, a in metadata_table(meta_src, "Juz")]

    order = sorted(uthmani)
    if len(order) != 6236 or set(order) != set(simple):
        print(f"unexpected verse set: {len(order)} uthmani, {len(simple)} simple")
        return 1

    def numbering(starts: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
        index, current, result = {k: i + 1 for i, k in enumerate(starts)}, 0, {}
        for key in order:
            current = index.get(key, current)
            result[key] = current
        return result

    pages, juzs = numbering(page_starts), numbering(juz_starts)
    verses = []
    for i, (s, a) in enumerate(order, start=1):
        text, bismillah = uthmani[(s, a)]
        text_simple, bismillah_simple = simple[(s, a)]
        sura = suras[s - 1]
        verses.append({
            "id": i,
            "sura_no": s,
            "sura_name_ar": f"سورة {sura[4]}",
            "sura_name_en": sura[5],
            "aya_no": a,
            "aya_text": text,
            "aya_text_emlaey": text_simple,
            "bismillah": bismillah,
            "bismillah_emlaey": bismillah_simple,
            "page": pages[(s, a)],
            "jozz": juzs[(s, a)],
        })

    sources = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(SRC.iterdir())}
    out = {
        "copyright": {
            "uthmani": copyright_block(SRC / "quran-uthmani.xml"),
            "simple": copyright_block(SRC / "quran-simple.xml"),
            "attribution": "Qur'an text: Tanzil Project (https://tanzil.net), Creative Commons Attribution 3.0. Verbatim; changing it is not allowed.",
        },
        "fields": {
            "aya_text": "Tanzil Uthmani text, verbatim",
            "aya_text_emlaey": "Tanzil Simple text, verbatim",
            "bismillah": "Tanzil's Bismillah for the first verse of the surah (Uthmani), verbatim; not part of the verse",
            "bismillah_emlaey": "the same, Simple text",
            "page": "Madinah Mushaf page (Tanzil metadata)",
            "jozz": "juz (Tanzil metadata)",
        },
        "source_sha256": sources,
        "verses": verses,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(verses)} verses, {sum(1 for v in verses if v['bismillah'])} with a Bismillah")
    return 0


if __name__ == "__main__":
    sys.exit(main())
