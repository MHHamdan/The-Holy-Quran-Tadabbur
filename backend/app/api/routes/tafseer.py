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
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio
import hashlib
import json

from app.services.tafseer_api import (
    get_tafseer_client,
    DEFAULT_TAFSIR_EDITION,
    EDITION_METADATA,
    EDITION_NOT_LICENSED,
    LICENSED_DB_EDITIONS,
    is_allowed_edition,
    servable_editions,
)
from app.services.tafsir_api import (
    ALLOWED_QURAN_COM_IDS,
    TAFSIR_EDITIONS,
    external_tafsir_service,
    tafsir_llm_service,
)
from app.services.redis_cache import get_hybrid_cache
from app.services.tafsir_comparison import tafsir_comparison_service
from app.services.tafsir_sources import is_tafsir_placeholder
from app.models.tafseer import TafseerChunk, TafseerSource
from app.db.database import get_async_session
from app.core.config import settings
from app.core.rate_limit import rag_rate_limit
from app.rag.source_validator import TRUSTED_SOURCE_IDS

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


def _edition_not_licensed() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "code": "EDITION_NOT_LICENSED",
            "message": "This edition is not available: its licence is not recorded.",
            "message_ar": "هذه النسخة غير متاحة لعدم توثيق ترخيصها.",
        },
    )


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
                "identifier": "ar.baghawi",
                "name_ar": "تفسير البغوي",
                "name_en": "Tafsir Al-Baghawi",
                "author_ar": "البغوي",
                "author_en": "Al-Baghawi",
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
    List the tafseer and translation editions this API will serve.

    Only allowlisted editions (ALLOWED_EDITIONS) whose source is enabled and
    licence-verified right now are listed, whatever feature_external_tafseer
    says: the upstream catalogue holds editions with no recorded licence or
    author. Can be filtered by language.
    """
    try:
        identifiers = await servable_editions()
    except Exception as e:  # database unavailable: only the translations are certain
        logger.warning("Tafsir licence lookup failed, listing translations only: %s", e)
        identifiers = sorted(LICENSED_DB_EDITIONS)
    editions = []
    for identifier in identifiers:
        metadata = EDITION_METADATA[identifier]
        lang = "ar" if identifier.startswith("ar.") else "en"
        if language and lang != language:
            continue
        editions.append(EditionResponse(
            identifier=identifier,
            name_ar=metadata["name_ar"],
            name_en=metadata["name_en"],
            author_ar=metadata.get("author_ar", ""),
            author_en=metadata.get("author_en", ""),
            language=lang,
            type="tafsir" if lang == "ar" else "translation",
        ))
    return EditionsListResponse(ok=True, editions=editions, total=len(editions))


@router.get("/surah/{surah}", response_model=SurahTafseerResponse)
async def get_surah_tafseer(
    surah: int,
    edition: str = Query(
        DEFAULT_TAFSIR_EDITION,
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

    if not is_allowed_edition(edition):
        raise _edition_not_licensed()
    try:
        servable = await servable_editions()
    except Exception as e:
        logger.error(f"Tafsir licence lookup failed: {e}")
        raise HTTPException(status_code=503, detail="Tafseer service unavailable")
    if edition not in servable:
        raise _edition_not_licensed()

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
    # Set when the passage comes from the local licensed library
    # (source == LOCAL_LIBRARY_SOURCE): the tafseer_sources id and chunk id.
    source_id: Optional[str] = None
    chunk_id: Optional[str] = None


# `source` value for passages read from tafseer_chunks rather than proxied.
LOCAL_LIBRARY_SOURCE = "tadabbur_library"


class _EditionNotServable(Exception):
    """The edition's tafseer_sources row exists but is disabled or unverified."""


class _EditionNotSeeded(Exception):
    """The edition's tafseer_sources row does not exist in this installation."""


def _no_passage(info, sura: int, ayah: int) -> HTTPException:
    """Bilingual 'this source has no passage for this verse' (never a placeholder)."""
    return HTTPException(
        status_code=404,
        detail={
            "code": "NO_PASSAGE_IN_SOURCE",
            "source_id": info.db_source_id,
            "verse_key": f"{sura}:{ayah}",
            "message": f"{info.name_en} has no separate passage for verse {sura}:{ayah}.",
            "message_ar": f"لا يوجد في {info.name_ar} مقطع مستقل للآية {sura}:{ayah}.",
        },
    )


