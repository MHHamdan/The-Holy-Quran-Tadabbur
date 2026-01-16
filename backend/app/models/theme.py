"""
Quranic Thematic Classification Models (المحاور القرآنية)

DESIGN PHILOSOPHY:
==================
This module implements structured navigation of Quranic themes following:
1. EVIDENCE-FIRST: Every claim grounded in Quran + tafsir
2. ARABIC-FIRST: Primary labels in Arabic, English secondary
3. HIERARCHY-AWARE: Themes can have parent/child relationships
4. CONSEQUENCE-LINKED: Themes connected to rewards/punishments (sunan ilahiyyah)

GROUNDING RULES:
================
- NO speculation or modern ideological reinterpretation
- Evidence MUST come from 4 madhab tafsir sources only:
  - Ibn Kathir, Al-Tabari, Al-Qurtubi, Al-Baghawi, Al-Sa'di
- Every segment MUST have at least 1 tafsir citation
- Layer separation: Quran text → Tafsir → Classification

THEME CATEGORIES (Methodological Order):
========================================
1. aqidah        - التوحيد والعقيدة (Theology & Creed)
2. iman          - الإيمان (Pillars of Faith)
3. ibadat        - العبادات (Acts of Worship)
4. akhlaq_fardi  - الأخلاق الفردية (Individual Ethics)
5. akhlaq_ijtima - الأخلاق الاجتماعية (Social Ethics)
6. muharramat    - المحرمات والكبائر (Prohibitions)
7. sunan_ilahiyyah - السنن الإلهية (Divine Laws)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ThemeCategory(str, Enum):
    """
    Categories of Quranic themes following classical Islamic methodology.

    Order reflects methodological priority (Aqidah first, as it is the
    foundation upon which all other aspects of the deen are built).
    """
    AQIDAH = "aqidah"               # التوحيد والعقيدة - Theology & Creed
    IMAN = "iman"                   # الإيمان - Pillars of Faith
    IBADAT = "ibadat"               # العبادات - Acts of Worship
    AKHLAQ_FARDI = "akhlaq_fardi"   # الأخلاق الفردية - Individual Ethics
    AKHLAQ_IJTIMA = "akhlaq_ijtima" # الأخلاق الاجتماعية - Social Ethics
    MUHARRAMAT = "muharramat"       # المحرمات والكبائر - Prohibitions
    SUNAN_ILAHIYYAH = "sunan_ilahiyyah"  # السنن الإلهية - Divine Laws


class ThemeEdgeType(str, Enum):
    """Types of relationships between theme segments."""
    ELABORATION = "elaboration"         # تفصيل - One elaborates on another
    CONTRAST = "contrast"               # تضاد - Contrasting perspectives
    CAUSE_EFFECT = "cause_effect"       # سبب ونتيجة - Causal relationship
    PARALLEL = "parallel"               # تشابه - Similar treatment
    PROGRESSION = "progression"         # تدرج - Progressive revelation
    SUMMARY = "summary"                 # إجمال - One summarizes another
    EVIDENCE = "evidence"               # دليل - One provides evidence for another
    PREREQUISITE = "prerequisite"       # شرط - One is prerequisite for another


class ConsequenceType(str, Enum):
    """Types of divine consequences for themes (السنن الإلهية)."""
    REWARD = "reward"                   # جزاء - Promised reward in akhirah
    PUNISHMENT = "punishment"           # عقاب - Warned punishment
    BLESSING = "blessing"               # بركة - Worldly blessing
    WARNING = "warning"                 # تحذير - Divine warning
    PROMISE = "promise"                 # وعد - Divine promise


class RevelationContext(str, Enum):
    """Revelation context (Makki/Madani)."""
    MAKKI = "makki"     # مكي - Revealed in Makkah
    MADANI = "madani"   # مدني - Revealed in Madinah
    MIXED = "mixed"     # مختلط - Theme spans both


# =============================================================================
# TRANSLATION DICTIONARIES
# =============================================================================

THEME_CATEGORY_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "aqidah": {"ar": "التوحيد والعقيدة", "en": "Theology & Creed"},
    "iman": {"ar": "الإيمان", "en": "Pillars of Faith"},
    "ibadat": {"ar": "العبادات", "en": "Acts of Worship"},
    "akhlaq_fardi": {"ar": "الأخلاق الفردية", "en": "Individual Ethics"},
    "akhlaq_ijtima": {"ar": "الأخلاق الاجتماعية", "en": "Social Ethics"},
    "muharramat": {"ar": "المحرمات والكبائر", "en": "Prohibitions"},
    "sunan_ilahiyyah": {"ar": "السنن الإلهية", "en": "Divine Laws"},
}

THEME_CATEGORY_ORDER: Dict[str, int] = {
    "aqidah": 1,
    "iman": 2,
    "ibadat": 3,
    "akhlaq_fardi": 4,
    "akhlaq_ijtima": 5,
    "muharramat": 6,
    "sunan_ilahiyyah": 7,
}

CONSEQUENCE_TYPE_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "reward": {"ar": "جزاء", "en": "Reward"},
    "punishment": {"ar": "عقاب", "en": "Punishment"},
    "blessing": {"ar": "بركة", "en": "Blessing"},
    "warning": {"ar": "تحذير", "en": "Warning"},
    "promise": {"ar": "وعد", "en": "Promise"},
}

EDGE_TYPE_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "elaboration": {"ar": "تفصيل", "en": "Elaboration"},
    "contrast": {"ar": "تضاد", "en": "Contrast"},
    "cause_effect": {"ar": "سبب ونتيجة", "en": "Cause & Effect"},
    "parallel": {"ar": "تشابه", "en": "Parallel"},
    "progression": {"ar": "تدرج", "en": "Progression"},
    "summary": {"ar": "إجمال", "en": "Summary"},
    "evidence": {"ar": "دليل", "en": "Evidence"},
    "prerequisite": {"ar": "شرط", "en": "Prerequisite"},
}


# =============================================================================
# QURANIC THEME MODEL
# =============================================================================

class QuranicTheme(Base):
    """
    Root entity for Quranic themes (محاور قرآنية).

    A theme represents a fundamental Islamic concept that appears throughout
    the Quran, such as Tawheed, Sabr, Birr al-Walidayn, etc.

    Themes are organized hierarchically (parent-child) and can have
    relationships to other themes via related_theme_ids.
    """
    __tablename__ = "quranic_themes"

    id = Column(String(100), primary_key=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)

    # Arabic-first titles
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=False)
    short_title_ar = Column(String(100), nullable=True)
    short_title_en = Column(String(100), nullable=True)

    # Classification
    category = Column(String(50), nullable=False, index=True)
    order_of_importance = Column(Integer, default=0)

    # Arabic key concepts for search (e.g., ["التوحيد", "الربوبية", "الألوهية"])
    key_concepts = Column(ARRAY(String), nullable=False)

    # Hierarchy
    parent_theme_id = Column(
        String(100),
        ForeignKey("quranic_themes.id"),
        nullable=True
    )
    related_theme_ids = Column(ARRAY(String), nullable=True)

    # Content
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    # Approved tafsir sources used for this theme
    tafsir_sources = Column(ARRAY(String), nullable=True)

    # Metadata
    is_complete = Column(Boolean, default=False)
    segment_count = Column(Integer, default=0)
    total_verses = Column(Integer, default=0)
    suras_mentioned = Column(ARRAY(Integer), nullable=True)
    makki_percentage = Column(Float, default=0)
    madani_percentage = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship(
        "QuranicTheme",
        remote_side=[id],
        backref="children"
    )
    segments = relationship(
        "ThemeSegment",
        back_populates="theme",
        order_by="ThemeSegment.segment_order",
        cascade="all, delete-orphan"
    )
    consequences = relationship(
        "ThemeConsequence",
        back_populates="theme",
        order_by="ThemeConsequence.display_order",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_theme_category", "category"),
        Index("ix_theme_importance", "order_of_importance"),
        Index("ix_theme_parent", "parent_theme_id"),
    )

    @property
    def category_label_ar(self) -> str:
        return THEME_CATEGORY_TRANSLATIONS.get(self.category, {}).get("ar", self.category)

    @property
    def category_label_en(self) -> str:
        return THEME_CATEGORY_TRANSLATIONS.get(self.category, {}).get("en", self.category)

    @property
    def category_order(self) -> int:
        return THEME_CATEGORY_ORDER.get(self.category, 99)

    def __repr__(self) -> str:
        return f"<QuranicTheme(id={self.id}, title_ar={self.title_ar})>"


# =============================================================================
# THEME SEGMENT MODEL
# =============================================================================

class ThemeSegment(Base):
    """
    A theme segment represents a theme as it appears in specific Quranic verses.

    Each segment links a theme to a verse range with:
    - Summary explaining how the theme manifests in these verses
    - Evidence from tafsir (REQUIRED - enforced by CHECK constraint)
    - Semantic tags for cross-referencing
    - Revelation context (Makki/Madani)

    GROUNDING RULE: evidence_chunk_ids MUST have at least 1 element.
    """
    __tablename__ = "theme_segments"

    id = Column(String(200), primary_key=True)
    theme_id = Column(
        String(100),
        ForeignKey("quranic_themes.id"),
        nullable=False
    )

    # Ordering
    segment_order = Column(Integer, nullable=False)
    chronological_index = Column(Integer, nullable=True)

    # Quran location
    sura_no = Column(Integer, nullable=False, index=True)
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)

    # Content
    title_ar = Column(String(200), nullable=True)
    title_en = Column(String(200), nullable=True)
    summary_ar = Column(Text, nullable=False)
    summary_en = Column(Text, nullable=False)

    # Tags and context
    semantic_tags = Column(ARRAY(String), nullable=True)
    revelation_context = Column(String(20), nullable=True)
    is_entry_point = Column(Boolean, default=False)
    importance_weight = Column(Float, default=0.5)
    is_verified = Column(Boolean, default=False)

    # CRITICAL: Evidence grounding
    # Format: [{"source_id": "ibn_kathir_ar", "chunk_id": "...", "snippet": "..."}]
    evidence_sources = Column(JSONB, nullable=False)
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Discovery fields (for Quran-wide theme discovery)
    match_type = Column(String(50), nullable=True, default='manual')  # lexical, root, semantic, mixed, manual
    confidence = Column(Float, nullable=True, default=1.0)  # 0.0-1.0 confidence score
    reasons_ar = Column(Text, nullable=True)  # Arabic explanation of why verse belongs to theme
    reasons_en = Column(Text, nullable=True)  # English explanation
    is_core = Column(Boolean, nullable=True, default=True)  # True if core verse, False if supporting
    discovered_at = Column(DateTime, nullable=True)  # When segment was discovered by automated process

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    theme = relationship("QuranicTheme", back_populates="segments")

    __table_args__ = (
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_theme_segment_has_evidence"
        ),
        Index("ix_segment_theme", "theme_id"),
        Index("ix_segment_location", "sura_no", "ayah_start"),
        Index("ix_segment_revelation", "revelation_context"),
        Index("ix_segment_chronological", "theme_id", "chronological_index"),
    )

    @property
    def verse_reference(self) -> str:
        """Return formatted verse reference like '2:21-22' or '112:1'."""
        if self.ayah_start == self.ayah_end:
            return f"{self.sura_no}:{self.ayah_start}"
        return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"

    @property
    def verse_count(self) -> int:
        """Return number of verses covered by this segment."""
        return self.ayah_end - self.ayah_start + 1

    @property
    def evidence_count(self) -> int:
        """Return number of evidence sources."""
        return len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0

    def __repr__(self) -> str:
        return f"<ThemeSegment(id={self.id}, theme={self.theme_id}, ref={self.verse_reference})>"


# =============================================================================
# THEME CONNECTION MODEL
# =============================================================================

class ThemeConnection(Base):
    """
    Connection between theme segments.

    Connections represent relationships between different verse segments
    where a theme appears, such as:
    - ELABORATION: Later verses elaborate on earlier ones
    - CONTRAST: Contrasting perspectives on the same theme
    - PROGRESSION: Progressive revelation of the theme

    is_sequential indicates if this is part of the recommended reading order.
    """
    __tablename__ = "theme_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_segment_id = Column(
        String(200),
        ForeignKey("theme_segments.id"),
        nullable=False
    )
    target_segment_id = Column(
        String(200),
        ForeignKey("theme_segments.id"),
        nullable=False
    )

    edge_type = Column(String(50), nullable=False)
    is_sequential = Column(Boolean, default=False)
    strength = Column(Float, default=0.5)

    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)
    evidence_chunk_ids = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_segment = relationship(
        "ThemeSegment",
        foreign_keys=[source_segment_id]
    )
    target_segment = relationship(
        "ThemeSegment",
        foreign_keys=[target_segment_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "source_segment_id", "target_segment_id", "edge_type",
            name="uq_theme_connection"
        ),
        Index("ix_theme_conn_source", "source_segment_id"),
        Index("ix_theme_conn_target", "target_segment_id"),
        Index("ix_theme_conn_type", "edge_type"),
    )

    @property
    def edge_type_label_ar(self) -> str:
        return EDGE_TYPE_TRANSLATIONS.get(self.edge_type, {}).get("ar", self.edge_type)

    @property
    def edge_type_label_en(self) -> str:
        return EDGE_TYPE_TRANSLATIONS.get(self.edge_type, {}).get("en", self.edge_type)

    def __repr__(self) -> str:
        return f"<ThemeConnection(source={self.source_segment_id}, target={self.target_segment_id}, type={self.edge_type})>"


# =============================================================================
# THEME CONSEQUENCE MODEL
# =============================================================================

class ThemeConsequence(Base):
    """
    Divine consequences (السنن الإلهية) for themes.

    Each theme can have associated consequences:
    - REWARD: What Allah promises for those who follow this theme
    - PUNISHMENT: What Allah warns for those who violate it
    - BLESSING: Worldly benefits mentioned in Quran
    - WARNING: Divine warnings about neglecting the theme

    GROUNDING RULE: evidence_chunk_ids MUST have at least 1 element.
    """
    __tablename__ = "theme_consequences"

    id = Column(Integer, primary_key=True, autoincrement=True)

    theme_id = Column(
        String(100),
        ForeignKey("quranic_themes.id"),
        nullable=False
    )
    consequence_type = Column(String(50), nullable=False)

    description_ar = Column(Text, nullable=False)
    description_en = Column(Text, nullable=False)

    # Format: [{"sura": 2, "ayah": 155, "relevance": "primary"}]
    supporting_verses = Column(JSONB, nullable=False)
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    theme = relationship("QuranicTheme", back_populates="consequences")

    __table_args__ = (
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_consequence_has_evidence"
        ),
        Index("ix_consequence_theme", "theme_id"),
        Index("ix_consequence_type", "consequence_type"),
    )

    @property
    def type_label_ar(self) -> str:
        return CONSEQUENCE_TYPE_TRANSLATIONS.get(self.consequence_type, {}).get("ar", self.consequence_type)

    @property
    def type_label_en(self) -> str:
        return CONSEQUENCE_TYPE_TRANSLATIONS.get(self.consequence_type, {}).get("en", self.consequence_type)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0

    def __repr__(self) -> str:
        return f"<ThemeConsequence(theme={self.theme_id}, type={self.consequence_type})>"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_category_display_order() -> List[str]:
    """Return categories in methodological order."""
    return sorted(THEME_CATEGORY_ORDER.keys(), key=lambda x: THEME_CATEGORY_ORDER[x])


def validate_tafsir_source(source_id: str) -> bool:
    """Validate that a tafsir source is from approved 4 madhab sources."""
    APPROVED_SOURCES = [
        "ibn_kathir_ar", "ibn_kathir_en",
        "tabari_ar",
        "qurtubi_ar",
        "baghawi_ar",
        "saadi_ar",
        "nasafi_ar",       # Madarik al-Tanzil (Hanafi)
        "shinqiti_ar",     # Adwa al-Bayan
        "jalalayn_ar", "jalalayn_en",
    ]
    return source_id in APPROVED_SOURCES


# =============================================================================
# SUGGESTION STATUS & ORIGIN
# =============================================================================

class SuggestionStatus(str, Enum):
    """Status of a theme suggestion for admin review."""
    PENDING = "pending"         # Awaiting review
    APPROVED = "approved"       # Approved and promoted to segment
    REJECTED = "rejected"       # Rejected by reviewer


class SuggestionOrigin(str, Enum):
    """Origin of a theme suggestion."""
    AUTO_DISCOVERY = "auto_discovery"  # Discovered by automated script
    MANUAL = "manual"                  # Manually submitted


SUGGESTION_STATUS_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "pending": {"ar": "قيد المراجعة", "en": "Pending Review"},
    "approved": {"ar": "موافق عليه", "en": "Approved"},
    "rejected": {"ar": "مرفوض", "en": "Rejected"},
}

SUGGESTION_ORIGIN_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "auto_discovery": {"ar": "اكتشاف آلي", "en": "Auto Discovery"},
    "manual": {"ar": "إدخال يدوي", "en": "Manual Entry"},
}


# Approval requirements for auto-discovered suggestions
APPROVAL_MIN_SOURCES = 2                # Minimum tafsir sources for approval
APPROVAL_HIGH_CONFIDENCE = 0.85         # High confidence threshold
APPROVAL_DIRECT_MATCH_TYPES = {'direct', 'exact', 'lexical', 'root'}  # Direct match types

# Required attribution phrases in reasons_ar for auto-discovered content
ATTRIBUTION_PHRASES = [
    "استنتج آليًا من",   # Inferred automatically from
    "تفسير ابن كثير",   # Ibn Kathir tafsir
    "تفسير الطبري",     # Tabari tafsir
    "تفسير القرطبي",    # Qurtubi tafsir
    "تفسير البغوي",     # Baghawi tafsir
    "تفسير السعدي",     # Sa'di tafsir
]


# =============================================================================
# THEME SUGGESTION MODEL
# =============================================================================

class ThemeSuggestion(Base):
    """
    Theme suggestion for admin review workflow.

    Suggestions are created by:
    1. Discovery scripts running in 'suggest' mode
    2. User-submitted suggestions (future)

    Admin reviewers can:
    - APPROVE: Convert suggestion to ThemeSegment
    - REJECT: Reject with reason
    - MODIFY: Edit before approving

    Workflow:
    1. Discovery script finds potential verses
    2. Creates ThemeSuggestion with status=PENDING
    3. Admin reviews in admin panel
    4. On approve: Creates ThemeSegment, deletes suggestion
    5. On reject: Updates status, keeps for audit trail
    """
    __tablename__ = "theme_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Which theme this suggestion is for
    theme_id = Column(
        String(100),
        ForeignKey("quranic_themes.id"),
        nullable=False
    )

    # Quran location
    sura_no = Column(Integer, nullable=False)
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)

    # Discovery metadata
    match_type = Column(String(50), nullable=False)  # lexical, root, semantic, mixed
    confidence = Column(Float, nullable=False)
    reasons_ar = Column(Text, nullable=False)
    reasons_en = Column(Text, nullable=True)

    # Evidence supporting this suggestion
    evidence_sources = Column(JSONB, nullable=False)
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Review workflow
    status = Column(String(20), nullable=False, default='pending', index=True)
    reviewed_by = Column(String(100), nullable=True)  # Admin username
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Tracking & Origin
    origin = Column(String(50), default='auto_discovery', index=True)  # auto_discovery, manual
    source = Column(String(50), default='discovery')  # discovery, user, import (legacy)
    batch_id = Column(String(100), nullable=True)  # For batch imports
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    theme = relationship("QuranicTheme")

    __table_args__ = (
        UniqueConstraint(
            "theme_id", "sura_no", "ayah_start", "ayah_end",
            name="uq_theme_suggestion_location"
        ),
        Index("ix_suggestion_theme", "theme_id"),
        Index("ix_suggestion_status", "status"),
        Index("ix_suggestion_location", "sura_no", "ayah_start"),
        Index("ix_suggestion_confidence", "confidence"),
        Index("ix_suggestion_batch", "batch_id"),
    )

    @property
    def verse_reference(self) -> str:
        """Return formatted verse reference like '2:21-22' or '112:1'."""
        if self.ayah_start == self.ayah_end:
            return f"{self.sura_no}:{self.ayah_start}"
        return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"

    @property
    def status_label_ar(self) -> str:
        return SUGGESTION_STATUS_TRANSLATIONS.get(self.status, {}).get("ar", self.status)

    @property
    def status_label_en(self) -> str:
        return SUGGESTION_STATUS_TRANSLATIONS.get(self.status, {}).get("en", self.status)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0

    @property
    def origin_label_ar(self) -> str:
        return SUGGESTION_ORIGIN_TRANSLATIONS.get(self.origin, {}).get("ar", self.origin)

    @property
    def origin_label_en(self) -> str:
        return SUGGESTION_ORIGIN_TRANSLATIONS.get(self.origin, {}).get("en", self.origin)

    @property
    def is_auto_discovery(self) -> bool:
        """Check if this suggestion was auto-discovered."""
        return self.origin == SuggestionOrigin.AUTO_DISCOVERY.value or self.origin == 'auto_discovery'

    @property
    def meets_approval_requirements(self) -> bool:
        """
        Check if suggestion meets requirements for approval.

        APPROVAL RULES (Sunni-safe):
        1. Manual suggestions: Always approvable (scholar-submitted)
        2. Auto-discovered suggestions require:
           - At least 2 tafsir sources OR
           - (confidence >= 0.85 AND match_type in {direct, exact, lexical, root})
        """
        # Manual suggestions are always approvable
        if not self.is_auto_discovery:
            return True

        # Rule 1: At least 2 tafsir sources
        if self.evidence_count >= APPROVAL_MIN_SOURCES:
            return True

        # Rule 2: High confidence with direct match
        match_type = (self.match_type or '').lower()
        if self.confidence >= APPROVAL_HIGH_CONFIDENCE and match_type in APPROVAL_DIRECT_MATCH_TYPES:
            return True

        return False

    @property
    def approval_blockers(self) -> List[str]:
        """
        Return list of reasons why this suggestion cannot be approved.

        Empty list means the suggestion is ready for approval.
        """
        blockers = []

        if not self.is_auto_discovery:
            return blockers  # Manual = no blockers

        if self.evidence_count < APPROVAL_MIN_SOURCES:
            blocker = f"يحتاج {APPROVAL_MIN_SOURCES} مصادر تفسير على الأقل (الحالي: {self.evidence_count})"
            blockers.append(blocker)

        match_type = (self.match_type or '').lower()
        if self.confidence < APPROVAL_HIGH_CONFIDENCE:
            blocker = f"درجة الثقة ({self.confidence:.2f}) أقل من {APPROVAL_HIGH_CONFIDENCE}"
            blockers.append(blocker)

        if match_type not in APPROVAL_DIRECT_MATCH_TYPES:
            blocker = f"نوع المطابقة '{match_type}' ليس من الأنواع المباشرة"
            blockers.append(blocker)

        # If high confidence + direct match, clear the blockers
        if self.confidence >= APPROVAL_HIGH_CONFIDENCE and match_type in APPROVAL_DIRECT_MATCH_TYPES:
            return []

        # If enough sources, clear the blockers
        if self.evidence_count >= APPROVAL_MIN_SOURCES:
            return []

        return blockers

    @property
    def has_proper_attribution(self) -> bool:
        """
        Check if reasons_ar has proper attribution for auto-discovered content.

        Auto-discovered suggestions must include attribution phrases like:
        - "استنتج آليًا من..." (Inferred automatically from...)
        - Or explicit tafsir citations
        """
        if not self.is_auto_discovery:
            return True  # Manual = no attribution needed

        reasons = self.reasons_ar or ''
        for phrase in ATTRIBUTION_PHRASES:
            if phrase in reasons:
                return True

        return False

    def __repr__(self) -> str:
        return f"<ThemeSuggestion(id={self.id}, theme={self.theme_id}, ref={self.verse_reference}, status={self.status}, origin={self.origin})>"
