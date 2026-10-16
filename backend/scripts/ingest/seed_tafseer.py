#!/usr/bin/env python3
"""
Seed tafseer data into PostgreSQL from downloaded JSON files.

PROVENANCE REQUIREMENTS:
- Every source MUST have complete provenance metadata
- Creates audit log entries for every ingestion
- Fails if provenance data is incomplete

LICENSING:
- The licence state written to tafseer_sources comes from
  data/manifests/tafseer_sources.json, not from the metadata below. A source
  is written with license_verified=1 and is_enabled=1 only when the manifest
  lists it in enabled_ids with a verified licence (verified_date set, type not
  pending). Anything else is skipped, or with --allow-unverified written
  disabled and unverified, for review only.

REPLACING A STORED COPY (--replace):
- By default existing chunks are never touched, so a source seeded earlier
  from another origin keeps that origin's text. --replace swaps the stored
  copy of each named source for the file in data/raw in ONE transaction:
  changed passages are updated in place (chunk ids are derived from
  source:sura:ayah, so they stay stable and evidence references keep
  resolving), new verses are inserted, verses the new file has no passage for
  are deleted, and the source row's provenance (source_url, cdn_url,
  version_tag, data_hash, licence URL) is rewritten to the new origin.
- It requires the <source_id>.provenance.json sidecar written by
  scripts/datasets/fetch_hf_tafseers.py (pinned revision, SHA-256 checked):
  the point is that the recorded origin is true.
- Changed and deleted chunks are marked is_embedded=0 and their Qdrant
  points are removed, so RAG never serves the old text; re-index with
  scripts/index/index_tafseer.py --source <source_id>.
- After a replace, update the source's entry in
  frontend/src/data/sourceRegistry.ts and the stored_copy note in
  data/manifests/tafseer_sources.json to name the new origin
  (tests/unit/test_tafseer_provenance_truth.py checks they agree).

Usage:
    python scripts/ingest/seed_tafseer.py [--allow-unverified] [source_id ...]
    python scripts/ingest/seed_tafseer.py --replace [--no-qdrant] source_id ...

Example:
    python scripts/datasets/fetch_hf_tafseers.py --exclude muyassar_ar
    python scripts/ingest/seed_tafseer.py --replace tabari_ar qurtubi_ar ibn_kathir_ar
"""
import sys
import os
import re
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
from app.services.tafsir_sources import TAFSIR_PLACEHOLDER_TEXTS

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
        # The Arabic original is public domain by age; this modern English
        # translation (Darussalam abridgement) is not.
        "translator": "Darussalam abridgement",
        "license_type": "pending_verification",
        "license": "Modern English translation - permission required",
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
        "translator": "Feras Hamza (Royal Aal al-Bayt Institute)",
        "license_type": "pending_verification",
        "license": "Modern English translation - permission required",
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
        "license_type": "pending_verification",
        "license": "Modern English translation - permission required",
        "license_url": "https://github.com/spa5k/tafsir_api",
    },
}


MANIFEST_PATH = MANIFESTS_DIR / "tafseer_sources.json"

# Upstream rows that say "there is no tafsir for this verse". They are not the
# scholar's words: storing them showed the placeholder as al-Qurtubi's or Ibn
# Kathir's commentary and let RAG cite it. The upstream groups commentary across
# verses, so such a verse simply has no separate passage in that source.
PLACEHOLDER_TEXTS = TAFSIR_PLACEHOLDER_TEXTS


def is_placeholder(text: str) -> bool:
    return " ".join(text.split()).strip(" .") in PLACEHOLDER_TEXTS


# Upstream lost the separator between a quoted Qur'an span (fully vowelled)
# and the commentary that follows ("بِكَلِمَاتٍقال أبو جعفر"), so the Qur'anic
# word looks altered. A single U+0020 is restored at that boundary only; no
# letter or mark is added, removed or changed.
_MARKS = "\u064B-\u0652\u0670"
_CONNECTORS = "أي|يعني|قال|وقيل|وهو|وهي"
_GLUED = re.compile(rf"(\S*?[{_MARKS}])({_CONNECTORS})(?=[\s.,،:؛»\"\)]|$)")
_LONG_ALIF = "اآى"


