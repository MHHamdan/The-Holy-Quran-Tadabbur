"""
Stories API routes for Quranic narratives and connections.

Enhanced API with:
- Story graph visualization with chronological/thematic modes
- Timeline endpoint for step-by-step learning
- Cross-story connections for thematic exploration
"""
import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_async_session
from app.models.story import Story, StorySegment, StoryConnection, CrossStoryConnection, Theme
from app.models.tafseer import TafseerChunk, TafseerSource
from app.services.story_graph import StoryGraphService
from app.services.similarity import SimilarityService

router = APIRouter()


# ---------------------------------------------------------------------------
# Derived verse coverage
#
# Story.total_verses is an unmaintained column that is 0 for every seeded
# story, so the figure is derived from the segments instead.  Segments of the
# same story routinely overlap (Badr covers 8:5-14 and again 8:9-12), so the
# count is the size of the union of (sura, aya) pairs rather than the sum of
# the range widths, which would double-count the overlap.
# ---------------------------------------------------------------------------


def _segment_verse_keys(
    sura_no: Optional[int], aya_start: Optional[int], aya_end: Optional[int]
) -> Set[Tuple[int, int]]:
    """Every (sura, aya) pair a single segment covers."""
    if sura_no is None or aya_start is None:
        return set()
    last = aya_start if aya_end is None else aya_end
    first, last = min(aya_start, last), max(aya_start, last)
    return {(sura_no, aya) for aya in range(first, last + 1)}


async def _verse_counts_by_story(
    session: AsyncSession, story_ids: Iterable[str]
) -> Dict[str, int]:
    """
    Distinct Quranic verses covered by each story, in one batched query.

    Returns an empty mapping for story ids that have no segments.
    """
    ids = list(story_ids)
    if not ids:
        return {}

    result = await session.execute(
        select(
            StorySegment.story_id,
            StorySegment.sura_no,
            StorySegment.aya_start,
            StorySegment.aya_end,
        ).where(StorySegment.story_id.in_(ids))
    )

    covered: Dict[str, Set[Tuple[int, int]]] = defaultdict(set)
    for story_id, sura_no, aya_start, aya_end in result.all():
        covered[story_id] |= _segment_verse_keys(sura_no, aya_start, aya_end)

    return {story_id: len(keys) for story_id, keys in covered.items()}


def _resolve_total_verses(stored: Optional[int], derived: Optional[int]) -> int:
    """Prefer the figure derived from segments; fall back to the stored column."""
    if derived:
        return derived
    return stored or 0


# ---------------------------------------------------------------------------
# Manifest-backed review flags for cross-story connections
#
# Some inter-story connections in data/manifests/stories.json cite verses that
# do not clearly support the stated link (e.g. a lineage or destruction claim).
# They carry "needs_review": true and are hidden from the public API until a
# scholar reviews them — even if an older seed already wrote them to the DB.
# ---------------------------------------------------------------------------

_MANIFEST_CANDIDATES = (
    Path("/app/data/manifests/stories.json"),
    Path(__file__).resolve().parents[4] / "data" / "manifests" / "stories.json",
)

# Fallback when the manifest is not shipped with the API image.
_KNOWN_NEEDS_REVIEW: Tuple[Tuple[str, str, str, bool], ...] = (
    ("story_ibrahim", "story_musa", "thematic", False),           # conn_ibrahim_ismail_sacrifice
    ("story_musa", "story_sabbath_breakers", "thematic", False),  # conn_musa_sabbath
    ("story_luqman", "story_ibrahim", "thematic", True),          # conn_luqman_ibrahim
    ("story_nuh", "story_ibrahim", "thematic", True),             # conn_nuh_ibrahim_destruction
    ("story_isa", "story_ibrahim", "thematic", False),            # conn_isa_muhammad_lineage
)


