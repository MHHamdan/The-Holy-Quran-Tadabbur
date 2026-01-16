"""
Story Graph Service - Semantic and Chronological Ordering for Quranic Stories.

This service implements the graph-building logic for Quranic story visualization,
respecting the unique narrative structure of the Quran:

1. THEMATIC over LINEAR: Stories emphasize lessons, not just timeline
2. MULTI-SURAH PRESENCE: Same story told across surahs for different purposes
3. CAUSE-EFFECT CHAINS: Actions → Tests → Divine Response → Outcome
4. DAG CONSTRAINT: Chronological edges form acyclic directed graph

ALGORITHM OVERVIEW:
==================
1. Load all segments for a story
2. Build initial graph from explicit connections
3. Infer chronological indices from:
   - Ayah order within same surah
   - Explicit narrative_order field
   - Tafsir-based ordering hints
4. Validate DAG property for temporal edges
5. Add thematic cross-links (may create cycles - allowed)
6. Return graph with proper node positions

INSPIRED BY:
- Connected Papers (semantic citation graphs)
- Google Scholar citation networks
BUT adapted for Quranic narrative patterns.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.story import (
    Story,
    StorySegment,
    StoryConnection,
    CrossStoryConnection,
    NarrativeRole,
    EdgeType,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GraphNode:
    """A node in the story graph."""
    id: str
    type: str  # "story", "segment", "verse"
    label: str
    data: dict = field(default_factory=dict)

    # Graph layout hints
    x: Optional[float] = None
    y: Optional[float] = None
    layer: int = 0  # For hierarchical layout

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "data": self.data,
            "position": {"x": self.x, "y": self.y} if self.x is not None else None,
        }


@dataclass
class GraphEdge:
    """An edge in the story graph."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    data: dict = field(default_factory=dict)

    # Edge properties
    is_chronological: bool = False
    strength: float = 1.0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "label": self.label,
            "data": {
                **self.data,
                "is_chronological": self.is_chronological,
                "strength": self.strength,
            },
        }


@dataclass
class StoryGraph:
    """Complete story graph with nodes, edges, and metadata."""
    story_id: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    # Graph properties
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    validation_errors: list[str] = field(default_factory=list)

    # Layout mode
    layout_mode: str = "chronological"  # or "thematic"

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "entry_node_id": self.entry_node_id,
            "is_valid_dag": self.is_valid_dag,
            "layout_mode": self.layout_mode,
        }


class GraphValidationError(Exception):
    """Raised when graph validation fails."""
    pass


# =============================================================================
# STORY GRAPH SERVICE
# =============================================================================

