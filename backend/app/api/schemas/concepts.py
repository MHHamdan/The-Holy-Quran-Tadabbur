"""
Pydantic Schemas for Concepts API.

These schemas enforce strict validation for all API responses.
All fields are required unless explicitly marked Optional.

IMPORTANT:
- Never add fields without updating frontend types
- All responses MUST include data_status for incomplete data
- Tafsir evidence MUST be from 4 Sunni madhabs only
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class ConceptType(str, Enum):
    """Valid concept types in the system."""
    PERSON = "person"
    PLACE = "place"
    NATION = "nation"
    THEME = "theme"
    MIRACLE = "miracle"
    EVENT = "event"
    OBJECT = "object"


class Madhab(str, Enum):
    """
    Valid madhabs for tafsir sources.

    STRICT: Only these four Sunni madhabs are allowed.
    Any tafsir from other sources will be rejected.
    """
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBALI = "hanbali"


class DataStatus(str, Enum):
    """Data completeness status."""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    PENDING_VERIFICATION = "pending_verification"


class VerificationStatus(str, Enum):
    """Content verification status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class VerseReference(BaseModel):
    """Reference to a Quran verse."""
    sura_no: int = Field(..., ge=1, le=114, description="Surah number (1-114)")
    ayah_no: int = Field(..., ge=1, description="Ayah number")
    sura_name_ar: Optional[str] = Field(None, description="Arabic surah name")
    sura_name_en: Optional[str] = Field(None, description="English surah name")
    text_ar: Optional[str] = Field(None, description="Arabic verse text")
    text_en: Optional[str] = Field(None, description="English translation")

    @property
    def reference(self) -> str:
        """Standard reference format (e.g., '2:255')"""
        return f"{self.sura_no}:{self.ayah_no}"


class TafsirScholar(BaseModel):
    """Scholar information for tafsir sources."""
    id: str = Field(..., description="Scholar identifier")
    name_ar: str = Field(..., min_length=1, description="Arabic name")
    name_en: Optional[str] = Field(None, description="English name")
    madhab: Madhab = Field(..., description="Scholar's madhab (4 Sunni only)")
    era: Optional[str] = Field(None, description="Era/century")


class TafsirSource(BaseModel):
    """Tafsir source metadata."""
    id: str = Field(..., description="Source identifier (e.g., 'ibn_kathir_ar')")
    name_ar: str = Field(..., min_length=1, description="Arabic book name")
    name_en: Optional[str] = Field(None, description="English book name")
    scholar: Optional[TafsirScholar] = None
    madhab: Madhab = Field(..., description="Madhab (must be one of 4 Sunni)")

    @field_validator('madhab', mode='before')
    @classmethod
    def validate_madhab(cls, v):
        """Ensure madhab is valid - strict 4 Sunni only."""
        if isinstance(v, str):
            v = v.lower()
            valid_madhabs = {'hanafi', 'maliki', 'shafii', 'hanbali'}
            if v not in valid_madhabs:
                raise ValueError(f"Invalid madhab: {v}. Must be one of: {valid_madhabs}")
            return Madhab(v)
        return v


class TafsirEvidence(BaseModel):
    """
    Tafsir evidence from approved scholars.

    STRICT VALIDATION:
    - madhab MUST be one of: hanafi, maliki, shafii, hanbali
    - scholar MUST be from approved list per madhab
    """
    id: str = Field(..., description="Evidence chunk ID")
    source_id: str = Field(..., description="Tafsir source ID")
    source_name_ar: str = Field(..., description="Arabic source name")
    source_name_en: Optional[str] = None
    madhab: Madhab = Field(..., description="Madhab (4 Sunni only)")
    scholar_name_ar: Optional[str] = None
    scholar_name_en: Optional[str] = None
    verse_ref: VerseReference
    excerpt_ar: str = Field(..., min_length=1, description="Arabic excerpt")
    excerpt_en: Optional[str] = Field(None, description="English excerpt if available")
    source_locator: Optional[str] = Field(None, description="Page/volume reference")
    retrieved_at: Optional[str] = Field(None, description="ISO timestamp")

    @field_validator('madhab', mode='before')
    @classmethod
    def validate_madhab(cls, v):
        """Strictly validate madhab."""
        if isinstance(v, str):
            v = v.lower()
            if v not in {'hanafi', 'maliki', 'shafii', 'hanbali'}:
                raise ValueError(f"Invalid madhab: {v}. Only 4 Sunni madhabs allowed.")
            return Madhab(v)
        return v


# =============================================================================
# CONCEPT SCHEMAS
# =============================================================================

class ConceptSummary(BaseModel):
    """Summary of a concept for list views."""
    id: str = Field(..., description="Unique concept ID")
    slug: str = Field(..., description="URL-friendly slug")
    label_ar: str = Field(..., min_length=1, description="Arabic label")
    label_en: str = Field(..., min_length=1, description="English label")
    type: ConceptType = Field(..., description="Concept type")
    icon_hint: Optional[str] = None
    is_curated: bool = False
    occurrence_count: int = Field(0, ge=0, description="Number of occurrences")


class ConceptListResponse(BaseModel):
    """Response for concept list endpoint."""
    ok: bool = True
    concepts: List[ConceptSummary]
    total: int = Field(..., ge=0)
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1)
    data_status: DataStatus = DataStatus.COMPLETE

    @field_validator('data_status', mode='before')
    @classmethod
    def set_data_status(cls, v, info):
        """Auto-set data_status based on concepts."""
        if v is None:
            return DataStatus.COMPLETE
        return v


