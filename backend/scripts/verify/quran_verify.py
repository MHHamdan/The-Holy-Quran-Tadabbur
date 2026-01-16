#!/usr/bin/env python3
"""
Quran Story Verification Script.

Runs comprehensive verification checks on the Quran story registry
and produces JSON + Markdown reports.

Usage:
    python scripts/verify/quran_verify.py
    python scripts/verify/quran_verify.py --format json
    python scripts/verify/quran_verify.py --output-dir reports/
    python scripts/verify/quran_verify.py --ci  # Exit with error code if checks fail

Example:
    # Run verification and save reports
    python scripts/verify/quran_verify.py --output-dir reports/verification/

    # Run in CI mode (exit 1 on errors)
    python scripts/verify/quran_verify.py --ci
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.verify.registry import QuranStoryRegistry
from app.verify.engine import QuranVerificationEngine
from app.verify.report import VerificationReport, format_report_for_ci


def main():
    parser = argparse.ArgumentParser(
        description="Quran Story Verification - تحقق من قصص القرآن",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run all checks, print summary
  %(prog)s --format both             # Generate JSON and Markdown reports
  %(prog)s --output-dir reports/     # Save reports to directory
  %(prog)s --ci                      # CI mode: exit 1 on errors
  %(prog)s --manifest path/to.json   # Use custom manifest
        """
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=backend_dir / "data" / "manifests" / "stories.json",
        help="Path to stories manifest (default: data/manifests/stories.json)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output reports"
    )

    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)"
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with code 1 if any errors"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Validate manifest exists
    if not args.manifest.exists():
        # Try relative to backend
        args.manifest = backend_dir.parent / "data" / "manifests" / "stories.json"
        if not args.manifest.exists():
            print(f"❌ Manifest not found: {args.manifest}")
            sys.exit(1)

    print(f"📖 Loading stories from: {args.manifest}")

    # Load registry
    registry = QuranStoryRegistry()
    loaded = registry.load_from_manifest(args.manifest)
    print(f"📚 Loaded {loaded} stories")

    # Run verification
    print("🔍 Running verification checks...")
    engine = QuranVerificationEngine(registry)
    report_dict = engine.run_all_checks()

    # Create report object
    report = VerificationReport.from_engine_report(report_dict)

    # Print summary
    print("")
    print(format_report_for_ci(report))
    print("")

    # Save reports if output dir specified
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if args.format in ("json", "both"):
            json_path = args.output_dir / f"verification_{timestamp}.json"
            engine.save_report(report_dict, json_path)
            print(f"📄 JSON report: {json_path}")

        if args.format in ("markdown", "both"):
            md_path = args.output_dir / f"verification_{timestamp}.md"
            engine.save_markdown_report(report_dict, md_path)
            print(f"📝 Markdown report: {md_path}")

    # Verbose output
    if args.verbose:
        print("\n" + "=" * 60)
        print("DETAILED CHECKS:")
        print("=" * 60)
        for check in report.checks:
            icon = "✅" if check.get("passed") else "❌"
            print(f"{icon} {check.get('check_id')}: {check.get('message_ar')}")

    # CI mode exit code
    if args.ci:
        if report.errors > 0:
            print(f"\n❌ CI mode: Exiting with code 1 ({report.errors} errors)")
            sys.exit(1)
        else:
            print(f"\n✅ CI mode: All critical checks passed")
            sys.exit(0)


if __name__ == "__main__":
    main()
