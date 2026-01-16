#!/usr/bin/env python3
"""
Seed Rhetorical Device Types from JSON dictionary.

This script:
1. Loads rhetorical device definitions from app/data/rhetoric/rhetorical_devices.json
2. Creates RhetoricalDeviceType entries in the database
3. Optionally creates corresponding Concept entries (type="rhetorical")
4. Does NOT create occurrences - those come from tafsir extraction

EPISTEMIC RULES:
================
1. NO occurrence creation without tafsir evidence
2. Device types are canonical - from classical balagha taxonomy
3. Each device must be in one of the three categories:
   - bayaan (علم البيان)
   - maani (علم المعاني)
   - badeea (علم البديع)

Usage:
    python scripts/ingest/seed_rhetorical_devices.py [--with-concepts]
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.models.rhetoric import RhetoricalDeviceType
from app.models.concept import Concept

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Path resolution for container vs host
if Path("/app/app/data/rhetoric").exists():
    DATA_DIR = Path("/app/app/data/rhetoric")
else:
    DATA_DIR = PROJECT_ROOT / "app" / "data" / "rhetoric"


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def load_rhetorical_devices() -> dict:
    """Load rhetorical devices from JSON file."""
    devices_path = DATA_DIR / "rhetorical_devices.json"
    print(f"Loading devices from: {devices_path}")

    if not devices_path.exists():
        raise FileNotFoundError(f"Devices file not found: {devices_path}")

    with open(devices_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_table_exists(session: Session) -> bool:
    """Check if the rhetorical_device_types table exists."""
    try:
        result = session.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'rhetorical_device_types'"
        ))
        return result.fetchone() is not None
    except Exception as e:
        print(f"Error checking table existence: {e}")
        return False


def seed_device_types(session: Session, data: dict) -> int:
    """Seed rhetorical device types from loaded data."""
    devices = data.get("devices", [])
    created_count = 0
    updated_count = 0

    print(f"\nProcessing {len(devices)} rhetorical devices...")

    for device in devices:
        device_id = device.get("id")

        # Check if device already exists
        existing = session.execute(
            select(RhetoricalDeviceType).where(RhetoricalDeviceType.id == device_id)
        ).scalar_one_or_none()

        if existing:
            # Update existing device
            existing.slug = device.get("slug", device_id)
            existing.name_ar = device.get("name_ar")
            existing.name_en = device.get("name_en")
            existing.category = device.get("category")
            existing.definition_ar = device.get("definition_ar")
            existing.definition_en = device.get("definition_en")
            existing.examples_json = device.get("examples")
            existing.sub_types_json = device.get("sub_types")
            existing.display_order = device.get("display_order", 0)
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            updated_count += 1
            print(f"  Updated: {device_id} ({device.get('name_en')})")
        else:
            # Create new device
            new_device = RhetoricalDeviceType(
                id=device_id,
                slug=device.get("slug", device_id),
                name_ar=device.get("name_ar"),
                name_en=device.get("name_en"),
                category=device.get("category"),
                definition_ar=device.get("definition_ar"),
                definition_en=device.get("definition_en"),
                examples_json=device.get("examples"),
                sub_types_json=device.get("sub_types"),
                display_order=device.get("display_order", 0),
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(new_device)
            created_count += 1
            print(f"  Created: {device_id} ({device.get('name_en')})")

    session.commit()
    print(f"\nDevice types: {created_count} created, {updated_count} updated")
    return created_count + updated_count


def seed_concepts(session: Session, data: dict) -> int:
    """Create corresponding Concept entries for rhetorical devices."""
    devices = data.get("devices", [])
    created_count = 0

    print(f"\nCreating Concept entries for rhetorical devices...")

    for device in devices:
        device_id = device.get("id")
        concept_id = f"rhetorical_{device_id}"

        # Check if concept already exists
        existing = session.execute(
            select(Concept).where(Concept.id == concept_id)
        ).scalar_one_or_none()

        if existing:
            print(f"  Concept exists: {concept_id}")
            continue

        # Create new concept
        new_concept = Concept(
            id=concept_id,
            slug=f"rhetorical-{device.get('slug', device_id)}",
            concept_type="rhetorical",
            label_ar=device.get("name_ar"),
            label_en=device.get("name_en"),
            description_ar=device.get("definition_ar"),
            description_en=device.get("definition_en"),
            is_curated=True,
            source="balagha_taxonomy",
            icon_hint="rhetoric",
            display_order=device.get("display_order", 0),
            created_at=datetime.utcnow(),
        )
        session.add(new_concept)
        created_count += 1
        print(f"  Created concept: {concept_id}")

    session.commit()
    print(f"\nConcepts: {created_count} created")
    return created_count


def print_summary(session: Session):
    """Print summary of rhetorical device data."""
    # Count by category
    result = session.execute(text("""
        SELECT category, COUNT(*)
        FROM rhetorical_device_types
        WHERE is_active = true
        GROUP BY category
        ORDER BY category
    """))

    print("\n" + "=" * 50)
    print("RHETORICAL DEVICES SUMMARY")
    print("=" * 50)

    total = 0
    for row in result:
        category, count = row
        category_names = {
            "bayaan": "علم البيان (Figures of Speech)",
            "maani": "علم المعاني (Semantics)",
            "badeea": "علم البديع (Embellishment)",
        }
        print(f"  {category_names.get(category, category)}: {count}")
        total += count

    print(f"\n  Total active devices: {total}")

    # Count occurrences (will be 0 initially)
    occ_result = session.execute(text(
        "SELECT COUNT(*) FROM rhetorical_occurrences"
    ))
    occ_count = occ_result.scalar() or 0
    print(f"  Total occurrences: {occ_count}")

    if occ_count == 0:
        print("\n  Note: Run tafsir extraction script to populate occurrences")


def main():
    parser = argparse.ArgumentParser(
        description="Seed rhetorical device types from JSON dictionary"
    )
    parser.add_argument(
        "--with-concepts",
        action="store_true",
        help="Also create corresponding Concept entries"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RHETORICAL DEVICE SEEDER")
    print("=" * 60)

    # Load data
    try:
        data = load_rhetorical_devices()
        print(f"Loaded {len(data.get('devices', []))} devices from JSON")
        print(f"Schema version: {data.get('schema_version', 'unknown')}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n[DRY RUN] Would create/update the following devices:")
        for device in data.get("devices", []):
            print(f"  - {device.get('id')}: {device.get('name_en')} ({device.get('category')})")
        print(f"\nTotal: {len(data.get('devices', []))} devices")
        return

    # Connect to database
    db_url = get_db_url()
    print(f"\nConnecting to database...")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check if table exists
        if not ensure_table_exists(session):
            print("\nERROR: rhetorical_device_types table does not exist!")
            print("Please run the migration first:")
            print("  alembic upgrade head")
            sys.exit(1)

        # Seed device types
        seed_device_types(session, data)

        # Optionally seed concepts
        if args.with_concepts:
            # Check if concepts table exists
            concepts_exist = session.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'concepts'"
            )).fetchone()

            if concepts_exist:
                seed_concepts(session, data)
            else:
                print("\nWARNING: concepts table does not exist, skipping concept creation")

        # Print summary
        print_summary(session)

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
