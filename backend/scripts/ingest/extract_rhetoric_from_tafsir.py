#!/usr/bin/env python3
"""
Extract Rhetorical Device Occurrences from Balagha-Focused Tafsirs

This script:
1. Searches tafsir chunks for Arabic rhetorical terms (استعارة, تشبيه, طباق, etc.)
2. Parses context to identify the verse range being discussed
3. Creates RhetoricalOccurrence entries with evidence_chunk_ids
4. Marks all extractions as is_verified=False for scholar review

EPISTEMIC GROUNDING:
===================
All occurrences MUST have at least one evidence_chunk_id from balagha-focused tafsirs.

Priority sources (in order):
1. Al-Zamakhshari (الكشاف) - Primary balagha source
2. Al-Razi (التفسير الكبير) - Philosophical + rhetorical
3. Abu Su'ud (إرشاد العقل السليم) - Ottoman rhetorical tradition
4. Ibn Ashur (التحرير والتنوير) - Modern linguistic analysis

Usage:
    python scripts/ingest/extract_rhetoric_from_tafsir.py [--source zamakhshari] [--limit 100]
"""
import sys
import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.models.rhetoric import RhetoricalOccurrence, RhetoricalDeviceType


# =============================================================================
# ARABIC SEARCH TERMS FOR RHETORICAL DEVICES
# =============================================================================

# Maps device ID to Arabic search terms
DEVICE_SEARCH_TERMS: Dict[str, List[str]] = {
    "istiaara": ["استعارة", "استعير", "المستعار", "استعاره"],
    "tashbih": ["تشبيه", "شُبّه", "المشبه", "التمثيل", "التشبيه"],
    "tibaq": ["طباق", "المطابقة", "الضد", "الأضداد"],
    "jinas": ["جناس", "التجانس", "الجناس"],
    "kinaya": ["كناية", "كنى", "الكناية", "كنايه"],
    "majaz": ["مجاز", "المجاز", "مجازي", "مجازاً"],
    "iltifat": ["التفات", "الالتفات", "التحول"],
    "istifham": ["استفهام", "السؤال البلاغي", "الاستفهام"],
    "itnaab": ["إطناب", "الإطناب", "التفصيل"],
    "ijaz": ["إيجاز", "الإيجاز", "الحذف", "ايجاز"],
    "taqdim": ["تقديم", "التقديم والتأخير", "قدّم", "التقديم"],
    "saj": ["سجع", "الفاصلة", "الفواصل", "السجع"],
    "tawriya": ["تورية", "التورية"],
    "muqabala": ["مقابلة", "المقابلة"],
    "qasr": ["قصر", "القصر", "الحصر"],
    "nida": ["نداء", "النداء"],
    "amr": ["أمر بلاغي", "الأمر"],
    "nahy": ["نهي بلاغي", "النهي"],
    "radd_al_ajz": ["رد العجز", "رد العجز على الصدر"],
    "liff_wa_nashr": ["لف ونشر", "اللف والنشر"],
    "taqsim": ["تقسيم", "التقسيم"],
}

# Priority tafsir source IDs (balagha-focused)
PRIORITY_SOURCES = [
    "zamakhshari",      # الكشاف - Primary
    "al_kashaf",        # Alternative ID for الكشاف
    "razi",             # التفسير الكبير
    "fakhr_razi",       # Alternative ID for الرازي
    "abu_suud",         # إرشاد العقل السليم
    "abu_saud",         # Alternative ID
    "ibn_ashur",        # التحرير والتنوير
    "tahrir",           # Alternative ID for ابن عاشور
]

