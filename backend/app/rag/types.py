"""
Type definitions for RAG pipeline.

LANGUAGE POLICY:
================
The RAG pipeline supports two categories of languages:

1. RAG REASONING LANGUAGES (Arabic & English only):
   - These languages are used for semantic search, retrieval, and LLM reasoning
   - Tafseer content exists in Arabic (ar) and English (en)
   - All RAG operations (embedding, retrieval, synthesis) use these languages
   - Supported values: "ar", "en"

2. DISPLAY-ONLY LANGUAGES (other languages):
   - Languages like Urdu, Indonesian, Turkish, etc. are DISPLAY-ONLY
   - These come from the translations table, NOT from tafseer RAG
   - No semantic search or RAG reasoning is performed in these languages
   - Users can request display translations, but answers are still grounded
     in Arabic/English tafseer sources

IMPORTANT: Never use display-only languages for RAG retrieval or reasoning.
"""
from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass, field


# Supported languages for RAG reasoning (tafseer retrieval and synthesis)
RAG_SUPPORTED_LANGUAGES = {"ar", "en"}

# Display-only languages (translations table, no RAG reasoning)
DISPLAY_ONLY_LANGUAGES = {"ur", "id", "tr", "bn", "ms", "fa"}  # Can be extended


class QueryIntent(str, Enum):
    """Types of queries the RAG can handle."""
    VERSE_MEANING = "verse_meaning"
    STORY_EXPLORATION = "story_exploration"
    THEME_SEARCH = "theme_search"
    COMPARATIVE = "comparative"
    LINGUISTIC = "linguistic"
    RULING = "ruling"  # Fiqh-related (informational only)
    UNKNOWN = "unknown"


