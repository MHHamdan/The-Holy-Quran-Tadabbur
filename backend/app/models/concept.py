"""
Quran Concept Graph (QCG) Models

ONTOLOGY DESIGN:
================
This module implements a Topic Map-inspired concept layer for Quranic navigation:
- Concept: A semantic unit (theme, person, nation, place, miracle, pattern)
- Occurrence: Links concepts to specific ayat, segments, stories, or tafsir chunks
- Association: Semantic relationships between concepts with evidence grounding

EPISTEMIC RULES:
================
1. NO novel tafsir generation - all claims must be grounded
2. Every Association MUST have evidence_refs (ayah + tafsir chunk IDs)
3. If evidence is weak, display uncertainty: "لا توجد أدلة كافية"

CONCEPT TYPES:
==============
- theme: موضوع (patience, obedience, repentance, etc.)
- miracle: معجزة/آية (staff turning to snake, splitting of sea, etc.)
- person: شخصية (prophets, rulers, righteous individuals)
- nation: قوم/أمة (Aad, Thamud, Pharaoh's people, etc.)
- place: مكان (Egypt, Makkah, Madyan, etc.)
- moral_pattern: نمط سنني (test→patience→salvation pattern)
- rhetorical_device: أسلوب بلاغي (optional - quranic rhetoric patterns)

RELATION TYPES:
===============
- cause_effect: سبب ونتيجة (only if grounded in evidence)
- similarity: تشابه (shared themes/patterns)
- contrast: تضاد/مقارنة (opposing lessons)
- elaboration: تفصيل (one expands on another)
- summarization: إجمال (one summarizes another)
- attribute_of: صفة لـ (concept is attribute of another)
- sunnah_pattern: نمط سنني (divine pattern across stories)
- part_of: جزء من (concept is part of larger concept)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ConceptType(str, Enum):
    """Types of Quranic concepts."""
    THEME = "theme"                     # موضوع
    MIRACLE = "miracle"                 # معجزة/آية
    PERSON = "person"                   # شخصية
    NATION = "nation"                   # قوم/أمة
    PLACE = "place"                     # مكان
    MORAL_PATTERN = "moral_pattern"     # نمط سنني
    RHETORICAL_DEVICE = "rhetorical"    # أسلوب بلاغي


class RelationType(str, Enum):
    """Types of relationships between concepts."""
    CAUSE_EFFECT = "cause_effect"       # سبب ونتيجة
    SIMILARITY = "similarity"           # تشابه
    CONTRAST = "contrast"               # تضاد/مقارنة
    ELABORATION = "elaboration"         # تفصيل
    SUMMARIZATION = "summarization"     # إجمال
    ATTRIBUTE_OF = "attribute_of"       # صفة لـ
    SUNNAH_PATTERN = "sunnah_pattern"   # نمط سنني
    PART_OF = "part_of"                 # جزء من
    RELATED = "related"                 # عام - related


class OccurrenceRefType(str, Enum):
    """Types of references an occurrence can point to."""
    AYAH = "ayah"                       # Direct ayah reference
    SEGMENT = "segment"                 # Story segment
    STORY = "story"                     # Story
    CLUSTER = "cluster"                 # Story atlas cluster
    TAFSIR_CHUNK = "tafsir_chunk"       # Tafsir evidence


# =============================================================================
# CONCEPT MODEL
# =============================================================================

class Concept(Base):
    """
    A semantic concept in the Quran Concept Graph.

    Represents themes, miracles, persons, nations, places, and patterns
    that appear across the Quran and form the basis for semantic navigation.
    """
    __tablename__ = "concepts"

    id = Column(String(100), primary_key=True)  # e.g., "theme_patience", "person_musa"
    slug = Column(String(100), nullable=False, unique=True, index=True)

    # Bilingual labels
    label_ar = Column(String(200), nullable=False)
    label_en = Column(String(200), nullable=False)

    # Type classification
    concept_type = Column(String(50), nullable=False, index=True)  # From ConceptType enum

    # Aliases for search (multiple terms that refer to same concept)
    aliases_ar = Column(ARRAY(String), nullable=True)  # ["الصبر", "التصبر", "الصابرين"]
    aliases_en = Column(ARRAY(String), nullable=True)  # ["patience", "perseverance", "steadfastness"]

    # Short descriptions (NOT tafsir - just identification)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    # Hierarchy (for grouping)
    parent_concept_id = Column(String(100), ForeignKey("concepts.id"), nullable=True)

    # Icon/category hint for UI
    icon_hint = Column(String(50), nullable=True)  # "book", "user", "map-pin", etc.

    # Display order within type
    display_order = Column(Integer, default=0)

    # Is this concept verified/curated?
    is_curated = Column(Boolean, default=False)

    # Source of this concept (for traceability)
    source = Column(String(100), nullable=True)  # "story_themes", "curated_dict", "tafsir_extraction"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("Concept", remote_side=[id], backref="children")
    occurrences = relationship("Occurrence", back_populates="concept", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_concept_type_slug", "concept_type", "slug"),
        Index("ix_concept_label_ar", "label_ar"),
    )

    def __repr__(self):
        return f"<Concept {self.id}: {self.label_en}>"

    def to_dict(self, language: str = "en") -> dict:
        """Convert to API response format."""
        return {
            "id": self.id,
            "slug": self.slug,
            "label": self.label_ar if language == "ar" else self.label_en,
            "label_ar": self.label_ar,
            "label_en": self.label_en,
            "type": self.concept_type,
            "aliases": self.aliases_ar if language == "ar" else self.aliases_en,
            "description": self.description_ar if language == "ar" else self.description_en,
            "parent_id": self.parent_concept_id,
            "icon_hint": self.icon_hint,
            "is_curated": self.is_curated,
        }


# =============================================================================
# OCCURRENCE MODEL
# =============================================================================

class Occurrence(Base):
    """
    Links a concept to a specific location in Quran text or related content.

    An occurrence anchors a concept to:
    - Specific ayat (surah:ayah range)
    - Story segments
    - Stories
    - Atlas clusters
    - Tafsir chunks (as evidence)
    """
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to concept
    concept_id = Column(String(100), ForeignKey("concepts.id"), nullable=False, index=True)

    # Reference type and ID
    ref_type = Column(String(50), nullable=False)  # From OccurrenceRefType enum
    ref_id = Column(String(200), nullable=True)    # ID of referenced entity (segment_id, story_id, etc.)

    # Ayah location (always populated for Quran-grounded occurrences)
    sura_no = Column(Integer, nullable=True, index=True)
    ayah_start = Column(Integer, nullable=True)
    ayah_end = Column(Integer, nullable=True)

    # Relevance weight (0.0 - 1.0)
    weight = Column(Float, default=1.0)

    # Evidence grounding (CRITICAL for epistemic safety)
    evidence_chunk_ids = Column(ARRAY(String), nullable=True)  # Tafsir chunk IDs supporting this occurrence

    # Context/excerpt (short, for display)
    context_ar = Column(Text, nullable=True)
    context_en = Column(Text, nullable=True)

    # Is this occurrence verified?
    is_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    concept = relationship("Concept", back_populates="occurrences")

    __table_args__ = (
        Index("ix_occurrence_concept", "concept_id"),
        Index("ix_occurrence_ref", "ref_type", "ref_id"),
        Index("ix_occurrence_ayah", "sura_no", "ayah_start"),
    )

    def __repr__(self):
        return f"<Occurrence {self.concept_id} @ {self.ref_type}:{self.ref_id}>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference string."""
        if self.sura_no and self.ayah_start:
            if self.ayah_end and self.ayah_end != self.ayah_start:
                return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"
            return f"{self.sura_no}:{self.ayah_start}"
        return ""

    def to_dict(self, language: str = "en") -> dict:
        """Convert to API response format."""
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "verse_reference": self.verse_reference,
            "sura_no": self.sura_no,
            "ayah_start": self.ayah_start,
            "ayah_end": self.ayah_end,
            "weight": self.weight,
            "context": self.context_ar if language == "ar" else self.context_en,
            "has_evidence": bool(self.evidence_chunk_ids),
            "evidence_count": len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0,
        }


