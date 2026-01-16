#!/usr/bin/env python3
"""
Verify chunking invariants for tafseer data.

Validates:
1. No chunks cross surah boundaries
2. All chunks have valid ayah ranges
3. Raw text is preserved and hash matches
4. Chunk IDs are deterministic

Exit codes:
  0 - All chunks valid
  1 - Validation failed
  2 - No data to verify
"""
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFESTS_DIR = DATA_DIR / "manifests"
RAW_DIR = DATA_DIR / "raw"

# Add parent to path for chunker import
sys.path.insert(0, str(SCRIPT_DIR.parent))

from ingest.ingest_tafseer import AyahAnchoredChunker, TafseerChunk


@dataclass
class ChunkingTestResult:
    """Result of a chunking test."""
    test_name: str
    passed: bool
    message: str
    details: Optional[list] = None


def create_test_data() -> list[dict]:
    """Create test data with known edge cases."""
    return [
        # Surah 1 (Al-Fatiha) - 7 verses
        {"surah": 1, "ayah": 1, "text": "This is the tafseer for verse 1 of Al-Fatiha. " * 20},
        {"surah": 1, "ayah": 2, "text": "This is the tafseer for verse 2. " * 30},
        {"surah": 1, "ayah": 3, "text": "Verse 3 tafseer content here. " * 25},
        {"surah": 1, "ayah": 4, "text": "Master of the Day of Judgment explanation. " * 20},
        {"surah": 1, "ayah": 5, "text": "You alone we worship. " * 15},
        {"surah": 1, "ayah": 6, "text": "Guide us to the straight path. " * 25},
        {"surah": 1, "ayah": 7, "text": "The path of those You have blessed. " * 20},

        # Surah 2 (Al-Baqarah) - first few verses
        {"surah": 2, "ayah": 1, "text": "Alif Lam Meem explanation. " * 15},
        {"surah": 2, "ayah": 2, "text": "This is the Book, no doubt. " * 40},
        {"surah": 2, "ayah": 3, "text": "Those who believe in the unseen. " * 35},
        {"surah": 2, "ayah": 4, "text": "And who believe in what was revealed. " * 30},
        {"surah": 2, "ayah": 5, "text": "Those are upon guidance. " * 25},

        # Surah 114 (An-Nas) - to test surah boundary
        {"surah": 114, "ayah": 1, "text": "Say I seek refuge in the Lord of mankind. " * 20},
        {"surah": 114, "ayah": 2, "text": "The King of mankind. " * 15},
        {"surah": 114, "ayah": 3, "text": "The God of mankind. " * 15},
    ]


def test_no_cross_surah_chunks(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that no chunks cross surah boundaries."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en",
        "methodology": "test",
        "era": "test"
    }

    chunks = chunker.chunk_verses(test_data, source)

    # Check each chunk has single surah
    violations = []
    for i, chunk in enumerate(chunks):
        # All entries in raw_text should be from same surah
        lines = chunk.raw_text.split("\n---\n")
        surahs_in_chunk = set()
        for line in lines:
            if line.startswith("["):
                # Parse [surah:ayah]
                ref = line.split("]")[0].strip("[")
                if ":" in ref:
                    surah = int(ref.split(":")[0])
                    surahs_in_chunk.add(surah)

        if len(surahs_in_chunk) > 1:
            violations.append(f"Chunk {i}: Contains surahs {surahs_in_chunk}")

    if violations:
        return ChunkingTestResult(
            test_name="no_cross_surah_chunks",
            passed=False,
            message=f"Found {len(violations)} chunks crossing surah boundaries",
            details=violations
        )

    return ChunkingTestResult(
        test_name="no_cross_surah_chunks",
        passed=True,
        message=f"All {len(chunks)} chunks respect surah boundaries"
    )


def test_valid_ayah_ranges(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that all chunks have valid ayah ranges."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en"
    }

    chunks = chunker.chunk_verses(test_data, source)

    violations = []
    for i, chunk in enumerate(chunks):
        if chunk.ayah_start > chunk.ayah_end:
            violations.append(f"Chunk {i}: ayah_start ({chunk.ayah_start}) > ayah_end ({chunk.ayah_end})")

        if chunk.ayah_start < 1:
            violations.append(f"Chunk {i}: ayah_start ({chunk.ayah_start}) < 1")

        if chunk.surah_number < 1 or chunk.surah_number > 114:
            violations.append(f"Chunk {i}: Invalid surah_number ({chunk.surah_number})")

    if violations:
        return ChunkingTestResult(
            test_name="valid_ayah_ranges",
            passed=False,
            message=f"Found {len(violations)} invalid ayah ranges",
            details=violations
        )

    return ChunkingTestResult(
        test_name="valid_ayah_ranges",
        passed=True,
        message=f"All {len(chunks)} chunks have valid ayah ranges"
    )


