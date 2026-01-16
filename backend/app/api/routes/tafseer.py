"""
Tafseer API Routes - FAANG-Optimized for Performance.

Provides endpoints for accessing Quranic tafsir and translations
from multiple sources including alquran.cloud API.

Performance optimizations:
- Redis caching via HybridCache for distributed caching
- HTTP cache headers for browser/CDN caching
- Request timeouts for LLM services
- Async operations with proper error handling

Endpoints:
- GET /editions - List available tafseer editions
- GET /{surah}/{ayah} - Get tafseer for a specific verse
- GET /surah/{surah} - Get tafseer for entire surah
- GET /health - Check tafseer service health
"""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Response
from pydantic import BaseModel, Field
import logging
import asyncio
import hashlib
from datetime import datetime

from app.services.tafseer_api import (
    get_tafseer_client,
    TafseerEdition,
    EDITION_METADATA,
)
from app.services.tafsir_api import external_tafsir_service, tafsir_llm_service, TAFSIR_EDITIONS
from app.services.redis_cache import get_hybrid_cache
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tafseer", tags=["tafseer"])

# =============================================================================
# Cache Configuration
# =============================================================================

# Cache TTLs (in seconds)
CACHE_TTL_EDITIONS = 86400      # 24 hours for editions list
CACHE_TTL_TAFSIR = 3600         # 1 hour for tafsir text
CACHE_TTL_LLM = 1800            # 30 minutes for LLM responses

# LLM Timeout (in seconds)
LLM_TIMEOUT = 30.0


def set_cache_headers(response: Response, max_age: int = 3600, etag_data: str = "") -> None:
    """Set HTTP cache headers for optimal browser/CDN caching."""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    if etag_data:
        etag = hashlib.md5(etag_data.encode()).hexdigest()[:16]
        response.headers["ETag"] = f'"{etag}"'
    response.headers["Vary"] = "Accept-Encoding"


# =============================================================================
# Response Models
# =============================================================================

class EditionResponse(BaseModel):
    """Response model for a tafseer edition."""
    identifier: str
    name_ar: str
    name_en: str
    author_ar: str = ""
    author_en: str = ""
    language: str
    type: str = "tafsir"

    class Config:
        json_schema_extra = {
            "example": {
                "identifier": "ar.muyassar",
                "name_ar": "التفسير الميسر",
                "name_en": "Al-Muyassar (Simplified)",
                "author_ar": "مجمع الملك فهد",
                "author_en": "King Fahd Complex",
                "language": "ar",
                "type": "tafsir",
            }
        }


class EditionsListResponse(BaseModel):
    """Response model for editions list."""
    ok: bool = True
    editions: List[EditionResponse]
    total: int


class TafseerVerseResponse(BaseModel):
    """Response model for a single tafseer verse."""
    surah: int
    ayah: int
    text: str
    edition: str
    edition_name: str
    language: str


class TafseerResponse(BaseModel):
    """Response model for tafseer request."""
    ok: bool = True
    surah: int
    ayah: int
    tafasir: List[TafseerVerseResponse] = []
    latency_ms: int = 0
    error: Optional[str] = None


class SurahTafseerResponse(BaseModel):
    """Response model for surah tafseer."""
    ok: bool = True
    surah: int
    edition: str
    verses: List[TafseerVerseResponse] = []
    total: int = 0


class HealthResponse(BaseModel):
    """Response model for health check."""
    ok: bool
    api_available: bool
    editions_count: int
    message_ar: str
    message_en: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/editions", response_model=EditionsListResponse)
