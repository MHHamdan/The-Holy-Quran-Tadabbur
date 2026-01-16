"""
Theme Graph Service - Graph visualization and timeline for Quranic themes.

This service provides:
1. Graph building (nodes/edges) for theme visualization
2. Timeline view (linear progression through segments)
3. DAG validation for sequential edges
4. Cross-theme connections

Pattern follows: app/services/story_graph.py
"""
from typing import List, Optional, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.theme import (
    QuranicTheme, ThemeSegment, ThemeConnection,
    EDGE_TYPE_TRANSLATIONS, THEME_CATEGORY_TRANSLATIONS,
)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ThemeGraphNode:
    """Node in a theme graph."""
    id: str
    type: str  # "theme", "segment"
    label: str
    label_ar: str
    data: Dict[str, Any] = field(default_factory=dict)
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass
class ThemeGraphEdge:
    """Edge in a theme graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    label_ar: Optional[str] = None
    is_sequential: bool = False
    strength: float = 1.0
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThemeGraph:
    """Complete graph for a theme."""
    theme_id: str
    theme_title_ar: str
    theme_title_en: str
    nodes: List[ThemeGraphNode] = field(default_factory=list)
    edges: List[ThemeGraphEdge] = field(default_factory=list)
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "sequential"
    total_segments: int = 0
    total_connections: int = 0


@dataclass
class TimelineNode:
    """Node in a theme timeline."""
    segment_id: str
    segment_order: int
    chronological_index: Optional[int]
    sura_no: int
    ayah_start: int
    ayah_end: int
    verse_reference: str
    title_ar: Optional[str]
    title_en: Optional[str]
    summary_ar: str
    summary_en: str
    revelation_context: Optional[str]
    is_entry_point: bool
    is_verified: bool


# =============================================================================
# THEME GRAPH SERVICE
# =============================================================================

class ThemeGraphService:
    """Service for building theme graphs and timelines."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # GRAPH BUILDING
    # =========================================================================

    async def build_theme_graph(
        self,
        theme_id: str,
        language: str = "en",
        layout_mode: str = "sequential",  # or "revelation", "thematic"
        include_subthemes: bool = False,
    ) -> Optional[ThemeGraph]:
        """
        Build complete graph for a theme.

        Args:
            theme_id: Theme ID to build graph for
            language: Language for labels ("en" or "ar")
            layout_mode: Layout algorithm ("sequential", "revelation", "thematic")
            include_subthemes: Include child themes in graph

        Returns:
            ThemeGraph with nodes and edges, or None if theme not found
        """
        # Get theme with segments and connections
        theme = await self._get_theme_with_segments(theme_id)
        if not theme:
            return None

        nodes: List[ThemeGraphNode] = []
        edges: List[ThemeGraphEdge] = []
        entry_node_id: Optional[str] = None

        # Create nodes for segments
        for segment in theme.segments:
            node_label = (
                segment.title_ar if language == "ar"
                else segment.title_en or segment.title_ar
            )
            if not node_label:
                node_label = segment.verse_reference

            node = ThemeGraphNode(
                id=segment.id,
                type="segment",
                label=node_label or segment.verse_reference,
                label_ar=segment.title_ar or segment.verse_reference,
                data={
                    "sura_no": segment.sura_no,
                    "ayah_start": segment.ayah_start,
                    "ayah_end": segment.ayah_end,
                    "verse_reference": segment.verse_reference,
                    "revelation_context": segment.revelation_context,
                    "is_entry_point": segment.is_entry_point,
                    "is_verified": segment.is_verified,
                    "segment_order": segment.segment_order,
                    "chronological_index": segment.chronological_index,
                    "semantic_tags": segment.semantic_tags or [],
                }
            )
            nodes.append(node)

            if segment.is_entry_point and not entry_node_id:
                entry_node_id = segment.id

        # Get connections
        connections = await self._get_theme_connections(theme_id)

        for conn in connections:
            edge_label = (
                conn.explanation_ar if language == "ar"
                else conn.explanation_en or conn.explanation_ar
            )
            edge_type_label = EDGE_TYPE_TRANSLATIONS.get(conn.edge_type, {})

            edge = ThemeGraphEdge(
                source=conn.source_segment_id,
                target=conn.target_segment_id,
                type=conn.edge_type,
                label=edge_label or edge_type_label.get("en", conn.edge_type),
                label_ar=edge_type_label.get("ar", conn.edge_type),
                is_sequential=conn.is_sequential or False,
                strength=conn.strength or 0.5,
                data={
                    "has_evidence": bool(conn.evidence_chunk_ids),
                }
            )
            edges.append(edge)

        # Validate DAG for sequential edges
        is_valid_dag = self._validate_sequential_dag(edges)

        # Compute layout positions
        nodes = self._compute_layout(nodes, edges, layout_mode)

        # If no entry node found, use first segment
        if not entry_node_id and nodes:
            entry_node_id = nodes[0].id

        return ThemeGraph(
            theme_id=theme_id,
            theme_title_ar=theme.title_ar,
            theme_title_en=theme.title_en,
            nodes=nodes,
            edges=edges,
            entry_node_id=entry_node_id,
            is_valid_dag=is_valid_dag,
            layout_mode=layout_mode,
            total_segments=len(nodes),
            total_connections=len(edges),
        )

    async def _get_theme_with_segments(
        self,
        theme_id: str
    ) -> Optional[QuranicTheme]:
        """Get theme with segments loaded."""
        query = (
            select(QuranicTheme)
            .where(QuranicTheme.id == theme_id)
            .options(selectinload(QuranicTheme.segments))
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_theme_connections(
        self,
        theme_id: str
    ) -> List[ThemeConnection]:
        """Get all connections for segments in a theme."""
        # Get segment IDs for this theme
        segment_ids_query = (
            select(ThemeSegment.id)
            .where(ThemeSegment.theme_id == theme_id)
        )

        # Get connections where source is in this theme
        query = (
            select(ThemeConnection)
            .where(ThemeConnection.source_segment_id.in_(segment_ids_query))
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    def _validate_sequential_dag(self, edges: List[ThemeGraphEdge]) -> bool:
        """
        Validate that sequential edges form a valid DAG (no cycles).

        Uses DFS-based cycle detection.
        """
        # Build adjacency list for sequential edges only
        adj: Dict[str, List[str]] = defaultdict(list)
        nodes: Set[str] = set()

        for edge in edges:
            if edge.is_sequential:
                adj[edge.source].append(edge.target)
                nodes.add(edge.source)
                nodes.add(edge.target)

        if not nodes:
            return True  # No sequential edges, trivially valid

        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node: WHITE for node in nodes}

        def has_cycle(node: str) -> bool:
            color[node] = GRAY

            for neighbor in adj[node]:
                if neighbor not in color:
                    color[neighbor] = WHITE

                if color[neighbor] == GRAY:
                    return True  # Back edge = cycle
                if color[neighbor] == WHITE and has_cycle(neighbor):
                    return True

            color[node] = BLACK
            return False

        for node in nodes:
            if color[node] == WHITE:
                if has_cycle(node):
                    return False

        return True

    def _compute_layout(
        self,
        nodes: List[ThemeGraphNode],
        edges: List[ThemeGraphEdge],
        layout_mode: str
    ) -> List[ThemeGraphNode]:
        """Compute x,y positions for nodes based on layout mode."""
        if not nodes:
            return nodes

        if layout_mode == "sequential":
            # Vertical timeline based on segment_order
            sorted_nodes = sorted(
                nodes,
                key=lambda n: n.data.get("segment_order", 0)
            )
            for i, node in enumerate(sorted_nodes):
                node.x = 0
                node.y = i * 100

        elif layout_mode == "revelation":
            # Group by revelation context (Makki left, Madani right)
            makki_nodes = [n for n in nodes if n.data.get("revelation_context") == "makki"]
            madani_nodes = [n for n in nodes if n.data.get("revelation_context") == "madani"]
            other_nodes = [n for n in nodes if n.data.get("revelation_context") not in ("makki", "madani")]

            for i, node in enumerate(makki_nodes):
                node.x = 0
                node.y = i * 100

            for i, node in enumerate(madani_nodes):
                node.x = 300
                node.y = i * 100

            for i, node in enumerate(other_nodes):
                node.x = 150
                node.y = (len(makki_nodes) + i) * 100

        elif layout_mode == "thematic":
            # Cluster by semantic tags
            # For now, use simple grid layout
            cols = 3
            for i, node in enumerate(nodes):
                node.x = (i % cols) * 200
                node.y = (i // cols) * 100

        else:
            # Default: simple vertical
            for i, node in enumerate(nodes):
                node.x = 0
                node.y = i * 100

        return nodes

    # =========================================================================
    # TIMELINE
    # =========================================================================

    async def get_theme_timeline(
        self,
        theme_id: str,
        language: str = "en",
        order_by: str = "segment_order",  # or "chronological", "revelation"
    ) -> List[TimelineNode]:
        """
        Get linear timeline view of theme segments.

        Args:
            theme_id: Theme ID
            language: Language for sorting/display
            order_by: Ordering method

        Returns:
            List of timeline nodes in order
        """
        query = (
            select(ThemeSegment)
            .where(ThemeSegment.theme_id == theme_id)
        )

        # Determine ordering
        if order_by == "chronological":
            query = query.order_by(
                ThemeSegment.chronological_index.nullslast(),
                ThemeSegment.segment_order
            )
        elif order_by == "revelation":
            # Makki first, then Madani, within each by segment_order
            query = query.order_by(
                ThemeSegment.revelation_context.desc(),  # makki < madani alphabetically, so desc
                ThemeSegment.segment_order
            )
        else:  # segment_order
            query = query.order_by(ThemeSegment.segment_order)

        result = await self.session.execute(query)
        segments = result.scalars().all()

        return [
            TimelineNode(
                segment_id=s.id,
                segment_order=s.segment_order,
                chronological_index=s.chronological_index,
                sura_no=s.sura_no,
                ayah_start=s.ayah_start,
                ayah_end=s.ayah_end,
                verse_reference=s.verse_reference,
                title_ar=s.title_ar,
                title_en=s.title_en,
                summary_ar=s.summary_ar,
                summary_en=s.summary_en,
                revelation_context=s.revelation_context,
                is_entry_point=s.is_entry_point or False,
                is_verified=s.is_verified or False,
            )
            for s in segments
        ]

    # =========================================================================
    # CROSS-THEME CONNECTIONS
    # =========================================================================

    async def get_cross_theme_connections(
        self,
        theme_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get connections to other themes.

        Finds themes that share:
        - Related theme IDs
        - Overlapping verse ranges
        - Common semantic tags
        """
        # Get the theme
        theme_query = select(QuranicTheme).where(QuranicTheme.id == theme_id)
        result = await self.session.execute(theme_query)
        theme = result.scalar_one_or_none()

        if not theme:
            return []

        connections = []

        # 1. Related themes from related_theme_ids
        if theme.related_theme_ids:
            related_query = (
                select(QuranicTheme)
                .where(QuranicTheme.id.in_(theme.related_theme_ids))
            )
            related_result = await self.session.execute(related_query)
            related_themes = related_result.scalars().all()

            for rt in related_themes:
                connections.append({
                    "connection_type": "related",
                    "theme_id": rt.id,
                    "theme_title_ar": rt.title_ar,
                    "theme_title_en": rt.title_en,
                    "category": rt.category,
                    "strength": 0.9,
                })

        # 2. Themes in same category (siblings)
        sibling_query = (
            select(QuranicTheme)
            .where(
                and_(
                    QuranicTheme.category == theme.category,
                    QuranicTheme.id != theme.id,
                    QuranicTheme.parent_theme_id == theme.parent_theme_id,
                )
            )
            .limit(5)
        )
        sibling_result = await self.session.execute(sibling_query)
        siblings = sibling_result.scalars().all()

        for sib in siblings:
            if not any(c["theme_id"] == sib.id for c in connections):
                connections.append({
                    "connection_type": "sibling",
                    "theme_id": sib.id,
                    "theme_title_ar": sib.title_ar,
                    "theme_title_en": sib.title_en,
                    "category": sib.category,
                    "strength": 0.7,
                })

        # 3. Themes with overlapping suras
        if theme.suras_mentioned:
            overlap_query = (
                select(QuranicTheme)
                .where(
                    and_(
                        QuranicTheme.id != theme.id,
                        QuranicTheme.suras_mentioned.overlap(theme.suras_mentioned),
                    )
                )
                .limit(5)
            )
            overlap_result = await self.session.execute(overlap_query)
            overlapping = overlap_result.scalars().all()

            for ov in overlapping:
                if not any(c["theme_id"] == ov.id for c in connections):
                    # Calculate overlap strength
                    if ov.suras_mentioned:
                        shared = set(theme.suras_mentioned) & set(ov.suras_mentioned)
                        strength = len(shared) / max(
                            len(theme.suras_mentioned),
                            len(ov.suras_mentioned)
                        )
                    else:
                        strength = 0.3

                    connections.append({
                        "connection_type": "sura_overlap",
                        "theme_id": ov.id,
                        "theme_title_ar": ov.title_ar,
                        "theme_title_en": ov.title_en,
                        "category": ov.category,
                        "strength": strength,
                    })

        # Sort by strength
        connections.sort(key=lambda x: x["strength"], reverse=True)

        return connections[:10]  # Limit to top 10
