#!/usr/bin/env python3
"""
Fix Theme Graph Script

Fixes graph connectivity issues by:
1. Adding related_theme_ids to isolated themes
2. Creating theme_connections for cross-theme relationships
3. Ensuring no orphan nodes in the theme graph

Usage:
    python scripts/ingest/fix_theme_graph.py
    python scripts/ingest/fix_theme_graph.py --dry-run

Author: Claude Code (Tadabbur-AI)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


# =============================================================================
# CONSTANTS - Semantic Theme Relationships
# =============================================================================

# Predefined meaningful theme relationships (bidirectional)
THEME_RELATIONSHIPS = {
    # Hajj connects to multiple themes
    'theme_hajj': [
        ('theme_taqwa', 'related', 'الحج يُعزز التقوى', 'Hajj reinforces Taqwa'),
        ('theme_tawheed', 'prerequisite', 'التوحيد أساس الحج', 'Tawheed is the foundation of Hajj'),
        ('theme_infaq', 'related', 'الإنفاق جزء من الحج', 'Spending is part of Hajj'),
        ('theme_sabr', 'related', 'الحج يتطلب الصبر', 'Hajj requires patience'),
        ('theme_dhikr', 'related', 'الحج مليء بالذكر', 'Hajj is full of Dhikr'),
    ],

    # Tawheed (core concept) connects to many
    'theme_tawheed': [
        ('theme_shirk', 'opposite', 'التوحيد ضد الشرك', 'Tawheed is opposite of Shirk'),
        ('theme_tawheed_rububiyyah', 'parent', 'الربوبية فرع من التوحيد', 'Rububiyyah is branch of Tawheed'),
        ('theme_tawheed_uluhiyyah', 'parent', 'الألوهية فرع من التوحيد', 'Uluhiyyah is branch of Tawheed'),
        ('theme_asma_sifat', 'parent', 'الأسماء والصفات فرع من التوحيد', 'Names/Attributes is branch of Tawheed'),
        ('theme_ikhlas', 'related', 'الإخلاص من ثمار التوحيد', 'Ikhlas is fruit of Tawheed'),
    ],

    # Salah connects to worship themes
    'theme_salah': [
        ('theme_khushu', 'related', 'الخشوع روح الصلاة', 'Khushu is soul of Salah'),
        ('theme_dhikr', 'related', 'الصلاة أعظم الذكر', 'Salah is greatest Dhikr'),
        ('theme_taqwa', 'related', 'الصلاة تنهى عن الفحشاء', 'Salah forbids immorality'),
        ('theme_dua', 'related', 'الصلاة تتضمن الدعاء', 'Salah includes Du\'a'),
    ],

    # Akhlaq (ethics) connections
    'theme_birr_walidayn': [
        ('theme_uquq_walidayn', 'opposite', 'البر ضد العقوق', 'Birr is opposite of Uquq'),
        ('theme_silat_rahim', 'related', 'البر أساس صلة الرحم', 'Birr is basis of family ties'),
        ('theme_ihsan', 'related', 'البر من الإحسان', 'Birr is part of Ihsan'),
    ],

    # Consequence themes
    'theme_jannah': [
        ('theme_nar', 'opposite', 'الجنة مقابل النار', 'Jannah vs Nar'),
        ('theme_taqwa', 'consequence', 'الجنة جزاء التقوى', 'Jannah is reward of Taqwa'),
        ('theme_iman_yawm_akhir', 'related', 'الجنة من الإيمان باليوم الآخر', 'Jannah is part of belief in Last Day'),
    ],

    'theme_nar': [
        ('theme_jannah', 'opposite', 'النار مقابل الجنة', 'Nar vs Jannah'),
        ('theme_shirk', 'consequence', 'النار جزاء الشرك', 'Nar is punishment for Shirk'),
        ('theme_iman_yawm_akhir', 'related', 'النار من الإيمان باليوم الآخر', 'Nar is part of belief in Last Day'),
    ],

    # Faith pillars connections
    'theme_iman_billah': [
        ('theme_iman_malaika', 'related', 'أركان الإيمان مترابطة', 'Pillars of faith are connected'),
        ('theme_iman_kutub', 'related', 'أركان الإيمان مترابطة', 'Pillars of faith are connected'),
        ('theme_iman_rusul', 'related', 'أركان الإيمان مترابطة', 'Pillars of faith are connected'),
        ('theme_iman_yawm_akhir', 'related', 'أركان الإيمان مترابطة', 'Pillars of faith are connected'),
        ('theme_iman_qadr', 'related', 'أركان الإيمان مترابطة', 'Pillars of faith are connected'),
    ],

    # Divine laws (sunan) connections
    'theme_sunnah_ibtila': [
        ('theme_sabr', 'related', 'الابتلاء يتطلب الصبر', 'Testing requires patience'),
        ('theme_tawakkul', 'related', 'الابتلاء يتطلب التوكل', 'Testing requires reliance on Allah'),
    ],

    'theme_sunnah_taghyir': [
        ('theme_tawbah', 'related', 'التغيير يبدأ بالتوبة', 'Change starts with repentance'),
        ('theme_islah', 'related', 'التغيير يتطلب الإصلاح', 'Change requires reform'),
    ],

    # Prohibitions connections
    'theme_riba': [
        ('theme_infaq', 'opposite', 'الربا ضد الإنفاق', 'Riba is opposite of spending'),
        ('theme_zakah', 'opposite', 'الربا ضد الزكاة', 'Riba is opposite of Zakah'),
    ],

    'theme_kidhb': [
        ('theme_sidq', 'opposite', 'الكذب ضد الصدق', 'Lying is opposite of truthfulness'),
        ('theme_nifaq', 'related', 'الكذب من صفات المنافقين', 'Lying is trait of hypocrites'),
    ],

    'theme_kibr': [
        ('theme_tawadu', 'opposite', 'الكبر ضد التواضع', 'Arrogance is opposite of humility'),
    ],
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GraphFix:
    """A single graph fix."""
    theme_id: str
    fix_type: str  # 'add_related', 'add_connection'
    target_theme: str
    relation_type: str
    explanation_ar: str


@dataclass
class FixReport:
    """Report of graph fixes."""
    timestamp: str
    mode: str
    isolated_themes_before: List[str] = field(default_factory=list)
    isolated_themes_after: List[str] = field(default_factory=list)
    related_ids_added: int = 0
    connections_added: int = 0
    fixes: List[GraphFix] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


# =============================================================================
# DATABASE QUERIES
# =============================================================================

def fetch_all_themes(session: Session) -> List[Dict]:
    """Fetch all themes with their related_theme_ids."""
    result = session.execute(text("""
        SELECT id, title_ar, related_theme_ids, parent_theme_id
        FROM quranic_themes
        ORDER BY id
    """))

    themes = []
    for row in result:
        themes.append({
            'id': row[0],
            'title_ar': row[1],
            'related_theme_ids': row[2] or [],
            'parent_theme_id': row[3],
        })
    return themes


def find_isolated_themes(themes: List[Dict]) -> List[str]:
    """Find themes with no connections."""
    isolated = []

    for theme in themes:
        has_related = len(theme['related_theme_ids']) > 0
        has_parent = theme['parent_theme_id'] is not None

        # Check if any other theme references this one
        is_referenced = any(
            theme['id'] in t['related_theme_ids'] or t['parent_theme_id'] == theme['id']
            for t in themes if t['id'] != theme['id']
        )

        if not has_related and not has_parent and not is_referenced:
            isolated.append(theme['id'])

    return isolated


def update_theme_related_ids(session: Session, theme_id: str, related_ids: List[str]):
    """Update related_theme_ids for a theme."""
    session.execute(text("""
        UPDATE quranic_themes
        SET related_theme_ids = :related_ids,
            updated_at = NOW()
        WHERE id = :theme_id
    """), {
        'theme_id': theme_id,
        'related_ids': related_ids,
    })


def get_current_related_ids(session: Session, theme_id: str) -> List[str]:
    """Get current related_theme_ids for a theme."""
    result = session.execute(text("""
        SELECT related_theme_ids FROM quranic_themes WHERE id = :theme_id
    """), {'theme_id': theme_id})
    row = result.fetchone()
    return row[0] if row and row[0] else []


# =============================================================================
# MAIN FIX FUNCTION
# =============================================================================

def fix_theme_graph(
    session: Session,
    dry_run: bool = False,
    verbose: bool = False
) -> FixReport:
    """
    Fix theme graph connectivity.

    Args:
        session: Database session
        dry_run: If True, don't write changes
        verbose: Print detailed output

    Returns:
        FixReport with results
    """
    report = FixReport(
        timestamp=datetime.utcnow().isoformat(),
        mode="dry-run" if dry_run else "live",
    )

    # Fetch current state
    themes = fetch_all_themes(session)
    theme_ids = {t['id'] for t in themes}

    report.isolated_themes_before = find_isolated_themes(themes)
    print(f"Found {len(report.isolated_themes_before)} isolated themes before fix")

    if verbose and report.isolated_themes_before:
        for tid in report.isolated_themes_before:
            print(f"  - {tid}")

    # Apply predefined relationships
    for theme_id, relationships in THEME_RELATIONSHIPS.items():
        if theme_id not in theme_ids:
            continue

        # Get current related IDs
        current_related = get_current_related_ids(session, theme_id)
        new_related = set(current_related)

        for target_id, relation_type, explanation_ar, explanation_en in relationships:
            if target_id not in theme_ids:
                continue

            # Add bidirectional relationship
            if target_id not in new_related:
                new_related.add(target_id)
                report.fixes.append(GraphFix(
                    theme_id=theme_id,
                    fix_type='add_related',
                    target_theme=target_id,
                    relation_type=relation_type,
                    explanation_ar=explanation_ar,
                ))
                report.related_ids_added += 1

                if verbose:
                    print(f"  {theme_id} -> {target_id} ({relation_type})")

        # Update if changed
        if new_related != set(current_related):
            if not dry_run:
                try:
                    update_theme_related_ids(session, theme_id, list(new_related))
                except Exception as e:
                    report.errors.append(f"Error updating {theme_id}: {e}")

    # Also add reverse relationships
    for theme_id, relationships in THEME_RELATIONSHIPS.items():
        for target_id, relation_type, explanation_ar, explanation_en in relationships:
            if target_id not in theme_ids or theme_id not in theme_ids:
                continue

            # Get target's current related IDs
            target_related = get_current_related_ids(session, target_id)
            if theme_id not in target_related:
                new_target_related = list(target_related) + [theme_id]
                if not dry_run:
                    try:
                        update_theme_related_ids(session, target_id, new_target_related)
                        report.related_ids_added += 1
                    except Exception as e:
                        report.errors.append(f"Error updating reverse for {target_id}: {e}")

    # Commit if not dry run
    if not dry_run:
        session.commit()

    # Re-check isolated themes
    themes_after = fetch_all_themes(session)
    report.isolated_themes_after = find_isolated_themes(themes_after)

    return report


# =============================================================================
# OUTPUT
# =============================================================================

def print_report(report: FixReport):
    """Print human-readable report."""
    print("\n" + "=" * 60)
    print("THEME GRAPH FIX REPORT")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Mode: {report.mode}")

    print("\n--- SUMMARY ---")
    print(f"Isolated themes before: {len(report.isolated_themes_before)}")
    print(f"Isolated themes after: {len(report.isolated_themes_after)}")
    print(f"Related IDs added: {report.related_ids_added}")

    if report.isolated_themes_before:
        print("\nPreviously isolated:")
        for tid in report.isolated_themes_before:
            status = "✓ fixed" if tid not in report.isolated_themes_after else "✗ still isolated"
            print(f"  - {tid}: {status}")

    if report.isolated_themes_after:
        print("\nStill isolated (need manual fix):")
        for tid in report.isolated_themes_after:
            print(f"  - {tid}")

    if report.errors:
        print(f"\nErrors: {len(report.errors)}")
        for err in report.errors[:10]:
            print(f"  - {err}")

    print("\n" + "=" * 60)
    if report.isolated_themes_after:
        print("STATUS: PARTIAL SUCCESS (some themes still isolated)")
    elif report.errors:
        print("STATUS: FAILED")
    else:
        print("STATUS: SUCCESS")
    print("=" * 60)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fix theme graph connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to database"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 if isolated themes remain"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        report = fix_theme_graph(
            session=session,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

    print_report(report)

    # Exit code
    if args.ci and (report.isolated_themes_after or report.errors):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
