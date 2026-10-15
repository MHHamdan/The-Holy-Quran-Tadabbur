"""
Smart search: one entry point that understands what the reader typed.

Pipeline (GET /quran/search/smart):
  a. Reference   "2:255", "٢:٢٥٥", "2 255", "سورة 2:255", "2:255-257", bare "18"
                 -> jump (validated against the verse counts in the database)
  b. Surah name  "البقرة", "سورة البقرة", "Baqarah", "al-baqara" -> surahs[]
  c. Alias       "آية الكرسي" / "Ayat al-Kursi" -> alias (verse kind) or
                 surahs[] (whole-surah kind, never replaces verse results)
  d. Arabic text ILIKE on the normalized columns with a real COUNT total,
                 offset paging and whole-word > prefix > substring > Mushaf
                 order ranking
  e. Translation Latin input searches the default edition of `lang`
  f. Semantic    only when HF is configured and Qdrant answers, under a 5 s
                 timeout; otherwise {available: false}

Every verse text in the response comes from quran_verses.
"""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse, Translation, TranslationEdition
from app.services.arabic_normalize import (
    TRANSLIT_FOLD_FROM,
    TRANSLIT_FOLD_TO,
    escape_like,
    find_spans,
    fold_digits,
    has_arabic,
    normalize_for_search,
)
from app.services.quran_aliases import resolve_alias
from app.services.search_suggestions import SURAH_DATA

logger = logging.getLogger(__name__)

SEMANTIC_TIMEOUT_S = 5.0

_TRANSLIT_TABLE = str.maketrans(
    TRANSLIT_FOLD_FROM[: len(TRANSLIT_FOLD_TO)], TRANSLIT_FOLD_TO, TRANSLIT_FOLD_FROM[len(TRANSLIT_FOLD_TO):]
)

# ---------------------------------------------------------------------------
# a. References
# ---------------------------------------------------------------------------

_SURAH_WORD = r"(?:سور[ةه]|surah?|surat|sura)"
_REF_RE = re.compile(
    rf"^\s*(?:{_SURAH_WORD}\s*)?(\d{{1,3}})\s*[:.\-/ ]\s*(\d{{1,3}})(?:\s*[-–]\s*(\d{{1,3}}))?\s*$",
    re.IGNORECASE,
)
_BARE_RE = re.compile(rf"^\s*(?:{_SURAH_WORD}\s*)?(\d{{1,3}})\s*$", re.IGNORECASE)


def _fold_reference_text(q: str) -> str:
    q = fold_digits(q or "")
    # full-width / small colons and the Arabic comma used as separators
    return q.replace("：", ":").replace("﹕", ":").replace("،", ":")


@dataclass(frozen=True)
class ParsedReference:
    sura_no: int
    aya_no: Optional[int]  # None = whole surah
    aya_end: Optional[int] = None


def parse_reference(q: str) -> Optional[ParsedReference]:
    """Parse a verse/surah reference. Range checks happen against the DB."""
    text = _fold_reference_text(q)
    m = _REF_RE.match(text)
    if m:
        s, a, e = int(m.group(1)), int(m.group(2)), m.group(3)
        return ParsedReference(s, a, int(e) if e else None)
    m = _BARE_RE.match(text)
    if m:
        return ParsedReference(int(m.group(1)), None)
    return None


_VERSE_COUNTS: Dict[int, int] = {}
_SURAH_NAMES: Dict[int, Tuple[str, str]] = {}


async def _load_surah_meta(session: AsyncSession) -> None:
    """Verse counts and DB surah names, loaded once (the Quran is immutable)."""
    if _VERSE_COUNTS:
        return
    rows = (await session.execute(
        select(
            QuranVerse.sura_no,
            func.max(QuranVerse.aya_no),
            func.min(QuranVerse.sura_name_ar),
            func.min(QuranVerse.sura_name_en),
        ).group_by(QuranVerse.sura_no)
    )).all()
    for s, n, ar, en in rows:
        _VERSE_COUNTS[s] = n
        _SURAH_NAMES[s] = (ar, en)


