"""
Quranic Themes API Routes (المحاور القرآنية)

Endpoints for navigating Quranic themes with strict evidence grounding
from Sunni tafsir sources (4 madhabs only).

ENDPOINTS:
==========
GET /themes                      - List all themes with filtering
GET /themes/categories           - Get theme categories with counts
GET /themes/stats                - Get overall theme statistics
GET /themes/by-sura/{sura}       - Get themes in a surah
GET /themes/by-category/{cat}    - Get themes by category
GET /themes/by-ayah/{sura}/{ayah} - Get themes covering an ayah
GET /themes/{id}                 - Get theme detail
GET /themes/{id}/segments        - Get theme segments paginated
GET /themes/{id}/graph           - Get graph visualization data
GET /themes/{id}/timeline        - Get linear progression
GET /themes/{id}/consequences    - Get rewards/punishments
GET /themes/{id}/related         - Get related themes

GROUNDING RULES:
================
- All segments require tafsir evidence
- Evidence from 4 madhab sources only
- Layer separation: Quran → Tafsir → Classification
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.services.theme_service import ThemeService
from app.services.theme_graph_service import ThemeGraphService
from app.core.responses import APIError, ErrorCode
from app.api.routes import theme_admin

router = APIRouter()

# Include admin sub-router
router.include_router(theme_admin.router)


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class ThemeSummaryResponse(BaseModel):
    """Summary view of a theme."""
    id: str
    slug: str
    title_ar: str
    title_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    order_of_importance: int
    key_concepts: List[str]
    segment_count: int
    total_verses: int
    has_consequences: bool
    parent_id: Optional[str] = None
    short_title_ar: Optional[str] = None
    short_title_en: Optional[str] = None


class ThemeListResponse(BaseModel):
    """Response for theme listing."""
    themes: List[ThemeSummaryResponse]
    total: int
    offset: int
    limit: int


class ThemeDetailResponse(BaseModel):
    """Full detail view of a theme."""
    id: str
    slug: str
    title_ar: str
    title_en: str
    short_title_ar: Optional[str] = None
    short_title_en: Optional[str] = None
    category: str
    category_label_ar: str
    category_label_en: str
    order_of_importance: int
    key_concepts: List[str]
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    parent_id: Optional[str] = None
    related_theme_ids: List[str] = []
    tafsir_sources: List[str] = []
    segment_count: int
    total_verses: int
    suras_mentioned: List[int] = []
    makki_percentage: float = 0
    madani_percentage: float = 0
    is_complete: bool = False
    children: List[ThemeSummaryResponse] = []


class ThemeSegmentResponse(BaseModel):
    """Theme segment information."""
    id: str
    segment_order: int
    chronological_index: Optional[int] = None
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    summary_ar: str
    summary_en: str
    semantic_tags: List[str] = []
    revelation_context: Optional[str] = None
    is_entry_point: bool = False
    is_verified: bool = False
    importance_weight: float = 0.5
    evidence_count: int = 0
    # Discovery fields
    match_type: Optional[str] = None
    confidence: Optional[float] = None
    reasons_ar: Optional[str] = None
    reasons_en: Optional[str] = None
    is_core: Optional[bool] = None
    discovered_at: Optional[str] = None


class SegmentListResponse(BaseModel):
    """Response for segment listing."""
    segments: List[ThemeSegmentResponse]
    total: int
    offset: int
    limit: int


class ThemeConsequenceResponse(BaseModel):
    """Divine consequence information."""
    id: int
    consequence_type: str
    type_label_ar: str
    type_label_en: str
    description_ar: str
    description_en: str
    supporting_verses: List[Dict[str, Any]] = []
    evidence_count: int = 0


class ThemeCategoryResponse(BaseModel):
    """Theme category with count."""
    category: str
    label_ar: str
    label_en: str
    theme_count: int
    order: int


class ThemeOccurrenceResponse(BaseModel):
    """Theme occurrence at a verse."""
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    segment_id: str
    segment_title_ar: Optional[str] = None
    segment_title_en: Optional[str] = None
    summary_ar: str
    summary_en: str


# Graph Response Schemas
class ThemeGraphNodeResponse(BaseModel):
    """Node in theme graph."""
    id: str
    type: str
    label: str
    label_ar: str
    data: Dict[str, Any] = {}
    x: Optional[float] = None
    y: Optional[float] = None


class ThemeGraphEdgeResponse(BaseModel):
    """Edge in theme graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    label_ar: Optional[str] = None
    is_sequential: bool = False
    strength: float = 1.0
    data: Dict[str, Any] = {}


