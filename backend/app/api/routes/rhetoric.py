"""
Arabic Rhetoric (علم البلاغة) API Routes

Endpoints for:
1. Rhetorical Device Detection - Arabic rhetoric tagging with tafsir grounding
2. Discourse Segmentation - Classify verse clusters by discourse type
3. Tone/Sentiment Detection - Tag emotional context of verses

All data is grounded in balagha-focused tafsir sources:
- Al-Zamakhshari (الكشاف)
- Al-Razi (التفسير الكبير)
- Abu Su'ud (إرشاد العقل السليم)
- Ibn Ashur (التحرير والتنوير)
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.services.rhetorical_analyzer import RhetoricalAnalyzer
from app.services.discourse_classifier import DiscourseClassifier
from app.services.tone_analyzer import ToneAnalyzer
from app.core.responses import APIError, ErrorCode, get_request_id

router = APIRouter()


# =============================================================================
# RHETORICAL DEVICES - RESPONSE SCHEMAS
# =============================================================================

class RhetoricalDeviceSummaryResponse(BaseModel):
    """Summary of a rhetorical device type."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    occurrence_count: int = 0


class RhetoricalDeviceDetailResponse(BaseModel):
    """Full detail of a rhetorical device type."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    category: str
    category_label_ar: str
    category_label_en: str
    definition_ar: Optional[str] = None
    definition_en: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None
    sub_types: Optional[List[Dict[str, Any]]] = None
    parent_device_id: Optional[str] = None
    is_active: bool = True


class RhetoricalDeviceListResponse(BaseModel):
    """Response for device type listing."""
    devices: List[RhetoricalDeviceSummaryResponse]
    total: int
    offset: int
    limit: int


class CategoryFacetResponse(BaseModel):
    """Balagha category with count."""
    category: str
    label_ar: str
    label_en: str
    count: int


class RhetoricalOccurrenceResponse(BaseModel):
    """Occurrence of a rhetorical device."""
    id: int
    device_type_id: str
    device_name_ar: str
    device_name_en: str
    device_category: str
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    text_snippet_ar: Optional[str] = None
    explanation_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    evidence_count: int = 0
    confidence: float = 1.0
    source: Optional[str] = None
    is_verified: bool = False


class OccurrenceListResponse(BaseModel):
    """Response for occurrence listing."""
    occurrences: List[RhetoricalOccurrenceResponse]
    total: int
    offset: int
    limit: int


class RhetoricalStatsResponse(BaseModel):
    """Rhetorical analysis statistics."""
    total_device_types: int
    total_occurrences: int
    verified_occurrences: int
    verification_rate: float
    by_category: Dict[str, int]
    by_source: Dict[str, int]


# =============================================================================
# DISCOURSE SEGMENTS - RESPONSE SCHEMAS
# =============================================================================

class DiscourseSegmentSummaryResponse(BaseModel):
    """Summary of a discourse segment."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    discourse_type: str
    type_label_ar: str
    type_label_en: str
    sub_type: Optional[str] = None
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    linked_story_id: Optional[str] = None
    is_verified: bool = False


class DiscourseSegmentDetailResponse(BaseModel):
    """Full detail of a discourse segment."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    discourse_type: str
    type_label_ar: str
    type_label_en: str
    sub_type: Optional[str] = None
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None
    linked_story_id: Optional[str] = None
    linked_segment_ids: Optional[List[str]] = None
    evidence_count: int = 0
    confidence: float = 1.0
    source: Optional[str] = None
    is_verified: bool = False


class DiscourseSegmentListResponse(BaseModel):
    """Response for segment listing."""
    segments: List[DiscourseSegmentSummaryResponse]
    total: int
    offset: int
    limit: int


class DiscourseTypeFacetResponse(BaseModel):
    """Discourse type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


class SurahDiscourseProfileResponse(BaseModel):
    """Discourse profile for a surah."""
    sura_no: int
    total_segments: int
    type_distribution: Dict[str, int]
    dominant_type: str
    narrative_segments: int
    has_legal_rulings: bool
    has_stories: bool


class DiscourseStatsResponse(BaseModel):
    """Discourse classification statistics."""
    total_segments: int
    verified_segments: int
    verification_rate: float
    story_linked_segments: int
    surahs_covered: int
    by_type: Dict[str, int]


