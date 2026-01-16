#!/usr/bin/env python3
"""
Theme Quality Distribution Analysis

Outputs per-theme histograms for:
- Confidence buckets (0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8+)
- Distinct tafsir sources count
- Match type distribution
- Segments meeting current "core" rule

Usage:
    python scripts/verify/theme_quality_distribution.py
    python scripts/verify/theme_quality_distribution.py --theme theme_tawheed
    python scripts/verify/theme_quality_distribution.py --json --output report.json
"""
import sys
import os
import json
import argparse
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Classification thresholds (current)
CURRENT_CORE_MIN_CONFIDENCE = 0.72
CURRENT_CORE_MIN_SOURCES = 2

# Proposed 3-tier thresholds
CORE_CONFIDENCE_DIRECT = 0.82
CORE_CONFIDENCE_MULTI_SOURCE = 0.74
RECOMMENDED_CONFIDENCE_SINGLE = 0.70
RECOMMENDED_CONFIDENCE_MULTI = 0.65
DIRECT_MATCH_TYPES = {'direct', 'exact', 'root', 'lexical'}
WEAK_MATCH_TYPES = {'weak', 'semantic_low'}


@dataclass
class ConfidenceBucket:
    """Confidence distribution bucket."""
    range_label: str
    min_val: float
    max_val: float
    count: int = 0


@dataclass
class ThemeDistribution:
    """Distribution stats for a single theme."""
    theme_id: str
    title_ar: str
    title_en: str
    total_segments: int
    manual_segments: int
    discovered_segments: int

    # Confidence distribution
    confidence_0_5_to_0_6: int = 0
    confidence_0_6_to_0_7: int = 0
    confidence_0_7_to_0_8: int = 0
    confidence_0_8_plus: int = 0

    # Source distribution
    sources_0: int = 0
    sources_1: int = 0
    sources_2: int = 0
    sources_3_plus: int = 0

    # Match type distribution
    match_manual: int = 0
    match_lexical: int = 0
    match_root: int = 0
    match_semantic: int = 0
    match_mixed: int = 0
    match_other: int = 0

    # Current classification
    current_core: int = 0
    current_supporting: int = 0

    # Proposed 3-tier classification
    proposed_core: int = 0
    proposed_recommended: int = 0
    proposed_supporting: int = 0

    # Failure reasons for core
    fail_low_confidence: int = 0
    fail_few_sources: int = 0
    fail_weak_match: int = 0
    fail_no_reasons: int = 0


@dataclass
class GlobalDistribution:
    """Global distribution across all themes."""
    total_segments: int = 0
    total_themes: int = 0

    # Global confidence
    confidence_0_5_to_0_6: int = 0
    confidence_0_6_to_0_7: int = 0
    confidence_0_7_to_0_8: int = 0
    confidence_0_8_plus: int = 0

    # Global sources
    sources_0: int = 0
    sources_1: int = 0
    sources_2: int = 0
    sources_3_plus: int = 0

    # Global match types
    match_manual: int = 0
    match_lexical: int = 0
    match_root: int = 0
    match_semantic: int = 0
    match_mixed: int = 0
    match_other: int = 0

    # Classification totals
    current_core: int = 0
    current_supporting: int = 0
    proposed_core: int = 0
    proposed_recommended: int = 0
    proposed_supporting: int = 0

    # Failure reasons
    fail_low_confidence: int = 0
    fail_few_sources: int = 0
    fail_weak_match: int = 0
    fail_no_reasons: int = 0