@lru_cache(maxsize=1)
def _manifest_connection_index() -> Tuple[FrozenSet[Tuple[str, str, str]], Dict[Tuple[str, str, str], Tuple[str, ...]]]:
    """(hidden (src, tgt, type) keys, (src, tgt, type) -> verse refs "S:A-B")."""
    hidden: Set[Tuple[str, str, str]] = set()
    refs: Dict[Tuple[str, str, str], Tuple[str, ...]] = {}
    manifest = None
    for path in _MANIFEST_CANDIDATES:
        if path.exists():
            manifest = json.loads(path.read_text(encoding="utf-8"))
            break
    if manifest is None:
        for src, tgt, ctype, bidi in _KNOWN_NEEDS_REVIEW:
            hidden.add((src, tgt, ctype))
            if bidi:
                hidden.add((tgt, src, ctype))
        return frozenset(hidden), refs
    for conn in manifest.get("inter_story_connections", []):
        key = (conn["source_story_id"], conn["target_story_id"], conn.get("connection_type", "thematic"))
        keys = [key, (key[1], key[0], key[2])] if conn.get("bidirectional") else [key]
        verse_refs: List[str] = []
        for ev in conn.get("evidence_chunk_ids") or []:
            m = re.match(r"^[a-z_]+:(\d{1,3}:\d{1,3}(?:-\d{1,3})?)$", ev or "")
            if m and m.group(1) not in verse_refs:
                verse_refs.append(m.group(1))
        for k in keys:
            refs[k] = tuple(verse_refs)
            if conn.get("needs_review"):
                hidden.add(k)
    return frozenset(hidden), refs


async def _segment_evidence(
    session: AsyncSession, segments: Iterable[StorySegment]
) -> Dict[str, List["SegmentEvidence"]]:
    """segment id -> resolved tafsir evidence (enabled sources only), one batched query."""
    by_segment = {s.id: list(s.evidence_chunk_ids or []) for s in segments}
    all_ids = sorted({cid for ids in by_segment.values() for cid in ids})
    if not all_ids:
        return {}
    rows = (
        await session.execute(
            select(
                TafseerChunk.chunk_id,
                TafseerChunk.source_id,
                TafseerChunk.sura_no,
                TafseerChunk.aya_start,
                TafseerChunk.aya_end,
                TafseerSource.name_ar,
                TafseerSource.name_en,
                TafseerSource.author_ar,
                TafseerSource.author_en,
            )
            .join(TafseerSource, TafseerSource.id == TafseerChunk.source_id)
            .where(TafseerChunk.chunk_id.in_(all_ids))
            .where(TafseerSource.is_enabled == 1)
        )
    ).all()
    info = {r.chunk_id: r for r in rows}
    out: Dict[str, List[SegmentEvidence]] = {}
    for seg_id, ids in by_segment.items():
        items = []
        for cid in ids:
            r = info.get(cid)
            if r is None:
                continue
            items.append(
                SegmentEvidence(
                    chunk_id=r.chunk_id,
                    source_id=r.source_id,
                    title=r.name_en,
                    title_ar=r.name_ar,
                    author=r.author_en,
                    author_ar=r.author_ar,
                    sura_no=r.sura_no,
                    aya_start=r.aya_start,
                    aya_end=r.aya_end,
                )
            )
        out[seg_id] = items
    return out


# Pydantic schemas
class SegmentEvidence(BaseModel):
    """A tafsir chunk cited as evidence for a segment (never the chunk text)."""
    chunk_id: str
    source_id: str
    title: Optional[str] = None
    title_ar: Optional[str] = None
    author: Optional[str] = None
    author_ar: Optional[str] = None
    sura_no: int
    aya_start: int
    aya_end: int


class SegmentResponse(BaseModel):
    """Story segment response."""
    id: str
    narrative_order: int
    chronological_index: Optional[int] = None
    narrative_role: Optional[str] = None
    segment_type: Optional[str] = None
    aspect: Optional[str] = None
    sura_no: int
    aya_start: int
    aya_end: int
    verse_reference: str
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None
    semantic_tags: Optional[List[str]] = None
    is_entry_point: bool = False
    evidence: List[SegmentEvidence] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ConnectionResponse(BaseModel):
    """Story connection response."""
    id: int
    source_segment_id: str
    target_segment_id: str
    edge_type: Optional[str] = None
    connection_type: Optional[str] = None
    strength: float
    is_chronological: bool = False
    explanation_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    justification_en: Optional[str] = None
    evidence_chunk_ids: List[str]
    shared_themes: Optional[List[str]] = None

    class Config:
        from_attributes = True


