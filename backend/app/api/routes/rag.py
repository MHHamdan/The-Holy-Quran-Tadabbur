"""
RAG API routes for grounded Quranic Q&A.

CRITICAL: All responses MUST be grounded in retrieved sources.
NEVER generate tafseer without proper citations.

ERROR HANDLING:
- All errors return structured JSON with error_id for tracing
- Arabic error messages are always included
- Internal details are NEVER exposed to client
- Correlation IDs enable reproduction of any error
"""
from typing import List, Optional, Union
from datetime import datetime
import logging
import httpx
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.core.config import settings
from app.core.errors import (
    ErrorCode,
    RAGError,
    RAGRequestContext,
    create_error,
)
from app.rag.pipeline import RAGPipeline
from app.rag.types import QueryIntent, RelatedVerse, TafsirExplanation
from app.services.redis_cache import RedisCache
from app.services.conversation_service import (
    get_conversation_service,
    ConversationSession,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# RAG response cache - 1 hour TTL for grounded responses
# Uses Redis for distributed caching across instances
_rag_cache: Optional[RedisCache] = None

def get_rag_cache() -> RedisCache:
    """Get or create RAG cache instance."""
    global _rag_cache
    if _rag_cache is None:
        _rag_cache = RedisCache(
            url=settings.redis_url,
            key_prefix="tadabbur:rag:",
            default_ttl=3600,  # 1 hour for RAG responses
        )
    return _rag_cache


def make_rag_cache_key(request: "AskRequest") -> str:
    """Generate cache key from request parameters."""
    # Normalize question: lowercase, strip whitespace
    normalized_question = request.question.lower().strip()

    # Include all parameters that affect the response
    key_parts = [
        normalized_question,
        request.language,
        str(request.include_scholarly_debate),
        ",".join(sorted(request.preferred_sources)) if request.preferred_sources else "",
        str(request.max_sources),
    ]

    # Create hash for storage efficiency
    key_string = "|".join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]

    return f"ask:{key_hash}"


# Request/Response schemas
class AskRequest(BaseModel):
    """Request schema for asking questions."""
    question: str = Field(..., min_length=5, max_length=1000)
    language: str = Field(default="en", pattern="^(ar|en)$")
    include_scholarly_debate: bool = Field(default=True)
    preferred_sources: List[str] = Field(default=[])
    max_sources: int = Field(default=5, ge=1, le=20)
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation continuity")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean question."""
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Question must be at least 5 characters")
        return v


class FollowUpRequest(BaseModel):
    """Request schema for follow-up questions."""
    session_id: str = Field(..., description="Session ID from previous question")
    question: str = Field(..., min_length=5, max_length=1000)
    language: str = Field(default="en", pattern="^(ar|en)$")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean question."""
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Question must be at least 5 characters")
        return v


class ExpandRequest(BaseModel):
    """Request schema for expanding on a topic."""
    session_id: str = Field(..., description="Session ID from previous question")
    topic: str = Field(..., min_length=3, max_length=500, description="Topic to expand on")
    verse_reference: Optional[str] = Field(default=None, description="Specific verse to expand on")
    language: str = Field(default="en", pattern="^(ar|en)$")


class Citation(BaseModel):
    """Citation reference in response."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str
    verse_reference: str
    excerpt: str
    relevance_score: float


