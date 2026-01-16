"""
Thematic Mapping Service.

Provides cross-story theme analysis and connections:
- Theme discovery across stories
- Thematic journey tracking
- Theme evolution visualization
- Cross-reference identification

Arabic: خدمة ربط المواضيع
"""
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.kg.client import get_kg_client, KGClient
from app.db.database import get_async_session
from app.models.concept import Concept, Occurrence, Association

logger = logging.getLogger(__name__)


class ThemeCategory(str, Enum):
    """Categories of Quranic themes."""
    FAITH = "faith"                 # إيمان
    WORSHIP = "worship"             # عبادة
    MORALITY = "morality"           # أخلاق
    STORIES = "stories"             # قصص
    ESCHATOLOGY = "eschatology"     # الآخرة
    JURISPRUDENCE = "jurisprudence" # أحكام
    NATURE = "nature"               # كونيات
    SOCIETY = "society"             # مجتمع


@dataclass
class ThemeOccurrence:
    """A theme occurrence in a specific context."""
    theme_id: str
    theme_label_ar: str
    theme_label_en: str
    story_id: Optional[str] = None
    story_title_ar: Optional[str] = None
    story_title_en: Optional[str] = None
    verse_reference: Optional[str] = None
    sura_no: Optional[int] = None
    ayah_start: Optional[int] = None
    ayah_end: Optional[int] = None
    context_ar: str = ""
    context_en: str = ""
    weight: float = 1.0


@dataclass
class ThemeConnection:
    """Connection between two themes."""
    theme1_id: str
    theme1_label_ar: str
    theme1_label_en: str
    theme2_id: str
    theme2_label_ar: str
    theme2_label_en: str
    connection_type: str  # co_occurrence, cause_effect, contrast, etc.
    strength: float
    evidence_count: int
    example_verses: List[str] = field(default_factory=list)


@dataclass
class ThematicJourney:
    """A journey through connected themes."""
    start_theme: str
    themes: List[str]
    connections: List[ThemeConnection]
    total_verses: int
    stories_covered: List[str]


@dataclass
class ThemeProgression:
    """How a theme progresses through the Quran."""
    theme_id: str
    theme_label_ar: str
    theme_label_en: str
    total_occurrences: int
    by_surah: Dict[int, int]  # surah_no -> count
    by_story: Dict[str, int]  # story_id -> count
    evolution_stages: List[Dict[str, Any]]


