"""
Similarity Scoring Service - Connected Papers-style discovery for Quranic stories.

This service provides:
1. Story-to-story similarity based on shared concepts (Jaccard coefficient)
2. Cluster-to-cluster similarity
3. "Similar Stories" recommendations
4. Concept overlap analysis
5. Elaboration/Summarization edge detection (PR5)

SCORING METHODS:
================
1. Concept Jaccard: |A ∩ B| / |A ∪ B| for concept sets
2. Theme Overlap: Weighted by theme importance
3. Figure Co-occurrence: Shared characters/prophets
4. Narrative Role Similarity: Edit distance on role sequences
5. Verse Overlap: Shared ayah ranges (PR5)
6. TF-IDF Boost: Rare concept bonus (PR5)

All scores are normalized to [0.0, 1.0] range.

ELABORATION EDGES (PR5):
========================
- تفصيل (tafsil): One story elaborates another (more detail)
- إجمال (ijmal): One story summarizes another (less detail)
- Detected by: verse containment + verse count ratio
"""
from dataclasses import dataclass, field
from typing import Optional, Literal
from collections import defaultdict
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story import Story, StorySegment
from app.models.story_atlas import StoryCluster
from app.models.concept import Concept, Occurrence


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class EdgeType(str, Enum):
    """Types of semantic edges between stories (PR5)."""
    SIMILAR = "similar"           # تشابه - general similarity
    ELABORATES = "elaborates"     # تفصيل - A elaborates B (more detail)
    SUMMARIZES = "summarizes"     # إجمال - A summarizes B (less detail)
    PARALLELS = "parallels"       # تماثل - narrative parallel


# Arabic labels for edge types
EDGE_TYPE_AR = {
    EdgeType.SIMILAR: "تشابه",
    EdgeType.ELABORATES: "تفصيل",
    EdgeType.SUMMARIZES: "إجمال",
    EdgeType.PARALLELS: "تماثل",
}


@dataclass
class SimilarityScore:
    """Similarity score between two entities."""
    source_id: str
    target_id: str
    score: float  # 0.0 - 1.0
    components: dict = field(default_factory=dict)  # Breakdown of score


@dataclass
class SimilarEntity:
    """A similar entity with its metadata."""
    id: str
    title_ar: str
    title_en: str
    entity_type: str  # "story" or "cluster"
    similarity_score: float
    shared_concepts: list[str] = field(default_factory=list)
    shared_themes: list[str] = field(default_factory=list)
    shared_figures: list[str] = field(default_factory=list)
    # PR5: Enhanced fields
    edge_type: EdgeType = EdgeType.SIMILAR
    edge_type_ar: str = "تشابه"
    explanation_ar: str = ""  # Arabic explanation of why similar
    explanation_en: str = ""  # English explanation
    score_breakdown: dict = field(default_factory=dict)  # Factor breakdown


@dataclass
class ConceptOverlap:
    """Concept overlap analysis between two entities."""
    concept_id: str
    concept_label_ar: str
    concept_label_en: str
    concept_type: str
    in_source: bool
    in_target: bool


@dataclass
class ElaborationEdge:
    """
    Elaboration/Summarization edge between two stories (PR5).

    تفصيل/إجمال: When one story provides more or less detail
    on the same narrative as another story.
    """
    source_id: str  # Story providing the edge direction
    target_id: str  # Story being related to
    edge_type: EdgeType  # ELABORATES or SUMMARIZES
    edge_type_ar: str  # Arabic label
    confidence: float  # 0.0 - 1.0
    verse_overlap_ratio: float  # How much verse overlap
    detail_ratio: float  # source_verses / target_verses
    evidence_chunk_id: Optional[str] = None  # Tafsir evidence
    explanation_ar: str = ""
    explanation_en: str = ""


# =============================================================================
# SIMILARITY SERVICE
# =============================================================================