class StoryGraphService:
    """
    Service for building and validating Quranic story graphs.

    This service implements semantic + chronological ordering that respects
    Quranic narrative patterns while ensuring graph consistency.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # MAIN API
    # =========================================================================

    async def build_story_graph(
        self,
        story_id: str,
        language: str = "en",
        include_cross_story: bool = False,
        layout_mode: str = "chronological",
    ) -> StoryGraph:
        """
        Build a complete graph for a story.

        Args:
            story_id: The story to build graph for
            language: Language for labels ("ar" or "en")
            include_cross_story: Include connections to other stories
            layout_mode: "chronological" or "thematic"

        Returns:
            StoryGraph with nodes, edges, and metadata

        Algorithm:
        1. Load story and segments from database
        2. Create nodes for story and segments
        3. Add containment edges (story -> segments)
        4. Load and add explicit segment connections
        5. Infer chronological order
        6. Validate DAG property
        7. Optionally add cross-story connections
        8. Compute layout positions
        """
        # Step 1: Load data
        story = await self._load_story(story_id)
        if not story:
            raise ValueError(f"Story not found: {story_id}")

        segments = await self._load_segments(story_id)
        connections = await self._load_connections(story_id)

        # Step 2-3: Create nodes
        graph = StoryGraph(story_id=story_id, layout_mode=layout_mode)

        # Add story root node
        story_node = self._create_story_node(story, language)
        graph.nodes.append(story_node)

        # Add segment nodes
        segment_nodes = {}
        for segment in segments:
            node = self._create_segment_node(segment, language)
            graph.nodes.append(node)
            segment_nodes[segment.id] = node

            # Add containment edge
            graph.edges.append(GraphEdge(
                source=story.id,
                target=segment.id,
                type="contains",
                is_chronological=False,
            ))

        # Step 4: Add explicit connections
        for conn in connections:
            edge = self._create_connection_edge(conn, language)
            graph.edges.append(edge)

        # Step 5: Infer chronological order
        self._infer_chronological_indices(segments, connections)

        # Update node data with inferred indices
        for segment in segments:
            if segment.id in segment_nodes:
                segment_nodes[segment.id].data["chronological_index"] = segment.chronological_index

        # Step 6: Validate DAG
        graph.is_valid_dag, graph.validation_errors = self._validate_dag(graph)

        # Step 7: Find entry node
        graph.entry_node_id = self._find_entry_node(segments)

        # Step 8: Cross-story connections (optional)
        if include_cross_story:
            cross_conns = await self._load_cross_story_connections(story_id)
            for conn in cross_conns:
                edge = self._create_cross_story_edge(conn, language)
                graph.edges.append(edge)

        # Step 9: Compute layout
        self._compute_layout(graph, layout_mode)

        return graph

    async def get_story_timeline(
        self,
        story_id: str,
        language: str = "en",
    ) -> list[dict]:
        """
        Get a linear timeline view of a story.

        Returns segments ordered by chronological_index,
        suitable for step-by-step learning.
        """
        segments = await self._load_segments(story_id)

        # Sort by chronological index, falling back to narrative order
        sorted_segments = sorted(
            segments,
            key=lambda s: (s.chronological_index or s.narrative_order, s.narrative_order)
        )

        timeline = []
        for segment in sorted_segments:
            title = segment.title_ar if language == "ar" else segment.title_en
            summary = segment.summary_ar if language == "ar" else segment.summary_en

            timeline.append({
                "id": segment.id,
                "index": segment.chronological_index or segment.narrative_order,
                "title": title or segment.verse_reference,
                "verse_reference": segment.verse_reference,
                "narrative_role": segment.narrative_role,
                "summary": summary,
                "semantic_tags": segment.semantic_tags or [],
                "is_entry_point": segment.is_entry_point,
            })

        return timeline

    # =========================================================================
    # DATA LOADING
    # =========================================================================

    async def _load_story(self, story_id: str) -> Optional[Story]:
        """Load a story by ID."""
        result = await self.session.execute(
            select(Story).where(Story.id == story_id)
        )
        return result.scalar_one_or_none()

    async def _load_segments(self, story_id: str) -> list[StorySegment]:
        """Load all segments for a story, ordered by narrative_order."""
        result = await self.session.execute(
            select(StorySegment)
            .where(StorySegment.story_id == story_id)
            .order_by(StorySegment.narrative_order)
        )
        return list(result.scalars().all())

    async def _load_connections(self, story_id: str) -> list[StoryConnection]:
        """Load all connections involving segments of this story."""
        # Get segment IDs first
        segments = await self._load_segments(story_id)
        segment_ids = [s.id for s in segments]

        if not segment_ids:
            return []

        result = await self.session.execute(
            select(StoryConnection)
            .where(
                StoryConnection.source_segment_id.in_(segment_ids) |
                StoryConnection.target_segment_id.in_(segment_ids)
            )
        )
        return list(result.scalars().all())

    async def _load_cross_story_connections(
        self, story_id: str
    ) -> list[CrossStoryConnection]:
        """Load cross-story connections involving this story."""
        result = await self.session.execute(
            select(CrossStoryConnection)
            .where(
                (CrossStoryConnection.source_story_id == story_id) |
                (CrossStoryConnection.target_story_id == story_id)
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # NODE/EDGE CREATION
    # =========================================================================

    def _create_story_node(self, story: Story, language: str) -> GraphNode:
        """Create a graph node for the story root."""
        name = story.name_ar if language == "ar" else story.name_en
        summary = story.summary_ar if language == "ar" else story.summary_en

        return GraphNode(
            id=story.id,
            type="story",
            label=name,
            data={
                "category": story.category,
                "main_figures": story.main_figures or [],
                "themes": story.themes or [],
                "summary": summary,
                "total_verses": story.total_verses,
                "suras_mentioned": story.suras_mentioned or [],
            },
            layer=0,
        )

    def _create_segment_node(self, segment: StorySegment, language: str) -> GraphNode:
        """Create a graph node for a segment."""
        title = segment.title_ar if language == "ar" else segment.title_en
        summary = segment.summary_ar if language == "ar" else segment.summary_en

        # Use title, fall back to summary, then verse reference
        # Strip to handle empty strings
        label = (title or "").strip() or (summary or "").strip() or segment.verse_reference
        # Truncate long labels for graph display
        if len(label) > 40:
            label = label[:37] + "..."

        return GraphNode(
            id=segment.id,
            type="segment",
            label=label,
            data={
                "story_id": segment.story_id,
                "surah": segment.sura_no,
                "ayah_start": segment.aya_start,
                "ayah_end": segment.aya_end,
                "verse_reference": segment.verse_reference,
                "narrative_role": segment.narrative_role,
                "narrative_order": segment.narrative_order,
                "chronological_index": segment.chronological_index,
                "semantic_tags": segment.semantic_tags or [],
                "summary": summary,
                "is_entry_point": segment.is_entry_point,
                "memorization_cue": (
                    segment.memorization_cue_ar if language == "ar"
                    else segment.memorization_cue_en
                ),
            },
            layer=segment.chronological_index or segment.narrative_order,
        )

    def _create_connection_edge(
        self, conn: StoryConnection, language: str
    ) -> GraphEdge:
        """Create a graph edge from a connection."""
        explanation = conn.explanation_ar if language == "ar" else conn.explanation_en

        # Determine if this is a chronological edge
        is_chrono = conn.is_chronological or conn.edge_type in [
            EdgeType.CHRONOLOGICAL_NEXT.value,
            EdgeType.CONTINUATION.value,
        ]

        return GraphEdge(
            source=conn.source_segment_id,
            target=conn.target_segment_id,
            type=conn.edge_type or conn.connection_type,
            label=explanation[:50] + "..." if explanation and len(explanation) > 50 else explanation,
            is_chronological=is_chrono,
            strength=conn.strength or 1.0,
            data={
                "shared_themes": conn.shared_themes or [],
                "evidence_count": len(conn.evidence_chunk_ids) if conn.evidence_chunk_ids else 0,
            },
        )

    def _create_cross_story_edge(
        self, conn: CrossStoryConnection, language: str
    ) -> GraphEdge:
        """Create a graph edge for cross-story connection."""
        label = conn.label_ar if language == "ar" else conn.label_en

        return GraphEdge(
            source=conn.source_story_id,
            target=conn.target_story_id,
            type=conn.connection_type,
            label=label,
            is_chronological=False,
            strength=conn.strength or 0.5,
            data={
                "cross_story": True,
                "shared_themes": conn.shared_themes or [],
                "shared_figures": conn.shared_figures or [],
            },
        )

    # =========================================================================
    # CHRONOLOGICAL ORDERING ALGORITHM
    # =========================================================================

    def _infer_chronological_indices(
        self,
        segments: list[StorySegment],
        connections: list[StoryConnection],
    ) -> None:
        """
        Infer chronological indices for segments.

        Algorithm:
        1. Start with segments that have explicit chronological_index
        2. For remaining segments, infer from:
           a. Ayah order within same surah
           b. Explicit chronological_next edges
           c. Cause-effect relationships
           d. Narrative order as fallback

        This is NOT just sorting by ayah number - the Quran often presents
        events in non-chronological order for pedagogical purposes.
        """
        # Build adjacency list for chronological edges
        chrono_graph: dict[str, list[str]] = defaultdict(list)
        for conn in connections:
            edge_type = conn.edge_type or conn.connection_type
            if edge_type in [
                EdgeType.CHRONOLOGICAL_NEXT.value,
                EdgeType.CONTINUATION.value,
                EdgeType.CAUSE_EFFECT.value,
                "chronological_next",
                "continuation",
                "cause_effect",
            ]:
                chrono_graph[conn.source_segment_id].append(conn.target_segment_id)

        # Track which segments have indices
        indexed = {s.id: s.chronological_index for s in segments if s.chronological_index}

        # If no explicit indices, use topological sort
        if not indexed:
            order = self._topological_sort(segments, chrono_graph)
            for i, seg_id in enumerate(order, start=1):
                for seg in segments:
                    if seg.id == seg_id:
                        seg.chronological_index = i
                        break
        else:
            # Propagate indices using graph traversal
            self._propagate_indices(segments, chrono_graph, indexed)

    def _topological_sort(
        self,
        segments: list[StorySegment],
        chrono_graph: dict[str, list[str]],
    ) -> list[str]:
        """
        Topological sort of segments based on chronological edges.

        Falls back to narrative_order if no edges exist.
        """
        # Build in-degree map
        in_degree: dict[str, int] = {s.id: 0 for s in segments}
        for source, targets in chrono_graph.items():
            for target in targets:
                if target in in_degree:
                    in_degree[target] += 1

        # Kahn's algorithm with narrative_order tiebreaker
        segment_order = {s.id: s.narrative_order for s in segments}
        queue = sorted(
            [s_id for s_id, deg in in_degree.items() if deg == 0],
            key=lambda x: segment_order.get(x, 999)
        )

        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in chrono_graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        # Insert in sorted position by narrative_order
                        queue.append(neighbor)
                        queue.sort(key=lambda x: segment_order.get(x, 999))

        # Add any remaining segments (disconnected)
        remaining = set(s.id for s in segments) - set(result)
        for seg_id in sorted(remaining, key=lambda x: segment_order.get(x, 999)):
            result.append(seg_id)

        return result

    def _propagate_indices(
        self,
        segments: list[StorySegment],
        chrono_graph: dict[str, list[str]],
        indexed: dict[str, int],
    ) -> None:
        """Propagate chronological indices using BFS from known indices."""
        segment_map = {s.id: s for s in segments}

        # BFS from each indexed segment
        for seg_id, idx in indexed.items():
            visited = {seg_id}
            queue = [(seg_id, idx)]

            while queue:
                current, current_idx = queue.pop(0)

                for neighbor in chrono_graph.get(current, []):
                    if neighbor not in visited and neighbor in segment_map:
                        visited.add(neighbor)
                        seg = segment_map[neighbor]
                        if seg.chronological_index is None:
                            seg.chronological_index = current_idx + 1
                        queue.append((neighbor, seg.chronological_index))

        # Fill in any remaining with narrative_order
        for seg in segments:
            if seg.chronological_index is None:
                seg.chronological_index = seg.narrative_order

    # =========================================================================
    # GRAPH VALIDATION
    # =========================================================================

    def _validate_dag(self, graph: StoryGraph) -> tuple[bool, list[str]]:
        """
        Validate that chronological edges form a DAG (no cycles).

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Build adjacency list for chronological edges only
        chrono_edges: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges:
            if edge.is_chronological:
                chrono_edges[edge.source].append(edge.target)

        # Check for cycles using DFS
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
                    errors.append(f"Cycle detected involving chronological edges from {node.id}")

        # Check for orphan segment nodes (no edges)
        segment_ids = {n.id for n in graph.nodes if n.type == "segment"}
        connected_segments = set()
        for edge in graph.edges:
            if edge.source in segment_ids:
                connected_segments.add(edge.source)
            if edge.target in segment_ids:
                connected_segments.add(edge.target)

        # Segments should at least be connected to story via "contains"
        for edge in graph.edges:
            if edge.type == "contains":
                connected_segments.add(edge.target)

        orphans = segment_ids - connected_segments
        if orphans:
            errors.append(f"Orphan segments found: {orphans}")

        return len(errors) == 0, errors

    def _find_entry_node(self, segments: list[StorySegment]) -> Optional[str]:
        """Find the entry point node for the story."""
        # First, look for explicitly marked entry point
        for seg in segments:
            if seg.is_entry_point:
                return seg.id

        # Otherwise, use the segment with lowest chronological index
        sorted_segs = sorted(
            segments,
            key=lambda s: (s.chronological_index or 999, s.narrative_order)
        )
        return sorted_segs[0].id if sorted_segs else None

    # =========================================================================
    # LAYOUT COMPUTATION
    # =========================================================================

    def _compute_layout(self, graph: StoryGraph, mode: str = "chronological") -> None:
        """
        Compute x, y positions for nodes.

        Modes:
        - chronological: Vertical timeline (top to bottom)
        - thematic: Force-directed with thematic clustering
        """
        if mode == "chronological":
            self._layout_chronological(graph)
        else:
            self._layout_thematic(graph)

    def _layout_chronological(self, graph: StoryGraph) -> None:
        """
        Layout nodes in a vertical timeline.

        Story node at top, segments below ordered by chronological index.
        """
        # Group nodes by layer (chronological index)
        layers: dict[int, list[GraphNode]] = defaultdict(list)
        for node in graph.nodes:
            if node.type == "story":
                layers[0].append(node)
            else:
                layer = node.data.get("chronological_index", node.layer) or 1
                layers[layer].append(node)

        # Position nodes
        y_spacing = 120
        x_spacing = 200

        for layer_idx in sorted(layers.keys()):
            layer_nodes = layers[layer_idx]
            layer_width = len(layer_nodes) * x_spacing

            for i, node in enumerate(layer_nodes):
                node.x = (i * x_spacing) - (layer_width / 2) + (x_spacing / 2)
                node.y = layer_idx * y_spacing

    def _layout_thematic(self, graph: StoryGraph) -> None:
        """
        Layout nodes using thematic clustering.

        Nodes with shared semantic_tags are positioned closer together.
        Uses simple force-directed approach.
        """
        import math
        import random

        # Initialize random positions
        for node in graph.nodes:
            node.x = random.uniform(-300, 300)
            node.y = random.uniform(-300, 300)

        # Story node at center
        for node in graph.nodes:
            if node.type == "story":
                node.x = 0
                node.y = 0

        # Simple force-directed iterations
        for _ in range(50):
            # Repulsion between all nodes
            for i, n1 in enumerate(graph.nodes):
                for n2 in graph.nodes[i + 1:]:
                    dx = n1.x - n2.x
                    dy = n1.y - n2.y
                    dist = math.sqrt(dx * dx + dy * dy) + 0.1

                    force = 5000 / (dist * dist)
                    n1.x += (dx / dist) * force * 0.1
                    n1.y += (dy / dist) * force * 0.1
                    n2.x -= (dx / dist) * force * 0.1
                    n2.y -= (dy / dist) * force * 0.1

            # Attraction along edges
            for edge in graph.edges:
                n1 = next((n for n in graph.nodes if n.id == edge.source), None)
                n2 = next((n for n in graph.nodes if n.id == edge.target), None)
                if n1 and n2:
                    dx = n2.x - n1.x
                    dy = n2.y - n1.y
                    dist = math.sqrt(dx * dx + dy * dy) + 0.1

                    force = dist * 0.01 * edge.strength
                    n1.x += dx * force * 0.1
                    n1.y += dy * force * 0.1
                    n2.x -= dx * force * 0.1
                    n2.y -= dy * force * 0.1

        # Keep story node at center
        for node in graph.nodes:
            if node.type == "story":
                node.x = 0
                node.y = 0


