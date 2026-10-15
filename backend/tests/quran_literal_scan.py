"""
Find hand-typed Qur'an text in the frontend sources.

An Arabic run whose letter skeleton occurs in the Qur'an must be a byte-exact
substring of the canonical Tanzil text (aya_text or aya_text_emlaey of one
verse, or of consecutive verses joined by a space or ' ۝ '). Anything else is
Qur'an text that was typed or altered by hand. A run is checked when it is
  - vowelled (3+ harakat): 2+ words and a skeleton of 8+ letters;
  - unvowelled or lightly vowelled: 4+ words and 14+ letters (canonical text
    is always vowelled, so such a run can never match it).
Exceptions (dhikr formulas or hadith wording that overlaps the Qur'an) go in
quran_literal_allowlist.json with a reason. Fields that a generator derives
mechanically from the canonical text are listed in DERIVED_FIELDS and are
checked against their record's verse by test_quran_canonical_integrity.py.

Used by tests/test_quran_canonical_integrity.py; run directly to list hits:
    python tests/quran_literal_scan.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TANZIL = ROOT / "data" / "raw" / "quran_tanzil.json"
FRONTEND = ROOT / "frontend" / "src"
ALLOWLIST = Path(__file__).resolve().parent / "quran_literal_allowlist.json"

_HARAKAT = re.compile("[ً-ْٰ]")
# An Arabic run: Arabic letters/marks/Qur'anic signs and the spaces between
# them. Quotes, brackets, digits, Latin text and ':' end a run.
_RUN = re.compile("[ؐ-ؚء-ٰٟ-ۓە-ۭۺ-ۿـ](?:[ؐ-ؚء-ٰٟ-ۭۺ-ۿـ ]*[ؐ-ؚء-ٰٟ-ۭۺ-ۿـ])?")


def skeleton(text: str) -> str:
    """Letters only: no marks, tatweel, pause signs; seat/alif variants unified."""
    out = []
    for ch in text.replace("﻿", ""):
        if unicodedata.category(ch).startswith("M") or ch == "ـ" or 0x06D6 <= ord(ch) <= 0x06ED or ch in "۞۩":
            continue
        out.append(ch)
    t = "".join(out).replace("ءا", "ا")
    for a, b in (("ٱ", "ا"), ("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ئ", "ي"), ("ؤ", "و"), ("ة", "ه"), ("ء", "")):
        t = t.replace(a, b)
    return re.sub(r"\s+", "", t)


@lru_cache(maxsize=1)
def canonical():
    verses = json.loads(TANZIL.read_text(encoding="utf-8"))["verses"]
    texts = []
    skel = []
    for i, v in enumerate(verses):
        texts.append(v["aya_text"])
        texts.append(v["aya_text_emlaey"])
        # Both scripts: Uthmani writes some long vowels as marks (dagger alif),
        # the simple script as letters, so their skeletons differ.
        skel.append(skeleton(v["aya_text"]))
        skel.append(skeleton(v["aya_text_emlaey"]))
        if i + 1 < len(verses) and verses[i + 1]["sura_no"] == v["sura_no"]:
            nxt = verses[i + 1]
            for sep in (" ", " ۝ "):
                texts.append(v["aya_text"] + sep + nxt["aya_text"])
                texts.append(v["aya_text_emlaey"] + sep + nxt["aya_text_emlaey"])
            skel.append(skeleton(v["aya_text"] + nxt["aya_text"]))
            skel.append(skeleton(v["aya_text_emlaey"] + nxt["aya_text_emlaey"]))
    return "\n".join(texts), "\n".join(skel)


# Generated JSON fields copied from the canonical verse by a script, e.g. the
# call phrase that scripts/scan-quranic-calls.ts cuts from the diacritic-
# stripped aya_text_emlaey. Lines holding these keys are not scanned.
DERIVED_FIELDS = {
    "frontend/src/data/generated/quranicCallsAtlas.json": ('"callText":',),
    "frontend/src/data/generated/quranicCallsClassified.json": ('"callText":',),
}


def needs_check(run: str) -> bool:
    """Whether a run is long or vowelled enough to be a Qur'an quotation."""
    harakat = len(_HARAKAT.findall(run))
    words = len(run.split())
    letters = len(skeleton(run))
    if words >= 2 and harakat >= 3:
        return letters >= 8
    if words >= 4:
        return letters >= 14
    return False


def _allowlist() -> list:
    if not ALLOWLIST.exists():
        return []
    return json.loads(ALLOWLIST.read_text(encoding="utf-8"))["entries"]


def scan(paths=None):
    """[(relative_path, line_no, run)] for non-verbatim Qur'an-skeleton runs."""
    canon_text, canon_skel = canonical()
    allowed = {(e["file"], e["text"]) for e in _allowlist()}
    hits = []
    files = paths or sorted(
        p for p in FRONTEND.rglob("*")
        if p.suffix in {".ts", ".tsx", ".json"} and "node_modules" not in p.parts
    )
    for path in files:
        rel = str(path.relative_to(ROOT))
        derived = DERIVED_FIELDS.get(rel, ())
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if derived and line.lstrip().startswith(derived):
                continue
            # ' ۝ ' joins separate quoted segments; each must be verbatim.
            segments = (seg for m in _RUN.finditer(line) for seg in m.group(0).split("۝"))
            for run in segments:
                run = run.strip()
                if not needs_check(run) or skeleton(run) not in canon_skel:
                    continue
                if run in canon_text or (rel, run) in allowed:
                    continue
                hits.append((rel, n, run))
    return hits


if __name__ == "__main__":
    found = scan([Path(a).resolve() for a in sys.argv[1:]] or None)
    for rel, n, run in found:
        print(f"{rel}:{n}: {run[:90]}")
    print(f"{len(found)} non-verbatim Qur'an literals")
