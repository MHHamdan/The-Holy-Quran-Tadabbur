"""
Story and connection models for Quranic narrative tracking.

ONTOLOGY DESIGN PHILOSOPHY:
===========================
This ontology is specifically designed for Qur'anic storytelling, which differs
fundamentally from Western narrative structures:

1. THEMATIC GROUPING over linear plot:
   - Stories are told across multiple surahs for emphasis
   - Repetition serves pedagogical and spiritual purposes
   - Same event may appear with different lessons highlighted

2. CAUSE-EFFECT over chronology:
   - Divine tests → Human response → Divine outcome
   - Actions tied to moral consequences
   - Temporal sequence secondary to lesson structure

3. CYCLICAL PATTERNS:
   - Prophet → Rejection → Divine intervention → Outcome
   - Nations repeat patterns (Nuh, 'Ad, Thamud, Lut, etc.)
   - Lessons meant for memorization and reflection

4. EVIDENCE GROUNDING:
   - Every claim must be grounded in Qur'an text or classical tafsir
   - No speculation or Western interpretive frameworks
   - Scholarly chain preserved through evidence_chunk_ids

NODE-EDGE STRUCTURE:
===================
- Nodes: Story segments with narrative roles and pedagogical summaries
- Edges: Relationships with types, strength, and tafsir justification
- DAG constraint: Chronological edges form acyclic path
- Cross-links: Thematic edges may create cycles (allowed)
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
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


# =============================================================================
# ENUMERATIONS - Core ontology types
# =============================================================================

class StoryCategory(str, Enum):
    """Categories of Quranic stories."""
    PROPHET = "prophet"
    NATION = "nation"
    PARABLE = "parable"
    HISTORICAL = "historical"
    UNSEEN = "unseen"  # Afterlife, angels, etc.


class NarrativeRole(str, Enum):
    """
    The narrative role of a story segment within the overall story arc.

    This enum captures Qur'anic storytelling patterns, not Western plot structure.
    A segment may emphasize one primary role while touching on others.
    """
    # Opening/Context
    INTRODUCTION = "introduction"           # Scene setting, historical context
    DIVINE_MISSION = "divine_mission"       # Prophet receives command/revelation

    # Journey/Development
    JOURNEY_PHASE = "journey_phase"         # Physical or spiritual travel
    ENCOUNTER = "encounter"                 # Meeting people, facing challenges

    # Test/Trial
    TEST_OR_TRIAL = "test_or_trial"         # Divine test of faith/character
    MORAL_DECISION = "moral_decision"       # Critical choice point

    # Divine Action
    DIVINE_INTERVENTION = "divine_intervention"  # Allah's direct action
    MIRACLE = "miracle"                     # Supernatural sign/proof

    # Outcome/Resolution
    OUTCOME = "outcome"                     # Result of actions/choices
    PUNISHMENT = "punishment"               # Consequence for disbelief/sin
    REWARD = "reward"                       # Blessing for faith/obedience

    # Reflection/Lesson
    REFLECTION = "reflection"               # Explicit lesson or moral
    WARNING = "warning"                     # Admonition for future
    GLAD_TIDINGS = "glad_tidings"          # Promise of good for believers


class EdgeType(str, Enum):
    """
    Types of edges connecting story segments.

    Edges are categorized by their semantic relationship:
    - TEMPORAL: Time-based ordering
    - CAUSAL: Cause-effect relationships
    - THEMATIC: Conceptual connections
    """
    # Temporal/Sequential (must form DAG)
    CHRONOLOGICAL_NEXT = "chronological_next"   # Direct temporal succession
    CONTINUATION = "continuation"                # Same narrative continues

    # Causal (may form DAG)
    CAUSE_EFFECT = "cause_effect"               # A leads to B
    CONSEQUENCE = "consequence"                  # B results from A

    # Thematic (may create cycles - allowed)
    THEMATIC_LINK = "thematic_link"             # Shared theme/concept
    PARALLEL = "parallel"                        # Similar events/patterns
    CONTRAST = "contrast"                        # Opposing lessons
    REFERENCE = "reference"                      # Brief mention
    EXPANSION = "expansion"                      # Adds details to prior mention

    # Cross-story (for inter-story connections)
    SHARED_FIGURE = "shared_figure"             # Same person appears
    SHARED_THEME = "shared_theme"               # Same lesson/concept
    PROPHETIC_CHAIN = "prophetic_chain"         # Succession of prophets
    HISTORICAL_CONTEXT = "historical_context"   # Same era/location


# Legacy alias for backward compatibility
ConnectionType = EdgeType


class Theme(Base):
    """
    Quranic themes that appear across stories and verses.
    """
    __tablename__ = "themes"

    id = Column(String(50), primary_key=True)  # e.g., "tawakkul", "sabr"
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)

    # Hierarchy
    parent_theme_id = Column(String(50), ForeignKey("themes.id"), nullable=True)

    # Description
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    # Related themes (for graph)
    related_themes = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("Theme", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<Theme {self.id}: {self.name_en}>"


class Story(Base):
    """
    Quranic stories - major narratives mentioned in the Quran.
    """
    __tablename__ = "stories"

    id = Column(String(50), primary_key=True)  # e.g., "story_musa", "story_ibrahim"
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)

    category = Column(String(50), nullable=False)  # From StoryCategory enum

    # Main figures in the story
    main_figures = Column(ARRAY(String), nullable=True)  # ["Musa", "Firawn"]

    # Themes covered
    themes = Column(ARRAY(String), nullable=True)  # ["liberation", "miracles"]

    # Summary
    summary_ar = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    # Historical context
    timeline_era = Column(String(50), nullable=True)  # "ancient_egypt", "pre-islamic"

    # Lessons
    lessons_ar = Column(Text, nullable=True)
    lessons_en = Column(Text, nullable=True)

    # Metadata
    total_verses = Column(Integer, default=0)
    suras_mentioned = Column(ARRAY(Integer), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    segments = relationship("StorySegment", back_populates="story", lazy="selectin")

    def __repr__(self):
        return f"<Story {self.id}: {self.name_en}>"


class StorySegment(Base):
    """
    Story segments - portions of a story as they appear in different surahs.

    A story like Musa's appears in 27+ surahs, each segment captures
    a specific portion of the narrative in a specific location.

    ONTOLOGY FIELDS:
    ================
    - narrative_role: The segment's function in the story arc (NarrativeRole enum)
    - chronological_index: Position in temporal sequence (1-based, local to story)
    - semantic_tags: Concepts/themes for cross-referencing
    - evidence_sources: Tafsir citations with explanations

    PEDAGOGICAL DESIGN:
    ===================
    - title_ar/en: Short, memorable label (not just ayah range)
    - summary_ar/en: 1-2 sentences for understanding (not tafsir copy)
    - memorization_cue: Optional mnemonic or key phrase
    """
    __tablename__ = "story_segments"

    id = Column(String(100), primary_key=True)  # e.g., "musa_birth_qasas"
    story_id = Column(String(50), ForeignKey("stories.id"), nullable=False, index=True)

    # =========================================================================
    # NARRATIVE STRUCTURE (Enhanced ontology)
    # =========================================================================

    # Position in narrative
    narrative_order = Column(Integer, nullable=False)  # Order as told in Quran
    chronological_index = Column(Integer, nullable=True)  # Position in timeline (may differ from narrative_order)

    # Role in story arc (from NarrativeRole enum)
    narrative_role = Column(String(50), nullable=True)  # "introduction", "divine_mission", "test_or_trial", etc.

    # Legacy field - kept for backward compatibility
    segment_type = Column(String(50), nullable=True)  # Deprecated: use narrative_role

    # What aspect of the story is covered
    aspect = Column(String(100), nullable=True)  # "birth", "exile", "return", "revelation"

    # =========================================================================
    # QURAN LOCATION
    # =========================================================================

    sura_no = Column(Integer, nullable=False, index=True)
    aya_start = Column(Integer, nullable=False)
    aya_end = Column(Integer, nullable=False)

    # Verse IDs (for joining with quran_verses table)
    verse_ids = Column(ARRAY(Integer), nullable=True)

    # =========================================================================
    # SEMANTIC TAGGING
    # =========================================================================

    # Semantic tags for thematic linking (e.g., ["justice", "power", "travel", "barrier"])
    semantic_tags = Column(ARRAY(String), nullable=True)

    # =========================================================================
    # PEDAGOGICAL CONTENT
    # =========================================================================

    # Human-readable title (not just ayah range)
    title_ar = Column(String(200), nullable=True)  # "الرحلة إلى الغرب - اختبار العدل"
    title_en = Column(String(200), nullable=True)  # "Journey to the West - Justice Test"

    # Pedagogical summary (1-2 sentences, for understanding)
    summary_ar = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    # Key points for learning
    key_points_ar = Column(ARRAY(String), nullable=True)
    key_points_en = Column(ARRAY(String), nullable=True)

    # Memorization aid (optional mnemonic)
    memorization_cue_ar = Column(String(200), nullable=True)
    memorization_cue_en = Column(String(200), nullable=True)

    # =========================================================================
    # EVIDENCE SOURCES
    # =========================================================================

    # Tafsir evidence as structured data
    # Format: [{"source_id": "ibn_kathir_ar", "chunk_id": "...", "snippet": "..."}]
    evidence_sources = Column(JSONB, nullable=True)

    # Legacy: simple chunk IDs (kept for backward compatibility)
    evidence_chunk_ids = Column(ARRAY(String), nullable=True)

    # =========================================================================
    # METADATA
    # =========================================================================

    # Is this segment an entry point for the story?
    is_entry_point = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    story = relationship("Story", back_populates="segments")

    __table_args__ = (
        Index("ix_segment_story", "story_id"),
        Index("ix_segment_location", "sura_no", "aya_start", "aya_end"),
        Index("ix_segment_narrative_role", "narrative_role"),
        Index("ix_segment_chronological", "story_id", "chronological_index"),
    )

    def __repr__(self):
        return f"<StorySegment {self.id} ({self.sura_no}:{self.aya_start}-{self.aya_end})>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference for this segment."""
        if self.aya_start == self.aya_end:
            return f"{self.sura_no}:{self.aya_start}"
        return f"{self.sura_no}:{self.aya_start}-{self.aya_end}"

    @property
    def display_title(self) -> str:
        """Get display title, falling back to verse reference."""
        return self.title_en or self.aspect or self.verse_reference

    def to_graph_node(self, language: str = "en") -> dict:
        """Convert segment to graph node format."""
        title = self.title_ar if language == "ar" else self.title_en
        summary = self.summary_ar if language == "ar" else self.summary_en

        return {
            "id": self.id,
            "type": "segment",
            "label": title or self.verse_reference,
            "data": {
                "story_id": self.story_id,
                "surah": self.sura_no,
                "ayah_start": self.aya_start,
                "ayah_end": self.aya_end,
                "verse_reference": self.verse_reference,
                "narrative_role": self.narrative_role,
                "chronological_index": self.chronological_index,
                "semantic_tags": self.semantic_tags or [],
                "summary": summary,
                "is_entry_point": self.is_entry_point,
            }
        }


