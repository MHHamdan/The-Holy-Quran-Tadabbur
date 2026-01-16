#!/usr/bin/env python3
"""
Quranic Themes Completeness Audit Script - CI Gate

A FANG-grade validation gate for the Tadabbur Quranic Themes system ensuring:
- No theme ships without Quran grounding
- No theme segment ships without verified ayah references
- Arabic content contains no English leakage
- Theme consequences are logically aligned with Islamic framing
- Theme graph is connected and meaningful

Exit Codes:
- 0: All validations pass (warnings allowed in non-CI mode)
- 1: Any ERROR present in --ci mode or --strict mode

Usage:
    python scripts/verify/theme_completeness_audit.py
    python scripts/verify/theme_completeness_audit.py --ci
    python scripts/verify/theme_completeness_audit.py --json reports/theme_audit.json
    python scripts/verify/theme_completeness_audit.py --markdown reports/theme_audit.md
    python scripts/verify/theme_completeness_audit.py --min-verses 3
    python scripts/verify/theme_completeness_audit.py --strict

Author: Claude Code (Tadabbur-AI)
"""
import sys
import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Tuple, Optional, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Quran verse counts per surah (1-114)
QURAN_VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6
]

# Approved Sunni tafsir sources (4 madhabs)
APPROVED_TAFSIR_SOURCES = {
    "ibn_kathir_ar", "ibn_kathir_en",
    "tabari_ar",
    "qurtubi_ar",
    "nasafi_ar",
    "shinqiti_ar",
    "baghawi_ar",
    "saadi_ar",
    "jalalayn_ar", "jalalayn_en",
}

# Common English words for leakage detection
ENGLISH_COMMON_WORDS = {
    'the', 'and', 'of', 'to', 'in', 'for', 'is', 'on', 'that', 'by',
    'this', 'with', 'from', 'or', 'an', 'be', 'are', 'was', 'were',
    'has', 'have', 'had', 'not', 'but', 'what', 'all', 'can', 'will',
    'there', 'their', 'which', 'also', 'as', 'we', 'it', 'been', 'more',
    'when', 'who', 'they', 'if', 'would', 'about', 'into', 'than', 'its',
}

# Placeholder patterns to detect
PLACEHOLDER_PATTERNS = [
    r'\bTODO\b', r'\bTBD\b', r'\bFIXME\b',
    r'\blorem\b', r'\bipsum\b', r'\bexample\b',
    r'\bplaceholder\b', r'\b\[.*?\]\b',
]

# Theme categories requiring specific consequences
CATEGORIES_REQUIRING_PUNISHMENT = {'muharramat'}
CATEGORIES_REQUIRING_REWARD = {'ibadat', 'akhlaq_fardi', 'akhlaq_ijtima'}

# Rule codes for clear error identification
class RuleCode(str, Enum):
    THEME_MIN_VERSES = "THEME_MIN_VERSES"
    THEME_HAS_SEGMENT = "THEME_HAS_SEGMENT"
    THEME_TAFSIR_SOURCES = "THEME_TAFSIR_SOURCES"
    THEME_GRAPH_CONNECTED = "THEME_GRAPH_CONNECTED"
    THEME_CONSEQUENCE_REWARD = "THEME_CONSEQUENCE_REWARD"
    THEME_CONSEQUENCE_PUNISHMENT = "THEME_CONSEQUENCE_PUNISHMENT"
    SEGMENT_VALID_SURA = "SEGMENT_VALID_SURA"
    SEGMENT_VALID_AYAH = "SEGMENT_VALID_AYAH"
    SEGMENT_HAS_EVIDENCE = "SEGMENT_HAS_EVIDENCE"
    SEGMENT_APPROVED_SOURCE = "SEGMENT_APPROVED_SOURCE"
    SEGMENT_HAS_REASONS_AR = "SEGMENT_HAS_REASONS_AR"
    SEGMENT_VALID_CONFIDENCE = "SEGMENT_VALID_CONFIDENCE"
    SEGMENT_VALID_MATCH_TYPE = "SEGMENT_VALID_MATCH_TYPE"
    ARABIC_NO_ENGLISH_LEAK = "ARABIC_NO_ENGLISH_LEAK"
    ARABIC_NO_PLACEHOLDER = "ARABIC_NO_PLACEHOLDER"
    ARABIC_NOT_EMPTY = "ARABIC_NOT_EMPTY"
    GRAPH_NO_SELF_LOOP = "GRAPH_NO_SELF_LOOP"
    GRAPH_NO_DUPLICATE_EDGE = "GRAPH_NO_DUPLICATE_EDGE"
    CONSEQUENCE_HAS_EVIDENCE = "CONSEQUENCE_HAS_EVIDENCE"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: Severity
    rule_code: str
    theme_id: str
    theme_name_ar: str
    message: str
    suggested_fix: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThemeAuditResult:
    """Audit result for a single theme."""
    theme_id: str
    title_ar: str
    title_en: str
    category: str

    # Coverage metrics
    segment_count: int = 0
    unique_verse_count: int = 0
    tafsir_source_count: int = 0
    consequence_count: int = 0
    connection_count: int = 0

    # Validation flags
    has_min_verses: bool = False
    has_required_consequence: bool = False
    has_tafsir_grounding: bool = False
    arabic_clean: bool = False
    is_connected: bool = False

    # Issues
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def coverage_score(self) -> int:
        """Calculate coverage score (0-100)."""
        score = 0
        if self.has_min_verses:
            score += 40
        if self.tafsir_source_count >= 2:
            score += 20
        if self.has_required_consequence:
            score += 20
        if self.arabic_clean:
            score += 10
        if self.is_connected:
            score += 10
        return score

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARN)


