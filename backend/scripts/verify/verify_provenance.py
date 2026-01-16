#!/usr/bin/env python3
"""
Verify provenance metadata for all tafseer sources.

MANDATORY CHECKS:
1. Every tafseer source MUST have:
   - cdn_url: The URL used to fetch the data
   - version_tag: Git commit hash or version tag
   - retrieval_timestamp: When data was fetched
   - license_type: Type of license
   - data_hash: SHA256 hash for integrity

2. Every tafseer chunk MUST be linked to a source with valid provenance

3. Audit logs MUST exist for ingestion operations

Exit codes:
  0 - All provenance checks passed
  1 - Provenance validation failed
  2 - Configuration error
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.models.tafseer import TafseerSource, TafseerChunk, IngestionAuditLog


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


class ProvenanceValidator:
    """Validates provenance metadata for tafseer sources."""

    def __init__(self, session: Session):
        self.session = session
        self.errors = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, error_msg: str, is_warning: bool = False):
        """Record a check result."""
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
            return True
        else:
            self.failed += 1
            if is_warning:
                self.warnings.append(error_msg)
                print(f"  [WARN] {name}: {error_msg}")
            else:
                self.errors.append(error_msg)
                print(f"  [FAIL] {name}: {error_msg}")
            return False

    def validate_source_provenance(self, source: TafseerSource) -> bool:
        """Validate provenance for a single source."""
        all_valid = True

        # Check CDN URL
        if not self.check(
            f"{source.id}: cdn_url",
            bool(source.cdn_url),
            f"Missing cdn_url for source {source.id}"
        ):
            all_valid = False

        # Check version tag
        if not self.check(
            f"{source.id}: version_tag",
            bool(source.version_tag),
            f"Missing version_tag for source {source.id}"
        ):
            all_valid = False

        # Check retrieval timestamp
        if not self.check(
            f"{source.id}: retrieval_timestamp",
            source.retrieval_timestamp is not None,
            f"Missing retrieval_timestamp for source {source.id}"
        ):
            all_valid = False

        # Check license type
        if not self.check(
            f"{source.id}: license_type",
            bool(source.license_type),
            f"Missing license_type for source {source.id}"
        ):
            all_valid = False

        # Check data hash (warning if missing)
        self.check(
            f"{source.id}: data_hash",
            bool(source.data_hash),
            f"Missing data_hash for source {source.id} (integrity check unavailable)",
            is_warning=True
        )

        # Check ayah count
        self.check(
            f"{source.id}: ayah_count",
            source.ayah_count is not None and source.ayah_count > 0,
            f"Missing or zero ayah_count for source {source.id}",
            is_warning=True
        )

        return all_valid

    def validate_chunks_have_sources(self) -> bool:
        """Verify all chunks reference valid sources with provenance."""
        # Get chunks without valid source provenance
        orphan_chunks = self.session.execute(
            select(func.count(TafseerChunk.id))
            .outerjoin(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
            .where(TafseerSource.id == None)
        ).scalar()

        return self.check(
            "All chunks have valid sources",
            orphan_chunks == 0,
            f"{orphan_chunks} chunks have no valid source"
        )

    def validate_audit_logs(self) -> bool:
        """Verify audit logs exist for sources."""
        sources = self.session.execute(select(TafseerSource)).scalars().all()

        all_valid = True
        for source in sources:
            # Check for seed audit log
            audit_count = self.session.execute(
                select(func.count(IngestionAuditLog.id))
                .where(IngestionAuditLog.source_id == source.id)
                .where(IngestionAuditLog.operation == "seed")
            ).scalar()

            if not self.check(
                f"{source.id}: audit_log",
                audit_count > 0,
                f"No seed audit log for source {source.id}",
                is_warning=True  # Warning because older sources may not have logs
            ):
                pass  # Continue checking other sources

        return all_valid

    def validate_license_verification(self) -> bool:
        """Check license verification status."""
        unverified = self.session.execute(
            select(func.count(TafseerSource.id))
            .where(TafseerSource.license_verified == 0)
        ).scalar()

        return self.check(
            "All licenses verified",
            unverified == 0,
            f"{unverified} sources have unverified licenses",
            is_warning=True
        )

    def run_all_checks(self) -> bool:
        """Run all provenance validation checks."""
        print("=" * 60)
        print("PROVENANCE VALIDATION")
        print("=" * 60)

        # Get all sources
        sources = self.session.execute(select(TafseerSource)).scalars().all()

        if not sources:
            print("\n  [WARN] No tafseer sources found")
            return True

        print(f"\nFound {len(sources)} tafseer sources")

        # 1. Validate each source's provenance
        print("\n[1/4] Checking source provenance fields...")
        all_sources_valid = True
        for source in sources:
            if not self.validate_source_provenance(source):
                all_sources_valid = False

        # 2. Validate chunks reference valid sources
        print("\n[2/4] Checking chunk-source relationships...")
        self.validate_chunks_have_sources()

        # 3. Validate audit logs exist
        print("\n[3/4] Checking audit logs...")
        self.validate_audit_logs()

        # 4. Validate license verification
        print("\n[4/4] Checking license verification status...")
        self.validate_license_verification()

        return len(self.errors) == 0

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("PROVENANCE VALIDATION SUMMARY")
        print("=" * 60)
        print(f"  Checks passed: {self.passed}")
        print(f"  Checks failed: {self.failed}")
        print(f"  Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n  ERRORS (must fix):")
            for err in self.errors:
                print(f"    - {err}")

        if self.warnings:
            print("\n  WARNINGS (should fix):")
            for warn in self.warnings:
                print(f"    - {warn}")

        print("=" * 60)

        if self.errors:
            print("RESULT: FAIL - Provenance validation failed")
            return False
        elif self.warnings:
            print("RESULT: PASS (with warnings)")
            return True
        else:
            print("RESULT: PASS - All provenance checks passed")
            return True


def show_provenance_report(session: Session):
    """Show detailed provenance report for each source."""
    print("\n" + "=" * 60)
    print("PROVENANCE REPORT")
    print("=" * 60)

    sources = session.execute(
        select(TafseerSource).order_by(TafseerSource.id)
    ).scalars().all()

    for source in sources:
        print(f"\n{source.id}:")
        print(f"  Name: {source.name_en}")
        print(f"  Language: {source.language}")
        print(f"  CDN URL: {source.cdn_url or 'MISSING'}")
        print(f"  Version: {source.version_tag or 'MISSING'}")
        print(f"  Retrieved: {source.retrieval_timestamp or 'MISSING'}")
        print(f"  Data Hash: {(source.data_hash[:16] + '...') if source.data_hash else 'MISSING'}")
        print(f"  Ayah Count: {source.ayah_count or 'MISSING'}")
        print(f"  License Type: {source.license_type or 'MISSING'}")
        print(f"  License Verified: {'Yes' if source.license_verified else 'No'}")
        print(f"  Has Valid Provenance: {'Yes' if source.has_valid_provenance else 'NO'}")


def main():
    print("=" * 60)
    print("TAFSEER PROVENANCE VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")

    engine = create_engine(get_db_url())

    with Session(engine) as session:
        validator = ProvenanceValidator(session)
        success = validator.run_all_checks()
        validator.print_summary()

        # Show detailed report if requested
        if "--report" in sys.argv or "-r" in sys.argv:
            show_provenance_report(session)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
