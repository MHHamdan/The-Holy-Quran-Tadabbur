#!/usr/bin/env python3
"""
Populate evidence pointers for Quranic stories.

PR2/PR4: Auto-populate stories with evidence pointers using the resolver.
Evidence chunk IDs follow pattern: {source_id}:{sura}:{ayah_start}-{ayah_end}

DETERMINISM GUARANTEE:
======================
- Running this script twice produces IDENTICAL output (same evidence IDs)
- Selection heuristic: round-robin across 4 sources for diversity
- Each segment gets evidence from 2 sources (MIN_DISTINCT_SOURCES)

MULTI-SOURCE COVERAGE:
======================
- Sources: ibn_kathir, tabari, qurtubi, saadi
- Round-robin selection ensures even distribution
- No bias to any single tafsir source

Usage:
    python scripts/verify/populate_evidence.py [--dry-run] [--verbose] [--review] [--multi-source]

Options:
    --dry-run       Show what would be changed without modifying files
    --verbose       Show detailed output for each story
    --review        Mark all auto-populated evidence as needing review
    --multi-source  Use multi-source diversity (2 sources per segment)
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Available tafsir sources
TAFSIR_SOURCES = ["ibn_kathir", "tabari", "qurtubi", "saadi"]


def find_manifest() -> Path:
    """Find the stories.json manifest file."""
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data" / "manifests" / "stories.json",
        Path(__file__).parent.parent.parent / "data" / "manifests" / "stories.json",
        Path("/home/mhamdan/tadabbur/data/manifests/stories.json"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError("Could not find stories.json manifest")


def generate_evidence_pointer(
    source_id: str,
    sura: int,
    ayah_start: int,
    ayah_end: int,
    needs_review: bool = False
) -> Dict[str, Any]:
    """Generate an evidence pointer for a segment (DETERMINISTIC)."""
    if ayah_start == ayah_end:
        chunk_id = f"{source_id}:{sura}:{ayah_start}"
        ayah_ref = f"{sura}:{ayah_start}"
    else:
        chunk_id = f"{source_id}:{sura}:{ayah_start}-{ayah_end}"
        ayah_ref = f"{sura}:{ayah_start}-{ayah_end}"

    return {
        "source_id": source_id,
        "chunk_id": chunk_id,
        "ayah_ref": ayah_ref,
        "needs_review": needs_review
    }


def get_sources_for_index(index: int, multi_source: bool = True) -> List[str]:
    """
    Get sources for a given segment index (DETERMINISTIC round-robin).

    Args:
        index: Segment index (for round-robin selection)
        multi_source: If True, return 2 sources; otherwise return 1

    Returns:
        List of source IDs to use
    """
    if not multi_source:
        return [TAFSIR_SOURCES[0]]  # Default to ibn_kathir

    # Round-robin selection of 2 sources
    primary_idx = index % len(TAFSIR_SOURCES)
    secondary_idx = (index + 1) % len(TAFSIR_SOURCES)
    return [TAFSIR_SOURCES[primary_idx], TAFSIR_SOURCES[secondary_idx]]


def populate_story_evidence(
    story: Dict[str, Any],
    story_index: int = 0,
    needs_review: bool = False,
    multi_source: bool = True
) -> Tuple[int, int, Dict[str, int]]:
    """
    Populate evidence for a story and its segments with multi-source diversity.

    Returns:
        (story_evidence_added, segment_evidence_added, source_counts)
    """
    story_evidence_added = 0
    segment_evidence_added = 0
    source_counts: Dict[str, int] = {}

    # Initialize evidence array if not present
    if 'evidence' not in story:
        story['evidence'] = []

    # Add evidence for each segment
    segments = story.get('segments', [])
    for seg_idx, seg in enumerate(segments):
        sura = seg.get('sura_no')
        ayah_start = seg.get('aya_start')
        ayah_end = seg.get('aya_end')

        if not all([sura, ayah_start, ayah_end]):
            continue

        # Initialize segment evidence if needed
        if 'evidence' not in seg:
            seg['evidence'] = []

        # Get sources for this segment (deterministic based on global index)
        global_index = story_index * 100 + seg_idx
        sources = get_sources_for_index(global_index, multi_source)

        for source_id in sources:
            # Create evidence pointer for segment
            evidence = generate_evidence_pointer(
                source_id, sura, ayah_start, ayah_end, needs_review
            )

            # Check if evidence already exists (by chunk_id)
            existing_ids = {e.get('chunk_id') for e in seg.get('evidence', [])}
            if evidence['chunk_id'] not in existing_ids:
                seg['evidence'].append(evidence)
                segment_evidence_added += 1
                source_counts[source_id] = source_counts.get(source_id, 0) + 1

            # Also add to story-level evidence if not already present
            story_existing_ids = {e.get('chunk_id') for e in story.get('evidence', [])}
            if evidence['chunk_id'] not in story_existing_ids:
                story['evidence'].append(evidence)
                story_evidence_added += 1

    return story_evidence_added, segment_evidence_added, source_counts


def main():
    parser = argparse.ArgumentParser(description='Populate evidence pointers in stories manifest')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--review', action='store_true', help='Mark evidence as needing review')
    parser.add_argument('--multi-source', action='store_true', default=True,
                        help='Use multi-source diversity (2 sources per segment)')
    parser.add_argument('--single-source', dest='multi_source', action='store_false',
                        help='Use single source only (ibn_kathir)')
    args = parser.parse_args()

    # Find and load manifest
    manifest_path = find_manifest()
    print(f"📂 Found manifest: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_stories = len(data.get('stories', []))
    stories_updated = 0
    total_story_evidence = 0
    total_segment_evidence = 0
    aggregate_source_counts: Dict[str, int] = {}

    print(f"📚 Processing {total_stories} stories...")
    if args.multi_source:
        print(f"📖 Using MULTI-SOURCE diversity: {', '.join(TAFSIR_SOURCES)}")
    else:
        print(f"📖 Using single source: ibn_kathir")
    if args.review:
        print("⚠️  Marking all evidence as needing review")
    print()

    for story_idx, story in enumerate(data.get('stories', [])):
        story_id = story.get('id', 'unknown')
        story_ev, seg_ev, source_counts = populate_story_evidence(
            story,
            story_index=story_idx,
            needs_review=args.review,
            multi_source=args.multi_source
        )

        if story_ev > 0 or seg_ev > 0:
            stories_updated += 1
            total_story_evidence += story_ev
            total_segment_evidence += seg_ev
            for src, cnt in source_counts.items():
                aggregate_source_counts[src] = aggregate_source_counts.get(src, 0) + cnt

            if args.verbose:
                print(f"  ✓ {story_id}: +{story_ev} story, +{seg_ev} segment evidence")

    print()
    print("📊 Summary:")
    print(f"   Stories updated: {stories_updated}/{total_stories}")
    print(f"   Story-level evidence added: {total_story_evidence}")
    print(f"   Segment-level evidence added: {total_segment_evidence}")
    print()
    print("📈 Source distribution:")
    for src, cnt in sorted(aggregate_source_counts.items()):
        print(f"   {src}: {cnt} chunks")

    if args.dry_run:
        print("\n🔍 Dry run - no changes saved")
        return 0

    if stories_updated == 0:
        print("\n✅ No changes needed - all stories already have evidence")
        return 0

    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved to {manifest_path}")
    return 0


if __name__ == '__main__':
    exit(main())