@dataclass
class CategoryAudit:
    """Audit summary for a category."""
    category: str
    label_ar: str
    label_en: str
    theme_count: int = 0
    themes_with_segments: int = 0
    themes_meeting_min_verses: int = 0
    themes_with_consequences: int = 0
    total_segments: int = 0
    total_verses: int = 0
    average_score: float = 0.0


@dataclass
class AuditReport:
    """Complete audit report."""
    # Metadata
    timestamp: str
    version: str = "2.0.0"
    mode: str = "default"
    min_verses_threshold: int = 3

    # Summary counts
    total_themes: int = 0
    themes_with_segments: int = 0
    themes_meeting_min_verses: int = 0
    total_segments: int = 0
    total_consequences: int = 0
    total_connections: int = 0

    # Issue counts
    error_count: int = 0
    warn_count: int = 0
    info_count: int = 0

    # Graph metrics
    connected_components: int = 0
    isolated_themes: List[str] = field(default_factory=list)

    # Category breakdown
    categories: Dict[str, CategoryAudit] = field(default_factory=dict)

    # Theme results
    theme_results: List[ThemeAuditResult] = field(default_factory=list)

    # All issues
    all_issues: List[ValidationIssue] = field(default_factory=list)

    # Top/bottom themes
    top_themes: List[Dict[str, Any]] = field(default_factory=list)
    bottom_themes: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_themes == 0:
            return 0.0
        valid = sum(1 for t in self.theme_results if t.error_count == 0)
        return (valid / self.total_themes) * 100

    @property
    def coverage_rate(self) -> float:
        if self.total_themes == 0:
            return 0.0
        return (self.themes_meeting_min_verses / self.total_themes) * 100


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def detect_english_leakage(text: str) -> Tuple[bool, float]:
    """
    Detect English leakage in Arabic text.

    Returns:
        (has_leakage, latin_percentage)
    """
    if not text:
        return False, 0.0

    # Count Latin letters
    latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    alpha_count = sum(1 for c in text if c.isalpha())

    if alpha_count == 0:
        return False, 0.0

    latin_percentage = (latin_count / alpha_count) * 100

    # Check percentage threshold
    if latin_percentage > 15:
        return True, latin_percentage

    # Check for common English words
    words = text.lower().split()
    english_word_count = sum(1 for w in words if w in ENGLISH_COMMON_WORDS)

    if english_word_count >= 3:
        return True, latin_percentage

    return False, latin_percentage


def detect_placeholders(text: str) -> List[str]:
    """Detect placeholder text patterns."""
    if not text:
        return []

    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(pattern)
    return found


def has_arabic_content(text: str) -> bool:
    """Check if text contains Arabic characters."""
    if not text:
        return False
    return any('\u0600' <= c <= '\u06FF' for c in text)


def validate_sura_ayah(sura: int, ayah: int) -> Tuple[bool, str]:
    """Validate sura/ayah is within Quran bounds."""
    if sura < 1 or sura > 114:
        return False, f"Invalid sura number: {sura} (must be 1-114)"

    max_ayah = QURAN_VERSE_COUNTS[sura - 1]
    if ayah < 1 or ayah > max_ayah:
        return False, f"Invalid ayah {ayah} for sura {sura} (max: {max_ayah})"

    return True, ""


def is_approved_tafsir(source_id: str) -> bool:
    """Check if tafsir source is from approved list."""
    return source_id in APPROVED_TAFSIR_SOURCES


# =============================================================================
# DATABASE QUERIES
# =============================================================================

def get_db_url() -> str:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur")


def check_tables_exist(session: Session) -> bool:
    """Check if required tables exist."""
    try:
        result = session.execute(text(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'quranic_themes'"
        ))
        return result.fetchone() is not None
    except Exception:
        return False


def fetch_all_themes(session: Session) -> List[Dict]:
    """Fetch all themes with related data."""
    result = session.execute(text("""
        SELECT
            qt.id,
            qt.title_ar,
            qt.title_en,
            qt.category,
            qt.description_ar,
            qt.description_en,
            qt.key_concepts,
            qt.related_theme_ids,
            qt.parent_theme_id,
            qt.tafsir_sources,
            qt.segment_count,
            qt.total_verses,
            (SELECT COUNT(*) FROM quranic_themes WHERE parent_theme_id = qt.id) as child_count
        FROM quranic_themes qt
        ORDER BY qt.category, qt.order_of_importance
    """))

    themes = []
    for row in result:
        themes.append({
            'id': row[0],
            'title_ar': row[1],
            'title_en': row[2],
            'category': row[3],
            'description_ar': row[4],
            'description_en': row[5],
            'key_concepts': row[6] or [],
            'related_theme_ids': row[7] or [],
            'parent_theme_id': row[8],
            'tafsir_sources': row[9] or [],
            'segment_count': row[10] or 0,
            'total_verses': row[11] or 0,
            'child_count': row[12] or 0,
        })
    return themes