def _is_vowelled_quote(token: str) -> bool:
    """True when a token reads as fully vowelled Qur'an text.

    At least two letters; ignoring a leading definite article and long alifs,
    a two-letter token must be fully marked and a longer one at least half
    marked. Commentary words such as يُقال, فَقال or رَأي (one letter before
    the connector) never qualify.
    """
    letters: list = []
    for ch in token:
        if "\u0621" <= ch <= "\u064A":
            letters.append([ch, False])
        elif letters and re.match(f"[{_MARKS}]", ch):
            letters[-1][1] = True
    if len(letters) < 2:
        return False
    if letters[0][0] == "ا" and letters[1][0] == "ل":
        letters = letters[2:]
    letters = [l for l in letters if l[0] not in _LONG_ALIF]
    if not letters:
        return False
    if len(letters) <= 2:
        return all(marked for _, marked in letters)
    return sum(1 for _, marked in letters if marked) * 2 >= len(letters)


def restore_quote_boundaries(text: str) -> tuple:
    """(text, n): insert one space between a glued Qur'an quote and commentary.

    Deterministic and idempotent; removing all spaces from the result gives
    back the input byte for byte.
    """
    out, pos, n = [], 0, 0
    for m in _GLUED.finditer(text):
        if _is_vowelled_quote(m.group(1)):
            out.append(text[pos:m.end(1)])
            out.append(" ")
            pos = m.end(1)
            n += 1
    out.append(text[pos:])
    return "".join(out), n


def load_licence_state(source_id: str, manifest_path: Path = MANIFEST_PATH) -> dict:
    """Licence state for a source, read from the manifest.

    Returns {"verified": bool, "enabled": bool, "reason": str}. A source is
    verified when the manifest has a structured licence with a verified_date
    and a non-pending type, and enabled only when also listed in enabled_ids.
    Unknown sources are unverified.
    """
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"verified": False, "enabled": False, "reason": f"manifest unreadable: {e}"}
    entry = next((s for s in manifest.get("sources", []) if s.get("id") == source_id), None)
    if entry is None:
        return {"verified": False, "enabled": False, "reason": "not in manifest.sources"}
    licence = entry.get("license")
    if not isinstance(licence, dict):
        return {"verified": False, "enabled": False, "reason": "no structured licence"}
    if str(licence.get("type", "")).startswith("pending") or not licence.get("verified_date"):
        return {"verified": False, "enabled": False, "reason": f"licence {licence.get('type')} not verified"}
    enabled = source_id in set(manifest.get("enabled_ids", []))
    return {"verified": True, "enabled": enabled, "reason": "ok" if enabled else "not in enabled_ids"}


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


def seed_source(session: Session, source_id: str, allow_unverified: bool = False) -> tuple[int, int, int]:
    """Seed a single tafseer source. Returns (inserted, skipped, failed)."""
    started_at = datetime.utcnow()

    licence_state = load_licence_state(source_id)
    if not licence_state["verified"] and not allow_unverified:
        print(f"  SKIPPED: licence not verified ({licence_state['reason']}).")
        print("  Record the licence in data/manifests/tafseer_sources.json, or pass")
        print("  --allow-unverified to seed it disabled for review only.")
        return 0, 0, 0
    verified = 1 if licence_state["verified"] else 0
    enabled = 1 if licence_state["verified"] and licence_state["enabled"] else 0

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
    # Files produced by scripts/datasets/fetch_hf_tafseers.py carry their real
    # origin (dataset + pinned revision) in a sidecar; record that, not the CDN.
    sidecar = RAW_DIR / f"{source_id}.provenance.json"
    license_url = meta.get("license_url")
    if sidecar.exists():
        prov = json.loads(sidecar.read_text(encoding="utf-8"))
        cdn_url = prov["source_url"]
        version_tag = prov["revision"]
        # The licence that applies to the digital text is the dataset's, not
        # the spa5k repository's.
        license_url = f"https://huggingface.co/datasets/{prov['dataset']}"
        print(f"  Provenance: {prov['dataset']}@{version_tag[:12]} ({prov['dataset_license']})")
    # source_url records where this text really came from (the pinned dataset
    # file, or the CDN folder it was fetched from).
    source_url = cdn_url
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
            source_url=source_url,
            cdn_url=cdn_url,
            version_tag=version_tag,
            retrieval_timestamp=retrieval_timestamp,
            data_hash=data_hash,
            ayah_count=len(data),
            license_type=meta.get("license_type"),
            license=meta.get("license"),
            license_url=license_url,
            license_verified=verified,
            is_enabled=enabled,
            translator=meta.get("translator"),
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
            existing.source_url = source_url
            existing.cdn_url = cdn_url
            existing.version_tag = version_tag
            existing.retrieval_timestamp = retrieval_timestamp
            existing.data_hash = data_hash
            existing.ayah_count = len(data)
            existing.license_type = meta.get("license_type")
            existing.license = meta.get("license")
            existing.license_url = license_url
            print(f"  Updated provenance for: {source_id}")
        else:
            print(f"  Source exists with provenance: {source_id}")
            # Existing chunks are kept (skipped below), so the recorded origin
            # stays the one they were fetched from: the row's cdn_url.
            if not existing.source_url:
                existing.source_url = existing.cdn_url
        # Licence state always follows the manifest, never an older row.
        existing.license_verified = verified
        existing.is_enabled = enabled
        if meta.get("translator"):
            existing.translator = meta["translator"]

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
    placeholders = 0
    boundaries_restored = 0
    batch_size = 500

    for i, entry in enumerate(data):
        sura = entry.get("surah", entry.get("sura", 0))
        ayah = entry.get("ayah", entry.get("aya", 0))
        text = entry.get("text", "").strip()

        if not sura or not ayah or not text:
            skipped += 1
            continue
        if is_placeholder(text):
            placeholders += 1
            skipped += 1
            continue
        if language == "ar":
            text, restored = restore_quote_boundaries(text)
            boundaries_restored += restored

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
            session.commit()
            print(f"    Inserted {inserted} chunks...")

    print(f"  Placeholder rows skipped: {placeholders}")
    print(f"  Quote/commentary boundaries restored (whitespace_restored): {boundaries_restored}")

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


