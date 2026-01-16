"""
Story Importer - Import verified registry to SurrealDB Knowledge Graph.

PR3: Reads the verified QuranStoryRegistry and imports:
- Story clusters (story_cluster table)
- Story events (story_event table)
- Persons (person table)
- Places (place table)
- Edge relationships (has_event, involves, etc.)

Idempotent: Re-running will overwrite gracefully using UPSERT.

Usage:
    from app.kg.story_importer import StoryImporter

    importer = StoryImporter()
    await importer.import_all()
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.verify.registry import (
    QuranStoryRegistry,
    StoryRegistryEntry,
    StoryEvent,
    Person,
    Place,
    AyahRange,
    StoryCategory,
)
from app.kg.client import KGClient, get_kg_client

logger = logging.getLogger(__name__)


def content_hash(content: str) -> str:
    """Generate a short content hash for idempotency."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def sanitize_id(raw_id: str) -> str:
    """
    Sanitize a string to be a valid SurrealDB record ID.

    SurrealDB record IDs can only contain:
    - Alphanumeric characters (a-z, A-Z, 0-9)
    - Underscores (_)

    This function:
    - Converts to lowercase
    - Replaces spaces with underscores
    - Removes parentheses and their contents
    - Replaces hyphens with underscores
    - Removes apostrophes
    - Transliterates Arabic characters to ASCII
    - Removes any other invalid characters
    """
    import re
    import unicodedata

    # Normalize Unicode
    s = unicodedata.normalize('NFKD', raw_id)

    # Remove Arabic characters by converting to ASCII equivalent or removing
    # Simple transliteration map for common Arabic characters
    arabic_map = {
        'آ': 'a', 'أ': 'a', 'إ': 'i', 'ا': 'a',
        'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
        'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'dh',
        'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
        'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z',
        'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
        'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a',
        'ة': 'h', 'ء': '', 'ئ': 'y', 'ؤ': 'w',
        'ُ': '', 'ِ': '', 'َ': '', 'ْ': '', 'ّ': '',
    }

    result = []
    for char in s:
        if char in arabic_map:
            result.append(arabic_map[char])
        elif char.isascii():
            result.append(char)
        # Skip non-ASCII, non-Arabic characters

    s = ''.join(result)

    # Lowercase
    s = s.lower()

    # Remove content in parentheses
    s = re.sub(r'\([^)]*\)', '', s)

    # Replace hyphens and spaces with underscores
    s = s.replace('-', '_').replace(' ', '_')

    # Remove apostrophes and quotes
    s = s.replace("'", '').replace('"', '')

    # Keep only alphanumeric and underscores
    s = re.sub(r'[^a-z0-9_]', '', s)

    # Clean up multiple underscores
    s = re.sub(r'_+', '_', s)

    # Remove leading/trailing underscores
    s = s.strip('_')

    # Ensure non-empty
    if not s:
        s = content_hash(raw_id)[:8]

    return s


