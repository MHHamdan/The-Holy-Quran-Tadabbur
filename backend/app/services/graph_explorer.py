"""
Graph Exploration Service.

Provides advanced graph traversal and pathfinding capabilities:
- BFS (Breadth-First Search) for shortest paths
- DFS (Depth-First Search) for deep exploration
- Path finding between entities
- Subgraph extraction
- Relationship strength calculation

Arabic: خدمة استكشاف الرسم البياني
"""
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from app.kg.client import get_kg_client, KGClient

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    STORY = "story_cluster"
    EVENT = "story_event"
    PERSON = "person"
    CONCEPT = "concept"
    THEME = "concept_tag"
    PLACE = "place"
    AYAH = "ayah"


class EdgeType(str, Enum):
    """Types of edges in the knowledge graph."""
    NEXT = "next"                    # Chronological flow
    HAS_EVENT = "has_event"          # Story cluster contains events
    THEMATIC_LINK = "thematic_link"  # Theme connection
    EXPLAINS = "explains"            # Tafseer explains ayah
    INVOLVES = "involves"            # Event involves person
    LOCATED_IN = "located_in"        # Event in place
    TAGGED_WITH = "tagged_with"      # Entity tagged with concept
    SIMILAR_TO = "similar_to"        # Semantic similarity
    PART_OF = "part_of"              # Part of larger entity
    RELATES_TO = "relates_to"        # General relationship


@dataclass
class GraphNode:
    """Node in the exploration result."""
    id: str
    type: str
    label: str
    label_ar: str
    data: Dict[str, Any] = field(default_factory=dict)
    depth: int = 0
    weight: float = 1.0


@dataclass
class GraphEdge:
    """Edge in the exploration result."""
    source: str
    target: str
    type: str
    label: str = ""
    weight: float = 1.0
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphPath:
    """A path between two nodes."""
    start: str
    end: str
    nodes: List[str]
    edges: List[Dict[str, Any]]
    length: int
    total_weight: float


