"""
Warning Budget Service

Reduces warning noise by:
1. Grouping similar warnings together
2. Implementing a per-category warning budget
3. Providing summary reports instead of individual warnings

Usage:
------
from app.core.warning_budget import WarningBudget

# Create budget with 10 warnings per category
budget = WarningBudget(default_budget=10)

# Add warnings (returns True if within budget)
if budget.add("missing_tafsir", f"No tafsir for {verse}"):
    logger.warning(f"No tafsir for {verse}")

# At the end, log summary
budget.log_summary(logger)

# Categories with custom budgets
budget = WarningBudget(
    default_budget=10,
    category_budgets={
        "missing_tafsir": 5,
        "low_confidence": 20,
    }
)
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime


@dataclass
class WarningEntry:
    """A single warning entry."""
    category: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CategorySummary:
    """Summary for a warning category."""
    category: str
    total_count: int
    logged_count: int
    suppressed_count: int
    sample_messages: List[str]
    budget: int


class WarningBudget:
    """
    Warning budget manager that groups and limits warnings.

    Provides:
    - Per-category warning budgets
    - Grouping of similar warnings
    - Summary reporting
    - Suppression of warnings over budget
    """

    def __init__(
        self,
        default_budget: int = 10,
        category_budgets: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize warning budget.

        Args:
            default_budget: Default budget per category
            category_budgets: Override budgets for specific categories
        """
        self.default_budget = default_budget
        self.category_budgets = category_budgets or {}
        self.warnings: Dict[str, List[WarningEntry]] = defaultdict(list)
        self.logged_counts: Dict[str, int] = defaultdict(int)

    def get_budget(self, category: str) -> int:
        """Get budget for a category."""
        return self.category_budgets.get(category, self.default_budget)

    def add(
        self,
        category: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a warning and check if it should be logged.

        Returns True if warning is within budget and should be logged.
        Returns False if warning is suppressed (over budget).
        """
        entry = WarningEntry(
            category=category,
            message=message,
            metadata=metadata or {},
        )
        self.warnings[category].append(entry)

        budget = self.get_budget(category)
        current_logged = self.logged_counts[category]

        if current_logged < budget:
            self.logged_counts[category] += 1
            return True
        return False

    def get_summary(self) -> List[CategorySummary]:
        """Get summary of all warning categories."""
        summaries = []
        for category, entries in self.warnings.items():
            budget = self.get_budget(category)
            logged = min(len(entries), budget)
            suppressed = max(0, len(entries) - budget)

            # Sample messages (first 3)
            sample_messages = [e.message for e in entries[:3]]

            summaries.append(CategorySummary(
                category=category,
                total_count=len(entries),
                logged_count=logged,
                suppressed_count=suppressed,
                sample_messages=sample_messages,
                budget=budget,
            ))

        # Sort by total count descending
        summaries.sort(key=lambda s: s.total_count, reverse=True)
        return summaries

    def log_summary(self, logger: logging.Logger):
        """Log a summary of all warnings."""
        summaries = self.get_summary()
        if not summaries:
            return

        total_warnings = sum(s.total_count for s in summaries)
        total_suppressed = sum(s.suppressed_count for s in summaries)

        logger.info(f"Warning summary: {total_warnings} total, {total_suppressed} suppressed")

        for summary in summaries:
            if summary.suppressed_count > 0:
                logger.info(
                    f"  [{summary.category}] {summary.total_count} warnings "
                    f"({summary.suppressed_count} suppressed)"
                )
            else:
                logger.debug(
                    f"  [{summary.category}] {summary.total_count} warnings"
                )

    def reset(self):
        """Reset all warnings and counts."""
        self.warnings.clear()
        self.logged_counts.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        summaries = self.get_summary()
        return {
            "total_warnings": sum(s.total_count for s in summaries),
            "total_suppressed": sum(s.suppressed_count for s in summaries),
            "categories": [
                {
                    "category": s.category,
                    "total": s.total_count,
                    "logged": s.logged_count,
                    "suppressed": s.suppressed_count,
                    "samples": s.sample_messages,
                }
                for s in summaries
            ],
        }


# Global warning budget instance (can be used app-wide)
_global_budget: Optional[WarningBudget] = None


def get_warning_budget() -> WarningBudget:
    """Get or create global warning budget instance."""
    global _global_budget
    if _global_budget is None:
        _global_budget = WarningBudget(
            default_budget=10,
            category_budgets={
                "missing_tafsir": 5,
                "low_confidence": 15,
                "no_evidence": 10,
                "placeholder_text": 5,
                "theme_guard_fail": 10,
            }
        )
    return _global_budget


def reset_warning_budget():
    """Reset global warning budget."""
    global _global_budget
    if _global_budget:
        _global_budget.reset()


class WarningContext:
    """
    Context manager for warning budget in a specific operation.

    Usage:
    ------
    with WarningContext("discovery", default_budget=20) as budget:
        # ... do work, add warnings ...
        budget.add("category", "message")

    # Summary is automatically logged at end
    """

    def __init__(
        self,
        operation_name: str,
        default_budget: int = 10,
        category_budgets: Optional[Dict[str, int]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.operation_name = operation_name
        self.budget = WarningBudget(
            default_budget=default_budget,
            category_budgets=category_budgets,
        )
        self.logger = logger or logging.getLogger(__name__)

    def __enter__(self) -> WarningBudget:
        return self.budget

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"[{self.operation_name}] Operation completed")
        else:
            self.logger.error(f"[{self.operation_name}] Operation failed: {exc_val}")
        self.budget.log_summary(self.logger)
        return False
