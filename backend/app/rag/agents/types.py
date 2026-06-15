"""
Typed handoff contracts for the Tadabbur-AI agentic RAG pipeline.

Every agent produces one of these dataclasses as output; downstream agents
receive them as input. Provenance (source_id, review_status, chunk_id) is
preserved end-to-end — no agent may drop it.

Design rules:
- All fields are immutable once created (use frozen=False only for incremental
  enrichment inside the orchestrator, never across agent boundaries).
- `safe_refusal_required` on RetrieverOutput or ValidationOutput short-circuits
  the pipeline immediately to the Safety agent (no LLM call).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ─── Shared enumerations ─────────────────────────────────────────────────────

class ReviewStatus(str, Enum):
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    EXPERIMENTAL = "experimental"


class DisagreementType(str, Enum):
    LEXICAL = "lexical"
    GRAMMATICAL = "grammatical"
    JURISPRUDENTIAL = "jurisprudential"
    NARRATIVE = "narrative"
    THEOLOGICAL = "theological"
    VARIANT_READING = "variant_reading"


class ConsensusLevel(str, Enum):
    STRONG = "strong_consensus"
    PARTIAL = "partial_consensus"
    SIGNIFICANT = "significant_disagreement"
    SINGLE_SOURCE = "single_source_only"


class ValidationStatus(str, Enum):
    VALID = "valid"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


# ─── Agent 1: Retriever Agent output ─────────────────────────────────────────

@dataclass
class RetrievedItem:
    """One evidence item returned by the Retriever Agent."""
    item_id: str
    item_type: str              # tafsir_chunk | story_segment | concept_verse
    source_id: str
    text: str
    score: float
    review_status: ReviewStatus
    sura_no: int = 0
    aya_start: int = 0
    aya_end: int = 0
    source_name: str = ""
    source_name_ar: str = ""
    methodology: Optional[str] = None
    evidence_chain_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "source_id": self.source_id,
            "text": self.text,
            "score": self.score,
            "review_status": self.review_status.value,
            "sura_no": self.sura_no,
            "aya_start": self.aya_start,
            "aya_end": self.aya_end,
            "source_name": self.source_name,
            "source_name_ar": self.source_name_ar,
            "methodology": self.methodology,
        }


@dataclass
class RetrieverOutput:
    """Output of Agent 1: Retriever Agent."""
    retrieved_items: List[RetrievedItem]
    total_found: int
    hop: int = 1                    # which retrieval hop produced this
    safe_refusal_required: bool = False
    retriever_metrics: dict = field(default_factory=dict)

    @property
    def approved_items(self) -> List[RetrievedItem]:
        return [i for i in self.retrieved_items if i.review_status == ReviewStatus.APPROVED]

    @property
    def has_sufficient_evidence(self) -> bool:
        return len(self.approved_items) >= 2


# ─── Agent 2: Validation Agent output ────────────────────────────────────────

@dataclass
class ValidatedItem:
    """One validated evidence item from Agent 2."""
    item_id: str
    validation_status: ValidationStatus
    citation_present: bool
    source_id_verified: bool
    text_match_score: float
    original_item: RetrievedItem
    rejection_reason: Optional[str] = None


@dataclass
class ValidationOutput:
    """Output of Agent 2: Validation Agent."""
    validated_items: List[ValidatedItem]
    overall_status: str             # pass | partial | fail
    evidence_sufficiency_score: float
    safe_refusal_required: bool = False

    @property
    def valid_items(self) -> List[ValidatedItem]:
        return [v for v in self.validated_items if v.validation_status == ValidationStatus.VALID]

    @property
    def valid_retrieved_items(self) -> List[RetrievedItem]:
        return [v.original_item for v in self.valid_items]


# ─── Agent 3: Consensus / Disagreement Agent output ──────────────────────────

@dataclass
class ScholarlyPosition:
    """One scholarly position in a disagreement."""
    source_id: str
    source_name: str
    claim_summary: str


@dataclass
class DisagreementObject:
    """
    Structured representation of scholarly disagreement.

    The adjudication field is always NOT_ADJUDICATED — the platform
    presents both views without endorsing either.
    """
    disagreement_type: DisagreementType
    position_a: ScholarlyPosition
    position_b: ScholarlyPosition
    adjudication: str = "NOT_ADJUDICATED — platform presents both views"
    resolution_status: str = "unresolved"  # unresolved | school_specific | academic_contested

    def to_dict(self) -> dict:
        return {
            "disagreement_type": self.disagreement_type.value,
            "position_a": {
                "source_id": self.position_a.source_id,
                "source_name": self.position_a.source_name,
                "claim_summary": self.position_a.claim_summary,
            },
            "position_b": {
                "source_id": self.position_b.source_id,
                "source_name": self.position_b.source_name,
                "claim_summary": self.position_b.claim_summary,
            },
            "adjudication": self.adjudication,
            "resolution_status": self.resolution_status,
        }


@dataclass
class ConsensusOutput:
    """Output of Agent 3: Consensus / Disagreement Agent."""
    consensus_level: ConsensusLevel
    majority_position: Optional[ScholarlyPosition]
    disagreements: List[DisagreementObject] = field(default_factory=list)
    display_warning: Optional[str] = None
    sources_analysed: int = 0

    @property
    def has_disagreements(self) -> bool:
        return len(self.disagreements) > 0

    def to_dict(self) -> dict:
        return {
            "consensus_level": self.consensus_level.value,
            "majority_position": {
                "source_id": self.majority_position.source_id,
                "source_name": self.majority_position.source_name,
                "claim_summary": self.majority_position.claim_summary,
            } if self.majority_position else None,
            "disagreements": [d.to_dict() for d in self.disagreements],
            "display_warning": self.display_warning,
            "sources_analysed": self.sources_analysed,
        }


# ─── Agentic pipeline result ──────────────────────────────────────────────────

@dataclass
class AgenticPipelineResult:
    """
    Final typed result of the full agentic pipeline.

    Wraps the existing GroundedResponse with additional agentic metadata:
    - which hop produced the final evidence
    - consensus analysis
    - structured disagreements
    """
    # Core response (from existing pipeline)
    answer: str
    citations: list
    confidence: float
    status: str
    answer_language: str

    # Agentic metadata
    hops_used: int = 1
    consensus: Optional[ConsensusOutput] = None
    validation_output: Optional[ValidationOutput] = None

    # Pass-through from GroundedResponse
    answer_mode: str = "tafsir_summary"
    disagreement_warning: Optional[str] = None
    ai_summary_disclaimer: bool = True
    related_verses: list = field(default_factory=list)
    tafsir_by_source: dict = field(default_factory=dict)
    follow_up_suggestions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    confidence_level: str = "medium"
    confidence_message: Optional[str] = None
    scholarly_consensus: Optional[str] = None
    evidence: list = field(default_factory=list)
    session_id: Optional[str] = None
    processing_time_ms: int = 0
    api_version: str = "2.0.0"

    def to_dict(self) -> dict:
        d = {
            "answer": self.answer,
            "status": self.status,
            "answer_language": self.answer_language,
            "citations": self.citations,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_message": self.confidence_message,
            "scholarly_consensus": self.scholarly_consensus,
            "warnings": self.warnings,
            "answer_mode": self.answer_mode,
            "disagreement_warning": self.disagreement_warning,
            "ai_summary_disclaimer": self.ai_summary_disclaimer,
            "related_verses": self.related_verses,
            "tafsir_by_source": self.tafsir_by_source,
            "follow_up_suggestions": self.follow_up_suggestions,
            "evidence": self.evidence,
            "session_id": self.session_id,
            "processing_time_ms": self.processing_time_ms,
            "api_version": self.api_version,
            # Agentic extensions
            "agentic": {
                "hops_used": self.hops_used,
                "consensus": self.consensus.to_dict() if self.consensus else None,
                "evidence_validated": (
                    len(self.validation_output.valid_items)
                    if self.validation_output else None
                ),
            },
        }
        return d
