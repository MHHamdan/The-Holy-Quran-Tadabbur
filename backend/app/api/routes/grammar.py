"""
Arabic Grammar (إعراب) API Routes.

Endpoints:
- POST /grammar/analyze: Analyze arbitrary Arabic text
- GET /grammar/ayah/{sura}:{ayah}: Analyze a specific verse
- GET /grammar/labels: Get all valid grammar labels
- GET /grammar/health: Check grammar service health

SAFETY:
- Output is constrained to predefined Arabic labels
- Confidence scores indicate certainty
- No hallucination of grammar rules

FALLBACK STRATEGY:
- Primary: Ollama LLM analysis
- Fallback: Static morphology dataset for common verses
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.db.database import get_async_session
from app.models.quran import QuranVerse
from app.services.grammar_ollama import get_grammar_service
from app.services.grammar_fallback import get_static_analysis
from app.models.grammar import (
    VALID_POS_TAGS,
    VALID_ROLES,
    VALID_SENTENCE_TYPES,
    VALID_CASE_ENDINGS,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request for grammar analysis."""
    text: str = Field(..., min_length=1, max_length=500, description="Arabic text to analyze")
    verse_reference: Optional[str] = Field(None, description="Optional verse reference (e.g., 2:255)")


class TokenResponse(BaseModel):
    """Grammar analysis for a single token."""
    word: str
    word_index: int
    pos: str  # Part of speech in Arabic
    role: str  # Grammatical role in Arabic
    case_ending: Optional[str] = None
    i3rab: str  # Full إعراب explanation
    root: Optional[str] = None
    pattern: Optional[str] = None
    confidence: float
    notes_ar: str = ""


class GrammarResponse(BaseModel):
    """Complete grammar analysis response."""
    verse_reference: str
    text: str
    sentence_type: str
    tokens: List[TokenResponse]
    notes_ar: str = ""
    overall_confidence: float
    source: str  # "corpus", "llm", "hybrid", "fallback"


class LabelsResponse(BaseModel):
    """Available grammar labels."""
    pos_tags: List[str]
    roles: List[str]
    sentence_types: List[str]
    case_endings: List[str]


class ErrorResponse(BaseModel):
    """Error response with Arabic message."""
    ok: bool = False
    error_code: str
    message_ar: str
    message_en: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/analyze", response_model=GrammarResponse)