def fetch_theme_segments(session: Session, theme_id: str) -> List[Dict]:
    """Fetch segments for a theme."""
    result = session.execute(text("""
        SELECT
            id, sura_no, ayah_start, ayah_end,
            summary_ar, summary_en, title_ar, title_en,
            evidence_sources, evidence_chunk_ids,
            is_verified, match_type, confidence, reasons_ar, is_core
        FROM theme_segments
        WHERE theme_id = :theme_id
        ORDER BY segment_order
    """), {"theme_id": theme_id})

    segments = []
    for row in result:
        segments.append({
            'id': row[0],
            'sura_no': row[1],
            'ayah_start': row[2],
            'ayah_end': row[3],
            'summary_ar': row[4],
            'summary_en': row[5],
            'title_ar': row[6],
            'title_en': row[7],
            'evidence_sources': row[8] or [],
            'evidence_chunk_ids': row[9] or [],
            'is_verified': row[10],
            'match_type': row[11],
            'confidence': row[12],
            'reasons_ar': row[13],
            'is_core': row[14],
        })
    return segments


def fetch_theme_consequences(session: Session, theme_id: str) -> List[Dict]:
    """Fetch consequences for a theme."""
    result = session.execute(text("""
        SELECT
            id, consequence_type, description_ar, description_en,
            supporting_verses, evidence_chunk_ids
        FROM theme_consequences
        WHERE theme_id = :theme_id
        ORDER BY display_order
    """), {"theme_id": theme_id})

    consequences = []
    for row in result:
        consequences.append({
            'id': row[0],
            'consequence_type': row[1],
            'description_ar': row[2],
            'description_en': row[3],
            'supporting_verses': row[4] or [],
            'evidence_chunk_ids': row[5] or [],
        })
    return consequences


def fetch_theme_connections(session: Session) -> List[Dict]:
    """Fetch all theme connections."""
    result = session.execute(text("""
        SELECT
            tc.id, tc.source_segment_id, tc.target_segment_id, tc.edge_type,
            ts1.theme_id as source_theme,
            ts2.theme_id as target_theme
        FROM theme_connections tc
        JOIN theme_segments ts1 ON tc.source_segment_id = ts1.id
        JOIN theme_segments ts2 ON tc.target_segment_id = ts2.id
    """))

    connections = []
    for row in result:
        connections.append({
            'id': row[0],
            'source_segment_id': row[1],
            'target_segment_id': row[2],
            'edge_type': row[3],
            'source_theme': row[4],
            'target_theme': row[5],
        })
    return connections


def fetch_global_stats(session: Session) -> Dict:
    """Fetch global statistics."""
    # Total themes
    total_themes = session.execute(text(
        "SELECT COUNT(*) FROM quranic_themes"
    )).scalar() or 0

    # Total segments
    total_segments = session.execute(text(
        "SELECT COUNT(*) FROM theme_segments"
    )).scalar() or 0

    # Total consequences
    total_consequences = session.execute(text(
        "SELECT COUNT(*) FROM theme_consequences"
    )).scalar() or 0

    # Total connections
    total_connections = session.execute(text(
        "SELECT COUNT(*) FROM theme_connections"
    )).scalar() or 0

    # Themes with segments
    themes_with_segments = session.execute(text(
        "SELECT COUNT(DISTINCT theme_id) FROM theme_segments"
    )).scalar() or 0

    return {
        'total_themes': total_themes,
        'total_segments': total_segments,
        'total_consequences': total_consequences,
        'total_connections': total_connections,
        'themes_with_segments': themes_with_segments,
    }


# =============================================================================
# GRAPH ANALYSIS
# =============================================================================

def analyze_graph_connectivity(
    themes: List[Dict],
    connections: List[Dict]
) -> Tuple[int, List[str]]:
    """
    Analyze theme graph connectivity.

    Returns:
        (num_components, isolated_theme_ids)
    """
    # Build adjacency from related_theme_ids and connections
    adjacency: Dict[str, Set[str]] = defaultdict(set)

    # Add edges from related_theme_ids
    for theme in themes:
        theme_id = theme['id']
        for related_id in theme.get('related_theme_ids', []):
            adjacency[theme_id].add(related_id)
            adjacency[related_id].add(theme_id)

        # Add parent-child relationships
        parent_id = theme.get('parent_theme_id')
        if parent_id:
            adjacency[theme_id].add(parent_id)
            adjacency[parent_id].add(theme_id)

    # Add edges from connections (segment-level connections create theme-level links)
    for conn in connections:
        source_theme = conn.get('source_theme')
        target_theme = conn.get('target_theme')
        if source_theme and target_theme and source_theme != target_theme:
            adjacency[source_theme].add(target_theme)
            adjacency[target_theme].add(source_theme)

    # Find connected components using DFS
    all_theme_ids = {t['id'] for t in themes}
    visited: Set[str] = set()
    components: List[Set[str]] = []

    def dfs(node: str, component: Set[str]):
        if node in visited:
            return
        visited.add(node)
        component.add(node)
        for neighbor in adjacency.get(node, set()):
            if neighbor in all_theme_ids:
                dfs(neighbor, component)

    for theme_id in all_theme_ids:
        if theme_id not in visited:
            component: Set[str] = set()
            dfs(theme_id, component)
            components.append(component)

    # Find isolated themes (components of size 1 with no edges)
    isolated = []
    for theme_id in all_theme_ids:
        if len(adjacency.get(theme_id, set())) == 0:
            isolated.append(theme_id)

    return len(components), isolated


