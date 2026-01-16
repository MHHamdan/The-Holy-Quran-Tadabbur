"""
Graph Exploration API Routes.

Endpoints for advanced graph exploration:
- BFS/DFS exploration
- Pathfinding between entities
- Subgraph extraction
- Relationship analysis
- Thematic connections
- Semantic search

Arabic: واجهة برمجة تطبيقات استكشاف الرسم البياني
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.graph_explorer import get_graph_explorer, GraphNode, GraphEdge, GraphPath
from app.services.thematic_mapper import get_thematic_mapper
from app.services.semantic_search import get_semantic_search, SearchIntent
from app.core.responses import APIError, ErrorCode, get_request_id

router = APIRouter()


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class NodeResponse(BaseModel):
    """Graph node response."""
    id: str
    type: str
    label: str
    label_ar: str
    depth: int = 0
    weight: float = 1.0
    data: Dict[str, Any] = {}


class EdgeResponse(BaseModel):
    """Graph edge response."""
    source: str
    target: str
    type: str
    label: str = ""
    weight: float = 1.0


class PathResponse(BaseModel):
    """Path response."""
    start: str
    end: str
    nodes: List[str]
    length: int
    total_weight: float


class ExplorationResponse(BaseModel):
    """Graph exploration response."""
    ok: bool = True
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    center_node: Optional[str] = None
    max_depth: int = 0
    total_nodes: int = 0
    total_edges: int = 0


class PathfindingResponse(BaseModel):
    """Pathfinding response."""
    ok: bool = True
    path_found: bool
    path: Optional[PathResponse] = None


class AllPathsResponse(BaseModel):
    """All paths response."""
    ok: bool = True
    paths: List[PathResponse]
    total_paths: int = 0


class RelationshipStrengthResponse(BaseModel):
    """Relationship strength response."""
    ok: bool = True
    entity1: str
    entity2: str
    direct_connection: Optional[Dict[str, Any]] = None
    shared_neighbors: int = 0
    shortest_path_length: Optional[int] = None
    overall_strength: float = 0.0


class ThemeOccurrenceResponse(BaseModel):
    """Theme occurrence response."""
    theme_id: str
    theme_label_ar: str
    theme_label_en: str
    story_id: Optional[str] = None
    story_title_ar: Optional[str] = None
    story_title_en: Optional[str] = None
    verse_reference: Optional[str] = None
    context_ar: str = ""
    context_en: str = ""
    weight: float = 1.0


class ThemeConnectionResponse(BaseModel):
    """Theme connection response."""
    theme1_id: str
    theme1_label_ar: str
    theme1_label_en: str
    theme2_id: str
    theme2_label_ar: str
    theme2_label_en: str
    connection_type: str
    strength: float
    evidence_count: int


class ThematicJourneyResponse(BaseModel):
    """Thematic journey response."""
    ok: bool = True
    start_theme: str
    themes: List[str]
    connections: List[ThemeConnectionResponse]
    total_verses: int
    stories_covered: List[str]


class ThemeProgressionResponse(BaseModel):
    """Theme progression response."""
    ok: bool = True
    theme_id: str
    theme_label_ar: str
    theme_label_en: str
    total_occurrences: int
    by_surah: Dict[int, int]
    by_story: Dict[str, int]
    evolution_stages: List[Dict[str, Any]]


class SearchHitResponse(BaseModel):
    """Search hit response."""
    id: str
    type: str
    title: str
    title_ar: str
    content: str
    content_ar: str
    score: float
    confidence: float
    verse_reference: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    ok: bool = True
    query: str
    expanded_query: str
    intent: str
    hits: List[SearchHitResponse]
    total_found: int
    related_concepts: List[Dict[str, Any]] = []
    suggested_queries: List[str] = []
    search_time_ms: int = 0


class ThemeGraphResponse(BaseModel):
    """Theme graph visualization response."""
    ok: bool = True
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    center_theme: str
    depth: int


# =============================================================================
# GRAPH EXPLORATION ENDPOINTS
# =============================================================================

@router.get("/explore/bfs", response_model=ExplorationResponse)
async def explore_bfs(
    start_id: str = Query(..., description="Starting node ID"),
    max_depth: int = Query(default=3, ge=1, le=5, description="Maximum depth"),
    edge_types: Optional[str] = Query(None, description="Comma-separated edge types"),
    max_nodes: int = Query(default=50, ge=1, le=200, description="Maximum nodes"),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
):
    """
    Breadth-first exploration from a starting node.

    Returns all reachable nodes within max_depth hops,
    ordered by distance from start.
    """
    explorer = get_graph_explorer()

    edge_type_list = None
    if edge_types:
        edge_type_list = [e.strip() for e in edge_types.split(",")]

    result = await explorer.bfs_explore(
        start_id=start_id,
        max_depth=max_depth,
        edge_types=edge_type_list,
        max_nodes=max_nodes,
        language=lang,
    )

    return ExplorationResponse(
        ok=True,
        nodes=[
            NodeResponse(
                id=n.id,
                type=n.type,
                label=n.label,
                label_ar=n.label_ar,
                depth=n.depth,
                weight=n.weight,
                data=n.data,
            )
            for n in result.nodes
        ],
        edges=[
            EdgeResponse(
                source=e.source,
                target=e.target,
                type=e.type,
                label=e.label,
                weight=e.weight,
            )
            for e in result.edges
        ],
        center_node=result.center_node,
        max_depth=result.max_depth,
        total_nodes=result.total_nodes,
        total_edges=result.total_edges,
    )


@router.get("/explore/dfs", response_model=ExplorationResponse)
async def explore_dfs(
    start_id: str = Query(..., description="Starting node ID"),
    max_depth: int = Query(default=5, ge=1, le=10, description="Maximum depth"),
    edge_types: Optional[str] = Query(None, description="Comma-separated edge types"),
    max_nodes: int = Query(default=50, ge=1, le=200, description="Maximum nodes"),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
):
    """
    Depth-first exploration from a starting node.

    Goes as deep as possible before backtracking.
    Good for finding complete paths through the graph.
    """
    explorer = get_graph_explorer()

    edge_type_list = None
    if edge_types:
        edge_type_list = [e.strip() for e in edge_types.split(",")]

    result = await explorer.dfs_explore(
        start_id=start_id,
        max_depth=max_depth,
        edge_types=edge_type_list,
        max_nodes=max_nodes,
        language=lang,
    )

    return ExplorationResponse(
        ok=True,
        nodes=[
            NodeResponse(
                id=n.id,
                type=n.type,
                label=n.label,
                label_ar=n.label_ar,
                depth=n.depth,
                weight=n.weight,
                data=n.data,
            )
            for n in result.nodes
        ],
        edges=[
            EdgeResponse(
                source=e.source,
                target=e.target,
                type=e.type,
                label=e.label,
                weight=e.weight,
            )
            for e in result.edges
        ],
        center_node=result.center_node,
        max_depth=result.max_depth,
        total_nodes=result.total_nodes,
        total_edges=result.total_edges,
    )


@router.get("/path", response_model=PathfindingResponse)
async def find_path(
    start_id: str = Query(..., description="Starting node ID"),
    end_id: str = Query(..., description="Target node ID"),
    edge_types: Optional[str] = Query(None, description="Comma-separated edge types"),
    max_depth: int = Query(default=10, ge=1, le=20, description="Maximum search depth"),
):
    """
    Find shortest path between two nodes using BFS.
    """
    explorer = get_graph_explorer()

    edge_type_list = None
    if edge_types:
        edge_type_list = [e.strip() for e in edge_types.split(",")]

    path = await explorer.find_path(
        start_id=start_id,
        end_id=end_id,
        edge_types=edge_type_list,
        max_depth=max_depth,
    )

    if path:
        return PathfindingResponse(
            ok=True,
            path_found=True,
            path=PathResponse(
                start=path.start,
                end=path.end,
                nodes=path.nodes,
                length=path.length,
                total_weight=path.total_weight,
            ),
        )

    return PathfindingResponse(
        ok=True,
        path_found=False,
        path=None,
    )


@router.get("/paths/all", response_model=AllPathsResponse)
async def find_all_paths(
    start_id: str = Query(..., description="Starting node ID"),
    end_id: str = Query(..., description="Target node ID"),
    edge_types: Optional[str] = Query(None, description="Comma-separated edge types"),
    max_depth: int = Query(default=5, ge=1, le=10, description="Maximum path length"),
    max_paths: int = Query(default=10, ge=1, le=50, description="Maximum paths to return"),
):
    """
    Find all paths between two nodes (up to max_paths).
    """
    explorer = get_graph_explorer()

    edge_type_list = None
    if edge_types:
        edge_type_list = [e.strip() for e in edge_types.split(",")]

    paths = await explorer.find_all_paths(
        start_id=start_id,
        end_id=end_id,
        edge_types=edge_type_list,
        max_depth=max_depth,
        max_paths=max_paths,
    )

    return AllPathsResponse(
        ok=True,
        paths=[
            PathResponse(
                start=p.start,
                end=p.end,
                nodes=p.nodes,
                length=p.length,
                total_weight=p.total_weight,
            )
            for p in paths
        ],
        total_paths=len(paths),
    )


@router.get("/relationship-strength", response_model=RelationshipStrengthResponse)
async def get_relationship_strength(
    entity1_id: str = Query(..., description="First entity ID"),
    entity2_id: str = Query(..., description="Second entity ID"),
):
    """
    Calculate the strength of relationship between two entities.
    """
    explorer = get_graph_explorer()

    result = await explorer.calculate_relationship_strength(
        entity1_id=entity1_id,
        entity2_id=entity2_id,
    )

    return RelationshipStrengthResponse(
        ok=True,
        entity1=result["entity1"],
        entity2=result["entity2"],
        direct_connection=result.get("direct_connection"),
        shared_neighbors=result["shared_neighbors"],
        shortest_path_length=result.get("shortest_path_length"),
        overall_strength=result["overall_strength"],
    )


@router.get("/related", response_model=ExplorationResponse)
async def get_related_entities(
    entity_id: str = Query(..., description="Entity ID"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types to filter"),
    limit: int = Query(default=20, ge=1, le=100),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
):
    """
    Get entities related to a given entity.
    """
    explorer = get_graph_explorer()

    type_list = None
    if entity_types:
        type_list = [t.strip() for t in entity_types.split(",")]

    nodes = await explorer.get_related_entities(
        entity_id=entity_id,
        entity_types=type_list,
        limit=limit,
        language=lang,
    )

    return ExplorationResponse(
        ok=True,
        nodes=[
            NodeResponse(
                id=n.id,
                type=n.type,
                label=n.label,
                label_ar=n.label_ar,
                depth=n.depth,
                weight=n.weight,
                data=n.data,
            )
            for n in nodes
        ],
        edges=[],
        total_nodes=len(nodes),
        total_edges=0,
    )


# =============================================================================
# THEMATIC ENDPOINTS
# =============================================================================

@router.get("/thematic/occurrences")
async def get_theme_occurrences(
    theme: str = Query(..., description="Theme key (e.g., 'صبر', 'patience')"),
    limit: int = Query(default=50, ge=1, le=200),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
):
    """
    Get all occurrences of a theme across stories and verses.
    """
    mapper = get_thematic_mapper()

    occurrences = await mapper.get_theme_occurrences(
        theme_key=theme,
        limit=limit,
        language=lang,
    )

    return {
        "ok": True,
        "theme": theme,
        "occurrences": [
            {
                "theme_id": o.theme_id,
                "theme_label_ar": o.theme_label_ar,
                "theme_label_en": o.theme_label_en,
                "story_id": o.story_id,
                "story_title_ar": o.story_title_ar,
                "story_title_en": o.story_title_en,
                "verse_reference": o.verse_reference,
                "context_ar": o.context_ar,
                "context_en": o.context_en,
                "weight": o.weight,
            }
            for o in occurrences
        ],
        "total": len(occurrences),
    }


@router.get("/thematic/connections")
async def get_theme_connections(
    theme: str = Query(..., description="Theme key"),
    min_strength: float = Query(default=0.3, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=50),
):
    """
    Find themes connected to a given theme.
    """
    mapper = get_thematic_mapper()

    connections = await mapper.find_theme_connections(
        theme_key=theme,
        min_strength=min_strength,
        limit=limit,
    )

    return {
        "ok": True,
        "theme": theme,
        "connections": [
            {
                "theme1_id": c.theme1_id,
                "theme1_label_ar": c.theme1_label_ar,
                "theme1_label_en": c.theme1_label_en,
                "theme2_id": c.theme2_id,
                "theme2_label_ar": c.theme2_label_ar,
                "theme2_label_en": c.theme2_label_en,
                "connection_type": c.connection_type,
                "strength": c.strength,
                "evidence_count": c.evidence_count,
            }
            for c in connections
        ],
        "total": len(connections),
    }


@router.get("/thematic/stories")
async def get_stories_by_theme(
    theme: str = Query(..., description="Theme key"),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
):
    """
    Get all stories that feature a specific theme.
    """
    mapper = get_thematic_mapper()

    stories = await mapper.get_stories_by_theme(
        theme_key=theme,
        language=lang,
    )

    return {
        "ok": True,
        "theme": theme,
        "stories": stories,
        "total": len(stories),
    }


@router.get("/thematic/progression", response_model=ThemeProgressionResponse)
async def get_theme_progression(
    theme: str = Query(..., description="Theme key"),
):
    """
    Analyze how a theme progresses through the Quran.
    """
    mapper = get_thematic_mapper()

    progression = await mapper.get_theme_progression(theme_key=theme)

    return ThemeProgressionResponse(
        ok=True,
        theme_id=progression.theme_id,
        theme_label_ar=progression.theme_label_ar,
        theme_label_en=progression.theme_label_en,
        total_occurrences=progression.total_occurrences,
        by_surah=progression.by_surah,
        by_story=progression.by_story,
        evolution_stages=progression.evolution_stages,
    )


@router.get("/thematic/journey", response_model=ThematicJourneyResponse)
async def build_thematic_journey(
    start_theme: str = Query(..., description="Starting theme"),
    max_steps: int = Query(default=5, ge=2, le=10, description="Maximum journey length"),
):
    """
    Build a journey through connected themes.
    """
    mapper = get_thematic_mapper()

    journey = await mapper.build_thematic_journey(
        start_theme=start_theme,
        max_steps=max_steps,
    )

    return ThematicJourneyResponse(
        ok=True,
        start_theme=journey.start_theme,
        themes=journey.themes,
        connections=[
            ThemeConnectionResponse(
                theme1_id=c.theme1_id,
                theme1_label_ar=c.theme1_label_ar,
                theme1_label_en=c.theme1_label_en,
                theme2_id=c.theme2_id,
                theme2_label_ar=c.theme2_label_ar,
                theme2_label_en=c.theme2_label_en,
                connection_type=c.connection_type,
                strength=c.strength,
                evidence_count=c.evidence_count,
            )
            for c in journey.connections
        ],
        total_verses=journey.total_verses,
        stories_covered=journey.stories_covered,
    )


@router.get("/thematic/cross-story")
async def get_cross_story_themes(
    story_ids: str = Query(..., description="Comma-separated story IDs"),
    min_occurrences: int = Query(default=2, ge=2, le=10),
):
    """
    Find themes that appear across multiple stories.
    """
    mapper = get_thematic_mapper()

    id_list = [s.strip() for s in story_ids.split(",")]

    themes = await mapper.get_cross_story_themes(
        story_ids=id_list,
        min_occurrences=min_occurrences,
    )

    return {
        "ok": True,
        "story_ids": id_list,
        "shared_themes": themes,
        "total": len(themes),
    }


@router.get("/thematic/graph", response_model=ThemeGraphResponse)
async def get_theme_graph(
    theme: str = Query(..., description="Central theme"),
    depth: int = Query(default=2, ge=1, le=3, description="Graph depth"),
):
    """
    Get graph visualization data for a theme.
    """
    mapper = get_thematic_mapper()

    graph_data = await mapper.get_theme_graph_data(
        theme_key=theme,
        depth=depth,
    )

    return ThemeGraphResponse(
        ok=True,
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
        center_theme=graph_data["center_theme"],
        depth=graph_data["depth"],
    )


# =============================================================================
# SEMANTIC SEARCH ENDPOINTS
# =============================================================================

@router.get("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    lang: str = Query(default="ar", pattern="^(ar|en)$"),
    intent: Optional[str] = Query(None, description="Search intent (auto-detected if not provided)"),
    expand: bool = Query(default=True, description="Expand query with related concepts"),
    limit: int = Query(default=20, ge=1, le=100),
    min_confidence: float = Query(default=0.3, ge=0.0, le=1.0),
):
    """
    Perform enhanced semantic search.

    Supports:
    - Query intent detection
    - Concept expansion
    - Confidence scoring
    - Multi-type search (verses, stories, themes, persons)
    """
    search_service = get_semantic_search()

    search_intent = None
    if intent:
        try:
            search_intent = SearchIntent(intent)
        except ValueError:
            pass

    result = await search_service.search(
        query=q,
        language=lang,
        intent=search_intent,
        expand_concepts=expand,
        include_related=True,
        limit=limit,
        min_confidence=min_confidence,
    )

    return SemanticSearchResponse(
        ok=True,
        query=result.query,
        expanded_query=result.expanded_query,
        intent=result.intent.value,
        hits=[
            SearchHitResponse(
                id=h.id,
                type=h.type,
                title=h.title,
                title_ar=h.title_ar,
                content=h.content,
                content_ar=h.content_ar,
                score=h.score,
                confidence=h.confidence,
                verse_reference=h.verse_reference,
                metadata=h.metadata,
            )
            for h in result.hits
        ],
        total_found=result.total_found,
        related_concepts=result.related_concepts,
        suggested_queries=result.suggested_queries,
        search_time_ms=result.search_time_ms,
    )


@router.get("/search/intents")
async def get_search_intents():
    """Get available search intents."""
    return {
        "ok": True,
        "intents": [
            {"value": "verse_meaning", "label_en": "Verse Meaning", "label_ar": "معنى الآية"},
            {"value": "theme_search", "label_en": "Theme Search", "label_ar": "بحث الموضوع"},
            {"value": "story_search", "label_en": "Story Search", "label_ar": "بحث القصة"},
            {"value": "concept_search", "label_en": "Concept Search", "label_ar": "بحث المفهوم"},
            {"value": "person_search", "label_en": "Person Search", "label_ar": "بحث الشخصية"},
            {"value": "general", "label_en": "General", "label_ar": "عام"},
        ],
    }


# =============================================================================
# GLOBAL GRAPH OVERVIEW ENDPOINTS
# =============================================================================

class GraphStatsResponse(BaseModel):
    """Graph statistics response."""
    ok: bool = True
    node_counts: Dict[str, int]
    edge_counts: Dict[str, int]
    total_nodes: int
    total_edges: int
    most_connected: List[Dict[str, Any]]


class EntityTypeResponse(BaseModel):
    """Entity types response."""
    ok: bool = True
    types: List[Dict[str, Any]]


class GraphOverviewResponse(BaseModel):
    """Full graph overview for exploration."""
    ok: bool = True
    stats: Dict[str, Any]
    entity_types: List[Dict[str, Any]]
    sample_entities: Dict[str, List[Dict[str, Any]]]


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats():
    """
    Get knowledge graph statistics.

    Returns counts of nodes and edges by type.
    Arabic: إحصائيات الرسم البياني المعرفي
    """
    from app.kg.client import get_kg_client

    kg = get_kg_client()

    # Count nodes by type
    node_tables = ["story_cluster", "story_event", "person", "place", "concept_tag"]
    node_counts = {}
    total_nodes = 0

    for table in node_tables:
        try:
            result = await kg.query(f"SELECT count() FROM {table} GROUP ALL;")
            count = result[0].get("count", 0) if result else 0
            node_counts[table] = count
            total_nodes += count
        except Exception:
            node_counts[table] = 0

    # Count edges by type
    edge_tables = ["next", "involves", "located_in", "tagged_with", "part_of", "thematic_link"]
    edge_counts = {}
    total_edges = 0

    for table in edge_tables:
        try:
            result = await kg.query(f"SELECT count() FROM {table} GROUP ALL;")
            count = result[0].get("count", 0) if result else 0
            edge_counts[table] = count
            total_edges += count
        except Exception:
            edge_counts[table] = 0

    # Find most connected entities
    most_connected = []
    try:
        # Count outgoing edges for stories
        result = await kg.query("""
            SELECT id, title_en, title_ar,
                   count(->tagged_with) as tag_count,
                   count(->involves) as person_count,
                   count(<-part_of<-story_event) as event_count
            FROM story_cluster
            ORDER BY (tag_count + person_count + event_count) DESC
            LIMIT 10;
        """)
        for r in result:
            if r.get("id"):
                total_connections = (r.get("tag_count", 0) or 0) + (r.get("person_count", 0) or 0) + (r.get("event_count", 0) or 0)
                most_connected.append({
                    "id": r.get("id"),
                    "title_en": r.get("title_en", ""),
                    "title_ar": r.get("title_ar", ""),
                    "type": "story",
                    "connection_count": total_connections,
                })
    except Exception:
        pass

    return GraphStatsResponse(
        node_counts=node_counts,
        edge_counts=edge_counts,
        total_nodes=total_nodes,
        total_edges=total_edges,
        most_connected=most_connected,
    )


@router.get("/entity-types", response_model=EntityTypeResponse)
async def get_entity_types():
    """
    Get available entity types for exploration.

    Arabic: أنواع الكيانات المتاحة
    """
    return EntityTypeResponse(
        types=[
            {
                "key": "story_cluster",
                "label_en": "Stories",
                "label_ar": "القصص",
                "description_en": "Quranic narrative clusters",
                "description_ar": "مجموعات السرد القرآني",
                "icon": "📖",
            },
            {
                "key": "story_event",
                "label_en": "Events",
                "label_ar": "الأحداث",
                "description_en": "Story events and segments",
                "description_ar": "أحداث وفصول القصص",
                "icon": "📍",
            },
            {
                "key": "person",
                "label_en": "Persons",
                "label_ar": "الشخصيات",
                "description_en": "Prophets and figures",
                "description_ar": "الأنبياء والشخصيات",
                "icon": "👤",
            },
            {
                "key": "place",
                "label_en": "Places",
                "label_ar": "الأماكن",
                "description_en": "Locations in stories",
                "description_ar": "المواقع في القصص",
                "icon": "🏛️",
            },
            {
                "key": "concept_tag",
                "label_en": "Themes & Concepts",
                "label_ar": "المواضيع والمفاهيم",
                "description_en": "Thematic concepts and morals",
                "description_ar": "المفاهيم الموضوعية والعبر",
                "icon": "🏷️",
            },
        ]
    )


@router.get("/overview", response_model=GraphOverviewResponse)
async def get_graph_overview():
    """
    Get comprehensive graph overview for exploration UI.

    Combines stats, entity types, and sample entities.
    Arabic: نظرة شاملة على الرسم البياني المعرفي
    """
    from app.kg.client import get_kg_client

    kg = get_kg_client()

    # Get stats
    stats = {}
    node_tables = ["story_cluster", "story_event", "person", "place", "concept_tag"]
    for table in node_tables:
        try:
            result = await kg.query(f"SELECT count() FROM {table} GROUP ALL;")
            stats[table] = result[0].get("count", 0) if result else 0
        except Exception:
            stats[table] = 0

    edge_tables = ["tagged_with", "involves", "part_of", "next"]
    for table in edge_tables:
        try:
            result = await kg.query(f"SELECT count() FROM {table} GROUP ALL;")
            stats[f"edge_{table}"] = result[0].get("count", 0) if result else 0
        except Exception:
            stats[f"edge_{table}"] = 0

    # Get sample entities
    sample_entities = {}

    # Sample stories
    try:
        stories = await kg.query("SELECT id, slug, title_en, title_ar, category FROM story_cluster LIMIT 10;")
        sample_entities["stories"] = [
            {"id": s.get("id"), "slug": s.get("slug"), "title_en": s.get("title_en"), "title_ar": s.get("title_ar"), "category": s.get("category")}
            for s in stories
        ]
    except Exception:
        sample_entities["stories"] = []

    # Sample concepts
    try:
        concepts = await kg.query("SELECT id, key, label_en, label_ar, category FROM concept_tag LIMIT 15;")
        sample_entities["concepts"] = [
            {"id": c.get("id"), "key": c.get("key"), "label_en": c.get("label_en"), "label_ar": c.get("label_ar"), "category": c.get("category")}
            for c in concepts
        ]
    except Exception:
        sample_entities["concepts"] = []

    # Sample persons
    try:
        persons = await kg.query("SELECT id, key, name_en, name_ar, type FROM person LIMIT 10;")
        sample_entities["persons"] = [
            {"id": p.get("id"), "key": p.get("key"), "name_en": p.get("name_en"), "name_ar": p.get("name_ar"), "type": p.get("type")}
            for p in persons
        ]
    except Exception:
        sample_entities["persons"] = []

    # Entity types
    entity_types = [
        {"key": "story_cluster", "label_en": "Stories", "label_ar": "القصص", "icon": "📖"},
        {"key": "story_event", "label_en": "Events", "label_ar": "الأحداث", "icon": "📍"},
        {"key": "person", "label_en": "Persons", "label_ar": "الشخصيات", "icon": "👤"},
        {"key": "place", "label_en": "Places", "label_ar": "الأماكن", "icon": "🏛️"},
        {"key": "concept_tag", "label_en": "Themes", "label_ar": "المواضيع", "icon": "🏷️"},
    ]

    return GraphOverviewResponse(
        stats=stats,
        entity_types=entity_types,
        sample_entities=sample_entities,
    )


@router.get("/entity/{entity_id:path}")
async def get_entity_details(entity_id: str):
    """
    Get detailed information about a specific entity.

    Args:
        entity_id: Full entity ID (e.g., 'story_cluster:musa', 'concept_tag:patience')

    Arabic: تفاصيل الكيان
    """
    from app.kg.client import get_kg_client

    kg = get_kg_client()

    try:
        # Get entity
        result = await kg.query(f"SELECT * FROM {entity_id};")
        if not result:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")

        entity = result[0]

        # Get relationships
        relationships = {
            "outgoing": [],
            "incoming": [],
        }

        # Outgoing edges
        edge_types = ["tagged_with", "involves", "located_in", "part_of", "next"]
        for edge_type in edge_types:
            try:
                edges = await kg.query(f"SELECT out.id, out.* FROM {edge_type} WHERE in = {entity_id} LIMIT 20;")
                for edge in edges:
                    if edge.get("id"):
                        relationships["outgoing"].append({
                            "type": edge_type,
                            "target_id": edge.get("id"),
                            "target_data": {k: v for k, v in edge.items() if k not in ["id", "in", "out"]},
                        })
            except Exception:
                pass

        # Incoming edges
        for edge_type in edge_types:
            try:
                edges = await kg.query(f"SELECT in.id, in.* FROM {edge_type} WHERE out = {entity_id} LIMIT 20;")
                for edge in edges:
                    if edge.get("id"):
                        relationships["incoming"].append({
                            "type": edge_type,
                            "source_id": edge.get("id"),
                            "source_data": {k: v for k, v in edge.items() if k not in ["id", "in", "out"]},
                        })
            except Exception:
                pass

        return {
            "ok": True,
            "entity": entity,
            "relationships": relationships,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