async def list_editions(
    language: Optional[str] = Query(None, description="Filter by language (ar, en)"),
) -> EditionsListResponse:
    """
    List available tafseer and translation editions.

    Returns all editions from alquran.cloud that are enabled for use.
    Can be filtered by language.
    """
    client = get_tafseer_client()

    # Check if feature is enabled
    if not settings.feature_external_tafseer:
        # Return only local/known editions
        editions = []
        for identifier, metadata in EDITION_METADATA.items():
            if language and not identifier.startswith(language):
                continue
            editions.append(EditionResponse(
                identifier=identifier,
                name_ar=metadata["name_ar"],
                name_en=metadata["name_en"],
                author_ar=metadata.get("author_ar", ""),
                author_en=metadata.get("author_en", ""),
                language="ar" if identifier.startswith("ar") else "en",
                type="tafsir" if "tafsir" in identifier or identifier.startswith("ar") else "translation",
            ))
        return EditionsListResponse(
            ok=True,
            editions=editions,
            total=len(editions),
        )

    # Fetch from API
    try:
        api_editions = await client.get_editions()
        editions = []

        for ed in api_editions:
            if language and ed.language != language:
                continue

            metadata = client.get_edition_metadata(ed.identifier)
            editions.append(EditionResponse(
                identifier=ed.identifier,
                name_ar=metadata.get("name_ar", ed.name),
                name_en=metadata.get("name_en", ed.english_name),
                author_ar=metadata.get("author_ar", ""),
                author_en=metadata.get("author_en", ""),
                language=ed.language,
                type=ed.type,
            ))

        return EditionsListResponse(
            ok=True,
            editions=editions,
            total=len(editions),
        )

    except Exception as e:
        logger.error(f"Failed to list editions: {e}")
        raise HTTPException(status_code=503, detail="Tafseer service unavailable")


@router.get("/surah/{surah}", response_model=SurahTafseerResponse)
async def get_surah_tafseer(
    surah: int,
    edition: str = Query(
        "ar.muyassar",
        description="Edition identifier",
    ),
) -> SurahTafseerResponse:
    """
    Get tafseer for an entire surah.

    Returns tafseer content for all ayahs in the surah.
    Only one edition at a time to avoid large responses.
    """
    # Validate surah
    if not 1 <= surah <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURAH",
                "message": "Surah must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    client = get_tafseer_client()

    try:
        verses = await client.get_surah_tafseer(surah, edition)

        return SurahTafseerResponse(
            ok=True,
            surah=surah,
            edition=edition,
            verses=[
                TafseerVerseResponse(
                    surah=v.surah,
                    ayah=v.ayah,
                    text=v.text,
                    edition=v.edition,
                    edition_name=v.edition_name,
                    language=v.language,
                )
                for v in verses
            ],
            total=len(verses),
        )

    except Exception as e:
        logger.error(f"Failed to get surah tafseer: {e}")
        raise HTTPException(status_code=503, detail="Tafseer service unavailable")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check tafseer service health.

    Returns status of the alquran.cloud API and available editions.
    """
    client = get_tafseer_client()

    api_available = await client.health_check()
    editions_count = 0

    if api_available:
        try:
            editions = await client.get_editions()
            editions_count = len(editions)
        except Exception:
            pass

    if api_available:
        return HealthResponse(
            ok=True,
            api_available=True,
            editions_count=editions_count,
            message_ar="خدمة التفسير متاحة",
            message_en="Tafseer service is available",
        )
    else:
        return HealthResponse(
            ok=False,
            api_available=False,
            editions_count=0,
            message_ar="خدمة التفسير غير متاحة حالياً",
            message_en="Tafseer service is currently unavailable",
        )


# =============================================================================
# External Tafsir API (with Audio Support)
# =============================================================================

class ExternalEditionResponse(BaseModel):
    """Response model for an external tafsir edition with audio support."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    author_ar: str
    author_en: str
    language: str
    has_audio: bool
    source: str


class ExternalEditionsResponse(BaseModel):
    """Response for external editions list."""
    ok: bool = True
    editions: List[ExternalEditionResponse]
    total: int


class ExternalTafsirResponse(BaseModel):
    """Response for external tafsir with audio."""
    ok: bool = True
    verse_key: str
    text: str
    source: str
    edition: dict
    audio_url: Optional[str] = None


class AudioUrlResponse(BaseModel):
    """Response for audio URL."""
    ok: bool = True
    edition_id: str
    sura: int
    audio_url: Optional[str] = None
    has_audio: bool


@router.get("/external/editions", response_model=ExternalEditionsResponse)
async def list_external_editions(
    language: Optional[str] = Query(None, description="Filter by language (ar, en)"),
    has_audio: Optional[bool] = Query(None, description="Filter by audio availability"),
) -> ExternalEditionsResponse:
    """
    List available external tafsir editions.

    Returns editions from Quran.com API and read.tafsir.one with audio availability.
    """
    editions = external_tafsir_service.get_editions(language=language, has_audio=has_audio)
    return ExternalEditionsResponse(
        ok=True,
        editions=[ExternalEditionResponse(**ed) for ed in editions],
        total=len(editions),
    )