# Fallback sources that also contain rhetorical analysis
FALLBACK_SOURCES = [
    "qurtubi_ar",       # Tafsir al-Qurtubi - Contains linguistic analysis
    "tabari_ar",        # Tafsir al-Tabari - Foundational with balagha
    "nasafi_ar",        # Madarik al-Tanzil - Good rhetorical content
    "ibn_kathir_ar",    # Tafsir Ibn Kathir - Some rhetorical notes
    "shinqiti_ar",      # Adwa al-Bayan - Linguistic focus
]


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def get_available_sources(session: Session) -> List[Dict[str, Any]]:
    """Get list of available tafsir sources."""
    result = session.execute(text("""
        SELECT id, name_ar, name_en, author_ar
        FROM tafseer_sources
        ORDER BY name_en
    """))

    sources = []
    for row in result:
        sources.append({
            "id": row[0],
            "name_ar": row[1],
            "name_en": row[2],
            "author_ar": row[3],
        })
    return sources


def find_balagha_sources(session: Session) -> List[str]:
    """Find tafsir sources that focus on balagha (rhetoric)."""
    result = session.execute(text("""
        SELECT id, name_ar, name_en, methodology
        FROM tafseer_sources
        WHERE methodology ILIKE '%balagha%'
           OR methodology ILIKE '%rhetoric%'
           OR methodology ILIKE '%linguistic%'
           OR name_en ILIKE '%kashaf%'
           OR name_en ILIKE '%razi%'
           OR name_en ILIKE '%su%ud%'
           OR name_en ILIKE '%ashur%'
        ORDER BY name_en
    """))

    sources = []
    for row in result:
        print(f"  Found balagha source: {row[1]} ({row[2]})")
        sources.append(row[0])

    # Also include priority sources if they exist
    for source_id in PRIORITY_SOURCES:
        if source_id not in sources:
            check = session.execute(text(
                "SELECT id FROM tafseer_sources WHERE id = :id"
            ), {"id": source_id}).fetchone()
            if check:
                sources.append(source_id)
                print(f"  Added priority source: {source_id}")

    # If no priority sources found, use fallback sources
    if not sources:
        print("  No priority balagha sources found, using fallback sources...")
        for source_id in FALLBACK_SOURCES:
            check = session.execute(text(
                "SELECT id, name_en FROM tafseer_sources WHERE id = :id"
            ), {"id": source_id}).fetchone()
            if check:
                sources.append(source_id)
                print(f"  Added fallback source: {source_id} ({check[1]})")

    return sources


