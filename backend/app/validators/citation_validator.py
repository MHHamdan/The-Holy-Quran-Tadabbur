"""
Citation validation for RAG responses.

CRITICAL: Ensures all citations in responses map to retrieved sources.

Single source of truth for matching an inline citation such as
``[Ibn Kathir, 2:255]``, ``[Al-Tabari, Al-Baqarah:45]`` or ``[الطبري، البقرة:٤٥]``
against the retrieved tafsir chunks. Used by the RAG pipeline and by
POST /rag/validate-citations.

Matching rules (fail closed):
  - Every bracketed attribution whose reference contains a digit is a
    citation, whatever the name looks like ("[I, 2:255]", "[ , 2:255]").
  - The reference resolves numerically ("2:255", "٢:٢٥٥", "2:255-257") or as
    "<surah name>:<ayah>" through a surah-name table built from quran_verses.
  - Every cited ayah must exist (114 surahs / 6,236 ayahs) — "0:0" never
    matches anything.
  - The source matches a chunk only on an exact normalised alias (source id,
    catalogue names, author names, common short names), minimum 3 letters.
  - The cited range must lie inside the matched chunk's [aya_start, aya_end].
  - "[Quran, s:a]" is a reference to the verse itself: valid when the ayat exist.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tafseer import TafseerChunk, TafseerSource
from app.safety.quran_answer_guard import SURAH_AYAH_COUNTS
from app.services.tafsir_sources import (
    SOURCE_CITATION_ALIASES,
    catalog_entry,
    source_base_id,
)

# Any bracketed "[name, reference]" whose reference contains a digit. The name
# may be empty or one letter: such markers must be caught and rejected, not
# silently ignored. Latin and Arabic commas are both accepted.
CITATION_MARKER_PATTERN = (
    r"\[([^\[\]\n]{0,80}?)\s*[,،]\s*"
    r"((?=[^\[\]\n]*[0-9٠-٩۰-۹])[^\[\]\n,،]{1,40}?)\s*\]"
)
CITATION_MARKER_RE = re.compile(CITATION_MARKER_PATTERN)

MIN_ALIAS_LENGTH = 3

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_AR_MARKS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_AR_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"})
_APOSTROPHES = re.compile(r"['’‘`ʿʾ]")

_SOURCE_STOP_TOKENS = frozenset({
    "tafsir", "tafseer", "tafsīr", "imam", "the", "al", "el", "an", "ar", "as", "at",
    "ad", "ash", "az", "adh", "ath", "تفسير", "التفسير", "الامام", "امام",
})
_SURAH_WORDS = re.compile(r"\b(surah|surat|sura|soorah|suurah)\b")
_SURAH_ARTICLES = frozenset({
    "al", "el", "an", "ar", "as", "at", "ad", "ash", "az", "adh", "ath", "aal", "ali", "i",
})
_QURAN_SOURCE = re.compile(
    r"^\s*(the\s+)?(holy\s+)?(qur'?an|quran|koran|surah|sura|القرآن|القران|سورة)\b",
    re.IGNORECASE,
)


# ------------------------------------------------------------- normalising

def _fold_arabic(s: str) -> str:
    return _AR_MARKS.sub("", s).translate(_AR_FOLD)


def normalize_source_alias(name: str) -> str:
    """'Al-Tafsir Al-Muyassar' / 'التفسير الميسر' / 'muyassar_ar' -> comparable key."""
    s = unicodedata.normalize("NFKC", name or "").lower()
    s = _fold_arabic(s)
    s = re.sub(r"\([^)]*\)", " ", s)          # "(English)", "(Arabic)"
    s = _APOSTROPHES.sub("", s)
    s = re.sub(r"[^\w\s]|_", " ", s)
    tokens = [t for t in s.split() if t not in _SOURCE_STOP_TOKENS]
    # Arabic definite article on each word ("الطبري" == "طبري")
    tokens = [t[2:] if t.startswith("ال") and len(t) > 4 else t for t in tokens]
    return "".join(tokens)


def is_quran_self_citation(source_name: str) -> bool:
    """True for citations that reference the Qur'an itself rather than a tafsir work."""
    return bool(_QURAN_SOURCE.match(source_name or ""))


def chunk_aliases(chunk) -> Set[str]:
    """Every exact name under which a retrieved chunk may be cited."""
    base = source_base_id(getattr(chunk, "source_id", "") or "")
    names: List[str] = [
        base,
        getattr(chunk, "source_id", "") or "",
        getattr(chunk, "source_name", "") or "",
        getattr(chunk, "source_name_ar", "") or "",
    ]
    entry = catalog_entry(base)
    if entry:
        names += [entry.get(k) or "" for k in ("name_en", "name_ar", "author_en", "author_ar")]
    names += SOURCE_CITATION_ALIASES.get(base, [])
    aliases = {normalize_source_alias(n) for n in names}
    return {a for a in aliases if len(a) >= MIN_ALIAS_LENGTH}


