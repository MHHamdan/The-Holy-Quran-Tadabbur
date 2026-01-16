#!/usr/bin/env python3
"""
System Integrity Verification Script - Final Acceptance Gate

This script is the FINAL verification before system acceptance.
ALL checks must pass before the system is considered production-ready.

Checks performed:
1. Provenance verification for all tafseer sources
2. No orphaned chunks (missing source_id)
3. Embedding dimension consistency
4. RAG language policy compliance
5. Data quantity thresholds met
6. Confidence scoring operational

Exit codes:
  0 - All checks passed (SYSTEM ACCEPTED)
  1 - One or more checks failed (SYSTEM REJECTED)
  2 - Configuration error

Usage:
  python scripts/verify/verify_system_integrity.py
  python scripts/verify/verify_system_integrity.py --verbose
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient

# Import acceptance criteria
from app.core.acceptance import (
    MIN_VERSES,
    MIN_TAFSEER_CHUNKS,
    MIN_TAFSEER_SOURCES,
    MIN_STORIES,
    MIN_EVIDENCE_CHUNKS,
    MIN_EVIDENCE_SOURCES,
    EXPECTED_EMBEDDING_DIMENSION,
    QDRANT_COLLECTION,
    RAG_LANGUAGES,
    REFUSAL_THRESHOLD,
    get_acceptance_summary,
)

# Import models
from app.models.quran import QuranVerse
from app.models.tafseer import TafseerSource, TafseerChunk
from app.models.story import Story, StorySegment

# Import RAG components for verification
from app.rag.types import RAG_SUPPORTED_LANGUAGES
from app.rag.confidence import (
    confidence_scorer,
    run_refusal_tests,
    MIN_DISTINCT_CHUNKS,
    MIN_DISTINCT_SOURCES,
)


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def get_qdrant_client() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port, check_compatibility=False)


class IntegrityChecker:
    """System integrity verification."""

    def __init__(self, session: Session, qdrant: QdrantClient, verbose: bool = False):
        self.session = session
        self.qdrant = qdrant
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"    {message}")

    def check(self, name: str, condition: bool, error_msg: str) -> bool:
        """Record a check result."""
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
            return True
        else:
            self.failed += 1
            self.errors.append(error_msg)
            print(f"  [FAIL] {name}: {error_msg}")
            return False

    def warn(self, name: str, condition: bool, warn_msg: str) -> bool:
        """Record a warning (non-fatal)."""
        if condition:
            return True
        else:
            self.warnings += 1
            print(f"  [WARN] {name}: {warn_msg}")
            return False

    # =========================================================================
    # CHECK 1: Provenance Verification
    # =========================================================================
    def check_provenance(self) -> bool:
        """Verify all tafseer sources have valid provenance."""
        print("\n[1/6] PROVENANCE VERIFICATION")

        sources = self.session.execute(select(TafseerSource)).scalars().all()

        if not sources:
            return self.check("Sources exist", False, "No tafseer sources found")

        self.check("Sources loaded", True, "")
        self.log(f"Found {len(sources)} sources")

        all_valid = True
        verified_count = 0

        for source in sources:
            has_provenance = source.has_valid_provenance
            if has_provenance:
                verified_count += 1
            else:
                self.log(f"  {source.id}: missing provenance")
                all_valid = False

        return self.check(
            "All sources have provenance",
            all_valid,
            f"Only {verified_count}/{len(sources)} sources have valid provenance"
        )

    # =========================================================================
    # CHECK 2: No Orphaned Chunks
    # =========================================================================
    def check_orphaned_chunks(self) -> bool:
        """Verify no chunks are missing source_id."""
        print("\n[2/6] ORPHANED CHUNK CHECK")

        # Check for chunks without source
        orphan_count = self.session.execute(
            select(func.count(TafseerChunk.id))
            .outerjoin(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
            .where(TafseerSource.id == None)
        ).scalar()

        # Check for chunks without chunk_id
        no_chunk_id = self.session.execute(
            select(func.count(TafseerChunk.id))
            .where(TafseerChunk.chunk_id == None)
        ).scalar()

        self.check(
            "No orphaned chunks",
            orphan_count == 0,
            f"{orphan_count} chunks have no valid source"
        )

        return self.check(
            "All chunks have chunk_id",
            no_chunk_id == 0,
            f"{no_chunk_id} chunks missing chunk_id"
        )

    # =========================================================================
    # CHECK 3: Embedding Dimension Consistency
    # =========================================================================
    def check_embedding_dimension(self) -> bool:
        """Verify Qdrant collection has correct dimension."""
        print("\n[3/6] EMBEDDING DIMENSION CHECK")

        try:
            collection_info = self.qdrant.get_collection(QDRANT_COLLECTION)
            actual_dim = collection_info.config.params.vectors.size

            self.log(f"Collection: {QDRANT_COLLECTION}")
            self.log(f"Expected dimension: {EXPECTED_EMBEDDING_DIMENSION}")
            self.log(f"Actual dimension: {actual_dim}")

            return self.check(
                f"Dimension is {EXPECTED_EMBEDDING_DIMENSION}D",
                actual_dim == EXPECTED_EMBEDDING_DIMENSION,
                f"Dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, got {actual_dim}"
            )
        except Exception as e:
            return self.check(
                "Qdrant collection accessible",
                False,
                f"Could not access collection: {e}"
            )

    # =========================================================================
    # CHECK 4: RAG Language Policy
    # =========================================================================
    def check_language_policy(self) -> bool:
        """Verify RAG language policy is correctly configured."""
        print("\n[4/6] LANGUAGE POLICY CHECK")

        # Check constants match
        self.check(
            "RAG_SUPPORTED_LANGUAGES configured",
            RAG_SUPPORTED_LANGUAGES == RAG_LANGUAGES,
            f"Mismatch: types={RAG_SUPPORTED_LANGUAGES}, acceptance={RAG_LANGUAGES}"
        )

        # Check evidence density constants
        self.check(
            "MIN_DISTINCT_CHUNKS configured",
            MIN_DISTINCT_CHUNKS == MIN_EVIDENCE_CHUNKS,
            f"Mismatch: confidence={MIN_DISTINCT_CHUNKS}, acceptance={MIN_EVIDENCE_CHUNKS}"
        )

        return self.check(
            "MIN_DISTINCT_SOURCES configured",
            MIN_DISTINCT_SOURCES == MIN_EVIDENCE_SOURCES,
            f"Mismatch: confidence={MIN_DISTINCT_SOURCES}, acceptance={MIN_EVIDENCE_SOURCES}"
        )

    # =========================================================================
    # CHECK 5: Data Quantity Thresholds
    # =========================================================================
    def check_data_thresholds(self) -> bool:
        """Verify minimum data quantities are met."""
        print("\n[5/6] DATA QUANTITY CHECK")

        # Quran verses
        verse_count = self.session.execute(
            select(func.count(QuranVerse.id))
        ).scalar() or 0

        self.check(
            f"Quran verses >= {MIN_VERSES}",
            verse_count >= MIN_VERSES,
            f"Only {verse_count} verses (need {MIN_VERSES})"
        )

        # Tafseer chunks
        chunk_count = self.session.execute(
            select(func.count(TafseerChunk.id))
        ).scalar() or 0

        self.check(
            f"Tafseer chunks >= {MIN_TAFSEER_CHUNKS}",
            chunk_count >= MIN_TAFSEER_CHUNKS,
            f"Only {chunk_count} chunks (need {MIN_TAFSEER_CHUNKS})"
        )

        # Tafseer sources
        source_count = self.session.execute(
            select(func.count(TafseerSource.id))
        ).scalar() or 0

        self.check(
            f"Tafseer sources >= {MIN_TAFSEER_SOURCES}",
            source_count >= MIN_TAFSEER_SOURCES,
            f"Only {source_count} sources (need {MIN_TAFSEER_SOURCES})"
        )

        # Stories (warning only - may not be fully populated)
        story_count = self.session.execute(
            select(func.count(Story.id))
        ).scalar() or 0

        self.warn(
            f"Stories >= {MIN_STORIES}",
            story_count >= MIN_STORIES,
            f"Only {story_count} stories (need {MIN_STORIES})"
        )

        # Vector count in Qdrant
        try:
            collection_info = self.qdrant.get_collection(QDRANT_COLLECTION)
            vector_count = collection_info.points_count

            return self.check(
                f"Indexed vectors >= {MIN_TAFSEER_CHUNKS}",
                vector_count >= MIN_TAFSEER_CHUNKS,
                f"Only {vector_count} vectors (need {MIN_TAFSEER_CHUNKS})"
            )
        except Exception as e:
            return self.check(
                "Vector count accessible",
                False,
                f"Could not get vector count: {e}"
            )

    # =========================================================================
    # CHECK 6: Confidence Scoring Operational
    # =========================================================================
    def check_confidence_scoring(self) -> bool:
        """Verify confidence scoring tests pass."""
        print("\n[6/6] CONFIDENCE SCORING CHECK")

        results = run_refusal_tests()
        passed = sum(1 for r in results if r['passed'])
        total = len(results)

        self.log(f"Running {total} refusal test cases...")

        for r in results:
            if not r['passed']:
                self.log(f"  FAILED: {r['name']}")

        return self.check(
            f"Refusal tests ({passed}/{total})",
            passed == total,
            f"Only {passed}/{total} tests passed"
        )

    # =========================================================================
    # Run All Checks
    # =========================================================================
    def run_all_checks(self) -> bool:
        """Run all integrity checks."""
        print("=" * 60)
        print("SYSTEM INTEGRITY VERIFICATION")
        print("=" * 60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")

        self.check_provenance()
        self.check_orphaned_chunks()
        self.check_embedding_dimension()
        self.check_language_policy()
        self.check_data_thresholds()
        self.check_confidence_scoring()

        return self.failed == 0

    def print_summary(self) -> bool:
        """Print verification summary."""
        print("\n" + "=" * 60)
        print("SYSTEM INTEGRITY SUMMARY")
        print("=" * 60)
        print(f"  Checks passed: {self.passed}")
        print(f"  Checks failed: {self.failed}")
        print(f"  Warnings: {self.warnings}")

        if self.errors:
            print("\n  ERRORS (must fix):")
            for err in self.errors:
                print(f"    - {err}")

        print("\n" + "=" * 60)

        if self.failed > 0:
            print("RESULT: REJECTED - System integrity verification failed")
            print("=" * 60)
            return False
        elif self.warnings > 0:
            print("RESULT: ACCEPTED (with warnings)")
            print("=" * 60)
            return True
        else:
            print("RESULT: ACCEPTED - All integrity checks passed")
            print("=" * 60)
            return True


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 60)
    print("TADABBUR SYSTEM INTEGRITY VERIFICATION")
    print("Final Acceptance Gate")
    print("=" * 60)

    try:
        engine = create_engine(get_db_url())
        qdrant = get_qdrant_client()

        with Session(engine) as session:
            checker = IntegrityChecker(session, qdrant, verbose=verbose)
            success = checker.run_all_checks()
            checker.print_summary()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\nCONFIGURATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