class StoryConnection(Base):
    """
    Connections between story segments - tracks how parts of a story
    relate to each other across different surahs.

    EDGE ONTOLOGY:
    ==============
    Edges represent semantic relationships between segments:

    1. TEMPORAL EDGES (form DAG - no cycles allowed):
       - chronological_next: Direct temporal succession
       - continuation: Same narrative continues

    2. CAUSAL EDGES (may form DAG):
       - cause_effect: A leads to B
       - consequence: B results from A

    3. THEMATIC EDGES (cycles allowed):
       - thematic_link, parallel, contrast, etc.

    EVIDENCE GROUNDING:
    ===================
    Every connection MUST have at least one evidence_chunk_id to maintain
    scholarly grounding. The justification field explains WHY this
    connection exists, grounded in tafsir.
    """
    __tablename__ = "story_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # =========================================================================
    # SOURCE AND TARGET
    # =========================================================================

    source_segment_id = Column(
        String(100), ForeignKey("story_segments.id"), nullable=False, index=True
    )
    target_segment_id = Column(
        String(100), ForeignKey("story_segments.id"), nullable=False, index=True
    )

    # =========================================================================
    # EDGE TYPE AND STRENGTH
    # =========================================================================

    # Edge type from EdgeType enum
    edge_type = Column(String(50), nullable=False)

    # Legacy field for backward compatibility
    connection_type = Column(String(50), nullable=True)

    # Strength/confidence of the connection (0.0-1.0)
    strength = Column(Float, default=1.0)

    # Is this edge part of the chronological DAG?
    is_chronological = Column(Boolean, default=False)

    # =========================================================================
    # JUSTIFICATION
    # =========================================================================

    # Human-readable explanation of WHY this connection exists
    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)

    # Scholarly justification grounded in tafsir
    justification_ar = Column(Text, nullable=True)
    justification_en = Column(Text, nullable=True)

    # =========================================================================
    # EVIDENCE
    # =========================================================================

    # CRITICAL: Evidence from tafseer - at least one required
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Structured evidence with source details
    # Format: [{"source_id": "...", "chunk_id": "...", "text": "..."}]
    evidence_details = Column(JSONB, nullable=True)

    # =========================================================================
    # THEMATIC LINKING
    # =========================================================================

    # Themes linking these segments
    shared_themes = Column(ARRAY(String), nullable=True)

    # For cross-story connections: which stories are linked
    cross_story = Column(Boolean, default=False)

    # =========================================================================
    # METADATA
    # =========================================================================

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_segment = relationship("StorySegment", foreign_keys=[source_segment_id])
    target_segment = relationship("StorySegment", foreign_keys=[target_segment_id])

    __table_args__ = (
        # Ensure at least one evidence chunk is provided
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_connection_has_evidence"
        ),
        Index("ix_connection_source", "source_segment_id"),
        Index("ix_connection_target", "target_segment_id"),
        Index("ix_connection_edge_type", "edge_type"),
        Index("ix_connection_chronological", "is_chronological"),
    )

    def __repr__(self):
        return f"<StoryConnection {self.source_segment_id} -> {self.target_segment_id} ({self.edge_type})>"

    def to_graph_edge(self, language: str = "en") -> dict:
        """Convert connection to graph edge format."""
        explanation = self.explanation_ar if language == "ar" else self.explanation_en

        return {
            "source": self.source_segment_id,
            "target": self.target_segment_id,
            "type": self.edge_type or self.connection_type,
            "label": explanation[:50] + "..." if explanation and len(explanation) > 50 else explanation,
            "data": {
                "strength": self.strength,
                "is_chronological": self.is_chronological,
                "shared_themes": self.shared_themes or [],
                "cross_story": self.cross_story,
                "evidence_count": len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0,
            }
        }


