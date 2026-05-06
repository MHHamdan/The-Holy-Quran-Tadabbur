"""
Admin API Key Authentication — Tadabbur (Phase Security)

Protects all /api/v1/admin/* endpoints with a header-based API key.

Header:   X-Admin-API-Key: <key>
Env var:  ADMIN_API_KEY

Security properties:
  - Key hash (SHA-256) computed at request time from environment; never
    cached as plaintext.
  - Constant-time comparison via hmac.compare_digest to prevent timing attacks.
  - Key value is NEVER stored in plaintext memory, NEVER logged, NEVER
    returned in error responses.
  - Fail-closed in production/staging: if ADMIN_API_KEY is not configured,
    all admin endpoints return 503 (misconfiguration) rather than open access.
  - Development without a key configured: 401 with instruction to set the var.
  - Missing header → 401 Unauthorized
  - Wrong key → 403 Forbidden
  - Correct key → passes through (None returned)

Usage:
    from app.core.admin_auth import require_admin_api_key

    # Per-endpoint:
    @router.get("/admin/thing")
    async def endpoint(_: None = Depends(require_admin_api_key)):
        ...

    # Or at router level (preferred — applies to all routes):
    router = APIRouter(dependencies=[Depends(require_admin_api_key)])
"""
import hashlib
import hmac
import logging
from typing import Optional

from fastapi import Request, Header, Depends
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_configured_key_hash() -> Optional[str]:
    """
    Return the SHA-256 hash of the configured ADMIN_API_KEY, or None if not set.

    Reads from `settings.admin_api_key` which pydantic-settings populates from
    the ADMIN_API_KEY environment variable and/or the `.env` file.

    Called at request time (not module load time) so that tests can patch this
    function to inject different key scenarios without reloading the module.

    SECURITY: Never return, log, or store the raw key value.
    """
    raw = settings.admin_api_key
    if not raw or not raw.strip():
        return None
    return hashlib.sha256(raw.strip().encode()).hexdigest()


def _verify_key(provided: str) -> bool:
    """
    Verify a provided key against the configured hash in constant time.

    Returns False (rather than raising) if no key is configured so that
    callers can produce the appropriate HTTP error.

    SECURITY: Do NOT log the provided value on failure.
    """
    configured_hash = _get_configured_key_hash()
    if not configured_hash:
        return False
    provided_hash = hashlib.sha256(provided.strip().encode()).hexdigest()
    return hmac.compare_digest(provided_hash, configured_hash)


async def require_admin_api_key(
    request: Request,
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key"),
) -> None:
    """
    FastAPI dependency that enforces X-Admin-API-Key authentication.

    Raises APIError (→ HTTP 401/403/503) on any auth failure.
    Returns None on success so it can be used as a typed dependency:
        _: None = Depends(require_admin_api_key)

    SECURITY NOTES:
    - ADMIN_API_KEY not configured + production/staging → 503 (not 401).
      This surfaces the misconfiguration loudly rather than silently opening
      the endpoint.
    - ADMIN_API_KEY not configured + development → 401 with setup instructions.
    - Wrong key → 403 (not 401) to distinguish "no credentials" from "bad creds".
    - Correct key → log authentication success (key value never logged).
    """
    from app.core.responses import APIError, ErrorCode, get_request_id

    request_id = get_request_id(request)
    env = settings.environment.lower()
    is_production_or_staging = env in ("production", "staging", "prod")

    configured_hash = _get_configured_key_hash()

    # ---- Fail-closed: key not configured ----
    if not configured_hash:
        if is_production_or_staging:
            logger.error(
                "[%s] Admin endpoint called but ADMIN_API_KEY is not configured "
                "(environment=%s). Returning 503.",
                request_id,
                env,
            )
            raise APIError(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message_en=(
                    "Admin authentication is not configured on this server. "
                    "Contact the platform administrator."
                ),
                message_ar=(
                    "لم يتم تهيئة المصادقة الإدارية على هذا الخادم. "
                    "تواصل مع مسؤول المنصة."
                ),
                request_id=request_id,
                status_code=503,
            )
        else:
            logger.warning(
                "[%s] ADMIN_API_KEY is not set (environment=%s). "
                "Admin endpoints are disabled until ADMIN_API_KEY is configured.",
                request_id,
                env,
            )
            raise APIError(
                code=ErrorCode.UNAUTHORIZED,
                message_en=(
                    "Admin access is not configured. "
                    "Set ADMIN_API_KEY environment variable to enable admin endpoints."
                ),
                message_ar=(
                    "يتطلب الوصول إلى لوحة المراجعة صلاحية إدارية. "
                    "قم بتعيين متغير البيئة ADMIN_API_KEY لتفعيل نقاط النهاية الإدارية."
                ),
                request_id=request_id,
                status_code=401,
            )

    # ---- Missing header ----
    if x_admin_api_key is None:
        logger.warning(
            "[%s] Admin access denied: X-Admin-API-Key header missing",
            request_id,
        )
        raise APIError(
            code=ErrorCode.UNAUTHORIZED,
            message_en="Authentication required. Provide X-Admin-API-Key header.",
            message_ar=(
                "يتطلب الوصول إلى لوحة المراجعة صلاحية إدارية. "
                "أرسل رأس X-Admin-API-Key."
            ),
            request_id=request_id,
            status_code=401,
        )

    # ---- Wrong key (constant-time comparison) ----
    if not _verify_key(x_admin_api_key):
        # SECURITY: Do NOT log the provided key value.
        logger.warning(
            "[%s] Admin access denied: invalid X-Admin-API-Key provided",
            request_id,
        )
        raise APIError(
            code=ErrorCode.FORBIDDEN,
            message_en="Invalid admin API key.",
            message_ar="مفتاح API الإداري غير صالح.",
            request_id=request_id,
            status_code=403,
        )

    # ---- Authenticated ----
    logger.info("[%s] Admin authenticated via X-Admin-API-Key", request_id)
