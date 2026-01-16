"""
Theme Quality Distribution Tests

Tests the 3-tier classification system to ensure quality thresholds are met:
1. At least 10% of segments are CORE or RECOMMENDED
2. Top 10 themes by segment count have at least 3 quality segments each
3. No theme has 0 quality segments (CORE + RECOMMENDED)
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List

from app.services.theme_quality import (
    ThemeQualityService,
    SegmentTier,
    CORE_CONFIDENCE_DIRECT,
    CORE_CONFIDENCE_MULTI_SOURCE,
    RECOMMENDED_CONFIDENCE_SINGLE,
    RECOMMENDED_CONFIDENCE_MULTI,
    DIRECT_MATCH_TYPES,
    WEAK_MATCH_TYPES,
)


@dataclass
class MockSegment:
    """Mock ThemeSegment for testing."""
    id: str
    theme_id: str
    confidence: float
    evidence_sources: List[str]
    match_type: str
    reasons_ar: str
    sura_no: int = 1
    ayah_start: int = 1
    ayah_end: int = 1
    is_core: bool = False


def run_async(coro):
    """Helper to run async code in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSegmentTierClassification:
    """Test the 3-tier classification logic."""

    @pytest.fixture
    def service(self):
        """Create service with mock session."""
        mock_session = MagicMock()
        return ThemeQualityService(mock_session)

    def test_manual_segments_are_core(self, service):
        """Manual (scholar-curated) segments should always be CORE."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.5,  # Even low confidence
            evidence_sources=[],  # Even no sources
            match_type="manual",
            reasons_ar="",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.CORE
        assert result.is_core is True
        assert "Manual segment" in result.classification_reason

    def test_empty_match_type_is_core(self, service):
        """Empty match_type (legacy manual) should be CORE."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.8,
            evidence_sources=["ibn_kathir"],
            match_type="",
            reasons_ar="تفسير مفصل للآية",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.CORE
        assert result.is_core is True

    def test_high_confidence_direct_match_is_core(self, service):
        """High confidence (>=0.82) with direct match type should be CORE."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.85,
            evidence_sources=["ibn_kathir"],
            match_type="lexical",
            reasons_ar="تفسير مفصل",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.CORE
        assert result.confidence >= CORE_CONFIDENCE_DIRECT

    def test_multi_source_good_confidence_is_core(self, service):
        """Multiple tafsir sources (>=2) with conf>=0.74 should be CORE."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.76,
            evidence_sources=["ibn_kathir", "tabari", "qurtubi"],
            match_type="root",
            reasons_ar="تفسير مفصل",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.CORE
        assert len(segment.evidence_sources) >= 2
        assert result.confidence >= CORE_CONFIDENCE_MULTI_SOURCE

    def test_good_confidence_non_weak_is_recommended(self, service):
        """Confidence >=0.70 with non-weak match should be RECOMMENDED."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.72,
            evidence_sources=["ibn_kathir"],
            match_type="root",
            reasons_ar="تفسير مفصل",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.RECOMMENDED
        assert result.confidence >= RECOMMENDED_CONFIDENCE_SINGLE

    def test_multi_source_moderate_confidence_is_recommended(self, service):
        """Multiple sources with conf>=0.65 should be RECOMMENDED."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.67,
            evidence_sources=["ibn_kathir", "tabari"],
            match_type="root",
            reasons_ar="تفسير مفصل",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.RECOMMENDED

    def test_low_confidence_single_source_is_supporting(self, service):
        """Low confidence with single source should be SUPPORTING."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.55,
            evidence_sources=["ibn_kathir"],
            match_type="root",
            reasons_ar="تفسير",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.SUPPORTING
        assert result.is_core is False

    def test_weak_match_type_not_recommended(self, service):
        """Weak match types should not qualify for RECOMMENDED."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.75,  # Above threshold
            evidence_sources=["ibn_kathir"],
            match_type="weak",
            reasons_ar="تفسير",
        )
        result = run_async(service.classify_segment(segment))
        # Should be SUPPORTING because of weak match type
        assert result.tier == SegmentTier.SUPPORTING