@router.get("/external/audio/{edition_id}/{sura}", response_model=AudioUrlResponse)
async def get_tafsir_audio_url(
    edition_id: str,
    sura: int,
) -> AudioUrlResponse:
    """
    Get audio URL for a tafsir edition and sura.

    Audio is available from read.tafsir.one for supported editions.
    Returns the direct MP3 URL for streaming.
    """
    if not 1 <= sura <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURA",
                "message": "Sura must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    audio_url = external_tafsir_service.get_audio_url(edition_id, sura)
    edition = TAFSIR_EDITIONS.get(edition_id)

    return AudioUrlResponse(
        ok=True,
        edition_id=edition_id,
        sura=sura,
        audio_url=audio_url,
        has_audio=edition.has_audio if edition else False,
    )


@router.get("/external/verse/{sura}/{ayah}", response_model=ExternalTafsirResponse)
async def get_external_tafsir(
    sura: int,
    ayah: int,
    edition: str = Query("muyassar", description="Edition identifier"),
    response: Response = None,
) -> ExternalTafsirResponse:
    """
    Get tafsir for a specific verse from external API.

    Fetches from Quran.com API or read.tafsir.one based on edition.
    Includes audio URL if available for the edition.

    Performance: Uses Redis caching + HTTP cache headers.
    """
    if not 1 <= sura <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURA",
                "message": "Sura must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    # Check Redis cache first
    cache_key = f"tafsir:external:{edition}:{sura}:{ayah}"
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)

    if cached:
        logger.debug(f"Cache HIT: {cache_key}")
        # Set cache headers
        if response:
            set_cache_headers(response, max_age=CACHE_TTL_TAFSIR, etag_data=cache_key)
        return ExternalTafsirResponse(**cached)

    # Fetch from external API
    result = await external_tafsir_service.get_tafsir(edition, sura, ayah)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TAFSIR_NOT_FOUND",
                "message": f"Tafsir not found for {sura}:{ayah} in edition {edition}",
                "message_ar": f"التفسير غير موجود للآية {sura}:{ayah}",
            }
        )

    # Build response
    response_data = {
        "ok": True,
        "verse_key": result.get("verse_key", f"{sura}:{ayah}"),
        "text": result.get("text", ""),
        "source": result.get("source", ""),
        "edition": result.get("edition", {}),
        "audio_url": result.get("audio_url"),
    }

    # Cache the result
    await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_TAFSIR)

    # Set cache headers
    if response:
        set_cache_headers(response, max_age=CACHE_TTL_TAFSIR, etag_data=cache_key)

    return ExternalTafsirResponse(**response_data)


@router.get("/quran-com/verse/{sura}/{ayah}")
async def get_quran_com_tafsir(
    sura: int,
    ayah: int,
    tafsir_id: int = Query(169, description="Quran.com tafsir ID (169=Ibn Kathir EN, 168=Ma'arif, 817=Tazkirul)"),
    response: Response = None,
) -> dict:
    """
    Get tafsir directly from Quran.com API v4 using tafsir ID.

    This endpoint is specifically for English tafsirs from Quran.com.
    Common IDs:
    - 169: Ibn Kathir (English)
    - 168: Ma'arif al-Qur'an
    - 817: Tazkirul Quran

    Performance: Uses Redis caching + HTTP cache headers.
    """
    if not 1 <= sura <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURA",
                "message": "Sura must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    # Check Redis cache first
    cache_key = f"tafsir:quran_com:{tafsir_id}:{sura}:{ayah}"
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)

    if cached:
        logger.debug(f"Cache HIT: {cache_key}")
        if response:
            set_cache_headers(response, max_age=CACHE_TTL_TAFSIR, etag_data=cache_key)
        return cached

    # Fetch from Quran.com API
    result = await external_tafsir_service.fetch_from_quran_com(tafsir_id, sura, ayah)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TAFSIR_NOT_FOUND",
                "message": f"Tafsir not found for {sura}:{ayah} with tafsir_id {tafsir_id}",
                "message_ar": f"التفسير غير موجود للآية {sura}:{ayah}",
            }
        )

    # Build response
    response_data = {
        "ok": True,
        "verse_key": f"{sura}:{ayah}",
        "text": result.get("text", ""),
        "source": "quran_com",
        "tafsir_id": tafsir_id,
        "resource_name": result.get("resource_name", ""),
    }

    # Cache the result
    await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_TAFSIR)

    # Set cache headers
    if response:
        set_cache_headers(response, max_age=CACHE_TTL_TAFSIR, etag_data=cache_key)

    return response_data


