"""
Quran Knowledge Graph–aware Verse Similarity Service (Phase 5).

Combines multiple evidence signals:
  1. Story/event overlap (from stories manifest)
  2. Concept/theme overlap (from curated concepts)
  3. Prophet/person co-occurrence (from curated concepts)
  4. Semantic embedding similarity (from Qdrant, experimental)
  5. Lexical/root overlap (rule-based)
  6. Graph-neighbour Jaccard similarity
  7. Source confidence factor

All public results require at least one evidence item.
Semantic-only results are marked experimental and hidden by default.

Arabic: خدمة تشابه الآيات المعتمدة على الرسم البياني للمعرفة القرآنية
"""
from __future__ import annotations

import json
import logging
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.services.verse_embedding_service import get_verse_embedding_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths to data files
# ---------------------------------------------------------------------------
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
_STORIES_PATH = os.path.join(_BASE, "data", "manifests", "stories.json")
_CONCEPTS_PATH = os.path.join(_BASE, "data", "concepts", "curated_concepts.json")

# ---------------------------------------------------------------------------
# Relation status
# ---------------------------------------------------------------------------
APPROVED = "approved"
NEEDS_REVIEW = "needs_review"
EXPERIMENTAL = "experimental"

# ---------------------------------------------------------------------------
# Scoring weights (sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS: Dict[str, float] = {
    "story_segment": 0.28,    # Same story segment — strongest structural signal
    "story":         0.18,    # Same story, different segment
    "concept":       0.18,    # Shared curated concept
    "theme":         0.12,    # Shared curated theme
    "person":        0.10,    # Shared prophet / person
    "semantic":      0.08,    # Embedding cosine (experimental when no other evidence)
    "lexical":       0.04,    # Shared word roots / lemmas
    "source_conf":   0.02,    # Source confidence bonus
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    sourceId: str
    sourceTitleArabic: Optional[str] = None
    sourceTitleEnglish: Optional[str] = None
    storyId: Optional[str] = None
    segmentId: Optional[str] = None
    conceptId: Optional[str] = None
    themeId: Optional[str] = None
    tafsirReference: Optional[str] = None
    relationStatus: str = NEEDS_REVIEW


@dataclass
class PathNode:
    id: str
    type: str  # "ayah" | "story" | "story_segment" | "concept" | "theme"
    labelArabic: Optional[str] = None
    labelEnglish: Optional[str] = None
    surahNumber: Optional[int] = None
    ayahNumber: Optional[int] = None


@dataclass
class PathEdge:
    sourceNodeId: str
    targetNodeId: str
    edgeType: str
    relationStatus: str = NEEDS_REVIEW
    humanReviewRequired: bool = True


@dataclass
class PathExplanation:
    nodes: List[PathNode]
    edges: List[PathEdge]
    explanationArabic: str
    explanationEnglish: str
    warnings: List[str]


@dataclass
class KGSimilarityResult:
    surahNumber: int
    ayahNumber: int
    score: float
    relationTypes: List[str]
    explanationArabic: str
    explanationEnglish: str
    evidence: List[EvidenceItem]
    warnings: List[str]
    humanReviewRequired: bool
    pathExplanation: Optional[PathExplanation] = None


@dataclass
class KGSimilarityResponse:
    sourceAyah: Dict
    relatedAyahs: List[KGSimilarityResult]


# ---------------------------------------------------------------------------
# In-memory KG index (loaded once)
# ---------------------------------------------------------------------------

