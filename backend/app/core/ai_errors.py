"""
Bilingual error responses for AI (Hugging Face) failures.

One envelope for every route that calls the LLM, so clients can tell a quota
problem (429, ``ai_quota_exceeded``) from an outage (503,
``service_unavailable``) and show natural Arabic or English text:

    {"ok": false,
     "error": {"code", "message", "message_ar", "request_id"},
     "message_en": ..., "message_ar": ..., "request_id": ...}

No upstream response text or internal error kind is ever included.
"""
from __future__ import annotations

from fastapi.responses import JSONResponse

AI_QUOTA_EXCEEDED = "ai_quota_exceeded"
SERVICE_UNAVAILABLE = "service_unavailable"
AI_BAD_OUTPUT = "ai_bad_output"

_QUOTA_EN = "The AI service has reached its usage limit. Please try again later."
_QUOTA_AR = "بلغت خدمة الذكاء الاصطناعي حد الاستخدام. حاول لاحقاً."
_DOWN_EN = "The AI service is temporarily unavailable."
_DOWN_AR = "خدمة الذكاء الاصطناعي غير متاحة مؤقتاً."


def ai_error_response(
    code: str, message_en: str, message_ar: str, status_code: int, request_id: str = ""
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message_en,
                "message_ar": message_ar,
                "request_id": request_id,
            },
            "message_en": message_en,
            "message_ar": message_ar,
            "request_id": request_id,
        },
    )


def hf_failure_response(exc, request_id: str = "") -> JSONResponse:
    """429 + ai_quota_exceeded for quota, otherwise 503 + service_unavailable."""
    from app.ai.hf_client import HFErrorKind

    quota = exc.kind == HFErrorKind.QUOTA
    return ai_error_response(
        code=AI_QUOTA_EXCEEDED if quota else SERVICE_UNAVAILABLE,
        message_en=_QUOTA_EN if quota else _DOWN_EN,
        message_ar=_QUOTA_AR if quota else _DOWN_AR,
        status_code=429 if quota else 503,
        request_id=request_id,
    )
