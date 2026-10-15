"""
Frequency claims in frontend content, recounted against the canonical text.

QuranWondersPage once said سجيل, إستبرق and قسطاس each occur only once (they
occur 3, 4 and 2 times). Every countable claim the UI makes about word or
phrase frequency is listed here with the file that makes it, and recounted
from data/raw/quran_tanzil.json, so a wrong number cannot ship again.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
TANZIL = ROOT / "data" / "raw" / "quran_tanzil.json"
FRONTEND = ROOT / "frontend" / "src"

_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def _norm(text: str) -> str:
    text = _DIACRITICS.sub("", text)
    text = re.sub("[آأإٱ]", "ا", text)
    return text.replace("ى", "ي").replace("ة", "ه")


@pytest.fixture(scope="module")
def verses():
    data = json.loads(TANZIL.read_text(encoding="utf-8"))
    return [(v["sura_no"], v["aya_no"], _norm(v["aya_text_emlaey"]), v) for v in data["verses"]]


def _verses_with(verses, phrase, sura=None):
    p = _norm(phrase)
    return [(s, a) for s, a, t, _ in verses if p in t and (sura is None or s == sura)]


def _name_count(verses, name):
    pat = re.compile(r"(?:و|ف|ب|ك|يا)?(?:ل)?" + _norm(name))
    return sum(1 for _, _, t, _ in verses for w in t.split() if pat.fullmatch(w))


def _source(rel):
    return (FRONTEND / rel).read_text(encoding="utf-8")


# (file making the claim, text that must appear there, phrase, sura or None, claimed count)
PHRASE_CLAIMS = [
    ("data/quranicTrivia.ts", "31 times", "فبأي آلاء ربكما تكذبان", 55, 31),
    ("pages/QuranWondersPage.tsx", "in six verses (12:2, 20:113, 39:28, 41:3, 42:7, 43:3)",
     "قرآنا عربيا", None, 6),
]

NAME_CLAIMS = [
    ("data/quranicTrivia.ts", "136 times", "موسى", 136),
    ("data/quranicTrivia.ts", "Ibrahim is mentioned 69 times", "إبراهيم", 69),
    ("data/quranicTrivia.ts", "mentioned 25 times", "عيسى", 25),
    ("data/quranicTrivia.ts", "by name only 4 times", "محمد", 4),
]


@pytest.mark.parametrize("rel,marker,phrase,sura,claimed", PHRASE_CLAIMS)
def test_phrase_counts(verses, rel, marker, phrase, sura, claimed):
    assert marker in _source(rel), f"claim no longer in {rel}; update this list"
    assert len(_verses_with(verses, phrase, sura)) == claimed


@pytest.mark.parametrize("rel,marker,name,claimed", NAME_CLAIMS)
def test_name_counts(verses, rel, marker, name, claimed):
    assert marker in _source(rel), f"claim no longer in {rel}; update this list"
    assert _name_count(verses, name) == claimed


def test_bismillah_total(verses):
    """Trivia: 114 = 113 surah openings (1:1 included, not 9) + 27:30."""
    assert "Bismillah appears 114 times" in _source("data/quranicTrivia.ts")
    openings = sum(1 for _, _, _, v in verses if v.get("bismillah"))
    in_text = _verses_with(verses, "بسم الله الرحمن الرحيم")
    assert in_text == [(1, 1), (27, 30)]
    assert openings + len(in_text) == 114


@pytest.mark.parametrize("word,expected", [
    ("سجيل", [(11, 82), (15, 74), (105, 4)]),
    ("استبرق", [(18, 31), (44, 53), (55, 54), (76, 21)]),
    ("قسطاس", [(17, 35), (26, 182)]),
])
def test_removed_hapax_claim_stays_removed(verses, word, expected):
    """These words occur more than once, so no page may call them hapax."""
    hits = [(s, a) for s, a, t, _ in verses if any(word in w for w in t.split())]
    assert hits == expected
    wonders = _source("pages/QuranWondersPage.tsx")
    assert "w_hapax_legomena" not in wonders
    assert "only once" not in wonders.lower() and "إلا مرة واحدة" not in wonders