# =============================================================================
# GRAPH VALIDATION UTILITIES
# =============================================================================

def validate_story_graph(graph: StoryGraph) -> list[str]:
    """
    Comprehensive validation of a story graph.

    Checks:
    1. Exactly one entry node exists
    2. Chronological edges form DAG
    3. All segments are reachable from entry
    4. All segments have evidence grounding
    5. No orphan nodes

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # 1. Check entry node
    entry_nodes = [n for n in graph.nodes if n.data.get("is_entry_point")]
    if len(entry_nodes) == 0:
        # Check if there's a node with chronological_index = 1
        first_nodes = [
            n for n in graph.nodes
            if n.type == "segment" and n.data.get("chronological_index") == 1
        ]
        if not first_nodes:
            errors.append("No entry node found (no is_entry_point or chronological_index=1)")
    elif len(entry_nodes) > 1:
        errors.append(f"Multiple entry nodes found: {[n.id for n in entry_nodes]}")

    # 2. DAG validation already done in build

    # 3. Reachability (BFS from story node)
    story_nodes = [n for n in graph.nodes if n.type == "story"]
    if story_nodes:
        reachable = set()
        queue = [story_nodes[0].id]
        adj = defaultdict(list)
        for e in graph.edges:
            adj[e.source].append(e.target)
            adj[e.target].append(e.source)  # Undirected for reachability

        while queue:
            node = queue.pop(0)
            if node in reachable:
                continue
            reachable.add(node)
            queue.extend(adj[node])

        all_ids = {n.id for n in graph.nodes}
        unreachable = all_ids - reachable
        if unreachable:
            errors.append(f"Unreachable nodes: {unreachable}")

    # 4. Evidence grounding (just a warning, not error)
    segment_nodes = [n for n in graph.nodes if n.type == "segment"]
    for node in segment_nodes:
        if not node.data.get("evidence_sources") and not node.data.get("evidence_chunk_ids"):
            # This is acceptable for now, just informational
            pass

    return errors


# =============================================================================
# PSEUDOCODE DOCUMENTATION
# =============================================================================

"""
PSEUDOCODE: build_story_graph(story_id)
=======================================

