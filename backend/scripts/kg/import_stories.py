#!/usr/bin/env python3
"""
Import verified story registry to SurrealDB Knowledge Graph.

PR3: CLI for importing stories, events, persons, and edges.

Usage:
    python scripts/kg/import_stories.py [--dry-run] [--verbose]

Prerequisites:
    - SurrealDB must be running
    - Schema must be initialized (run POST /kg/init-schema first)
    - Stories must be verified (run python scripts/verify/quran_verify.py first)
"""

import asyncio
import argparse
import logging
from pathlib import Path


async def main():
    parser = argparse.ArgumentParser(description='Import stories to SurrealDB Knowledge Graph')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--manifest', type=str, help='Path to stories.json manifest')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print("📊 Story Import to SurrealDB Knowledge Graph")
    print("=" * 50)

    # Find manifest
    manifest_path = None
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json",
            Path(__file__).parent.parent.parent / "data" / "manifests" / "stories.json",
            Path("/home/mhamdan/tadabbur/data/manifests/stories.json"),
        ]
        for p in possible_paths:
            if p.exists():
                manifest_path = p
                break

    if not manifest_path or not manifest_path.exists():
        print("❌ Could not find stories.json manifest")
        return 1

    print(f"📂 Manifest: {manifest_path}")

    if args.dry_run:
        # Just load and count
        import json
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stories = data.get('stories', [])
        total_segments = sum(len(s.get('segments', [])) for s in stories)

        print(f"\n🔍 Dry run - would import:")
        print(f"   📚 Stories: {len(stories)}")
        print(f"   📖 Events: {total_segments}")
        print("\nNo changes made.")
        return 0

    # Import for real
    try:
        from app.kg.story_importer import StoryImporter
        from app.kg.client import get_kg_client

        # Check SurrealDB health
        kg = get_kg_client()
        health = await kg.health_check()

        if health.get("status") != "ok":
            print(f"❌ SurrealDB not available: {health}")
            print("\n💡 Make sure SurrealDB is running:")
            print("   docker-compose up -d surrealdb")
            return 1

        print(f"✅ SurrealDB connected: {health.get('host')}:{health.get('port')}")

        # Run import
        print("\n🚀 Starting import...")
        importer = StoryImporter(kg)
        metrics = await importer.import_all(manifest_path=manifest_path)

        print("\n✅ Import complete!")
        print(f"   📚 Stories imported: {metrics['stories_imported']}")
        print(f"   📖 Events imported: {metrics['events_imported']}")
        print(f"   👤 Persons imported: {metrics['persons_imported']}")
        print(f"   📍 Places imported: {metrics['places_imported']}")
        print(f"   🔗 Edges created: {metrics['edges_created']}")

        if metrics.get('errors'):
            print(f"\n⚠️  Errors: {len(metrics['errors'])}")
            for err in metrics['errors'][:5]:
                print(f"   - {err}")

        return 0

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure you're running from the backend directory:")
        print("   cd /home/mhamdan/tadabbur/backend")
        print("   PYTHONPATH=. python scripts/kg/import_stories.py")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