def check_graph_issues(connections: List[Dict]) -> List[ValidationIssue]:
    """Check for graph structure issues (self-loops, duplicates)."""
    issues = []

    # Track seen edges
    seen_edges: Set[Tuple[str, str, str]] = set()

    for conn in connections:
        source = conn['source_segment_id']
        target = conn['target_segment_id']
        edge_type = conn['edge_type']

        # Check for self-loops
        if source == target:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                rule_code=RuleCode.GRAPH_NO_SELF_LOOP.value,
                theme_id="graph",
                theme_name_ar="الرسم البياني",
                message=f"Self-loop detected: {source}",
                suggested_fix="Remove self-referencing connection",
                details={'connection_id': conn['id']}
            ))

        # Check for duplicates
        edge_key = (source, target, edge_type)
        if edge_key in seen_edges:
            issues.append(ValidationIssue(
                severity=Severity.WARN,
                rule_code=RuleCode.GRAPH_NO_DUPLICATE_EDGE.value,
                theme_id="graph",
                theme_name_ar="الرسم البياني",
                message=f"Duplicate edge: {source} -> {target} ({edge_type})",
                suggested_fix="Remove duplicate connection",
                details={'connection_id': conn['id']}
            ))
        seen_edges.add(edge_key)

    return issues


# =============================================================================
# THEME VALIDATION
# =============================================================================

