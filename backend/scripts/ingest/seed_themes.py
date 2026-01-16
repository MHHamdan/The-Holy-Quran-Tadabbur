#!/usr/bin/env python3
"""
Seed Quranic Themes from JSON data.

This script:
1. Loads theme definitions from app/data/themes/quranic_themes.json
2. Creates QuranicTheme entries (root themes and subthemes)
3. Creates ThemeSegment entries with evidence sources
4. Creates ThemeConsequence entries (rewards/punishments)
5. Creates ThemeConnection entries for sequential segments

EPISTEMIC RULES:
================
1. Every segment MUST have at least one evidence_source from approved tafsir
2. Approved sources: ibn_kathir_ar, tabari_ar, qurtubi_ar, nasafi_ar, shinqiti_ar
3. Themes are derived from explicit Quranic text with tafsir backing
4. All Arabic text is preserved in original form (Uthmani)

Usage:
    python scripts/ingest/seed_themes.py [--with-concepts] [--clear]
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select, text, delete
from sqlalchemy.orm import Session

from app.models.theme import (
    QuranicTheme, ThemeSegment, ThemeConnection, ThemeConsequence,
    ThemeCategory, ThemeEdgeType, ConsequenceType,
)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Approved tafsir sources (Sunni 4 Madhabs)
APPROVED_SOURCES = {
    "ibn_kathir_ar",
    "tabari_ar",
    "qurtubi_ar",
    "nasafi_ar",
    "shinqiti_ar",
}

# Path resolution for container vs host
if Path("/app/app/data/themes").exists():
    DATA_DIR = Path("/app/app/data/themes")
else:
    DATA_DIR = PROJECT_ROOT / "app" / "data" / "themes"


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def load_themes_data() -> dict:
    """Load themes from JSON file."""
    themes_path = DATA_DIR / "quranic_themes.json"
    print(f"Loading themes from: {themes_path}")

    if not themes_path.exists():
        raise FileNotFoundError(f"Themes file not found: {themes_path}")

    with open(themes_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_evidence_sources(sources: List[Dict]) -> List[str]:
    """
    Validate that evidence sources are from approved tafsir.
    Returns list of chunk_ids.
    """
    valid_chunks = []
    for source in sources:
        source_id = source.get("source_id", "")
        if source_id in APPROVED_SOURCES:
            chunk_id = source.get("chunk_id", "")
            if chunk_id:
                valid_chunks.append(chunk_id)
        else:
            print(f"    WARNING: Unapproved source '{source_id}' - skipping")
    return valid_chunks


def ensure_tables_exist(session: Session) -> bool:
    """Check if theme tables exist."""
    try:
        result = session.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'quranic_themes'"
        ))
        return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking table existence: {e}")
        return False


def clear_existing_data(session: Session):
    """Clear existing theme data (for re-seeding)."""
    print("\nClearing existing theme data...")

    # Delete in order due to foreign keys
    session.execute(delete(ThemeConnection))
    session.execute(delete(ThemeConsequence))
    session.execute(delete(ThemeSegment))
    session.execute(delete(QuranicTheme))
    session.commit()
    print("  Cleared all theme data")


def seed_themes(session: Session, data: dict) -> int:
    """Seed QuranicTheme entries from loaded data."""
    themes = data.get("themes", [])
    created_count = 0
    updated_count = 0

    print(f"\nProcessing {len(themes)} themes...")

    # First pass: create/update all themes (without parent references)
    for theme in themes:
        theme_id = theme.get("id")

        # Check if theme already exists
        existing = session.execute(
            select(QuranicTheme).where(QuranicTheme.id == theme_id)
        ).scalar_one_or_none()

        # Validate category
        category = theme.get("category", "aqidah")
        if category not in [c.value for c in ThemeCategory]:
            print(f"    WARNING: Invalid category '{category}' for {theme_id}")
            category = "aqidah"

        if existing:
            # Update existing theme
            existing.slug = theme.get("slug", theme_id)
            existing.title_ar = theme.get("title_ar")
            existing.title_en = theme.get("title_en")
            existing.short_title_ar = theme.get("short_title_ar")
            existing.short_title_en = theme.get("short_title_en")
            existing.category = category
            existing.order_of_importance = theme.get("order_of_importance", 0)
            existing.key_concepts = theme.get("key_concepts", [])
            existing.description_ar = theme.get("description_ar")
            existing.description_en = theme.get("description_en")
            existing.related_theme_ids = theme.get("related_theme_ids", [])
            existing.tafsir_sources = theme.get("tafsir_sources", [])
            existing.updated_at = datetime.utcnow()
            updated_count += 1
            print(f"  Updated: {theme_id} ({theme.get('title_en')})")
        else:
            # Create new theme
            new_theme = QuranicTheme(
                id=theme_id,
                slug=theme.get("slug", theme_id),
                title_ar=theme.get("title_ar"),
                title_en=theme.get("title_en"),
                short_title_ar=theme.get("short_title_ar"),
                short_title_en=theme.get("short_title_en"),
                category=category,
                order_of_importance=theme.get("order_of_importance", 0),
                key_concepts=theme.get("key_concepts", []),
                description_ar=theme.get("description_ar"),
                description_en=theme.get("description_en"),
                related_theme_ids=theme.get("related_theme_ids", []),
                tafsir_sources=theme.get("tafsir_sources", []),
                is_complete=False,
                segment_count=0,
                total_verses=0,
                created_at=datetime.utcnow(),
            )
            session.add(new_theme)
            created_count += 1
            print(f"  Created: {theme_id} ({theme.get('title_en')})")

    session.commit()

    # Second pass: set parent references
    print("\n  Setting parent theme references...")
    for theme in themes:
        theme_id = theme.get("id")
        parent_id = theme.get("parent_theme_id")

        if parent_id:
            # Verify parent exists
            parent_exists = session.execute(
                select(QuranicTheme).where(QuranicTheme.id == parent_id)
            ).scalar_one_or_none()

            if parent_exists:
                session.execute(
                    text("UPDATE quranic_themes SET parent_theme_id = :parent WHERE id = :id"),
                    {"parent": parent_id, "id": theme_id}
                )
                print(f"    {theme_id} -> parent: {parent_id}")
            else:
                print(f"    WARNING: Parent '{parent_id}' not found for {theme_id}")

    session.commit()
    print(f"\nThemes: {created_count} created, {updated_count} updated")
    return created_count + updated_count


def seed_segments(session: Session, data: dict) -> int:
    """Seed ThemeSegment entries from loaded data."""
    segments = data.get("segments", [])
    created_count = 0
    skipped_count = 0

    print(f"\nProcessing {len(segments)} segments...")

    for segment in segments:
        segment_id = segment.get("id")
        theme_id = segment.get("theme_id")

        # Verify theme exists
        theme_exists = session.execute(
            select(QuranicTheme).where(QuranicTheme.id == theme_id)
        ).scalar_one_or_none()

        if not theme_exists:
            print(f"  SKIP: Theme '{theme_id}' not found for segment {segment_id}")
            skipped_count += 1
            continue

        # Check if segment already exists
        existing = session.execute(
            select(ThemeSegment).where(ThemeSegment.id == segment_id)
        ).scalar_one_or_none()

        if existing:
            print(f"  EXISTS: {segment_id}")
            continue

        # Validate evidence sources (CRITICAL - must have at least one)
        evidence_sources = segment.get("evidence_sources", [])
        evidence_chunk_ids = validate_evidence_sources(evidence_sources)

        if not evidence_chunk_ids:
            print(f"  SKIP: No valid evidence for segment {segment_id}")
            skipped_count += 1
            continue

        # Create segment
        new_segment = ThemeSegment(
            id=segment_id,
            theme_id=theme_id,
            segment_order=segment.get("segment_order", 1),
            chronological_index=segment.get("chronological_index"),
            sura_no=segment.get("sura_no"),
            ayah_start=segment.get("ayah_start"),
            ayah_end=segment.get("ayah_end"),
            title_ar=segment.get("title_ar"),
            title_en=segment.get("title_en"),
            summary_ar=segment.get("summary_ar", ""),
            summary_en=segment.get("summary_en", ""),
            semantic_tags=segment.get("semantic_tags", []),
            revelation_context=segment.get("revelation_context"),
            is_entry_point=segment.get("is_entry_point", False),
            is_verified=True,  # Manually curated
            importance_weight=segment.get("importance_weight", 0.5),
            evidence_sources=evidence_sources,
            evidence_chunk_ids=evidence_chunk_ids,
            created_at=datetime.utcnow(),
        )
        session.add(new_segment)
        created_count += 1
        print(f"  Created: {segment_id}")

    session.commit()

    # Update theme metadata (segment counts, suras, etc.)
    update_theme_metadata(session)

    print(f"\nSegments: {created_count} created, {skipped_count} skipped")
    return created_count


def seed_consequences(session: Session, data: dict) -> int:
    """Seed ThemeConsequence entries from loaded data."""
    consequences = data.get("consequences", [])
    created_count = 0
    skipped_count = 0

    print(f"\nProcessing {len(consequences)} consequences...")

    for idx, consequence in enumerate(consequences):
        theme_id = consequence.get("theme_id")

        # Verify theme exists
        theme_exists = session.execute(
            select(QuranicTheme).where(QuranicTheme.id == theme_id)
        ).scalar_one_or_none()

        if not theme_exists:
            print(f"  SKIP: Theme '{theme_id}' not found")
            skipped_count += 1
            continue

        # Validate consequence type
        consequence_type = consequence.get("consequence_type", "reward")
        if consequence_type not in [c.value for c in ConsequenceType]:
            print(f"  WARNING: Invalid consequence type '{consequence_type}'")
            consequence_type = "reward"

        # Generate evidence chunk IDs from supporting verses
        supporting_verses = consequence.get("supporting_verses", [])
        evidence_chunk_ids = [
            f"consequence:{theme_id}:{v.get('sura')}:{v.get('ayah')}"
            for v in supporting_verses
        ]

        if not evidence_chunk_ids:
            print(f"  SKIP: No supporting verses for consequence")
            skipped_count += 1
            continue

        # Create consequence
        new_consequence = ThemeConsequence(
            theme_id=theme_id,
            consequence_type=consequence_type,
            description_ar=consequence.get("description_ar", ""),
            description_en=consequence.get("description_en", ""),
            supporting_verses=supporting_verses,
            evidence_chunk_ids=evidence_chunk_ids,
            display_order=consequence.get("display_order", idx),
            created_at=datetime.utcnow(),
        )
        session.add(new_consequence)
        created_count += 1
        print(f"  Created: {theme_id} - {consequence_type}")

    session.commit()
    print(f"\nConsequences: {created_count} created, {skipped_count} skipped")
    return created_count


def create_sequential_connections(session: Session) -> int:
    """Create ThemeConnection entries for sequential segments within themes."""
    print("\nCreating sequential connections...")

    created_count = 0

    # Get all themes with segments
    themes = session.execute(
        select(QuranicTheme).where(QuranicTheme.segment_count > 1)
    ).scalars().all()

    for theme in themes:
        # Get segments ordered by segment_order
        segments = session.execute(
            select(ThemeSegment)
            .where(ThemeSegment.theme_id == theme.id)
            .order_by(ThemeSegment.segment_order)
        ).scalars().all()

        # Create sequential connections
        for i in range(len(segments) - 1):
            source = segments[i]
            target = segments[i + 1]

            # Check if connection already exists
            existing = session.execute(
                select(ThemeConnection).where(
                    ThemeConnection.source_segment_id == source.id,
                    ThemeConnection.target_segment_id == target.id,
                    ThemeConnection.edge_type == ThemeEdgeType.PROGRESSION.value,
                )
            ).scalar_one_or_none()

            if existing:
                continue

            # Create connection
            connection = ThemeConnection(
                source_segment_id=source.id,
                target_segment_id=target.id,
                edge_type=ThemeEdgeType.PROGRESSION.value,
                is_sequential=True,
                strength=0.8,
                explanation_ar="تتابع في الموضوع",
                explanation_en="Sequential progression in theme",
                created_at=datetime.utcnow(),
            )
            session.add(connection)
            created_count += 1

    session.commit()
    print(f"  Created {created_count} sequential connections")
    return created_count


def update_theme_metadata(session: Session):
    """Update theme metadata (counts, suras mentioned, percentages)."""
    print("\nUpdating theme metadata...")

    themes = session.execute(select(QuranicTheme)).scalars().all()

    for theme in themes:
        # Get segments for this theme
        segments = session.execute(
            select(ThemeSegment).where(ThemeSegment.theme_id == theme.id)
        ).scalars().all()

        # Count segments
        theme.segment_count = len(segments)

        # Calculate total verses
        total_verses = sum(
            (s.ayah_end - s.ayah_start + 1) for s in segments
        )
        theme.total_verses = total_verses

        # Get unique suras
        suras = list(set(s.sura_no for s in segments))
        theme.suras_mentioned = sorted(suras)

        # Calculate Makki/Madani percentages
        makki_count = sum(1 for s in segments if s.revelation_context == "makki")
        madani_count = sum(1 for s in segments if s.revelation_context == "madani")

        if segments:
            theme.makki_percentage = (makki_count / len(segments)) * 100
            theme.madani_percentage = (madani_count / len(segments)) * 100

        theme.updated_at = datetime.utcnow()

    session.commit()
    print("  Theme metadata updated")


def print_summary(session: Session):
    """Print summary of theme data."""
    print("\n" + "=" * 60)
    print("QURANIC THEMES SUMMARY (المحاور القرآنية)")
    print("=" * 60)

    # Count by category
    result = session.execute(text("""
        SELECT category, COUNT(*) as cnt
        FROM quranic_themes
        GROUP BY category
        ORDER BY
            CASE category
                WHEN 'aqidah' THEN 1
                WHEN 'iman' THEN 2
                WHEN 'ibadat' THEN 3
                WHEN 'akhlaq_fardi' THEN 4
                WHEN 'akhlaq_ijtima' THEN 5
                WHEN 'muharramat' THEN 6
                WHEN 'sunan_ilahiyyah' THEN 7
            END
    """))

    category_names = {
        "aqidah": "التوحيد والعقيدة (Theology & Creed)",
        "iman": "الإيمان (Pillars of Faith)",
        "ibadat": "العبادات (Acts of Worship)",
        "akhlaq_fardi": "الأخلاق الفردية (Individual Ethics)",
        "akhlaq_ijtima": "الأخلاق الاجتماعية (Social Ethics)",
        "muharramat": "المحرمات والكبائر (Prohibitions)",
        "sunan_ilahiyyah": "السنن الإلهية (Divine Laws)",
    }

    total_themes = 0
    print("\nThemes by Category:")
    for row in result:
        category, count = row
        print(f"  {category_names.get(category, category)}: {count}")
        total_themes += count

    print(f"\n  Total themes: {total_themes}")

    # Count segments
    segment_result = session.execute(text("SELECT COUNT(*) FROM theme_segments"))
    segment_count = segment_result.scalar() or 0
    print(f"  Total segments: {segment_count}")

    # Count connections
    conn_result = session.execute(text("SELECT COUNT(*) FROM theme_connections"))
    conn_count = conn_result.scalar() or 0
    print(f"  Total connections: {conn_count}")

    # Count consequences
    cons_result = session.execute(text("SELECT COUNT(*) FROM theme_consequences"))
    cons_count = cons_result.scalar() or 0
    print(f"  Total consequences: {cons_count}")

    # Makki/Madani breakdown
    context_result = session.execute(text("""
        SELECT revelation_context, COUNT(*)
        FROM theme_segments
        WHERE revelation_context IS NOT NULL
        GROUP BY revelation_context
    """))
    print("\nRevelation Context:")
    for row in context_result:
        context, count = row
        label = "مكي (Makki)" if context == "makki" else "مدني (Madani)"
        print(f"  {label}: {count} segments")


def main():
    parser = argparse.ArgumentParser(
        description="Seed Quranic themes from JSON data"
    )
    parser.add_argument(
        "--with-concepts",
        action="store_true",
        help="Also create corresponding Concept entries for themes"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing theme data before seeding"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("QURANIC THEMES SEEDER (المحاور القرآنية)")
    print("=" * 60)
    print("Methodology: Sunni Orthodox - 4 Madhabs Only")
    print("=" * 60)

    # Load data
    try:
        data = load_themes_data()
        print(f"Loaded {len(data.get('themes', []))} themes")
        print(f"Loaded {len(data.get('segments', []))} segments")
        print(f"Loaded {len(data.get('consequences', []))} consequences")
        print(f"Version: {data.get('version', 'unknown')}")
        print(f"Approved sources: {', '.join(data.get('approved_tafsir_sources', []))}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n[DRY RUN] Would process:")
        print(f"  - {len(data.get('themes', []))} themes")
        print(f"  - {len(data.get('segments', []))} segments")
        print(f"  - {len(data.get('consequences', []))} consequences")
        print("\nCategories:")
        categories = {}
        for theme in data.get("themes", []):
            cat = theme.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        return

    # Connect to database
    db_url = get_db_url()
    print(f"\nConnecting to database...")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check if tables exist
        if not ensure_tables_exist(session):
            print("\nERROR: quranic_themes table does not exist!")
            print("Please run the migration first:")
            print("  alembic upgrade head")
            sys.exit(1)

        # Clear existing data if requested
        if args.clear:
            clear_existing_data(session)

        # Seed in order
        seed_themes(session, data)
        seed_segments(session, data)
        seed_consequences(session, data)
        create_sequential_connections(session)

        # Optionally create concepts
        if args.with_concepts:
            print("\n--with-concepts not yet implemented")
            # TODO: Create Concept entries for themes

        # Print summary
        print_summary(session)

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
