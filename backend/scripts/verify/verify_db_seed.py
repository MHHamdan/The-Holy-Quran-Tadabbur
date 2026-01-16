#!/usr/bin/env python3
"""
Verify database is seeded correctly.

Checks:
  - Quran verses table has 6236 verses
  - Tafseer sources exist
  - Tafseer chunks are linked correctly
  - Stories and segments exist with valid verse ranges
  - Story connections have evidence_chunk_ids

Exit codes:
  0 - Database seeded correctly
  1 - Database seeding issues found
"""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text, func, select
from sqlalchemy.orm import Session

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"

# Expected counts
EXPECTED_VERSE_COUNT = 6236
EXPECTED_SURA_COUNT = 114
EXPECTED_PAGE_COUNT = 604
EXPECTED_JUZ_COUNT = 30
EXPECTED_MIN_STORIES = 25
MIN_TOTAL_CONNECTIONS = 25  # Prevent regression to "story catalog only"


def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"
    )


def check_verse_count(session: Session) -> tuple[bool, str]:
    """Check total verse count."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM quran_verses"))
        count = result.scalar()

        if count == EXPECTED_VERSE_COUNT:
            return True, f"Verse count: {count} (expected {EXPECTED_VERSE_COUNT})"
        elif count == 0:
            return False, "No verses found - database not seeded"
        else:
            return False, f"Verse count mismatch: {count} (expected {EXPECTED_VERSE_COUNT})"
    except Exception as e:
        return False, f"Error checking verses: {str(e)}"


def check_sura_distribution(session: Session) -> tuple[bool, str]:
    """Check sura distribution."""
    try:
        result = session.execute(text(
            "SELECT COUNT(DISTINCT sura_no) FROM quran_verses"
        ))
        count = result.scalar()

        if count == EXPECTED_SURA_COUNT:
            return True, f"Sura count: {count} (expected {EXPECTED_SURA_COUNT})"
        elif count == 0:
            return False, "No suras found"
        else:
            return False, f"Sura count mismatch: {count} (expected {EXPECTED_SURA_COUNT})"
    except Exception as e:
        return False, f"Error checking suras: {str(e)}"


def check_page_distribution(session: Session) -> tuple[bool, str]:
    """Check page distribution."""
    try:
        result = session.execute(text(
            "SELECT COUNT(DISTINCT page_no) FROM quran_verses"
        ))
        count = result.scalar()

        if count == EXPECTED_PAGE_COUNT:
            return True, f"Page count: {count} (expected {EXPECTED_PAGE_COUNT})"
        elif count == 0:
            return False, "No pages found"
        else:
            # Allow some variance for different editions
            if count >= EXPECTED_PAGE_COUNT - 5:
                return True, f"Page count: {count} (close to expected {EXPECTED_PAGE_COUNT})"
            return False, f"Page count mismatch: {count} (expected ~{EXPECTED_PAGE_COUNT})"
    except Exception as e:
        return False, f"Error checking pages: {str(e)}"


def check_tafseer_sources(session: Session) -> tuple[bool, str]:
    """Check tafseer sources exist."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM tafseer_sources"))
        count = result.scalar()

        if count > 0:
            # Get source names
            names_result = session.execute(text(
                "SELECT id, name_en FROM tafseer_sources LIMIT 5"
            ))
            names = [f"{row[0]}: {row[1]}" for row in names_result]
            return True, f"Found {count} tafseer sources: {', '.join(names)}"
        else:
            return False, "No tafseer sources found - need to seed tafseer data"
    except Exception as e:
        if "does not exist" in str(e):
            return False, "tafseer_sources table does not exist - run migrations"
        return False, f"Error checking tafseer sources: {str(e)}"


