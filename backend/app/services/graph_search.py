"""
Advanced Graph Search for Thematic Connections.

Provides graph-based exploration:
1. Theme-to-verse connections with strength scores
2. Prophet story interconnections
3. Concept relationship mapping
4. Interactive graph visualization data
5. Path finding between concepts

Arabic: البحث المتقدم بالرسم البياني للروابط الموضوعية
"""

import logging
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    THEME = "theme"
    VERSE = "verse"
    SURA = "sura"
    PROPHET = "prophet"
    CONCEPT = "concept"
    LESSON = "lesson"
    SCHOLAR = "scholar"


class EdgeType(str, Enum):
    """Types of edges (relationships) in the graph."""
    CONTAINS = "contains"           # Sura contains verse
    MENTIONS = "mentions"           # Verse mentions prophet
    RELATES_TO = "relates_to"       # Theme relates to theme
    TEACHES = "teaches"             # Verse teaches lesson
    INTERPRETED_BY = "interpreted_by"  # Verse interpreted by scholar
    EXAMPLE_OF = "example_of"       # Prophet is example of theme


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    node_id: str
    node_type: NodeType
    label_ar: str
    label_en: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    # For visualization
    size: float = 1.0
    color: Optional[str] = None
    group: Optional[str] = None


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    label_ar: Optional[str] = None
    label_en: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphPath:
    """A path through the knowledge graph."""
    nodes: List[str]
    edges: List[Tuple[str, str, EdgeType]]
    total_weight: float
    description_ar: str
    description_en: str


# =============================================================================
# KNOWLEDGE GRAPH DATA
# =============================================================================

# Core thematic connections with weights
THEME_CONNECTIONS = {
    "patience": {
        "relates_to": [
            ("trust", 0.9, "الصبر يتطلب التوكل على الله"),
            ("trial", 0.95, "الصبر عند الابتلاء"),
            ("reward", 0.85, "جزاء الصابرين"),
            ("hope", 0.8, "الصبر مع الأمل"),
            ("gratitude", 0.7, "الشكر في السراء والضراء"),
        ],
        "prophets": ["أيوب", "يعقوب", "موسى", "محمد"],
        "key_verses": ["2:153", "2:155-157", "3:200", "11:115", "16:126"],
    },
    "mercy": {
        "relates_to": [
            ("forgiveness", 0.95, "الرحمة أساس المغفرة"),
            ("love", 0.9, "من الرحمة تنبع المحبة"),
            ("kindness", 0.85, "الرحمة تظهر في الإحسان"),
            ("justice", 0.7, "العدل مع الرحمة"),
        ],
        "prophets": ["محمد", "عيسى", "يوسف"],
        "key_verses": ["21:107", "6:54", "7:156", "12:92"],
    },
    "faith": {
        "relates_to": [
            ("tawhid", 0.95, "الإيمان أساسه التوحيد"),
            ("prayer", 0.9, "الصلاة ركن الإيمان"),
            ("guidance", 0.85, "الهداية ثمرة الإيمان"),
            ("trust", 0.85, "التوكل من علامات الإيمان"),
            ("righteous", 0.8, "العمل الصالح برهان الإيمان"),
        ],
        "prophets": ["إبراهيم", "محمد", "نوح"],
        "key_verses": ["2:285", "49:15", "8:2-4", "23:1-11"],
    },
    "forgiveness": {
        "relates_to": [
            ("repentance", 0.95, "التوبة سبيل المغفرة"),
            ("mercy", 0.9, "المغفرة من رحمة الله"),
            ("sin", 0.85, "المغفرة تمحو الذنوب"),
            ("hope", 0.8, "لا تيأس من رحمة الله"),
        ],
        "prophets": ["يوسف", "محمد", "آدم"],
        "key_verses": ["39:53", "4:110", "3:135", "12:92"],
    },
    "justice": {
        "relates_to": [
            ("truth", 0.9, "العدل يقوم على الحق"),
            ("rights", 0.85, "العدل إعطاء الحقوق"),
            ("equality", 0.8, "المساواة من العدل"),
            ("witness", 0.75, "الشهادة بالعدل"),
        ],
        "prophets": ["داود", "سليمان", "موسى"],
        "key_verses": ["4:135", "5:8", "16:90", "57:25"],
    },
    "gratitude": {
        "relates_to": [
            ("blessing", 0.95, "الشكر على النعم"),
            ("contentment", 0.85, "القناعة مع الشكر"),
            ("worship", 0.8, "الشكر عبادة"),
            ("patience", 0.7, "الشكر في السراء والضراء"),
        ],
        "prophets": ["سليمان", "داود", "إبراهيم"],
        "key_verses": ["14:7", "31:12", "2:152", "34:13"],
    },
    "trial": {
        "relates_to": [
            ("patience", 0.95, "الصبر عند الابتلاء"),
            ("faith", 0.9, "الابتلاء اختبار للإيمان"),
            ("reward", 0.85, "أجر الصابرين"),
            ("wisdom", 0.8, "حكمة الابتلاء"),
        ],
        "prophets": ["أيوب", "يعقوب", "إبراهيم", "يونس"],
        "key_verses": ["2:155-157", "29:2-3", "21:35", "67:2"],
    },
    "guidance": {
        "relates_to": [
            ("light", 0.9, "الهداية نور"),
            ("truth", 0.85, "الهداية إلى الحق"),
            ("prayer", 0.8, "الدعاء للهداية"),
            ("quran", 0.95, "القرآن هدى"),
        ],
        "prophets": ["محمد", "موسى", "إبراهيم"],
        "key_verses": ["1:6-7", "2:2", "6:161", "17:9"],
    },
}