# =============================================================================
# TONE ANNOTATIONS - RESPONSE SCHEMAS
# =============================================================================

class ToneAnnotationSummaryResponse(BaseModel):
    """Summary of a tone annotation."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    tone_type: str
    tone_label_ar: str
    tone_label_en: str
    intensity: float = 0.5
    is_verified: bool = False


class ToneAnnotationDetailResponse(BaseModel):
    """Full detail of a tone annotation."""
    id: int
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    tone_type: str
    tone_label_ar: str
    tone_label_en: str
    intensity: float = 0.5
    explanation_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    evidence_count: int = 0
    confidence: float = 1.0
    source: Optional[str] = None
    is_verified: bool = False


class ToneAnnotationListResponse(BaseModel):
    """Response for tone annotation listing."""
    annotations: List[ToneAnnotationSummaryResponse]
    total: int
    offset: int
    limit: int


class ToneTypeFacetResponse(BaseModel):
    """Tone type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


class SurahToneProfileResponse(BaseModel):
    """Tone profile for a surah."""
    sura_no: int
    total_annotations: int
    tone_distribution: Dict[str, int]
    dominant_tone: str
    average_intensity: float
    intensity_by_tone: Dict[str, float]
    has_warning: bool
    has_glad_tidings: bool
    emotional_range: List[str]


class ToneStatsResponse(BaseModel):
    """Tone analysis statistics."""
    total_annotations: int
    verified_annotations: int
    verification_rate: float
    average_intensity: float
    high_intensity_count: int
    surahs_covered: int
    by_type: Dict[str, int]


# =============================================================================
# RHETORICAL DEVICES ENDPOINTS
# =============================================================================

