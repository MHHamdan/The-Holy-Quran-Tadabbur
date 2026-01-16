#!/usr/bin/env python3
"""
Quran-wide Theme Segment Discovery Script

Discovers ALL relevant verses for each theme across the entire Quran (6236 verses).
Uses a 3-stage retrieval pipeline: Lexical → Semantic → Tafsir Confirmation.

Two modes:
- strict: Only adds verses with tafsir evidence support
- suggest: Produces candidates for human review

Hard Constraints:
- Never modifies Quran text
- Every new segment must have tafsir evidence from approved Sunni sources
- Deterministic and idempotent (safe to rerun)

Usage:
    python scripts/ingest/discover_theme_segments_quran_wide.py --mode strict --all
    python scripts/ingest/discover_theme_segments_quran_wide.py --mode suggest --all --output suggestions.json
    python scripts/ingest/discover_theme_segments_quran_wide.py --mode strict --theme theme_tawheed

Author: Claude Code (Tadabbur-AI)
"""

import sys
import os
import re
import json
import argparse
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Approved Sunni tafsir sources
APPROVED_SOURCES = [
    'ibn_kathir_ar',
    'qurtubi_ar',
    'tabari_ar',
    'nasafi_ar',
    'shinqiti_ar',
    'muyassar_ar',
]

# Core themes requiring >=2 tafsir sources
CORE_THEMES = {
    'theme_tawheed', 'theme_salah', 'theme_zakah', 'theme_siyam', 'theme_hajj',
    'theme_birr_walidayn', 'theme_sidq', 'theme_riba', 'theme_shirk',
}

# Thresholds (configurable)
DEFAULT_SEMANTIC_THRESHOLD = 0.62
DEFAULT_TAFSIR_THRESHOLD = 0.55
DEFAULT_MIN_SOURCES_CORE = 2
DEFAULT_MIN_SOURCES_REGULAR = 1

# Arabic diacritics for normalization
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670]')