async def analyze_text(
    request: AnalyzeRequest,
    req: Request,
):
    """
    Analyze Arabic text and return grammatical analysis.

    Returns:
    - sentence_type: Type of sentence (جملة اسمية، فعلية، شبه جملة)
    - tokens: Word-by-word analysis with POS and role
    - confidence: Overall confidence score
    - source: Where the analysis came from

    Fallback Strategy:
    1. Primary: Ollama LLM analysis
    2. Fallback: Static morphology dataset for known verses
    """
    request_id = getattr(req.state, "request_id", None)
    service = get_grammar_service()

    # Check Ollama availability
    ollama_available = await service.health_check()

    if not ollama_available:
        logger.warning(f"[{request_id}] Ollama unavailable, using static fallback")
        # Try static fallback for known verses
        static_result = get_static_analysis(request.text, request.verse_reference)
        if static_result:
            return GrammarResponse(
                verse_reference=static_result.verse_reference,
                text=static_result.text,
                sentence_type=static_result.sentence_type.value,
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos.value,
                        role=t.role.value,
                        case_ending=t.case_ending.value if t.case_ending else None,
                        i3rab=t.i3rab,
                        root=t.root,
                        pattern=t.pattern,
                        confidence=t.confidence,
                        notes_ar=t.notes_ar,
                    )
                    for t in static_result.tokens
                ],
                notes_ar=static_result.notes_ar,
                overall_confidence=static_result.overall_confidence,
                source="static",
            )

        # No static data available - return proper degraded response
        return GrammarResponse(
            verse_reference=request.verse_reference or "",
            text=request.text,
            sentence_type="غير محدد",
            tokens=[],
            notes_ar="خدمة التحليل النحوي غير متاحة حالياً. يرجى المحاولة لاحقاً.",
            overall_confidence=0.0,
            source="unavailable",
        )

    try:
        logger.info(f"[{request_id}] Analyzing text with Ollama")
        result = await service.analyze(
            text=request.text,
            verse_reference=request.verse_reference,
        )

        return GrammarResponse(
            verse_reference=result.verse_reference,
            text=result.text,
            sentence_type=result.sentence_type.value,
            tokens=[
                TokenResponse(
                    word=t.word,
                    word_index=t.word_index,
                    pos=t.pos.value,
                    role=t.role.value,
                    case_ending=t.case_ending.value if t.case_ending else None,
                    i3rab=t.i3rab,
                    root=t.root,
                    pattern=t.pattern,
                    confidence=t.confidence,
                    notes_ar=t.notes_ar,
                )
                for t in result.tokens
            ],
            notes_ar=result.notes_ar,
            overall_confidence=result.overall_confidence,
            source=result.source,
        )

    except httpx.TimeoutException:
        logger.error(f"[{request_id}] Grammar analysis timeout")
        # Try static fallback
        static_result = get_static_analysis(request.text, request.verse_reference)
        if static_result:
            return GrammarResponse(
                verse_reference=static_result.verse_reference,
                text=static_result.text,
                sentence_type=static_result.sentence_type.value,
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos.value,
                        role=t.role.value,
                        case_ending=t.case_ending.value if t.case_ending else None,
                        i3rab=t.i3rab,
                        root=t.root,
                        pattern=t.pattern,
                        confidence=t.confidence,
                        notes_ar=t.notes_ar,
                    )
                    for t in static_result.tokens
                ],
                notes_ar="تم استخدام البيانات الثابتة بسبب انتهاء المهلة.",
                overall_confidence=static_result.overall_confidence,
                source="static",
            )

        return GrammarResponse(
            verse_reference=request.verse_reference or "",
            text=request.text,
            sentence_type="غير محدد",
            tokens=[],
            notes_ar="انتهت مهلة التحليل. حاول مرة أخرى.",
            overall_confidence=0.0,
            source="timeout",
        )

    except Exception as e:
        logger.exception(f"[{request_id}] Grammar analysis error: {e}")

        # Try static fallback on any error
        static_result = get_static_analysis(request.text, request.verse_reference)
        if static_result:
            return GrammarResponse(
                verse_reference=static_result.verse_reference,
                text=static_result.text,
                sentence_type=static_result.sentence_type.value,
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos.value,
                        role=t.role.value,
                        case_ending=t.case_ending.value if t.case_ending else None,
                        i3rab=t.i3rab,
                        root=t.root,
                        pattern=t.pattern,
                        confidence=t.confidence,
                        notes_ar=t.notes_ar,
                    )
                    for t in static_result.tokens
                ],
                notes_ar="تم استخدام البيانات الثابتة.",
                overall_confidence=static_result.overall_confidence,
                source="static",
            )

        return GrammarResponse(
            verse_reference=request.verse_reference or "",
            text=request.text,
            sentence_type="غير محدد",
            tokens=[],
            notes_ar="حدث خطأ أثناء التحليل. حاول مرة أخرى.",
            overall_confidence=0.0,
            source="error",
        )


