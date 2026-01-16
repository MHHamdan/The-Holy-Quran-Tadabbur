"""
Story Atlas API Routes - Quran-wide story indexing and visualization.

Endpoints:
- GET /story-atlas: List all clusters with filtering
- GET /story-atlas/facets: Get filter facets (persons, places, eras)
- GET /story-atlas/{cluster_id}: Get cluster detail with events
- GET /story-atlas/{cluster_id}/graph: Get cluster graph data
- GET /story-atlas/{cluster_id}/timeline: Get linear timeline
- GET /story-atlas/{cluster_id}/related: Get related clusters
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.services.story_atlas import StoryAtlasService, get_role_style
from app.services.similarity import SimilarityService

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class PlaceInfo(BaseModel):
    """Place information with basis."""
    name: str
    name_ar: Optional[str] = None
    basis: str = "unknown"  # explicit, inferred, unknown


class ClusterSummaryResponse(BaseModel):
    """Summary of a story cluster."""
    id: str
    title_ar: str
    title_en: str
    short_title_en: Optional[str] = None
    category: str
    era: Optional[str] = None
    main_persons: List[str] = []
    places: List[dict] = []
    tags: List[str] = []
    event_count: int = 0
    primary_sura: Optional[int] = None
    summary_en: Optional[str] = None


class ClusterListResponse(BaseModel):
    """Response for cluster listing."""
    clusters: List[ClusterSummaryResponse]
    total: int
    offset: int
    limit: int


class FacetsResponse(BaseModel):
    """Available filter facets."""
    persons: List[str]
    places: List[dict]
    eras: List[str]
    categories: List[str]
    tags: List[str]


class EvidenceItem(BaseModel):
    """Evidence citation."""
    source_id: str
    reference: Optional[str] = None
    snippet: Optional[str] = None


class EventResponse(BaseModel):
    """Story event response."""
    id: str
    title_ar: str
    title_en: str
    narrative_role: str
    chronological_index: int
    sura_no: int
    aya_start: int
    aya_end: int
    verse_reference: str
    summary_ar: str
    summary_en: str
    semantic_tags: List[str] = []
    is_entry_point: bool = False
    evidence: List[dict] = []


class ClusterDetailResponse(BaseModel):
    """Full cluster detail with events."""
    id: str
    title_ar: str
    title_en: str
    short_title_ar: Optional[str] = None
    short_title_en: Optional[str] = None
    category: str
    main_persons: List[str] = []
    groups: List[str] = []
    places: List[dict] = []
    era: Optional[str] = None
    era_basis: str = "unknown"
    time_description_en: Optional[str] = None
    ayah_spans: List[dict] = []
    primary_sura: Optional[int] = None
    suras_mentioned: Optional[List[int]] = None
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None
    lessons_ar: Optional[List[str]] = None
    lessons_en: Optional[List[str]] = None
    tags: List[str] = []
    total_verses: int = 0
    event_count: int = 0
    events: List[EventResponse] = []


class GraphNodeResponse(BaseModel):
    """Node in the story graph."""
    id: str
    type: str
    label: str
    data: dict = Field(default_factory=dict)
    position: Optional[dict] = None


class GraphEdgeResponse(BaseModel):
    """Edge in the story graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    is_chronological: bool = False
    strength: float = 1.0
    data: dict = Field(default_factory=dict)


class GraphResponse(BaseModel):
    """Story graph response."""
    cluster_id: str
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "timeline"


class TimelineStepResponse(BaseModel):
    """Step in the timeline."""
    id: str
    index: int
    title: str
    verse_reference: str
    narrative_role: str
    summary: Optional[str] = None
    semantic_tags: List[str] = []
    is_entry_point: bool = False
    evidence: List[dict] = []
    role_style: dict = Field(default_factory=dict)


class RelatedClusterResponse(BaseModel):
    """Related cluster information."""
    cluster_id: str
    title_en: str
    title_ar: str
    connection_type: str
    strength: float = 0.5
    label_en: Optional[str] = None
    shared_persons: List[str] = []
    shared_places: List[str] = []
    shared_themes: List[str] = []


