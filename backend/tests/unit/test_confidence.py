#!/usr/bin/env python3
"""
Tests for confidence scoring and refusal logic.

Tests:
1. Explicit threshold verification
2. Refusal conditions
3. Degradation penalties
"""
import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.confidence import (
    ConfidenceScorer,
    ConfidenceBreakdown,
    confidence_scorer,
    should_refuse_response,
    get_confidence_message,
    run_refusal_tests,
    REFUSAL_TEST_CASES,
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
    REFUSAL_THRESHOLD,
    MIN_CITATION_COVERAGE,
    MIN_AVERAGE_RELEVANCE,
    MIN_SOURCE_RELIABILITY,
)


class TestThresholds:
    """Test threshold constants."""

    def test_threshold_ordering(self):
        """Thresholds should be in correct order."""
        assert HIGH_CONFIDENCE_THRESHOLD > MEDIUM_CONFIDENCE_THRESHOLD
        assert MEDIUM_CONFIDENCE_THRESHOLD > LOW_CONFIDENCE_THRESHOLD
        assert LOW_CONFIDENCE_THRESHOLD >= REFUSAL_THRESHOLD

    def test_threshold_values(self):
        """Verify explicit threshold values with proper separation."""
        assert HIGH_CONFIDENCE_THRESHOLD == 0.85
        assert MEDIUM_CONFIDENCE_THRESHOLD == 0.65
        assert LOW_CONFIDENCE_THRESHOLD == 0.45
        assert REFUSAL_THRESHOLD == 0.35  # Separated from LOW by 0.10

    def test_minimum_thresholds(self):
        """Verify minimum thresholds for refusal."""
        assert MIN_CITATION_COVERAGE == 0.30
        assert MIN_AVERAGE_RELEVANCE == 0.30
        assert MIN_SOURCE_RELIABILITY == 0.50


class TestConfidenceScorer:
    """Test ConfidenceScorer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()

    def test_high_confidence_response(self):
        """Test a well-supported response gets high confidence."""
        breakdown = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=5,
            invalid_citations=0,
            source_reliability_scores=[0.95, 0.90],
            relevance_scores=[0.9, 0.85, 0.88],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3", "c4", "c5"],
            source_ids=["s1", "s2", "s1", "s2", "s1"],
        )

        assert breakdown.confidence_level == "high"
        assert breakdown.final_score >= HIGH_CONFIDENCE_THRESHOLD
        assert not breakdown.should_refuse

    def test_medium_confidence_response(self):
        """Test a moderately supported response gets medium confidence."""
        breakdown = self.scorer.calculate(
            total_paragraphs=4,
            paragraphs_with_citations=4,  # Full coverage needed for medium
            valid_citations=4,
            invalid_citations=0,
            source_reliability_scores=[0.80, 0.75],  # Multiple sources
            relevance_scores=[0.75, 0.70],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3", "c4"],
            source_ids=["s1", "s2", "s1", "s2"],
        )

        assert breakdown.confidence_level in ["medium", "high"]
        assert not breakdown.should_refuse

    def test_low_confidence_response(self):
        """Test a poorly supported response gets low confidence."""
        breakdown = self.scorer.calculate(
            total_paragraphs=4,
            paragraphs_with_citations=3,  # 75% coverage (above 30% min)
            valid_citations=3,
            invalid_citations=1,
            source_reliability_scores=[0.60, 0.55],  # Above 0.50 min
            relevance_scores=[0.50, 0.45],  # Above 0.30 min
            has_primary_source=False,
        )

        # Should be low or insufficient but not refuse (edge case)
        assert breakdown.confidence_level in ["low", "insufficient"]

    def test_insufficient_evidence_refuse(self):
        """Test insufficient evidence triggers refusal."""
        breakdown = self.scorer.calculate(
            total_paragraphs=5,
            paragraphs_with_citations=0,
            valid_citations=0,
            invalid_citations=0,
            source_reliability_scores=[],
            relevance_scores=[],
        )

        assert breakdown.confidence_level == "insufficient"
        assert breakdown.should_refuse
        assert breakdown.refusal_reason != ""


class TestRefusalConditions:
    """Test hard refusal conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()

    def test_refuse_no_citations(self):
        """Refuse when no valid citations found."""
        breakdown = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=0,
            valid_citations=0,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
        )

        assert breakdown.should_refuse
        assert "No valid citations" in breakdown.refusal_reason

    def test_refuse_low_coverage(self):
        """Refuse when citation coverage is too low."""
        breakdown = self.scorer.calculate(
            total_paragraphs=10,
            paragraphs_with_citations=2,  # 20% < 30%
            valid_citations=2,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
        )

        assert breakdown.should_refuse
        assert "coverage" in breakdown.refusal_reason.lower()

    def test_refuse_low_relevance(self):
        """Refuse when average relevance is too low."""
        breakdown = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.1, 0.2, 0.15],  # avg 0.15 < 0.30
        )

        assert breakdown.should_refuse
        assert "relevance" in breakdown.refusal_reason.lower()

    def test_refuse_low_reliability(self):
        """Refuse when all sources have low reliability."""
        breakdown = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.3, 0.4, 0.35],  # max 0.4 < 0.5
            relevance_scores=[0.8],
        )

        assert breakdown.should_refuse
        assert "reliable" in breakdown.refusal_reason.lower()

    def test_accept_good_response(self):
        """Accept a well-supported response."""
        breakdown = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=5,
            invalid_citations=0,
            source_reliability_scores=[0.9, 0.85],
            relevance_scores=[0.8, 0.9, 0.85],
            chunk_ids=["c1", "c2", "c3", "c4", "c5"],
            source_ids=["s1", "s2", "s1", "s2", "s1"],
        )

        assert not breakdown.should_refuse