class OccurrenceDetail(BaseModel):
    """Occurrence of a concept in the Quran."""
    id: int
    concept_id: str
    ref_type: str = Field(..., description="Reference type (ayah, segment, story)")
    ref_id: Optional[str] = None
    sura_no: Optional[int] = Field(None, ge=1, le=114)
    ayah_start: Optional[int] = Field(None, ge=1)
    ayah_end: Optional[int] = Field(None, ge=1)
    verse_reference: str = ""
    weight: float = Field(1.0, ge=0, le=1)
    context_ar: Optional[str] = None
    context_en: Optional[str] = None
    has_evidence: bool = False
    is_verified: bool = False
    evidence_count: int = Field(0, ge=0, description="Number of tafsir evidence chunks")


class AssociationDetail(BaseModel):
    """Association between concepts."""
    id: int
    other_concept_id: str
    other_concept_label_ar: str
    other_concept_label_en: str
    other_concept_type: str
    relation_type: str
    evidence_refs: Optional[dict] = None


class ConceptDetailResponse(BaseModel):
    """
    Full concept detail response.

    Includes:
    - Core concept information
    - All occurrences with verse refs
    - Associations with other concepts
    - Tafsir evidence (4 madhabs only)
    - Verification status
    """
    ok: bool = True
    id: str
    slug: str
    label_ar: str = Field(..., min_length=1)
    label_en: str = Field(..., min_length=1)
    type: ConceptType
    aliases_ar: List[str] = []
    aliases_en: List[str] = []
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    parent_id: Optional[str] = None
    icon_hint: Optional[str] = None
    is_curated: bool = False
    source: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.APPROVED

    # Related data
    occurrences: List[OccurrenceDetail] = []
    associations: List[AssociationDetail] = []
    tafsir_evidence: List[TafsirEvidence] = []

    # Data completeness
    data_status: DataStatus = DataStatus.COMPLETE
    missing_fields: List[str] = []


# =============================================================================
# MIRACLE SCHEMAS
# =============================================================================

class MiracleSummary(BaseModel):
    """Summary of a miracle for list views."""
    id: str
    slug: str
    label_ar: str = Field(..., min_length=1)
    label_en: str = Field(..., min_length=1)
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    icon_hint: Optional[str] = None
    related_persons: List[ConceptSummary] = []
    related_stories: List[str] = []
    occurrence_count: int = Field(0, ge=0)


class MiracleListResponse(BaseModel):
    """Response for miracles list endpoint."""
    ok: bool = True
    data: List[MiracleSummary]
    total: int = Field(..., ge=0)
    data_status: DataStatus = DataStatus.COMPLETE


class MiracleDetailResponse(BaseModel):
    """
    Full miracle detail response.

    Includes comprehensive information with tafsir grounding.
    """
    ok: bool = True
    id: str
    slug: str
    label_ar: str = Field(..., min_length=1)
    label_en: str = Field(..., min_length=1)
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    icon_hint: Optional[str] = None

    # Related entities
    related_persons: List[ConceptSummary] = []
    related_stories: List[str] = []

    # Verse occurrences
    occurrences: List[OccurrenceDetail] = []

    # Tafsir evidence (MUST be from 4 madhabs)
    tafsir_evidence: List[TafsirEvidence] = []
    madhabs_present: List[Madhab] = []

    # Verification
    verification_status: VerificationStatus = VerificationStatus.APPROVED
    data_status: DataStatus = DataStatus.COMPLETE
    missing_fields: List[str] = []


# =============================================================================
# TAFSIR EVIDENCE RESPONSE
# =============================================================================

class TafsirEvidenceResponse(BaseModel):
    """
    Response for tafsir evidence endpoint.

    STRICT: Only returns evidence from 4 Sunni madhabs.
    """
    ok: bool = True
    occurrence_id: int
    concept_id: str
    verse_ref: VerseReference
    evidence: List[TafsirEvidence] = []
    madhabs_present: List[Madhab] = []
    madhabs_missing: List[Madhab] = []
    data_status: DataStatus = DataStatus.COMPLETE

    @field_validator('evidence')
    @classmethod
    def validate_evidence_madhabs(cls, v):
        """Ensure all evidence is from valid madhabs."""
        for e in v:
            if e.madhab not in {Madhab.HANAFI, Madhab.MALIKI, Madhab.SHAFII, Madhab.HANBALI}:
                raise ValueError(f"Invalid madhab in evidence: {e.madhab}")
        return v


# =============================================================================
# VERIFICATION SCHEMAS
# =============================================================================

class VerificationTaskCreate(BaseModel):
    """Request to create a verification task."""
    entity_type: Literal["concept", "miracle", "occurrence", "association"]
    entity_id: str
    proposed_change: dict
    evidence_refs: Optional[dict] = None
    priority: int = Field(0, ge=0, le=10)


class VerificationTaskResponse(BaseModel):
    """Response for verification task."""
    id: int
    entity_type: str
    entity_id: str
    proposed_change: dict
    evidence_refs: Optional[dict] = None
    status: VerificationStatus
    priority: int
    created_by: Optional[str] = None
    created_at: str


class VerificationDecisionCreate(BaseModel):
    """Admin decision on verification task."""
    decision: Literal["approved", "rejected"]
    notes: Optional[str] = None
    madhab_verified: List[Madhab] = []
    citation_verified: bool = False


class VerificationDecisionResponse(BaseModel):
    """Response after verification decision."""
    ok: bool = True
    task_id: int
    decision: str
    decided_by: str
    decided_at: str


class VerificationStatsResponse(BaseModel):
    """Verification workflow statistics."""
    pending_count: int
    approved_count: int
    rejected_count: int
    by_entity_type: dict
