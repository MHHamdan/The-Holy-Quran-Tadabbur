"""
Story Atlas Service - Quran-wide story graph generation and faceted search.

This service provides:
1. Graph building for story clusters (timeline and concept modes)
2. Faceted search by person, place, era, category
3. Cross-cluster thematic exploration

GROUNDING RULES:
================
- All data comes from seeded clusters/events with tafsir evidence
- Place/time basis is tracked (explicit/inferred/unknown)
- No data invention
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.story_atlas import (
    StoryCluster,
    StoryEvent,
    EventConnection,
    ClusterConnection,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GraphNode:
    """A node in the story graph."""
    id: str
    type: str  # "cluster", "event"
    label: str
    data: dict = field(default_factory=dict)
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass
class GraphEdge:
    """An edge in the story graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    is_chronological: bool = False
    strength: float = 1.0
    data: dict = field(default_factory=dict)


@dataclass
class StoryGraph:
    """Complete story graph with nodes, edges, and metadata."""
    cluster_id: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "timeline"


@dataclass
class ClusterSummary:
    """Summary of a cluster for listing."""
    id: str
    title_ar: str
    title_en: str
    short_title_en: Optional[str]
    category: str
    era: Optional[str]
    main_persons: list[str]
    places: list[dict]
    tags: list[str]
    event_count: int
    primary_sura: Optional[int]
    summary_en: Optional[str]


@dataclass
class Facets:
    """Available facets for filtering."""
    persons: list[str]
    places: list[dict]
    eras: list[str]
    categories: list[str]
    tags: list[str]


# =============================================================================
# STORY ATLAS SERVICE
# =============================================================================

