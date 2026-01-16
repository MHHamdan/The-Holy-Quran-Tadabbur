"""
Standardized API Response Envelope for Tadabbur.

All API endpoints MUST use these response models to ensure:
1. Consistent structure: { ok: bool, data?: T, error?: ErrorEnvelope }
2. Request tracing: request_id always present in error responses
3. Bilingual error messages: Arabic + English
4. Type safety: Pydantic validation on all responses

USAGE:
    from app.core.responses import success_response, error_response, APIError

    # Success
    return success_response(data={"concepts": [...]})

    # Error
    raise APIError(
        code=ErrorCode.NOT_FOUND,
        message_en="Concept not found",
        message_ar="المفهوم غير موجود",
        request_id=request.state.request_id
    )
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    # Client errors (4xx)
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    CONFLICT = "conflict"

    # Server errors (5xx)
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    SERVICE_UNAVAILABLE = "service_unavailable"

    # Domain-specific errors
    CONCEPT_NOT_FOUND = "concept_not_found"
    MIRACLE_NOT_FOUND = "miracle_not_found"
    OCCURRENCE_NOT_FOUND = "occurrence_not_found"
    TAFSIR_NOT_FOUND = "tafsir_not_found"
    INVALID_MADHAB = "invalid_madhab"
    VERIFICATION_REQUIRED = "verification_required"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    DATA_INCOMPLETE = "data_incomplete"


# Arabic error messages
ERROR_MESSAGES_AR: Dict[ErrorCode, str] = {
    ErrorCode.BAD_REQUEST: "طلب غير صالح",
    ErrorCode.UNAUTHORIZED: "غير مصرح - يرجى تسجيل الدخول",
    ErrorCode.FORBIDDEN: "غير مسموح بالوصول",
    ErrorCode.NOT_FOUND: "المورد غير موجود",
    ErrorCode.VALIDATION_ERROR: "خطأ في التحقق من البيانات",
    ErrorCode.CONFLICT: "تعارض في البيانات",
    ErrorCode.INTERNAL_ERROR: "حدث خطأ داخلي. تم تسجيل المشكلة.",
    ErrorCode.DATABASE_ERROR: "خطأ في قاعدة البيانات",
    ErrorCode.SERVICE_UNAVAILABLE: "الخدمة غير متاحة حالياً",
    ErrorCode.CONCEPT_NOT_FOUND: "المفهوم غير موجود",
    ErrorCode.MIRACLE_NOT_FOUND: "الآية/المعجزة غير موجودة",
    ErrorCode.OCCURRENCE_NOT_FOUND: "الموضع غير موجود",
    ErrorCode.TAFSIR_NOT_FOUND: "التفسير غير موجود",
    ErrorCode.INVALID_MADHAB: "المذهب غير معتمد - المذاهب الأربعة فقط",
    ErrorCode.VERIFICATION_REQUIRED: "يتطلب مراجعة وموافقة المشرف",
    ErrorCode.INSUFFICIENT_EVIDENCE: "أدلة غير كافية من مصادر التفسير",
    ErrorCode.DATA_INCOMPLETE: "البيانات غير مكتملة",
}


class ErrorDetail(BaseModel):
    """Detail information for validation errors."""
    field: Optional[str] = None
    message: str
    message_ar: Optional[str] = None


class ErrorEnvelope(BaseModel):
    """Standardized error envelope returned in all error responses."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message (English)")
    message_ar: str = Field(..., description="Human-readable error message (Arabic)")
    request_id: str = Field(..., description="Request ID for debugging/support")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")
    data_status: Optional[str] = Field(None, description="Data completeness status if applicable")


class APIResponseEnvelope(BaseModel, Generic[T]):
    """
    Standardized API response envelope.

    All API responses follow this structure for consistency.
    """
    ok: bool = Field(..., description="Whether the request succeeded")
    data: Optional[T] = Field(None, description="Response data on success")
    error: Optional[ErrorEnvelope] = Field(None, description="Error details on failure")
    request_id: Optional[str] = Field(None, description="Request ID (always present in errors)")


