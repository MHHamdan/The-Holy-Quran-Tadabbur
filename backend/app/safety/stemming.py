"""
Stemmers for the cross-lingual evidence view (no external dependencies).

* ``porter`` — the classic Porter (1980) English suffix-stripping algorithm.
* ``arabic_stem`` — a light Arabic stemmer: clitics (و ف ب ل ك س ال), object
  and possessive pronoun suffixes, verb person suffixes and the imperfect
  prefix are removed, keeping at least three letters, so "أصابته",
  "أصابتكم", "يصيب" and "أصاب" fall together more often than not.
"""
from __future__ import annotations

from functools import lru_cache

# ------------------------------------------------------------------ Porter

_VOWELS = "aeiou"


def _cons(w: str, i: int) -> bool:
    ch = w[i]
    if ch in _VOWELS:
        return False
    if ch == "y":
        return i == 0 or not _cons(w, i - 1)
    return True


def _m(stem: str) -> int:
    """Number of VC sequences in ``stem``."""
    n, i, L = 0, 0, len(stem)
    while i < L and _cons(stem, i):
        i += 1
    while i < L:
        while i < L and not _cons(stem, i):
            i += 1
        if i >= L:
            break
        while i < L and _cons(stem, i):
            i += 1
        n += 1
    return n


def _has_vowel(stem: str) -> bool:
    return any(not _cons(stem, i) for i in range(len(stem)))


def _double_cons(w: str) -> bool:
    return len(w) >= 2 and w[-1] == w[-2] and _cons(w, len(w) - 1)


def _cvc(w: str) -> bool:
    if len(w) < 3:
        return False
    return (_cons(w, len(w) - 3) and not _cons(w, len(w) - 2) and _cons(w, len(w) - 1)
            and w[-1] not in "wxy")


def _replace(w: str, suffix: str, rep: str, cond) -> tuple:
    if w.endswith(suffix):
        stem = w[: len(w) - len(suffix)]
        if cond(stem):
            return stem + rep, True
        return w, True
    return w, False


_STEP2 = (("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"), ("izer", "ize"),
          ("abli", "able"), ("alli", "al"), ("entli", "ent"), ("eli", "e"), ("ousli", "ous"),
          ("ization", "ize"), ("ation", "ate"), ("ator", "ate"), ("alism", "al"), ("iveness", "ive"),
          ("fulness", "ful"), ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"))
_STEP3 = (("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"), ("ical", "ic"), ("ful", ""),
          ("ness", ""))
_STEP4 = ("al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement", "ment", "ent", "ion", "ou",
          "ism", "ate", "iti", "ous", "ive", "ize")


@lru_cache(maxsize=65536)
def porter(word: str) -> str:
    w = word.lower()
    if len(w) <= 2:
        return w
    # Step 1a
    if w.endswith("sses"):
        w = w[:-2]
    elif w.endswith("ies"):
        w = w[:-2]
    elif w.endswith("ss"):
        pass
    elif w.endswith("s"):
        w = w[:-1]
    # Step 1b
    flag = False
    if w.endswith("eed"):
        if _m(w[:-3]) > 0:
            w = w[:-1]
    elif w.endswith("ed") and _has_vowel(w[:-2]):
        w, flag = w[:-2], True
    elif w.endswith("ing") and _has_vowel(w[:-3]):
        w, flag = w[:-3], True
    if flag:
        if w.endswith(("at", "bl", "iz")):
            w += "e"
        elif _double_cons(w) and w[-1] not in "lsz":
            w = w[:-1]
        elif _m(w) == 1 and _cvc(w):
            w += "e"
    # Step 1c
    if w.endswith("y") and _has_vowel(w[:-1]):
        w = w[:-1] + "i"
    # Step 2
    for suf, rep in _STEP2:
        w, hit = _replace(w, suf, rep, lambda st: _m(st) > 0)
        if hit:
            break
    # Step 3
    for suf, rep in _STEP3:
        w, hit = _replace(w, suf, rep, lambda st: _m(st) > 0)
        if hit:
            break
    # Step 4
    for suf in _STEP4:
        if w.endswith(suf):
            stem = w[: len(w) - len(suf)]
            if _m(stem) > 1 and (suf != "ion" or stem.endswith(("s", "t"))):
                w = stem
            break
    # Step 5
    if w.endswith("e"):
        stem = w[:-1]
        if _m(stem) > 1 or (_m(stem) == 1 and not _cvc(stem)):
            w = stem
    if _m(w) > 1 and _double_cons(w) and w.endswith("l"):
        w = w[:-1]
    return w


# ------------------------------------------------------------------ Arabic

_AR_PROCLITICS = ("وبال", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك", "س")
_AR_ENCLITICS = ("كموها", "تموها", "هما", "كما", "تما", "هم", "هن", "كم", "كن", "نا", "ها", "ني", "ه", "ك", "ي")
_AR_VERB_SUFFIXES = ("تم", "وا", "ون", "ين", "ات", "ت")


@lru_cache(maxsize=131072)
def arabic_stem(token: str) -> str:
    """Light stem of a normalised Arabic token (see module doc)."""
    t = token
    # Accusative tanween carrier ("أعرابيًا" -> "أعرابي"), not the plural "وا".
    if len(t) >= 4 and t.endswith("ا") and not t.endswith(("وا", "اا")):
        t = t[:-1]
    for p in _AR_PROCLITICS:
        # The conjunctions و/ف before any 3+ letter word; the prepositions
        # ب/ل/ك/س only before 4+ letters ("بيوت" is not "ب" + "يوت").
        if t.startswith(p) and len(t) - len(p) >= (3 if len(p) > 1 or p in "وف" else 4):
            t = t[len(p):]
            break
    for s in _AR_ENCLITICS:
        if t.endswith(s) and len(t) - len(s) >= 3:
            t = t[: -len(s)]
            break
    for s in _AR_VERB_SUFFIXES:
        if t.endswith(s) and len(t) - len(s) >= 3:
            t = t[: -len(s)]
            break
    if len(t) >= 4 and t[0] in "يتنا":
        t = t[1:]
    if len(t) >= 4 and t.endswith("ه"):
        t = t[:-1]  # ta marbuta (normalised to ه)
    return t
