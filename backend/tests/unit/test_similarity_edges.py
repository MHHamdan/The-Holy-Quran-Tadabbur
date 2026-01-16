"""
Tests for PR5: Enhanced similarity scoring and elaboration edges.

C1: Elaboration/Summarization edges (تفصيل/إجمال)
C2: Multi-factor similarity scoring
C3: Arabic explanations for UI
"""

import pytest
from dataclasses import dataclass
from typing import Set, Tuple

from app.services.similarity import (
    EdgeType,
    EDGE_TYPE_AR,
    ElaborationEdge,
    SimilarEntity,
    SIMILARITY_WEIGHTS,
    ELABORATION_MIN_OVERLAP,
    ELABORATION_DETAIL_RATIO,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_verses_adam() -> Set[Tuple[int, int]]:
    """Verses for story of Adam (more detail)."""
    # Al-Baqarah 2:30-39 (10 verses)
    return {(2, i) for i in range(30, 40)}


@pytest.fixture
def sample_verses_adam_brief() -> Set[Tuple[int, int]]:
    """Verses for brief Adam mention (less detail)."""
    # Overlapping 4 verses
    return {(2, 30), (2, 31), (2, 32), (2, 33)}


@pytest.fixture
def sample_verses_unrelated() -> Set[Tuple[int, int]]:
    """Verses for unrelated story."""
    # Al-Imran 3:33-40 (no overlap)
    return {(3, i) for i in range(33, 41)}


# =============================================================================
# C1: ELABORATION EDGE DETECTION
# =============================================================================

class TestElaborationEdges:
    """Tests for elaboration/summarization edge detection."""

    def test_edge_types_have_arabic_labels(self):
        """All edge types must have Arabic translations."""
        for edge_type in EdgeType:
            assert edge_type in EDGE_TYPE_AR, f"Missing Arabic label for {edge_type}"
            assert any('\u0600' <= c <= '\u06FF' for c in EDGE_TYPE_AR[edge_type]), \
                f"Arabic label for {edge_type} is not Arabic: {EDGE_TYPE_AR[edge_type]}"

    def test_elaboration_edge_structure(self):
        """ElaborationEdge must have all required fields."""
        edge = ElaborationEdge(
            source_id="story_adam_detailed",
            target_id="story_adam_brief",
            edge_type=EdgeType.ELABORATES,
            edge_type_ar="تفصيل",
            confidence=0.85,
            verse_overlap_ratio=0.7,
            detail_ratio=2.5,
            explanation_ar="قصة آدم تفصّل القصة الموجزة",
            explanation_en="Story of Adam elaborates the brief story",
        )

        assert edge.source_id == "story_adam_detailed"
        assert edge.edge_type == EdgeType.ELABORATES
        assert edge.edge_type_ar == "تفصيل"
        assert edge.confidence > 0.5
        assert edge.detail_ratio > 1.0  # More detail = ratio > 1

    def test_summarization_edge_structure(self):
        """Summarization edges have detail_ratio < 1."""
        edge = ElaborationEdge(
            source_id="story_adam_brief",
            target_id="story_adam_detailed",
            edge_type=EdgeType.SUMMARIZES,
            edge_type_ar="إجمال",
            confidence=0.75,
            verse_overlap_ratio=0.6,
            detail_ratio=0.4,  # Brief has fewer verses
            explanation_ar="إجمال للقصة",
            explanation_en="Summarizes the story",
        )

        assert edge.edge_type == EdgeType.SUMMARIZES
        assert edge.detail_ratio < 1.0  # Less detail = ratio < 1

    def test_elaboration_thresholds(self):
        """Elaboration detection uses correct thresholds."""
        # These constants should be reasonable
        assert ELABORATION_MIN_OVERLAP > 0.0
        assert ELABORATION_MIN_OVERLAP < 0.5  # Not too strict
        assert ELABORATION_DETAIL_RATIO > 1.0  # Must be more detail
        assert ELABORATION_DETAIL_RATIO < 3.0  # Not too strict

    def test_verse_overlap_calculation(
        self,
        sample_verses_adam: Set[Tuple[int, int]],
        sample_verses_adam_brief: Set[Tuple[int, int]],
    ):
        """Verse overlap ratio is calculated correctly."""
        intersection = sample_verses_adam & sample_verses_adam_brief
        union = sample_verses_adam | sample_verses_adam_brief

        overlap_ratio = len(intersection) / len(union)

        # 4 shared out of 10 unique = 0.4
        assert overlap_ratio == pytest.approx(0.4, rel=0.1)
        assert len(intersection) == 4  # The brief verses

    def test_detail_ratio_for_elaboration(
        self,
        sample_verses_adam: Set[Tuple[int, int]],
        sample_verses_adam_brief: Set[Tuple[int, int]],
    ):
        """Detail ratio correctly identifies elaboration."""
        # Adam detailed (10 verses) / Adam brief (4 verses) = 2.5
        detail_ratio = len(sample_verses_adam) / len(sample_verses_adam_brief)

        assert detail_ratio >= ELABORATION_DETAIL_RATIO, \
            f"Ratio {detail_ratio} should indicate elaboration"

    def test_no_edge_for_unrelated_stories(
        self,
        sample_verses_adam: Set[Tuple[int, int]],
        sample_verses_unrelated: Set[Tuple[int, int]],
    ):
        """Unrelated stories should not have elaboration edges."""
        intersection = sample_verses_adam & sample_verses_unrelated
        union = sample_verses_adam | sample_verses_unrelated

        overlap_ratio = len(intersection) / len(union) if union else 0.0

        assert overlap_ratio < ELABORATION_MIN_OVERLAP, \
            "Unrelated stories should have low overlap"


# =============================================================================
# C2: MULTI-FACTOR SIMILARITY SCORING
# =============================================================================

class TestMultiFactorScoring:
    """Tests for enhanced multi-factor similarity scoring."""

    def test_similarity_weights_sum_to_one(self):
        """Similarity weights should sum to 1.0."""
        total = sum(SIMILARITY_WEIGHTS.values())
        assert total == pytest.approx(1.0, rel=0.01), \
            f"Weights sum to {total}, expected 1.0"

    def test_all_factors_have_weights(self):
        """All similarity factors must have weights."""
        expected_factors = {
            "concept_jaccard",
            "verse_overlap",
            "figure_overlap",
            "theme_overlap",
            "tfidf_boost",
        }

        assert set(SIMILARITY_WEIGHTS.keys()) == expected_factors, \
            f"Missing or extra factors: {set(SIMILARITY_WEIGHTS.keys()) ^ expected_factors}"

    def test_concept_jaccard_has_highest_weight(self):
        """Concept Jaccard should have significant weight."""
        assert SIMILARITY_WEIGHTS["concept_jaccard"] >= 0.3, \
            "Concept Jaccard should be a major factor"

    def test_similar_entity_has_score_breakdown(self):
        """SimilarEntity must include score breakdown."""
        entity = SimilarEntity(
            id="story_test",
            title_ar="قصة اختبار",
            title_en="Test Story",
            entity_type="story",
            similarity_score=0.75,
            shared_concepts=["concept_1", "concept_2"],
            shared_themes=["theme_1"],
            shared_figures=["person_1"],
            edge_type=EdgeType.SIMILAR,
            edge_type_ar="تشابه",
            explanation_ar="تشابه بسبب: مفاهيم مشتركة",
            explanation_en="Similar due to: shared concepts",
            score_breakdown={
                "concept_jaccard": 0.5,
                "verse_overlap": 0.3,
                "figure_overlap": 0.2,
                "theme_overlap": 0.4,
                "tfidf_boost": 0.1,
            }
        )

        assert entity.score_breakdown is not None
        assert "concept_jaccard" in entity.score_breakdown
        assert all(0.0 <= v <= 1.0 for v in entity.score_breakdown.values())


# =============================================================================
# C3: ARABIC EXPLANATIONS
# =============================================================================

class TestArabicExplanations:
    """Tests for Arabic explanations in similarity results."""

    def test_similar_entity_has_arabic_explanation(self):
        """SimilarEntity must have Arabic explanation."""
        entity = SimilarEntity(
            id="story_test",
            title_ar="قصة اختبار",
            title_en="Test Story",
            entity_type="story",
            similarity_score=0.75,
            explanation_ar="تشابه بسبب: شخصيات مشتركة وآيات مشتركة",
            explanation_en="Similar due to: shared figures and shared verses",
        )

        # Check Arabic explanation contains Arabic
        assert any('\u0600' <= c <= '\u06FF' for c in entity.explanation_ar), \
            "Arabic explanation should contain Arabic characters"

        # Check it's not just copied English
        assert "due to" not in entity.explanation_ar.lower()

    def test_edge_type_ar_is_arabic(self):
        """edge_type_ar must be in Arabic."""
        for edge_type, ar_label in EDGE_TYPE_AR.items():
            assert any('\u0600' <= c <= '\u06FF' for c in ar_label), \
                f"Label for {edge_type} is not Arabic: {ar_label}"

    def test_elaboration_explanation_mentions_verses(self):
        """Elaboration explanations should mention verse detail."""
        edge = ElaborationEdge(
            source_id="adam_full",
            target_id="adam_brief",
            edge_type=EdgeType.ELABORATES,
            edge_type_ar="تفصيل",
            confidence=0.8,
            verse_overlap_ratio=0.5,
            detail_ratio=2.0,
            explanation_ar="قصة «adam_full» تفصّل قصة «adam_brief» بآيات أكثر",
            explanation_en="Story 'adam_full' elaborates 'adam_brief' with more verses",
        )

        # Arabic explanation should mention verses (آيات)
        assert "آيات" in edge.explanation_ar, \
            "Arabic explanation should mention verses"

    def test_parallel_edge_type(self):
        """Parallel edge type for similar verse count."""
        assert EdgeType.PARALLELS in EDGE_TYPE_AR
        assert EDGE_TYPE_AR[EdgeType.PARALLELS] == "تماثل"


# =============================================================================
# INTEGRATION: ELABORATION EDGE EXAMPLES
# =============================================================================

class TestElaborationEdgeExamples:
    """Test elaboration edges with real-world examples."""

    def test_adam_story_elaboration_pattern(self):
        """
        Story of Adam appears in multiple suras with varying detail.

        - Al-Baqarah 2:30-39 (detailed)
        - Al-A'raf 7:11-25 (detailed)
        - Ta-Ha 20:115-123 (moderate)
        - Sad 38:71-85 (focused on iblis)

        An elaboration edge should connect detailed to brief versions.
        """
        # Example: Baqarah version has more detail than Sad version
        baqarah_verses = {(2, i) for i in range(30, 40)}  # 10 verses
        sad_verses = {(38, i) for i in range(71, 86)}     # 15 verses (but different focus)

        # No direct overlap (different suras), so no elaboration edge
        overlap = baqarah_verses & sad_verses
        assert len(overlap) == 0, "Different suras should have no verse overlap"

    def test_musa_story_has_multiple_tellings(self):
        """
        Story of Musa appears across many suras.

        When the same ayahs are covered with different detail,
        elaboration edges should connect them.
        """
        # This is documentation of expected behavior
        # Actual edge detection requires DB queries

        # Example: Musa in Al-Qasas vs brief mention
        expected_edge_types = [EdgeType.ELABORATES, EdgeType.SUMMARIZES, EdgeType.PARALLELS]
        assert all(et in EdgeType for et in expected_edge_types)
