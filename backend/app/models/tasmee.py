"""
Database models for Tasmeeʿ (Memorization) feature.

This module defines the SQLAlchemy models for storing memorization
sessions, events, and mistake history.

Tables:
- tasmee_sessions: Recording sessions with metadata
- tasmee_events: Individual events during a session
- tasmee_mistakes: Detailed mistake records
- tasmee_progress: User progress tracking per surah/ayah
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class SessionStatus(str, PyEnum):
    """Status of a Tasmee session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class MistakeTypeEnum(str, PyEnum):
    """Types of recitation mistakes."""

    SUBSTITUTION = "substitution"
    DELETION = "deletion"
    INSERTION = "insertion"
    REPETITION = "repetition"
    HESITATION = "hesitation"
    MISPRONUNCIATION = "mispronunciation"


class EventType(str, PyEnum):
    """Types of events during a session."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"
    WORD_MATCHED = "word_matched"
    MISTAKE_DETECTED = "mistake_detected"
    CORRECTION = "correction"
    VERSE_COMPLETED = "verse_completed"


class TasmeeSession(Base):
    """
    A memorization practice session.

    Records a single recitation attempt with audio, timing,
    and performance metrics.
    """

    __tablename__ = "tasmee_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # User identification (for future user accounts)
    user_id = Column(String(255), nullable=True, index=True)
    device_id = Column(String(255), nullable=True)

    # Session metadata
    status = Column(
        Enum(SessionStatus, name='session_status', create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=SessionStatus.ACTIVE,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at = Column(DateTime, nullable=True)

    # Quran reference
    sura_no = Column(Integer, nullable=False, index=True)
    sura_name_ar = Column(String(100), nullable=True)
    sura_name_en = Column(String(100), nullable=True)
    aya_start = Column(Integer, nullable=False)
    aya_end = Column(Integer, nullable=False)
    total_verses = Column(Integer, nullable=False)
    total_words = Column(Integer, nullable=False)

    # Audio file reference
    audio_file_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    audio_format = Column(String(20), default="wav")

    # Performance metrics
    words_completed = Column(Integer, default=0)
    words_correct = Column(Integer, default=0)
    mistakes_count = Column(Integer, default=0)
    accuracy_score = Column(Float, nullable=True)  # 0.0-1.0
    completion_percentage = Column(Float, default=0.0)  # 0.0-100.0

    # Timing
    active_duration_seconds = Column(Float, default=0.0)
    total_duration_seconds = Column(Float, default=0.0)

    # STT configuration
    stt_provider = Column(String(50), default="huggingface")
    stt_model = Column(String(50), default="base")

    # Additional data (JSON) - stores expected_text and other session data
    # Note: Using 'extra_data' as column name since 'metadata' is reserved in SQLAlchemy
    extra_data = Column("metadata", JSON, nullable=True)

    # Relationships
    events = relationship(
        "TasmeeEvent",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    mistakes = relationship(
        "TasmeeMistake",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<TasmeeSession(id={self.id}, sura={self.sura_no}, "
            f"ayat={self.aya_start}-{self.aya_end}, status={self.status})>"
        )

    def calculate_accuracy(self) -> float:
        """Calculate accuracy score based on words and mistakes."""
        if self.words_completed == 0:
            return 0.0
        return max(0.0, min(1.0, self.words_correct / self.words_completed))

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "sura_no": self.sura_no,
            "sura_name_ar": self.sura_name_ar,
            "sura_name_en": self.sura_name_en,
            "aya_start": self.aya_start,
            "aya_end": self.aya_end,
            "total_verses": self.total_verses,
            "total_words": self.total_words,
            "words_completed": self.words_completed,
            "words_correct": self.words_correct,
            "mistakes_count": self.mistakes_count,
            "accuracy_score": self.accuracy_score,
            "completion_percentage": self.completion_percentage,
            "audio_duration_seconds": self.audio_duration_seconds,
            "active_duration_seconds": self.active_duration_seconds,
        }


class TasmeeEvent(Base):
    """
    Individual events during a Tasmee session.

    Records word matches, mistakes, pauses, and other events
    with timestamps for detailed analysis.
    """

    __tablename__ = "tasmee_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("tasmee_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event details
    event_type = Column(Enum(EventType, name='event_type', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    timestamp = Column(Float, nullable=False)  # Seconds from session start
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Word reference
    expected_word_index = Column(Integer, nullable=True)
    expected_word = Column(String(100), nullable=True)
    recognized_word = Column(String(100), nullable=True)

    # For verse completion events
    verse_sura_no = Column(Integer, nullable=True)
    verse_aya_no = Column(Integer, nullable=True)

    # Confidence and matching
    confidence = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)

    # Additional data (JSON)
    data = Column(JSON, nullable=True)

    # Relationships
    session = relationship("TasmeeSession", back_populates="events")

    def __repr__(self):
        return (
            f"<TasmeeEvent(id={self.id}, type={self.event_type}, "
            f"timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "expected_word_index": self.expected_word_index,
            "expected_word": self.expected_word,
            "recognized_word": self.recognized_word,
            "confidence": self.confidence,
            "similarity_score": self.similarity_score,
            "data": self.data,
        }


class TasmeeMistake(Base):
    """
    Detailed record of a recitation mistake.

    Stores comprehensive information about each mistake for
    analysis, review, and learning.
    """

    __tablename__ = "tasmee_mistakes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("tasmee_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Mistake classification
    mistake_type = Column(Enum(MistakeTypeEnum, name='mistake_type', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    severity = Column(String(20), default="moderate")  # minor, moderate, major

    # Position in text
    word_position = Column(Integer, nullable=False)
    verse_sura_no = Column(Integer, nullable=False)
    verse_aya_no = Column(Integer, nullable=False)

    # Words
    expected_word = Column(String(200), nullable=False)
    expected_normalized = Column(String(200), nullable=False)
    actual_word = Column(String(200), nullable=True)  # Null for deletions
    actual_normalized = Column(String(200), nullable=True)

    # Timing
    timestamp = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Confidence
    confidence = Column(Float, default=0.8)

    # Context
    context_before = Column(JSON, nullable=True)  # List of previous words
    context_after = Column(JSON, nullable=True)  # List of following words

    # Audio reference (for playback)
    audio_start_time = Column(Float, nullable=True)
    audio_end_time = Column(Float, nullable=True)

    # User correction tracking
    was_corrected = Column(Boolean, default=False)
    corrected_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("TasmeeSession", back_populates="mistakes")

    def __repr__(self):
        return (
            f"<TasmeeMistake(id={self.id}, type={self.mistake_type}, "
            f"expected={self.expected_word})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "mistake_type": self.mistake_type.value,
            "severity": self.severity,
            "word_position": self.word_position,
            "verse_sura_no": self.verse_sura_no,
            "verse_aya_no": self.verse_aya_no,
            "expected_word": self.expected_word,
            "expected_normalized": self.expected_normalized,
            "actual_word": self.actual_word,
            "actual_normalized": self.actual_normalized,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "was_corrected": self.was_corrected,
        }


class TasmeeProgress(Base):
    """
    User progress tracking per surah/ayah.

    Aggregates data across sessions to track memorization progress.
    """

    __tablename__ = "tasmee_progress"

    id = Column(Integer, primary_key=True, index=True)

    # User identification
    user_id = Column(String(255), nullable=True, index=True)
    device_id = Column(String(255), nullable=True)

    # Quran reference
    sura_no = Column(Integer, nullable=False, index=True)
    aya_no = Column(Integer, nullable=False, index=True)

    # Progress metrics
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    best_accuracy = Column(Float, default=0.0)
    average_accuracy = Column(Float, default=0.0)

    # Memorization status
    is_memorized = Column(Boolean, default=False)
    memorized_at = Column(DateTime, nullable=True)

    # Common mistakes for this ayah
    common_mistakes = Column(JSON, nullable=True)  # {word_position: count}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", "sura_no", "aya_no"),
    )

    def __repr__(self):
        return (
            f"<TasmeeProgress(sura={self.sura_no}, aya={self.aya_no}, "
            f"attempts={self.total_attempts})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "sura_no": self.sura_no,
            "aya_no": self.aya_no,
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "last_attempt_at": (
                self.last_attempt_at.isoformat() if self.last_attempt_at else None
            ),
            "best_accuracy": self.best_accuracy,
            "average_accuracy": self.average_accuracy,
            "is_memorized": self.is_memorized,
        }
