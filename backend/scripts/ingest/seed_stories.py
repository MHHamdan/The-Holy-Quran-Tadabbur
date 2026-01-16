#!/usr/bin/env python3
"""
Seed Quranic stories from manifest with comprehensive validation.

This script:
1. Reads the stories.json manifest
2. VALIDATES data before seeding:
   - Every aya range resolves to existing verse_ids
   - Arabic/English summary parity
   - Theme bilingual mapping exists
   - Required fields are present
3. Creates stories, segments, themes, and connections
4. Links segments to verse ranges

IMPORTANT: All story data must be Quran-grounded - no invented facts.
Every segment must trace to actual ayat ranges.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.models.story import Story, StorySegment, Theme, StoryConnection, CrossStoryConnection
from app.models.quran import QuranVerse
from app.models.audit import AuditLog

SCRIPT_DIR = Path(__file__).parent
# In container: /app/scripts/ingest/ -> /app
# On host: .../backend/scripts/ingest/ -> .../backend/../ (project root)
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
# Also check if running inside container at /app
if Path("/app/data/manifests").exists():
    MANIFESTS_DIR = Path("/app/data/manifests")
else:
    MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"

# =============================================================================
# VALIDATION
# =============================================================================

class ValidationError:
    """Represents a validation issue."""
    def __init__(self, level: str, entity: str, message: str):
        self.level = level  # "error" or "warning"
        self.entity = entity
        self.message = message

    def __str__(self):
        return f"[{self.level.upper()}] {self.entity}: {self.message}"


class StoryValidator:
    """Validates story manifest data before seeding."""

    def __init__(self, session: Session):
        self.session = session
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self._verse_cache: Dict[Tuple[int, int, int], bool] = {}

    def validate_manifest(self, manifest: dict) -> bool:
        """
        Validate entire manifest. Returns True if no errors (warnings allowed).
        """
        print("  Validating manifest structure...")

        # Validate themes
        for theme in manifest.get("themes", []):
            self._validate_theme(theme)

        # Validate stories
        for story in manifest.get("stories", []):
            self._validate_story(story)

        # Print results
        if self.warnings:
            print(f"\n  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings[:10]:  # Show first 10
                print(f"    {w}")
            if len(self.warnings) > 10:
                print(f"    ... and {len(self.warnings) - 10} more warnings")

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for e in self.errors[:10]:
                print(f"    {e}")
            if len(self.errors) > 10:
                print(f"    ... and {len(self.errors) - 10} more errors")
            return False

        return True

    def _validate_theme(self, theme: dict):
        """Validate a theme has bilingual mapping."""
        theme_id = theme.get("id", "unknown")

        # Check required fields
        if not theme.get("name_ar"):
            self.warnings.append(ValidationError(
                "warning", f"theme:{theme_id}",
                "Missing Arabic name (name_ar)"
            ))
        if not theme.get("name_en"):
            self.warnings.append(ValidationError(
                "warning", f"theme:{theme_id}",
                "Missing English name (name_en)"
            ))

    def _validate_story(self, story: dict):
        """Validate a story and its segments."""
        story_id = story.get("id", "unknown")

        # Required fields
        required = ["id", "name_ar", "name_en", "category"]
        for field in required:
            if not story.get(field):
                self.errors.append(ValidationError(
                    "error", f"story:{story_id}",
                    f"Missing required field: {field}"
                ))

        # Bilingual summary parity
        has_ar = bool(story.get("summary_ar"))
        has_en = bool(story.get("summary_en"))
        if has_en and not has_ar:
            self.warnings.append(ValidationError(
                "warning", f"story:{story_id}",
                "Has English summary but missing Arabic summary"
            ))

        # Validate segments
        segments = story.get("segments", [])
        if not segments:
            self.warnings.append(ValidationError(
                "warning", f"story:{story_id}",
                "No segments defined"
            ))

        for segment in segments:
            self._validate_segment(story_id, segment)

    def _validate_segment(self, story_id: str, segment: dict):
        """Validate a segment's verse range and content."""
        segment_id = segment.get("id", "unknown")

        # Required fields
        required = ["id", "sura_no", "aya_start", "aya_end", "narrative_order"]
        for field in required:
            if segment.get(field) is None:
                self.errors.append(ValidationError(
                    "error", f"segment:{segment_id}",
                    f"Missing required field: {field}"
                ))
                return  # Can't validate further without these

        # Validate verse range exists
        sura_no = segment["sura_no"]
        aya_start = segment["aya_start"]
        aya_end = segment["aya_end"]

        if not self._verse_range_exists(sura_no, aya_start, aya_end):
            self.errors.append(ValidationError(
                "error", f"segment:{segment_id}",
                f"Verse range {sura_no}:{aya_start}-{aya_end} does not exist in database"
            ))

        # Bilingual summary parity
        has_ar = bool(segment.get("summary_ar"))
        has_en = bool(segment.get("summary_en"))
        if has_en and not has_ar:
            self.warnings.append(ValidationError(
                "warning", f"segment:{segment_id}",
                "Has English summary but missing Arabic summary"
            ))

        # Validate narrative_order is positive
        if segment.get("narrative_order", 0) <= 0:
            self.errors.append(ValidationError(
                "error", f"segment:{segment_id}",
                f"narrative_order must be positive, got {segment.get('narrative_order')}"
            ))

    def _verse_range_exists(self, sura_no: int, aya_start: int, aya_end: int) -> bool:
        """Check if a verse range exists in the database."""
        cache_key = (sura_no, aya_start, aya_end)
        if cache_key in self._verse_cache:
            return self._verse_cache[cache_key]

        result = self.session.execute(
            select(func.count(QuranVerse.id)).where(
                QuranVerse.sura_no == sura_no,
                QuranVerse.aya_no >= aya_start,
                QuranVerse.aya_no <= aya_end,
            )
        ).scalar()

        expected_count = aya_end - aya_start + 1
        exists = result == expected_count

        self._verse_cache[cache_key] = exists
        return exists


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def load_manifest() -> dict:
    manifest_path = MANIFESTS_DIR / "stories.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_verse_ids_for_range(session: Session, sura_no: int, aya_start: int, aya_end: int) -> list:
    """Get verse IDs for a sura/aya range."""
    result = session.execute(
        select(QuranVerse.id).where(
            QuranVerse.sura_no == sura_no,
            QuranVerse.aya_no >= aya_start,
            QuranVerse.aya_no <= aya_end,
        ).order_by(QuranVerse.aya_no)
    )
    return [row[0] for row in result.all()]


