#!/usr/bin/env python3
"""
Extract Theme Segments from Tafsir for Quranic Themes

This script:
1. Searches tafsir chunks for theme-related Arabic terms
2. Parses context to identify the verse range being discussed
3. Creates ThemeSegment entries with evidence_chunk_ids
4. Marks all extractions as is_verified=False for scholar review

EPISTEMIC GROUNDING:
===================
All segments MUST have at least one evidence_chunk_id from approved tafsirs.
Manual curation takes priority - this script adds supporting verses.

Approved Tafsir Sources (4 Madhabs Only):
1. Ibn Kathir (ibn_kathir_ar)
2. Al-Tabari (tabari_ar)
3. Al-Qurtubi (qurtubi_ar)
4. Al-Nasafi (nasafi_ar)
5. Al-Shinqiti (shinqiti_ar)

Usage:
    python scripts/ingest/extract_themes_from_tafsir.py [--theme theme_tawheed] [--limit 100]
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

from app.models.theme import QuranicTheme, ThemeSegment


# =============================================================================
# ARABIC SEARCH TERMS FOR QURANIC THEMES
# =============================================================================

# Maps theme ID to Arabic search terms (for content search)
THEME_SEARCH_TERMS: Dict[str, List[str]] = {
    # Aqidah (Theology)
    "theme_tawheed": ["التوحيد", "توحيد الله", "لا إله إلا الله", "الوحدانية", "إله واحد"],
    "theme_tawheed_rububiyyah": ["الربوبية", "رب العالمين", "الخلق والرزق", "التدبير"],
    "theme_tawheed_uluhiyyah": ["الألوهية", "العبادة", "لا تعبدوا", "اعبدوا ربكم"],
    "theme_asma_sifat": ["الأسماء والصفات", "الأسماء الحسنى", "صفات الله"],
    "theme_shirk": ["الشرك", "أشركوا", "الشريك", "الأصنام", "الأوثان"],

    # Iman (Faith)
    "theme_iman_billah": ["الإيمان بالله", "آمنوا بالله", "المؤمنون"],
    "theme_iman_malaika": ["الملائكة", "جبريل", "الكرام الكاتبون"],
    "theme_iman_kutub": ["الكتب المنزلة", "القرآن", "التوراة", "الإنجيل"],
    "theme_iman_rusul": ["الرسل", "الأنبياء", "رسول الله"],
    "theme_iman_yawm_akhir": ["اليوم الآخر", "يوم القيامة", "البعث", "الحساب"],
    "theme_iman_qadr": ["القدر", "القضاء والقدر", "المشيئة"],
    "theme_jannah": ["الجنة", "جنات", "النعيم", "الفردوس"],
    "theme_nar": ["النار", "جهنم", "العذاب", "السعير"],

    # Ibadat (Worship)
    "theme_salah": ["الصلاة", "أقيموا الصلاة", "المصلون", "صلّوا"],
    "theme_zakah": ["الزكاة", "آتوا الزكاة", "الإنفاق", "أنفقوا"],
    "theme_siyam": ["الصيام", "صوم رمضان", "الصائمون"],
    "theme_hajj": ["الحج", "حج البيت", "الكعبة", "المناسك"],
    "theme_dua": ["الدعاء", "ادعوني", "استجب لكم", "يدعو ربه"],
    "theme_dhikr": ["الذكر", "اذكروا الله", "التسبيح"],
    "theme_tawbah": ["التوبة", "توبوا إلى الله", "الاستغفار", "التائبون"],

    # Individual Ethics
    "theme_sidq": ["الصدق", "الصادقون", "الصادقين"],
    "theme_sabr": ["الصبر", "الصابرون", "الصابرين", "اصبروا"],
    "theme_ikhlas": ["الإخلاص", "مخلصين له الدين"],
    "theme_tawadu": ["التواضع", "الخاشعين", "اللين"],
    "theme_shukr": ["الشكر", "اشكروا", "الشاكرون"],
    "theme_taqwa": ["التقوى", "اتقوا الله", "المتقون", "المتقين"],
    "theme_tawakkul": ["التوكل", "توكلوا على الله", "المتوكلون"],
    "theme_khushu": ["الخشوع", "الخاشعين", "يخشون ربهم"],

    # Social Ethics
    "theme_birr_walidayn": ["بر الوالدين", "والوالدين إحساناً", "أمك ثم أمك"],
    "theme_silat_rahim": ["صلة الرحم", "الأرحام", "ذي القربى"],
    "theme_adl": ["العدل", "اعدلوا", "القسط", "المقسطين"],
    "theme_ihsan": ["الإحسان", "أحسنوا", "المحسنين"],
    "theme_amanah": ["الأمانة", "الأمانات", "المؤتمنون"],
    "theme_infaq": ["الإنفاق في سبيل الله", "أنفقوا", "المنفقين"],
    "theme_islah": ["الإصلاح", "المصلحون", "أصلحوا بينهم"],

    # Prohibitions
    "theme_zulm": ["الظلم", "الظالمون", "الظالمين", "لا تظلمون"],
    "theme_kidhb": ["الكذب", "الكاذبون", "الكاذبين", "الافتراء"],
    "theme_ghish": ["الغش", "المطففين", "الكيل والميزان"],
    "theme_riba": ["الربا", "أكل الربا", "البيع الحرام"],
    "theme_kibr": ["الكبر", "المتكبرين", "الاستكبار"],
    "theme_uquq_walidayn": ["عقوق الوالدين", "أف", "لا تقل لهما أف"],
    "theme_nifaq": ["النفاق", "المنافقون", "المنافقين"],
    "theme_fasad": ["الفساد", "المفسدون", "المفسدين", "الفساد في الأرض"],

    # Divine Laws
    "theme_sunnah_nasr": ["سنة النصر", "ينصر الله", "النصر للمؤمنين"],
    "theme_sunnah_ihlak": ["إهلاك الأمم", "أهلكنا", "عاقبة المكذبين"],
    "theme_sunnah_istidraj": ["الاستدراج", "نملي لهم", "الإملاء"],
    "theme_sunnah_taghyir": ["التغيير", "لا يغير الله", "يغيروا ما بأنفسهم"],
    "theme_maghfira": ["المغفرة", "الغفور", "يغفر الذنوب"],
    "theme_rahma": ["رحمة الله", "الرحمن الرحيم", "رحمتي وسعت"],
    "theme_sunnah_ibtila": ["الابتلاء", "نبلوكم", "الفتنة"],
}

# Approved tafsir source IDs
APPROVED_SOURCES = [
    "ibn_kathir_ar",
    "tabari_ar",
    "qurtubi_ar",
    "nasafi_ar",
    "shinqiti_ar",
]


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def get_available_sources(session: Session) -> List[Dict[str, Any]]:
    """Get list of available tafsir sources."""
    result = session.execute(text("""
        SELECT id, name_ar, name_en, author_ar
        FROM tafseer_sources
        ORDER BY id
    """))
    return [{"id": r[0], "name_ar": r[1], "name_en": r[2], "author_ar": r[3]} for r in result]


def search_tafsir_chunks(
    session: Session,
    search_terms: List[str],
    source_ids: List[str],
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Search tafsir chunks for theme-related terms.
    Returns chunks with verse references.
    """
    # Build OR pattern for terms
    terms_pattern = "|".join(search_terms)

    results = []

    for source_id in source_ids:
        try:
            query = text("""
                SELECT
                    tc.id,
                    tc.sura_no,
                    tc.aya_start,
                    tc.content_ar,
                    ts.id as source_id,
                    ts.name_ar as source_name
                FROM tafseer_chunks tc
                JOIN tafseer_sources ts ON tc.source_id = ts.id
                WHERE ts.id = :source_id
                AND tc.content_ar ~* :pattern
                ORDER BY tc.sura_no, tc.aya_start
                LIMIT :limit
            """)

            result = session.execute(query, {
                "source_id": source_id,
                "pattern": terms_pattern,
                "limit": limit,
            })

            for row in result:
                results.append({
                    "chunk_id": row[0],
                    "sura_no": row[1],
                    "ayah_no": row[2],
                    "content_ar": row[3],
                    "source_id": row[4],
                    "source_name": row[5],
                })

        except Exception as e:
            print(f"  Warning: Error searching {source_id}: {e}")

    return results


