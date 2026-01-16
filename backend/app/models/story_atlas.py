"""
Story Atlas Models - Quran-wide story indexing with Person/Place/Time classification.

DESIGN PHILOSOPHY:
==================
The Story Atlas provides comprehensive coverage of ALL Quranic narratives,
organized by three primary facets:

1. PERSON: Prophets, named characters, groups/nations
2. PLACE: Locations (explicit in Quran or inferred from tafsir)
3. TIME: Era buckets (pre-history, ancient, etc.)

GROUNDING RULES:
================
- NON-NEGOTIABLE: Do NOT invent details
- If time/place not explicit in Quran, mark as inferred (from tafsir) or unknown
- Every claim must have evidence_basis: "explicit" (Quran text) or "inferred" (tafsir)

STRUCTURE:
==========
- StoryCluster: A coherent narrative unit (e.g., "Musa & Pharaoh", "People of the Cave")
- StoryEvent: A node in the story timeline with clear narrative role
- Facets: Person, Place, Era for filtering and exploration
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

class ClusterCategory(str, Enum):
    """Categories of story clusters."""
    PROPHET = "prophet"              # Stories of prophets
    NAMED_CHARACTER = "named_char"   # Non-prophet named individuals (Luqman, Maryam, Dhul-Qarnayn)
    NATION = "nation"                # Peoples/nations (ʿĀd, Thamūd, People of Lūṭ)
    PARABLE = "parable"              # Parables/lessons (Two Gardens, etc.)
    HISTORICAL = "historical"        # Historical events (Elephant, Sabbath Breakers)
    UNSEEN = "unseen"                # Afterlife, angels, jinn


class EvidenceBasis(str, Enum):
    """Basis for claims about place/time."""
    EXPLICIT = "explicit"    # Directly stated in Quran
    INFERRED = "inferred"    # Derived from tafsir
    UNKNOWN = "unknown"      # Cannot be determined


class NarrativeRole(str, Enum):
    """Narrative role of a story event."""
    INTRODUCTION = "introduction"
    WARNING = "warning"
    TRIAL = "trial"
    MIRACLE = "miracle"
    MIGRATION = "migration"
    CONFRONTATION = "confrontation"
    DIVINE_INTERVENTION = "divine_intervention"
    OUTCOME = "outcome"
    REFLECTION = "reflection"
    DIALOGUE = "dialogue"
    PROPHECY = "prophecy"


class EraBucket(str, Enum):
    """Time era buckets for classification."""
    PRIMORDIAL = "primordial"        # Adam, creation
    ANCIENT_PROPHETS = "ancient"     # Nuh, Hud, Salih, Ibrahim
    EGYPT_ERA = "egypt"              # Yusuf, Musa
    ISRAELITE = "israelite"          # Dawud, Sulayman, Zakariyya, Yahya, Isa
    PRE_ISLAMIC = "pre_islamic"      # Dhul-Qarnayn, People of Cave, Elephant
    UNKNOWN = "unknown"


# =============================================================================
# STORY CLUSTER (Main entity)
# =============================================================================

class StoryCluster(Base):
    """
    A coherent Quranic narrative unit.

    Examples:
    - "Musa & Pharaoh" (prophet + confrontation arc)
    - "People of the Cave" (Surah Al-Kahf)
    - "Owners of Two Gardens" (parable)
    - "ʿĀd & Hud" (nation + prophet)
    """
    __tablename__ = "story_clusters"

    id = Column(String(100), primary_key=True)  # e.g., "cluster_musa_pharaoh"

    # =========================================================================
    # TITLES
    # =========================================================================
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=False)

    # Short memorable title for UI
    short_title_ar = Column(String(100), nullable=True)
    short_title_en = Column(String(100), nullable=True)

    # =========================================================================
    # CLASSIFICATION
    # =========================================================================
    category = Column(String(50), nullable=False)  # From ClusterCategory

    # Primary persons (prophets/characters)
    main_persons = Column(ARRAY(String), nullable=True)  # ["Musa", "Firawn"]

    # Groups/nations involved
    groups = Column(ARRAY(String), nullable=True)  # ["Bani Israil", "Egyptians"]

    # Tags for search/filtering
    tags = Column(ARRAY(String), nullable=True)  # ["liberation", "miracles", "patience"]

    # =========================================================================
    # PLACE CLASSIFICATION
    # =========================================================================
    # Format: [{"name": "Egypt", "name_ar": "مصر", "basis": "explicit/inferred"}]
    places = Column(JSONB, nullable=True)

    # =========================================================================
    # TIME CLASSIFICATION
    # =========================================================================
    era = Column(String(50), nullable=True)  # From EraBucket
    era_basis = Column(String(20), default="unknown")  # From EvidenceBasis

    # Optional: approximate time description
    time_description_ar = Column(String(200), nullable=True)
    time_description_en = Column(String(200), nullable=True)

    # =========================================================================
    # QURAN COVERAGE
    # =========================================================================
    # All ayah spans where this story appears
    # Format: [{"sura": 18, "start": 83, "end": 98}, {"sura": 21, "start": 85, "end": 86}]
    ayah_spans = Column(JSONB, nullable=False)

    # Primary sura (where story is most complete)
    primary_sura = Column(Integer, nullable=True)

    # Total verse count
    total_verses = Column(Integer, default=0)

    # Suras mentioned (for quick filtering)
    suras_mentioned = Column(ARRAY(Integer), nullable=True)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    summary_ar = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    # Key lessons (1-3 bullet points)
    lessons_ar = Column(ARRAY(String), nullable=True)
    lessons_en = Column(ARRAY(String), nullable=True)

    # =========================================================================
    # METADATA
    # =========================================================================
    is_complete = Column(Boolean, default=False)  # Has all events been added?
    event_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("StoryEvent", back_populates="cluster", lazy="selectin",
                         order_by="StoryEvent.chronological_index")

    __table_args__ = (
        Index("ix_cluster_category", "category"),
        Index("ix_cluster_era", "era"),
        Index("ix_cluster_primary_sura", "primary_sura"),
    )

    def __repr__(self):
        return f"<StoryCluster {self.id}: {self.title_en}>"

    @property
    def verse_count(self) -> int:
        """Calculate total verses from ayah_spans."""
        if not self.ayah_spans:
            return 0
        total = 0
        for span in self.ayah_spans:
            total += span.get("end", span.get("start", 0)) - span.get("start", 0) + 1
        return total


# =============================================================================
# STORY EVENT (Timeline node)
# =============================================================================

class StoryEvent(Base):
    """
    A node in the story timeline - a coherent narrative segment.

    Each event represents a discrete moment or phase in the story,
    with a clear narrative role and evidence grounding.
    """
    __tablename__ = "story_events"

    id = Column(String(150), primary_key=True)  # e.g., "cluster_musa_pharaoh:staff_miracle"
    cluster_id = Column(String(100), ForeignKey("story_clusters.id"), nullable=False, index=True)

    # =========================================================================
    # TITLES (Human-friendly, memorization-ready)
    # =========================================================================
    title_ar = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)

    # =========================================================================
    # NARRATIVE STRUCTURE
    # =========================================================================
    narrative_role = Column(String(50), nullable=False)  # From NarrativeRole

    # Position in story timeline (1-based)
    chronological_index = Column(Integer, nullable=False)

    # Is this the entry point?
    is_entry_point = Column(Boolean, default=False)

    # =========================================================================
    # QURAN LOCATION
    # =========================================================================
    sura_no = Column(Integer, nullable=False, index=True)
    aya_start = Column(Integer, nullable=False)
    aya_end = Column(Integer, nullable=False)

    # =========================================================================
    # CONTENT (Memorization-friendly)
    # =========================================================================
    summary_ar = Column(Text, nullable=False)  # 1-2 lines
    summary_en = Column(Text, nullable=False)

    # Optional memorization cue
    memorization_cue_ar = Column(String(200), nullable=True)
    memorization_cue_en = Column(String(200), nullable=True)

    # Semantic tags for cross-referencing
    semantic_tags = Column(ARRAY(String), nullable=True)

    # =========================================================================
    # EVIDENCE GROUNDING (Required)
    # =========================================================================
    # At least one tafsir citation required
    # Format: [{"source_id": "ibn_kathir_en", "chunk_id": "...", "snippet": "..."}]
    evidence = Column(JSONB, nullable=False)

    # =========================================================================
    # METADATA
    # =========================================================================
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cluster = relationship("StoryCluster", back_populates="events")

    __table_args__ = (
        Index("ix_event_cluster", "cluster_id"),
        Index("ix_event_location", "sura_no", "aya_start"),
        Index("ix_event_role", "narrative_role"),
        Index("ix_event_chronological", "cluster_id", "chronological_index"),
        CheckConstraint(
            "jsonb_array_length(evidence) >= 1",
            name="ck_event_has_evidence"
        ),
    )

    def __repr__(self):
        return f"<StoryEvent {self.id} ({self.sura_no}:{self.aya_start}-{self.aya_end})>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference string."""
        if self.aya_start == self.aya_end:
            return f"{self.sura_no}:{self.aya_start}"
        return f"{self.sura_no}:{self.aya_start}-{self.aya_end}"