class ThemeGraphResponse(BaseModel):
    """Complete theme graph."""
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    nodes: List[ThemeGraphNodeResponse] = []
    edges: List[ThemeGraphEdgeResponse] = []
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "sequential"
    total_segments: int = 0
    total_connections: int = 0


class TimelineNodeResponse(BaseModel):
    """Node in theme timeline."""
    segment_id: str
    segment_order: int
    chronological_index: Optional[int] = None
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    summary_ar: str
    summary_en: str
    revelation_context: Optional[str] = None
    is_entry_point: bool = False
    is_verified: bool = False


class ThemeStatsResponse(BaseModel):
    """Overall theme statistics."""
    total_themes: int
    total_segments: int
    verified_segments: int
    verification_rate: float
    by_category: List[Dict[str, Any]]


class CrossThemeConnectionResponse(BaseModel):
    """Cross-theme connection."""
    connection_type: str
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    category: str
    strength: float


class ThemeCoverageResponse(BaseModel):
    """Theme coverage statistics including discovery data."""
    theme_id: str
    title_ar: str
    title_en: str
    total_segments: int
    total_verses: int
    manual_segments: int
    discovered_segments: int
    core_segments: int
    supporting_segments: int
    avg_confidence: float
    by_match_type: Dict[str, int]
    by_confidence_band: Dict[str, int]
    tafsir_sources_used: List[str]
    quran_coverage_percentage: float


class SegmentEvidenceResponse(BaseModel):
    """Evidence explaining why a verse belongs to a theme."""
    segment_id: str
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    sura_no: int
    ayah_no: int
    text_uthmani: str
    match_type: str
    confidence: float
    reasons_ar: str
    reasons_en: Optional[str] = None
    is_core: bool
    evidence_sources: List[Dict[str, Any]]
    matching_keywords: List[str] = []


# =============================================================================
# LISTING ENDPOINTS
# =============================================================================

