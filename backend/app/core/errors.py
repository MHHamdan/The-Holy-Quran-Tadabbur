"""
Structured Error Handling for Tadabbur RAG API.

This module provides:
1. Error types with Arabic + English messages
2. Correlation ID generation and tracking
3. Safe error responses that never leak internal details
4. Structured logging with redaction

SECURITY:
- Never log sensitive data (tokens, user PII)
- Only log question hash in production
- Include correlation_id in all error responses
"""
import uuid
import hashlib
import logging
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Error codes for structured error handling."""
    # Connection errors
    LLM_UNAVAILABLE = "llm_unavailable"
    RETRIEVAL_FAILED = "retrieval_failed"
    DATABASE_ERROR = "database_error"

    # Validation errors
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_QUESTION = "invalid_question"
    NO_SOURCES_SELECTED = "no_sources_selected"

    # Processing errors
    GENERATION_FAILED = "generation_failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"

    # Internal errors
    INTERNAL_ERROR = "internal_error"
    CONFIGURATION_ERROR = "configuration_error"


# Arabic error messages for each error code
ERROR_MESSAGES_AR: Dict[ErrorCode, str] = {
    ErrorCode.LLM_UNAVAILABLE: "تعذّر الاتصال بنموذج اللغة حالياً. حاول لاحقاً.",
    ErrorCode.RETRIEVAL_FAILED: "تعذّر البحث في مصادر التفسير. حاول لاحقاً.",
    ErrorCode.DATABASE_ERROR: "حدث خطأ في قاعدة البيانات. حاول لاحقاً.",
    ErrorCode.INSUFFICIENT_EVIDENCE: "لم نعثر على أدلة تفسيرية كافية للإجابة بدقة على هذا السؤال.",
    ErrorCode.INVALID_QUESTION: "السؤال غير صالح. يرجى إعادة صياغته.",
    ErrorCode.NO_SOURCES_SELECTED: "يرجى اختيار مصدر تفسير واحد على الأقل.",
    ErrorCode.GENERATION_FAILED: "تعذّر توليد الإجابة. حاول مرة أخرى.",
    ErrorCode.TIMEOUT: "انتهت مهلة المعالجة. حاول بسؤال أقصر.",
    ErrorCode.RATE_LIMITED: "تم تجاوز حد الطلبات. انتظر قليلاً ثم حاول مجدداً.",
    ErrorCode.INTERNAL_ERROR: "حدث خطأ داخلي. تم تسجيل المشكلة وسنعمل على حلها.",
    ErrorCode.CONFIGURATION_ERROR: "خطأ في تكوين الخدمة. يرجى التواصل مع الدعم.",
}

# English error messages
ERROR_MESSAGES_EN: Dict[ErrorCode, str] = {
    ErrorCode.LLM_UNAVAILABLE: "Language model service is currently unavailable. Please try again later.",
    ErrorCode.RETRIEVAL_FAILED: "Failed to search tafseer sources. Please try again later.",
    ErrorCode.DATABASE_ERROR: "A database error occurred. Please try again later.",
    ErrorCode.INSUFFICIENT_EVIDENCE: "Insufficient scholarly evidence found to answer this question accurately.",
    ErrorCode.INVALID_QUESTION: "Invalid question format. Please rephrase your question.",
    ErrorCode.NO_SOURCES_SELECTED: "Please select at least one tafseer source.",
    ErrorCode.GENERATION_FAILED: "Failed to generate response. Please try again.",
    ErrorCode.TIMEOUT: "Request timed out. Please try a shorter question.",
    ErrorCode.RATE_LIMITED: "Rate limit exceeded. Please wait and try again.",
    ErrorCode.INTERNAL_ERROR: "An internal error occurred. This has been logged for investigation.",
    ErrorCode.CONFIGURATION_ERROR: "Service configuration error. Please contact support.",
}


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())[:8]  # Short but unique enough


def hash_question(question: str) -> str:
    """
    Hash a question for logging purposes.

    In production, we don't want to log user questions directly
    but need a way to correlate logs with user reports.
    """
    return hashlib.sha256(question.encode()).hexdigest()[:16]


@dataclass
class RAGError:
    """
    Structured RAG error with bilingual messages.

    This is the internal error representation. Use to_response()
    to get a safe, user-facing response.
    """
    code: ErrorCode
    correlation_id: str
    message_ar: str = ""
    message_en: str = ""
    internal_details: str = ""  # Never exposed to client
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retrieval_stats: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.message_ar:
            self.message_ar = ERROR_MESSAGES_AR.get(self.code, ERROR_MESSAGES_AR[ErrorCode.INTERNAL_ERROR])
        if not self.message_en:
            self.message_en = ERROR_MESSAGES_EN.get(self.code, ERROR_MESSAGES_EN[ErrorCode.INTERNAL_ERROR])

    def to_response(self, language: str = "ar") -> Dict[str, Any]:
        """
        Convert to safe API response.

        NEVER includes internal_details or stack traces.
        """
        return {
            "ok": False,
            "error_code": self.code.value,
            "error_id": self.correlation_id,
            "message": self.message_ar if language == "ar" else self.message_en,
            "message_ar": self.message_ar,
            "message_en": self.message_en,
            "timestamp": self.timestamp.isoformat(),
        }

    def log(self, question_hash: str = "", route: str = "/rag/ask"):
        """
        Log error with structured fields for observability.

        SECURITY: Never logs the actual question text.
        """
        log_data = {
            "correlation_id": self.correlation_id,
            "error_code": self.code.value,
            "route": route,
            "question_hash": question_hash,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.retrieval_stats:
            log_data["retrieval_stats"] = self.retrieval_stats

        # Log internal details at ERROR level
        logger.error(
            f"RAG Error [{self.correlation_id}]: {self.code.value} - {self.internal_details}",
            extra=log_data,
        )


@dataclass
class RAGRequestContext:
    """
    Request context for tracking and logging.

    Created at the start of each request and passed through the pipeline.
    """
    correlation_id: str
    question_hash: str
    language: str
    start_time: datetime = field(default_factory=datetime.utcnow)

    # Stats collected during processing
    retrieval_chunk_count: int = 0
    retrieval_source_count: int = 0
    llm_provider: str = ""
    llm_latency_ms: int = 0

    @classmethod
    def create(cls, question: str, language: str = "ar") -> "RAGRequestContext":
        """Create a new request context."""
        return cls(
            correlation_id=generate_correlation_id(),
            question_hash=hash_question(question),
            language=language,
        )

    def log_success(self, route: str = "/rag/ask"):
        """Log successful request with stats."""
        elapsed_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)
        logger.info(
            f"RAG Success [{self.correlation_id}]: "
            f"chunks={self.retrieval_chunk_count}, "
            f"sources={self.retrieval_source_count}, "
            f"llm={self.llm_provider}, "
            f"total_ms={elapsed_ms}",
            extra={
                "correlation_id": self.correlation_id,
                "route": route,
                "question_hash": self.question_hash,
                "retrieval_chunk_count": self.retrieval_chunk_count,
                "retrieval_source_count": self.retrieval_source_count,
                "llm_provider": self.llm_provider,
                "llm_latency_ms": self.llm_latency_ms,
                "total_ms": elapsed_ms,
            }
        )


def create_error(
    code: ErrorCode,
    correlation_id: str,
    internal_details: str = "",
    retrieval_stats: Optional[Dict[str, Any]] = None,
) -> RAGError:
    """
    Factory function to create a RAGError.

    Usage:
        error = create_error(
            ErrorCode.LLM_UNAVAILABLE,
            ctx.correlation_id,
            internal_details="Ollama returned 503"
        )
    """
    return RAGError(
        code=code,
        correlation_id=correlation_id,
        internal_details=internal_details,
        retrieval_stats=retrieval_stats,
    )
