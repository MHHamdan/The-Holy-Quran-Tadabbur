"""
Quran API routes for verses, translations, and tafseer.
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_async_session
from app.models.quran import QuranVerse, Translation
from app.models.tafseer import TafseerChunk, TafseerSource

router = APIRouter()


# =============================================================================
# Rate Limiting for Resolve Endpoint
# =============================================================================
import time
from collections import defaultdict
from threading import Lock

class ResolveRateLimiter:
    """
    Simple in-memory rate limiter for the resolve endpoint.
    Limits requests per IP to prevent abuse of fuzzy search.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        """
        Check if request is allowed for this IP.
        Returns (allowed, requests_remaining).
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Clean old requests
            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip] if ts > cutoff
            ]

            # Check limit
            current_count = len(self._requests[client_ip])
            if current_count >= self.max_requests:
                return False, 0

            # Record this request
            self._requests[client_ip].append(now)
            return True, self.max_requests - current_count - 1

    def cleanup(self):
        """Remove stale entries."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            stale_ips = [
                ip for ip, timestamps in self._requests.items()
                if not timestamps or all(ts <= cutoff for ts in timestamps)
            ]
            for ip in stale_ips:
                del self._requests[ip]


# Global rate limiter instance for resolve endpoint
_resolve_rate_limiter = ResolveRateLimiter(max_requests=30, window_seconds=60)


# Pydantic schemas
class TranslationResponse(BaseModel):
    """Translation response schema."""
    language: str
    translator: str
    text: str

    class Config:
        from_attributes = True


class VerseResponse(BaseModel):
    """Verse response schema."""
    id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    text_imlaei: str
    page_no: int
    juz_no: int
    translations: List[TranslationResponse] = []

    class Config:
        from_attributes = True


class TafseerChunkResponse(BaseModel):
    """Tafseer chunk response schema."""
    chunk_id: str
    source_id: str
    source_name: Optional[str] = None
    verse_reference: str
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    scholarly_consensus: Optional[str] = None

    class Config:
        from_attributes = True


class SuraMetadata(BaseModel):
    """Sura metadata response."""
    sura_no: int
    name_ar: str
    name_en: str
    total_verses: int
    revelation_type: Optional[str] = None


class VerseResolveResponse(BaseModel):
    """Response for verse text resolution."""
    sura_no: int
    aya_no: int
    text_ar: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    match_type: str  # "exact", "fuzzy", "partial"


# =============================================================================
# Arabic Text Normalization Utilities
# =============================================================================

def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text for matching:
    - Remove diacritics (tashkeel)
    - Normalize alef forms (أإآ → ا)
    - Normalize taa marbutah (ة → ه)
    - Normalize yaa forms (ى → ي)
    - Remove punctuation
    - Collapse whitespace
    """
    import re

    # Remove diacritics
    diacritics = re.compile(r'[\u064B-\u065F\u0670]')
    text = diacritics.sub('', text)

    # Normalize alef forms
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ٱ', 'ا')

    # Normalize taa marbutah
    text = text.replace('ة', 'ه')

    # Normalize yaa
    text = text.replace('ى', 'ي')

    # Remove common punctuation and special chars
    text = re.sub(r'[۞۩٭﴿﴾،؛؟!\.\,\:\"\']', '', text)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def calculate_token_overlap(text1: str, text2: str) -> float:
    """Calculate token overlap ratio between two texts."""
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union) if union else 0.0


# =============================================================================
# Verse Resolver with Multi-Candidate Decision Logic
# =============================================================================

def compute_highlight_spans(query_normalized: str, verse_normalized: str) -> list:
    """
    Compute character spans where query tokens appear in verse.
    Returns list of [start, end] spans for highlighting.
    """
    spans = []
    query_tokens = query_normalized.split()
    for token in query_tokens:
        start = 0
        while True:
            idx = verse_normalized.find(token, start)
            if idx == -1:
                break
            spans.append([idx, idx + len(token)])
            start = idx + 1
    # Merge overlapping spans
    if not spans:
        return []
    spans.sort()
    merged = [spans[0]]
    for span in spans[1:]:
        if span[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], span[1])
        else:
            merged.append(span)
    return merged


# Routes
@router.get("/resolve")
async def resolve_verse_text(
    text: str = Query(..., description="Verse text to resolve"),
    session: AsyncSession = Depends(get_async_session),
    request: "Request" = None,  # type: ignore
):
    """
    Resolve verse text to sura:ayah reference with candidate selection.

    Performs text matching against the Quran database:
    1. Exact normalized match (after removing diacritics)
    2. Partial match (input contained in verse)
    3. Fuzzy match using token overlap

    Decision Logic:
    - exact/normalized_exact → decision: "auto"
    - confidence >= 0.85 AND margin >= 0.08 → decision: "auto"
    - confidence in [0.70, 0.85) → decision: "needs_user_choice" with top 5
    - confidence < 0.70 OR short input → decision: "not_found"

    Minimum Input Constraints:
    - Normalized text must be >= 8 characters
    - Must have >= 2 tokens
    - Otherwise, never auto-resolve

    Rate Limited: 30 requests per minute per IP.

    Returns:
    {
      ok: true,
      data: {
        query_original: str,
        query_normalized: str,
        mode_detected: "text",
        best_match: { surah, ayah, text_ar, confidence, match_type } | null,
        candidates: [{ surah, ayah, text_ar, confidence, match_type, highlight_spans }],
        decision: "auto" | "needs_user_choice" | "not_found"
      },
      request_id: str
    }
    """
    import logging
    import hashlib
    from fastapi import Request
    from app.core.responses import success_response, error_response, ErrorCode

    logger = logging.getLogger(__name__)

    # Rate limiting check
    client_ip = "unknown"
    if request:
        client_ip = request.client.host if request.client else "unknown"
        # Check forwarded headers for proxied requests
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

    is_allowed, remaining = _resolve_rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        logger.warning(f"[RESOLVE] Rate limited: client_ip={client_ip}")
        return error_response(
            code=ErrorCode.RATE_LIMITED,
            message_en="Too many requests. Please wait a moment before trying again.",
            message_ar="طلبات كثيرة جداً. يرجى الانتظار قليلاً قبل المحاولة مجدداً.",
            request_id=f"resolve-ratelimit-{client_ip[:8]}",
            status_code=429
        )

    # Generate deterministic request_id for tracing
    query_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
    request_id = f"resolve-{query_hash}"

    # Normalize input text
    normalized_input = normalize_arabic_text(text)
    input_tokens = normalized_input.split()
    token_count = len(input_tokens)

    # Structured log: request received
    logger.info(
        f"[RESOLVE] request_id={request_id} "
        f"query_hash={query_hash} "
        f"input_len={len(normalized_input)} "
        f"token_count={token_count}"
    )

    # Minimum input validation
    if len(normalized_input) < 3:
        logger.warning(f"[RESOLVE] request_id={request_id} decision=not_found reason=too_short")
        return success_response(
            data={
                "query_original": text,
                "query_normalized": normalized_input,
                "mode_detected": "text",
                "best_match": None,
                "candidates": [],
                "decision": "not_found",
                "message_ar": "النص قصير جداً للمطابقة (الحد الأدنى 3 أحرف)",
                "message_en": "Text too short for matching (minimum 3 characters)",
            },
            request_id=request_id
        )

    # Check if input is too short for auto-resolution
    # Minimum: 8 chars AND 2 tokens for auto
    is_short_input = len(normalized_input) < 8 or token_count < 2

    # Fetch all verses for matching
    result = await session.execute(
        select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani)
    )
    verses = result.all()

    # Calculate scores for all verses
    candidates = []
    exact_match_found = False

    for verse in verses:
        sura_no, aya_no, verse_text = verse
        normalized_verse = normalize_arabic_text(verse_text)

        score = 0.0
        match_type = "none"

        # Check exact match
        if normalized_input == normalized_verse:
            score = 1.0
            match_type = "exact"
            exact_match_found = True
        # Check partial match (input contained in verse)
        elif normalized_input in normalized_verse:
            base_score = len(normalized_input) / len(normalized_verse)
            score = min(1.0, base_score + 0.5)
            match_type = "partial"
        else:
            # Fuzzy matching via token overlap
            overlap = calculate_token_overlap(normalized_input, normalized_verse)
            if overlap > 0:
                score = overlap
                match_type = "fuzzy"

        if score > 0:
            highlight_spans = compute_highlight_spans(normalized_input, normalized_verse)
            candidates.append({
                "surah": sura_no,
                "ayah": aya_no,
                "text_ar": verse_text,
                "confidence": round(score, 4),
                "match_type": match_type,
                "highlight_spans": highlight_spans,
            })

        # Early exit on exact match
        if exact_match_found:
            break

    # Sort candidates by confidence descending
    candidates.sort(key=lambda x: x["confidence"], reverse=True)

    # Keep top 5 candidates for response
    top_candidates = candidates[:5]

    # Determine decision
    if not candidates:
        decision = "not_found"
        best_match = None
        logger.warning(f"[RESOLVE] request_id={request_id} decision=not_found reason=no_matches")
    else:
        best = candidates[0]
        best_confidence = best["confidence"]
        best_match_type = best["match_type"]

        # Calculate margin to second candidate
        margin = best_confidence - (candidates[1]["confidence"] if len(candidates) > 1 else 0)

        # Decision rules
        if best_match_type == "exact":
            # Exact match is always auto
            decision = "auto"
        elif is_short_input:
            # Short input: never auto, require user choice or not_found
            if best_confidence >= 0.70:
                decision = "needs_user_choice"
            else:
                decision = "not_found"
        elif best_confidence >= 0.85 and margin >= 0.08:
            # High confidence with clear margin
            decision = "auto"
        elif best_confidence >= 0.70:
            # Moderate confidence: user must choose
            decision = "needs_user_choice"
        else:
            # Low confidence
            decision = "not_found"

        best_match = {
            "surah": best["surah"],
            "ayah": best["ayah"],
            "text_ar": best["text_ar"],
            "confidence": best["confidence"],
            "match_type": best["match_type"],
        }

        # Structured log: decision made
        logger.info(
            f"[RESOLVE] request_id={request_id} "
            f"decision={decision} "
            f"best_confidence={best_confidence:.4f} "
            f"match_type={best_match_type} "
            f"margin={margin:.4f} "
            f"is_short_input={is_short_input} "
            f"candidate_count={len(candidates)}"
        )

    # Build response
    response_data = {
        "query_original": text,
        "query_normalized": normalized_input,
        "mode_detected": "text",
        "best_match": best_match,
        "candidates": top_candidates,
        "decision": decision,
    }

    # Add messages for non-auto decisions
    if decision == "needs_user_choice":
        response_data["message_ar"] = "تم العثور على عدة آيات محتملة. يرجى اختيار الآية الصحيحة."
        response_data["message_en"] = "Multiple possible verses found. Please select the correct one."
        response_data["warning_ar"] = "تنبيه: تم مطابقة نص الآية بطريقة تقريبية. يُرجى التأكد من المرجع قبل الاعتماد."
    elif decision == "not_found":
        response_data["message_ar"] = "لم يتم العثور على آية مطابقة. جرّب إدخال رقم السورة والآية مثل 2:255"
        response_data["message_en"] = "No matching verse found. Try entering the reference directly (e.g., 2:255)."

    # Add warning for non-exact matches in auto mode
    if decision == "auto" and best_match and best_match["match_type"] != "exact":
        response_data["warning_ar"] = "تنبيه: تم مطابقة نص الآية بطريقة تقريبية. يُرجى التأكد من المرجع قبل الاعتماد."

    return success_response(data=response_data, request_id=request_id)


@router.get("/metadata")
async def get_quran_metadata(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get Quran metadata - total verses, suras, etc.
    """
    result = await session.execute(
        select(QuranVerse.sura_no, QuranVerse.sura_name_ar, QuranVerse.sura_name_en)
        .distinct()
        .order_by(QuranVerse.sura_no)
    )
    suras = result.all()

    # Get verse count per sura
    verse_counts = await session.execute(
        select(QuranVerse.sura_no, QuranVerse.id)
    )
    verse_count_map = {}
    for row in verse_counts.all():
        sura_no = row[0]
        verse_count_map[sura_no] = verse_count_map.get(sura_no, 0) + 1

    return {
        "total_verses": sum(verse_count_map.values()),
        "total_suras": len(suras),
        "suras": [
            {
                "sura_no": s[0],
                "name_ar": s[1],
                "name_en": s[2],
                "total_verses": verse_count_map.get(s[0], 0),
            }
            for s in suras
        ],
    }


@router.get("/suras/{sura_no}", response_model=List[VerseResponse])
async def get_sura_verses(
    sura_no: int,
    include_translations: bool = Query(True, description="Include translations"),
    language: Optional[str] = Query(None, description="Filter translations by language"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all verses for a specific sura.
    """
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Sura number must be between 1 and 114")

    query = select(QuranVerse).where(QuranVerse.sura_no == sura_no).order_by(QuranVerse.aya_no)

    if include_translations:
        query = query.options(selectinload(QuranVerse.translations))

    result = await session.execute(query)
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(status_code=404, detail=f"Sura {sura_no} not found")

    # Filter translations by language if specified
    response = []
    for verse in verses:
        verse_data = VerseResponse.model_validate(verse)
        if language and verse.translations:
            verse_data.translations = [
                TranslationResponse.model_validate(t)
                for t in verse.translations
                if t.language == language
            ]
        response.append(verse_data)

    return response


@router.get("/verses/{sura_no}/{aya_no}", response_model=VerseResponse)
async def get_verse(
    sura_no: int,
    aya_no: int,
    include_translations: bool = Query(True),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific verse by sura and aya number.
    """
    query = select(QuranVerse).where(
        QuranVerse.sura_no == sura_no,
        QuranVerse.aya_no == aya_no,
    )

    if include_translations:
        query = query.options(selectinload(QuranVerse.translations))

    result = await session.execute(query)
    verse = result.scalar_one_or_none()

    if not verse:
        raise HTTPException(
            status_code=404, detail=f"Verse {sura_no}:{aya_no} not found"
        )

    return VerseResponse.model_validate(verse)


@router.get("/verses/{sura_no}/{aya_start}/{aya_end}", response_model=List[VerseResponse])
async def get_verse_range(
    sura_no: int,
    aya_start: int,
    aya_end: int,
    include_translations: bool = Query(True),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a range of verses from a sura.
    """
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Sura number must be between 1 and 114")
    if aya_start > aya_end:
        raise HTTPException(status_code=400, detail="aya_start must be <= aya_end")

    query = select(QuranVerse).where(
        QuranVerse.sura_no == sura_no,
        QuranVerse.aya_no >= aya_start,
        QuranVerse.aya_no <= aya_end,
    ).order_by(QuranVerse.aya_no)

    if include_translations:
        query = query.options(selectinload(QuranVerse.translations))

    result = await session.execute(query)
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(
            status_code=404, detail=f"Verses {sura_no}:{aya_start}-{aya_end} not found"
        )

    return [VerseResponse.model_validate(v) for v in verses]


@router.get("/page/{page_no}", response_model=List[VerseResponse])
async def get_page_verses(
    page_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all verses on a specific page of the Mushaf.
    """
    if page_no < 1 or page_no > 604:
        raise HTTPException(status_code=400, detail="Page number must be between 1 and 604")

    query = (
        select(QuranVerse)
        .where(QuranVerse.page_no == page_no)
        .order_by(QuranVerse.id)
        .options(selectinload(QuranVerse.translations))
    )

    result = await session.execute(query)
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(status_code=404, detail=f"Page {page_no} not found")

    return [VerseResponse.model_validate(v) for v in verses]


@router.get("/juz/{juz_no}", response_model=List[VerseResponse])
async def get_juz_verses(
    juz_no: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verses for a specific juz (with pagination).
    """
    if juz_no < 1 or juz_no > 30:
        raise HTTPException(status_code=400, detail="Juz number must be between 1 and 30")

    query = (
        select(QuranVerse)
        .where(QuranVerse.juz_no == juz_no)
        .order_by(QuranVerse.id)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    verses = result.scalars().all()

    return [VerseResponse.model_validate(v) for v in verses]


@router.get("/tafseer/{sura_no}/{aya_no}", response_model=List[TafseerChunkResponse])
async def get_verse_tafseer(
    sura_no: int,
    aya_no: int,
    sources: Optional[List[str]] = Query(None, description="Filter by source IDs"),
    language: Optional[str] = Query(None, description="Filter by language (ar/en)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get tafseer for a specific verse.
    """
    # First get the verse ID
    verse_result = await session.execute(
        select(QuranVerse.id).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no,
        )
    )
    verse_id = verse_result.scalar_one_or_none()

    if not verse_id:
        raise HTTPException(status_code=404, detail=f"Verse {sura_no}:{aya_no} not found")

    # Get tafseer chunks
    query = select(TafseerChunk).where(
        TafseerChunk.verse_start_id <= verse_id,
        TafseerChunk.verse_end_id >= verse_id,
    )

    if sources:
        query = query.where(TafseerChunk.source_id.in_(sources))

    result = await session.execute(query)
    chunks = result.scalars().all()

    # Filter by language if specified
    response = []
    for chunk in chunks:
        if language == "ar" and not chunk.content_ar:
            continue
        if language == "en" and not chunk.content_en:
            continue

        response.append(
            TafseerChunkResponse(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                verse_reference=chunk.verse_reference,
                content_ar=chunk.content_ar if language != "en" else None,
                content_en=chunk.content_en if language != "ar" else None,
                scholarly_consensus=chunk.scholarly_consensus,
            )
        )

    return response


@router.get("/tafseer/sources", response_model=List[dict])
async def get_tafseer_sources(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get available tafseer sources.
    """
    result = await session.execute(select(TafseerSource))
    sources = result.scalars().all()

    return [
        {
            "id": s.id,
            "name_ar": s.name_ar,
            "name_en": s.name_en,
            "author_en": s.author_en,
            "language": s.language,
            "methodology": s.methodology,
            "reliability_score": s.reliability_score,
        }
        for s in sources
    ]


@router.get("/search")
async def search_quran(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search Quran text (simplified search, not full-text).
    """
    # Normalize query for diacritic-free search
    from app.services.quran_search import normalize_arabic
    q_normalized = normalize_arabic(q)

    # Simple LIKE search on normalized text (no diacritics)
    query = (
        select(QuranVerse)
        .where(QuranVerse.text_normalized.ilike(f"%{q_normalized}%"))
        .limit(limit)
    )

    result = await session.execute(query)
    verses = result.scalars().all()

    return {
        "query": q,
        "count": len(verses),
        "results": [
            {
                "id": v.id,
                "reference": f"{v.sura_no}:{v.aya_no}",
                "sura_name": v.sura_name_en,
                "text": v.text_uthmani,
            }
            for v in verses
        ],
    }


# =============================================================================
# ENHANCED SEARCH ENDPOINTS (PR: Quran Search)
# =============================================================================

from app.services.quran_search import (
    QuranSearchService,
    SearchResult,
    SearchMatch,
    WordAnalytics,
    normalize_arabic,
    GrammaticalRole,
    SentenceType,
    GRAMMATICAL_ROLE_AR,
    SENTENCE_TYPE_AR,
)
from app.services.grammatical_analyzer import GrammaticalAnalyzer
from app.services.semantic_search import (
    SemanticSearchService,
    ThematicCategory,
    THEME_LABELS_AR,
)


# Pydantic schemas for enhanced search
class SearchMatchResponse(BaseModel):
    """Enhanced search match response."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    reference: str
    text_uthmani: str
    text_imlaei: str
    page_no: int
    juz_no: int
    highlighted_text: str
    context_before: str
    context_after: str
    relevance_score: float
    tfidf_score: float
    exact_match: bool
    # Grammatical analysis (optional)
    word_role: Optional[str] = None
    word_role_ar: Optional[str] = None
    sentence_type: Optional[str] = None
    sentence_type_ar: Optional[str] = None

    class Config:
        from_attributes = True


class EnhancedSearchResponse(BaseModel):
    """Enhanced search result response."""
    query: str
    query_normalized: str
    total_matches: int
    search_time_ms: float
    matches: List[SearchMatchResponse]
    sura_distribution: dict
    juz_distribution: dict
    related_terms: List[str]


class WordAnalyticsResponse(BaseModel):
    """Word analytics response."""
    word: str
    word_normalized: str
    total_occurrences: int
    by_sura: dict
    by_juz: dict
    top_verses: List[dict]
    co_occurring_words: List[dict]


class GrammaticalFilterRequest(BaseModel):
    """Request for filtering by grammatical role."""
    role: Optional[str] = Field(None, description="Grammatical role filter (subject, object, verb, etc.)")
    sentence_type: Optional[str] = Field(None, description="Sentence type filter (verbal, nominal, etc.)")


@router.get("/search/enhanced/{word}")
async def enhanced_search(
    word: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sura: Optional[int] = Query(None, ge=1, le=114, description="Filter by sura number"),
    juz: Optional[int] = Query(None, ge=1, le=30, description="Filter by juz number"),
    include_semantic: bool = Query(True, description="Include semantically related terms"),
    theme: Optional[str] = Query(None, description="Filter by thematic category (e.g., 'tawheed', 'prophets', 'afterlife')"),
    session: AsyncSession = Depends(get_async_session),
) -> EnhancedSearchResponse:
    """
    Enhanced search for a word across the entire Quran.

    Features:
    - Exact and semantic matching
    - TF-IDF relevance scoring
    - Context highlighting
    - Distribution statistics
    - Thematic filtering

    Arabic: بحث محسّن عن كلمة في القرآن الكريم

    Args:
        word: Arabic word to search (e.g., "الله", "صبر", "رحمة")
        limit: Maximum number of results (default 50)
        offset: Pagination offset
        sura: Filter to specific sura (1-114)
        juz: Filter to specific juz (1-30)
        include_semantic: Include related concepts in search
        theme: Filter by thematic category (tawheed, prophets, afterlife, worship, ethics, law, history, nature, guidance, community)

    Returns:
        EnhancedSearchResponse with matches, statistics, and related terms
    """
    search_service = QuranSearchService(session)

    result = await search_service.search(
        query=word,
        limit=limit,
        offset=offset,
        sura_filter=sura,
        juz_filter=juz,
        include_semantic=include_semantic,
        theme_filter=theme,
    )

    # Convert matches to response format
    matches = [
        SearchMatchResponse(
            verse_id=m.verse_id,
            sura_no=m.sura_no,
            sura_name_ar=m.sura_name_ar,
            sura_name_en=m.sura_name_en,
            aya_no=m.aya_no,
            reference=f"{m.sura_no}:{m.aya_no}",
            text_uthmani=m.text_uthmani,
            text_imlaei=m.text_imlaei,
            page_no=m.page_no,
            juz_no=m.juz_no,
            highlighted_text=m.highlighted_text,
            context_before=m.context_before,
            context_after=m.context_after,
            relevance_score=round(m.relevance_score, 4),
            tfidf_score=round(m.tfidf_score, 4),
            exact_match=m.exact_match,
            word_role=m.word_role.value if m.word_role else None,
            word_role_ar=m.word_role_ar or None,
            sentence_type=m.sentence_type.value if m.sentence_type else None,
            sentence_type_ar=m.sentence_type_ar or None,
        )
        for m in result.matches
    ]

    return EnhancedSearchResponse(
        query=result.query,
        query_normalized=result.query_normalized,
        total_matches=result.total_matches,
        search_time_ms=round(result.search_time_ms, 2),
        matches=matches,
        sura_distribution=result.sura_distribution,
        juz_distribution=result.juz_distribution,
        related_terms=result.related_terms,
    )


# =============================================================================
# ROOT EXTRACTION API
# =============================================================================

from app.services.quran_search import extract_root, get_words_by_root, expand_by_root


class RootExtractionResponse(BaseModel):
    """Response for root extraction."""
    word: str
    word_normalized: str
    root: Optional[str]
    root_meaning: Optional[str] = None
    derived_words: List[str]


@router.get("/root/{word}")
async def get_word_root(word: str) -> RootExtractionResponse:
    """
    Extract the Arabic root (جذر) from a word and find related derived words.

    Arabic: استخراج الجذر العربي من الكلمة

    Args:
        word: Arabic word to analyze (e.g., "رحمة", "مؤمنون", "صابرين")

    Returns:
        The root and all words derived from it

    Examples:
        - رحمة -> root: رحم, derived: [رحمة, رحيم, رحمن, ...]
        - مؤمنون -> root: امن, derived: [إيمان, مؤمن, آمن, ...]
    """
    from app.services.quran_search import normalize_arabic

    word_normalized = normalize_arabic(word)
    root = extract_root(word)
    derived = get_words_by_root(root) if root else []

    return RootExtractionResponse(
        word=word,
        word_normalized=word_normalized,
        root=root,
        derived_words=derived,
    )


@router.get("/search/root/{root}")
async def search_by_root(
    root: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: AsyncSession = Depends(get_async_session),
) -> EnhancedSearchResponse:
    """
    Search for all words derived from a specific Arabic root.

    Arabic: البحث عن جميع الكلمات المشتقة من جذر معين

    Args:
        root: 3-letter Arabic root (e.g., "رحم", "صبر", "علم")
        limit: Maximum results
        offset: Pagination offset

    Returns:
        All verses containing words derived from this root
    """
    # Get all derived words from the root
    derived_words = get_words_by_root(root)

    if not derived_words:
        # If no derived words found, use the root itself
        derived_words = [root]

    # Search using the derived words
    search_service = QuranSearchService(session)
    result = await search_service.search(
        query=root,
        limit=limit,
        offset=offset,
        include_semantic=True,  # This will expand using root
    )

    # Convert matches to response format
    matches = [
        SearchMatchResponse(
            verse_id=m.verse_id,
            sura_no=m.sura_no,
            sura_name_ar=m.sura_name_ar,
            sura_name_en=m.sura_name_en,
            aya_no=m.aya_no,
            reference=f"{m.sura_no}:{m.aya_no}",
            text_uthmani=m.text_uthmani,
            text_imlaei=m.text_imlaei,
            page_no=m.page_no,
            juz_no=m.juz_no,
            highlighted_text=m.highlighted_text,
            context_before=m.context_before,
            context_after=m.context_after,
            relevance_score=round(m.relevance_score, 4),
            tfidf_score=round(m.tfidf_score, 4),
            exact_match=m.exact_match,
        )
        for m in result.matches
    ]

    return EnhancedSearchResponse(
        query=root,
        query_normalized=normalize_arabic(root),
        total_matches=result.total_matches,
        search_time_ms=round(result.search_time_ms, 2),
        matches=matches,
        sura_distribution=result.sura_distribution,
        juz_distribution=result.juz_distribution,
        related_terms=derived_words,  # Show derived words as related terms
    )


@router.get("/search/enhanced/{word}/context/{sura_no}/{aya_no}")
async def get_word_context(
    word: str,
    sura_no: int,
    aya_no: int,
    include_grammar: bool = Query(False, description="Include grammatical analysis"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get full context of a word occurrence in a specific verse.

    Returns the verse with the word highlighted, surrounding verses for context,
    and optionally grammatical analysis.

    Arabic: الحصول على سياق كامل لورود كلمة في آية معينة
    """
    # Get the verse
    verse_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no
        )
    )
    verse = verse_result.scalar_one_or_none()

    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    # Check if word exists in verse
    normalized_word = normalize_arabic(word)
    if normalized_word not in normalize_arabic(verse.text_imlaei):
        raise HTTPException(
            status_code=404,
            detail=f"Word '{word}' not found in verse {sura_no}:{aya_no}"
        )

    # Get surrounding verses for context (previous 2 and next 2)
    context_verses = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no >= max(1, aya_no - 2),
            QuranVerse.aya_no <= aya_no + 2
        ).order_by(QuranVerse.aya_no)
    )
    surrounding = context_verses.scalars().all()

    # Get tafseer for this verse
    tafseer_result = await session.execute(
        select(TafseerChunk).where(
            TafseerChunk.sura_no == sura_no,
            TafseerChunk.aya_start <= aya_no,
            TafseerChunk.aya_end >= aya_no
        ).limit(3)
    )
    tafseer_chunks = tafseer_result.scalars().all()

    response = {
        "word": word,
        "word_normalized": normalized_word,
        "verse": {
            "sura_no": verse.sura_no,
            "sura_name_ar": verse.sura_name_ar,
            "sura_name_en": verse.sura_name_en,
            "aya_no": verse.aya_no,
            "reference": f"{verse.sura_no}:{verse.aya_no}",
            "text_uthmani": verse.text_uthmani,
            "text_imlaei": verse.text_imlaei,
            "page_no": verse.page_no,
            "juz_no": verse.juz_no,
        },
        "context_verses": [
            {
                "aya_no": v.aya_no,
                "text_uthmani": v.text_uthmani,
                "is_target": v.aya_no == aya_no,
            }
            for v in surrounding
        ],
        "tafseer": [
            {
                "source_id": t.source_id,
                "content_ar": t.content_ar[:500] if t.content_ar else None,
                "content_en": t.content_en[:500] if t.content_en else None,
            }
            for t in tafseer_chunks
        ],
    }

    # Add grammatical analysis if requested
    if include_grammar:
        try:
            analyzer = GrammaticalAnalyzer()
            analysis = await analyzer.analyze_word(
                word=word,
                verse_text=verse.text_uthmani,
                verse_reference=f"{sura_no}:{aya_no}",
            )
            await analyzer.close()

            response["grammar"] = {
                "role": analysis.role.value,
                "role_ar": analysis.role_ar,
                "role_explanation": analysis.role_explanation,
                "sentence_type": analysis.sentence_type.value,
                "sentence_type_ar": analysis.sentence_type_ar,
                "root": analysis.root,
                "pattern": analysis.pattern,
                "word_type": analysis.word_type,
                "case": analysis.case,
                "notes_ar": analysis.notes_ar,
            }
        except Exception as e:
            response["grammar"] = {"error": str(e)}

    return response


@router.get("/search/analytics/{word}")
async def get_word_analytics(
    word: str,
    session: AsyncSession = Depends(get_async_session),
) -> WordAnalyticsResponse:
    """
    Get comprehensive analytics for a word's usage in the Quran.

    Returns:
    - Total occurrences
    - Distribution by sura (with percentages)
    - Distribution by juz
    - Top verses containing the word
    - Co-occurring words

    Arabic: تحليلات شاملة لاستخدام كلمة في القرآن
    """
    search_service = QuranSearchService(session)
    analytics = await search_service.get_word_analytics(word)

    return WordAnalyticsResponse(
        word=analytics.word,
        word_normalized=analytics.word_normalized,
        total_occurrences=analytics.total_occurrences,
        by_sura=analytics.by_sura,
        by_juz=analytics.by_juz,
        top_verses=analytics.top_verses,
        co_occurring_words=[
            {"word": w, "count": c}
            for w, c in analytics.co_occurring_words
        ],
    )


@router.get("/search/phrase")
async def search_phrase(
    phrase: str = Query(..., min_length=3, description="Arabic phrase to search"),
    exact: bool = Query(True, description="Exact phrase match"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search for an exact phrase in the Quran.

    Arabic: البحث عن عبارة في القرآن

    Args:
        phrase: Arabic phrase (e.g., "بسم الله الرحمن الرحيم")
        exact: If True, match exact phrase order; if False, all words must appear
        limit: Maximum results
    """
    search_service = QuranSearchService(session)
    result = await search_service.search_phrase(phrase, exact=exact, limit=limit)

    return {
        "phrase": result.query,
        "phrase_normalized": result.query_normalized,
        "exact_match": exact,
        "total_matches": result.total_matches,
        "matches": [
            {
                "reference": f"{m.sura_no}:{m.aya_no}",
                "sura_name_ar": m.sura_name_ar,
                "sura_name_en": m.sura_name_en,
                "text_uthmani": m.text_uthmani,
                "highlighted_text": m.highlighted_text,
            }
            for m in result.matches
        ],
    }


@router.get("/search/sura/{sura_no}/frequency")
async def get_sura_word_frequency(
    sura_no: int,
    top_n: int = Query(50, ge=10, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get word frequency analysis for a specific sura.

    Returns the most common words in the sura (excluding stop words).

    Arabic: تحليل تكرار الكلمات في سورة
    """
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Invalid sura number (1-114)")

    search_service = QuranSearchService(session)
    frequency = await search_service.get_sura_word_frequency(sura_no, top_n)

    # Get sura name
    sura_result = await session.execute(
        select(QuranVerse.sura_name_ar, QuranVerse.sura_name_en).where(
            QuranVerse.sura_no == sura_no
        ).limit(1)
    )
    sura_info = sura_result.first()

    return {
        "sura_no": sura_no,
        "sura_name_ar": sura_info[0] if sura_info else "",
        "sura_name_en": sura_info[1] if sura_info else "",
        "total_unique_words": len(frequency),
        "word_frequency": [
            {"word": word, "count": count, "rank": i + 1}
            for i, (word, count) in enumerate(frequency)
        ],
    }


@router.post("/search/grammar/analyze")
async def analyze_grammar(
    word: str = Query(..., description="Word to analyze"),
    sura_no: int = Query(..., ge=1, le=114),
    aya_no: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Analyze the grammatical role of a word in a specific verse using LLM.

    Arabic: تحليل الدور النحوي لكلمة في آية معينة

    Returns:
    - Grammatical role (فاعل، مفعول به، خبر، إلخ)
    - Sentence type (جملة فعلية، جملة اسمية، إلخ)
    - Morphological details (الجذر، الوزن، إلخ)
    """
    # Get the verse
    verse_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no
        )
    )
    verse = verse_result.scalar_one_or_none()

    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    # Analyze with LLM
    try:
        analyzer = GrammaticalAnalyzer()
        analysis = await analyzer.analyze_word(
            word=word,
            verse_text=verse.text_uthmani,
            verse_reference=f"{sura_no}:{aya_no}",
        )
        await analyzer.close()

        return {
            "word": analysis.word,
            "verse_reference": analysis.verse_reference,
            "grammatical_analysis": {
                "role": analysis.role.value,
                "role_ar": analysis.role_ar,
                "role_explanation": analysis.role_explanation,
                "sentence_type": analysis.sentence_type.value,
                "sentence_type_ar": analysis.sentence_type_ar,
            },
            "morphology": {
                "root": analysis.root,
                "pattern": analysis.pattern,
                "word_type": analysis.word_type,
                "gender": analysis.gender,
                "number": analysis.number,
                "case": analysis.case,
                "tense": analysis.tense,
            },
            "notes": {
                "ar": analysis.notes_ar,
                "en": analysis.notes_en,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Grammar analysis failed: {str(e)}"
        )


@router.get("/search/categories")
async def get_search_categories():
    """
    Get available grammatical categories for filtering search results.

    Arabic: الحصول على التصنيفات النحوية المتاحة للتصفية
    """
    return {
        "grammatical_roles": [
            {"value": role.value, "label_en": role.value.title(), "label_ar": GRAMMATICAL_ROLE_AR[role]}
            for role in GrammaticalRole
        ],
        "sentence_types": [
            {"value": st.value, "label_en": st.value.title(), "label_ar": SENTENCE_TYPE_AR[st]}
            for st in SentenceType
        ],
    }


# =============================================================================
# SEMANTIC SEARCH ENDPOINTS
# =============================================================================

class SemanticMatchResponse(BaseModel):
    """Semantic match response."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    reference: str
    text_uthmani: str
    text_imlaei: str
    semantic_score: float
    shared_concepts: List[str]
    themes: List[str]
    connection_type: str


class ThematicConnectionResponse(BaseModel):
    """Thematic connection response."""
    source_verse: str
    target_verse: str
    theme: str
    theme_ar: str
    similarity_score: float
    shared_keywords: List[str]


class ConceptEvolutionResponse(BaseModel):
    """Concept evolution response."""
    concept: str
    concept_normalized: str
    total_occurrences: int
    chronological_order: List[dict]
    related_concepts: List[str]


@router.get("/semantic/similar/{sura_no}/{aya_no}")
async def find_similar_verses(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(10, ge=1, le=50),
    theme: Optional[str] = Query(None, description="Filter by theme (tawheed, prophets, afterlife, etc.)"),
    cross_sura: bool = Query(True, description="Only return verses from other suras"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find semantically similar verses to a given verse.

    Uses vector embeddings to find verses with similar meaning,
    even if the exact words differ.

    Arabic: البحث عن آيات متشابهة دلالياً

    Args:
        sura_no: Sura number (1-114)
        aya_no: Aya number
        top_k: Maximum number of results
        theme: Filter by thematic category
        cross_sura: If True, exclude verses from the same sura

    Returns:
        List of semantically similar verses with scores
    """
    # Get the source verse
    result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no
        )
    )
    source_verse = result.scalar_one_or_none()

    if not source_verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    # Parse theme filter
    theme_filter = None
    if theme:
        try:
            theme_filter = ThematicCategory(theme.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid theme. Valid themes: {[t.value for t in ThematicCategory]}"
            )

    semantic_service = SemanticSearchService(session)
    similar = await semantic_service.find_similar_verses(
        verse_text=source_verse.text_imlaei,
        top_k=top_k,
        theme_filter=theme_filter,
        exclude_sura=sura_no if cross_sura else None,
    )

    return {
        "source_verse": {
            "reference": f"{sura_no}:{aya_no}",
            "sura_name_ar": source_verse.sura_name_ar,
            "sura_name_en": source_verse.sura_name_en,
            "text_uthmani": source_verse.text_uthmani,
        },
        "similar_verses": [
            SemanticMatchResponse(
                verse_id=m.verse_id,
                sura_no=m.sura_no,
                sura_name_ar=m.sura_name_ar,
                sura_name_en=m.sura_name_en,
                aya_no=m.aya_no,
                reference=f"{m.sura_no}:{m.aya_no}",
                text_uthmani=m.text_uthmani,
                text_imlaei=m.text_imlaei,
                semantic_score=round(m.semantic_score, 4),
                shared_concepts=m.shared_concepts[:5],
                themes=m.themes,
                connection_type=m.connection_type,
            )
            for m in similar
        ],
        "total_found": len(similar),
    }


@router.get("/semantic/connections/{sura_no}/{aya_no}")
async def get_thematic_connections(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(5, ge=1, le=20),
    theme: Optional[str] = Query(None, description="Filter by specific theme"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get thematic connections between a verse and verses in other suras.

    Helps discover how themes are presented across the Quran.

    Arabic: روابط موضوعية بين الآيات في سور مختلفة
    """
    theme_filter = None
    if theme:
        try:
            theme_filter = ThematicCategory(theme.lower())
        except ValueError:
            pass

    semantic_service = SemanticSearchService(session)
    connections = await semantic_service.find_thematic_connections(
        sura_no=sura_no,
        aya_no=aya_no,
        theme=theme_filter,
        top_k=top_k,
    )

    return {
        "source_reference": f"{sura_no}:{aya_no}",
        "connections": [
            ThematicConnectionResponse(
                source_verse=c.source_verse,
                target_verse=c.target_verse,
                theme=c.theme.value,
                theme_ar=c.theme_ar,
                similarity_score=round(c.similarity_score, 4),
                shared_keywords=c.shared_keywords,
            )
            for c in connections
        ],
        "total_connections": len(connections),
    }


@router.get("/semantic/evolution/{concept}")
async def get_concept_evolution(
    concept: str,
    include_related: bool = Query(True, description="Include related concepts"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Track how a concept evolves throughout the Quran.

    Shows the concept's usage pattern and related terms.

    Arabic: تتبع تطور مفهوم عبر القرآن الكريم

    Args:
        concept: Arabic concept/word to track
        include_related: Include related concepts from expansion dictionary

    Returns:
        Concept evolution data including occurrences and related concepts
    """
    semantic_service = SemanticSearchService(session)
    evolution = await semantic_service.get_concept_evolution(
        concept=concept,
        include_related=include_related,
    )

    return ConceptEvolutionResponse(
        concept=evolution.concept,
        concept_normalized=evolution.concept_normalized,
        total_occurrences=evolution.total_occurrences,
        chronological_order=evolution.chronological_order[:50],  # Limit for response size
        related_concepts=evolution.related_concepts,
    )


@router.get("/semantic/themes")
async def get_available_themes():
    """
    Get list of available thematic categories for filtering.

    Arabic: قائمة المواضيع المتاحة للتصفية
    """
    return {
        "themes": [
            {
                "id": theme.value,
                "name_en": theme.value.replace("_", " ").title(),
                "name_ar": THEME_LABELS_AR.get(theme, ""),
            }
            for theme in ThematicCategory
        ]
    }


# =============================================================================
# ADVANCED SIMILARITY SEARCH API
# =============================================================================

from app.services.advanced_similarity import (
    AdvancedSimilarityService,
    AdvancedSimilarityMatch,
    SimilaritySearchResult,
    SimilarityScores,
    ConnectionType,
    THEME_COLORS,
    THEME_LABELS_AR as ADV_THEME_LABELS_AR,
)


class SimilarityScoresResponse(BaseModel):
    """Detailed similarity scores."""
    jaccard: float
    cosine: float
    concept_overlap: float
    grammatical: float
    semantic: float
    root_based: float
    contextual_jaccard: float = 0.0  # Weighted by thematic significance
    contextual_cosine: float = 0.0   # Weighted TF-IDF
    prophetic: float = 0.0           # Prophetic theme similarity
    narrative: float = 0.0           # Narrative arc similarity
    combined: float


class AdvancedSimilarityMatchResponse(BaseModel):
    """Response model for an advanced similarity match."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    text_imlaei: str
    reference: str
    scores: SimilarityScoresResponse
    connection_type: str
    connection_strength: str
    shared_words: List[str]
    shared_roots: List[str]
    shared_concepts: List[str]
    shared_themes: List[str]
    primary_theme: str
    primary_theme_ar: str
    theme_color: str
    sentence_structure: str
    sentence_structure_ar: str
    # Prophetic/narrative connections
    shared_prophets: List[str] = []
    cross_story_theme: str = ""
    cross_story_theme_ar: str = ""
    narrative_position: str = ""
    # Tafsir availability
    tafsir_available: bool = False
    # User feedback
    relevance_score: Optional[float] = None
    # Explanations
    similarity_explanation_ar: str
    similarity_explanation_en: str

    class Config:
        from_attributes = True


class AdvancedSimilaritySearchResponse(BaseModel):
    """Response for advanced similarity search."""
    source_verse: Dict[str, Any]
    source_themes: List[str]
    source_structure: str
    total_similar: int
    matches: List[AdvancedSimilarityMatchResponse]
    theme_distribution: Dict[str, int]
    connection_type_distribution: Dict[str, int]
    search_time_ms: float
    theme_colors: Dict[str, str]
    connection_types: List[Dict[str, str]]


@router.get("/similarity/fast/{sura_no}/{aya_no}")
async def fast_similarity_search(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_score: float = Query(0.1, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    exclude_same_sura: bool = Query(False, description="Exclude verses from same sura"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Fast similarity search using pre-computed TF-IDF vectors.

    This endpoint is optimized for speed (<100ms) using:
    - Pre-computed TF-IDF matrix loaded in memory
    - Numpy vectorized cosine similarity
    - LRU caching for repeated queries
    - Bismillah exclusion built-in

    Arabic: بحث سريع عن الآيات المتشابهة باستخدام المتجهات المحسوبة مسبقًا
    """
    from app.services.fast_similarity import get_fast_similarity_service

    service = get_fast_similarity_service()

    # Initialize if not already done
    if not service.is_initialized():
        await service.initialize(session)

    result = await service.find_similar(
        sura_no=sura_no,
        aya_no=aya_no,
        top_k=top_k,
        min_score=min_score,
        exclude_same_sura=exclude_same_sura,
        session=session,
    )

    return result


@router.get("/similarity/advanced/{sura_no}/{aya_no}")
async def advanced_similarity_search(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(20, ge=1, le=100, description="Maximum results"),
    min_score: float = Query(0.25, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    exclude_same_sura: bool = Query(False, description="Exclude verses from same sura"),
    connection_type: Optional[str] = Query(None, description="Filter by connection type"),
    exclude_bismillah: bool = Query(True, description="Exclude Bismillah from similarity computation (recommended)"),
    use_fast: bool = Query(True, description="Use fast pre-computed similarity (recommended)"),
    session: AsyncSession = Depends(get_async_session),
) -> AdvancedSimilaritySearchResponse:
    """
    Advanced similarity search with multi-layered scoring.

    This endpoint finds verses similar to the given verse using multiple
    similarity algorithms and provides detailed scoring breakdown.

    Arabic: بحث متقدم عن الآيات المتشابهة مع تحليل متعدد المستويات

    Algorithms used:
    - Jaccard Similarity: Word overlap measure
    - Cosine Similarity: TF-IDF vector comparison
    - Concept Overlap: Shared thematic concepts
    - Grammatical Similarity: Sentence structure comparison
    - Root-Based: Shared Arabic root morphology

    Args:
        sura_no: Source verse sura number (1-114)
        aya_no: Source verse aya number
        top_k: Maximum number of results
        min_score: Minimum combined score threshold (0-1)
        theme: Filter results by theme
        exclude_same_sura: Only show verses from other suras
        connection_type: Filter by connection type (lexical, thematic, conceptual, grammatical, semantic, root_based)

    Returns:
        Detailed similarity results with score breakdowns and visual metadata
    """
    # Use fast pre-computed similarity when no special filters are needed
    if use_fast and not theme and not connection_type:
        from app.services.fast_similarity import get_fast_similarity_service

        fast_service = get_fast_similarity_service()
        if not fast_service.is_initialized():
            await fast_service.initialize(session)

        if fast_service.is_initialized():
            fast_result = await fast_service.find_similar(
                sura_no=sura_no,
                aya_no=aya_no,
                top_k=top_k,
                min_score=min_score,
                exclude_same_sura=exclude_same_sura,
                session=session,
            )

            # Convert fast results to advanced response format
            matches_response = []
            for m in fast_result.get('matches', []):
                matches_response.append(AdvancedSimilarityMatchResponse(
                    verse_id=m['verse_id'],
                    sura_no=m['sura_no'],
                    sura_name_ar=m['sura_name_ar'],
                    sura_name_en=m['sura_name_en'],
                    aya_no=m['aya_no'],
                    text_uthmani=m['text_uthmani'],
                    text_imlaei=m['text_imlaei'],
                    reference=m['reference'],
                    scores=SimilarityScoresResponse(
                        jaccard=0.0,
                        cosine=m['similarity_score'],
                        concept_overlap=0.0,
                        grammatical=0.0,
                        semantic=0.0,
                        root_based=0.0,
                        contextual_jaccard=0.0,
                        contextual_cosine=m['similarity_score'],
                        prophetic=0.0,
                        narrative=0.0,
                        combined=m['similarity_score'],
                    ),
                    connection_type="lexical",
                    connection_strength="moderate" if m['similarity_score'] >= 0.4 else "weak",
                    shared_words=m.get('shared_words', []),
                    shared_roots=[],
                    shared_concepts=[],
                    shared_themes=[],
                    primary_theme="",
                    primary_theme_ar="",
                    theme_color="#6B7280",
                    sentence_structure="",
                    sentence_structure_ar="",
                    shared_prophets=[],
                    cross_story_theme="",
                    cross_story_theme_ar="",
                    narrative_position="",
                    tafsir_available=True,
                    relevance_score=None,
                    similarity_explanation_ar=f"كلمات مشتركة: {', '.join(m.get('shared_words', [])[:3])}" if m.get('shared_words') else "تشابه في المعنى",
                    similarity_explanation_en=f"Shared words: {', '.join(m.get('shared_words', [])[:3])}" if m.get('shared_words') else "Semantic similarity",
                ))

            source_verse = fast_result.get('source_verse', {})
            return AdvancedSimilaritySearchResponse(
                source_verse={
                    'verse_id': source_verse.get('verse_id', 0),
                    'sura_no': source_verse.get('sura_no', sura_no),
                    'sura_name_ar': source_verse.get('sura_name_ar', ''),
                    'sura_name_en': source_verse.get('sura_name_en', ''),
                    'aya_no': source_verse.get('aya_no', aya_no),
                    'text_uthmani': source_verse.get('text_uthmani', ''),
                    'text_imlaei': source_verse.get('text_imlaei', ''),
                    'reference': source_verse.get('reference', f"{sura_no}:{aya_no}"),
                },
                source_themes=[],
                source_structure="",
                total_similar=fast_result.get('total_similar', len(matches_response)),
                matches=matches_response,
                theme_distribution={},
                connection_type_distribution={"lexical": len(matches_response)},
                search_time_ms=fast_result.get('search_time_ms', 0),
                theme_colors={},
                connection_types=[{"type": "lexical", "label": "Lexical", "label_ar": "لفظي"}],
            )

    # Fallback to slow advanced search
    service = AdvancedSimilarityService(session)

    connection_types_filter = [connection_type] if connection_type else None

    result = await service.find_similar_verses(
        sura_no=sura_no,
        aya_no=aya_no,
        top_k=top_k,
        min_score=min_score,
        theme_filter=theme,
        exclude_same_sura=exclude_same_sura,
        connection_types=connection_types_filter,
        exclude_bismillah=exclude_bismillah,  # Explicitly pass to filter out Bismillah-based matches
    )

    # Convert matches to response format
    matches_response = []
    for match in result.matches:
        matches_response.append(AdvancedSimilarityMatchResponse(
            verse_id=match.verse_id,
            sura_no=match.sura_no,
            sura_name_ar=match.sura_name_ar,
            sura_name_en=match.sura_name_en,
            aya_no=match.aya_no,
            text_uthmani=match.text_uthmani,
            text_imlaei=match.text_imlaei,
            reference=match.reference,
            scores=SimilarityScoresResponse(
                jaccard=match.scores.jaccard,
                cosine=match.scores.cosine,
                concept_overlap=match.scores.concept_overlap,
                grammatical=match.scores.grammatical,
                semantic=match.scores.semantic,
                root_based=match.scores.root_based,
                contextual_jaccard=match.scores.contextual_jaccard,
                contextual_cosine=match.scores.contextual_cosine,
                prophetic=match.scores.prophetic,
                narrative=match.scores.narrative,
                combined=match.scores.combined,
            ),
            connection_type=match.connection_type.value,
            connection_strength=match.connection_strength,
            shared_words=match.shared_words,
            shared_roots=match.shared_roots,
            shared_concepts=match.shared_concepts,
            shared_themes=match.shared_themes,
            primary_theme=match.primary_theme,
            primary_theme_ar=match.primary_theme_ar,
            theme_color=match.theme_color,
            sentence_structure=match.sentence_structure,
            sentence_structure_ar=match.sentence_structure_ar,
            # Enhanced prophetic/narrative connections
            shared_prophets=match.shared_prophets,
            cross_story_theme=match.cross_story_theme,
            cross_story_theme_ar=match.cross_story_theme_ar,
            narrative_position=match.narrative_position,
            tafsir_available=match.tafsir_available,
            relevance_score=match.relevance_score,
            similarity_explanation_ar=match.similarity_explanation_ar,
            similarity_explanation_en=match.similarity_explanation_en,
        ))

    # Connection type info for UI
    connection_type_info = [
        {"id": "lexical", "name_en": "Lexical (Word Match)", "name_ar": "لفظي (تطابق الكلمات)", "color": "#3B82F6"},
        {"id": "thematic", "name_en": "Thematic", "name_ar": "موضوعي", "color": "#8B5CF6"},
        {"id": "conceptual", "name_en": "Conceptual", "name_ar": "مفاهيمي", "color": "#06B6D4"},
        {"id": "grammatical", "name_en": "Grammatical", "name_ar": "نحوي", "color": "#F59E0B"},
        {"id": "semantic", "name_en": "Semantic", "name_ar": "دلالي", "color": "#10B981"},
        {"id": "root_based", "name_en": "Root-Based", "name_ar": "جذري", "color": "#EF4444"},
    ]

    return AdvancedSimilaritySearchResponse(
        source_verse=result.source_verse,
        source_themes=result.source_themes,
        source_structure=result.source_structure,
        total_similar=result.total_similar,
        matches=matches_response,
        theme_distribution=result.theme_distribution,
        connection_type_distribution=result.connection_type_distribution,
        search_time_ms=result.search_time_ms,
        theme_colors=THEME_COLORS,
        connection_types=connection_type_info,
    )


@router.get("/similarity/cross-sura/{sura_no}/{aya_no}")
async def cross_sura_connections(
    sura_no: int,
    aya_no: int,
    top_k: int = Query(10, ge=1, le=50, description="Maximum results"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find similar verses from OTHER suras only.

    Useful for discovering how themes and concepts appear across different suras.

    Arabic: البحث عن آيات متشابهة من سور أخرى
    """
    service = AdvancedSimilarityService(session)

    matches = await service.find_cross_sura_connections(
        sura_no=sura_no,
        aya_no=aya_no,
        top_k=top_k,
    )

    return {
        "source_reference": f"{sura_no}:{aya_no}",
        "total_connections": len(matches),
        "connections": [
            {
                "reference": m.reference,
                "sura_name_ar": m.sura_name_ar,
                "sura_name_en": m.sura_name_en,
                "text_uthmani": m.text_uthmani,
                "combined_score": m.scores.combined,
                "connection_type": m.connection_type.value,
                "connection_strength": m.connection_strength,
                "shared_themes": m.shared_themes,
                "theme_color": m.theme_color,
                "explanation_ar": m.similarity_explanation_ar,
                "explanation_en": m.similarity_explanation_en,
            }
            for m in matches
        ],
    }


@router.get("/similarity/theme/{theme}")
async def verses_by_theme(
    theme: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all verses related to a specific theme.

    Arabic: الحصول على الآيات المتعلقة بموضوع معين

    Available themes: tawheed, prophets, afterlife, worship, ethics, law, history, nature, guidance, community
    """
    service = AdvancedSimilarityService(session)

    verses = await service.get_theme_verses(theme=theme, limit=limit)

    return {
        "theme": theme,
        "theme_ar": ADV_THEME_LABELS_AR.get(theme, theme),
        "theme_color": THEME_COLORS.get(theme, "#6B7280"),
        "total_verses": len(verses),
        "verses": verses,
    }


@router.get("/similarity/connection-types")
async def get_connection_types():
    """
    Get available connection types for filtering.

    Arabic: قائمة أنواع الروابط المتاحة
    """
    return {
        "connection_types": [
            {"id": ct.value, "name_en": ct.value.replace("_", " ").title(), "name_ar": label_ar}
            for ct, label_ar in [
                (ConnectionType.LEXICAL, "لفظي"),
                (ConnectionType.THEMATIC, "موضوعي"),
                (ConnectionType.CONCEPTUAL, "مفاهيمي"),
                (ConnectionType.GRAMMATICAL, "نحوي"),
                (ConnectionType.SEMANTIC, "دلالي"),
                (ConnectionType.ROOT_BASED, "جذري"),
                (ConnectionType.NARRATIVE, "سردي"),
                (ConnectionType.PROPHETIC, "نبوي"),
            ]
        ]
    }


# =============================================================================
# CROSS-STORY & STORY MODE ENDPOINTS
# =============================================================================


class CrossStoryConnectionResponse(BaseModel):
    """Response for cross-story connection."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    reference: str
    prophet: str
    theme_id: str
    theme_ar: str
    theme_en: str


class CrossStoryResponse(BaseModel):
    """Response for cross-story thematic connections."""
    prophet: str
    prophet_themes: List[str]
    related_prophets: List[str]
    source_verses_count: int
    cross_story_connections: List[CrossStoryConnectionResponse]
    available_themes: List[Dict[str, str]]


class NarrativeSectionResponse(BaseModel):
    """Response for a narrative arc section."""
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    verses: List[Dict[str, Any]]


class NarrativeArcResponse(BaseModel):
    """Response for story mode narrative arc."""
    introduction: NarrativeSectionResponse
    development: NarrativeSectionResponse
    climax: NarrativeSectionResponse
    resolution: NarrativeSectionResponse


class StoryModeResponse(BaseModel):
    """Response for story mode."""
    theme: str
    theme_ar: str
    theme_en: str
    theme_color: str
    total_verses: int
    related_prophets: List[str]
    narrative_arc: NarrativeArcResponse


class StoryThemeResponse(BaseModel):
    """Response for an available story theme."""
    id: str
    name_ar: str
    name_en: str
    color: str
    related_prophets: Optional[List[str]] = None
    category: str


@router.get("/story/cross-connections/{prophet}")
async def get_cross_story_connections(
    prophet: str,
    theme: Optional[str] = Query(None, description="Filter by cross-story theme"),
    limit: int = Query(30, ge=1, le=100, description="Maximum results"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find cross-story thematic connections for a prophet's trials and experiences.

    This endpoint allows users to explore how themes from one prophet's story
    appear in other prophets' narratives. For example, searching for Prophet Musa
    will show similar trials (divine tests, community opposition) from other prophets.

    Arabic: البحث عن الروابط الموضوعية عبر قصص الأنبياء

    Args:
        prophet: Prophet name in Arabic (e.g., "موسى", "إبراهيم", "يوسف")
        theme: Optional filter by theme (e.g., "divine_tests", "community_opposition")
        limit: Maximum number of related verses to return

    Returns:
        Cross-story connections with related prophets and themes

    Examples:
        - /story/cross-connections/موسى - Find stories related to Musa's trials
        - /story/cross-connections/إبراهيم?theme=sacrifice_submission - Ibrahim's sacrifice theme
        - /story/cross-connections/يوسف?theme=family_trials - Yusuf's family trials
    """
    service = AdvancedSimilarityService(session)

    result = await service.find_cross_story_connections(
        prophet_name=prophet,
        cross_theme=theme,
        limit=limit,
    )

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Prophet not found")
        )

    return result


@router.get("/story/narrative/{theme}")
async def get_story_mode_narrative(
    theme: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum verses"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Story Mode: Generate a narrative arc of verses on a theme.

    This endpoint presents related verses in a story-like narrative arc,
    linking thematic verses across different surahs to create a cohesive
    journey through the Quran on a specific topic.

    Arabic: وضع القصة - عرض الآيات في قوس سردي موضوعي

    Args:
        theme: Theme identifier (patience, gratitude, trust, divine_tests, etc.)
        limit: Maximum total verses to include

    Returns:
        Verses organized in narrative sections: introduction, development, climax, resolution

    Available themes:
        - patience (الصبر)
        - gratitude (الشكر)
        - trust (التوكل)
        - mercy (الرحمة)
        - guidance (الهداية)
        - divine_tests (الابتلاءات الإلهية)
        - community_opposition (معارضة القوم)
        - divine_rescue (النجاة الإلهية)
        - sacrifice_submission (التضحية والتسليم)
        - family_trials (ابتلاءات الأسرة)
        - patience_reward (الصبر والجزاء)

    Example response structure:
        narrative_arc:
            introduction: Opening verses about the theme
            development: Elaboration and examples
            climax: Key moments and peak verses
            resolution: Lessons and wisdom
    """
    service = AdvancedSimilarityService(session)

    result = await service.get_story_mode_narrative(
        theme=theme,
        limit=limit,
    )

    return result


@router.get("/story/themes", response_model=List[StoryThemeResponse])
async def get_available_story_themes(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get available themes for Story Mode.

    Returns all themes that can be used with the story mode narrative endpoint,
    including cross-story themes, virtues, and divine attributes.

    Arabic: قائمة المواضيع المتاحة لوضع القصة
    """
    service = AdvancedSimilarityService(session)
    themes = await service.get_available_story_themes()

    return [
        StoryThemeResponse(
            id=t["id"],
            name_ar=t.get("name_ar", ""),
            name_en=t.get("name_en", ""),
            color=t.get("color", "#6B7280"),
            related_prophets=t.get("related_prophets"),
            category=t.get("category", "general"),
        )
        for t in themes
    ]


@router.get("/story/prophets")
async def get_available_prophets():
    """
    Get list of prophets available for cross-story connections.

    Arabic: قائمة الأنبياء المتاحين للبحث عن الروابط الموضوعية
    """
    from app.services.advanced_similarity import PROPHETIC_THEMES

    return {
        "prophets": [
            {
                "name_ar": prophet,
                "themes": data.get("themes", []),
                "related_prophets": data.get("related_prophets", []),
                "trials": data.get("trials", []),
            }
            for prophet, data in PROPHETIC_THEMES.items()
        ]
    }


# =============================================================================
# Search History & Personalization Endpoints
# =============================================================================

from app.services.search_history import search_history_service


class SearchHistoryEntryResponse(BaseModel):
    """Search history entry response."""
    query: str
    query_type: str
    timestamp: str
    result_count: int
    clicked_verses: List[str]


class SearchSuggestionResponse(BaseModel):
    """Search suggestion response."""
    query: str
    query_type: str
    frequency: int
    relevance_score: float


class VerseRecommendationResponse(BaseModel):
    """Verse recommendation response."""
    sura_no: int
    aya_no: int
    reference: str
    text_uthmani: str
    sura_name_ar: str
    sura_name_en: str
    reason: str
    reason_ar: str
    confidence: float


class RecordSearchRequest(BaseModel):
    """Request to record a search."""
    query: str
    query_type: str = "text"
    result_count: int = 0
    themes: Optional[List[str]] = None


class RecordClickRequest(BaseModel):
    """Request to record a verse click."""
    sura_no: int
    aya_no: int
    context: str = "search"


@router.post("/history/search")
async def record_search(
    request: RecordSearchRequest,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Record a search query in the user's history.

    Arabic: تسجيل استعلام بحث في سجل المستخدم
    """
    await search_history_service.record_search(
        session_id=session_id,
        query=request.query,
        query_type=request.query_type,
        result_count=request.result_count,
        themes=request.themes,
    )
    return {"status": "recorded", "session_id": session_id}


@router.post("/history/click")
async def record_verse_click(
    request: RecordClickRequest,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Record a verse click/view in the user's history.

    Arabic: تسجيل عرض آية في سجل المستخدم
    """
    await search_history_service.record_verse_click(
        session_id=session_id,
        sura_no=request.sura_no,
        aya_no=request.aya_no,
        context=request.context,
    )
    return {"status": "recorded", "verse": f"{request.sura_no}:{request.aya_no}"}


@router.get("/history", response_model=List[SearchHistoryEntryResponse])
async def get_search_history(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(20, ge=1, le=100),
    query_type: Optional[str] = Query(None),
):
    """
    Get user's search history.

    Arabic: استرجاع سجل بحث المستخدم
    """
    history = await search_history_service.get_session_history(
        session_id=session_id,
        limit=limit,
        query_type=query_type,
    )

    return [
        SearchHistoryEntryResponse(
            query=entry.query,
            query_type=entry.query_type,
            timestamp=entry.timestamp.isoformat(),
            result_count=entry.result_count,
            clicked_verses=entry.clicked_verses,
        )
        for entry in history
    ]


@router.get("/history/suggestions", response_model=List[SearchSuggestionResponse])
async def get_search_suggestions(
    session_id: str = Query(..., description="User session ID"),
    prefix: Optional[str] = Query(None, description="Search prefix for filtering"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get personalized search suggestions based on history.

    Arabic: الحصول على اقتراحات بحث مخصصة
    """
    suggestions = await search_history_service.get_search_suggestions(
        session_id=session_id,
        prefix=prefix,
        limit=limit,
    )

    return [
        SearchSuggestionResponse(
            query=s.query,
            query_type=s.query_type,
            frequency=s.frequency,
            relevance_score=s.relevance_score,
        )
        for s in suggestions
    ]


@router.get("/history/recommendations", response_model=List[VerseRecommendationResponse])
async def get_personalized_recommendations(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get personalized verse recommendations based on user's search history and interests.

    Arabic: الحصول على توصيات آيات مخصصة بناءً على اهتمامات المستخدم
    """
    recommendations = await search_history_service.get_personalized_recommendations(
        session_id=session_id,
        session=session,
        limit=limit,
    )

    return [
        VerseRecommendationResponse(
            sura_no=r.sura_no,
            aya_no=r.aya_no,
            reference=r.reference,
            text_uthmani=r.text_uthmani,
            sura_name_ar=r.sura_name_ar,
            sura_name_en=r.sura_name_en,
            reason=r.reason,
            reason_ar=r.reason_ar,
            confidence=r.confidence,
        )
        for r in recommendations
    ]


@router.get("/history/interests")
async def get_theme_interests(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get user's theme interests based on search history.

    Arabic: الحصول على اهتمامات المستخدم الموضوعية
    """
    interests = await search_history_service.get_theme_interests(session_id)
    return {
        "session_id": session_id,
        "interests": interests,
        "top_themes": sorted(interests.items(), key=lambda x: x[1], reverse=True)[:10],
    }


@router.delete("/history")
async def clear_search_history(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Clear user's search history.

    Arabic: مسح سجل بحث المستخدم
    """
    await search_history_service.clear_session_history(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/history/stats")
async def get_search_stats():
    """
    Get global search statistics (admin endpoint).

    Arabic: إحصائيات البحث العامة
    """
    return search_history_service.get_stats()


# =============================================================================
# USER FEEDBACK SYSTEM FOR SIMILARITY RESULTS
# =============================================================================


class SimilarityFeedbackRequest(BaseModel):
    """Request to record similarity feedback."""
    source_reference: str = Field(..., description="Source verse reference (e.g., '2:255')")
    target_reference: str = Field(..., description="Target verse reference (e.g., '3:18')")
    is_relevant: bool = Field(..., description="True if user found the result relevant")
    feedback_type: str = Field(default="thumbs_up", description="Type: thumbs_up, thumbs_down, or rating")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Optional 1-5 star rating")
    notes: Optional[str] = Field(None, max_length=500, description="Optional user comment")


class SimilarityFeedbackResponse(BaseModel):
    """Response for similarity feedback."""
    source_reference: str
    target_reference: str
    is_relevant: bool
    feedback_type: str
    rating: Optional[float]
    timestamp: str
    notes: Optional[str]


@router.post("/similarity/feedback")
async def record_similarity_feedback(
    request: SimilarityFeedbackRequest,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Record user feedback on a similarity search result.

    This feedback is used to improve search relevance over time through
    machine learning. Users can mark results as relevant/irrelevant.

    Arabic: تسجيل ملاحظات المستخدم على نتيجة البحث عن التشابه

    Args:
        session_id: User's session identifier
        request.source_reference: The source verse (e.g., "2:255")
        request.target_reference: The similar verse shown (e.g., "3:18")
        request.is_relevant: True if user found this result helpful
        request.feedback_type: "thumbs_up", "thumbs_down", or "rating"
        request.rating: Optional 1-5 star rating
        request.notes: Optional comment

    Returns:
        Status and updated community relevance score
    """
    result = await search_history_service.record_similarity_feedback(
        session_id=session_id,
        source_reference=request.source_reference,
        target_reference=request.target_reference,
        is_relevant=request.is_relevant,
        feedback_type=request.feedback_type,
        rating=request.rating,
        notes=request.notes,
    )

    return result


@router.get("/similarity/feedback/score")
async def get_similarity_relevance_score(
    source_reference: str = Query(..., description="Source verse reference"),
    target_reference: str = Query(..., description="Target verse reference"),
):
    """
    Get the community relevance score for a verse pair.

    Returns the aggregated user feedback score for how relevant
    users have found this similarity pairing.

    Arabic: الحصول على درجة الصلة المجتمعية لزوج الآيات
    """
    score = await search_history_service.get_relevance_score(
        source_reference=source_reference,
        target_reference=target_reference,
    )

    return {
        "source_reference": source_reference,
        "target_reference": target_reference,
        "relevance_score": score,
        "has_feedback": score is not None,
    }


@router.get("/similarity/feedback/history", response_model=List[SimilarityFeedbackResponse])
async def get_session_similarity_feedback(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get user's similarity feedback history.

    Arabic: الحصول على سجل ملاحظات التشابه للمستخدم
    """
    feedback_list = await search_history_service.get_session_feedback(
        session_id=session_id,
        limit=limit,
    )

    return [
        SimilarityFeedbackResponse(
            source_reference=fb.source_reference,
            target_reference=fb.target_reference,
            is_relevant=fb.is_relevant,
            feedback_type=fb.feedback_type,
            rating=fb.rating,
            timestamp=fb.timestamp.isoformat(),
            notes=fb.notes,
        )
        for fb in feedback_list
    ]


@router.get("/similarity/feedback/stats")
async def get_feedback_statistics():
    """
    Get aggregated feedback statistics (admin endpoint).

    Shows most/least relevant pairs and overall feedback metrics.

    Arabic: إحصائيات الملاحظات المجمعة
    """
    return await search_history_service.get_feedback_stats()


# =============================================================================
# TAFSIR INTEGRATION FOR SIMILARITY RESULTS
# =============================================================================


@router.get("/similarity/tafsir/{sura_no}/{aya_no}")
async def get_verse_tafsir_for_similarity(
    sura_no: int,
    aya_no: int,
    sources: Optional[List[str]] = Query(None, description="Filter by source IDs"),
    language: Optional[str] = Query(None, description="Filter by language (ar/en)"),
    limit: int = Query(3, ge=1, le=10, description="Max tafsir entries"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get tafsir for a verse in similarity search context.

    This endpoint provides tafsir summaries optimized for display alongside
    similarity search results - shorter excerpts with source info.

    Arabic: الحصول على تفسير الآية في سياق البحث عن التشابه

    Returns:
        Compact tafsir entries with source info and preview text
    """
    # First get the verse ID
    verse_result = await session.execute(
        select(QuranVerse.id).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no,
        )
    )
    verse_id = verse_result.scalar_one_or_none()

    if not verse_id:
        raise HTTPException(status_code=404, detail=f"Verse {sura_no}:{aya_no} not found")

    # Get tafseer chunks
    query = select(TafseerChunk).where(
        TafseerChunk.verse_start_id <= verse_id,
        TafseerChunk.verse_end_id >= verse_id,
    ).limit(limit)

    if sources:
        query = query.where(TafseerChunk.source_id.in_(sources))

    result = await session.execute(query)
    chunks = result.scalars().all()

    # Get tafsir sources for names
    sources_result = await session.execute(select(TafseerSource))
    source_map = {s.id: s for s in sources_result.scalars().all()}

    tafsir_entries = []
    for chunk in chunks:
        if language == "ar" and not chunk.content_ar:
            continue
        if language == "en" and not chunk.content_en:
            continue

        source = source_map.get(chunk.source_id)

        # Create preview (first 300 chars)
        content_ar = chunk.content_ar or ""
        content_en = chunk.content_en or ""
        preview_ar = content_ar[:300] + "..." if len(content_ar) > 300 else content_ar
        preview_en = content_en[:300] + "..." if len(content_en) > 300 else content_en

        tafsir_entries.append({
            "chunk_id": chunk.chunk_id,
            "source_id": chunk.source_id,
            "source_name_ar": source.name_ar if source else None,
            "source_name_en": source.name_en if source else None,
            "verse_reference": f"{sura_no}:{aya_no}",
            "preview_ar": preview_ar if language != "en" else None,
            "preview_en": preview_en if language != "ar" else None,
            "full_content_available": len(content_ar) > 300 or len(content_en) > 300,
            "methodology": source.methodology if source else None,
        })

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "tafsir_available": len(tafsir_entries) > 0,
        "tafsir_count": len(tafsir_entries),
        "tafsir_entries": tafsir_entries,
    }


# =============================================================================
# CROSS-TAFSIR COMPARISON
# =============================================================================


@router.get("/tafsir/compare/{sura_no}/{aya_no}")
async def compare_tafsir_interpretations(
    sura_no: int,
    aya_no: int,
    sources: Optional[List[str]] = Query(None, description="Specific source IDs to compare"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Compare tafsir interpretations from multiple classical sources.

    This endpoint allows users to see how different scholars interpreted
    the same verse, enhancing comprehension and contextual understanding.

    Arabic: مقارنة تفسيرات العلماء المختلفة للآية الواحدة

    Returns:
        Multiple tafsir interpretations side-by-side with source metadata
    """
    # Get verse ID
    verse_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no,
        )
    )
    verse = verse_result.scalar_one_or_none()

    if not verse:
        raise HTTPException(status_code=404, detail=f"Verse {sura_no}:{aya_no} not found")

    # Get all tafsir chunks for this verse
    query = select(TafseerChunk).where(
        TafseerChunk.verse_start_id <= verse.id,
        TafseerChunk.verse_end_id >= verse.id,
    )

    if sources:
        query = query.where(TafseerChunk.source_id.in_(sources))

    result = await session.execute(query)
    chunks = result.scalars().all()

    # Get all tafsir sources
    sources_result = await session.execute(select(TafseerSource))
    source_map = {s.id: s for s in sources_result.scalars().all()}

    # Group by source for comparison
    comparisons = []
    for chunk in chunks:
        source = source_map.get(chunk.source_id)
        if not source:
            continue

        comparisons.append({
            "source_id": chunk.source_id,
            "source_name_ar": source.name_ar,
            "source_name_en": source.name_en,
            "author_ar": source.author_ar,
            "author_en": source.author_en,
            "methodology": source.methodology,
            "era": source.era,
            "content_ar": chunk.content_ar,
            "content_en": chunk.content_en,
            "chunk_id": chunk.chunk_id,
        })

    # Sort by era/historical order if available
    comparisons.sort(key=lambda x: x.get("era") or "z")

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "verse_text": verse.text_uthmani,
        "sura_name_ar": verse.sura_name_ar,
        "sura_name_en": verse.sura_name_en,
        "comparison_count": len(comparisons),
        "interpretations": comparisons,
    }


# =============================================================================
# BOOKMARKS & PERSONALIZATION ENDPOINTS
# =============================================================================


class BookmarkRequest(BaseModel):
    """Request to add a bookmark."""
    sura_no: int
    aya_no: int
    note: Optional[str] = None
    collection: str = "default"
    tags: Optional[List[str]] = None


class StudyGoalRequest(BaseModel):
    """Request to set a study goal."""
    goal_type: str = Field(..., description="memorization, comprehension, research, or reflection")
    themes: Optional[List[str]] = None
    prophets: Optional[List[str]] = None
    suras: Optional[List[int]] = None


@router.post("/bookmarks")
async def add_bookmark(
    request: BookmarkRequest,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Add a verse bookmark.

    Users can save verses for later reference with notes and tags.
    Collections help organize bookmarks by purpose (memorization, study, etc.)

    Arabic: إضافة آية إلى المحفوظات
    """
    result = await search_history_service.add_bookmark(
        session_id=session_id,
        sura_no=request.sura_no,
        aya_no=request.aya_no,
        note=request.note,
        collection=request.collection,
        tags=request.tags,
    )
    return result


@router.delete("/bookmarks/{sura_no}/{aya_no}")
async def remove_bookmark(
    sura_no: int,
    aya_no: int,
    session_id: str = Query(..., description="User session ID"),
):
    """Remove a verse bookmark."""
    result = await search_history_service.remove_bookmark(
        session_id=session_id,
        sura_no=sura_no,
        aya_no=aya_no,
    )
    return result


@router.get("/bookmarks")
async def get_bookmarks(
    session_id: str = Query(..., description="User session ID"),
    collection: Optional[str] = Query(None, description="Filter by collection"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
):
    """
    Get user's bookmarks.

    Arabic: الحصول على المحفوظات
    """
    bookmarks = await search_history_service.get_bookmarks(
        session_id=session_id,
        collection=collection,
        tags=tags,
    )
    return {"bookmarks": bookmarks, "count": len(bookmarks)}


@router.get("/bookmarks/collections")
async def get_bookmark_collections(
    session_id: str = Query(..., description="User session ID"),
):
    """Get user's bookmark collections with counts."""
    collections = await search_history_service.get_bookmark_collections(session_id)
    return {"collections": collections}


@router.post("/personalization/study-goal")
async def set_study_goal(
    request: StudyGoalRequest,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Set user's study goal for personalized results.

    Study goals affect how similarity results are ranked:
    - memorization: Emphasizes lexical and root-based connections
    - comprehension: Emphasizes thematic and conceptual connections
    - research: Emphasizes prophetic and narrative connections
    - reflection: Emphasizes thematic and semantic connections

    Arabic: تحديد هدف الدراسة للحصول على نتائج مخصصة
    """
    result = await search_history_service.set_study_goal(
        session_id=session_id,
        goal_type=request.goal_type,
        themes=request.themes,
        prophets=request.prophets,
        suras=request.suras,
    )
    return result


@router.get("/personalization/study-goal")
async def get_study_goal(
    session_id: str = Query(..., description="User session ID"),
):
    """Get user's current study goal."""
    goal = await search_history_service.get_study_goal(session_id)
    return {"goal": goal}


@router.get("/personalization/filters")
async def get_personalized_filters(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get personalized search filters based on user's history and goals.

    Returns suggested themes, prophets, and weight adjustments.

    Arabic: الحصول على الفلاتر المخصصة بناءً على سجل المستخدم
    """
    filters = await search_history_service.get_personalized_filters(session_id)
    return filters


@router.get("/personalization/topic-clusters")
async def get_topic_clusters(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get topic clusters based on user's search history.

    Arabic: الحصول على مجموعات المواضيع بناءً على سجل البحث
    """
    clusters = await search_history_service.get_topic_clusters_summary(session_id)
    return {"clusters": clusters}


@router.get("/similarity/feedback/learning")
async def get_feedback_learning_insights():
    """
    Get AI-based learning insights from user feedback.

    This endpoint analyzes feedback patterns to suggest algorithm improvements.

    Arabic: الحصول على رؤى التعلم من ملاحظات المستخدمين
    """
    insights = await search_history_service.learn_from_feedback()
    return insights


# =============================================================================
# ENHANCED THEMATIC EXPLORATION
# =============================================================================


@router.get("/themes/categories")
async def get_theme_categories():
    """
    Get all theme categories with their themes.

    Returns organized theme categories for exploration UI.

    Arabic: الحصول على فئات المواضيع
    """
    from app.services.advanced_similarity import (
        THEME_CATEGORIES,
        THEME_LABELS_AR,
        THEME_COLORS,
    )

    categories = []
    for cat_id, cat_data in THEME_CATEGORIES.items():
        themes = []
        for theme_id in cat_data.get("themes", []):
            themes.append({
                "id": theme_id,
                "name_ar": THEME_LABELS_AR.get(theme_id, theme_id),
                "name_en": theme_id.replace("_", " ").title(),
                "color": THEME_COLORS.get(theme_id, "#6B7280"),
            })

        categories.append({
            "id": cat_id,
            "name_ar": cat_data.get("ar", cat_id),
            "name_en": cat_data.get("en", cat_id),
            "themes": themes,
        })

    return {"categories": categories}


@router.get("/themes/all")
async def get_all_themes():
    """
    Get all available themes with metadata.

    Arabic: الحصول على جميع المواضيع المتاحة
    """
    from app.services.advanced_similarity import (
        THEME_LABELS_AR,
        THEME_COLORS,
        EXTENDED_THEME_KEYWORDS,
    )

    themes = []
    for theme_id, keywords in EXTENDED_THEME_KEYWORDS.items():
        themes.append({
            "id": theme_id,
            "name_ar": THEME_LABELS_AR.get(theme_id, theme_id),
            "name_en": theme_id.replace("_", " ").title(),
            "color": THEME_COLORS.get(theme_id, "#6B7280"),
            "keywords_sample": keywords[:5],
        })

    return {"themes": themes, "count": len(themes)}


@router.get("/prophets/all")
async def get_all_prophets_with_themes():
    """
    Get all prophets with their themes and moral lessons.

    Arabic: الحصول على جميع الأنبياء مع مواضيعهم ودروسهم
    """
    from app.services.advanced_similarity import PROPHETIC_THEMES

    prophets = []
    for prophet_name, data in PROPHETIC_THEMES.items():
        prophets.append({
            "name_ar": prophet_name,
            "trials": data.get("trials", []),
            "themes": data.get("themes", []),
            "related_prophets": data.get("related_prophets", []),
            "suras": data.get("suras", []),
            "moral_lessons": data.get("moral_lessons", {"ar": [], "en": []}),
        })

    return {"prophets": prophets, "count": len(prophets)}


@router.get("/cross-story/themes")
async def get_cross_story_themes():
    """
    Get all cross-story thematic connections.

    Arabic: الحصول على الروابط الموضوعية عبر القصص
    """
    from app.services.advanced_similarity import CROSS_STORY_THEMES

    themes = []
    for theme_id, data in CROSS_STORY_THEMES.items():
        themes.append({
            "id": theme_id,
            "name_ar": data.get("ar", theme_id),
            "name_en": data.get("en", theme_id),
            "description_ar": data.get("description_ar", ""),
            "description_en": data.get("description_en", ""),
            "keywords": data.get("keywords", []),
            "stories": data.get("stories", []),
        })

    return {"themes": themes, "count": len(themes)}


# =============================================================================
# SEMANTIC EMBEDDINGS & ADVANCED SIMILARITY
# =============================================================================


@router.get("/similarity/semantic/{sura_no}/{aya_no}")
async def get_semantic_similarity(
    sura_no: int,
    aya_no: int,
    limit: int = Query(20, ge=1, le=50),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find semantically similar verses using contextual embeddings.

    Uses transformer-based embeddings for deep semantic understanding
    beyond simple word overlap.

    Arabic: البحث عن آيات متشابهة دلالياً باستخدام التضمينات السياقية
    """
    from app.services.semantic_embeddings import semantic_embedding_service, contextual_enhancer

    # Get source verse
    source_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no,
        )
    )
    source_verse = source_result.scalar_one_or_none()

    if not source_verse:
        raise HTTPException(status_code=404, detail=f"Verse {sura_no}:{aya_no} not found")

    # Get candidate verses (sample for performance)
    candidates_result = await session.execute(
        select(QuranVerse.id, QuranVerse.text_uthmani)
        .where(QuranVerse.id != source_verse.id)
        .limit(500)  # Sample for performance
    )
    candidates = [(row.id, row.text_uthmani) for row in candidates_result.fetchall()]

    # Find similar by embedding
    similar_ids = await semantic_embedding_service.find_similar_by_embedding(
        source_verse.text_uthmani,
        candidates,
        top_k=limit,
        min_similarity=min_similarity,
    )

    # Get full verse data for results
    results = []
    for verse_id, sim_score in similar_ids:
        verse_result = await session.execute(
            select(QuranVerse).where(QuranVerse.id == verse_id)
        )
        verse = verse_result.scalar_one_or_none()
        if verse:
            # Get enhanced analysis
            enhanced = await contextual_enhancer.compute_enhanced_similarity(
                source_verse.text_uthmani,
                verse.text_uthmani,
                source_verse.sura_no,
                verse.sura_no,
                source_verse.aya_no,
                verse.aya_no,
            )

            results.append({
                "verse_id": verse.id,
                "sura_no": verse.sura_no,
                "sura_name_ar": verse.sura_name_ar,
                "sura_name_en": verse.sura_name_en,
                "aya_no": verse.aya_no,
                "reference": f"{verse.sura_no}:{verse.aya_no}",
                "text_uthmani": verse.text_uthmani,
                "semantic_similarity": sim_score,
                "enhanced_analysis": enhanced,
            })

    return {
        "source_verse": {
            "sura_no": source_verse.sura_no,
            "aya_no": source_verse.aya_no,
            "reference": f"{sura_no}:{aya_no}",
            "text": source_verse.text_uthmani,
        },
        "results": results,
        "count": len(results),
        "model_info": semantic_embedding_service.get_model_info(),
    }


@router.get("/similarity/model-info")
async def get_embedding_model_info():
    """Get information about the semantic embedding model."""
    from app.services.semantic_embeddings import semantic_embedding_service
    return semantic_embedding_service.get_model_info()


# =============================================================================
# STUDY PROGRESS TRACKING
# =============================================================================


@router.post("/progress/session/start")
async def start_study_session(
    goal_type: str = Query(..., description="memorization, comprehension, research, or reflection"),
    session_id: str = Query(..., description="User session ID"),
):
    """
    Start a new study session.

    Arabic: بدء جلسة دراسة جديدة
    """
    from app.services.study_progress import study_progress_service

    session = await study_progress_service.start_study_session(
        user_session_id=session_id,
        goal_type=goal_type,
    )

    return {
        "status": "started",
        "session_id": session.session_id,
        "goal_type": session.goal_type,
        "start_time": session.start_time.isoformat(),
    }


@router.post("/progress/session/end")
async def end_study_session(
    session_id: str = Query(..., description="User session ID"),
    verses_studied: Optional[List[str]] = Query(None),
    themes_explored: Optional[List[str]] = Query(None),
    prophets_studied: Optional[List[str]] = Query(None),
    notes: Optional[str] = Query(None),
):
    """
    End the current study session.

    Arabic: إنهاء جلسة الدراسة الحالية
    """
    from app.services.study_progress import study_progress_service

    session = await study_progress_service.end_study_session(
        user_session_id=session_id,
        verses_studied=verses_studied,
        themes_explored=themes_explored,
        prophets_studied=prophets_studied,
        notes=notes,
    )

    if not session:
        raise HTTPException(status_code=404, detail="No active session found")

    return {
        "status": "ended",
        "session_id": session.session_id,
        "duration_minutes": (
            (session.end_time - session.start_time).total_seconds() / 60
            if session.end_time else 0
        ),
        "verses_studied": len(session.verses_studied),
        "completion_percentage": session.completion_percentage,
    }


@router.post("/progress/memorization")
async def record_memorization_attempt(
    session_id: str = Query(..., description="User session ID"),
    sura_no: int = Query(...),
    aya_no: int = Query(...),
    confidence_level: int = Query(..., ge=0, le=5, description="0-5 confidence scale"),
):
    """
    Record a memorization attempt for a verse.

    Confidence levels:
    - 0: Can't recall at all
    - 1: Recognize but can't recite
    - 2: Can recite with many mistakes
    - 3: Can recite with few mistakes
    - 4: Can recite correctly with effort
    - 5: Can recite fluently

    Arabic: تسجيل محاولة حفظ آية
    """
    from app.services.study_progress import study_progress_service

    progress = await study_progress_service.record_memorization_attempt(
        user_session_id=session_id,
        sura_no=sura_no,
        aya_no=aya_no,
        confidence_level=confidence_level,
    )

    return {
        "verse_reference": progress.verse_reference,
        "status": progress.status,
        "confidence_level": progress.confidence_level,
        "review_count": progress.review_count,
        "next_review_due": progress.next_review_due.isoformat() if progress.next_review_due else None,
    }


@router.get("/progress/memorization")
async def get_memorization_progress(
    session_id: str = Query(..., description="User session ID"),
    sura_no: Optional[int] = Query(None, description="Filter by sura"),
):
    """
    Get memorization progress.

    Arabic: الحصول على تقدم الحفظ
    """
    from app.services.study_progress import study_progress_service

    progress_list = await study_progress_service.get_memorization_progress(
        user_session_id=session_id,
        sura_no=sura_no,
    )

    return {
        "progress": [
            {
                "verse_reference": p.verse_reference,
                "sura_no": p.sura_no,
                "aya_no": p.aya_no,
                "status": p.status,
                "confidence_level": p.confidence_level,
                "review_count": p.review_count,
                "last_review": p.last_review.isoformat() if p.last_review else None,
                "next_review_due": p.next_review_due.isoformat() if p.next_review_due else None,
            }
            for p in progress_list
        ],
        "count": len(progress_list),
    }


@router.get("/progress/memorization/due")
async def get_verses_due_for_review(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get verses that are due for review (spaced repetition).

    Arabic: الحصول على الآيات المستحقة للمراجعة
    """
    from app.services.study_progress import study_progress_service

    due_verses = await study_progress_service.get_verses_due_for_review(
        user_session_id=session_id,
        limit=limit,
    )

    return {
        "due_verses": [
            {
                "verse_reference": p.verse_reference,
                "sura_no": p.sura_no,
                "aya_no": p.aya_no,
                "confidence_level": p.confidence_level,
                "next_review_due": p.next_review_due.isoformat() if p.next_review_due else None,
            }
            for p in due_verses
        ],
        "count": len(due_verses),
    }


@router.get("/progress/memorization/stats")
async def get_memorization_stats(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get memorization statistics.

    Arabic: إحصائيات الحفظ
    """
    from app.services.study_progress import study_progress_service
    return await study_progress_service.get_memorization_stats(session_id)


@router.post("/progress/reflection")
async def add_reflection(
    session_id: str = Query(..., description="User session ID"),
    verse_reference: str = Query(..., description="e.g., '2:255'"),
    reflection_text: str = Query(..., description="Personal reflection"),
    theme: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
):
    """
    Add a personal reflection on a verse.

    Arabic: إضافة تأمل شخصي في آية
    """
    from app.services.study_progress import study_progress_service

    entry = await study_progress_service.add_reflection(
        user_session_id=session_id,
        verse_reference=verse_reference,
        reflection_text=reflection_text,
        theme=theme,
        tags=tags,
    )

    return {
        "status": "added",
        "entry_id": entry.entry_id,
        "verse_reference": entry.verse_reference,
        "created_at": entry.created_at.isoformat(),
    }


@router.get("/progress/reflections")
async def get_reflections(
    session_id: str = Query(..., description="User session ID"),
    verse_reference: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get personal reflections.

    Arabic: الحصول على التأملات الشخصية
    """
    from app.services.study_progress import study_progress_service

    reflections = await study_progress_service.get_reflections(
        user_session_id=session_id,
        verse_reference=verse_reference,
        theme=theme,
        limit=limit,
    )

    return {
        "reflections": [
            {
                "entry_id": r.entry_id,
                "verse_reference": r.verse_reference,
                "theme": r.theme,
                "reflection_text": r.reflection_text,
                "tags": r.tags,
                "created_at": r.created_at.isoformat(),
            }
            for r in reflections
        ],
        "count": len(reflections),
    }


@router.get("/progress/overall")
async def get_overall_progress(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get comprehensive progress overview.

    Arabic: نظرة شاملة على التقدم
    """
    from app.services.study_progress import study_progress_service
    return await study_progress_service.get_overall_progress(session_id)


@router.get("/progress/daily-stats")
async def get_daily_stats(
    session_id: str = Query(..., description="User session ID"),
    days: int = Query(7, ge=1, le=30),
):
    """
    Get daily study statistics.

    Arabic: إحصائيات الدراسة اليومية
    """
    from app.services.study_progress import study_progress_service
    return await study_progress_service.get_daily_stats(session_id, days)


@router.get("/progress/recommendations")
async def get_study_recommendations(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get personalized study recommendations.

    Arabic: الحصول على توصيات الدراسة المخصصة
    """
    from app.services.study_progress import study_progress_service
    return await study_progress_service.get_recommendations(session_id)


# =============================================================================
# RECOMMENDATION ENGINE
# =============================================================================


@router.get("/recommendations/themes")
async def get_theme_recommendations(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get personalized theme recommendations.

    Arabic: توصيات المواضيع المخصصة
    """
    from app.services.recommendation_engine import recommendation_engine
    from app.services.search_history import search_history_service

    # Get user's history
    theme_interests = await search_history_service.get_theme_interests(session_id)
    themes_explored = list(theme_interests.keys())

    # Get study goal
    goal = await search_history_service.get_study_goal(session_id)
    goal_type = goal.get("goal_type") if goal else None

    recommendations = await recommendation_engine.get_theme_recommendations(
        user_themes_explored=themes_explored,
        user_prophets_studied=[],
        study_goal=goal_type,
        limit=limit,
    )

    return {
        "recommendations": [
            {
                "theme_id": r.theme_id,
                "theme_name_ar": r.theme_name_ar,
                "theme_name_en": r.theme_name_en,
                "relevance_score": round(r.relevance_score, 3),
                "reason": r.reason,
                "reason_ar": r.reason_ar,
                "color": r.color,
            }
            for r in recommendations
        ],
        "count": len(recommendations),
    }


@router.get("/recommendations/prophets")
async def get_prophet_recommendations(
    session_id: str = Query(..., description="User session ID"),
    limit: int = Query(3, ge=1, le=10),
):
    """
    Get prophet study recommendations.

    Arabic: توصيات دراسة الأنبياء
    """
    from app.services.recommendation_engine import recommendation_engine
    from app.services.search_history import search_history_service

    # Get user's history
    theme_interests = await search_history_service.get_theme_interests(session_id)
    themes_explored = list(theme_interests.keys())

    recommendations = await recommendation_engine.get_prophet_recommendations(
        user_themes_explored=themes_explored,
        prophets_already_studied=[],
        limit=limit,
    )

    return {
        "recommendations": [
            {
                "prophet_name": r.prophet_name,
                "relevance_score": round(r.relevance_score, 3),
                "themes": r.themes,
                "moral_lessons": r.moral_lessons,
                "suggested_suras": r.suggested_suras,
                "reason": r.reason,
                "reason_ar": r.reason_ar,
            }
            for r in recommendations
        ],
        "count": len(recommendations),
    }


@router.get("/recommendations/exploration-path/{theme}")
async def get_theme_exploration_path(
    theme: str,
    depth: int = Query(3, ge=1, le=5),
):
    """
    Get an exploration path starting from a theme.

    Returns a graph of connected themes for interactive exploration.

    Arabic: مسار استكشاف المواضيع
    """
    from app.services.recommendation_engine import recommendation_engine

    path = await recommendation_engine.get_cross_theme_exploration_path(
        start_theme=theme,
        depth=depth,
    )

    return path


@router.get("/recommendations/journey/{theme}")
async def get_thematic_journey(
    theme: str,
    session_id: str = Query(..., description="User session ID"),
):
    """
    Generate a personalized thematic journey through the Quran.

    Creates a structured multi-step learning path.

    Arabic: رحلة موضوعية مخصصة عبر القرآن
    """
    from app.services.recommendation_engine import recommendation_engine

    journey = await recommendation_engine.get_thematic_journey(
        start_theme=theme,
        user_session_id=session_id,
        user_history={},
    )

    return journey


# =============================================================================
# MODERN TAFSIR SOURCES
# =============================================================================


@router.get("/tafsir/sources")
async def get_tafsir_sources(
    era: Optional[str] = Query(None, description="Filter by era: classical, modern, contemporary"),
    language: Optional[str] = Query(None, description="Filter by language: ar, en, fr, ur, id"),
    methodology: Optional[str] = Query(None, description="Filter by methodology"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all Tafsir sources with optional filtering.

    Returns a comprehensive catalog of classical and modern Tafsir sources.

    Arabic: الحصول على جميع مصادر التفسير
    """
    from app.services.tafsir_sources import (
        modern_tafsir_service,
        TafsirEra,
        TafsirLanguage,
        TafsirMethodology,
    )

    # Convert string params to enums
    era_enum = None
    if era:
        era_map = {"classical": TafsirEra.CLASSICAL, "modern": TafsirEra.MODERN, "contemporary": TafsirEra.CONTEMPORARY}
        era_enum = era_map.get(era.lower())

    lang_enum = None
    if language:
        lang_map = {"ar": TafsirLanguage.ARABIC, "en": TafsirLanguage.ENGLISH, "fr": TafsirLanguage.FRENCH,
                    "ur": TafsirLanguage.URDU, "id": TafsirLanguage.INDONESIAN}
        lang_enum = lang_map.get(language.lower())

    method_enum = None
    if methodology:
        method_map = {
            "bil_mathur": TafsirMethodology.BIL_MATHUR,
            "bil_ray": TafsirMethodology.BIL_RAY,
            "linguistic": TafsirMethodology.LINGUISTIC,
            "thematic": TafsirMethodology.THEMATIC,
            "scientific": TafsirMethodology.SCIENTIFIC,
            "social": TafsirMethodology.SOCIAL,
            "comprehensive": TafsirMethodology.COMPREHENSIVE,
        }
        method_enum = method_map.get(methodology.lower())

    sources = await modern_tafsir_service.get_all_sources(
        era=era_enum,
        language=lang_enum,
        methodology=method_enum,
        session=session,
    )

    return {
        "sources": [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "author_ar": s.author_ar,
                "author_en": s.author_en,
                "era": s.era.value,
                "methodology": s.methodology.value,
                "languages": s.languages,
                "description_ar": s.description_ar,
                "description_en": s.description_en,
                "strengths": s.strengths,
                "focus_areas": s.focus_areas,
                "is_available": s.is_available,
            }
            for s in sources
        ],
        "count": len(sources),
        "filters_applied": {
            "era": era,
            "language": language,
            "methodology": methodology,
        },
    }


@router.get("/tafsir/sources/modern")
async def get_modern_tafsir_sources(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get modern and contemporary Tafsir sources only.

    Arabic: الحصول على مصادر التفسير الحديثة والمعاصرة
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirEra

    modern_sources = await modern_tafsir_service.get_all_sources(era=TafsirEra.MODERN, session=session)
    contemporary_sources = await modern_tafsir_service.get_all_sources(era=TafsirEra.CONTEMPORARY, session=session)

    all_sources = modern_sources + contemporary_sources

    return {
        "modern_sources": [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "author_en": s.author_en,
                "era": s.era.value,
                "methodology": s.methodology.value,
                "languages": s.languages,
                "description_en": s.description_en,
                "is_available": s.is_available,
            }
            for s in all_sources
        ],
        "count": len(all_sources),
    }


@router.get("/tafsir/sources/{source_id}")
async def get_tafsir_source_details(
    source_id: str,
):
    """
    Get detailed information about a specific Tafsir source.

    Arabic: الحصول على تفاصيل مصدر التفسير
    """
    from app.services.tafsir_sources import modern_tafsir_service

    source = await modern_tafsir_service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Tafsir source '{source_id}' not found")

    return {
        "id": source.id,
        "name_ar": source.name_ar,
        "name_en": source.name_en,
        "author_ar": source.author_ar,
        "author_en": source.author_en,
        "era": source.era.value,
        "methodology": source.methodology.value,
        "languages": source.languages,
        "description_ar": source.description_ar,
        "description_en": source.description_en,
        "strengths": source.strengths,
        "focus_areas": source.focus_areas,
    }


@router.get("/tafsir/sources/recommended")
async def get_recommended_tafsir_sources(
    study_goal: str = Query(..., description="memorization, comprehension, research, or reflection"),
    language: Optional[str] = Query(None, description="Preferred language: ar, en, fr, ur"),
    themes: Optional[List[str]] = Query(None, description="Themes of interest"),
    limit: int = Query(5, ge=1, le=10),
):
    """
    Get recommended Tafsir sources based on study goals.

    Arabic: الحصول على مصادر التفسير الموصى بها حسب أهداف الدراسة
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirLanguage

    lang_enum = None
    if language:
        lang_map = {"ar": TafsirLanguage.ARABIC, "en": TafsirLanguage.ENGLISH,
                    "fr": TafsirLanguage.FRENCH, "ur": TafsirLanguage.URDU}
        lang_enum = lang_map.get(language.lower())

    recommendations = await modern_tafsir_service.get_recommended_sources(
        study_goal=study_goal,
        language_preference=lang_enum,
        themes_of_interest=themes,
        limit=limit,
    )

    return {
        "recommendations": recommendations,
        "study_goal": study_goal,
        "count": len(recommendations),
    }


@router.get("/tafsir/themes")
async def get_tafsir_thematic_categories():
    """
    Get thematic categories for Tafsir study.

    Arabic: الحصول على التصنيفات الموضوعية للتفسير
    """
    from app.services.tafsir_sources import modern_tafsir_service

    categories = modern_tafsir_service.get_thematic_categories()

    return {
        "categories": [
            {
                "id": cat_id,
                "name_ar": cat_data["ar"],
                "name_en": cat_data["en"],
                "description_ar": cat_data["description_ar"],
                "description_en": cat_data["description_en"],
                "recommended_sources": cat_data["recommended_sources"],
            }
            for cat_id, cat_data in categories.items()
        ],
        "count": len(categories),
    }


@router.get("/tafsir/themes/{theme}/sources")
async def get_sources_for_theme(
    theme: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get recommended Tafsir sources for a specific thematic category.

    Arabic: الحصول على مصادر التفسير الموصى بها لموضوع معين
    """
    from app.services.tafsir_sources import modern_tafsir_service

    sources = await modern_tafsir_service.get_sources_by_theme(theme, session)

    if not sources:
        raise HTTPException(status_code=404, detail=f"Theme '{theme}' not found")

    return {
        "theme": theme,
        "sources": [
            {
                "id": s.id,
                "name_ar": s.name_ar,
                "name_en": s.name_en,
                "author_en": s.author_en,
                "methodology": s.methodology.value,
                "description_en": s.description_en,
            }
            for s in sources
        ],
        "count": len(sources),
    }


@router.get("/tafsir/multilingual/{sura_no}/{aya_no}")
async def get_multilingual_tafsir(
    sura_no: int,
    aya_no: int,
    languages: List[str] = Query(["ar", "en"], description="Languages: ar, en, fr, ur, id"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get Tafsir in multiple languages for a verse.

    Arabic: الحصول على التفسير بلغات متعددة
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirLanguage

    lang_map = {
        "ar": TafsirLanguage.ARABIC,
        "en": TafsirLanguage.ENGLISH,
        "fr": TafsirLanguage.FRENCH,
        "ur": TafsirLanguage.URDU,
        "id": TafsirLanguage.INDONESIAN,
    }

    lang_enums = [lang_map[l] for l in languages if l in lang_map]

    results = await modern_tafsir_service.get_multilingual_tafsir(
        sura_no=sura_no,
        aya_no=aya_no,
        languages=lang_enums,
        session=session,
    )

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "tafsir_by_language": results,
        "languages_requested": languages,
    }


@router.get("/tafsir/methodologies")
async def get_tafsir_methodologies():
    """
    Get information about different Tafsir methodologies.

    Arabic: الحصول على معلومات عن مناهج التفسير المختلفة
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirMethodology

    methodologies = []
    for method in TafsirMethodology:
        info = modern_tafsir_service.get_methodology_info(method)
        if info:
            methodologies.append({
                "id": method.value,
                "name_ar": info["ar"],
                "name_en": info["en"],
                "description_ar": info["description_ar"],
                "description_en": info["description_en"],
            })

    return {
        "methodologies": methodologies,
        "count": len(methodologies),
    }


@router.get("/tafsir/eras")
async def get_tafsir_eras():
    """
    Get information about different Tafsir eras.

    Arabic: الحصول على معلومات عن العصور المختلفة للتفسير
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirEra

    eras = []
    for era in TafsirEra:
        info = modern_tafsir_service.get_era_info(era)
        if info:
            eras.append({
                "id": era.value,
                "name_ar": info["ar"],
                "name_en": info["en"],
                "period_ar": info["period_ar"],
                "period_en": info["period_en"],
                "description_ar": info["description_ar"],
                "description_en": info["description_en"],
            })

    return {
        "eras": eras,
        "count": len(eras),
    }


@router.get("/tafsir/compare/detailed/{sura_no}/{aya_no}")
async def compare_tafsir_detailed(
    sura_no: int,
    aya_no: int,
    source_ids: List[str] = Query(["ibn_kathir", "fi_zilal", "saadi"], description="Sources to compare"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Detailed comparison of Tafsir interpretations from multiple sources.

    Arabic: مقارنة مفصلة بين تفسيرات مختلفة
    """
    from app.services.tafsir_sources import modern_tafsir_service

    comparison = await modern_tafsir_service.compare_interpretations(
        sura_no=sura_no,
        aya_no=aya_no,
        source_ids=source_ids,
        session=session,
    )

    return {
        "verse_reference": comparison.verse_reference,
        "verse_text_ar": comparison.verse_text_ar,
        "interpretations": comparison.interpretations,
        "common_themes": comparison.common_themes,
        "sources_compared": len(comparison.interpretations),
    }


# =============================================================================
# CROSS-STORY THEMATIC CONNECTIONS
# =============================================================================


@router.get("/cross-story/themes")
async def get_all_cross_story_themes():
    """
    Get all cross-story themes for exploring connections across prophet narratives.

    Arabic: الحصول على جميع المواضيع المشتركة عبر قصص الأنبياء
    """
    from app.services.cross_story_themes import cross_story_service

    themes = cross_story_service.get_all_themes()
    return {
        "themes": themes,
        "count": len(themes),
    }


@router.get("/cross-story/themes/{theme_id}")
async def get_cross_story_theme_details(theme_id: str):
    """
    Get detailed information about a specific cross-story theme.

    Arabic: الحصول على تفاصيل موضوع معين عبر القصص
    """
    from app.services.cross_story_themes import cross_story_service

    details = cross_story_service.get_theme_details(theme_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")

    return details


@router.get("/cross-story/prophet/{prophet_name}/themes")
async def get_prophet_theme_profile(prophet_name: str):
    """
    Get all themes associated with a specific prophet.

    Arabic: الحصول على جميع المواضيع المرتبطة بنبي معين
    """
    from app.services.cross_story_themes import cross_story_service

    profile = cross_story_service.get_prophet_themes(prophet_name)

    return {
        "prophet_name": profile.prophet_name,
        "themes": profile.themes,
        "key_suras": profile.key_suras,
        "total_theme_coverage": profile.total_theme_coverage,
        "primary_narrative_aspects": profile.primary_narrative_aspects,
        "theme_count": len(profile.themes),
    }


@router.get("/cross-story/shared-themes")
async def find_shared_themes_between_prophets(
    prophets: List[str] = Query(..., description="Prophet names in Arabic"),
    min_relevance: float = Query(0.5, ge=0.0, le=1.0),
):
    """
    Find themes shared between multiple prophets.

    Arabic: إيجاد المواضيع المشتركة بين عدة أنبياء
    """
    from app.services.cross_story_themes import cross_story_service

    connections = cross_story_service.find_shared_themes(prophets, min_relevance)

    return {
        "prophets_compared": prophets,
        "shared_themes": [
            {
                "theme_id": c.theme_id,
                "theme_ar": c.theme_ar,
                "theme_en": c.theme_en,
                "category": c.category.value,
                "prophets_involved": c.prophets_involved,
                "connection_strength": c.connection_strength.value,
                "shared_verses": c.shared_verses,
                "moral_lessons_ar": c.moral_lessons_ar,
                "moral_lessons_en": c.moral_lessons_en,
            }
            for c in connections
        ],
        "count": len(connections),
    }


@router.get("/cross-story/visualization")
async def get_cross_story_visualization(
    prophets: Optional[List[str]] = Query(None, description="Filter by prophets"),
    themes: Optional[List[str]] = Query(None, description="Filter by themes"),
):
    """
    Get visualization data for interactive cross-story exploration.

    Returns nodes (prophets and themes) and edges (connections) for graph visualization.

    Arabic: الحصول على بيانات التصور للاستكشاف التفاعلي عبر القصص
    """
    from app.services.cross_story_themes import cross_story_service

    viz_data = cross_story_service.get_visualization_data(
        focus_prophets=prophets,
        focus_themes=themes,
    )

    return {
        "nodes": viz_data.nodes,
        "edges": viz_data.edges,
        "clusters": viz_data.clusters,
        "statistics": viz_data.statistics,
    }


@router.get("/cross-story/sura/{sura_no}/connections")
async def get_sura_thematic_connections(
    sura_no: int,
    theme: Optional[str] = Query(None, description="Filter by specific theme"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find thematic connections from a sura to other suras.

    Arabic: إيجاد الروابط الموضوعية من سورة إلى سور أخرى
    """
    from app.services.cross_story_themes import cross_story_service

    connections = await cross_story_service.get_cross_sura_connections(
        sura_no=sura_no,
        theme_filter=theme,
        session=session,
    )

    # Group by target sura
    grouped = {}
    for conn in connections:
        target = conn["target_sura"]
        if target not in grouped:
            grouped[target] = {
                "target_sura": target,
                "themes": [],
            }
        grouped[target]["themes"].append({
            "theme_id": conn["theme_id"],
            "theme_ar": conn["theme_ar"],
            "theme_en": conn["theme_en"],
            "prophet": conn["prophet"],
            "key_verses": conn["key_verses"],
        })

    return {
        "source_sura": sura_no,
        "connected_suras": list(grouped.values()),
        "total_connections": len(connections),
        "unique_suras": len(grouped),
    }


@router.get("/cross-story/theme-journey/{start_theme}")
async def get_theme_learning_journey(
    start_theme: str,
    max_steps: int = Query(5, ge=1, le=10),
):
    """
    Generate a learning journey starting from a theme.

    Creates a sequence of related themes for structured learning.

    Arabic: إنشاء رحلة تعلم بدءاً من موضوع معين
    """
    from app.services.cross_story_themes import cross_story_service

    journey = cross_story_service.get_theme_journey(start_theme, max_steps)

    if not journey:
        raise HTTPException(status_code=404, detail=f"Theme '{start_theme}' not found")

    return {
        "start_theme": start_theme,
        "journey": journey,
        "total_steps": len(journey),
    }


@router.get("/cross-story/search")
async def search_cross_story_themes(
    keyword: str = Query(..., min_length=2),
    language: str = Query("en", description="en or ar"),
):
    """
    Search cross-story themes by keyword.

    Arabic: البحث في المواضيع المشتركة بكلمة مفتاحية
    """
    from app.services.cross_story_themes import cross_story_service

    results = cross_story_service.search_themes_by_keyword(keyword, language)

    return {
        "keyword": keyword,
        "language": language,
        "results": results,
        "count": len(results),
    }


@router.get("/cross-story/categories/{category}")
async def get_themes_by_category(
    category: str,
):
    """
    Get all themes in a specific category.

    Arabic: الحصول على جميع المواضيع في فئة معينة
    """
    from app.services.cross_story_themes import cross_story_service, ThemeCategory

    category_map = {
        "trials": ThemeCategory.TRIALS,
        "divine_intervention": ThemeCategory.DIVINE_INTERVENTION,
        "community_response": ThemeCategory.COMMUNITY_RESPONSE,
        "moral_lesson": ThemeCategory.MORAL_LESSON,
        "divine_attribute": ThemeCategory.DIVINE_ATTRIBUTE,
        "human_quality": ThemeCategory.HUMAN_QUALITY,
        "outcome": ThemeCategory.OUTCOME,
    }

    cat_enum = category_map.get(category.lower())
    if not cat_enum:
        raise HTTPException(status_code=400, detail=f"Invalid category. Valid: {list(category_map.keys())}")

    themes = cross_story_service.get_category_themes(cat_enum)

    return {
        "category": category,
        "themes": themes,
        "count": len(themes),
    }


# =============================================================================
# CROSS-SURA SIMILARITY SCORING
# =============================================================================


@router.get("/similarity/cross-sura/{sura_no}")
async def get_cross_sura_similarity(
    sura_no: int,
    themes: Optional[List[str]] = Query(None, description="Filter by themes"),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Find similar suras based on thematic content.

    Arabic: إيجاد السور المتشابهة موضوعياً
    """
    from app.services.cross_story_themes import cross_story_service

    # Get all connections from this sura
    connections = await cross_story_service.get_cross_sura_connections(sura_no, session=session)

    # Calculate similarity scores
    sura_scores = {}
    for conn in connections:
        target = conn["target_sura"]
        if target not in sura_scores:
            sura_scores[target] = {
                "sura_no": target,
                "themes": set(),
                "prophets": set(),
                "total_score": 0,
            }
        sura_scores[target]["themes"].add(conn["theme_id"])
        sura_scores[target]["prophets"].add(conn["prophet"])
        sura_scores[target]["total_score"] += 0.1  # Base score per connection

    # Normalize and filter
    max_score = max((s["total_score"] for s in sura_scores.values()), default=1)
    results = []
    for sura_data in sura_scores.values():
        normalized_score = sura_data["total_score"] / max_score if max_score > 0 else 0
        if normalized_score >= min_score:
            # Filter by themes if specified
            if themes and not sura_data["themes"].intersection(set(themes)):
                continue

            results.append({
                "sura_no": sura_data["sura_no"],
                "similarity_score": round(normalized_score, 3),
                "shared_themes": list(sura_data["themes"]),
                "shared_prophets": list(sura_data["prophets"]),
                "theme_count": len(sura_data["themes"]),
            })

    # Sort by score
    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "source_sura": sura_no,
        "similar_suras": results[:limit],
        "count": len(results[:limit]),
        "total_matches": len(results),
    }


@router.get("/similarity/thematic-search")
async def thematic_verse_search(
    theme: str = Query(..., description="Theme to search for"),
    prophets: Optional[List[str]] = Query(None, description="Filter by prophets"),
    min_relevance: float = Query(0.5, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search for verses by thematic content across all suras.

    Arabic: البحث عن الآيات حسب المحتوى الموضوعي
    """
    from app.services.cross_story_themes import cross_story_service
    from app.models.quran import QuranVerse

    # Get theme details
    theme_details = cross_story_service.get_theme_details(theme)
    if not theme_details:
        raise HTTPException(status_code=404, detail=f"Theme '{theme}' not found")

    # Collect all relevant verses
    verses_info = []
    for prophet_data in theme_details["prophets"]:
        prophet_name = prophet_data["name"]

        # Filter by prophets if specified
        if prophets and prophet_name not in prophets:
            continue

        if prophet_data["relevance"] < min_relevance:
            continue

        for verse_ref in prophet_data["key_verses"]:
            try:
                parts = verse_ref.split(":")
                s_no, a_no = int(parts[0]), int(parts[1].split("-")[0])

                # Get verse text
                result = await session.execute(
                    select(QuranVerse).where(
                        QuranVerse.sura_no == s_no,
                        QuranVerse.aya_no == a_no,
                    )
                )
                verse = result.scalar_one_or_none()

                if verse:
                    verses_info.append({
                        "verse_reference": verse_ref,
                        "sura_no": s_no,
                        "aya_no": a_no,
                        "text_uthmani": verse.text_uthmani,
                        "prophet": prophet_name,
                        "aspect": prophet_data["aspect"],
                        "relevance": prophet_data["relevance"],
                    })
            except (ValueError, IndexError):
                continue

    # Sort by relevance
    verses_info.sort(key=lambda x: x["relevance"], reverse=True)

    return {
        "theme_id": theme,
        "theme_ar": theme_details["name_ar"],
        "theme_en": theme_details["name_en"],
        "category": theme_details["category"],
        "moral_lessons": theme_details["moral_lessons"],
        "verses": verses_info,
        "count": len(verses_info),
    }


# =============================================================================
# ENHANCED TAFSIR SEARCH
# =============================================================================


@router.get("/tafsir/scholar/{scholar_id}/search")
async def search_tafsir_by_scholar(
    scholar_id: str,
    keyword: Optional[str] = Query(None, description="Search keyword"),
    sura_no: Optional[int] = Query(None, description="Filter by sura"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search Tafsir content by a specific scholar.

    Arabic: البحث في تفسير عالم معين
    """
    from app.services.tafsir_sources import modern_tafsir_service

    results = await modern_tafsir_service.search_tafsir_by_scholar(
        scholar_id=scholar_id,
        keyword=keyword,
        sura_no=sura_no,
        limit=limit,
        session=session,
    )

    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])

    return results


@router.get("/tafsir/scholar/{scholar_id}/profile")
async def get_scholar_profile(scholar_id: str):
    """
    Get comprehensive profile of a Tafsir scholar.

    Arabic: الحصول على ملف شامل لمفسر
    """
    from app.services.tafsir_sources import modern_tafsir_service

    profile = modern_tafsir_service.get_scholar_profile(scholar_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Scholar '{scholar_id}' not found")

    return profile


@router.get("/tafsir/scholars/by-focus/{focus_area}")
async def get_scholars_by_focus(focus_area: str):
    """
    Get scholars specializing in a specific focus area.

    Focus areas include: fiqh, spiritual_guidance, linguistic_analysis,
    hadith_based, social_reform, word_analysis, etc.

    Arabic: الحصول على العلماء المتخصصين في مجال معين
    """
    from app.services.tafsir_sources import modern_tafsir_service

    scholars = modern_tafsir_service.get_scholars_by_focus(focus_area)

    return {
        "focus_area": focus_area,
        "scholars": scholars,
        "count": len(scholars),
    }


@router.get("/tafsir/for-study-goal/{sura_no}/{aya_no}")
async def get_tafsir_for_study_goal(
    sura_no: int,
    aya_no: int,
    study_goal: str = Query(..., description="memorization, comprehension, research, or reflection"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get Tafsir content tailored to a specific study goal.

    Returns the most appropriate Tafsir sources for your learning objective.

    Arabic: الحصول على التفسير المناسب لهدف الدراسة
    """
    from app.services.tafsir_sources import modern_tafsir_service

    results = await modern_tafsir_service.get_tafsir_for_study_goal(
        sura_no=sura_no,
        aya_no=aya_no,
        study_goal=study_goal,
        session=session,
    )

    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])

    return results


@router.get("/tafsir/highlights/{sura_no}/{aya_no}")
async def get_tafsir_interpretation_highlights(
    sura_no: int,
    aya_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get key highlights and differences from multiple Tafsir interpretations.

    Shows how different scholars approach the same verse, grouped by
    methodology and era.

    Arabic: الحصول على أبرز النقاط والاختلافات بين التفاسير
    """
    from app.services.tafsir_sources import modern_tafsir_service

    results = await modern_tafsir_service.get_interpretation_highlights(
        sura_no=sura_no,
        aya_no=aya_no,
        session=session,
    )

    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])

    return results


@router.get("/tafsir/all-scholars")
async def get_all_tafsir_scholars():
    """
    Get list of all available Tafsir scholars/sources.

    Arabic: الحصول على قائمة بجميع المفسرين المتاحين
    """
    from app.services.tafsir_sources import modern_tafsir_service

    sources = await modern_tafsir_service.get_all_sources()

    # Group by era
    by_era = {"classical": [], "modern": [], "contemporary": []}
    for s in sources:
        era = s.era.value
        by_era[era].append({
            "id": s.id,
            "name_ar": s.name_ar,
            "name_en": s.name_en,
            "author_en": s.author_en,
            "methodology": s.methodology.value,
        })

    return {
        "total_scholars": len(sources),
        "by_era": by_era,
        "classical_count": len(by_era["classical"]),
        "modern_count": len(by_era["modern"]),
        "contemporary_count": len(by_era["contemporary"]),
    }


# =============================================================================
# AI-BASED PERSONALIZATION
# =============================================================================


@router.get("/personalization/adaptive-recommendations")
async def get_adaptive_recommendations(
    session_id: str = Query(..., description="User session ID"),
    context: str = Query("general", description="Context: general, memorization, research, reflection"),
    limit: int = Query(10, ge=1, le=30),
):
    """
    Get AI-powered adaptive recommendations based on user behavior.

    Analyzes search history, feedback, and study patterns to provide
    personalized suggestions.

    Arabic: الحصول على توصيات متكيفة بناءً على سلوك المستخدم
    """
    from app.services.search_history import search_history_service
    from app.services.recommendation_engine import recommendation_engine

    # Get user's history and interests
    theme_interests = await search_history_service.get_theme_interests(session_id)
    study_goal = await search_history_service.get_study_goal(session_id)
    weight_adjustments = await search_history_service.get_personalized_weight_adjustments(session_id)

    # Get recommendations based on context
    if context == "memorization":
        # Recommend verses due for review
        from app.services.study_progress import study_progress_service
        due_verses = await study_progress_service.get_verses_due_for_review(session_id, limit)
        recommendations = {
            "type": "memorization_review",
            "items": [
                {
                    "verse_reference": v.verse_reference,
                    "confidence_level": v.confidence_level,
                    "priority": "high" if v.confidence_level < 3 else "normal",
                }
                for v in due_verses
            ],
        }
    else:
        # Theme-based recommendations
        themes_explored = list(theme_interests.keys())
        theme_recs = await recommendation_engine.get_theme_recommendations(
            user_themes_explored=themes_explored,
            user_prophets_studied=[],
            study_goal=study_goal.get("goal_type", "comprehension") if study_goal else "comprehension",
            limit=limit,
        )
        recommendations = {
            "type": "thematic_exploration",
            "items": [
                {
                    "theme_id": r.theme_id,
                    "theme_name_ar": r.theme_name_ar,
                    "theme_name_en": r.theme_name_en,
                    "relevance_score": round(r.relevance_score, 3),
                    "reason": r.reason,
                }
                for r in theme_recs
            ],
        }

    return {
        "session_id": session_id,
        "context": context,
        "user_profile": {
            "themes_explored": len(theme_interests),
            "top_themes": list(theme_interests.keys())[:5],
            "study_goal": study_goal.get("goal_type") if study_goal else None,
            "personalization_level": "high" if len(theme_interests) > 5 else "medium" if theme_interests else "low",
        },
        "weight_adjustments": weight_adjustments,
        "recommendations": recommendations,
    }


@router.post("/personalization/learn-from-interaction")
async def learn_from_user_interaction(
    session_id: str = Query(..., description="User session ID"),
    interaction_type: str = Query(..., description="view, search, bookmark, feedback"),
    target_type: str = Query(..., description="verse, theme, prophet, tafsir"),
    target_id: str = Query(..., description="ID of the target item"),
    value: Optional[float] = Query(None, description="Interaction value (e.g., rating)"),
):
    """
    Record user interaction for AI learning.

    Used to improve future recommendations based on user behavior.

    Arabic: تسجيل تفاعل المستخدم للتعلم الذكي
    """
    from app.services.search_history import search_history_service

    # Record the interaction
    interaction = {
        "session_id": session_id,
        "interaction_type": interaction_type,
        "target_type": target_type,
        "target_id": target_id,
        "value": value,
    }

    # Update theme interests if relevant
    if target_type == "theme":
        await search_history_service.update_theme_interest(
            session_id=session_id,
            theme=target_id,
            weight=value or 1.0,
        )

    return {
        "status": "recorded",
        "interaction": interaction,
        "message": "Interaction recorded for personalization",
    }


@router.get("/personalization/learning-insights")
async def get_learning_insights(
    session_id: str = Query(..., description="User session ID"),
):
    """
    Get insights about user's learning patterns.

    Arabic: الحصول على رؤى حول أنماط تعلم المستخدم
    """
    from app.services.search_history import search_history_service
    from app.services.study_progress import study_progress_service

    # Get various user data
    theme_interests = await search_history_service.get_theme_interests(session_id)
    study_goal = await search_history_service.get_study_goal(session_id)
    feedback_learning = await search_history_service.learn_from_feedback()

    # Get study progress
    overall_progress = await study_progress_service.get_overall_progress(session_id)
    daily_stats = await study_progress_service.get_daily_stats(session_id, days=7)

    # Analyze patterns
    theme_focus = sorted(theme_interests.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "session_id": session_id,
        "learning_profile": {
            "primary_study_goal": study_goal.get("goal_type") if study_goal else "exploration",
            "focus_themes": [t[0] for t in theme_focus],
            "engagement_level": "high" if len(theme_interests) > 10 else "medium" if len(theme_interests) > 3 else "developing",
        },
        "progress_summary": overall_progress,
        "weekly_activity": daily_stats,
        "ai_insights": {
            "recommendation_quality": feedback_learning.get("relevance_rate", 0),
            "suggested_adjustment": feedback_learning.get("recommendation", "continue_current"),
        },
        "suggestions": {
            "ar": "استمر في استكشاف المواضيع ذات الصلة بأهدافك",
            "en": "Continue exploring themes related to your goals",
        },
    }


# =============================================================================
# ADVANCED SEARCH WITH QUERY EXPANSION
# =============================================================================


@router.get("/search/advanced")
async def advanced_search_with_expansion(
    query: str = Query(..., min_length=2, description="Search query in Arabic or English"),
    include_explanation: bool = Query(True, description="Include score explanations"),
    theme_filter: Optional[str] = Query(None, description="Filter by theme"),
    prophet_filter: Optional[str] = Query(None, description="Filter by prophet (Arabic name)"),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Advanced search with automatic query expansion and score transparency.

    Features:
    - Automatic expansion of search terms with related concepts
    - Root-based Arabic morphological search
    - Thematic connection discovery
    - Detailed score breakdown explaining why results matched

    Arabic: البحث المتقدم مع توسيع الاستعلام وشفافية النتائج
    """
    from app.services.advanced_search import advanced_search_service

    results = await advanced_search_service.search_with_expansion(
        query=query,
        session=session,
        limit=limit,
        include_explanation=include_explanation,
        theme_filter=theme_filter,
        prophet_filter=prophet_filter,
    )

    return results


@router.get("/search/expand-query")
async def expand_search_query(
    query: str = Query(..., min_length=2),
):
    """
    Preview how a query would be expanded without executing search.

    Shows detected themes, roots, and expanded Arabic terms.

    Arabic: معاينة كيفية توسيع الاستعلام
    """
    from app.services.advanced_search import advanced_search_service

    expanded = advanced_search_service.expand_query(query)

    return {
        "original_query": expanded.original_query,
        "expanded_terms_ar": expanded.expanded_terms_ar,
        "expanded_terms_en": expanded.expanded_terms_en,
        "detected_themes": expanded.detected_themes,
        "detected_roots": expanded.detected_roots,
        "expansion_strategy": expanded.expansion_strategy,
        "total_expanded_terms": len(expanded.expanded_terms_ar),
    }


@router.get("/search/cross-story")
async def cross_story_thematic_search(
    theme: str = Query(..., description="Theme to search (e.g., patience, mercy, trust)"),
    prophets: Optional[List[str]] = Query(None, description="Filter by prophets (Arabic names)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search across prophet stories for a specific theme.

    Finds how the same theme appears in different prophetic narratives.

    Arabic: البحث عبر قصص الأنبياء لموضوع معين
    """
    from app.services.advanced_search import advanced_search_service

    results = await advanced_search_service.cross_story_search(
        theme=theme,
        prophets=prophets,
        session=session,
    )

    return results


@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
):
    """
    Get search suggestions based on partial query.

    Arabic: الحصول على اقتراحات البحث
    """
    from app.services.advanced_search import advanced_search_service

    suggestions = await advanced_search_service.get_search_suggestions(query, limit)

    return {
        "query": query,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@router.get("/search/themes")
async def get_available_search_themes():
    """
    Get list of available themes for thematic search.

    Arabic: الحصول على قائمة المواضيع المتاحة للبحث
    """
    from app.services.advanced_search import advanced_search_service

    themes = advanced_search_service.get_available_themes()

    # Group by category
    categorized = {
        "divine_attributes": [],
        "human_qualities": [],
        "trials_tests": [],
        "consequences": [],
        "narratives": [],
        "social": [],
    }

    category_mapping = {
        "mercy": "divine_attributes",
        "justice": "divine_attributes",
        "power": "divine_attributes",
        "wisdom": "divine_attributes",
        "forgiveness": "divine_attributes",
        "patience": "human_qualities",
        "gratitude": "human_qualities",
        "trust": "human_qualities",
        "faith": "human_qualities",
        "repentance": "human_qualities",
        "fear": "human_qualities",
        "hope": "human_qualities",
        "love": "human_qualities",
        "trial": "trials_tests",
        "adversity": "trials_tests",
        "hardship": "trials_tests",
        "punishment": "consequences",
        "reward": "consequences",
        "paradise": "consequences",
        "hellfire": "consequences",
        "prophet": "narratives",
        "story": "narratives",
        "miracle": "narratives",
        "guidance": "narratives",
        "family": "social",
        "community": "social",
        "oppression": "social",
        "covenant": "social",
    }

    for theme in themes:
        cat = category_mapping.get(theme["theme_id"], "other")
        if cat in categorized:
            categorized[cat].append(theme)

    return {
        "themes": themes,
        "categorized": categorized,
        "total_count": len(themes),
    }


@router.get("/search/roots")
async def get_available_arabic_roots():
    """
    Get list of available Arabic roots for root-based search.

    Arabic: الحصول على قائمة الجذور العربية المتاحة للبحث
    """
    from app.services.advanced_search import advanced_search_service

    roots = advanced_search_service.get_available_roots()

    return {
        "roots": roots,
        "count": len(roots),
    }


# =============================================================================
# ENHANCED TAFSIR COMPARISON WITH EVOLUTION
# =============================================================================


@router.get("/tafsir/evolution/{sura_no}/{aya_no}")
async def get_tafsir_historical_evolution(
    sura_no: int,
    aya_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get historical evolution of Tafsir interpretations for a verse.

    Shows how understanding of the verse evolved from classical to modern scholars.

    Arabic: الحصول على التطور التاريخي لتفسيرات الآية
    """
    from app.services.tafsir_sources import modern_tafsir_service, TafsirEra
    from app.models.quran import QuranVerse
    from app.models.tafseer import TafseerChunk, TafseerSource

    # Get verse
    verse_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no
        )
    )
    verse = verse_result.scalar_one_or_none()
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    # Get all Tafsir chunks
    chunks_result = await session.execute(
        select(TafseerChunk, TafseerSource).join(
            TafseerSource, TafseerChunk.source_id == TafseerSource.id
        ).where(
            TafseerChunk.verse_start_id <= verse.id,
            TafseerChunk.verse_end_id >= verse.id,
        )
    )

    # Organize by era
    evolution = {
        "classical": {
            "era_ar": "التفاسير الكلاسيكية",
            "era_en": "Classical Tafsirs",
            "period": "Before 1900 CE",
            "interpretations": [],
        },
        "modern": {
            "era_ar": "التفاسير الحديثة",
            "era_en": "Modern Tafsirs",
            "period": "1900-2000 CE",
            "interpretations": [],
        },
        "contemporary": {
            "era_ar": "التفاسير المعاصرة",
            "era_en": "Contemporary Tafsirs",
            "period": "2000 CE onwards",
            "interpretations": [],
        },
    }

    catalog = modern_tafsir_service._catalog

    for chunk, source in chunks_result.all():
        base_id = source.id.replace("_ar", "").replace("_en", "")
        source_info = catalog.get(base_id, {})

        era = source.era or "classical"
        if era not in evolution:
            era = "classical"

        interpretation = {
            "source_id": base_id,
            "source_name_ar": source_info.get("name_ar", source.name_ar),
            "source_name_en": source_info.get("name_en", source.name_en),
            "author_en": source_info.get("author_en", source.author_en),
            "death_year": source_info.get("death_year_ce"),
            "methodology": source_info.get("methodology", "comprehensive"),
            "content_ar": chunk.content_ar,
            "content_en": chunk.content_en,
            "focus_areas": source_info.get("focus_areas", []),
        }

        evolution[era]["interpretations"].append(interpretation)

    # Sort by death year within each era
    for era_data in evolution.values():
        era_data["interpretations"].sort(
            key=lambda x: x.get("death_year") or 9999
        )

    # Analysis insights
    total_sources = sum(len(e["interpretations"]) for e in evolution.values())

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "verse_text": verse.text_uthmani,
        "evolution": evolution,
        "total_sources": total_sources,
        "insights": {
            "classical_focus": "Hadith-based interpretation and linguistic analysis",
            "modern_evolution": "Integration of contemporary context and social application",
            "trend_ar": "تطور من التفسير بالمأثور إلى التطبيق المعاصر",
            "trend_en": "Evolution from narration-based to contemporary application",
        },
    }


@router.get("/tafsir/side-by-side/{sura_no}/{aya_no}")
async def get_side_by_side_tafsir(
    sura_no: int,
    aya_no: int,
    source_ids: List[str] = Query(
        ["ibn_kathir", "fi_zilal"],
        description="Two or more sources to compare"
    ),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get side-by-side Tafsir comparison for detailed analysis.

    Highlights differences in approach and interpretation between scholars.

    Arabic: مقارنة التفاسير جنباً إلى جنب
    """
    from app.services.tafsir_sources import modern_tafsir_service
    from app.models.quran import QuranVerse
    from app.models.tafseer import TafseerChunk

    # Get verse
    verse_result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no
        )
    )
    verse = verse_result.scalar_one_or_none()
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")

    catalog = modern_tafsir_service._catalog
    comparisons = []

    for source_id in source_ids:
        source_info = catalog.get(source_id, {})

        # Try to find chunk
        chunk = None
        for sid in [source_id, f"{source_id}_ar", f"{source_id}_en"]:
            chunk_result = await session.execute(
                select(TafseerChunk).where(
                    TafseerChunk.source_id == sid,
                    TafseerChunk.verse_start_id <= verse.id,
                    TafseerChunk.verse_end_id >= verse.id,
                )
            )
            chunk = chunk_result.scalar_one_or_none()
            if chunk:
                break

        comparisons.append({
            "source_id": source_id,
            "source_name_ar": source_info.get("name_ar", source_id),
            "source_name_en": source_info.get("name_en", source_id),
            "author_en": source_info.get("author_en", ""),
            "era": source_info.get("era", "classical").value if hasattr(source_info.get("era"), "value") else str(source_info.get("era", "classical")),
            "methodology": source_info.get("methodology", "comprehensive").value if hasattr(source_info.get("methodology"), "value") else str(source_info.get("methodology", "comprehensive")),
            "methodology_description": modern_tafsir_service.get_methodology_info(source_info.get("methodology")) if source_info.get("methodology") else {},
            "strengths": source_info.get("strengths", []),
            "content_ar": chunk.content_ar if chunk else None,
            "content_en": chunk.content_en if chunk else None,
            "available": chunk is not None,
        })

    # Generate comparison insights
    methodologies = [c["methodology"] for c in comparisons if c["available"]]
    unique_methodologies = list(set(methodologies))

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "verse_text": verse.text_uthmani,
        "comparisons": comparisons,
        "sources_requested": len(source_ids),
        "sources_available": sum(1 for c in comparisons if c["available"]),
        "comparison_insights": {
            "methodology_diversity": len(unique_methodologies),
            "methodologies_present": unique_methodologies,
            "suggestion_ar": "قارن بين المنهج اللغوي والمنهج المأثور لفهم أعمق",
            "suggestion_en": "Compare linguistic and narration-based approaches for deeper understanding",
        },
    }


# =============================================================================
# USER FEEDBACK LOOP
# =============================================================================


@router.post("/feedback/search-result")
async def submit_search_result_feedback(
    session_id: str = Query(...),
    search_query: str = Query(...),
    verse_reference: str = Query(...),
    relevance_rating: int = Query(..., ge=1, le=5, description="1=not relevant, 5=very relevant"),
    feedback_type: str = Query("relevance", description="relevance, helpful, accurate"),
    comment: Optional[str] = Query(None),
):
    """
    Submit feedback on a search result to improve future recommendations.

    Arabic: تقديم ملاحظات على نتيجة البحث لتحسين التوصيات المستقبلية
    """
    from app.services.search_history import search_history_service

    # Record feedback
    feedback = await search_history_service.record_feedback(
        session_id=session_id,
        query=search_query,
        verse_ref=verse_reference,
        relevance=relevance_rating >= 4,  # 4-5 is relevant
        feedback_type=feedback_type,
    )

    # Learn from feedback
    learning = await search_history_service.learn_from_feedback()

    return {
        "status": "recorded",
        "feedback": {
            "search_query": search_query,
            "verse_reference": verse_reference,
            "relevance_rating": relevance_rating,
            "feedback_type": feedback_type,
        },
        "learning_status": learning.get("status", "pending"),
        "message_ar": "شكراً لملاحظاتك، ستساعد في تحسين نتائج البحث",
        "message_en": "Thank you for your feedback, it will help improve search results",
    }


@router.post("/feedback/tafsir")
async def submit_tafsir_feedback(
    session_id: str = Query(...),
    verse_reference: str = Query(...),
    source_id: str = Query(...),
    helpfulness_rating: int = Query(..., ge=1, le=5),
    clarity_rating: int = Query(..., ge=1, le=5),
    comment: Optional[str] = Query(None),
):
    """
    Submit feedback on a Tafsir interpretation.

    Arabic: تقديم ملاحظات على تفسير معين
    """
    return {
        "status": "recorded",
        "feedback": {
            "verse_reference": verse_reference,
            "source_id": source_id,
            "helpfulness_rating": helpfulness_rating,
            "clarity_rating": clarity_rating,
        },
        "message_ar": "شكراً لملاحظاتك على التفسير",
        "message_en": "Thank you for your feedback on this Tafsir",
    }


@router.get("/feedback/summary")
async def get_feedback_summary(
    session_id: str = Query(...),
):
    """
    Get summary of user's feedback contributions.

    Arabic: ملخص مساهمات المستخدم بالملاحظات
    """
    from app.services.search_history import search_history_service

    learning = await search_history_service.learn_from_feedback()

    return {
        "session_id": session_id,
        "feedback_stats": {
            "total_feedback": learning.get("total_feedback", 0),
            "positive_feedback": learning.get("positive_feedback", 0),
            "relevance_rate": learning.get("relevance_rate", 0),
        },
        "impact": {
            "ar": "ملاحظاتك تساعد في تحسين نتائج البحث للجميع",
            "en": "Your feedback helps improve search results for everyone",
        },
        "recommendation": learning.get("recommendation", "continue_current"),
    }


# =============================================================================
# ARABIC SEMANTIC SEARCH (PHASE 5)
# =============================================================================


@router.get("/semantic/search")
async def arabic_semantic_search(
    q: str = Query(..., min_length=1, description="Search query (Arabic or English)"),
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.3, ge=0.0, le=1.0),
    include_life_lessons: bool = Query(True),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Arabic-optimized semantic search with AraBERT support.

    Supports:
    - Arabic queries with morphological understanding
    - English queries with automatic Arabic translation
    - Cross-language concept matching
    - Life lessons integration

    Arabic: البحث الدلالي المحسّن للعربية مع دعم AraBERT
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    results = await arabic_semantic_service.semantic_search(
        query=q,
        session=session,
        limit=limit,
        min_score=min_score,
        include_life_lessons=include_life_lessons,
    )

    return results


@router.get("/semantic/expand-query")
async def expand_query_cross_language(
    q: str = Query(..., min_length=1, description="Query to expand"),
):
    """
    Expand a query across Arabic and English with concept detection.

    Returns detected concepts, Arabic terms, English terms, and applicable life lessons.

    Arabic: توسيع الاستعلام عبر اللغات مع اكتشاف المفاهيم
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    expanded = arabic_semantic_service.expand_cross_language_query(q)

    return {
        "original_query": expanded.original_query,
        "source_language": expanded.source_language,
        "arabic_terms": expanded.arabic_terms,
        "english_terms": expanded.english_terms,
        "detected_concepts": expanded.detected_concepts,
        "life_lessons_applicable": expanded.life_lessons_applicable,
        "suggestion_ar": "استخدم المصطلحات العربية للحصول على نتائج أفضل",
        "suggestion_en": "Use the Arabic terms for better results",
    }


@router.get("/semantic/concepts")
async def get_semantic_concepts():
    """
    Get all available cross-language semantic concepts.

    Returns concepts with their Arabic terms, English translations, and related terms.

    Arabic: الحصول على جميع المفاهيم الدلالية المتاحة
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    concepts = arabic_semantic_service.get_concepts()

    return {
        "concepts": concepts,
        "count": len(concepts),
        "usage_ar": "استخدم هذه المفاهيم للبحث المتقدم",
        "usage_en": "Use these concepts for advanced search",
    }


@router.get("/semantic/model-info")
async def get_semantic_model_info():
    """
    Get information about the Arabic semantic search model.

    Arabic: معلومات عن نموذج البحث الدلالي العربي
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    return arabic_semantic_service.get_model_info()


# =============================================================================
# LIFE LESSONS (PHASE 5)
# =============================================================================


@router.get("/life-lessons")
async def get_life_lessons(
    situation: Optional[str] = Query(None, description="Filter by life situation"),
    concept: Optional[str] = Query(None, description="Filter by concept (e.g., patience, forgiveness)"),
):
    """
    Get Quranic life lessons with practical applications.

    Can filter by:
    - Life situation (e.g., 'loss', 'financial difficulties')
    - Concept (e.g., 'patience', 'forgiveness')

    Arabic: الحصول على الدروس الحياتية من القرآن مع تطبيقات عملية
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    lessons = arabic_semantic_service.get_life_lessons(
        situation=situation,
        concept=concept,
    )

    return {
        "lessons": lessons,
        "count": len(lessons),
        "filters_applied": {
            "situation": situation,
            "concept": concept,
        },
    }


@router.get("/life-lessons/{lesson_id}")
async def get_life_lesson_details(
    lesson_id: str,
):
    """
    Get detailed information about a specific life lesson.

    Arabic: تفاصيل درس حياتي معين
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    lesson = arabic_semantic_service.get_life_lesson_details(lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Life lesson not found",
                "ar": "لم يتم العثور على الدرس الحياتي",
            },
        )

    return lesson


@router.get("/life-lessons/{lesson_id}/verses")
async def get_life_lesson_verses(
    lesson_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verses associated with a specific life lesson.

    Arabic: الآيات المرتبطة بدرس حياتي معين
    """
    from app.services.arabic_semantic_search import arabic_semantic_service
    from app.models.quran import QuranVerse

    lesson = arabic_semantic_service.get_life_lesson_details(lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail={"error": "Life lesson not found"},
        )

    verses = []
    for verse_ref in lesson.get("key_verses", []):
        if ":" in verse_ref:
            parts = verse_ref.split(":")
            if "-" in parts[1]:
                # Range: e.g., "2:155-156"
                sura_no = int(parts[0])
                aya_range = parts[1].split("-")
                for aya_no in range(int(aya_range[0]), int(aya_range[1]) + 1):
                    result = await session.execute(
                        select(QuranVerse).where(
                            QuranVerse.sura_no == sura_no,
                            QuranVerse.aya_no == aya_no,
                        )
                    )
                    verse = result.scalar_one_or_none()
                    if verse:
                        verses.append({
                            "reference": f"{sura_no}:{aya_no}",
                            "text_uthmani": verse.text_uthmani,
                            "sura_no": verse.sura_no,
                            "aya_no": verse.aya_no,
                        })
            else:
                sura_no = int(parts[0])
                aya_no = int(parts[1])
                result = await session.execute(
                    select(QuranVerse).where(
                        QuranVerse.sura_no == sura_no,
                        QuranVerse.aya_no == aya_no,
                    )
                )
                verse = result.scalar_one_or_none()
                if verse:
                    verses.append({
                        "reference": f"{sura_no}:{aya_no}",
                        "text_uthmani": verse.text_uthmani,
                        "sura_no": verse.sura_no,
                        "aya_no": verse.aya_no,
                    })

    return {
        "lesson_id": lesson_id,
        "lesson_name_ar": lesson["name_ar"],
        "lesson_name_en": lesson["name_en"],
        "verses": verses,
        "count": len(verses),
    }


@router.get("/life-lessons/by-situation/{situation}")
async def get_lessons_by_situation(
    situation: str,
):
    """
    Get life lessons relevant to a specific life situation.

    Examples: 'loss', 'financial', 'health', 'family', 'work'

    Arabic: الدروس الحياتية المتعلقة بموقف معين
    """
    from app.services.arabic_semantic_search import arabic_semantic_service

    lessons = arabic_semantic_service.get_life_lessons(situation=situation)

    return {
        "situation": situation,
        "lessons": lessons,
        "count": len(lessons),
        "advice_ar": "كل محنة فيها منحة، والصبر مفتاح الفرج",
        "advice_en": "Every hardship contains a gift, and patience is the key to relief",
    }


# =============================================================================
# SPACED REPETITION MEMORIZATION (SM2 ALGORITHM - PHASE 5)
# =============================================================================


@router.post("/memorization/add-verses")
async def add_verses_to_memorization(
    user_id: str = Query(...),
    sura_no: int = Query(..., ge=1, le=114),
    start_aya: int = Query(..., ge=1),
    end_aya: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Add a range of verses to the user's memorization queue.

    Arabic: إضافة آيات لقائمة الحفظ
    """
    from app.services.spaced_repetition import spaced_repetition_service
    from app.models.quran import QuranVerse

    # Get verses from database
    result = await session.execute(
        select(QuranVerse).where(
            and_(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no >= start_aya,
                QuranVerse.aya_no <= end_aya,
            )
        ).order_by(QuranVerse.aya_no)
    )
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(
            status_code=404,
            detail={"error": "Verses not found"},
        )

    verse_data = [
        {
            "verse_id": v.id,
            "sura_no": v.sura_no,
            "aya_no": v.aya_no,
            "reference": f"{v.sura_no}:{v.aya_no}",
            "text_uthmani": v.text_uthmani,
            "juz_no": v.juz_no,
            "hizb_no": v.hizb_no,
        }
        for v in verses
    ]

    return await spaced_repetition_service.add_verses_to_learn(
        user_id=user_id,
        verses=verse_data,
        session=session,
    )


@router.get("/memorization/due-reviews")
async def get_due_reviews(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get verses due for review today using SM2 algorithm.

    Arabic: الآيات المستحقة للمراجعة اليوم
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.get_due_reviews(
        user_id=user_id,
        limit=limit,
    )


@router.post("/memorization/record-review")
async def record_memorization_review(
    user_id: str = Query(...),
    verse_id: int = Query(...),
    quality: int = Query(..., ge=0, le=5, description="Quality of recall: 0=blackout, 5=perfect"),
):
    """
    Record a review and calculate next interval using SM2 algorithm.

    Quality scale:
    - 0: Complete blackout - no recall
    - 1: Incorrect, but recognized when shown
    - 2: Incorrect, but easy to recall after hint
    - 3: Correct with significant difficulty
    - 4: Correct with some hesitation
    - 5: Perfect recall - no hesitation

    Arabic: تسجيل مراجعة وحساب الفاصل الزمني التالي
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.record_review(
        user_id=user_id,
        verse_id=verse_id,
        quality=quality,
    )


@router.get("/memorization/stats")
async def get_memorization_stats(
    user_id: str = Query(...),
):
    """
    Get comprehensive memorization statistics.

    Arabic: إحصائيات الحفظ الشاملة
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.get_memorization_stats(user_id=user_id)


@router.get("/memorization/quality-ratings")
async def get_quality_ratings():
    """
    Get quality rating descriptions for the SM2 algorithm.

    Arabic: وصف تقييمات جودة التذكر
    """
    from app.services.spaced_repetition import QUALITY_RATINGS

    return {
        "ratings": QUALITY_RATINGS,
        "success_threshold": 3,
        "instructions_ar": "قيّم تذكرك من 0 (نسيان تام) إلى 5 (تذكر مثالي)",
        "instructions_en": "Rate your recall from 0 (complete blackout) to 5 (perfect recall)",
    }


@router.get("/memorization/learning-path")
async def get_learning_path(
    user_id: str = Query(...),
    target_type: str = Query("juz", description="Type: 'juz' or 'hizb'"),
    target_number: int = Query(30, ge=1, description="Juz number (1-30) or Hizb number (1-60)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a structured learning path for a Juz or Hizb.

    Arabic: مسار تعلم منظم لجزء أو حزب
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.get_learning_path(
        user_id=user_id,
        target=target_type,
        target_number=target_number,
        session=session,
    )


@router.post("/memorization/suspend")
async def suspend_verse_from_reviews(
    user_id: str = Query(...),
    verse_id: int = Query(...),
):
    """
    Suspend a verse from reviews temporarily.

    Arabic: إيقاف مراجعة آية مؤقتًا
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.suspend_verse(
        user_id=user_id,
        verse_id=verse_id,
    )


@router.post("/memorization/unsuspend")
async def unsuspend_verse_for_reviews(
    user_id: str = Query(...),
    verse_id: int = Query(...),
):
    """
    Resume reviews for a suspended verse.

    Arabic: استئناف مراجعة آية موقوفة
    """
    from app.services.spaced_repetition import spaced_repetition_service

    return await spaced_repetition_service.unsuspend_verse(
        user_id=user_id,
        verse_id=verse_id,
    )


@router.get("/memorization/daily-limits")
async def get_daily_limits():
    """
    Get recommended daily review limits.

    Arabic: الحدود اليومية الموصى بها للمراجعة
    """
    from app.services.spaced_repetition import DAILY_LIMITS

    return {
        "limits": DAILY_LIMITS,
        "recommendations_ar": {
            "new_verses": "الحد الأقصى للآيات الجديدة يوميًا",
            "reviews": "الحد الأقصى للمراجعات يوميًا",
            "learning_verses": "الحد الأقصى للآيات في مرحلة التعلم",
        },
        "recommendations_en": {
            "new_verses": "Maximum new verses per day",
            "reviews": "Maximum reviews per day",
            "learning_verses": "Maximum verses in learning stage",
        },
    }


# =============================================================================
# MULTI-SCHOOL TAFSIR COMPARISON (PHASE 5)
# =============================================================================


@router.get("/tafsir-schools")
async def get_all_tafsir_schools():
    """
    Get all Tafsir schools with descriptions.

    Returns schools like: Sunni Traditional, Linguistic, Rational, Sufi, Shia, Contemporary, etc.

    Arabic: جميع مذاهب التفسير مع وصفها
    """
    from app.services.tafsir_schools import tafsir_schools_service

    schools = tafsir_schools_service.get_all_schools()

    return {
        "schools": schools,
        "count": len(schools),
        "guidance_ar": "كل مذهب له منهجه الخاص في فهم القرآن",
        "guidance_en": "Each school has its own methodology for understanding the Quran",
    }


@router.get("/tafsir-schools/{school_id}/scholars")
async def get_scholars_by_school(
    school_id: str,
):
    """
    Get scholars belonging to a specific Tafsir school.

    Arabic: العلماء المنتمون لمذهب تفسيري معين
    """
    from app.services.tafsir_schools import tafsir_schools_service

    scholars = tafsir_schools_service.get_scholars_by_school(school_id)

    if not scholars:
        raise HTTPException(
            status_code=404,
            detail={"error": f"School '{school_id}' not found"},
        )

    return {
        "school_id": school_id,
        "scholars": scholars,
        "count": len(scholars),
    }


@router.get("/tafsir-schools/scholar/{scholar_id}")
async def get_scholar_details(
    scholar_id: str,
):
    """
    Get detailed information about a Tafsir scholar.

    Arabic: معلومات تفصيلية عن عالم تفسير
    """
    from app.services.tafsir_schools import tafsir_schools_service

    scholar = tafsir_schools_service.get_scholar_details(scholar_id)

    if not scholar:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Scholar '{scholar_id}' not found"},
        )

    return scholar


@router.get("/tafsir-schools/compare/{sura_no}/{aya_no}")
async def compare_schools_on_verse(
    sura_no: int,
    aya_no: int,
    schools: Optional[str] = Query(None, description="Comma-separated school IDs"),
):
    """
    Compare interpretations from different schools on a specific verse.

    Arabic: مقارنة تفاسير المذاهب المختلفة لآية معينة
    """
    from app.services.tafsir_schools import tafsir_schools_service

    school_list = schools.split(",") if schools else None

    return tafsir_schools_service.compare_schools_on_verse(
        sura_no=sura_no,
        aya_no=aya_no,
        schools=school_list,
    )


@router.get("/tafsir-schools/theological-topics")
async def get_theological_topics():
    """
    Get all comparative theological topics where schools differ.

    Examples: Divine Attributes, Free Will, Seeing Allah, Intercession

    Arabic: المواضيع العقدية التي تختلف فيها المذاهب
    """
    from app.services.tafsir_schools import tafsir_schools_service

    topics = tafsir_schools_service.get_theological_topics()

    return {
        "topics": topics,
        "count": len(topics),
        "note_ar": "هذه خلافات فكرية تاريخية ضمن إطار الإسلام",
        "note_en": "These are historical intellectual differences within Islam",
    }


@router.get("/tafsir-schools/theological-topics/{topic_id}")
async def get_topic_comparison(
    topic_id: str,
):
    """
    Get detailed comparison of schools on a theological topic.

    Arabic: مقارنة تفصيلية للمذاهب في موضوع عقدي
    """
    from app.services.tafsir_schools import tafsir_schools_service

    comparison = tafsir_schools_service.get_topic_comparison(topic_id)

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Topic '{topic_id}' not found"},
        )

    return comparison


@router.get("/tafsir-schools/methodologies")
async def get_tafsir_methodologies():
    """
    Get all Tafsir methodologies with descriptions.

    Arabic: منهجيات التفسير مع وصفها
    """
    from app.services.tafsir_schools import tafsir_schools_service

    return {
        "methodologies": tafsir_schools_service.get_methodologies(),
    }


@router.get("/tafsir-schools/recommend")
async def recommend_tafsir_for_goal(
    goal: str = Query(..., description="Study goal: beginner, linguistic, hadith, philosophical, spiritual, contemporary"),
):
    """
    Recommend Tafsir sources based on study goal.

    Arabic: توصية بمصادر التفسير حسب هدف الدراسة
    """
    from app.services.tafsir_schools import tafsir_schools_service

    return tafsir_schools_service.recommend_tafsir_for_goal(goal)


# =============================================================================
# INTERACTIVE THEMATIC EXPLORATION (PHASE 5)
# =============================================================================


@router.get("/explore/themes")
async def get_all_themes(
    category: Optional[str] = Query(None, description="Filter by category: faith, ethics, worship, stories, afterlife, social"),
):
    """
    Get all exploration themes with life lessons.

    Arabic: جميع المواضيع الاستكشافية مع الدروس الحياتية
    """
    from app.services.thematic_exploration import thematic_exploration_service

    themes = thematic_exploration_service.get_all_themes(category=category)

    return {
        "themes": themes,
        "count": len(themes),
        "filter": category,
    }


@router.get("/explore/categories")
async def get_theme_categories():
    """
    Get all theme categories.

    Arabic: جميع فئات المواضيع
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return {
        "categories": thematic_exploration_service.get_categories(),
    }


@router.get("/explore/themes/{theme_id}")
async def get_theme_details(
    theme_id: str,
):
    """
    Get detailed information about a theme including life lessons.

    Arabic: تفاصيل موضوع معين مع الدروس الحياتية
    """
    from app.services.thematic_exploration import thematic_exploration_service

    theme = thematic_exploration_service.get_theme_details(theme_id)

    if not theme:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Theme '{theme_id}' not found"},
        )

    return theme


@router.get("/explore/life-lessons")
async def get_life_lessons_by_situation(
    situation: str = Query(..., description="Life situation: loss, fear, conflict, decision, etc."),
):
    """
    Find life lessons relevant to a specific life situation.

    Arabic: إيجاد الدروس الحياتية المناسبة لموقف معين
    """
    from app.services.thematic_exploration import thematic_exploration_service

    lessons = thematic_exploration_service.get_life_lessons_by_situation(situation)

    return {
        "situation": situation,
        "lessons": lessons,
        "count": len(lessons),
        "encouragement_ar": "القرآن فيه شفاء لما في الصدور",
        "encouragement_en": "The Quran contains healing for what is in the hearts",
    }


@router.get("/explore/path/{start_theme}")
async def get_exploration_path(
    start_theme: str,
    depth: int = Query(3, ge=1, le=10),
):
    """
    Generate an exploration path starting from a theme.

    Arabic: مسار استكشافي يبدأ من موضوع معين
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return thematic_exploration_service.get_exploration_path(
        start_theme=start_theme,
        depth=depth,
    )


@router.post("/explore/journey/start")
async def start_exploration_journey(
    user_id: str = Query(...),
    mode: str = Query("guided", description="Mode: guided, free, goal, situational"),
    goals: Optional[str] = Query(None, description="Comma-separated goals"),
):
    """
    Start a new exploration journey.

    Arabic: بدء رحلة استكشافية جديدة
    """
    from app.services.thematic_exploration import thematic_exploration_service

    goal_list = goals.split(",") if goals else None

    return thematic_exploration_service.start_journey(
        user_id=user_id,
        mode=mode,
        goals=goal_list,
    )


@router.post("/explore/journey/visit")
async def visit_theme(
    user_id: str = Query(...),
    theme_id: str = Query(...),
):
    """
    Record a theme visit and get theme details with suggestions.

    Arabic: تسجيل زيارة لموضوع والحصول على اقتراحات
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return thematic_exploration_service.visit_theme(
        user_id=user_id,
        theme_id=theme_id,
    )


@router.post("/explore/journey/save-lesson")
async def save_life_lesson(
    user_id: str = Query(...),
    theme_id: str = Query(...),
    lesson_index: int = Query(..., ge=0),
):
    """
    Save a life lesson to user's collection.

    Arabic: حفظ درس حياتي في مجموعة المستخدم
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return thematic_exploration_service.save_lesson(
        user_id=user_id,
        theme_id=theme_id,
        lesson_index=lesson_index,
    )


@router.get("/explore/journey/summary")
async def get_journey_summary(
    user_id: str = Query(...),
):
    """
    Get summary of user's exploration journey.

    Arabic: ملخص رحلة المستخدم الاستكشافية
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return thematic_exploration_service.get_journey_summary(user_id)


@router.get("/explore/graph")
async def get_themes_graph_data():
    """
    Get data for visualizing themes as an interactive graph.

    Returns nodes and edges for graph visualization.

    Arabic: بيانات لعرض المواضيع كرسم بياني تفاعلي
    """
    from app.services.thematic_exploration import thematic_exploration_service

    return thematic_exploration_service.get_graph_data()


# =============================================================================
# ADAPTIVE LEARNING PATHS (PHASE 5)
# =============================================================================


@router.post("/learning/profile/initialize")
async def initialize_learning_profile(
    user_id: str = Query(...),
    goal: str = Query("understanding", description="Goal: memorization, understanding, recitation, translation, tafsir, daily_practice"),
    level: str = Query("beginner", description="Level: beginner, intermediate, advanced, expert"),
    pace: str = Query("moderate", description="Pace: slow, moderate, fast, intensive"),
):
    """
    Initialize a user's learning profile with preferences.

    Arabic: تهيئة ملف التعلم للمستخدم مع التفضيلات
    """
    from app.services.adaptive_learning import adaptive_learning_service

    return await adaptive_learning_service.initialize_profile(
        user_id=user_id,
        goal=goal,
        level=level,
        pace=pace,
    )


@router.post("/learning/session/record")
async def record_study_session(
    user_id: str = Query(...),
    duration_minutes: int = Query(..., ge=1, description="Session duration in minutes"),
    verses_studied: int = Query(..., ge=0),
    goal: Optional[str] = Query(None),
    performance: float = Query(0.7, ge=0.0, le=1.0, description="Performance score 0-1"),
    topics: Optional[str] = Query(None, description="Comma-separated topics"),
):
    """
    Record a study session and update user profile.

    Arabic: تسجيل جلسة دراسة وتحديث الملف الشخصي
    """
    from app.services.adaptive_learning import adaptive_learning_service

    topic_list = topics.split(",") if topics else None

    return await adaptive_learning_service.record_study_session(
        user_id=user_id,
        duration_minutes=duration_minutes,
        verses_studied=verses_studied,
        goal=goal,
        performance=performance,
        topics=topic_list,
    )


@router.get("/learning/recommendations")
async def get_learning_recommendations(
    user_id: str = Query(...),
):
    """
    Get personalized content recommendations based on user patterns.

    Arabic: توصيات محتوى مخصصة بناءً على أنماط المستخدم
    """
    from app.services.adaptive_learning import adaptive_learning_service

    return await adaptive_learning_service.get_personalized_recommendations(user_id)


@router.get("/learning/daily-plan")
async def get_daily_learning_plan(
    user_id: str = Query(...),
):
    """
    Generate a personalized daily study plan.

    Arabic: إنشاء خطة دراسة يومية مخصصة
    """
    from app.services.adaptive_learning import adaptive_learning_service

    return await adaptive_learning_service.get_daily_plan(user_id)


@router.get("/learning/analytics")
async def get_learning_analytics(
    user_id: str = Query(...),
):
    """
    Get detailed progress analytics and insights.

    Arabic: تحليلات التقدم والرؤى التفصيلية
    """
    from app.services.adaptive_learning import adaptive_learning_service

    return await adaptive_learning_service.get_progress_analytics(user_id)


@router.get("/learning/quiz")
async def get_adaptive_quiz(
    user_id: str = Query(...),
    topic: Optional[str] = Query(None),
):
    """
    Generate an adaptive quiz based on user's level and history.

    Arabic: اختبار تكيفي بناءً على مستوى المستخدم
    """
    from app.services.adaptive_learning import adaptive_learning_service

    return await adaptive_learning_service.get_adaptive_quiz(
        user_id=user_id,
        topic=topic,
    )


@router.get("/learning/goals")
async def get_available_learning_goals():
    """
    Get all available learning goals with descriptions.

    Arabic: جميع أهداف التعلم المتاحة مع وصفها
    """
    goals = {
        "memorization": {
            "ar": "الحفظ",
            "en": "Memorization (Hifz)",
            "description_ar": "حفظ القرآن الكريم آية آية",
            "description_en": "Memorizing the Quran verse by verse",
        },
        "understanding": {
            "ar": "الفهم والتدبر",
            "en": "Understanding (Tadabbur)",
            "description_ar": "فهم معاني الآيات والتأمل فيها",
            "description_en": "Understanding verse meanings and contemplating them",
        },
        "recitation": {
            "ar": "التلاوة والتجويد",
            "en": "Recitation (Tajweed)",
            "description_ar": "إتقان تلاوة القرآن بالتجويد",
            "description_en": "Mastering Quran recitation with proper Tajweed",
        },
        "translation": {
            "ar": "الترجمة",
            "en": "Translation",
            "description_ar": "فهم القرآن من خلال الترجمات",
            "description_en": "Understanding Quran through translations",
        },
        "tafsir": {
            "ar": "التفسير",
            "en": "Tafsir (Interpretation)",
            "description_ar": "دراسة تفسير القرآن بعمق",
            "description_en": "Studying Quran interpretation in depth",
        },
        "daily_practice": {
            "ar": "الورد اليومي",
            "en": "Daily Practice",
            "description_ar": "قراءة ورد يومي من القرآن",
            "description_en": "Reading a daily portion of Quran",
        },
    }

    return {
        "goals": goals,
        "guidance_ar": "اختر الهدف الذي يناسب احتياجاتك",
        "guidance_en": "Choose the goal that suits your needs",
    }


@router.get("/learning/levels")
async def get_difficulty_levels():
    """
    Get all difficulty levels with descriptions.

    Arabic: جميع مستويات الصعوبة مع وصفها
    """
    levels = {
        "beginner": {
            "ar": "مبتدئ",
            "en": "Beginner",
            "description_ar": "للبدء في رحلة القرآن",
            "description_en": "Starting the Quran journey",
            "recommended_for": "New learners",
        },
        "intermediate": {
            "ar": "متوسط",
            "en": "Intermediate",
            "description_ar": "لمن لديه أساس في القرآن",
            "description_en": "Those with Quran fundamentals",
            "recommended_for": "Those who can read Arabic",
        },
        "advanced": {
            "ar": "متقدم",
            "en": "Advanced",
            "description_ar": "لمن أتقن الأساسيات",
            "description_en": "Those who mastered basics",
            "recommended_for": "Experienced students",
        },
        "expert": {
            "ar": "خبير",
            "en": "Expert",
            "description_ar": "للدراسة المتعمقة",
            "description_en": "For in-depth study",
            "recommended_for": "Scholars and teachers",
        },
    }

    return {"levels": levels}


@router.get("/learning/paces")
async def get_learning_paces():
    """
    Get all learning pace options with descriptions.

    Arabic: جميع خيارات وتيرة التعلم مع وصفها
    """
    paces = {
        "slow": {
            "ar": "بطيء",
            "en": "Slow",
            "verses_per_day": "1-3",
            "session_minutes": "10-20",
            "suitable_for_ar": "المبتدئين والمشغولين",
            "suitable_for_en": "Beginners and busy individuals",
        },
        "moderate": {
            "ar": "متوسط",
            "en": "Moderate",
            "verses_per_day": "4-7",
            "session_minutes": "20-40",
            "suitable_for_ar": "معظم المتعلمين",
            "suitable_for_en": "Most learners",
        },
        "fast": {
            "ar": "سريع",
            "en": "Fast",
            "verses_per_day": "8-15",
            "session_minutes": "30-60",
            "suitable_for_ar": "المتعلمين الجادين",
            "suitable_for_en": "Serious learners",
        },
        "intensive": {
            "ar": "مكثف",
            "en": "Intensive",
            "verses_per_day": "15+",
            "session_minutes": "45-90",
            "suitable_for_ar": "طلاب العلم المتفرغين",
            "suitable_for_en": "Full-time students",
        },
    }

    return {"paces": paces}


# =============================================================================
# CONTEXTUAL SEMANTIC SEARCH (PHASE 6)
# =============================================================================


@router.get("/contextual-search")
async def contextual_semantic_search(
    q: str = Query(..., min_length=1, description="Search query (Arabic or English)"),
    mode: str = Query("hybrid", description="Search mode: semantic, lexical, hybrid, contextual"),
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.25, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Advanced contextual semantic search with bilingual support.

    Features:
    - Cross-sentence context understanding
    - Bilingual query expansion (Arabic ↔ English)
    - Intent detection and optimization
    - Phrase-level matching

    Arabic: البحث الدلالي السياقي المتقدم مع دعم ثنائي اللغة
    """
    from app.services.contextual_search import contextual_search_service

    return await contextual_search_service.contextual_search(
        query=q,
        session=session,
        limit=limit,
        min_score=min_score,
        search_mode=mode,
    )


@router.get("/contextual-search/expand")
async def expand_query_contextually(
    q: str = Query(..., min_length=1),
):
    """
    Expand query with contextual understanding.

    Returns detected intent, language, and expanded terms.

    Arabic: توسيع الاستعلام مع الفهم السياقي
    """
    from app.services.contextual_search import contextual_search_service

    expanded = contextual_search_service.expand_query_contextually(q)

    return {
        "original": expanded.original,
        "detected_language": expanded.detected_language,
        "intent": expanded.intent.value,
        "primary_terms": expanded.primary_terms,
        "expanded_arabic": expanded.expanded_arabic,
        "expanded_english": expanded.expanded_english,
        "context_phrases": expanded.context_phrases,
        "related_themes": expanded.related_themes,
        "confidence": round(expanded.confidence, 2),
        "explanation": expanded.explanation,
    }


@router.get("/contextual-search/concepts")
async def get_bilingual_concepts():
    """
    Get all available bilingual concepts for search.

    Arabic: جميع المفاهيم ثنائية اللغة المتاحة للبحث
    """
    from app.services.contextual_search import contextual_search_service

    concepts = contextual_search_service.get_available_concepts()

    return {
        "concepts": concepts,
        "count": len(concepts),
    }


@router.get("/contextual-search/modes")
async def get_search_modes():
    """
    Get available search modes with descriptions.

    Arabic: أوضاع البحث المتاحة مع وصفها
    """
    from app.services.contextual_search import contextual_search_service

    return {
        "modes": contextual_search_service.get_search_modes(),
    }


# =============================================================================
# AI RECOMMENDATIONS (PHASE 6)
# =============================================================================


@router.post("/ai/track-event")
async def track_user_event(
    user_id: str = Query(...),
    event_type: str = Query(..., description="Event: search, view_verse, view_tafsir, bookmark, share, study, memorize"),
    content_type: str = Query(..., description="Content type: verse, sura, theme, tafsir, prophet"),
    content_id: str = Query(...),
    topics: Optional[str] = Query(None, description="Comma-separated topics"),
):
    """
    Track a user interaction event for personalization.

    Arabic: تتبع حدث تفاعل المستخدم للتخصيص
    """
    from app.services.ai_recommendations import ai_recommendation_service

    metadata = {}
    if topics:
        metadata["topics"] = topics.split(",")

    return await ai_recommendation_service.track_event(
        user_id=user_id,
        event_type=event_type,
        content_type=content_type,
        content_id=content_id,
        metadata=metadata,
    )


@router.get("/ai/recommendations")
async def get_ai_recommendations(
    user_id: str = Query(...),
    rec_type: Optional[str] = Query(None, description="Type: similar_verses, related_themes, next_lesson, tafsir, prophet_story, trending, personalized"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get personalized AI recommendations.

    Arabic: الحصول على توصيات الذكاء الاصطناعي المخصصة
    """
    from app.services.ai_recommendations import ai_recommendation_service

    return await ai_recommendation_service.get_recommendations(
        user_id=user_id,
        rec_type=rec_type,
        limit=limit,
    )


@router.get("/ai/collaborative-recommendations")
async def get_collaborative_recommendations(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get recommendations based on similar users' preferences.

    Arabic: توصيات بناءً على تفضيلات المستخدمين المشابهين
    """
    from app.services.ai_recommendations import ai_recommendation_service

    return await ai_recommendation_service.get_collaborative_recommendations(
        user_id=user_id,
        limit=limit,
    )


@router.get("/ai/similar-users")
async def get_similar_users(
    user_id: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Find users with similar preferences.

    Arabic: إيجاد المستخدمين ذوي الاهتمامات المشابهة
    """
    from app.services.ai_recommendations import ai_recommendation_service

    similar = await ai_recommendation_service.get_similar_users(
        user_id=user_id,
        limit=limit,
    )

    return {
        "user_id": user_id,
        "similar_users": similar,
        "count": len(similar),
    }


@router.get("/ai/behavior-summary")
async def get_behavior_summary(
    user_id: str = Query(...),
):
    """
    Get summary of user's behavior patterns.

    Arabic: ملخص أنماط سلوك المستخدم
    """
    from app.services.ai_recommendations import ai_recommendation_service

    return await ai_recommendation_service.get_user_behavior_summary(user_id)


# =============================================================================
# GRAPH SEARCH (PHASE 6)
# =============================================================================


@router.get("/graph/connections/{node_id}")
async def find_graph_connections(
    node_id: str,
    max_depth: int = Query(3, ge=1, le=5),
    min_weight: float = Query(0.5, ge=0.0, le=1.0),
):
    """
    Find all connections from a node in the knowledge graph.

    Arabic: إيجاد جميع الروابط من عقدة في الرسم البياني المعرفي
    """
    from app.services.graph_search import graph_search_service

    return await graph_search_service.find_connections(
        source_id=node_id,
        max_depth=max_depth,
        min_weight=min_weight,
    )


@router.get("/graph/path")
async def find_graph_path(
    source: str = Query(..., description="Source node ID (e.g., 'patience', 'إبراهيم')"),
    target: str = Query(..., description="Target node ID"),
    max_depth: int = Query(5, ge=1, le=10),
):
    """
    Find shortest path between two nodes.

    Arabic: إيجاد أقصر مسار بين عقدتين
    """
    from app.services.graph_search import graph_search_service

    return await graph_search_service.find_path(
        source_id=source,
        target_id=target,
        max_depth=max_depth,
    )


@router.get("/graph/related/{node_id}")
async def get_related_content(
    node_id: str,
    content_type: Optional[str] = Query(None, description="Filter: themes, prophets, verses"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get content related to a node.

    Arabic: الحصول على المحتوى المرتبط بعقدة
    """
    from app.services.graph_search import graph_search_service

    return await graph_search_service.get_related_content(
        node_id=node_id,
        content_type=content_type,
        limit=limit,
    )


@router.get("/graph/visualization")
async def get_graph_visualization(
    center: Optional[str] = Query(None, description="Center node for subgraph"),
    depth: int = Query(2, ge=1, le=4),
):
    """
    Get data for graph visualization.

    Arabic: الحصول على بيانات التصور البياني
    """
    from app.services.graph_search import graph_search_service

    return await graph_search_service.get_visualization_data(
        center_node=center,
        depth=depth,
    )


@router.get("/graph/centrality")
async def compute_graph_centrality():
    """
    Compute centrality scores for all nodes.

    Arabic: حساب درجات المركزية لجميع العقد
    """
    from app.services.graph_search import graph_search_service

    return await graph_search_service.compute_centrality()


# =============================================================================
# CACHE MANAGEMENT (PHASE 6)
# =============================================================================


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.

    Arabic: إحصائيات الذاكرة المؤقتة
    """
    from app.services.cache_service import cache_service

    return cache_service.get_all_stats()


@router.post("/cache/cleanup")
async def cleanup_expired_cache():
    """
    Cleanup expired cache entries.

    Arabic: تنظيف إدخالات الذاكرة المؤقتة المنتهية
    """
    from app.services.cache_service import cache_service

    results = await cache_service.cleanup_all_expired()

    return {
        "status": "cleaned",
        "expired_entries_removed": results,
    }


@router.post("/cache/warm")
async def warm_cache(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Pre-warm cache with frequently accessed data.

    Arabic: تسخين الذاكرة المؤقتة بالبيانات المستخدمة بكثرة
    """
    from app.services.cache_service import cache_service

    return await cache_service.warm_cache(session)


@router.delete("/cache/user/{user_id}")
async def invalidate_user_cache(
    user_id: str,
):
    """
    Invalidate all caches for a user.

    Arabic: إبطال جميع ذاكرة التخزين المؤقت للمستخدم
    """
    from app.services.cache_service import cache_service

    await cache_service.invalidate_user_cache(user_id)

    return {
        "status": "invalidated",
        "user_id": user_id,
    }


# =============================================================================
# NAMED ENTITY RECOGNITION (NER) - PHASE 7
# =============================================================================


class EntityResponse(BaseModel):
    """Named entity response."""
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    english_name: str
    confidence: float
    metadata: Dict[str, Any] = {}


class EntityAnalysisResponse(BaseModel):
    """Entity analysis response."""
    original_text: str
    entities: List[EntityResponse]
    entity_counts: Dict[str, int]
    primary_entities: List[EntityResponse]
    context_summary: Dict[str, str]


@router.post("/ner/analyze")
async def analyze_text_for_entities(
    text: str = Query(..., min_length=2, description="Arabic or English text to analyze"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
):
    """
    Analyze text for named entities (prophets, angels, places, events, etc.)

    Features:
    - Identifies 25+ prophets with metadata
    - Recognizes 7 angels mentioned in Quran
    - Detects 11+ significant places
    - Identifies historical events
    - Recognizes divine names
    - Detects nations mentioned in Quran

    Arabic: تحليل النص لاستخراج الكيانات المسماة (أنبياء، ملائكة، أماكن، أحداث)
    """
    from app.services.ner_service import ner_service

    result = ner_service.extract_entities(
        text=text,
        min_confidence=min_confidence,
    )

    return EntityAnalysisResponse(
        original_text=result.original_text,
        entities=[
            EntityResponse(
                text=e.text,
                entity_type=e.entity_type.value,
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                english_name=e.english_name,
                confidence=e.confidence,
                metadata=e.metadata,
            )
            for e in result.entities
        ],
        entity_counts=result.entity_counts,
        primary_entities=[
            EntityResponse(
                text=e.text,
                entity_type=e.entity_type.value,
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                english_name=e.english_name,
                confidence=e.confidence,
                metadata=e.metadata,
            )
            for e in result.primary_entities
        ],
        context_summary=result.context_summary,
    )


@router.get("/ner/entity/{entity_name}")
async def get_entity_details(
    entity_name: str,
    entity_type: Optional[str] = Query(None, description="Type: prophet, place, nation, angel"),
):
    """
    Get detailed information about a specific entity.

    Arabic: الحصول على معلومات تفصيلية عن كيان محدد
    """
    from app.services.ner_service import ner_service

    details = ner_service.get_entity_details(
        entity_name=entity_name,
        entity_type=entity_type,
    )

    if not details:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Entity '{entity_name}' not found"},
        )

    return details


@router.get("/ner/prophets")
async def get_all_prophets():
    """
    Get list of all prophets mentioned in the Quran.

    Returns 25 prophets with:
    - Arabic and English names
    - Number of mentions in Quran
    - Key suras where they appear
    - Descriptions

    Arabic: قائمة جميع الأنبياء المذكورين في القرآن
    """
    from app.services.ner_service import ner_service

    prophets = ner_service.get_all_prophets()

    # Sort by mentions (most mentioned first)
    prophets_sorted = sorted(prophets, key=lambda p: p["mentions"], reverse=True)

    return {
        "prophets": prophets_sorted,
        "count": len(prophets_sorted),
        "most_mentioned": prophets_sorted[0] if prophets_sorted else None,
        "guidance_ar": "الأنبياء قدوة للبشرية",
        "guidance_en": "The prophets are exemplars for humanity",
    }


@router.get("/ner/places")
async def get_all_places():
    """
    Get list of all places mentioned in the Quran.

    Returns places with:
    - Arabic and English names
    - Type (city, mountain, region, etc.)
    - Significance
    - Key suras

    Arabic: قائمة جميع الأماكن المذكورة في القرآن
    """
    from app.services.ner_service import ner_service

    places = ner_service.get_all_places()

    return {
        "places": places,
        "count": len(places),
        "note_ar": "الأماكن القرآنية لها دلالات تاريخية ودينية",
        "note_en": "Quranic places have historical and religious significance",
    }


@router.get("/ner/events")
async def get_all_events():
    """
    Get list of all historical events mentioned in the Quran.

    Returns events with:
    - Arabic and English names
    - Associated prophet
    - Type (miracle, battle, divine punishment, etc.)
    - Key suras

    Arabic: قائمة جميع الأحداث التاريخية المذكورة في القرآن
    """
    from app.services.ner_service import ner_service

    events = ner_service.get_all_events()

    return {
        "events": events,
        "count": len(events),
        "note_ar": "القصص القرآني عبرة للعالمين",
        "note_en": "Quranic stories are lessons for all of humanity",
    }


@router.get("/ner/stats")
async def get_ner_statistics():
    """
    Get statistics about all named entities in the database.

    Arabic: إحصائيات الكيانات المسماة في قاعدة البيانات
    """
    from app.services.ner_service import ner_service

    return ner_service.get_entity_stats()


@router.get("/ner/types")
async def get_entity_types():
    """
    Get all available entity types for NER.

    Arabic: أنواع الكيانات المتاحة للتعرف
    """
    from app.services.ner_service import EntityType

    return {
        "entity_types": [
            {"id": e.value, "description_ar": desc_ar, "description_en": desc_en}
            for e, desc_ar, desc_en in [
                (EntityType.PROPHET, "نبي أو رسول", "Prophet or messenger"),
                (EntityType.ANGEL, "ملاك", "Angel"),
                (EntityType.HISTORICAL_FIGURE, "شخصية تاريخية", "Historical figure"),
                (EntityType.PLACE, "مكان", "Place"),
                (EntityType.EVENT, "حدث تاريخي", "Historical event"),
                (EntityType.DIVINE_NAME, "اسم من أسماء الله", "Divine name"),
                (EntityType.DIVINE_ATTRIBUTE, "صفة إلهية", "Divine attribute"),
                (EntityType.RELIGIOUS_CONCEPT, "مفهوم ديني", "Religious concept"),
                (EntityType.NATION, "أمة أو قوم", "Nation or people"),
                (EntityType.BOOK, "كتاب سماوي", "Divine book"),
                (EntityType.TIME_PERIOD, "فترة زمنية", "Time period"),
            ]
        ],
        "count": 11,
    }


@router.get("/ner/analyze-verse/{sura_no}/{aya_no}")
async def analyze_verse_entities(
    sura_no: int,
    aya_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Analyze a specific verse for named entities.

    Arabic: تحليل آية معينة لاستخراج الكيانات المسماة
    """
    from app.services.ner_service import ner_service
    from app.models.quran import QuranVerse

    # Get verse
    result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no == aya_no,
        )
    )
    verse = result.scalar_one_or_none()

    if not verse:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Verse {sura_no}:{aya_no} not found"},
        )

    # Analyze verse text
    analysis = ner_service.extract_entities(verse.text_uthmani)

    return {
        "verse_reference": f"{sura_no}:{aya_no}",
        "verse_text": verse.text_uthmani,
        "entities": [
            {
                "text": e.text,
                "type": e.entity_type.value,
                "english_name": e.english_name,
                "confidence": e.confidence,
            }
            for e in analysis.entities
        ],
        "entity_counts": analysis.entity_counts,
        "context_summary": analysis.context_summary,
    }


@router.get("/ner/search-by-entity")
async def search_by_entity(
    entity_name: str = Query(..., description="Entity name in Arabic or English"),
    entity_type: Optional[str] = Query(None, description="Type: prophet, place, event, nation"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Search verses containing a specific entity.

    Arabic: البحث عن الآيات التي تحتوي على كيان معين
    """
    from app.services.ner_service import ner_service
    from app.models.quran import QuranVerse

    # Get entity details to find aliases
    entity_details = ner_service.get_entity_details(entity_name, entity_type)

    if not entity_details:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Entity '{entity_name}' not found"},
        )

    # Build search terms
    search_terms = [entity_details.get("name_ar", entity_name)]
    if "aliases" in entity_details:
        search_terms.extend(entity_details["aliases"])

    # Search in key suras first
    key_suras = entity_details.get("key_suras", [])

    matching_verses = []

    for sura_no in key_suras[:5]:  # Limit to first 5 key suras
        result = await session.execute(
            select(QuranVerse).where(QuranVerse.sura_no == sura_no)
        )
        verses = result.scalars().all()

        for verse in verses:
            for term in search_terms:
                if term in verse.text_uthmani:
                    matching_verses.append({
                        "sura_no": verse.sura_no,
                        "aya_no": verse.aya_no,
                        "reference": f"{verse.sura_no}:{verse.aya_no}",
                        "text_uthmani": verse.text_uthmani,
                        "matched_term": term,
                    })
                    break

    return {
        "entity": entity_details,
        "search_terms": search_terms,
        "verses": matching_verses[:30],  # Limit results
        "count": len(matching_verses),
    }


@router.get("/ner/entity-connections/{entity_name}")
async def get_entity_connections(
    entity_name: str,
    entity_type: Optional[str] = Query(None),
):
    """
    Get connections between an entity and other entities.

    Arabic: الحصول على روابط بين كيان وكيانات أخرى
    """
    from app.services.ner_service import ner_service, PROPHETS, NATIONS, EVENTS

    # Get entity details
    entity = ner_service.get_entity_details(entity_name, entity_type)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Entity '{entity_name}' not found"},
        )

    connections = {
        "related_prophets": [],
        "related_places": [],
        "related_events": [],
        "related_nations": [],
    }

    entity_ar = entity.get("name_ar", entity_name)

    # Find related events
    for event_ar, event_data in EVENTS.items():
        if event_data.get("prophet") == entity_ar:
            connections["related_events"].append({
                "name_ar": event_ar,
                "name_en": event_data["en"],
                "type": event_data["type"],
            })

    # Find related nations
    for nation_ar, nation_data in NATIONS.items():
        if nation_data.get("prophet") == entity_ar:
            connections["related_nations"].append({
                "name_ar": nation_ar,
                "name_en": nation_data["en"],
                "fate_en": nation_data["fate_en"],
            })

    # Find prophets with shared suras
    if entity.get("type") == "prophet" and "key_suras" in entity:
        entity_suras = set(entity["key_suras"])
        for prophet_ar, prophet_data in PROPHETS.items():
            if prophet_ar != entity_ar:
                prophet_suras = set(prophet_data.get("key_suras", []))
                shared = entity_suras.intersection(prophet_suras)
                if len(shared) >= 2:
                    connections["related_prophets"].append({
                        "name_ar": prophet_ar,
                        "name_en": prophet_data["en"],
                        "shared_suras": list(shared)[:5],
                    })

    return {
        "entity": entity,
        "connections": connections,
        "total_connections": sum(len(v) for v in connections.values()),
    }


# =============================================================================
# CROSS-SURA NARRATIVE ARC EXPLORATION (PHASE 7)
# =============================================================================


@router.get("/narrative/arcs")
async def get_all_narrative_arcs():
    """
    Get all available narrative arcs for exploration.

    Features:
    - Prophet stories spanning multiple suras
    - Story phases (introduction, rising action, climax, resolution)
    - Key themes and moral lessons

    Arabic: جميع الأقواس السردية المتاحة للاستكشاف
    """
    from app.services.narrative_arc_service import narrative_arc_service

    arcs = narrative_arc_service.get_all_narrative_arcs()

    return {
        "narrative_arcs": arcs,
        "count": len(arcs),
        "guidance_ar": "استكشف قصص الأنبياء عبر سور متعددة",
        "guidance_en": "Explore prophet stories across multiple suras",
    }


@router.get("/narrative/arcs/{arc_id}")
async def get_narrative_arc_details(
    arc_id: str,
):
    """
    Get detailed information about a specific narrative arc.

    Arabic: تفاصيل قوس سردي معين
    """
    from app.services.narrative_arc_service import narrative_arc_service

    arc = narrative_arc_service.get_narrative_arc(arc_id)

    if not arc:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Narrative arc '{arc_id}' not found"},
        )

    return arc


@router.get("/narrative/arcs/{arc_id}/segment/{segment_index}")
async def get_narrative_segment(
    arc_id: str,
    segment_index: int,
):
    """
    Get a specific segment of a narrative arc.

    Arabic: الحصول على جزء معين من القوس السردي
    """
    from app.services.narrative_arc_service import narrative_arc_service

    segment = narrative_arc_service.get_arc_segment(arc_id, segment_index)

    if not segment:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Segment {segment_index} not found in arc '{arc_id}'"},
        )

    return segment


@router.get("/narrative/arcs/{arc_id}/timeline")
async def get_story_timeline(
    arc_id: str,
):
    """
    Get timeline visualization data for a story arc.

    Arabic: بيانات الجدول الزمني للقصة
    """
    from app.services.narrative_arc_service import narrative_arc_service

    timeline = narrative_arc_service.get_story_timeline(arc_id)

    if "error" in timeline:
        raise HTTPException(status_code=404, detail=timeline)

    return timeline


@router.get("/narrative/arcs/{arc_id}/cross-references")
async def get_arc_cross_references(
    arc_id: str,
):
    """
    Get cross-references to other narrative arcs.

    Arabic: الروابط مع أقواس سردية أخرى
    """
    from app.services.narrative_arc_service import narrative_arc_service

    refs = narrative_arc_service.get_narrative_cross_references(arc_id)

    return {
        "arc_id": arc_id,
        "cross_references": refs,
        "count": len(refs),
    }


@router.get("/narrative/by-sura/{sura_no}")
async def get_narratives_by_sura(
    sura_no: int,
):
    """
    Get all narrative arcs that include a specific sura.

    Arabic: جميع الأقواس السردية التي تشمل سورة معينة
    """
    from app.services.narrative_arc_service import narrative_arc_service

    stories = narrative_arc_service.get_story_by_sura(sura_no)

    return {
        "sura_no": sura_no,
        "narratives": stories,
        "count": len(stories),
    }


@router.get("/narrative/thematic-progressions")
async def get_all_thematic_progressions():
    """
    Get all tracked thematic progressions across the Quran.

    Arabic: جميع التطورات الموضوعية المتتبعة عبر القرآن
    """
    from app.services.narrative_arc_service import narrative_arc_service

    progressions = narrative_arc_service.get_all_thematic_progressions()

    return {
        "thematic_progressions": progressions,
        "count": len(progressions),
        "guidance_ar": "تتبع كيف تتطور المواضيع عبر سور القرآن",
        "guidance_en": "Track how themes evolve across Quranic suras",
    }


@router.get("/narrative/thematic-progressions/{theme_id}")
async def get_thematic_progression_details(
    theme_id: str,
):
    """
    Get detailed progression of a theme across suras.

    Arabic: تفاصيل تطور موضوع عبر السور
    """
    from app.services.narrative_arc_service import narrative_arc_service

    progression = narrative_arc_service.get_thematic_progression(theme_id)

    if not progression:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Thematic progression '{theme_id}' not found"},
        )

    return progression


@router.get("/narrative/search")
async def search_narratives_by_theme(
    theme: str = Query(..., description="Theme to search for"),
):
    """
    Search narrative arcs by theme.

    Arabic: البحث في الأقواس السردية حسب الموضوع
    """
    from app.services.narrative_arc_service import narrative_arc_service

    results = narrative_arc_service.search_narratives_by_theme(theme)

    return {
        "search_theme": theme,
        "results": results,
        "count": len(results),
    }


@router.post("/narrative/journey/start")
async def start_narrative_journey(
    user_id: str = Query(...),
    arc_id: str = Query(...),
):
    """
    Start a user's journey through a narrative arc.

    Arabic: بدء رحلة المستخدم عبر قوس سردي
    """
    from app.services.narrative_arc_service import narrative_arc_service

    result = narrative_arc_service.start_arc_journey(user_id, arc_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.post("/narrative/journey/advance")
async def advance_narrative_journey(
    user_id: str = Query(...),
    arc_id: str = Query(...),
):
    """
    Advance to the next segment in a narrative arc journey.

    Arabic: التقدم للجزء التالي في رحلة القوس السردي
    """
    from app.services.narrative_arc_service import narrative_arc_service

    result = narrative_arc_service.advance_arc_journey(user_id, arc_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/narrative/journey/progress")
async def get_narrative_journey_progress(
    user_id: str = Query(...),
):
    """
    Get user's progress across all narrative arc journeys.

    Arabic: تقدم المستخدم في جميع رحلات الأقواس السردية
    """
    from app.services.narrative_arc_service import narrative_arc_service

    return narrative_arc_service.get_user_arc_progress(user_id)


@router.get("/narrative/stats")
async def get_narrative_statistics():
    """
    Get statistics about all narrative arcs.

    Arabic: إحصائيات الأقواس السردية
    """
    from app.services.narrative_arc_service import narrative_arc_service

    return narrative_arc_service.get_narrative_statistics()


# =============================================================================
# CROSS-DISCIPLINARY KNOWLEDGE INTEGRATION (PHASE 7)
# =============================================================================


@router.get("/cross-discipline/verse/{sura_no}/{aya_no}")
async def get_verse_cross_references(
    sura_no: int,
    aya_no: int,
):
    """
    Get cross-disciplinary references for a verse (Fiqh, Hadith, Sira).

    Arabic: المراجع متعددة التخصصات لآية
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    verse_ref = f"{sura_no}:{aya_no}"
    return cross_disciplinary_service.get_verse_cross_references(verse_ref)


@router.get("/cross-discipline/fiqh")
async def get_all_fiqh_rulings(
    category: Optional[str] = Query(None, description="Filter by category: worship, dress, transactions, family"),
):
    """
    Get all Fiqh rulings.

    Categories: worship, dress, transactions, family

    Arabic: جميع الأحكام الفقهية
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    rulings = cross_disciplinary_service.get_all_fiqh_rulings(category=category)

    return {
        "fiqh_rulings": rulings,
        "count": len(rulings),
        "filter": category,
    }


@router.get("/cross-discipline/fiqh/{ruling_id}")
async def get_fiqh_ruling_details(
    ruling_id: str,
):
    """
    Get detailed Fiqh ruling with evidence and school positions.

    Arabic: تفاصيل الحكم الفقهي مع الأدلة ومواقف المذاهب
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    ruling = cross_disciplinary_service.get_fiqh_ruling(ruling_id)

    if not ruling:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Fiqh ruling '{ruling_id}' not found"},
        )

    return ruling


@router.get("/cross-discipline/fiqh/categories")
async def get_fiqh_categories():
    """
    Get all Fiqh categories.

    Arabic: فئات الفقه
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    categories = cross_disciplinary_service.get_fiqh_categories()

    return {
        "categories": categories,
        "count": len(categories),
    }


@router.get("/cross-discipline/hadith")
async def get_all_hadith(
    grade: Optional[str] = Query(None, description="Filter by grade: sahih, hasan, daif, mutawatir"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
):
    """
    Get all Hadith references.

    Arabic: جميع الأحاديث
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    hadith = cross_disciplinary_service.get_all_hadith(grade=grade, theme=theme)

    return {
        "hadith": hadith,
        "count": len(hadith),
        "filters": {"grade": grade, "theme": theme},
    }


@router.get("/cross-discipline/hadith/{hadith_id}")
async def get_hadith_details(
    hadith_id: str,
):
    """
    Get detailed Hadith information.

    Arabic: تفاصيل الحديث
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    hadith = cross_disciplinary_service.get_hadith_details(hadith_id)

    if not hadith:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Hadith '{hadith_id}' not found"},
        )

    return hadith


@router.get("/cross-discipline/hadith/themes")
async def get_hadith_themes():
    """
    Get all Hadith themes.

    Arabic: مواضيع الأحاديث
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    themes = cross_disciplinary_service.get_hadith_themes()

    return {
        "themes": themes,
        "count": len(themes),
    }


@router.get("/cross-discipline/sira")
async def get_all_sira_events(
    era: Optional[str] = Query(None, description="Filter by era: pre_prophethood, meccan, medinan, final_years"),
):
    """
    Get all Sira (Prophetic Biography) events.

    Arabic: جميع أحداث السيرة النبوية
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    events = cross_disciplinary_service.get_all_sira_events(era=era)

    return {
        "sira_events": events,
        "count": len(events),
        "filter": era,
    }


@router.get("/cross-discipline/sira/timeline")
async def get_sira_timeline():
    """
    Get Sira events as a chronological timeline.

    Arabic: السيرة النبوية كجدول زمني
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    timeline = cross_disciplinary_service.get_sira_timeline()

    return {
        "timeline": timeline,
        "count": len(timeline),
        "guidance_ar": "السيرة النبوية منهج حياة",
        "guidance_en": "The Prophetic biography is a way of life",
    }


@router.get("/cross-discipline/sira/{event_id}")
async def get_sira_event_details(
    event_id: str,
):
    """
    Get detailed Sira event information.

    Arabic: تفاصيل حدث من السيرة
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    event = cross_disciplinary_service.get_sira_event(event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Sira event '{event_id}' not found"},
        )

    return event


@router.get("/cross-discipline/sira/eras")
async def get_sira_eras():
    """
    Get all Sira eras with descriptions.

    Arabic: حقب السيرة النبوية
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    return {
        "eras": cross_disciplinary_service.get_sira_eras(),
    }


@router.get("/cross-discipline/search")
async def search_cross_discipline(
    topic: str = Query(..., description="Topic to search across all disciplines"),
):
    """
    Search across Fiqh, Hadith, and Sira by topic.

    Arabic: البحث عبر الفقه والحديث والسيرة
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    return cross_disciplinary_service.search_by_topic(topic)


@router.get("/cross-discipline/stats")
async def get_cross_discipline_statistics():
    """
    Get statistics about cross-disciplinary data.

    Arabic: إحصائيات البيانات متعددة التخصصات
    """
    from app.services.cross_disciplinary_service import cross_disciplinary_service

    return cross_disciplinary_service.get_statistics()


# =============================================================================
# CROWDSOURCED ANNOTATION SYSTEM (PHASE 7)
# =============================================================================


class AnnotationSubmitRequest(BaseModel):
    """Request to submit an annotation."""
    verse_reference: str = Field(..., description="Verse reference (e.g., '2:255')")
    annotation_type: str = Field(..., description="Type: reflection, explanation, linguistic, thematic, life_lesson, historical, connection, question")
    content_ar: str = Field(default="", description="Arabic content")
    content_en: str = Field(default="", description="English content")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags")


class AnnotationVoteRequest(BaseModel):
    """Request to vote on an annotation."""
    vote_type: str = Field(..., description="Vote type: helpful, insightful, accurate, well_written")


class AnnotationReviewRequest(BaseModel):
    """Request to review an annotation."""
    decision: str = Field(..., description="Decision: approve, reject, feature")
    feedback: Optional[str] = Field(default=None, description="Review feedback")


@router.post("/annotations/submit")
async def submit_annotation(
    request: AnnotationSubmitRequest,
    user_id: str = Query(..., description="User ID"),
):
    """
    Submit a new annotation for a verse.

    Features:
    - NLP-based quality analysis
    - Automatic theme detection
    - Sentiment analysis
    - Auto-approval for high-quality contributions

    Arabic: تقديم تعليق توضيحي جديد لآية
    """
    from app.services.annotation_service import annotation_service

    if not request.content_ar and not request.content_en:
        raise HTTPException(
            status_code=400,
            detail={"error": "Content in at least one language is required"},
        )

    return annotation_service.submit_annotation(
        user_id=user_id,
        verse_reference=request.verse_reference,
        annotation_type=request.annotation_type,
        content_ar=request.content_ar,
        content_en=request.content_en,
        tags=request.tags,
    )


@router.get("/annotations/verse/{sura_no}/{aya_no}")
async def get_verse_annotations(
    sura_no: int,
    aya_no: int,
    annotation_type: Optional[str] = Query(None, description="Filter by type"),
    status: str = Query("approved", description="Status: approved, featured, pending"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get annotations for a specific verse.

    Arabic: الحصول على التعليقات التوضيحية لآية
    """
    from app.services.annotation_service import annotation_service

    verse_ref = f"{sura_no}:{aya_no}"
    annotations = annotation_service.get_verse_annotations(
        verse_reference=verse_ref,
        annotation_type=annotation_type,
        status=status,
        limit=limit,
    )

    return {
        "verse_reference": verse_ref,
        "annotations": annotations,
        "count": len(annotations),
    }


@router.post("/annotations/{annotation_id}/vote")
async def vote_on_annotation(
    annotation_id: str,
    request: AnnotationVoteRequest,
    user_id: str = Query(..., description="User ID"),
):
    """
    Vote on an annotation.

    Vote types: helpful, insightful, accurate, well_written

    Arabic: التصويت على تعليق توضيحي
    """
    from app.services.annotation_service import annotation_service

    result = annotation_service.vote_on_annotation(
        annotation_id=annotation_id,
        user_id=user_id,
        vote_type=request.vote_type,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/annotations/user/{user_id}")
async def get_user_annotations(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get all annotations by a user.

    Arabic: الحصول على تعليقات المستخدم
    """
    from app.services.annotation_service import annotation_service

    return {
        "user_id": user_id,
        "annotations": annotation_service.get_user_annotations(user_id, limit),
    }


@router.get("/annotations/user/{user_id}/profile")
async def get_contributor_profile(
    user_id: str,
):
    """
    Get contributor profile with reputation and statistics.

    Arabic: ملف المساهم مع السمعة والإحصائيات
    """
    from app.services.annotation_service import annotation_service

    return annotation_service.get_user_contributor_profile(user_id)


@router.get("/annotations/featured")
async def get_featured_annotations(
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get featured (highest quality) annotations.

    Arabic: التعليقات المميزة (الأعلى جودة)
    """
    from app.services.annotation_service import annotation_service

    annotations = annotation_service.get_featured_annotations(limit)

    return {
        "featured_annotations": annotations,
        "count": len(annotations),
    }


@router.get("/annotations/by-theme/{theme}")
async def get_annotations_by_theme(
    theme: str,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get annotations containing a specific theme.

    Arabic: التعليقات التي تحتوي على موضوع معين
    """
    from app.services.annotation_service import annotation_service

    annotations = annotation_service.get_annotations_by_theme(theme, limit)

    return {
        "theme": theme,
        "annotations": annotations,
        "count": len(annotations),
    }


@router.get("/annotations/pending-reviews")
async def get_pending_reviews(
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get annotations pending review (moderator endpoint).

    Arabic: التعليقات في انتظار المراجعة
    """
    from app.services.annotation_service import annotation_service

    return {
        "pending_reviews": annotation_service.get_pending_reviews(limit),
    }


@router.post("/annotations/{annotation_id}/review")
async def review_annotation(
    annotation_id: str,
    request: AnnotationReviewRequest,
    reviewer_id: str = Query(..., description="Reviewer/Moderator ID"),
):
    """
    Review and approve/reject an annotation (moderator action).

    Arabic: مراجعة تعليق والموافقة عليه أو رفضه
    """
    from app.services.annotation_service import annotation_service

    result = annotation_service.review_annotation(
        annotation_id=annotation_id,
        reviewer_id=reviewer_id,
        decision=request.decision,
        feedback=request.feedback,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/annotations/types")
async def get_annotation_types():
    """
    Get all available annotation types.

    Arabic: أنواع التعليقات المتاحة
    """
    from app.services.annotation_service import annotation_service

    return {
        "annotation_types": annotation_service.get_annotation_types(),
    }


@router.get("/annotations/top-contributors")
async def get_top_contributors(
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get top contributors by reputation.

    Arabic: أفضل المساهمين حسب السمعة
    """
    from app.services.annotation_service import annotation_service

    return {
        "top_contributors": annotation_service.get_top_contributors(limit),
    }


@router.get("/annotations/stats")
async def get_annotation_statistics():
    """
    Get statistics about the annotation system.

    Arabic: إحصائيات نظام التعليقات
    """
    from app.services.annotation_service import annotation_service

    return annotation_service.get_annotation_statistics()


# =============================================================================
# ENTITY RELATIONSHIPS (PHASE 8)
# =============================================================================


@router.get("/ner/relationships/{entity_name}")
async def get_entity_relationships(
    entity_name: str,
):
    """
    Get all relationships for an entity (family, parallels, place connections).

    Arabic: جميع العلاقات لكيان (أسرة، تجارب متوازية، روابط مكانية)
    """
    from app.services.ner_service import entity_relationship_service

    return entity_relationship_service.get_entity_relationships(entity_name)


@router.get("/ner/parallel-experiences/{prophet_name}")
async def get_parallel_experiences(
    prophet_name: str,
):
    """
    Get prophets with parallel experiences to the given prophet.

    Arabic: الأنبياء ذوو التجارب المتوازية مع النبي المحدد
    """
    from app.services.ner_service import entity_relationship_service

    parallels = entity_relationship_service.get_parallel_experiences(prophet_name)

    return {
        "prophet": prophet_name,
        "parallel_experiences": parallels,
        "count": len(parallels),
    }


@router.get("/ner/thematic-parallels")
async def get_thematic_parallels(
    theme: Optional[str] = Query(None, description="Filter by theme"),
):
    """
    Get thematic parallels between prophets.

    Arabic: التوازيات الموضوعية بين الأنبياء
    """
    from app.services.ner_service import entity_relationship_service

    parallels = entity_relationship_service.get_thematic_parallels(theme)

    return {
        "thematic_parallels": parallels,
        "count": len(parallels),
        "filter": theme,
    }


@router.get("/ner/prophets-by-theme/{theme_id}")
async def get_prophets_by_thematic_parallel(
    theme_id: str,
):
    """
    Get prophets associated with a thematic parallel (e.g., patience_under_trial).

    Arabic: الأنبياء المرتبطون بموضوع معين
    """
    from app.services.ner_service import entity_relationship_service

    result = entity_relationship_service.get_prophets_by_theme(theme_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Theme '{theme_id}' not found"},
        )

    return result


@router.get("/ner/relationship-graph")
async def get_entity_relationship_graph():
    """
    Get data for visualizing entity relationships as an interactive graph.

    Arabic: بيانات لتصور علاقات الكيانات كرسم بياني تفاعلي
    """
    from app.services.ner_service import entity_relationship_service

    return entity_relationship_service.get_relationship_graph()


@router.get("/ner/connection-path")
async def find_entity_connection_path(
    entity1: str = Query(..., description="First entity name (Arabic)"),
    entity2: str = Query(..., description="Second entity name (Arabic)"),
    max_depth: int = Query(3, ge=1, le=5),
):
    """
    Find connection path between two entities using graph traversal.

    Arabic: إيجاد مسار الاتصال بين كيانين
    """
    from app.services.ner_service import entity_relationship_service

    return entity_relationship_service.find_connection_path(
        entity1=entity1,
        entity2=entity2,
        max_depth=max_depth,
    )


@router.get("/ner/relationship-stats")
async def get_entity_relationship_statistics():
    """
    Get statistics about entity relationships.

    Arabic: إحصائيات علاقات الكيانات
    """
    from app.services.ner_service import entity_relationship_service

    return entity_relationship_service.get_relationship_statistics()


# =============================================================================
# MULTI-DISCIPLINARY LEARNING PATHS (PHASE 8)
# =============================================================================


@router.get("/learning-paths")
async def get_all_learning_paths(
    category: Optional[str] = Query(None, description="Filter by category: foundational, thematic, prophet_study, jurisprudence, spirituality, research"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: beginner, intermediate, advanced, scholar"),
):
    """
    Get all available multi-disciplinary learning paths.

    These paths guide users through cross-disciplinary exploration
    integrating Fiqh, Hadith, Tafsir, Sira, and thematic studies.

    Arabic: الحصول على جميع مسارات التعلم متعددة التخصصات
    """
    from app.services.learning_path_service import learning_path_service

    paths = learning_path_service.get_all_paths(
        category=category,
        difficulty=difficulty,
    )

    return {
        "paths": paths,
        "count": len(paths),
        "filter": {
            "category": category,
            "difficulty": difficulty,
        },
    }


@router.get("/learning-paths/categories")
async def get_learning_path_categories():
    """
    Get all available learning path categories.

    Arabic: أقسام مسارات التعلم المتاحة
    """
    from app.services.learning_path_service import learning_path_service

    return {
        "categories": learning_path_service.get_path_categories(),
    }


@router.get("/learning-paths/difficulties")
async def get_learning_path_difficulties():
    """
    Get all difficulty levels with descriptions.

    Arabic: مستويات الصعوبة مع الوصف
    """
    from app.services.learning_path_service import learning_path_service

    return {
        "difficulty_levels": learning_path_service.get_difficulty_levels(),
    }


@router.get("/learning-paths/stats")
async def get_learning_paths_statistics():
    """
    Get statistics about the learning path system.

    Arabic: إحصائيات نظام مسارات التعلم
    """
    from app.services.learning_path_service import learning_path_service

    return learning_path_service.get_statistics()


@router.get("/learning-paths/{path_id}")
async def get_learning_path_details(
    path_id: str,
):
    """
    Get detailed information about a specific learning path.

    Returns modules, lessons, duration, and learning outcomes.

    Arabic: معلومات تفصيلية عن مسار تعلم محدد
    """
    from app.services.learning_path_service import learning_path_service

    path = learning_path_service.get_path_details(path_id)

    if not path:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Learning path '{path_id}' not found"},
        )

    return path


@router.get("/learning-paths/{path_id}/modules/{module_id}/lessons/{lesson_id}")
async def get_lesson_content(
    path_id: str,
    module_id: str,
    lesson_id: str,
):
    """
    Get detailed content for a specific lesson.

    Returns lesson content, objectives, and resources.

    Arabic: محتوى الدرس التفصيلي
    """
    from app.services.learning_path_service import learning_path_service

    lesson = learning_path_service.get_lesson_content(
        path_id=path_id,
        module_id=module_id,
        lesson_id=lesson_id,
    )

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail={"error": "Lesson not found"},
        )

    return lesson


@router.post("/learning-paths/{path_id}/enroll")
async def enroll_in_learning_path(
    path_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """
    Enroll a user in a learning path.

    Arabic: تسجيل المستخدم في مسار تعلم
    """
    from app.services.learning_path_service import learning_path_service

    result = learning_path_service.enroll_in_path(
        user_id=user_id,
        path_id=path_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.post("/learning-paths/{path_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    path_id: str,
    lesson_id: str,
    user_id: str = Query(..., description="User ID"),
):
    """
    Mark a lesson as complete.

    Arabic: تحديد الدرس كمكتمل
    """
    from app.services.learning_path_service import learning_path_service

    result = learning_path_service.complete_lesson(
        user_id=user_id,
        path_id=path_id,
        lesson_id=lesson_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/learning-paths/user/{user_id}/progress")
async def get_user_learning_progress(
    user_id: str,
    path_id: Optional[str] = Query(None, description="Filter by specific path"),
):
    """
    Get user's progress in learning paths.

    Arabic: تقدم المستخدم في مسارات التعلم
    """
    from app.services.learning_path_service import learning_path_service

    progress = learning_path_service.get_user_progress(
        user_id=user_id,
        path_id=path_id,
    )

    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress)

    return progress


@router.get("/learning-paths/user/{user_id}/recommendations")
async def get_recommended_learning_paths(
    user_id: str,
    interests: Optional[List[str]] = Query(None, description="User interests (e.g., patience, prophets, fiqh)"),
    difficulty: Optional[str] = Query(None, description="Preferred difficulty level"),
):
    """
    Get personalized learning path recommendations.

    Arabic: توصيات مسارات التعلم المخصصة
    """
    from app.services.learning_path_service import learning_path_service

    recommendations = learning_path_service.get_recommended_paths(
        user_id=user_id,
        interests=interests,
        difficulty=difficulty,
    )

    return {
        "user_id": user_id,
        "recommendations": recommendations,
        "count": len(recommendations),
        "message_ar": "مسارات موصى بها بناءً على اهتماماتك",
        "message_en": "Recommended paths based on your interests",
    }


# =============================================================================
# CROSS-STORY SEARCH (PHASE 8)
# =============================================================================


@router.get("/cross-story-search")
async def cross_story_search(
    query: str = Query(..., min_length=2, description="Search query"),
    search_type: str = Query("all", description="Type: all, theme, event, lesson"),
):
    """
    Search across all prophet stories for themes, events, or lessons.

    Enables discovering connections between stories and common themes.

    Arabic: البحث عبر جميع قصص الأنبياء عن المواضيع والأحداث والدروس
    """
    from app.services.narrative_arc_service import cross_story_search_service

    return cross_story_search_service.cross_story_search(
        query=query,
        search_type=search_type,
    )


@router.get("/cross-story-search/parallel-themes")
async def get_all_parallel_themes():
    """
    Get all available parallel experience themes for prophet comparison.

    Arabic: جميع المواضيع المتوازية المتاحة لمقارنة الأنبياء
    """
    from app.services.narrative_arc_service import cross_story_search_service

    themes = cross_story_search_service.get_all_parallel_themes()

    return {
        "parallel_themes": themes,
        "count": len(themes),
    }


@router.get("/cross-story-search/parallel-experiences/{theme_id}")
async def get_parallel_experiences(
    theme_id: str,
):
    """
    Get prophets' parallel experiences for a specific theme.

    Shows how different prophets handled similar situations.

    Arabic: التجارب المتوازية للأنبياء في موضوع معين
    """
    from app.services.narrative_arc_service import cross_story_search_service

    result = cross_story_search_service.get_parallel_experiences(theme_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Theme '{theme_id}' not found"},
        )

    return result


@router.get("/cross-story-search/compare-prophets")
async def compare_prophets(
    prophet1: str = Query(..., description="First prophet name (Arabic)"),
    prophet2: str = Query(..., description="Second prophet name (Arabic)"),
):
    """
    Compare two prophets across all parallel themes.

    Arabic: مقارنة نبيين عبر جميع المواضيع المتوازية
    """
    from app.services.narrative_arc_service import cross_story_search_service

    return cross_story_search_service.compare_prophets(
        prophet1=prophet1,
        prophet2=prophet2,
    )


@router.get("/cross-story-search/story-connections/{arc_id}")
async def get_story_connections(
    arc_id: str,
):
    """
    Get all connections from a story to other stories.

    Shows cross-references, shared themes, and parallel experiences.

    Arabic: جميع الروابط من قصة إلى قصص أخرى
    """
    from app.services.narrative_arc_service import cross_story_search_service

    result = cross_story_search_service.get_story_connections(arc_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.post("/cross-story-search/journey/start")
async def start_multi_story_journey(
    user_id: str = Query(..., description="User ID"),
    theme_id: str = Query(..., description="Theme ID (e.g., patience_under_trial)"),
):
    """
    Start a journey through multiple stories connected by a theme.

    Arabic: بدء رحلة عبر قصص متعددة مرتبطة بموضوع
    """
    from app.services.narrative_arc_service import cross_story_search_service

    result = cross_story_search_service.start_multi_story_journey(
        user_id=user_id,
        theme_id=theme_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.post("/cross-story-search/journey/advance")
async def advance_multi_story_journey(
    user_id: str = Query(..., description="User ID"),
    insight: Optional[str] = Query(None, description="Personal insight from current prophet's story"),
):
    """
    Advance to the next prophet in a multi-story journey.

    Arabic: التقدم إلى النبي التالي في الرحلة
    """
    from app.services.narrative_arc_service import cross_story_search_service

    result = cross_story_search_service.advance_multi_story_journey(
        user_id=user_id,
        insight=insight,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/cross-story-search/journey/status/{user_id}")
async def get_multi_story_journey_status(
    user_id: str,
):
    """
    Get user's current multi-story journey status.

    Arabic: حالة رحلة المستخدم الحالية
    """
    from app.services.narrative_arc_service import cross_story_search_service

    return cross_story_search_service.get_user_journey_status(user_id)


# =============================================================================
# EXPERT ANNOTATION SYSTEM (PHASE 8)
# =============================================================================


@router.get("/expert/scholars")
async def get_verified_scholars():
    """
    Get all verified scholars.

    Arabic: جميع العلماء المعتمدين
    """
    from app.services.annotation_service import expert_annotation_service

    return {
        "scholars": expert_annotation_service.get_all_verified_scholars(),
    }


@router.get("/expert/scholars/{scholar_id}")
async def get_scholar_profile(
    scholar_id: str,
):
    """
    Get detailed scholar profile.

    Arabic: الملف الشخصي المفصل للعالم
    """
    from app.services.annotation_service import expert_annotation_service

    profile = expert_annotation_service.get_scholar_profile(scholar_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail={"error": "Scholar not found"},
        )

    return profile


class ScholarRegistrationRequest(BaseModel):
    name_ar: str
    name_en: str
    credentials: List[str]
    institution: str
    specializations: List[str]
    bio_ar: str = ""
    bio_en: str = ""


@router.post("/expert/scholars/register")
async def register_scholar(
    scholar_id: str = Query(..., description="Unique scholar ID"),
    request: ScholarRegistrationRequest = None,
):
    """
    Register a new scholar (pending verification).

    Arabic: تسجيل عالم جديد (في انتظار التحقق)
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.register_scholar(
        scholar_id=scholar_id,
        name_ar=request.name_ar,
        name_en=request.name_en,
        credentials=request.credentials,
        institution=request.institution,
        specializations=request.specializations,
        bio_ar=request.bio_ar,
        bio_en=request.bio_en,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.post("/expert/scholars/{scholar_id}/verify")
async def verify_scholar(
    scholar_id: str,
    verifier_id: str = Query(..., description="Admin/verifier ID"),
):
    """
    Verify a scholar's credentials (admin action).

    Arabic: التحقق من أوراق اعتماد العالم
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.verify_scholar(
        scholar_id=scholar_id,
        verifier_id=verifier_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


class ExpertAnnotationRequest(BaseModel):
    verse_reference: str
    annotation_type: str
    content_ar: str
    content_en: str
    tags: Optional[List[str]] = None
    requires_peer_review: bool = True


@router.post("/expert/annotations/submit")
async def submit_expert_annotation(
    scholar_id: str = Query(..., description="Scholar ID"),
    request: ExpertAnnotationRequest = None,
):
    """
    Submit an expert annotation from a verified scholar.

    Arabic: تقديم تعليق خبير من عالم معتمد
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.submit_expert_annotation(
        scholar_id=scholar_id,
        verse_reference=request.verse_reference,
        annotation_type=request.annotation_type,
        content_ar=request.content_ar,
        content_en=request.content_en,
        tags=request.tags,
        requires_peer_review=request.requires_peer_review,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/expert/annotations")
async def get_expert_annotations(
    verse_reference: Optional[str] = Query(None, description="Filter by verse"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get expert-contributed annotations.

    Arabic: التعليقات المقدمة من الخبراء
    """
    from app.services.annotation_service import expert_annotation_service

    annotations = expert_annotation_service.get_expert_annotations(
        verse_reference=verse_reference,
        limit=limit,
    )

    return {
        "annotations": annotations,
        "count": len(annotations),
    }


class PeerReviewRequest(BaseModel):
    accuracy_score: float
    depth_score: float
    relevance_score: float
    suggestions_ar: str = ""
    suggestions_en: str = ""
    verdict: str = "approve"


@router.post("/expert/peer-review/{annotation_id}")
async def submit_peer_review(
    annotation_id: str,
    reviewer_id: str = Query(..., description="Reviewer (scholar) ID"),
    request: PeerReviewRequest = None,
):
    """
    Submit a peer review for an annotation.

    Arabic: تقديم مراجعة من الأقران لتعليق
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.submit_peer_review(
        annotation_id=annotation_id,
        reviewer_id=reviewer_id,
        accuracy_score=request.accuracy_score,
        depth_score=request.depth_score,
        relevance_score=request.relevance_score,
        suggestions_ar=request.suggestions_ar,
        suggestions_en=request.suggestions_en,
        verdict=request.verdict,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/expert/peer-reviews/{annotation_id}")
async def get_annotation_peer_reviews(
    annotation_id: str,
):
    """
    Get all peer reviews for an annotation.

    Arabic: جميع مراجعات الأقران لتعليق
    """
    from app.services.annotation_service import expert_annotation_service

    return expert_annotation_service.get_annotation_peer_reviews(annotation_id)


@router.get("/expert/peer-reviews/pending")
async def get_pending_peer_reviews(
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get annotations pending peer review.

    Arabic: التعليقات في انتظار مراجعة الأقران
    """
    from app.services.annotation_service import expert_annotation_service

    return {
        "pending_reviews": expert_annotation_service.get_pending_peer_reviews(limit),
    }


class EndorsementRequest(BaseModel):
    endorsement_type: str
    comment_ar: str = ""
    comment_en: str = ""


@router.post("/expert/endorse/{annotation_id}")
async def endorse_annotation(
    annotation_id: str,
    scholar_id: str = Query(..., description="Scholar ID"),
    request: EndorsementRequest = None,
):
    """
    Scholar endorses an annotation.

    Arabic: تأييد العالم لتعليق
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.endorse_annotation(
        annotation_id=annotation_id,
        scholar_id=scholar_id,
        endorsement_type=request.endorsement_type,
        comment_ar=request.comment_ar,
        comment_en=request.comment_en,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/expert/endorsements/{annotation_id}")
async def get_annotation_endorsements(
    annotation_id: str,
):
    """
    Get all endorsements for an annotation.

    Arabic: جميع التأييدات لتعليق
    """
    from app.services.annotation_service import expert_annotation_service

    result = expert_annotation_service.get_annotation_endorsements(annotation_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.get("/expert/endorsement-types")
async def get_endorsement_types():
    """
    Get all endorsement types.

    Arabic: أنواع التأييدات
    """
    from app.services.annotation_service import expert_annotation_service

    return {
        "endorsement_types": expert_annotation_service.get_endorsement_types(),
    }


@router.get("/expert/credential-types")
async def get_credential_types():
    """
    Get all scholar credential types.

    Arabic: أنواع أوراق اعتماد العلماء
    """
    from app.services.annotation_service import expert_annotation_service

    return {
        "credential_types": expert_annotation_service.get_credential_types(),
    }


@router.get("/expert/stats")
async def get_expert_statistics():
    """
    Get statistics about the expert annotation system.

    Arabic: إحصائيات نظام التعليقات الخبيرة
    """
    from app.services.annotation_service import expert_annotation_service

    return expert_annotation_service.get_expert_statistics()


# =============================================================================
# KNOWLEDGE GRAPH (PHASE 8)
# =============================================================================


@router.get("/knowledge-graph/stats")
async def get_knowledge_graph_statistics():
    """
    Get statistics about the knowledge graph.

    Arabic: إحصائيات الرسم البياني المعرفي
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    return knowledge_graph_service.get_statistics()


@router.get("/knowledge-graph/timeline/eras")
async def get_historical_eras():
    """
    Get all historical eras in Islamic history.

    Arabic: جميع العصور التاريخية في التاريخ الإسلامي
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    return {
        "eras": knowledge_graph_service.get_all_eras(),
    }


@router.get("/knowledge-graph/timeline/eras/{era_id}")
async def get_era_details(
    era_id: str,
):
    """
    Get detailed information about a historical era.

    Arabic: معلومات تفصيلية عن عصر تاريخي
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    details = knowledge_graph_service.get_era_details(era_id)

    if not details:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Era '{era_id}' not found"},
        )

    return details


@router.get("/knowledge-graph/timeline/complete")
async def get_complete_timeline():
    """
    Get complete timeline of events across all eras.

    Arabic: الجدول الزمني الكامل للأحداث عبر جميع العصور
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    timeline = knowledge_graph_service.get_complete_timeline()

    return {
        "timeline": timeline,
        "count": len(timeline),
    }


@router.get("/knowledge-graph/timeline/search")
async def search_timeline(
    query: str = Query(..., min_length=2, description="Search query"),
):
    """
    Search timeline for events matching query.

    Arabic: البحث في الجدول الزمني عن أحداث مطابقة
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    results = knowledge_graph_service.search_timeline(query)

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


@router.get("/knowledge-graph/timeline/by-figure/{figure_name}")
async def get_events_by_figure(
    figure_name: str,
):
    """
    Get all events involving a specific figure.

    Arabic: جميع الأحداث التي تتضمن شخصية معينة
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    events = knowledge_graph_service.get_events_by_figure(figure_name)

    return {
        "figure": figure_name,
        "events": events,
        "count": len(events),
    }


@router.get("/knowledge-graph/nodes")
async def get_all_graph_nodes(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    era: Optional[str] = Query(None, description="Filter by era"),
):
    """
    Get all nodes in the knowledge graph.

    Arabic: جميع العقد في الرسم البياني المعرفي
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    nodes = knowledge_graph_service.get_all_nodes(
        entity_type=entity_type,
        era=era,
    )

    return {
        "nodes": nodes,
        "count": len(nodes),
        "filter": {"entity_type": entity_type, "era": era},
    }


@router.get("/knowledge-graph/nodes/{node_id}")
async def get_graph_node(
    node_id: str,
):
    """
    Get a specific node by ID.

    Arabic: الحصول على عقدة محددة بواسطة المعرف
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    node = knowledge_graph_service.get_node(node_id)

    if not node:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Node '{node_id}' not found"},
        )

    return node


@router.get("/knowledge-graph/nodes/{node_id}/connections")
async def get_node_connections(
    node_id: str,
):
    """
    Get all connections for a node.

    Arabic: جميع الاتصالات لعقدة
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    result = knowledge_graph_service.get_node_connections(node_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.get("/knowledge-graph/path")
async def find_graph_path(
    start: str = Query(..., description="Starting node ID"),
    end: str = Query(..., description="Ending node ID"),
    max_depth: int = Query(5, ge=1, le=10),
):
    """
    Find path between two nodes.

    Arabic: إيجاد مسار بين عقدتين
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    result = knowledge_graph_service.find_path(
        start_id=start,
        end_id=end,
        max_depth=max_depth,
    )

    if not result:
        return {
            "path_found": False,
            "message": f"No path found between {start} and {end} within depth {max_depth}",
        }

    return {
        "path_found": True,
        **result,
    }


@router.get("/knowledge-graph/explore/{node_id}")
async def explore_from_node(
    node_id: str,
    depth: int = Query(2, ge=1, le=4),
):
    """
    Explore the graph from a starting node to a given depth.

    Arabic: استكشاف الرسم البياني من عقدة بداية إلى عمق معين
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    result = knowledge_graph_service.explore_from_node(
        node_id=node_id,
        depth=depth,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.get("/knowledge-graph/visualization")
async def get_graph_visualization_data():
    """
    Get data formatted for graph visualization.

    Arabic: بيانات منسقة لتصور الرسم البياني
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    return knowledge_graph_service.get_graph_visualization_data()


@router.get("/knowledge-graph/entity-types")
async def get_entity_types():
    """
    Get all entity types in the knowledge graph.

    Arabic: جميع أنواع الكيانات في الرسم البياني
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    return {
        "entity_types": knowledge_graph_service.get_entity_types(),
    }


@router.get("/knowledge-graph/relation-types")
async def get_relation_types():
    """
    Get all relation types in the knowledge graph.

    Arabic: جميع أنواع العلاقات في الرسم البياني
    """
    from app.services.knowledge_graph_service import knowledge_graph_service

    return {
        "relation_types": knowledge_graph_service.get_relation_types(),
    }


# =============================================================================
# SEMANTIC SEARCH (PHASE 9)
# =============================================================================


@router.get("/semantic-search/themes")
async def get_available_themes():
    """
    Get all available themes for semantic search.

    Arabic: جميع المواضيع المتاحة للبحث الدلالي
    """
    from app.services.semantic_search_service import semantic_search_service

    return {
        "themes": semantic_search_service.get_available_themes(),
    }


@router.get("/semantic-search/similar-themes/{theme}")
async def find_similar_themes(
    theme: str,
    top_n: int = Query(5, ge=1, le=10),
):
    """
    Find themes semantically similar to the given theme.

    Arabic: إيجاد مواضيع مشابهة دلالياً للموضوع المحدد
    """
    from app.services.semantic_search_service import semantic_search_service

    return {
        "theme": theme,
        "similar_themes": semantic_search_service.find_similar_themes(theme, top_n),
    }


@router.get("/semantic-search/similar-stories/{prophet}")
async def find_similar_prophet_stories(
    prophet: str,
    similarity_type: str = Query("all", description="Type: all, thematic, moral, narrative"),
):
    """
    Find prophet stories similar to the given prophet's story.

    Arabic: إيجاد قصص أنبياء مشابهة لقصة النبي المحدد
    """
    from app.services.semantic_search_service import semantic_search_service

    results = semantic_search_service.find_similar_prophet_stories(prophet, similarity_type)

    return {
        "prophet": prophet,
        "similar_stories": results,
        "count": len(results),
    }


@router.get("/semantic-search/expand-query")
async def expand_search_query(
    query: str = Query(..., min_length=2),
    expansion_type: str = Query("semantic", description="Type: semantic, synonym, thematic"),
):
    """
    Expand query with semantically related terms.

    Arabic: توسيع الاستعلام بمصطلحات مرتبطة دلالياً
    """
    from app.services.semantic_search_service import semantic_search_service

    return semantic_search_service.expand_query(query, expansion_type)


@router.get("/semantic-search/user-preferences/{user_id}")
async def get_user_theme_preferences(
    user_id: str,
):
    """
    Get user's theme preferences based on search history.

    Arabic: تفضيلات المواضيع للمستخدم بناءً على سجل البحث
    """
    from app.services.semantic_search_service import semantic_search_service

    return semantic_search_service.get_user_theme_preferences(user_id)


@router.get("/semantic-search/stats")
async def get_semantic_search_statistics():
    """
    Get semantic search service statistics.

    Arabic: إحصائيات خدمة البحث الدلالي
    """
    from app.services.semantic_search_service import semantic_search_service

    return semantic_search_service.get_statistics()


# =============================================================================
# PERSONALIZATION (PHASE 9)
# =============================================================================


@router.post("/personalization/profile/create")
async def create_user_profile(
    user_id: str = Query(..., description="User ID"),
    preferred_language: str = Query("en", description="Preferred language: en, ar"),
    initial_level: str = Query("beginner", description="Level: beginner, intermediate, advanced"),
    daily_goal_minutes: int = Query(15, ge=5, le=120),
):
    """
    Create a new user profile for personalization.

    Arabic: إنشاء ملف شخصي جديد للمستخدم للتخصيص
    """
    from app.services.personalization_service import personalization_service

    result = personalization_service.create_user_profile(
        user_id=user_id,
        preferred_language=preferred_language,
        initial_level=initial_level,
        daily_goal_minutes=daily_goal_minutes,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/personalization/profile/{user_id}")
async def get_personalization_profile(
    user_id: str,
):
    """
    Get user's personalization profile.

    Arabic: الحصول على ملف التخصيص للمستخدم
    """
    from app.services.personalization_service import personalization_service

    profile = personalization_service.get_user_profile(user_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail={"error": "User not found"},
        )

    return profile


class InteractionRequest(BaseModel):
    content_type: str
    content_id: str
    metadata: Optional[Dict[str, Any]] = None
    duration_seconds: int = 0


@router.post("/personalization/record-interaction")
async def record_user_interaction(
    user_id: str = Query(..., description="User ID"),
    interaction_type: str = Query(..., description="Type: search, view, save, complete_lesson, annotation"),
    request: InteractionRequest = None,
):
    """
    Record a user interaction for learning preferences.

    Arabic: تسجيل تفاعل المستخدم لتعلم التفضيلات
    """
    from app.services.personalization_service import personalization_service

    result = personalization_service.record_interaction(
        user_id=user_id,
        interaction_type=interaction_type,
        content_type=request.content_type,
        content_id=request.content_id,
        metadata=request.metadata,
        duration_seconds=request.duration_seconds,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/personalization/recommendations/{user_id}")
async def get_personalized_recommendations(
    user_id: str,
    content_types: Optional[List[str]] = Query(None, description="Filter by content types"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get personalized content recommendations.

    Arabic: الحصول على توصيات محتوى مخصصة
    """
    from app.services.personalization_service import personalization_service

    return personalization_service.get_recommendations(
        user_id=user_id,
        content_types=content_types,
        limit=limit,
    )


@router.get("/personalization/daily/{user_id}")
async def get_daily_recommendations(
    user_id: str,
):
    """
    Get daily personalized recommendations.

    Arabic: الحصول على التوصيات اليومية المخصصة
    """
    from app.services.personalization_service import personalization_service

    return personalization_service.get_daily_recommendations(user_id)


@router.get("/personalization/insights/{user_id}")
async def get_study_insights(
    user_id: str,
):
    """
    Get study insights and analytics for user.

    Arabic: الحصول على رؤى وتحليلات الدراسة للمستخدم
    """
    from app.services.personalization_service import personalization_service

    result = personalization_service.get_study_insights(user_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result)

    return result


@router.get("/personalization/next-study/{user_id}")
async def suggest_next_study(
    user_id: str,
):
    """
    Suggest what to study next based on user's journey.

    Arabic: اقتراح ما يجب دراسته بعد ذلك بناءً على رحلة المستخدم
    """
    from app.services.personalization_service import personalization_service

    return personalization_service.suggest_next_study(user_id)


@router.get("/personalization/stats")
async def get_personalization_statistics():
    """
    Get personalization service statistics.

    Arabic: إحصائيات خدمة التخصيص
    """
    from app.services.personalization_service import personalization_service

    return personalization_service.get_statistics()


# =============================================================================
# ADAPTIVE QUIZ SYSTEM (PHASE 9)
# =============================================================================


@router.post("/quiz/start")
async def start_quiz(
    user_id: str = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Quiz category"),
    num_questions: int = Query(5, ge=3, le=20),
    difficulty: Optional[str] = Query(None, description="Difficulty: easy, medium, hard, expert"),
):
    """
    Start a new quiz session.

    Arabic: بدء جلسة اختبار جديدة
    """
    from app.services.quiz_service import quiz_service

    result = quiz_service.start_quiz(
        user_id=user_id,
        category=category,
        num_questions=num_questions,
        difficulty=difficulty,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


class QuizAnswerRequest(BaseModel):
    answer_index: int
    time_taken_seconds: int = 0


@router.post("/quiz/{session_id}/answer")
async def submit_quiz_answer(
    session_id: str,
    request: QuizAnswerRequest,
):
    """
    Submit answer for current question.

    Arabic: تقديم إجابة للسؤال الحالي
    """
    from app.services.quiz_service import quiz_service

    result = quiz_service.submit_answer(
        session_id=session_id,
        answer_index=request.answer_index,
        time_taken_seconds=request.time_taken_seconds,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/quiz/profile/{user_id}")
async def get_quiz_profile(
    user_id: str,
):
    """
    Get user's quiz profile and statistics.

    Arabic: الحصول على ملف الاختبار وإحصائيات المستخدم
    """
    from app.services.quiz_service import quiz_service

    return quiz_service.get_user_quiz_profile(user_id)


@router.post("/quiz/practice")
async def get_practice_quiz(
    user_id: str = Query(..., description="User ID"),
    focus_weak_areas: bool = Query(True, description="Focus on weak areas"),
    num_questions: int = Query(5, ge=3, le=10),
):
    """
    Get a personalized practice quiz focusing on weak areas.

    Arabic: الحصول على اختبار تدريبي مخصص يركز على نقاط الضعف
    """
    from app.services.quiz_service import quiz_service

    result = quiz_service.get_practice_quiz(
        user_id=user_id,
        focus_weak_areas=focus_weak_areas,
        num_questions=num_questions,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/quiz/categories")
async def get_quiz_categories():
    """
    Get all available quiz categories.

    Arabic: الحصول على جميع فئات الاختبارات المتاحة
    """
    from app.services.quiz_service import quiz_service

    return {
        "categories": quiz_service.get_quiz_categories(),
    }


@router.get("/quiz/difficulties")
async def get_quiz_difficulties():
    """
    Get all difficulty levels.

    Arabic: الحصول على جميع مستويات الصعوبة
    """
    from app.services.quiz_service import quiz_service

    return {
        "difficulty_levels": quiz_service.get_difficulty_levels(),
    }


@router.get("/quiz/stats")
async def get_quiz_statistics():
    """
    Get quiz service statistics.

    Arabic: إحصائيات خدمة الاختبارات
    """
    from app.services.quiz_service import quiz_service

    return quiz_service.get_statistics()


# =============================================================================
# Multi-School Tafsir Comparison API Endpoints
# مقارنة التفاسير من مختلف المدارس الفكرية
# =============================================================================


@router.get("/tafsir/scholars")
async def get_all_tafsir_scholars():
    """
    Get all tafsir scholars across different schools of thought.

    Arabic: الحصول على جميع علماء التفسير من مختلف المذاهب
    """
    from app.services.tafsir_service import tafsir_service

    return {
        "scholars": tafsir_service.get_all_scholars(),
        "total": len(tafsir_service.get_all_scholars()),
    }


@router.get("/tafsir/scholars/{scholar_id}")
async def get_tafsir_scholar(scholar_id: str):
    """
    Get detailed information about a specific tafsir scholar.

    Arabic: الحصول على معلومات تفصيلية عن عالم تفسير معين
    """
    from app.services.tafsir_service import tafsir_service

    scholar = tafsir_service.get_scholar(scholar_id)
    if not scholar:
        raise HTTPException(status_code=404, detail="Scholar not found")

    return scholar


@router.get("/tafsir/schools")
async def get_schools_of_thought():
    """
    Get all Islamic schools of thought represented in tafsir.

    Arabic: الحصول على جميع المذاهب الإسلامية الممثلة في التفسير
    """
    from app.services.tafsir_service import tafsir_service

    return {
        "schools": tafsir_service.get_schools_of_thought(),
    }


@router.get("/tafsir/schools/{school_id}/scholars")
async def get_scholars_by_school(school_id: str):
    """
    Get all scholars belonging to a specific school of thought.

    Arabic: الحصول على جميع العلماء المنتمين لمذهب معين
    """
    from app.services.tafsir_service import tafsir_service

    scholars = tafsir_service.get_scholars_by_school(school_id)
    return {
        "school": school_id,
        "scholars": scholars,
        "total": len(scholars),
    }


@router.get("/tafsir/methodologies")
async def get_tafsir_methodologies():
    """
    Get all tafsir methodologies (bil-mathur, bil-ray, ishari, etc.).

    Arabic: الحصول على جميع مناهج التفسير
    """
    from app.services.tafsir_service import tafsir_service

    return {
        "methodologies": tafsir_service.get_methodologies(),
    }


@router.get("/tafsir/methodologies/{methodology_id}/scholars")
async def get_scholars_by_methodology(methodology_id: str):
    """
    Get scholars using a specific tafsir methodology.

    Arabic: الحصول على العلماء الذين يستخدمون منهج تفسير معين
    """
    from app.services.tafsir_service import tafsir_service

    scholars = tafsir_service.get_scholars_by_methodology(methodology_id)
    return {
        "methodology": methodology_id,
        "scholars": scholars,
        "total": len(scholars),
    }


@router.get("/tafsir/eras")
async def get_tafsir_eras():
    """
    Get all historical eras of tafsir scholarship.

    Arabic: الحصول على جميع العصور التاريخية لعلم التفسير
    """
    from app.services.tafsir_service import tafsir_service

    return {
        "eras": tafsir_service.get_eras(),
    }


@router.get("/tafsir/eras/{era_id}/scholars")
async def get_scholars_by_era(era_id: str):
    """
    Get scholars from a specific historical era.

    Arabic: الحصول على علماء من عصر تاريخي معين
    """
    from app.services.tafsir_service import tafsir_service

    scholars = tafsir_service.get_scholars_by_era(era_id)
    return {
        "era": era_id,
        "scholars": scholars,
        "total": len(scholars),
    }


@router.get("/tafsir/verse/{surah}/{ayah}")
async def get_tafsir_for_verse(
    surah: int,
    ayah: int,
    scholar_ids: Optional[str] = Query(None, description="Comma-separated scholar IDs"),
):
    """
    Get tafsir interpretations for a specific verse.

    Arabic: الحصول على تفسيرات آية معينة
    """
    from app.services.tafsir_service import tafsir_service

    scholars = scholar_ids.split(",") if scholar_ids else None
    entries = tafsir_service.get_tafsir_for_verse(surah, ayah, scholars)

    return {
        "verse": f"{surah}:{ayah}",
        "interpretations": entries,
        "total": len(entries),
    }


@router.get("/tafsir/compare/{surah}/{ayah}")
async def compare_tafsir_for_verse(
    surah: int,
    ayah: int,
    scholar_ids: Optional[str] = Query(None, description="Comma-separated scholar IDs"),
):
    """
    Compare tafsir interpretations for a verse across multiple scholars.

    Arabic: مقارنة تفسيرات آية من علماء متعددين
    """
    from app.services.tafsir_service import tafsir_service

    scholars = scholar_ids.split(",") if scholar_ids else None
    return tafsir_service.compare_tafsir(surah, ayah, scholars)


@router.get("/tafsir/search/theme")
async def search_tafsir_by_theme(
    theme: str = Query(..., description="Theme to search for"),
):
    """
    Search tafsir entries by theme.

    Arabic: البحث في التفاسير حسب الموضوع
    """
    from app.services.tafsir_service import tafsir_service

    results = tafsir_service.search_tafsir_by_theme(theme)
    return {
        "theme": theme,
        "results": results,
        "total": len(results),
    }


@router.get("/tafsir/fiqhi-rulings/{surah}/{ayah}")
async def get_fiqhi_rulings_from_verse(surah: int, ayah: int):
    """
    Extract fiqhi (legal) rulings from tafsir entries for a verse.

    Arabic: استخراج الأحكام الفقهية من تفاسير آية معينة
    """
    from app.services.tafsir_service import tafsir_service

    return tafsir_service.get_fiqhi_rulings_from_tafsir(surah, ayah)


@router.get("/tafsir/recommend/scholars")
async def get_recommended_scholars_for_topic(
    topic: str = Query(..., description="Topic of interest (e.g., 'fiqh', 'linguistics', 'spirituality')"),
):
    """
    Get scholar recommendations based on topic of interest.

    Arabic: الحصول على توصيات بالعلماء بناءً على الموضوع المطلوب
    """
    from app.services.tafsir_service import tafsir_service

    recommendations = tafsir_service.get_recommended_scholars_for_topic(topic)
    return {
        "topic": topic,
        "recommendations": recommendations,
        "total": len(recommendations),
    }


# User Tafsir Preferences


@router.post("/tafsir/preferences")
async def create_user_tafsir_preferences(
    user_id: str = Query(..., description="User ID"),
    preferred_schools: Optional[str] = Query(None, description="Comma-separated school IDs"),
    preferred_methodologies: Optional[str] = Query(None, description="Comma-separated methodology IDs"),
    preferred_scholars: Optional[str] = Query(None, description="Comma-separated scholar IDs"),
    language_preference: str = Query("english", description="Preferred language"),
    study_level: str = Query("intermediate", description="Study level: beginner, intermediate, advanced, scholarly"),
):
    """
    Create or update user's tafsir study preferences.

    Arabic: إنشاء أو تحديث تفضيلات دراسة التفسير للمستخدم
    """
    from app.services.tafsir_service import tafsir_service

    schools = preferred_schools.split(",") if preferred_schools else None
    methodologies = preferred_methodologies.split(",") if preferred_methodologies else None
    scholars = preferred_scholars.split(",") if preferred_scholars else None

    return tafsir_service.create_user_preference(
        user_id=user_id,
        preferred_schools=schools,
        preferred_methodologies=methodologies,
        preferred_scholars=scholars,
        language_preference=language_preference,
        study_level=study_level,
    )


@router.get("/tafsir/preferences/{user_id}")
async def get_user_tafsir_preferences(user_id: str):
    """
    Get user's tafsir study preferences.

    Arabic: الحصول على تفضيلات دراسة التفسير للمستخدم
    """
    from app.services.tafsir_service import tafsir_service

    preferences = tafsir_service.get_user_preference(user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")

    return preferences


@router.get("/tafsir/personalized/{user_id}/{surah}/{ayah}")
async def get_personalized_tafsir(user_id: str, surah: int, ayah: int):
    """
    Get tafsir personalized to user's preferences.

    Arabic: الحصول على تفسير مخصص حسب تفضيلات المستخدم
    """
    from app.services.tafsir_service import tafsir_service

    return tafsir_service.get_personalized_tafsir(user_id, surah, ayah)


@router.post("/tafsir/notes")
async def save_user_tafsir_note(
    user_id: str = Query(..., description="User ID"),
    surah: int = Query(..., ge=1, le=114),
    ayah: int = Query(..., ge=1),
    note: str = Query(..., description="User's personal note"),
):
    """
    Save user's personal note on a verse.

    Arabic: حفظ ملاحظة شخصية للمستخدم على آية
    """
    from app.services.tafsir_service import tafsir_service

    return tafsir_service.save_user_note(user_id, surah, ayah, note)


@router.get("/tafsir/notes/{user_id}")
async def get_user_tafsir_notes(user_id: str):
    """
    Get all user's tafsir notes.

    Arabic: الحصول على جميع ملاحظات التفسير للمستخدم
    """
    from app.services.tafsir_service import tafsir_service

    return tafsir_service.get_user_notes(user_id)


@router.get("/tafsir/stats")
async def get_tafsir_statistics():
    """
    Get overall tafsir service statistics.

    Arabic: إحصائيات خدمة التفسير
    """
    from app.services.tafsir_service import tafsir_service

    return tafsir_service.get_statistics()


# =============================================================================
# Advanced Semantic Search API Endpoints
# البحث الدلالي المتقدم باستخدام AraBERT
# =============================================================================


@router.get("/advanced-search/semantic")
async def advanced_semantic_search(
    query: str = Query(..., description="Search query (Arabic or English)"),
    mode: str = Query("hybrid", description="Search mode: lexical, semantic, or hybrid"),
    metric: str = Query("combined", description="Similarity metric: cosine, jaccard, bm25, or combined"),
    expand_query: bool = Query(True, description="Expand query using theme synonyms"),
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.1, ge=0.0, le=1.0),
):
    """
    Perform advanced semantic search on Quranic verses.

    Uses AraBERT-style embeddings combined with TF-IDF for hybrid search.
    Supports query expansion based on 18+ Quranic themes.

    Arabic: البحث الدلالي المتقدم في آيات القرآن
    """
    from app.services.advanced_semantic_search_service import (
        advanced_semantic_search_service,
        SearchMode,
        SimilarityMetric,
    )

    # Map string to enum
    mode_map = {"lexical": SearchMode.LEXICAL, "semantic": SearchMode.SEMANTIC, "hybrid": SearchMode.HYBRID}
    metric_map = {
        "cosine": SimilarityMetric.COSINE,
        "jaccard": SimilarityMetric.JACCARD,
        "bm25": SimilarityMetric.BM25,
        "combined": SimilarityMetric.COMBINED,
    }

    search_mode = mode_map.get(mode.lower(), SearchMode.HYBRID)
    similarity_metric = metric_map.get(metric.lower(), SimilarityMetric.COMBINED)

    return advanced_semantic_search_service.semantic_search(
        query=query,
        mode=search_mode,
        metric=similarity_metric,
        expand_query=expand_query,
        limit=limit,
        min_score=min_score,
    )


@router.get("/advanced-search/expand-query")
async def expand_search_query(
    query: str = Query(..., description="Query to expand"),
    include_arabic: bool = Query(True, description="Include Arabic expansions"),
    include_english: bool = Query(True, description="Include English expansions"),
):
    """
    Expand a search query using semantic themes and Arabic root words.

    Returns synonyms, related themes, and root word derivatives.

    Arabic: توسيع الاستعلام باستخدام المواضيع الدلالية وجذور الكلمات العربية
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    return advanced_semantic_search_service.expand_query(
        query=query, include_arabic=include_arabic, include_english=include_english
    )


@router.get("/advanced-search/themes")
async def get_all_quranic_themes():
    """
    Get all available Quranic themes for semantic search.

    Returns 18+ themes with Arabic/English terms and relationships.

    Arabic: الحصول على جميع المواضيع القرآنية للبحث الدلالي
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    return {
        "themes": advanced_semantic_search_service.get_all_themes(),
        "total": len(advanced_semantic_search_service.get_all_themes()),
    }


@router.get("/advanced-search/themes/{theme_id}")
async def get_theme_details(theme_id: str):
    """
    Get detailed information about a specific Quranic theme.

    Includes synonyms, root words, antonyms, and sample verses.

    Arabic: الحصول على تفاصيل موضوع قرآني معين
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    details = advanced_semantic_search_service.get_theme_details(theme_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")

    return details


@router.get("/advanced-search/themes/{theme_id}/verses")
async def search_verses_by_theme(
    theme_id: str,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search Quranic verses by a specific theme.

    Arabic: البحث في الآيات القرآنية حسب موضوع معين
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    result = advanced_semantic_search_service.search_by_theme(theme_id, limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/advanced-search/themes/{theme_id}/connections")
async def get_theme_connections(theme_id: str):
    """
    Get semantic connections between themes.

    Shows related themes with similarity scores.

    Arabic: الحصول على الروابط الدلالية بين المواضيع
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    result = advanced_semantic_search_service.get_theme_connections(theme_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/advanced-search/similar-verses/{surah}/{ayah}")
async def find_similar_verses(
    surah: int,
    ayah: int,
    limit: int = Query(5, ge=1, le=20),
):
    """
    Find verses semantically similar to a given verse.

    Uses embedding similarity to find related verses.

    Arabic: إيجاد الآيات المشابهة دلالياً لآية معينة
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    verse_id = f"{surah}:{ayah}"
    result = advanced_semantic_search_service.find_similar_verses(verse_id, limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/advanced-search/analyze-verse/{surah}/{ayah}")
async def analyze_verse_themes(surah: int, ayah: int):
    """
    Analyze themes present in a specific verse.

    Arabic: تحليل المواضيع الموجودة في آية معينة
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    verse_id = f"{surah}:{ayah}"
    result = advanced_semantic_search_service.analyze_verse_themes(verse_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/advanced-search/arabic-roots")
async def get_arabic_roots():
    """
    Get all Arabic root words and their derivatives.

    Used for morphological analysis and query expansion.

    Arabic: الحصول على جذور الكلمات العربية ومشتقاتها
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    roots = advanced_semantic_search_service.get_arabic_roots()
    return {
        "roots": [{"root": root, "derivatives": derivatives} for root, derivatives in roots.items()],
        "total": len(roots),
    }


@router.get("/advanced-search/stats")
async def get_advanced_search_statistics():
    """
    Get advanced semantic search service statistics.

    Arabic: إحصائيات خدمة البحث الدلالي المتقدم
    """
    from app.services.advanced_semantic_search_service import advanced_semantic_search_service

    return advanced_semantic_search_service.get_statistics()


# =============================================================================
# Enhanced Cross-School Tafsir Comparison API Endpoints
# مقارنة التفاسير المتقدمة عبر المذاهب الأربعة
# =============================================================================


@router.get("/tafsir-comparison/verse/{surah}/{ayah}")
async def compare_verse_across_schools(
    surah: int,
    ayah: int,
    schools: Optional[str] = Query(None, description="Comma-separated school IDs (hanafi,maliki,shafii,hanbali)"),
    include_footnotes: bool = Query(True, description="Include scholarly footnotes"),
    include_methodology: bool = Query(True, description="Include methodology analysis"),
):
    """
    Compare tafsir interpretations of a verse across the four madhabs.

    Returns interpretations organized by school with methodology analysis and footnotes.

    Arabic: مقارنة تفسيرات آية عبر المذاهب الأربعة
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    school_list = schools.split(",") if schools else None

    return enhanced_tafsir_comparison_service.compare_verse_across_schools(
        surah=surah,
        ayah=ayah,
        schools=school_list,
        include_footnotes=include_footnotes,
        include_methodology=include_methodology,
    )


@router.get("/tafsir-comparison/theme/{theme}")
async def compare_theme_across_schools(
    theme: str,
    schools: Optional[str] = Query(None, description="Comma-separated school IDs"),
):
    """
    Compare how different schools interpret a specific theme across related verses.

    Available themes: mercy, patience, justice, guidance, tawhid, prayer, forgiveness, gratitude, trust, knowledge

    Arabic: مقارنة تفسير موضوع معين عبر المذاهب
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    school_list = schools.split(",") if schools else None

    result = enhanced_tafsir_comparison_service.compare_theme_across_schools(
        theme=theme, schools=school_list
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/tafsir-comparison/methodology")
async def get_methodology_comparison(
    schools: Optional[str] = Query(None, description="Comma-separated school IDs"),
):
    """
    Get detailed methodology comparison between the four madhabs.

    Includes approach, key principles, sources used, strengths, and considerations.

    Arabic: مقارنة المنهجيات بين المذاهب الأربعة
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    school_list = schools.split(",") if schools else None

    return enhanced_tafsir_comparison_service.get_methodology_comparison(schools=school_list)


@router.get("/tafsir-comparison/madhab/{madhab}/scholars")
async def get_scholars_by_madhab(madhab: str):
    """
    Get available scholars within a specific madhab for detailed comparison.

    Arabic: الحصول على العلماء المتاحين في مذهب معين
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    return enhanced_tafsir_comparison_service.get_scholar_selection_by_madhab(madhab)


@router.get("/tafsir-comparison/verse/{surah}/{ayah}/references")
async def get_verse_with_references(surah: int, ayah: int):
    """
    Get verse interpretation with detailed scholarly references and footnotes.

    Arabic: الحصول على تفسير الآية مع المراجع العلمية التفصيلية
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    return enhanced_tafsir_comparison_service.get_verse_with_references(surah, ayah)


@router.get("/tafsir-comparison/filter")
async def filter_tafsir_by_preference(
    surah: int = Query(..., ge=1, le=114),
    ayah: int = Query(..., ge=1),
    preferred_schools: str = Query(..., description="Comma-separated preferred schools"),
    preferred_scholars: Optional[str] = Query(None, description="Comma-separated preferred scholar IDs"),
):
    """
    Get tafsir filtered by user's school and scholar preferences.

    Arabic: الحصول على التفسير المفلتر حسب تفضيلات المستخدم
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    schools = preferred_schools.split(",")
    scholars = preferred_scholars.split(",") if preferred_scholars else None

    return enhanced_tafsir_comparison_service.filter_tafsir_by_preference(
        surah=surah, ayah=ayah, preferred_schools=schools, preferred_scholars=scholars
    )


@router.get("/tafsir-comparison/themes")
async def get_available_comparison_themes():
    """
    Get all available themes for thematic tafsir comparison.

    Arabic: الحصول على المواضيع المتاحة للمقارنة الموضوعية
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    return enhanced_tafsir_comparison_service.get_available_themes()


@router.get("/tafsir-comparison/stats")
async def get_tafsir_comparison_statistics():
    """
    Get enhanced tafsir comparison service statistics.

    Arabic: إحصائيات خدمة مقارنة التفاسير المتقدمة
    """
    from app.services.enhanced_tafsir_comparison_service import enhanced_tafsir_comparison_service

    return enhanced_tafsir_comparison_service.get_statistics()


# =============================================================================
# Personalized Learning Paths with SM2 Spaced Repetition API Endpoints
# مسارات التعلم الشخصية مع خوارزمية التكرار المتباعد
# =============================================================================


@router.get("/learning/paths")
async def get_all_learning_paths():
    """
    Get all available learning paths.

    Arabic: الحصول على جميع مسارات التعلم المتاحة
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return {
        "paths": personalized_learning_service.get_all_learning_paths(),
        "total": len(personalized_learning_service.get_all_learning_paths()),
    }


@router.get("/learning/paths/{path_id}")
async def get_learning_path(path_id: str):
    """
    Get detailed information about a specific learning path.

    Arabic: الحصول على تفاصيل مسار تعلم معين
    """
    from app.services.personalized_learning_service import personalized_learning_service

    path = personalized_learning_service.get_learning_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Learning path '{path_id}' not found")

    return path


@router.get("/learning/recommended/{user_id}")
async def get_recommended_paths(user_id: str):
    """
    Get personalized learning path recommendations for a user.

    Arabic: الحصول على توصيات مسارات التعلم للمستخدم
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return {
        "user_id": user_id,
        "recommendations": personalized_learning_service.get_recommended_paths(user_id),
    }


@router.post("/learning/goals")
async def create_study_goal(
    user_id: str = Query(..., description="User ID"),
    goal_type: str = Query(..., description="Goal type: memorization, comprehension, reflection, tafsir_study, theme_exploration"),
    target_description: str = Query(..., description="Description of the goal"),
    target_items: str = Query(..., description="Comma-separated item IDs (e.g., verse references)"),
    daily_target_minutes: int = Query(15, ge=5, le=120),
    deadline_days: Optional[int] = Query(None, description="Days until deadline"),
):
    """
    Create a new study goal with SM2 spaced repetition tracking.

    Arabic: إنشاء هدف دراسي جديد مع تتبع التكرار المتباعد
    """
    from app.services.personalized_learning_service import personalized_learning_service

    items = [i.strip() for i in target_items.split(",")]

    result = personalized_learning_service.create_study_goal(
        user_id=user_id,
        goal_type=goal_type,
        target_description=target_description,
        target_items=items,
        daily_target_minutes=daily_target_minutes,
        deadline_days=deadline_days,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/learning/goals/{user_id}")
async def get_user_goals(user_id: str):
    """
    Get all study goals for a user.

    Arabic: الحصول على جميع أهداف المستخدم الدراسية
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_user_goals(user_id)


@router.post("/learning/review/add")
async def add_item_for_review(
    user_id: str = Query(..., description="User ID"),
    item_id: str = Query(..., description="Item ID (e.g., verse reference)"),
    item_type: str = Query("verse", description="Item type: verse, surah, theme, tafsir"),
):
    """
    Add an item to user's SM2 spaced repetition queue.

    Arabic: إضافة عنصر لقائمة التكرار المتباعد
    """
    from app.services.personalized_learning_service import personalized_learning_service, ContentType

    try:
        content_type = ContentType(item_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid item type. Valid types: {[t.value for t in ContentType]}")

    content = {"item_id": item_id, "type": item_type}

    return personalized_learning_service.add_item_for_review(user_id, item_id, content_type, content)


@router.post("/learning/review/submit")
async def submit_review(
    user_id: str = Query(..., description="User ID"),
    item_id: str = Query(..., description="Item ID being reviewed"),
    quality: int = Query(..., ge=0, le=5, description="Quality of recall: 0=blackout, 3=pass, 5=perfect"),
):
    """
    Submit a review result and get next review date using SM2 algorithm.

    Quality ratings:
    - 5: Perfect response
    - 4: Correct with hesitation
    - 3: Correct with difficulty
    - 2: Incorrect but remembered when shown
    - 1: Incorrect with hint
    - 0: Complete blackout

    Arabic: تقديم نتيجة المراجعة والحصول على موعد المراجعة القادم
    """
    from app.services.personalized_learning_service import personalized_learning_service

    result = personalized_learning_service.review_item(user_id, item_id, quality)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/learning/review/due/{user_id}")
async def get_due_reviews(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get items due for review today.

    Arabic: الحصول على العناصر المستحقة للمراجعة اليوم
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_due_reviews(user_id, limit)


@router.get("/learning/review/stats/{user_id}")
async def get_review_statistics(user_id: str):
    """
    Get user's spaced repetition review statistics.

    Arabic: إحصائيات التكرار المتباعد للمستخدم
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_review_statistics(user_id)


@router.get("/learning/progress/{user_id}")
async def get_user_progress(user_id: str):
    """
    Get user's overall learning progress and achievements.

    Arabic: الحصول على تقدم المستخدم وإنجازاته
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_user_progress(user_id)


@router.get("/learning/daily/{user_id}")
async def get_daily_recommendation(user_id: str):
    """
    Get personalized daily study recommendation.

    Arabic: الحصول على توصية الدراسة اليومية المخصصة
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_daily_recommendation(user_id)


@router.get("/learning/quiz/{quiz_id}")
async def get_quiz(quiz_id: str):
    """
    Get a quiz by ID.

    Arabic: الحصول على اختبار معين
    """
    from app.services.personalized_learning_service import personalized_learning_service

    result = personalized_learning_service.get_quiz(quiz_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("/learning/quiz/{quiz_id}/answer")
async def submit_quiz_answer(
    quiz_id: str,
    question_index: int = Query(..., ge=0),
    answer_index: int = Query(..., ge=0),
):
    """
    Submit and check a quiz answer.

    Arabic: تقديم إجابة الاختبار والتحقق منها
    """
    from app.services.personalized_learning_service import personalized_learning_service

    result = personalized_learning_service.submit_quiz_answer(quiz_id, question_index, answer_index)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/learning/reflection/{prompt_id}")
async def get_reflection_prompts(prompt_id: str):
    """
    Get reflection prompts for a specific topic.

    Arabic: الحصول على أسئلة التأمل لموضوع معين
    """
    from app.services.personalized_learning_service import personalized_learning_service

    result = personalized_learning_service.get_reflection_prompts(prompt_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/learning/stats")
async def get_learning_statistics():
    """
    Get personalized learning service statistics.

    Arabic: إحصائيات خدمة التعلم الشخصي
    """
    from app.services.personalized_learning_service import personalized_learning_service

    return personalized_learning_service.get_statistics()


# =============================================================================
# Enhanced Knowledge Graph with Entity Relationships and BFS Pathfinding
# الرسم البياني المعرفي المحسّن مع علاقات الكيانات والبحث بالعرض أولاً
# =============================================================================


@router.get("/enhanced-kg/entities")
async def get_all_kg_entities(
    entity_type: Optional[str] = Query(None, description="Filter by type: prophet, companion, place, divine_name, concept, event"),
):
    """
    Get all entities in the enhanced knowledge graph.

    Includes prophets, companions, places, divine names, concepts, and events.

    Arabic: الحصول على جميع الكيانات في الرسم البياني المعرفي
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    if entity_type:
        entities = enhanced_knowledge_graph_service.get_entities_by_type(entity_type)
    else:
        stats = enhanced_knowledge_graph_service.get_statistics()
        entities = []
        for etype in stats["entity_types"]:
            entities.extend(enhanced_knowledge_graph_service.get_entities_by_type(etype))

    return {
        "entities": entities,
        "total": len(entities),
        "filter": entity_type,
    }


@router.get("/enhanced-kg/entities/{entity_id}")
async def get_kg_entity(entity_id: str):
    """
    Get detailed information about a specific entity with all relationships.

    Arabic: الحصول على معلومات تفصيلية عن كيان معين مع جميع العلاقات
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    entity = enhanced_knowledge_graph_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

    return entity


@router.get("/enhanced-kg/entities/by-theme/{theme}")
async def get_entities_by_theme(theme: str):
    """
    Get all entities related to a specific theme.

    Themes include: mercy, patience, justice, guidance, sacrifice, monotheism, etc.

    Arabic: الحصول على جميع الكيانات المتعلقة بموضوع معين
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    entities = enhanced_knowledge_graph_service.get_entities_by_theme(theme)

    return {
        "theme": theme,
        "entities": entities,
        "total": len(entities),
    }


@router.get("/enhanced-kg/explore/{entity_id}")
async def explore_from_entity(
    entity_id: str,
    depth: int = Query(2, ge=1, le=4, description="Exploration depth"),
):
    """
    Explore the knowledge graph from a starting entity.

    Returns nodes and edges within the specified depth for visualization.

    Arabic: استكشاف الرسم البياني المعرفي من كيان بداية
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    result = enhanced_knowledge_graph_service.explore_from_entity(entity_id, depth)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/enhanced-kg/path")
async def find_path_between_entities(
    source: str = Query(..., description="Source entity ID (e.g., 'ibrahim')"),
    target: str = Query(..., description="Target entity ID (e.g., 'muhammad')"),
    max_depth: int = Query(10, ge=1, le=15, description="Maximum search depth"),
):
    """
    Find the shortest path between two entities using BFS.

    Useful for discovering connections between prophets, places, concepts, etc.

    Arabic: إيجاد أقصر مسار بين كيانين باستخدام البحث بالعرض أولاً
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    result = enhanced_knowledge_graph_service.find_path_bfs(source, target, max_depth)

    if not result:
        return {
            "path_found": False,
            "source": source,
            "target": target,
            "message_ar": f"لم يتم العثور على مسار بين {source} و {target}",
            "message_en": f"No path found between {source} and {target} within depth {max_depth}",
        }

    return {
        "path_found": True,
        **result,
    }


@router.get("/enhanced-kg/all-paths")
async def find_all_paths_between_entities(
    source: str = Query(..., description="Source entity ID"),
    target: str = Query(..., description="Target entity ID"),
    max_depth: int = Query(5, ge=1, le=7, description="Maximum search depth"),
):
    """
    Find all possible paths between two entities (up to max_depth).

    Returns multiple paths with different relationship chains.

    Arabic: إيجاد جميع المسارات الممكنة بين كيانين
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    paths = enhanced_knowledge_graph_service.find_all_paths(source, target, max_depth)

    return {
        "source": source,
        "target": target,
        "paths": paths,
        "total_paths": len(paths),
        "message_ar": "جميع المسارات المتاحة" if paths else "لم يتم العثور على مسارات",
        "message_en": "All available paths" if paths else "No paths found",
    }


@router.get("/enhanced-kg/prophet-lineage/{prophet_id}")
async def get_prophet_lineage(prophet_id: str):
    """
    Get the lineage (ancestors and descendants) of a prophet.

    Arabic: الحصول على نسب النبي (الأسلاف والأحفاد)
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    result = enhanced_knowledge_graph_service.get_prophet_lineage(prophet_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/enhanced-kg/thematic-journey/{theme}")
async def get_thematic_journey(theme: str):
    """
    Create a thematic journey through related entities.

    Connects entities that share the specified theme (e.g., patience, mercy, trust).

    Arabic: إنشاء رحلة موضوعية عبر الكيانات ذات الصلة
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    result = enhanced_knowledge_graph_service.get_thematic_journey(theme)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/enhanced-kg/visualization")
async def get_kg_visualization_data():
    """
    Get complete graph data formatted for visualization.

    Returns all nodes and edges with labels and types for rendering an interactive graph.

    Arabic: الحصول على بيانات الرسم البياني الكاملة للتصور
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    return enhanced_knowledge_graph_service.get_graph_visualization_data()


@router.get("/enhanced-kg/entity-types")
async def get_kg_entity_types():
    """
    Get all available entity types in the knowledge graph.

    Arabic: الحصول على جميع أنواع الكيانات المتاحة
    """
    from app.services.enhanced_knowledge_graph_service import EntityType

    return {
        "entity_types": [
            {"id": t.value, "name_en": t.name.replace("_", " ").title()}
            for t in EntityType
        ],
        "total": len(EntityType),
    }


@router.get("/enhanced-kg/relationship-types")
async def get_kg_relationship_types():
    """
    Get all available relationship types in the knowledge graph.

    Arabic: الحصول على جميع أنواع العلاقات المتاحة
    """
    from app.services.enhanced_knowledge_graph_service import RelationshipType

    return {
        "relationship_types": [
            {"id": t.value, "name_en": t.name.replace("_", " ").title()}
            for t in RelationshipType
        ],
        "total": len(RelationshipType),
    }


@router.get("/enhanced-kg/stats")
async def get_enhanced_kg_statistics():
    """
    Get enhanced knowledge graph statistics.

    Arabic: إحصائيات الرسم البياني المعرفي المحسّن
    """
    from app.services.enhanced_knowledge_graph_service import enhanced_knowledge_graph_service

    return enhanced_knowledge_graph_service.get_statistics()


# =============================================================================
# Grounded Ask Feature - Deterministic Answers from Four Sunni Schools
# ميزة الإجابة المسندة - إجابات محددة من المذاهب السنية الأربعة
# =============================================================================


class AskRequest(BaseModel):
    """Request model for asking questions"""
    query: str = Field(..., min_length=1, max_length=500, description="The question to ask")
    preferred_madhabs: Optional[List[str]] = Field(
        None,
        description="Preferred madhabs: hanafi, maliki, shafii, hanbali"
    )


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    query: str = Field(..., description="The original query")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    helpful: bool = Field(..., description="Was the answer helpful?")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")


class UserPreferencesRequest(BaseModel):
    """Request model for user preferences"""
    preferred_madhabs: Optional[List[str]] = Field(None, description="Preferred madhabs")
    preferred_language: str = Field("english", description="Preferred language: english or arabic")
    study_focus: Optional[List[str]] = Field(None, description="Study focus areas")


@router.post("/ask")
async def ask_question(
    request: AskRequest,
    user_id: Optional[str] = Query(None, description="User ID for personalization"),
):
    """
    Ask a question about the Quran and receive grounded scholarly answers.

    Features:
    - Validated sources from the four Sunni schools (Hanafi, Maliki, Shafi'i, Hanbali)
    - Query validation with helpful suggestions
    - Tafsir from Ibn Kathir, Al-Qurtubi, Al-Sa'di, and more
    - Related Hadith from Sahih Bukhari, Muslim, Abu Dawud
    - Fiqh rulings with madhab comparison
    - Thematic connections across Quranic verses
    - External resource links for further study

    Example queries:
    - "What does Ayat al-Kursi mean?"
    - "What does the Quran say about patience?"
    - "What are the prayer times according to the four madhabs?"

    Arabic: اسأل سؤالاً عن القرآن واحصل على إجابات علمية مسندة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.ask(
        query=request.query,
        user_id=user_id,
        preferred_madhabs=request.preferred_madhabs,
    )


@router.get("/ask/validate")
async def validate_query(
    query: str = Query(..., min_length=1, max_length=500, description="Query to validate"),
):
    """
    Validate a query before asking.

    Returns query type, extracted verse references, themes, and suggestions.

    Arabic: التحقق من صحة الاستعلام قبل طرحه
    """
    from app.services.grounded_ask_service import grounded_ask_service

    validation = grounded_ask_service.validate_query(query)

    return {
        "is_valid": validation.is_valid,
        "query_type": validation.query_type.value if validation.query_type else None,
        "normalized_query": validation.normalized_query,
        "detected_language": validation.detected_language,
        "extracted_verse_refs": validation.extracted_verse_refs,
        "extracted_themes": validation.extracted_themes,
        "suggestions": validation.suggestions,
        "error": {
            "code": validation.error_code.value if validation.error_code else None,
            "message_ar": validation.error_message_ar,
            "message_en": validation.error_message_en,
        } if validation.error_code else None,
    }


@router.post("/ask/feedback")
async def submit_answer_feedback(
    request: FeedbackRequest,
    user_id: str = Query(..., description="User ID"),
):
    """
    Submit feedback on an answer to help improve the system.

    Arabic: تقديم ملاحظات على الإجابة لتحسين النظام
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.submit_feedback(
        user_id=user_id,
        query=request.query,
        rating=request.rating,
        helpful=request.helpful,
        comment=request.comment,
    )


@router.post("/ask/preferences")
async def set_user_ask_preferences(
    request: UserPreferencesRequest,
    user_id: str = Query(..., description="User ID"),
):
    """
    Set user preferences for personalized answers.

    Preferences include:
    - Preferred madhabs for fiqh rulings
    - Preferred language (Arabic or English)
    - Study focus areas (e.g., tafsir, fiqh, hadith)

    Arabic: تعيين تفضيلات المستخدم للإجابات المخصصة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.set_user_preferences(
        user_id=user_id,
        preferred_madhabs=request.preferred_madhabs,
        preferred_language=request.preferred_language,
        study_focus=request.study_focus,
    )


@router.get("/ask/preferences/{user_id}")
async def get_user_ask_preferences(user_id: str):
    """
    Get user's ask preferences.

    Arabic: الحصول على تفضيلات المستخدم
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.get_user_preferences(user_id)


@router.get("/ask/scholars")
async def get_verified_ask_scholars(
    madhab: Optional[str] = Query(None, description="Filter by madhab: hanafi, maliki, shafii, hanbali"),
):
    """
    Get all verified scholars used for grounded answers.

    Only scholars from the four Sunni schools are included.

    Arabic: الحصول على جميع العلماء المعتمدين للإجابات المسندة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    if madhab:
        scholars = grounded_ask_service.get_scholars_by_madhab(madhab)
        return {
            "madhab": madhab,
            "scholars": scholars,
            "total": len(scholars),
        }

    return {
        "scholars": grounded_ask_service.get_all_scholars(),
        "total": len(grounded_ask_service.get_all_scholars()),
    }


@router.get("/ask/sources")
async def get_verified_sources():
    """
    Get all verified sources used for grounded answers.

    Includes:
    - Tafsir: Ibn Kathir, Al-Qurtubi, Al-Sa'di, Al-Tabari, Al-Jassas
    - Hadith: Sahih Bukhari, Sahih Muslim, Sunan Abu Dawud, Al-Muwatta
    - Fiqh: Al-Hidaya, Al-Umm, Al-Mughni

    Arabic: الحصول على جميع المصادر المعتمدة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return {
        "sources": grounded_ask_service.get_all_sources(),
        "total": len(grounded_ask_service.get_all_sources()),
        "note_ar": "جميع المصادر من العلماء المعتمدين من المذاهب الأربعة",
        "note_en": "All sources are from verified scholars of the four madhabs",
    }


@router.get("/ask/themes")
async def get_available_ask_themes():
    """
    Get all available themes for thematic questions.

    Themes include: patience, mercy, justice, guidance, gratitude, tawhid, etc.

    Arabic: الحصول على جميع المواضيع المتاحة للأسئلة الموضوعية
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return {
        "themes": grounded_ask_service.get_all_themes(),
        "total": len(grounded_ask_service.get_all_themes()),
    }


@router.get("/ask/madhabs")
async def get_supported_madhabs():
    """
    Get information about the four supported Sunni madhabs.

    Arabic: الحصول على معلومات عن المذاهب السنية الأربعة المدعومة
    """
    return {
        "madhabs": [
            {
                "id": "hanafi",
                "name_ar": "الحنفي",
                "name_en": "Hanafi",
                "founder_ar": "أبو حنيفة النعمان",
                "founder_en": "Abu Hanifa",
                "key_texts": ["Al-Hidaya", "Radd al-Muhtar"],
            },
            {
                "id": "maliki",
                "name_ar": "المالكي",
                "name_en": "Maliki",
                "founder_ar": "مالك بن أنس",
                "founder_en": "Malik ibn Anas",
                "key_texts": ["Al-Muwatta", "Al-Mudawwana"],
            },
            {
                "id": "shafii",
                "name_ar": "الشافعي",
                "name_en": "Shafi'i",
                "founder_ar": "محمد بن إدريس الشافعي",
                "founder_en": "Muhammad ibn Idris al-Shafi'i",
                "key_texts": ["Al-Umm", "Al-Risala"],
            },
            {
                "id": "hanbali",
                "name_ar": "الحنبلي",
                "name_en": "Hanbali",
                "founder_ar": "أحمد بن حنبل",
                "founder_en": "Ahmad ibn Hanbal",
                "key_texts": ["Al-Mughni", "Musnad Ahmad"],
            },
        ],
        "note_ar": "المذاهب الأربعة كلها على الحق ومعتبرة",
        "note_en": "All four madhabs are valid and respected",
    }


@router.get("/ask/example-queries")
async def get_example_queries():
    """
    Get example queries to help users understand how to ask questions.

    Arabic: الحصول على أمثلة على الاستعلامات
    """
    return {
        "examples": [
            {
                "category": "verse_meaning",
                "queries": [
                    "What does Ayat al-Kursi (2:255) mean?",
                    "Explain the meaning of Al-Fatiha",
                    "ما معنى آية الكرسي؟",
                ],
            },
            {
                "category": "thematic",
                "queries": [
                    "What does the Quran say about patience?",
                    "Verses about mercy in the Quran",
                    "ماذا يقول القرآن عن الصبر؟",
                ],
            },
            {
                "category": "fiqh",
                "queries": [
                    "What are the prayer times according to the four madhabs?",
                    "Rules of fasting in Ramadan",
                    "أحكام الصيام في رمضان",
                ],
            },
            {
                "category": "tafsir",
                "queries": [
                    "What do the scholars say about 2:255?",
                    "Ibn Kathir's explanation of Al-Fatiha",
                    "تفسير ابن كثير لسورة الفاتحة",
                ],
            },
        ],
        "tips": [
            "Include verse references (e.g., 2:255) for specific answers",
            "Mention themes (patience, mercy, justice) for thematic answers",
            "Specify a madhab if you want that school's perspective",
            "Use simpler queries for better results",
        ],
    }


@router.get("/ask/feedback-stats")
async def get_ask_feedback_statistics():
    """
    Get feedback statistics for the Ask feature.

    Arabic: إحصائيات الملاحظات لميزة الإجابة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.get_feedback_stats()


@router.get("/ask/stats")
async def get_ask_statistics():
    """
    Get statistics about the Grounded Ask service.

    Arabic: إحصائيات خدمة الإجابة المسندة
    """
    from app.services.grounded_ask_service import grounded_ask_service

    return grounded_ask_service.get_statistics()


# =============================================================================
# Alatlas (Atlas) - Quranic Stories with Arabic Classification
# أطلس القصص القرآنية - التصنيف العربي الكامل
# =============================================================================


@router.get("/atlas/stories")
async def get_all_atlas_stories(
    category: Optional[str] = Query(None, description="Filter by category: prophets, nations, parables, historical, unseen, miracles, creation, afterlife"),
    theme: Optional[str] = Query(None, description="Filter by theme: patience, trust, faith, justice, mercy, etc."),
    verified_only: bool = Query(False, description="Only show verified stories"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get all Quranic stories with optional filtering.

    Features:
    - Arabic tagging and classification
    - Filter by category (الأنبياء، الأمم، الأمثال، etc.)
    - Filter by theme (الصبر، التوكل، الإيمان، etc.)
    - Completeness scoring

    Arabic: الحصول على جميع القصص القرآنية مع التصفية الاختيارية
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_all_stories(
        category=category,
        theme=theme,
        verified_only=verified_only,
        limit=limit,
        offset=offset,
    )


@router.get("/atlas/stories/{story_id}")
async def get_atlas_story(story_id: str):
    """
    Get complete details of a specific Quranic story.

    Returns:
    - Full Arabic and English content
    - All figures/characters with roles
    - Events in sequence with verse references
    - Key lessons and themes
    - Relationships to other stories
    - Tafsir references

    Arabic: الحصول على تفاصيل قصة قرآنية كاملة
    """
    from app.services.alatlas_service import alatlas_service

    story = alatlas_service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    return story


@router.get("/atlas/stories/{story_id}/verify")
async def verify_atlas_story(story_id: str):
    """
    Verify story classification and check for completeness.

    Returns:
    - Classification check (category, themes)
    - Completeness score
    - Issues found (missing data)
    - Suggestions for improvement

    Arabic: التحقق من تصنيف القصة واكتمالها
    """
    from app.services.alatlas_service import alatlas_service

    result = alatlas_service.verify_story(story_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/atlas/stories/{story_id}/graph")
async def get_atlas_story_graph(story_id: str):
    """
    Get graph visualization data for a story (الرسم البياني).

    Returns nodes and edges for:
    - Story (central node)
    - Figures/Prophets
    - Events (in sequence)
    - Themes
    - Relationships

    Suitable for rendering with D3.js, Cytoscape, or similar libraries.

    Arabic: الحصول على بيانات الرسم البياني للقصة
    """
    from app.services.alatlas_service import alatlas_service

    result = alatlas_service.get_story_graph(story_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/atlas/stories/{story_id}/relationships")
async def get_atlas_story_relationships(story_id: str):
    """
    Get all relationships for a story.

    Returns:
    - Direct relationships (prophet-to-place, father-son, etc.)
    - Related stories with shared themes
    - Inverse relationships (stories that reference this one)

    Arabic: الحصول على جميع علاقات القصة
    """
    from app.services.alatlas_service import alatlas_service

    result = alatlas_service.get_story_relationships(story_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/atlas/search")
async def search_atlas_stories(
    query: str = Query(..., min_length=1, description="Search query (Arabic or English)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    prophet: Optional[str] = Query(None, description="Filter by prophet name"),
    event: Optional[str] = Query(None, description="Filter by event name"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search Quranic stories by various criteria.

    Searches in:
    - Story titles (Arabic and English)
    - Summaries
    - Figure/character names
    - Event names

    Arabic: البحث في القصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.search_stories(
        query=query,
        category=category,
        theme=theme,
        prophet=prophet,
        event=event,
        limit=limit,
    )


@router.get("/atlas/categories")
async def get_atlas_categories():
    """
    Get all story categories with Arabic names.

    Categories:
    - الأنبياء (Prophets)
    - الأمم (Nations)
    - الأمثال (Parables)
    - التاريخية (Historical)
    - الغيب (Unseen)
    - المعجزات (Miracles)
    - الخلق (Creation)
    - الآخرة (Afterlife)

    Arabic: الحصول على جميع فئات القصص
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_categories()


@router.get("/atlas/themes")
async def get_atlas_themes():
    """
    Get all story themes with Arabic names.

    Themes include:
    - الصبر (Patience)
    - التوكل (Trust)
    - الإيمان (Faith)
    - العدل (Justice)
    - الرحمة (Mercy)
    - التوبة (Repentance)
    - And more...

    Arabic: الحصول على جميع مواضيع القصص
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_themes()


@router.get("/atlas/prophets")
async def get_atlas_prophets():
    """
    Get all prophets mentioned in Quranic stories.

    Returns prophet details with:
    - Arabic and English names
    - Descriptions
    - Stories they appear in

    Arabic: الحصول على جميع الأنبياء في القصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_prophets()


@router.get("/atlas/filter")
async def filter_atlas_stories(
    categories: Optional[str] = Query(None, description="Comma-separated category IDs"),
    themes: Optional[str] = Query(None, description="Comma-separated theme IDs"),
    prophets: Optional[str] = Query(None, description="Comma-separated prophet names"),
    min_completeness: float = Query(0.0, ge=0.0, le=1.0, description="Minimum completeness score"),
    sort_by: str = Query("title", description="Sort by: title, completeness, events"),
    order: str = Query("asc", description="Order: asc or desc"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Advanced filtering for Quranic stories.

    Allows multiple filters to be combined.

    Arabic: التصفية المتقدمة للقصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    # Parse comma-separated values
    category_list = categories.split(",") if categories else None
    theme_list = themes.split(",") if themes else None
    prophet_list = prophets.split(",") if prophets else None

    # Get all stories first
    all_stories = alatlas_service.get_all_stories(limit=1000)["stories"]

    # Apply filters
    filtered = all_stories

    if category_list:
        filtered = [s for s in filtered if s["category"] in category_list]

    if theme_list:
        filtered = [s for s in filtered if any(t in theme_list for t in s["themes"])]

    if prophet_list:
        # Need to check each story's figures
        result = []
        for story in filtered:
            full_story = alatlas_service.get_story(story["id"])
            if full_story:
                story_prophets = [f["name_en"].lower() for f in full_story["figures"] if f["is_prophet"]]
                if any(p.lower() in story_prophets for p in prophet_list):
                    result.append(story)
        filtered = result

    if min_completeness > 0:
        filtered = [s for s in filtered if s["completeness_score"] >= min_completeness]

    # Sort
    reverse = order.lower() == "desc"
    if sort_by == "completeness":
        filtered.sort(key=lambda x: x["completeness_score"], reverse=reverse)
    elif sort_by == "events":
        filtered.sort(key=lambda x: x["event_count"], reverse=reverse)
    else:
        filtered.sort(key=lambda x: x["title_en"], reverse=reverse)

    return {
        "stories": filtered[:limit],
        "total": len(filtered),
        "filters": {
            "categories": category_list,
            "themes": theme_list,
            "prophets": prophet_list,
            "min_completeness": min_completeness,
        },
        "sort": {"by": sort_by, "order": order},
    }


@router.get("/atlas/stories/by-category/{category}")
async def get_stories_by_category(category: str):
    """
    Get all stories in a specific category.

    Arabic: الحصول على جميع القصص في فئة معينة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_all_stories(category=category)


@router.get("/atlas/stories/by-theme/{theme}")
async def get_stories_by_theme(theme: str):
    """
    Get all stories with a specific theme.

    Arabic: الحصول على جميع القصص ذات موضوع معين
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_all_stories(theme=theme)


@router.get("/atlas/stories/by-prophet/{prophet_name}")
async def get_stories_by_prophet(prophet_name: str):
    """
    Get all stories featuring a specific prophet.

    Arabic: الحصول على جميع القصص التي يظهر فيها نبي معين
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.search_stories(
        query=prophet_name,
        prophet=prophet_name,
        limit=50,
    )


@router.get("/atlas/timeline")
async def get_atlas_timeline():
    """
    Get chronological timeline of Quranic stories.

    Returns stories ordered by the sequence of prophets/events.

    Arabic: الحصول على الجدول الزمني للقصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    # Define chronological order of prophets
    prophet_order = [
        "adam", "nuh", "hud", "salih", "ibrahim", "lut", "ismail", "ishaq",
        "yaqub", "yusuf", "shuayb", "musa", "harun", "dawud", "sulaiman",
        "ilyas", "alyasa", "yunus", "zakariyya", "yahya", "isa", "muhammad"
    ]

    all_stories = alatlas_service.get_all_stories(limit=100)["stories"]

    # Sort by prophet order
    def get_order(story):
        story_full = alatlas_service.get_story(story["id"])
        if story_full:
            for figure in story_full.get("figures", []):
                if figure["is_prophet"]:
                    prophet_id = figure["id"]
                    if prophet_id in prophet_order:
                        return prophet_order.index(prophet_id)
        return 999

    sorted_stories = sorted(all_stories, key=get_order)

    return {
        "timeline": sorted_stories,
        "total": len(sorted_stories),
        "note_ar": "القصص مرتبة حسب تسلسل الأنبياء",
        "note_en": "Stories ordered by sequence of prophets",
    }


@router.get("/atlas/graph/complete")
async def get_complete_atlas_graph():
    """
    Get complete graph of all Quranic stories and their relationships.

    Returns a unified graph with all stories as nodes and
    relationships between them as edges.

    Suitable for full atlas visualization.

    Arabic: الحصول على الرسم البياني الكامل لجميع القصص
    """
    from app.services.alatlas_service import alatlas_service

    all_stories = alatlas_service.get_all_stories(limit=100)["stories"]

    nodes = []
    edges = []
    seen_edges = set()

    # Add all stories as nodes
    for i, story in enumerate(all_stories):
        import math
        angle = (2 * math.pi * i) / len(all_stories)
        radius = 400

        # Get category color
        category_colors = {
            "prophets": "#4CAF50",
            "nations": "#2196F3",
            "parables": "#FF9800",
            "historical": "#9C27B0",
            "unseen": "#607D8B",
            "miracles": "#E91E63",
            "creation": "#00BCD4",
            "afterlife": "#FFC107",
        }

        nodes.append({
            "id": story["id"],
            "label": story["title_ar"],
            "label_en": story["title_en"],
            "type": "story",
            "category": story["category"],
            "category_ar": story["category_ar"],
            "x": radius * math.cos(angle),
            "y": radius * math.sin(angle),
            "size": 20 + (story["event_count"] * 2),
            "color": category_colors.get(story["category"], "#666666"),
        })

    # Add relationships between stories
    for story in all_stories:
        relationships = alatlas_service.get_story_relationships(story["id"])
        if "error" not in relationships:
            for related in relationships.get("related_stories", []):
                edge_id = tuple(sorted([story["id"], related["id"]]))
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append({
                        "source": story["id"],
                        "target": related["id"],
                        "label": ", ".join(related.get("shared_themes", [])),
                        "type": "related",
                    })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "legend": {
            "categories": [
                {"id": k, "color": v, "name_ar": alatlas_service.get_categories()["categories"][i]["name_ar"] if i < len(alatlas_service.get_categories()["categories"]) else k}
                for i, (k, v) in enumerate({
                    "prophets": "#4CAF50",
                    "nations": "#2196F3",
                    "parables": "#FF9800",
                    "historical": "#9C27B0",
                    "unseen": "#607D8B",
                    "miracles": "#E91E63",
                    "creation": "#00BCD4",
                    "afterlife": "#FFC107",
                }.items())
            ],
        },
    }


@router.get("/atlas/stats")
async def get_atlas_statistics():
    """
    Get Alatlas statistics.

    Returns:
    - Total stories, verified stories
    - Stories by category
    - Total events, figures, relationships
    - Average completeness score

    Arabic: إحصائيات أطلس القصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_statistics()


# ============================================
# ENHANCED SEARCH ENDPOINTS
# ============================================

@router.get("/atlas/search/advanced")
async def search_stories_advanced(
    query: str = Query(..., description="Search query"),
    categories: Optional[str] = Query(None, description="Comma-separated category filters"),
    themes: Optional[str] = Query(None, description="Comma-separated theme filters"),
    prophets: Optional[str] = Query(None, description="Comma-separated prophet filters"),
    time_period: Optional[str] = Query(None, description="Time period filter"),
    fuzzy: bool = Query(True, description="Enable fuzzy matching"),
    fuzzy_threshold: float = Query(0.5, description="Fuzzy match threshold (0-1)"),
    limit: int = Query(20, description="Maximum results")
):
    """
    Advanced search with fuzzy matching, keyword expansion, and filters.

    Features:
    - Fuzzy search with typo tolerance
    - Query expansion (Arabic/English variations)
    - Multiple filter dimensions

    Arabic: البحث المتقدم مع دعم الأخطاء الإملائية
    """
    from app.services.alatlas_service import alatlas_service

    cat_list = categories.split(",") if categories else None
    theme_list = themes.split(",") if themes else None
    prophet_list = prophets.split(",") if prophets else None

    return alatlas_service.search_advanced(
        query=query,
        categories=cat_list,
        themes=theme_list,
        prophets=prophet_list,
        time_period=time_period,
        fuzzy=fuzzy,
        fuzzy_threshold=fuzzy_threshold,
        limit=limit
    )


@router.get("/atlas/search/{theme}/{prophet}")
async def search_by_theme_and_prophet(
    theme: str,
    prophet: str,
    limit: int = Query(10, description="Maximum results")
):
    """
    Search stories by specific theme and prophet combination.

    Arabic: البحث حسب الموضوع والنبي
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.search_by_theme_and_prophet(
        theme=theme,
        prophet=prophet,
        limit=limit
    )


# ============================================
# DYNAMIC THEME & CATEGORY ENDPOINTS
# ============================================

@router.get("/atlas/themes/dynamic")
async def get_dynamic_themes():
    """
    Get dynamically updated themes with statistics.

    Returns:
    - Theme usage statistics
    - Related themes
    - Popularity rankings

    Arabic: المواضيع الديناميكية مع الإحصائيات
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_dynamic_themes()


@router.get("/atlas/categories/dynamic")
async def get_dynamic_categories():
    """
    Get dynamically updated categories with statistics.

    Returns:
    - Category usage statistics
    - Theme distribution per category
    - Completeness averages

    Arabic: التصنيفات الديناميكية مع الإحصائيات
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_dynamic_categories()


# ============================================
# ENHANCED GRAPH VISUALIZATION ENDPOINTS
# ============================================

@router.get("/atlas/graph/expanded")
async def get_expanded_graph(
    include_themes: bool = Query(True, description="Include theme nodes"),
    include_events: bool = Query(True, description="Include event nodes"),
    include_places: bool = Query(True, description="Include place nodes"),
    color_by_theme: bool = Query(True, description="Color-code by primary theme")
):
    """
    Get enhanced graph visualization with themes, events, and color-coding.

    Features:
    - Color-coded themes
    - Event nodes
    - Interactive metadata
    - D3.js/Cytoscape compatible

    Arabic: الرسم البياني المتقدم مع الألوان والأحداث
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_expanded_graph(
        include_themes=include_themes,
        include_events=include_events,
        include_places=include_places,
        color_by_theme=color_by_theme
    )


@router.get("/atlas/graph/path/{start_story_id}/{end_story_id}")
async def find_thematic_path(
    start_story_id: str,
    end_story_id: str,
    max_depth: int = Query(5, description="Maximum path depth")
):
    """
    Find thematic connection path between two stories using BFS.

    Shows how stories are interconnected through themes, prophets, and relationships.

    Arabic: إيجاد المسار الموضوعي بين قصتين
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.find_thematic_path(
        start_story_id=start_story_id,
        end_story_id=end_story_id,
        max_depth=max_depth
    )


# ============================================
# STORY COMPLETENESS & VERIFICATION ENDPOINTS
# ============================================

@router.get("/atlas/stories/{story_id}/verify/completeness")
async def verify_story_completeness(story_id: str):
    """
    Comprehensive verification of story completeness.

    Checks:
    - Basic info, themes, figures, events
    - Verses, lessons, relationships
    - Provides improvement suggestions

    Arabic: التحقق الشامل من اكتمال القصة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.verify_completeness(story_id)


class StoryUpdateRequest(BaseModel):
    """Request model for story updates."""
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None
    themes_ar: Optional[List[str]] = None
    key_lessons_ar: Optional[List[str]] = None
    key_lessons_en: Optional[List[str]] = None
    related_stories: Optional[List[str]] = None
    tafsir_references: Optional[List[Dict[str, str]]] = None


@router.post("/atlas/stories/{story_id}/update")
async def update_story(story_id: str, updates: StoryUpdateRequest):
    """
    Update a story with new or corrected information.

    Returns updated story and new verification result.

    Arabic: تحديث بيانات القصة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.update_story(story_id, updates.model_dump(exclude_none=True))


# ============================================
# USER FEEDBACK ENDPOINTS
# ============================================

class StoryFeedbackRequest(BaseModel):
    """Request model for story feedback."""
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    accuracy_rating: int = Field(..., ge=1, le=5)
    completeness_rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None


@router.post("/atlas/feedback/{story_id}")
async def submit_story_feedback(story_id: str, feedback: StoryFeedbackRequest):
    """
    Submit user feedback for a story.

    Includes:
    - Overall rating
    - Accuracy rating
    - Completeness rating
    - Comments and suggestions

    Arabic: إرسال تقييم القصة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.submit_story_feedback(
        story_id=story_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        accuracy_rating=feedback.accuracy_rating,
        completeness_rating=feedback.completeness_rating,
        comment=feedback.comment,
        suggested_improvements=feedback.suggested_improvements
    )


@router.get("/atlas/stories/{story_id}/feedback")
async def get_story_feedback(story_id: str):
    """
    Get aggregated user feedback for a story.

    Returns:
    - Average ratings
    - Recent comments
    - Improvement suggestions

    Arabic: الحصول على تقييمات القصة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_story_feedback(story_id)


# ============================================
# CONTENT EXPANSION ENDPOINTS
# ============================================

@router.get("/atlas/prophet/{prophet_id}/details")
async def get_prophet_details(prophet_id: str):
    """
    Get comprehensive details for a specific prophet.

    Includes:
    - Associated stories
    - Events
    - Places
    - Related prophets

    Arabic: تفاصيل النبي الشاملة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_prophet_details(prophet_id)


@router.get("/atlas/events")
async def get_all_events(
    category: Optional[str] = Query(None, description="Filter by category"),
    prophet: Optional[str] = Query(None, description="Filter by prophet"),
    limit: int = Query(50, description="Maximum results")
):
    """
    Get all historical events from Quranic stories.

    Arabic: جميع الأحداث التاريخية من القصص القرآنية
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_all_events(
        category=category,
        prophet=prophet,
        limit=limit
    )


# ============================================
# USER JOURNEY & PROGRESS ENDPOINTS
# ============================================

class UserJourneyRequest(BaseModel):
    """Request model for saving user journey."""
    user_id: str
    current_story_id: str
    themes_explored: List[str]
    time_spent_seconds: int = 0
    notes: Optional[str] = None


@router.post("/atlas/user/journey")
async def save_user_journey(journey: UserJourneyRequest):
    """
    Save user's thematic journey through stories.

    Tracks:
    - Stories visited
    - Themes explored
    - Time spent
    - Personal notes

    Arabic: حفظ رحلة المستخدم في القصص
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.save_user_journey(
        user_id=journey.user_id,
        current_story_id=journey.current_story_id,
        themes_explored=journey.themes_explored,
        time_spent_seconds=journey.time_spent_seconds,
        notes=journey.notes
    )


@router.get("/atlas/user/progress/{user_id}")
async def get_user_progress(user_id: str):
    """
    Get user's study progress and achievements.

    Returns:
    - Stories completed
    - Themes explored
    - Milestones achieved
    - Suggested next stories

    Arabic: تقدم المستخدم والإنجازات
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_user_progress(user_id)


# ============================================
# MULTILINGUAL & TAFSIR ENDPOINTS
# ============================================

@router.get("/atlas/languages")
async def get_available_languages():
    """
    Get available language support for the app.

    Arabic: اللغات المتاحة
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_available_languages()


@router.get("/atlas/stories/{story_id}/tafsir")
async def get_story_with_tafsir(
    story_id: str,
    language: str = Query("ar", description="Display language (ar/en)"),
    tafsir_source: Optional[str] = Query(None, description="Specific tafsir source")
):
    """
    Get story with integrated Tafsir explanations.

    Includes:
    - Ibn Kathir, Al-Qurtubi, Al-Saadi tafsir
    - Verse-by-verse explanations
    - Multi-language support

    Arabic: القصة مع التفسير المتكامل
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_story_with_tafsir(
        story_id=story_id,
        language=language,
        tafsir_source=tafsir_source
    )


# ============================================
# RECOMMENDATIONS ENDPOINTS
# ============================================

@router.get("/atlas/recommendations")
async def get_recommendations(
    user_id: Optional[str] = Query(None, description="User ID for personalized recommendations"),
    current_story_id: Optional[str] = Query(None, description="Current story for related recommendations"),
    based_on: str = Query("mixed", description="Recommendation basis: themes, category, prophets, mixed"),
    limit: int = Query(5, description="Maximum recommendations")
):
    """
    Get automated story recommendations.

    Based on:
    - Shared themes
    - Same category
    - Related prophets
    - User history

    Arabic: التوصيات التلقائية للقصص
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_recommendations(
        user_id=user_id,
        current_story_id=current_story_id,
        based_on=based_on,
        limit=limit
    )


# ============================================
# CACHING & PERFORMANCE ENDPOINTS
# ============================================

@router.get("/atlas/stories/cached")
async def get_cached_stories(
    force_refresh: bool = Query(False, description="Force cache refresh")
):
    """
    Get cached story data for quicker access.

    Features:
    - 5-minute TTL cache
    - Faster response times
    - Cache status indicator

    Arabic: البيانات المخزنة مؤقتاً للوصول السريع
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_cached_stories(force_refresh=force_refresh)


@router.get("/atlas/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.

    Arabic: إحصائيات التخزين المؤقت
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.get_cache_stats()


@router.delete("/atlas/cache")
async def clear_cache(
    cache_key: Optional[str] = Query(None, description="Specific cache key to clear, or all if not specified")
):
    """
    Clear cache data.

    Arabic: مسح البيانات المخزنة مؤقتاً
    """
    from app.services.alatlas_service import alatlas_service

    return alatlas_service.clear_cache(cache_key)


# ============================================
# ADVANCED FEATURES - FANG LEVEL ENHANCEMENTS
# ============================================

# --- VERIFICATION PIPELINE (HUMAN IN THE LOOP) ---

class VerificationTaskRequest(BaseModel):
    """Request model for creating verification task."""
    story_id: str
    task_type: str  # "accuracy", "completeness", "categorization", "tafsir"
    issues_found: List[str]
    ai_confidence: float
    priority: Optional[str] = None


@router.post("/atlas/verification/create")
async def create_verification_task(request: VerificationTaskRequest):
    """
    Create a verification task for human review.
    AI flags issues, humans verify.

    Arabic: إنشاء مهمة تحقق للمراجعة البشرية
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.create_verification_task(
        story_id=request.story_id,
        task_type=request.task_type,
        issues_found=request.issues_found,
        ai_confidence=request.ai_confidence,
        priority=request.priority
    )


@router.get("/atlas/verification/queue")
async def get_verification_queue(
    admin_id: str = Query(..., description="Admin user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(20, description="Maximum results")
):
    """
    Get verification queue for admins.

    Arabic: قائمة مهام التحقق للمسؤولين
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_verification_queue(
        admin_id=admin_id,
        status_filter=status,
        priority_filter=priority,
        limit=limit
    )


class VerificationResultRequest(BaseModel):
    """Request model for submitting verification result."""
    reviewer_id: str
    decision: str  # "approve", "reject", "needs_revision"
    madhab_verified: Dict[str, bool]
    notes: Optional[str] = None
    resolution: Optional[str] = None


@router.post("/atlas/verification/{task_id}/submit")
async def submit_verification_result(task_id: str, request: VerificationResultRequest):
    """
    Submit verification result from reviewer.

    Arabic: تسجيل نتيجة التحقق
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.submit_verification_result(
        task_id=task_id,
        reviewer_id=request.reviewer_id,
        decision=request.decision,
        madhab_verified=request.madhab_verified,
        notes=request.notes,
        resolution=request.resolution
    )


class FlagStoryRequest(BaseModel):
    """Request model for flagging a story."""
    user_id: str
    reason: str
    details: Optional[str] = None


@router.post("/atlas/stories/{story_id}/flag")
async def flag_story_for_review(story_id: str, request: FlagStoryRequest):
    """
    Flag a story for admin review.

    Arabic: الإبلاغ عن قصة للمراجعة
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.flag_story_for_review(
        story_id=story_id,
        user_id=request.user_id,
        reason=request.reason,
        details=request.details
    )


@router.get("/atlas/stories/{story_id}/auto-verify")
async def auto_verify_story(story_id: str):
    """
    AI-assisted automatic verification of a story.

    Arabic: التحقق التلقائي بالذكاء الاصطناعي
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.auto_verify_story(story_id)


# --- SEMANTIC SEARCH WITH INTENT DETECTION ---

@router.get("/search/contextual-query")
async def contextual_search(
    query: str = Query(..., description="Search query"),
    intent: Optional[str] = Query(None, description="Override detected intent"),
    limit: int = Query(10, description="Maximum results")
):
    """
    Semantic search with contextual intent detection.

    Features:
    - Intent detection (story_search, theme_exploration, prophet_info, etc.)
    - Concept matching
    - Contextual ranking

    Arabic: البحث الدلالي مع فهم السياق
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.semantic_search(
        query=query,
        intent=intent,
        limit=limit
    )


@router.get("/search/detect-intent")
async def detect_query_intent(query: str = Query(..., description="Query to analyze")):
    """
    Detect user intent from query.

    Returns:
    - Primary intent
    - Detected concepts
    - Suggested filters

    Arabic: تحليل نية المستخدم من الاستعلام
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.detect_query_intent(query)


@router.post("/search/expand-query")
async def expand_search_query(query: str = Query(..., description="Query to expand")):
    """
    Expand query with synonyms, related terms, and Ahadith references.

    Arabic: توسيع الاستعلام بالمترادفات والأحاديث
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.expand_query(query)


# --- AI-DRIVEN PERSONALIZATION & LEARNING ---

class UserProfileRequest(BaseModel):
    """Request model for creating user profile."""
    user_id: str
    learning_goal: str
    preferred_language: str = "ar"
    preferred_madhab: Optional[str] = None
    themes_of_interest: Optional[List[str]] = None


@router.post("/learning/profile/create")
async def create_user_profile(request: UserProfileRequest):
    """
    Create user learning profile.

    Goals: memorization, comprehension, tafsir_study, thematic_study, story_exploration

    Arabic: إنشاء ملف تعلم المستخدم
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.create_user_profile(
        user_id=request.user_id,
        learning_goal=request.learning_goal,
        preferred_language=request.preferred_language,
        preferred_madhab=request.preferred_madhab,
        themes_of_interest=request.themes_of_interest
    )


class TrackInteractionRequest(BaseModel):
    """Request model for tracking interaction."""
    user_id: str
    interaction_type: str  # "view", "complete", "quiz", "bookmark"
    story_id: str
    time_spent_seconds: int = 0
    score: Optional[float] = None
    themes_explored: Optional[List[str]] = None


@router.post("/learning/track-interactions")
async def track_user_interaction(request: TrackInteractionRequest):
    """
    Track user interaction for personalization.

    Arabic: تتبع تفاعل المستخدم للتخصيص
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.track_interaction(
        user_id=request.user_id,
        interaction_type=request.interaction_type,
        story_id=request.story_id,
        time_spent_seconds=request.time_spent_seconds,
        score=request.score,
        themes_explored=request.themes_explored
    )


@router.post("/learning/sm2-review")
async def calculate_sm2_review(
    user_id: str = Query(..., description="User ID"),
    story_id: str = Query(..., description="Story ID"),
    quality: int = Query(..., ge=0, le=5, description="Response quality 0-5")
):
    """
    Calculate SM2 spaced repetition for story review.

    Quality: 0=complete blackout, 5=perfect response

    Arabic: حساب التكرار المتباعد للمراجعة
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.calculate_sm2_review(
        user_id=user_id,
        story_id=story_id,
        quality=quality
    )


@router.get("/learning/recommendations/{user_id}")
async def get_personalized_recommendations(
    user_id: str,
    limit: int = Query(5, description="Maximum recommendations")
):
    """
    Get personalized story recommendations based on user profile.

    Arabic: التوصيات الشخصية بناءً على ملف المستخدم
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_personalized_recommendations(
        user_id=user_id,
        limit=limit
    )


@router.get("/learning/goal/{user_id}")
async def get_learning_goal_content(
    user_id: str,
    goal: Optional[str] = Query(None, description="Override learning goal")
):
    """
    Get content tailored to user's learning goal.

    Arabic: المحتوى المخصص لهدف التعلم
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_learning_goal_content(
        user_id=user_id,
        goal=goal
    )


# --- KNOWLEDGE GRAPH EXPANSION ---

@router.get("/graph/explore")
async def explore_deep_relationships(
    entity_id: str = Query(..., description="Entity ID"),
    entity_type: str = Query(..., description="prophet, theme, place, event"),
    depth: int = Query(2, description="Exploration depth")
):
    """
    Explore deep relationships in the knowledge graph.

    Arabic: استكشاف العلاقات العميقة في رسم المعرفة
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.explore_deep_relationships(
        entity_id=entity_id,
        entity_type=entity_type,
        depth=depth
    )


@router.get("/graph/theme-progression/{theme}")
async def get_theme_progression(theme: str):
    """
    Track how a theme evolves across stories and verses.

    Arabic: تتبع تطور الموضوع عبر القصص
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_theme_progression(theme)


@router.get("/graph/interactive-explore")
async def explore_graph_interactive(
    start_node: str = Query(..., description="Starting node ID"),
    node_type: str = Query(..., description="story, theme, prophet"),
    mode: str = Query("connected", description="connected, thematic, chronological"),
    depth: int = Query(2, description="Exploration depth")
):
    """
    Interactive graph exploration with click-through navigation.

    Arabic: الاستكشاف التفاعلي للرسم البياني
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.explore_graph_interactive(
        start_node=start_node,
        node_type=node_type,
        exploration_mode=mode,
        depth=depth
    )


@router.get("/graph/thematic-exploration/{theme}")
async def get_thematic_journey(
    theme: str,
    start_story: Optional[str] = Query(None, description="Optional starting story")
):
    """
    Visualize the journey of a theme across prophets and stories.

    Arabic: رحلة الموضوع عبر الأنبياء والقصص
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_thematic_journey(
        theme=theme,
        start_story=start_story
    )


# --- SCALABILITY & PERFORMANCE ---

@router.post("/cache/warm-up")
async def warm_up_cache(
    data_types: Optional[str] = Query(None, description="Comma-separated: stories,themes,categories,prophets")
):
    """
    Preload frequently accessed data into cache.

    Arabic: تحميل البيانات المتكررة مسبقاً
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    types_list = data_types.split(",") if data_types else None
    return advanced_atlas_service.warm_up_cache(types_list)


@router.get("/performance/stats")
async def get_performance_stats():
    """
    Get performance and cache statistics.

    Arabic: إحصائيات الأداء والتخزين المؤقت
    """
    from app.services.advanced_atlas_service import advanced_atlas_service

    return advanced_atlas_service.get_performance_stats()


# ============================================
# MIRACLES & VERSES API ROUTES
# ============================================
# Comprehensive Quranic miracles with tafsir from four Sunni madhabs

@router.get("/miracles")
async def search_miracles(
    query: Optional[str] = Query(None, description="Search query in Arabic or English"),
    category: Optional[str] = Query(None, description="Filter by category: prophetic, divine, creation, natural, revelation, historical"),
    prophet_id: Optional[str] = Query(None, description="Filter by prophet ID"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    limit: int = Query(20, description="Maximum results to return")
):
    """
    Search and list Quranic miracles.
    Supports filtering by category, prophet, and theme.

    Arabic: البحث في المعجزات القرآنية
    """
    from app.services.miracles_service import miracles_service

    if query:
        return miracles_service.search_miracles(query=query, limit=limit)
    elif prophet_id:
        return miracles_service.get_miracles_by_prophet(prophet_id)
    else:
        return miracles_service.get_all_miracles(category=category, limit=limit)


@router.get("/miracles/semantic-search")
async def semantic_search_miracles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum results"),
    min_similarity: float = Query(0.1, description="Minimum similarity threshold")
):
    """
    Semantic search for miracles using AraBERT-like embeddings.
    Finds miracles based on meaning rather than exact keywords.

    Arabic: البحث الدلالي في المعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.semantic_search_miracles(
        query=query,
        limit=limit,
        min_similarity=min_similarity
    )


@router.get("/miracles/categories")
async def get_miracle_categories():
    """
    Get all miracle categories with counts.

    Arabic: تصنيفات المعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracle_categories()


@router.get("/miracles/themes")
async def get_miracle_themes():
    """
    Get all themes associated with miracles.

    Arabic: مواضيع المعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracle_themes()


@router.get("/miracles/prophets")
async def get_prophets_with_miracles():
    """
    Get all prophets who have miracles in the database.

    Arabic: الأنبياء ومعجزاتهم
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_prophets_with_miracles()


@router.get("/miracles/tafsir-sources")
async def get_miracle_tafsir_sources():
    """
    Get all tafsir sources used in miracle explanations.
    Includes scholars from four Sunni madhabs: Hanafi, Maliki, Shafi'i, Hanbali.

    Arabic: مصادر التفسير للمعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_tafsir_sources()


@router.get("/miracles/graph")
async def get_miracles_graph(
    center_miracle_id: Optional[str] = Query(None, description="Center the graph on this miracle"),
    depth: int = Query(2, description="Graph exploration depth")
):
    """
    Get graph visualization data for miracles.
    Shows connections between miracles, prophets, and themes.

    Arabic: رسم بياني للعلاقات بين المعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracle_graph(
        center_miracle_id=center_miracle_id,
        depth=depth
    )


@router.get("/miracles/{miracle_id}")
async def get_miracle_details(
    miracle_id: str
):
    """
    Get detailed information for a specific miracle.
    Includes verses, tafsir from all four madhabs, lessons, and related miracles.

    Arabic: تفاصيل المعجزة
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracle(miracle_id)


@router.get("/miracles/{miracle_id}/feedback")
async def get_miracle_feedback(
    miracle_id: str,
    status: Optional[str] = Query(None, description="Filter by status: pending, reviewed, accepted, rejected")
):
    """
    Get user feedback for a specific miracle.

    Arabic: آراء المستخدمين حول المعجزة
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracle_feedback(
        miracle_id=miracle_id,
        status_filter=status
    )


@router.post("/miracles/feedback")
async def submit_miracle_feedback(
    miracle_id: str = Query(..., description="Miracle ID"),
    user_id: str = Query(..., description="User ID"),
    feedback_type: str = Query(..., description="Type: correction, addition, question, insight"),
    content_ar: str = Query(..., description="Feedback content in Arabic"),
    content_en: Optional[str] = Query("", description="Feedback content in English")
):
    """
    Submit feedback or insights about a miracle.
    Feedback types: correction, addition, question, insight.

    Arabic: إرسال ملاحظات حول المعجزة
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.submit_feedback(
        miracle_id=miracle_id,
        user_id=user_id,
        feedback_type=feedback_type,
        content_ar=content_ar,
        content_en=content_en
    )


@router.get("/miracles/admin/dashboard")
async def get_miracles_admin_dashboard(
    admin_id: str = Query(..., description="Admin user ID")
):
    """
    Get admin dashboard with statistics and pending reviews.
    Requires admin privileges.

    Arabic: لوحة تحكم المشرف للمعجزات
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_admin_dashboard(admin_id)


@router.post("/miracles/admin/review-feedback")
async def review_miracle_feedback(
    admin_id: str = Query(..., description="Admin user ID"),
    feedback_id: str = Query(..., description="Feedback ID to review"),
    decision: str = Query(..., description="Decision: accepted or rejected"),
    notes: Optional[str] = Query(None, description="Reviewer notes")
):
    """
    Review and decide on user feedback.
    Requires admin privileges.

    Arabic: مراجعة ملاحظات المستخدمين
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.review_feedback(
        admin_id=admin_id,
        feedback_id=feedback_id,
        decision=decision,
        notes=notes
    )


@router.get("/miracles/prophet/{prophet_id}")
async def get_miracles_by_prophet(
    prophet_id: str
):
    """
    Get all miracles for a specific prophet.

    Arabic: معجزات النبي
    """
    from app.services.miracles_service import miracles_service

    return miracles_service.get_miracles_by_prophet(prophet_id)


# =============================================================================
# AUDIO RECITATION ENDPOINTS
# =============================================================================

@router.get("/audio/reciters")
async def get_reciters():
    """
    Get list of available Quran reciters.

    Arabic: قائمة القراء المتاحين
    """
    from app.services.audio_service import get_audio_service

    audio_service = get_audio_service()
    return {
        "ok": True,
        "reciters": audio_service.get_reciters(),
    }


@router.get("/audio/surah/{sura_no}")
async def get_surah_audio(
    sura_no: int,
    reciter: str = Query(default="mishary_afasy", description="Reciter ID"),
):
    """
    Get audio URL for a complete Surah.

    Args:
        sura_no: Surah number (1-114)
        reciter: Reciter ID (default: mishary_afasy)

    Arabic: رابط صوت السورة كاملة
    """
    from app.services.audio_service import get_audio_service

    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

    audio_service = get_audio_service()
    url = audio_service.get_surah_audio_url(sura_no, reciter)

    if not url:
        raise HTTPException(status_code=404, detail="Audio not found")

    return {
        "ok": True,
        "sura_no": sura_no,
        "reciter": reciter,
        "audio_url": url,
        "type": "surah",
    }


@router.get("/audio/verse/{sura_no}/{aya_no}")
async def get_verse_audio(
    sura_no: int,
    aya_no: int,
    reciter: str = Query(default="mishary_afasy", description="Reciter ID"),
    include_fallback: bool = Query(default=True, description="Include fallback URLs"),
):
    """
    Get audio URL for a single verse with optional fallback sources.

    Args:
        sura_no: Surah number (1-114)
        aya_no: Verse number
        reciter: Reciter ID (default: mishary_afasy)
        include_fallback: Include alternative audio sources

    Arabic: رابط صوت الآية مع البدائل
    """
    from app.services.audio_service import get_audio_service

    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

    audio_service = get_audio_service()

    if include_fallback:
        urls = audio_service.get_verse_audio_urls_with_fallback(sura_no, aya_no, reciter)
        if not urls:
            raise HTTPException(status_code=404, detail="Audio not found")

        # Collect all fallback URLs for high availability
        fallback_urls = [
            u for u in [urls.get("fallback1"), urls.get("fallback2")]
            if u
        ]

        return {
            "ok": True,
            "sura_no": sura_no,
            "aya_no": aya_no,
            "reference": f"{sura_no}:{aya_no}",
            "reciter": reciter,
            "audio_url": urls.get("primary"),
            "fallback_url": fallback_urls[0] if fallback_urls else None,  # Legacy support
            "fallback_urls": fallback_urls,  # New: array of all fallbacks
            "type": "verse",
        }

    url = audio_service.get_verse_audio_url(sura_no, aya_no, reciter)
    if not url:
        raise HTTPException(status_code=404, detail="Audio not found")

    return {
        "ok": True,
        "sura_no": sura_no,
        "aya_no": aya_no,
        "reference": f"{sura_no}:{aya_no}",
        "reciter": reciter,
        "audio_url": url,
        "type": "verse",
    }


@router.get("/audio/range/{sura_no}/{aya_start}/{aya_end}")
async def get_verse_range_audio(
    sura_no: int,
    aya_start: int,
    aya_end: int,
    reciter: str = Query(default="mishary_afasy", description="Reciter ID"),
):
    """
    Get audio URLs for a range of verses.

    Args:
        sura_no: Surah number (1-114)
        aya_start: Starting verse number
        aya_end: Ending verse number
        reciter: Reciter ID (default: mishary_afasy)

    Arabic: روابط صوت مجموعة آيات
    """
    from app.services.audio_service import get_audio_service

    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")

    if aya_start > aya_end:
        raise HTTPException(status_code=400, detail="Start verse must be before end verse")

    audio_service = get_audio_service()
    urls = audio_service.get_verse_range_audio_urls(sura_no, aya_start, aya_end, reciter)

    return {
        "ok": True,
        "sura_no": sura_no,
        "aya_start": aya_start,
        "aya_end": aya_end,
        "reciter": reciter,
        "verse_audios": urls,
        "total_verses": len(urls),
        "type": "range",
    }


@router.get("/audio/page/{page_no}")
async def get_page_audio(
    page_no: int,
    reciter: str = Query(default="mishary_afasy", description="Reciter ID"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get audio URLs for all verses on a Mushaf page.

    Args:
        page_no: Mushaf page number (1-604)
        reciter: Reciter ID (default: mishary_afasy)

    Arabic: روابط صوت صفحة المصحف
    """
    from app.services.audio_service import get_audio_service

    if page_no < 1 or page_no > 604:
        raise HTTPException(status_code=400, detail="Page number must be between 1 and 604")

    # Get verses on this page
    query = (
        select(QuranVerse)
        .where(QuranVerse.page_no == page_no)
        .order_by(QuranVerse.id)
    )
    result = await session.execute(query)
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(status_code=404, detail=f"Page {page_no} not found")

    # Convert to dict for audio service
    verse_dicts = [{"sura_no": v.sura_no, "aya_no": v.aya_no} for v in verses]

    audio_service = get_audio_service()
    audio_info = audio_service.get_page_audio_info(page_no, reciter, verse_dicts)

    return {
        "ok": True,
        **audio_info,
        "type": "page",
    }


# =============================================================================
# Concept-based Verse Highlighting
# =============================================================================

@router.get("/highlights/concept/{concept_id}")
async def get_concept_verse_highlights(
    concept_id: str,
    page_no: Optional[int] = Query(None, description="Filter by page number"),
    sura_no: Optional[int] = Query(None, description="Filter by Surah number"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verse highlights for a specific concept.

    Returns verses that should be highlighted when viewing a concept.
    Can filter by page or surah to get only relevant highlights.

    Arabic: آيات مرتبطة بمفهوم معين
    """
    from app.models.concept import Occurrence

    # Build query for occurrences
    query = (
        select(Occurrence)
        .where(Occurrence.concept_id == concept_id)
        .where(Occurrence.ref_type == "ayah")
        .where(Occurrence.sura_no.isnot(None))
    )

    # Filter by page if provided
    if page_no:
        page_verse_query = (
            select(QuranVerse.sura_no, QuranVerse.aya_no)
            .where(QuranVerse.page_no == page_no)
        )
        page_verses_result = await session.execute(page_verse_query)
        page_verses = {(r.sura_no, r.aya_no) for r in page_verses_result.all()}

        if not page_verses:
            return {
                "ok": True,
                "concept_id": concept_id,
                "highlights": [],
                "total": 0,
            }

    # Filter by surah if provided
    if sura_no:
        query = query.where(Occurrence.sura_no == sura_no)

    result = await session.execute(query.order_by(Occurrence.sura_no, Occurrence.ayah_start))
    occurrences = result.scalars().all()

    highlights = []
    for occ in occurrences:
        # Build list of highlighted verses
        if occ.ayah_end and occ.ayah_end > occ.ayah_start:
            for aya in range(occ.ayah_start, occ.ayah_end + 1):
                # If filtering by page, check if this verse is on the page
                if page_no and (occ.sura_no, aya) not in page_verses:
                    continue
                highlights.append({
                    "sura_no": occ.sura_no,
                    "aya_no": aya,
                    "reference": f"{occ.sura_no}:{aya}",
                    "weight": occ.weight,
                })
        else:
            # Single verse
            if page_no and (occ.sura_no, occ.ayah_start) not in page_verses:
                continue
            highlights.append({
                "sura_no": occ.sura_no,
                "aya_no": occ.ayah_start,
                "reference": f"{occ.sura_no}:{occ.ayah_start}",
                "weight": occ.weight,
            })

    # Remove duplicates while preserving order and keeping highest weight
    unique_highlights = {}
    for h in highlights:
        key = (h["sura_no"], h["aya_no"])
        if key not in unique_highlights or h["weight"] > unique_highlights[key]["weight"]:
            unique_highlights[key] = h

    return {
        "ok": True,
        "concept_id": concept_id,
        "highlights": list(unique_highlights.values()),
        "total": len(unique_highlights),
    }


@router.get("/highlights/concepts/multi")
async def get_multi_concept_verse_highlights(
    concept_ids: str = Query(..., description="Comma-separated concept IDs (e.g., 'person_musa,person_firaun')"),
    page_no: Optional[int] = Query(None, description="Filter by page number"),
    sura_no: Optional[int] = Query(None, description="Filter by Surah number"),
    expand_related: bool = Query(True, description="Include related concepts via associations"),
    include_aliases: bool = Query(True, description="Search using concept aliases"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verse highlights for multiple concepts with query expansion.

    Supports "Suleiman + Queen of Sheba" style queries by accepting
    multiple concept IDs and optionally expanding to related concepts.

    Query expansion includes:
    - Related concepts via associations (similarity, related types)
    - Parent/child concepts in hierarchy
    - Concept aliases for broader matching

    Arabic: آيات مرتبطة بعدة مفاهيم مع توسيع البحث
    """
    from app.models.concept import Occurrence, Concept, Association
    from sqlalchemy import or_

    # Parse concept IDs
    requested_concepts = [c.strip() for c in concept_ids.split(",") if c.strip()]
    if not requested_concepts:
        return {
            "ok": False,
            "error": "No concept IDs provided",
            "highlights": [],
            "total": 0,
        }

    # Build expanded concept set (for query expansion)
    all_concept_ids = set(requested_concepts)
    expansion_info = {}

    if expand_related:
        # Find related concepts via associations
        for concept_id in requested_concepts:
            # Get associations where this concept is involved
            assoc_query = (
                select(Association)
                .where(
                    or_(
                        Association.concept_a_id == concept_id,
                        Association.concept_b_id == concept_id
                    )
                )
                .where(
                    Association.relation_type.in_(["similarity", "related", "part_of", "attribute_of"])
                )
                .where(Association.strength >= 0.5)  # Only strong associations
            )
            assoc_result = await session.execute(assoc_query)
            associations = assoc_result.scalars().all()

            related_ids = []
            for assoc in associations:
                related_id = assoc.concept_b_id if assoc.concept_a_id == concept_id else assoc.concept_a_id
                all_concept_ids.add(related_id)
                related_ids.append({
                    "id": related_id,
                    "relation": assoc.relation_type,
                    "strength": assoc.strength,
                })

            # Get parent/child concepts
            parent_query = (
                select(Concept.id, Concept.parent_concept_id)
                .where(Concept.id == concept_id)
            )
            parent_result = await session.execute(parent_query)
            concept_row = parent_result.first()
            if concept_row and concept_row.parent_concept_id:
                all_concept_ids.add(concept_row.parent_concept_id)
                related_ids.append({
                    "id": concept_row.parent_concept_id,
                    "relation": "parent",
                    "strength": 0.8,
                })

            # Get children
            children_query = select(Concept.id).where(Concept.parent_concept_id == concept_id)
            children_result = await session.execute(children_query)
            for child in children_result.scalars().all():
                all_concept_ids.add(child)
                related_ids.append({
                    "id": child,
                    "relation": "child",
                    "strength": 0.7,
                })

            if related_ids:
                expansion_info[concept_id] = related_ids

    # Get page verses if filtering by page
    page_verses = None
    if page_no:
        page_verse_query = (
            select(QuranVerse.sura_no, QuranVerse.aya_no)
            .where(QuranVerse.page_no == page_no)
        )
        page_verses_result = await session.execute(page_verse_query)
        page_verses = {(r.sura_no, r.aya_no) for r in page_verses_result.all()}

        if not page_verses:
            return {
                "ok": True,
                "concept_ids": requested_concepts,
                "expanded_concepts": list(all_concept_ids - set(requested_concepts)),
                "highlights": [],
                "total": 0,
                "expansion_info": expansion_info,
            }

    # Get occurrences for all concepts
    query = (
        select(Occurrence)
        .where(Occurrence.concept_id.in_(all_concept_ids))
        .where(Occurrence.ref_type == "ayah")
        .where(Occurrence.sura_no.isnot(None))
    )

    if sura_no:
        query = query.where(Occurrence.sura_no == sura_no)

    result = await session.execute(query.order_by(Occurrence.sura_no, Occurrence.ayah_start))
    occurrences = result.scalars().all()

    # Build highlights with aggregated weights
    highlights_map = {}  # key: (sura_no, aya_no), value: highlight dict

    for occ in occurrences:
        is_primary = occ.concept_id in requested_concepts
        weight_multiplier = 1.0 if is_primary else 0.7  # Lower weight for expanded concepts

        verses_to_add = []
        if occ.ayah_end and occ.ayah_end > occ.ayah_start:
            for aya in range(occ.ayah_start, occ.ayah_end + 1):
                verses_to_add.append((occ.sura_no, aya))
        else:
            verses_to_add.append((occ.sura_no, occ.ayah_start))

        for sura, aya in verses_to_add:
            # Filter by page if provided
            if page_verses and (sura, aya) not in page_verses:
                continue

            key = (sura, aya)
            effective_weight = occ.weight * weight_multiplier

            if key not in highlights_map:
                highlights_map[key] = {
                    "sura_no": sura,
                    "aya_no": aya,
                    "reference": f"{sura}:{aya}",
                    "weight": effective_weight,
                    "matched_concepts": [occ.concept_id],
                    "is_primary_match": is_primary,
                }
            else:
                # Aggregate weight (max weight + bonus for multiple matches)
                current = highlights_map[key]
                current["weight"] = min(1.0, max(current["weight"], effective_weight) + 0.1)
                if occ.concept_id not in current["matched_concepts"]:
                    current["matched_concepts"].append(occ.concept_id)
                if is_primary:
                    current["is_primary_match"] = True

    # Sort by weight (highest first), then by verse order
    highlights = sorted(
        highlights_map.values(),
        key=lambda h: (-h["weight"], h["sura_no"], h["aya_no"])
    )

    return {
        "ok": True,
        "concept_ids": requested_concepts,
        "expanded_concepts": list(all_concept_ids - set(requested_concepts)),
        "expansion_info": expansion_info,
        "highlights": highlights,
        "total": len(highlights),
        "stats": {
            "primary_matches": sum(1 for h in highlights if h["is_primary_match"]),
            "expanded_matches": sum(1 for h in highlights if not h["is_primary_match"]),
            "multi_concept_matches": sum(1 for h in highlights if len(h["matched_concepts"]) > 1),
        },
    }


@router.get("/search/concepts/expand")
async def expand_concept_query(
    query: str = Query(..., min_length=2, description="Search query to expand"),
    max_concepts: int = Query(10, description="Maximum concepts to return"),
    include_aliases: bool = Query(True, description="Search using aliases"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Expand a search query to related concepts.

    Given a search term like "patience" or "صبر", returns matching concepts
    and their related concepts for query expansion.

    Arabic: توسيع استعلام البحث للمفاهيم ذات الصلة
    """
    from app.models.concept import Concept, Association
    from sqlalchemy import or_, func

    # Search for matching concepts
    search_conditions = [
        Concept.label_ar.ilike(f"%{query}%"),
        Concept.label_en.ilike(f"%{query}%"),
        Concept.slug.ilike(f"%{query}%"),
    ]

    if include_aliases:
        # PostgreSQL array contains check
        search_conditions.extend([
            func.array_to_string(Concept.aliases_ar, ' ').ilike(f"%{query}%"),
            func.array_to_string(Concept.aliases_en, ' ').ilike(f"%{query}%"),
        ])

    concept_query = (
        select(Concept)
        .where(or_(*search_conditions))
        .limit(max_concepts)
    )
    result = await session.execute(concept_query)
    concepts = result.scalars().all()

    expanded_results = []
    for concept in concepts:
        # Get related concepts
        related_query = (
            select(Association, Concept)
            .join(Concept, or_(
                Association.concept_b_id == Concept.id,
                Association.concept_a_id == Concept.id
            ))
            .where(or_(
                Association.concept_a_id == concept.id,
                Association.concept_b_id == concept.id
            ))
            .where(Concept.id != concept.id)
            .where(Association.strength >= 0.3)
            .limit(5)
        )
        related_result = await session.execute(related_query)

        related_concepts = []
        for assoc, related_concept in related_result.all():
            related_concepts.append({
                "id": related_concept.id,
                "label_ar": related_concept.label_ar,
                "label_en": related_concept.label_en,
                "relation_type": assoc.relation_type,
                "strength": assoc.strength,
            })

        expanded_results.append({
            "concept": concept.to_dict(),
            "aliases": {
                "ar": concept.aliases_ar or [],
                "en": concept.aliases_en or [],
            },
            "related_concepts": related_concepts,
            "suggested_query": f"{concept.id}",
        })

    # Also check cross-language concepts from semantic search
    from app.services.arabic_semantic_search import arabic_semantic_service
    cross_language = arabic_semantic_service.expand_cross_language_query(query)

    return {
        "ok": True,
        "query": query,
        "matched_concepts": expanded_results,
        "total": len(expanded_results),
        "cross_language_expansion": {
            "source_language": cross_language.source_language,
            "arabic_terms": cross_language.arabic_terms[:10],
            "english_terms": cross_language.english_terms[:10],
            "detected_themes": cross_language.detected_concepts,
            "life_lessons": cross_language.life_lessons_applicable,
        },
    }


# =============================================================================
# Semantic Verse Search (Qdrant Vector Search)
# =============================================================================

@router.get("/search/semantic")
async def semantic_verse_search(
    query: str = Query(..., min_length=2, description="Search query (Arabic or English)"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    min_score: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity score"),
    sura_no: Optional[int] = Query(None, description="Filter by Surah number"),
    juz_no: Optional[int] = Query(None, description="Filter by Juz number"),
    include_cross_language: bool = Query(True, description="Include cross-language expansion"),
):
    """
    Semantic search for Quran verses using vector embeddings.

    Supports Arabic and English queries for cross-language semantic matching.
    Uses Qdrant vector database for efficient similarity search.

    Arabic: البحث الدلالي في آيات القرآن باستخدام التضمينات المتجهة
    """
    from app.services.verse_embedding_service import get_verse_embedding_service
    from app.services.arabic_semantic_search import arabic_semantic_service

    verse_service = get_verse_embedding_service()

    # Check if index exists
    stats = await verse_service.get_collection_stats()
    if not stats.get("exists") or stats.get("vectors_count", 0) == 0:
        # Fallback to database search if index not built
        return {
            "ok": True,
            "query": query,
            "results": [],
            "total": 0,
            "index_status": "not_indexed",
            "message": "Verse embeddings not yet indexed. Use /admin/index-verses to build index.",
        }

    # Get cross-language expansion
    expanded = None
    if include_cross_language:
        expanded = arabic_semantic_service.expand_cross_language_query(query)

    # Perform semantic search
    results = await verse_service.semantic_search(
        query=query,
        limit=limit,
        min_score=min_score,
        sura_filter=sura_no,
        juz_filter=juz_no,
    )

    response = {
        "ok": True,
        "query": query,
        "results": [
            {
                "verse_id": r.verse_id,
                "sura_no": r.sura_no,
                "aya_no": r.aya_no,
                "reference": r.reference,
                "text_uthmani": r.text_uthmani,
                "text_imlaei": r.text_imlaei,
                "similarity_score": round(r.similarity_score, 4),
                "matched_themes": r.matched_themes,
            }
            for r in results
        ],
        "total": len(results),
        "index_status": "indexed",
        "vectors_count": stats.get("vectors_count", 0),
    }

    if expanded:
        response["cross_language_expansion"] = {
            "source_language": expanded.source_language,
            "arabic_terms": expanded.arabic_terms[:5],
            "english_terms": expanded.english_terms[:5],
            "detected_concepts": expanded.detected_concepts,
        }

    return response


@router.get("/search/similar/{sura_no}/{aya_no}")
async def find_similar_verses(
    sura_no: int = Path(..., ge=1, le=114, description="Surah number"),
    aya_no: int = Path(..., ge=1, description="Ayah number"),
    limit: int = Query(10, ge=1, le=30, description="Maximum results"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity"),
    exclude_same_sura: bool = Query(False, description="Exclude verses from same Surah"),
):
    """
    Find verses semantically similar to a specific verse.

    Uses vector embeddings to find thematically related verses across the Quran.

    Arabic: البحث عن آيات مشابهة لآية معينة
    """
    from app.services.verse_embedding_service import get_verse_embedding_service

    verse_service = get_verse_embedding_service()

    # Check if index exists
    stats = await verse_service.get_collection_stats()
    if not stats.get("exists") or stats.get("vectors_count", 0) == 0:
        return {
            "ok": True,
            "source_verse": f"{sura_no}:{aya_no}",
            "similar_verses": [],
            "total": 0,
            "index_status": "not_indexed",
        }

    results = await verse_service.find_similar_to_verse(
        sura_no=sura_no,
        aya_no=aya_no,
        limit=limit,
        min_score=min_score,
        exclude_same_sura=exclude_same_sura,
    )

    return {
        "ok": True,
        "source_verse": f"{sura_no}:{aya_no}",
        "similar_verses": [
            {
                "verse_id": r.verse_id,
                "sura_no": r.sura_no,
                "aya_no": r.aya_no,
                "reference": r.reference,
                "text_uthmani": r.text_uthmani,
                "text_imlaei": r.text_imlaei,
                "similarity_score": round(r.similarity_score, 4),
            }
            for r in results
        ],
        "total": len(results),
        "index_status": "indexed",
    }


@router.get("/search/semantic/stats")
async def get_semantic_search_stats():
    """
    Get statistics about the semantic search index.

    Arabic: إحصائيات فهرس البحث الدلالي
    """
    from app.services.verse_embedding_service import get_verse_embedding_service

    verse_service = get_verse_embedding_service()
    stats = await verse_service.get_collection_stats()

    return {
        "ok": True,
        "collection": "quran_verses",
        "stats": stats,
        "model": "multilingual-MiniLM-L12-v2",
        "embedding_dimension": 384,
    }


@router.post("/search/semantic/index")
async def index_verses_for_semantic_search(
    batch_size: int = Query(100, ge=10, le=500, description="Batch size for indexing"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Index all Quran verses for semantic search.

    Admin endpoint to build or rebuild the verse embedding index in Qdrant.
    This may take several minutes depending on the server.

    Arabic: فهرسة جميع الآيات للبحث الدلالي
    """
    from app.services.verse_embedding_service import get_verse_embedding_service

    verse_service = get_verse_embedding_service()

    # Get all verses from database
    result = await session.execute(
        select(QuranVerse)
        .join(QuranSurah, QuranVerse.sura_no == QuranSurah.number)
        .order_by(QuranVerse.sura_no, QuranVerse.aya_no)
    )
    verses = result.scalars().all()

    if not verses:
        return {
            "ok": False,
            "error": "No verses found in database",
        }

    # Prepare verses for indexing
    verse_dicts = []
    for v in verses:
        verse_dicts.append({
            "id": v.id,
            "sura_no": v.sura_no,
            "aya_no": v.aya_no,
            "juz_no": v.juz_no,
            "page_no": v.page_no,
            "text_uthmani": v.text_uthmani,
            "text_imlaei": v.text_imlaei,
            "sura_name_ar": "",  # Could be enriched
            "sura_name_en": "",
        })

    # Index verses
    indexed_count = await verse_service.index_verses(verse_dicts, batch_size=batch_size)

    return {
        "ok": True,
        "indexed_count": indexed_count,
        "total_verses": len(verses),
        "batch_size": batch_size,
    }


# =============================================================================
# Multi-Concept Search (Solomon and Queen of Sheba, etc.)
# =============================================================================

@router.get("/search/multi-concept")
async def search_multi_concept(
    query: str = Query(..., min_length=2, description="Multi-concept query (e.g., 'Solomon and Queen of Sheba')"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sura_no: Optional[int] = Query(None, description="Filter by Surah number"),
    connector: str = Query("or", description="Connector type: 'and' (all concepts required) or 'or' (any)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Multi-concept search for Quran verses.

    Parses queries like "Solomon and the Queen of Sheba" to find verses
    mentioning either or both concepts. Supports both Arabic and English
    concept names with automatic bilingual expansion.

    Examples:
    - "Solomon and Queen of Sheba" -> Finds verses about سليمان or ملكة سبأ
    - "موسى و فرعون" -> Finds verses about Moses or Pharaoh
    - "patience and gratitude" -> Finds verses about صبر or شكر

    Arabic: البحث متعدد المفاهيم في آيات القرآن
    """
    from app.services.quran_search import QuranSearchService
    from app.services.metrics import get_metrics

    metrics = get_metrics()
    search_service = QuranSearchService(session)

    result = await search_service.search_multi_concept(
        query=query,
        limit=limit,
        offset=offset,
        sura_filter=sura_no,
        connector_type=connector,
    )

    # Record metrics for performance monitoring
    metrics.record_search(
        search_type="multi_concept",
        latency=result.get("search_time_ms", 0) / 1000,  # Convert to seconds
        results_count=result.get("total_matches", 0),
    )

    return {
        "ok": True,
        **result,
    }


@router.get("/search/concept-suggestions")
async def get_concept_search_suggestions(
    query: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get auto-suggestions for concept search.

    Returns matching concepts from the bilingual concept database
    with Arabic and English forms for auto-complete.

    Arabic: الحصول على اقتراحات البحث عن المفاهيم
    """
    from app.services.quran_search import QuranSearchService

    search_service = QuranSearchService(session)
    suggestions = await search_service.get_concept_suggestions(query, limit)

    return {
        "ok": True,
        "query": query,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@router.get("/search/concepts/list")
async def list_available_concepts():
    """
    List all available concepts for multi-concept search.

    Returns the complete bilingual concept mapping with
    Arabic/English terms and relationships.

    Arabic: قائمة المفاهيم المتاحة للبحث
    """
    from app.services.quran_text_utils import BILINGUAL_CONCEPTS

    # Group concepts by category
    categories = {
        "prophets": [],
        "virtues": [],
        "places_events": [],
    }

    prophet_keys = {
        "solomon", "moses", "abraham", "ishmael", "isaac", "jacob", "joseph",
        "noah", "jesus", "mary", "david", "muhammad", "adam", "job", "jonah",
        "lot", "aaron", "shuayb", "hud", "salih", "zakariya", "john", "pharaoh",
        "queen_of_sheba",
    }

    place_event_keys = {
        "paradise", "hellfire", "day_of_judgment", "mecca", "kaaba",
    }

    for key, data in BILINGUAL_CONCEPTS.items():
        concept_info = {
            "key": key,
            "ar": data.get("ar", [])[:3],
            "en": data.get("en", [])[:3],
            "related": data.get("related", [])[:5],
        }

        if key in prophet_keys:
            categories["prophets"].append(concept_info)
        elif key in place_event_keys:
            categories["places_events"].append(concept_info)
        else:
            categories["virtues"].append(concept_info)

    return {
        "ok": True,
        "total_concepts": len(BILINGUAL_CONCEPTS),
        "categories": categories,
    }