#!/usr/bin/env python3
"""
Re-source the Qur'an text embedded in curated frontend data from the canonical
Tanzil text (data/raw/quran_tanzil.json), by reference, without editing words.

- frontend/src/data/surahAtlas.ts: firstAyahPreview / lastAyahPreview are the
  full first and last verse of each surah.
- frontend/src/data/quranicDuas.ts: ayatUthmani is the dua as quoted: whole
  verses or an excerpt, verses joined by " ۝ ". Each "۝"-separated segment is
  located in its verse by its letters (diacritics ignored) and replaced by the
  same word span of the Tanzil verse. A segment that is not a contiguous
  excerpt (words dropped from the middle) is replaced by the complete verse:
  the app never shows an abridged verse as Qur'an text. Each such case is
  reported.

Usage: python scripts/resource_curated_verse_text.py [--check]
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TANZIL = {(v["sura_no"], v["aya_no"]): v for v in
          json.loads((ROOT / "data/raw/quran_tanzil.json").read_text(encoding="utf-8"))["verses"]}
SEP = " ۝ "


def skel(word: str) -> str:
    w = "".join(ch for ch in word.replace("﻿", "")
                if not unicodedata.category(ch).startswith("M") and ch != "ـ" and not 0x06D6 <= ord(ch) <= 0x06ED)
    w = w.replace("ءا", "ا")
    for a, b in [("ٱ", "ا"), ("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ئ", "ي"), ("ؤ", "و"), ("ة", "ه")]:
        w = w.replace(a, b)
    return w


def words(text: str) -> list[tuple[int, str]]:
    """(token index, skeleton) for tokens that are words, not pause marks."""
    return [(i, skel(t)) for i, t in enumerate(text.split()) if skel(t)]


def excerpt(segment: str, verse_text: str) -> str | None:
    """The Tanzil span of verse_text whose letters equal segment's, or None."""
    want = [s for _, s in words(segment)]
    have = words(verse_text)
    tokens = verse_text.split()
    for start in range(len(have) - len(want) + 1):
        if [s for _, s in have[start:start + len(want)]] == want:
            first, last = have[start][0], have[start + len(want) - 1][0]
            # keep a pause mark that directly follows the last word, as the excerpt did
            if segment.split()[-1:] and not skel(segment.split()[-1]) and last + 1 < len(tokens) and not skel(tokens[last + 1]):
                last += 1
            return " ".join(tokens[first:last + 1])
    return None


expanded: list[str] = []


def resource_duas(check: bool) -> list[str]:
    path = ROOT / "frontend/src/data/quranicDuas.ts"
    src = path.read_text(encoding="utf-8")
    problems: list[str] = []
    pattern = re.compile(r"(surah:\s*(\d+),\s*ayah:\s*(\d+)(?:,\s*ayahEnd:\s*(\d+))?[\s\S]*?ayatUthmani:\s*')([^']*)(')")

    def fix(m: re.Match) -> str:
        sura, aya = int(m.group(2)), int(m.group(3))
        end = int(m.group(4)) if m.group(4) else aya
        segments = m.group(5).split(SEP)
        verses = list(range(aya, end + 1))
        out, v = [], 0
        for seg in segments:
            if v >= len(verses):
                problems.append(f"quranicDuas {sura}:{aya}-{end}: more segments than verses")
                return m.group(0)
            found = excerpt(seg, TANZIL[(sura, verses[v])]["aya_text"])
            if found is None:
                # Not a contiguous excerpt of this verse: use the whole verse.
                found = TANZIL[(sura, verses[v])]["aya_text"]
                expanded.append(f"quranicDuas {sura}:{verses[v]}: abridged quote replaced by the complete verse")
            out.append(found)
            v += 1
        return m.group(1) + SEP.join(out) + m.group(6)

    new = pattern.sub(fix, src)
    for e in expanded:
        print("EXPANDED", e)
    if not check:
        path.write_text(new, encoding="utf-8")
    return problems


def resource_surah_atlas(check: bool) -> list[str]:
    path = ROOT / "frontend/src/data/surahAtlas.ts"
    src = path.read_text(encoding="utf-8")
    last = {}
    for s, a in TANZIL:
        last[s] = max(last.get(s, 0), a)
    parts = re.split(r"(?=surahNumber:\s*\d+,)", src)
    for i, part in enumerate(parts[1:], start=1):
        n = int(re.match(r"surahNumber:\s*(\d+)", part).group(1))
        part = re.sub(r'(firstAyahPreview:\s*")[^"]*(")',
                      lambda m: m.group(1) + TANZIL[(n, 1)]["aya_text"] + m.group(2), part, count=1)
        part = re.sub(r'(lastAyahPreview:\s*")[^"]*(")',
                      lambda m: m.group(1) + TANZIL[(n, last[n])]["aya_text"] + m.group(2), part, count=1)
        parts[i] = part
    if not check:
        path.write_text("".join(parts), encoding="utf-8")
    return []


if __name__ == "__main__":
    check = "--check" in sys.argv
    issues = resource_surah_atlas(check) + resource_duas(check)
    for p in issues:
        print("UNRESOLVED", p)
    print(f"{'checked' if check else 'rewrote'}: {len(issues)} unresolved")
    sys.exit(1 if issues else 0)