class StoryImporter:
    """
    Imports verified story registry to SurrealDB Knowledge Graph.

    Features:
    - Idempotent imports using UPSERT
    - Creates all nodes (stories, events, persons, places)
    - Creates all edges (has_event, involves, located_in, next)
    - Tracks import metrics
    """

    def __init__(self, kg_client: KGClient = None):
        self.kg = kg_client or get_kg_client()
        self.metrics = {
            "stories_imported": 0,
            "events_imported": 0,
            "persons_imported": 0,
            "places_imported": 0,
            "edges_created": 0,
            "errors": [],
        }
        self._person_cache: Dict[str, str] = {}  # name -> record_id
        self._place_cache: Dict[str, str] = {}

    async def import_all(
        self,
        registry: QuranStoryRegistry = None,
        manifest_path: Path = None,
        run_id: str = None,
    ) -> Dict[str, Any]:
        """
        Import all stories from registry to SurrealDB.

        Args:
            registry: Pre-loaded registry (optional)
            manifest_path: Path to stories.json (used if registry not provided)
            run_id: Optional ingest run ID for tracking

        Returns:
            Import metrics and summary
        """
        # Load registry if not provided
        if registry is None:
            registry = QuranStoryRegistry()
            if manifest_path is None:
                # Default path
                manifest_path = Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json"
            registry.load_from_manifest(manifest_path)

        run_id = run_id or f"import_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting story import: run_id={run_id}, stories={len(registry.stories)}")

        # Reset metrics
        self.metrics = {
            "run_id": run_id,
            "started_at": datetime.utcnow().isoformat(),
            "stories_imported": 0,
            "events_imported": 0,
            "persons_imported": 0,
            "places_imported": 0,
            "edges_created": 0,
            "errors": [],
        }

        try:
            # Import in order: persons -> places -> stories -> events -> edges
            for story in registry.stories.values():
                await self._import_persons(story)
                await self._import_places(story)

            for story in registry.stories.values():
                await self._import_story(story, run_id)

            # Create inter-event edges (NEXT)
            for story in registry.stories.values():
                await self._create_next_edges(story)

        except Exception as e:
            self.metrics["errors"].append(str(e))
            logger.error(f"Import failed: {e}")
            raise

        self.metrics["finished_at"] = datetime.utcnow().isoformat()
        logger.info(f"Import complete: {self.metrics}")

        return self.metrics

    async def _import_persons(self, story: StoryRegistryEntry):
        """Import persons from a story."""
        for person in story.main_persons:
            person_id = sanitize_id(person.id)

            if person_id in self._person_cache:
                continue

            data = {
                "name_ar": person.name_ar,
                "name_en": person.name_en,
                "kind": "prophet" if person.is_prophet else "named",
                "aliases_ar": person.aliases_ar,
                "aliases_en": person.aliases_en,
                "_hash": content_hash(f"{person.name_ar}{person.name_en}"),
                "_source": "registry_import",
            }

            try:
                await self.kg.upsert("person", person_id, data)
                self._person_cache[person_id] = f"person:{person_id}"
                self.metrics["persons_imported"] += 1
            except Exception as e:
                self.metrics["errors"].append(f"Person {person_id}: {e}")

    async def _import_places(self, story: StoryRegistryEntry):
        """Import places from a story."""
        for place in story.places:
            place_id = sanitize_id(place.name_en)

            if place_id in self._place_cache:
                continue

            data = {
                "name_ar": place.name_ar,
                "name_en": place.name_en,
                "basis": place.basis.value if hasattr(place.basis, 'value') else str(place.basis),
                "_hash": content_hash(f"{place.name_ar}{place.name_en}"),
                "_source": "registry_import",
            }

            try:
                await self.kg.upsert("place", place_id, data)
                self._place_cache[place_id] = f"place:{place_id}"
                self.metrics["places_imported"] += 1
            except Exception as e:
                self.metrics["errors"].append(f"Place {place_id}: {e}")

    async def _import_story(self, story: StoryRegistryEntry, run_id: str):
        """Import a story cluster and its events."""
        cluster_id = story.slug or story.id.replace("story_", "")

        # Build ayah_spans from primary ranges
        ayah_spans = [
            {
                "sura": r.sura,
                "ayah_start": r.start,
                "ayah_end": r.end,
                "verse_reference": r.reference,
            }
            for r in story.primary_ayah_ranges
        ]

        # Story cluster data
        cluster_data = {
            "slug": cluster_id,
            "title_ar": story.title_ar,
            "title_en": story.title_en,
            "short_title_ar": story.short_title_ar,
            "short_title_en": story.short_title_en,
            "category": story.category.value,
            "era": story.era,
            "era_basis": story.era_basis.value if story.era_basis else None,
            "main_persons": [p.name_en for p in story.main_persons],
            "groups": story.nations,
            "places": [{"name_ar": p.name_ar, "name_en": p.name_en} for p in story.places],
            "tags": story.themes,
            "ayah_spans": ayah_spans,
            "primary_sura": story.primary_ayah_ranges[0].sura if story.primary_ayah_ranges else None,
            "total_verses": story.total_verses,
            "suras_mentioned": story.suras_mentioned,
            "summary_ar": story.summary_ar,
            "summary_en": story.summary_en,
            "lessons_ar": story.lessons_ar,
            "lessons_en": story.lessons_en,
            "is_complete": story.is_complete,
            "event_count": len(story.events),
            "_hash": content_hash(f"{story.id}{story.title_ar}"),
            "_source": "registry_import",
            "_ingest_run_id": run_id,
        }

        try:
            await self.kg.upsert("story_cluster", cluster_id, cluster_data)
            self.metrics["stories_imported"] += 1

            # Import events
            for event in story.events:
                await self._import_event(story, event, cluster_id, run_id)

        except Exception as e:
            self.metrics["errors"].append(f"Story {story.id}: {e}")

    async def _import_event(
        self,
        story: StoryRegistryEntry,
        event: StoryEvent,
        cluster_id: str,
        run_id: str,
    ):
        """Import a story event."""
        event_id = event.id

        # Convert evidence to serializable format
        evidence_data = [
            {
                "source_id": ev.source_id,
                "chunk_id": ev.chunk_id,
                "ayah_ref": ev.ayah_ref,
            }
            for ev in event.evidence
        ]

        event_data = {
            "cluster_id": f"story_cluster:{cluster_id}",
            "slug": event_id,
            "title_ar": event.title_ar,
            "title_en": event.title_en,
            "narrative_role": event.narrative_role,
            "chronological_index": event.chronological_index,
            "is_entry_point": event.is_entry_point,
            "sura_no": event.ayah_range.sura,
            "ayah_start": event.ayah_range.start,
            "ayah_end": event.ayah_range.end,
            "verse_reference": event.ayah_range.reference,
            "summary_ar": event.summary_ar,
            "summary_en": event.summary_en,
            "semantic_tags": event.semantic_tags,
            "evidence": evidence_data,
            "_hash": content_hash(f"{event_id}{event.title_ar}"),
            "_source": "registry_import",
            "_ingest_run_id": run_id,
        }

        try:
            await self.kg.upsert("story_event", event_id, event_data)
            self.metrics["events_imported"] += 1

            # Create HAS_EVENT edge from cluster to event
            await self.kg.create_edge(
                "has_event",
                f"story_cluster:{cluster_id}",
                f"story_event:{event_id}",
                {"order": event.chronological_index},
            )
            self.metrics["edges_created"] += 1

            # Create INVOLVES edges for persons
            for person in story.main_persons:
                person_record_id = self._person_cache.get(sanitize_id(person.id))
                if person_record_id:
                    await self.kg.create_edge(
                        "involves",
                        f"story_event:{event_id}",
                        person_record_id,
                        {"role": "main"},
                    )
                    self.metrics["edges_created"] += 1

        except Exception as e:
            self.metrics["errors"].append(f"Event {event_id}: {e}")

    async def _create_next_edges(self, story: StoryRegistryEntry):
        """Create NEXT edges between consecutive events."""
        if len(story.events) < 2:
            return

        # Sort events by chronological index
        sorted_events = sorted(story.events, key=lambda e: e.chronological_index)

        for i in range(len(sorted_events) - 1):
            from_event = sorted_events[i]
            to_event = sorted_events[i + 1]

            try:
                await self.kg.create_edge(
                    "next",
                    f"story_event:{from_event.id}",
                    f"story_event:{to_event.id}",
                    {"gap_type": None},
                )
                self.metrics["edges_created"] += 1
            except Exception as e:
                # Edge may already exist
                pass


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def run_import(manifest_path: Path = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Run story import as standalone operation.

    Usage:
        python -c "import asyncio; from app.kg.story_importer import run_import; asyncio.run(run_import())"
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    importer = StoryImporter()
    return await importer.import_all(manifest_path=manifest_path)
