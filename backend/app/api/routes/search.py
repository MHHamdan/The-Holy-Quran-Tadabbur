"""
Search API Routes.

Provides endpoints for:
- Auto-complete suggestions
- Enhanced search with filters
- Query expansion
- Trending content
- Search recommendations

Arabic: واجهة برمجة تطبيقات البحث
"""
from typing import List, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_async_session
from app.services.search_suggestions import (
    get_suggestions_service,
    SuggestionType,
    SearchSuggestion,
)
from app.services.recommendations import (
    get_recommendations_service,
    ContentType,
    Recommendation,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SuggestionResponse(BaseModel):
    """A single search suggestion."""
    text: str
    text_ar: str
    type: str
    relevance: float
    metadata: dict = {}


class SuggestionsListResponse(BaseModel):
    """Response for suggestions endpoint."""
    ok: bool = True
    query: str
    suggestions: List[SuggestionResponse]
    total: int


class QueryExpansionResponse(BaseModel):
    """Response for query expansion."""
    ok: bool = True
    original_query: str
    expanded_terms: List[str]
    total: int


class TrendingTheme(BaseModel):
    """A trending theme."""
    text: str
    text_ar: str
    key: str = ""


class TrendingResponse(BaseModel):
    """Response for trending content."""
    ok: bool = True
    themes: List[TrendingTheme]
    popular_searches: List[dict]


class SearchFilter(BaseModel):
    """Search filters."""
    types: Optional[List[str]] = None  # surah, prophet, theme, verse
    madhab: Optional[str] = None  # hanafi, shafii, maliki, hanbali
    surah_range: Optional[tuple] = None  # (start, end)
    include_tafseer: bool = True
    include_translation: bool = True
    language: str = "both"  # ar, en, both


class EnhancedSearchRequest(BaseModel):
    """Request for enhanced search."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilter] = None
    expand_query: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="relevance")  # relevance, surah, date


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/suggestions", response_model=SuggestionsListResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Max suggestions"),
    types: Optional[str] = Query(
        None,
        description="Filter by types (comma-separated): surah,prophet,theme"
    ),
):
    """
    Get auto-complete suggestions for a search query.

    Returns suggestions for:
    - Surah names (Arabic and English)
    - Prophet names
    - Quranic themes and concepts

    Supports bilingual queries (Arabic or English).
    """
    service = get_suggestions_service()

    # Parse types filter
    type_list = None
    if types:
        try:
            type_list = [SuggestionType(t.strip()) for t in types.split(",")]
        except ValueError:
            pass  # Ignore invalid types

    suggestions = service.get_suggestions(q, limit=limit, types=type_list)

    return SuggestionsListResponse(
        ok=True,
        query=q,
        suggestions=[
            SuggestionResponse(
                text=s.text,
                text_ar=s.text_ar,
                type=s.type.value,
                relevance=round(s.relevance, 2),
                metadata=s.metadata,
            )
            for s in suggestions
        ],
        total=len(suggestions),
    )


@router.get("/expand", response_model=QueryExpansionResponse)
async def expand_search_query(
    q: str = Query(..., min_length=1, max_length=200, description="Query to expand"),
):
    """
    Expand a search query with synonyms and related terms.

    Useful for improving search coverage:
    - "Moses" expands to ["Moses", "Musa", "موسى", "كليم الله"]
    - "الجنة" expands to ["الجنة", "الفردوس", "النعيم", "دار السلام"]
    """
    service = get_suggestions_service()
    expanded = service.expand_query(q)

    return QueryExpansionResponse(
        ok=True,
        original_query=q,
        expanded_terms=expanded,
        total=len(expanded),
    )


@router.get("/trending", response_model=TrendingResponse)
async def get_trending_content():
    """
    Get trending themes and popular searches.

    Returns:
    - Trending Quranic themes
    - Most popular recent searches
    """
    service = get_suggestions_service()

    trending_themes = service.get_trending_themes()
    popular_searches = service.get_popular_searches(limit=10)

    return TrendingResponse(
        ok=True,
        themes=[
            TrendingTheme(
                text=t.text,
                text_ar=t.text_ar,
                key=t.metadata.get("key", ""),
            )
            for t in trending_themes
        ],
        popular_searches=[
            {"query": q, "count": c}
            for q, c in popular_searches
        ],
    )


@router.get("/recent")
async def get_recent_searches(
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get recent search queries.

    Returns the most recent searches performed by users.
    """
    service = get_suggestions_service()
    recent = service.get_recent_searches(limit=limit)

    return {
        "ok": True,
        "recent_searches": recent,
        "total": len(recent),
    }


@router.post("/record")
async def record_search(
    q: str = Query(..., min_length=1, max_length=200),
):
    """
    Record a search query for analytics.

    Used to track popular and recent searches.
    """
    service = get_suggestions_service()
    service.record_search(q)

    return {"ok": True, "message": "Search recorded"}


@router.get("/filters")
async def get_available_filters():
    """
    Get available search filters and options.

    Returns all filterable dimensions:
    - Content types (surah, verse, tafseer, etc.)
    - Madhab options
    - Language options
    - Sort options
    """
    return {
        "ok": True,
        "filters": {
            "types": [
                {"value": "surah", "label_en": "Surah", "label_ar": "سورة"},
                {"value": "verse", "label_en": "Verse", "label_ar": "آية"},
                {"value": "tafseer", "label_en": "Tafseer", "label_ar": "تفسير"},
                {"value": "theme", "label_en": "Theme", "label_ar": "موضوع"},
                {"value": "prophet", "label_en": "Prophet", "label_ar": "نبي"},
                {"value": "story", "label_en": "Story", "label_ar": "قصة"},
            ],
            "madhab": [
                {"value": "hanafi", "label_en": "Hanafi", "label_ar": "حنفي"},
                {"value": "shafii", "label_en": "Shafi'i", "label_ar": "شافعي"},
                {"value": "maliki", "label_en": "Maliki", "label_ar": "مالكي"},
                {"value": "hanbali", "label_en": "Hanbali", "label_ar": "حنبلي"},
            ],
            "language": [
                {"value": "ar", "label_en": "Arabic", "label_ar": "العربية"},
                {"value": "en", "label_en": "English", "label_ar": "الإنجليزية"},
                {"value": "both", "label_en": "Both", "label_ar": "كلاهما"},
            ],
            "sort_options": [
                {"value": "relevance", "label_en": "Most Relevant", "label_ar": "الأكثر صلة"},
                {"value": "surah", "label_en": "By Surah Order", "label_ar": "ترتيب السور"},
                {"value": "popularity", "label_en": "Most Popular", "label_ar": "الأكثر شعبية"},
            ],
        },
    }


@router.get("/surah-list")
async def get_surah_list():
    """
    Get complete list of Surahs for search/filter UI.

    Returns all 114 Surahs with Arabic and English names.
    """
    from app.services.search_suggestions import SURAH_DATA

    return {
        "ok": True,
        "surahs": [
            {
                "number": num,
                "name_ar": ar,
                "name_en": en,
                "meaning": meaning,
            }
            for num, ar, en, meaning in SURAH_DATA
        ],
        "total": len(SURAH_DATA),
    }


@router.get("/prophets-list")
async def get_prophets_list():
    """
    Get complete list of Prophets for search/filter UI.

    Returns all Prophets mentioned in the Quran.
    """
    from app.services.search_suggestions import PROPHET_DATA

    return {
        "ok": True,
        "prophets": [
            {
                "name_ar": ar,
                "name_en": en,
                "aliases": aliases,
            }
            for ar, en, aliases in PROPHET_DATA
        ],
        "total": len(PROPHET_DATA),
    }


@router.get("/themes-list")
async def get_themes_list():
    """
    Get complete list of Quranic themes for search/filter UI.

    Returns major themes and concepts in the Quran.
    """
    from app.services.search_suggestions import THEME_DATA

    return {
        "ok": True,
        "themes": [
            {
                "name_ar": ar,
                "name_en": en,
                "key": key,
                "related": related,
            }
            for ar, en, key, related in THEME_DATA
        ],
        "total": len(THEME_DATA),
    }


# =============================================================================
# RECOMMENDATIONS ENDPOINTS
# =============================================================================

class RecommendationResponse(BaseModel):
    """A single recommendation item."""
    content_type: str
    content_id: str
    title: str
    title_ar: str
    description: str = ""
    description_ar: str = ""
    relevance_score: float
    reason: str
    reason_ar: str
    metadata: dict = {}


class RecommendationsListResponse(BaseModel):
    """Response for recommendations endpoint."""
    ok: bool = True
    recommendations: List[RecommendationResponse]
    total: int


@router.get("/recommendations", response_model=RecommendationsListResponse)
async def get_recommendations(
    user_id: Optional[str] = Query(None, description="User ID for personalized recommendations"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get content recommendations.

    If user_id is provided, returns personalized recommendations
    based on user's viewing history. Otherwise returns popular content.
    """
    service = get_recommendations_service()

    if user_id:
        recs = service.get_personalized_recommendations(user_id, limit)
    else:
        recs = service.get_popular_recommendations(limit)

    return RecommendationsListResponse(
        ok=True,
        recommendations=[
            RecommendationResponse(
                content_type=r.content_type.value,
                content_id=r.content_id,
                title=r.title,
                title_ar=r.title_ar,
                description=r.description,
                description_ar=r.description_ar,
                relevance_score=round(r.relevance_score, 2),
                reason=r.reason,
                reason_ar=r.reason_ar,
                metadata=r.metadata,
            )
            for r in recs
        ],
        total=len(recs),
    )


@router.get("/recommendations/verse/{verse_ref}")
async def get_verse_recommendations(
    verse_ref: str,
    limit: int = Query(default=5, ge=1, le=20),
):
    """
    Get recommendations related to a specific verse.

    Args:
        verse_ref: Verse reference (e.g., "2:255" for Ayat al-Kursi)
        limit: Max recommendations
    """
    service = get_recommendations_service()
    recs = service.get_recommendations_for_verse(verse_ref, limit)

    return {
        "ok": True,
        "verse_ref": verse_ref,
        "recommendations": [
            {
                "content_type": r.content_type.value,
                "content_id": r.content_id,
                "title": r.title,
                "title_ar": r.title_ar,
                "relevance_score": round(r.relevance_score, 2),
                "reason": r.reason,
                "reason_ar": r.reason_ar,
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.get("/recommendations/prophet/{prophet_key}")
async def get_prophet_recommendations(
    prophet_key: str,
    limit: int = Query(default=10, ge=1, le=20),
):
    """
    Get recommendations related to a Prophet.

    Args:
        prophet_key: Prophet key (e.g., "musa", "ibrahim", "yusuf")
        limit: Max recommendations
    """
    service = get_recommendations_service()
    recs = service.get_recommendations_for_prophet(prophet_key, limit)

    return {
        "ok": True,
        "prophet": prophet_key,
        "recommendations": [
            {
                "content_type": r.content_type.value,
                "content_id": r.content_id,
                "title": r.title,
                "title_ar": r.title_ar,
                "relevance_score": round(r.relevance_score, 2),
                "reason": r.reason,
                "reason_ar": r.reason_ar,
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.get("/recommendations/theme/{theme}")
async def get_theme_recommendations(
    theme: str,
    limit: int = Query(default=5, ge=1, le=20),
):
    """
    Get recommendations related to a Quranic theme.

    Args:
        theme: Theme key (e.g., "صبر", "توبة", "رحمة")
        limit: Max recommendations
    """
    service = get_recommendations_service()
    recs = service.get_recommendations_for_theme(theme, limit)

    return {
        "ok": True,
        "theme": theme,
        "recommendations": [
            {
                "content_type": r.content_type.value,
                "content_id": r.content_id,
                "title": r.title,
                "title_ar": r.title_ar,
                "relevance_score": round(r.relevance_score, 2),
                "reason": r.reason,
                "reason_ar": r.reason_ar,
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.post("/recommendations/record")
async def record_content_view(
    user_id: str = Query(..., description="User identifier"),
    content_type: str = Query(..., description="Content type (verse, surah, theme, etc.)"),
    content_id: str = Query(..., description="Content identifier"),
):
    """
    Record a content view for recommendations.

    Used to track user interactions for personalized recommendations.
    """
    service = get_recommendations_service()

    try:
        ctype = ContentType(content_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid content_type: {content_type}")

    service.record_interaction(user_id, ctype, content_id, "view")

    return {"ok": True, "message": "Interaction recorded"}