# =============================================================================
# ASSOCIATION MODEL
# =============================================================================

class Association(Base):
    """
    Semantic relationship between two concepts.

    EPISTEMIC REQUIREMENT:
    Every association MUST have evidence_refs to be displayed.
    If evidence is insufficient, the association should be flagged
    and displayed with uncertainty markers.
    """
    __tablename__ = "associations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Concepts being associated
    concept_a_id = Column(String(100), ForeignKey("concepts.id"), nullable=False, index=True)
    concept_b_id = Column(String(100), ForeignKey("concepts.id"), nullable=False, index=True)

    # Relationship type
    relation_type = Column(String(50), nullable=False)  # From RelationType enum

    # Direction indicator (some relations are directional)
    is_directional = Column(Boolean, default=False)  # If True, A→B, not B→A

    # Strength (0.0 - 1.0)
    strength = Column(Float, default=0.5)

    # Bilingual explanation (derived from evidence, not invented)
    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)

    # CRITICAL: Evidence grounding
    # Must include both ayah refs AND tafsir chunk IDs
    evidence_refs = Column(JSONB, nullable=False)
    # Format: {"ayah_refs": ["2:155", "3:200"], "chunk_ids": ["ibn_kathir:2:155", ...]}

    # Is evidence sufficient for confident display?
    has_sufficient_evidence = Column(Boolean, default=False)

    # Source of association
    source = Column(String(100), nullable=True)  # "story_themes", "curated", "tafsir_extraction"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    concept_a = relationship("Concept", foreign_keys=[concept_a_id])
    concept_b = relationship("Concept", foreign_keys=[concept_b_id])

    __table_args__ = (
        # Ensure evidence is provided
        CheckConstraint(
            "evidence_refs IS NOT NULL AND evidence_refs != '{}'::jsonb",
            name="ck_association_has_evidence"
        ),
        Index("ix_association_concepts", "concept_a_id", "concept_b_id"),
        Index("ix_association_type", "relation_type"),
        # Prevent duplicate associations (same concepts, same type)
        UniqueConstraint("concept_a_id", "concept_b_id", "relation_type", name="uq_association_pair"),
    )

    def __repr__(self):
        return f"<Association {self.concept_a_id} --[{self.relation_type}]--> {self.concept_b_id}>"

    def to_dict(self, language: str = "en") -> dict:
        """Convert to API response format."""
        return {
            "id": self.id,
            "concept_a_id": self.concept_a_id,
            "concept_b_id": self.concept_b_id,
            "relation_type": self.relation_type,
            "is_directional": self.is_directional,
            "strength": self.strength,
            "explanation": self.explanation_ar if language == "ar" else self.explanation_en,
            "has_sufficient_evidence": self.has_sufficient_evidence,
            "evidence_refs": self.evidence_refs,
        }