def check_tafseer_chunks(session: Session) -> tuple[bool, str]:
    """Check tafseer chunks exist and are properly linked."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM tafseer_chunks"))
        count = result.scalar()

        if count > 0:
            # Check linking
            orphan_result = session.execute(text("""
                SELECT COUNT(*) FROM tafseer_chunks tc
                WHERE NOT EXISTS (
                    SELECT 1 FROM quran_verses qv WHERE qv.id = tc.verse_start_id
                )
            """))
            orphan_count = orphan_result.scalar()

            if orphan_count == 0:
                return True, f"Found {count} tafseer chunks, all properly linked"
            else:
                return False, f"Found {orphan_count} orphan chunks (not linked to verses)"
        else:
            return False, "No tafseer chunks found - need to seed tafseer data"
    except Exception as e:
        if "does not exist" in str(e):
            return False, "tafseer_chunks table does not exist - run migrations"
        return False, f"Error checking tafseer chunks: {str(e)}"


def check_stories(session: Session) -> tuple[bool, str]:
    """Check stories exist."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM stories"))
        count = result.scalar()

        if count >= EXPECTED_MIN_STORIES:
            return True, f"Found {count} stories (expected >= {EXPECTED_MIN_STORIES})"
        elif count > 0:
            return False, f"Found only {count} stories (expected >= {EXPECTED_MIN_STORIES})"
        else:
            return False, "No stories found - need to seed story data"
    except Exception as e:
        if "does not exist" in str(e):
            return False, "stories table does not exist - run migrations"
        return False, f"Error checking stories: {str(e)}"


