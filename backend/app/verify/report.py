"""
VerificationReport - Data structures for verification results.

PR4/D: Enhanced reporting with actionable insights:
- Coverage map by sura
- Category distribution
- Evidence density metrics
- Weakest/strongest stories
- Next actions
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    """Output format for verification reports."""
    JSON = "json"
    MARKDOWN = "markdown"
    BOTH = "both"


@dataclass
class VerificationReport:
    """
    Complete verification report.

    Contains:
    - Metadata (generation time, versions)
    - Summary statistics
    - Coverage statistics
    - Individual check results
    """

    generated_at: datetime = field(default_factory=datetime.utcnow)
    registry_version: str = "2.0.0"
    engine_version: str = "1.0.0"

    # Summary
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    errors: int = 0
    warnings: int = 0

    # Coverage
    total_stories: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    empty_categories: List[str] = field(default_factory=list)
    suras_with_stories: int = 0
    total_verses_covered: int = 0

    # Detailed results
    checks: List[Dict[str, Any]] = field(default_factory=list)
    checks_by_category: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    # Issues
    stories_without_arabic: List[str] = field(default_factory=list)
    stories_without_evidence: List[str] = field(default_factory=list)
    invalid_ayah_ranges: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_checks == 0:
            return 0.0
        return round(self.passed_checks / self.total_checks * 100, 1)

    @property
    def is_healthy(self) -> bool:
        """Check if the registry is in a healthy state."""
        return self.errors == 0

    @property
    def needs_attention(self) -> bool:
        """Check if there are warnings that need attention."""
        return self.warnings > 0 or self.errors > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "registry_version": self.registry_version,
                "engine_version": self.engine_version,
            },
            "summary": {
                "total_checks": self.total_checks,
                "passed_checks": self.passed_checks,
                "failed_checks": self.failed_checks,
                "errors": self.errors,
                "warnings": self.warnings,
                "pass_rate": self.pass_rate,
                "is_healthy": self.is_healthy,
            },
            "coverage": {
                "total_stories": self.total_stories,
                "category_counts": self.category_counts,
                "empty_categories": self.empty_categories,
                "suras_with_stories": self.suras_with_stories,
                "total_verses_covered": self.total_verses_covered,
            },
            "issues": {
                "stories_without_arabic": self.stories_without_arabic,
                "stories_without_evidence": self.stories_without_evidence,
                "invalid_ayah_ranges": self.invalid_ayah_ranges,
            },
            "checks": self.checks,
            "checks_by_category": self.checks_by_category,
        }

    @classmethod
    def from_engine_report(cls, report: Dict[str, Any]) -> "VerificationReport":
        """Create from engine report dictionary."""
        instance = cls()

        # Metadata
        metadata = report.get("metadata", {})
        if metadata.get("generated_at"):
            instance.generated_at = datetime.fromisoformat(metadata["generated_at"])
        instance.registry_version = metadata.get("registry_version", "2.0.0")
        instance.engine_version = metadata.get("engine_version", "1.0.0")

        # Summary
        summary = report.get("summary", {})
        instance.total_checks = summary.get("total_checks", 0)
        instance.passed_checks = summary.get("passed_checks", 0)
        instance.failed_checks = summary.get("failed_checks", 0)
        instance.errors = summary.get("errors", 0)
        instance.warnings = summary.get("warnings", 0)

        # Coverage
        coverage = report.get("coverage_stats", {})
        instance.total_stories = coverage.get("total_stories", 0)
        instance.category_counts = coverage.get("category_counts", {})
        instance.empty_categories = coverage.get("empty_categories", [])
        instance.suras_with_stories = coverage.get("suras_with_stories", 0)
        instance.total_verses_covered = coverage.get("total_verses_covered", 0)
        instance.stories_without_arabic = coverage.get("stories_without_arabic", [])
        instance.stories_without_evidence = coverage.get("stories_without_evidence", [])

        # Checks
        instance.checks = report.get("all_checks", [])
        instance.checks_by_category = report.get("checks_by_category", {})

        return instance


def format_report_for_ci(report: VerificationReport) -> str:
    """
    Format report for CI output.

    Returns a summary suitable for CI logs with exit status indication.
    """
    lines = []

    # Status header
    if report.is_healthy:
        lines.append("✅ VERIFICATION PASSED")
    else:
        lines.append("❌ VERIFICATION FAILED")

    lines.append("")

    # Quick stats
    lines.append(f"📊 Checks: {report.passed_checks}/{report.total_checks} passed ({report.pass_rate}%)")
    lines.append(f"📚 Stories: {report.total_stories}")
    lines.append(f"📖 Suras covered: {report.suras_with_stories}/114")
    lines.append("")

    # Errors
    if report.errors > 0:
        lines.append(f"❌ Errors: {report.errors}")
        for check in report.checks:
            if not check.get("passed") and check.get("severity") == "error":
                lines.append(f"   - {check['message_ar']}")

    # Warnings
    if report.warnings > 0:
        lines.append(f"⚠️ Warnings: {report.warnings}")

    # Empty categories
    if report.empty_categories:
        lines.append(f"⚠️ Empty categories: {', '.join(report.empty_categories)}")

    return "\n".join(lines)


# =============================================================================
# PR4/D: ENHANCED REPORTING - ACTIONABLE INSIGHTS
# =============================================================================

@dataclass
class StoryQualityRank:
    """Story ranked by quality for weakest/strongest lists."""
    story_id: str
    story_name_ar: str
    story_name_en: str
    category: str
    evidence_count: int
    event_count: int
    segment_count: int
    quality_score: float  # 0.0 - 1.0
    issues: List[str] = field(default_factory=list)


@dataclass
class NextAction:
    """Actionable insight for improving coverage or quality."""
    action_id: str
    priority: int  # 1 = highest
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    affected_count: int
    category: str  # "coverage", "quality", "i18n", "evidence"


@dataclass
class EnhancedVerificationReport(VerificationReport):
    """
    Enhanced verification report with actionable insights (PR4/D).

    Extends base VerificationReport with:
    - Sura-level coverage map
    - Evidence density metrics
    - Weakest/strongest story rankings
    - Prioritized next actions
    """

    # PR4/D: Coverage map
    coverage_map: Dict[int, List[str]] = field(default_factory=dict)  # sura -> [story_ids]
    missing_suras: List[int] = field(default_factory=list)
    coverage_by_juz: Dict[int, int] = field(default_factory=dict)  # juz -> story_count

    # PR4/D: Evidence density
    evidence_density: float = 0.0  # Overall evidence coverage rate
    stories_below_evidence_threshold: List[str] = field(default_factory=list)
    average_evidence_per_story: float = 0.0
    source_distribution: Dict[str, int] = field(default_factory=dict)

    # PR4/D: Quality rankings
    weakest_stories: List[StoryQualityRank] = field(default_factory=list)
    strongest_stories: List[StoryQualityRank] = field(default_factory=list)

    # PR4/D: Actionable insights
    next_actions: List[NextAction] = field(default_factory=list)

    # PR4: Milestone tracking
    current_milestone: str = "A"
    milestone_target_suras: int = 50
    milestone_progress_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enhanced fields."""
        base = super().to_dict()

        # Add PR4/D fields
        base["coverage_map"] = {
            "by_sura": {str(k): v for k, v in self.coverage_map.items()},
            "missing_suras": self.missing_suras,
            "by_juz": self.coverage_by_juz,
        }

        base["evidence"] = {
            "density": self.evidence_density,
            "below_threshold": self.stories_below_evidence_threshold,
            "average_per_story": self.average_evidence_per_story,
            "source_distribution": self.source_distribution,
        }

        base["quality_rankings"] = {
            "weakest_10": [self._rank_to_dict(r) for r in self.weakest_stories[:10]],
            "strongest_10": [self._rank_to_dict(r) for r in self.strongest_stories[:10]],
        }

        base["next_actions"] = [self._action_to_dict(a) for a in self.next_actions]

        base["milestone"] = {
            "current": self.current_milestone,
            "target_suras": self.milestone_target_suras,
            "progress_percent": self.milestone_progress_pct,
        }

        return base

    def _rank_to_dict(self, rank: StoryQualityRank) -> Dict[str, Any]:
        return {
            "story_id": rank.story_id,
            "name_ar": rank.story_name_ar,
            "name_en": rank.story_name_en,
            "category": rank.category,
            "evidence_count": rank.evidence_count,
            "event_count": rank.event_count,
            "quality_score": rank.quality_score,
            "issues": rank.issues,
        }

    def _action_to_dict(self, action: NextAction) -> Dict[str, Any]:
        return {
            "id": action.action_id,
            "priority": action.priority,
            "title_ar": action.title_ar,
            "title_en": action.title_en,
            "description_ar": action.description_ar,
            "description_en": action.description_en,
            "affected_count": action.affected_count,
            "category": action.category,
        }