def audit_theme(
    session: Session,
    theme: Dict,
    min_verses: int,
    strict: bool
) -> ThemeAuditResult:
    """Run all validations for a single theme."""
    result = ThemeAuditResult(
        theme_id=theme['id'],
        title_ar=theme['title_ar'],
        title_en=theme['title_en'],
        category=theme['category'],
    )

    # Fetch related data
    segments = fetch_theme_segments(session, theme['id'])
    consequences = fetch_theme_consequences(session, theme['id'])

    result.segment_count = len(segments)
    result.consequence_count = len(consequences)

    # === Rule 2.1: Coverage Rules ===

    # Check segment existence
    if len(segments) == 0:
        result.issues.append(ValidationIssue(
            severity=Severity.ERROR,
            rule_code=RuleCode.THEME_HAS_SEGMENT.value,
            theme_id=theme['id'],
            theme_name_ar=theme['title_ar'],
            message="Theme has no verse segments",
            suggested_fix=f"Add at least 1 segment with Quranic verses to theme {theme['id']}",
        ))

    # Count unique verses
    unique_verses: Set[Tuple[int, int]] = set()
    tafsir_sources: Set[str] = set()

    for seg in segments:
        sura = seg['sura_no']
        ayah_start = seg['ayah_start']
        ayah_end = seg['ayah_end']

        # Validate sura/ayah bounds
        for ayah in range(ayah_start, ayah_end + 1):
            valid, error_msg = validate_sura_ayah(sura, ayah)
            if not valid:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    rule_code=RuleCode.SEGMENT_VALID_AYAH.value,
                    theme_id=theme['id'],
                    theme_name_ar=theme['title_ar'],
                    message=error_msg,
                    suggested_fix=f"Fix ayah reference in segment {seg['id']}",
                    details={'segment_id': seg['id'], 'sura': sura, 'ayah': ayah}
                ))
            else:
                unique_verses.add((sura, ayah))

        # Collect tafsir sources from evidence
        for evidence in seg.get('evidence_sources', []):
            source_id = evidence.get('source_id', '')
            if source_id:
                tafsir_sources.add(source_id)
                if not is_approved_tafsir(source_id):
                    result.issues.append(ValidationIssue(
                        severity=Severity.WARN,
                        rule_code=RuleCode.SEGMENT_APPROVED_SOURCE.value,
                        theme_id=theme['id'],
                        theme_name_ar=theme['title_ar'],
                        message=f"Unapproved tafsir source: {source_id}",
                        suggested_fix=f"Use approved tafsir (Ibn Kathir, Tabari, Qurtubi, etc.)",
                        details={'segment_id': seg['id'], 'source_id': source_id}
                    ))

        # Check evidence exists
        if not seg.get('evidence_chunk_ids'):
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                rule_code=RuleCode.SEGMENT_HAS_EVIDENCE.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message=f"Segment {seg['id']} has no evidence chunk IDs",
                suggested_fix="Add tafsir evidence to segment",
                details={'segment_id': seg['id']}
            ))

        # === Rule 2.2.1: Discovery Fields Validation ===
        # Check match_type if present (for discovered segments)
        match_type = seg.get('match_type')
        if match_type and match_type not in ('lexical', 'root', 'semantic', 'mixed', 'manual'):
            result.issues.append(ValidationIssue(
                severity=Severity.WARN,
                rule_code=RuleCode.SEGMENT_VALID_MATCH_TYPE.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message=f"Invalid match_type: {match_type}",
                suggested_fix="Use valid match_type: lexical, root, semantic, mixed, or manual",
                details={'segment_id': seg['id'], 'match_type': match_type}
            ))

        # Check confidence if present
        confidence = seg.get('confidence')
        if confidence is not None:
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                result.issues.append(ValidationIssue(
                    severity=Severity.WARN,
                    rule_code=RuleCode.SEGMENT_VALID_CONFIDENCE.value,
                    theme_id=theme['id'],
                    theme_name_ar=theme['title_ar'],
                    message=f"Invalid confidence: {confidence} (must be 0.0-1.0)",
                    suggested_fix="Set confidence between 0.0 and 1.0",
                    details={'segment_id': seg['id'], 'confidence': confidence}
                ))

        # Check reasons_ar for discovered (non-manual) segments
        if match_type and match_type != 'manual':
            reasons_ar = seg.get('reasons_ar')
            if not reasons_ar or len(str(reasons_ar).strip()) < 10:
                result.issues.append(ValidationIssue(
                    severity=Severity.WARN,
                    rule_code=RuleCode.SEGMENT_HAS_REASONS_AR.value,
                    theme_id=theme['id'],
                    theme_name_ar=theme['title_ar'],
                    message=f"Discovered segment missing Arabic reasons",
                    suggested_fix="Add Arabic explanation for why verse belongs to theme",
                    details={'segment_id': seg['id'], 'match_type': match_type}
                ))

        # === Rule 2.3: Arabic Integrity ===
        for field_name, field_value in [
            ('summary_ar', seg.get('summary_ar')),
            ('title_ar', seg.get('title_ar')),
        ]:
            if field_value:
                # Check English leakage
                has_leak, latin_pct = detect_english_leakage(field_value)
                if has_leak:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        rule_code=RuleCode.ARABIC_NO_ENGLISH_LEAK.value,
                        theme_id=theme['id'],
                        theme_name_ar=theme['title_ar'],
                        message=f"English leakage in {field_name}: {latin_pct:.1f}% Latin",
                        suggested_fix=f"Replace English text with Arabic in {field_name}",
                        details={'segment_id': seg['id'], 'field': field_name, 'latin_pct': latin_pct}
                    ))

                # Check placeholders
                placeholders = detect_placeholders(field_value)
                if placeholders:
                    result.issues.append(ValidationIssue(
                        severity=Severity.ERROR,
                        rule_code=RuleCode.ARABIC_NO_PLACEHOLDER.value,
                        theme_id=theme['id'],
                        theme_name_ar=theme['title_ar'],
                        message=f"Placeholder text in {field_name}",
                        suggested_fix=f"Replace placeholder with actual Arabic content",
                        details={'segment_id': seg['id'], 'field': field_name, 'patterns': placeholders}
                    ))

    result.unique_verse_count = len(unique_verses)
    result.tafsir_source_count = len(tafsir_sources)

    # Check min verses threshold
    result.has_min_verses = result.unique_verse_count >= min_verses
    if not result.has_min_verses and segments:
        result.issues.append(ValidationIssue(
            severity=Severity.ERROR,
            rule_code=RuleCode.THEME_MIN_VERSES.value,
            theme_id=theme['id'],
            theme_name_ar=theme['title_ar'],
            message=f"Theme has only {result.unique_verse_count} unique verses (min: {min_verses})",
            suggested_fix=f"Add more verse segments to reach {min_verses} unique verses",
            details={'current': result.unique_verse_count, 'required': min_verses}
        ))

    # === Rule 2.2: Tafsir Grounding ===
    approved_count = sum(1 for s in tafsir_sources if is_approved_tafsir(s))
    result.has_tafsir_grounding = approved_count > 0

    if approved_count == 0 and segments:
        result.issues.append(ValidationIssue(
            severity=Severity.ERROR,
            rule_code=RuleCode.THEME_TAFSIR_SOURCES.value,
            theme_id=theme['id'],
            theme_name_ar=theme['title_ar'],
            message="No approved tafsir sources found",
            suggested_fix="Add evidence from Ibn Kathir, Tabari, Qurtubi, etc.",
        ))
    elif approved_count < 2 and segments:
        result.issues.append(ValidationIssue(
            severity=Severity.WARN,
            rule_code=RuleCode.THEME_TAFSIR_SOURCES.value,
            theme_id=theme['id'],
            theme_name_ar=theme['title_ar'],
            message=f"Only {approved_count} approved tafsir source(s), recommend >= 2",
            suggested_fix="Add evidence from additional tafsir sources",
            details={'current': approved_count, 'recommended': 2}
        ))

    # === Rule 2.3: Theme-level Arabic fields ===
    for field_name, field_value in [
        ('title_ar', theme.get('title_ar')),
        ('description_ar', theme.get('description_ar')),
    ]:
        if not field_value or len(field_value.strip()) == 0:
            result.issues.append(ValidationIssue(
                severity=Severity.ERROR,
                rule_code=RuleCode.ARABIC_NOT_EMPTY.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'] or theme['id'],
                message=f"Arabic field '{field_name}' is empty",
                suggested_fix=f"Add Arabic content to {field_name}",
            ))
        elif field_value:
            has_leak, latin_pct = detect_english_leakage(field_value)
            if has_leak:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    rule_code=RuleCode.ARABIC_NO_ENGLISH_LEAK.value,
                    theme_id=theme['id'],
                    theme_name_ar=theme['title_ar'],
                    message=f"English leakage in {field_name}: {latin_pct:.1f}% Latin",
                    suggested_fix=f"Replace English text with Arabic",
                    details={'field': field_name, 'latin_pct': latin_pct}
                ))

            placeholders = detect_placeholders(field_value)
            if placeholders:
                result.issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    rule_code=RuleCode.ARABIC_NO_PLACEHOLDER.value,
                    theme_id=theme['id'],
                    theme_name_ar=theme['title_ar'],
                    message=f"Placeholder text in {field_name}",
                    suggested_fix="Replace placeholder with actual Arabic content",
                    details={'field': field_name, 'patterns': placeholders}
                ))

    # === Rule 2.4: Consequence Rules ===
    category = theme['category']
    consequence_types = {c['consequence_type'] for c in consequences}

    # Check if category requires punishment
    if category in CATEGORIES_REQUIRING_PUNISHMENT:
        has_punishment = any(t in consequence_types for t in ['punishment', 'warning'])
        if not has_punishment:
            severity = Severity.ERROR if strict else Severity.WARN
            result.issues.append(ValidationIssue(
                severity=severity,
                rule_code=RuleCode.THEME_CONSEQUENCE_PUNISHMENT.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message="Prohibition theme missing punishment/warning consequence",
                suggested_fix="Add punishment or warning consequence for this muharramat theme",
            ))
        else:
            result.has_required_consequence = True

    # Check if category requires reward
    elif category in CATEGORIES_REQUIRING_REWARD:
        has_reward = any(t in consequence_types for t in ['reward', 'blessing', 'promise'])
        if not has_reward:
            severity = Severity.ERROR if strict else Severity.WARN
            result.issues.append(ValidationIssue(
                severity=severity,
                rule_code=RuleCode.THEME_CONSEQUENCE_REWARD.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message="Virtue theme missing reward/blessing consequence",
                suggested_fix="Add reward or blessing consequence for this theme",
            ))
        else:
            result.has_required_consequence = True
    else:
        # For other categories, having any consequence counts
        result.has_required_consequence = len(consequences) > 0

    # Check consequence evidence grounding
    for cons in consequences:
        if not cons.get('evidence_chunk_ids'):
            result.issues.append(ValidationIssue(
                severity=Severity.WARN,
                rule_code=RuleCode.CONSEQUENCE_HAS_EVIDENCE.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message=f"Consequence {cons['id']} has no evidence",
                suggested_fix="Add evidence for consequence",
                details={'consequence_id': cons['id']}
            ))

    # Set arabic_clean flag
    arabic_issues = [i for i in result.issues if i.rule_code in (
        RuleCode.ARABIC_NO_ENGLISH_LEAK.value,
        RuleCode.ARABIC_NO_PLACEHOLDER.value,
        RuleCode.ARABIC_NOT_EMPTY.value
    )]
    result.arabic_clean = len(arabic_issues) == 0

    return result