@router.get("/external/compare/{sura}/{ayah}")
async def compare_external_tafsirs(
    sura: int,
    ayah: int,
    editions: str = Query("muyassar,ibn_kathir,saadi", description="Comma-separated edition IDs"),
) -> dict:
    """
    Compare tafsir from multiple editions for a verse.

    Returns tafsir text from multiple scholars for comparison.
    """
    if not 1 <= sura <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURA",
                "message": "Sura must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    edition_list = [e.strip() for e in editions.split(",")]
    results = await external_tafsir_service.get_multiple_tafsirs(edition_list, sura, ayah)

    return {
        "ok": True,
        "verse_key": f"{sura}:{ayah}",
        "tafsirs": results,
        "editions_requested": len(edition_list),
        "editions_found": len(results),
    }


# =============================================================================
# LLM-Enhanced Tafsir Endpoints
# =============================================================================

class LLMSummarizeRequest(BaseModel):
    """Request model for tafsir summarization."""
    tafsir_text: str = Field(..., description="The tafsir text to summarize")
    verse_text: str = Field(..., description="The Quranic verse text")
    language: str = Field("ar", description="Output language (ar/en)")


class LLMExplainWordRequest(BaseModel):
    """Request model for word explanation."""
    word: str = Field(..., description="The word to explain")
    verse_text: str = Field(..., description="The Quranic verse containing the word")
    context: str = Field("", description="Optional tafsir context")
    language: str = Field("ar", description="Output language (ar/en)")


class LLMQuestionRequest(BaseModel):
    """Request model for Q&A about tafsir."""
    question: str = Field(..., description="The question to answer")
    verse_text: str = Field(..., description="The Quranic verse text")
    tafsir_text: str = Field(..., description="The tafsir text for context")
    language: str = Field("ar", description="Output language (ar/en)")


class LLMResponse(BaseModel):
    """Response model for LLM operations."""
    ok: bool = True
    result: Optional[str] = None
    error: Optional[str] = None


@router.post("/llm/summarize", response_model=LLMResponse)
async def summarize_tafsir(request: LLMSummarizeRequest) -> LLMResponse:
    """
    Generate a concise summary of tafsir text using LLM.

    Provides a 2-3 sentence summary highlighting:
    - Main meaning of the verse
    - Key lessons and insights

    Performance: 30-second timeout, Redis caching for repeated requests.
    """
    # Check cache first
    cache_key = f"llm:summary:{hashlib.md5((request.tafsir_text[:100] + request.verse_text).encode()).hexdigest()}"
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)

    if cached:
        logger.debug(f"LLM Cache HIT: {cache_key}")
        return LLMResponse(**cached)

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            tafsir_llm_service.summarize_tafsir(
                tafsir_text=request.tafsir_text,
                verse_text=request.verse_text,
                language=request.language,
            ),
            timeout=LLM_TIMEOUT
        )

        if result:
            response_data = {"ok": True, "result": result, "error": None}
            # Cache successful results
            await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_LLM)
            return LLMResponse(**response_data)
        else:
            return LLMResponse(
                ok=False,
                error="LLM service unavailable" if request.language == "en" else "خدمة الذكاء الاصطناعي غير متاحة"
            )
    except asyncio.TimeoutError:
        logger.error(f"LLM summarize timeout after {LLM_TIMEOUT}s")
        return LLMResponse(
            ok=False,
            error="Request timeout" if request.language == "en" else "انتهت مهلة الطلب"
        )
    except Exception as e:
        logger.error(f"LLM summarize error: {e}")
        return LLMResponse(ok=False, error=str(e))


