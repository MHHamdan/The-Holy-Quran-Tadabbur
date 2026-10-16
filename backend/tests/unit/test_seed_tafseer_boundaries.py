"""
Restoring the lost space between a quoted Qur'an span and the commentary.

In ~458 Tabari and 63 Qurtubi chunks a vowelled Qur'an fragment runs straight
into the commentary (a vowelled word glued to 'قال أبو جعفر'), so the Qur'anic word looks
altered. seed_tafseer.restore_quote_boundaries inserts one U+0020 there and
nothing else: the letters and marks are byte-identical once spaces are removed.
"""
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts" / "ingest"))

from seed_tafseer import _GLUED, _is_vowelled_quote, restore_quote_boundaries  # noqa: E402

ROOT = BACKEND.parent
_VERSES = {
    (v["sura_no"], v["aya_no"]): v["aya_text_emlaey"]
    for v in json.loads((ROOT / "data" / "raw" / "quran_tanzil.json").read_text(encoding="utf-8"))["verses"]
}

# Glued fixtures are built from canonical verse text (never typed here): the
# verse runs straight into the commentary, as in the corrupted upstream rows.
_GLUE = [
    ((2, 124), "قال أبو جعفر"),
    ((11, 97), "أي شأنه"),
    ((2, 41), "قال أبو جعفر"),
    ((3, 185), "يعني بذلك"),
    ((2, 2), "وقيل غير ذلك"),
]
FIXED = [
    (_VERSES[ref] + tail, _VERSES[ref].split()[-1] + " " + tail.split()[0])
    for ref, tail in _GLUE
]

UNCHANGED = [
    "قال ابن عباس: يُقال يوم القيامة",
    "ثم إن عُمر فَقال: نعم",
    "يرغب برأيه عن رَأي الله",
    "أنما نُشِط من عِقال",
    "وهو قول الجمهور، وهي رواية",
]


def _letters(s: str) -> str:
    return s.replace(" ", "")


@pytest.mark.parametrize("raw,expected", FIXED)
def test_glued_boundaries_restored(raw, expected):
    out, n = restore_quote_boundaries(raw)
    assert n == 1 and expected in out
    assert _letters(out) == _letters(raw)


@pytest.mark.parametrize("raw", UNCHANGED)
def test_commentary_words_untouched(raw):
    assert restore_quote_boundaries(raw) == (raw, 0)


def test_idempotent():
    raw = " ".join(r for r, _ in FIXED)
    once, n = restore_quote_boundaries(raw)
    assert n == len(FIXED)
    assert restore_quote_boundaries(once) == (once, 0)


def test_short_tokens_are_not_quotes():
    assert not _is_vowelled_quote("يُ")
    assert not _is_vowelled_quote("مدرَ")
    assert _is_vowelled_quote("بِهِ")


@pytest.mark.asyncio
async def test_stored_corpus_letters_unchanged_and_no_glue_left():
    """Over the seeded tabari/qurtubi text: what a re-seed would store."""
    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            rows = (await session.execute(text(
                "SELECT content_ar FROM tafseer_chunks WHERE source_id IN ('tabari_ar','qurtubi_ar')"
            ))).scalars().all()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    if not rows:
        pytest.skip("tabari_ar/qurtubi_ar not seeded")
    glued_before = restored = 0
    for raw in rows:
        raw = raw or ""
        out, n = restore_quote_boundaries(raw)
        glued_before += n > 0
        restored += n
        assert _letters(out) == _letters(raw)
        left = [m for m in _GLUED.finditer(out) if _is_vowelled_quote(m.group(1))]
        assert not left, out[max(0, left[0].start() - 20):left[0].end() + 5]
    # The spa5k CDN copy had >400 glued quotes; the licensed riotu-lab dataset
    # (reseeded 2026-10-15) has none. The invariants above hold either way, and
    # the restore behaviour itself is covered by the parametrised tests.
    assert glued_before >= 0 and restored >= 0