def generate_next_actions(report: EnhancedVerificationReport) -> List[NextAction]:
    """
    Generate prioritized next actions based on report findings.

    Returns list of actionable insights sorted by priority.
    """
    actions = []
    priority = 1

    # 1. Coverage gaps (highest priority)
    if report.missing_suras and len(report.missing_suras) > 0:
        actions.append(NextAction(
            action_id="expand_coverage",
            priority=priority,
            title_ar="توسيع التغطية",
            title_en="Expand Coverage",
            description_ar=f"أضف قصصاً لـ {len(report.missing_suras)} سورة غير مغطاة",
            description_en=f"Add stories for {len(report.missing_suras)} uncovered suras",
            affected_count=len(report.missing_suras),
            category="coverage",
        ))
        priority += 1

    # 2. Evidence gaps
    if report.stories_below_evidence_threshold:
        actions.append(NextAction(
            action_id="improve_evidence",
            priority=priority,
            title_ar="تحسين الأدلة",
            title_en="Improve Evidence",
            description_ar=f"أضف أدلة لـ {len(report.stories_below_evidence_threshold)} قصة",
            description_en=f"Add evidence for {len(report.stories_below_evidence_threshold)} stories",
            affected_count=len(report.stories_below_evidence_threshold),
            category="evidence",
        ))
        priority += 1

    # 3. Arabic content gaps
    if report.stories_without_arabic:
        actions.append(NextAction(
            action_id="add_arabic_content",
            priority=priority,
            title_ar="إضافة محتوى عربي",
            title_en="Add Arabic Content",
            description_ar=f"أضف ملخصات عربية لـ {len(report.stories_without_arabic)} قصة",
            description_en=f"Add Arabic summaries for {len(report.stories_without_arabic)} stories",
            affected_count=len(report.stories_without_arabic),
            category="i18n",
        ))
        priority += 1

    # 4. Weak stories need improvement
    weak_count = len([s for s in report.weakest_stories if s.quality_score < 0.3])
    if weak_count > 0:
        actions.append(NextAction(
            action_id="strengthen_weak_stories",
            priority=priority,
            title_ar="تقوية القصص الضعيفة",
            title_en="Strengthen Weak Stories",
            description_ar=f"حسّن {weak_count} قصة ذات جودة منخفضة",
            description_en=f"Improve {weak_count} low-quality stories",
            affected_count=weak_count,
            category="quality",
        ))
        priority += 1

    # 5. Empty categories
    if report.empty_categories:
        actions.append(NextAction(
            action_id="populate_categories",
            priority=priority,
            title_ar="ملء التصنيفات الفارغة",
            title_en="Populate Empty Categories",
            description_ar=f"أضف قصصاً إلى {len(report.empty_categories)} تصنيفات فارغة",
            description_en=f"Add stories to {len(report.empty_categories)} empty categories",
            affected_count=len(report.empty_categories),
            category="coverage",
        ))
        priority += 1

    return actions


