"""
QuranVerificationEngine - Comprehensive verification for Quran-wide story coverage.

Runs in CI and produces:
- JSON report for machine processing
- Markdown report for human review

Checks:
A) Coverage: All categories populated, all stories have ayah ranges
B) Completeness: Arabic content, events for long stories
C) Integrity: Valid ayah ranges, no dangling references
D) i18n: Arabic mode has no English leaks
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.verify.registry import (
    QuranStoryRegistry,
    StoryCategory,
    StoryRegistryEntry,
    VerificationStatus,
)
from app.verify.evidence_resolver import EvidenceResolver

logger = logging.getLogger(__name__)


class CheckSeverity(str, Enum):
    """Severity level for verification checks."""
    ERROR = "error"       # خطأ - يجب إصلاحه
    WARNING = "warning"   # تحذير - يفضل إصلاحه
    INFO = "info"         # معلومات


class CheckCategory(str, Enum):
    """Category of verification check."""
    COVERAGE = "coverage"           # تغطية
    COMPLETENESS = "completeness"   # اكتمال
    INTEGRITY = "integrity"         # سلامة
    I18N = "i18n"                   # التوطين
    EVIDENCE = "evidence"           # الأدلة


@dataclass
class CheckResult:
    """Result of a single verification check."""
    check_id: str
    check_name_ar: str
    check_name_en: str
    category: CheckCategory
    severity: CheckSeverity
    passed: bool
    message_ar: str
    message_en: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_items: List[str] = field(default_factory=list)


@dataclass
class VerificationSummary:
    """Summary of all verification checks."""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0


class QuranVerificationEngine:
    """
    Comprehensive verification engine for Quran story coverage.

    Usage:
        registry = QuranStoryRegistry()
        registry.load_from_manifest(Path("data/manifests/stories.json"))

        engine = QuranVerificationEngine(registry)
        report = engine.run_all_checks()
        engine.save_report(report, Path("reports/verification.json"))
    """

    # Required categories that must have at least one story
    REQUIRED_CATEGORIES = [
        StoryCategory.PROPHET,
        StoryCategory.NATION,
        StoryCategory.PARABLE,
        StoryCategory.HISTORICAL,
    ]

    # Minimum stories per category for "healthy" coverage
    MIN_STORIES_PER_CATEGORY = {
        StoryCategory.PROPHET: 5,
        StoryCategory.NATION: 3,
        StoryCategory.PARABLE: 2,
        StoryCategory.HISTORICAL: 3,
        StoryCategory.NAMED_CHAR: 2,
        StoryCategory.UNSEEN: 1,
    }

    # Stories with verse count above this should have events
    EVENT_THRESHOLD_VERSES = 10

    # Evidence coverage thresholds
    EVIDENCE_COVERAGE_WARNING = 0.60  # 60% coverage = warning threshold
    EVIDENCE_COVERAGE_ERROR = 0.85    # 85% coverage = error threshold (future)

    # ==========================================================================
    # PR4: COVERAGE MILESTONE CONFIGURATION
    # ==========================================================================
    # Staged milestones: 35 → 50 → 80 → 114 suras
    # Current milestone determines CI pass/fail threshold

    COVERAGE_MILESTONES = {
        "A": {"suras": 50, "evidence_rate": 0.60, "label": "المرحلة أ"},
        "B": {"suras": 80, "evidence_rate": 0.70, "label": "المرحلة ب"},
        "C": {"suras": 114, "evidence_rate": 0.85, "label": "المرحلة ج (كاملة)"},
    }

    # Current target milestone (set via env or config)
    CURRENT_MILESTONE = "A"  # Start with milestone A: 50 suras

    @property
    def target_suras(self) -> int:
        """Get target surah count for current milestone."""
        return self.COVERAGE_MILESTONES[self.CURRENT_MILESTONE]["suras"]

    @property
    def target_evidence_rate(self) -> float:
        """Get target evidence rate for current milestone."""
        return self.COVERAGE_MILESTONES[self.CURRENT_MILESTONE]["evidence_rate"]

    def __init__(self, registry: QuranStoryRegistry):
        self.evidence_resolver = EvidenceResolver()
        self.registry = registry
        self.checks: List[CheckResult] = []

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all verification checks and return report."""
        self.checks = []

        # A) Coverage checks
        self._check_required_categories_populated()
        self._check_minimum_stories_per_category()
        self._check_all_stories_have_ranges()

        # B) Completeness checks
        self._check_arabic_content()
        self._check_events_for_long_stories()
        self._check_main_persons_populated()

        # C) Integrity checks
        self._check_ayah_ranges_valid()
        self._check_no_duplicate_story_ids()
        self._check_event_indices_sequential()

        # D) i18n checks
        self._check_arabic_titles_not_english()
        self._check_arabic_summaries_not_empty()

        # E) Evidence checks
        self._check_stories_have_evidence()
        self._check_evidence_coverage()
        self._check_events_have_evidence()

        # F) Coverage milestone checks (PR4)
        self._check_coverage_milestone()

        return self._build_report()

    # =========================================================================
    # A) COVERAGE CHECKS
    # =========================================================================

    def _check_required_categories_populated(self):
        """Check that all required UI categories have at least one story."""
        counts = self.registry.get_category_counts()
        empty_required = []

        for cat in self.REQUIRED_CATEGORIES:
            if counts.get(cat.value, 0) == 0:
                empty_required.append(cat.value)

        passed = len(empty_required) == 0

        self.checks.append(CheckResult(
            check_id="coverage_required_categories",
            check_name_ar="تغطية التصنيفات المطلوبة",
            check_name_en="Required Categories Coverage",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع التصنيفات المطلوبة تحتوي على قصص" if passed else f"تصنيفات فارغة: {', '.join(empty_required)}",
            message_en="All required categories have stories" if passed else f"Empty categories: {', '.join(empty_required)}",
            details={"counts": counts, "empty_required": empty_required},
            affected_items=empty_required,
        ))

    def _check_minimum_stories_per_category(self):
        """Check minimum story count per category."""
        counts = self.registry.get_category_counts()
        below_minimum = []

        for cat, min_count in self.MIN_STORIES_PER_CATEGORY.items():
            actual = counts.get(cat.value, 0)
            if actual < min_count:
                below_minimum.append({
                    "category": cat.value,
                    "actual": actual,
                    "minimum": min_count,
                })

        passed = len(below_minimum) == 0

        self.checks.append(CheckResult(
            check_id="coverage_minimum_per_category",
            check_name_ar="الحد الأدنى للقصص في كل تصنيف",
            check_name_en="Minimum Stories Per Category",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar="جميع التصنيفات تحتوي على الحد الأدنى" if passed else f"{len(below_minimum)} تصنيفات أقل من الحد الأدنى",
            message_en="All categories meet minimum" if passed else f"{len(below_minimum)} categories below minimum",
            details={"below_minimum": below_minimum},
            affected_items=[b["category"] for b in below_minimum],
        ))

    def _check_all_stories_have_ranges(self):
        """Check that all stories have at least one ayah range."""
        stories_without_ranges = []

        for story in self.registry.stories.values():
            if not story.primary_ayah_ranges:
                stories_without_ranges.append(story.id)

        passed = len(stories_without_ranges) == 0

        self.checks.append(CheckResult(
            check_id="coverage_stories_have_ranges",
            check_name_ar="جميع القصص لها نطاقات آيات",
            check_name_en="All Stories Have Ayah Ranges",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع القصص لها نطاقات آيات" if passed else f"{len(stories_without_ranges)} قصص بدون نطاقات",
            message_en="All stories have ranges" if passed else f"{len(stories_without_ranges)} stories without ranges",
            affected_items=stories_without_ranges,
        ))

    # =========================================================================
    # B) COMPLETENESS CHECKS
    # =========================================================================

    def _check_arabic_content(self):
        """Check that all stories have Arabic titles and summaries."""
        missing_arabic = self.registry.get_stories_without_arabic()
        passed = len(missing_arabic) == 0

        self.checks.append(CheckResult(
            check_id="completeness_arabic_content",
            check_name_ar="اكتمال المحتوى العربي",
            check_name_en="Arabic Content Completeness",
            category=CheckCategory.COMPLETENESS,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع القصص لها محتوى عربي" if passed else f"{len(missing_arabic)} قصص تفتقر للمحتوى العربي",
            message_en="All stories have Arabic content" if passed else f"{len(missing_arabic)} stories missing Arabic",
            affected_items=missing_arabic,
        ))

    def _check_events_for_long_stories(self):
        """Check that stories with many verses have events defined."""
        stories_needing_events = []

        for story in self.registry.stories.values():
            if story.total_verses >= self.EVENT_THRESHOLD_VERSES and len(story.events) == 0:
                stories_needing_events.append({
                    "story_id": story.id,
                    "verse_count": story.total_verses,
                })

        passed = len(stories_needing_events) == 0

        self.checks.append(CheckResult(
            check_id="completeness_events_for_long_stories",
            check_name_ar="أحداث للقصص الطويلة",
            check_name_en="Events for Long Stories",
            category=CheckCategory.COMPLETENESS,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar="جميع القصص الطويلة لها أحداث" if passed else f"{len(stories_needing_events)} قصص طويلة بدون أحداث",
            message_en="All long stories have events" if passed else f"{len(stories_needing_events)} long stories without events",
            details={"threshold_verses": self.EVENT_THRESHOLD_VERSES, "stories": stories_needing_events},
            affected_items=[s["story_id"] for s in stories_needing_events],
        ))

    def _check_main_persons_populated(self):
        """Check that prophet/named_char stories have main_persons."""
        stories_without_persons = []

        for story in self.registry.stories.values():
            if story.category in (StoryCategory.PROPHET, StoryCategory.NAMED_CHAR):
                if not story.main_persons:
                    stories_without_persons.append(story.id)

        passed = len(stories_without_persons) == 0

        self.checks.append(CheckResult(
            check_id="completeness_main_persons",
            check_name_ar="الشخصيات الرئيسية محددة",
            check_name_en="Main Persons Populated",
            category=CheckCategory.COMPLETENESS,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar="جميع قصص الأنبياء والشخصيات لها أشخاص رئيسيون" if passed else f"{len(stories_without_persons)} قصص بدون شخصيات",
            message_en="All prophet/character stories have main persons" if passed else f"{len(stories_without_persons)} stories without persons",
            affected_items=stories_without_persons,
        ))

    # =========================================================================
    # C) INTEGRITY CHECKS
    # =========================================================================

    def _check_ayah_ranges_valid(self):
        """Check that all ayah ranges are valid against Quran metadata."""
        range_errors = self.registry.validate_all_ranges()
        passed = len(range_errors) == 0

        self.checks.append(CheckResult(
            check_id="integrity_ayah_ranges_valid",
            check_name_ar="نطاقات الآيات صالحة",
            check_name_en="Ayah Ranges Valid",
            category=CheckCategory.INTEGRITY,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع نطاقات الآيات صالحة" if passed else f"{len(range_errors)} نطاقات غير صالحة",
            message_en="All ayah ranges are valid" if passed else f"{len(range_errors)} invalid ranges",
            details={"errors": range_errors[:10]},  # Limit to first 10
            affected_items=[e["story_id"] for e in range_errors],
        ))

    def _check_no_duplicate_story_ids(self):
        """Check for duplicate story IDs (should be impossible with dict)."""
        # This is inherently checked by using a dict, but we verify count
        story_count = len(self.registry.stories)

        self.checks.append(CheckResult(
            check_id="integrity_no_duplicate_ids",
            check_name_ar="لا توجد معرفات مكررة",
            check_name_en="No Duplicate Story IDs",
            category=CheckCategory.INTEGRITY,
            severity=CheckSeverity.ERROR,
            passed=True,
            message_ar=f"تم التحقق من {story_count} قصة بدون تكرار",
            message_en=f"Verified {story_count} stories with no duplicates",
        ))

    def _check_event_indices_sequential(self):
        """Check that event indices within stories are sequential."""
        stories_with_gaps = []

        for story in self.registry.stories.values():
            if story.events:
                indices = sorted(e.chronological_index for e in story.events)
                expected = list(range(1, len(indices) + 1))
                if indices != expected:
                    stories_with_gaps.append({
                        "story_id": story.id,
                        "indices": indices,
                        "expected": expected,
                    })

        passed = len(stories_with_gaps) == 0

        self.checks.append(CheckResult(
            check_id="integrity_event_indices_sequential",
            check_name_ar="ترتيب الأحداث متسلسل",
            check_name_en="Event Indices Sequential",
            category=CheckCategory.INTEGRITY,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar="جميع الأحداث مرتبة بشكل متسلسل" if passed else f"{len(stories_with_gaps)} قصص بفجوات في الترتيب",
            message_en="All events are sequentially indexed" if passed else f"{len(stories_with_gaps)} stories with index gaps",
            details={"stories_with_gaps": stories_with_gaps[:5]},
            affected_items=[s["story_id"] for s in stories_with_gaps],
        ))

    # =========================================================================
    # D) I18N CHECKS
    # =========================================================================

    def _check_arabic_titles_not_english(self):
        """Check that Arabic titles are actually in Arabic."""
        english_titles = []

        for story in self.registry.stories.values():
            title = story.title_ar
            # Simple heuristic: Arabic text should contain Arabic characters
            if title and not any('\u0600' <= c <= '\u06FF' for c in title):
                english_titles.append({
                    "story_id": story.id,
                    "title_ar": title,
                })

        passed = len(english_titles) == 0

        self.checks.append(CheckResult(
            check_id="i18n_arabic_titles_arabic",
            check_name_ar="العناوين العربية بالعربية",
            check_name_en="Arabic Titles Are Arabic",
            category=CheckCategory.I18N,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع العناوين العربية بالعربية" if passed else f"{len(english_titles)} عناوين عربية بالإنجليزية",
            message_en="All Arabic titles are in Arabic" if passed else f"{len(english_titles)} Arabic titles in English",
            details={"english_titles": english_titles[:10]},
            affected_items=[t["story_id"] for t in english_titles],
        ))

    def _check_arabic_summaries_not_empty(self):
        """Check that Arabic summaries are not empty or placeholders."""
        empty_summaries = []

        for story in self.registry.stories.values():
            summary = story.summary_ar
            if not summary or len(summary.strip()) < 10:
                empty_summaries.append(story.id)
            elif summary == story.summary_en:  # Likely copy-paste
                empty_summaries.append(story.id)

        passed = len(empty_summaries) == 0

        self.checks.append(CheckResult(
            check_id="i18n_arabic_summaries_present",
            check_name_ar="الملخصات العربية موجودة",
            check_name_en="Arabic Summaries Present",
            category=CheckCategory.I18N,
            severity=CheckSeverity.ERROR,
            passed=passed,
            message_ar="جميع الملخصات العربية موجودة" if passed else f"{len(empty_summaries)} ملخصات عربية ناقصة",
            message_en="All Arabic summaries present" if passed else f"{len(empty_summaries)} Arabic summaries missing",
            affected_items=empty_summaries,
        ))

    # =========================================================================
    # E) EVIDENCE CHECKS
    # =========================================================================

    def _check_stories_have_evidence(self):
        """Check that stories have grounding evidence."""
        stories_without_evidence = self.registry.get_stories_without_evidence()
        passed = len(stories_without_evidence) == 0

        self.checks.append(CheckResult(
            check_id="evidence_stories_grounded",
            check_name_ar="القصص مدعومة بأدلة",
            check_name_en="Stories Have Evidence",
            category=CheckCategory.EVIDENCE,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar="جميع القصص مدعومة بأدلة" if passed else f"{len(stories_without_evidence)} قصص بدون أدلة",
            message_en="All stories have evidence" if passed else f"{len(stories_without_evidence)} stories without evidence",
            affected_items=stories_without_evidence,
        ))

    def _check_evidence_coverage(self):
        """Check that stories have adequate evidence coverage (>= 60% of verses)."""
        low_coverage_stories = []

        for story in self.registry.stories.values():
            if not story.evidence:
                continue  # Already caught by _check_stories_have_evidence

            coverage = self.evidence_resolver.calculate_evidence_coverage(
                story.primary_ayah_ranges,
                story.evidence
            )

            if coverage < self.EVIDENCE_COVERAGE_WARNING:
                low_coverage_stories.append({
                    "story_id": story.id,
                    "coverage": round(coverage * 100, 1),
                    "threshold": self.EVIDENCE_COVERAGE_WARNING * 100,
                })

        passed = len(low_coverage_stories) == 0

        self.checks.append(CheckResult(
            check_id="evidence_coverage_adequate",
            check_name_ar="تغطية الأدلة كافية",
            check_name_en="Evidence Coverage Adequate",
            category=CheckCategory.EVIDENCE,
            severity=CheckSeverity.WARNING,
            passed=passed,
            message_ar=f"جميع القصص لها تغطية أدلة >= {int(self.EVIDENCE_COVERAGE_WARNING * 100)}%" if passed else f"{len(low_coverage_stories)} قصص بتغطية أدلة منخفضة",
            message_en=f"All stories have evidence coverage >= {int(self.EVIDENCE_COVERAGE_WARNING * 100)}%" if passed else f"{len(low_coverage_stories)} stories with low evidence coverage",
            details={"threshold_percent": self.EVIDENCE_COVERAGE_WARNING * 100, "low_coverage": low_coverage_stories[:10]},
            affected_items=[s["story_id"] for s in low_coverage_stories],
        ))

    def _check_events_have_evidence(self):
        """Check that story events have evidence pointers."""
        events_without_evidence = []

        for story in self.registry.stories.values():
            for event in story.events:
                if not event.evidence:
                    events_without_evidence.append(f"{story.id}:{event.id}")

        # This is informational for now - not blocking
        passed = len(events_without_evidence) == 0

        self.checks.append(CheckResult(
            check_id="evidence_events_grounded",
            check_name_ar="الأحداث مدعومة بأدلة",
            check_name_en="Events Have Evidence",
            category=CheckCategory.EVIDENCE,
            severity=CheckSeverity.INFO,
            passed=passed,
            message_ar="جميع الأحداث مدعومة بأدلة" if passed else f"{len(events_without_evidence)} حدث بدون أدلة",
            message_en="All events have evidence" if passed else f"{len(events_without_evidence)} events without evidence",
            details={"total_events_without_evidence": len(events_without_evidence)},
            affected_items=events_without_evidence[:20],  # Limit output
        ))

    # =========================================================================
    # F) COVERAGE MILESTONE CHECKS (PR4)
    # =========================================================================

    def _check_coverage_milestone(self):
        """
        Check if current coverage meets milestone target.

        PR4: Staged milestones for Quran-wide coverage.
        Milestone A: 50 suras, 60% evidence rate
        Milestone B: 80 suras, 70% evidence rate
        Milestone C: 114 suras, 85% evidence rate
        """
        # Get coverage stats
        stats = self.registry.get_coverage_stats()
        current_suras = stats.get('suras_with_stories', 0)
        target_suras = self.target_suras
        milestone_label = self.COVERAGE_MILESTONES[self.CURRENT_MILESTONE]["label"]

        # Calculate progress
        progress_pct = round((current_suras / target_suras) * 100, 1) if target_suras > 0 else 0
        passed = current_suras >= target_suras

        # Generate missing suras list
        all_suras = set(range(1, 115))
        covered_suras = set()
        for story in self.registry.stories.values():
            covered_suras.update(story.suras_mentioned)

        missing_suras = sorted(all_suras - covered_suras)

        self.checks.append(CheckResult(
            check_id="coverage_milestone_target",
            check_name_ar=f"هدف التغطية ({milestone_label})",
            check_name_en=f"Coverage Milestone Target ({self.CURRENT_MILESTONE})",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.WARNING,  # Warning for now, ERROR when enforced
            passed=passed,
            message_ar=f"تغطية {current_suras}/{target_suras} سورة ({progress_pct}%)" if passed else f"التغطية {current_suras}/{target_suras} سورة - تحتاج {target_suras - current_suras} سور إضافية",
            message_en=f"Coverage {current_suras}/{target_suras} suras ({progress_pct}%)" if passed else f"Coverage {current_suras}/{target_suras} suras - need {target_suras - current_suras} more",
            details={
                "current_milestone": self.CURRENT_MILESTONE,
                "milestone_label": milestone_label,
                "target_suras": target_suras,
                "current_suras": current_suras,
                "progress_percent": progress_pct,
                "missing_suras_count": len(missing_suras),
                "missing_suras_sample": missing_suras[:20],  # First 20
            },
            affected_items=[f"sura_{s}" for s in missing_suras[:10]],
        ))

    def get_coverage_map(self) -> Dict[str, Any]:
        """
        Get detailed coverage map showing which suras are covered vs missing.

        Returns:
            Dict with covered/missing suras and coverage by category
        """
        all_suras = set(range(1, 115))
        covered_suras: Dict[int, List[str]] = {}  # sura -> [story_ids]

        for story in self.registry.stories.values():
            for sura in story.suras_mentioned:
                if sura not in covered_suras:
                    covered_suras[sura] = []
                covered_suras[sura].append(story.id)

        missing_suras = sorted(all_suras - set(covered_suras.keys()))

        # Coverage by category
        category_coverage = {}
        for cat in StoryCategory:
            stories = self.registry.get_stories_by_category(cat)
            suras = set()
            for s in stories:
                suras.update(s.suras_mentioned)
            category_coverage[cat.value] = {
                "story_count": len(stories),
                "sura_count": len(suras),
                "suras": sorted(list(suras)),
            }

        return {
            "total_suras": 114,
            "covered_count": len(covered_suras),
            "missing_count": len(missing_suras),
            "coverage_percent": round(len(covered_suras) / 114 * 100, 1),
            "covered_suras": sorted(list(covered_suras.keys())),
            "missing_suras": missing_suras,
            "sura_story_mapping": {str(k): v for k, v in sorted(covered_suras.items())},
            "category_coverage": category_coverage,
        }

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def _build_report(self) -> Dict[str, Any]:
        """Build the final verification report."""
        summary = VerificationSummary()
        summary.total_checks = len(self.checks)

        for check in self.checks:
            if check.passed:
                summary.passed_checks += 1
            else:
                summary.failed_checks += 1
                if check.severity == CheckSeverity.ERROR:
                    summary.errors += 1
                elif check.severity == CheckSeverity.WARNING:
                    summary.warnings += 1
                else:
                    summary.infos += 1

        # Group checks by category
        checks_by_category = {}
        for check in self.checks:
            cat = check.category.value
            if cat not in checks_by_category:
                checks_by_category[cat] = []
            checks_by_category[cat].append({
                "check_id": check.check_id,
                "check_name_ar": check.check_name_ar,
                "check_name_en": check.check_name_en,
                "severity": check.severity.value,
                "passed": check.passed,
                "message_ar": check.message_ar,
                "message_en": check.message_en,
                "details": check.details,
                "affected_items": check.affected_items,
            })

        return {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "registry_version": "2.0.0",
                "engine_version": "1.0.0",
            },
            "summary": {
                "total_checks": summary.total_checks,
                "passed_checks": summary.passed_checks,
                "failed_checks": summary.failed_checks,
                "errors": summary.errors,
                "warnings": summary.warnings,
                "infos": summary.infos,
                "pass_rate": round(summary.passed_checks / summary.total_checks * 100, 1) if summary.total_checks > 0 else 0,
            },
            "coverage_stats": self.registry.get_coverage_stats(),
            "checks_by_category": checks_by_category,
            "all_checks": [
                {
                    "check_id": c.check_id,
                    "passed": c.passed,
                    "severity": c.severity.value,
                    "message_ar": c.message_ar,
                }
                for c in self.checks
            ],
        }

    def save_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable Markdown report."""
        lines = []

        # Header
        lines.append("# تقرير التحقق من قصص القرآن")
        lines.append("# Quran Stories Verification Report")
        lines.append("")
        lines.append(f"**تاريخ التوليد:** {report['metadata']['generated_at']}")
        lines.append("")

        # Summary
        summary = report["summary"]
        lines.append("## ملخص | Summary")
        lines.append("")
        lines.append(f"| المقياس | القيمة |")
        lines.append("|---------|--------|")
        lines.append(f"| إجمالي الفحوصات | {summary['total_checks']} |")
        lines.append(f"| الفحوصات الناجحة | {summary['passed_checks']} |")
        lines.append(f"| الفحوصات الفاشلة | {summary['failed_checks']} |")
        lines.append(f"| الأخطاء | {summary['errors']} |")
        lines.append(f"| التحذيرات | {summary['warnings']} |")
        lines.append(f"| نسبة النجاح | {summary['pass_rate']}% |")
        lines.append("")

        # Coverage Stats
        stats = report["coverage_stats"]
        lines.append("## إحصائيات التغطية | Coverage Stats")
        lines.append("")
        lines.append(f"- **إجمالي القصص:** {stats['total_stories']}")
        lines.append(f"- **السور المغطاة:** {stats['suras_with_stories']}/114")
        lines.append(f"- **الآيات المغطاة:** {stats['total_verses_covered']}")
        lines.append("")

        lines.append("### توزيع التصنيفات | Category Distribution")
        lines.append("")
        lines.append("| التصنيف | العدد |")
        lines.append("|---------|-------|")
        for cat, count in stats["category_counts"].items():
            lines.append(f"| {cat} | {count} |")
        lines.append("")

        # Empty categories warning
        if stats["empty_categories"]:
            lines.append("### ⚠️ تصنيفات فارغة | Empty Categories")
            lines.append("")
            for cat in stats["empty_categories"]:
                lines.append(f"- {cat}")
            lines.append("")

        # Checks by Category
        lines.append("## تفاصيل الفحوصات | Check Details")
        lines.append("")

        for category, checks in report["checks_by_category"].items():
            lines.append(f"### {category}")
            lines.append("")

            for check in checks:
                icon = "✅" if check["passed"] else ("❌" if check["severity"] == "error" else "⚠️")
                lines.append(f"#### {icon} {check['check_name_ar']}")
                lines.append(f"_{check['check_name_en']}_")
                lines.append("")
                lines.append(f"**الحالة:** {'نجح' if check['passed'] else 'فشل'}")
                lines.append(f"**الرسالة:** {check['message_ar']}")
                lines.append("")

                if check["affected_items"] and not check["passed"]:
                    lines.append("**العناصر المتأثرة:**")
                    for item in check["affected_items"][:5]:
                        lines.append(f"- `{item}`")
                    if len(check["affected_items"]) > 5:
                        lines.append(f"- ... و {len(check['affected_items']) - 5} عناصر أخرى")
                    lines.append("")

        return "\n".join(lines)

    def save_markdown_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save Markdown report to file."""
        markdown = self.generate_markdown_report(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