# =============================================================================
# STORY EVENT CONNECTIONS
# =============================================================================

class EventConnection(Base):
    """
    Connection between story events within or across clusters.
    """
    __tablename__ = "event_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_event_id = Column(String(150), ForeignKey("story_events.id"), nullable=False, index=True)
    target_event_id = Column(String(150), ForeignKey("story_events.id"), nullable=False, index=True)

    # Edge type
    edge_type = Column(String(50), nullable=False)  # chronological_next, cause_effect, thematic, parallel

    # Is this a chronological edge (must form DAG)
    is_chronological = Column(Boolean, default=False)

    # Connection strength (0.0-1.0)
    strength = Column(Float, default=1.0)

    # Justification
    justification_en = Column(Text, nullable=True)
    justification_ar = Column(Text, nullable=True)

    # Evidence
    evidence_chunk_ids = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_event = relationship("StoryEvent", foreign_keys=[source_event_id])
    target_event = relationship("StoryEvent", foreign_keys=[target_event_id])

    __table_args__ = (
        Index("ix_event_conn_source", "source_event_id"),
        Index("ix_event_conn_target", "target_event_id"),
    )


# =============================================================================
# CLUSTER CONNECTIONS (Cross-story links)
# =============================================================================

class ClusterConnection(Base):
    """
    Thematic connections between story clusters.

    Examples:
    - Musa ↔ Yusuf (both in Egypt)
    - Dhul-Qarnayn ↔ Sulayman (righteous power)
    """
    __tablename__ = "cluster_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_cluster_id = Column(String(100), ForeignKey("story_clusters.id"), nullable=False, index=True)
    target_cluster_id = Column(String(100), ForeignKey("story_clusters.id"), nullable=False, index=True)

    # Connection type
    connection_type = Column(String(50), nullable=False)  # shared_theme, shared_person, shared_place, parallel

    # Strength
    strength = Column(Float, default=0.5)

    # Labels
    label_ar = Column(String(200), nullable=True)
    label_en = Column(String(200), nullable=True)

    # Shared attributes
    shared_persons = Column(ARRAY(String), nullable=True)
    shared_places = Column(ARRAY(String), nullable=True)
    shared_themes = Column(ARRAY(String), nullable=True)

    # Evidence
    evidence_chunk_ids = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_cluster = relationship("StoryCluster", foreign_keys=[source_cluster_id])
    target_cluster = relationship("StoryCluster", foreign_keys=[target_cluster_id])

    __table_args__ = (
        Index("ix_cluster_conn_source", "source_cluster_id"),
        Index("ix_cluster_conn_target", "target_cluster_id"),
        UniqueConstraint("source_cluster_id", "target_cluster_id", "connection_type",
                        name="uq_cluster_connection"),
    )