def _edition_not_seeded(info) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "code": "EDITION_NOT_SEEDED",
            "source_id": info.db_source_id,
            "message": f"{info.name_en} is not in this installation's tafsir library.",
            "message_ar": f"{info.name_ar} غير موجود في مكتبة التفسير لهذه النسخة.",
        },
    )


async def _local_licensed_passage(
    session: AsyncSession, db_source_id: str, sura: int, ayah: int
) -> Optional[Dict[str, Any]]:
    """The stored passage covering sura:ayah from an enabled, licence-verified
    source, or None when the source has no passage for this verse (an empty
    or upstream-placeholder row counts as none). Raises _EditionNotSeeded
    when the source has no row here, and _EditionNotServable when the row
    exists but is disabled or unverified."""
    source = (
        await session.execute(select(TafseerSource).where(TafseerSource.id == db_source_id))
    ).scalar_one_or_none()
    if source is None:
        raise _EditionNotSeeded(db_source_id)
    if not (source.is_enabled and source.license_verified):
        raise _EditionNotServable(db_source_id)
    chunk = (
        await session.execute(
            select(TafseerChunk)
            .where(
                TafseerChunk.source_id == db_source_id,
                TafseerChunk.sura_no == sura,
                TafseerChunk.aya_start <= ayah,
                TafseerChunk.aya_end >= ayah,
            )
            .order_by(TafseerChunk.aya_start.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if chunk is None:
        return None
    text = (chunk.content_ar if source.language == "ar" else chunk.content_en) or chunk.content_ar or chunk.content_en
    if is_tafsir_placeholder(text):
        return None
    return {"text": text.strip(), "chunk_id": chunk.chunk_id}


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
    edition: str = Query("baghawi", description="Edition identifier"),
    response: Response = None,
    session: AsyncSession = Depends(get_async_session),
) -> ExternalTafsirResponse:
    """
    Get tafsir for a specific verse.

    Every edition names its tafseer_sources id (db_source_id), and only the
    stored, licence-verified passage is served (source "tadabbur_library",
    with source_id and chunk_id). Nothing is proxied: the Quran.com /
    quran-tafseer.com / read.tafsir.one terms are not recorded, and Quran.com
    answers verses without a separate passage with a placeholder ("لا يوجد
    تفسير لهذه الأية") that was being shown as the scholar's tafsir.

    - disabled or unverified source: 403 EDITION_NOT_LICENSED
    - source not seeded here: 404 EDITION_NOT_SEEDED
    - no passage for this verse (or only a placeholder): 404
      NO_PASSAGE_IN_SOURCE, with a bilingual message naming the source
    - database unavailable: 503 TAFSIR_UNAVAILABLE
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

    # Refuse unlisted editions before the cache: copies cached while the
    # copyrighted English works were still proxied must not be served.
    if edition not in TAFSIR_EDITIONS:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "TAFSIR_NOT_FOUND",
                "message": f"Unknown or unavailable tafsir edition: {edition}",
                "message_ar": "نسخة التفسير غير متاحة",
            },
        )

    info = TAFSIR_EDITIONS[edition]
    if not info.db_source_id:  # every listed edition has one; never proxy
        raise _edition_not_seeded(info)
    try:
        local = await _local_licensed_passage(session, info.db_source_id, sura, ayah)
    except _EditionNotServable:
        raise _edition_not_licensed()
    except _EditionNotSeeded:
        raise _edition_not_seeded(info)
    except Exception as e:
        logger.warning("Local tafsir lookup failed for %s %s:%s: %s", edition, sura, ayah, e)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "TAFSIR_UNAVAILABLE",
                "message": "The tafsir library is temporarily unavailable. Please retry.",
                "message_ar": "مكتبة التفسير غير متاحة مؤقتاً. أعد المحاولة.",
            },
        )
    if not local:
        raise _no_passage(info, sura, ayah)

    if response:
        set_cache_headers(response, max_age=CACHE_TTL_TAFSIR, etag_data=local["chunk_id"])
    return ExternalTafsirResponse(
        ok=True,
        verse_key=f"{sura}:{ayah}",
        text=local["text"],
        source=LOCAL_LIBRARY_SOURCE,
        edition={
            "id": info.id,
            "name_ar": info.name_ar,
            "name_en": info.name_en,
            "author_ar": info.author_ar,
            "author_en": info.author_en,
            "language": info.language,
            "has_audio": False,
            "db_source_id": info.db_source_id,
        },
        audio_url=None,
        source_id=info.db_source_id,
        chunk_id=local["chunk_id"],
    )


@router.get("/quran-com/verse/{sura}/{ayah}")
async def get_quran_com_tafsir(
    sura: int,
    ayah: int,
    tafsir_id: int = Query(..., description="Quran.com tafsir ID of an allowlisted edition"),
) -> dict:
    """
    Former Quran.com proxy, now closed.

    The English works it used to serve (169 Ibn Kathir EN, 168 Ma'arif
    al-Qur'an, 817 Tazkirul Quran) are copyrighted with no recorded
    permission and stay refused with 403. The Arabic editions are served from
    the licensed library by /external/verse: Quran.com's terms are not
    recorded, and it answers verses without a separate passage with a
    placeholder that is not tafsir. Listed ids get 410 PROXY_DISABLED.
    """
    if tafsir_id not in ALLOWED_QURAN_COM_IDS:
        raise _edition_not_licensed()
    raise HTTPException(
        status_code=410,
        detail={
            "code": "PROXY_DISABLED",
            "message": "Tafsir is served from the app's licensed library: use /api/v1/tafseer/external/verse.",
            "message_ar": "يُعرض التفسير من مكتبة التطبيق المرخّصة: استخدم /api/v1/tafseer/external/verse.",
        },
    )


@router.get("/external/compare/{sura}/{ayah}")
async def compare_external_tafsirs(
    sura: int,
    ayah: int,
    editions: str = Query("baghawi,ibn_kathir,tabari", description="Comma-separated edition IDs"),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Compare tafsir from several editions for a verse.

    Each edition's passage comes from the licensed library only (as in
    /external/verse); an edition that is unknown, unlicensed, not seeded or
    has no passage for the verse is simply absent. Nothing is proxied.
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

    edition_list = [e.strip() for e in editions.split(",") if e.strip()][:len(TAFSIR_EDITIONS)]
    results = []
    for edition_id in edition_list:
        info = TAFSIR_EDITIONS.get(edition_id)
        if not info or not info.db_source_id:
            continue
        try:
            local = await _local_licensed_passage(session, info.db_source_id, sura, ayah)
        except (_EditionNotServable, _EditionNotSeeded):
            continue
        if not local:
            continue
        results.append({
            "verse_key": f"{sura}:{ayah}",
            "text": local["text"],
            "source": LOCAL_LIBRARY_SOURCE,
            "source_id": info.db_source_id,
            "chunk_id": local["chunk_id"],
            "edition": {
                "id": info.id,
                "name_ar": info.name_ar,
                "name_en": info.name_en,
                "author_ar": info.author_ar,
                "author_en": info.author_en,
                "language": info.language,
                "has_audio": False,
                "db_source_id": info.db_source_id,
            },
        })

    return {
        "ok": True,
        "verse_key": f"{sura}:{ayah}",
        "tafsirs": results,
        "editions_requested": len(edition_list),
        "editions_found": len(results),
    }


@router.get("/compare/{surah}/{ayah}")
async def compare_seeded_tafsirs(
    surah: int,
    ayah: int,
    response: Response,
    sources: Optional[str] = Query(
        None,
        description="Comma-separated source ids (default: every enabled source)",
    ),
    language: Optional[str] = Query(
        None, pattern="^(ar|en)$", description="Restrict to one language"
    ),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Compare every seeded tafsir for one verse, side by side.

    Unlike /external/compare, this reads the local corpus — all six seeded
    sources across all 6,236 verses — so it needs no third-party API and
    returns the chunk_id of each passage for citation.

    Entries are ordered oldest author first, and each carries its author, era,
    death year, methodology and licence status. The `comparison` block reports
    descriptive statistics only; see the disclaimer it carries.

    Arabic: مقارنة التفاسير المتاحة لآية واحدة
    """
    if not 1 <= surah <= 114:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SURAH",
                "message": "Surah must be between 1 and 114",
                "message_ar": "رقم السورة يجب أن يكون بين 1 و 114",
            },
        )
    if ayah < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_AYAH",
                "message": "Ayah must be 1 or greater",
                "message_ar": "رقم الآية يجب أن يكون 1 أو أكثر",
            },
        )

    source_ids = [s.strip() for s in sources.split(",") if s.strip()] if sources else None

    result = await tafsir_comparison_service.compare_verse(
        session, surah=surah, ayah=ayah, source_ids=source_ids, language=language
    )

    if not result["entries"]:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_TAFSIR_FOUND",
                "message": f"No seeded tafsir found for {surah}:{ayah}",
                "message_ar": f"لا يوجد تفسير مُخزَّن للآية {surah}:{ayah}",
            },
        )

    # Seeded tafsir is immutable once ingested (see models/tafseer.py), so it
    # is safe to cache hard.
    response.headers["Cache-Control"] = "public, max-age=86400"
    return result


