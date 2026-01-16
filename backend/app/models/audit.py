"""
Audit log model for tracking system operations.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Data operations
    DATA_IMPORT = "data_import"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"

    # RAG operations
    RAG_QUERY = "rag_query"
    RAG_RESPONSE = "rag_response"
    CITATION_VALIDATION = "citation_validation"

    # Translation
    TRANSLATION_CREATE = "translation_create"
    TRANSLATION_VERIFY = "translation_verify"

    # Pipeline operations
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_FAIL = "pipeline_fail"

    # Verification
    VERIFY_PASS = "verify_pass"
    VERIFY_FAIL = "verify_fail"


class AuditLog(Base):
    """
    Audit log for tracking all significant system operations.

    Critical for:
    - Tracking data provenance
    - Debugging pipeline failures
    - Monitoring RAG quality
    - Compliance and accountability
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # What happened
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)  # "verse", "tafseer_chunk", "story"
    entity_id = Column(String(100), nullable=True)

    # Who/what did it
    actor = Column(String(100), nullable=False)  # "system", "pipeline", "user:123"

    # Details
    message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)  # Additional structured data

    # Status
    status = Column(String(20), default="success")  # "success", "failure", "warning"
    error_message = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer, nullable=True)

    # Context
    request_id = Column(String(50), nullable=True)  # For tracing
    ip_address = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_audit_action_time", "action", "created_at"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_status", "status"),
    )

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} ({self.status})>"

    @classmethod
    def log(
        cls,
        session,
        action: str,
        actor: str = "system",
        entity_type: str = None,
        entity_id: str = None,
        message: str = None,
        details: dict = None,
        status: str = "success",
        error_message: str = None,
        duration_ms: int = None,
    ):
        """
        Create an audit log entry.

        Usage:
            AuditLog.log(
                session,
                action=AuditAction.DATA_IMPORT,
                actor="pipeline",
                entity_type="tafseer_chunk",
                message="Imported 1000 tafseer chunks",
                details={"source": "ibn_kathir", "count": 1000}
            )
        """
        log_entry = cls(
            action=action,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            details=details,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        session.add(log_entry)
        return log_entry