class StoryAtlasService:
    """Service for Story Atlas operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # LISTING & SEARCH
    # =========================================================================

    async def list_clusters(
        self,
        category: Optional[str] = None,
        era: Optional[str] = None,
        person: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ClusterSummary], int]:
        """
        List story clusters with optional filtering.

        Returns tuple of (clusters, total_count).
        """
        query = select(StoryCluster)

        # Apply filters
        if category:
            query = query.where(StoryCluster.category == category)

        if era:
            query = query.where(StoryCluster.era == era)

        if person:
            query = query.where(StoryCluster.main_persons.contains([person]))

        if tag:
            query = query.where(StoryCluster.tags.contains([tag]))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    StoryCluster.title_en.ilike(search_pattern),
                    StoryCluster.title_ar.ilike(search_pattern),
                    StoryCluster.summary_en.ilike(search_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(StoryCluster.title_en).offset(offset).limit(limit)

        result = await self.session.execute(query)
        clusters = result.scalars().all()

        return (
            [self._cluster_to_summary(c) for c in clusters],
            total
        )

    async def get_facets(self) -> Facets:
        """Get all available facets for filtering."""
        # Get all clusters
        result = await self.session.execute(select(StoryCluster))
        clusters = result.scalars().all()

        # Collect unique values
        persons = set()
        places = []
        place_names = set()
        eras = set()
        categories = set()
        tags = set()

        for cluster in clusters:
            if cluster.main_persons:
                persons.update(cluster.main_persons)

            if cluster.places:
                for place in cluster.places:
                    if place.get("name") not in place_names:
                        place_names.add(place.get("name"))
                        places.append(place)

            if cluster.era:
                eras.add(cluster.era)

            categories.add(cluster.category)

            if cluster.tags:
                tags.update(cluster.tags)

        return Facets(
            persons=sorted(persons),
            places=places,
            eras=sorted(eras),
            categories=sorted(categories),
            tags=sorted(tags),
        )

    # =========================================================================
    # CLUSTER DETAIL
    # =========================================================================

    async def get_cluster(self, cluster_id: str) -> Optional[dict]:
        """Get full cluster details with events."""
        result = await self.session.execute(
            select(StoryCluster)
            .where(StoryCluster.id == cluster_id)
            .options(selectinload(StoryCluster.events))
        )
        cluster = result.scalar_one_or_none()

        if not cluster:
            return None

        # Sort events by chronological index
        events = sorted(cluster.events, key=lambda e: e.chronological_index)

        return {
            "id": cluster.id,
            "title_ar": cluster.title_ar,
            "title_en": cluster.title_en,
            "short_title_ar": cluster.short_title_ar,
            "short_title_en": cluster.short_title_en,
            "category": cluster.category,
            "main_persons": cluster.main_persons or [],
            "groups": cluster.groups or [],
            "places": cluster.places or [],
            "era": cluster.era,
            "era_basis": cluster.era_basis,
            "time_description_en": cluster.time_description_en,
            "ayah_spans": cluster.ayah_spans,
            "primary_sura": cluster.primary_sura,
            "suras_mentioned": cluster.suras_mentioned,
            "summary_ar": cluster.summary_ar,
            "summary_en": cluster.summary_en,
            "lessons_ar": cluster.lessons_ar,
            "lessons_en": cluster.lessons_en,
            "tags": cluster.tags or [],
            "total_verses": cluster.total_verses,
            "event_count": cluster.event_count,
            "events": [
                {
                    "id": e.id,
                    "title_ar": e.title_ar,
                    "title_en": e.title_en,
                    "narrative_role": e.narrative_role,
                    "chronological_index": e.chronological_index,
                    "sura_no": e.sura_no,
                    "aya_start": e.aya_start,
                    "aya_end": e.aya_end,
                    "verse_reference": e.verse_reference,
                    "summary_ar": e.summary_ar,
                    "summary_en": e.summary_en,
                    "semantic_tags": e.semantic_tags or [],
                    "is_entry_point": e.is_entry_point,
                    "evidence": e.evidence,
                }
                for e in events
            ],
        }

    # =========================================================================
    # GRAPH BUILDING
    # =========================================================================

    async def build_cluster_graph(
        self,
        cluster_id: str,
        language: str = "en",
        layout_mode: str = "timeline",
    ) -> Optional[StoryGraph]:
        """
        Build a graph for a story cluster.

        Layout modes:
        - timeline: Vertical top-to-bottom chronological
        - concept: Hub-and-spoke thematic layout
        """
        # Load cluster with events
        result = await self.session.execute(
            select(StoryCluster)
            .where(StoryCluster.id == cluster_id)
            .options(selectinload(StoryCluster.events))
        )
        cluster = result.scalar_one_or_none()

        if not cluster:
            return None

        # Load connections
        event_ids = [e.id for e in cluster.events]
        conn_result = await self.session.execute(
            select(EventConnection)
            .where(
                or_(
                    EventConnection.source_event_id.in_(event_ids),
                    EventConnection.target_event_id.in_(event_ids),
                )
            )
        )
        connections = conn_result.scalars().all()

        # Build graph
        graph = StoryGraph(cluster_id=cluster_id, layout_mode=layout_mode)

        # Add cluster root node
        cluster_label = cluster.title_ar if language == "ar" else cluster.title_en
        graph.nodes.append(GraphNode(
            id=cluster.id,
            type="cluster",
            label=cluster_label,
            data={
                "category": cluster.category,
                "main_persons": cluster.main_persons or [],
                "era": cluster.era,
                "summary": cluster.summary_ar if language == "ar" else cluster.summary_en,
            },
        ))

        # Add event nodes
        events_sorted = sorted(cluster.events, key=lambda e: e.chronological_index)
        entry_node = None

        for event in events_sorted:
            label = event.title_ar if language == "ar" else event.title_en
            summary = event.summary_ar if language == "ar" else event.summary_en

            node = GraphNode(
                id=event.id,
                type="event",
                label=label,
                data={
                    "narrative_role": event.narrative_role,
                    "chronological_index": event.chronological_index,
                    "verse_reference": event.verse_reference,
                    "sura_no": event.sura_no,
                    "aya_start": event.aya_start,
                    "aya_end": event.aya_end,
                    "summary": summary,
                    "semantic_tags": event.semantic_tags or [],
                    "is_entry_point": event.is_entry_point,
                    "evidence": event.evidence,
                },
            )
            graph.nodes.append(node)

            # Track entry node
            if event.is_entry_point or entry_node is None:
                if event.is_entry_point:
                    entry_node = event.id
                elif entry_node is None:
                    entry_node = event.id

            # Add containment edge
            graph.edges.append(GraphEdge(
                source=cluster.id,
                target=event.id,
                type="contains",
                is_chronological=False,
            ))

        graph.entry_node_id = entry_node

        # Add connection edges
        for conn in connections:
            graph.edges.append(GraphEdge(
                source=conn.source_event_id,
                target=conn.target_event_id,
                type=conn.edge_type,
                is_chronological=conn.is_chronological,
                strength=conn.strength or 1.0,
                label=conn.justification_en[:40] + "..." if conn.justification_en and len(conn.justification_en) > 40 else conn.justification_en,
            ))

        # Validate DAG
        graph.is_valid_dag = self._validate_dag(graph)

        # Compute layout
        self._compute_layout(graph, layout_mode)

        return graph

    async def get_timeline(
        self,
        cluster_id: str,
        language: str = "en",
    ) -> Optional[list[dict]]:
        """Get a linear timeline view of a cluster."""
        cluster = await self.get_cluster(cluster_id)
        if not cluster:
            return None

        timeline = []
        for event in cluster["events"]:
            timeline.append({
                "id": event["id"],
                "index": event["chronological_index"],
                "title": event["title_ar"] if language == "ar" else event["title_en"],
                "verse_reference": event["verse_reference"],
                "narrative_role": event["narrative_role"],
                "summary": event["summary_ar"] if language == "ar" else event["summary_en"],
                "semantic_tags": event["semantic_tags"],
                "is_entry_point": event["is_entry_point"],
                "evidence": event["evidence"],
            })

        return timeline

    # =========================================================================
    # CROSS-CLUSTER CONNECTIONS
    # =========================================================================

    async def get_related_clusters(self, cluster_id: str) -> list[dict]:
        """Get clusters related to this one."""
        result = await self.session.execute(
            select(ClusterConnection)
            .where(
                or_(
                    ClusterConnection.source_cluster_id == cluster_id,
                    ClusterConnection.target_cluster_id == cluster_id,
                )
            )
        )
        connections = result.scalars().all()

        related = []
        for conn in connections:
            other_id = (
                conn.target_cluster_id
                if conn.source_cluster_id == cluster_id
                else conn.source_cluster_id
            )

            # Load other cluster
            other_result = await self.session.execute(
                select(StoryCluster).where(StoryCluster.id == other_id)
            )
            other = other_result.scalar_one_or_none()

            if other:
                related.append({
                    "cluster_id": other.id,
                    "title_en": other.title_en,
                    "title_ar": other.title_ar,
                    "connection_type": conn.connection_type,
                    "strength": conn.strength,
                    "label_en": conn.label_en,
                    "shared_persons": conn.shared_persons or [],
                    "shared_places": conn.shared_places or [],
                    "shared_themes": conn.shared_themes or [],
                })

        return related

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _cluster_to_summary(self, cluster: StoryCluster) -> ClusterSummary:
        """Convert cluster to summary."""
        return ClusterSummary(
            id=cluster.id,
            title_ar=cluster.title_ar,
            title_en=cluster.title_en,
            short_title_en=cluster.short_title_en,
            category=cluster.category,
            era=cluster.era,
            main_persons=cluster.main_persons or [],
            places=cluster.places or [],
            tags=cluster.tags or [],
            event_count=cluster.event_count or 0,
            primary_sura=cluster.primary_sura,
            summary_en=cluster.summary_en,
        )

    def _validate_dag(self, graph: StoryGraph) -> bool:
        """Validate that chronological edges form a DAG."""
        chrono_edges: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges:
            if edge.is_chronological:
                chrono_edges[edge.source].append(edge.target)

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in chrono_edges.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph.nodes:
            if node.id not in visited:
                if has_cycle(node.id):
                    return False

        return True

    def _compute_layout(self, graph: StoryGraph, mode: str) -> None:
        """Compute node positions."""
        if mode == "timeline":
            self._layout_timeline(graph)
        else:
            self._layout_concept(graph)

    def _layout_timeline(self, graph: StoryGraph) -> None:
        """Layout nodes as vertical timeline."""
        y_spacing = 100
        x_center = 0

        # Cluster node at top
        for node in graph.nodes:
            if node.type == "cluster":
                node.x = x_center
                node.y = 0

        # Event nodes below, ordered by chronological_index
        event_nodes = [n for n in graph.nodes if n.type == "event"]
        event_nodes.sort(key=lambda n: n.data.get("chronological_index", 0))

        for i, node in enumerate(event_nodes):
            node.x = x_center
            node.y = (i + 1) * y_spacing

    def _layout_concept(self, graph: StoryGraph) -> None:
        """Layout nodes in hub-and-spoke pattern."""
        import math

        # Cluster at center
        for node in graph.nodes:
            if node.type == "cluster":
                node.x = 0
                node.y = 0

        # Events in a circle around cluster
        event_nodes = [n for n in graph.nodes if n.type == "event"]
        n_events = len(event_nodes)

        if n_events > 0:
            radius = 200
            for i, node in enumerate(event_nodes):
                angle = (2 * math.pi * i) / n_events
                node.x = radius * math.cos(angle)
                node.y = radius * math.sin(angle)


# =============================================================================
# ROLE ICONS AND COLORS (for UI)
# =============================================================================

ROLE_STYLES = {
    "introduction": {"icon": "play", "color": "#4CAF50"},
    "warning": {"icon": "alert-triangle", "color": "#FF9800"},
    "trial": {"icon": "target", "color": "#E91E63"},
    "miracle": {"icon": "star", "color": "#9C27B0"},
    "migration": {"icon": "map-pin", "color": "#2196F3"},
    "confrontation": {"icon": "users", "color": "#F44336"},
    "divine_intervention": {"icon": "zap", "color": "#FFD700"},
    "outcome": {"icon": "check-circle", "color": "#00BCD4"},
    "reflection": {"icon": "book-open", "color": "#607D8B"},
    "dialogue": {"icon": "message-circle", "color": "#795548"},
    "prophecy": {"icon": "eye", "color": "#673AB7"},
    "encounter": {"icon": "users", "color": "#3F51B5"},
}


def get_role_style(role: str) -> dict:
    """Get icon and color for a narrative role."""
    return ROLE_STYLES.get(role, {"icon": "circle", "color": "#9E9E9E"})