def test_raw_text_hash_integrity(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that raw text hash matches content."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en"
    }

    chunks = chunker.chunk_verses(test_data, source)

    violations = []
    for i, chunk in enumerate(chunks):
        computed_hash = hashlib.sha256(chunk.raw_text.encode('utf-8')).hexdigest()
        if computed_hash != chunk.raw_text_hash:
            violations.append(f"Chunk {i}: Hash mismatch (expected {chunk.raw_text_hash[:16]}..., got {computed_hash[:16]}...)")

    if violations:
        return ChunkingTestResult(
            test_name="raw_text_hash_integrity",
            passed=False,
            message=f"Found {len(violations)} hash mismatches",
            details=violations
        )

    return ChunkingTestResult(
        test_name="raw_text_hash_integrity",
        passed=True,
        message=f"All {len(chunks)} chunks have valid raw text hashes"
    )


def test_deterministic_chunk_ids(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that chunk IDs are deterministic."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en"
    }

    # Generate chunks twice
    chunks1 = chunker.chunk_verses(test_data, source)
    chunks2 = chunker.chunk_verses(test_data, source)

    if len(chunks1) != len(chunks2):
        return ChunkingTestResult(
            test_name="deterministic_chunk_ids",
            passed=False,
            message=f"Chunk count differs: {len(chunks1)} vs {len(chunks2)}"
        )

    mismatches = []
    for i, (c1, c2) in enumerate(zip(chunks1, chunks2)):
        if c1.chunk_id != c2.chunk_id:
            mismatches.append(f"Chunk {i}: ID changed from {c1.chunk_id} to {c2.chunk_id}")

    if mismatches:
        return ChunkingTestResult(
            test_name="deterministic_chunk_ids",
            passed=False,
            message=f"Found {len(mismatches)} non-deterministic chunk IDs",
            details=mismatches
        )

    return ChunkingTestResult(
        test_name="deterministic_chunk_ids",
        passed=True,
        message=f"All {len(chunks1)} chunk IDs are deterministic"
    )


def test_raw_text_preservation(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that raw text is preserved with verse references."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en"
    }

    chunks = chunker.chunk_verses(test_data, source)

    violations = []
    for i, chunk in enumerate(chunks):
        # Raw text should contain verse references
        if not chunk.raw_text:
            violations.append(f"Chunk {i}: raw_text is empty")
            continue

        # Check format: [surah:ayah] text
        lines = chunk.raw_text.split("\n---\n")
        for line in lines:
            if not line.startswith("[") or "]" not in line:
                violations.append(f"Chunk {i}: Missing verse reference format in raw_text")
                break

    if violations:
        return ChunkingTestResult(
            test_name="raw_text_preservation",
            passed=False,
            message=f"Found {len(violations)} raw text issues",
            details=violations[:5]  # Limit details
        )

    return ChunkingTestResult(
        test_name="raw_text_preservation",
        passed=True,
        message=f"All {len(chunks)} chunks preserve raw text with verse references"
    )


def test_word_count_limit(chunker: AyahAnchoredChunker, test_data: list[dict]) -> ChunkingTestResult:
    """Test that chunks respect max word limit (with reasonable tolerance)."""
    source = {
        "id": "test_source",
        "name_ar": "تفسير اختباري",
        "name_en": "Test Tafsir",
        "language": "en"
    }

    chunks = chunker.chunk_verses(test_data, source)

    max_words = chunker.max_words
    tolerance = max_words * 0.2  # 20% tolerance for edge cases

    violations = []
    for i, chunk in enumerate(chunks):
        if chunk.word_count > max_words + tolerance:
            violations.append(f"Chunk {i}: {chunk.word_count} words exceeds limit {max_words}")

    if violations:
        return ChunkingTestResult(
            test_name="word_count_limit",
            passed=False,
            message=f"Found {len(violations)} chunks exceeding word limit",
            details=violations
        )

    return ChunkingTestResult(
        test_name="word_count_limit",
        passed=True,
        message=f"All {len(chunks)} chunks respect word limit ({max_words})"
    )


def main():
    """Run all chunking verification tests."""
    print("=" * 60)
    print("CHUNKING VERIFICATION")
    print("=" * 60)

    # Load config
    manifest_path = MANIFESTS_DIR / "tafseer_sources.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        config = manifest.get("ingestion_config", {})
    else:
        config = {"max_chunk_words": 500, "preserve_raw_text": True, "prevent_cross_surah": True}

    print(f"\nConfig: {json.dumps(config, indent=2)}")

    # Create chunker
    chunker = AyahAnchoredChunker(config)

    # Create test data
    test_data = create_test_data()
    print(f"\nTest data: {len(test_data)} entries across 3 surahs\n")

    # Run tests
    tests = [
        test_no_cross_surah_chunks,
        test_valid_ayah_ranges,
        test_raw_text_hash_integrity,
        test_deterministic_chunk_ids,
        test_raw_text_preservation,
        test_word_count_limit,
    ]

    results = []
    for test_fn in tests:
        result = test_fn(chunker, test_data)
        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.test_name}")
        print(f"       {result.message}")
        if result.details:
            for detail in result.details[:3]:
                print(f"         - {detail}")
            if len(result.details) > 3:
                print(f"         ... and {len(result.details) - 3} more")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if not r.passed:
                print(f"    - {r.test_name}")

    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
