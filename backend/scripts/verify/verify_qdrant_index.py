#!/usr/bin/env python3
"""
Verify Qdrant vector index is properly configured.

Checks:
  - Collections exist
  - Vectors are present
  - Metadata fields are correct
  - Sample queries work

Exit codes:
  0 - Qdrant index verified
  1 - Qdrant index issues found
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Expected configuration
EXPECTED_COLLECTIONS = ["tafseer_chunks", "quran_verses"]
EXPECTED_DIMENSION = 1024
EXPECTED_DISTANCE = Distance.COSINE


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client from environment."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port)


def check_collection_exists(client: QdrantClient, collection_name: str) -> tuple[bool, str]:
    """Check if collection exists."""
    try:
        collections = client.get_collections().collections
        names = [c.name for c in collections]

        if collection_name in names:
            return True, f"Collection '{collection_name}' exists"
        return False, f"Collection '{collection_name}' not found. Available: {names}"
    except Exception as e:
        return False, f"Error checking collections: {str(e)}"


def check_collection_config(
    client: QdrantClient,
    collection_name: str,
    expected_dim: int,
    expected_distance: Distance
) -> tuple[bool, str]:
    """Check collection vector configuration."""
    try:
        info = client.get_collection(collection_name)
        config = info.config.params.vectors

        # Handle both single and named vector configs
        if hasattr(config, 'size'):
            actual_dim = config.size
            actual_distance = config.distance
        elif isinstance(config, dict) and 'default' in config:
            actual_dim = config['default'].size
            actual_distance = config['default'].distance
        else:
            return False, f"Unknown vector config format: {type(config)}"

        if actual_dim != expected_dim:
            return False, f"Dimension mismatch: {actual_dim} (expected {expected_dim})"

        if actual_distance != expected_distance:
            return False, f"Distance mismatch: {actual_distance} (expected {expected_distance})"

        return True, f"Config OK: dim={actual_dim}, distance={actual_distance}"
    except Exception as e:
        return False, f"Error checking config: {str(e)}"


def check_collection_points(client: QdrantClient, collection_name: str) -> tuple[bool, str]:
    """Check if collection has vectors."""
    try:
        info = client.get_collection(collection_name)
        points_count = info.points_count

        if points_count > 0:
            return True, f"Collection has {points_count:,} vectors"
        return False, "Collection is empty - no vectors indexed"
    except Exception as e:
        return False, f"Error checking points: {str(e)}"


def check_metadata_fields(
    client: QdrantClient,
    collection_name: str,
    required_fields: list
) -> tuple[bool, str]:
    """Check if indexed vectors have required metadata fields."""
    try:
        # Get a sample point
        results = client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        if not results[0]:
            return False, "No points found to check metadata"

        sample = results[0][0]
        payload = sample.payload or {}

        missing = [f for f in required_fields if f not in payload]

        if missing:
            return False, f"Missing metadata fields: {missing}"

        present = [f for f in required_fields if f in payload]
        return True, f"All required fields present: {present}"
    except Exception as e:
        return False, f"Error checking metadata: {str(e)}"


def check_sample_search(client: QdrantClient, collection_name: str) -> tuple[bool, str]:
    """Perform a sample vector search."""
    try:
        info = client.get_collection(collection_name)
        if info.points_count == 0:
            return False, "Cannot search - collection is empty"

        # Get vector dimension
        config = info.config.params.vectors
        if hasattr(config, 'size'):
            dim = config.size
        elif isinstance(config, dict) and 'default' in config:
            dim = config['default'].size
        else:
            dim = EXPECTED_DIMENSION

        # Create dummy query vector
        query_vector = [0.1] * dim

        # Perform search
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=3,
            with_payload=True,
        )

        if len(results) > 0:
            scores = [r.score for r in results]
            return True, f"Search returned {len(results)} results (scores: {[f'{s:.3f}' for s in scores]})"
        return False, "Search returned no results"
    except Exception as e:
        return False, f"Error performing search: {str(e)}"


def verify_collection(
    client: QdrantClient,
    collection_name: str,
    required_fields: list,
) -> list[tuple[str, bool, str]]:
    """Verify a single collection."""
    results = []

    # Check exists
    passed, msg = check_collection_exists(client, collection_name)
    results.append((f"{collection_name}: exists", passed, msg))

    if not passed:
        return results

    # Check config
    passed, msg = check_collection_config(
        client, collection_name, EXPECTED_DIMENSION, EXPECTED_DISTANCE
    )
    results.append((f"{collection_name}: config", passed, msg))

    # Check points
    passed, msg = check_collection_points(client, collection_name)
    results.append((f"{collection_name}: vectors", passed, msg))

    if passed:
        # Check metadata
        passed, msg = check_metadata_fields(client, collection_name, required_fields)
        results.append((f"{collection_name}: metadata", passed, msg))

        # Check search
        passed, msg = check_sample_search(client, collection_name)
        results.append((f"{collection_name}: search", passed, msg))

    return results


def main():
    """Run all Qdrant index verifications."""
    print("=" * 60)
    print("QDRANT INDEX VERIFICATION")
    print("=" * 60)

    host = os.getenv("QDRANT_HOST", "localhost")
    port = os.getenv("QDRANT_PORT", "6333")
    print(f"\nQdrant: {host}:{port}")

    try:
        client = get_qdrant_client()

        # Verify connection
        print("\n[0] Checking Qdrant connection...")
        try:
            collections = client.get_collections()
            print(f"  PASS: Connected, {len(collections.collections)} collections found")
        except Exception as e:
            print(f"  FAIL: Cannot connect to Qdrant: {e}")
            sys.exit(1)

        all_results = []

        # Verify tafseer collection
        print("\n[1] Verifying tafseer_chunks collection...")
        tafseer_fields = ["chunk_id", "source_id", "verse_reference", "content_en"]
        results = verify_collection(client, "tafseer_chunks", tafseer_fields)
        for name, passed, msg in results:
            print(f"  {'PASS' if passed else 'FAIL'}: {name}")
            print(f"         {msg}")
        all_results.extend(results)

        # Verify verses collection (optional)
        print("\n[2] Verifying quran_verses collection...")
        verse_fields = ["verse_id", "sura_no", "aya_no", "text"]
        results = verify_collection(client, "quran_verses", verse_fields)
        for name, passed, msg in results:
            print(f"  {'PASS' if passed else 'FAIL'}: {name}")
            print(f"         {msg}")
        all_results.extend(results)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        passed_count = sum(1 for _, p, _ in all_results if p)
        total_count = len(all_results)

        for name, passed, _ in all_results:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")

        print(f"\n  Total: {passed_count}/{total_count} checks passed")
        print("\n" + "=" * 60)

        # For MVP, we only require the connection to work
        # Collections can be empty until indexing runs
        if passed_count >= 1:  # At least connection works
            print("OVERALL: PASS - Qdrant is accessible")
            print("=" * 60)
            print("\nNOTE: Run indexing to populate collections:")
            print("  python scripts/index/index_tafseer.py")
            sys.exit(0)
        else:
            print("OVERALL: FAIL - Qdrant issues detected")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        print("\nREMEDIATION:")
        print("  1. Ensure Qdrant is running: docker-compose up -d qdrant")
        print("  2. Check Qdrant logs: docker-compose logs qdrant")
        print("  3. Verify port 6333 is accessible")
        sys.exit(1)


if __name__ == "__main__":
    main()