class EvidenceChunk(BaseModel):
    """Raw evidence chunk for transparency panel."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str
    verse_reference: str
    sura_no: int
    aya_start: int
    aya_end: int
    content: str
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    relevance_score: float
    methodology: Optional[str] = None


class EvidenceDensity(BaseModel):
    """Evidence density metadata for transparency."""
    chunk_count: int = Field(ge=0, description="Number of distinct evidence chunks used")
    source_count: int = Field(ge=0, description="Number of distinct tafseer sources used")


class RelatedVerseResponse(BaseModel):
    """A Quranic verse related to the query."""
    sura_no: int
    aya_no: int
    verse_reference: str
    text_ar: str
    text_en: str
    sura_name_ar: Optional[str] = None
    sura_name_en: Optional[str] = None
    topic: Optional[str] = None
    relevance_score: float


class TafsirExplanationResponse(BaseModel):
    """A tafsir explanation from a specific source."""
    source_id: str
    source_name: str
    source_name_ar: str
    author_name: Optional[str] = None
    author_name_ar: Optional[str] = None
    methodology: Optional[str] = None
    explanation: str
    verse_reference: str
    era: str = "classical"
    reliability_score: float = 0.8


class GroundedResponse(BaseModel):
    """Grounded response with mandatory citations."""
    answer: str
    citations: List[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: Optional[str] = None  # high, medium, low, borderline, insufficient
    confidence_message: Optional[str] = None
    scholarly_consensus: Optional[str] = None  # "agreed", "majority", "disputed"
    warnings: List[str] = []
    related_queries: List[str] = []
    intent: str
    processing_time_ms: int
    query_expansion: Optional[List[str]] = None
    degradation_reasons: List[str] = []
    # Evidence density for user transparency (read-only, no raw IDs)
    evidence_density: Optional[EvidenceDensity] = None
    # Raw evidence chunks for transparency panel
    evidence: List[EvidenceChunk] = []
    # Cache indicator
    cached: bool = False
    # API version for compatibility
    api_version: Optional[str] = None
    # === NEW: Chat experience fields ===
    # Session ID for conversation continuity
    session_id: Optional[str] = None
    # Related Quranic verses - displayed first
    related_verses: List[RelatedVerseResponse] = []
    # Tafsir explanations grouped by source for accordion display
    tafsir_by_source: Optional[dict] = None  # Dict[str, List[TafsirExplanationResponse]]
    # Follow-up question suggestions
    follow_up_suggestions: List[str] = []


class ValidationResult(BaseModel):
    """Citation validation result."""
    is_valid: bool
    valid_citations: List[str]
    invalid_citations: List[str]
    missing_citations: List[str]
    coverage_score: float


# Error response schema for OpenAPI docs
class ErrorResponse(BaseModel):
    """Structured error response with bilingual messages."""
    ok: bool = False
    error_code: str
    error_id: str
    message: str
    message_ar: str
    message_en: str
    timestamp: str


# Routes
@router.post("/ask", response_model=Union[GroundedResponse, ErrorResponse])
async def ask_question(
    request: AskRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Ask a question about the Quran with grounded, cited response.

    SAFETY RULES:
    - All claims MUST be backed by retrieved tafseer chunks
    - Citations are MANDATORY and validated
    - If evidence is insufficient, returns safe refusal
    - For fiqh questions, clearly states this is informational only

    ERROR HANDLING:
    - Returns structured error with error_id for tracing
    - Arabic messages always included (message_ar)
    - Never exposes internal details or stack traces

    RETURNS:
    - On success: GroundedResponse with answer, citations, confidence
    - On error: ErrorResponse with error_code, error_id, bilingual messages
    """
    # Create request context for tracing
    ctx = RAGRequestContext.create(request.question, request.language)
    logger.info(f"RAG request [{ctx.correlation_id}]: language={request.language}, sources={len(request.preferred_sources)}")

    # Check cache first for faster responses
    cache_key = make_rag_cache_key(request)
    rag_cache = get_rag_cache()

    try:
        cached_response = await rag_cache.get(cache_key)
        if cached_response:
            logger.info(f"RAG cache HIT [{ctx.correlation_id}]: returning cached response")
            # Add cache indicator to response
            cached_response["cached"] = True
            cached_response["request_id"] = ctx.correlation_id
            cached_response["processing_time_ms"] = 0  # Instant from cache
            return cached_response
    except Exception as e:
        logger.warning(f"RAG cache check failed [{ctx.correlation_id}]: {e}")
        # Continue without cache on error

    logger.info(f"RAG cache MISS [{ctx.correlation_id}]: processing query")

    # Check for LLM provider configuration
    if settings.llm_provider == "claude" and not settings.anthropic_api_key:
        error = create_error(
            ErrorCode.CONFIGURATION_ERROR,
            ctx.correlation_id,
            internal_details="ANTHROPIC_API_KEY not configured for Claude provider"
        )
        error.log(ctx.question_hash)
        return JSONResponse(
            status_code=503,
            content=error.to_response(request.language)
        )

    # Verify LLM availability
    if settings.llm_provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                if resp.status_code != 200:
                    error = create_error(
                        ErrorCode.LLM_UNAVAILABLE,
                        ctx.correlation_id,
                        internal_details=f"Ollama returned status {resp.status_code}"
                    )
                    error.log(ctx.question_hash)
                    return JSONResponse(
                        status_code=503,
                        content=error.to_response(request.language)
                    )
        except httpx.TimeoutException:
            error = create_error(
                ErrorCode.LLM_UNAVAILABLE,
                ctx.correlation_id,
                internal_details="Ollama health check timed out"
            )
            error.log(ctx.question_hash)
            return JSONResponse(
                status_code=503,
                content=error.to_response(request.language)
            )
        except httpx.RequestError as e:
            error = create_error(
                ErrorCode.LLM_UNAVAILABLE,
                ctx.correlation_id,
                internal_details=f"Cannot connect to Ollama: {type(e).__name__}"
            )
            error.log(ctx.question_hash)
            return JSONResponse(
                status_code=503,
                content=error.to_response(request.language)
            )

    try:
        # Initialize RAG pipeline
        pipeline = RAGPipeline(session)
        ctx.llm_provider = settings.llm_provider

        # Get or create conversation session for chat continuity
        conv_service = get_conversation_service()
        conv_session = await conv_service.get_or_create_session(
            session_id=request.session_id,
            language=request.language,
            preferred_sources=request.preferred_sources,
        )

        # Get conversation context for follow-up questions
        conversation_context = None
        if conv_session.messages:
            conversation_context = conv_session.get_context_for_llm(max_messages=4)

        # Process query with session context
        result = await pipeline.query(
            question=request.question,
            language=request.language,
            include_scholarly_debate=request.include_scholarly_debate,
            preferred_sources=request.preferred_sources,
            max_sources=request.max_sources,
            session_id=conv_session.session_id,
            conversation_context=conversation_context,
        )

        # Store conversation messages
        # Extract verse references from related_verses
        verse_refs = [v.verse_reference for v in result.related_verses] if result.related_verses else []

        await conv_service.add_message(
            session_id=conv_session.session_id,
            role="user",
            content=request.question,
            verses_referenced=[],
        )
        await conv_service.add_message(
            session_id=conv_session.session_id,
            role="assistant",
            content=result.answer[:500],  # Truncate for storage
            verses_referenced=verse_refs,
        )

        # Update context with stats
        ctx.retrieval_chunk_count = result.evidence_chunk_count
        ctx.retrieval_source_count = result.evidence_source_count
        ctx.llm_latency_ms = result.processing_time_ms

        # Check if we got insufficient evidence (this is a controlled failure)
        if result.confidence == 0.0 and not result.citations:
            error = create_error(
                ErrorCode.INSUFFICIENT_EVIDENCE,
                ctx.correlation_id,
                internal_details="No chunks retrieved or all filtered",
                retrieval_stats={
                    "chunk_count": ctx.retrieval_chunk_count,
                    "source_count": ctx.retrieval_source_count,
                }
            )
            error.log(ctx.question_hash)
            # Return the result anyway (it has safe refusal message)
            # but add error_id for tracing
            response_dict = result.to_dict()
            response_dict["error_id"] = ctx.correlation_id
            return response_dict

        # Calculate total processing time
        processing_time = int((datetime.now() - ctx.start_time).total_seconds() * 1000)
        result.processing_time_ms = processing_time

        # Log success
        ctx.log_success()

        # Convert to dict and add correlation ID for transparency
        response_dict = result.to_dict()
        response_dict["request_id"] = ctx.correlation_id
        response_dict["cached"] = False

        # Cache successful responses with good confidence
        if result.confidence >= 0.3:  # Only cache meaningful responses
            try:
                await rag_cache.set(cache_key, response_dict, ttl=3600)  # 1 hour TTL
                logger.info(f"RAG cache STORED [{ctx.correlation_id}]: confidence={result.confidence:.2f}")
            except Exception as e:
                logger.warning(f"RAG cache store failed [{ctx.correlation_id}]: {e}")

        return response_dict

    except httpx.TimeoutException as e:
        error = create_error(
            ErrorCode.TIMEOUT,
            ctx.correlation_id,
            internal_details=f"LLM request timed out: {type(e).__name__}"
        )
        error.log(ctx.question_hash)
        return JSONResponse(
            status_code=504,
            content=error.to_response(request.language)
        )

    except Exception as e:
        # Catch-all for unexpected errors
        error = create_error(
            ErrorCode.INTERNAL_ERROR,
            ctx.correlation_id,
            internal_details=f"{type(e).__name__}: {str(e)}"
        )
        error.log(ctx.question_hash)
        logger.exception(f"Unexpected error in RAG [{ctx.correlation_id}]")
        return JSONResponse(
            status_code=500,
            content=error.to_response(request.language)
        )


