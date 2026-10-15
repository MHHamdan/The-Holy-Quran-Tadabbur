"""
One Arabic search normalizer for the whole search stack.

The seeder (quran_verses.text_normalized / text_imlaei_normalized), query
terms, alias keys and in-Python re-checks must all fold text the same way;
when they disagreed (tatweel kept on one side, ة folded on the other, small
Quranic letters kept in the column) rows the SQL matched were silently
dropped.

This is a *search key*. It is never shown to a reader and never written back
to the canonical text columns (text_uthmani / text_imlaei).
"""
from __future__ import annotations

import re
from functools import lru_cache

# Characters removed before matching:
#   U+0610-U+061A  Quranic honorific/annotation marks
#   U+064B-U+065F  harakat, tanwin, shadda, sukun, hamza marks
#   U+0670         superscript (dagger) alef
#   U+06D6-U+06ED  small Quranic letters, pause marks, rub el hizb, sajda,
#                  small high/low meem, small waw/yeh, etc.
#   U+08D3-U+08FF  extended Quranic annotation marks
#   U+0640         tatweel
#   BOM and zero-width characters
MARKS_RE = re.compile(
    "[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ"
    "﻿​-‏⁠]"
)

_FOLD = str.maketrans({
    "آ": "ا",  # آ -> ا
    "أ": "ا",  # أ -> ا
    "إ": "ا",  # إ -> ا
    "ٱ": "ا",  # ٱ -> ا (alef wasla)
    "ى": "ي",  # ى -> ي
    "ة": "ه",  # ة -> ه
    "ؤ": "و",  # ؤ -> و
    "ئ": "ي",  # ئ -> ي
})

_WS_RE = re.compile(r"\s+")

# Arabic-Indic (U+0660-0669) and Eastern Arabic-Indic (U+06F0-06F9) digits.
_DIGITS = str.maketrans(
    {**{chr(0x0660 + i): str(i) for i in range(10)}, **{chr(0x06F0 + i): str(i) for i in range(10)}}
)

ARABIC_LETTER_RE = re.compile("[ء-يٱ-ۓ]")

# Transliteration marks used by the English editions ("Allāh", "Mūsā", "ʿĀd"),
# folded away on both sides so plain-ASCII queries match. The translations
# folded trigram index (migration ws4a1b2c3d4e5) is built on exactly
# lower(translate(text, TRANSLIT_FOLD_FROM, TRANSLIT_FOLD_TO)); keep them in sync.
TRANSLIT_FOLD_FROM = "āīūĀĪŪḥḤṣṢḍḌṭṬẓẒġĠʿʾ’‘"
TRANSLIT_FOLD_TO = "aiuAIUhHsSdDtTzZgG"  # shorter: the trailing marks are deleted


@lru_cache(maxsize=200_000)
def normalize_for_search(text: str) -> str:
    """Fold Arabic text to its search key.

    >>> normalize_for_search("ٱلرَّحْمَـٰنِ")
    'الرحمن'
    """
    if not text:
        return ""
    t = MARKS_RE.sub("", text)
    t = t.translate(_FOLD)
    return _WS_RE.sub(" ", t).strip()


def fold_digits(text: str) -> str:
    """Map Arabic-Indic digits to ASCII."""
    return text.translate(_DIGITS) if text else ""


def has_arabic(text: str) -> bool:
    return bool(text and ARABIC_LETTER_RE.search(text))


def escape_like(term: str) -> str:
    """Escape LIKE/ILIKE wildcards so user input matches literally (escape char '\\')."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def is_removed_char(ch: str) -> bool:
    """True when normalize_for_search drops this character (zero width in the key)."""
    return bool(MARKS_RE.match(ch))


def key_with_offsets(text: str) -> tuple[str, list[int]]:
    """Return (normalize_for_search(text), offsets) where offsets[i] is the
    index in ``text`` of the character that produced key character i.

    Used to map a match found in the search key back onto the original
    (vowelled) text for highlighting.
    """
    out: list[str] = []
    offs: list[int] = []
    for i, ch in enumerate(text or ""):
        if MARKS_RE.match(ch):
            continue
        if ch.isspace():
            if not out or out[-1] == " ":
                continue
            out.append(" ")
            offs.append(i)
            continue
        out.append(ch.translate(_FOLD))
        offs.append(i)
    while out and out[-1] == " ":
        out.pop()
        offs.pop()
    return "".join(out), offs


def find_spans(text: str, terms) -> list[tuple[int, int]]:
    """Spans (start, end) in the ORIGINAL text where any search term occurs,
    matched on the normalized key. Trailing marks after the last matched
    letter are included so the highlight covers the vowelled letters.
    """
    key, offs = key_with_offsets(text)
    if not key:
        return []
    spans: list[tuple[int, int]] = []
    for term in terms:
        nt = normalize_for_search(term)
        if not nt:
            continue
        start = 0
        while True:
            pos = key.find(nt, start)
            if pos == -1:
                break
            o_start = offs[pos]
            o_end = offs[pos + len(nt) - 1] + 1
            while o_end < len(text) and MARKS_RE.match(text[o_end]):
                o_end += 1
            spans.append((o_start, o_end))
            start = pos + 1
    spans.sort()
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def search_terms(terms, cap: int = 12) -> list[str]:
    """Normalize, de-duplicate and minimise a set of Arabic search terms.

    Non-Arabic terms are dropped (they cannot match verse text). A term that
    contains another kept term is dropped too: a substring match on 'صبر'
    already covers 'الصبر'. At most ``cap`` terms are returned, shortest
    first, so the original query (usually the shortest) survives.
    """
    norm = sorted(
        {normalize_for_search(t) for t in terms if t and has_arabic(t)} - {""},
        key=lambda t: (len(t), t),
    )
    kept: list[str] = []
    for t in norm:
        if any(k in t for k in kept):
            continue
        kept.append(t)
    return kept[:cap]