@router.post("/llm/explain-word", response_model=LLMResponse)
async def explain_word(request: LLMExplainWordRequest) -> LLMResponse:
    """
    Explain a specific word in the context of the verse using LLM.

    Provides:
    - Linguistic meaning
    - Quranic context meaning
    - Special connotations

    Performance: 30-second timeout, Redis caching for repeated requests.
    """
    # Check cache first
    cache_key = f"llm:explain:{hashlib.md5((request.word + request.verse_text[:50]).encode()).hexdigest()}"
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)

    if cached:
        logger.debug(f"LLM Cache HIT: {cache_key}")
        return LLMResponse(**cached)

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            tafsir_llm_service.explain_word(
                word=request.word,
                verse_text=request.verse_text,
                context=request.context,
                language=request.language,
            ),
            timeout=LLM_TIMEOUT
        )

        if result:
            response_data = {"ok": True, "result": result, "error": None}
            # Cache successful results
            await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_LLM)
            return LLMResponse(**response_data)
        else:
            return LLMResponse(
                ok=False,
                error="LLM service unavailable" if request.language == "en" else "خدمة الذكاء الاصطناعي غير متاحة"
            )
    except asyncio.TimeoutError:
        logger.error(f"LLM explain word timeout after {LLM_TIMEOUT}s")
        return LLMResponse(
            ok=False,
            error="Request timeout" if request.language == "en" else "انتهت مهلة الطلب"
        )
    except Exception as e:
        logger.error(f"LLM explain word error: {e}")
        return LLMResponse(ok=False, error=str(e))


@router.post("/llm/answer", response_model=LLMResponse)
async def answer_question(request: LLMQuestionRequest) -> LLMResponse:
    """
    Answer a question about the verse based on tafsir context using LLM.

    Answers are grounded in the provided tafsir text only.

    Performance: 30-second timeout, Redis caching for repeated requests.
    """
    # Check cache first
    cache_key = f"llm:answer:{hashlib.md5((request.question + request.verse_text[:50]).encode()).hexdigest()}"
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)

    if cached:
        logger.debug(f"LLM Cache HIT: {cache_key}")
        return LLMResponse(**cached)

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            tafsir_llm_service.answer_question(
                question=request.question,
                verse_text=request.verse_text,
                tafsir_text=request.tafsir_text,
                language=request.language,
            ),
            timeout=LLM_TIMEOUT
        )

        if result:
            response_data = {"ok": True, "result": result, "error": None}
            # Cache successful results
            await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_LLM)
            return LLMResponse(**response_data)
        else:
            return LLMResponse(
                ok=False,
                error="LLM service unavailable" if request.language == "en" else "خدمة الذكاء الاصطناعي غير متاحة"
            )
    except asyncio.TimeoutError:
        logger.error(f"LLM answer timeout after {LLM_TIMEOUT}s")
        return LLMResponse(
            ok=False,
            error="Request timeout" if request.language == "en" else "انتهت مهلة الطلب"
        )
    except Exception as e:
        logger.error(f"LLM answer error: {e}")
        return LLMResponse(ok=False, error=str(e))


# NOTE: This route must be LAST because it matches /{surah}/{ayah}
# which would otherwise intercept /surah/{surah} and /health
@router.get("/{surah}/{ayah}", response_model=TafseerResponse)
async def get_verse_tafseer(
    surah: int,
    ayah: int,
    editions: Optional[str] = Query(
        None,
        description="Comma-separated edition identifiers (default: ar.muyassar,en.sahih)",
    ),
) -> TafseerResponse:
    """
    Get tafseer for a specific verse.

    Returns tafseer/translation content from the requested editions.
    Defaults to Al-Muyassar (Arabic) and Sahih International (English).

    Args:
        surah: Surah number (1-114)
        ayah: Ayah number within the surah
        editions: Comma-separated list of edition identifiers
    """
    # Validate surah
    if not 1 <= surah <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURAH",
                "message": "Surah must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            }
        )

    # Parse editions
    edition_list = None
    if editions:
        edition_list = [e.strip() for e in editions.split(",")]

    client = get_tafseer_client()

    try:
        result = await client.get_tafseer(surah, ayah, edition_list)

        if not result.success:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "VERSE_NOT_FOUND",
                    "message": f"Verse {surah}:{ayah} not found",
                    "message_ar": f"الآية {surah}:{ayah} غير موجودة",
                }
            )

        return TafseerResponse(
            ok=True,
            surah=surah,
            ayah=ayah,
            tafasir=[
                TafseerVerseResponse(
                    surah=t.surah,
                    ayah=t.ayah,
                    text=t.text,
                    edition=t.edition,
                    edition_name=t.edition_name,
                    language=t.language,
                )
                for t in result.tafasir
            ],
            latency_ms=result.latency_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tafseer: {e}")
        raise HTTPException(status_code=503, detail="Tafseer service unavailable")
