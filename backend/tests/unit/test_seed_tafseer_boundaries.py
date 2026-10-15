"""
Restoring the lost space between a quoted Qur'an span and the commentary.

In ~458 Tabari and 63 Qurtubi chunks a vowelled Qur'an fragment runs straight
into the commentary ('بِكَلِمَاتٍقال أبو جعفر'), so the Qur'anic word looks
altered. seed_tafseer.restore_quote_boundaries inserts one U+0020 there and
nothing else: the letters and marks are byte-identical once spaces are removed.
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts" / "ingest"))

from seed_tafseer import _GLUED, _is_vowelled_quote, restore_quote_boundaries  # noqa: E402

FIXED = [
    ("وَإِذِ ابْتَلَى إِبْرَاهِيمَ رَبُّهُ بِكَلِمَاتٍقال أبو جعفر", "بِكَلِمَاتٍ قال أبو جعفر"),
    ("وَمَلَئِهِ فَاتَّبَعُوا أَمْرَ فِرْعَوْنَأي شأنه", "فِرْعَوْنَ أي شأنه"),
    ("وَلا تُؤْمِنُوا بِهِقال أبو جعفر", "بِهِ قال"),
    ("وَأَنْتُمْ تَعْلَمُونَ مِنَ النَّاسِقال أبو جعفر", "النَّاسِ قال"),
    ("فِي الْيَوْمِ الآخِرِيعني بذلك", "الآخِرِ يعني"),
]

UNCHANGED = [
    "قال ابن عباس: يُقال يوم القيامة",
    "استرجع عُمر فَقال: إنا لله",
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
    assert glued_before > 400 and restored > 700
