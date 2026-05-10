"""
User Feedback Model — Phase G.

Stores user-submitted feedback about content quality, accuracy, and UI issues.
Feeds into the admin review queue for prioritized human oversight.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Index

from app.db.database import Base


class FeedbackCategory(str, Enum):
    TRANSLATION_ISSUE = "translation_issue"
    SOURCE_MISSING = "source_missing"
    TAFSIR_ERROR = "tafsir_error"
    QURAN_REF_ERROR = "quran_ref_error"
    UI_FEEDBACK = "ui_feedback"
    INAPPROPRIATE = "inappropriate"
    OTHER = "other"


class FeedbackStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# Auto-priority by category (1 = most urgent)
CATEGORY_PRIORITY: dict[str, int] = {
    FeedbackCategory.TAFSIR_ERROR: 1,
    FeedbackCategory.QURAN_REF_ERROR: 1,
    FeedbackCategory.SOURCE_MISSING: 2,
    FeedbackCategory.TRANSLATION_ISSUE: 3,
    FeedbackCategory.INAPPROPRIATE: 3,
    FeedbackCategory.UI_FEEDBACK: 5,
    FeedbackCategory.OTHER: 5,
}

CATEGORY_LABELS: dict[str, dict[str, str]] = {
    FeedbackCategory.TRANSLATION_ISSUE: {"en": "Translation Issue", "ar": "مشكلة في الترجمة"},
    FeedbackCategory.SOURCE_MISSING: {"en": "Source Missing", "ar": "مصدر مفقود"},
    FeedbackCategory.TAFSIR_ERROR: {"en": "Tafsir Error", "ar": "خطأ في التفسير"},
    FeedbackCategory.QURAN_REF_ERROR: {"en": "Quran Reference Error", "ar": "خطأ في المرجع القرآني"},
    FeedbackCategory.UI_FEEDBACK: {"en": "UI / UX Feedback", "ar": "ملاحظة على الواجهة"},
    FeedbackCategory.INAPPROPRIATE: {"en": "Inappropriate Content", "ar": "محتوى غير لائق"},
    FeedbackCategory.OTHER: {"en": "Other", "ar": "أخرى"},
}


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # What the feedback is about
    category = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True, index=True)  # story, tafsir, concept, etc.
    entity_id = Column(String(200), nullable=True)
    page_url = Column(String(500), nullable=True)

    # Feedback content
    message = Column(Text, nullable=False)

    # Workflow
    status = Column(String(20), nullable=False, default="open", index=True)
    priority = Column(Integer, nullable=False, default=5, index=True)  # 1=highest, 5=lowest
    admin_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_user_feedback_status_priority", "status", "priority"),
        Index("ix_user_feedback_created_at", "created_at"),
    )