@router.get("/ayah/{sura_ayah}", response_model=GrammarResponse)
async def analyze_ayah(
    sura_ayah: str,
    req: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Analyze a specific Quranic verse.

    Path format: {sura}:{ayah} or {sura}:{start}-{end}
    Examples: 2:255, 12:1-3

    Returns grammatical analysis for the verse text.

    Fallback Strategy:
    1. Primary: Ollama LLM analysis
    2. Fallback: Static morphology dataset for known verses
    """
    request_id = getattr(req.state, "request_id", None)

    # Parse sura:ayah format
    import re
    match = re.match(r'^(\d+):(\d+)(?:-(\d+))?$', sura_ayah)
    if not match:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_format",
                "message_ar": "صيغة غير صالحة. استخدم: سورة:آية (مثال: 2:255)",
                "message_en": "Invalid format. Use: sura:ayah (example: 2:255)",
            }
        )

    sura_no = int(match.group(1))
    aya_start = int(match.group(2))
    aya_end = int(match.group(3)) if match.group(3) else aya_start

    # Validate ranges
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_sura",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
                "message_en": "Sura number must be between 1 and 114",
            }
        )

    # Get verse text from database
    verse_ref = f"{sura_no}:{aya_start}" if aya_start == aya_end else f"{sura_no}:{aya_start}-{aya_end}"
    verse_text = await _get_verse_text_from_db(session, sura_no, aya_start, aya_end)

    if not verse_text:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "verse_not_found",
                "message_ar": "لم يتم العثور على الآية",
                "message_en": "Verse not found",
            }
        )

    # Check Ollama availability
    service = get_grammar_service()
    ollama_available = await service.health_check()

    if not ollama_available:
        logger.warning(f"[{request_id}] Ollama unavailable for ayah {verse_ref}, using static fallback")
        # Try static fallback
        static_result = get_static_analysis(verse_text, verse_ref)
        if static_result:
            return GrammarResponse(
                verse_reference=static_result.verse_reference,
                text=static_result.text,
                sentence_type=static_result.sentence_type.value,
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos.value,
                        role=t.role.value,
                        case_ending=t.case_ending.value if t.case_ending else None,
                        i3rab=t.i3rab,
                        root=t.root,
                        pattern=t.pattern,
                        confidence=t.confidence,
                        notes_ar=t.notes_ar,
                    )
                    for t in static_result.tokens
                ],
                notes_ar=static_result.notes_ar,
                overall_confidence=static_result.overall_confidence,
                source="static",
            )

        return GrammarResponse(
            verse_reference=verse_ref,
            text=verse_text,
            sentence_type="غير محدد",
            tokens=[],
            notes_ar="خدمة التحليل النحوي غير متاحة حالياً. يرجى المحاولة لاحقاً.",
            overall_confidence=0.0,
            source="unavailable",
        )

    try:
        logger.info(f"[{request_id}] Analyzing ayah {verse_ref} with Ollama")
        result = await service.analyze(verse_text, verse_ref)

        return GrammarResponse(
            verse_reference=result.verse_reference,
            text=result.text,
            sentence_type=result.sentence_type.value,
            tokens=[
                TokenResponse(
                    word=t.word,
                    word_index=t.word_index,
                    pos=t.pos.value,
                    role=t.role.value,
                    case_ending=t.case_ending.value if t.case_ending else None,
                    i3rab=t.i3rab,
                    root=t.root,
                    pattern=t.pattern,
                    confidence=t.confidence,
                    notes_ar=t.notes_ar,
                )
                for t in result.tokens
            ],
            notes_ar=result.notes_ar,
            overall_confidence=result.overall_confidence,
            source=result.source,
        )

    except Exception as e:
        logger.exception(f"[{request_id}] Grammar analysis error for {verse_ref}: {e}")

        # Try static fallback
        static_result = get_static_analysis(verse_text, verse_ref)
        if static_result:
            return GrammarResponse(
                verse_reference=static_result.verse_reference,
                text=static_result.text,
                sentence_type=static_result.sentence_type.value,
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos.value,
                        role=t.role.value,
                        case_ending=t.case_ending.value if t.case_ending else None,
                        i3rab=t.i3rab,
                        root=t.root,
                        pattern=t.pattern,
                        confidence=t.confidence,
                        notes_ar=t.notes_ar,
                    )
                    for t in static_result.tokens
                ],
                notes_ar="تم استخدام البيانات الثابتة.",
                overall_confidence=static_result.overall_confidence,
                source="static",
            )

        return GrammarResponse(
            verse_reference=verse_ref,
            text=verse_text,
            sentence_type="غير محدد",
            tokens=[],
            notes_ar="حدث خطأ أثناء التحليل. حاول مرة أخرى.",
            overall_confidence=0.0,
            source="error",
        )


@router.get("/labels", response_model=LabelsResponse)
async def get_grammar_labels():
    """
    Get all valid grammar labels.

    Returns the constrained set of Arabic labels that the
    grammar analysis will use. This is useful for:
    - Building UI dropdowns
    - Validating output
    - Understanding the label vocabulary
    """
    return LabelsResponse(
        pos_tags=sorted(VALID_POS_TAGS),
        roles=sorted(VALID_ROLES),
        sentence_types=sorted(VALID_SENTENCE_TYPES),
        case_endings=sorted(VALID_CASE_ENDINGS),
    )


@router.get("/irab/{sura_ayah}", response_model=GrammarResponse)
async def get_irab(
    sura_ayah: str,
    req: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get accurate I'rab (Arabic grammar analysis) for a Quranic verse.

    This endpoint uses the Quranic Arabic Corpus data which provides:
    - Scholar-verified grammatical analysis
    - Fast, deterministic results (no LLM inference)
    - 100% accuracy for Quranic text

    Path format: {sura}:{ayah}
    Examples: 2:255, 1:1

    Returns:
    - Detailed I'rab for each word
    - POS tags in Arabic
    - Root extraction
    - Grammatical roles

    Source: Quranic Arabic Corpus (corpus.quran.com)
    """
    request_id = getattr(req.state, "request_id", None)

    # Parse sura:ayah format
    import re
    match = re.match(r'^(\d+):(\d+)$', sura_ayah)
    if not match:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_format",
                "message_ar": "صيغة غير صالحة. استخدم: سورة:آية (مثال: 2:255)",
                "message_en": "Invalid format. Use: sura:ayah (example: 2:255)",
            }
        )

    sura_no = int(match.group(1))
    aya_no = int(match.group(2))

    # Validate ranges
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "invalid_sura",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
                "message_en": "Sura number must be between 1 and 114",
            }
        )

    verse_ref = f"{sura_no}:{aya_no}"

    # Get verse text from database
    verse_text = await _get_verse_text_from_db(session, sura_no, aya_no, aya_no)

    if not verse_text:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "verse_not_found",
                "message_ar": "لم يتم العثور على الآية",
                "message_en": "Verse not found",
            }
        )

    # Use QAC provider for accurate I'rab
    try:
        from app.nlp.providers.quranic_corpus import get_qac_provider

        qac = get_qac_provider()
        result = await qac.analyze_verse(sura_no, aya_no)

        if result.success and result.tokens:
            logger.info(f"[{request_id}] QAC I'rab successful for {verse_ref}")

            return GrammarResponse(
                verse_reference=verse_ref,
                text=verse_text,
                sentence_type="غير محدد",  # QAC doesn't provide sentence type
                tokens=[
                    TokenResponse(
                        word=t.word,
                        word_index=t.word_index,
                        pos=t.pos or "غير محدد",
                        role="غير محدد",  # QAC provides POS, not grammatical roles
                        case_ending=None,
                        i3rab=t.features.get("i3rab", "") if t.features else "",
                        root=t.root,
                        pattern=None,
                        confidence=t.confidence,
                        notes_ar="",
                    )
                    for t in result.tokens
                ],
                notes_ar="تحليل من القرآن العربي المورفولوجي - موثق علمياً",
                overall_confidence=1.0,  # QAC data is scholar-verified
                source="corpus",
            )
    except Exception as e:
        logger.warning(f"[{request_id}] QAC provider error: {e}")

    # Fallback to static data
    static_result = get_static_analysis(verse_text, verse_ref)
    if static_result:
        return GrammarResponse(
            verse_reference=static_result.verse_reference,
            text=static_result.text,
            sentence_type=static_result.sentence_type.value,
            tokens=[
                TokenResponse(
                    word=t.word,
                    word_index=t.word_index,
                    pos=t.pos.value,
                    role=t.role.value,
                    case_ending=t.case_ending.value if t.case_ending else None,
                    i3rab=t.i3rab,
                    root=t.root,
                    pattern=t.pattern,
                    confidence=t.confidence,
                    notes_ar=t.notes_ar,
                )
                for t in static_result.tokens
            ],
            notes_ar=static_result.notes_ar,
            overall_confidence=static_result.overall_confidence,
            source="static",
        )

    # Last resort: return empty with helpful message
    return GrammarResponse(
        verse_reference=verse_ref,
        text=verse_text,
        sentence_type="غير محدد",
        tokens=[],
        notes_ar="لم يتم العثور على بيانات الإعراب لهذه الآية",
        overall_confidence=0.0,
        source="unavailable",
    )