def seed_themes(session: Session, themes: list) -> int:
    """Seed themes."""
    count = 0
    for theme_data in themes:
        theme = Theme(
            id=theme_data["id"],
            name_ar=theme_data["name_ar"],
            name_en=theme_data["name_en"],
            description_ar=theme_data.get("description_ar"),
            description_en=theme_data.get("description_en"),
            created_at=datetime.utcnow(),
        )
        session.merge(theme)
        count += 1
    session.commit()
    return count


def seed_stories(session: Session, stories: list) -> tuple[int, int]:
    """Seed stories and segments."""
    story_count = 0
    segment_count = 0

    for story_data in stories:
        # Create story
        story = Story(
            id=story_data["id"],
            name_ar=story_data["name_ar"],
            name_en=story_data["name_en"],
            category=story_data["category"],
            main_figures=story_data.get("main_figures"),
            themes=story_data.get("themes"),
            summary_ar=story_data.get("summary_ar"),
            summary_en=story_data.get("summary_en"),
            suras_mentioned=story_data.get("suras_mentioned"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.merge(story)
        story_count += 1

        # Create segments
        for seg_data in story_data.get("segments", []):
            verse_ids = get_verse_ids_for_range(
                session,
                seg_data["sura_no"],
                seg_data["aya_start"],
                seg_data["aya_end"],
            )

            segment = StorySegment(
                id=seg_data["id"],
                story_id=story_data["id"],
                narrative_order=seg_data["narrative_order"],
                segment_type=seg_data.get("segment_type"),
                aspect=seg_data.get("aspect"),
                sura_no=seg_data["sura_no"],
                aya_start=seg_data["aya_start"],
                aya_end=seg_data["aya_end"],
                verse_ids=verse_ids if verse_ids else None,
                summary_ar=seg_data.get("summary_ar"),
                summary_en=seg_data.get("summary_en"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.merge(segment)
            segment_count += 1

        session.commit()

    return story_count, segment_count


def seed_cross_story_connections(session: Session, connections: list) -> int:
    """Seed cross-story connections from manifest."""
    count = 0
    for conn_data in connections:
        explanation = conn_data.get("explanation", {})

        # Calculate strength based on connection type
        connection_type = conn_data.get("connection_type", "thematic")
        strength = 0.8 if connection_type == "continuation" else 0.6

        connection = CrossStoryConnection(
            source_story_id=conn_data["source_story_id"],
            target_story_id=conn_data["target_story_id"],
            connection_type=connection_type,
            strength=strength,
            label_ar=explanation.get("ar", "")[:200] if explanation.get("ar") else None,
            label_en=explanation.get("en", "")[:200] if explanation.get("en") else None,
            explanation_ar=explanation.get("ar"),
            explanation_en=explanation.get("en"),
            evidence_chunk_ids=conn_data.get("evidence_chunk_ids", ["unknown:0:0"]),
            shared_themes=[conn_data.get("shared_theme")] if conn_data.get("shared_theme") else None,
            shared_figures=conn_data.get("shared_figures"),
        )

        # Check if source and target stories exist
        source_exists = session.execute(
            select(Story.id).where(Story.id == conn_data["source_story_id"])
        ).first()
        target_exists = session.execute(
            select(Story.id).where(Story.id == conn_data["target_story_id"])
        ).first()

        if source_exists and target_exists:
            session.merge(connection)
            count += 1

            # If bidirectional, create reverse connection
            if conn_data.get("bidirectional"):
                reverse = CrossStoryConnection(
                    source_story_id=conn_data["target_story_id"],
                    target_story_id=conn_data["source_story_id"],
                    connection_type=connection_type,
                    strength=strength,
                    label_ar=explanation.get("ar", "")[:200] if explanation.get("ar") else None,
                    label_en=explanation.get("en", "")[:200] if explanation.get("en") else None,
                    explanation_ar=explanation.get("ar"),
                    explanation_en=explanation.get("en"),
                    evidence_chunk_ids=conn_data.get("evidence_chunk_ids", ["unknown:0:0"]),
                    shared_themes=[conn_data.get("shared_theme")] if conn_data.get("shared_theme") else None,
                    shared_figures=conn_data.get("shared_figures"),
                )
                session.merge(reverse)
                count += 1
        else:
            print(f"  Warning: Skipping connection {conn_data.get('id', 'unknown')} - missing stories")

    session.commit()
    return count


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed Quranic stories with validation")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate manifest, don't seed")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip validation (not recommended)")
    parser.add_argument("--fail-on-warnings", action="store_true",
                       help="Treat warnings as errors")
    args = parser.parse_args()

    print("=" * 60)
    print("STORIES SEEDING WITH VALIDATION")
    print("=" * 60)

    start_time = datetime.now()

    try:
        print("\n[1/4] Loading manifest...")
        manifest = load_manifest()
        print(f"  Found {len(manifest.get('stories', []))} stories")
        print(f"  Found {len(manifest.get('themes', []))} themes")

        print("\n[2/4] Connecting to database...")
        engine = create_engine(get_db_url())

        with Session(engine) as session:
            # Check if verses exist
            verse_count = session.execute(select(QuranVerse.id).limit(1)).first()
            if not verse_count:
                print("  ERROR: No verses found. Run seed_quran.py first.")
                sys.exit(1)

            # Validate manifest
            if not args.skip_validation:
                print("\n[3/4] Validating manifest...")
                validator = StoryValidator(session)
                is_valid = validator.validate_manifest(manifest)

                if args.fail_on_warnings and validator.warnings:
                    print("\n  FAILED: Warnings present with --fail-on-warnings flag")
                    sys.exit(1)

                if not is_valid:
                    print("\n  FAILED: Validation errors found. Fix before seeding.")
                    sys.exit(1)

                print(f"\n  Validation passed with {len(validator.warnings)} warnings")

                if args.validate_only:
                    print("\n  --validate-only flag set, skipping seeding.")
                    sys.exit(0)
            else:
                print("\n[3/4] Skipping validation (--skip-validation)")

            print("\n[4/4] Seeding data...")

            # Seed themes
            theme_count = seed_themes(session, manifest.get("themes", []))
            print(f"  Seeded {theme_count} themes")

            # Seed stories
            story_count, segment_count = seed_stories(session, manifest.get("stories", []))
            print(f"  Seeded {story_count} stories with {segment_count} segments")

            # Seed cross-story connections
            cross_conn_count = seed_cross_story_connections(
                session, manifest.get("inter_story_connections", [])
            )
            print(f"  Seeded {cross_conn_count} cross-story connections")

            # Audit log
            AuditLog.log(
                session,
                action="data_import",
                actor="pipeline",
                entity_type="story",
                message=f"Seeded {story_count} stories, {segment_count} segments",
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )
            session.commit()

        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print(f"SUCCESS: Seeding complete in {duration:.2f}s")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
