#!/usr/bin/env python3
"""
Fix Theme Arabic Fields Script

Detects and fixes Arabic fields that contain English leakage.
Replaces placeholder text like "آية تتعلق بموضوع: sabr" with proper Arabic.

Strategy:
1. Detect Latin characters in *_ar fields
2. Replace theme name placeholders with Arabic titles
3. Generate proper Arabic summaries based on verse content

Usage:
    python scripts/ingest/fix_theme_arabic_fields.py
    python scripts/ingest/fix_theme_arabic_fields.py --dry-run
    python scripts/ingest/fix_theme_arabic_fields.py --only theme_sabr

Author: Claude Code (Tadabbur-AI)
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


# =============================================================================
# CONSTANTS
# =============================================================================

# Theme ID to Arabic title mapping
THEME_TITLES_AR = {
    'adl': 'العدل',
    'amanah': 'الأمانة',
    'asma_sifat': 'الأسماء والصفات',
    'birr_walidayn': 'بر الوالدين',
    'dhikr': 'الذكر',
    'dua': 'الدعاء',
    'fasad': 'الفساد في الأرض',
    'ghish': 'الغش والخداع',
    'hajj': 'الحج',
    'ihsan': 'الإحسان',
    'ikhlas': 'الإخلاص',
    'iman_billah': 'الإيمان بالله',
    'iman_kutub': 'الإيمان بالكتب',
    'iman_malaika': 'الإيمان بالملائكة',
    'iman_qadr': 'الإيمان بالقدر',
    'iman_rusul': 'الإيمان بالرسل',
    'iman_yawm_akhir': 'الإيمان باليوم الآخر',
    'infaq': 'الإنفاق في سبيل الله',
    'islah': 'الإصلاح',
    'jannah': 'الجنة ونعيمها',
    'khushu': 'الخشوع',
    'kibr': 'الكبر',
    'kidhb': 'الكذب',
    'maghfira': 'المغفرة والرحمة',
    'nar': 'النار وعذابها',
    'nifaq': 'النفاق',
    'rahma': 'رحمة الله',
    'riba': 'الربا',
    'sabr': 'الصبر',
    'salah': 'الصلاة',
    'shirk': 'الشرك',
    'shukr': 'الشكر',
    'sidq': 'الصدق',
    'silat_rahim': 'صلة الرحم',
    'siyam': 'الصيام',
    'sunnah_ibtila': 'سنة الابتلاء',
    'sunnah_ihlak': 'سنة إهلاك الأمم',
    'sunnah_istidraj': 'سنة الاستدراج',
    'sunnah_nasr': 'سنة النصر والتمكين',
    'sunnah_taghyir': 'سنة التغيير',
    'taqwa': 'التقوى',
    'tawadu': 'التواضع',
    'tawakkul': 'التوكل على الله',
    'tawbah': 'التوبة',
    'tawheed': 'التوحيد',
    'tawheed_rububiyyah': 'توحيد الربوبية',
    'tawheed_uluhiyyah': 'توحيد الألوهية',
    'uquq_walidayn': 'عقوق الوالدين',
    'zakah': 'الزكاة',
    'zulm': 'الظلم',
}

# Pattern to detect Latin characters (excluding common punctuation)
LATIN_PATTERN = re.compile(r'[a-zA-Z]')

# Placeholder patterns
PLACEHOLDER_PATTERN = re.compile(r'آية تتعلق بموضوع:\s*(\w+)', re.UNICODE)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FieldFix:
    """A single field fix."""
    segment_id: str
    field_name: str
    old_value: str
    new_value: str
    fix_type: str  # 'placeholder_replace', 'remove_latin', etc.


@dataclass
class FixReport:
    """Report of fixes made."""
    timestamp: str
    mode: str
    total_segments_checked: int = 0
    segments_with_issues: int = 0
    fields_fixed: int = 0
    fixes: List[FieldFix] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def has_latin_chars(text: str) -> bool:
    """Check if text contains Latin characters."""
    if not text:
        return False
    return bool(LATIN_PATTERN.search(text))


def get_latin_percentage(text: str) -> float:
    """Calculate percentage of Latin characters."""
    if not text:
        return 0.0
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return 0.0
    latin = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    return (latin / total_alpha) * 100


def extract_theme_key(theme_id: str) -> str:
    """Extract theme key from theme_id (remove 'theme_' prefix)."""
    if theme_id.startswith('theme_'):
        return theme_id[6:]
    return theme_id


def get_arabic_title(theme_id: str) -> str:
    """Get Arabic title for a theme."""
    key = extract_theme_key(theme_id)
    return THEME_TITLES_AR.get(key, key)


def fix_placeholder_text(text: str, theme_id: str) -> Tuple[str, bool]:
    """
    Fix placeholder text like 'آية تتعلق بموضوع: sabr'.

    Returns:
        (fixed_text, was_fixed)
    """
    if not text:
        return text, False

    # Check for placeholder pattern
    match = PLACEHOLDER_PATTERN.search(text)
    if match:
        english_theme = match.group(1)
        arabic_title = THEME_TITLES_AR.get(english_theme, get_arabic_title(theme_id))

        # Create proper Arabic summary
        new_text = f"آيات في {arabic_title}"
        return new_text, True

    return text, False


def generate_verse_summary_ar(sura: int, aya_start: int, aya_end: int, theme_id: str) -> str:
    """Generate a proper Arabic summary for a verse segment."""
    arabic_title = get_arabic_title(theme_id)

    if aya_start == aya_end:
        return f"آية في {arabic_title} من سورة {sura}:{aya_start}"
    else:
        return f"آيات في {arabic_title} من سورة {sura}:{aya_start}-{aya_end}"


def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


# =============================================================================
# DATABASE QUERIES
# =============================================================================

def fetch_segments_with_arabic_issues(session: Session, only_theme: Optional[str] = None) -> List[Dict]:
    """Fetch segments that have Arabic field issues."""
    query = """
        SELECT id, theme_id, sura_no, ayah_start, ayah_end,
               summary_ar, summary_en, title_ar, title_en
        FROM theme_segments
        WHERE 1=1
    """
    params = {}

    if only_theme:
        query += " AND theme_id = :theme_id"
        params['theme_id'] = only_theme

    query += " ORDER BY theme_id, segment_order"

    result = session.execute(text(query), params)

    segments = []
    for row in result:
        segments.append({
            'id': row[0],
            'theme_id': row[1],
            'sura_no': row[2],
            'ayah_start': row[3],
            'ayah_end': row[4],
            'summary_ar': row[5],
            'summary_en': row[6],
            'title_ar': row[7],
            'title_en': row[8],
        })
    return segments


def update_segment_arabic_fields(
    session: Session,
    segment_id: str,
    summary_ar: Optional[str] = None,
    title_ar: Optional[str] = None
):
    """Update Arabic fields for a segment."""
    updates = []
    params = {'segment_id': segment_id}

    if summary_ar is not None:
        updates.append("summary_ar = :summary_ar")
        params['summary_ar'] = summary_ar

    if title_ar is not None:
        updates.append("title_ar = :title_ar")
        params['title_ar'] = title_ar

    if updates:
        updates.append("updated_at = NOW()")
        query = f"UPDATE theme_segments SET {', '.join(updates)} WHERE id = :segment_id"
        session.execute(text(query), params)


# =============================================================================
# MAIN FIX FUNCTION
# =============================================================================

def fix_arabic_fields(
    session: Session,
    dry_run: bool = False,
    only_theme: Optional[str] = None,
    verbose: bool = False
) -> FixReport:
    """
    Fix Arabic fields in theme segments.

    Args:
        session: Database session
        dry_run: If True, don't write changes
        only_theme: Filter to specific theme
        verbose: Print detailed output

    Returns:
        FixReport with results
    """
    report = FixReport(
        timestamp=datetime.utcnow().isoformat(),
        mode="dry-run" if dry_run else "live",
    )

    # Fetch segments
    segments = fetch_segments_with_arabic_issues(session, only_theme)
    report.total_segments_checked = len(segments)

    print(f"Checking {len(segments)} segments for Arabic issues...")

    for segment in segments:
        segment_fixes = []

        # Check summary_ar
        summary_ar = segment.get('summary_ar') or ''
        if has_latin_chars(summary_ar):
            # Try to fix placeholder text
            fixed_text, was_fixed = fix_placeholder_text(summary_ar, segment['theme_id'])

            if was_fixed:
                segment_fixes.append(FieldFix(
                    segment_id=segment['id'],
                    field_name='summary_ar',
                    old_value=summary_ar,
                    new_value=fixed_text,
                    fix_type='placeholder_replace',
                ))
            else:
                # Generate new summary if still has Latin
                if has_latin_chars(fixed_text):
                    new_summary = generate_verse_summary_ar(
                        segment['sura_no'],
                        segment['ayah_start'],
                        segment['ayah_end'],
                        segment['theme_id']
                    )
                    segment_fixes.append(FieldFix(
                        segment_id=segment['id'],
                        field_name='summary_ar',
                        old_value=summary_ar,
                        new_value=new_summary,
                        fix_type='regenerate',
                    ))

        # Check title_ar
        title_ar = segment.get('title_ar') or ''
        if has_latin_chars(title_ar):
            arabic_title = get_arabic_title(segment['theme_id'])
            new_title = f"مقطع في {arabic_title}"
            segment_fixes.append(FieldFix(
                segment_id=segment['id'],
                field_name='title_ar',
                old_value=title_ar,
                new_value=new_title,
                fix_type='regenerate',
            ))

        # Apply fixes
        if segment_fixes:
            report.segments_with_issues += 1

            for fix in segment_fixes:
                report.fixes.append(fix)
                report.fields_fixed += 1

                if verbose:
                    print(f"  {fix.segment_id}.{fix.field_name}: '{fix.old_value[:40]}...' -> '{fix.new_value}'")

            if not dry_run:
                try:
                    summary_fix = next((f for f in segment_fixes if f.field_name == 'summary_ar'), None)
                    title_fix = next((f for f in segment_fixes if f.field_name == 'title_ar'), None)

                    update_segment_arabic_fields(
                        session,
                        segment['id'],
                        summary_ar=summary_fix.new_value if summary_fix else None,
                        title_ar=title_fix.new_value if title_fix else None,
                    )
                except Exception as e:
                    report.errors.append(f"Error updating {segment['id']}: {e}")

    # Commit if not dry run
    if not dry_run:
        session.commit()

    return report


# =============================================================================
# OUTPUT
# =============================================================================

def print_report(report: FixReport):
    """Print human-readable report."""
    print("\n" + "=" * 60)
    print("ARABIC FIELD FIX REPORT")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Mode: {report.mode}")

    print("\n--- SUMMARY ---")
    print(f"Total segments checked: {report.total_segments_checked}")
    print(f"Segments with issues: {report.segments_with_issues}")
    print(f"Fields fixed: {report.fields_fixed}")

    if report.errors:
        print(f"\nErrors: {len(report.errors)}")
        for err in report.errors[:10]:
            print(f"  - {err}")

    if report.fixes:
        print("\n--- FIXES MADE ---")
        # Group by theme
        by_theme: Dict[str, List[FieldFix]] = {}
        for fix in report.fixes:
            theme = fix.segment_id.split(':')[0]
            if theme not in by_theme:
                by_theme[theme] = []
            by_theme[theme].append(fix)

        for theme_id, fixes in sorted(by_theme.items()):
            print(f"\n{theme_id}: {len(fixes)} fixes")
            for fix in fixes[:3]:
                old_short = fix.old_value[:30] + '...' if len(fix.old_value) > 30 else fix.old_value
                print(f"    {fix.fix_type}: '{old_short}' -> '{fix.new_value}'")
            if len(fixes) > 3:
                print(f"    ... and {len(fixes) - 3} more")

    print("\n" + "=" * 60)
    if report.errors:
        print("STATUS: FAILED")
    else:
        print("STATUS: SUCCESS")
    print("=" * 60)


def export_json(report: FixReport, filepath: str):
    """Export report as JSON."""
    from dataclasses import asdict

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)
    print(f"Report exported to: {filepath}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fix Arabic fields in theme segments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to database"
    )
    parser.add_argument(
        "--only",
        type=str,
        metavar="THEME_ID",
        help="Only process a specific theme"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="PATH",
        help="Export report as JSON"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 on errors"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        report = fix_arabic_fields(
            session=session,
            dry_run=args.dry_run,
            only_theme=args.only,
            verbose=args.verbose,
        )

    print_report(report)

    if args.json:
        export_json(report, args.json)

    # Exit code
    if args.ci and report.errors:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
