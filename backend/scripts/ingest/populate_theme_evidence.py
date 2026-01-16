#!/usr/bin/env python3
"""
Populate Theme Evidence Script

Populates evidence_chunk_ids and evidence_sources for all ThemeSegments
using tafseer chunks from approved Sunni sources.

Strategy:
1. For each ThemeSegment verse range, find matching tafseer chunks
2. Use round-robin source selection to ensure diversity
3. Store evidence_chunk_ids (list) and evidence_sources (JSON array)

Usage:
    python scripts/ingest/populate_theme_evidence.py
    python scripts/ingest/populate_theme_evidence.py --dry-run
    python scripts/ingest/populate_theme_evidence.py --only theme_tawheed
    python scripts/ingest/populate_theme_evidence.py --min-sources 2
    python scripts/ingest/populate_theme_evidence.py --ci

Exit Codes:
    0: Success
    1: Errors found (in --ci mode)

Author: Claude Code (Tadabbur-AI)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


# =============================================================================
# CONSTANTS
# =============================================================================

# Approved Sunni tafsir sources (priority order for round-robin)
APPROVED_SOURCES_PRIORITY = [
    'ibn_kathir_ar',    # Shafi'i - most comprehensive
    'qurtubi_ar',       # Maliki - fiqh focused
    'tabari_ar',        # Classical - isnad focused
    'nasafi_ar',        # Hanafi - theological
    'shinqiti_ar',      # Hanbali - Quran-explains-Quran
    'muyassar_ar',      # Simplified - fallback
]

# Core themes requiring >=2 distinct sources
CORE_THEMES = {
    'theme_tawheed',
    'theme_salah',
    'theme_zakah',
    'theme_siyam',
    'theme_hajj',
    'theme_birr_walidayn',
    'theme_sidq',
    'theme_riba',
}

# Maximum snippet length (words)
MAX_SNIPPET_WORDS = 25


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EvidenceChunk:
    """A single evidence chunk."""
    chunk_id: str           # Formatted as 'source:sura:aya'
    source_id: str
    sura_no: int
    aya_start: int
    aya_end: int
    snippet: str
    db_chunk_id: str        # Original DB chunk_id (hash)


@dataclass
class SegmentEvidence:
    """Evidence collected for a segment."""
    segment_id: str
    theme_id: str
    sura_no: int
    ayah_start: int
    ayah_end: int
    chunks: List[EvidenceChunk] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(set(c.source_id for c in self.chunks))

    @property
    def coverage(self) -> float:
        """Percentage of ayahs in range covered by evidence."""
        total_ayahs = self.ayah_end - self.ayah_start + 1
        covered = set()
        for chunk in self.chunks:
            for aya in range(chunk.aya_start, chunk.aya_end + 1):
                if self.ayah_start <= aya <= self.ayah_end:
                    covered.add(aya)
        return len(covered) / total_ayahs if total_ayahs > 0 else 0.0


@dataclass
class PopulationReport:
    """Report of evidence population."""
    timestamp: str
    mode: str
    total_segments: int = 0
    segments_populated: int = 0
    segments_already_have: int = 0
    segments_no_chunks_found: int = 0
    total_chunks_added: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Per-theme stats
    theme_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def truncate_snippet(text: str, max_words: int = MAX_SNIPPET_WORDS) -> str:
    """Truncate snippet to max words."""
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'


def format_chunk_id(source_id: str, sura: int, aya: int) -> str:
    """Format chunk ID in human-readable format."""
    # Remove _ar/_en suffix for cleaner ID
    source_base = source_id.replace('_ar', '').replace('_en', '')
    return f"{source_base}:{sura}:{aya}"


def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


# =============================================================================
# DATABASE QUERIES
# =============================================================================

def fetch_segments_needing_evidence(session: Session, only_theme: Optional[str] = None) -> List[Dict]:
    """Fetch theme segments that need evidence."""
    query = """
        SELECT id, theme_id, sura_no, ayah_start, ayah_end,
               evidence_sources, evidence_chunk_ids
        FROM theme_segments
        WHERE 1=1
    """
    params = {}

    if only_theme:
        query += " AND theme_id = :theme_id"
        params['theme_id'] = only_theme

    query += " ORDER BY theme_id, segment_order"

    result = session.execute(text(query), params)

    segments = []
    for row in result:
        segments.append({
            'id': row[0],
            'theme_id': row[1],
            'sura_no': row[2],
            'ayah_start': row[3],
            'ayah_end': row[4],
            'evidence_sources': row[5],
            'evidence_chunk_ids': row[6],
        })
    return segments


def fetch_tafseer_chunks_for_range(
    session: Session,
    sura: int,
    aya_start: int,
    aya_end: int,
    sources: List[str]
) -> List[Dict]:
    """Fetch tafseer chunks covering an ayah range."""
    result = session.execute(text("""
        SELECT chunk_id, source_id, sura_no, aya_start, aya_end,
               LEFT(content_ar, 500) as snippet
        FROM tafseer_chunks
        WHERE sura_no = :sura
          AND aya_start <= :aya_end
          AND aya_end >= :aya_start
          AND source_id = ANY(:sources)
          AND content_ar IS NOT NULL
          AND LENGTH(content_ar) > 10
        ORDER BY source_id, aya_start
    """), {
        'sura': sura,
        'aya_start': aya_start,
        'aya_end': aya_end,
        'sources': sources,
    })

    chunks = []
    for row in result:
        chunks.append({
            'chunk_id': row[0],
            'source_id': row[1],
            'sura_no': row[2],
            'aya_start': row[3],
            'aya_end': row[4],
            'snippet': row[5],
        })
    return chunks


def update_segment_evidence(
    session: Session,
    segment_id: str,
    evidence_chunk_ids: List[str],
    evidence_sources: List[Dict]
):
    """Update a segment with evidence."""
    session.execute(text("""
        UPDATE theme_segments
        SET evidence_chunk_ids = :chunk_ids,
            evidence_sources = :sources,
            updated_at = NOW()
        WHERE id = :segment_id
    """), {
        'segment_id': segment_id,
        'chunk_ids': evidence_chunk_ids,
        'sources': json.dumps(evidence_sources),
    })


# =============================================================================
# EVIDENCE COLLECTION
# =============================================================================

def collect_evidence_for_segment(
    session: Session,
    segment: Dict,
    min_sources: int = 1,
    core_min_sources: int = 2
) -> SegmentEvidence:
    """Collect evidence chunks for a segment."""
    evidence = SegmentEvidence(
        segment_id=segment['id'],
        theme_id=segment['theme_id'],
        sura_no=segment['sura_no'],
        ayah_start=segment['ayah_start'],
        ayah_end=segment['ayah_end'],
    )

    # Determine required sources
    is_core = segment['theme_id'] in CORE_THEMES
    required_sources = core_min_sources if is_core else min_sources

    # Fetch chunks from all approved sources
    chunks = fetch_tafseer_chunks_for_range(
        session,
        segment['sura_no'],
        segment['ayah_start'],
        segment['ayah_end'],
        APPROVED_SOURCES_PRIORITY
    )

    if not chunks:
        return evidence

    # Group chunks by source
    chunks_by_source: Dict[str, List[Dict]] = defaultdict(list)
    for chunk in chunks:
        chunks_by_source[chunk['source_id']].append(chunk)

    # Round-robin selection to ensure diversity
    selected_chunks: List[EvidenceChunk] = []
    sources_used: Set[str] = set()

    # First pass: select one chunk per source in priority order
    for source_id in APPROVED_SOURCES_PRIORITY:
        if source_id in chunks_by_source:
            source_chunks = chunks_by_source[source_id]
            # Select first chunk (usually covers verse start)
            chunk = source_chunks[0]
            selected_chunks.append(EvidenceChunk(
                chunk_id=format_chunk_id(chunk['source_id'], chunk['sura_no'], chunk['aya_start']),
                source_id=chunk['source_id'],
                sura_no=chunk['sura_no'],
                aya_start=chunk['aya_start'],
                aya_end=chunk['aya_end'],
                snippet=truncate_snippet(chunk['snippet']),
                db_chunk_id=chunk['chunk_id'],
            ))
            sources_used.add(source_id)

            # Stop if we have enough sources
            if len(sources_used) >= required_sources:
                break

    evidence.chunks = selected_chunks
    return evidence


# =============================================================================
# MAIN POPULATION FUNCTION
# =============================================================================

def populate_evidence(
    session: Session,
    dry_run: bool = False,
    only_theme: Optional[str] = None,
    min_sources: int = 1,
    force: bool = False,
    verbose: bool = False
) -> PopulationReport:
    """
    Populate evidence for all theme segments.

    Args:
        session: Database session
        dry_run: If True, don't write changes
        only_theme: Filter to specific theme
        min_sources: Minimum sources per segment
        force: Overwrite existing evidence
        verbose: Print detailed output

    Returns:
        PopulationReport with results
    """
    report = PopulationReport(
        timestamp=datetime.utcnow().isoformat(),
        mode="dry-run" if dry_run else "live",
    )

    # Fetch segments
    segments = fetch_segments_needing_evidence(session, only_theme)
    report.total_segments = len(segments)

    print(f"Processing {len(segments)} segments...")

    for i, segment in enumerate(segments):
        if verbose or (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(segments)}] {segment['id']}")

        # Check if already has evidence
        existing_chunks = segment.get('evidence_chunk_ids') or []
        if existing_chunks and not force:
            report.segments_already_have += 1
            continue

        # Collect evidence
        evidence = collect_evidence_for_segment(
            session, segment,
            min_sources=min_sources,
            core_min_sources=2
        )

        if not evidence.chunks:
            report.segments_no_chunks_found += 1
            report.warnings.append(f"No chunks found for {segment['id']}")
            continue

        # Prepare update data
        chunk_ids = [c.chunk_id for c in evidence.chunks]
        sources = [
            {
                'chunk_id': c.chunk_id,
                'source_id': c.source_id,
                'snippet': c.snippet,
            }
            for c in evidence.chunks
        ]

        # Update segment
        if not dry_run:
            try:
                update_segment_evidence(session, segment['id'], chunk_ids, sources)
                report.segments_populated += 1
                report.total_chunks_added += len(chunk_ids)
            except Exception as e:
                report.errors.append(f"Error updating {segment['id']}: {e}")
        else:
            report.segments_populated += 1
            report.total_chunks_added += len(chunk_ids)

        # Track per-theme stats
        theme_id = segment['theme_id']
        if theme_id not in report.theme_stats:
            report.theme_stats[theme_id] = {
                'total': 0,
                'populated': 0,
                'sources_avg': 0,
            }
        report.theme_stats[theme_id]['total'] += 1
        report.theme_stats[theme_id]['populated'] += 1
        report.theme_stats[theme_id]['sources_avg'] = (
            (report.theme_stats[theme_id]['sources_avg'] * (report.theme_stats[theme_id]['populated'] - 1) + evidence.source_count)
            / report.theme_stats[theme_id]['populated']
        )

    # Commit if not dry run
    if not dry_run:
        session.commit()

    return report


# =============================================================================
# OUTPUT
# =============================================================================

def print_report(report: PopulationReport):
    """Print human-readable report."""
    print("\n" + "=" * 60)
    print("EVIDENCE POPULATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Mode: {report.mode}")

    print("\n--- SUMMARY ---")
    print(f"Total segments: {report.total_segments}")
    print(f"Already had evidence: {report.segments_already_have}")
    print(f"Newly populated: {report.segments_populated}")
    print(f"No chunks found: {report.segments_no_chunks_found}")
    print(f"Total chunks added: {report.total_chunks_added}")

    if report.errors:
        print(f"\nErrors: {len(report.errors)}")
        for err in report.errors[:10]:
            print(f"  - {err}")

    if report.warnings:
        print(f"\nWarnings: {len(report.warnings)}")
        for warn in report.warnings[:10]:
            print(f"  - {warn}")

    print("\n--- PER-THEME STATS ---")
    for theme_id, stats in sorted(report.theme_stats.items()):
        print(f"  {theme_id}: {stats['populated']}/{stats['total']} segments, avg {stats['sources_avg']:.1f} sources")

    print("\n" + "=" * 60)
    if report.errors:
        print("STATUS: FAILED")
    else:
        print("STATUS: SUCCESS")
    print("=" * 60)


def export_json(report: PopulationReport, filepath: str):
    """Export report as JSON."""
    from dataclasses import asdict

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)
    print(f"Report exported to: {filepath}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Populate evidence for theme segments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to database"
    )
    parser.add_argument(
        "--only",
        type=str,
        metavar="THEME_ID",
        help="Only process a specific theme"
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=1,
        help="Minimum tafsir sources per segment (default: 1)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing evidence"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="PATH",
        help="Export report as JSON"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 on errors"
    )

    args = parser.parse_args()

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        report = populate_evidence(
            session=session,
            dry_run=args.dry_run,
            only_theme=args.only,
            min_sources=args.min_sources,
            force=args.force,
            verbose=args.verbose,
        )

    print_report(report)

    if args.json:
        export_json(report, args.json)

    # Exit code
    if args.ci and (report.errors or report.segments_no_chunks_found > 0):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