def _surah_entry(no: int) -> Dict[str, Any]:
    ar, en = _SURAH_NAMES.get(no, ("", ""))
    if not ar or not en:
        for n, data_ar, data_en, _ in SURAH_DATA:
            if n == no:
                ar, en = ar or data_ar, en or data_en
                break
    return {"number": no, "name_ar": ar, "name_en": en}


# ---------------------------------------------------------------------------
# b. Surah names
# ---------------------------------------------------------------------------

_LATIN_ARTICLE_RE = re.compile(r"^(?:al|an|ash|as|at|ad|adh|ar|az|ath|aal)[\s\-]+")
_LATIN_PREFIX_RE = re.compile(r"^(?:surah|surat|sura)\s+")


def latin_key(name: str) -> str:
    """Fold a Latin surah name: 'Al-Baqarah', 'al baqara', 'Baqarah' -> 'baqara'."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.translate(_TRANSLIT_TABLE)
    s = re.sub(r"['`’‘ʿʾ]", "", s)
    s = _LATIN_PREFIX_RE.sub("", s.strip())
    stripped = _LATIN_ARTICLE_RE.sub("", s)
    s = stripped
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("ee", "i").replace("oo", "u").replace("ou", "u")
    s = re.sub(r"(.)\1+", r"\1", s)
    if len(s) > 3 and s.endswith("h"):
        s = s[:-1]
    return s


def arabic_surah_key(name: str) -> str:
    k = normalize_for_search(name)
    k = re.sub(r"^سوره\s+", "", k)
    return k


def _arabic_variants(key: str) -> set:
    out = {key}
    if key.startswith("ال") and len(key) > 3:
        out.add(key[2:])
    return out


_SURAH_INDEX: Dict[str, set] = {}


def _surah_index() -> Dict[str, set]:
    """key -> {surah numbers}, from SURAH_DATA and the DB spellings."""
    if _SURAH_INDEX and len(_SURAH_INDEX) > 200:
        return _SURAH_INDEX
    idx: Dict[str, set] = {}

    def add(key: str, no: int):
        if key:
            idx.setdefault(key, set()).add(no)

    for no, ar, en, _meaning in SURAH_DATA:
        for v in _arabic_variants(arabic_surah_key(ar)):
            add(v, no)
        add(latin_key(en), no)
    for no, (ar, en) in _SURAH_NAMES.items():
        for v in _arabic_variants(arabic_surah_key(ar)):
            add(v, no)
        add(latin_key(en), no)
    _SURAH_INDEX.clear()
    _SURAH_INDEX.update(idx)
    return _SURAH_INDEX


def match_surahs(q: str) -> List[int]:
    q = (q or "").strip()
    if not q:
        return []
    idx = _surah_index()
    if has_arabic(q):
        keys = _arabic_variants(arabic_surah_key(q))
    else:
        keys = {latin_key(q)}
        low = q.lower().strip()
        if low.startswith("al") and not _LATIN_ARTICLE_RE.match(low):
            keys.add(latin_key(low[2:]))  # "Albaqara"
    found: set = set()
    for k in keys:
        if len(k) >= 2:
            found |= idx.get(k, set())
    return sorted(found)


# ---------------------------------------------------------------------------
# d. Arabic text
# ---------------------------------------------------------------------------

def _pg_regex_escape(term: str) -> str:
    return re.sub(r"([.^$*+?()\[\]{}|\\-])", r"\\\1", term)


def _verse_item(v: QuranVerse, match_type: str, terms: List[str]) -> Dict[str, Any]:
    spans = find_spans(v.text_uthmani, terms) if terms else []
    highlighted = v.text_uthmani
    if spans:
        parts, last = [], 0
        for s, e in spans:
            parts += [v.text_uthmani[last:s], "【", v.text_uthmani[s:e], "】"]
            last = e
        parts.append(v.text_uthmani[last:])
        highlighted = "".join(parts)
    return {
        "verse_id": v.id,
        "sura_no": v.sura_no,
        "aya_no": v.aya_no,
        "reference": f"{v.sura_no}:{v.aya_no}",
        "sura_name_ar": v.sura_name_ar,
        "sura_name_en": v.sura_name_en,
        "text_uthmani": v.text_uthmani,
        "text_imlaei": v.text_imlaei,
        "highlighted_text": highlighted,
        "page_no": v.page_no,
        "juz_no": v.juz_no,
        "match_type": match_type,
    }


async def search_arabic_text(
    session: AsyncSession, q: str, limit: int, offset: int
) -> Dict[str, Any]:
    term = normalize_for_search(q)
    if not term:
        return {"total": 0, "offset": offset, "items": []}

    rx = _pg_regex_escape(term)
    whole = rf"(^|\s){rx}(\s|$)"
    prefix = rf"(^|\s){rx}"
    short = len(term.replace(" ", "")) <= 2

    if short:
        # 'يس' must not match inside 'ليس'
        cond = or_(QuranVerse.text_normalized.op("~")(whole), QuranVerse.text_imlaei_normalized.op("~")(whole))
    else:
        pattern = f"%{escape_like(term)}%"
        cond = or_(
            QuranVerse.text_normalized.ilike(pattern, escape="\\"),
            QuranVerse.text_imlaei_normalized.ilike(pattern, escape="\\"),
        )

    rank = case(
        (or_(QuranVerse.text_normalized.op("~")(whole), QuranVerse.text_imlaei_normalized.op("~")(whole)), 0),
        (or_(QuranVerse.text_normalized.op("~")(prefix), QuranVerse.text_imlaei_normalized.op("~")(prefix)), 1),
        else_=2,
    )
    total = (await session.execute(select(func.count()).select_from(QuranVerse).where(cond))).scalar_one()
    rows = (await session.execute(
        select(QuranVerse, rank.label("rank")).where(cond).order_by(rank, QuranVerse.id).offset(offset).limit(limit)
    )).all()
    types = {0: "exact", 1: "prefix", 2: "normalized"}
    return {
        "total": total,
        "offset": offset,
        "items": [_verse_item(v, types[r], [term]) for v, r in rows],
    }


# ---------------------------------------------------------------------------
# e. Translation
# ---------------------------------------------------------------------------

async def default_edition_keys(session: AsyncSession, lang: str) -> List[str]:
    rows = await session.execute(
        select(TranslationEdition.key).where(
            TranslationEdition.language == lang, TranslationEdition.is_default.is_(True)
        )
    )
    return list(rows.scalars().all())


def translation_terms(q: str) -> List[str]:
    return [t for t in q.translate(_TRANSLIT_TABLE).lower().split() if len(t) >= 2][:6]


async def search_translation_text(
    session: AsyncSession,
    q: str,
    keys: List[str],
    limit: int,
    offset: int,
) -> Tuple[int, List[Tuple[Translation, QuranVerse]], List[str]]:
    """Verses whose translation contains every word of q (word-start match,
    case- and transliteration-mark-insensitive), in Mushaf order.

    Returns (total, [(translation, verse)], terms). The total comes from a
    window count in the same query (one scan, served by the folded trigram
    index on translations).
    """
    terms = translation_terms(q)
    if not terms or not keys:
        return 0, [], terms
    folded = func.lower(func.translate(Translation.text, TRANSLIT_FOLD_FROM, TRANSLIT_FOLD_TO))
    conditions = [Translation.translator.in_(keys)] + [
        folded.op("~")("\\m" + re.sub(r"([^\w\s])", r"\\\1", t)) for t in terms
    ]
    rows = (await session.execute(
        select(Translation, QuranVerse, func.count().over().label("total"))
        .join(QuranVerse, QuranVerse.id == Translation.verse_id)
        .where(*conditions)
        .order_by(QuranVerse.id, Translation.translator)
        .offset(offset)
        .limit(limit)
    )).all()
    if rows:
        total = rows[0][2]
    elif offset:
        total = (await session.execute(
            select(func.count()).select_from(Translation).where(*conditions)
        )).scalar_one()
    else:
        total = 0
    return total, [(t, v) for t, v, _ in rows], terms


# ---------------------------------------------------------------------------
# f. Semantic (optional)
# ---------------------------------------------------------------------------

async def semantic_section(session: AsyncSession, q: str, limit: int) -> Dict[str, Any]:
    from app.ai.hf_client import hf_configured

    if not hf_configured():
        return {"available": False, "reason": "ai_unavailable", "items": []}
    try:
        from app.services.verse_embedding_service import get_verse_embedding_service

        svc = get_verse_embedding_service()
        stats = await asyncio.wait_for(svc.get_collection_stats(), timeout=SEMANTIC_TIMEOUT_S)
        if not stats.get("exists") or not stats.get("vectors_count"):
            return {"available": False, "reason": "not_indexed", "items": []}
        results = await asyncio.wait_for(
            svc.semantic_search(query=q, limit=limit, min_score=0.3, session=session),
            timeout=SEMANTIC_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        return {"available": False, "reason": "timeout", "items": []}
    except Exception as exc:  # HF / Qdrant failure: degrade, never 5xx
        logger.warning("smart search semantic stage unavailable: %s", type(exc).__name__)
        return {"available": False, "reason": "ai_unavailable", "items": []}
    return {
        "available": True,
        "items": [
            {
                "verse_id": r.verse_id,
                "sura_no": r.sura_no,
                "aya_no": r.aya_no,
                "reference": r.reference,
                "text_uthmani": r.text_uthmani,
                "similarity_score": round(r.similarity_score, 4),
            }
            for r in results
        ],
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def smart_search(
    session: AsyncSession,
    q: str,
    lang: str = "ar",
    limit: int = 20,
    offset: int = 0,
    include_semantic: bool = False,
) -> Dict[str, Any]:
    await _load_surah_meta(session)
    query = (q or "").strip()
    out: Dict[str, Any] = {
        "query": query,
        "intent": "empty",
        "jump": None,
        "reference_error": None,
        "surahs": [],
        "alias": None,
        "verses": {"total": 0, "offset": offset, "items": []},
        "translations": {"total": 0, "offset": offset, "editions": [], "hits": []},
        "semantic": {"available": False, "reason": "not_requested", "items": []},
    }
    if not query:
        return out

    # a. reference
    ref = parse_reference(query)
    if ref is not None:
        count = _VERSE_COUNTS.get(ref.sura_no)
        if count is None:
            out["reference_error"] = {
                "message_ar": f"لا توجد سورة برقم {ref.sura_no}. أرقام السور من 1 إلى 114.",
                "message_en": f"There is no surah {ref.sura_no}. Surahs are numbered 1 to 114.",
            }
        elif ref.aya_no is None:
            out["surahs"] = [_surah_entry(ref.sura_no)]
            out["jump"] = {"sura_no": ref.sura_no, "aya_no": None, "aya_end": None, **_names(ref.sura_no)}
            out["intent"] = "surah"
            return out
        elif not (1 <= ref.aya_no <= count) or (ref.aya_end and not (ref.aya_no <= ref.aya_end <= count)):
            out["reference_error"] = {
                "message_ar": f"{_names(ref.sura_no)['name_ar']} فيها {count} آية فقط.",
                "message_en": f"Surah {ref.sura_no} has {count} verses.",
            }
            out["surahs"] = [_surah_entry(ref.sura_no)]
        else:
            out["jump"] = {"sura_no": ref.sura_no, "aya_no": ref.aya_no, "aya_end": ref.aya_end, **_names(ref.sura_no)}
            v = (await session.execute(
                select(QuranVerse).where(QuranVerse.sura_no == ref.sura_no, QuranVerse.aya_no == ref.aya_no)
            )).scalar_one_or_none()
            if v is not None:
                out["verses"] = {"total": 1, "offset": 0, "items": [_verse_item(v, "reference", [])]}
            out["intent"] = "reference"
            return out
        if out["reference_error"]:
            out["intent"] = "reference"
            return out

    # b. surah names
    surah_nos = match_surahs(query)

    # c. aliases
    alias = resolve_alias(query)
    alias_items: List[Dict[str, Any]] = []
    if alias is not None and alias.kind == "surah":
        if alias.sura_no not in surah_nos:
            surah_nos.append(alias.sura_no)
    elif alias is not None:
        end = alias.aya_end or alias.aya_start
        rows = (await session.execute(
            select(QuranVerse)
            .where(QuranVerse.sura_no == alias.sura_no, QuranVerse.aya_no.between(alias.aya_start, end))
            .order_by(QuranVerse.aya_no)
            .limit(50)
        )).scalars().all()
        alias_items = [_verse_item(v, "alias", []) for v in rows]
        out["alias"] = {
            "sura_no": alias.sura_no,
            "aya_start": alias.aya_start,
            "aya_end": alias.aya_end,
            "label_ar": alias.label_ar,
            "label_en": alias.label_en,
        }
    out["surahs"] = [_surah_entry(n) for n in surah_nos]

    # d. Arabic text
    if has_arabic(query):
        text_res = await search_arabic_text(session, query, limit, offset)
        if alias_items and offset == 0:
            seen = {i["verse_id"] for i in alias_items}
            text_res["items"] = alias_items + [i for i in text_res["items"] if i["verse_id"] not in seen]
            text_res["total"] += len(alias_items)
        out["verses"] = text_res
    elif alias_items:
        out["verses"] = {"total": len(alias_items), "offset": 0, "items": alias_items if offset == 0 else []}

    # e. translation (Latin input)
    if re.search(r"[A-Za-z]", query) and not has_arabic(query):
        tr_lang = lang if lang != "ar" else "en"
        keys = await default_edition_keys(session, tr_lang) or await default_edition_keys(session, "en")
        total, hits, _terms = await search_translation_text(session, query, keys, limit, offset)
        editions = []
        if keys:
            eds = (await session.execute(
                select(TranslationEdition).where(TranslationEdition.key.in_(keys))
            )).scalars().all()
            editions = [
                {"key": e.key, "title": e.title, "translator_name": e.translator_name,
                 "license": e.license, "attribution": e.attribution, "source_url": e.source_url}
                for e in eds
            ]
        out["translations"] = {
            "total": total,
            "offset": offset,
            "editions": editions,
            "hits": [
                {
                    "verse_id": v.id,
                    "sura_no": v.sura_no,
                    "aya_no": v.aya_no,
                    "reference": f"{v.sura_no}:{v.aya_no}",
                    "sura_name_ar": v.sura_name_ar,
                    "sura_name_en": v.sura_name_en,
                    "text_uthmani": v.text_uthmani,
                    "translation": {
                        "edition": t.translator,
                        "language": t.language,
                        "text": t.text,
                        "source_id": t.source_id,
                        "edition_version": t.edition_version,
                    },
                }
                for t, v in hits
            ],
        }

    # f. semantic
    if include_semantic:
        out["semantic"] = await semantic_section(session, query, min(limit, 20))
    else:
        from app.ai.hf_client import hf_configured
        out["semantic"] = {
            "available": False,
            "reason": "not_requested" if hf_configured() else "ai_unavailable",
            "items": [],
        }

    if out["alias"]:
        out["intent"] = "alias"
    elif out["verses"]["total"]:
        out["intent"] = "text"
    elif out["surahs"]:
        out["intent"] = "surah"
    elif out["translations"]["total"]:
        out["intent"] = "translation"
    else:
        out["intent"] = "none"
    return out


def _names(no: int) -> Dict[str, str]:
    e = _surah_entry(no)
    return {"name_ar": e["name_ar"], "name_en": e["name_en"]}