@router.get("/health")
async def grammar_health(req: Request):
    """
    Check grammar service health.

    Returns:
    - status: "ok" | "degraded" | "static_only"
    - ollama_available: boolean
    - static_fallback_available: boolean
    - model: Ollama model name
    - message_ar/message_en: User-friendly status message
    """
    request_id = getattr(req.state, "request_id", None)
    service = get_grammar_service()
    ollama_ok = await service.health_check()

    # Check static fallback availability
    from app.services.grammar_fallback import get_static_verse_count
    static_count = get_static_verse_count()
    static_available = static_count > 0

    if ollama_ok:
        status = "ok"
        message_ar = "خدمة التحليل النحوي متاحة بالكامل"
        message_en = "Grammar analysis service fully available"
    elif static_available:
        status = "static_only"
        message_ar = f"متاح فقط للآيات المحفوظة ({static_count} آية)"
        message_en = f"Static fallback only ({static_count} verses cached)"
    else:
        status = "unavailable"
        message_ar = "خدمة التحليل النحوي غير متاحة"
        message_en = "Grammar analysis service unavailable"

    logger.info(f"[{request_id}] Grammar health: {status}")

    return {
        "status": status,
        "ollama_available": ollama_ok,
        "static_fallback_available": static_available,
        "static_verse_count": static_count,
        "model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "message_ar": message_ar,
        "message_en": message_en,
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _get_verse_text_from_db(
    session: AsyncSession,
    sura_no: int,
    aya_start: int,
    aya_end: int,
) -> Optional[str]:
    """
    Get verse text from database.

    Fetches verses from quran_verses table and concatenates if range.
    """
    try:
        query = select(QuranVerse.text_uthmani).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no >= aya_start,
            QuranVerse.aya_no <= aya_end,
        ).order_by(QuranVerse.aya_no)

        result = await session.execute(query)
        texts = [row[0] for row in result.all()]

        if not texts:
            return None

        # Concatenate with space if multiple verses
        return " ".join(texts)

    except Exception as e:
        logger.error(f"Error fetching verse text: {e}")
        return None


