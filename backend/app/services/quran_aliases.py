"""
Curated alias map for well-known Quranic verse/surah names.

These are verse or surah *names* (metadata labels) that do not appear as literal
text inside the Quran. Searching "آية الكرسي" would return 0 results against
text_imlaei / text_normalized because no verse contains that phrase.

Rules:
- Every entry is hand-curated and cites the authoritative surah:ayah reference.
- No model-generated aliases. No speculative aliases.
- Quran text is never modified; only references are stored here.
- match_type = "alias" distinguishes these from full-text and concept hits.

To add a new alias:
1. Confirm the canonical reference in the mushaf.
2. Add all spelling variants the user is likely to type (with/without hamza,
   with/without diacritics, transliteration variants).
3. Record sura_no, aya_start, aya_end (None for single-verse aliases).
4. Add a test in tests/unit/test_quran_aliases.py.
"""
from __future__ import annotations

import re
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class AliasTarget:
    sura_no: int
    aya_start: int          # first (or only) ayah
    aya_end: Optional[int]  # last ayah in range; None = single verse
    label_ar: str           # canonical Arabic label for display
    label_en: str           # canonical English label for display


# ---------------------------------------------------------------------------
# Arabic diacritics for alias-key normalisation (same ranges as quran_search)
# ---------------------------------------------------------------------------
_DIACRITIC_RE = re.compile(
    r'[ؐ-ًؚ-ٰٟۖ-ۜ۟-۪ۤۧۨ-ۭ]'
)


def _norm_key(text: str) -> str:
    """Lowercase + strip Arabic diacritics + collapse whitespace."""
    stripped = _DIACRITIC_RE.sub('', text)
    return re.sub(r'\s+', ' ', stripped).strip().lower()