@dataclass
class ExplorationResult:
    """Result of graph exploration."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    paths: List[GraphPath] = field(default_factory=list)
    center_node: Optional[str] = None
    max_depth: int = 0
    total_nodes: int = 0
    total_edges: int = 0


class GraphExplorer:
    """
    Advanced graph exploration service.

    Provides BFS, DFS, and pathfinding capabilities
    for the Quranic knowledge graph.
    """

    # Default edge types to follow during traversal
    DEFAULT_EDGE_TYPES = [
        EdgeType.HAS_EVENT,
        EdgeType.NEXT,
        EdgeType.INVOLVES,
        EdgeType.THEMATIC_LINK,
        EdgeType.TAGGED_WITH,
        EdgeType.SIMILAR_TO,
        EdgeType.RELATES_TO,
    ]

    def __init__(self, kg_client: KGClient = None):
        self.kg = kg_client or get_kg_client()

    async def bfs_explore(
        self,
        start_id: str,
        max_depth: int = 3,
        edge_types: List[str] = None,
        max_nodes: int = 100,
        language: str = "ar",
    ) -> ExplorationResult:
        """
        Breadth-first exploration from a starting node.

        Returns all reachable nodes within max_depth hops,
        ordered by distance from start.

        Args:
            start_id: Starting node ID
            max_depth: Maximum traversal depth
            edge_types: Edge types to follow (None = all)
            max_nodes: Maximum nodes to return
            language: Response language (ar/en)

        Returns:
            ExplorationResult with nodes and edges
        """
        visited: Set[str] = set()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Queue: (node_id, depth)
        queue = deque([(start_id, 0)])
        visited.add(start_id)

        edge_filter = edge_types or [e.value for e in self.DEFAULT_EDGE_TYPES]

        while queue and len(nodes) < max_nodes:
            current_id, depth = queue.popleft()

            if depth > max_depth:
                continue

            # Get current node data
            node_data = await self.kg.get(current_id)
            if node_data:
                node = self._create_node(node_data, depth, language)
                nodes.append(node)

            if depth < max_depth:
                # Get neighbors
                for edge_type in edge_filter:
                    # Outgoing edges
                    out_edges = await self.kg.get_edges(
                        from_id=current_id,
                        edge_type=edge_type
                    )
                    for edge in out_edges:
                        target_id = edge.get("out")
                        if target_id and target_id not in visited:
                            visited.add(target_id)
                            queue.append((target_id, depth + 1))

                            edges.append(GraphEdge(
                                source=current_id,
                                target=target_id,
                                type=edge_type,
                                weight=edge.get("strength", 1.0),
                                data=edge,
                            ))

                    # Incoming edges (bidirectional exploration)
                    in_edges = await self.kg.get_edges(
                        to_id=current_id,
                        edge_type=edge_type
                    )
                    for edge in in_edges:
                        source_id = edge.get("in")
                        if source_id and source_id not in visited:
                            visited.add(source_id)
                            queue.append((source_id, depth + 1))

                            edges.append(GraphEdge(
                                source=source_id,
                                target=current_id,
                                type=edge_type,
                                weight=edge.get("strength", 1.0),
                                data=edge,
                            ))

        return ExplorationResult(
            nodes=nodes,
            edges=edges,
            center_node=start_id,
            max_depth=max_depth,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )

    async def dfs_explore(
        self,
        start_id: str,
        max_depth: int = 5,
        edge_types: List[str] = None,
        max_nodes: int = 100,
        language: str = "ar",
    ) -> ExplorationResult:
        """
        Depth-first exploration from a starting node.

        Goes as deep as possible before backtracking.
        Good for finding complete paths through the graph.

        Args:
            start_id: Starting node ID
            max_depth: Maximum traversal depth
            edge_types: Edge types to follow
            max_nodes: Maximum nodes to return
            language: Response language

        Returns:
            ExplorationResult with nodes and edges
        """
        visited: Set[str] = set()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        edge_filter = edge_types or [e.value for e in self.DEFAULT_EDGE_TYPES]

        async def dfs_visit(node_id: str, depth: int):
            if depth > max_depth or node_id in visited or len(nodes) >= max_nodes:
                return

            visited.add(node_id)

            # Get node data
            node_data = await self.kg.get(node_id)
            if node_data:
                node = self._create_node(node_data, depth, language)
                nodes.append(node)

            # Explore neighbors depth-first
            for edge_type in edge_filter:
                out_edges = await self.kg.get_edges(
                    from_id=node_id,
                    edge_type=edge_type
                )
                for edge in out_edges:
                    target_id = edge.get("out")
                    if target_id and target_id not in visited:
                        edges.append(GraphEdge(
                            source=node_id,
                            target=target_id,
                            type=edge_type,
                            weight=edge.get("strength", 1.0),
                            data=edge,
                        ))
                        await dfs_visit(target_id, depth + 1)

        await dfs_visit(start_id, 0)

        return ExplorationResult(
            nodes=nodes,
            edges=edges,
            center_node=start_id,
            max_depth=max_depth,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )

    async def find_path(
        self,
        start_id: str,
        end_id: str,
        edge_types: List[str] = None,
        max_depth: int = 10,
    ) -> Optional[GraphPath]:
        """
        Find shortest path between two nodes using BFS.

        Args:
            start_id: Starting node ID
            end_id: Target node ID
            edge_types: Edge types to follow
            max_depth: Maximum search depth

        Returns:
            GraphPath if found, None otherwise
        """
        if start_id == end_id:
            return GraphPath(
                start=start_id,
                end=end_id,
                nodes=[start_id],
                edges=[],
                length=0,
                total_weight=0,
            )

        visited: Set[str] = set()
        # Queue: (node_id, path_nodes, path_edges, total_weight)
        queue = deque([(start_id, [start_id], [], 0.0)])
        visited.add(start_id)

        edge_filter = edge_types or [e.value for e in self.DEFAULT_EDGE_TYPES]

        while queue:
            current_id, path_nodes, path_edges, total_weight = queue.popleft()

            if len(path_nodes) > max_depth:
                continue

            # Check all edge types
            for edge_type in edge_filter:
                # Outgoing edges
                out_edges = await self.kg.get_edges(
                    from_id=current_id,
                    edge_type=edge_type
                )
                for edge in out_edges:
                    target_id = edge.get("out")
                    if not target_id:
                        continue

                    edge_weight = edge.get("strength", 1.0)
                    new_weight = total_weight + edge_weight

                    if target_id == end_id:
                        # Found the target!
                        return GraphPath(
                            start=start_id,
                            end=end_id,
                            nodes=path_nodes + [target_id],
                            edges=path_edges + [edge],
                            length=len(path_nodes),
                            total_weight=new_weight,
                        )

                    if target_id not in visited:
                        visited.add(target_id)
                        queue.append((
                            target_id,
                            path_nodes + [target_id],
                            path_edges + [edge],
                            new_weight,
                        ))

                # Incoming edges (for undirected traversal)
                in_edges = await self.kg.get_edges(
                    to_id=current_id,
                    edge_type=edge_type
                )
                for edge in in_edges:
                    source_id = edge.get("in")
                    if not source_id:
                        continue

                    edge_weight = edge.get("strength", 1.0)
                    new_weight = total_weight + edge_weight

                    if source_id == end_id:
                        return GraphPath(
                            start=start_id,
                            end=end_id,
                            nodes=path_nodes + [source_id],
                            edges=path_edges + [edge],
                            length=len(path_nodes),
                            total_weight=new_weight,
                        )

                    if source_id not in visited:
                        visited.add(source_id)
                        queue.append((
                            source_id,
                            path_nodes + [source_id],
                            path_edges + [edge],
                            new_weight,
                        ))

        return None  # No path found

    async def find_all_paths(
        self,
        start_id: str,
        end_id: str,
        edge_types: List[str] = None,
        max_depth: int = 5,
        max_paths: int = 10,
    ) -> List[GraphPath]:
        """
        Find all paths between two nodes (up to max_paths).

        Uses DFS to enumerate all possible paths.

        Args:
            start_id: Starting node ID
            end_id: Target node ID
            edge_types: Edge types to follow
            max_depth: Maximum path length
            max_paths: Maximum paths to return

        Returns:
            List of GraphPath objects
        """
        paths: List[GraphPath] = []
        edge_filter = edge_types or [e.value for e in self.DEFAULT_EDGE_TYPES]

        async def dfs_paths(
            current_id: str,
            visited: Set[str],
            path_nodes: List[str],
            path_edges: List[Dict],
            total_weight: float,
        ):
            if len(paths) >= max_paths:
                return

            if current_id == end_id:
                paths.append(GraphPath(
                    start=start_id,
                    end=end_id,
                    nodes=path_nodes.copy(),
                    edges=path_edges.copy(),
                    length=len(path_nodes) - 1,
                    total_weight=total_weight,
                ))
                return

            if len(path_nodes) > max_depth:
                return

            for edge_type in edge_filter:
                out_edges = await self.kg.get_edges(
                    from_id=current_id,
                    edge_type=edge_type
                )
                for edge in out_edges:
                    target_id = edge.get("out")
                    if target_id and target_id not in visited:
                        visited.add(target_id)
                        path_nodes.append(target_id)
                        path_edges.append(edge)

                        await dfs_paths(
                            target_id,
                            visited,
                            path_nodes,
                            path_edges,
                            total_weight + edge.get("strength", 1.0),
                        )

                        path_nodes.pop()
                        path_edges.pop()
                        visited.discard(target_id)

        await dfs_paths(start_id, {start_id}, [start_id], [], 0.0)

        # Sort by path length, then by weight
        paths.sort(key=lambda p: (p.length, -p.total_weight))

        return paths

    async def get_subgraph(
        self,
        node_ids: List[str],
        include_connections: bool = True,
        edge_types: List[str] = None,
        language: str = "ar",
    ) -> ExplorationResult:
        """
        Extract a subgraph containing the specified nodes.

        Optionally includes all edges between the nodes.

        Args:
            node_ids: List of node IDs to include
            include_connections: Whether to include edges between nodes
            edge_types: Edge types to include
            language: Response language

        Returns:
            ExplorationResult with the subgraph
        """
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        node_set = set(node_ids)

        # Get all nodes
        for node_id in node_ids:
            node_data = await self.kg.get(node_id)
            if node_data:
                nodes.append(self._create_node(node_data, 0, language))

        # Get edges between nodes
        if include_connections:
            edge_filter = edge_types or [e.value for e in EdgeType]

            for node_id in node_ids:
                for edge_type in edge_filter:
                    out_edges = await self.kg.get_edges(
                        from_id=node_id,
                        edge_type=edge_type
                    )
                    for edge in out_edges:
                        target_id = edge.get("out")
                        if target_id in node_set:
                            edges.append(GraphEdge(
                                source=node_id,
                                target=target_id,
                                type=edge_type,
                                weight=edge.get("strength", 1.0),
                                data=edge,
                            ))

        return ExplorationResult(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )

    async def get_related_entities(
        self,
        entity_id: str,
        entity_types: List[str] = None,
        limit: int = 20,
        language: str = "ar",
    ) -> List[GraphNode]:
        """
        Get entities related to a given entity.

        Finds all directly connected nodes of specified types.

        Args:
            entity_id: Source entity ID
            entity_types: Filter by entity types
            limit: Maximum results
            language: Response language

        Returns:
            List of related GraphNode objects
        """
        neighbors = await self.kg.get_neighbors(entity_id)
        related: List[GraphNode] = []
        seen: Set[str] = set()

        for direction_edge, neighbor_list in neighbors.items():
            for neighbor in neighbor_list:
                neighbor_id = neighbor.get("id")
                if not neighbor_id or neighbor_id in seen:
                    continue

                # Filter by entity type if specified
                if entity_types:
                    node_type = neighbor_id.split(":")[0] if ":" in neighbor_id else ""
                    if node_type not in entity_types:
                        continue

                seen.add(neighbor_id)
                related.append(self._create_node(neighbor, 1, language))

                if len(related) >= limit:
                    break

            if len(related) >= limit:
                break

        return related

    async def calculate_relationship_strength(
        self,
        entity1_id: str,
        entity2_id: str,
    ) -> Dict[str, Any]:
        """
        Calculate the strength of relationship between two entities.

        Considers:
        - Direct connection weight
        - Number of shared neighbors
        - Path lengths
        - Theme overlap

        Returns:
            Dict with strength score and breakdown
        """
        result = {
            "entity1": entity1_id,
            "entity2": entity2_id,
            "direct_connection": None,
            "shared_neighbors": 0,
            "shortest_path_length": None,
            "theme_overlap": 0.0,
            "overall_strength": 0.0,
        }

        # Check direct connection
        for edge_type in EdgeType:
            edges = await self.kg.get_edges(
                from_id=entity1_id,
                to_id=entity2_id,
                edge_type=edge_type.value
            )
            if edges:
                result["direct_connection"] = {
                    "type": edge_type.value,
                    "weight": edges[0].get("strength", 1.0),
                }
                break

        # Find shared neighbors
        neighbors1 = await self.kg.get_neighbors(entity1_id)
        neighbors2 = await self.kg.get_neighbors(entity2_id)

        neighbor_ids1 = set()
        neighbor_ids2 = set()

        for neighbors in neighbors1.values():
            for n in neighbors:
                if n.get("id"):
                    neighbor_ids1.add(n["id"])

        for neighbors in neighbors2.values():
            for n in neighbors:
                if n.get("id"):
                    neighbor_ids2.add(n["id"])

        shared = neighbor_ids1.intersection(neighbor_ids2)
        result["shared_neighbors"] = len(shared)

        # Find shortest path
        path = await self.find_path(entity1_id, entity2_id, max_depth=5)
        if path:
            result["shortest_path_length"] = path.length

        # Calculate overall strength
        strength = 0.0

        if result["direct_connection"]:
            strength += 0.5 * result["direct_connection"]["weight"]

        if result["shared_neighbors"] > 0:
            strength += 0.3 * min(result["shared_neighbors"] / 10, 1.0)

        if result["shortest_path_length"]:
            # Closer = stronger
            path_score = 1.0 / (result["shortest_path_length"] + 1)
            strength += 0.2 * path_score

        result["overall_strength"] = round(strength, 3)

        return result

    def _create_node(
        self,
        data: Dict[str, Any],
        depth: int,
        language: str,
    ) -> GraphNode:
        """Create a GraphNode from raw data."""
        node_id = data.get("id", "")
        node_type = node_id.split(":")[0] if ":" in node_id else "unknown"

        # Get localized labels
        label_ar = data.get("title_ar") or data.get("label_ar") or data.get("name_ar") or ""
        label_en = data.get("title_en") or data.get("label_en") or data.get("name_en") or ""

        label = label_ar if language == "ar" else label_en
        if not label:
            label = label_en or label_ar or node_id

        return GraphNode(
            id=node_id,
            type=node_type,
            label=label,
            label_ar=label_ar,
            data=data,
            depth=depth,
        )


# Singleton instance
_graph_explorer: Optional[GraphExplorer] = None


def get_graph_explorer() -> GraphExplorer:
    """Get the graph explorer singleton."""
    global _graph_explorer
    if _graph_explorer is None:
        _graph_explorer = GraphExplorer()
    return _graph_explorer