# =============================================================================
# MAIN AUDIT FUNCTION
# =============================================================================

def run_audit(
    session: Session,
    min_verses: int = 3,
    strict: bool = False,
    ci_mode: bool = False,
    max_issues: int = 0,
    only_category: Optional[str] = None,
    only_theme_id: Optional[str] = None,
) -> AuditReport:
    """
    Run complete theme audit.

    Args:
        session: Database session
        min_verses: Minimum unique verses per theme
        strict: If True, WARN becomes ERROR for consequence rules
        ci_mode: If True, determines exit code behavior
        max_issues: Maximum issues to report (0 = unlimited)
        only_category: Filter to specific category
        only_theme_id: Filter to specific theme

    Returns:
        AuditReport with all findings
    """
    report = AuditReport(
        timestamp=datetime.utcnow().isoformat(),
        mode="ci" if ci_mode else ("strict" if strict else "default"),
        min_verses_threshold=min_verses,
    )

    # Fetch global stats
    stats = fetch_global_stats(session)
    report.total_themes = stats['total_themes']
    report.total_segments = stats['total_segments']
    report.total_consequences = stats['total_consequences']
    report.total_connections = stats['total_connections']
    report.themes_with_segments = stats['themes_with_segments']

    # Fetch all themes
    themes = fetch_all_themes(session)

    # Apply filters
    if only_category:
        themes = [t for t in themes if t['category'] == only_category]
    if only_theme_id:
        themes = [t for t in themes if t['id'] == only_theme_id]

    # Fetch connections for graph analysis
    connections = fetch_theme_connections(session)

    # Analyze graph connectivity
    num_components, isolated = analyze_graph_connectivity(themes, connections)
    report.connected_components = num_components
    report.isolated_themes = isolated

    # Check graph structure issues
    graph_issues = check_graph_issues(connections)
    report.all_issues.extend(graph_issues)

    # Initialize category audits
    category_labels = {
        "aqidah": ("التوحيد والعقيدة", "Theology & Creed"),
        "iman": ("الإيمان", "Pillars of Faith"),
        "ibadat": ("العبادات", "Acts of Worship"),
        "akhlaq_fardi": ("الأخلاق الفردية", "Individual Ethics"),
        "akhlaq_ijtima": ("الأخلاق الاجتماعية", "Social Ethics"),
        "muharramat": ("المحرمات والكبائر", "Prohibitions"),
        "sunan_ilahiyyah": ("السنن الإلهية", "Divine Laws"),
    }

    for cat, (ar, en) in category_labels.items():
        report.categories[cat] = CategoryAudit(
            category=cat,
            label_ar=ar,
            label_en=en,
        )

    # Audit each theme
    isolated_set = set(isolated)
    for theme in themes:
        theme_result = audit_theme(session, theme, min_verses, strict)

        # Check graph connectivity for this theme
        theme_result.is_connected = theme['id'] not in isolated_set
        if not theme_result.is_connected:
            severity = Severity.ERROR if (ci_mode and len(isolated) > 5) or strict else Severity.WARN
            theme_result.issues.append(ValidationIssue(
                severity=severity,
                rule_code=RuleCode.THEME_GRAPH_CONNECTED.value,
                theme_id=theme['id'],
                theme_name_ar=theme['title_ar'],
                message="Theme is isolated in graph (no connections)",
                suggested_fix="Add related_theme_ids or parent_theme_id",
            ))

        # Count connections for this theme
        theme_result.connection_count = sum(
            1 for c in connections
            if c['source_theme'] == theme['id'] or c['target_theme'] == theme['id']
        )

        report.theme_results.append(theme_result)
        report.all_issues.extend(theme_result.issues)

        # Update category stats
        cat = theme['category']
        if cat in report.categories:
            cat_audit = report.categories[cat]
            cat_audit.theme_count += 1
            if theme_result.segment_count > 0:
                cat_audit.themes_with_segments += 1
            if theme_result.has_min_verses:
                cat_audit.themes_meeting_min_verses += 1
                report.themes_meeting_min_verses += 1
            if theme_result.consequence_count > 0:
                cat_audit.themes_with_consequences += 1
            cat_audit.total_segments += theme_result.segment_count
            cat_audit.total_verses += theme_result.unique_verse_count

    # Calculate category averages
    for cat, cat_audit in report.categories.items():
        if cat_audit.theme_count > 0:
            scores = [
                t.coverage_score for t in report.theme_results
                if t.category == cat
            ]
            cat_audit.average_score = sum(scores) / len(scores) if scores else 0.0

    # Count issues by severity
    report.error_count = sum(1 for i in report.all_issues if i.severity == Severity.ERROR)
    report.warn_count = sum(1 for i in report.all_issues if i.severity == Severity.WARN)
    report.info_count = sum(1 for i in report.all_issues if i.severity == Severity.INFO)

    # Apply max_issues limit
    if max_issues > 0 and len(report.all_issues) > max_issues:
        report.all_issues = report.all_issues[:max_issues]

    # Top and bottom themes
    sorted_by_score = sorted(report.theme_results, key=lambda t: t.coverage_score, reverse=True)
    report.top_themes = [
        {'id': t.theme_id, 'title_ar': t.title_ar, 'score': t.coverage_score}
        for t in sorted_by_score[:10]
    ]
    report.bottom_themes = [
        {'id': t.theme_id, 'title_ar': t.title_ar, 'score': t.coverage_score, 'errors': t.error_count}
        for t in sorted_by_score[-10:]
    ]

    return report


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================

