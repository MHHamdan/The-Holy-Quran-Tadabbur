#!/usr/bin/env python3
"""
Fix event index gaps in stories.json manifest.

PR1: Normalize narrative_order to be strictly sequential (1..N) for each story.

The issue: Multiple segments within a story have duplicate narrative_order values
because they describe the same event from different surahs/perspectives.

The fix: Renumber all segments strictly sequentially based on their array position.

Usage:
    python scripts/verify/fix_event_indices.py [--dry-run] [--verbose]
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List


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


def check_index_gaps(story: Dict[str, Any]) -> tuple[bool, List[int], List[int]]:
    """
    Check if a story has index gaps or duplicates.

    Returns:
        (has_issues, actual_indices, expected_indices)
    """
    segments = story.get('segments', [])
    if not segments:
        return False, [], []

    actual = [seg.get('narrative_order', i+1) for i, seg in enumerate(segments)]
    expected = list(range(1, len(segments) + 1))

    has_issues = actual != expected
    return has_issues, actual, expected


def fix_story_indices(story: Dict[str, Any]) -> bool:
    """
    Fix narrative_order indices for a story.

    Returns True if changes were made.
    """
    segments = story.get('segments', [])
    if not segments:
        return False

    changed = False
    for i, seg in enumerate(segments, start=1):
        if seg.get('narrative_order') != i:
            seg['narrative_order'] = i
            changed = True

    return changed


def main():
    parser = argparse.ArgumentParser(description='Fix event index gaps in stories manifest')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    # Find and load manifest
    manifest_path = find_manifest()
    print(f"📂 Found manifest: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check all stories for issues
    stories_with_issues = []
    for story in data.get('stories', []):
        has_issues, actual, expected = check_index_gaps(story)
        if has_issues:
            stories_with_issues.append({
                'id': story['id'],
                'name_ar': story.get('name_ar', ''),
                'actual': actual,
                'expected': expected
            })

    if not stories_with_issues:
        print("✅ No index gaps found - all stories have sequential indices")
        return 0

    print(f"\n⚠️  Found {len(stories_with_issues)} stories with index gaps:\n")

    for issue in stories_with_issues:
        print(f"  📖 {issue['id']} ({issue['name_ar']})")
        if args.verbose:
            print(f"      Actual:   {issue['actual']}")
            print(f"      Expected: {issue['expected']}")

    if args.dry_run:
        print("\n🔍 Dry run - no changes made")
        return 0

    # Apply fixes
    print("\n🔧 Applying fixes...")

    fixed_count = 0
    for story in data.get('stories', []):
        if fix_story_indices(story):
            fixed_count += 1
            if args.verbose:
                print(f"  ✓ Fixed {story['id']}")

    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fixed {fixed_count} stories")
    print(f"📁 Saved to {manifest_path}")

    # Verify fixes
    print("\n🔍 Verifying fixes...")
    remaining_issues = []
    for story in data.get('stories', []):
        has_issues, actual, expected = check_index_gaps(story)
        if has_issues:
            remaining_issues.append(story['id'])

    if remaining_issues:
        print(f"❌ Still have issues in: {remaining_issues}")
        return 1

    print("✅ All stories now have sequential indices")
    return 0


if __name__ == '__main__':
    exit(main())