# =============================================================================
# RELATION TYPE TRANSLATIONS
# =============================================================================

RELATION_TYPE_TRANSLATIONS = {
    "cause_effect": {"ar": "سبب ونتيجة", "en": "Cause & Effect"},
    "similarity": {"ar": "تشابه", "en": "Similarity"},
    "contrast": {"ar": "تضاد", "en": "Contrast"},
    "elaboration": {"ar": "تفصيل", "en": "Elaboration"},
    "summarization": {"ar": "إجمال", "en": "Summarization"},
    "attribute_of": {"ar": "صفة لـ", "en": "Attribute of"},
    "sunnah_pattern": {"ar": "نمط سنني", "en": "Divine Pattern"},
    "part_of": {"ar": "جزء من", "en": "Part of"},
    "related": {"ar": "متصل", "en": "Related"},
}


CONCEPT_TYPE_TRANSLATIONS = {
    "theme": {"ar": "موضوع", "en": "Theme"},
    "miracle": {"ar": "معجزة", "en": "Miracle"},
    "person": {"ar": "شخصية", "en": "Person"},
    "nation": {"ar": "قوم", "en": "Nation"},
    "place": {"ar": "مكان", "en": "Place"},
    "moral_pattern": {"ar": "نمط سنني", "en": "Pattern"},
    "rhetorical": {"ar": "أسلوب بلاغي", "en": "Rhetorical"},
}