def clean_entries(data: list, language: str) -> dict:
    """{(sura, ayah): text} exactly as seed_source would store them."""
    out = {}
    for entry in data:
        sura = entry.get("surah", entry.get("sura", 0))
        ayah = entry.get("ayah", entry.get("aya", 0))
        text = (entry.get("text") or "").strip()
        if not sura or not ayah or not text or is_placeholder(text):
            continue
        if language == "ar":
            text, _ = restore_quote_boundaries(text)
        out[(int(sura), int(ayah))] = text
    return out


def plan_replacement(new: dict, stored: dict) -> dict:
    """Diff the new copy against the stored one.

    new:    {(sura, ayah): text}
    stored: {(sura, ayah): text}
    Returns {"update": [...], "insert": [...], "delete": [...], "unchanged": n}
    with sorted (sura, ayah) keys.
    """
    update = sorted(k for k in new if k in stored and stored[k] != new[k])
    insert = sorted(k for k in new if k not in stored)
    delete = sorted(k for k in stored if k not in new)
    unchanged = sum(1 for k in new if k in stored and stored[k] == new[k])
    return {"update": update, "insert": insert, "delete": delete, "unchanged": unchanged}


def _drop_qdrant_points(point_ids: list) -> None:
    """Remove stale vectors: their payload carries the old text."""
    if not point_ids:
        return
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointIdsList

        from app.core.config import settings

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, check_compatibility=False)
        collection = os.getenv("QDRANT_COLLECTION", settings.qdrant_collection_tafseer)
        for i in range(0, len(point_ids), 1000):
            client.delete(collection_name=collection, points_selector=PointIdsList(points=point_ids[i:i + 1000]))
        print(f"  Qdrant: removed {len(point_ids)} stale points from {collection}")
    except Exception as e:  # pragma: no cover - depends on a running Qdrant
        print(f"  WARNING: could not remove {len(point_ids)} stale Qdrant points ({type(e).__name__}: {e}).")
        print("  RAG may serve the old text until they are removed and the source is re-indexed.")


