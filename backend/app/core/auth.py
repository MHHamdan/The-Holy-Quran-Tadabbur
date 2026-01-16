"""
Authentication and Authorization for Tadabbur API.

Security requirements:
- Admin endpoints use Bearer token authentication
- Tokens MUST NOT appear in query strings or logs
- Basic RBAC with admin/user roles

Usage:
    from app.core.auth import require_admin, get_current_user

    @router.get("/admin/stats")
    async def get_stats(admin: AdminUser = Depends(require_admin)):
        ...
"""
import os
import logging
import hashlib
import hmac
from typing import Optional
from dataclasses import dataclass
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security configuration
# Token should be set via ADMIN_TOKEN environment variable
ADMIN_TOKEN_HASH: Optional[str] = None

if settings.admin_token:
    # Store hash of token, never the token itself
    ADMIN_TOKEN_HASH = hashlib.sha256(settings.admin_token.encode()).hexdigest()


@dataclass
class AdminUser:
    """Authenticated admin user."""
    user_id: str
    role: str = "admin"
    permissions: list = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = ["read", "write", "verify", "admin"]


# Bearer token security scheme
security = HTTPBearer(auto_error=False)


def _verify_token(token: str) -> bool:
    """
    Verify admin token using constant-time comparison.

    SECURITY: Never log the actual token value.
    """
    if not ADMIN_TOKEN_HASH:
        logger.warning("ADMIN_TOKEN not configured - admin endpoints are disabled")
        return False

    # Constant-time comparison to prevent timing attacks
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return hmac.compare_digest(token_hash, ADMIN_TOKEN_HASH)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AdminUser]:
    """
    Get current user from Bearer token.

    Returns None if no valid credentials provided.
    Does NOT raise - use require_admin for protected endpoints.
    """
    if not credentials:
        return None

    if not _verify_token(credentials.credentials):
        return None

    # Log successful auth (but not the token!)
    logger.info("Admin authenticated via Bearer token")

    return AdminUser(
        user_id="admin",
        role="admin"
    )


async def require_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AdminUser:
    """
    Require admin authentication for an endpoint.

    Raises HTTPException if not authenticated.

    Usage:
        @router.get("/admin/endpoint")
        async def admin_endpoint(admin: AdminUser = Depends(require_admin)):
            ...
    """
    from app.core.responses import APIError, ErrorCode, get_request_id

    request_id = get_request_id(request)

    if not credentials:
        logger.warning(f"[{request_id}] Admin access denied: No credentials provided")
        raise APIError(
            code=ErrorCode.UNAUTHORIZED,
            message_en="Authentication required. Provide Bearer token in Authorization header.",
            message_ar="مطلوب المصادقة. قدم رمز Bearer في رأس Authorization.",
            request_id=request_id,
            status_code=401
        )

    if not _verify_token(credentials.credentials):
        # Log failed attempt (but not the invalid token!)
        logger.warning(f"[{request_id}] Admin access denied: Invalid token")
        raise APIError(
            code=ErrorCode.UNAUTHORIZED,
            message_en="Invalid admin token",
            message_ar="رمز المشرف غير صالح",
            request_id=request_id,
            status_code=401
        )

    logger.info(f"[{request_id}] Admin authenticated successfully")

    return AdminUser(
        user_id="admin",
        role="admin"
    )


def require_permission(permission: str):
    """
    Decorator to require specific permission.

    Usage:
        @require_permission("verify")
        async def verify_content(admin: AdminUser = Depends(require_admin)):
            ...
    """
    async def check_permission(admin: AdminUser = Depends(require_admin)):
        if permission not in admin.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required"
            )
        return admin
    return check_permission


# Redaction utilities for logging
def redact_token(token: str) -> str:
    """Redact a token for safe logging."""
    if not token or len(token) < 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def redact_headers(headers: dict) -> dict:
    """Redact sensitive headers for logging."""
    safe_headers = {}
    sensitive_keys = {"authorization", "x-api-key", "cookie", "set-cookie"}

    for key, value in headers.items():
        if key.lower() in sensitive_keys:
            safe_headers[key] = "[REDACTED]"
        else:
            safe_headers[key] = value

    return safe_headers
