"""
Tests for Part D: Enhanced reporting with actionable insights.

D1: Coverage map by sura
D2: Evidence density metrics
D3: Weakest/strongest story rankings
D4: Next actions generation
D5: Markdown report formatting
"""

import pytest
from datetime import datetime

from app.verify.report import (
    EnhancedVerificationReport,
    StoryQualityRank,
    NextAction,
    generate_next_actions,
    format_enhanced_report_markdown,
    compute_story_quality_score,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_enhanced_report() -> EnhancedVerificationReport:
    """Create sample enhanced report for testing."""
    return EnhancedVerificationReport(
        generated_at=datetime.utcnow(),
        total_checks=15,
        passed_checks=14,
        failed_checks=1,
        errors=0,
        warnings=1,
        total_stories=37,
        suras_with_stories=35,
        category_counts={
            "prophet": 14,
            "nation": 8,
            "parable": 6,
            "historical": 7,
            "named_char": 2,
        },
        empty_categories=[],
        coverage_map={2: ["adam", "ibrahim"], 7: ["adam", "musa"], 12: ["yusuf"]},
        missing_suras=[33, 34, 36, 37, 40],
        evidence_density=0.85,
        stories_below_evidence_threshold=["story_weak_1", "story_weak_2"],
        average_evidence_per_story=4.2,
        source_distribution={
            "ibn_kathir": 151,
            "tabari": 95,
            "qurtubi": 73,
            "saadi": 59,
        },
        weakest_stories=[
            StoryQualityRank(
                story_id="weak_1",
                story_name_ar="قصة ضعيفة",
                story_name_en="Weak Story",
                category="nation",
                evidence_count=0,
                event_count=0,
                segment_count=1,
                quality_score=0.15,
                issues=["no_evidence", "no_events"],
            )
        ],
        strongest_stories=[
            StoryQualityRank(
                story_id="strong_1",
                story_name_ar="قصة آدم",
                story_name_en="Story of Adam",
                category="prophet",
                evidence_count=10,
                event_count=5,
                segment_count=3,
                quality_score=0.95,
                issues=[],
            )
        ],
        current_milestone="A",
        milestone_target_suras=50,
        milestone_progress_pct=70.0,
    )


# =============================================================================
# D1: COVERAGE MAP
# =============================================================================

class TestCoverageMap:
    """Tests for coverage map functionality."""

    def test_coverage_map_structure(self, sample_enhanced_report):
        """Coverage map must have sura -> story_ids mapping."""
        assert sample_enhanced_report.coverage_map is not None
        assert isinstance(sample_enhanced_report.coverage_map, dict)

        # Sura 2 should have Adam and Ibrahim stories
        assert 2 in sample_enhanced_report.coverage_map
        assert "adam" in sample_enhanced_report.coverage_map[2]

    def test_missing_suras_identified(self, sample_enhanced_report):
        """Missing suras must be tracked."""
        assert sample_enhanced_report.missing_suras is not None
        assert len(sample_enhanced_report.missing_suras) > 0

        # These suras should be missing
        for sura in [33, 34, 36]:
            assert sura in sample_enhanced_report.missing_suras

    def test_coverage_map_in_dict(self, sample_enhanced_report):
        """Coverage map appears in to_dict() output."""
        data = sample_enhanced_report.to_dict()

        assert "coverage_map" in data
        assert "by_sura" in data["coverage_map"]
        assert "missing_suras" in data["coverage_map"]


# =============================================================================
# D2: EVIDENCE DENSITY METRICS
# =============================================================================

class TestEvidenceDensity:
    """Tests for evidence density metrics."""

    def test_evidence_density_range(self, sample_enhanced_report):
        """Evidence density must be 0.0 - 1.0."""
        assert 0.0 <= sample_enhanced_report.evidence_density <= 1.0

    def test_source_distribution_tracked(self, sample_enhanced_report):
        """Source distribution must track all tafsir sources."""
        sources = sample_enhanced_report.source_distribution

        assert "ibn_kathir" in sources
        assert "tabari" in sources
        assert all(count > 0 for count in sources.values())

    def test_stories_below_threshold_tracked(self, sample_enhanced_report):
        """Stories below evidence threshold must be tracked."""
        below = sample_enhanced_report.stories_below_evidence_threshold

        assert isinstance(below, list)
        # These weak stories should be tracked
        assert "story_weak_1" in below

    def test_evidence_in_dict(self, sample_enhanced_report):
        """Evidence metrics appear in to_dict() output."""
        data = sample_enhanced_report.to_dict()

        assert "evidence" in data
        assert "density" in data["evidence"]
        assert "source_distribution" in data["evidence"]


# =============================================================================
# D3: QUALITY RANKINGS
# =============================================================================

class TestQualityRankings:
    """Tests for story quality rankings."""

    def test_quality_score_calculation(self):
        """Quality score calculation must be accurate."""
        # Full quality story
        score, issues = compute_story_quality_score(
            "story_1",
            evidence_count=5,
            event_count=4,
            segment_count=3,
            has_arabic=True,
            has_english=True,
        )

        assert score == pytest.approx(1.0, rel=0.1)
        assert len(issues) == 0

    def test_quality_score_issues_tracked(self):
        """Quality issues must be tracked."""
        # Story with no evidence or events
        score, issues = compute_story_quality_score(
            "story_weak",
            evidence_count=0,
            event_count=0,
            segment_count=1,
            has_arabic=True,
            has_english=True,
        )

        assert score < 0.5
        assert "no_evidence" in issues
        assert "no_events" in issues

    def test_weakest_stories_sorted(self, sample_enhanced_report):
        """Weakest stories must be sorted by quality score."""
        weakest = sample_enhanced_report.weakest_stories

        assert len(weakest) > 0
        assert weakest[0].quality_score < 0.5

    def test_strongest_stories_sorted(self, sample_enhanced_report):
        """Strongest stories must be sorted by quality score."""
        strongest = sample_enhanced_report.strongest_stories

        assert len(strongest) > 0
        assert strongest[0].quality_score > 0.8

    def test_rankings_in_dict(self, sample_enhanced_report):
        """Rankings appear in to_dict() output."""
        data = sample_enhanced_report.to_dict()

        assert "quality_rankings" in data
        assert "weakest_10" in data["quality_rankings"]
        assert "strongest_10" in data["quality_rankings"]


# =============================================================================
# D4: NEXT ACTIONS GENERATION
# =============================================================================

class TestNextActions:
    """Tests for actionable insights generation."""

    def test_next_actions_generated(self, sample_enhanced_report):
        """Next actions must be generated based on report."""
        actions = generate_next_actions(sample_enhanced_report)

        assert len(actions) > 0
        assert all(isinstance(a, NextAction) for a in actions)

    def test_actions_have_arabic_titles(self, sample_enhanced_report):
        """Next actions must have Arabic titles."""
        actions = generate_next_actions(sample_enhanced_report)

        for action in actions:
            assert action.title_ar is not None
            assert any('\u0600' <= c <= '\u06FF' for c in action.title_ar), \
                f"Title not Arabic: {action.title_ar}"

    def test_actions_prioritized(self, sample_enhanced_report):
        """Actions must be prioritized 1=highest."""
        actions = generate_next_actions(sample_enhanced_report)

        priorities = [a.priority for a in actions]
        assert priorities == sorted(priorities)  # Ascending order
        assert priorities[0] == 1 if priorities else True

    def test_coverage_action_first_priority(self, sample_enhanced_report):
        """Coverage gaps should be first priority."""
        actions = generate_next_actions(sample_enhanced_report)

        if sample_enhanced_report.missing_suras:
            coverage_actions = [a for a in actions if a.category == "coverage"]
            assert len(coverage_actions) > 0
            assert coverage_actions[0].priority == 1

    def test_actions_in_dict(self, sample_enhanced_report):
        """Actions appear in to_dict() output."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        data = sample_enhanced_report.to_dict()

        assert "next_actions" in data
        assert len(data["next_actions"]) > 0


# =============================================================================
# D5: MARKDOWN REPORT FORMATTING
# =============================================================================

class TestMarkdownFormatting:
    """Tests for Markdown report formatting."""

    def test_markdown_output_not_empty(self, sample_enhanced_report):
        """Markdown output must not be empty."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        md = format_enhanced_report_markdown(sample_enhanced_report)

        assert len(md) > 100
        assert isinstance(md, str)

    def test_markdown_has_arabic_header(self, sample_enhanced_report):
        """Markdown must have Arabic header."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        md = format_enhanced_report_markdown(sample_enhanced_report)

        assert "تقرير التحقق" in md

    def test_markdown_has_sections(self, sample_enhanced_report):
        """Markdown must have all required sections."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        md = format_enhanced_report_markdown(sample_enhanced_report)

        # Check for section headers
        assert "## ملخص" in md  # Summary
        assert "## خريطة التغطية" in md  # Coverage Map
        assert "## كثافة الأدلة" in md  # Evidence Density
        assert "## ترتيب الجودة" in md  # Quality Rankings
        assert "## الإجراءات التالية" in md  # Next Actions

    def test_markdown_has_milestone_progress(self, sample_enhanced_report):
        """Markdown must show milestone progress."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        md = format_enhanced_report_markdown(sample_enhanced_report)

        assert "تقدم المرحلة" in md
        assert "70" in md  # Progress percentage


# =============================================================================
# INTEGRATION: FULL REPORT GENERATION
# =============================================================================

class TestFullReportGeneration:
    """Integration tests for full report generation."""

    def test_full_report_to_dict(self, sample_enhanced_report):
        """Full report can be serialized to dict."""
        sample_enhanced_report.next_actions = generate_next_actions(sample_enhanced_report)
        data = sample_enhanced_report.to_dict()

        # All major sections present
        assert "metadata" in data
        assert "summary" in data
        assert "coverage" in data
        assert "coverage_map" in data
        assert "evidence" in data
        assert "quality_rankings" in data
        assert "next_actions" in data
        assert "milestone" in data

    def test_report_pass_rate_calculation(self, sample_enhanced_report):
        """Pass rate must be calculated correctly."""
        # 14 passed out of 15 = 93.3%
        assert sample_enhanced_report.pass_rate == pytest.approx(93.3, rel=0.1)

    def test_report_is_healthy(self, sample_enhanced_report):
        """Report health status must be correct."""
        # No errors = healthy
        assert sample_enhanced_report.is_healthy is True

    def test_report_needs_attention(self, sample_enhanced_report):
        """Report attention flag must be correct."""
        # Has warnings = needs attention
        assert sample_enhanced_report.needs_attention is True