class ThematicMapper:
    """
    Service for thematic analysis and mapping.

    Discovers and visualizes thematic connections
    across the Quranic knowledge graph.
    """

    # Major themes with their Arabic labels
    MAJOR_THEMES = {
        "توحيد": ("توحيد", "Monotheism", ThemeCategory.FAITH),
        "صبر": ("صبر", "Patience", ThemeCategory.MORALITY),
        "توبة": ("توبة", "Repentance", ThemeCategory.WORSHIP),
        "رحمة": ("رحمة", "Mercy", ThemeCategory.FAITH),
        "عدل": ("عدل", "Justice", ThemeCategory.SOCIETY),
        "شكر": ("شكر", "Gratitude", ThemeCategory.WORSHIP),
        "تقوى": ("تقوى", "Piety", ThemeCategory.FAITH),
        "إيمان": ("إيمان", "Faith", ThemeCategory.FAITH),
        "جهاد": ("جهاد", "Striving", ThemeCategory.WORSHIP),
        "هداية": ("هداية", "Guidance", ThemeCategory.FAITH),
    }

    def __init__(self, kg_client: KGClient = None, db_session: AsyncSession = None):
        self.kg = kg_client or get_kg_client()
        self.db = db_session

    async def get_theme_occurrences(
        self,
        theme_key: str,
        limit: int = 50,
        language: str = "ar",
    ) -> List[ThemeOccurrence]:
        """
        Get all occurrences of a theme across stories and verses.

        Args:
            theme_key: Theme key (e.g., "صبر", "patience")
            limit: Maximum occurrences to return
            language: Response language

        Returns:
            List of ThemeOccurrence objects
        """
        occurrences: List[ThemeOccurrence] = []

        # Search in concept graph
        label_field = "label_ar" if language == "ar" else "label_en"
        concepts = await self.kg.query(
            f"SELECT * FROM concept_tag WHERE {label_field} CONTAINS $key OR aliases CONTAINS $key LIMIT {limit};",
        )

        for concept in concepts:
            concept_id = concept.get("id")
            if not concept_id:
                continue

            # Get occurrences (tagged entities)
            tagged_entities = await self.kg.get_edges(
                to_id=concept_id,
                edge_type="tagged_with"
            )

            for edge in tagged_entities:
                entity_id = edge.get("in")
                if not entity_id:
                    continue

                entity_data = await self.kg.get(entity_id)
                if not entity_data:
                    continue

                # Determine entity type and extract info
                entity_type = entity_id.split(":")[0] if ":" in entity_id else ""

                occurrence = ThemeOccurrence(
                    theme_id=concept_id,
                    theme_label_ar=concept.get("label_ar", ""),
                    theme_label_en=concept.get("label_en", ""),
                    weight=edge.get("weight", 1.0),
                )

                if entity_type == "story_event":
                    occurrence.story_id = entity_data.get("cluster_id")
                    occurrence.verse_reference = entity_data.get("verse_reference")
                    occurrence.sura_no = entity_data.get("sura_no")
                    occurrence.ayah_start = entity_data.get("ayah_start")
                    occurrence.ayah_end = entity_data.get("ayah_end")
                    occurrence.context_ar = entity_data.get("summary_ar", "")
                    occurrence.context_en = entity_data.get("summary_en", "")
                elif entity_type == "story_cluster":
                    occurrence.story_id = entity_id
                    occurrence.story_title_ar = entity_data.get("title_ar", "")
                    occurrence.story_title_en = entity_data.get("title_en", "")

                occurrences.append(occurrence)

                if len(occurrences) >= limit:
                    break

            if len(occurrences) >= limit:
                break

        return occurrences

    async def find_theme_connections(
        self,
        theme_key: str,
        min_strength: float = 0.3,
        limit: int = 20,
    ) -> List[ThemeConnection]:
        """
        Find themes connected to a given theme.

        Looks for co-occurrence, causal relationships,
        and semantic similarity.

        Args:
            theme_key: Theme key
            min_strength: Minimum connection strength
            limit: Maximum connections to return

        Returns:
            List of ThemeConnection objects
        """
        connections: List[ThemeConnection] = []

        # Find the theme concept
        concepts = await self.kg.query(
            f"SELECT * FROM concept_tag WHERE label_ar = '{theme_key}' OR label_en = '{theme_key}';"
        )

        if not concepts:
            return connections

        theme_concept = concepts[0]
        theme_id = theme_concept.get("id")

        # Get thematic links to other concepts
        theme_links = await self.kg.get_edges(
            from_id=theme_id,
            edge_type="thematic_link"
        )

        for edge in theme_links[:limit]:
            target_id = edge.get("out")
            if not target_id:
                continue

            strength = edge.get("strength", 0.5)
            if strength < min_strength:
                continue

            target_data = await self.kg.get(target_id)
            if not target_data:
                continue

            connections.append(ThemeConnection(
                theme1_id=theme_id,
                theme1_label_ar=theme_concept.get("label_ar", ""),
                theme1_label_en=theme_concept.get("label_en", ""),
                theme2_id=target_id,
                theme2_label_ar=target_data.get("label_ar", ""),
                theme2_label_en=target_data.get("label_en", ""),
                connection_type=edge.get("relation_type", "related"),
                strength=strength,
                evidence_count=len(edge.get("evidence_refs", [])),
                example_verses=edge.get("example_ayahs", []),
            ))

        # Sort by strength
        connections.sort(key=lambda c: c.strength, reverse=True)

        return connections

    async def get_stories_by_theme(
        self,
        theme_key: str,
        language: str = "ar",
    ) -> List[Dict[str, Any]]:
        """
        Get all stories that feature a specific theme.

        Args:
            theme_key: Theme key
            language: Response language

        Returns:
            List of story summaries with theme context
        """
        stories: List[Dict[str, Any]] = []

        # Get theme occurrences
        occurrences = await self.get_theme_occurrences(theme_key, limit=100, language=language)

        # Group by story
        story_occurrences: Dict[str, List[ThemeOccurrence]] = defaultdict(list)
        for occ in occurrences:
            if occ.story_id:
                story_occurrences[occ.story_id].append(occ)

        # Build story summaries
        for story_id, occs in story_occurrences.items():
            story_data = await self.kg.get(story_id)
            if not story_data:
                continue

            title_field = "title_ar" if language == "ar" else "title_en"
            summary_field = "summary_ar" if language == "ar" else "summary_en"

            stories.append({
                "story_id": story_id,
                "title": story_data.get(title_field) or story_data.get("title_ar", ""),
                "category": story_data.get("category"),
                "occurrence_count": len(occs),
                "total_weight": sum(o.weight for o in occs),
                "verse_references": [o.verse_reference for o in occs if o.verse_reference],
                "summary": story_data.get(summary_field, ""),
            })

        # Sort by occurrence count
        stories.sort(key=lambda s: s["occurrence_count"], reverse=True)

        return stories

    async def get_theme_progression(
        self,
        theme_key: str,
    ) -> ThemeProgression:
        """
        Analyze how a theme progresses through the Quran.

        Shows evolution from early to late surahs,
        across different story contexts.

        Args:
            theme_key: Theme key

        Returns:
            ThemeProgression object
        """
        occurrences = await self.get_theme_occurrences(theme_key, limit=500)

        by_surah: Dict[int, int] = defaultdict(int)
        by_story: Dict[str, int] = defaultdict(int)

        for occ in occurrences:
            if occ.sura_no:
                by_surah[occ.sura_no] += 1
            if occ.story_id:
                by_story[occ.story_id] += 1

        # Build evolution stages (early Meccan, late Meccan, Medinan)
        # Simplified: surahs 1-20 early, 21-80 middle, 81-114 late
        evolution_stages = [
            {
                "stage": "early",
                "label_ar": "المرحلة المبكرة",
                "label_en": "Early Period",
                "surahs": list(range(90, 115)),
                "count": sum(by_surah.get(s, 0) for s in range(90, 115)),
            },
            {
                "stage": "middle",
                "label_ar": "المرحلة الوسطى",
                "label_en": "Middle Period",
                "surahs": list(range(20, 90)),
                "count": sum(by_surah.get(s, 0) for s in range(20, 90)),
            },
            {
                "stage": "late",
                "label_ar": "المرحلة المتأخرة",
                "label_en": "Late Period",
                "surahs": list(range(1, 20)),
                "count": sum(by_surah.get(s, 0) for s in range(1, 20)),
            },
        ]

        theme_label = self.MAJOR_THEMES.get(theme_key, (theme_key, theme_key, None))

        return ThemeProgression(
            theme_id=f"theme:{theme_key}",
            theme_label_ar=theme_label[0],
            theme_label_en=theme_label[1],
            total_occurrences=len(occurrences),
            by_surah=dict(by_surah),
            by_story=dict(by_story),
            evolution_stages=evolution_stages,
        )

    async def build_thematic_journey(
        self,
        start_theme: str,
        max_steps: int = 5,
    ) -> ThematicJourney:
        """
        Build a journey through connected themes.

        Follows thematic connections to create
        a learning path through related concepts.

        Args:
            start_theme: Starting theme key
            max_steps: Maximum journey length

        Returns:
            ThematicJourney object
        """
        themes: List[str] = [start_theme]
        connections: List[ThemeConnection] = []
        stories_covered: Set[str] = set()
        total_verses = 0

        current_theme = start_theme
        visited: Set[str] = {start_theme}

        for _ in range(max_steps):
            # Get connections from current theme
            theme_connections = await self.find_theme_connections(
                current_theme,
                min_strength=0.4,
                limit=5
            )

            # Find unvisited connection with highest strength
            next_connection = None
            for conn in theme_connections:
                next_theme_key = conn.theme2_label_ar
                if next_theme_key not in visited:
                    next_connection = conn
                    break

            if not next_connection:
                break

            # Add to journey
            next_theme = next_connection.theme2_label_ar
            themes.append(next_theme)
            connections.append(next_connection)
            visited.add(next_theme)
            total_verses += next_connection.evidence_count

            # Track stories
            stories = await self.get_stories_by_theme(next_theme)
            for story in stories[:5]:
                stories_covered.add(story["story_id"])

            current_theme = next_theme

        return ThematicJourney(
            start_theme=start_theme,
            themes=themes,
            connections=connections,
            total_verses=total_verses,
            stories_covered=list(stories_covered),
        )

    async def get_cross_story_themes(
        self,
        story_ids: List[str],
        min_occurrences: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Find themes that appear across multiple stories.

        Identifies common thematic threads between stories.

        Args:
            story_ids: List of story IDs to analyze
            min_occurrences: Minimum times theme must appear

        Returns:
            List of shared themes with occurrence details
        """
        theme_stories: Dict[str, Set[str]] = defaultdict(set)
        theme_data: Dict[str, Dict[str, Any]] = {}

        for story_id in story_ids:
            # Get events for this story
            events = await self.kg.select(
                "story_event",
                where=f"cluster_id = {story_id}"
            )

            for event in events:
                event_id = event.get("id")
                if not event_id:
                    continue

                # Get themes tagged to this event
                tags = await self.kg.get_edges(
                    from_id=event_id,
                    edge_type="tagged_with"
                )

                for tag_edge in tags:
                    theme_id = tag_edge.get("out")
                    if theme_id:
                        theme_stories[theme_id].add(story_id)

                        # Cache theme data
                        if theme_id not in theme_data:
                            t_data = await self.kg.get(theme_id)
                            if t_data:
                                theme_data[theme_id] = t_data

        # Filter to themes appearing in multiple stories
        shared_themes = []
        for theme_id, stories in theme_stories.items():
            if len(stories) >= min_occurrences:
                t_data = theme_data.get(theme_id, {})
                shared_themes.append({
                    "theme_id": theme_id,
                    "theme_label_ar": t_data.get("label_ar", ""),
                    "theme_label_en": t_data.get("label_en", ""),
                    "story_count": len(stories),
                    "story_ids": list(stories),
                })

        # Sort by story count
        shared_themes.sort(key=lambda t: t["story_count"], reverse=True)

        return shared_themes

    async def get_theme_graph_data(
        self,
        theme_key: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Get graph visualization data for a theme.

        Returns nodes and edges for rendering
        a thematic network visualization.

        Args:
            theme_key: Central theme
            depth: How many connection levels

        Returns:
            Dict with nodes and edges for visualization
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        visited: Set[str] = set()

        async def explore_theme(theme: str, current_depth: int):
            if current_depth > depth or theme in visited:
                return

            visited.add(theme)

            # Get theme data
            concepts = await self.kg.query(
                f"SELECT * FROM concept_tag WHERE label_ar = '{theme}' OR label_en = '{theme}';"
            )

            if concepts:
                concept = concepts[0]
                nodes.append({
                    "id": concept.get("id", theme),
                    "label": concept.get("label_ar", theme),
                    "label_en": concept.get("label_en", theme),
                    "type": "theme",
                    "depth": current_depth,
                    "size": 10 - current_depth,  # Larger for central nodes
                })

                # Get connections
                connections = await self.find_theme_connections(theme, min_strength=0.3)

                for conn in connections[:5]:  # Limit connections per level
                    edges.append({
                        "source": conn.theme1_id,
                        "target": conn.theme2_id,
                        "type": conn.connection_type,
                        "weight": conn.strength,
                    })

                    # Recursively explore connected themes
                    await explore_theme(conn.theme2_label_ar, current_depth + 1)

        await explore_theme(theme_key, 0)

        return {
            "nodes": nodes,
            "edges": edges,
            "center_theme": theme_key,
            "depth": depth,
        }


# Singleton instance
_thematic_mapper: Optional[ThematicMapper] = None


def get_thematic_mapper() -> ThematicMapper:
    """Get the thematic mapper singleton."""
    global _thematic_mapper
    if _thematic_mapper is None:
        _thematic_mapper = ThematicMapper()
    return _thematic_mapper