# ============================================================================
# NEW: Chat Experience Endpoints
# ============================================================================

@router.post("/ask/followup", response_model=Union[GroundedResponse, ErrorResponse])
async def ask_followup_question(
    request: FollowUpRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Ask a follow-up question within an existing conversation session.

    This endpoint preserves conversation context from previous questions,
    allowing for a more natural chat-like experience.

    The session must exist (created from a previous /ask call).
    """
    # Get conversation service and session
    conv_service = get_conversation_service()
    conv_session = await conv_service.get_session(request.session_id)

    if not conv_session:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error_code": "SESSION_NOT_FOUND",
                "error_id": request.session_id,
                "message": "Session not found or expired",
                "message_ar": "الجلسة غير موجودة أو منتهية",
                "message_en": "Session not found or expired",
                "timestamp": datetime.now().isoformat(),
            }
        )

    # Build conversation context
    conversation_context = conv_session.get_context_for_llm(max_messages=6)

    try:
        # Initialize RAG pipeline
        pipeline = RAGPipeline(session)

        # Process follow-up query with context
        result = await pipeline.query(
            question=request.question,
            language=request.language,
            include_scholarly_debate=True,
            preferred_sources=conv_session.preferred_sources,
            max_sources=5,
            session_id=conv_session.session_id,
            conversation_context=conversation_context,
        )

        # Store follow-up messages
        verse_refs = [v.verse_reference for v in result.related_verses] if result.related_verses else []

        await conv_service.add_message(
            session_id=conv_session.session_id,
            role="user",
            content=request.question,
            verses_referenced=[],
        )
        await conv_service.add_message(
            session_id=conv_session.session_id,
            role="assistant",
            content=result.answer[:500],
            verses_referenced=verse_refs,
        )

        return result.to_dict()

    except Exception as e:
        logger.exception(f"Error in follow-up question: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_code": "INTERNAL_ERROR",
                "error_id": request.session_id,
                "message": str(e),
                "message_ar": "حدث خطأ أثناء معالجة السؤال",
                "message_en": "An error occurred while processing the question",
                "timestamp": datetime.now().isoformat(),
            }
        )


@router.post("/ask/expand", response_model=Union[GroundedResponse, ErrorResponse])
async def expand_topic(
    request: ExpandRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get expanded explanation on a specific topic or verse.

    This endpoint provides deeper analysis of a topic discussed
    in a previous question within the same session.
    """
    # Get conversation service and session
    conv_service = get_conversation_service()
    conv_session = await conv_service.get_session(request.session_id)

    if not conv_session:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error_code": "SESSION_NOT_FOUND",
                "error_id": request.session_id,
                "message": "Session not found or expired",
                "message_ar": "الجلسة غير موجودة أو منتهية",
                "message_en": "Session not found or expired",
                "timestamp": datetime.now().isoformat(),
            }
        )

    # Build expansion query
    if request.verse_reference:
        expansion_query = f"Explain in detail verse {request.verse_reference} regarding: {request.topic}"
    else:
        expansion_query = f"Provide a detailed explanation of: {request.topic}"

    # Build conversation context
    conversation_context = conv_session.get_context_for_llm(max_messages=4)

    try:
        # Initialize RAG pipeline
        pipeline = RAGPipeline(session)

        # Process expansion query
        result = await pipeline.query(
            question=expansion_query,
            language=request.language,
            include_scholarly_debate=True,
            preferred_sources=conv_session.preferred_sources,
            max_sources=7,  # More sources for expansion
            session_id=conv_session.session_id,
            conversation_context=conversation_context,
        )

        # Store expansion request
        await conv_service.add_message(
            session_id=conv_session.session_id,
            role="user",
            content=f"[Expand] {request.topic}",
            verses_referenced=[request.verse_reference] if request.verse_reference else [],
        )

        return result.to_dict()

    except Exception as e:
        logger.exception(f"Error in expand topic: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_code": "INTERNAL_ERROR",
                "error_id": request.session_id,
                "message": str(e),
                "message_ar": "حدث خطأ أثناء التوسع في الموضوع",
                "message_en": "An error occurred while expanding the topic",
                "timestamp": datetime.now().isoformat(),
            }
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get conversation session history.

    Returns the messages and metadata for a conversation session.
    Sessions expire after 24 hours of inactivity.
    """
    conv_service = get_conversation_service()
    conv_session = await conv_service.get_session(session_id)

    if not conv_session:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "Session not found or expired",
                "error_ar": "الجلسة غير موجودة أو منتهية",
            }
        )

    return {
        "ok": True,
        "session": {
            "session_id": conv_session.session_id,
            "language": conv_session.language,
            "preferred_sources": conv_session.preferred_sources,
            "created_at": conv_session.created_at,
            "last_activity": conv_session.last_activity,
            "message_count": len(conv_session.messages),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "verses_referenced": msg.verses_referenced,
                }
                for msg in conv_session.messages
            ],
        }
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a conversation session.

    Permanently removes the session and all its messages.
    """
    conv_service = get_conversation_service()
    deleted = await conv_service.delete_session(session_id)

    if deleted:
        return {"ok": True, "message": "Session deleted"}
    else:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error": "Session not found or already deleted"}
        )