def print_report(report: AuditReport, verbose: bool = False):
    """Print human-readable report to console."""
    print("=" * 80)
    print("QURANIC THEMES COMPLETENESS AUDIT REPORT")
    print("المحاور القرآنية - تقرير التدقيق الشامل")
    print("=" * 80)
    print(f"Timestamp: {report.timestamp}")
    print(f"Mode: {report.mode}")
    print(f"Min Verses Threshold: {report.min_verses_threshold}")

    # Summary
    print("\n" + "-" * 40)
    print("📊 SUMMARY")
    print("-" * 40)
    print(f"Total Themes: {report.total_themes}")
    print(f"Themes with Segments: {report.themes_with_segments}")
    print(f"Themes Meeting Min Verses: {report.themes_meeting_min_verses} ({report.coverage_rate:.1f}%)")
    print(f"Total Segments: {report.total_segments}")
    print(f"Total Consequences: {report.total_consequences}")
    print(f"Total Connections: {report.total_connections}")
    print(f"Pass Rate: {report.pass_rate:.1f}%")

    # Issue counts
    print("\n" + "-" * 40)
    print("🚨 ISSUE COUNTS")
    print("-" * 40)
    print(f"Errors: {report.error_count} ❌")
    print(f"Warnings: {report.warn_count} ⚠️")
    print(f"Info: {report.info_count} ℹ️")

    # Graph connectivity
    print("\n" + "-" * 40)
    print("📈 GRAPH CONNECTIVITY")
    print("-" * 40)
    print(f"Connected Components: {report.connected_components}")
    if report.isolated_themes:
        print(f"Isolated Themes: {len(report.isolated_themes)}")
        for tid in report.isolated_themes[:5]:
            print(f"  - {tid}")
        if len(report.isolated_themes) > 5:
            print(f"  ... and {len(report.isolated_themes) - 5} more")
    else:
        print("No isolated themes ✓")

    # Category breakdown
    print("\n" + "-" * 40)
    print("📁 CATEGORY BREAKDOWN")
    print("-" * 40)
    for cat, cat_audit in sorted(report.categories.items(), key=lambda x: x[1].label_en):
        if cat_audit.theme_count > 0:
            pct = (cat_audit.themes_meeting_min_verses / cat_audit.theme_count * 100) if cat_audit.theme_count else 0
            print(f"\n{cat_audit.label_en} ({cat_audit.label_ar}):")
            print(f"  Themes: {cat_audit.theme_count}")
            print(f"  With Segments: {cat_audit.themes_with_segments}")
            print(f"  Meeting Min Verses: {cat_audit.themes_meeting_min_verses} ({pct:.0f}%)")
            print(f"  Average Score: {cat_audit.average_score:.0f}/100")

    # Top themes
    print("\n" + "-" * 40)
    print("🏆 TOP 10 THEMES (by coverage score)")
    print("-" * 40)
    for t in report.top_themes[:10]:
        print(f"  {t['score']:3d}/100 - {t['id']} ({t['title_ar']})")

    # Bottom themes
    print("\n" + "-" * 40)
    print("⚠️ BOTTOM 10 THEMES (need attention)")
    print("-" * 40)
    for t in report.bottom_themes[-10:]:
        print(f"  {t['score']:3d}/100 - {t['id']} ({t['title_ar']}) - {t['errors']} errors")

    # Critical issues
    if report.error_count > 0:
        print("\n" + "-" * 40)
        print("❌ CRITICAL ERRORS (first 20)")
        print("-" * 40)
        errors = [i for i in report.all_issues if i.severity == Severity.ERROR]
        for issue in errors[:20]:
            print(f"\n[{issue.rule_code}] {issue.theme_id}")
            print(f"  {issue.message}")
            print(f"  Fix: {issue.suggested_fix}")
        if len(errors) > 20:
            print(f"\n... and {len(errors) - 20} more errors")

    print("\n" + "=" * 80)

    # Final verdict
    if report.error_count == 0:
        print("✅ AUDIT PASSED - No critical errors")
    else:
        print(f"❌ AUDIT FAILED - {report.error_count} critical errors")

    print("=" * 80)


