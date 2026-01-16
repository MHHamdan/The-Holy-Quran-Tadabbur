#!/usr/bin/env python3
"""
Export stories manifest from database.

This script generates a stories.json manifest from the current database state,
ensuring the manifest stays in sync with DB as the single source of truth.

Usage:
    python scripts/ingest/export_manifest.py                    # Print to stdout
    python scripts/ingest/export_manifest.py --output FILE      # Write to file
    python scripts/ingest/export_manifest.py --validate         # Validate only

The export preserves the existing manifest structure for backwards compatibility.
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.story import Story, StorySegment, Theme, CrossStoryConnection


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def export_themes(session: Session) -> List[Dict[str, Any]]:
    """Export all themes from database."""
    result = session.execute(select(Theme).order_by(Theme.id))
    themes = []

    for theme in result.scalars():
        themes.append({
            "id": theme.id,
            "name_ar": theme.name_ar,
            "name_en": theme.name_en,
            "description_ar": theme.description_ar,
            "description_en": theme.description_en,
        })

    return themes


def export_stories(session: Session) -> List[Dict[str, Any]]:
    """Export all stories with segments from database."""
    result = session.execute(
        select(Story).order_by(Story.id)
    )

    stories = []
    for story in result.scalars():
        # Get segments ordered by narrative_order
        segments_result = session.execute(
            select(StorySegment)
            .where(StorySegment.story_id == story.id)
            .order_by(StorySegment.narrative_order)
        )

        segments = []
        for seg in segments_result.scalars():
            segment_data = {
                "id": seg.id,
                "narrative_order": seg.narrative_order,
                "sura_no": seg.sura_no,
                "aya_start": seg.aya_start,
                "aya_end": seg.aya_end,
            }

            # Optional fields
            if seg.aspect:
                segment_data["aspect"] = seg.aspect
            if seg.segment_type:
                segment_data["segment_type"] = seg.segment_type
            if seg.narrative_role:
                segment_data["narrative_role"] = seg.narrative_role
            if seg.summary_ar:
                segment_data["summary_ar"] = seg.summary_ar
            if seg.summary_en:
                segment_data["summary_en"] = seg.summary_en
            if seg.title_ar:
                segment_data["title_ar"] = seg.title_ar
            if seg.title_en:
                segment_data["title_en"] = seg.title_en
            if seg.semantic_tags:
                segment_data["semantic_tags"] = seg.semantic_tags
            if seg.is_entry_point:
                segment_data["is_entry_point"] = seg.is_entry_point

            segments.append(segment_data)

        story_data = {
            "id": story.id,
            "name_ar": story.name_ar,
            "name_en": story.name_en,
            "category": story.category,
        }

        # Optional fields
        if story.main_figures:
            story_data["main_figures"] = story.main_figures
        if story.themes:
            story_data["themes"] = story.themes
        if story.summary_ar:
            story_data["summary_ar"] = story.summary_ar
        if story.summary_en:
            story_data["summary_en"] = story.summary_en
        if story.suras_mentioned:
            story_data["suras_mentioned"] = story.suras_mentioned

        story_data["segments"] = segments
        stories.append(story_data)

    return stories


def export_cross_connections(session: Session) -> List[Dict[str, Any]]:
    """Export all cross-story connections from database."""
    result = session.execute(
        select(CrossStoryConnection).order_by(CrossStoryConnection.id)
    )

    connections = []
    seen = set()  # Avoid duplicates (bidirectional pairs)

    for conn in result.scalars():
        # Create a normalized key to detect duplicates
        pair_key = tuple(sorted([conn.source_story_id, conn.target_story_id]))
        if pair_key in seen:
            continue
        seen.add(pair_key)

        conn_data = {
            "id": f"conn_{conn.source_story_id}_{conn.target_story_id}".replace("story_", ""),
            "source_story_id": conn.source_story_id,
            "target_story_id": conn.target_story_id,
            "connection_type": conn.connection_type,
        }

        # Explanation
        if conn.explanation_ar or conn.explanation_en:
            conn_data["explanation"] = {}
            if conn.explanation_ar:
                conn_data["explanation"]["ar"] = conn.explanation_ar
            if conn.explanation_en:
                conn_data["explanation"]["en"] = conn.explanation_en

        # Evidence
        if conn.evidence_chunk_ids:
            conn_data["evidence_chunk_ids"] = conn.evidence_chunk_ids

        # Shared themes/figures
        if conn.shared_themes:
            if len(conn.shared_themes) == 1:
                conn_data["shared_theme"] = conn.shared_themes[0]
            else:
                conn_data["shared_themes"] = conn.shared_themes

        if conn.shared_figures:
            conn_data["shared_figures"] = conn.shared_figures

        # Check if bidirectional (has reverse in DB)
        reverse_check = session.execute(
            select(CrossStoryConnection).where(
                CrossStoryConnection.source_story_id == conn.target_story_id,
                CrossStoryConnection.target_story_id == conn.source_story_id
            )
        ).first()

        if reverse_check:
            conn_data["bidirectional"] = True

        connections.append(conn_data)

    return connections


def generate_manifest(session: Session) -> Dict[str, Any]:
    """Generate complete manifest from database."""
    stories = export_stories(session)
    themes = export_themes(session)
    connections = export_cross_connections(session)

    # Category distribution for validation
    categories = {}
    for story in stories:
        cat = story.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    manifest = {
        "name": "Quranic Stories Manifest",
        "version": "2.0.0",
        "description": "Comprehensive manifest of 25+ Quranic stories with verse mappings and cross-surah connections",
        "license": "Original scholarly research - cite appropriately",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),

        "stories": stories,

        "themes": themes,

        "connection_types": [
            {"type": "expansion", "description": "One passage expands on details of another"},
            {"type": "parallel", "description": "Two passages tell the same event from different angles"},
            {"type": "continuation", "description": "One passage continues the narrative from another"},
            {"type": "thematic", "description": "Passages share a common theme across stories"}
        ],

        "inter_story_connections": connections,

        "validation_rules": {
            "min_stories": 25,
            "min_total_connections": 20,
            "require_evidence_chunk_ids": True,
            "evidence_chunk_id_pattern": "^[a-z_]+:\\d+:\\d+(-\\d+)?$"
        },

        "_export_metadata": {
            "exported_at": datetime.now().isoformat(),
            "story_count": len(stories),
            "theme_count": len(themes),
            "connection_count": len(connections),
            "categories": categories,
        }
    }

    return manifest


def validate_manifest(manifest: Dict[str, Any]) -> bool:
    """Validate generated manifest against rules."""
    rules = manifest.get("validation_rules", {})
    errors = []

    # Check story count
    min_stories = rules.get("min_stories", 25)
    story_count = len(manifest.get("stories", []))
    if story_count < min_stories:
        errors.append(f"Insufficient stories: {story_count} < {min_stories}")

    # Check connection count
    min_connections = rules.get("min_total_connections", 20)
    conn_count = len(manifest.get("inter_story_connections", []))
    if conn_count < min_connections:
        errors.append(f"Insufficient connections: {conn_count} < {min_connections}")

    # Check all categories have stories
    required_categories = ["prophet", "nation", "parable", "historical", "righteous"]
    # Calculate categories from stories if metadata not available
    categories = manifest.get("_export_metadata", {}).get("categories", {})
    if not categories:
        categories = {}
        for story in manifest.get("stories", []):
            cat = story.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
    empty_cats = [cat for cat in required_categories if categories.get(cat, 0) == 0]
    if empty_cats:
        errors.append(f"Empty categories: {empty_cats}")

    # Check stories have segments
    stories_without_segments = []
    for story in manifest.get("stories", []):
        if not story.get("segments"):
            stories_without_segments.append(story.get("id"))
    if stories_without_segments:
        errors.append(f"Stories without segments: {stories_without_segments}")

    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return False

    print("Validation passed!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Export stories manifest from database")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--validate", action="store_true", help="Validate only, don't export")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON", default=True)
    parser.add_argument("--no-metadata", action="store_true", help="Exclude export metadata")
    args = parser.parse_args()

    print("=" * 60)
    print("STORIES MANIFEST EXPORT")
    print("=" * 60)

    try:
        print("\n[1/3] Connecting to database...")
        engine = create_engine(get_db_url())

        with Session(engine) as session:
            print("\n[2/3] Exporting data...")
            manifest = generate_manifest(session)

            # Remove metadata if requested
            if args.no_metadata:
                manifest.pop("_export_metadata", None)

            meta = manifest.get("_export_metadata", {})
            print(f"  Stories: {meta.get('story_count', len(manifest.get('stories', [])))}")
            print(f"  Themes: {meta.get('theme_count', len(manifest.get('themes', [])))}")
            print(f"  Connections: {meta.get('connection_count', len(manifest.get('inter_story_connections', [])))}")
            print(f"  Categories: {meta.get('categories', {})}")

            print("\n[3/3] Validating...")
            is_valid = validate_manifest(manifest)

            if args.validate:
                sys.exit(0 if is_valid else 1)

            # Output
            indent = 2 if args.pretty else None
            json_output = json.dumps(manifest, indent=indent, ensure_ascii=False)

            if args.output:
                output_path = Path(args.output)
                output_path.write_text(json_output, encoding="utf-8")
                print(f"\nExported to: {output_path}")
            else:
                print("\n" + "=" * 60)
                print("MANIFEST JSON:")
                print("=" * 60)
                print(json_output)

        print("\n" + "=" * 60)
        print("SUCCESS: Export complete")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
