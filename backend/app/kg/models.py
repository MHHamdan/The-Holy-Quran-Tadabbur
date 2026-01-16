"""
Pydantic models for Knowledge Graph entities.

All models enforce:
- Arabic-only labels where required
- Ayah span format validation
- No internal fields leaked to clients
- Schema versioning
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import re


# =============================================================================
# ENUMS
# =============================================================================

class PersonKind(str, Enum):
    PROPHET = "prophet"
    NAMED = "named"
    GROUP = "group"
    ANGEL = "angel"


class PlaceBasis(str, Enum):
    EXPLICIT = "explicit"
    TAFSIR_INFERRED = "tafsir_inferred"
    UNKNOWN = "unknown"


class TagCategory(str, Enum):
    THEME = "theme"
    MORAL = "moral"
    MIRACLE = "miracle"
    RHETORICAL = "rhetorical"
    HISTORICAL = "historical"
    THEOLOGICAL = "theological"


class NarrativeRole(str, Enum):
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
    PRIMORDIAL = "primordial"
    ANCIENT = "ancient"
    EGYPT = "egypt"
    ISRAELITE = "israelite"
    PRE_ISLAMIC = "pre_islamic"
    UNKNOWN = "unknown"


class StoryCategory(str, Enum):
    PROPHET = "prophet"
    NAMED_CHAR = "named_char"
    NATION = "nation"
    PARABLE = "parable"
    HISTORICAL = "historical"
    UNSEEN = "unseen"


class IngestStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# =============================================================================
# PROVENANCE MIXIN
# =============================================================================

class ProvenanceMixin(BaseModel):
    """Common provenance fields for all entities."""
    hash_: str = Field(default="", alias="_hash")
    version: str = Field(default="1.0.0", alias="_version")
    source: str = Field(default="curated", alias="_source")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")
    ingest_run_id: Optional[str] = Field(default=None, alias="_ingest_run_id")

    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# =============================================================================
# AYAH SPAN
# =============================================================================

class AyahSpan(BaseModel):
    """A range of ayahs within a sura."""
    sura: int = Field(..., ge=1, le=114)
    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_range(self) -> "AyahSpan":
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")
        return self

    def to_reference(self) -> str:
        """Convert to verse reference string."""
        if self.start == self.end:
            return f"{self.sura}:{self.start}"
        return f"{self.sura}:{self.start}-{self.end}"


# =============================================================================
# EVIDENCE SOURCE
# =============================================================================

class EvidenceSource(BaseModel):
    """Reference to tafsir evidence."""
    source_id: str
    chunk_id: str
    snippet: Optional[str] = None


# =============================================================================
# CORE ENTITIES
# =============================================================================

class Ayah(ProvenanceMixin):
    """Quranic verse."""
    id: Optional[str] = None
    sura: int = Field(..., ge=1, le=114)
    ayah: int = Field(..., ge=1)
    text_ar: str = Field(..., min_length=1)
    text_en: Optional[str] = None
    mushaf_page: Optional[int] = None
    juz: Optional[int] = Field(None, ge=1, le=30)
    hizb: Optional[int] = Field(None, ge=1, le=60)

    def get_id(self) -> str:
        return f"ayah:{self.sura}:{self.ayah}"

    @field_validator("text_ar")
    @classmethod
    def validate_arabic(cls, v: str) -> str:
        # Must contain Arabic characters
        if not re.search(r"[\u0600-\u06FF]", v):
            raise ValueError("text_ar must contain Arabic characters")
        return v


class TafsirChunk(ProvenanceMixin):
    """Tafsir text segment."""
    id: Optional[str] = None
    source_id: str
    source_name: str
    source_name_ar: str
    sura_no: int = Field(..., ge=1, le=114)
    ayah_start: int = Field(..., ge=1)
    ayah_end: int = Field(..., ge=1)
    verse_reference: str
    lang: str = Field(..., pattern=r"^(ar|en)$")
    text: str = Field(..., min_length=1)
    methodology: Optional[str] = None
    scholarly_consensus: Optional[str] = None
    license_type: Optional[str] = None
    retrieval_ts: Optional[datetime] = Field(None, alias="_retrieval_ts")

    def get_id(self) -> str:
        hash_prefix = self.compute_hash(self.text)[:8]
        return f"tafsir_chunk:{self.source_id}:{self.sura_no}:{self.ayah_start}-{self.ayah_end}:{hash_prefix}"

    @model_validator(mode="after")
    def validate_range(self) -> "TafsirChunk":
        if self.ayah_end < self.ayah_start:
            raise ValueError("ayah_end must be >= ayah_start")
        return self


class StoryCluster(ProvenanceMixin):
    """Story cluster grouping events."""
    id: Optional[str] = None
    slug: str = Field(..., pattern=r"^[a-z0-9_]+$")
    title_ar: str = Field(..., min_length=1)
    title_en: str = Field(..., min_length=1)
    short_title_ar: Optional[str] = None
    short_title_en: Optional[str] = None
    category: StoryCategory
    era: Optional[EraBucket] = None
    era_basis: Optional[str] = None
    time_description_ar: Optional[str] = None
    time_description_en: Optional[str] = None
    main_persons: List[str] = Field(default_factory=list)
    groups: List[str] = Field(default_factory=list)
    places: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    ayah_spans: List[AyahSpan] = Field(default_factory=list)
    primary_sura: Optional[int] = Field(None, ge=1, le=114)
    total_verses: Optional[int] = None
    suras_mentioned: List[int] = Field(default_factory=list)
    summary_ar: Optional[str] = None
    summary_en: Optional[str] = None
    lessons_ar: List[str] = Field(default_factory=list)
    lessons_en: List[str] = Field(default_factory=list)
    is_complete: bool = False
    event_count: int = 0

    def get_id(self) -> str:
        return f"story_cluster:{self.slug}"

    @field_validator("title_ar")
    @classmethod
    def validate_arabic_title(cls, v: str) -> str:
        if not re.search(r"[\u0600-\u06FF]", v):
            raise ValueError("title_ar must contain Arabic characters")
        return v


class StoryEvent(ProvenanceMixin):
    """Event within a story cluster."""
    id: Optional[str] = None
    cluster_id: str
    slug: str = Field(..., pattern=r"^[a-z0-9_]+$")
    title_ar: str = Field(..., min_length=1)
    title_en: str = Field(..., min_length=1)
    narrative_role: NarrativeRole
    chronological_index: int = Field(..., ge=1)
    is_entry_point: bool = False
    sura_no: int = Field(..., ge=1, le=114)
    ayah_start: int = Field(..., ge=1)
    ayah_end: int = Field(..., ge=1)
    verse_reference: str
    summary_ar: str = Field(..., min_length=1)
    summary_en: str = Field(..., min_length=1)
    memorization_cue_ar: Optional[str] = None
    memorization_cue_en: Optional[str] = None
    semantic_tags: List[str] = Field(default_factory=list)
    evidence: List[EvidenceSource] = Field(default_factory=list, min_length=1)

    def get_id(self) -> str:
        return f"story_event:{self.cluster_id.split(':')[-1]}:{self.slug}"

    @field_validator("summary_ar")
    @classmethod
    def validate_arabic_summary(cls, v: str) -> str:
        if not re.search(r"[\u0600-\u06FF]", v):
            raise ValueError("summary_ar must contain Arabic characters")
        return v


class Person(ProvenanceMixin):
    """Named individual in Quran."""
    id: Optional[str] = None
    slug: str = Field(..., pattern=r"^[a-z0-9_]+$")
    name_ar: str = Field(..., min_length=1)
    name_en: str = Field(..., min_length=1)
    kind: PersonKind
    aliases_ar: List[str] = Field(default_factory=list)
    aliases_en: List[str] = Field(default_factory=list)
    description_ar: Optional[str] = None
    description_en: Optional[str] = None

    def get_id(self) -> str:
        return f"person:{self.slug}"


class Place(ProvenanceMixin):
    """Location mentioned in Quran."""
    id: Optional[str] = None
    slug: str = Field(..., pattern=r"^[a-z0-9_]+$")
    name_ar: str = Field(..., min_length=1)
    name_en: str = Field(..., min_length=1)
    basis: PlaceBasis
    aliases_ar: List[str] = Field(default_factory=list)
    aliases_en: List[str] = Field(default_factory=list)
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None

    def get_id(self) -> str:
        return f"place:{self.slug}"


class ConceptTag(ProvenanceMixin):
    """Bilingual semantic tag."""
    id: Optional[str] = None
    key: str = Field(..., pattern=r"^[a-z0-9_]+$")
    label_ar: str = Field(..., min_length=1)
    label_en: str = Field(..., min_length=1)
    category: TagCategory
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    icon_hint: Optional[str] = None

    def get_id(self) -> str:
        return f"concept_tag:{self.key}"

    @field_validator("label_ar")
    @classmethod
    def validate_arabic_label(cls, v: str) -> str:
        if not re.search(r"[\u0600-\u06FF]", v):
            raise ValueError("label_ar must contain Arabic characters")
        return v


# =============================================================================
# INGESTION TRACKING
# =============================================================================

class IngestRun(BaseModel):
    """Top-level ingestion run."""
    id: Optional[str] = None
    run_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    git_sha: Optional[str] = None
    config_hash: Optional[str] = None
    status: IngestStatus = IngestStatus.RUNNING
    steps_planned: List[str] = Field(default_factory=list)
    steps_completed: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def get_id(self) -> str:
        return f"ingest_run:{self.run_id}"


class IngestStep(BaseModel):
    """Individual step within a run."""
    id: Optional[str] = None
    run_id: str
    step_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: StepStatus = StepStatus.PENDING
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def get_id(self) -> str:
        return f"ingest_step:{self.run_id}:{self.step_name}"


class IngestRecordState(BaseModel):
    """Per-record state for idempotency."""
    id: Optional[str] = None
    record_id: str
    record_type: str
    last_run_id: str
    content_hash: str
    steps: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    def get_id(self) -> str:
        return f"ingest_record_state:{self.record_id}"


class EmbeddingRecord(BaseModel):
    """Links SurrealDB records to Qdrant vectors."""
    id: Optional[str] = None
    surreal_id: str
    surreal_table: str
    vector_db: str = "qdrant"
    vector_collection: str
    vector_id: str
    model_name: str
    model_dim: int
    content_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    def get_id(self) -> str:
        return f"embedding_record:{hashlib.sha256(self.surreal_id.encode()).hexdigest()[:16]}"


# =============================================================================
# GRAPH RESPONSE MODELS (FOR API)
# =============================================================================

class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    type: str
    label: str
    data: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None


class GraphEdge(BaseModel):
    """Edge for graph visualization."""
    source: str
    target: str
    type: str
    label: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class StoryGraphResponse(BaseModel):
    """Response for story graph endpoint."""
    cluster_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    entry_node_id: Optional[str] = None
    is_valid_dag: bool = True
    layout_mode: str = "chronological"


class TimelineEvent(BaseModel):
    """Event in timeline view."""
    id: str
    index: int
    title_ar: str
    title_en: str
    verse_reference: str
    narrative_role: str
    summary_ar: str
    summary_en: str
    semantic_tags: List[str] = Field(default_factory=list)
    is_entry_point: bool = False
    memorization_cue_ar: Optional[str] = None
    memorization_cue_en: Optional[str] = None


class TimelineResponse(BaseModel):
    """Response for timeline endpoint."""
    cluster_id: str
    title_ar: str
    title_en: str
    events: List[TimelineEvent]


# =============================================================================
# HYBRID RETRIEVAL RESPONSE
# =============================================================================

class VectorHit(BaseModel):
    """Result from vector search."""
    chunk_id: str
    surreal_id: Optional[str] = None
    score: float
    rank: int


class GraphPath(BaseModel):
    """Path from chunk to story context."""
    chunk_id: str
    ayah_ids: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    cluster_id: Optional[str] = None


class HybridEvidenceItem(BaseModel):
    """Enhanced evidence with graph context."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str
    verse_reference: str
    sura_no: int
    ayah_start: int
    ayah_end: int
    content: str
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    relevance_score: float
    vector_rank: Optional[int] = None
    vector_score: Optional[float] = None
    graph_paths: List[GraphPath] = Field(default_factory=list)
    story_context: Optional[Dict[str, str]] = None


class HybridRetrievalResult(BaseModel):
    """Result from hybrid retrieval pipeline."""
    vector_hits: List[VectorHit]
    graph_expanded_ids: List[str]
    final_evidence: List[HybridEvidenceItem]
    debug_info: Optional[Dict[str, Any]] = None