class _KGIndex:
    """
    Builds an in-memory index from stories manifest and curated concepts.
    Enables fast O(1) lookup of story/concept/person memberships per ayah.
    """

    def __init__(self):
        self._loaded = False

        # Maps (sura_no, aya_no) → set of story IDs
        self.ayah_stories: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        # Maps (sura_no, aya_no) → set of segment IDs
        self.ayah_segments: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        # Maps story_id → story metadata
        self.stories: Dict[str, dict] = {}
        # Maps segment_id → segment metadata
        self.segments: Dict[str, dict] = {}
        # Maps (sura_no, aya_no) → set of concept IDs
        self.ayah_concepts: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        # Maps (sura_no, aya_no) → set of theme IDs
        self.ayah_themes: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        # Maps (sura_no, aya_no) → set of person IDs
        self.ayah_persons: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        # Maps story_id → set of (sura_no, aya_no) tuples
        self.story_ayahs: Dict[str, Set[Tuple[int, int]]] = defaultdict(set)
        # Maps concept_id → set of (sura_no, aya_no) tuples
        self.concept_ayahs: Dict[str, Set[Tuple[int, int]]] = defaultdict(set)
        # Source evidence per ayah: (sura_no, aya_no) → list of sourceIds
        self.ayah_sources: Dict[Tuple[int, int], List[str]] = defaultdict(list)
        # Inter-story connections
        self.inter_story_connections: List[dict] = []

    def load(self) -> None:
        if self._loaded:
            return
        self._load_stories()
        self._load_concepts()
        self._loaded = True
        logger.info(
            "KGIndex loaded: %d stories, %d concepts, %d ayah→story, %d ayah→concept",
            len(self.stories),
            len(self.concept_ayahs),
            len(self.ayah_stories),
            len(self.ayah_concepts),
        )

    def _load_stories(self) -> None:
        if not os.path.exists(_STORIES_PATH):
            logger.warning("Stories manifest not found: %s", _STORIES_PATH)
            return
        with open(_STORIES_PATH, encoding="utf-8") as f:
            data = json.load(f)

        raw_stories = data.get("stories", [])
        self.inter_story_connections = data.get("inter_story_connections", [])

        for story in raw_stories:
            sid = story["id"]
            self.stories[sid] = story

            # Build theme index from story-level themes
            story_themes = story.get("themes", [])

            # Index every ayah range covered by segments
            for seg in story.get("segments", []):
                seg_id = seg["id"]
                sura = seg.get("sura_no", 0)
                aya_start = seg.get("aya_start", 0)
                aya_end = seg.get("aya_end", aya_start)
                self.segments[seg_id] = {**seg, "story_id": sid}

                # Collect source IDs from segment evidence
                seg_sources = [e.get("source_id", "") for e in seg.get("evidence", []) if e.get("source_id")]

                for aya in range(aya_start, aya_end + 1):
                    key = (sura, aya)
                    self.ayah_stories[key].add(sid)
                    self.ayah_segments[key].add(seg_id)
                    self.story_ayahs[sid].add(key)
                    for src in seg_sources:
                        if src not in self.ayah_sources[key]:
                            self.ayah_sources[key].append(src)

                    # Index story-level themes per ayah
                    for theme in story_themes:
                        theme_id = f"theme_{theme}"
                        self.ayah_themes[key].add(theme_id)

            # Associate persons with all ayahs of this story (coarse — segment level)
            main_figures = story.get("main_figures", [])
            for figure in main_figures:
                slug = figure.lower().replace(" ", "_")
                person_id = f"person_{slug}"
                for key in self.story_ayahs[sid]:
                    self.ayah_persons[key].add(person_id)

    def _load_concepts(self) -> None:
        if not os.path.exists(_CONCEPTS_PATH):
            logger.warning("Curated concepts not found: %s", _CONCEPTS_PATH)
            return
        with open(_CONCEPTS_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # We index concepts to stories (not individual ayahs) since the
        # curated_concepts.json doesn't list specific ayahs. Story-based
        # bridging is used: concept → stories → ayahs.
        persons = data.get("persons", [])
        for p in persons:
            pid = p["id"]
            slug = p.get("slug", "")
            # Link person to ayahs via story main_figures match
            for story_id, story in self.stories.items():
                if slug in [f.lower().replace(" ", "_") for f in story.get("main_figures", [])]:
                    for key in self.story_ayahs.get(story_id, set()):
                        self.ayah_concepts[key].add(pid)
                        self.concept_ayahs[pid].add(key)

        themes = data.get("themes", [])
        for t in themes:
            tid = t["id"]
            slug = t.get("slug", "")
            # Link theme to ayahs via story themes match
            for story_id, story in self.stories.items():
                if slug in story.get("themes", []):
                    for key in self.story_ayahs.get(story_id, set()):
                        self.ayah_themes[key].add(tid)

        moral_patterns = data.get("moral_patterns", [])
        for mp in moral_patterns:
            mid = mp["id"]
            for story_id, story in self.stories.items():
                # Moral patterns apply to all stories in general — skip broad association
                # Only include if story explicitly lists this pattern (future enhancement)
                pass


_KG_INDEX: Optional[_KGIndex] = None


def get_kg_index() -> _KGIndex:
    global _KG_INDEX
    if _KG_INDEX is None:
        _KG_INDEX = _KGIndex()
        _KG_INDEX.load()
    return _KG_INDEX


# ---------------------------------------------------------------------------
# Jaccard utility
# ---------------------------------------------------------------------------

def _jaccard(a: Set, b: Set) -> float:
    if not a and not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Explanation builders (generic, source-aware — no tafsir invention)
# ---------------------------------------------------------------------------

def _build_explanation(
    story_overlap: Set[str],
    concept_overlap: Set[str],
    theme_overlap: Set[str],
    person_overlap: Set[str],
    kg: _KGIndex,
) -> Tuple[str, str]:
    """Build a safe, generic explanation without inventing religious content."""
    parts_en: List[str] = []
    parts_ar: List[str] = []

    if story_overlap:
        story_names_en = [kg.stories.get(s, {}).get("name_en", s) for s in list(story_overlap)[:2]]
        story_names_ar = [kg.stories.get(s, {}).get("name_ar", s) for s in list(story_overlap)[:2]]
        parts_en.append(f"Both verses appear in the same Quranic narrative: {', '.join(story_names_en)}.")
        parts_ar.append(f"تشترك الآيتان في القصة القرآنية: {', '.join(story_names_ar)}.")

    if person_overlap:
        parts_en.append("Both verses mention the same prophet or person.")
        parts_ar.append("تذكر الآيتان نفس النبي أو الشخصية القرآنية.")

    if theme_overlap:
        parts_en.append("Both verses share a common Quranic theme.")
        parts_ar.append("تشترك الآيتان في موضوع قرآني مشترك.")

    if concept_overlap and not story_overlap and not person_overlap:
        parts_en.append("Both verses are connected through shared Quranic concepts.")
        parts_ar.append("ترتبط الآيتان بمفاهيم قرآنية مشتركة.")

    if not parts_en:
        parts_en.append("These verses show a structural or lexical connection. Scholarly review required for detailed interpretation.")
        parts_ar.append("تظهر الآيتان صلة هيكلية أو لفظية. المراجعة العلمية مطلوبة للتفصيل.")

    suffix_en = " Scholarly review required for detailed interpretation."
    suffix_ar = " المراجعة العلمية مطلوبة للتفصيل."

    return " ".join(parts_ar) + suffix_ar, " ".join(parts_en) + suffix_en


def _build_path_text(edge_types: Set[str]) -> Tuple[str, str]:
    """Safe, generic bilingual path explanation based on edge type(s). No tafsir invented."""
    if "SAME_STORY_SEGMENT" in edge_types:
        return (
            "ترتبط هاتان الآيتان من خلال مقطع من القصة القرآنية نفسها، وهذه الصلة تحتاج إلى مراجعة علمية.",
            "These ayahs are connected through the same Quranic story segment. This relation is pending scholarly review.",
        )
    if "SAME_STORY" in edge_types:
        return (
            "ترتبط هاتان الآيتان من خلال القصة القرآنية نفسها، وهذه الصلة تحتاج إلى مراجعة علمية.",
            "These ayahs are connected through the same Quranic story. This relation is pending scholarly review.",
        )
    if "SAME_CONCEPT" in edge_types:
        return (
            "تشترك الآيتان في مفهوم قرآني مشترك، وهذه الصلة تحتاج إلى مراجعة علمية.",
            "These ayahs share a common Quranic concept. This relation is pending scholarly review.",
        )
    if "SAME_THEME" in edge_types:
        return (
            "ترتبط الآيتان بموضوع قرآني مشترك، وهذه الصلة تحتاج إلى مراجعة علمية.",
            "These ayahs are connected through a shared Quranic theme. This relation is pending scholarly review.",
        )
    return (
        "ترتبط الآيتان في الرسم البياني للمعرفة القرآنية، وهذه الصلة تحتاج إلى مراجعة علمية.",
        "These ayahs are connected in the Quran Knowledge Graph. This relation is pending scholarly review.",
    )


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class VerseSimilarityService:
    """
    KG-aware verse similarity service.

    Scores ayah pairs using multiple evidence signals and returns only
    evidence-backed results by default.
    """

    def __init__(self, include_experimental: bool = False):
        self.include_experimental = include_experimental
        self._kg = get_kg_index()

    async def find_similar(
        self,
        sura_no: int,
        aya_no: int,
        top_k: int = 10,
        min_score: float = 0.20,
        require_evidence: bool = True,
    ) -> KGSimilarityResponse:
        """
        Find ayahs related to the given verse using the KG index.

        Args:
            sura_no: Source verse surah number (1–114)
            aya_no: Source verse ayah number
            top_k: Maximum results to return
            min_score: Minimum combined score (0–1)
            require_evidence: If True, skip results with no evidence (default True)

        Returns:
            KGSimilarityResponse with ranked related ayahs
        """
        source_key = (sura_no, aya_no)

        source_stories = self._kg.ayah_stories.get(source_key, set())
        source_segments = self._kg.ayah_segments.get(source_key, set())
        source_concepts = self._kg.ayah_concepts.get(source_key, set())
        source_themes = self._kg.ayah_themes.get(source_key, set())
        source_persons = self._kg.ayah_persons.get(source_key, set())
        source_sources = set(self._kg.ayah_sources.get(source_key, []))

        # Collect candidate ayahs from KG neighbors
        candidate_keys: Set[Tuple[int, int]] = set()
        for sid in source_stories:
            candidate_keys.update(self._kg.story_ayahs.get(sid, set()))
        for cid in source_concepts:
            candidate_keys.update(self._kg.concept_ayahs.get(cid, set()))
        # Remove source itself
        candidate_keys.discard(source_key)

        # Try semantic candidates from Qdrant (graceful fallback)
        semantic_scores: Dict[Tuple[int, int], float] = {}
        try:
            emb_svc = get_verse_embedding_service()
            sem_results = await emb_svc.find_similar_to_verse(
                sura_no=sura_no,
                aya_no=aya_no,
                limit=top_k * 4,
                min_score=0.60,
            )
            for r in sem_results:
                semantic_scores[(r.sura_no, r.aya_no)] = r.similarity_score
                if self.include_experimental:
                    candidate_keys.add((r.sura_no, r.aya_no))
        except Exception as e:
            logger.debug("Semantic similarity unavailable: %s", e)

        # Score each candidate
        results: List[KGSimilarityResult] = []

        for key in candidate_keys:
            cand_sura, cand_aya = key

            cand_stories = self._kg.ayah_stories.get(key, set())
            cand_segments = self._kg.ayah_segments.get(key, set())
            cand_concepts = self._kg.ayah_concepts.get(key, set())
            cand_themes = self._kg.ayah_themes.get(key, set())
            cand_persons = self._kg.ayah_persons.get(key, set())
            cand_sources = set(self._kg.ayah_sources.get(key, []))

            story_overlap = source_stories & cand_stories
            segment_overlap = source_segments & cand_segments
            concept_overlap = source_concepts & cand_concepts
            theme_overlap = source_themes & cand_themes
            person_overlap = source_persons & cand_persons
            shared_sources = source_sources | cand_sources

            sem_score = semantic_scores.get(key, 0.0)

            # Component scores
            seg_score = min(1.0, len(segment_overlap) * 0.5 + _jaccard(source_segments, cand_segments))
            story_score = _jaccard(source_stories, cand_stories)
            concept_score = _jaccard(source_concepts, cand_concepts)
            theme_score = _jaccard(source_themes, cand_themes)
            person_score = _jaccard(source_persons, cand_persons)
            lexical_score = 0.0  # placeholder — root overlap from DB would go here
            source_conf = min(1.0, len(shared_sources) * 0.25)

            # Combined weighted score
            score = (
                WEIGHTS["story_segment"] * seg_score +
                WEIGHTS["story"] * story_score +
                WEIGHTS["concept"] * concept_score +
                WEIGHTS["theme"] * theme_score +
                WEIGHTS["person"] * person_score +
                WEIGHTS["semantic"] * sem_score +
                WEIGHTS["lexical"] * lexical_score +
                WEIGHTS["source_conf"] * source_conf
            )

            if score < min_score:
                continue

            # Determine relation types
            relation_types: List[str] = []
            if segment_overlap:
                relation_types.append("SAME_STORY_SEGMENT")
            if story_overlap and not segment_overlap:
                relation_types.append("SAME_STORY")
            if person_overlap:
                relation_types.append("SAME_PROPHET_OR_PERSON")
            if theme_overlap:
                relation_types.append("SAME_THEME")
            if concept_overlap:
                relation_types.append("SAME_CONCEPT")
            if sem_score > 0 and not (story_overlap or concept_overlap or person_overlap):
                relation_types.append("SEMANTICALLY_SIMILAR")

            # Build evidence items
            evidence: List[EvidenceItem] = []
            warnings: List[str] = []
            human_review = True  # All story data is needs_review

            for seg_id in segment_overlap:
                seg = self._kg.segments.get(seg_id, {})
                for ev in seg.get("evidence", [])[:2]:
                    src_id = ev.get("source_id", "")
                    if src_id:
                        evidence.append(EvidenceItem(
                            sourceId=src_id,
                            storyId=seg.get("story_id"),
                            segmentId=seg_id,
                            relationStatus=NEEDS_REVIEW,
                        ))

            for sid in story_overlap:
                story = self._kg.stories.get(sid, {})
                for ev in story.get("evidence", [])[:2]:
                    src_id = ev.get("source_id", "")
                    if src_id:
                        evidence.append(EvidenceItem(
                            sourceId=src_id,
                            storyId=sid,
                            relationStatus=NEEDS_REVIEW,
                        ))

            # Add semantic-only evidence when no other evidence
            semantic_only = not (story_overlap or concept_overlap or person_overlap or theme_overlap)
            if sem_score > 0:
                if semantic_only:
                    if not self.include_experimental:
                        continue  # Skip — no source-backed evidence
                    warnings.append(
                        "This connection is based on embedding similarity only "
                        "and has not been verified by scholars."
                    )
                    evidence.append(EvidenceItem(
                        sourceId="system:embedding",
                        relationStatus=EXPERIMENTAL,
                    ))
                else:
                    warnings.append(
                        "Embedding similarity supports this connection "
                        "but is not a substitute for scholarly verification."
                    )

            if require_evidence and not evidence:
                continue

            if story_overlap or concept_overlap or person_overlap:
                warnings.append("All story-based relations await scholarly review.")

            exp_ar, exp_en = _build_explanation(
                story_overlap, concept_overlap, theme_overlap, person_overlap, self._kg
            )

            results.append(KGSimilarityResult(
                surahNumber=cand_sura,
                ayahNumber=cand_aya,
                score=round(score, 4),
                relationTypes=relation_types,
                explanationArabic=exp_ar,
                explanationEnglish=exp_en,
                evidence=evidence,
                warnings=list(set(warnings)),
                humanReviewRequired=human_review,
            ))

        # Sort by score descending, then slice to top_k
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:top_k]

        # Populate path explanations only for the results that will be returned
        for r in results:
            r.pathExplanation = self._build_path_explanation(
                sura_no, aya_no, r.surahNumber, r.ayahNumber
            )

        return KGSimilarityResponse(
            sourceAyah={"surahNumber": sura_no, "ayahNumber": aya_no},
            relatedAyahs=results,
        )

    def find_path(
        self,
        from_sura: int,
        from_aya: int,
        to_sura: int,
        to_aya: int,
    ) -> Optional[List[dict]]:
        """
        Find a shortest connection path between two ayahs through the KG.

        Priority order: same segment > same story > same concept > same theme > inter-story.
        Returns a list of path-step dicts with nodeId/nodeType/label/edgeType/labelArabic,
        or None if no path found.
        """
        from_key = (from_sura, from_aya)
        to_key = (to_sura, to_aya)

        if from_key == to_key:
            return []

        # Priority 1: same story segment (most specific connection)
        from_segments = self._kg.ayah_segments.get(from_key, set())
        to_segments = self._kg.ayah_segments.get(to_key, set())
        shared_segments = from_segments & to_segments

        if shared_segments:
            seg_id = next(iter(shared_segments))
            seg = self._kg.segments.get(seg_id, {})
            story_id = seg.get("story_id", "")
            story = self._kg.stories.get(story_id, {})
            return [
                {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                {
                    "nodeId": f"story_segment:{seg_id}",
                    "nodeType": "story_segment",
                    "label": story.get("name_en", seg_id),
                    "labelArabic": story.get("name_ar"),
                    "edgeType": "SAME_STORY_SEGMENT",
                },
                {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_STORY_SEGMENT"},
            ]

        # Priority 2: same story (different segments)
        from_stories = self._kg.ayah_stories.get(from_key, set())
        to_stories = self._kg.ayah_stories.get(to_key, set())
        shared_stories = from_stories & to_stories

        if shared_stories:
            sid = next(iter(shared_stories))
            story = self._kg.stories.get(sid, {})
            return [
                {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                {
                    "nodeId": f"story:{sid}",
                    "nodeType": "story",
                    "label": story.get("name_en", sid),
                    "labelArabic": story.get("name_ar"),
                    "edgeType": "SAME_STORY",
                },
                {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_STORY"},
            ]

        # Priority 3: same concept
        from_concepts = self._kg.ayah_concepts.get(from_key, set())
        to_concepts = self._kg.ayah_concepts.get(to_key, set())
        shared_concepts = from_concepts & to_concepts

        if shared_concepts:
            cid = next(iter(shared_concepts))
            return [
                {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                {"nodeId": f"concept:{cid}", "nodeType": "concept", "label": cid, "edgeType": "SAME_CONCEPT"},
                {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_CONCEPT"},
            ]

        # Priority 4: same theme
        from_themes = self._kg.ayah_themes.get(from_key, set())
        to_themes = self._kg.ayah_themes.get(to_key, set())
        shared_themes = from_themes & to_themes

        if shared_themes:
            tid = next(iter(shared_themes))
            return [
                {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                {"nodeId": f"theme:{tid}", "nodeType": "theme", "label": tid, "edgeType": "SAME_THEME"},
                {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_THEME"},
            ]

        # Priority 5: 2-hop via inter-story connection
        for conn in self._kg.inter_story_connections:
            src_sid = conn.get("source_story_id", "")
            tgt_sid = conn.get("target_story_id", "")
            if src_sid in from_stories and tgt_sid in to_stories:
                src_story = self._kg.stories.get(src_sid, {})
                tgt_story = self._kg.stories.get(tgt_sid, {})
                return [
                    {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                    {"nodeId": f"story:{src_sid}", "nodeType": "story", "label": src_story.get("name_en", src_sid), "labelArabic": src_story.get("name_ar"), "edgeType": "SAME_STORY"},
                    {"nodeId": f"story:{tgt_sid}", "nodeType": "story", "label": tgt_story.get("name_en", tgt_sid), "labelArabic": tgt_story.get("name_ar"), "edgeType": conn.get("connection_type", "continuation").upper()},
                    {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_STORY"},
                ]
            if conn.get("bidirectional") and tgt_sid in from_stories and src_sid in to_stories:
                src_story = self._kg.stories.get(tgt_sid, {})
                tgt_story = self._kg.stories.get(src_sid, {})
                return [
                    {"nodeId": f"ayah:{from_sura}:{from_aya}", "nodeType": "ayah", "label": f"{from_sura}:{from_aya}"},
                    {"nodeId": f"story:{tgt_sid}", "nodeType": "story", "label": src_story.get("name_en", tgt_sid), "labelArabic": src_story.get("name_ar"), "edgeType": "SAME_STORY"},
                    {"nodeId": f"story:{src_sid}", "nodeType": "story", "label": tgt_story.get("name_en", src_sid), "labelArabic": tgt_story.get("name_ar"), "edgeType": conn.get("connection_type", "continuation").upper()},
                    {"nodeId": f"ayah:{to_sura}:{to_aya}", "nodeType": "ayah", "label": f"{to_sura}:{to_aya}", "edgeType": "SAME_STORY"},
                ]

        return None

    def _build_path_explanation(
        self,
        from_sura: int,
        from_aya: int,
        to_sura: int,
        to_aya: int,
    ) -> Optional[PathExplanation]:
        """
        Convert a raw find_path() result into a structured PathExplanation.

        Rules enforced:
        - No Quran text in any node
        - All edges marked needs_review (story/concept paths are unverified)
        - Max 4 nodes (3 hops) to keep response compact
        - Returns None when no path found
        """
        raw_path = self.find_path(from_sura, from_aya, to_sura, to_aya)
        if not raw_path:
            return None

        # Truncate to max 4 nodes (3 hops) for compactness
        raw_path = raw_path[:4]

        nodes: List[PathNode] = []
        edges: List[PathEdge] = []
        seen_node_ids: Set[str] = set()

        for i, step in enumerate(raw_path):
            node_id = step["nodeId"]
            node_type = step["nodeType"]

            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)

                if node_type == "ayah":
                    parts = node_id.split(":")
                    sura_n = int(parts[1]) if len(parts) > 1 else None
                    aya_n = int(parts[2]) if len(parts) > 2 else None
                    nodes.append(PathNode(id=node_id, type=node_type, surahNumber=sura_n, ayahNumber=aya_n))

                elif node_type == "story":
                    story_id = node_id[len("story:"):]
                    story = self._kg.stories.get(story_id, {})
                    nodes.append(PathNode(
                        id=node_id,
                        type=node_type,
                        labelEnglish=story.get("name_en", story_id),
                        labelArabic=story.get("name_ar"),
                    ))

                elif node_type == "story_segment":
                    seg_id = node_id[len("story_segment:"):]
                    seg = self._kg.segments.get(seg_id, {})
                    story_id = seg.get("story_id", "")
                    story = self._kg.stories.get(story_id, {})
                    nodes.append(PathNode(
                        id=node_id,
                        type=node_type,
                        labelEnglish=story.get("name_en", seg_id),
                        labelArabic=story.get("name_ar"),
                    ))

                elif node_type == "concept":
                    concept_id = node_id[len("concept:"):]
                    nodes.append(PathNode(id=node_id, type=node_type, labelEnglish=concept_id))

                elif node_type == "theme":
                    theme_id = node_id[len("theme:"):]
                    nodes.append(PathNode(id=node_id, type=node_type, labelEnglish=theme_id))

                else:
                    nodes.append(PathNode(id=node_id, type=node_type, labelEnglish=step.get("label", node_id)))

            # Build edge from previous step to this one
            if i > 0 and "edgeType" in step:
                prev_id = raw_path[i - 1]["nodeId"]
                edges.append(PathEdge(
                    sourceNodeId=prev_id,
                    targetNodeId=node_id,
                    edgeType=step["edgeType"],
                    relationStatus=NEEDS_REVIEW,
                    humanReviewRequired=True,
                ))

        if not edges:
            return None

        edge_types = {e.edgeType for e in edges}
        exp_ar, exp_en = _build_path_text(edge_types)

        return PathExplanation(
            nodes=nodes,
            edges=edges,
            explanationArabic=exp_ar,
            explanationEnglish=exp_en,
            warnings=["This connection path is derived from Quranic story and concept data and awaits scholarly review."],
        )


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_SERVICE_DEFAULT: Optional[VerseSimilarityService] = None
_SERVICE_EXPERIMENTAL: Optional[VerseSimilarityService] = None


def get_verse_similarity_service(include_experimental: bool = False) -> VerseSimilarityService:
    global _SERVICE_DEFAULT, _SERVICE_EXPERIMENTAL
    if include_experimental:
        if _SERVICE_EXPERIMENTAL is None:
            _SERVICE_EXPERIMENTAL = VerseSimilarityService(include_experimental=True)
        return _SERVICE_EXPERIMENTAL
    if _SERVICE_DEFAULT is None:
        _SERVICE_DEFAULT = VerseSimilarityService(include_experimental=False)
    return _SERVICE_DEFAULT