def format_enhanced_report_markdown(report: EnhancedVerificationReport) -> str:
    """
    Format enhanced report as Markdown for human review.

    Includes coverage map, quality rankings, and next actions.
    """
    lines = []

    # Header
    lines.append("# تقرير التحقق من القصص القرآنية")
    lines.append(f"# Quran Stories Verification Report")
    lines.append("")
    lines.append(f"تاريخ التوليد: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Summary
    lines.append("## ملخص | Summary")
    lines.append("")
    status = "✅ ناجح" if report.is_healthy else "❌ فشل"
    lines.append(f"**الحالة**: {status}")
    lines.append(f"**الفحوصات**: {report.passed_checks}/{report.total_checks} ({report.pass_rate}%)")
    lines.append(f"**القصص**: {report.total_stories}")
    lines.append(f"**السور المغطاة**: {report.suras_with_stories}/114")
    lines.append("")

    # Milestone Progress
    lines.append("## تقدم المرحلة | Milestone Progress")
    lines.append("")
    lines.append(f"**المرحلة الحالية**: {report.current_milestone}")
    lines.append(f"**الهدف**: {report.milestone_target_suras} سورة")
    lines.append(f"**التقدم**: {report.milestone_progress_pct}%")
    lines.append("")

    # Coverage Map
    lines.append("## خريطة التغطية | Coverage Map")
    lines.append("")
    if report.coverage_map:
        lines.append(f"السور المغطاة: {len(report.coverage_map)}")
        lines.append(f"السور المفقودة: {len(report.missing_suras)}")
        if report.missing_suras[:10]:
            lines.append(f"أمثلة السور المفقودة: {', '.join(map(str, report.missing_suras[:10]))}")
    lines.append("")

    # Evidence Density
    lines.append("## كثافة الأدلة | Evidence Density")
    lines.append("")
    lines.append(f"**معدل التغطية بالأدلة**: {report.evidence_density * 100:.1f}%")
    lines.append(f"**متوسط الأدلة لكل قصة**: {report.average_evidence_per_story:.1f}")
    if report.source_distribution:
        lines.append("**توزيع المصادر**:")
        for source, count in sorted(report.source_distribution.items()):
            lines.append(f"  - {source}: {count}")
    lines.append("")

    # Quality Rankings
    lines.append("## ترتيب الجودة | Quality Rankings")
    lines.append("")

    if report.strongest_stories:
        lines.append("### أقوى 5 قصص | Top 5 Strongest")
        for rank in report.strongest_stories[:5]:
            lines.append(f"- **{rank.story_name_ar}**: {rank.quality_score:.2f} ({rank.evidence_count} أدلة)")
        lines.append("")

    if report.weakest_stories:
        lines.append("### أضعف 5 قصص | Top 5 Weakest")
        for rank in report.weakest_stories[:5]:
            issues_str = f" [{', '.join(rank.issues)}]" if rank.issues else ""
            lines.append(f"- **{rank.story_name_ar}**: {rank.quality_score:.2f}{issues_str}")
        lines.append("")

    # Next Actions
    lines.append("## الإجراءات التالية | Next Actions")
    lines.append("")
    if report.next_actions:
        for action in report.next_actions:
            lines.append(f"### {action.priority}. {action.title_ar} | {action.title_en}")
            lines.append(f"{action.description_ar}")
            lines.append(f"العدد المتأثر: {action.affected_count}")
            lines.append("")
    else:
        lines.append("لا توجد إجراءات مطلوبة | No actions required")
        lines.append("")

    return "\n".join(lines)


def compute_story_quality_score(
    story_id: str,
    evidence_count: int,
    event_count: int,
    segment_count: int,
    has_arabic: bool,
    has_english: bool,
) -> tuple[float, List[str]]:
    """
    Compute quality score for a story.

    Returns (score, issues) where score is 0.0-1.0.
    """
    score = 0.0
    issues = []

    # Evidence (40% weight)
    if evidence_count >= 3:
        score += 0.4
    elif evidence_count >= 1:
        score += 0.2
    else:
        issues.append("no_evidence")

    # Events (30% weight)
    if event_count >= 3:
        score += 0.3
    elif event_count >= 1:
        score += 0.15
    else:
        issues.append("no_events")

    # Segments (15% weight)
    if segment_count >= 2:
        score += 0.15
    elif segment_count >= 1:
        score += 0.075

    # i18n (15% weight)
    if has_arabic and has_english:
        score += 0.15
    elif has_arabic or has_english:
        score += 0.075
        if not has_arabic:
            issues.append("no_arabic")

    return score, issues