class TimelineStepResponse(BaseModel):
    """A step in the story timeline."""
    id: str
    index: int
    title: Optional[str]
    verse_reference: str
    narrative_role: Optional[str]
    summary: Optional[str]
    semantic_tags: List[str]
    is_entry_point: bool
    memorization_cue: Optional[str] = None


class StoryResponse(BaseModel):
    """Story response schema."""
    id: str
    name_ar: str
    name_en: str
    category: str
    main_figures: Optional[List[str]]
    themes: Optional[List[str]]
    summary_ar: Optional[str]
    summary_en: Optional[str]
    total_verses: int
    suras_mentioned: Optional[List[int]]

    class Config:
        from_attributes = True


class StoryDetailResponse(StoryResponse):
    """Story with segments."""
    segments: List[SegmentResponse] = []


class ThemeResponse(BaseModel):
    """Theme response schema."""
    id: str
    name_ar: str
    name_en: str
    description_ar: Optional[str]
    description_en: Optional[str]
    parent_theme_id: Optional[str]
    related_themes: Optional[List[str]]

    class Config:
        from_attributes = True


class StoryGraphNode(BaseModel):
    """Node in the story graph."""
    id: str
    type: str  # "story", "segment", "verse"
    label: str
    data: dict = Field(default_factory=dict)
    position: Optional[dict] = None  # {x, y} for layout


class StoryGraphEdge(BaseModel):
    """Edge in the story graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    data: dict = Field(default_factory=dict)


class StoryGraphResponse(BaseModel):
    """Story graph data for visualization."""
    story_id: str
    nodes: List[StoryGraphNode]
    edges: List[StoryGraphEdge]
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "chronological"


class CrossStoryConnectionResponse(BaseModel):
    """Cross-story connection for thematic exploration."""
    id: int
    source_story_id: str
    target_story_id: str
    connection_type: str
    strength: float
    label_en: Optional[str] = None
    label_ar: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_ar: Optional[str] = None
    shared_themes: Optional[List[str]] = None
    shared_figures: Optional[List[str]] = None
    evidence_chunk_ids: List[str] = Field(default_factory=list)
    # Verse references ("S:A-B") the connection cites, for display as links.
    verse_refs: List[str] = Field(default_factory=list)
    # Connections are app-authored analytical links, not tafsir.
    provenance: str = "analytical"
    review_status: str = "needs_review"

    class Config:
        from_attributes = True


class SimilarStoryResponse(BaseModel):
    """Similar story based on concept overlap."""
    id: str
    title_ar: str
    title_en: str
    similarity_score: float
    shared_concepts: List[str] = []
    shared_themes: List[str] = []
    shared_figures: List[str] = []


# Routes
@router.get("/", response_model=List[StoryResponse])
async def list_stories(
    category: Optional[str] = Query(None, description="Filter by category"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List all Quranic stories with optional filtering.
    """
    query = select(Story).order_by(Story.name_en)

    if category:
        query = query.where(Story.category == category)

    if theme:
        query = query.where(Story.themes.contains([theme]))

    result = await session.execute(query)
    stories = result.scalars().all()

    verse_counts = await _verse_counts_by_story(session, [s.id for s in stories])

    responses = []
    for story in stories:
        payload = StoryResponse.model_validate(story)
        payload.total_verses = _resolve_total_verses(
            story.total_verses, verse_counts.get(story.id)
        )
        responses.append(payload)

    return responses