# ============================================================================
# Existing Endpoints
# ============================================================================

class ValidateCitationsRequest(BaseModel):
    """Request schema for citation validation."""
    answer: str = Field(..., description="Answer text with citations")
    retrieved_chunk_ids: List[str] = Field(..., description="List of retrieved chunk IDs")


@router.post("/validate-citations", response_model=ValidationResult)
async def validate_citations(
    request: ValidateCitationsRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Validate that all citations in an answer exist in retrieved sources.

    Used to verify RAG response integrity before displaying to users.
    """
    from app.validators.citation_validator import CitationValidator

    validator = CitationValidator(session)
    result = await validator.validate(request.answer, request.retrieved_chunk_ids)

    return ValidationResult(
        is_valid=result.is_valid,
        valid_citations=result.valid_citations,
        invalid_citations=result.invalid_citations,
        missing_citations=result.missing_citations,
        coverage_score=result.coverage_score,
    )


@router.get("/intents")
async def get_query_intents():
    """
    Get available query intent types.
    """
    return {
        "intents": [
            {
                "id": "verse_meaning",
                "name_en": "Verse Meaning",
                "name_ar": "معنى الآية",
                "description": "Questions about the meaning of specific verses",
            },
            {
                "id": "story_exploration",
                "name_en": "Story Exploration",
                "name_ar": "استكشاف القصة",
                "description": "Questions about prophets and Quranic stories",
            },
            {
                "id": "theme_search",
                "name_en": "Theme Search",
                "name_ar": "البحث عن موضوع",
                "description": "Questions about topics and themes in Quran",
            },
            {
                "id": "comparative",
                "name_en": "Comparative",
                "name_ar": "مقارنة",
                "description": "Comparing verses or interpretations",
            },
            {
                "id": "linguistic",
                "name_en": "Linguistic",
                "name_ar": "لغوي",
                "description": "Arabic grammar, root words, rhetoric",
            },
            {
                "id": "ruling",
                "name_en": "Ruling (Informational)",
                "name_ar": "الحكم (معلوماتي)",
                "description": "Fiqh-related questions (informational only, not fatwa)",
            },
        ]
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get RAG cache statistics for monitoring.

    Returns hit rate, total hits/misses, and connection status.
    Useful for monitoring cache effectiveness and performance.
    """
    cache = get_rag_cache()
    stats = cache._stats

    return {
        "ok": True,
        "cache": {
            "connected": stats.connected,
            "hits": stats.hits,
            "misses": stats.misses,
            "errors": stats.errors,
            "hit_rate": f"{stats.hit_rate:.2%}",
            "hit_rate_raw": stats.hit_rate,
            "last_error": stats.last_error,
            "last_error_time": stats.last_error_time.isoformat() if stats.last_error_time else None,
        },
        "config": {
            "ttl_seconds": 3600,
            "min_confidence_for_cache": 0.3,
        }
    }


@router.delete("/cache/clear")
async def clear_rag_cache():
    """
    Clear all cached RAG responses.

    Admin endpoint for forcing cache refresh when tafseer data is updated.
    """
    cache = get_rag_cache()
    try:
        # Clear all keys with the rag: prefix
        if cache._connected and cache._client:
            keys = await cache._client.keys(f"{cache.key_prefix}ask:*")
            if keys:
                await cache._client.delete(*keys)
                return {"ok": True, "cleared_keys": len(keys)}
            return {"ok": True, "cleared_keys": 0}
        return {"ok": False, "error": "Cache not connected"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/cache/warm")
async def warm_rag_cache_endpoint(
    languages: List[str] = Query(["en", "ar"], description="Languages to warm"),
    max_questions: Optional[int] = Query(None, description="Max questions per language"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Warm the RAG cache with popular questions.

    Pre-populates the cache with answers to common questions
    to improve response time for users.

    NOTE: This can take several minutes to complete as it
    processes each question through the full RAG pipeline.
    """
    from app.services.cache_warmer import warm_rag_cache

    try:
        result = await warm_rag_cache(
            session,
            languages=languages,
            max_questions=max_questions,
        )
        return {
            "ok": True,
            "warming_result": result,
        }
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        return {
            "ok": False,
            "error": str(e),
        }


@router.get("/reranker/status")
async def get_reranker_status():
    """
    Get the status of the cross-encoder reranker.

    Returns information about:
    - Whether reranking is available
    - Method being used (cross_encoder or keyword_overlap)
    - Model details and device (GPU/CPU)
    """
    from app.rag.reranker import is_reranker_available, RERANKER_CONFIG

    status = is_reranker_available()
    return {
        "ok": True,
        "reranker": {
            **status,
            "config": {
                "enabled": RERANKER_CONFIG.get("enabled", True),
                "use_cross_encoder": RERANKER_CONFIG.get("use_cross_encoder", True),
                "max_input_length": RERANKER_CONFIG.get("max_input_length", 512),
            }
        }
    }


@router.get("/sample-questions")
async def get_sample_questions(
    language: str = Query("en", pattern="^(ar|en)$"),
):
    """
    Get sample questions for each intent type.
    """
    samples = {
        "en": [
            {
                "intent": "verse_meaning",
                "question": "What is the meaning of Ayat al-Kursi (2:255)?",
            },
            {
                "intent": "story_exploration",
                "question": "Tell me about the story of Prophet Yusuf and his brothers",
            },
            {
                "intent": "theme_search",
                "question": "What does the Quran say about patience (sabr)?",
            },
            {
                "intent": "comparative",
                "question": "How is the story of Musa narrated differently in Surah Al-Qasas vs Surah Taha?",
            },
            {
                "intent": "linguistic",
                "question": "What is the root word and meaning of 'taqwa'?",
            },
        ],
        "ar": [
            {
                "intent": "verse_meaning",
                "question": "ما معنى آية الكرسي؟",
            },
            {
                "intent": "story_exploration",
                "question": "أخبرني عن قصة يوسف عليه السلام مع إخوته",
            },
            {
                "intent": "theme_search",
                "question": "ماذا يقول القرآن عن الصبر؟",
            },
        ],
    }

    return {"language": language, "samples": samples.get(language, samples["en"])}


@router.get("/suggestions")
async def get_query_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial query for suggestions"),
    language: str = Query("en", pattern="^(ar|en)$"),
    limit: int = Query(8, ge=1, le=20),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get auto-suggestions for the Ask page search box.

    Returns relevant suggestions based on:
    - Concept names matching the query
    - Prophet and story names
    - Sample questions containing similar terms
    - Common Islamic terminology

    Used for real-time search suggestions as user types.
    """
    from sqlalchemy import select, or_, func
    from app.models.concept import Concept
    from app.rag.query_expander import ISLAMIC_TERM_MAPPINGS

    suggestions = []
    q_lower = q.lower().strip()

    # 1. Search concepts for matching names
    try:
        if language == "ar":
            query = (
                select(Concept.label_ar, Concept.concept_type)
                .where(
                    or_(
                        func.lower(Concept.label_ar).contains(q),
                        func.lower(Concept.label_en).contains(q_lower),
                    )
                )
                .limit(limit)
            )
        else:
            query = (
                select(Concept.label_en, Concept.concept_type)
                .where(
                    or_(
                        func.lower(Concept.label_en).contains(q_lower),
                        func.lower(Concept.label_ar).contains(q),
                    )
                )
                .limit(limit)
            )

        result = await session.execute(query)
        for row in result:
            label = row[0]
            concept_type = row[1]
            if label:
                # Format as question based on concept type
                if concept_type == "person":
                    suggestion = f"Tell me about {label}" if language == "en" else f"أخبرني عن {label}"
                elif concept_type in ("theme", "moral_pattern"):
                    suggestion = f"What does the Quran say about {label}?" if language == "en" else f"ماذا يقول القرآن عن {label}؟"
                else:
                    suggestion = f"Explain {label}" if language == "en" else f"اشرح {label}"
                suggestions.append({
                    "text": suggestion,
                    "type": "concept",
                    "concept_type": concept_type,
                })
    except Exception as e:
        logger.warning(f"Concept search failed: {e}")

    # 2. Search Islamic terminology mappings
    for term, (arabic, translits, synonyms, _) in ISLAMIC_TERM_MAPPINGS.items():
        # Match against English term, Arabic, transliterations
        if (q_lower in term.lower() or
            q in arabic or
            any(q_lower in t.lower() for t in translits) or
            any(q_lower in s.lower() for s in synonyms)):

            if language == "ar":
                suggestion = f"ما معنى {arabic}؟"
            else:
                suggestion = f"What is the meaning of {term}?"

            if {"text": suggestion} not in [{"text": s["text"]} for s in suggestions]:
                suggestions.append({
                    "text": suggestion,
                    "type": "term",
                })

            if len(suggestions) >= limit:
                break

    # 3. Add template suggestions based on common query patterns
    templates = {
        "en": [
            f"What does the Quran say about {q}?",
            f"Story of {q} in the Quran",
            f"Meaning of {q} in Arabic",
            f"Verses about {q}",
        ],
        "ar": [
            f"ماذا يقول القرآن عن {q}؟",
            f"قصة {q} في القرآن",
            f"معنى {q}",
            f"آيات عن {q}",
        ],
    }

    for template in templates.get(language, templates["en"]):
        if len(suggestions) >= limit:
            break
        if not any(s["text"] == template for s in suggestions):
            suggestions.append({
                "text": template,
                "type": "template",
            })

    return {
        "ok": True,
        "query": q,
        "suggestions": suggestions[:limit],
        "count": len(suggestions[:limit]),
    }


class TafseerSourceInfo(BaseModel):
    """Tafseer source information with provenance."""
    id: str
    name_ar: str
    name_en: str
    author_ar: Optional[str] = None
    author_en: Optional[str] = None
    methodology: Optional[str] = None
    era: Optional[str] = None
    language: str
    reliability_score: float
    is_primary_source: bool
    is_enabled: bool = True  # Admin control

    # Provenance (for transparency)
    version_tag: Optional[str] = None
    license_type: Optional[str] = None
    license: Optional[str] = None
    license_verified: bool = False
    has_valid_provenance: bool = False
    ayah_count: Optional[int] = None


class SourcesResponse(BaseModel):
    """Response containing all tafseer sources."""
    sources: List[TafseerSourceInfo]
    count: int
    provenance_verified: int  # Number with valid provenance


@router.get("/sources", response_model=SourcesResponse)
async def get_available_sources(
    language: str = Query(None, pattern="^(ar|en)$", description="Filter by language"),
    include_provenance: bool = Query(True, description="Include provenance metadata"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get available tafseer sources with full transparency.

    This endpoint exposes:
    - Source metadata (name, author, methodology)
    - Provenance data (version, license, verification status)
    - Quality indicators (reliability score, primary source status)

    NOTE: This PUBLIC endpoint only returns ENABLED sources.
    Use /admin/sources with admin token to see all sources.

    Used for:
    - Mobile app source selection
    - Transparency about data origins
    - Citation verification
    """
    from sqlalchemy import select
    from app.models.tafseer import TafseerSource

    # PUBLIC endpoint: Only return ENABLED sources (is_enabled is INTEGER: 1=enabled, 0=disabled)
    query = (
        select(TafseerSource)
        .where(TafseerSource.is_enabled == 1)
        .order_by(TafseerSource.reliability_score.desc())
    )

    if language:
        query = query.where(TafseerSource.language == language)

    result = await session.execute(query)
    sources = result.scalars().all()

    source_infos = []
    provenance_verified = 0

    for s in sources:
        has_provenance = s.has_valid_provenance
        if has_provenance:
            provenance_verified += 1

        info = TafseerSourceInfo(
            id=s.id,
            name_ar=s.name_ar,
            name_en=s.name_en,
            author_ar=s.author_ar,
            author_en=s.author_en,
            methodology=s.methodology,
            era=s.era,
            language=s.language,
            reliability_score=s.reliability_score or 0.0,
            is_primary_source=bool(s.is_primary_source),
            is_enabled=bool(s.is_enabled) if s.is_enabled is not None else True,
            version_tag=s.version_tag if include_provenance else None,
            license_type=s.license_type if include_provenance else None,
            license=s.license if include_provenance else None,
            license_verified=bool(s.license_verified) if include_provenance else False,
            has_valid_provenance=has_provenance,
            ayah_count=s.ayah_count if include_provenance else None,
        )
        source_infos.append(info)

    return SourcesResponse(
        sources=source_infos,
        count=len(source_infos),
        provenance_verified=provenance_verified,
    )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

class ToggleSourceRequest(BaseModel):
    """Request to toggle source enabled status."""
    is_enabled: bool


class ToggleSourceResponse(BaseModel):
    """Response from toggling source."""
    source_id: str
    is_enabled: bool
    message: str


def verify_admin_token(x_admin_token: str = Header(..., description="Admin token for authentication")):
    """
    Verify admin token from X-Admin-Token header.

    SECURITY: Admin token MUST be sent via header, never via query parameter.
    Query parameters leak in browser history, server logs, and Referer headers.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=503,
            detail="Admin token not configured. Set ADMIN_TOKEN environment variable."
        )
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin token"
        )
    return True


@router.put("/admin/sources/{source_id}/toggle", response_model=ToggleSourceResponse)
async def toggle_source_enabled(
    source_id: str,
    request: ToggleSourceRequest,
    session: AsyncSession = Depends(get_async_session),
    _: bool = Depends(verify_admin_token),
):
    """
    Enable or disable a tafseer source for RAG.

    Requires admin token authentication.
    Disabled sources will not be retrieved for RAG queries.
    """
    from sqlalchemy import select, update
    from app.models.tafseer import TafseerSource

    # Check if source exists
    result = await session.execute(
        select(TafseerSource).where(TafseerSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_id}' not found"
        )

    # Update source
    await session.execute(
        update(TafseerSource)
        .where(TafseerSource.id == source_id)
        .values(is_enabled=1 if request.is_enabled else 0)
    )
    await session.commit()

    status = "enabled" if request.is_enabled else "disabled"
    return ToggleSourceResponse(
        source_id=source_id,
        is_enabled=request.is_enabled,
        message=f"Source '{source_id}' has been {status}"
    )


@router.get("/admin/sources", response_model=SourcesResponse)
async def get_all_sources_admin(
    session: AsyncSession = Depends(get_async_session),
    _: bool = Depends(verify_admin_token),
):
    """
    Get all sources including disabled ones (admin only).
    """
    from sqlalchemy import select
    from app.models.tafseer import TafseerSource

    query = select(TafseerSource).order_by(TafseerSource.reliability_score.desc())
    result = await session.execute(query)
    sources = result.scalars().all()

    source_infos = []
    provenance_verified = 0

    for s in sources:
        has_provenance = s.has_valid_provenance
        if has_provenance:
            provenance_verified += 1

        info = TafseerSourceInfo(
            id=s.id,
            name_ar=s.name_ar,
            name_en=s.name_en,
            author_ar=s.author_ar,
            author_en=s.author_en,
            methodology=s.methodology,
            era=s.era,
            language=s.language,
            reliability_score=s.reliability_score or 0.0,
            is_primary_source=bool(s.is_primary_source),
            is_enabled=bool(s.is_enabled) if s.is_enabled is not None else True,
            version_tag=s.version_tag,
            license_type=s.license_type,
            license=s.license,
            license_verified=bool(s.license_verified),
            has_valid_provenance=has_provenance,
            ayah_count=s.ayah_count,
        )
        source_infos.append(info)

    return SourcesResponse(
        sources=source_infos,
        count=len(source_infos),
        provenance_verified=provenance_verified,
    )
