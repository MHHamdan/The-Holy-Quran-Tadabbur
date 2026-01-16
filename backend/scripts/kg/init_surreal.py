#!/usr/bin/env python3
"""
Initialize SurrealDB Knowledge Graph.

Performs:
1. Schema initialization (creates tables, indexes, edges)
2. Concept tag import (themes, morals, miracles)
3. Story import (clusters, events, persons, places)

Usage:
    # From backend directory:
    PYTHONPATH=. python scripts/kg/init_surreal.py [--skip-schema] [--skip-concepts] [--skip-stories]

    # Or via docker exec:
    docker exec tadabbur-backend python scripts/kg/init_surreal.py

Prerequisites:
    - SurrealDB must be running (docker-compose up -d surrealdb)
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


async def wait_for_surreal(max_retries: int = 30, delay: float = 2.0) -> bool:
    """Wait for SurrealDB to be available."""
    from app.kg.client import get_kg_client

    kg = get_kg_client()

    for attempt in range(max_retries):
        try:
            health = await kg.health_check()
            if health.get("status") == "ok":
                print(f"   SurrealDB ready at {health.get('host')}:{health.get('port')}")
                return True
        except Exception as e:
            if attempt == 0:
                print(f"   Waiting for SurrealDB... (attempt {attempt + 1}/{max_retries})")
            else:
                print(f"   Retry {attempt + 1}/{max_retries}...")

        await asyncio.sleep(delay)

    return False


async def init_schema() -> Dict[str, Any]:
    """Initialize SurrealDB schema."""
    from app.kg.client import get_kg_client
    from app.kg.schema import get_schema_sql, SCHEMA_VERSION

    print("\n2. Initializing schema...")

    kg = get_kg_client()
    schema_sql = get_schema_sql()

    # Split into statements and execute
    statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]

    executed = 0
    errors = []

    for stmt in statements:
        try:
            await kg.query(stmt + ';')
            executed += 1
        except Exception as e:
            if "already exists" not in str(e).lower():
                errors.append(f"{stmt[:50]}...: {e}")

    print(f"   Executed {executed} schema statements")
    print(f"   Schema version: {SCHEMA_VERSION}")

    if errors:
        print(f"   Warnings: {len(errors)}")
        for err in errors[:3]:
            print(f"      - {err}")

    return {"executed": executed, "errors": len(errors), "version": SCHEMA_VERSION}


async def import_concepts(manifest_path: Path) -> Dict[str, Any]:
    """Import concept tags from curated_concepts.json."""
    from app.kg.client import get_kg_client
    import hashlib

    print("\n3. Importing concepts...")

    if not manifest_path.exists():
        print(f"   Concept manifest not found: {manifest_path}")
        return {"imported": 0, "skipped": 0}

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    concepts = data.get('concepts', [])
    kg = get_kg_client()

    imported = 0
    skipped = 0

    for concept in concepts:
        key = concept.get('key', concept.get('id', ''))
        if not key:
            skipped += 1
            continue

        # Create concept tag record
        record_id = f"concept_tag:{key}"

        record = {
            "key": key,
            "label_ar": concept.get('label_ar', concept.get('name_ar', '')),
            "label_en": concept.get('label_en', concept.get('name_en', '')),
            "category": concept.get('category', 'theme'),
            "description_ar": concept.get('description_ar', ''),
            "description_en": concept.get('description_en', ''),
            "icon_hint": concept.get('icon', ''),
            "_hash": hashlib.md5(json.dumps(concept, sort_keys=True).encode()).hexdigest()[:12],
            "_version": "1.0.0",
            "_source": "curated",
        }

        try:
            # UPDATE MERGE creates if not exists, merges if exists (preserves schema defaults)
            await kg.query(
                f"UPDATE {record_id} MERGE $data;",
                {"data": record}
            )
            imported += 1
        except Exception as e:
            logger.debug(f"Concept {key} error: {e}")
            skipped += 1

    print(f"   Imported {imported} concepts, skipped {skipped}")
    return {"imported": imported, "skipped": skipped}


async def import_stories(manifest_path: Path) -> Dict[str, Any]:
    """Import stories using the StoryImporter."""
    print("\n4. Importing stories...")

    if not manifest_path.exists():
        print(f"   Story manifest not found: {manifest_path}")
        return {"stories": 0, "events": 0, "persons": 0, "places": 0}

    try:
        from app.kg.story_importer import StoryImporter
        from app.kg.client import get_kg_client

        kg = get_kg_client()
        importer = StoryImporter(kg)
        metrics = await importer.import_all(manifest_path=manifest_path)

        print(f"   Stories: {metrics.get('stories_imported', 0)}")
        print(f"   Events: {metrics.get('events_imported', 0)}")
        print(f"   Persons: {metrics.get('persons_imported', 0)}")
        print(f"   Places: {metrics.get('places_imported', 0)}")
        print(f"   Edges: {metrics.get('edges_created', 0)}")

        return metrics

    except ImportError as e:
        print(f"   Story importer not available: {e}")

        # Fallback: Load and import directly
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stories = data.get('stories', [])
        from app.kg.client import get_kg_client
        import hashlib

        kg = get_kg_client()
        imported_stories = 0
        imported_events = 0

        for story in stories:
            story_id = story.get('id', '')
            if not story_id:
                continue

            # Create story cluster
            record_id = f"story_cluster:{story_id}"

            record = {
                "slug": story_id,
                "title_ar": story.get('title_ar', ''),
                "title_en": story.get('title_en', ''),
                "category": story.get('category', 'prophets'),
                "tags": story.get('tags', []),
                "summary_ar": story.get('summary_ar', ''),
                "summary_en": story.get('summary_en', ''),
                "_hash": hashlib.md5(json.dumps(story, sort_keys=True).encode()).hexdigest()[:12],
            }

            try:
                await kg.query(
                    f"UPDATE {record_id} MERGE $data;",
                    {"data": record}
                )
                imported_stories += 1

                # Import events/segments
                segments = story.get('segments', [])
                for idx, segment in enumerate(segments):
                    event_id = f"story_event:{story_id}_{idx}"
                    event_record = {
                        "cluster_id": record_id,
                        "slug": f"{story_id}_event_{idx}",
                        "title_ar": segment.get('title_ar', segment.get('summary_ar', '')[:50]),
                        "title_en": segment.get('title_en', segment.get('summary_en', '')[:50]),
                        "chronological_index": idx,
                        "summary_ar": segment.get('summary_ar', ''),
                        "summary_en": segment.get('summary_en', ''),
                        "verse_reference": segment.get('verse_range', ''),
                        "_hash": hashlib.md5(json.dumps(segment, sort_keys=True).encode()).hexdigest()[:12],
                    }

                    await kg.query(
                        f"UPDATE {event_id} MERGE $data;",
                        {"data": event_record}
                    )
                    imported_events += 1

            except Exception as e:
                logger.debug(f"Story {story_id} error: {e}")

        print(f"   Stories: {imported_stories}")
        print(f"   Events: {imported_events}")

        return {"stories_imported": imported_stories, "events_imported": imported_events}


async def main():
    parser = argparse.ArgumentParser(description='Initialize SurrealDB Knowledge Graph')
    parser.add_argument('--skip-schema', action='store_true', help='Skip schema initialization')
    parser.add_argument('--skip-concepts', action='store_true', help='Skip concept import')
    parser.add_argument('--skip-stories', action='store_true', help='Skip story import')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    print("=" * 60)
    print("  SurrealDB Knowledge Graph Initialization")
    print("=" * 60)

    # Step 1: Wait for SurrealDB
    print("\n1. Connecting to SurrealDB...")
    if not await wait_for_surreal():
        print("\n   SurrealDB not available!")
        print("\n   Start SurrealDB with:")
        print("   docker-compose up -d surrealdb")
        return 1

    # Find data paths
    base_path = Path(__file__).parent.parent.parent.parent
    concepts_path = base_path / "data" / "concepts" / "curated_concepts.json"
    stories_path = base_path / "data" / "manifests" / "stories.json"

    # Fallback paths
    if not concepts_path.exists():
        concepts_path = Path("/home/mhamdan/tadabbur/data/concepts/curated_concepts.json")
    if not stories_path.exists():
        stories_path = Path("/home/mhamdan/tadabbur/data/manifests/stories.json")

    results = {}

    # Step 2: Initialize schema
    if not args.skip_schema:
        results['schema'] = await init_schema()
    else:
        print("\n2. Skipping schema initialization")

    # Step 3: Import concepts
    if not args.skip_concepts:
        results['concepts'] = await import_concepts(concepts_path)
    else:
        print("\n3. Skipping concept import")

    # Step 4: Import stories
    if not args.skip_stories:
        results['stories'] = await import_stories(stories_path)
    else:
        print("\n4. Skipping story import")

    # Summary
    print("\n" + "=" * 60)
    print("  Initialization Complete!")
    print("=" * 60)

    if 'schema' in results:
        print(f"  Schema: {results['schema']['executed']} statements (v{results['schema']['version']})")
    if 'concepts' in results:
        print(f"  Concepts: {results['concepts']['imported']} imported")
    if 'stories' in results:
        print(f"  Stories: {results['stories'].get('stories_imported', 0)} imported")
        print(f"  Events: {results['stories'].get('events_imported', 0)} imported")

    print("\n  Test with:")
    print("  curl http://localhost:8000/api/v1/graph/search/semantic?q=patience")
    print("  curl http://localhost:8000/api/v1/graph/explore/bfs?start_id=story_cluster:story_musa")

    return 0


if __name__ == '__main__':
    exit(asyncio.run(main()))