def _latin_surah_key(name: str) -> str:
    s = unicodedata.normalize("NFKC", name or "").lower()
    s = _APOSTROPHES.sub("", s)
    s = _SURAH_WORDS.sub(" ", s)
    tokens = [t for t in re.split(r"[^a-z0-9]+", s) if t and t not in _SURAH_ARTICLES]
    key = "".join(tokens)
    for a, b in (("ee", "i"), ("oo", "u"), ("ou", "u"), ("aa", "a"), ("ii", "i"), ("uu", "u")):
        key = key.replace(a, b)
    key = re.sub(r"(.)\1+", r"\1", key)
    return key[:-1] if key.endswith("h") and len(key) > 3 else key


def _arabic_surah_key(name: str) -> str:
    s = _fold_arabic(unicodedata.normalize("NFKC", name or ""))
    s = re.sub(r"[^ء-ي\s]", " ", s)
    tokens = [t for t in s.split() if t != "سوره"]
    tokens = [t[2:] if t.startswith("ال") else t for t in tokens]
    return "".join(t for t in tokens if t)


def surah_key(name: str) -> str:
    return _arabic_surah_key(name) if re.search(r"[؀-ۿ]", name or "") else _latin_surah_key(name)


def build_surah_name_index(rows: Iterable[Sequence]) -> Dict[str, int]:
    """
    rows: (sura_no, sura_name_ar, sura_name_en) from quran_verses. Keys that
    would map to two different surahs are dropped (never guess).
    """
    index: Dict[str, int] = {}
    clashes: Set[str] = set()
    for sura_no, name_ar, name_en in rows:
        for name in (name_ar, name_en):
            key = surah_key(name or "")
            if not key:
                continue
            if key in index and index[key] != int(sura_no):
                clashes.add(key)
            index[key] = int(sura_no)
    for key in clashes:
        index.pop(key, None)
    return index


# --------------------------------------------------------------- references

def is_valid_ayah(sura: int, aya: int) -> bool:
    return 1 <= sura <= len(SURAH_AYAH_COUNTS) and 1 <= aya <= SURAH_AYAH_COUNTS[sura - 1]


_REF = re.compile(r"^(.*?)\s*[:：]\s*(\d{1,3})(?:\s*[-–—]\s*(\d{1,3}))?$")


def parse_cited_reference(ref: str, surah_index: Optional[Dict[str, int]] = None) -> Optional[Tuple[int, int, int]]:
    """'2:255' / '٢:٢٥٥' / 'Al-Baqarah:255-257' / 'سورة البقرة:٤٥' -> (sura, start, end) or None."""
    ref = unicodedata.normalize("NFKC", ref or "").translate(_DIGITS).strip()
    m = _REF.match(ref)
    if not m:
        return None
    name, a0, a1 = m.group(1).strip(), int(m.group(2)), int(m.group(3) or m.group(2))
    numeric = re.fullmatch(r"(?:(?:surah|surat|sura)\s*|سورة\s*)?(\d{1,3})", name.lower())
    if numeric:
        sura = int(numeric.group(1))
    elif name:
        sura = (surah_index or {}).get(surah_key(name))
        if sura is None:
            return None
    else:
        return None
    if a1 < a0 or not all(is_valid_ayah(sura, a) for a in (a0, a1)):
        return None
    return sura, a0, a1


# ------------------------------------------------------------------ matching

@dataclass
class CitationMatch:
    marker: str                 # exact marker text as it appears in the answer
    source_name: str
    reference: str
    cited: Optional[Tuple[int, int, int]]
    chunk: object = None        # matched chunk (None for valid Qur'an self-references)
    is_quran: bool = False


@dataclass
class CitationMatchResult:
    valid: List[CitationMatch] = field(default_factory=list)
    invalid: List[CitationMatch] = field(default_factory=list)

    @property
    def invalid_markers(self) -> List[str]:
        return [m.marker for m in self.invalid]

    @property
    def matched_chunks(self) -> List[object]:
        seen, out = set(), []
        for m in self.valid:
            if m.chunk is not None and m.chunk.chunk_id not in seen:
                seen.add(m.chunk.chunk_id)
                out.append(m.chunk)
        return out


def match_citations(
    answer: str,
    chunks: Sequence,
    surah_index: Optional[Dict[str, int]] = None,
) -> CitationMatchResult:
    """Resolve every citation marker in ``answer`` against the retrieved chunks."""
    result = CitationMatchResult()
    aliases = [(c, chunk_aliases(c)) for c in chunks]
    for m in CITATION_MARKER_RE.finditer(answer or ""):
        source_name, reference = m.group(1).strip(), m.group(2).strip()
        cited = parse_cited_reference(reference, surah_index)
        match = CitationMatch(marker=m.group(0), source_name=source_name, reference=reference, cited=cited)
        if cited is None:
            result.invalid.append(match)
            continue
        if is_quran_self_citation(source_name):
            match.is_quran = True
            result.valid.append(match)
            continue
        key = normalize_source_alias(source_name)
        sura, a0, a1 = cited
        if len(key) >= MIN_ALIAS_LENGTH:
            for chunk, names in aliases:
                if key in names and chunk.sura_no == sura and chunk.aya_start <= a0 and a1 <= (chunk.aya_end or chunk.aya_start):
                    match.chunk = chunk
                    break
        (result.valid if match.chunk is not None else result.invalid).append(match)
    return result


