#!/usr/bin/env python3
"""
Seed tafseer data into PostgreSQL from downloaded JSON files.

PROVENANCE REQUIREMENTS:
- Every source MUST have complete provenance metadata
- Creates audit log entries for every ingestion
- Fails if provenance data is incomplete

Usage:
    python scripts/ingest/seed_tafseer.py [source_id ...]

Example:
    python scripts/ingest/seed_tafseer.py ibn_kathir_en ibn_kathir_ar
"""
import sys
import os
import json
import hashlib
import socket
import getpass
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.quran import QuranVerse
from app.models.tafseer import TafseerSource, TafseerChunk, IngestionAuditLog

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFESTS_DIR = DATA_DIR / "manifests"

# CDN base URL for spa5k/tafsir_api
CDN_BASE_URL = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir"

# Source metadata with MANDATORY provenance fields
SOURCE_METADATA = {
    "ibn_kathir_en": {
        "name_ar": "تفسير ابن كثير",
        "name_en": "Tafsir Ibn Kathir (English)",
        "author_ar": "إسماعيل بن عمر بن كثير",
        "author_en": "Ismail ibn Umar ibn Kathir",
        "era": "classical",
        "methodology": "bil_mathur",
        "language": "en",
        "reliability_score": 0.95,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "en-tafisr-ibn-kathir",
        "version_tag": "main",  # Git branch/tag
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain due to age (774 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "ibn_kathir_ar": {
        "name_ar": "تفسير ابن كثير",
        "name_en": "Tafsir Ibn Kathir (Arabic)",
        "author_ar": "إسماعيل بن عمر بن كثير",
        "author_en": "Ismail ibn Umar ibn Kathir",
        "era": "classical",
        "methodology": "bil_mathur",
        "language": "ar",
        "reliability_score": 0.98,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "ar-tafsir-ibn-kathir",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain due to age (774 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "muyassar_ar": {
        "name_ar": "التفسير الميسر",
        "name_en": "Al-Tafsir Al-Muyassar",
        "author_ar": "مجمع الملك فهد لطباعة المصحف الشريف",
        "author_en": "King Fahd Complex for Printing the Holy Quran",
        "era": "modern",
        "methodology": "simplified",
        "language": "ar",
        "reliability_score": 0.92,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "ar-tafsir-muyassar",
        "version_tag": "main",
        "license_type": "educational_use",
        "license": "King Fahd Complex - educational and non-commercial use",
        "license_url": "https://qurancomplex.gov.sa",
    },
    "qurtubi_ar": {
        "name_ar": "الجامع لأحكام القرآن",
        "name_en": "Tafsir al-Qurtubi",
        "author_ar": "محمد بن أحمد القرطبي",
        "author_en": "Muhammad ibn Ahmad al-Qurtubi",
        "era": "classical",
        "methodology": "fiqh_focused",
        "language": "ar",
        "reliability_score": 0.95,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "ar-tafseer-al-qurtubi",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain due to age (671 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "tabari_ar": {
        "name_ar": "جامع البيان عن تأويل آي القرآن",
        "name_en": "Tafsir al-Tabari",
        "author_ar": "محمد بن جرير الطبري",
        "author_en": "Muhammad ibn Jarir al-Tabari",
        "era": "classical",
        "methodology": "bil_mathur",
        "language": "ar",
        "reliability_score": 0.98,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "ar-tafsir-al-tabari",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain due to age (310 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "baghawi_ar": {
        "name_ar": "معالم التنزيل",
        "name_en": "Tafsir al-Baghawi",
        "author_ar": "الحسين بن مسعود البغوي",
        "author_en": "Al-Husayn ibn Mas'ud al-Baghawi",
        "era": "classical",
        "methodology": "bil_mathur",
        "language": "ar",
        "reliability_score": 0.93,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "ar-tafsir-al-baghawi",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain due to age (516 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "jalalayn_en": {
        "name_ar": "تفسير الجلالين",
        "name_en": "Tafsir al-Jalalayn (English)",
        "author_ar": "جلال الدين المحلي وجلال الدين السيوطي",
        "author_en": "Jalal ad-Din al-Mahalli and Jalal ad-Din as-Suyuti",
        "era": "classical",
        "methodology": "concise",
        "language": "en",
        "reliability_score": 0.90,
        "is_primary_source": True,
        # PROVENANCE
        "cdn_folder": "en-al-jalalayn",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain (864/911 AH)",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
    "ibn_abbas_en": {
        "name_ar": "تنوير المقباس من تفسير ابن عباس",
        "name_en": "Tanwir al-Miqbas min Tafsir Ibn Abbas",
        "author_ar": "عبدالله بن عباس",
        "author_en": "Abdullah ibn Abbas (attributed)",
        "era": "classical",
        "methodology": "bil_mathur",
        "language": "en",
        "reliability_score": 0.85,
        "is_primary_source": False,  # Attribution disputed
        # PROVENANCE
        "cdn_folder": "en-tafsir-ibn-abbas",
        "version_tag": "main",
        "license_type": "public_domain_classical",
        "license": "Classical Islamic text - public domain",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
}


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def generate_chunk_id(source_id: str, sura: int, ayah: int) -> str:
    """Generate unique chunk ID."""
    base = f"{source_id}:s{sura}:a{ayah}"
    return hashlib.md5(base.encode()).hexdigest()[:16]


def compute_data_hash(data: list) -> str:
    """Compute SHA256 hash of data for integrity verification."""
    content = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def load_tafseer_data(source_id: str) -> tuple[list, str]:
    """Load tafseer JSON file. Returns (data, hash)."""
    path = RAW_DIR / f"{source_id}.json"
    if not path.exists():
        return [], ""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data, compute_data_hash(data)


def get_retrieval_timestamp(source_id: str) -> datetime:
    """Get file modification time as retrieval timestamp."""
    path = RAW_DIR / f"{source_id}.json"
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.utcnow()


def validate_provenance(meta: dict, source_id: str) -> list[str]:
    """Validate that all required provenance fields are present."""
    errors = []
    required = ["cdn_folder", "version_tag", "license_type", "license"]
    for field in required:
        if not meta.get(field):
            errors.append(f"Missing required provenance field: {field}")
    return errors


def create_audit_log(
    session: Session,
    source_id: str,
    operation: str,
    cdn_url: str,
    version_tag: str,
    data_hash: str,
    records_processed: int,
    records_inserted: int,
    records_skipped: int,
    records_failed: int,
    status: str,
    error_message: str,
    started_at: datetime,
) -> IngestionAuditLog:
    """Create an audit log entry for the ingestion."""
    completed_at = datetime.utcnow()
    duration = (completed_at - started_at).total_seconds()

    log = IngestionAuditLog(
        source_id=source_id,
        operation=operation,
        cdn_url=cdn_url,
        version_tag=version_tag,
        data_hash=data_hash,
        records_processed=records_processed,
        records_inserted=records_inserted,
        records_skipped=records_skipped,
        records_failed=records_failed,
        status=status,
        error_message=error_message,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration,
        hostname=socket.gethostname(),
        user=getpass.getuser(),
    )
    session.add(log)
    return log


def seed_source(session: Session, source_id: str) -> tuple[int, int, int]:
    """Seed a single tafseer source. Returns (inserted, skipped, failed)."""
    started_at = datetime.utcnow()

    # Get metadata
    meta = SOURCE_METADATA.get(source_id, {})
    if not meta:
        print(f"  ERROR: No metadata defined for {source_id}")
        print(f"  Add entry to SOURCE_METADATA in seed_tafseer.py")
        return 0, 0, 1

    # Validate provenance
    provenance_errors = validate_provenance(meta, source_id)
    if provenance_errors:
        print(f"  PROVENANCE VALIDATION FAILED:")
        for err in provenance_errors:
            print(f"    - {err}")
        return 0, 0, 1

    # Load data
    data, data_hash = load_tafseer_data(source_id)
    if not data:
        print(f"  No data found for {source_id}")
        return 0, 0, 0

    print(f"  Loaded {len(data)} entries")
    print(f"  Data hash: {data_hash[:16]}...")

    # Build CDN URL and provenance
    cdn_folder = meta["cdn_folder"]
    cdn_url = f"{CDN_BASE_URL}/{cdn_folder}"
    version_tag = meta["version_tag"]
    retrieval_timestamp = get_retrieval_timestamp(source_id)
    language = meta.get("language", "en" if "_en" in source_id else "ar")

    # Get or create source with full provenance
    existing = session.execute(
        select(TafseerSource).where(TafseerSource.id == source_id)
    ).scalar_one_or_none()

    if not existing:
        source = TafseerSource(
            id=source_id,
            name_ar=meta.get("name_ar", source_id),
            name_en=meta.get("name_en", source_id),
            author_ar=meta.get("author_ar", ""),
            author_en=meta.get("author_en", ""),
            era=meta.get("era", "classical"),
            methodology=meta.get("methodology", ""),
            language=language,
            reliability_score=meta.get("reliability_score", 0.8),
            is_primary_source=1 if meta.get("is_primary_source") else 0,
            # PROVENANCE FIELDS
            cdn_url=cdn_url,
            version_tag=version_tag,
            retrieval_timestamp=retrieval_timestamp,
            data_hash=data_hash,
            ayah_count=len(data),
            license_type=meta.get("license_type"),
            license=meta.get("license"),
            license_url=meta.get("license_url"),
            license_verified=1 if meta.get("license_type") else 0,
        )
        session.add(source)
        session.flush()
        print(f"  Created source with provenance: {source_id}")
        print(f"    CDN URL: {cdn_url}")
        print(f"    Version: {version_tag}")
        print(f"    License: {meta.get('license_type')}")
    else:
        # Update provenance if missing
        if not existing.cdn_url:
            existing.cdn_url = cdn_url
            existing.version_tag = version_tag
            existing.retrieval_timestamp = retrieval_timestamp
            existing.data_hash = data_hash
            existing.ayah_count = len(data)
            existing.license_type = meta.get("license_type")
            existing.license = meta.get("license")
            existing.license_url = meta.get("license_url")
            existing.license_verified = 1
            print(f"  Updated provenance for: {source_id}")
        else:
            print(f"  Source exists with provenance: {source_id}")

    # Build verse lookup cache
    print("  Building verse lookup...")
    verse_cache = {}
    verses = session.execute(select(QuranVerse.id, QuranVerse.sura_no, QuranVerse.aya_no)).all()
    for vid, sura, aya in verses:
        verse_cache[(sura, aya)] = vid
    print(f"  Cached {len(verse_cache)} verses")

    # Insert chunks
    inserted = 0
    skipped = 0
    failed = 0
    batch_size = 500

    for i, entry in enumerate(data):
        sura = entry.get("surah", entry.get("sura", 0))
        ayah = entry.get("ayah", entry.get("aya", 0))
        text = entry.get("text", "").strip()

        if not sura or not ayah or not text:
            skipped += 1
            continue

        chunk_id = generate_chunk_id(source_id, sura, ayah)

        # Check if exists
        existing_chunk = session.execute(
            select(TafseerChunk.id).where(TafseerChunk.chunk_id == chunk_id)
        ).scalar_one_or_none()

        if existing_chunk:
            skipped += 1
            continue

        # Get verse IDs
        verse_id = verse_cache.get((sura, ayah))
        if not verse_id:
            failed += 1
            continue

        # Create chunk
        chunk = TafseerChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            verse_start_id=verse_id,
            verse_end_id=verse_id,
            sura_no=sura,
            aya_start=ayah,
            aya_end=ayah,
            content_ar=text if language == "ar" else None,
            content_en=text if language == "en" else None,
            word_count=len(text.split()),
            char_count=len(text),
            is_embedded=0,
        )
        session.add(chunk)
        inserted += 1

        # Batch commit
        if inserted % batch_size == 0:
            session.flush()
            print(f"    Inserted {inserted} chunks...")

    # Create audit log
    status = "success" if failed == 0 else ("partial" if inserted > 0 else "failed")
    create_audit_log(
        session=session,
        source_id=source_id,
        operation="seed",
        cdn_url=cdn_url,
        version_tag=version_tag,
        data_hash=data_hash,
        records_processed=len(data),
        records_inserted=inserted,
        records_skipped=skipped,
        records_failed=failed,
        status=status,
        error_message=None if failed == 0 else f"{failed} records failed to insert",
        started_at=started_at,
    )

    session.commit()
    return inserted, skipped, failed


def main():
    print("=" * 60)
    print("TAFSEER SEEDING (with Provenance Tracking)")
    print("=" * 60)

    start_time = datetime.utcnow()

    # Get source IDs
    if len(sys.argv) > 1:
        source_ids = sys.argv[1:]
    else:
        # Default: seed all available
        available = [f.stem for f in RAW_DIR.glob("*.json")]
        source_ids = [s for s in available if s in SOURCE_METADATA]

    if not source_ids:
        print("No tafseer sources to seed.")
        print(f"Place JSON files in: {RAW_DIR}")
        print(f"Available metadata: {list(SOURCE_METADATA.keys())}")
        sys.exit(0)

    print(f"Sources to seed: {source_ids}")

    # Connect to database
    engine = create_engine(get_db_url())

    total_inserted = 0
    total_skipped = 0
    total_failed = 0

    with Session(engine) as session:
        for source_id in source_ids:
            print(f"\nProcessing: {source_id}")
            inserted, skipped, failed = seed_source(session, source_id)
            total_inserted += inserted
            total_skipped += skipped
            total_failed += failed
            print(f"  Inserted: {inserted}, Skipped: {skipped}, Failed: {failed}")

    duration = (datetime.utcnow() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total inserted: {total_inserted}")
    print(f"  Total skipped: {total_skipped}")
    print(f"  Total failed: {total_failed}")
    print(f"  Duration: {duration:.2f}s")
    print("=" * 60)

    if total_failed > 0:
        print("\nWARNING: Some records failed to insert")
        sys.exit(1)


if __name__ == "__main__":
    main()