def extract_context_snippet(content: str, search_terms: List[str], max_length: int = 200) -> str:
    """Extract a context snippet around the first matching term."""
    for term in search_terms:
        if term in content:
            idx = content.find(term)
            start = max(0, idx - 50)
            end = min(len(content), idx + len(term) + 150)
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            return snippet
    return content[:max_length] + "..."


def get_existing_segments(session: Session, theme_id: str) -> set:
    """Get existing segment IDs for a theme to avoid duplicates."""
    result = session.execute(
        select(ThemeSegment.id).where(ThemeSegment.theme_id == theme_id)
    )
    return {row[0] for row in result}


def create_segment_id(theme_id: str, sura: int, ayah: int) -> str:
    """Generate segment ID in format: theme_id:sura:ayah"""
    return f"{theme_id}:{sura}:{ayah}"


def extract_segments_for_theme(
    session: Session,
    theme_id: str,
    search_terms: List[str],
    source_ids: List[str],
    limit: int = 100,
    dry_run: bool = False
) -> int:
    """
    Extract segments for a specific theme from tafsir.
    Returns count of segments created.
    """
    print(f"\n  Extracting for: {theme_id}")
    print(f"    Search terms: {', '.join(search_terms[:3])}...")

    # Search tafsir chunks
    chunks = search_tafsir_chunks(session, search_terms, source_ids, limit * 10)
    print(f"    Found {len(chunks)} matching chunks")

    if not chunks:
        return 0

    # Get existing segments to avoid duplicates
    existing_ids = get_existing_segments(session, theme_id)
    print(f"    Existing segments: {len(existing_ids)}")

    # Group by verse and collect evidence
    verse_evidence: Dict[Tuple[int, int], List[Dict]] = defaultdict(list)
    for chunk in chunks:
        key = (chunk["sura_no"], chunk["ayah_no"])
        verse_evidence[key].append({
            "source_id": chunk["source_id"],
            "chunk_id": chunk["chunk_id"],
            "snippet": extract_context_snippet(chunk["content_ar"], search_terms),
        })

    # Sort by sura/ayah and take top results
    sorted_verses = sorted(verse_evidence.keys())[:limit]
    print(f"    Processing {len(sorted_verses)} verses")

    created_count = 0

    for idx, (sura, ayah) in enumerate(sorted_verses):
        segment_id = create_segment_id(theme_id, sura, ayah)

        if segment_id in existing_ids:
            continue

        evidence = verse_evidence[(sura, ayah)]
        evidence_sources = [
            {"source_id": e["source_id"], "chunk_id": e["chunk_id"], "snippet": e["snippet"]}
            for e in evidence[:3]  # Max 3 evidence sources
        ]
        evidence_chunk_ids = [e["chunk_id"] for e in evidence[:3]]

        if dry_run:
            print(f"      [DRY RUN] Would create: {segment_id}")
            created_count += 1
            continue

        # Create segment
        segment = ThemeSegment(
            id=segment_id,
            theme_id=theme_id,
            segment_order=idx + 100,  # High order to distinguish from manual
            sura_no=sura,
            ayah_start=ayah,
            ayah_end=ayah,
            summary_ar=f"آية تتعلق بموضوع: {theme_id.replace('theme_', '')}",
            summary_en=f"Verse related to theme: {theme_id.replace('theme_', '')}",
            semantic_tags=[theme_id.replace("theme_", "")],
            is_entry_point=False,
            is_verified=False,  # CRITICAL: Not verified
            importance_weight=0.3,  # Lower weight for extracted
            evidence_sources=evidence_sources,
            evidence_chunk_ids=evidence_chunk_ids,
            created_at=datetime.utcnow(),
        )
        session.add(segment)
        created_count += 1

    if not dry_run:
        session.commit()

    print(f"    Created {created_count} new segments")
    return created_count