@dataclass
class CitationValidationResult:
    """Result of citation validation."""
    is_valid: bool
    valid_citations: List[str]
    invalid_citations: List[str]
    missing_citations: List[str]  # Paragraphs without citations
    coverage_score: float  # Percentage of text that is cited
    errors: List[str]


class CitationValidator:
    """
    Validates that citations in a response:
    1. Exist in the retrieved chunks (exact alias + ayah range, see module doc)
    2. Cover all major paragraphs
    """

    CITATION_PATTERN = CITATION_MARKER_RE

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate(
        self,
        response_text: str,
        retrieved_chunk_ids: List[str],
    ) -> CitationValidationResult:
        found = list(CITATION_MARKER_RE.finditer(response_text or ""))
        if not found:
            return CitationValidationResult(
                is_valid=False, valid_citations=[], invalid_citations=[],
                missing_citations=["Entire response lacks citations"],
                coverage_score=0.0, errors=["No citations found in response"],
            )

        chunks = await self._load_chunks(retrieved_chunk_ids)
        surah_index = await load_surah_name_index(self.session)
        matched = match_citations(response_text, chunks, surah_index)

        valid = [m.marker for m in matched.valid]
        invalid = [m.marker for m in matched.invalid]
        errors = [f"Citation {m} not found in retrieved sources" for m in invalid]
        missing = self._check_paragraph_coverage(response_text)
        coverage = len(valid) / len(found) if found else 0.0
        return CitationValidationResult(
            is_valid=not invalid and not missing and coverage >= 0.8,
            valid_citations=valid,
            invalid_citations=invalid,
            missing_citations=missing,
            coverage_score=coverage,
            errors=errors,
        )

    async def _load_chunks(self, chunk_ids: List[str]) -> list:
        if not chunk_ids:
            return []
        from types import SimpleNamespace

        rows = (await self.session.execute(
            select(TafseerChunk, TafseerSource)
            .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
            .where(TafseerChunk.chunk_id.in_(chunk_ids))
        )).all()
        return [
            SimpleNamespace(
                chunk_id=c.chunk_id, source_id=c.source_id, source_name=s.name_en or "",
                source_name_ar=s.name_ar or "", sura_no=c.sura_no, aya_start=c.aya_start,
                aya_end=c.aya_end,
            )
            for c, s in rows
        ]

    def _check_paragraph_coverage(self, response_text: str) -> List[str]:
        """Each substantive paragraph must carry at least one citation."""
        missing = []
        paragraphs = [p.strip() for p in response_text.split('\n\n') if p.strip()]
        for i, para in enumerate(paragraphs):
            if len(para) < 100 or para.startswith(('-', '*', '#')):
                continue
            if not CITATION_MARKER_RE.search(para):
                preview = para[:50] + "..." if len(para) > 50 else para
                missing.append(f"Paragraph {i+1}: {preview}")
        return missing


async def load_surah_name_index(session) -> Dict[str, int]:
    """Surah-name table from the canonical quran_verses rows ({} if unavailable)."""
    try:
        rows = (await session.execute(text(
            "SELECT DISTINCT sura_no, sura_name_ar, sura_name_en FROM quran_verses"
        ))).all()
        return build_surah_name_index(rows)
    except Exception:  # noqa: BLE001 - without the table only numeric refs resolve
        return {}


class CitationCoverageValidator:
    """
    Validates that citations actually support the claims made.

    This is a more sophisticated validator that checks semantic
    alignment between claims and cited evidence.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_claim_support(
        self,
        claim: str,
        cited_chunk_id: str,
    ) -> Tuple[bool, float, str]:
        """
        Check if a cited chunk actually supports the claim.

        Returns:
            (is_supported, confidence, explanation)
        """
        result = await self.session.execute(
            select(TafseerChunk).where(TafseerChunk.chunk_id == cited_chunk_id)
        )
        chunk = result.scalar_one_or_none()

        if not chunk:
            return (False, 0.0, f"Chunk {cited_chunk_id} not found")

        # Simple keyword overlap check
        claim_words = set(claim.lower().split())
        content = (chunk.content_en or chunk.content_ar or "").lower()
        content_words = set(content.split())

        overlap = len(claim_words & content_words)
        overlap_ratio = overlap / len(claim_words) if claim_words else 0

        if overlap_ratio >= 0.3:
            return (True, overlap_ratio, "Claim appears to be supported by source")
        else:
            return (False, overlap_ratio, "Claim may not be fully supported by source")