# =============================================================================
# ROUTES
# =============================================================================

@router.get("", response_model=ClusterListResponse)
async def list_clusters(
    category: Optional[str] = Query(None, description="Filter by category"),
    era: Optional[str] = Query(None, description="Filter by era"),
    person: Optional[str] = Query(None, description="Filter by person"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in titles and summaries"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List all story clusters with optional filtering.

    Filters:
    - category: prophet, named_char, nation, parable, historical, unseen
    - era: primordial, ancient, egypt, israelite, pre_islamic, unknown
    - person: Filter by main person (e.g., "Musa", "Ibrahim")
    - tag: Filter by tag (e.g., "patience", "miracles")
    - search: Full-text search in titles and summaries
    """
    service = StoryAtlasService(session)
    clusters, total = await service.list_clusters(
        category=category,
        era=era,
        person=person,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
    )

    return ClusterListResponse(
        clusters=[
            ClusterSummaryResponse(
                id=c.id,
                title_ar=c.title_ar,
                title_en=c.title_en,
                short_title_en=c.short_title_en,
                category=c.category,
                era=c.era,
                main_persons=c.main_persons,
                places=c.places,
                tags=c.tags,
                event_count=c.event_count,
                primary_sura=c.primary_sura,
                summary_en=c.summary_en,
            )
            for c in clusters
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/facets", response_model=FacetsResponse)
async def get_facets(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all available facets for filtering.

    Returns unique values for:
    - persons: All main persons across clusters
    - places: All places with basis (explicit/inferred)
    - eras: All time eras
    - categories: All story categories
    - tags: All tags
    """
    service = StoryAtlasService(session)
    facets = await service.get_facets()

    return FacetsResponse(
        persons=facets.persons,
        places=facets.places,
        eras=facets.eras,
        categories=facets.categories,
        tags=facets.tags,
    )


@router.get("/categories")
async def get_categories():
    """Get story categories with descriptions."""
    return {
        "categories": [
            {"id": "prophet", "name_en": "Prophet Stories", "name_ar": "قصص الأنبياء"},
            {"id": "named_char", "name_en": "Named Characters", "name_ar": "شخصيات مسماة"},
            {"id": "nation", "name_en": "Nations/Peoples", "name_ar": "الأمم والشعوب"},
            {"id": "parable", "name_en": "Parables", "name_ar": "الأمثال"},
            {"id": "historical", "name_en": "Historical Events", "name_ar": "أحداث تاريخية"},
            {"id": "unseen", "name_en": "The Unseen", "name_ar": "الغيب"},
        ]
    }


@router.get("/eras")
async def get_eras():
    """Get era buckets with descriptions."""
    return {
        "eras": [
            {"id": "primordial", "name_en": "Primordial (Adam)", "name_ar": "البدء (آدم)"},
            {"id": "ancient", "name_en": "Ancient Prophets", "name_ar": "الأنبياء الأوائل"},
            {"id": "egypt", "name_en": "Egypt Era", "name_ar": "عصر مصر"},
            {"id": "israelite", "name_en": "Israelite Era", "name_ar": "عصر بني إسرائيل"},
            {"id": "pre_islamic", "name_en": "Pre-Islamic", "name_ar": "ما قبل الإسلام"},
            {"id": "unknown", "name_en": "Unknown", "name_ar": "غير محدد"},
        ]
    }


@router.get("/roles")
async def get_narrative_roles():
    """Get narrative roles with icons and colors."""
    from app.services.story_atlas import ROLE_STYLES

    return {
        "roles": [
            {
                "id": role_id,
                "name_en": role_id.replace("_", " ").title(),
                "icon": style["icon"],
                "color": style["color"],
            }
            for role_id, style in ROLE_STYLES.items()
        ]
    }


@router.get("/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster(
    cluster_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get full cluster details with all events.

    Returns cluster metadata and ordered list of events with evidence.
    """
    service = StoryAtlasService(session)
    cluster = await service.get_cluster(cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    return ClusterDetailResponse(**cluster)


@router.get("/{cluster_id}/graph", response_model=GraphResponse)
async def get_cluster_graph(
    cluster_id: str,
    language: str = Query("en", description="Language for labels (ar or en)"),
    mode: str = Query("timeline", description="Layout mode: timeline or concept"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get cluster as a graph for visualization.

    Layout modes:
    - timeline: Vertical top-to-bottom chronological (default)
    - concept: Hub-and-spoke thematic layout

    Returns nodes and edges for graph rendering.
    """
    service = StoryAtlasService(session)
    graph = await service.build_cluster_graph(
        cluster_id=cluster_id,
        language=language,
        layout_mode=mode,
    )

    if not graph:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    return GraphResponse(
        cluster_id=graph.cluster_id,
        nodes=[
            GraphNodeResponse(
                id=n.id,
                type=n.type,
                label=n.label,
                data=n.data,
                position={"x": n.x, "y": n.y} if n.x is not None else None,
            )
            for n in graph.nodes
        ],
        edges=[
            GraphEdgeResponse(
                source=e.source,
                target=e.target,
                type=e.type,
                label=e.label,
                is_chronological=e.is_chronological,
                strength=e.strength,
                data=e.data,
            )
            for e in graph.edges
        ],
        entry_node_id=graph.entry_node_id,
        is_valid_dag=graph.is_valid_dag,
        layout_mode=graph.layout_mode,
    )


@router.get("/{cluster_id}/timeline", response_model=List[TimelineStepResponse])
async def get_cluster_timeline(
    cluster_id: str,
    language: str = Query("en", description="Language for content (ar or en)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get cluster as a linear timeline for step-by-step learning.

    Returns ordered list of events with:
    - Step number and title
    - Verse reference
    - Narrative role with icon/color
    - Summary and evidence
    """
    service = StoryAtlasService(session)
    timeline = await service.get_timeline(cluster_id, language)

    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    return [
        TimelineStepResponse(
            id=step["id"],
            index=step["index"],
            title=step["title"],
            verse_reference=step["verse_reference"],
            narrative_role=step["narrative_role"],
            summary=step["summary"],
            semantic_tags=step["semantic_tags"],
            is_entry_point=step["is_entry_point"],
            evidence=step["evidence"],
            role_style=get_role_style(step["narrative_role"]),
        )
        for step in timeline
    ]


@router.get("/{cluster_id}/related", response_model=List[RelatedClusterResponse])
async def get_related_clusters(
    cluster_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get clusters thematically related to this one.

    Returns clusters sharing:
    - Common persons
    - Common places
    - Common themes
    """
    service = StoryAtlasService(session)

    # First check cluster exists
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    related = await service.get_related_clusters(cluster_id)

    return [RelatedClusterResponse(**r) for r in related]


class SimilarClusterResponse(BaseModel):
    """Similar cluster based on concept overlap."""
    id: str
    title_ar: str
    title_en: str
    similarity_score: float
    shared_concepts: List[str] = []
    shared_themes: List[str] = []
    shared_figures: List[str] = []


@router.get("/{cluster_id}/similar", response_model=List[SimilarClusterResponse])
async def get_similar_clusters(
    cluster_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max similar clusters to return"),
    min_score: float = Query(0.1, ge=0, le=1, description="Minimum similarity score"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get clusters similar to the given cluster based on shared concepts.

    Uses Jaccard similarity on concept overlap.
    Different from /related which uses explicit connections.
    """
    similarity_service = SimilarityService(session)
    similar = await similarity_service.get_similar_clusters(
        cluster_id=cluster_id,
        limit=limit,
        min_score=min_score,
    )

    return [
        SimilarClusterResponse(
            id=s.id,
            title_ar=s.title_ar,
            title_en=s.title_en,
            similarity_score=s.similarity_score,
            shared_concepts=s.shared_concepts,
            shared_themes=s.shared_themes,
            shared_figures=s.shared_figures,
        )
        for s in similar
    ]
