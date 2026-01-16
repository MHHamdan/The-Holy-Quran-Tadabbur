#!/usr/bin/env python3
"""
Prune Low Quality Theme Segments

This script identifies and removes low-quality discovered theme segments.

PRUNING CRITERIA:
=================
1. confidence < 0.35 (very low quality)
2. evidence_sources = 0 (no tafsir support)
3. reasons_ar contains placeholder text only

SAFETY RULES:
=============
- Never prunes segments with match_type='manual'
- Always runs in dry_run mode by default
- Requires explicit --execute flag to actually delete

USAGE:
======
# Dry run - see what would be pruned
python scripts/ingest/prune_low_quality_theme_segments.py

# Dry run for specific theme
python scripts/ingest/prune_low_quality_theme_segments.py --theme theme_tawheed

# Actually prune (after reviewing dry run)
python scripts/ingest/prune_low_quality_theme_segments.py --execute

# Quality report only
python scripts/ingest/prune_low_quality_theme_segments.py --report-only
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.theme_quality import ThemeQualityService


async def main():
    parser = argparse.ArgumentParser(
        description="Prune low-quality theme segments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--theme", "-t",
        help="Theme ID to prune (default: all themes)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete segments (default: dry run)"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate quality report, don't prune"
    )
    parser.add_argument(
        "--classify",
        action="store_true",
        help="Also run classification to update is_core flags"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Create database connection
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        service = ThemeQualityService(session)

        # Generate quality report
        print("=" * 60)
        print("THEME QUALITY REPORT")
        print("=" * 60)

        report = await service.get_quality_report(args.theme)

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"\nTheme: {report['theme_id']}")
            print(f"Total segments: {report['total_segments']}")
            print(f"  - Manual: {report['manual_segments']}")
            print(f"  - Discovered: {report['discovered_segments']}")
            print(f"  - Core: {report['core_segments']} ({report['core_percentage']}%)")
            print(f"  - Supporting: {report['supporting_segments']}")

            print("\nConfidence Distribution:")
            for band, count in report['confidence_distribution'].items():
                print(f"  - {band}: {count}")

            print("\nEvidence Distribution:")
            for band, count in report['evidence_distribution'].items():
                print(f"  - {band}: {count}")

            print(f"\nPruning candidates: {report['pruning_candidates']}")
            if report['sample_prune_candidates']:
                print("\nSample candidates:")
                for c in report['sample_prune_candidates']:
                    print(f"  - {c['id']} ({c['verse']}): {c['reason']}")

        if args.report_only:
            print("\n[Report-only mode, exiting]")
            return

        # Run classification if requested
        if args.classify:
            print("\n" + "=" * 60)
            print("CLASSIFICATION")
            print("=" * 60)

            dry_run = not args.execute
            classify_result = await service.classify_all_segments(
                theme_id=args.theme,
                dry_run=dry_run
            )

            print(f"\nClassified {classify_result['total_segments']} segments:")
            print(f"  - Core: {classify_result['core_segments']}")
            print(f"  - Supporting: {classify_result['supporting_segments']}")

            if dry_run:
                print("\n[Dry run - is_core flags NOT updated]")
            else:
                print("\n[is_core flags UPDATED in database]")

        # Find pruning candidates
        print("\n" + "=" * 60)
        print("PRUNING")
        print("=" * 60)

        candidates = await service.find_pruning_candidates(args.theme)

        if not candidates:
            print("\nNo segments meet pruning criteria. Database is clean!")
            return

        print(f"\nFound {len(candidates)} segments to prune:")

        # Group by theme
        by_theme = {}
        for c in candidates:
            if c.theme_id not in by_theme:
                by_theme[c.theme_id] = []
            by_theme[c.theme_id].append(c)

        for theme_id, theme_candidates in sorted(by_theme.items()):
            print(f"\n{theme_id}: {len(theme_candidates)} segments")
            for c in theme_candidates[:3]:  # Show first 3
                print(f"  - {c.sura_no}:{c.ayah_start} (conf: {c.confidence:.2f}): {c.prune_reason[:50]}...")

            if len(theme_candidates) > 3:
                print(f"  ... and {len(theme_candidates) - 3} more")

        # Execute pruning
        dry_run = not args.execute

        if dry_run:
            print("\n" + "-" * 40)
            print("DRY RUN - No segments deleted")
            print("To actually prune, run with --execute flag")
            print("-" * 40)
        else:
            print("\n" + "-" * 40)
            print("EXECUTING PRUNE...")
            print("-" * 40)

            result = await service.prune_segments(candidates, dry_run=False)

            print(f"\nPruned {result['pruned_count']} segments")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