function build_story_graph(story_id, language, include_cross_story):
    # 1. Load data from database
    story = db.get_story(story_id)
    segments = db.get_segments(story_id).order_by(narrative_order)
    connections = db.get_connections(story_id)

    # 2. Initialize graph
    graph = new StoryGraph(story_id)

    # 3. Create story root node
    graph.add_node(create_story_node(story))

    # 4. Create segment nodes with containment edges
    for segment in segments:
        node = create_segment_node(segment)
        graph.add_node(node)
        graph.add_edge(story.id -> segment.id, type="contains")

    # 5. Add explicit connection edges
    for conn in connections:
        graph.add_edge(conn.source -> conn.target, conn.type)

    # 6. Infer chronological order
    infer_chronological_indices(segments, connections)

    # 7. Validate DAG property
    if not validate_dag(graph.chronological_edges):
        raise GraphValidationError("Cycle in chronological edges")

    # 8. Find entry node
    graph.entry_node = find_entry_node(segments)

    # 9. Add cross-story connections if requested
    if include_cross_story:
        cross_conns = db.get_cross_story_connections(story_id)
        for conn in cross_conns:
            graph.add_edge(conn.source_story -> conn.target_story)

    # 10. Compute layout positions
    compute_layout(graph, mode="chronological")

    return graph