@router.get("/categories")
async def get_story_categories(http_response: Response):
    """
    Get available story categories.
    """
    http_response.headers["Cache-Control"] = "public, max-age=86400"
    return {
        "categories": [
            {"id": "prophet", "name_en": "Prophet Stories", "name_ar": "قصص الأنبياء"},
            {"id": "nation", "name_en": "Nation Stories", "name_ar": "قصص الأمم"},
            {"id": "parable", "name_en": "Parables", "name_ar": "الأمثال"},
            {"id": "historical", "name_en": "Historical Events", "name_ar": "الأحداث التاريخية"},
            {"id": "unseen", "name_en": "The Unseen", "name_ar": "الغيب"},
        ]
    }


@router.get("/themes", response_model=List[ThemeResponse])
async def list_themes(
    parent_id: Optional[str] = Query(None, description="Filter by parent theme"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List all themes.
    """
    query = select(Theme).order_by(Theme.name_en)

    if parent_id:
        query = query.where(Theme.parent_theme_id == parent_id)

    result = await session.execute(query)
    themes = result.scalars().all()

    return [ThemeResponse.model_validate(t) for t in themes]


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story(
    story_id: str,
    include_segments: bool = Query(True),
    language: Optional[str] = Query(None, description="ar or en"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get a specific story with its segments.
    """
    query = select(Story).where(Story.id == story_id)

    if include_segments:
        query = query.options(selectinload(Story.segments))

    result = await session.execute(query)
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    response = StoryDetailResponse.model_validate(story)

    # Sort segments by narrative order
    if story.segments:
        evidence = await _segment_evidence(session, story.segments)
        segs = []
        for s in story.segments:
            seg = SegmentResponse.model_validate(s)
            seg.evidence = evidence.get(s.id, [])
            segs.append(seg)
        response.segments = sorted(segs, key=lambda x: x.narrative_order)

    if include_segments:
        # Segments are already loaded — count without a second round trip.
        covered: Set[Tuple[int, int]] = set()
        for segment in story.segments:
            covered |= _segment_verse_keys(
                segment.sura_no, segment.aya_start, segment.aya_end
            )
        derived = len(covered)
    else:
        derived = (await _verse_counts_by_story(session, [story.id])).get(story.id)

    response.total_verses = _resolve_total_verses(story.total_verses, derived)

    return response


@router.get("/{story_id}/connections", response_model=List[ConnectionResponse])
async def get_story_connections(
    story_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all connections for a story's segments.
    """
    # First get all segment IDs for this story
    segment_result = await session.execute(
        select(StorySegment.id).where(StorySegment.story_id == story_id)
    )
    segment_ids = [row[0] for row in segment_result.all()]

    if not segment_ids:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    # Get connections where source or target is in this story
    query = select(StoryConnection).where(
        (StoryConnection.source_segment_id.in_(segment_ids))
        | (StoryConnection.target_segment_id.in_(segment_ids))
    )

    result = await session.execute(query)
    connections = result.scalars().all()

    return [ConnectionResponse.model_validate(c) for c in connections]


@router.get("/{story_id}/graph", response_model=StoryGraphResponse)
async def get_story_graph(
    story_id: str,
    language: str = Query("en", description="Language for labels (ar or en)"),
    mode: str = Query("chronological", description="Layout mode: chronological or thematic"),
    include_cross_story: bool = Query(False, description="Include connections to other stories"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get story as an enhanced graph structure for visualization.

    Features:
    - Semantic ordering with chronological indices
    - Narrative role coloring
    - Entry/exit point marking
    - DAG validation
    - Optional cross-story connections

    Layout modes:
    - chronological: Vertical timeline (top to bottom)
    - thematic: Force-directed with conceptual clustering
    """
    try:
        graph_service = StoryGraphService(session)
        story_graph = await graph_service.build_story_graph(
            story_id=story_id,
            language=language,
            include_cross_story=include_cross_story,
            layout_mode=mode,
        )

        # Convert to response format
        nodes = [
            StoryGraphNode(
                id=n.id,
                type=n.type,
                label=n.label,
                data=n.data,
                position={"x": n.x, "y": n.y} if n.x is not None else None,
            )
            for n in story_graph.nodes
        ]

        edges = [
            StoryGraphEdge(
                source=e.source,
                target=e.target,
                type=e.type,
                label=e.label,
                data=e.data,
            )
            for e in story_graph.edges
        ]

        return StoryGraphResponse(
            story_id=story_id,
            nodes=nodes,
            edges=edges,
            entry_node_id=story_graph.entry_node_id,
            is_valid_dag=story_graph.is_valid_dag,
            layout_mode=mode,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{story_id}/timeline", response_model=List[TimelineStepResponse])
async def get_story_timeline(
    story_id: str,
    language: str = Query("en", description="Language for content (ar or en)"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get story as a linear timeline for step-by-step learning.

    Returns segments ordered by chronological_index,
    suitable for memorization mode and progressive reveal.
    """
    try:
        graph_service = StoryGraphService(session)
        timeline = await graph_service.get_story_timeline(
            story_id=story_id,
            language=language,
        )

        return [TimelineStepResponse(**step) for step in timeline]

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{story_id}/cross-connections", response_model=List[CrossStoryConnectionResponse])
async def get_cross_story_connections(
    story_id: str,
    include_needs_review: bool = Query(
        False,
        description="Include connections hidden pending scholar review (admin/review use only)",
    ),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get connections between this story and other stories.

    Returns thematic links, shared figures, and narrative parallels
    for exploration across the Quranic story corpus. These are analytical
    links (not tafsir); connections flagged needs_review in the manifest are
    excluded by default.
    """
    result = await session.execute(
        select(CrossStoryConnection).where(
            (CrossStoryConnection.source_story_id == story_id) |
            (CrossStoryConnection.target_story_id == story_id)
        )
    )
    connections = result.scalars().all()

    hidden, verse_refs = _manifest_connection_index()
    out = []
    for c in connections:
        key = (c.source_story_id, c.target_story_id, c.connection_type)
        if key in hidden and not include_needs_review:
            continue
        payload = CrossStoryConnectionResponse.model_validate(c)
        payload.evidence_chunk_ids = list(c.evidence_chunk_ids or [])
        payload.verse_refs = list(verse_refs.get(key, ()))
        out.append(payload)
    return out


@router.get("/{story_id}/similar", response_model=List[SimilarStoryResponse])
async def get_similar_stories(
    story_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max similar stories to return"),
    min_score: float = Query(0.1, ge=0, le=1, description="Minimum similarity score"),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get stories similar to the given story based on shared concepts.

    Uses Jaccard similarity on concept overlap.
    Returns stories ranked by similarity score.
    """
    similarity_service = SimilarityService(session)
    similar = await similarity_service.get_similar_stories(
        story_id=story_id,
        limit=limit,
        min_score=min_score,
    )

    return [
        SimilarStoryResponse(
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


@router.get("/by-figure/{figure}")
async def get_stories_by_figure(
    figure: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get stories featuring a specific figure (prophet, king, etc.).
    """
    query = select(Story).where(Story.main_figures.contains([figure]))
    result = await session.execute(query)
    stories = result.scalars().all()

    return {
        "figure": figure,
        "count": len(stories),
        "stories": [StoryResponse.model_validate(s) for s in stories],
    }


@router.get("/by-sura/{sura_no}")
async def get_stories_in_sura(
    sura_no: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get all story segments that appear in a specific sura.
    """
    if sura_no < 1 or sura_no > 114:
        raise HTTPException(status_code=400, detail="Sura must be between 1 and 114")

    query = (
        select(StorySegment)
        .where(StorySegment.sura_no == sura_no)
        .order_by(StorySegment.aya_start)
    )
    result = await session.execute(query)
    segments = result.scalars().all()

    # Group by story
    story_map = {}
    for seg in segments:
        if seg.story_id not in story_map:
            story_map[seg.story_id] = []
        story_map[seg.story_id].append(SegmentResponse.model_validate(seg))

    return {
        "sura_no": sura_no,
        "stories": story_map,
    }