def update_theme_metadata(session: Session, theme_id: str):
    """Update theme metadata after extraction."""
    # Get segments for this theme
    segments = session.execute(
        select(ThemeSegment).where(ThemeSegment.theme_id == theme_id)
    ).scalars().all()

    theme = session.execute(
        select(QuranicTheme).where(QuranicTheme.id == theme_id)
    ).scalar_one_or_none()

    if not theme:
        return

    # Update counts
    theme.segment_count = len(segments)
    theme.total_verses = sum(s.ayah_end - s.ayah_start + 1 for s in segments)
    theme.suras_mentioned = sorted(list(set(s.sura_no for s in segments)))
    theme.updated_at = datetime.utcnow()

    session.commit()


def print_summary(session: Session):
    """Print summary of extraction results."""
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    # Count by verification status
    result = session.execute(text("""
        SELECT
            is_verified,
            COUNT(*)
        FROM theme_segments
        GROUP BY is_verified
        ORDER BY is_verified
    """))

    for row in result:
        status = "Verified (manual)" if row[0] else "Unverified (extracted)"
        print(f"  {status}: {row[1]} segments")

    # Total
    total = session.execute(text("SELECT COUNT(*) FROM theme_segments")).scalar()
    print(f"\n  Total segments: {total}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract theme segments from tafsir"
    )
    parser.add_argument(
        "--theme",
        type=str,
        help="Extract for specific theme ID only (e.g., theme_tawheed)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max segments per theme (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes"
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List available tafsir sources and exit"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("QURANIC THEME EXTRACTOR")
    print("=" * 60)
    print("Methodology: Sunni Orthodox - 4 Madhabs Only")
    print("All extractions marked as UNVERIFIED for scholar review")
    print("=" * 60)

    # Connect to database
    db_url = get_db_url()
    print(f"\nConnecting to database...")
    engine = create_engine(db_url)

    with Session(engine) as session:
        # List sources if requested
        if args.list_sources:
            sources = get_available_sources(session)
            print("\nAvailable tafsir sources:")
            for src in sources:
                approved = "✓" if src["id"] in APPROVED_SOURCES else " "
                print(f"  [{approved}] {src['id']}: {src['name_ar']} ({src['name_en']})")
            return

        # Filter to approved sources only
        print(f"\nApproved sources: {', '.join(APPROVED_SOURCES)}")

        # Determine which themes to process
        if args.theme:
            if args.theme not in THEME_SEARCH_TERMS:
                print(f"\nERROR: Unknown theme '{args.theme}'")
                print("Available themes:")
                for theme_id in sorted(THEME_SEARCH_TERMS.keys()):
                    print(f"  {theme_id}")
                sys.exit(1)
            themes_to_process = {args.theme: THEME_SEARCH_TERMS[args.theme]}
        else:
            themes_to_process = THEME_SEARCH_TERMS

        print(f"\nProcessing {len(themes_to_process)} themes...")

        # Extract for each theme
        total_created = 0
        for theme_id, search_terms in themes_to_process.items():
            # Verify theme exists in database
            theme_exists = session.execute(
                select(QuranicTheme).where(QuranicTheme.id == theme_id)
            ).scalar_one_or_none()

            if not theme_exists:
                print(f"\n  SKIP: Theme '{theme_id}' not found in database")
                continue

            created = extract_segments_for_theme(
                session,
                theme_id,
                search_terms,
                APPROVED_SOURCES,
                limit=args.limit,
                dry_run=args.dry_run,
            )
            total_created += created

            # Update metadata
            if not args.dry_run and created > 0:
                update_theme_metadata(session, theme_id)

        # Print summary
        if not args.dry_run:
            print_summary(session)

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total segments created: {total_created}")

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