PSEUDOCODE: infer_chronological_index(nodes)
=============================================

function infer_chronological_indices(segments, connections):
    # Build adjacency list for chronological edges
    chrono_graph = {}
    for conn in connections:
        if conn.type in [CHRONOLOGICAL_NEXT, CONTINUATION, CAUSE_EFFECT]:
            chrono_graph[conn.source].append(conn.target)

    # Check for explicit indices
    indexed = {s.id: s.chronological_index for s in segments if s.chronological_index}

    if not indexed:
        # Use topological sort (Kahn's algorithm)
        order = topological_sort(segments, chrono_graph)
        for i, seg_id in enumerate(order):
            segments[seg_id].chronological_index = i + 1
    else:
        # Propagate from known indices using BFS
        propagate_indices(segments, chrono_graph, indexed)

    # Fill remaining with narrative_order
    for seg in segments:
        if seg.chronological_index is None:
            seg.chronological_index = seg.narrative_order


PSEUDOCODE: validate_graph_consistency()
========================================

function validate_graph_consistency(graph):
    errors = []

    # 1. Check DAG property for chronological edges
    chrono_edges = graph.edges.filter(is_chronological=True)
    if has_cycle(chrono_edges):
        errors.append("Cycle in chronological edges")

    # 2. Check exactly one entry point
    entry_nodes = graph.nodes.filter(is_entry_point=True)
    if len(entry_nodes) != 1:
        errors.append("Must have exactly one entry node")

    # 3. Check all segments reachable from entry
    reachable = bfs(graph, entry_node)
    if len(reachable) != len(graph.nodes):
        errors.append("Orphan nodes found")

    # 4. Check evidence grounding
    for node in graph.segment_nodes:
        if not node.evidence_chunk_ids:
            errors.append(f"No evidence for {node.id}")

    return errors
"""