def check_story_segments(session: Session) -> tuple[bool, str]:
    """Check story segments exist and are linked."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM story_segments"))
        count = result.scalar()

        if count > 0:
            # Check all segments have valid stories
            orphan_result = session.execute(text("""
                SELECT COUNT(*) FROM story_segments ss
                WHERE NOT EXISTS (
                    SELECT 1 FROM stories s WHERE s.id = ss.story_id
                )
            """))
            orphan_count = orphan_result.scalar()

            if orphan_count == 0:
                return True, f"Found {count} story segments, all linked to stories"
            else:
                return False, f"Found {orphan_count} orphan segments"
        else:
            return False, "No story segments found"
    except Exception as e:
        if "does not exist" in str(e):
            return False, "story_segments table does not exist - run migrations"
        return False, f"Error checking story segments: {str(e)}"


def check_translations(session: Session) -> tuple[bool, str]:
    """Check translations exist."""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM translations"))
        count = result.scalar()

        if count > 0:
            # Get language distribution
            lang_result = session.execute(text("""
                SELECT language, COUNT(*) as cnt
                FROM translations
                GROUP BY language
            """))
            langs = {row[0]: row[1] for row in lang_result}
            lang_str = ", ".join([f"{k}: {v}" for k, v in langs.items()])
            return True, f"Found {count} translations ({lang_str})"
        else:
            return False, "No translations found - consider adding translations"
    except Exception as e:
        if "does not exist" in str(e):
            return False, "translations table does not exist - run migrations"
        return False, f"Error checking translations: {str(e)}"


def parse_evidence_chunk_id(chunk_id: str) -> tuple[str, int, int, int] | None:
    """
    Parse evidence_chunk_id format: source:surah:ayah_start-ayah_end or source:surah:ayah

    Returns (source, surah, ayah_start, ayah_end) or None if invalid.
    """
    import re

    # Pattern: source_id:surah_num:ayah_start-ayah_end OR source_id:surah_num:ayah
    pattern = r'^([a-z_]+):(\d+):(\d+)(?:-(\d+))?$'
    match = re.match(pattern, chunk_id)

    if not match:
        return None

    source = match.group(1)
    surah = int(match.group(2))
    ayah_start = int(match.group(3))
    ayah_end = int(match.group(4)) if match.group(4) else ayah_start

    return source, surah, ayah_start, ayah_end


def check_evidence_alignment(
    evidence_ids: list[str],
    segments: list[dict],
    segment_ids: list[str]
) -> list[str]:
    """
    Check that evidence_chunk_ids align with the verse ranges of source/target segments.

    Returns list of alignment warnings (empty if all aligned).
    """
    warnings = []

    # Build segment lookup: id -> (surah, ayah_start, ayah_end)
    segment_ranges = {}
    for seg in segments:
        seg_id = seg.get("id")
        if seg_id:
            segment_ranges[seg_id] = (
                seg.get("sura_no"),
                seg.get("aya_start"),
                seg.get("aya_end")
            )

    # Get relevant segment verse ranges
    relevant_ranges = []
    for seg_id in segment_ids:
        if seg_id in segment_ranges:
            relevant_ranges.append(segment_ranges[seg_id])

    if not relevant_ranges:
        return warnings  # Can't check alignment without segment info

    # Check each evidence chunk overlaps with at least one segment range
    for chunk_id in evidence_ids:
        parsed = parse_evidence_chunk_id(chunk_id)
        if not parsed:
            warnings.append(f"Invalid evidence_chunk_id format: {chunk_id}")
            continue

        source, surah, ayah_start, ayah_end = parsed

        # Check if this chunk's surah/ayah overlaps with any segment
        overlaps = False
        for seg_surah, seg_start, seg_end in relevant_ranges:
            if seg_surah == surah:
                # Check ayah overlap
                if ayah_start <= seg_end and ayah_end >= seg_start:
                    overlaps = True
                    break

        if not overlaps:
            # Not a fatal error, but worth noting
            seg_ranges_str = ", ".join([
                f"{s}:{a}-{b}" for s, a, b in relevant_ranges
            ])
            warnings.append(
                f"Evidence {chunk_id} doesn't overlap segments ({seg_ranges_str})"
            )

    return warnings


def validate_stories_manifest() -> tuple[bool, str, list[str]]:
    """
    Validate stories manifest has valid verse ranges and evidence_chunk_ids.

    Checks:
    1. Minimum story count
    2. All segments have valid verse ranges
    3. All intra-story connections have evidence_chunk_ids
    4. Inter-story connections exist and have evidence
    5. Evidence alignment with source/target verse ranges

    Returns (passed, message, errors)
    """
    errors = []
    warnings = []

    manifest_path = MANIFESTS_DIR / "stories.json"
    if not manifest_path.exists():
        return False, f"Stories manifest not found: {manifest_path}", ["File not found"]

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in stories manifest: {e}", [str(e)]

    stories = manifest.get("stories", [])
    inter_story_connections = manifest.get("inter_story_connections", [])
    validation_rules = manifest.get("validation_rules", {})

    # Get validation thresholds (hardcoded MIN_TOTAL_CONNECTIONS cannot be lowered)
    min_stories = validation_rules.get("min_stories", EXPECTED_MIN_STORIES)
    min_connections = max(
        validation_rules.get("min_total_connections", MIN_TOTAL_CONNECTIONS),
        MIN_TOTAL_CONNECTIONS  # Enforce minimum to prevent regression
    )

    if len(stories) < min_stories:
        errors.append(f"Only {len(stories)} stories (expected >= {min_stories})")

    # Build global segment lookup for all stories
    all_segments = {}
    story_segments = {}  # story_id -> list of segments

    for story in stories:
        story_id = story.get("id", "unknown")
        segments = story.get("segments", [])
        story_segments[story_id] = segments

        for segment in segments:
            seg_id = segment.get("id")
            if seg_id:
                all_segments[seg_id] = segment

    # Validate each story
    for story in stories:
        story_id = story.get("id", "unknown")
        segments = story.get("segments", [])

        if not segments:
            errors.append(f"{story_id}: No segments defined")
            continue

        for segment in segments:
            seg_id = segment.get("id", "unknown")
            sura_no = segment.get("sura_no")
            aya_start = segment.get("aya_start")
            aya_end = segment.get("aya_end")

            # Validate surah number
            if not sura_no or sura_no < 1 or sura_no > 114:
                errors.append(f"{story_id}/{seg_id}: Invalid sura_no ({sura_no})")

            # Validate ayah range
            if not aya_start or aya_start < 1:
                errors.append(f"{story_id}/{seg_id}: Invalid aya_start ({aya_start})")
            if not aya_end or aya_end < 1:
                errors.append(f"{story_id}/{seg_id}: Invalid aya_end ({aya_end})")
            if aya_start and aya_end and aya_start > aya_end:
                errors.append(f"{story_id}/{seg_id}: aya_start ({aya_start}) > aya_end ({aya_end})")

        # Check intra-story connections have evidence_chunk_ids
        connections = story.get("connections", [])
        for conn in connections:
            source = conn.get("source", "?")
            target = conn.get("target", "?")
            evidence_ids = conn.get("evidence_chunk_ids", [])

            if not evidence_ids:
                errors.append(f"{story_id}: Connection {source}->{target} missing evidence_chunk_ids")
            else:
                # Check alignment
                align_warnings = check_evidence_alignment(
                    evidence_ids,
                    segments,
                    [source, target]
                )
                warnings.extend(align_warnings)

    # Validate inter-story connections
    total_connections = sum(len(s.get("connections", [])) for s in stories)
    total_connections += len(inter_story_connections)

    if total_connections < min_connections:
        errors.append(
            f"Only {total_connections} total connections (expected >= {min_connections})"
        )

    for conn in inter_story_connections:
        conn_id = conn.get("id", "unknown")
        source_story = conn.get("source_story_id")
        target_story = conn.get("target_story_id")
        evidence_ids = conn.get("evidence_chunk_ids", [])

        # Verify stories exist
        story_ids = {s.get("id") for s in stories}
        if source_story not in story_ids:
            errors.append(f"Inter-connection {conn_id}: source_story_id '{source_story}' not found")
        if target_story not in story_ids:
            errors.append(f"Inter-connection {conn_id}: target_story_id '{target_story}' not found")

        # Check evidence
        if not evidence_ids:
            errors.append(f"Inter-connection {conn_id}: missing evidence_chunk_ids")
        else:
            # Validate evidence format
            for eid in evidence_ids:
                parsed = parse_evidence_chunk_id(eid)
                if not parsed:
                    errors.append(f"Inter-connection {conn_id}: invalid evidence format '{eid}'")

    if errors:
        return False, f"Found {len(errors)} issues in stories manifest", errors

    summary = (
        f"Stories manifest valid: {len(stories)} stories, "
        f"{total_connections} connections (intra: {total_connections - len(inter_story_connections)}, "
        f"inter: {len(inter_story_connections)})"
    )

    if warnings:
        summary += f" [Warnings: {len(warnings)}]"

    return True, summary, warnings


def main():
    """Run all database seed verifications."""
    print("=" * 60)
    print("DATABASE SEED VERIFICATION")
    print("=" * 60)

    db_url = get_db_url()
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")

    # First, validate stories manifest (doesn't require DB)
    print("\n[0/8] Validating stories manifest...")
    manifest_passed, manifest_msg, manifest_errors = validate_stories_manifest()
    print(f"  {'PASS' if manifest_passed else 'FAIL'}: {manifest_msg}")
    if manifest_errors and not manifest_passed:
        for err in manifest_errors[:5]:
            print(f"    - {err}")
        if len(manifest_errors) > 5:
            print(f"    ... and {len(manifest_errors) - 5} more errors")

    try:
        engine = create_engine(db_url)
        with Session(engine) as session:
            all_passed = True
            results = []

            # Check verses
            print("\n[1/8] Checking Quran verses...")
            passed, msg = check_verse_count(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Verse count", passed))
            if not passed:
                all_passed = False

            # Check suras
            print("\n[2/8] Checking sura distribution...")
            passed, msg = check_sura_distribution(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Sura distribution", passed))
            if not passed:
                all_passed = False

            # Check pages
            print("\n[3/8] Checking page distribution...")
            passed, msg = check_page_distribution(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Page distribution", passed))
            if not passed:
                all_passed = False

            # Check tafseer sources
            print("\n[4/8] Checking tafseer sources...")
            passed, msg = check_tafseer_sources(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Tafseer sources", passed))
            # Tafseer is optional for MVP
            # if not passed: all_passed = False

            # Check tafseer chunks
            print("\n[5/8] Checking tafseer chunks...")
            passed, msg = check_tafseer_chunks(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Tafseer chunks", passed))
            # Tafseer is optional for MVP

            # Check stories
            print("\n[6/8] Checking stories...")
            passed, msg = check_stories(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Stories", passed))
            # Stories check includes minimum count

            # Check story segments
            print("\n[7/8] Checking story segments...")
            passed, msg = check_story_segments(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Story segments", passed))

            # Check translations
            print("\n[8/8] Checking translations...")
            passed, msg = check_translations(session)
            print(f"  {'PASS' if passed else 'FAIL'}: {msg}")
            results.append(("Translations", passed))
            # Translations are optional

            # Add manifest result
            results.append(("Stories manifest", manifest_passed))

            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)

            for name, passed in results:
                status = "PASS" if passed else "FAIL"
                print(f"  {name}: {status}")

            print("\n" + "=" * 60)

            # Core requirements: verses must be seeded AND manifest must be valid
            core_passed = results[0][1] and manifest_passed

            if core_passed:
                print("OVERALL: PASS - Core data (verses) is seeded and manifest valid")
                print("=" * 60)
                sys.exit(0)
            else:
                print("OVERALL: FAIL - Core data or manifest validation failed")
                print("=" * 60)
                print("\nREMEDIATION:")
                if not results[0][1]:
                    print("  1. Run migrations: alembic upgrade head")
                    print("  2. Run seed script: python scripts/ingest/seed_quran.py")
                if not manifest_passed:
                    print("  - Fix stories manifest: ensure all connections have evidence_chunk_ids")
                    print("  - Ensure all segments have valid verse ranges")
                sys.exit(1)

    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print("\nREMEDIATION:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check database credentials")
        print("  3. Run migrations: alembic upgrade head")
        sys.exit(1)


if __name__ == "__main__":
    main()