@dataclass
class RetrievedChunk:
    """A retrieved tafseer chunk with metadata."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str
    verse_reference: str
    sura_no: int
    aya_start: int
    aya_end: int
    content: str  # Content in requested language
    content_ar: Optional[str] = None
    content_en: Optional[str] = None
    relevance_score: float = 0.0
    scholarly_consensus: Optional[str] = None
    is_primary_source: bool = True
    source_reliability: float = 0.8
    methodology: Optional[str] = None  # bil_mathur, bil_rai, etc.


@dataclass
class Citation:
    """Citation in a grounded response."""
    chunk_id: str
    source_id: str
    source_name: str
    source_name_ar: str  # Arabic source name for display
    verse_reference: str
    excerpt: str
    relevance_score: float
    # Phase-2 enrichment fields
    reliability_level: Optional[str] = None   # canonical|verified|supporting|experimental
    author: Optional[str] = None              # Human scholar name
    surah_number: Optional[int] = None
    ayah_number: Optional[int] = None
    quoted_evidence: Optional[str] = None     # Verbatim tafsir excerpt used
    explanation: Optional[str] = None         # Why this citation supports the answer


@dataclass
class RelatedVerse:
    """A Quranic verse related to the query - displayed prominently before tafsir."""
    sura_no: int
    aya_no: int
    verse_reference: str  # e.g., "2:255"
    text_ar: str  # Arabic text of the verse
    text_en: str  # English translation
    sura_name_ar: Optional[str] = None  # e.g., "البقرة"
    sura_name_en: Optional[str] = None  # e.g., "Al-Baqarah"
    topic: Optional[str] = None  # Semantic topic from concept occurrences
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "sura_no": self.sura_no,
            "aya_no": self.aya_no,
            "verse_reference": self.verse_reference,
            "text_ar": self.text_ar,
            "text_en": self.text_en,
            "sura_name_ar": self.sura_name_ar,
            "sura_name_en": self.sura_name_en,
            "topic": self.topic,
            "relevance_score": self.relevance_score,
        }


@dataclass
class TafsirExplanation:
    """A tafsir explanation from a specific source."""
    source_id: str
    source_name: str  # English name
    source_name_ar: str  # Arabic name
    author_name: Optional[str] = None  # Author name
    author_name_ar: Optional[str] = None  # Arabic author name
    methodology: Optional[str] = None  # bil_mathur, bil_ray, linguistic, etc.
    explanation: str = ""  # The tafsir text
    verse_reference: str = ""  # Which verse this explains
    era: str = "classical"  # "classical" or "modern"
    reliability_score: float = 0.8

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_name_ar": self.source_name_ar,
            "author_name": self.author_name,
            "author_name_ar": self.author_name_ar,
            "methodology": self.methodology,
            "explanation": self.explanation,
            "verse_reference": self.verse_reference,
            "era": self.era,
            "reliability_score": self.reliability_score,
        }


@dataclass
class GroundedResponse:
    """Response from RAG pipeline with mandatory citations."""
    answer: str
    citations: List[Citation]
    confidence: float
    scholarly_consensus: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    related_queries: List[str] = field(default_factory=list)
    intent: str = "unknown"
    processing_time_ms: int = 0
    confidence_level: str = "medium"  # high, medium, low, insufficient
    confidence_message: Optional[str] = None
    query_expansion: Optional[List[str]] = None
    degradation_reasons: List[str] = field(default_factory=list)
    # Phase-2: explicit status and answer language
    status: str = "answered"          # answered|no_verified_source|needs_clarification|error
    answer_language: str = "en"       # ar|en

    # Evidence density metadata (for transparency)
    # These expose HOW MUCH evidence backs the response without exposing raw IDs
    evidence_chunk_count: int = 0   # Number of distinct chunks used
    evidence_source_count: int = 0  # Number of distinct tafseer sources used

    # Raw evidence chunks for transparency panel
    evidence: List['RetrievedChunk'] = field(default_factory=list)

    # === NEW: Enhanced response fields for chat experience ===
    # Session ID for conversation continuity
    session_id: Optional[str] = None

    # Related Quranic verses - displayed prominently before tafsir
    related_verses: List['RelatedVerse'] = field(default_factory=list)

    # Tafsir explanations grouped by source for accordion display
    tafsir_by_source: Dict[str, List['TafsirExplanation']] = field(default_factory=dict)

    # AI-generated follow-up question suggestions
    follow_up_suggestions: List[str] = field(default_factory=list)

    # API version for client compatibility checking
    api_version: str = "1.0.0"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "answer": self.answer,
            "status": self.status,
            "answer_language": self.answer_language,
            "citations": [
                {
                    "chunk_id": c.chunk_id,
                    "source_id": c.source_id,
                    "source_name": c.source_name,
                    "source_name_ar": c.source_name_ar,
                    "verse_reference": c.verse_reference,
                    "excerpt": c.excerpt,
                    "relevance_score": c.relevance_score,
                    "reliability_level": c.reliability_level,
                    "author": c.author,
                    "surah_number": c.surah_number,
                    "ayah_number": c.ayah_number,
                    "quoted_evidence": c.quoted_evidence,
                    "explanation": c.explanation,
                }
                for c in self.citations
            ],
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_message": self.confidence_message,
            "scholarly_consensus": self.scholarly_consensus,
            "warnings": self.warnings,
            "related_queries": self.related_queries,
            "intent": self.intent,
            "processing_time_ms": self.processing_time_ms,
            "query_expansion": self.query_expansion,
            "degradation_reasons": self.degradation_reasons,
            # Evidence density (read-only transparency)
            "evidence_density": {
                "chunk_count": self.evidence_chunk_count,
                "source_count": self.evidence_source_count,
            },
            # Raw evidence for transparency panel
            "evidence": [
                {
                    "chunk_id": e.chunk_id,
                    "source_id": e.source_id,
                    "source_name": e.source_name,
                    "source_name_ar": e.source_name_ar,
                    "verse_reference": e.verse_reference,
                    "sura_no": e.sura_no,
                    "aya_start": e.aya_start,
                    "aya_end": e.aya_end,
                    "content": e.content,
                    "content_ar": e.content_ar,
                    "content_en": e.content_en,
                    "relevance_score": e.relevance_score,
                    "methodology": e.methodology,
                }
                for e in self.evidence
            ],
            # === NEW: Chat experience fields ===
            # Session ID for conversation continuity
            "session_id": self.session_id,
            # Related Quranic verses - displayed first
            "related_verses": [v.to_dict() for v in self.related_verses],
            # Tafsir explanations grouped by source
            "tafsir_by_source": {
                source_id: [t.to_dict() for t in explanations]
                for source_id, explanations in self.tafsir_by_source.items()
            },
            # Follow-up question suggestions
            "follow_up_suggestions": self.follow_up_suggestions,
            # API version for contract compatibility
            "api_version": self.api_version,
        }


@dataclass
class ValidationResult:
    """Result of citation validation."""
    is_valid: bool
    valid_citations: List[str]
    invalid_citations: List[str]
    missing_citations: List[str]
    coverage_score: float  # 0.0-1.0


# Safe refusal responses
SAFE_REFUSAL_INSUFFICIENT = (
    "This requires further scholarly consultation based on available sources. "
    "The retrieved evidence is insufficient to provide a complete answer."
)

SAFE_REFUSAL_NO_SOURCES = (
    "I could not find relevant sources to answer this question. "
    "Please consult qualified scholars for guidance."
)

# Phase-2: language-specific no_verified_source text (verbatim — do not modify without review)
SAFE_REFUSAL_NO_SOURCES_EN = "No verified source available for this answer."
SAFE_REFUSAL_NO_SOURCES_AR = "لا يوجد مصدر موثوق متاح لهذه الإجابة."

# Phase-2: needs_clarification refusal text
NEEDS_CLARIFICATION_EN = (
    "Your question needs more context. "
    "Please specify a verse reference, surah name, or topic so I can find relevant sources."
)
NEEDS_CLARIFICATION_AR = (
    "سؤالك يحتاج إلى مزيد من التوضيح. "
    "يرجى تحديد رقم الآية أو اسم السورة أو الموضوع حتى أتمكن من البحث في المصادر المناسبة."
)

SAFE_REFUSAL_FIQH = (
    "Note: This information is provided for educational purposes only and "
    "should not be taken as a religious ruling (fatwa). Please consult "
    "qualified scholars for personal religious guidance."
)

# Reliability level mapping from source_reliability float → string label
def reliability_float_to_level(score: float) -> str:
    """Map a 0–1 reliability score to a ReliabilityLevel string."""
    if score >= 0.9:
        return "canonical"
    if score >= 0.7:
        return "verified"
    if score >= 0.5:
        return "supporting"
    return "experimental"