# Alef variants
ALEF_VARIANTS = {
    '\u0622': '\u0627', '\u0623': '\u0627', '\u0625': '\u0627', '\u0671': '\u0627',
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ThemeProfile:
    """Profile of a theme for matching."""
    theme_id: str
    title_ar: str
    title_en: str
    key_concepts: List[str]
    description_ar: str
    keywords_normalized: List[str]
    roots: List[str]
    is_core: bool


@dataclass
class VerseCandidate:
    """A candidate verse for a theme."""
    verse_id: int
    sura_no: int
    aya_no: int
    text_uthmani: str
    text_normalized: str

    # Match info
    match_type: str  # lexical, root, semantic, mixed
    lexical_score: float
    semantic_score: float
    tafsir_support_score: float
    confidence: float

    # Evidence
    evidence_chunk_ids: List[str] = field(default_factory=list)
    evidence_sources: List[Dict] = field(default_factory=list)
    matching_keywords: List[str] = field(default_factory=list)

    # Reasoning
    reasons_ar: str = ""
    reasons_en: str = ""

    @property
    def combined_score(self) -> float:
        """Combine scores with weights."""
        return (
            0.3 * self.lexical_score +
            0.3 * self.semantic_score +
            0.4 * self.tafsir_support_score
        )


@dataclass
class DiscoveryResult:
    """Result of discovery for a single theme."""
    theme_id: str
    title_ar: str
    existing_segments: int
    candidates_found: int
    strict_additions: int
    suggestions: int
    candidates: List[VerseCandidate] = field(default_factory=list)


@dataclass
class DiscoveryReport:
    """Full discovery report."""
    timestamp: str
    mode: str
    themes_processed: int = 0
    total_candidates: int = 0
    total_strict_additions: int = 0
    total_suggestions: int = 0
    results: List[DiscoveryResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for matching."""
    if not text:
        return ""
    result = text
    result = ARABIC_DIACRITICS.sub('', result)
    for variant, normalized in ALEF_VARIANTS.items():
        result = result.replace(variant, normalized)
    return result


def extract_roots(text: str) -> List[str]:
    """Extract Arabic root patterns (simplified)."""
    # This is a simplified version - a full implementation would use
    # morphological analysis (e.g., from quranic corpus)
    normalized = normalize_arabic(text)
    words = normalized.split()
    roots = []
    for word in words:
        # Simple 3-letter root extraction (very basic)
        letters = [c for c in word if '\u0621' <= c <= '\u064A']
        if len(letters) >= 3:
            roots.append(''.join(letters[:3]))
    return list(set(roots))


def calculate_lexical_match(verse_text: str, keywords: List[str]) -> Tuple[float, List[str]]:
    """Calculate lexical match score."""
    verse_norm = normalize_arabic(verse_text)
    matching = []
    for kw in keywords:
        kw_norm = normalize_arabic(kw)
        if kw_norm in verse_norm:
            matching.append(kw)

    if not keywords:
        return 0.0, []

    score = len(matching) / len(keywords)
    return score, matching


def generate_reasons_ar(
    theme_title: str,
    matching_keywords: List[str],
    match_type: str,
    evidence_sources: Optional[List[Dict]] = None,
    confidence: float = 0.0
) -> str:
    """
    Generate scholarly Arabic reasoning for why verse belongs to theme.

    This function creates more detailed, tafsir-grounded explanations that
    explain the connection methodology and supporting evidence.
    """
    parts = []

    # Opening based on match type
    match_type_intros = {
        'lexical': 'تتضمن الآية ألفاظاً صريحة',
        'root': 'تحتوي الآية على جذور لغوية',
        'semantic': 'تتناسب الآية دلالياً',
        'mixed': 'ترتبط الآية',
    }
    intro = match_type_intros.get(match_type, 'تتعلق الآية')
    parts.append(f"{intro} في موضوع {theme_title}.")

    # Add matching keywords if present
    if matching_keywords:
        kw_display = matching_keywords[:4]  # Limit to 4 keywords
        if len(kw_display) == 1:
            parts.append(f"وردت لفظة «{kw_display[0]}» الدالة على هذا المعنى.")
        else:
            kw_str = '، '.join(f"«{kw}»" for kw in kw_display[:-1])
            kw_str += f" و«{kw_display[-1]}»"
            parts.append(f"وردت ألفاظ: {kw_str}.")

    # Add tafsir evidence if present
    if evidence_sources and len(evidence_sources) > 0:
        sources_count = len(evidence_sources)
        source_names = []
        for src in evidence_sources[:3]:
            source_id = src.get('source_id', '')
            # Map source IDs to readable names (all approved Sunni tafsir)
            source_map = {
                'ibn_kathir_ar': 'ابن كثير',
                'ibn_kathir': 'ابن كثير',
                'tabari_ar': 'الطبري',
                'tabari': 'الطبري',
                'qurtubi_ar': 'القرطبي',
                'qurtubi': 'القرطبي',
                'baghawi_ar': 'البغوي',
                'baghawi': 'البغوي',
                'saadi_ar': 'السعدي',
                'saadi': 'السعدي',
                'jalalayn_ar': 'الجلالين',
                'jalalayn': 'الجلالين',
                'shinqiti_ar': 'الشنقيطي',
                'shinqiti': 'الشنقيطي',
                'muyassar_ar': 'التفسير الميسر',
                'muyassar': 'التفسير الميسر',
                'nasafi_ar': 'النسفي',
                'nasafi': 'النسفي',
            }
            name = source_map.get(source_id, source_id)
            if name:
                source_names.append(name)

        if source_names:
            if len(source_names) == 1:
                parts.append(f"أشار إلى ذلك {source_names[0]} في تفسيره.")
            else:
                names_str = ' و'.join([', '.join(source_names[:-1]), source_names[-1]])
                parts.append(f"وقد أشار إلى هذا المعنى {names_str}.")

        if sources_count > 3:
            parts.append(f"مع {sources_count - 3} مصادر أخرى تؤيد هذا الربط.")

    # Add confidence qualifier if low
    if confidence < 0.6:
        parts.append("(يحتاج مراجعة)")

    return " ".join(parts)


# =============================================================================
# DATABASE QUERIES
# =============================================================================

def get_db_url() -> str:
    """Get database URL."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def fetch_all_themes(session: Session) -> List[Dict]:
    """Fetch all themes with their profiles."""
    result = session.execute(text("""
        SELECT id, title_ar, title_en, key_concepts, description_ar
        FROM quranic_themes
        ORDER BY order_of_importance
    """))

    themes = []
    for row in result:
        themes.append({
            'id': row[0],
            'title_ar': row[1],
            'title_en': row[2],
            'key_concepts': row[3] or [],
            'description_ar': row[4] or '',
        })
    return themes


def fetch_existing_segments(session: Session, theme_id: str) -> Set[Tuple[int, int, int]]:
    """Fetch existing segment verse ranges for a theme."""
    result = session.execute(text("""
        SELECT sura_no, ayah_start, ayah_end
        FROM theme_segments
        WHERE theme_id = :theme_id
    """), {'theme_id': theme_id})

    existing = set()
    for row in result:
        for aya in range(row[1], row[2] + 1):
            existing.add((row[0], aya, aya))
    return existing


def fetch_all_verses(session: Session) -> List[Dict]:
    """Fetch all Quran verses."""
    result = session.execute(text("""
        SELECT id, sura_no, aya_no, text_uthmani, text_normalized
        FROM quran_verses
        ORDER BY sura_no, aya_no
    """))

    verses = []
    for row in result:
        verses.append({
            'id': row[0],
            'sura_no': row[1],
            'aya_no': row[2],
            'text_uthmani': row[3],
            'text_normalized': row[4] or normalize_arabic(row[3]),
        })
    return verses


def fetch_tafsir_for_verse(session: Session, sura: int, aya: int) -> List[Dict]:
    """Fetch tafsir chunks for a verse."""
    result = session.execute(text("""
        SELECT chunk_id, source_id, content_ar
        FROM tafseer_chunks
        WHERE sura_no = :sura
          AND aya_start <= :aya
          AND aya_end >= :aya
          AND source_id = ANY(:sources)
          AND content_ar IS NOT NULL
    """), {
        'sura': sura,
        'aya': aya,
        'sources': APPROVED_SOURCES,
    })

    chunks = []
    for row in result:
        chunks.append({
            'chunk_id': row[0],
            'source_id': row[1],
            'content': row[2],
        })
    return chunks


def get_segment_count(session: Session, theme_id: str) -> int:
    """Get current segment count for a theme."""
    result = session.execute(text("""
        SELECT COUNT(*) FROM theme_segments WHERE theme_id = :theme_id
    """), {'theme_id': theme_id})
    return result.scalar() or 0


def insert_segment(
    session: Session,
    theme_id: str,
    candidate: VerseCandidate,
    segment_order: int,
    theme_title_en: str = ""
):
    """Insert a new theme segment."""
    segment_id = f"{theme_id}:{candidate.sura_no}:{candidate.aya_no}"

    # Build evidence_sources JSON
    evidence_sources = [
        {
            'chunk_id': f"{e['source_id'].replace('_ar', '')}:{candidate.sura_no}:{candidate.aya_no}",
            'source_id': e['source_id'],
            'snippet': e.get('content', '')[:200] if e.get('content') else '',
        }
        for e in candidate.evidence_sources[:3]
    ]

    # Generate English title and summary
    title_en = f"Verse {candidate.sura_no}:{candidate.aya_no}"

    # Generate English summary based on match type
    match_desc = {
        'lexical': 'keyword matching',
        'root': 'root-based semantic analysis',
        'semantic': 'semantic similarity',
        'mixed': 'combined lexical and semantic analysis',
    }.get(candidate.match_type, 'discovery')

    summary_en = f"Discovered via {match_desc} with {len(candidate.evidence_chunk_ids)} tafsir sources supporting relevance to {theme_title_en or theme_id.replace('theme_', '').replace('_', ' ')}."

    session.execute(text("""
        INSERT INTO theme_segments (
            id, theme_id, segment_order, sura_no, ayah_start, ayah_end,
            title_ar, title_en, summary_ar, summary_en, match_type, confidence, reasons_ar,
            is_core, evidence_sources, evidence_chunk_ids, discovered_at,
            created_at, updated_at
        ) VALUES (
            :id, :theme_id, :segment_order, :sura_no, :ayah_start, :ayah_end,
            :title_ar, :title_en, :summary_ar, :summary_en, :match_type, :confidence, :reasons_ar,
            :is_core, :evidence_sources, :evidence_chunk_ids, NOW(),
            NOW(), NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
            confidence = :confidence,
            reasons_ar = :reasons_ar,
            updated_at = NOW()
    """), {
        'id': segment_id,
        'theme_id': theme_id,
        'segment_order': segment_order,
        'sura_no': candidate.sura_no,
        'ayah_start': candidate.aya_no,
        'ayah_end': candidate.aya_no,
        'title_ar': f"آية {candidate.sura_no}:{candidate.aya_no}",
        'title_en': title_en,
        'summary_ar': candidate.reasons_ar,
        'summary_en': summary_en,
        'match_type': candidate.match_type,
        'confidence': candidate.confidence,
        'reasons_ar': candidate.reasons_ar,
        'is_core': candidate.confidence >= 0.8,
        'evidence_sources': json.dumps(evidence_sources),
        'evidence_chunk_ids': candidate.evidence_chunk_ids,
    })


# =============================================================================
# DISCOVERY ENGINE
# =============================================================================

def build_theme_profile(theme: Dict) -> ThemeProfile:
    """Build a searchable profile for a theme."""
    keywords = theme['key_concepts'] + [theme['title_ar']]
    keywords_normalized = [normalize_arabic(kw) for kw in keywords]

    # Extract roots from keywords and description
    all_text = ' '.join(keywords) + ' ' + theme['description_ar']
    roots = extract_roots(all_text)

    return ThemeProfile(
        theme_id=theme['id'],
        title_ar=theme['title_ar'],
        title_en=theme['title_en'],
        key_concepts=theme['key_concepts'],
        description_ar=theme['description_ar'],
        keywords_normalized=keywords_normalized,
        roots=roots,
        is_core=theme['id'] in CORE_THEMES,
    )


def calculate_tafsir_support(
    session: Session,
    sura: int,
    aya: int,
    theme_profile: ThemeProfile
) -> Tuple[float, List[Dict], List[str]]:
    """
    Calculate tafsir support score for a verse-theme pair.

    Returns: (score, evidence_sources, chunk_ids)
    """
    tafsir_chunks = fetch_tafsir_for_verse(session, sura, aya)

    if not tafsir_chunks:
        return 0.0, [], []

    evidence_sources = []
    chunk_ids = []
    support_count = 0

    for chunk in tafsir_chunks:
        content_norm = normalize_arabic(chunk['content'])

        # Check if tafsir mentions theme keywords
        keyword_matches = 0
        for kw in theme_profile.keywords_normalized:
            if kw in content_norm:
                keyword_matches += 1

        if keyword_matches > 0:
            support_count += 1
            source_base = chunk['source_id'].replace('_ar', '').replace('_en', '')
            chunk_id = f"{source_base}:{sura}:{aya}"

            evidence_sources.append({
                'chunk_id': chunk_id,
                'source_id': chunk['source_id'],
                'content': chunk['content'][:300],
                'keyword_matches': keyword_matches,
            })
            chunk_ids.append(chunk_id)

    # Score based on source diversity
    unique_sources = len(set(e['source_id'] for e in evidence_sources))

    if unique_sources == 0:
        return 0.0, [], []

    # Higher score for more source diversity
    score = min(1.0, (unique_sources / 3) + (support_count / len(tafsir_chunks)) * 0.3)

    return score, evidence_sources, chunk_ids


def discover_verses_for_theme(
    session: Session,
    theme_profile: ThemeProfile,
    all_verses: List[Dict],
    existing_segments: Set[Tuple[int, int, int]],
    semantic_threshold: float,
    tafsir_threshold: float,
    min_sources: int,
    mode: str,
    max_candidates: int = 100,
    verbose: bool = False
) -> List[VerseCandidate]:
    """
    Discover verses for a theme using 3-stage pipeline.

    Stage R1: Lexical matching
    Stage R2: Semantic matching (simplified without embeddings)
    Stage R3: Tafsir confirmation
    """
    candidates: List[VerseCandidate] = []

    # Stage R1: Lexical matching
    lexical_candidates = []
    for verse in all_verses:
        # Skip already existing
        if (verse['sura_no'], verse['aya_no'], verse['aya_no']) in existing_segments:
            continue

        lexical_score, matching_kw = calculate_lexical_match(
            verse['text_normalized'],
            theme_profile.keywords_normalized
        )

        if lexical_score > 0.1:  # At least one keyword match
            lexical_candidates.append({
                'verse': verse,
                'lexical_score': lexical_score,
                'matching_keywords': matching_kw,
            })

    if verbose:
        logger.info(f"  Stage R1: {len(lexical_candidates)} lexical candidates")

    # Stage R2: Root matching (simplified semantic)
    # For now, we'll use root matching as a simple semantic proxy
    root_candidates = []
    for verse in all_verses:
        if (verse['sura_no'], verse['aya_no'], verse['aya_no']) in existing_segments:
            continue

        verse_roots = extract_roots(verse['text_normalized'])
        common_roots = set(verse_roots) & set(theme_profile.roots)

        if len(common_roots) >= 1:
            root_candidates.append({
                'verse': verse,
                'root_score': len(common_roots) / max(len(theme_profile.roots), 1),
                'common_roots': list(common_roots),
            })

    if verbose:
        logger.info(f"  Stage R2: {len(root_candidates)} root/semantic candidates")

    # Combine candidates
    verse_scores: Dict[int, Dict] = {}

    for lc in lexical_candidates:
        vid = lc['verse']['id']
        verse_scores[vid] = {
            'verse': lc['verse'],
            'lexical_score': lc['lexical_score'],
            'semantic_score': 0.0,
            'matching_keywords': lc['matching_keywords'],
        }

    for rc in root_candidates:
        vid = rc['verse']['id']
        if vid in verse_scores:
            verse_scores[vid]['semantic_score'] = rc['root_score']
        else:
            verse_scores[vid] = {
                'verse': rc['verse'],
                'lexical_score': 0.0,
                'semantic_score': rc['root_score'],
                'matching_keywords': [],
            }

    # Stage R3: Tafsir confirmation
    confirmed_candidates = []
    processed = 0

    for vid, data in verse_scores.items():
        verse = data['verse']
        processed += 1

        if processed > max_candidates * 3:  # Limit processing
            break

        tafsir_score, evidence_sources, chunk_ids = calculate_tafsir_support(
            session,
            verse['sura_no'],
            verse['aya_no'],
            theme_profile
        )

        # Check threshold
        if tafsir_score < tafsir_threshold:
            continue

        # Check source requirements
        unique_sources = len(set(e['source_id'] for e in evidence_sources))
        required_sources = min_sources if not theme_profile.is_core else max(min_sources, DEFAULT_MIN_SOURCES_CORE)

        if unique_sources < required_sources:
            continue

        # Calculate combined score
        lexical = data['lexical_score']
        semantic = data['semantic_score']
        combined = 0.3 * lexical + 0.3 * semantic + 0.4 * tafsir_score

        # Determine match type
        if lexical > 0.3 and semantic > 0.3:
            match_type = 'mixed'
        elif lexical > semantic:
            match_type = 'lexical'
        else:
            match_type = 'root'

        # Create candidate
        candidate = VerseCandidate(
            verse_id=verse['id'],
            sura_no=verse['sura_no'],
            aya_no=verse['aya_no'],
            text_uthmani=verse['text_uthmani'],
            text_normalized=verse['text_normalized'],
            match_type=match_type,
            lexical_score=lexical,
            semantic_score=semantic,
            tafsir_support_score=tafsir_score,
            confidence=combined,
            evidence_chunk_ids=chunk_ids,
            evidence_sources=evidence_sources,
            matching_keywords=data.get('matching_keywords', []),
            reasons_ar=generate_reasons_ar(
                theme_profile.title_ar,
                data.get('matching_keywords', []),
                match_type,
                evidence_sources=evidence_sources,
                confidence=combined
            ),
        )

        confirmed_candidates.append(candidate)

    if verbose:
        logger.info(f"  Stage R3: {len(confirmed_candidates)} tafsir-confirmed candidates")

    # Sort by confidence and limit
    confirmed_candidates.sort(key=lambda c: c.confidence, reverse=True)

    return confirmed_candidates[:max_candidates]


# =============================================================================
# MAIN DISCOVERY FUNCTION
# =============================================================================

def run_discovery(
    session: Session,
    mode: str,
    themes_to_process: Optional[List[str]] = None,
    semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
    tafsir_threshold: float = DEFAULT_TAFSIR_THRESHOLD,
    min_sources: int = DEFAULT_MIN_SOURCES_REGULAR,
    max_per_theme: int = 50,
    dry_run: bool = False,
    verbose: bool = False
) -> DiscoveryReport:
    """
    Run Quran-wide theme discovery.

    Args:
        session: Database session
        mode: 'strict' or 'suggest'
        themes_to_process: List of theme IDs or None for all
        semantic_threshold: Minimum semantic score
        tafsir_threshold: Minimum tafsir support score
        min_sources: Minimum tafsir sources
        max_per_theme: Maximum new segments per theme
        dry_run: If True, don't insert
        verbose: Verbose logging

    Returns:
        DiscoveryReport
    """
    report = DiscoveryReport(
        timestamp=datetime.utcnow().isoformat(),
        mode=mode,
    )

    # Fetch all verses once
    logger.info("Loading all Quran verses...")
    all_verses = fetch_all_verses(session)
    logger.info(f"Loaded {len(all_verses)} verses")

    # Fetch all themes
    all_themes = fetch_all_themes(session)

    if themes_to_process:
        all_themes = [t for t in all_themes if t['id'] in themes_to_process]

    logger.info(f"Processing {len(all_themes)} themes...")

    for theme in all_themes:
        theme_id = theme['id']
        logger.info(f"\nDiscovering for {theme_id} ({theme['title_ar']})...")

        # Build profile
        profile = build_theme_profile(theme)

        # Get existing segments
        existing = fetch_existing_segments(session, theme_id)
        existing_count = get_segment_count(session, theme_id)

        # Discover candidates
        candidates = discover_verses_for_theme(
            session,
            profile,
            all_verses,
            existing,
            semantic_threshold,
            tafsir_threshold,
            min_sources,
            mode,
            max_candidates=max_per_theme * 2,
            verbose=verbose
        )

        # Create result
        result = DiscoveryResult(
            theme_id=theme_id,
            title_ar=theme['title_ar'],
            existing_segments=existing_count,
            candidates_found=len(candidates),
            strict_additions=0,
            suggestions=0,
            candidates=candidates,
        )

        # Process candidates based on mode
        if mode == 'strict' and not dry_run:
            # Insert high-confidence candidates
            inserted = 0
            segment_order = existing_count + 1
            theme_title_en = theme.get('title_en', '')

            for candidate in candidates:
                if candidate.confidence >= 0.5 and inserted < max_per_theme:
                    try:
                        insert_segment(session, theme_id, candidate, segment_order, theme_title_en)
                        inserted += 1
                        segment_order += 1
                        # Commit after each insert to avoid transaction issues
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        report.errors.append(f"Error inserting {theme_id}:{candidate.sura_no}:{candidate.aya_no}: {e}")

            result.strict_additions = inserted
            report.total_strict_additions += inserted

            if inserted > 0:
                logger.info(f"  Inserted {inserted} new segments")

        else:
            # Suggest mode - just report
            result.suggestions = len(candidates)
            report.total_suggestions += len(candidates)

        report.results.append(result)
        report.themes_processed += 1
        report.total_candidates += len(candidates)

    return report


# =============================================================================
# OUTPUT
# =============================================================================

def print_report(report: DiscoveryReport):
    """Print human-readable report."""
    print("\n" + "=" * 70)
    print("QURAN-WIDE THEME DISCOVERY REPORT")
    print("تقرير اكتشاف المحاور على مستوى القرآن")
    print("=" * 70)
    print(f"Timestamp: {report.timestamp}")
    print(f"Mode: {report.mode}")
    print(f"Themes processed: {report.themes_processed}")
    print(f"Total candidates found: {report.total_candidates}")

    if report.mode == 'strict':
        print(f"Total segments added: {report.total_strict_additions}")
    else:
        print(f"Total suggestions: {report.total_suggestions}")

    print("\n" + "-" * 40)
    print("PER-THEME RESULTS")
    print("-" * 40)

    for result in sorted(report.results, key=lambda r: r.candidates_found, reverse=True):
        status = f"+{result.strict_additions}" if result.strict_additions > 0 else f"~{result.suggestions} suggestions"
        print(f"  {result.theme_id}: {result.existing_segments} existing, {result.candidates_found} found ({status})")

    if report.errors:
        print(f"\nErrors: {len(report.errors)}")
        for err in report.errors[:10]:
            print(f"  - {err}")

    print("\n" + "=" * 70)


def export_json(report: DiscoveryReport, filepath: str):
    """Export report with candidates as JSON."""
    # Convert candidates to serializable format
    data = {
        'timestamp': report.timestamp,
        'mode': report.mode,
        'themes_processed': report.themes_processed,
        'total_candidates': report.total_candidates,
        'total_strict_additions': report.total_strict_additions,
        'total_suggestions': report.total_suggestions,
        'errors': report.errors,
        'results': [],
    }

    for result in report.results:
        result_data = {
            'theme_id': result.theme_id,
            'title_ar': result.title_ar,
            'existing_segments': result.existing_segments,
            'candidates_found': result.candidates_found,
            'strict_additions': result.strict_additions,
            'suggestions': result.suggestions,
            'candidates': [
                {
                    'sura_no': c.sura_no,
                    'aya_no': c.aya_no,
                    'text_uthmani': c.text_uthmani[:100] + '...' if len(c.text_uthmani) > 100 else c.text_uthmani,
                    'match_type': c.match_type,
                    'confidence': round(c.confidence, 3),
                    'reasons_ar': c.reasons_ar,
                    'evidence_chunk_ids': c.evidence_chunk_ids[:3],
                    'matching_keywords': c.matching_keywords,
                }
                for c in result.candidates[:20]  # Limit for file size
            ],
        }
        data['results'].append(result_data)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Report exported to: {filepath}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Quran-wide Theme Segment Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Strict mode - add all discovered verses
  python scripts/ingest/discover_theme_segments_quran_wide.py --mode strict --all

  # Suggest mode - generate candidates for review
  python scripts/ingest/discover_theme_segments_quran_wide.py --mode suggest --all --output suggestions.json

  # Single theme
  python scripts/ingest/discover_theme_segments_quran_wide.py --mode strict --theme theme_tawheed
        """
    )

    parser.add_argument(
        "--mode",
        choices=['strict', 'suggest'],
        required=True,
        help="Discovery mode: strict (insert) or suggest (review)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all themes"
    )
    parser.add_argument(
        "--theme",
        type=str,
        help="Process single theme by ID"
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=DEFAULT_SEMANTIC_THRESHOLD,
        help=f"Minimum semantic score (default: {DEFAULT_SEMANTIC_THRESHOLD})"
    )
    parser.add_argument(
        "--tafsir-threshold",
        type=float,
        default=DEFAULT_TAFSIR_THRESHOLD,
        help=f"Minimum tafsir support score (default: {DEFAULT_TAFSIR_THRESHOLD})"
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=DEFAULT_MIN_SOURCES_REGULAR,
        help=f"Minimum tafsir sources (default: {DEFAULT_MIN_SOURCES_REGULAR})"
    )
    parser.add_argument(
        "--max-per-theme",
        type=int,
        default=50,
        help="Maximum new segments per theme (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without inserting"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for suggestions"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Validate args
    if not args.all and not args.theme:
        parser.error("Must specify --all or --theme")

    themes_to_process = None
    if args.theme:
        themes_to_process = [args.theme]

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        report = run_discovery(
            session=session,
            mode=args.mode,
            themes_to_process=themes_to_process,
            semantic_threshold=args.semantic_threshold,
            tafsir_threshold=args.tafsir_threshold,
            min_sources=args.min_sources,
            max_per_theme=args.max_per_theme,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

    print_report(report)

    if args.output:
        export_json(report, args.output)


if __name__ == "__main__":
    main()