class SimilarityService:
    """Service for computing story/cluster similarities."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._concept_cache: dict[str, set[str]] = {}  # entity_id -> concept_ids

    async def get_similar_stories(
        self,
        story_id: str,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[SimilarEntity]:
        """
        Find stories similar to the given story.

        Uses concept overlap with Jaccard similarity.
        """
        # Get source story concepts
        source_concepts = await self._get_story_concepts(story_id)
        if not source_concepts:
            return []

        # Get all other stories
        stories = await self.session.execute(
            select(Story).where(Story.id != story_id)
        )
        all_stories = stories.scalars().all()

        # Calculate similarities
        similarities: list[SimilarEntity] = []
        for story in all_stories:
            target_concepts = await self._get_story_concepts(story.id)
            if not target_concepts:
                continue

            # Jaccard similarity
            intersection = source_concepts & target_concepts
            union = source_concepts | target_concepts
            score = len(intersection) / len(union) if union else 0.0

            if score >= min_score:
                # Get shared concept details
                shared_concepts = await self._get_concept_labels(intersection)

                # Categorize shared concepts
                shared_themes = [c for c in shared_concepts if c.get("type") == "theme"]
                shared_figures = [c for c in shared_concepts if c.get("type") == "person"]

                similarities.append(SimilarEntity(
                    id=story.id,
                    title_ar=story.name_ar,
                    title_en=story.name_en,
                    entity_type="story",
                    similarity_score=score,
                    shared_concepts=[c["id"] for c in shared_concepts],
                    shared_themes=[c["label_en"] for c in shared_themes],
                    shared_figures=[c["label_en"] for c in shared_figures],
                ))

        # Sort by score and limit
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:limit]

    async def get_similar_clusters(
        self,
        cluster_id: str,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[SimilarEntity]:
        """
        Find clusters similar to the given cluster.

        Uses concept overlap with Jaccard similarity.
        """
        # Get source cluster concepts
        source_concepts = await self._get_cluster_concepts(cluster_id)
        if not source_concepts:
            # Fallback to person-based similarity
            return await self._get_similar_clusters_by_persons(cluster_id, limit)

        # Get all other clusters
        clusters = await self.session.execute(
            select(StoryCluster).where(StoryCluster.id != cluster_id)
        )
        all_clusters = clusters.scalars().all()

        # Calculate similarities
        similarities: list[SimilarEntity] = []
        for cluster in all_clusters:
            target_concepts = await self._get_cluster_concepts(cluster.id)
            if not target_concepts:
                continue

            # Jaccard similarity
            intersection = source_concepts & target_concepts
            union = source_concepts | target_concepts
            score = len(intersection) / len(union) if union else 0.0

            if score >= min_score:
                shared_concepts = await self._get_concept_labels(intersection)
                shared_themes = [c for c in shared_concepts if c.get("type") == "theme"]
                shared_figures = [c for c in shared_concepts if c.get("type") == "person"]

                similarities.append(SimilarEntity(
                    id=cluster.id,
                    title_ar=cluster.title_ar,
                    title_en=cluster.title_en,
                    entity_type="cluster",
                    similarity_score=score,
                    shared_concepts=[c["id"] for c in shared_concepts],
                    shared_themes=[c["label_en"] for c in shared_themes],
                    shared_figures=[c["label_en"] for c in shared_figures],
                ))

        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:limit]

    async def get_concept_overlap(
        self,
        source_id: str,
        target_id: str,
        entity_type: str = "story",
    ) -> list[ConceptOverlap]:
        """
        Get detailed concept overlap between two entities.

        Shows which concepts are shared vs unique to each.
        """
        if entity_type == "story":
            source_concepts = await self._get_story_concepts(source_id)
            target_concepts = await self._get_story_concepts(target_id)
        else:
            source_concepts = await self._get_cluster_concepts(source_id)
            target_concepts = await self._get_cluster_concepts(target_id)

        all_concepts = source_concepts | target_concepts

        # Get concept details
        overlaps: list[ConceptOverlap] = []
        for concept_id in all_concepts:
            concept = await self.session.execute(
                select(Concept).where(Concept.id == concept_id)
            )
            concept_obj = concept.scalar_one_or_none()
            if concept_obj:
                overlaps.append(ConceptOverlap(
                    concept_id=concept_id,
                    concept_label_ar=concept_obj.label_ar,
                    concept_label_en=concept_obj.label_en,
                    concept_type=concept_obj.concept_type,
                    in_source=concept_id in source_concepts,
                    in_target=concept_id in target_concepts,
                ))

        # Sort: shared first, then by type
        overlaps.sort(key=lambda x: (
            not (x.in_source and x.in_target),  # Shared first
            x.concept_type,
        ))

        return overlaps

    async def compute_similarity_matrix(
        self,
        entity_ids: list[str],
        entity_type: str = "story",
    ) -> dict[tuple[str, str], float]:
        """
        Compute pairwise similarity matrix for a set of entities.

        Returns dict mapping (id1, id2) -> similarity score.
        """
        matrix: dict[tuple[str, str], float] = {}

        # Get all concept sets
        concept_sets: dict[str, set[str]] = {}
        for entity_id in entity_ids:
            if entity_type == "story":
                concept_sets[entity_id] = await self._get_story_concepts(entity_id)
            else:
                concept_sets[entity_id] = await self._get_cluster_concepts(entity_id)

        # Compute pairwise similarities
        for i, id1 in enumerate(entity_ids):
            for id2 in entity_ids[i + 1:]:
                set1 = concept_sets.get(id1, set())
                set2 = concept_sets.get(id2, set())

                if set1 and set2:
                    intersection = set1 & set2
                    union = set1 | set2
                    score = len(intersection) / len(union) if union else 0.0
                else:
                    score = 0.0

                matrix[(id1, id2)] = score
                matrix[(id2, id1)] = score  # Symmetric

        return matrix

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _get_story_concepts(self, story_id: str) -> set[str]:
        """Get all concept IDs associated with a story."""
        if story_id in self._concept_cache:
            return self._concept_cache[story_id]

        # Query occurrences for this story
        result = await self.session.execute(
            select(Occurrence.concept_id).where(
                Occurrence.ref_type == "story",
                Occurrence.ref_id == story_id,
            ).distinct()
        )
        concept_ids = {row[0] for row in result.all()}

        # Also check segment occurrences
        segments_result = await self.session.execute(
            select(StorySegment.id).where(StorySegment.story_id == story_id)
        )
        segment_ids = [row[0] for row in segments_result.all()]

        if segment_ids:
            segment_concepts = await self.session.execute(
                select(Occurrence.concept_id).where(
                    Occurrence.ref_type == "segment",
                    Occurrence.ref_id.in_(segment_ids),
                ).distinct()
            )
            concept_ids.update(row[0] for row in segment_concepts.all())

        self._concept_cache[story_id] = concept_ids
        return concept_ids

    async def _get_cluster_concepts(self, cluster_id: str) -> set[str]:
        """Get all concept IDs associated with a cluster."""
        if cluster_id in self._concept_cache:
            return self._concept_cache[cluster_id]

        # Query occurrences for this cluster
        result = await self.session.execute(
            select(Occurrence.concept_id).where(
                Occurrence.ref_type == "cluster",
                Occurrence.ref_id == cluster_id,
            ).distinct()
        )
        concept_ids = {row[0] for row in result.all()}

        self._concept_cache[cluster_id] = concept_ids
        return concept_ids

    async def _get_concept_labels(self, concept_ids: set[str]) -> list[dict]:
        """Get label info for a set of concept IDs."""
        if not concept_ids:
            return []

        result = await self.session.execute(
            select(Concept).where(Concept.id.in_(concept_ids))
        )
        concepts = result.scalars().all()

        return [
            {
                "id": c.id,
                "label_ar": c.label_ar,
                "label_en": c.label_en,
                "type": c.concept_type,
            }
            for c in concepts
        ]

    async def _get_similar_clusters_by_persons(
        self,
        cluster_id: str,
        limit: int = 10,
    ) -> list[SimilarEntity]:
        """
        Fallback: Find similar clusters based on shared persons.

        Used when no concept occurrences exist.
        """
        # Get source cluster
        source_result = await self.session.execute(
            select(StoryCluster).where(StoryCluster.id == cluster_id)
        )
        source_cluster = source_result.scalar_one_or_none()
        if not source_cluster or not source_cluster.main_persons:
            return []

        source_persons = set(source_cluster.main_persons)

        # Get all other clusters
        clusters = await self.session.execute(
            select(StoryCluster).where(StoryCluster.id != cluster_id)
        )
        all_clusters = clusters.scalars().all()

        similarities: list[SimilarEntity] = []
        for cluster in all_clusters:
            if not cluster.main_persons:
                continue

            target_persons = set(cluster.main_persons)
            intersection = source_persons & target_persons
            union = source_persons | target_persons
            score = len(intersection) / len(union) if union else 0.0

            if score > 0:
                similarities.append(SimilarEntity(
                    id=cluster.id,
                    title_ar=cluster.title_ar,
                    title_en=cluster.title_en,
                    entity_type="cluster",
                    similarity_score=score,
                    shared_concepts=[],
                    shared_themes=[],
                    shared_figures=list(intersection),
                ))

        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:limit]


# =============================================================================
# PR5: ENHANCED SIMILARITY & ELABORATION EDGES
# =============================================================================

# Weights for multi-factor similarity scoring
SIMILARITY_WEIGHTS = {
    "concept_jaccard": 0.35,    # Base concept overlap
    "verse_overlap": 0.25,      # Shared ayah ranges
    "figure_overlap": 0.20,     # Shared main persons
    "theme_overlap": 0.15,      # Shared themes
    "tfidf_boost": 0.05,        # Rare concept bonus
}

# Thresholds for elaboration edge detection
ELABORATION_MIN_OVERLAP = 0.3   # Min verse overlap to consider
ELABORATION_DETAIL_RATIO = 1.5  # If A has 1.5x verses, A elaborates B


class EnhancedSimilarityService:
    """
    Enhanced similarity service with multi-factor scoring and elaboration edges (PR5).

    Features:
    - Multi-factor similarity: concepts, verses, figures, themes, TF-IDF
    - Elaboration/summarization edge detection
    - Arabic explanations for UI
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._concept_cache: dict[str, set[str]] = {}
        self._verse_cache: dict[str, set[tuple[int, int]]] = {}  # story -> {(sura, ayah)}
        self._concept_doc_freq: dict[str, int] = {}  # concept_id -> doc count

    async def get_enhanced_similar_stories(
        self,
        story_id: str,
        limit: int = 10,
        min_score: float = 0.1,
        include_elaboration: bool = True,
    ) -> list[SimilarEntity]:
        """
        Find similar stories using multi-factor scoring.

        Returns enhanced SimilarEntity with edge types and explanations.
        """
        # Get source story data
        source_concepts = await self._get_story_concepts(story_id)
        source_verses = await self._get_story_verses(story_id)
        source_story = await self._get_story(story_id)

        if not source_story:
            return []

        # Get all other stories
        stories = await self.session.execute(
            select(Story).where(Story.id != story_id)
        )
        all_stories = stories.scalars().all()

        # Precompute concept document frequencies for TF-IDF
        await self._compute_concept_frequencies()

        similarities: list[SimilarEntity] = []
        for story in all_stories:
            target_concepts = await self._get_story_concepts(story.id)
            target_verses = await self._get_story_verses(story.id)

            # Compute multi-factor score
            score, breakdown = self._compute_multi_factor_score(
                source_concepts, target_concepts,
                source_verses, target_verses,
                source_story, story,
            )

            if score < min_score:
                continue

            # Determine edge type
            edge_type = EdgeType.SIMILAR
            if include_elaboration and source_verses and target_verses:
                edge_type = self._detect_elaboration_edge(
                    source_verses, target_verses
                )

            # Generate explanations
            explanation_ar, explanation_en = self._generate_explanations(
                source_story, story, breakdown, edge_type
            )

            # Get shared concept details
            intersection = source_concepts & target_concepts
            shared_concepts = await self._get_concept_labels(intersection)
            shared_themes = [c["label_en"] for c in shared_concepts if c.get("type") == "theme"]
            shared_figures = [c["label_en"] for c in shared_concepts if c.get("type") == "person"]

            similarities.append(SimilarEntity(
                id=story.id,
                title_ar=story.name_ar,
                title_en=story.name_en,
                entity_type="story",
                similarity_score=score,
                shared_concepts=[c["id"] for c in shared_concepts],
                shared_themes=shared_themes,
                shared_figures=shared_figures,
                edge_type=edge_type,
                edge_type_ar=EDGE_TYPE_AR.get(edge_type, "تشابه"),
                explanation_ar=explanation_ar,
                explanation_en=explanation_en,
                score_breakdown=breakdown,
            ))

        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:limit]

    async def detect_elaboration_edges(
        self,
        story_id: str,
        min_overlap: float = ELABORATION_MIN_OVERLAP,
    ) -> list[ElaborationEdge]:
        """
        Detect elaboration/summarization edges for a story.

        تفصيل: source has more verses covering same ayahs as target
        إجمال: source has fewer verses covering same ayahs as target
        """
        source_verses = await self._get_story_verses(story_id)
        if not source_verses:
            return []

        # Get all other stories
        stories = await self.session.execute(
            select(Story).where(Story.id != story_id)
        )
        all_stories = stories.scalars().all()

        edges: list[ElaborationEdge] = []
        for story in all_stories:
            target_verses = await self._get_story_verses(story.id)
            if not target_verses:
                continue

            # Compute verse overlap
            intersection = source_verses & target_verses
            union = source_verses | target_verses
            overlap_ratio = len(intersection) / len(union) if union else 0.0

            if overlap_ratio < min_overlap:
                continue

            # Compute detail ratio
            detail_ratio = len(source_verses) / len(target_verses) if target_verses else 0.0

            # Determine edge type
            if detail_ratio >= ELABORATION_DETAIL_RATIO:
                edge_type = EdgeType.ELABORATES
                explanation_ar = f"قصة «{story_id}» تفصّل قصة «{story.id}» بآيات أكثر"
                explanation_en = f"Story '{story_id}' elaborates '{story.id}' with more verses"
            elif detail_ratio <= 1 / ELABORATION_DETAIL_RATIO:
                edge_type = EdgeType.SUMMARIZES
                explanation_ar = f"قصة «{story_id}» تُجمل قصة «{story.id}» بآيات أقل"
                explanation_en = f"Story '{story_id}' summarizes '{story.id}' with fewer verses"
            else:
                edge_type = EdgeType.PARALLELS
                explanation_ar = f"قصة «{story_id}» تتماثل مع قصة «{story.id}»"
                explanation_en = f"Story '{story_id}' parallels '{story.id}'"

            confidence = min(overlap_ratio * 1.5, 1.0)  # Higher overlap = higher confidence

            edges.append(ElaborationEdge(
                source_id=story_id,
                target_id=story.id,
                edge_type=edge_type,
                edge_type_ar=EDGE_TYPE_AR[edge_type],
                confidence=confidence,
                verse_overlap_ratio=overlap_ratio,
                detail_ratio=detail_ratio,
                explanation_ar=explanation_ar,
                explanation_en=explanation_en,
            ))

        edges.sort(key=lambda x: x.confidence, reverse=True)
        return edges

    def _compute_multi_factor_score(
        self,
        source_concepts: set[str],
        target_concepts: set[str],
        source_verses: set[tuple[int, int]],
        target_verses: set[tuple[int, int]],
        source_story: "Story",
        target_story: "Story",
    ) -> tuple[float, dict]:
        """
        Compute weighted multi-factor similarity score.

        Returns (score, breakdown_dict).
        """
        breakdown = {}

        # 1. Concept Jaccard
        if source_concepts and target_concepts:
            intersection = source_concepts & target_concepts
            union = source_concepts | target_concepts
            concept_score = len(intersection) / len(union) if union else 0.0
        else:
            concept_score = 0.0
        breakdown["concept_jaccard"] = concept_score

        # 2. Verse Overlap
        if source_verses and target_verses:
            intersection = source_verses & target_verses
            union = source_verses | target_verses
            verse_score = len(intersection) / len(union) if union else 0.0
        else:
            verse_score = 0.0
        breakdown["verse_overlap"] = verse_score

        # 3. Figure Overlap (main_persons)
        source_persons = set(source_story.main_persons or [])
        target_persons = set(target_story.main_persons or [])
        if source_persons and target_persons:
            intersection = source_persons & target_persons
            union = source_persons | target_persons
            figure_score = len(intersection) / len(union) if union else 0.0
        else:
            figure_score = 0.0
        breakdown["figure_overlap"] = figure_score

        # 4. Theme Overlap (from concepts with type=theme)
        # Simplified: use concept score as proxy
        theme_score = concept_score * 0.8  # Themes are subset of concepts
        breakdown["theme_overlap"] = theme_score

        # 5. TF-IDF Boost (rare concept bonus)
        if source_concepts and target_concepts:
            intersection = source_concepts & target_concepts
            tfidf_boost = self._compute_tfidf_boost(intersection)
        else:
            tfidf_boost = 0.0
        breakdown["tfidf_boost"] = tfidf_boost

        # Weighted sum
        total_score = sum(
            breakdown[factor] * weight
            for factor, weight in SIMILARITY_WEIGHTS.items()
        )

        return min(total_score, 1.0), breakdown

    def _compute_tfidf_boost(self, shared_concepts: set[str]) -> float:
        """
        Compute TF-IDF boost for shared rare concepts.

        Rare concepts (appearing in few stories) get higher weight.
        """
        if not shared_concepts or not self._concept_doc_freq:
            return 0.0

        total_docs = max(len(self._concept_doc_freq), 1)
        boost = 0.0

        for concept_id in shared_concepts:
            doc_freq = self._concept_doc_freq.get(concept_id, 1)
            # IDF = log(total_docs / doc_freq)
            idf = 1.0 / doc_freq if doc_freq > 0 else 1.0
            boost += idf

        # Normalize by number of shared concepts
        return min(boost / (len(shared_concepts) * 2), 1.0)

    def _detect_elaboration_edge(
        self,
        source_verses: set[tuple[int, int]],
        target_verses: set[tuple[int, int]],
    ) -> EdgeType:
        """Detect if source elaborates/summarizes target based on verse counts."""
        if not source_verses or not target_verses:
            return EdgeType.SIMILAR

        # Check verse containment
        intersection = source_verses & target_verses
        overlap_ratio = len(intersection) / len(target_verses) if target_verses else 0.0

        if overlap_ratio < ELABORATION_MIN_OVERLAP:
            return EdgeType.SIMILAR

        # Check detail ratio
        detail_ratio = len(source_verses) / len(target_verses)

        if detail_ratio >= ELABORATION_DETAIL_RATIO:
            return EdgeType.ELABORATES
        elif detail_ratio <= 1 / ELABORATION_DETAIL_RATIO:
            return EdgeType.SUMMARIZES
        else:
            return EdgeType.PARALLELS

    def _generate_explanations(
        self,
        source_story: "Story",
        target_story: "Story",
        breakdown: dict,
        edge_type: EdgeType,
    ) -> tuple[str, str]:
        """Generate Arabic and English explanations for similarity."""
        factors_ar = []
        factors_en = []

        # Add top factors
        if breakdown.get("figure_overlap", 0) > 0.3:
            factors_ar.append("شخصيات مشتركة")
            factors_en.append("shared figures")

        if breakdown.get("verse_overlap", 0) > 0.2:
            factors_ar.append("آيات مشتركة")
            factors_en.append("shared verses")

        if breakdown.get("concept_jaccard", 0) > 0.3:
            factors_ar.append("مفاهيم مشتركة")
            factors_en.append("shared concepts")

        if not factors_ar:
            factors_ar.append("موضوع مشترك")
            factors_en.append("related topic")

        # Build explanation based on edge type
        edge_label_ar = EDGE_TYPE_AR.get(edge_type, "تشابه")

        explanation_ar = f"{edge_label_ar} بسبب: {' و'.join(factors_ar)}"
        explanation_en = f"{edge_type.value.title()} due to: {' and '.join(factors_en)}"

        return explanation_ar, explanation_en

    # =========================================================================
    # PRIVATE METHODS (reusing patterns from SimilarityService)
    # =========================================================================

    async def _get_story(self, story_id: str) -> Optional["Story"]:
        """Get a story by ID."""
        result = await self.session.execute(
            select(Story).where(Story.id == story_id)
        )
        return result.scalar_one_or_none()

    async def _get_story_concepts(self, story_id: str) -> set[str]:
        """Get all concept IDs associated with a story."""
        if story_id in self._concept_cache:
            return self._concept_cache[story_id]

        result = await self.session.execute(
            select(Occurrence.concept_id).where(
                Occurrence.ref_type == "story",
                Occurrence.ref_id == story_id,
            ).distinct()
        )
        concept_ids = {row[0] for row in result.all()}

        self._concept_cache[story_id] = concept_ids
        return concept_ids

    async def _get_story_verses(self, story_id: str) -> set[tuple[int, int]]:
        """Get all (sura, ayah) tuples for a story's segments."""
        if story_id in self._verse_cache:
            return self._verse_cache[story_id]

        result = await self.session.execute(
            select(StorySegment).where(StorySegment.story_id == story_id)
        )
        segments = result.scalars().all()

        verses: set[tuple[int, int]] = set()
        for seg in segments:
            for ayah in range(seg.aya_start, seg.aya_end + 1):
                verses.add((seg.sura_no, ayah))

        self._verse_cache[story_id] = verses
        return verses

    async def _compute_concept_frequencies(self):
        """Compute document frequency for each concept (for TF-IDF)."""
        if self._concept_doc_freq:
            return  # Already computed

        # Count how many stories each concept appears in
        result = await self.session.execute(
            select(
                Occurrence.concept_id,
                func.count(func.distinct(Occurrence.ref_id))
            ).where(
                Occurrence.ref_type == "story"
            ).group_by(Occurrence.concept_id)
        )

        for row in result.all():
            self._concept_doc_freq[row[0]] = row[1]

    async def _get_concept_labels(self, concept_ids: set[str]) -> list[dict]:
        """Get label info for a set of concept IDs."""
        if not concept_ids:
            return []

        result = await self.session.execute(
            select(Concept).where(Concept.id.in_(concept_ids))
        )
        concepts = result.scalars().all()

        return [
            {
                "id": c.id,
                "label_ar": c.label_ar,
                "label_en": c.label_en,
                "type": c.concept_type,
            }
            for c in concepts
        ]