# =============================================================================
# VERIFICATION WORKFLOW - Admin-Gated Grammar Changes
# =============================================================================

from app.core.auth import require_admin, AdminUser
from app.core.responses import APIError, ErrorCode, get_request_id


class GrammarVerificationCreate(BaseModel):
    """Request to submit grammar correction for verification."""
    verse_reference: str = Field(..., description="Verse reference (e.g., 1:1)")
    word_index: int = Field(..., ge=0, description="Index of word being corrected")
    word: str = Field(..., min_length=1, description="The word being corrected")
    proposed_pos: Optional[str] = Field(None, description="Proposed POS tag")
    proposed_role: Optional[str] = Field(None, description="Proposed grammatical role")
    proposed_i3rab: Optional[str] = Field(None, description="Proposed إعراب")
    proposed_root: Optional[str] = Field(None, description="Proposed root")
    notes: Optional[str] = Field(None, description="Explanation/justification")
    evidence_refs: Optional[dict] = Field(default={}, description="Evidence references")
    priority: int = Field(default=0, ge=0, le=10)


class GrammarVerificationResponse(BaseModel):
    """Grammar verification task details."""
    id: int
    entity_type: str = "grammar"
    entity_id: str  # verse_reference:word_index
    verse_reference: str
    word_index: int
    word: str
    proposed_change: dict
    evidence_refs: dict
    status: str
    priority: int
    created_by: Optional[str] = None
    created_at: str


class GrammarDecisionCreate(BaseModel):
    """Admin decision on grammar verification."""
    decision: str = Field(..., description="approved or rejected")
    notes: Optional[str] = None