def export_json(report: AuditReport, filepath: str):
    """Export report as JSON."""
    # Convert dataclasses to dicts
    def serialize(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, list):
            return [serialize(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        return obj

    data = serialize(report)

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Report exported to: {filepath}")


def export_markdown(report: AuditReport, filepath: str):
    """Export report as Markdown."""
    lines = [
        "# Quranic Themes Completeness Audit Report",
        "",
        f"**Timestamp:** {report.timestamp}",
        f"**Mode:** {report.mode}",
        f"**Min Verses Threshold:** {report.min_verses_threshold}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Themes | {report.total_themes} |",
        f"| Themes with Segments | {report.themes_with_segments} |",
        f"| Themes Meeting Min Verses | {report.themes_meeting_min_verses} ({report.coverage_rate:.1f}%) |",
        f"| Total Segments | {report.total_segments} |",
        f"| Total Consequences | {report.total_consequences} |",
        f"| Pass Rate | {report.pass_rate:.1f}% |",
        "",
        "## Issue Counts",
        "",
        f"- **Errors:** {report.error_count}",
        f"- **Warnings:** {report.warn_count}",
        "",
        "## Category Breakdown",
        "",
        "| Category | Themes | With Segments | Avg Score |",
        "|----------|--------|---------------|-----------|",
    ]

    for cat, ca in sorted(report.categories.items()):
        if ca.theme_count > 0:
            lines.append(f"| {ca.label_en} | {ca.theme_count} | {ca.themes_with_segments} | {ca.average_score:.0f} |")

    lines.extend([
        "",
        "## Top 10 Themes",
        "",
        "| Score | Theme ID | Title |",
        "|-------|----------|-------|",
    ])

    for t in report.top_themes[:10]:
        lines.append(f"| {t['score']} | {t['id']} | {t['title_ar']} |")

    if report.error_count > 0:
        lines.extend([
            "",
            "## Critical Errors",
            "",
        ])
        errors = [i for i in report.all_issues if i.severity == Severity.ERROR]
        for issue in errors[:30]:
            lines.append(f"- **[{issue.rule_code}]** {issue.theme_id}: {issue.message}")

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Report exported to: {filepath}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Quranic Themes Completeness Audit - CI Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify/theme_completeness_audit.py
  python scripts/verify/theme_completeness_audit.py --ci
  python scripts/verify/theme_completeness_audit.py --json reports/audit.json
  python scripts/verify/theme_completeness_audit.py --min-verses 3 --strict
  python scripts/verify/theme_completeness_audit.py --only category=aqidah

Exit Codes:
  0 - All validations pass
  1 - Errors found (in --ci or --strict mode)
        """
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 on any ERROR"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: treat WARN as ERROR for consequence rules"
    )
    parser.add_argument(
        "--min-verses",
        type=int,
        default=3,
        help="Minimum unique verses per theme (default: 3)"
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=0,
        help="Maximum issues to report (0 = unlimited)"
    )
    parser.add_argument(
        "--json",
        type=str,
        metavar="PATH",
        help="Export report as JSON to PATH"
    )
    parser.add_argument(
        "--markdown",
        type=str,
        metavar="PATH",
        help="Export report as Markdown to PATH"
    )
    parser.add_argument(
        "--only",
        type=str,
        metavar="FILTER",
        help="Filter: category=X or theme_id=X"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode: only print final verdict"
    )

    args = parser.parse_args()

    # Parse filter
    only_category = None
    only_theme_id = None
    if args.only:
        if args.only.startswith("category="):
            only_category = args.only.split("=", 1)[1]
        elif args.only.startswith("theme_id="):
            only_theme_id = args.only.split("=", 1)[1]

    # Connect to database
    db_url = get_db_url()
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check tables exist
        if not check_tables_exist(session):
            print("ERROR: quranic_themes table does not exist!")
            print("Run migrations first: alembic upgrade head")
            sys.exit(1)

        # Run audit
        report = run_audit(
            session=session,
            min_verses=args.min_verses,
            strict=args.strict,
            ci_mode=args.ci,
            max_issues=args.max_issues,
            only_category=only_category,
            only_theme_id=only_theme_id,
        )

    # Output
    if not args.quiet:
        print_report(report, verbose=args.verbose)

    if args.json:
        export_json(report, args.json)

    if args.markdown:
        export_markdown(report, args.markdown)

    # Determine exit code
    if args.ci or args.strict:
        if report.error_count > 0:
            if not args.quiet:
                print(f"\nCI GATE FAILED: {report.error_count} errors found")
            sys.exit(1)
        else:
            if not args.quiet:
                print("\nCI GATE PASSED")
            sys.exit(0)
    else:
        # Non-CI mode: always exit 0
        sys.exit(0)


if __name__ == "__main__":
    main()
