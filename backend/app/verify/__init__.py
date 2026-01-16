"""
Quran-wide Verification Engine.

Provides comprehensive verification of:
- Story registry coverage
- Ayah range validity
- Arabic localization completeness
- Evidence grounding
- Semantic relation integrity
"""

from app.verify.registry import QuranStoryRegistry
from app.verify.engine import QuranVerificationEngine
from app.verify.report import VerificationReport
from app.verify.evidence_resolver import EvidenceResolver, TafsirSource

__all__ = [
    "QuranStoryRegistry",
    "QuranVerificationEngine",
    "VerificationReport",
    "EvidenceResolver",
    "TafsirSource",
]