# Prophet interconnections
PROPHET_CONNECTIONS = {
    "إبراهيم": {
        "descendants": ["إسماعيل", "إسحاق", "يعقوب", "يوسف", "محمد"],
        "themes": ["tawhid", "sacrifice", "faith", "prayer"],
        "related_prophets": [("لوط", 0.9), ("إسماعيل", 0.95), ("إسحاق", 0.95)],
    },
    "موسى": {
        "descendants": [],
        "themes": ["courage", "patience", "leadership", "justice"],
        "related_prophets": [("هارون", 0.95), ("فرعون", 0.8), ("الخضر", 0.7)],
    },
    "يوسف": {
        "descendants": [],
        "themes": ["patience", "forgiveness", "chastity", "dreams"],
        "related_prophets": [("يعقوب", 0.95), ("إبراهيم", 0.8)],
    },
    "محمد": {
        "descendants": [],
        "themes": ["mercy", "guidance", "faith", "patience"],
        "related_prophets": [("إبراهيم", 0.9), ("موسى", 0.85), ("عيسى", 0.85)],
    },
}


# =============================================================================
# GRAPH SEARCH SERVICE
# =============================================================================

class GraphSearchService:
    """
    Advanced graph-based search and exploration.

    Features:
    - Build knowledge graph from themes and verses
    - Find connections between concepts
    - Compute connection strengths
    - Generate visualization data
    - Path finding between nodes
    """

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._reverse_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the knowledge graph."""
        if self._initialized:
            return

        # Build theme nodes
        for theme_id, theme_data in THEME_CONNECTIONS.items():
            self._nodes[f"theme:{theme_id}"] = GraphNode(
                node_id=f"theme:{theme_id}",
                node_type=NodeType.THEME,
                label_ar=self._get_theme_label_ar(theme_id),
                label_en=theme_id.replace("_", " ").title(),
                size=len(theme_data.get("relates_to", [])) + 5,
                group="theme",
            )

            # Add theme-to-theme edges
            for related, weight, description in theme_data.get("relates_to", []):
                edge = GraphEdge(
                    source_id=f"theme:{theme_id}",
                    target_id=f"theme:{related}",
                    edge_type=EdgeType.RELATES_TO,
                    weight=weight,
                    label_ar=description,
                    label_en=f"{theme_id} relates to {related}",
                )
                self._edges[f"theme:{theme_id}"].append(edge)
                self._reverse_edges[f"theme:{related}"].append(edge)

            # Add theme-to-prophet edges
            for prophet in theme_data.get("prophets", []):
                prophet_id = f"prophet:{prophet}"
                if prophet_id not in self._nodes:
                    self._nodes[prophet_id] = GraphNode(
                        node_id=prophet_id,
                        node_type=NodeType.PROPHET,
                        label_ar=prophet,
                        label_en=self._get_prophet_label_en(prophet),
                        size=8,
                        group="prophet",
                    )

                edge = GraphEdge(
                    source_id=prophet_id,
                    target_id=f"theme:{theme_id}",
                    edge_type=EdgeType.EXAMPLE_OF,
                    weight=0.8,
                )
                self._edges[prophet_id].append(edge)
                self._reverse_edges[f"theme:{theme_id}"].append(edge)

        # Build prophet interconnections
        for prophet_ar, data in PROPHET_CONNECTIONS.items():
            prophet_id = f"prophet:{prophet_ar}"
            if prophet_id not in self._nodes:
                self._nodes[prophet_id] = GraphNode(
                    node_id=prophet_id,
                    node_type=NodeType.PROPHET,
                    label_ar=prophet_ar,
                    label_en=self._get_prophet_label_en(prophet_ar),
                    size=10,
                    group="prophet",
                )

            for related_prophet, weight in data.get("related_prophets", []):
                edge = GraphEdge(
                    source_id=prophet_id,
                    target_id=f"prophet:{related_prophet}",
                    edge_type=EdgeType.RELATES_TO,
                    weight=weight,
                )
                self._edges[prophet_id].append(edge)

        self._initialized = True

    def _get_theme_label_ar(self, theme_id: str) -> str:
        """Get Arabic label for theme."""
        labels = {
            "patience": "الصبر",
            "mercy": "الرحمة",
            "faith": "الإيمان",
            "forgiveness": "المغفرة",
            "justice": "العدل",
            "gratitude": "الشكر",
            "trial": "الابتلاء",
            "guidance": "الهداية",
            "trust": "التوكل",
            "hope": "الأمل",
            "love": "المحبة",
            "kindness": "الإحسان",
            "repentance": "التوبة",
            "tawhid": "التوحيد",
            "prayer": "الصلاة",
            "reward": "الجزاء",
        }
        return labels.get(theme_id, theme_id)

    def _get_prophet_label_en(self, prophet_ar: str) -> str:
        """Get English label for prophet."""
        labels = {
            "إبراهيم": "Ibrahim (Abraham)",
            "موسى": "Musa (Moses)",
            "عيسى": "Isa (Jesus)",
            "محمد": "Muhammad",
            "يوسف": "Yusuf (Joseph)",
            "نوح": "Nuh (Noah)",
            "داود": "Dawud (David)",
            "سليمان": "Sulayman (Solomon)",
            "أيوب": "Ayyub (Job)",
            "يعقوب": "Yaqub (Jacob)",
            "إسماعيل": "Ismail (Ishmael)",
            "إسحاق": "Ishaq (Isaac)",
            "هارون": "Harun (Aaron)",
            "زكريا": "Zakariya (Zechariah)",
            "يونس": "Yunus (Jonah)",
        }
        return labels.get(prophet_ar, prophet_ar)

    async def find_connections(
        self,
        source_id: str,
        max_depth: int = 3,
        min_weight: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Find all connections from a source node.

        Arabic: إيجاد جميع الروابط من عقدة مصدر
        """
        await self.initialize()

        if source_id not in self._nodes:
            # Try with prefix
            for prefix in ["theme:", "prophet:", "verse:"]:
                if f"{prefix}{source_id}" in self._nodes:
                    source_id = f"{prefix}{source_id}"
                    break

        if source_id not in self._nodes:
            return {"error": f"Node '{source_id}' not found"}

        visited = set()
        connections = []
        queue = [(source_id, 0, 1.0)]

        while queue:
            current_id, depth, cumulative_weight = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            for edge in self._edges.get(current_id, []):
                if edge.weight >= min_weight:
                    new_weight = cumulative_weight * edge.weight

                    connections.append({
                        "from": current_id,
                        "to": edge.target_id,
                        "type": edge.edge_type.value,
                        "weight": round(edge.weight, 2),
                        "cumulative_weight": round(new_weight, 2),
                        "depth": depth + 1,
                        "label_ar": edge.label_ar,
                        "label_en": edge.label_en,
                    })

                    if edge.target_id not in visited:
                        queue.append((edge.target_id, depth + 1, new_weight))

        return {
            "source": source_id,
            "source_node": self._node_to_dict(self._nodes[source_id]),
            "connections": connections,
            "total_connections": len(connections),
            "max_depth_reached": max_depth,
        }

    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Find shortest path between two nodes.

        Arabic: إيجاد أقصر مسار بين عقدتين
        """
        await self.initialize()

        # Normalize IDs
        for prefix in ["theme:", "prophet:"]:
            if f"{prefix}{source_id}" in self._nodes:
                source_id = f"{prefix}{source_id}"
            if f"{prefix}{target_id}" in self._nodes:
                target_id = f"{prefix}{target_id}"

        if source_id not in self._nodes:
            return {"error": f"Source '{source_id}' not found"}
        if target_id not in self._nodes:
            return {"error": f"Target '{target_id}' not found"}

        # BFS for shortest path
        visited = {source_id}
        queue = [(source_id, [source_id], [], 0)]

        while queue:
            current, path, edges, total_weight = queue.pop(0)

            if current == target_id:
                return {
                    "found": True,
                    "source": source_id,
                    "target": target_id,
                    "path": path,
                    "edges": edges,
                    "length": len(path) - 1,
                    "total_weight": round(total_weight, 2),
                    "nodes": [self._node_to_dict(self._nodes[n]) for n in path],
                }

            if len(path) > max_depth:
                continue

            for edge in self._edges.get(current, []):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((
                        edge.target_id,
                        path + [edge.target_id],
                        edges + [(current, edge.target_id, edge.edge_type.value, edge.weight)],
                        total_weight + edge.weight,
                    ))

        return {
            "found": False,
            "source": source_id,
            "target": target_id,
            "message_ar": "لا يوجد مسار بين العقدتين",
            "message_en": "No path found between nodes",
        }

    async def get_related_content(
        self,
        node_id: str,
        content_type: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get content related to a node (themes, verses, prophets).

        Arabic: الحصول على المحتوى المرتبط بعقدة
        """
        await self.initialize()

        # Normalize ID
        for prefix in ["theme:", "prophet:", "verse:"]:
            if f"{prefix}{node_id}" in self._nodes:
                node_id = f"{prefix}{node_id}"
                break

        if node_id not in self._nodes:
            return {"error": f"Node '{node_id}' not found"}

        node = self._nodes[node_id]
        related = {
            "themes": [],
            "prophets": [],
            "verses": [],
        }

        # Get outgoing connections
        for edge in self._edges.get(node_id, []):
            target = self._nodes.get(edge.target_id)
            if target:
                item = {
                    **self._node_to_dict(target),
                    "connection_weight": round(edge.weight, 2),
                    "connection_type": edge.edge_type.value,
                }

                if target.node_type == NodeType.THEME:
                    related["themes"].append(item)
                elif target.node_type == NodeType.PROPHET:
                    related["prophets"].append(item)
                elif target.node_type == NodeType.VERSE:
                    related["verses"].append(item)

        # Get incoming connections
        for edge in self._reverse_edges.get(node_id, []):
            source = self._nodes.get(edge.source_id)
            if source:
                item = {
                    **self._node_to_dict(source),
                    "connection_weight": round(edge.weight, 2),
                    "connection_type": edge.edge_type.value,
                }

                if source.node_type == NodeType.THEME:
                    if item not in related["themes"]:
                        related["themes"].append(item)
                elif source.node_type == NodeType.PROPHET:
                    if item not in related["prophets"]:
                        related["prophets"].append(item)

        # Sort by weight and limit
        for key in related:
            related[key] = sorted(
                related[key],
                key=lambda x: x.get("connection_weight", 0),
                reverse=True
            )[:limit]

        # Filter by type if specified
        if content_type:
            if content_type in related:
                return {
                    "node": self._node_to_dict(node),
                    "related": related[content_type],
                    "count": len(related[content_type]),
                }

        return {
            "node": self._node_to_dict(node),
            "related": related,
            "counts": {k: len(v) for k, v in related.items()},
        }

    async def get_visualization_data(
        self,
        center_node: Optional[str] = None,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Get data for graph visualization.

        Arabic: الحصول على بيانات التصور البياني
        """
        await self.initialize()

        if center_node:
            # Get subgraph around center node
            for prefix in ["theme:", "prophet:"]:
                if f"{prefix}{center_node}" in self._nodes:
                    center_node = f"{prefix}{center_node}"
                    break

            if center_node not in self._nodes:
                return {"error": f"Node '{center_node}' not found"}

            # BFS to get nearby nodes
            visited = {center_node}
            queue = [(center_node, 0)]
            nodes_to_include = [center_node]

            while queue:
                current, d = queue.pop(0)
                if d >= depth:
                    continue

                for edge in self._edges.get(current, []):
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        nodes_to_include.append(edge.target_id)
                        queue.append((edge.target_id, d + 1))

            nodes = [
                self._node_to_vis_dict(self._nodes[n])
                for n in nodes_to_include
                if n in self._nodes
            ]

            edges = []
            for node_id in nodes_to_include:
                for edge in self._edges.get(node_id, []):
                    if edge.target_id in nodes_to_include:
                        edges.append(self._edge_to_vis_dict(edge))

        else:
            # Get full graph
            nodes = [self._node_to_vis_dict(n) for n in self._nodes.values()]
            edges = []
            for node_edges in self._edges.values():
                for edge in node_edges:
                    edges.append(self._edge_to_vis_dict(edge))

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "center_node": center_node,
        }

    def _node_to_dict(self, node: GraphNode) -> Dict[str, Any]:
        """Convert node to dict."""
        return {
            "id": node.node_id,
            "type": node.node_type.value,
            "label_ar": node.label_ar,
            "label_en": node.label_en,
            "size": node.size,
            "group": node.group,
        }

    def _node_to_vis_dict(self, node: GraphNode) -> Dict[str, Any]:
        """Convert node to visualization dict."""
        colors = {
            NodeType.THEME: "#4CAF50",
            NodeType.PROPHET: "#2196F3",
            NodeType.VERSE: "#FFC107",
            NodeType.CONCEPT: "#9C27B0",
            NodeType.LESSON: "#FF5722",
        }

        return {
            "id": node.node_id,
            "label": node.label_en,
            "title": node.label_ar,
            "group": node.group or node.node_type.value,
            "value": node.size,
            "color": colors.get(node.node_type, "#757575"),
        }

    def _edge_to_vis_dict(self, edge: GraphEdge) -> Dict[str, Any]:
        """Convert edge to visualization dict."""
        return {
            "from": edge.source_id,
            "to": edge.target_id,
            "value": edge.weight,
            "title": edge.label_ar or edge.edge_type.value,
            "arrows": "to",
        }

    async def compute_centrality(self) -> Dict[str, Any]:
        """
        Compute centrality scores for all nodes.

        Arabic: حساب درجات المركزية لجميع العقد
        """
        await self.initialize()

        # Degree centrality
        degree_centrality = {}
        for node_id in self._nodes:
            out_degree = len(self._edges.get(node_id, []))
            in_degree = len(self._reverse_edges.get(node_id, []))
            degree_centrality[node_id] = out_degree + in_degree

        # Normalize
        max_degree = max(degree_centrality.values()) if degree_centrality else 1
        normalized = {
            k: round(v / max_degree, 3)
            for k, v in degree_centrality.items()
        }

        # Sort by centrality
        sorted_nodes = sorted(normalized.items(), key=lambda x: x[1], reverse=True)

        return {
            "centrality_scores": [
                {
                    "node_id": node_id,
                    "node": self._node_to_dict(self._nodes[node_id]),
                    "centrality": score,
                }
                for node_id, score in sorted_nodes[:20]
            ],
            "most_central": sorted_nodes[0][0] if sorted_nodes else None,
            "total_nodes": len(self._nodes),
        }


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

graph_search_service = GraphSearchService()