@router.get("/devices", response_model=RhetoricalDeviceListResponse)
async def list_rhetorical_devices(
    category: Optional[str] = Query(None, description="Filter by balagha category (bayaan, maani, badeea)"),
    search: Optional[str] = Query(None, description="Search in names and definitions"),
    include_inactive: bool = Query(False, description="Include inactive devices"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List rhetorical device types.

    Categories (علم البلاغة):
    - bayaan (علم البيان): Figures of speech - metaphor, simile, metonymy
    - maani (علم المعاني): Semantics - inversion, ellipsis, rhetorical question
    - badeea (علم البديع): Embellishment - antithesis, paronomasia, person shift
    """
    analyzer = RhetoricalAnalyzer(session)
    devices, total = await analyzer.list_device_types(
        category=category,
        search=search,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )

    return RhetoricalDeviceListResponse(
        devices=[
            RhetoricalDeviceSummaryResponse(
                id=d.id,
                slug=d.slug,
                name_ar=d.name_ar,
                name_en=d.name_en,
                category=d.category,
                category_label_ar=d.category_label_ar,
                category_label_en=d.category_label_en,
                occurrence_count=d.occurrence_count,
            )
            for d in devices
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/devices/categories", response_model=List[CategoryFacetResponse])
async def get_balagha_categories(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get the three classical balagha categories with device counts.

    1. علم البيان (Bayaan) - Figures of Speech
    2. علم المعاني (Maani) - Semantics
    3. علم البديع (Badeea) - Embellishment
    """
    analyzer = RhetoricalAnalyzer(session)
    facets = await analyzer.get_categories()

    return [
        CategoryFacetResponse(
            category=f.category,
            label_ar=f.label_ar,
            label_en=f.label_en,
            count=f.count,
        )
        for f in facets
    ]


@router.get("/devices/{device_id}", response_model=RhetoricalDeviceDetailResponse)
async def get_rhetorical_device(
    request: Request,
    device_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get full details of a rhetorical device type including examples."""
    analyzer = RhetoricalAnalyzer(session)
    device = await analyzer.get_device_type(device_id)

    if not device:
        raise APIError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message_en=f"Rhetorical device '{device_id}' not found",
            message_ar=f"الأسلوب البلاغي '{device_id}' غير موجود",
            request_id=get_request_id(request),
            status_code=404
        )

    return RhetoricalDeviceDetailResponse(
        id=device.id,
        slug=device.slug,
        name_ar=device.name_ar,
        name_en=device.name_en,
        category=device.category,
        category_label_ar=device.category_label_ar,
        category_label_en=device.category_label_en,
        definition_ar=device.definition_ar,
        definition_en=device.definition_en,
        examples=device.examples,
        sub_types=device.sub_types,
        parent_device_id=device.parent_device_id,
        is_active=device.is_active,
    )


# =============================================================================
# RHETORICAL OCCURRENCES ENDPOINTS
# =============================================================================

@router.get("/occurrences", response_model=OccurrenceListResponse)
async def list_rhetorical_occurrences(
    device_type_id: Optional[str] = Query(None, description="Filter by device type"),
    sura_no: Optional[int] = Query(None, ge=1, le=114, description="Filter by surah"),
    category: Optional[str] = Query(None, description="Filter by balagha category"),
    verified_only: bool = Query(False, description="Only verified occurrences"),
    source: Optional[str] = Query(None, description="Filter by source (balagha_tafsir, curated, llm_extraction)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List rhetorical device occurrences with filtering.

    All occurrences are grounded in tafsir evidence (evidence_chunk_ids).
    """
    analyzer = RhetoricalAnalyzer(session)
    occurrences, total = await analyzer.list_occurrences(
        device_type_id=device_type_id,
        sura_no=sura_no,
        category=category,
        verified_only=verified_only,
        source=source,
        limit=limit,
        offset=offset,
    )

    return OccurrenceListResponse(
        occurrences=[
            RhetoricalOccurrenceResponse(
                id=o.id,
                device_type_id=o.device_type_id,
                device_name_ar=o.device_name_ar,
                device_name_en=o.device_name_en,
                device_category=o.device_category,
                sura_no=o.sura_no,
                ayah_start=o.ayah_start,
                ayah_end=o.ayah_end,
                verse_reference=o.verse_reference,
                text_snippet_ar=o.text_snippet_ar,
                explanation_ar=o.explanation_ar,
                explanation_en=o.explanation_en,
                evidence_count=o.evidence_count,
                confidence=o.confidence,
                source=o.source,
                is_verified=o.is_verified,
            )
            for o in occurrences
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/occurrences/by-verse/{sura_no}/{ayah_no}", response_model=List[RhetoricalOccurrenceResponse])
async def get_occurrences_by_verse(
    sura_no: int,
    ayah_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all rhetorical device occurrences for a specific verse."""
    analyzer = RhetoricalAnalyzer(session)
    occurrences = await analyzer.get_occurrences_by_verse(sura_no, ayah_no)

    return [
        RhetoricalOccurrenceResponse(
            id=o.id,
            device_type_id=o.device_type_id,
            device_name_ar=o.device_name_ar,
            device_name_en=o.device_name_en,
            device_category=o.device_category,
            sura_no=o.sura_no,
            ayah_start=o.ayah_start,
            ayah_end=o.ayah_end,
            verse_reference=o.verse_reference,
            text_snippet_ar=o.text_snippet_ar,
            explanation_ar=o.explanation_ar,
            explanation_en=o.explanation_en,
            evidence_count=o.evidence_count,
            confidence=o.confidence,
            source=o.source,
            is_verified=o.is_verified,
        )
        for o in occurrences
    ]


@router.get("/occurrences/by-sura/{sura_no}")
async def get_occurrences_by_sura(
    sura_no: int,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all rhetorical device occurrences for a surah with summary.

    Returns occurrences and a count by device type.
    """
    analyzer = RhetoricalAnalyzer(session)
    occurrences, device_counts = await analyzer.get_occurrences_by_sura(sura_no, limit)

    return {
        "sura_no": sura_no,
        "occurrences": [
            RhetoricalOccurrenceResponse(
                id=o.id,
                device_type_id=o.device_type_id,
                device_name_ar=o.device_name_ar,
                device_name_en=o.device_name_en,
                device_category=o.device_category,
                sura_no=o.sura_no,
                ayah_start=o.ayah_start,
                ayah_end=o.ayah_end,
                verse_reference=o.verse_reference,
                text_snippet_ar=o.text_snippet_ar,
                explanation_ar=o.explanation_ar,
                explanation_en=o.explanation_en,
                evidence_count=o.evidence_count,
                confidence=o.confidence,
                source=o.source,
                is_verified=o.is_verified,
            )
            for o in occurrences
        ],
        "device_counts": device_counts,
        "total_occurrences": len(occurrences),
    }


@router.get("/statistics", response_model=RhetoricalStatsResponse)
async def get_rhetorical_statistics(
    session: AsyncSession = Depends(get_async_session),
):
    """Get overall rhetorical analysis statistics."""
    analyzer = RhetoricalAnalyzer(session)
    stats = await analyzer.get_statistics()

    return RhetoricalStatsResponse(**stats)


# =============================================================================
# DISCOURSE SEGMENTATION ENDPOINTS
# =============================================================================

@router.get("/discourse", response_model=DiscourseSegmentListResponse)
async def list_discourse_segments(
    discourse_type: Optional[str] = Query(None, description="Filter by discourse type"),
    sura_no: Optional[int] = Query(None, ge=1, le=114, description="Filter by surah"),
    linked_story_id: Optional[str] = Query(None, description="Filter by linked story"),
    verified_only: bool = Query(False, description="Only verified segments"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List discourse segments with filtering.

    Discourse types:
    - narrative: Story narration (قصصي)
    - exhortation: Moral guidance (وعظي)
    - legal_ruling: Jurisprudential verses (تشريعي)
    - supplication: Prayers (دعائي)
    - promise: Divine promises (وعد)
    - warning: Warnings (وعيد)
    - parable: Parables (مثلي)
    - argumentation: Logical arguments (حجاجي)
    """
    classifier = DiscourseClassifier(session)
    segments, total = await classifier.list_segments(
        discourse_type=discourse_type,
        sura_no=sura_no,
        linked_story_id=linked_story_id,
        verified_only=verified_only,
        limit=limit,
        offset=offset,
    )

    return DiscourseSegmentListResponse(
        segments=[
            DiscourseSegmentSummaryResponse(
                id=s.id,
                sura_no=s.sura_no,
                ayah_start=s.ayah_start,
                ayah_end=s.ayah_end,
                verse_reference=s.verse_reference,
                discourse_type=s.discourse_type,
                type_label_ar=s.type_label_ar,
                type_label_en=s.type_label_en,
                sub_type=s.sub_type,
                title_ar=s.title_ar,
                title_en=s.title_en,
                linked_story_id=s.linked_story_id,
                is_verified=s.is_verified,
            )
            for s in segments
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/discourse/types", response_model=List[DiscourseTypeFacetResponse])
async def get_discourse_types(
    session: AsyncSession = Depends(get_async_session),
):
    """Get available discourse types with counts."""
    classifier = DiscourseClassifier(session)
    facets = await classifier.get_discourse_types()

    return [
        DiscourseTypeFacetResponse(
            type=f.type,
            label_ar=f.label_ar,
            label_en=f.label_en,
            count=f.count,
        )
        for f in facets
    ]


@router.get("/discourse/{segment_id}", response_model=DiscourseSegmentDetailResponse)
async def get_discourse_segment(
    request: Request,
    segment_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get full details of a discourse segment."""
    classifier = DiscourseClassifier(session)
    segment = await classifier.get_segment(segment_id)

    if not segment:
        raise APIError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message_en=f"Discourse segment {segment_id} not found",
            message_ar=f"المقطع الخطابي {segment_id} غير موجود",
            request_id=get_request_id(request),
            status_code=404
        )

    return DiscourseSegmentDetailResponse(
        id=segment.id,
        sura_no=segment.sura_no,
        ayah_start=segment.ayah_start,
        ayah_end=segment.ayah_end,
        verse_reference=segment.verse_reference,
        discourse_type=segment.discourse_type,
        type_label_ar=segment.type_label_ar,
        type_label_en=segment.type_label_en,
        sub_type=segment.sub_type,
        title_ar=segment.title_ar,
        title_en=segment.title_en,
        summary_ar=segment.summary_ar,
        summary_en=segment.summary_en,
        linked_story_id=segment.linked_story_id,
        linked_segment_ids=segment.linked_segment_ids,
        evidence_count=segment.evidence_count,
        confidence=segment.confidence,
        source=segment.source,
        is_verified=segment.is_verified,
    )


@router.get("/discourse/by-verse/{sura_no}/{ayah_no}", response_model=List[DiscourseSegmentSummaryResponse])
async def get_discourse_by_verse(
    sura_no: int,
    ayah_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get discourse segments containing a specific verse."""
    classifier = DiscourseClassifier(session)
    segments = await classifier.get_segments_by_verse(sura_no, ayah_no)

    return [
        DiscourseSegmentSummaryResponse(
            id=s.id,
            sura_no=s.sura_no,
            ayah_start=s.ayah_start,
            ayah_end=s.ayah_end,
            verse_reference=s.verse_reference,
            discourse_type=s.discourse_type,
            type_label_ar=s.type_label_ar,
            type_label_en=s.type_label_en,
            sub_type=s.sub_type,
            title_ar=s.title_ar,
            title_en=s.title_en,
            linked_story_id=s.linked_story_id,
            is_verified=s.is_verified,
        )
        for s in segments
    ]


@router.get("/discourse/profile/{sura_no}", response_model=SurahDiscourseProfileResponse)
async def get_surah_discourse_profile(
    sura_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get the discourse profile for a surah."""
    classifier = DiscourseClassifier(session)
    profile = await classifier.get_surah_discourse_profile(sura_no)

    return SurahDiscourseProfileResponse(
        sura_no=profile.sura_no,
        total_segments=profile.total_segments,
        type_distribution=profile.type_distribution,
        dominant_type=profile.dominant_type,
        narrative_segments=profile.narrative_segments,
        has_legal_rulings=profile.has_legal_rulings,
        has_stories=profile.has_stories,
    )


@router.get("/discourse/by-story/{story_id}", response_model=List[DiscourseSegmentSummaryResponse])
async def get_discourse_by_story(
    story_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all discourse segments linked to a specific story."""
    classifier = DiscourseClassifier(session)
    segments = await classifier.get_segments_by_story(story_id)

    return [
        DiscourseSegmentSummaryResponse(
            id=s.id,
            sura_no=s.sura_no,
            ayah_start=s.ayah_start,
            ayah_end=s.ayah_end,
            verse_reference=s.verse_reference,
            discourse_type=s.discourse_type,
            type_label_ar=s.type_label_ar,
            type_label_en=s.type_label_en,
            sub_type=s.sub_type,
            title_ar=s.title_ar,
            title_en=s.title_en,
            linked_story_id=s.linked_story_id,
            is_verified=s.is_verified,
        )
        for s in segments
    ]


@router.get("/discourse/statistics", response_model=DiscourseStatsResponse)
async def get_discourse_statistics(
    session: AsyncSession = Depends(get_async_session),
):
    """Get overall discourse classification statistics."""
    classifier = DiscourseClassifier(session)
    stats = await classifier.get_statistics()

    return DiscourseStatsResponse(**stats)


# =============================================================================
# TONE ANALYSIS ENDPOINTS
# =============================================================================

@router.get("/tones", response_model=ToneAnnotationListResponse)
async def list_tone_annotations(
    tone_type: Optional[str] = Query(None, description="Filter by tone type"),
    sura_no: Optional[int] = Query(None, ge=1, le=114, description="Filter by surah"),
    min_intensity: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum intensity"),
    verified_only: bool = Query(False, description="Only verified annotations"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List tone annotations with filtering.

    Tone types:
    - hope: Hope/expectation (رجاء)
    - fear: Fear/reverence (خوف)
    - awe: Awe/humility (خشوع)
    - glad_tidings: Good news (بشارة)
    - warning: Warning (تحذير)
    - consolation: Comfort (تسلية)
    - gratitude: Thankfulness (شكر)
    - urgency: Time-sensitive call (استعجال)
    """
    analyzer = ToneAnalyzer(session)
    annotations, total = await analyzer.list_annotations(
        tone_type=tone_type,
        sura_no=sura_no,
        min_intensity=min_intensity,
        verified_only=verified_only,
        limit=limit,
        offset=offset,
    )

    return ToneAnnotationListResponse(
        annotations=[
            ToneAnnotationSummaryResponse(
                id=a.id,
                sura_no=a.sura_no,
                ayah_start=a.ayah_start,
                ayah_end=a.ayah_end,
                verse_reference=a.verse_reference,
                tone_type=a.tone_type,
                tone_label_ar=a.tone_label_ar,
                tone_label_en=a.tone_label_en,
                intensity=a.intensity,
                is_verified=a.is_verified,
            )
            for a in annotations
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/tones/types", response_model=List[ToneTypeFacetResponse])
async def get_tone_types(
    session: AsyncSession = Depends(get_async_session),
):
    """Get available tone types with counts."""
    analyzer = ToneAnalyzer(session)
    facets = await analyzer.get_tone_types()

    return [
        ToneTypeFacetResponse(
            type=f.type,
            label_ar=f.label_ar,
            label_en=f.label_en,
            count=f.count,
        )
        for f in facets
    ]


@router.get("/tones/{annotation_id}", response_model=ToneAnnotationDetailResponse)
async def get_tone_annotation(
    request: Request,
    annotation_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get full details of a tone annotation."""
    analyzer = ToneAnalyzer(session)
    annotation = await analyzer.get_annotation(annotation_id)

    if not annotation:
        raise APIError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message_en=f"Tone annotation {annotation_id} not found",
            message_ar=f"تصنيف النبرة {annotation_id} غير موجود",
            request_id=get_request_id(request),
            status_code=404
        )

    return ToneAnnotationDetailResponse(
        id=annotation.id,
        sura_no=annotation.sura_no,
        ayah_start=annotation.ayah_start,
        ayah_end=annotation.ayah_end,
        verse_reference=annotation.verse_reference,
        tone_type=annotation.tone_type,
        tone_label_ar=annotation.tone_label_ar,
        tone_label_en=annotation.tone_label_en,
        intensity=annotation.intensity,
        explanation_ar=annotation.explanation_ar,
        explanation_en=annotation.explanation_en,
        evidence_count=annotation.evidence_count,
        confidence=annotation.confidence,
        source=annotation.source,
        is_verified=annotation.is_verified,
    )


@router.get("/tones/by-verse/{sura_no}/{ayah_no}", response_model=List[ToneAnnotationSummaryResponse])
async def get_tones_by_verse(
    sura_no: int,
    ayah_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get tone annotations for a specific verse."""
    analyzer = ToneAnalyzer(session)
    annotations = await analyzer.get_annotations_by_verse(sura_no, ayah_no)

    return [
        ToneAnnotationSummaryResponse(
            id=a.id,
            sura_no=a.sura_no,
            ayah_start=a.ayah_start,
            ayah_end=a.ayah_end,
            verse_reference=a.verse_reference,
            tone_type=a.tone_type,
            tone_label_ar=a.tone_label_ar,
            tone_label_en=a.tone_label_en,
            intensity=a.intensity,
            is_verified=a.is_verified,
        )
        for a in annotations
    ]


@router.get("/tones/profile/{sura_no}", response_model=SurahToneProfileResponse)
async def get_surah_tone_profile(
    sura_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get the emotional tone profile for a surah."""
    analyzer = ToneAnalyzer(session)
    profile = await analyzer.get_surah_tone_profile(sura_no)

    return SurahToneProfileResponse(
        sura_no=profile.sura_no,
        total_annotations=profile.total_annotations,
        tone_distribution=profile.tone_distribution,
        dominant_tone=profile.dominant_tone,
        average_intensity=profile.average_intensity,
        intensity_by_tone=profile.intensity_by_tone,
        has_warning=profile.has_warning,
        has_glad_tidings=profile.has_glad_tidings,
        emotional_range=profile.emotional_range,
    )


@router.get("/tones/high-intensity", response_model=List[ToneAnnotationSummaryResponse])
async def get_high_intensity_verses(
    sura_no: Optional[int] = Query(None, ge=1, le=114, description="Filter by surah"),
    tone_type: Optional[str] = Query(None, description="Filter by tone type"),
    min_intensity: float = Query(0.8, ge=0.5, le=1.0, description="Minimum intensity threshold"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """Get verses with high emotional intensity."""
    analyzer = ToneAnalyzer(session)
    annotations = await analyzer.get_high_intensity_verses(
        sura_no=sura_no,
        tone_type=tone_type,
        min_intensity=min_intensity,
        limit=limit,
    )

    return [
        ToneAnnotationSummaryResponse(
            id=a.id,
            sura_no=a.sura_no,
            ayah_start=a.ayah_start,
            ayah_end=a.ayah_end,
            verse_reference=a.verse_reference,
            tone_type=a.tone_type,
            tone_label_ar=a.tone_label_ar,
            tone_label_en=a.tone_label_en,
            intensity=a.intensity,
            is_verified=a.is_verified,
        )
        for a in annotations
    ]


@router.get("/tones/statistics", response_model=ToneStatsResponse)
async def get_tone_statistics(
    session: AsyncSession = Depends(get_async_session),
):
    """Get overall tone analysis statistics."""
    analyzer = ToneAnalyzer(session)
    stats = await analyzer.get_statistics()

    return ToneStatsResponse(**stats)


# =============================================================================
# COMBINED VERSE ANALYSIS ENDPOINT
# =============================================================================

class VerseAnalysisResponse(BaseModel):
    """Combined rhetorical, discourse, and tone analysis for a verse."""
    sura_no: int
    ayah_no: int
    rhetorical_devices: List[RhetoricalOccurrenceResponse]
    discourse_segments: List[DiscourseSegmentSummaryResponse]
    tones: List[ToneAnnotationSummaryResponse]
    total_devices: int
    total_segments: int
    total_tones: int


@router.get("/analyze/{sura_no}/{ayah_no}", response_model=VerseAnalysisResponse)
async def analyze_verse(
    sura_no: int,
    ayah_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get complete rhetorical, discourse, and tone analysis for a verse.

    Combines all three analytical dimensions:
    - Rhetorical devices (what balagha techniques are used)
    - Discourse type (what is the communicative function)
    - Emotional tone (what is the emotional context)
    """
    rhetorical_analyzer = RhetoricalAnalyzer(session)
    discourse_classifier = DiscourseClassifier(session)
    tone_analyzer = ToneAnalyzer(session)

    # Get all analysis types
    devices = await rhetorical_analyzer.get_occurrences_by_verse(sura_no, ayah_no)
    segments = await discourse_classifier.get_segments_by_verse(sura_no, ayah_no)
    tones = await tone_analyzer.get_annotations_by_verse(sura_no, ayah_no)

    return VerseAnalysisResponse(
        sura_no=sura_no,
        ayah_no=ayah_no,
        rhetorical_devices=[
            RhetoricalOccurrenceResponse(
                id=o.id,
                device_type_id=o.device_type_id,
                device_name_ar=o.device_name_ar,
                device_name_en=o.device_name_en,
                device_category=o.device_category,
                sura_no=o.sura_no,
                ayah_start=o.ayah_start,
                ayah_end=o.ayah_end,
                verse_reference=o.verse_reference,
                text_snippet_ar=o.text_snippet_ar,
                explanation_ar=o.explanation_ar,
                explanation_en=o.explanation_en,
                evidence_count=o.evidence_count,
                confidence=o.confidence,
                source=o.source,
                is_verified=o.is_verified,
            )
            for o in devices
        ],
        discourse_segments=[
            DiscourseSegmentSummaryResponse(
                id=s.id,
                sura_no=s.sura_no,
                ayah_start=s.ayah_start,
                ayah_end=s.ayah_end,
                verse_reference=s.verse_reference,
                discourse_type=s.discourse_type,
                type_label_ar=s.type_label_ar,
                type_label_en=s.type_label_en,
                sub_type=s.sub_type,
                title_ar=s.title_ar,
                title_en=s.title_en,
                linked_story_id=s.linked_story_id,
                is_verified=s.is_verified,
            )
            for s in segments
        ],
        tones=[
            ToneAnnotationSummaryResponse(
                id=a.id,
                sura_no=a.sura_no,
                ayah_start=a.ayah_start,
                ayah_end=a.ayah_end,
                verse_reference=a.verse_reference,
                tone_type=a.tone_type,
                tone_label_ar=a.tone_label_ar,
                tone_label_en=a.tone_label_en,
                intensity=a.intensity,
                is_verified=a.is_verified,
            )
            for a in tones
        ],
        total_devices=len(devices),
        total_segments=len(segments),
        total_tones=len(tones),
    )