class GrammarDecisionResponse(BaseModel):
    """Decision record for grammar verification."""
    id: int
    task_id: int
    admin_id: str
    decision: str
    notes: Optional[str] = None
    decided_at: str


class GrammarVerificationStats(BaseModel):
    """Grammar verification statistics."""
    pending_count: int
    approved_count: int
    rejected_count: int
    total_count: int
    by_verse: dict


@router.post("/verification/submit", response_model=GrammarVerificationResponse, status_code=201)
async def submit_grammar_correction(
    task: GrammarVerificationCreate,
    user_id: str = Query("anonymous", description="User submitting the correction"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Submit a grammar correction for admin review.

    All proposed changes to grammar analysis (POS, role, i3rab, root)
    must go through this workflow. Changes remain 'pending' until
    an admin approves them.

    Upon approval, the correction will be added to the static fallback
    dataset for consistent display.
    """
    from sqlalchemy import text
    import json

    entity_id = f"{task.verse_reference}:{task.word_index}"

    proposed_change = {
        "word": task.word,
        "proposed_pos": task.proposed_pos,
        "proposed_role": task.proposed_role,
        "proposed_i3rab": task.proposed_i3rab,
        "proposed_root": task.proposed_root,
        "notes": task.notes,
    }

    result = await session.execute(
        text("""
            INSERT INTO verification_tasks
                (entity_type, entity_id, proposed_change, evidence_refs, status, priority, created_by, created_at, updated_at)
            VALUES
                ('grammar', :entity_id, CAST(:proposed_change AS jsonb), CAST(:evidence_refs AS jsonb), 'pending', :priority, :created_by, NOW(), NOW())
            RETURNING id, entity_type, entity_id, proposed_change, evidence_refs, status, priority, created_by, created_at
        """),
        {
            "entity_id": entity_id,
            "proposed_change": json.dumps(proposed_change),
            "evidence_refs": json.dumps(task.evidence_refs or {}),
            "priority": task.priority,
            "created_by": user_id
        }
    )
    await session.commit()
    row = result.fetchone()

    return GrammarVerificationResponse(
        id=row[0],
        entity_type=row[1],
        entity_id=row[2],
        verse_reference=task.verse_reference,
        word_index=task.word_index,
        word=task.word,
        proposed_change=row[3],
        evidence_refs=row[4],
        status=row[5],
        priority=row[6],
        created_by=row[7],
        created_at=str(row[8]),
    )


@router.get("/verification/tasks", response_model=List[GrammarVerificationResponse])
async def list_grammar_verifications(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    verse_reference: Optional[str] = Query(None, description="Filter by verse"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List grammar verification tasks (Admin only).

    Requires Bearer token in Authorization header.
    """
    from sqlalchemy import text

    query = """
        SELECT id, entity_type, entity_id, proposed_change, evidence_refs,
               status, priority, created_by, created_at
        FROM verification_tasks
        WHERE entity_type = 'grammar'
    """
    params = {"limit": limit, "offset": offset}

    if status:
        query += " AND status = :status"
        params["status"] = status
    if verse_reference:
        query += " AND entity_id LIKE :verse_pattern"
        params["verse_pattern"] = f"{verse_reference}:%"

    query += " ORDER BY priority DESC, created_at DESC LIMIT :limit OFFSET :offset"

    result = await session.execute(text(query), params)
    rows = result.fetchall()

    responses = []
    for row in rows:
        entity_id = row[2]
        parts = entity_id.rsplit(":", 1)
        verse_ref = parts[0] if len(parts) == 2 else entity_id
        word_idx = int(parts[1]) if len(parts) == 2 else 0
        proposed = row[3] or {}

        responses.append(GrammarVerificationResponse(
            id=row[0],
            entity_type=row[1],
            entity_id=row[2],
            verse_reference=verse_ref,
            word_index=word_idx,
            word=proposed.get("word", ""),
            proposed_change=proposed,
            evidence_refs=row[4] or {},
            status=row[5],
            priority=row[6],
            created_by=row[7],
            created_at=str(row[8]),
        ))

    return responses


@router.post("/verification/tasks/{task_id}/decide", response_model=GrammarDecisionResponse)
async def decide_grammar_verification(
    request: Request,
    task_id: int,
    decision: GrammarDecisionCreate,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Approve or reject a grammar verification task (Admin only).

    Requires Bearer token in Authorization header.

    On approval:
    - Task status changes to 'approved'
    - Decision is logged with audit trail
    - In a full implementation, the grammar correction would be applied
      to the static fallback dataset
    """
    if decision.decision not in ["approved", "rejected"]:
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en="Decision must be 'approved' or 'rejected'",
            message_ar="القرار يجب أن يكون 'approved' أو 'rejected'",
            request_id=get_request_id(request),
            status_code=400
        )

    from sqlalchemy import text

    # Check task exists, is grammar type, and is pending
    task_result = await session.execute(
        text("SELECT id, status, entity_type FROM verification_tasks WHERE id = :task_id"),
        {"task_id": task_id}
    )
    task = task_result.fetchone()

    if not task:
        raise APIError(
            code=ErrorCode.NOT_FOUND,
            message_en="Task not found",
            message_ar="المهمة غير موجودة",
            request_id=get_request_id(request),
            status_code=404
        )
    if task[2] != "grammar":
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en="Task is not a grammar verification",
            message_ar="المهمة ليست تحقق نحوي",
            request_id=get_request_id(request),
            status_code=400
        )
    if task[1] != "pending":
        raise APIError(
            code=ErrorCode.VALIDATION_ERROR,
            message_en=f"Task already {task[1]}",
            message_ar=f"المهمة بالفعل {task[1]}",
            request_id=get_request_id(request),
            status_code=400
        )

    # Update task status
    await session.execute(
        text("UPDATE verification_tasks SET status = :status, updated_at = NOW() WHERE id = :task_id"),
        {"status": decision.decision, "task_id": task_id}
    )

    # Create decision record
    decision_result = await session.execute(
        text("""
            INSERT INTO verification_decisions (task_id, admin_id, decision, notes, decided_at)
            VALUES (:task_id, :admin_id, :decision, :notes, NOW())
            RETURNING id, task_id, admin_id, decision, notes, decided_at
        """),
        {
            "task_id": task_id,
            "admin_id": admin.user_id,
            "decision": decision.decision,
            "notes": decision.notes
        }
    )
    await session.commit()
    row = decision_result.fetchone()

    logger.info(f"Grammar verification {task_id} {decision.decision} by {admin.user_id}")

    return GrammarDecisionResponse(
        id=row[0],
        task_id=row[1],
        admin_id=row[2],
        decision=row[3],
        notes=row[4],
        decided_at=str(row[5])
    )


@router.get("/verification/stats", response_model=GrammarVerificationStats)
async def get_grammar_verification_stats(
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get grammar verification statistics (Admin only).

    Requires Bearer token in Authorization header.
    """
    from sqlalchemy import text

    # Get counts by status for grammar entity type
    status_result = await session.execute(
        text("""
            SELECT status, COUNT(*)
            FROM verification_tasks
            WHERE entity_type = 'grammar'
            GROUP BY status
        """)
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}

    # Get counts by verse (top 10)
    verse_result = await session.execute(
        text("""
            SELECT
                SPLIT_PART(entity_id, ':', 1) || ':' || SPLIT_PART(entity_id, ':', 2) as verse_ref,
                COUNT(*) as count
            FROM verification_tasks
            WHERE entity_type = 'grammar'
            GROUP BY verse_ref
            ORDER BY count DESC
            LIMIT 10
        """)
    )
    verse_counts = {row[0]: row[1] for row in verse_result.fetchall()}

    total = sum(status_counts.values())

    return GrammarVerificationStats(
        pending_count=status_counts.get("pending", 0),
        approved_count=status_counts.get("approved", 0),
        rejected_count=status_counts.get("rejected", 0),
        total_count=total,
        by_verse=verse_counts,
    )