def replace_source(session: Session, source_id: str, qdrant: bool = True) -> dict:
    """Replace the stored copy of one source atomically (see module docstring)."""
    started_at = datetime.utcnow()
    meta = SOURCE_METADATA.get(source_id)
    if not meta:
        raise SystemExit(f"  ERROR: no metadata for {source_id}")
    sidecar = RAW_DIR / f"{source_id}.provenance.json"
    if not sidecar.exists():
        raise SystemExit(
            f"  ERROR: --replace needs {sidecar.name} (run scripts/datasets/fetch_hf_tafseers.py); "
            "a stored copy is only replaced by one with a recorded, pinned origin."
        )
    prov = json.loads(sidecar.read_text(encoding="utf-8"))
    data, data_hash = load_tafseer_data(source_id)
    if not data:
        raise SystemExit(f"  ERROR: no data for {source_id} in {RAW_DIR}")
    licence_state = load_licence_state(source_id)
    if not licence_state["verified"]:
        raise SystemExit(f"  ERROR: licence of {source_id} not verified ({licence_state['reason']})")

    language = meta.get("language", "ar")
    new = clean_entries(data, language)
    source = session.execute(select(TafseerSource).where(TafseerSource.id == source_id)).scalar_one_or_none()
    if source is None:
        raise SystemExit(f"  ERROR: {source_id} is not seeded yet; run without --replace first")

    rows = session.execute(select(TafseerChunk).where(TafseerChunk.source_id == source_id)).scalars().all()
    by_key = {(c.sura_no, c.aya_start): c for c in rows}
    stored = {k: (c.content_ar if language == "ar" else c.content_en) for k, c in by_key.items()}
    plan = plan_replacement(new, stored)

    verse_ids = {
        (s, a): vid
        for vid, s, a in session.execute(select(QuranVerse.id, QuranVerse.sura_no, QuranVerse.aya_no)).all()
    }
    stale_points = []
    for k in plan["update"]:
        c = by_key[k]
        if c.is_embedded:
            stale_points.append(c.id)
        if language == "ar":
            c.content_ar = new[k]
        else:
            c.content_en = new[k]
        c.word_count = len(new[k].split())
        c.char_count = len(new[k])
        c.is_embedded = 0
        c.embedding_model = None
    failed = 0
    for k in plan["insert"]:
        vid = verse_ids.get(k)
        if not vid:
            failed += 1
            continue
        session.add(TafseerChunk(
            chunk_id=generate_chunk_id(source_id, *k),
            source_id=source_id,
            verse_start_id=vid,
            verse_end_id=vid,
            sura_no=k[0],
            aya_start=k[1],
            aya_end=k[1],
            content_ar=new[k] if language == "ar" else None,
            content_en=new[k] if language == "en" else None,
            word_count=len(new[k].split()),
            char_count=len(new[k]),
            is_embedded=0,
        ))
    for k in plan["delete"]:
        c = by_key[k]
        if c.is_embedded:
            stale_points.append(c.id)
        session.delete(c)

    source.source_url = prov["source_url"]
    source.cdn_url = prov["source_url"]
    source.version_tag = prov["revision"]
    source.license_url = f"https://huggingface.co/datasets/{prov['dataset']}"
    source.data_hash = data_hash
    source.ayah_count = len(new)
    source.retrieval_timestamp = get_retrieval_timestamp(source_id)

    create_audit_log(
        session=session,
        source_id=source_id,
        operation="replace",
        cdn_url=prov["source_url"],
        version_tag=prov["revision"],
        data_hash=data_hash,
        records_processed=len(data),
        records_inserted=len(plan["insert"]) - failed,
        records_skipped=plan["unchanged"],
        records_failed=failed,
        status="success" if failed == 0 else "partial",
        error_message=None if failed == 0 else f"{failed} verses missing from quran_verses",
        started_at=started_at,
    )
    session.commit()  # one transaction per source
    print(
        f"  {source_id}: updated {len(plan['update'])}, inserted {len(plan['insert']) - failed}, "
        f"deleted {len(plan['delete'])}, unchanged {plan['unchanged']}, failed {failed}"
    )
    print(f"  Provenance: {prov['dataset']}@{prov['revision'][:12]} ({prov['dataset_license']})")
    if qdrant:
        _drop_qdrant_points(stale_points)
    return {**{k: len(v) for k, v in plan.items() if isinstance(v, list)}, "failed": failed}


def main_replace(source_ids: list, qdrant: bool) -> None:
    if not source_ids:
        raise SystemExit("--replace needs explicit source ids")
    engine = create_engine(get_db_url().replace("+asyncpg", ""))
    for source_id in source_ids:
        print(f"\nReplacing stored copy: {source_id}")
        with Session(engine) as session:
            replace_source(session, source_id, qdrant=qdrant)
    print("\nRe-index the replaced sources: python scripts/index/index_tafseer.py "
          + " ".join(f"--source {s}" for s in source_ids))


def main():
    if "--replace" in sys.argv[1:]:
        rest = [a for a in sys.argv[1:] if a not in ("--replace", "--no-qdrant")]
        main_replace(rest, qdrant="--no-qdrant" not in sys.argv[1:])
        return

    print("=" * 60)
    print("TAFSEER SEEDING (with Provenance Tracking)")
    print("=" * 60)

    start_time = datetime.utcnow()

    args = sys.argv[1:]
    allow_unverified = "--allow-unverified" in args
    args = [a for a in args if a != "--allow-unverified"]

    # Get source IDs
    if args:
        source_ids = args
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

    for source_id in source_ids:
        print(f"\nProcessing: {source_id}")
        with Session(engine) as session:
            inserted, skipped, failed = seed_source(session, source_id, allow_unverified)
            session.commit()
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
