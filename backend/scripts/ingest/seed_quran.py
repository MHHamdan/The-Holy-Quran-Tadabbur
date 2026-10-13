#!/usr/bin/env python3
"""
Seed Quran verses from manifest sources.

This script:
1. Reads the quran_hafs.json manifest
2. Loads Quran data from the specified source
3. Parses and validates the data
4. Inserts verses into the database
5. Sets hizb/rub' and sajdah markers from quran_structure_markers.json

Usage:
    python backend/scripts/ingest/seed_quran.py                  # everything
    python backend/scripts/ingest/seed_quran.py --markers-only   # step 5 on an existing database
"""
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models.quran import QuranVerse
from app.models.audit import AuditLog

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"


def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"
    )


def load_manifest() -> dict:
    """Load quran manifest."""
    manifest_path = MANIFESTS_DIR / "quran_hafs.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_source_file(manifest: dict) -> Path:
    """Find the primary source file."""
    for source in manifest.get("sources", []):
        if source.get("is_primary") and "path" in source:
            path = (MANIFESTS_DIR / source["path"]).resolve()
            if path.exists():
                return path

    raise FileNotFoundError("No primary source file found")


def load_quran_data(source_path: Path, manifest: dict) -> list:
    """Load and parse Quran data from source file."""
    print(f"  Loading from: {source_path}")

    with open(source_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Get field mapping from manifest
    mapping = manifest.get("parser", {}).get("field_mapping", {})

    verses = []
    for item in raw_data:
        verse = {
            "id": item.get(mapping.get("id", "id")),
            "sura_no": item.get(mapping.get("sura_no", "sura_no")),
            "sura_name_ar": item.get(mapping.get("sura_name_ar", "sura_name_ar")),
            "sura_name_en": item.get(mapping.get("sura_name_en", "sura_name_en")),
            "aya_no": item.get(mapping.get("aya_no", "aya_no")),
            "text_uthmani": item.get(mapping.get("text_uthmani", "aya_text")),
            "text_imlaei": item.get(mapping.get("text_imlaei", "aya_text_emlaey")),
            "page_no": item.get(mapping.get("page_no", "page")),
            "juz_no": item.get(mapping.get("juz_no", "jozz")),
            "line_start": item.get(mapping.get("line_start", "line_start")),
            "line_end": item.get(mapping.get("line_end", "line_end")),
        }

        # Validate required fields
        if verse["sura_no"] and verse["aya_no"] and verse["text_uthmani"]:
            verses.append(verse)

    return verses


def seed_verses(session: Session, verses: list) -> int:
    """Insert verses into database."""
    count = 0
    batch_size = 500

    for i in range(0, len(verses), batch_size):
        batch = verses[i:i + batch_size]

        for verse_data in batch:
            verse = QuranVerse(
                id=verse_data["id"],
                sura_no=verse_data["sura_no"],
                sura_name_ar=verse_data["sura_name_ar"],
                sura_name_en=verse_data["sura_name_en"],
                aya_no=verse_data["aya_no"],
                text_uthmani=verse_data["text_uthmani"],
                text_imlaei=verse_data["text_imlaei"] or verse_data["text_uthmani"],
                page_no=verse_data["page_no"],
                juz_no=verse_data["juz_no"],
                line_start=verse_data.get("line_start"),
                line_end=verse_data.get("line_end"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.merge(verse)  # Use merge to handle re-runs
            count += 1

        session.commit()
        print(f"  Inserted {min(i + batch_size, len(verses))}/{len(verses)} verses")

    return count


def normalize_for_search(t: str) -> str:
    """Search key: no tatweel/diacritics, unified alef, ta marbuta -> ha, alef maqsura -> ya."""
    t = t.replace("\ufeff", "").replace("\u0640", "")
    t = re.sub(r"[\u064b-\u065f\u0670]", "", t)
    t = re.sub(r"[\u0622\u0623\u0625\u0671]", "\u0627", t)
    return t.replace("\u0629", "\u0647").replace("\u0649", "\u064a").strip()


def populate_text_normalized(session: Session) -> int:
    """Fill quran_verses.text_normalized (used by text search) for every verse."""
    rows = session.execute(text("SELECT id, text_uthmani FROM quran_verses")).all()
    session.execute(
        text("UPDATE quran_verses SET text_normalized = :n WHERE id = :i"),
        [{"i": i, "n": normalize_for_search(t or "")} for i, t in rows],
    )
    session.commit()
    return len(rows)


def populate_structure_markers(session: Session) -> tuple[int, int]:
    """
    Set rub_no (1-240), hizb_no (1-60) and sajda_type on every verse.

    Quarters are contiguous: each verse belongs to the last quarter that
    started at or before it. Returns (verses updated, sajdah verses).
    """
    markers = json.loads((MANIFESTS_DIR / "quran_structure_markers.json").read_text(encoding="utf-8"))
    starts = {tuple(q): i + 1 for i, q in enumerate(markers["hizb_quarters"])}
    sajdahs = {(s["sura"], s["aya"]): s["type"] for s in markers["sajdahs"]}

    rows = session.execute(text("SELECT id, sura_no, aya_no FROM quran_verses ORDER BY id")).all()
    if (rows[0].sura_no, rows[0].aya_no) not in starts:
        raise ValueError("first verse is not the start of a hizb quarter")
    updates, rub = [], 0
    for row in rows:
        rub = starts.get((row.sura_no, row.aya_no), rub)
        updates.append({
            "i": row.id,
            "rub": rub,
            "hizb": (rub - 1) // 4 + 1,
            "sajda": sajdahs.get((row.sura_no, row.aya_no)),
        })
    if rub != 240:
        raise ValueError(f"expected 240 hizb quarters, reached {rub}")
    session.execute(
        text("UPDATE quran_verses SET rub_no = :rub, hizb_no = :hizb, sajda_type = :sajda WHERE id = :i"),
        updates,
    )
    session.commit()
    return len(updates), sum(1 for u in updates if u["sajda"])


def main():
    """Main entry point."""
    if "--markers-only" in sys.argv:
        with Session(create_engine(get_db_url())) as session:
            count, sajdahs = populate_structure_markers(session)
        print(f"Structure markers set on {count} verses ({sajdahs} sajdah verses)")
        sys.exit(0)

    print("=" * 60)
    print("QURAN SEEDING")
    print("=" * 60)

    start_time = datetime.now()

    try:
        # Load manifest
        print("\n[1/4] Loading manifest...")
        manifest = load_manifest()
        print(f"  Manifest: {manifest['name']}")

        # Find source file
        print("\n[2/4] Finding source file...")
        source_path = find_source_file(manifest)
        print(f"  Found: {source_path}")

        # Load data
        print("\n[3/4] Loading Quran data...")
        verses = load_quran_data(source_path, manifest)
        print(f"  Loaded {len(verses)} verses")

        # Validate count
        expected = manifest.get("expected_structure", {}).get("total_verses", 6236)
        if len(verses) != expected:
            print(f"  WARNING: Expected {expected} verses, got {len(verses)}")

        # Seed database
        print("\n[4/4] Seeding database...")
        engine = create_engine(get_db_url())

        with Session(engine) as session:
            count = seed_verses(session, verses)

            # Log the action
            AuditLog.log(
                session,
                action="data_import",
                actor="pipeline",
                entity_type="quran_verse",
                message=f"Seeded {count} Quran verses",
                details={"source": str(source_path), "count": count},
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )
            session.commit()

            normalized = populate_text_normalized(session)
            print(f"  Normalized {normalized} verses for text search")

            marked, sajdahs = populate_structure_markers(session)
            print(f"  Hizb/rub' and sajdah markers on {marked} verses ({sajdahs} sajdah)")

        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  Verses seeded: {count}")
        print(f"  Duration: {duration:.2f}s")
        print("\nSUCCESS: Quran seeding complete")
        print("=" * 60)
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nREMEDIATION:")
        print("  1. Check manifest points to valid source file")
        print("  2. Ensure hafs_smart_v8.json exists in assets/")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