def search_tafsir_for_device(
    session: Session,
    device_id: str,
    search_terms: List[str],
    source_ids: List[str],
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Search tafsir chunks for mentions of a specific rhetorical device.

    Returns list of matches with chunk info, verse reference, and matched text.
    """
    matches = []

    # Build search pattern
    # We use ILIKE for case-insensitive search
    for term in search_terms:
        # Search in chunk content
        query = text("""
            SELECT
                tc.id::text as chunk_id,
                tc.source_id,
                tc.sura_no,
                tc.aya_start,
                tc.aya_end,
                SUBSTRING(COALESCE(tc.content_ar, tc.content_en, ''), 1, 500) as snippet,
                ts.name_ar as source_name_ar,
                ts.name_en as source_name_en
            FROM tafseer_chunks tc
            JOIN tafseer_sources ts ON tc.source_id = ts.id
            WHERE tc.source_id = ANY(:source_ids)
              AND (tc.content_ar ILIKE :pattern OR tc.content_en ILIKE :pattern)
            ORDER BY tc.sura_no, tc.aya_start
            LIMIT :limit
        """)

        result = session.execute(query, {
            "source_ids": source_ids,
            "pattern": f"%{term}%",
            "limit": limit,
        })

        for row in result:
            matches.append({
                "device_id": device_id,
                "chunk_id": row[0],
                "source_id": row[1],
                "sura_no": row[2],
                "ayah_start": row[3],
                "ayah_end": row[4] or row[3],
                "snippet": row[5],
                "source_name_ar": row[6],
                "source_name_en": row[7],
                "matched_term": term,
            })

    return matches


def create_occurrence(
    session: Session,
    device_id: str,
    sura_no: int,
    ayah_start: int,
    ayah_end: int,
    text_snippet: Optional[str],
    explanation_ar: Optional[str],
    evidence_chunk_ids: List[str],
    source: str = "balagha_tafsir",
) -> Optional[int]:
    """
    Create a rhetorical occurrence with evidence grounding.

    Returns the occurrence ID or None if already exists.
    """
    # Check if occurrence already exists for this device + verse
    existing = session.execute(text("""
        SELECT id FROM rhetorical_occurrences
        WHERE device_type_id = :device_id
          AND sura_no = :sura_no
          AND ayah_start = :ayah_start
    """), {
        "device_id": device_id,
        "sura_no": sura_no,
        "ayah_start": ayah_start,
    }).fetchone()

    if existing:
        # Update evidence if new chunks found
        session.execute(text("""
            UPDATE rhetorical_occurrences
            SET evidence_chunk_ids = array_cat(evidence_chunk_ids, :new_chunks),
                updated_at = NOW()
            WHERE id = :id
        """), {
            "id": existing[0],
            "new_chunks": evidence_chunk_ids,
        })
        return None  # Not a new occurrence

    # Create new occurrence
    result = session.execute(text("""
        INSERT INTO rhetorical_occurrences
            (device_type_id, sura_no, ayah_start, ayah_end,
             text_snippet_ar, explanation_ar,
             evidence_chunk_ids, confidence, source, is_verified, created_at)
        VALUES
            (:device_id, :sura_no, :ayah_start, :ayah_end,
             :snippet, :explanation,
             :evidence, 0.7, :source, false, NOW())
        RETURNING id
    """), {
        "device_id": device_id,
        "sura_no": sura_no,
        "ayah_start": ayah_start,
        "ayah_end": ayah_end,
        "snippet": text_snippet[:200] if text_snippet else None,
        "explanation": explanation_ar[:500] if explanation_ar else None,
        "evidence": evidence_chunk_ids,
        "source": source,
    })

    return result.fetchone()[0]


def extract_rhetoric_for_device(
    session: Session,
    device_id: str,
    source_ids: List[str],
    limit: int = 100,
) -> Tuple[int, int]:
    """
    Extract rhetorical occurrences for a single device type.

    Returns (created_count, matched_count)
    """
    search_terms = DEVICE_SEARCH_TERMS.get(device_id, [])
    if not search_terms:
        return 0, 0

    # Find matches in tafsir
    matches = search_tafsir_for_device(
        session, device_id, search_terms, source_ids, limit
    )

    if not matches:
        return 0, 0

    # Group matches by verse
    by_verse: Dict[Tuple[int, int], List[Dict]] = defaultdict(list)
    for match in matches:
        key = (match["sura_no"], match["ayah_start"])
        by_verse[key].append(match)

    created_count = 0
    for (sura_no, ayah_start), verse_matches in by_verse.items():
        # Collect all evidence chunk IDs for this verse
        evidence_chunks = list(set(m["chunk_id"] for m in verse_matches))

        # Get ayah_end (max from matches)
        ayah_end = max(m["ayah_end"] for m in verse_matches)

        # Get a snippet from the first match
        snippet = verse_matches[0].get("snippet")
        explanation = f"تم استخراج من: {verse_matches[0].get('source_name_ar', '')}"

        # Create occurrence
        occ_id = create_occurrence(
            session,
            device_id=device_id,
            sura_no=sura_no,
            ayah_start=ayah_start,
            ayah_end=ayah_end,
            text_snippet=snippet,
            explanation_ar=explanation,
            evidence_chunk_ids=evidence_chunks,
        )

        if occ_id:
            created_count += 1

    return created_count, len(matches)


def run_extraction(
    session: Session,
    source_filter: Optional[str] = None,
    device_filter: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Tuple[int, int]]:
    """
    Run the full extraction process.

    Returns dict mapping device_id -> (created, matched)
    """
    results = {}

    # Find balagha sources
    print("\nFinding balagha-focused tafsir sources...")
    source_ids = find_balagha_sources(session)

    if source_filter:
        source_ids = [s for s in source_ids if source_filter.lower() in s.lower()]

    if not source_ids:
        print("WARNING: No balagha tafsir sources found!")
        print("Available sources:")
        for src in get_available_sources(session):
            print(f"  - {src['id']}: {src['name_en']}")
        return results

    print(f"\nUsing {len(source_ids)} tafsir sources: {source_ids}")

    # Get device types to process
    if device_filter:
        device_ids = [device_filter]
    else:
        device_ids = list(DEVICE_SEARCH_TERMS.keys())

    print(f"\nProcessing {len(device_ids)} rhetorical device types...")

    for device_id in device_ids:
        # Verify device exists in database
        exists = session.execute(text(
            "SELECT 1 FROM rhetorical_device_types WHERE id = :id"
        ), {"id": device_id}).fetchone()

        if not exists:
            print(f"  Skipping {device_id}: not in database")
            continue

        created, matched = extract_rhetoric_for_device(
            session, device_id, source_ids, limit
        )
        results[device_id] = (created, matched)

        if matched > 0:
            print(f"  {device_id}: {matched} matches -> {created} new occurrences")
        else:
            print(f"  {device_id}: no matches found")

    return results


def print_summary(session: Session, results: Dict[str, Tuple[int, int]]):
    """Print extraction summary."""
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    total_created = sum(r[0] for r in results.values())
    total_matched = sum(r[1] for r in results.values())

    print(f"\nTotal tafsir matches: {total_matched}")
    print(f"New occurrences created: {total_created}")

    # Count by category
    result = session.execute(text("""
        SELECT dt.category, COUNT(*)
        FROM rhetorical_occurrences ro
        JOIN rhetorical_device_types dt ON ro.device_type_id = dt.id
        WHERE ro.is_verified = false
        GROUP BY dt.category
    """))

    print("\nUnverified occurrences by category:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    # Top devices
    top_result = session.execute(text("""
        SELECT ro.device_type_id, dt.name_en, COUNT(*)
        FROM rhetorical_occurrences ro
        JOIN rhetorical_device_types dt ON ro.device_type_id = dt.id
        GROUP BY ro.device_type_id, dt.name_en
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """))

    print("\nTop devices by occurrence count:")
    for row in top_result:
        print(f"  {row[1]}: {row[2]}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract rhetorical device occurrences from tafsir"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Filter by tafsir source ID (e.g., zamakhshari)"
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Extract for specific device only (e.g., istiaara)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max matches per device/term (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List available tafsir sources and exit"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RHETORIC EXTRACTION FROM TAFSIR")
    print("=" * 60)

    # Connect to database
    db_url = get_db_url()
    print(f"\nConnecting to database...")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # List sources if requested
        if args.list_sources:
            print("\nAvailable tafsir sources:")
            for src in get_available_sources(session):
                print(f"  {src['id']}: {src['name_en']} ({src['name_ar']})")
            return

        # Check if tables exist
        table_check = session.execute(text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'rhetorical_occurrences'
        """)).fetchone()

        if not table_check:
            print("\nERROR: rhetorical_occurrences table does not exist!")
            print("Run migration first: alembic upgrade head")
            sys.exit(1)

        tafsir_check = session.execute(text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'tafseer_chunks'
        """)).fetchone()

        if not tafsir_check:
            print("\nERROR: tafseer_chunks table does not exist!")
            print("Tafsir data must be loaded first.")
            sys.exit(1)

        if args.dry_run:
            print("\n[DRY RUN] Would extract from these devices:")
            for device_id, terms in DEVICE_SEARCH_TERMS.items():
                print(f"  {device_id}: {terms}")
            print(f"\nLimit per device: {args.limit}")
            return

        # Run extraction
        results = run_extraction(
            session,
            source_filter=args.source,
            device_filter=args.device,
            limit=args.limit,
        )

        session.commit()

        # Print summary
        print_summary(session, results)

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print("\nNote: All new occurrences are marked is_verified=False")
    print("Scholar review required before verification.")


if __name__ == "__main__":
    main()