@router.get("/compare/{surah}/{ayah}/sources")
async def list_comparable_sources(
    response: Response,
    surah: int,
    ayah: int,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    List which sources carry tafsir for this verse, without their text.

    Lets the UI render source pickers and counts before paying for the full
    payload, which runs to tens of thousands of words on well-commented verses.

    Arabic: قائمة المصادر المتاحة للآية
    """
    result = await tafsir_comparison_service.compare_verse(session, surah=surah, ayah=ayah)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return {
        "ok": True,
        "verse_key": result["verse_key"],
        "sources": [
            {
                k: entry[k]
                for k in (
                    "source_id", "name_ar", "name_en", "author_ar", "author_en",
                    "language", "era", "era_label_ar", "era_label_en",
                    "death_year_hijri", "death_year_ce", "methodology",
                    "methodology_label_ar", "methodology_label_en",
                    "word_count", "license_verified", "license",
                    "source_url", "translator",
                )
            }
            for entry in result["entries"]
        ],
        "total": result["sources_returned"],
    }


# =============================================================================
# LLM-Enhanced Tafsir Endpoints
# =============================================================================
#
# The client sends only identifiers (sura, aya, source_id) plus the user's own
# word or question. The verse text is read from quran_verses and the grounding
# tafsir from tafseer_chunks on the server, so a request cannot inject text
# that would then be cached and served to other readers. The cache key covers
# every input that changes the answer, plus the model id.

_LLM_REFUSAL_EN = (
    "No stored tafsir passage from this source covers this verse, so the AI "
    "assistant cannot answer here."
)
_LLM_REFUSAL_AR = "لا يوجد في مكتبة التطبيق مقطع تفسير من هذا المصدر لهذه الآية، لذلك لا يستطيع المساعد الإجابة هنا."


class _LLMVerseRequest(BaseModel):
    """Identifiers only: verse and tafsir text are loaded on the server."""

    model_config = ConfigDict(extra="forbid")

    sura: int = Field(..., ge=1, le=114, description="Surah number")
    aya: int = Field(..., ge=1, le=286, description="Ayah number")
    source_id: str = Field(
        ..., pattern=r"^[a-z0-9_]{1,64}$",
        description="Seeded tafsir source id (e.g. baghawi_ar)",
    )
    language: str = Field("ar", pattern="^(ar|en)$", description="Output language")

    @field_validator("source_id")
    @classmethod
    def _trusted_source(cls, value: str) -> str:
        if value not in TRUSTED_SOURCE_IDS:
            raise ValueError("source_id is not a trusted tafsir source")
        return value


class LLMSummarizeRequest(_LLMVerseRequest):
    """Request model for tafsir summarization."""


class LLMExplainWordRequest(_LLMVerseRequest):
    """Request model for word explanation."""

    word: str = Field(..., min_length=1, max_length=64, description="The word to explain")


class LLMQuestionRequest(_LLMVerseRequest):
    """Request model for Q&A about tafsir."""

    question: str = Field(..., min_length=1, max_length=500, description="The question to answer")


class LLMResponse(BaseModel):
    """
    Response model for LLM operations.

    ``result`` is AI-generated text, never Qur'an or tafsir: ``ai_generated``
    is always true so clients render it apart from the sources it summarises.
    """
    ok: bool = True
    result: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    source_id: Optional[str] = None
    ai_generated: bool = True
    disclaimer_en: str = (
        "AI-generated summary of the stored tafsir passage for this verse. It "
        "is not tafsir and not a religious ruling."
    )
    disclaimer_ar: str = "ملخص آلي لمقطع التفسير المخزّن لهذه الآية، وليس تفسيراً ولا فتوى."
    quotations_removed: int = 0


def _normalise_user_text(text: str) -> str:
    return " ".join(text.split())


def _llm_cache_key(kind: str, **parts: Any) -> str:
    """Key over every input that changes the answer, plus the model id."""
    parts["model"] = settings.hf_llm_model_id
    digest = hashlib.sha256(
        json.dumps(parts, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"llm:{kind}:v2:{digest}"


async def _load_grounding(
    session: AsyncSession, sura: int, aya: int, source_id: str
) -> Optional[Tuple[str, str]]:
    """(verse_text, tafsir_text) from the canonical tables, or None.

    Only enabled, licence-verified sources count; a range chunk that covers
    the ayah counts too.
    """
    from sqlalchemy import select
    from app.models.quran import QuranVerse
    from app.models.tafseer import TafseerChunk, TafseerSource

    verse_text = (
        await session.execute(
            select(QuranVerse.text_uthmani).where(
                QuranVerse.sura_no == sura, QuranVerse.aya_no == aya
            )
        )
    ).scalar_one_or_none()
    if not verse_text:
        return None

    rows = (
        await session.execute(
            select(TafseerChunk.content_ar, TafseerChunk.content_en)
            .join(TafseerSource, TafseerSource.id == TafseerChunk.source_id)
            .where(
                TafseerChunk.source_id == source_id,
                TafseerChunk.sura_no == sura,
                TafseerChunk.aya_start <= aya,
                TafseerChunk.aya_end >= aya,
                TafseerSource.is_enabled == 1,
                TafseerSource.license_verified == 1,
            )
            .order_by(TafseerChunk.chunk_order)
        )
    ).all()
    tafsir_text = "\n\n".join(
        (ar or en or "").strip() for ar, en in rows if (ar or en or "").strip()
    )
    if not tafsir_text:
        return None
    return verse_text, tafsir_text


def _refusal(request: _LLMVerseRequest) -> LLMResponse:
    return LLMResponse(
        ok=False,
        error=_LLM_REFUSAL_EN if request.language == "en" else _LLM_REFUSAL_AR,
        error_code="NO_VERIFIED_SOURCE",
        source_id=request.source_id,
    )


def _ground_llm_result(result: str, language: str, *evidence: str) -> tuple:
    """
    Quotations in the output must appear verbatim in the verse/tafsir text the
    server loaded; anything else is removed (it could be invented Qur'an text
    or a misattributed scholarly quote).
    """
    from app.safety.grounding import build_corpus_index, verify_quotations

    index = build_corpus_index(e for e in evidence if e)
    cleaned, report = verify_quotations(result, quran_index="", evidence_index=index, language=language)
    return cleaned, len(report.removed)


async def _run_llm(
    kind: str,
    request: _LLMVerseRequest,
    session: AsyncSession,
    call,
    **user_parts: str,
) -> LLMResponse:
    """Shared flow: load grounding, check cache, call, ground, cache."""
    grounding = await _load_grounding(session, request.sura, request.aya, request.source_id)
    if grounding is None:
        return _refusal(request)
    verse_text, tafsir_text = grounding

    cache_key = _llm_cache_key(
        kind,
        sura=request.sura,
        aya=request.aya,
        source_id=request.source_id,
        language=request.language,
        tafsir_sha=hashlib.sha256(tafsir_text.encode("utf-8")).hexdigest(),
        **user_parts,
    )
    cache = get_hybrid_cache()
    cached = await cache.get(cache_key)
    if cached:
        logger.debug(f"LLM Cache HIT: {cache_key}")
        return LLMResponse(**cached)

    en = request.language == "en"
    try:
        result = await asyncio.wait_for(call(verse_text, tafsir_text), timeout=LLM_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error(f"LLM {kind} timeout after {LLM_TIMEOUT}s")
        return LLMResponse(ok=False, error="Request timeout" if en else "انتهت مهلة الطلب")
    except Exception as e:
        logger.error(f"LLM {kind} error: {type(e).__name__}")
        return LLMResponse(ok=False, error="AI service error" if en else "خطأ في خدمة الذكاء الاصطناعي")

    if not result:
        return LLMResponse(
            ok=False,
            error="LLM service unavailable" if en else "خدمة الذكاء الاصطناعي غير متاحة",
        )

    result, removed = _ground_llm_result(result, request.language, verse_text, tafsir_text)
    response_data = {
        "ok": True, "result": result, "error": None,
        "quotations_removed": removed, "source_id": request.source_id,
    }
    await cache.set(cache_key, response_data, l1_ttl=300, l2_ttl=CACHE_TTL_LLM)
    return LLMResponse(**response_data)


@router.post("/llm/summarize", response_model=LLMResponse)
async def summarize_tafsir(
    request: LLMSummarizeRequest,
    session: AsyncSession = Depends(get_async_session),
    _rate: None = Depends(rag_rate_limit),
) -> LLMResponse:
    """
    Summarise the stored tafsir passage of one source for one verse.

    Refuses (ok=false, error_code NO_VERIFIED_SOURCE) when the source has no
    enabled, licence-verified passage for the verse.
    """
    return await _run_llm(
        "summary", request, session,
        lambda verse, tafsir: tafsir_llm_service.summarize_tafsir(
            tafsir_text=tafsir, verse_text=verse, language=request.language,
        ),
    )


@router.post("/llm/explain-word", response_model=LLMResponse)
async def explain_word(
    request: LLMExplainWordRequest,
    session: AsyncSession = Depends(get_async_session),
    _rate: None = Depends(rag_rate_limit),
) -> LLMResponse:
    """
    Explain a word of the verse, using the stored tafsir passage as context.
    """
    word = _normalise_user_text(request.word)
    return await _run_llm(
        "explain", request, session,
        lambda verse, tafsir: tafsir_llm_service.explain_word(
            word=word, verse_text=verse, context=tafsir, language=request.language,
        ),
        word=word,
    )


@router.post("/llm/answer", response_model=LLMResponse)
async def answer_question(
    request: LLMQuestionRequest,
    session: AsyncSession = Depends(get_async_session),
    _rate: None = Depends(rag_rate_limit),
) -> LLMResponse:
    """
    Answer a question about the verse from the stored tafsir passage only.
    """
    question = _normalise_user_text(request.question)
    return await _run_llm(
        "answer", request, session,
        lambda verse, tafsir: tafsir_llm_service.answer_question(
            question=question, verse_text=verse, tafsir_text=tafsir, language=request.language,
        ),
        question=question,
    )


# =============================================================================
# NOTE: This route must be LAST because it matches /{surah}/{ayah}
# which would otherwise intercept /surah/{surah} and /health
@router.get("/{surah}/{ayah}", response_model=TafseerResponse)
async def get_verse_tafseer(
    surah: int,
    ayah: int,
    editions: Optional[str] = Query(
        None,
        description="Comma-separated edition identifiers (default: ar.baghawi,en.sahih)",
    ),
) -> TafseerResponse:
    """
    Get tafseer for a specific verse.

    Returns tafseer/translation content from the requested editions.
    Defaults to Tafsir al-Baghawi (Arabic) and Saheeh International (English).
    Arabic tafsir comes from enabled, licence-verified sources only.

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

        if not result.success and result.error == EDITION_NOT_LICENSED:
            raise _edition_not_licensed()
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