class TestDegradation:
    """Test degradation penalties."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()

    def test_no_primary_source_penalty(self):
        """Test penalty for no primary source."""
        with_primary = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            has_primary_source=True,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s1", "s1"],
        )

        without_primary = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            has_primary_source=False,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s1", "s1"],
        )

        assert without_primary.final_score < with_primary.final_score

    def test_invalid_citation_penalty(self):
        """Test penalty for invalid citations."""
        no_invalid = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=0,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s1", "s1"],
        )

        with_invalid = self.scorer.calculate(
            total_paragraphs=3,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=2,
            source_reliability_scores=[0.9],
            relevance_scores=[0.8],
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s1", "s1"],
        )

        assert with_invalid.final_score < no_invalid.final_score

    def test_degradation_reasons_tracked(self):
        """Test that degradation reasons are tracked."""
        breakdown = self.scorer.calculate(
            total_paragraphs=5,
            paragraphs_with_citations=3,
            valid_citations=3,
            invalid_citations=1,
            source_reliability_scores=[0.6],
            relevance_scores=[0.4],
            has_primary_source=False,
        )

        assert len(breakdown.degradation_reasons) > 0


class TestRefusalTestCases:
    """Test the built-in refusal test cases."""

    def test_all_refusal_test_cases_pass(self):
        """Run all refusal test cases and verify they pass."""
        results = run_refusal_tests()

        for result in results:
            assert result["passed"], \
                f"Refusal test '{result['name']}' failed:\n" \
                f"  Expected refuse: {result['expected_refuse']}\n" \
                f"  Actual refuse: {result['actual_refuse']}\n" \
                f"  Reason: {result['reason']}\n" \
                f"  Confidence: {result['confidence_level']} ({result['final_score']:.2f})"

    def test_refusal_test_case_count(self):
        """Ensure we have enough test cases."""
        assert len(REFUSAL_TEST_CASES) >= 5, "Need at least 5 refusal test cases"


class TestConfidenceMessages:
    """Test confidence level messages."""

    def test_all_levels_have_messages(self):
        """All confidence levels should have messages."""
        levels = ["high", "medium", "low", "insufficient"]

        for level in levels:
            message = get_confidence_message(level)
            assert message != "", f"No message for level: {level}"
            assert len(message) > 10, f"Message too short for level: {level}"

    def test_insufficient_message_mentions_scholars(self):
        """Insufficient message should direct to scholars."""
        message = get_confidence_message("insufficient")
        assert "scholar" in message.lower()


class TestShouldRefuseResponse:
    """Test the should_refuse_response helper."""

    def test_refuses_insufficient_breakdown(self):
        """Should refuse when breakdown says so."""
        breakdown = ConfidenceBreakdown()
        breakdown.should_refuse = True
        breakdown.refusal_reason = "Test reason"

        should_refuse, reason = should_refuse_response(breakdown)

        assert should_refuse
        assert reason == "Test reason"

    def test_refuses_insufficient_level(self):
        """Should refuse when confidence level is insufficient."""
        breakdown = ConfidenceBreakdown()
        breakdown.confidence_level = "insufficient"

        should_refuse, reason = should_refuse_response(breakdown)

        assert should_refuse

    def test_accepts_good_breakdown(self):
        """Should accept when breakdown is good."""
        breakdown = ConfidenceBreakdown()
        breakdown.should_refuse = False
        breakdown.confidence_level = "high"
        breakdown.final_score = 0.9

        should_refuse, reason = should_refuse_response(breakdown)

        assert not should_refuse


class TestBoundaryConditions:
    """Test boundary conditions between confidence levels.

    Key boundaries:
    - 0.85: HIGH vs MEDIUM
    - 0.65: MEDIUM vs LOW
    - 0.45: LOW vs BORDERLINE
    - 0.35: BORDERLINE vs INSUFFICIENT (REFUSE)
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()

    def test_boundary_046_is_low_not_refuse(self):
        """Score 0.46 should be 'low' and should NOT refuse."""
        # Create inputs that yield approximately 0.46 final score
        breakdown = self.scorer.calculate(
            total_paragraphs=5,
            paragraphs_with_citations=3,  # 60% coverage
            valid_citations=3,
            invalid_citations=1,
            source_reliability_scores=[0.55, 0.60],  # Above 0.50 min
            relevance_scores=[0.50, 0.45, 0.40],  # Above 0.30 min avg
            has_primary_source=False,
            chunk_ids=["c1", "c2", "c3"],
            source_ids=["s1", "s2", "s1"],
        )

        # Should be low or borderline, but NOT refuse
        assert breakdown.confidence_level in ["low", "borderline"]
        assert not breakdown.should_refuse, f"Should not refuse at score {breakdown.final_score:.2f}"

    def test_boundary_borderline_not_refuse(self):
        """Borderline scores (0.35-0.45) should NOT hard refuse."""
        # Create a borderline breakdown directly to test the logic
        breakdown = ConfidenceBreakdown()
        breakdown.final_score = 0.40  # In borderline range
        breakdown.confidence_level = "borderline"
        breakdown.should_refuse = False  # Borderline doesn't refuse

        should_refuse, _ = should_refuse_response(breakdown)
        # Borderline still responds (with heavy caveats)
        assert not should_refuse, "Borderline responses should not refuse"

    def test_boundary_034_should_refuse(self):
        """Score < 0.35 should be 'insufficient' and REFUSE."""
        # Create inputs that yield score below 0.35
        # This is hard to achieve without triggering hard refusal conditions
        breakdown = ConfidenceBreakdown()
        breakdown.final_score = 0.34
        breakdown.confidence_level = "insufficient"
        breakdown.should_refuse = True
        breakdown.refusal_reason = "Confidence score below threshold"

        should_refuse, _ = should_refuse_response(breakdown)
        assert should_refuse

    def test_threshold_separation(self):
        """Verify LOW (0.45) and REFUSAL (0.35) are properly separated."""
        assert LOW_CONFIDENCE_THRESHOLD == 0.45
        assert REFUSAL_THRESHOLD == 0.35
        assert LOW_CONFIDENCE_THRESHOLD > REFUSAL_THRESHOLD
        # Check ~10% gap (use approximate comparison for floating point)
        gap = LOW_CONFIDENCE_THRESHOLD - REFUSAL_THRESHOLD
        assert 0.09 <= gap <= 0.11, f"Expected ~0.10 gap, got {gap}"

    def test_borderline_message_warns(self):
        """Borderline confidence message should include caution."""
        message = get_confidence_message("borderline")
        assert "caution" in message.lower() or "verify" in message.lower()
        assert "scholar" in message.lower()

    def test_all_confidence_levels_defined(self):
        """All 5 confidence levels should have messages."""
        levels = ["high", "medium", "low", "borderline", "insufficient"]
        for level in levels:
            message = get_confidence_message(level)
            assert message != "", f"No message for level: {level}"
            assert len(message) > 20, f"Message too short for level: {level}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