# ---------------------------------------------------------------------------
# Curated alias table
# key  = canonical spelling (will also be registered under _norm_key variants)
# ---------------------------------------------------------------------------
_RAW: list[tuple[list[str], AliasTarget]] = [

    # ── Ayat al-Kursi (2:255) ───────────────────────────────────────────────
    (
        [
            'آية الكرسي',
            'اية الكرسي',
            'آيه الكرسي',
            'ايه الكرسي',
            'آية الكُرسي',
            'Ayat al-Kursi',
            'Ayatul Kursi',
            'Ayat al Kursi',
            'Ayat ul Kursi',
            'Ayat-ul-Kursi',
            'Ayatul-Kursi',
        ],
        AliasTarget(
            sura_no=2,
            aya_start=255,
            aya_end=None,
            label_ar='آية الكرسي',
            label_en='Ayat al-Kursi',
        ),
    ),

    # ── Al-Fatihah (Surah 1, all 7 verses) ──────────────────────────────────
    (
        [
            'سورة الفاتحة',
            'الفاتحة',
            'سورة الفاتحه',
            'الفاتحه',
            'Al-Fatihah',
            'Al Fatihah',
            'Al-Fatiha',
            'Al Fatiha',
            'Fatiha',
            'Fatihah',
            'Surah Al-Fatihah',
            'Surah Fatiha',
        ],
        AliasTarget(
            sura_no=1,
            aya_start=1,
            aya_end=7,
            label_ar='سورة الفاتحة',
            label_en='Al-Fatihah',
        ),
    ),

    # ── Surah Al-Kahf (Surah 18) — top of surah ─────────────────────────────
    (
        [
            'سورة الكهف',
            'الكهف',
            'Al-Kahf',
            'Al Kahf',
            'Surah Al-Kahf',
            'Surah Kahf',
            'Kahf',
        ],
        AliasTarget(
            sura_no=18,
            aya_start=1,
            aya_end=None,
            label_ar='سورة الكهف',
            label_en='Surah Al-Kahf',
        ),
    ),

    # ── Companions / People of the Cave (18:9-26) ────────────────────────────
    (
        [
            'أصحاب الكهف',
            'اصحاب الكهف',
            'فتية الكهف',
            'People of the Cave',
            'Companions of the Cave',
            'Sleepers of the Cave',
            'Ashab al-Kahf',
            'Ashab al Kahf',
            'Seven Sleepers',
        ],
        AliasTarget(
            sura_no=18,
            aya_start=9,
            aya_end=26,
            label_ar='أصحاب الكهف',
            label_en='People of the Cave',
        ),
    ),

    # ── Dhul-Qarnayn (18:83-98) ──────────────────────────────────────────────
    (
        [
            'ذو القرنين',
            'ذو القرنين',       # without tanwin on ذو
            'Dhul-Qarnayn',
            'Dhul Qarnayn',
            'Dhul Qarnain',
            'Zul Qarnayn',
            'Zulqarnayn',
            'Dhulqarnayn',
        ],
        AliasTarget(
            sura_no=18,
            aya_start=83,
            aya_end=98,
            label_ar='ذو القرنين',
            label_en='Dhul-Qarnayn',
        ),
    ),

    # ── Last two surahs (Al-Falaq + An-Nas) — commonly called "al-Mu'awwidhatayn"
    (
        [
            'المعوذتان',
            'المعوذتين',
            'al-Muawwidhatayn',
            'al Muawwidhatayn',
            'Muawwidhatayn',
        ],
        AliasTarget(
            sura_no=113,
            aya_start=1,
            aya_end=None,
            label_ar='المعوذتان',
            label_en='Al-Mu\'awwidhatayn (Al-Falaq)',
        ),
    ),

    # ── Surah Al-Ikhlas (112) ────────────────────────────────────────────────
    (
        [
            'سورة الإخلاص',
            'الإخلاص',
            'سورة الاخلاص',
            'الاخلاص',
            'قل هو الله أحد',
            'Al-Ikhlas',
            'Al Ikhlas',
            'Surah Al-Ikhlas',
            'Surah Ikhlas',
            'Ikhlas',
        ],
        AliasTarget(
            sura_no=112,
            aya_start=1,
            aya_end=4,
            label_ar='سورة الإخلاص',
            label_en='Al-Ikhlas',
        ),
    ),

    # ── Surah Yasin (36) ─────────────────────────────────────────────────────
    (
        [
            'سورة يس',
            'يس',
            'يٰسٓ',
            'Surah Yasin',
            'Surah Ya-Sin',
            'Yasin',
            'Ya-Sin',
        ],
        AliasTarget(
            sura_no=36,
            aya_start=1,
            aya_end=None,
            label_ar='سورة يس',
            label_en='Surah Yasin',
        ),
    ),

    # ── Throne verse context — Surah Al-Baqarah verse 256 (لا إكراه في الدين)
    # Not an alias — no well-known metadata name; intentionally excluded.

    # ── Surah Al-Mulk (67) ───────────────────────────────────────────────────
    (
        [
            'سورة الملك',
            'الملك',
            'تبارك',
            'Al-Mulk',
            'Al Mulk',
            'Surah Al-Mulk',
            'Surah Mulk',
            'Tabarak',
        ],
        AliasTarget(
            sura_no=67,
            aya_start=1,
            aya_end=None,
            label_ar='سورة الملك',
            label_en='Al-Mulk',
        ),
    ),

    # ── Surah Ar-Rahman (55) ─────────────────────────────────────────────────
    (
        [
            'سورة الرحمن',
            'الرحمن',
            'Ar-Rahman',
            'Surah Ar-Rahman',
            'Surah Rahman',
            'Rahman',
        ],
        AliasTarget(
            sura_no=55,
            aya_start=1,
            aya_end=None,
            label_ar='سورة الرحمن',
            label_en='Ar-Rahman',
        ),
    ),
]

# ---------------------------------------------------------------------------
# Build the lookup dict (normalised key → AliasTarget)
# ---------------------------------------------------------------------------
ALIAS_MAP: dict[str, AliasTarget] = {}
for _spellings, _target in _RAW:
    for _s in _spellings:
        _k = _norm_key(_s)
        if _k in ALIAS_MAP and ALIAS_MAP[_k] != _target:
            raise ValueError(f"Alias collision on normalised key '{_k}'")
        ALIAS_MAP[_k] = _target


def resolve_alias(query: str) -> Optional[AliasTarget]:
    """
    Return AliasTarget if query matches a known Quranic verse/surah name,
    otherwise None.

    Matching is case-insensitive and diacritic-insensitive.
    """
    return ALIAS_MAP.get(_norm_key(query))