def get_db_url() -> str:
    """Get database URL from environment or default."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def classify_current(confidence: float, source_count: int, reasons_ar: str) -> str:
    """Current 2-tier classification."""
    if confidence >= CURRENT_CORE_MIN_CONFIDENCE and source_count >= CURRENT_CORE_MIN_SOURCES:
        if reasons_ar and len(reasons_ar.strip()) > 10:
            return "core"
    return "supporting"


def classify_proposed(confidence: float, source_count: int, match_type: str) -> str:
    """
    Proposed 3-tier classification:

    CORE if:
      (confidence >= 0.82 AND match_type in {DIRECT, EXACT, ROOT}) OR
      (confidence >= 0.74 AND distinct_sources >= 2)

    RECOMMENDED if:
      (confidence >= 0.70 AND match_type not WEAK) OR
      (confidence >= 0.65 AND distinct_sources >= 2)

    SUPPORTING otherwise
    """
    match_type_lower = (match_type or '').lower()
    is_direct = match_type_lower in DIRECT_MATCH_TYPES or match_type_lower == 'manual'
    is_weak = match_type_lower in WEAK_MATCH_TYPES

    # CORE criteria
    if confidence >= CORE_CONFIDENCE_DIRECT and is_direct:
        return "core"
    if confidence >= CORE_CONFIDENCE_MULTI_SOURCE and source_count >= 2:
        return "core"

    # RECOMMENDED criteria
    if confidence >= RECOMMENDED_CONFIDENCE_SINGLE and not is_weak:
        return "recommended"
    if confidence >= RECOMMENDED_CONFIDENCE_MULTI and source_count >= 2:
        return "recommended"

    return "supporting"


def get_failure_reason(confidence: float, source_count: int, match_type: str, reasons_ar: str) -> str:
    """Determine why a segment fails core classification."""
    if not reasons_ar or len(reasons_ar.strip()) < 10:
        return "no_reasons"
    if confidence < CURRENT_CORE_MIN_CONFIDENCE:
        return "low_confidence"
    if source_count < CURRENT_CORE_MIN_SOURCES:
        return "few_sources"
    match_type_lower = (match_type or '').lower()
    if match_type_lower in WEAK_MATCH_TYPES:
        return "weak_match"
    return "unknown"


def analyze_theme(session: Session, theme_id: str) -> ThemeDistribution:
    """Analyze distribution for a single theme."""
    # Get theme info
    theme_result = session.execute(text("""
        SELECT id, title_ar, title_en
        FROM quranic_themes
        WHERE id = :theme_id
    """), {"theme_id": theme_id})
    theme_row = theme_result.fetchone()

    if not theme_row:
        raise ValueError(f"Theme not found: {theme_id}")

    dist = ThemeDistribution(
        theme_id=theme_id,
        title_ar=theme_row[1] or "",
        title_en=theme_row[2] or "",
        total_segments=0,
        manual_segments=0,
        discovered_segments=0,
    )

    # Get all segments for this theme
    result = session.execute(text("""
        SELECT
            confidence,
            match_type,
            evidence_sources,
            reasons_ar,
            is_core
        FROM theme_segments
        WHERE theme_id = :theme_id
    """), {"theme_id": theme_id})

    for row in result:
        confidence = row[0] or 0.0
        match_type = row[1] or ""
        evidence_sources = row[2] or []
        reasons_ar = row[3] or ""
        is_core_db = row[4] or False

        dist.total_segments += 1

        # Count sources
        source_count = len(evidence_sources) if isinstance(evidence_sources, list) else 0

        # Manual vs discovered
        if match_type == 'manual' or match_type is None:
            dist.manual_segments += 1
        else:
            dist.discovered_segments += 1

        # Confidence buckets
        if confidence < 0.6:
            dist.confidence_0_5_to_0_6 += 1
        elif confidence < 0.7:
            dist.confidence_0_6_to_0_7 += 1
        elif confidence < 0.8:
            dist.confidence_0_7_to_0_8 += 1
        else:
            dist.confidence_0_8_plus += 1

        # Source buckets
        if source_count == 0:
            dist.sources_0 += 1
        elif source_count == 1:
            dist.sources_1 += 1
        elif source_count == 2:
            dist.sources_2 += 1
        else:
            dist.sources_3_plus += 1

        # Match type buckets
        mt = (match_type or '').lower()
        if mt == 'manual' or mt == '':
            dist.match_manual += 1
        elif mt == 'lexical':
            dist.match_lexical += 1
        elif mt == 'root':
            dist.match_root += 1
        elif mt == 'semantic':
            dist.match_semantic += 1
        elif mt == 'mixed':
            dist.match_mixed += 1
        else:
            dist.match_other += 1

        # Current classification
        current_class = classify_current(confidence, source_count, reasons_ar)
        if current_class == "core":
            dist.current_core += 1
        else:
            dist.current_supporting += 1
            # Track failure reason
            reason = get_failure_reason(confidence, source_count, match_type, reasons_ar)
            if reason == "low_confidence":
                dist.fail_low_confidence += 1
            elif reason == "few_sources":
                dist.fail_few_sources += 1
            elif reason == "weak_match":
                dist.fail_weak_match += 1
            elif reason == "no_reasons":
                dist.fail_no_reasons += 1

        # Proposed 3-tier classification
        proposed_class = classify_proposed(confidence, source_count, match_type)
        if proposed_class == "core":
            dist.proposed_core += 1
        elif proposed_class == "recommended":
            dist.proposed_recommended += 1
        else:
            dist.proposed_supporting += 1

    return dist


def analyze_all_themes(session: Session) -> tuple[GlobalDistribution, List[ThemeDistribution]]:
    """Analyze all themes and compute global distribution."""
    # Get all themes
    result = session.execute(text("""
        SELECT id FROM quranic_themes ORDER BY order_of_importance
    """))
    theme_ids = [row[0] for row in result]

    global_dist = GlobalDistribution(total_themes=len(theme_ids))
    theme_dists = []

    for theme_id in theme_ids:
        dist = analyze_theme(session, theme_id)
        theme_dists.append(dist)

        # Aggregate into global
        global_dist.total_segments += dist.total_segments

        global_dist.confidence_0_5_to_0_6 += dist.confidence_0_5_to_0_6
        global_dist.confidence_0_6_to_0_7 += dist.confidence_0_6_to_0_7
        global_dist.confidence_0_7_to_0_8 += dist.confidence_0_7_to_0_8
        global_dist.confidence_0_8_plus += dist.confidence_0_8_plus

        global_dist.sources_0 += dist.sources_0
        global_dist.sources_1 += dist.sources_1
        global_dist.sources_2 += dist.sources_2
        global_dist.sources_3_plus += dist.sources_3_plus

        global_dist.match_manual += dist.match_manual
        global_dist.match_lexical += dist.match_lexical
        global_dist.match_root += dist.match_root
        global_dist.match_semantic += dist.match_semantic
        global_dist.match_mixed += dist.match_mixed
        global_dist.match_other += dist.match_other

        global_dist.current_core += dist.current_core
        global_dist.current_supporting += dist.current_supporting
        global_dist.proposed_core += dist.proposed_core
        global_dist.proposed_recommended += dist.proposed_recommended
        global_dist.proposed_supporting += dist.proposed_supporting

        global_dist.fail_low_confidence += dist.fail_low_confidence
        global_dist.fail_few_sources += dist.fail_few_sources
        global_dist.fail_weak_match += dist.fail_weak_match
        global_dist.fail_no_reasons += dist.fail_no_reasons

    return global_dist, theme_dists


def print_histogram(label: str, buckets: Dict[str, int], total: int):
    """Print ASCII histogram."""
    print(f"\n{label}:")
    max_count = max(buckets.values()) if buckets.values() else 1
    bar_width = 40

    for name, count in buckets.items():
        pct = (count / total * 100) if total > 0 else 0
        bar_len = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = "█" * bar_len
        print(f"  {name:20} {count:5} ({pct:5.1f}%) {bar}")


def print_report(global_dist: GlobalDistribution, theme_dists: List[ThemeDistribution]):
    """Print human-readable report."""
    print("=" * 70)
    print("THEME QUALITY DISTRIBUTION REPORT")
    print("=" * 70)

    total = global_dist.total_segments

    print(f"\nTotal Segments: {total}")
    print(f"Total Themes: {global_dist.total_themes}")

    # Confidence distribution
    print_histogram("CONFIDENCE DISTRIBUTION", {
        "0.5-0.6 (Low)": global_dist.confidence_0_5_to_0_6,
        "0.6-0.7 (Medium)": global_dist.confidence_0_6_to_0_7,
        "0.7-0.8 (Good)": global_dist.confidence_0_7_to_0_8,
        "0.8+ (High)": global_dist.confidence_0_8_plus,
    }, total)

    # Source distribution
    print_histogram("TAFSIR SOURCE DISTRIBUTION", {
        "0 sources": global_dist.sources_0,
        "1 source": global_dist.sources_1,
        "2 sources": global_dist.sources_2,
        "3+ sources": global_dist.sources_3_plus,
    }, total)

    # Match type distribution
    print_histogram("MATCH TYPE DISTRIBUTION", {
        "Manual": global_dist.match_manual,
        "Lexical": global_dist.match_lexical,
        "Root": global_dist.match_root,
        "Semantic": global_dist.match_semantic,
        "Mixed": global_dist.match_mixed,
        "Other": global_dist.match_other,
    }, total)

    # Current classification
    print_histogram("CURRENT CLASSIFICATION (2-tier)", {
        "Core": global_dist.current_core,
        "Supporting": global_dist.current_supporting,
    }, total)

    # Proposed classification
    print_histogram("PROPOSED CLASSIFICATION (3-tier)", {
        "Core": global_dist.proposed_core,
        "Recommended": global_dist.proposed_recommended,
        "Supporting": global_dist.proposed_supporting,
    }, total)

    # Failure reasons
    supporting_count = global_dist.current_supporting
    if supporting_count > 0:
        print_histogram("REASONS FOR SUPPORTING (not Core)", {
            "Low confidence (<0.72)": global_dist.fail_low_confidence,
            "Few sources (<2)": global_dist.fail_few_sources,
            "Weak match type": global_dist.fail_weak_match,
            "Missing reasons_ar": global_dist.fail_no_reasons,
        }, supporting_count)

    # Improvement summary
    print("\n" + "=" * 70)
    print("IMPROVEMENT SUMMARY")
    print("=" * 70)

    current_quality = global_dist.current_core
    proposed_quality = global_dist.proposed_core + global_dist.proposed_recommended

    current_pct = (current_quality / total * 100) if total > 0 else 0
    proposed_pct = (proposed_quality / total * 100) if total > 0 else 0

    print(f"\nCurrent quality segments (Core only): {current_quality} ({current_pct:.1f}%)")
    print(f"Proposed quality segments (Core + Recommended): {proposed_quality} ({proposed_pct:.1f}%)")
    print(f"Improvement: +{proposed_quality - current_quality} segments (+{proposed_pct - current_pct:.1f}%)")

    # Top themes by proposed quality
    print("\n" + "-" * 40)
    print("TOP 10 THEMES BY QUALITY (Proposed)")
    print("-" * 40)

    sorted_themes = sorted(
        theme_dists,
        key=lambda t: t.proposed_core + t.proposed_recommended,
        reverse=True
    )[:10]

    for i, t in enumerate(sorted_themes, 1):
        quality = t.proposed_core + t.proposed_recommended
        print(f"{i:2}. {t.title_ar[:20]:20} Core: {t.proposed_core:3}, Rec: {t.proposed_recommended:3}, Total: {t.total_segments:3}")

    # Themes needing improvement
    print("\n" + "-" * 40)
    print("THEMES NEEDING IMPROVEMENT (0 Core+Recommended)")
    print("-" * 40)

    weak_themes = [t for t in theme_dists if t.proposed_core + t.proposed_recommended == 0]
    if weak_themes:
        for t in weak_themes[:10]:
            print(f"  - {t.theme_id}: {t.title_ar} ({t.total_segments} segments)")
        if len(weak_themes) > 10:
            print(f"  ... and {len(weak_themes) - 10} more")
    else:
        print("  None! All themes have at least 1 quality segment.")


def main():
    parser = argparse.ArgumentParser(
        description="Theme Quality Distribution Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--theme", "-t",
        help="Analyze specific theme only"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        if args.theme:
            # Single theme analysis
            dist = analyze_theme(session, args.theme)

            if args.json:
                output = asdict(dist)
            else:
                print(f"\nTheme: {dist.theme_id}")
                print(f"Title: {dist.title_ar} / {dist.title_en}")
                print(f"Total: {dist.total_segments} (Manual: {dist.manual_segments}, Discovered: {dist.discovered_segments})")
                print(f"\nConfidence: 0.5-0.6: {dist.confidence_0_5_to_0_6}, 0.6-0.7: {dist.confidence_0_6_to_0_7}, 0.7-0.8: {dist.confidence_0_7_to_0_8}, 0.8+: {dist.confidence_0_8_plus}")
                print(f"Sources: 0: {dist.sources_0}, 1: {dist.sources_1}, 2: {dist.sources_2}, 3+: {dist.sources_3_plus}")
                print(f"\nCurrent: Core: {dist.current_core}, Supporting: {dist.current_supporting}")
                print(f"Proposed: Core: {dist.proposed_core}, Recommended: {dist.proposed_recommended}, Supporting: {dist.proposed_supporting}")
                return
        else:
            # All themes analysis
            global_dist, theme_dists = analyze_all_themes(session)

            if args.json:
                output = {
                    "global": asdict(global_dist),
                    "themes": [asdict(t) for t in theme_dists],
                }
            else:
                print_report(global_dist, theme_dists)
                return

    # JSON output
    if args.json:
        json_str = json.dumps(output, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"Report written to: {args.output}")
        else:
            print(json_str)


if __name__ == "__main__":
    main()