class APIError(HTTPException):
    """
    Custom API error that produces standardized error responses.

    Usage:
        raise APIError(
            code=ErrorCode.CONCEPT_NOT_FOUND,
            message_en="Concept 'xyz' not found",
            request_id=request.state.request_id
        )
    """
    def __init__(
        self,
        code: ErrorCode,
        message_en: Optional[str] = None,
        message_ar: Optional[str] = None,
        request_id: str = "",
        status_code: int = 400,
        details: Optional[List[ErrorDetail]] = None,
        data_status: Optional[str] = None,
    ):
        self.error_code = code
        self.message_en = message_en or code.value.replace("_", " ").title()
        self.message_ar = message_ar or ERROR_MESSAGES_AR.get(code, "خطأ غير معروف")
        self.request_id = request_id
        self.details = details
        self.data_status = data_status
        super().__init__(status_code=status_code, detail=self.message_en)

    def to_response(self) -> JSONResponse:
        """Convert to JSONResponse with proper headers."""
        error_envelope = ErrorEnvelope(
            code=self.error_code.value,
            message=self.message_en,
            message_ar=self.message_ar,
            request_id=self.request_id,
            details=self.details,
            data_status=self.data_status,
        )

        content = {
            "ok": False,
            "error": error_envelope.model_dump(exclude_none=True),
            "request_id": self.request_id,
        }

        return JSONResponse(
            status_code=self.status_code,
            content=content,
            headers={"X-Request-Id": self.request_id}
        )


def get_request_id(request: Request) -> str:
    """Extract request_id from request state, with fallback."""
    return getattr(request.state, 'request_id', 'unknown')


def success_response(
    data: Any,
    request_id: Optional[str] = None,
    status_code: int = 200,
) -> JSONResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data (will be serialized)
        request_id: Optional request ID for tracing
        status_code: HTTP status code (default 200)

    Returns:
        JSONResponse with standardized envelope
    """
    content = {
        "ok": True,
        "data": data,
    }
    if request_id:
        content["request_id"] = request_id

    headers = {}
    if request_id:
        headers["X-Request-Id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers if headers else None
    )


def error_response(
    code: ErrorCode,
    message_en: str,
    message_ar: Optional[str] = None,
    request_id: str = "",
    status_code: int = 400,
    details: Optional[List[ErrorDetail]] = None,
    data_status: Optional[str] = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        code: Error code from ErrorCode enum
        message_en: English error message
        message_ar: Arabic error message (defaults from ERROR_MESSAGES_AR)
        request_id: Request ID for tracing
        status_code: HTTP status code
        details: Additional error details
        data_status: Data completeness status if applicable

    Returns:
        JSONResponse with standardized error envelope
    """
    if message_ar is None:
        message_ar = ERROR_MESSAGES_AR.get(code, "خطأ غير معروف")

    error_envelope = ErrorEnvelope(
        code=code.value,
        message=message_en,
        message_ar=message_ar,
        request_id=request_id,
        details=details,
        data_status=data_status,
    )

    content = {
        "ok": False,
        "error": error_envelope.model_dump(exclude_none=True),
        "request_id": request_id,
    }

    # Log error for observability
    logger.warning(
        f"API Error [{request_id}] {code.value}: {message_en}",
        extra={
            "request_id": request_id,
            "error_code": code.value,
            "data_status": data_status,
        }
    )

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"X-Request-Id": request_id}
    )


def incomplete_data_response(
    data: Any,
    message_en: str,
    message_ar: str,
    request_id: str = "",
    missing_fields: Optional[List[str]] = None,
) -> JSONResponse:
    """
    Create a response for successful but incomplete data.

    Use this when data exists but is missing required fields,
    so the UI can show appropriate "data incomplete" messaging.
    """
    content = {
        "ok": True,
        "data": data,
        "data_status": "incomplete",
        "data_message": message_en,
        "data_message_ar": message_ar,
    }

    if missing_fields:
        content["missing_fields"] = missing_fields

    if request_id:
        content["request_id"] = request_id

    headers = {}
    if request_id:
        headers["X-Request-Id"] = request_id

    return JSONResponse(
        status_code=200,
        content=content,
        headers=headers if headers else None
    )