# =============================================================================
# CROSS-STORY CONNECTIONS (Inter-story semantic links)
# =============================================================================

class CrossStoryConnection(Base):
    """
    Connections between different stories (not segments).

    Similar to citation graphs in academic papers, this tracks
    thematic and narrative links between distinct Quranic stories.

    Examples:
    - Dhul-Qarnayn ↔ Musa (journey & knowledge themes)
    - Dhul-Qarnayn ↔ Talut/Dawud (righteous power)
    - Yusuf ↔ Musa (dreams, Egypt, leadership)
    """
    __tablename__ = "cross_story_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Stories being connected
    source_story_id = Column(String(50), ForeignKey("stories.id"), nullable=False, index=True)
    target_story_id = Column(String(50), ForeignKey("stories.id"), nullable=False, index=True)

    # Connection type
    connection_type = Column(String(50), nullable=False)  # shared_theme, shared_figure, prophetic_chain, etc.

    # Strength of connection (0.0-1.0)
    strength = Column(Float, default=0.5)

    # Label for the connection
    label_ar = Column(String(200), nullable=True)
    label_en = Column(String(200), nullable=True)  # e.g., "Shared theme: righteous power"

    # Explanation
    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)

    # Evidence grounding
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Shared themes/figures
    shared_themes = Column(ARRAY(String), nullable=True)
    shared_figures = Column(ARRAY(String), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_story = relationship("Story", foreign_keys=[source_story_id])
    target_story = relationship("Story", foreign_keys=[target_story_id])

    __table_args__ = (
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_cross_story_has_evidence"
        ),
        Index("ix_cross_story_source", "source_story_id"),
        Index("ix_cross_story_target", "target_story_id"),
    )

    def __repr__(self):
        return f"<CrossStoryConnection {self.source_story_id} ↔ {self.target_story_id}>"
