"""
Verification Queue Models for Admin Review Workflow.

WORKFLOW DESIGN:
================
1. Content flagged by users/AI -> enters verification_queue
2. Admin reviews flagged content
3. Decision: approve, reject, revise
4. Actions executed based on decision

FLAG TYPES:
===========
- accuracy: Potential factual inaccuracy
- source: Missing or weak evidence
- translation: Translation quality issue
- formatting: Display/formatting issue
- inappropriate: Inappropriate content
- duplicate: Duplicate content
- enhancement: Suggested improvement

STATUS FLOW:
============
pending -> in_review -> (approved | rejected | deferred)
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base


class FlagType(str, Enum):
    """Types of flags that can be raised."""
    ACCURACY = "accuracy"           # Potential factual error
    SOURCE = "source"               # Missing/weak evidence
    TRANSLATION = "translation"     # Translation quality
    FORMATTING = "formatting"       # Display issues
    INAPPROPRIATE = "inappropriate" # Inappropriate content
    DUPLICATE = "duplicate"         # Duplicate entry
    ENHANCEMENT = "enhancement"     # Suggested improvement
    OTHER = "other"                 # Other issues


class VerificationStatus(str, Enum):
    """Status of verification queue item."""
    PENDING = "pending"           # Awaiting review
    IN_REVIEW = "in_review"       # Being reviewed
    APPROVED = "approved"         # Verified and approved
    REJECTED = "rejected"         # Rejected/removed
    DEFERRED = "deferred"         # Deferred for later
    NEEDS_INFO = "needs_info"     # Needs more information


class ReviewDecision(str, Enum):
    """Admin review decisions."""
    APPROVE = "approve"           # Content is correct
    REJECT = "reject"             # Content should be removed
    REVISE = "revise"             # Content needs revision
    DEFER = "defer"               # Defer decision
    ESCALATE = "escalate"         # Escalate to senior reviewer


class EntityType(str, Enum):
    """Types of entities that can be flagged."""
    CONCEPT = "concept"
    OCCURRENCE = "occurrence"
    ASSOCIATION = "association"
    STORY = "story"
    SEGMENT = "segment"
    TAFSEER = "tafseer"
    TRANSLATION = "translation"
    GRAMMAR = "grammar"


class VerificationQueue(Base):
    """
    Queue item for content verification.

    Tracks flagged content through the admin review workflow.
    """
    __tablename__ = "verification_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Entity being flagged
    entity_type = Column(String(50), nullable=False, index=True)  # From EntityType
    entity_id = Column(String(200), nullable=False)

    # Who flagged it
    flagged_by = Column(String(100), nullable=False)  # user_id or "ai_system"
    flagged_at = Column(DateTime, default=datetime.utcnow)

    # Flag details
    flag_type = Column(String(50), nullable=False, index=True)  # From FlagType
    flag_reason = Column(Text, nullable=True)  # Human-readable explanation
    flag_reason_ar = Column(Text, nullable=True)  # Arabic explanation

    # Context snapshot (entity state at flag time)
    context_snapshot = Column(JSONB, nullable=True)

    # AI verification assistant results
    ai_confidence = Column(Float, nullable=True)  # 0.0-1.0
    ai_suggestion = Column(Text, nullable=True)
    ai_suggestion_ar = Column(Text, nullable=True)
    ai_analysis = Column(JSONB, nullable=True)  # Detailed AI analysis

    # Review details
    status = Column(String(20), default="pending", nullable=False, index=True)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest

    # Reviewer assignment
    assigned_to = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Review outcome
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_decision = Column(String(20), nullable=True)  # From ReviewDecision
    review_notes = Column(Text, nullable=True)
    review_notes_ar = Column(Text, nullable=True)

    # Action taken
    action_taken = Column(String(100), nullable=True)  # e.g., "updated", "deleted"
    action_details = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_verification_entity", "entity_type", "entity_id"),
        Index("ix_verification_status_priority", "status", "priority"),
        Index("ix_verification_assigned", "assigned_to", "status"),
        Index("ix_verification_flagged_at", "flagged_at"),
    )

    def __repr__(self):
        return f"<VerificationQueue {self.id}: {self.entity_type}:{self.entity_id} [{self.status}]>"

    def to_dict(self, language: str = "en") -> dict:
        """Convert to API response format."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "flagged_by": self.flagged_by,
            "flagged_at": self.flagged_at.isoformat() if self.flagged_at else None,
            "flag_type": self.flag_type,
            "flag_reason": self.flag_reason_ar if language == "ar" else self.flag_reason,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "ai_confidence": self.ai_confidence,
            "ai_suggestion": self.ai_suggestion_ar if language == "ar" else self.ai_suggestion,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_decision": self.review_decision,
            "review_notes": self.review_notes_ar if language == "ar" else self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_admin_dict(self, language: str = "en") -> dict:
        """Convert to admin response format (includes more details)."""
        base = self.to_dict(language)
        base.update({
            "context_snapshot": self.context_snapshot,
            "ai_analysis": self.ai_analysis,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "action_taken": self.action_taken,
            "action_details": self.action_details,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        return base


# =============================================================================
# FLAG TYPE TRANSLATIONS
# =============================================================================

FLAG_TYPE_TRANSLATIONS = {
    "accuracy": {"ar": "دقة", "en": "Accuracy Issue"},
    "source": {"ar": "مصدر", "en": "Source/Evidence"},
    "translation": {"ar": "ترجمة", "en": "Translation"},
    "formatting": {"ar": "تنسيق", "en": "Formatting"},
    "inappropriate": {"ar": "غير مناسب", "en": "Inappropriate"},
    "duplicate": {"ar": "مكرر", "en": "Duplicate"},
    "enhancement": {"ar": "تحسين", "en": "Enhancement"},
    "other": {"ar": "أخرى", "en": "Other"},
}

STATUS_TRANSLATIONS = {
    "pending": {"ar": "قيد الانتظار", "en": "Pending"},
    "in_review": {"ar": "قيد المراجعة", "en": "In Review"},
    "approved": {"ar": "معتمد", "en": "Approved"},
    "rejected": {"ar": "مرفوض", "en": "Rejected"},
    "deferred": {"ar": "مؤجل", "en": "Deferred"},
    "needs_info": {"ar": "يحتاج معلومات", "en": "Needs Info"},
}

DECISION_TRANSLATIONS = {
    "approve": {"ar": "اعتماد", "en": "Approve"},
    "reject": {"ar": "رفض", "en": "Reject"},
    "revise": {"ar": "تعديل", "en": "Revise"},
    "defer": {"ar": "تأجيل", "en": "Defer"},
    "escalate": {"ar": "تصعيد", "en": "Escalate"},
}