class TestThresholdConstants:
    """Test that threshold constants are correctly defined."""

    def test_core_thresholds(self):
        """CORE thresholds should be properly set."""
        assert CORE_CONFIDENCE_DIRECT == 0.82
        assert CORE_CONFIDENCE_MULTI_SOURCE == 0.74

    def test_recommended_thresholds(self):
        """RECOMMENDED thresholds should be properly set."""
        assert RECOMMENDED_CONFIDENCE_SINGLE == 0.70
        assert RECOMMENDED_CONFIDENCE_MULTI == 0.65

    def test_direct_match_types(self):
        """DIRECT match types should include expected values."""
        expected = {'direct', 'exact', 'root', 'lexical', 'manual'}
        for match_type in expected:
            assert match_type in DIRECT_MATCH_TYPES

    def test_weak_match_types(self):
        """WEAK match types should include expected values."""
        expected = {'weak', 'semantic_low'}
        for match_type in expected:
            assert match_type in WEAK_MATCH_TYPES


class TestTierClassificationBackwardsCompatibility:
    """Test backwards compatibility with is_core field."""

    @pytest.fixture
    def service(self):
        mock_session = MagicMock()
        return ThemeQualityService(mock_session)

    def test_is_core_true_for_core_tier(self, service):
        """is_core should be True when tier is CORE."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.85,
            evidence_sources=["ibn_kathir", "tabari"],
            match_type="manual",
            reasons_ar="تفسير",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.CORE
        assert result.is_core is True

    def test_is_core_false_for_recommended_tier(self, service):
        """is_core should be False when tier is RECOMMENDED."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.72,
            evidence_sources=["ibn_kathir"],
            match_type="root",
            reasons_ar="تفسير",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.RECOMMENDED
        assert result.is_core is False

    def test_is_core_false_for_supporting_tier(self, service):
        """is_core should be False when tier is SUPPORTING."""
        segment = MockSegment(
            id="seg1",
            theme_id="theme_salah",
            confidence=0.50,
            evidence_sources=["ibn_kathir"],
            match_type="root",
            reasons_ar="تفسير",
        )
        result = run_async(service.classify_segment(segment))
        assert result.tier == SegmentTier.SUPPORTING
        assert result.is_core is False


class TestQualityDistributionThresholds:
    """
    Integration tests to validate quality distribution requirements.

    These tests require a database connection and should run against
    the actual theme data to verify:
    - At least 10% are CORE or RECOMMENDED
    - Top 10 themes have 3+ quality segments each
    """

    @pytest.mark.skip(reason="Requires database connection - run in integration tests")
    def test_minimum_quality_threshold_10_percent(self, db_session):
        """At least 10% of all segments should be CORE or RECOMMENDED."""
        service = ThemeQualityService(db_session)
        stats = run_async(service.classify_all_segments(dry_run=True))

        total = stats["total_segments"]
        quality = stats["core_segments"] + stats["recommended_segments"]
        quality_percentage = (quality / total * 100) if total > 0 else 0

        assert quality_percentage >= 10.0, (
            f"Quality segments ({quality_percentage:.1f}%) below 10% threshold. "
            f"Core: {stats['core_segments']}, Recommended: {stats['recommended_segments']}"
        )

    @pytest.mark.skip(reason="Requires database connection - run in integration tests")
    def test_top_10_themes_have_quality_segments(self, db_session):
        """Top 10 themes by segment count should have at least 3 quality segments."""
        from sqlalchemy import select, func
        from app.models.theme import ThemeSegment

        service = ThemeQualityService(db_session)

        # Get top 10 themes by segment count
        theme_counts = run_async(db_session.execute(
            select(ThemeSegment.theme_id, func.count().label('count'))
            .group_by(ThemeSegment.theme_id)
            .order_by(func.count().desc())
            .limit(10)
        ))
        top_themes = [row.theme_id for row in theme_counts.all()]

        for theme_id in top_themes:
            stats = run_async(service.classify_all_segments(theme_id=theme_id, dry_run=True))
            quality = stats["core_segments"] + stats["recommended_segments"]

            assert quality >= 3, (
                f"Theme {theme_id} has only {quality} quality segments (need 3+). "
                f"Core: {stats['core_segments']}, Recommended: {stats['recommended_segments']}"
            )