@router.get("", response_model=ThemeListResponse)
async def list_themes(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in titles and key concepts"),
    parent_only: bool = Query(False, description="Only return root themes"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List Quranic themes with optional filtering.

    Themes are ordered by methodological importance:
    1. Aqidah (Theology)
    2. Iman (Faith)
    3. Ibadat (Worship)
    4. Individual Akhlaq
    5. Social Akhlaq
    6. Prohibitions
    7. Divine Laws
    """
    service = ThemeService(session)
    themes, total = await service.list_themes(
        category=category,
        search=search,
        parent_only=parent_only,
        limit=limit,
        offset=offset,
    )

    return ThemeListResponse(
        themes=[
            ThemeSummaryResponse(
                id=t.id,
                slug=t.slug,
                title_ar=t.title_ar,
                title_en=t.title_en,
                short_title_ar=t.short_title_ar,
                short_title_en=t.short_title_en,
                category=t.category,
                category_label_ar=t.category_label_ar,
                category_label_en=t.category_label_en,
                order_of_importance=t.order_of_importance,
                key_concepts=t.key_concepts,
                segment_count=t.segment_count,
                total_verses=t.total_verses,
                has_consequences=t.has_consequences,
                parent_id=t.parent_id,
            )
            for t in themes
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/categories", response_model=List[ThemeCategoryResponse])
async def get_theme_categories(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get theme categories with counts, ordered methodologically.

    Categories follow classical Islamic methodology with Aqidah first.
    """
    service = ThemeService(session)
    categories = await service.get_theme_categories()

    return [
        ThemeCategoryResponse(
            category=c.category,
            label_ar=c.label_ar,
            label_en=c.label_en,
            theme_count=c.theme_count,
            order=c.order,
        )
        for c in categories
    ]


@router.get("/stats", response_model=ThemeStatsResponse)
async def get_theme_stats(
    session: AsyncSession = Depends(get_async_session),
):
    """Get overall statistics for the theme system."""
    service = ThemeService(session)
    stats = await service.get_theme_stats()

    return ThemeStatsResponse(**stats)


class ThemeHealthResponse(BaseModel):
    """Health check response for themes system."""
    status: str
    themes_count: int
    segments_count: int
    discovered_segments: int
    manual_segments: int
    avg_confidence: float
    unique_tafsir_sources: List[str]
    top_themes: List[Dict[str, Any]]
    warnings: List[str] = []


class QualityTierCounts(BaseModel):
    """Counts per classification tier."""
    core: int = 0
    recommended: int = 0
    supporting: int = 0


class FailureReasonCounts(BaseModel):
    """Counts for why segments fail core classification."""
    low_confidence: int = 0
    few_sources: int = 0
    weak_match: int = 0
    missing_reasons: int = 0


class ThemeQualitySummary(BaseModel):
    """Quality summary for a single theme."""
    theme_id: str
    title_ar: str
    title_en: str
    total_segments: int
    tiers: QualityTierCounts
    quality_percentage: float = Field(description="Percentage of core+recommended")


class QualitySummaryResponse(BaseModel):
    """Response for quality summary endpoint."""
    total_segments: int
    total_themes: int

    # Global tier counts
    global_tiers: QualityTierCounts

    # Confidence distribution
    confidence_distribution: Dict[str, int]

    # Source distribution
    source_distribution: Dict[str, int]

    # Match type distribution
    match_type_distribution: Dict[str, int]

    # Failure reasons (why segments aren't core)
    failure_reasons: FailureReasonCounts

    # Quality percentage
    quality_percentage: float = Field(description="Percentage of core+recommended")

    # Per-theme summaries
    themes: List[ThemeQualitySummary]

    # Themes needing improvement
    themes_needing_improvement: List[str]


@router.get("/health", response_model=ThemeHealthResponse)
async def get_themes_health(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Health check endpoint for themes system.

    Returns counts and basic stats for monitoring.
    Fails fast if critical counts are zero.
    """
    from sqlalchemy import text as sql_text

    warnings = []

    # Get theme count
    themes_result = await session.execute(sql_text("SELECT COUNT(*) FROM quranic_themes"))
    themes_count = themes_result.scalar() or 0

    if themes_count == 0:
        return ThemeHealthResponse(
            status="unhealthy",
            themes_count=0,
            segments_count=0,
            discovered_segments=0,
            manual_segments=0,
            avg_confidence=0.0,
            unique_tafsir_sources=[],
            top_themes=[],
            warnings=["CRITICAL: No themes found in database"]
        )

    # Get segment counts
    segments_result = await session.execute(sql_text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN match_type != 'manual' AND match_type IS NOT NULL THEN 1 END) as discovered,
            COUNT(CASE WHEN match_type = 'manual' OR match_type IS NULL THEN 1 END) as manual,
            AVG(COALESCE(confidence, 1.0)) as avg_conf
        FROM theme_segments
    """))
    row = segments_result.fetchone()
    segments_count = row[0] or 0
    discovered_segments = row[1] or 0
    manual_segments = row[2] or 0
    avg_confidence = float(row[3] or 0.0)

    if segments_count == 0:
        warnings.append("WARNING: No segments found")

    # Get unique tafsir sources
    sources_result = await session.execute(sql_text("""
        SELECT DISTINCT jsonb_array_elements(evidence_sources)->>'source_id' as source_id
        FROM theme_segments
        WHERE evidence_sources IS NOT NULL AND jsonb_array_length(evidence_sources) > 0
    """))
    unique_sources = [r[0] for r in sources_result if r[0]]

    # Get top themes by segment count
    top_result = await session.execute(sql_text("""
        SELECT ts.theme_id, qt.title_ar, qt.title_en, COUNT(*) as cnt
        FROM theme_segments ts
        JOIN quranic_themes qt ON ts.theme_id = qt.id
        GROUP BY ts.theme_id, qt.title_ar, qt.title_en
        ORDER BY cnt DESC
        LIMIT 5
    """))
    top_themes = [
        {"theme_id": r[0], "title_ar": r[1], "title_en": r[2], "segment_count": r[3]}
        for r in top_result
    ]

    # Determine status
    status = "healthy"
    if segments_count < 100:
        status = "degraded"
        warnings.append(f"Low segment count: {segments_count}")
    if discovered_segments == 0:
        warnings.append("No discovered segments - discovery may not have run")
    if avg_confidence < 0.5:
        warnings.append(f"Low average confidence: {avg_confidence:.2f}")

    return ThemeHealthResponse(
        status=status,
        themes_count=themes_count,
        segments_count=segments_count,
        discovered_segments=discovered_segments,
        manual_segments=manual_segments,
        avg_confidence=round(avg_confidence, 3),
        unique_tafsir_sources=unique_sources,
        top_themes=top_themes,
        warnings=warnings
    )


@router.get("/quality/summary", response_model=QualitySummaryResponse)
async def get_quality_summary(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get quality distribution summary across all themes.

    Returns:
    - Per-theme tier counts (core/recommended/supporting)
    - Global confidence and source distributions
    - Failure reasons for non-core segments
    - Themes needing improvement

    Uses the 3-tier classification:
    - CORE: confidence >= 0.82 + direct match, OR confidence >= 0.74 + 2+ sources
    - RECOMMENDED: confidence >= 0.70 + non-weak match, OR confidence >= 0.65 + 2+ sources
    - SUPPORTING: everything else
    """
    from sqlalchemy import text as sql_text

    # Classification thresholds
    CORE_CONFIDENCE_DIRECT = 0.82
    CORE_CONFIDENCE_MULTI_SOURCE = 0.74
    RECOMMENDED_CONFIDENCE_SINGLE = 0.70
    RECOMMENDED_CONFIDENCE_MULTI = 0.65
    DIRECT_MATCH_TYPES = {'direct', 'exact', 'root', 'lexical', 'manual', ''}
    WEAK_MATCH_TYPES = {'weak', 'semantic_low'}

    def classify_segment(confidence: float, source_count: int, match_type: str) -> str:
        """Classify a segment into tier."""
        mt = (match_type or '').lower()
        is_direct = mt in DIRECT_MATCH_TYPES
        is_weak = mt in WEAK_MATCH_TYPES

        # Manual segments are always core
        if mt == 'manual' or mt == '':
            return 'core'

        # CORE criteria
        if confidence >= CORE_CONFIDENCE_DIRECT and is_direct:
            return 'core'
        if confidence >= CORE_CONFIDENCE_MULTI_SOURCE and source_count >= 2:
            return 'core'

        # RECOMMENDED criteria
        if confidence >= RECOMMENDED_CONFIDENCE_SINGLE and not is_weak:
            return 'recommended'
        if confidence >= RECOMMENDED_CONFIDENCE_MULTI and source_count >= 2:
            return 'recommended'

        return 'supporting'

    # Get all themes with segments
    result = await session.execute(sql_text("""
        SELECT
            qt.id,
            qt.title_ar,
            qt.title_en,
            ts.confidence,
            ts.match_type,
            ts.evidence_sources,
            ts.reasons_ar
        FROM quranic_themes qt
        LEFT JOIN theme_segments ts ON qt.id = ts.theme_id
        ORDER BY qt.order_of_importance, ts.segment_order
    """))

    # Aggregate stats
    theme_stats: Dict[str, Dict] = {}
    global_tiers = QualityTierCounts()
    confidence_dist = {"0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8+": 0}
    source_dist = {"0 sources": 0, "1 source": 0, "2 sources": 0, "3+ sources": 0}
    match_dist = {"manual": 0, "lexical": 0, "root": 0, "semantic": 0, "mixed": 0, "other": 0}
    failure_reasons = FailureReasonCounts()
    total_segments = 0

    for row in result:
        theme_id, title_ar, title_en, confidence, match_type, evidence_sources, reasons_ar = row

        if theme_id not in theme_stats:
            theme_stats[theme_id] = {
                "theme_id": theme_id,
                "title_ar": title_ar or "",
                "title_en": title_en or "",
                "total": 0,
                "core": 0,
                "recommended": 0,
                "supporting": 0,
            }

        # Skip if no segment
        if confidence is None:
            continue

        total_segments += 1
        theme_stats[theme_id]["total"] += 1

        confidence = confidence or 0.0
        source_count = len(evidence_sources) if isinstance(evidence_sources, list) else 0
        match_type = match_type or ""

        # Confidence distribution
        if confidence < 0.6:
            confidence_dist["0.5-0.6"] += 1
        elif confidence < 0.7:
            confidence_dist["0.6-0.7"] += 1
        elif confidence < 0.8:
            confidence_dist["0.7-0.8"] += 1
        else:
            confidence_dist["0.8+"] += 1

        # Source distribution
        if source_count == 0:
            source_dist["0 sources"] += 1
        elif source_count == 1:
            source_dist["1 source"] += 1
        elif source_count == 2:
            source_dist["2 sources"] += 1
        else:
            source_dist["3+ sources"] += 1

        # Match type distribution
        mt = match_type.lower()
        if mt == "manual" or mt == "":
            match_dist["manual"] += 1
        elif mt == "lexical":
            match_dist["lexical"] += 1
        elif mt == "root":
            match_dist["root"] += 1
        elif mt == "semantic":
            match_dist["semantic"] += 1
        elif mt == "mixed":
            match_dist["mixed"] += 1
        else:
            match_dist["other"] += 1

        # Classify
        tier = classify_segment(confidence, source_count, match_type)
        theme_stats[theme_id][tier] += 1

        if tier == "core":
            global_tiers.core += 1
        elif tier == "recommended":
            global_tiers.recommended += 1
        else:
            global_tiers.supporting += 1
            # Track failure reason
            if not reasons_ar or len((reasons_ar or "").strip()) < 10:
                failure_reasons.missing_reasons += 1
            elif confidence < 0.70:
                failure_reasons.low_confidence += 1
            elif source_count < 2:
                failure_reasons.few_sources += 1
            elif mt in WEAK_MATCH_TYPES:
                failure_reasons.weak_match += 1

    # Build per-theme summaries
    theme_summaries = []
    themes_needing_improvement = []

    for theme_id, stats in theme_stats.items():
        quality_count = stats["core"] + stats["recommended"]
        quality_pct = (quality_count / stats["total"] * 100) if stats["total"] > 0 else 0

        theme_summaries.append(ThemeQualitySummary(
            theme_id=theme_id,
            title_ar=stats["title_ar"],
            title_en=stats["title_en"],
            total_segments=stats["total"],
            tiers=QualityTierCounts(
                core=stats["core"],
                recommended=stats["recommended"],
                supporting=stats["supporting"],
            ),
            quality_percentage=round(quality_pct, 1),
        ))

        # Track themes with no quality segments
        if quality_count == 0 and stats["total"] > 0:
            themes_needing_improvement.append(theme_id)

    # Sort by quality percentage descending
    theme_summaries.sort(key=lambda t: t.quality_percentage, reverse=True)

    # Global quality percentage
    quality_total = global_tiers.core + global_tiers.recommended
    quality_pct = (quality_total / total_segments * 100) if total_segments > 0 else 0

    return QualitySummaryResponse(
        total_segments=total_segments,
        total_themes=len(theme_stats),
        global_tiers=global_tiers,
        confidence_distribution=confidence_dist,
        source_distribution=source_dist,
        match_type_distribution=match_dist,
        failure_reasons=failure_reasons,
        quality_percentage=round(quality_pct, 1),
        themes=theme_summaries,
        themes_needing_improvement=themes_needing_improvement,
    )


# =============================================================================
# LOCATION-BASED ENDPOINTS
# =============================================================================

@router.get("/by-sura/{sura_no}", response_model=List[ThemeSummaryResponse])
async def get_themes_by_sura(
    sura_no: int = Path(..., ge=1, le=114, description="Surah number (1-114)"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all themes that appear in a specific surah."""
    service = ThemeService(session)
    themes = await service.get_themes_by_sura(sura_no)

    return [
        ThemeSummaryResponse(
            id=t.id,
            slug=t.slug,
            title_ar=t.title_ar,
            title_en=t.title_en,
            category=t.category,
            category_label_ar=t.category_label_ar,
            category_label_en=t.category_label_en,
            order_of_importance=t.order_of_importance,
            key_concepts=t.key_concepts,
            segment_count=t.segment_count,
            total_verses=t.total_verses,
            has_consequences=t.has_consequences,
            parent_id=t.parent_id,
        )
        for t in themes
    ]


@router.get("/by-category/{category}", response_model=ThemeListResponse)
async def get_themes_by_category(
    category: str = Path(..., description="Theme category"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all themes in a specific category."""
    service = ThemeService(session)
    themes, total = await service.list_themes(
        category=category,
        limit=limit,
        offset=offset,
    )

    return ThemeListResponse(
        themes=[
            ThemeSummaryResponse(
                id=t.id,
                slug=t.slug,
                title_ar=t.title_ar,
                title_en=t.title_en,
                category=t.category,
                category_label_ar=t.category_label_ar,
                category_label_en=t.category_label_en,
                order_of_importance=t.order_of_importance,
                key_concepts=t.key_concepts,
                segment_count=t.segment_count,
                total_verses=t.total_verses,
                has_consequences=t.has_consequences,
                parent_id=t.parent_id,
            )
            for t in themes
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/by-ayah/{sura_no}/{ayah_no}", response_model=List[ThemeOccurrenceResponse])
async def get_themes_by_ayah(
    sura_no: int = Path(..., ge=1, le=114),
    ayah_no: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_async_session),
):
    """Get themes that cover a specific ayah."""
    service = ThemeService(session)
    occurrences = await service.get_themes_by_ayah(sura_no, ayah_no)

    return [
        ThemeOccurrenceResponse(
            theme_id=o.theme_id,
            theme_title_ar=o.theme_title_ar,
            theme_title_en=o.theme_title_en,
            segment_id=o.segment_id,
            segment_title_ar=o.segment_title_ar,
            segment_title_en=o.segment_title_en,
            summary_ar=o.summary_ar,
            summary_en=o.summary_en,
        )
        for o in occurrences
    ]


# =============================================================================
# DETAIL ENDPOINTS
# =============================================================================

@router.get("/{theme_id}", response_model=ThemeDetailResponse)
async def get_theme(
    theme_id: str = Path(..., description="Theme ID"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get full theme detail with children."""
    service = ThemeService(session)
    theme = await service.get_theme(theme_id)

    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme not found: {theme_id}")

    return ThemeDetailResponse(
        id=theme.id,
        slug=theme.slug,
        title_ar=theme.title_ar,
        title_en=theme.title_en,
        short_title_ar=theme.short_title_ar,
        short_title_en=theme.short_title_en,
        category=theme.category,
        category_label_ar=theme.category_label_ar,
        category_label_en=theme.category_label_en,
        order_of_importance=theme.order_of_importance,
        key_concepts=theme.key_concepts,
        description_ar=theme.description_ar,
        description_en=theme.description_en,
        parent_id=theme.parent_id,
        related_theme_ids=theme.related_theme_ids,
        tafsir_sources=theme.tafsir_sources,
        segment_count=theme.segment_count,
        total_verses=theme.total_verses,
        suras_mentioned=theme.suras_mentioned,
        makki_percentage=theme.makki_percentage,
        madani_percentage=theme.madani_percentage,
        is_complete=theme.is_complete,
        children=[
            ThemeSummaryResponse(
                id=c.id,
                slug=c.slug,
                title_ar=c.title_ar,
                title_en=c.title_en,
                category=c.category,
                category_label_ar=c.category_label_ar,
                category_label_en=c.category_label_en,
                order_of_importance=c.order_of_importance,
                key_concepts=c.key_concepts,
                segment_count=c.segment_count,
                total_verses=c.total_verses,
                has_consequences=c.has_consequences,
                parent_id=c.parent_id,
            )
            for c in theme.children
        ],
    )


@router.get("/{theme_id}/segments", response_model=SegmentListResponse)
async def get_theme_segments(
    theme_id: str = Path(...),
    verified_only: bool = Query(False, description="Only return verified segments"),
    match_type: Optional[str] = Query(None, description="Filter by match_type: lexical, root, semantic, mixed, manual"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Minimum confidence threshold"),
    is_core: Optional[bool] = Query(None, description="Filter by core vs supporting segments"),
    sura_no: Optional[int] = Query(None, ge=1, le=114, description="Filter by surah number"),
    source: Optional[str] = Query(None, description="Filter by tafsir source (e.g., ibn_kathir_ar)"),
    sort: str = Query(
        "segment_order",
        regex="^(segment_order|confidence_desc|confidence_asc|sura_asc|sura_desc)$",
        description="Sort order: segment_order, confidence_desc, confidence_asc, sura_asc, sura_desc"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get segments for a theme (verse ranges with summaries).

    Filters:
    - verified_only: Only return verified segments
    - match_type: Filter by discovery method (lexical, root, semantic, mixed, manual)
    - min_confidence: Filter by minimum confidence score (0.0-1.0)
    - is_core: Filter by core (True) vs supporting (False) segments
    - sura_no: Filter by surah number (1-114)
    - source: Filter by tafsir source (e.g., 'ibn_kathir_ar')

    Sorting:
    - segment_order: Default ordering by segment order
    - confidence_desc: Highest confidence first
    - confidence_asc: Lowest confidence first
    - sura_asc: By surah number ascending
    - sura_desc: By surah number descending
    """
    service = ThemeService(session)
    segments, total = await service.get_theme_segments(
        theme_id=theme_id,
        verified_only=verified_only,
        match_type=match_type,
        min_confidence=min_confidence,
        is_core=is_core,
        sura_no=sura_no,
        source=source,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    return SegmentListResponse(
        segments=[
            ThemeSegmentResponse(
                id=s.id,
                segment_order=s.segment_order,
                chronological_index=getattr(s, 'chronological_index', None),
                sura_no=s.sura_no,
                ayah_start=s.ayah_start,
                ayah_end=s.ayah_end,
                verse_reference=getattr(s, 'verse_reference', f"{s.sura_no}:{s.ayah_start}-{s.ayah_end}"),
                title_ar=s.title_ar,
                title_en=s.title_en,
                summary_ar=s.summary_ar,
                summary_en=s.summary_en,
                semantic_tags=getattr(s, 'semantic_tags', []),
                revelation_context=getattr(s, 'revelation_context', None),
                is_entry_point=getattr(s, 'is_entry_point', False),
                is_verified=getattr(s, 'is_verified', False),
                importance_weight=getattr(s, 'importance_weight', 0.5),
                evidence_count=getattr(s, 'evidence_count', 0),
                # Discovery fields
                match_type=getattr(s, 'match_type', None),
                confidence=getattr(s, 'confidence', None),
                reasons_ar=getattr(s, 'reasons_ar', None),
                reasons_en=getattr(s, 'reasons_en', None),
                is_core=getattr(s, 'is_core', None),
                discovered_at=str(getattr(s, 'discovered_at', None)) if getattr(s, 'discovered_at', None) else None,
            )
            for s in segments
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{theme_id}/coverage", response_model=ThemeCoverageResponse)
async def get_theme_coverage(
    theme_id: str = Path(..., description="Theme ID"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get coverage statistics for a theme.

    Returns segment counts by match type, confidence bands, tafsir sources used,
    and overall Quran coverage percentage.
    """
    service = ThemeService(session)
    coverage = await service.get_theme_coverage(theme_id)

    if not coverage:
        raise HTTPException(status_code=404, detail=f"Theme not found: {theme_id}")

    return ThemeCoverageResponse(**coverage)


@router.get("/{theme_id}/segments/{segment_id}/evidence", response_model=SegmentEvidenceResponse)
async def get_segment_evidence(
    theme_id: str = Path(...),
    segment_id: str = Path(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get evidence explaining why a verse belongs to this theme ("Why this verse?").

    Returns:
    - Match type and confidence score
    - Arabic reasons explaining the connection
    - Supporting tafsir evidence with snippets
    - Matching keywords found
    """
    service = ThemeService(session)
    evidence = await service.get_segment_evidence(theme_id, segment_id)

    if not evidence:
        raise HTTPException(status_code=404, detail=f"Segment not found: {segment_id}")

    return SegmentEvidenceResponse(**evidence)


@router.get("/{theme_id}/graph", response_model=ThemeGraphResponse)
async def get_theme_graph(
    theme_id: str = Path(...),
    language: str = Query("en", regex="^(en|ar)$"),
    layout_mode: str = Query("sequential", regex="^(sequential|revelation|thematic)$"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get graph visualization data for a theme.

    Layout modes:
    - sequential: Vertical timeline by segment order
    - revelation: Group by Makki/Madani
    - thematic: Cluster by semantic tags
    """
    service = ThemeGraphService(session)
    graph = await service.build_theme_graph(
        theme_id=theme_id,
        language=language,
        layout_mode=layout_mode,
    )

    if not graph:
        raise HTTPException(status_code=404, detail=f"Theme not found: {theme_id}")

    return ThemeGraphResponse(
        theme_id=graph.theme_id,
        theme_title_ar=graph.theme_title_ar,
        theme_title_en=graph.theme_title_en,
        nodes=[
            ThemeGraphNodeResponse(
                id=n.id,
                type=n.type,
                label=n.label,
                label_ar=n.label_ar,
                data=n.data,
                x=n.x,
                y=n.y,
            )
            for n in graph.nodes
        ],
        edges=[
            ThemeGraphEdgeResponse(
                source=e.source,
                target=e.target,
                type=e.type,
                label=e.label,
                label_ar=e.label_ar,
                is_sequential=e.is_sequential,
                strength=e.strength,
                data=e.data,
            )
            for e in graph.edges
        ],
        entry_node_id=graph.entry_node_id,
        is_valid_dag=graph.is_valid_dag,
        layout_mode=graph.layout_mode,
        total_segments=graph.total_segments,
        total_connections=graph.total_connections,
    )


@router.get("/{theme_id}/timeline", response_model=List[TimelineNodeResponse])
async def get_theme_timeline(
    theme_id: str = Path(...),
    language: str = Query("en", regex="^(en|ar)$"),
    order_by: str = Query("segment_order", regex="^(segment_order|chronological|revelation)$"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get linear timeline view of theme segments.

    Order options:
    - segment_order: Default ordering
    - chronological: By chronological index
    - revelation: Makki first, then Madani
    """
    service = ThemeGraphService(session)
    timeline = await service.get_theme_timeline(
        theme_id=theme_id,
        language=language,
        order_by=order_by,
    )

    return [
        TimelineNodeResponse(
            segment_id=t.segment_id,
            segment_order=t.segment_order,
            chronological_index=t.chronological_index,
            sura_no=t.sura_no,
            ayah_start=t.ayah_start,
            ayah_end=t.ayah_end,
            verse_reference=t.verse_reference,
            title_ar=t.title_ar,
            title_en=t.title_en,
            summary_ar=t.summary_ar,
            summary_en=t.summary_en,
            revelation_context=t.revelation_context,
            is_entry_point=t.is_entry_point,
            is_verified=t.is_verified,
        )
        for t in timeline
    ]


@router.get("/{theme_id}/consequences", response_model=List[ThemeConsequenceResponse])
async def get_theme_consequences(
    theme_id: str = Path(...),
    consequence_type: Optional[str] = Query(
        None,
        regex="^(reward|punishment|blessing|warning|promise)$",
        description="Filter by consequence type"
    ),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get divine consequences (السنن الإلهية) for a theme.

    Types:
    - reward: Promised rewards in akhirah
    - punishment: Warned punishments
    - blessing: Worldly blessings
    - warning: Divine warnings
    - promise: Divine promises
    """
    service = ThemeService(session)
    consequences = await service.get_theme_consequences(
        theme_id=theme_id,
        consequence_type=consequence_type,
    )

    return [
        ThemeConsequenceResponse(
            id=c.id,
            consequence_type=c.consequence_type,
            type_label_ar=c.type_label_ar,
            type_label_en=c.type_label_en,
            description_ar=c.description_ar,
            description_en=c.description_en,
            supporting_verses=c.supporting_verses,
            evidence_count=c.evidence_count,
        )
        for c in consequences
    ]


@router.get("/{theme_id}/related", response_model=List[ThemeSummaryResponse])
async def get_related_themes(
    theme_id: str = Path(...),
    session: AsyncSession = Depends(get_async_session),
):
    """Get themes related to this one."""
    service = ThemeService(session)
    related = await service.get_related_themes(theme_id)

    return [
        ThemeSummaryResponse(
            id=t.id,
            slug=t.slug,
            title_ar=t.title_ar,
            title_en=t.title_en,
            category=t.category,
            category_label_ar=t.category_label_ar,
            category_label_en=t.category_label_en,
            order_of_importance=t.order_of_importance,
            key_concepts=t.key_concepts,
            segment_count=t.segment_count,
            total_verses=t.total_verses,
            has_consequences=t.has_consequences,
            parent_id=t.parent_id,
        )
        for t in related
    ]


@router.get("/{theme_id}/cross-connections", response_model=List[CrossThemeConnectionResponse])
async def get_cross_theme_connections(
    theme_id: str = Path(...),
    session: AsyncSession = Depends(get_async_session),
):
    """Get connections to other themes (related, siblings, overlapping)."""
    service = ThemeGraphService(session)
    connections = await service.get_cross_theme_connections(theme_id)

    return [
        CrossThemeConnectionResponse(**c)
        for c in connections
    ]
