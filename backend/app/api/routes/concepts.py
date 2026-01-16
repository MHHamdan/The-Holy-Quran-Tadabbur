"""
Concept Graph API Routes - Quran-wide semantic navigation.

Endpoints:
- GET /concepts: List concepts with filtering
- GET /concepts/types: Get concept types with counts
- GET /concepts/search: Search concepts
- GET /concepts/{concept_id}: Get concept detail
- GET /concepts/{concept_id}/occurrences: Get concept occurrences
- GET /concepts/{concept_id}/associations: Get related concepts
- GET /concepts/by-story/{story_id}: Get concepts for a story
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.db.database import get_async_session
from app.services.concept_graph import ConceptGraphService
from app.core.responses import APIError, ErrorCode, get_request_id
from app.core.auth import require_admin, AdminUser
from app.models.quran import QuranVerse

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class ConceptSummaryResponse(BaseModel):
    """Summary of a concept."""
    id: str
    slug: str
    label_ar: str
    label_en: str
    type: str
    icon_hint: Optional[str] = None
    is_curated: bool = False
    occurrence_count: int = 0


class ConceptListResponse(BaseModel):
    """Response for concept listing."""
    concepts: List[ConceptSummaryResponse]
    total: int
    offset: int
    limit: int


class ConceptDetailResponse(BaseModel):
    """Full concept detail."""
    id: str
    slug: str
    label_ar: str
    label_en: str
    type: str
    aliases_ar: List[str] = []
    aliases_en: List[str] = []
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    parent_id: Optional[str] = None
    icon_hint: Optional[str] = None
    is_curated: bool = False
    source: Optional[str] = None


class OccurrenceResponse(BaseModel):
    """Occurrence of a concept."""
    id: int
    concept_id: str
    ref_type: str
    ref_id: Optional[str] = None
    sura_no: Optional[int] = None
    ayah_start: Optional[int] = None
    ayah_end: Optional[int] = None
    page_no: Optional[int] = None  # Mushaf page number for navigation
    verse_reference: str = ""
    weight: float = 1.0
    context_ar: Optional[str] = None
    context_en: Optional[str] = None
    has_evidence: bool = False
    is_verified: bool = False


class OccurrenceListResponse(BaseModel):
    """Response for occurrence listing."""
    occurrences: List[OccurrenceResponse]
    total: int
    offset: int
    limit: int


class AssociationResponse(BaseModel):
    """Association between concepts."""
    id: int
    concept_a_id: str
    concept_b_id: str
    other_concept_id: str
    other_concept_label_ar: str
    other_concept_label_en: str
    other_concept_type: str
    relation_type: str
    relation_label_ar: str
    relation_label_en: str
    is_directional: bool = False
    strength: float = 0.5
    explanation_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    has_sufficient_evidence: bool = False


class ConceptTypeFacetResponse(BaseModel):
    """Concept type with count."""
    type: str
    label_ar: str
    label_en: str
    count: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=ConceptListResponse)
async def list_concepts(
    type: Optional[str] = Query(None, description="Filter by concept type"),
    search: Optional[str] = Query(None, description="Search in labels"),
    curated_only: bool = Query(False, description="Only curated concepts"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List concepts with optional filtering.

    Concept types: person, nation, place, miracle, theme, moral_pattern, rhetorical
    """
    service = ConceptGraphService(session)
    concepts, total = await service.list_concepts(
        concept_type=type,
        search=search,
        curated_only=curated_only,
        limit=limit,
        offset=offset,
    )

    return ConceptListResponse(
        concepts=[
            ConceptSummaryResponse(
                id=c.id,
                slug=c.slug,
                label_ar=c.label_ar,
                label_en=c.label_en,
                type=c.concept_type,
                icon_hint=c.icon_hint,
                is_curated=c.is_curated,
                occurrence_count=c.occurrence_count,
            )
            for c in concepts
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/types", response_model=List[ConceptTypeFacetResponse])
async def get_concept_types(
    session: AsyncSession = Depends(get_async_session),
):
    """Get available concept types with counts."""
    service = ConceptGraphService(session)
    facets = await service.get_concept_types()

    return [
        ConceptTypeFacetResponse(
            type=f.type,
            label_ar=f.label_ar,
            label_en=f.label_en,
            count=f.count,
        )
        for f in facets
    ]


@router.get("/search", response_model=List[ConceptSummaryResponse])
async def search_concepts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
):
    """Search concepts by text across labels, aliases, and descriptions."""
    service = ConceptGraphService(session)
    concepts = await service.search_concepts(q, limit=limit)

    return [
        ConceptSummaryResponse(
            id=c.id,
            slug=c.slug,
            label_ar=c.label_ar,
            label_en=c.label_en,
            type=c.concept_type,
            icon_hint=c.icon_hint,
            is_curated=c.is_curated,
            occurrence_count=c.occurrence_count,
        )
        for c in concepts
    ]


@router.get("/by-story/{story_id}", response_model=List[ConceptSummaryResponse])
async def get_concepts_by_story(
    story_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all concepts associated with a story."""
    service = ConceptGraphService(session)
    concepts = await service.get_concepts_by_story(story_id)

    return [
        ConceptSummaryResponse(
            id=c.id,
            slug=c.slug,
            label_ar=c.label_ar,
            label_en=c.label_en,
            type=c.concept_type,
            icon_hint=c.icon_hint,
            is_curated=c.is_curated,
            occurrence_count=c.occurrence_count,
        )
        for c in concepts
    ]


@router.get("/{concept_id}", response_model=ConceptDetailResponse)
async def get_concept(
    request: Request,
    concept_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get concept detail by ID."""
    service = ConceptGraphService(session)
    concept = await service.get_concept(concept_id)

    if not concept:
        raise APIError(
            code=ErrorCode.CONCEPT_NOT_FOUND,
            message_en=f"Concept '{concept_id}' not found",
            message_ar=f"المفهوم '{concept_id}' غير موجود",
            request_id=get_request_id(request),
            status_code=404
        )

    return ConceptDetailResponse(
        id=concept.id,
        slug=concept.slug,
        label_ar=concept.label_ar,
        label_en=concept.label_en,
        type=concept.concept_type,
        aliases_ar=concept.aliases_ar,
        aliases_en=concept.aliases_en,
        description_ar=concept.description_ar,
        description_en=concept.description_en,
        parent_id=concept.parent_id,
        icon_hint=concept.icon_hint,
        is_curated=concept.is_curated,
        source=concept.source,
    )


@router.get("/{concept_id}/occurrences", response_model=OccurrenceListResponse)
async def get_concept_occurrences(
    concept_id: str,
    ref_type: Optional[str] = Query(None, description="Filter by ref type (ayah, segment, story, cluster)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_verse_text: bool = Query(True, description="Include verse text snippets as context"),
    session: AsyncSession = Depends(get_async_session),
):
    """Get occurrences for a concept (where it appears in Quran/stories)."""
    service = ConceptGraphService(session)
    occurrences, total = await service.get_concept_occurrences(
        concept_id=concept_id,
        ref_type=ref_type,
        limit=limit,
        offset=offset,
    )

    # Build maps for verse data (page_no and text) from QuranVerse table
    verse_refs = [(o.sura_no, o.ayah_start) for o in occurrences if o.sura_no and o.ayah_start]
    page_map: dict[tuple[int, int], int] = {}
    verse_text_map: dict[tuple[int, int], str] = {}

    if verse_refs:
        # Query all relevant verses at once to get page numbers and text
        result = await session.execute(
            select(
                QuranVerse.sura_no,
                QuranVerse.aya_no,
                QuranVerse.page_no,
                QuranVerse.text_uthmani
            ).where(
                QuranVerse.sura_no.in_([r[0] for r in verse_refs])
            )
        )
        for row in result:
            page_map[(row.sura_no, row.aya_no)] = row.page_no
            if include_verse_text:
                # Store a snippet (first 80 chars) of the verse text
                text = row.text_uthmani or ""
                verse_text_map[(row.sura_no, row.aya_no)] = text[:100] + ("..." if len(text) > 100 else "")

    def get_context_ar(o) -> Optional[str]:
        """Get Arabic context: use stored context or verse text snippet."""
        if o.context_ar:
            return o.context_ar
        if include_verse_text and o.sura_no and o.ayah_start:
            return verse_text_map.get((o.sura_no, o.ayah_start))
        return None

    return OccurrenceListResponse(
        occurrences=[
            OccurrenceResponse(
                id=o.id,
                concept_id=o.concept_id,
                ref_type=o.ref_type,
                ref_id=o.ref_id,
                sura_no=o.sura_no,
                ayah_start=o.ayah_start,
                ayah_end=o.ayah_end,
                page_no=page_map.get((o.sura_no, o.ayah_start)) if o.sura_no and o.ayah_start else None,
                verse_reference=o.verse_reference,
                weight=o.weight,
                context_ar=get_context_ar(o),
                context_en=o.context_en,
                has_evidence=o.has_evidence,
                is_verified=o.is_verified,
            )
            for o in occurrences
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{concept_id}/associations", response_model=List[AssociationResponse])
async def get_concept_associations(
    concept_id: str,
    relation_type: Optional[str] = Query(None, description="Filter by relation type"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get associations for a concept (related concepts).

    Relation types: cause_effect, similarity, contrast, elaboration, summarization,
                   attribute_of, sunnah_pattern, part_of, related
    """
    service = ConceptGraphService(session)
    associations = await service.get_concept_associations(
        concept_id=concept_id,
        relation_type=relation_type,
        limit=limit,
    )

    return [
        AssociationResponse(
            id=a.id,
            concept_a_id=a.concept_a_id,
            concept_b_id=a.concept_b_id,
            other_concept_id=a.other_concept_id,
            other_concept_label_ar=a.other_concept_label_ar,
            other_concept_label_en=a.other_concept_label_en,
            other_concept_type=a.other_concept_type,
            relation_type=a.relation_type,
            relation_label_ar=a.relation_label_ar,
            relation_label_en=a.relation_label_en,
            is_directional=a.is_directional,
            strength=a.strength,
            explanation_ar=a.explanation_ar,
            explanation_en=a.explanation_en,
            has_sufficient_evidence=a.has_sufficient_evidence,
        )
        for a in associations
    ]


# =============================================================================
# MIRACLES LENS
# =============================================================================

class MiracleWithAssociationsResponse(BaseModel):
    """Miracle with its associated persons and stories."""
    id: str
    slug: str
    label_ar: str
    label_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    icon_hint: Optional[str] = None
    related_persons: List[ConceptSummaryResponse] = []
    related_stories: List[str] = []
    occurrence_count: int = 0


@router.get("/miracles/all", response_model=List[MiracleWithAssociationsResponse])
async def get_all_miracles(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all miracles with their associated persons and stories.

    Special lens for exploring Quranic miracles/signs (آيات).
    Falls back to MiraclesService if database table doesn't exist.
    """
    try:
        from app.models.concept import Concept, Occurrence, Association
        from sqlalchemy import select, func

        # Get all miracle concepts
        result = await session.execute(
            select(Concept)
            .where(Concept.concept_type == "miracle")
            .order_by(Concept.display_order, Concept.label_en)
        )
        miracles = result.scalars().all()

        # If no miracles in database, use MiraclesService fallback
        if not miracles:
            return _get_miracles_from_service()

        response = []
        for miracle in miracles:
            # Get occurrence count
            occ_count_result = await session.execute(
                select(func.count(Occurrence.id))
                .where(Occurrence.concept_id == miracle.id)
            )
            occ_count = occ_count_result.scalar() or 0

            # Get story refs from occurrences
            story_refs_result = await session.execute(
                select(Occurrence.ref_id)
                .where(
                    Occurrence.concept_id == miracle.id,
                    Occurrence.ref_type == "story"
                )
                .distinct()
            )
            story_refs = [row[0] for row in story_refs_result.all() if row[0]]

            # Get related persons via associations (performed_by relation)
            assoc_result = await session.execute(
                select(Association)
                .where(
                    ((Association.concept_a_id == miracle.id) | (Association.concept_b_id == miracle.id)),
                    Association.relation_type.in_(["performed_by", "revealed_to", "cause_effect"])
                )
            )
            associations = assoc_result.scalars().all()

            related_persons = []
            for assoc in associations:
                # Get the other concept
                other_id = assoc.concept_b_id if assoc.concept_a_id == miracle.id else assoc.concept_a_id
                person_result = await session.execute(
                    select(Concept).where(Concept.id == other_id, Concept.concept_type == "person")
                )
                person = person_result.scalar_one_or_none()
                if person:
                    related_persons.append(ConceptSummaryResponse(
                        id=person.id,
                        slug=person.slug,
                        label_ar=person.label_ar,
                        label_en=person.label_en,
                        type=person.concept_type,
                        icon_hint=person.icon_hint,
                        is_curated=person.is_curated,
                        occurrence_count=0,
                    ))

            response.append(MiracleWithAssociationsResponse(
                id=miracle.id,
                slug=miracle.slug,
                label_ar=miracle.label_ar,
                label_en=miracle.label_en,
                description_ar=miracle.description_ar,
                description_en=miracle.description_en,
                icon_hint=miracle.icon_hint,
                related_persons=related_persons,
                related_stories=story_refs,
                occurrence_count=occ_count,
            ))

        return response

    except Exception as e:
        # Fallback to MiraclesService if database query fails (e.g., table doesn't exist)
        import logging
        logging.warning(f"Database query failed for miracles, using MiraclesService fallback: {e}")
        return _get_miracles_from_service()


def _get_miracles_from_service() -> List[MiracleWithAssociationsResponse]:
    """
    Get miracles from MiraclesService and convert to frontend-expected format.
    This provides comprehensive miracle data with tafsir from four Sunni madhabs.
    """
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_all_miracles(limit=100)
    response = []

    for miracle_data in result.get("miracles", []):
        # Build related persons from prophet info
        related_persons = []
        if miracle_data.get("prophet_id"):
            related_persons.append(ConceptSummaryResponse(
                id=miracle_data["prophet_id"],
                slug=miracle_data["prophet_id"],
                label_ar=miracle_data.get("prophet_name_ar", ""),
                label_en=miracle_data.get("prophet_name_en", ""),
                type="person",
                icon_hint="prophet",
                is_curated=True,
                occurrence_count=len(miracle_data.get("verses", [])),
            ))

        # Build related stories from miracle themes/related miracles
        related_stories = miracle_data.get("related_miracles", [])

        # Count verse occurrences
        occurrence_count = len(miracle_data.get("verses", []))

        response.append(MiracleWithAssociationsResponse(
            id=miracle_data["id"],
            slug=miracle_data["id"],
            label_ar=miracle_data["name_ar"],
            label_en=miracle_data["name_en"],
            description_ar=miracle_data.get("description_ar"),
            description_en=miracle_data.get("description_en"),
            icon_hint=miracle_data.get("miracle_type", "miracle"),
            related_persons=related_persons,
            related_stories=related_stories,
            occurrence_count=occurrence_count,
        ))

    return response


# =============================================================================
# MIRACLE DETAIL SCHEMAS (Extended with Tafsir)
# =============================================================================

class VerseReferenceResponse(BaseModel):
    """Quranic verse reference for a miracle."""
    surah_number: int
    surah_name_ar: str
    surah_name_en: str
    ayah_number: int
    ayah_range: Optional[str] = None
    text_ar: str
    text_en: str
    relevance: str


class TafsirReferenceResponse(BaseModel):
    """Tafsir reference from classical scholars."""
    scholar_name_ar: str
    scholar_name_en: str
    madhab: str  # hanafi, maliki, shafii, hanbali
    book_name_ar: str
    book_name_en: str
    explanation_ar: str
    explanation_en: str
    volume: Optional[str] = None
    page: Optional[str] = None


class MiracleDetailResponse(BaseModel):
    """Full miracle detail with tafsir from four madhabs."""
    id: str
    slug: str
    name_ar: str
    name_en: str
    category: str
    miracle_type: str
    prophet_id: Optional[str] = None
    prophet_name_ar: Optional[str] = None
    prophet_name_en: Optional[str] = None
    description_ar: str
    description_en: str
    significance_ar: str
    significance_en: str
    lessons_ar: List[str]
    lessons_en: List[str]
    verses: List[VerseReferenceResponse]
    tafsir_references: List[TafsirReferenceResponse]
    themes: List[str]
    themes_ar: List[str]
    related_miracles: List[str]
    historical_context_ar: str
    historical_context_en: str
    verification_status: str


@router.get("/miracles/{miracle_id}", response_model=MiracleDetailResponse)
async def get_miracle_detail(miracle_id: str):
    """
    Get detailed miracle information including tafsir from four Sunni madhabs.

    Includes:
    - Full description in Arabic and English
    - Relevant Quranic verses
    - Tafsir from Hanafi, Maliki, Shafi'i, and Hanbali scholars
    - Lessons and significance
    - Related miracles
    """
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_miracle(miracle_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    miracle = result["miracle"]

    # Convert verses
    verses = [
        VerseReferenceResponse(
            surah_number=v["surah_number"],
            surah_name_ar=v["surah_name_ar"],
            surah_name_en=v["surah_name_en"],
            ayah_number=v["ayah_number"],
            ayah_range=v.get("ayah_range"),
            text_ar=v["text_ar"],
            text_en=v["text_en"],
            relevance=v["relevance"]
        )
        for v in miracle.get("verses", [])
    ]

    # Convert tafsir references
    tafsir_refs = [
        TafsirReferenceResponse(
            scholar_name_ar=t["scholar_name_ar"],
            scholar_name_en=t["scholar_name_en"],
            madhab=t["madhab"],
            book_name_ar=t["book_name_ar"],
            book_name_en=t["book_name_en"],
            explanation_ar=t["explanation_ar"],
            explanation_en=t["explanation_en"],
            volume=t.get("volume"),
            page=t.get("page")
        )
        for t in miracle.get("tafsir_references", [])
    ]

    return MiracleDetailResponse(
        id=miracle["id"],
        slug=miracle["id"],
        name_ar=miracle["name_ar"],
        name_en=miracle["name_en"],
        category=miracle["category"],
        miracle_type=miracle["miracle_type"],
        prophet_id=miracle.get("prophet_id"),
        prophet_name_ar=miracle.get("prophet_name_ar"),
        prophet_name_en=miracle.get("prophet_name_en"),
        description_ar=miracle["description_ar"],
        description_en=miracle["description_en"],
        significance_ar=miracle["significance_ar"],
        significance_en=miracle["significance_en"],
        lessons_ar=miracle.get("lessons_ar", []),
        lessons_en=miracle.get("lessons_en", []),
        verses=verses,
        tafsir_references=tafsir_refs,
        themes=miracle.get("themes", []),
        themes_ar=miracle.get("themes_ar", []),
        related_miracles=miracle.get("related_miracles", []),
        historical_context_ar=miracle.get("historical_context_ar", ""),
        historical_context_en=miracle.get("historical_context_en", ""),
        verification_status=miracle.get("verification_status", "verified")
    )


class MiracleCategoryResponse(BaseModel):
    """Miracle category with count."""
    id: str
    name_ar: str
    name_en: str
    miracle_count: int


@router.get("/miracles/categories/all", response_model=List[MiracleCategoryResponse])
async def get_miracle_categories():
    """Get all miracle categories with counts."""
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_miracle_categories()
    return [
        MiracleCategoryResponse(
            id=cat["id"],
            name_ar=cat["name_ar"],
            name_en=cat["name_en"],
            miracle_count=cat["miracle_count"]
        )
        for cat in result.get("categories", [])
    ]


class MiracleThemeResponse(BaseModel):
    """Miracle theme with count."""
    id: str
    name_ar: str
    name_en: str
    miracle_count: int


@router.get("/miracles/themes/all", response_model=List[MiracleThemeResponse])
async def get_miracle_themes():
    """Get all themes associated with miracles."""
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_miracle_themes()
    return [
        MiracleThemeResponse(
            id=theme["id"],
            name_ar=theme["name_ar"],
            name_en=theme["name_en"],
            miracle_count=theme["miracle_count"]
        )
        for theme in result.get("themes", [])
    ]


class TafsirSourceResponse(BaseModel):
    """Tafsir source information."""
    scholar_name_ar: str
    scholar_name_en: str
    madhab: str
    book_name_ar: str
    book_name_en: str
    miracle_count: int


@router.get("/miracles/tafsir-sources", response_model=List[TafsirSourceResponse])
async def get_miracle_tafsir_sources():
    """
    Get all tafsir sources used in miracle explanations.
    Includes scholars from four Sunni madhabs.
    """
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_tafsir_sources()
    return [
        TafsirSourceResponse(
            scholar_name_ar=src["scholar_name_ar"],
            scholar_name_en=src["scholar_name_en"],
            madhab=src["madhab"],
            book_name_ar=src["book_name_ar"],
            book_name_en=src["book_name_en"],
            miracle_count=src["miracle_count"]
        )
        for src in result.get("sources", [])
    ]


class ProphetMiraclesResponse(BaseModel):
    """Prophet with their miracles."""
    prophet_id: str
    prophet_name_ar: str
    prophet_name_en: str
    miracles: List[MiracleWithAssociationsResponse]
    miracle_count: int


@router.get("/miracles/by-prophet/{prophet_id}", response_model=ProphetMiraclesResponse)
async def get_miracles_by_prophet(prophet_id: str):
    """Get all miracles for a specific prophet."""
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_miracles_by_prophet(prophet_id)

    miracles = []
    for m in result.get("miracles", []):
        related_persons = []
        if m.get("prophet_id"):
            related_persons.append(ConceptSummaryResponse(
                id=m["prophet_id"],
                slug=m["prophet_id"],
                label_ar=m.get("prophet_name_ar", ""),
                label_en=m.get("prophet_name_en", ""),
                type="person",
                icon_hint="prophet",
                is_curated=True,
                occurrence_count=len(m.get("verses", [])),
            ))

        miracles.append(MiracleWithAssociationsResponse(
            id=m["id"],
            slug=m["id"],
            label_ar=m["name_ar"],
            label_en=m["name_en"],
            description_ar=m.get("description_ar"),
            description_en=m.get("description_en"),
            icon_hint=m.get("miracle_type", "miracle"),
            related_persons=related_persons,
            related_stories=m.get("related_miracles", []),
            occurrence_count=len(m.get("verses", [])),
        ))

    return ProphetMiraclesResponse(
        prophet_id=result.get("prophet_id", prophet_id),
        prophet_name_ar=result.get("prophet_name_ar", ""),
        prophet_name_en=result.get("prophet_name_en", ""),
        miracles=miracles,
        miracle_count=result.get("miracle_count", 0)
    )


class MiracleGraphResponse(BaseModel):
    """Graph visualization data for miracles."""
    nodes: List[dict]
    edges: List[dict]
    total_nodes: int
    total_edges: int
    legend: List[dict]


@router.get("/miracles/graph/visualization", response_model=MiracleGraphResponse)
async def get_miracles_graph(
    center_miracle_id: Optional[str] = Query(None, description="Center the graph on this miracle"),
    depth: int = Query(2, description="Graph exploration depth")
):
    """
    Get graph visualization data for miracles.
    Shows connections between miracles, prophets, and themes.
    """
    from app.services.miracles_service import miracles_service

    result = miracles_service.get_miracle_graph(
        center_miracle_id=center_miracle_id,
        depth=depth
    )

    return MiracleGraphResponse(
        nodes=result.get("nodes", []),
        edges=result.get("edges", []),
        total_nodes=result.get("total_nodes", 0),
        total_edges=result.get("total_edges", 0),
        legend=result.get("legend", [])
    )


# =============================================================================
# TAFSIR EVIDENCE FOR OCCURRENCES
# =============================================================================

class TafsirEvidenceItem(BaseModel):
    """Single tafsir evidence item."""
    chunk_id: str
    source_id: str
    source_name_ar: str
    source_name_en: str
    author_ar: str
    author_en: str
    madhab: Optional[str] = None
    verse_reference: str
    content: str
    methodology: Optional[str] = None


class OccurrenceEvidenceResponse(BaseModel):
    """Tafsir evidence for an occurrence."""
    occurrence_id: int
    concept_id: str
    concept_label_ar: str
    concept_label_en: str
    verse_reference: str
    evidence: List[TafsirEvidenceItem]
    evidence_count: int
    madhabs_covered: List[str]


@router.get("/{concept_id}/occurrences/{occurrence_id}/evidence", response_model=OccurrenceEvidenceResponse)
async def get_occurrence_evidence(
    request: Request,
    concept_id: str,
    occurrence_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get tafsir evidence for a specific occurrence.

    STRICT: Only returns evidence from the four Sunni madhabs:
    - Hanafi: Al-Nasafi (Madarik al-Tanzil)
    - Maliki: Al-Qurtubi (Al-Jami' li-Ahkam al-Quran)
    - Shafi'i: Ibn Kathir (Tafsir al-Quran al-Azim)
    - Hanbali: Al-Shinqiti (Adwa' al-Bayan)

    Other sources (classical, combined, simplified) are EXCLUDED.
    """
    from sqlalchemy import text
    from app.services.madhab_validator import (
        madhab_validator,
        get_approved_source_ids_list,
        is_valid_madhab,
        get_scholar_info
    )

    # Get approved source IDs for filtering
    approved_sources = get_approved_source_ids_list()

    # Get the occurrence
    occ_result = await session.execute(
        text("""
            SELECT o.id, o.concept_id, o.sura_no, o.ayah_start, o.evidence_chunk_ids,
                   c.label_ar, c.label_en
            FROM occurrences o
            JOIN concepts c ON o.concept_id = c.id
            WHERE o.id = :occ_id AND o.concept_id = :concept_id
        """),
        {"occ_id": occurrence_id, "concept_id": concept_id}
    )
    occ = occ_result.fetchone()

    if not occ:
        raise APIError(
            code=ErrorCode.OCCURRENCE_NOT_FOUND,
            message_en=f"Occurrence {occurrence_id} not found for concept {concept_id}",
            message_ar=f"الموضع {occurrence_id} غير موجود للمفهوم {concept_id}",
            request_id=get_request_id(request),
            status_code=404
        )

    occ_id, cid, sura_no, ayah_start, chunk_ids, label_ar, label_en = occ
    verse_ref = f"{sura_no}:{ayah_start}" if sura_no else ""

    evidence_items = []
    madhabs_seen = set()

    if chunk_ids:
        # Get tafsir chunks ONLY from approved 4 madhab sources
        chunks_result = await session.execute(
            text("""
                SELECT tc.id::text, tc.source_id,
                       COALESCE(tc.content_ar, tc.content_en, '') as content,
                       ts.name_ar, ts.name_en, ts.author_ar, ts.author_en,
                       ts.madhab, ts.methodology
                FROM tafseer_chunks tc
                JOIN tafseer_sources ts ON tc.source_id = ts.id
                WHERE tc.id::text = ANY(:ids)
                  AND ts.id = ANY(:approved_sources)
                ORDER BY ts.madhab NULLS LAST, ts.name_en
            """),
            {"ids": chunk_ids, "approved_sources": approved_sources}
        )

        for row in chunks_result:
            chunk_id, source_id, content, name_ar, name_en, author_ar, author_en, madhab, methodology = row

            # Double-check madhab is valid (defense in depth)
            if not is_valid_madhab(madhab):
                # Get validated madhab from source mapping
                scholar_info = get_scholar_info(source_id)
                if scholar_info:
                    madhab = scholar_info.get("madhab")
                else:
                    continue  # Skip if we can't validate

            if madhab:
                madhabs_seen.add(madhab.lower())

            evidence_items.append(TafsirEvidenceItem(
                chunk_id=chunk_id,
                source_id=source_id,
                source_name_ar=name_ar or "",
                source_name_en=name_en or "",
                author_ar=author_ar or "",
                author_en=author_en or "",
                madhab=madhab,
                verse_reference=verse_ref,
                content=content or "",
                methodology=methodology
            ))

    return OccurrenceEvidenceResponse(
        occurrence_id=occ_id,
        concept_id=cid,
        concept_label_ar=label_ar,
        concept_label_en=label_en,
        verse_reference=verse_ref,
        evidence=evidence_items,
        evidence_count=len(evidence_items),
        madhabs_covered=sorted(madhabs_seen)
    )


# =============================================================================
# VERIFICATION WORKFLOW - Admin-Gated Content Changes
# =============================================================================

class VerificationTaskCreate(BaseModel):
    """Request to create a verification task."""
    entity_type: str = Field(..., description="Type: concept, miracle, tafsir, occurrence")
    entity_id: str
    proposed_change: dict = Field(..., description="JSON object with proposed changes")
    evidence_refs: dict = Field(default={}, description="Evidence references (verses, sources)")
    priority: int = Field(default=0, ge=0, le=10)


class VerificationTaskResponse(BaseModel):
    """Verification task details."""
    id: int
    entity_type: str
    entity_id: str
    proposed_change: dict
    evidence_refs: dict
    status: str
    priority: int
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class VerificationDecisionCreate(BaseModel):
    """Admin decision on a verification task."""
    decision: str = Field(..., description="approved or rejected")
    notes: Optional[str] = None


class VerificationDecisionResponse(BaseModel):
    """Decision record."""
    id: int
    task_id: int
    admin_id: str
    decision: str
    notes: Optional[str] = None
    decided_at: str


@router.post("/verification/tasks", response_model=VerificationTaskResponse, status_code=201)
async def create_verification_task(
    task: VerificationTaskCreate,
    user_id: str = Query("anonymous", description="User submitting the task"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Submit a verification task for admin review.

    All content changes (concept definitions, miracle descriptions, tafsir summaries)
    must go through this workflow. Tasks remain 'pending' until an admin approves.

    Entity types: concept, miracle, tafsir, occurrence
    """
    from sqlalchemy import text
    import json

    result = await session.execute(
        text("""
            INSERT INTO verification_tasks
                (entity_type, entity_id, proposed_change, evidence_refs, status, priority, created_by, created_at, updated_at)
            VALUES
                (:entity_type, :entity_id, CAST(:proposed_change AS jsonb), CAST(:evidence_refs AS jsonb), 'pending', :priority, :created_by, NOW(), NOW())
            RETURNING id, entity_type, entity_id, proposed_change, evidence_refs, status, priority, created_by, created_at, updated_at
        """),
        {
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
            "proposed_change": json.dumps(task.proposed_change),
            "evidence_refs": json.dumps(task.evidence_refs),
            "priority": task.priority,
            "created_by": user_id
        }
    )
    await session.commit()
    row = result.fetchone()

    return VerificationTaskResponse(
        id=row[0],
        entity_type=row[1],
        entity_id=row[2],
        proposed_change=row[3],
        evidence_refs=row[4],
        status=row[5],
        priority=row[6],
        created_by=row[7],
        created_at=str(row[8]),
        updated_at=str(row[9])
    )


@router.get("/verification/tasks", response_model=List[VerificationTaskResponse])
async def list_verification_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: "AdminUser" = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List verification tasks (Admin only).

    Requires Bearer token in Authorization header.
    """

    from sqlalchemy import text

    query = """
        SELECT id, entity_type, entity_id, proposed_change, evidence_refs,
               status, priority, created_by, created_at, updated_at
        FROM verification_tasks
        WHERE 1=1
    """
    params = {"limit": limit, "offset": offset}

    if status:
        query += " AND status = :status"
        params["status"] = status
    if entity_type:
        query += " AND entity_type = :entity_type"
        params["entity_type"] = entity_type

    query += " ORDER BY priority DESC, created_at DESC LIMIT :limit OFFSET :offset"

    result = await session.execute(text(query), params)
    rows = result.fetchall()

    return [
        VerificationTaskResponse(
            id=row[0],
            entity_type=row[1],
            entity_id=row[2],
            proposed_change=row[3],
            evidence_refs=row[4],
            status=row[5],
            priority=row[6],
            created_by=row[7],
            created_at=str(row[8]),
            updated_at=str(row[9])
        )
        for row in rows
    ]


@router.post("/verification/tasks/{task_id}/decide", response_model=VerificationDecisionResponse)
async def decide_verification_task(
    request: Request,
    task_id: int,
    decision: VerificationDecisionCreate,
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Approve or reject a verification task (Admin only).

    Requires Bearer token in Authorization header.

    On approval:
    - Task status changes to 'approved'
    - Decision is logged with audit trail
    - (In a full implementation, the change would be applied to the entity)
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

    # Check task exists and is pending
    task_result = await session.execute(
        text("SELECT id, status FROM verification_tasks WHERE id = :task_id"),
        {"task_id": task_id}
    )
    task = task_result.fetchone()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task[1] != "pending":
        raise HTTPException(status_code=400, detail=f"Task already {task[1]}")

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

    return VerificationDecisionResponse(
        id=row[0],
        task_id=row[1],
        admin_id=row[2],
        decision=row[3],
        notes=row[4],
        decided_at=str(row[5])
    )


class VerificationStatsResponse(BaseModel):
    """Verification workflow statistics."""
    pending_count: int
    approved_count: int
    rejected_count: int
    by_entity_type: dict


@router.get("/verification/stats", response_model=VerificationStatsResponse)
async def get_verification_stats(
    admin: AdminUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get verification workflow statistics (Admin only).

    Requires Bearer token in Authorization header.
    """

    from sqlalchemy import text

    # Get counts by status
    status_result = await session.execute(
        text("SELECT status, COUNT(*) FROM verification_tasks GROUP BY status")
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}

    # Get counts by entity type
    type_result = await session.execute(
        text("SELECT entity_type, COUNT(*) FROM verification_tasks GROUP BY entity_type")
    )
    type_counts = {row[0]: row[1] for row in type_result.fetchall()}

    return VerificationStatsResponse(
        pending_count=status_counts.get("pending", 0),
        approved_count=status_counts.get("approved", 0),
        rejected_count=status_counts.get("rejected", 0),
        by_entity_type=type_counts
    )
