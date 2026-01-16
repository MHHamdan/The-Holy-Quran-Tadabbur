"""
API Schemas Package

Pydantic models for request/response validation.
"""
from .concepts import (
    # Enums
    ConceptType,
    Madhab,
    DataStatus,
    VerificationStatus,

    # Base schemas
    VerseReference,
    TafsirScholar,
    TafsirSource,
    TafsirEvidence,

    # Concept schemas
    ConceptSummary,
    ConceptListResponse,
    OccurrenceDetail,
    AssociationDetail,
    ConceptDetailResponse,

    # Miracle schemas
    MiracleSummary,
    MiracleListResponse,
    MiracleDetailResponse,

    # Tafsir schemas
    TafsirEvidenceResponse,

    # Verification schemas
    VerificationTaskCreate,
    VerificationTaskResponse,
    VerificationDecisionCreate,
    VerificationDecisionResponse,
    VerificationStatsResponse,
)

__all__ = [
    # Enums
    'ConceptType',
    'Madhab',
    'DataStatus',
    'VerificationStatus',

    # Base schemas
    'VerseReference',
    'TafsirScholar',
    'TafsirSource',
    'TafsirEvidence',

    # Concept schemas
    'ConceptSummary',
    'ConceptListResponse',
    'OccurrenceDetail',
    'AssociationDetail',
    'ConceptDetailResponse',

    # Miracle schemas
    'MiracleSummary',
    'MiracleListResponse',
    'MiracleDetailResponse',

    # Tafsir schemas
    'TafsirEvidenceResponse',

    # Verification schemas
    'VerificationTaskCreate',
    'VerificationTaskResponse',
    'VerificationDecisionCreate',
    'VerificationDecisionResponse',
    'VerificationStatsResponse',
]
