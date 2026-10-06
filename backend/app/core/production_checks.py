"""
Startup checks for production configuration.

Problems are reported loudly at startup instead of surfacing later as
confusing runtime failures. Nothing here prints a secret value.
"""
from __future__ import annotations

import logging
from typing import List, Sequence

logger = logging.getLogger(__name__)

# Origins used by the Capacitor WebViews of the Android/iOS apps.
MOBILE_APP_ORIGINS = ("capacitor://localhost", "https://localhost", "http://localhost")


def safe_cors_origins(origins: Sequence[str], environment: str) -> List[str]:
    """
    Drop a wildcard origin in production/staging.

    With credentials enabled, Starlette answers a "*" configuration by echoing
    the caller's Origin, which would let any website make credentialed
    requests to the API.
    """
    cleaned = [o for o in origins if o]
    if environment.lower() in ("production", "staging", "prod") and "*" in cleaned:
        logger.error("CORS_ORIGINS contains '*' in %s; ignoring the wildcard", environment)
        cleaned = [o for o in cleaned if o != "*"]
    return cleaned


def production_config_problems(settings, cors_origins: Sequence[str], cors_env_set: bool) -> List[str]:
    """Human-readable configuration problems for a production deployment."""
    problems: List[str] = []
    if settings.environment.lower() != "production":
        return problems

    if settings.hf_token is None or not settings.hf_token.get_secret_value().strip():
        problems.append("HF_TOKEN is not set: AI answers, embeddings and speech recognition are disabled")
    if not (settings.admin_api_key or "").strip():
        problems.append("ADMIN_API_KEY is not set: admin endpoints will answer 503")
    if not cors_env_set:
        problems.append("CORS_ORIGINS is not set: only localhost development origins are allowed")
    if any(o.startswith("http://") and "localhost" not in o and "127.0.0.1" not in o for o in cors_origins):
        problems.append("CORS_ORIGINS contains a non-HTTPS public origin")
    if "localhost" in settings.database_url or "127.0.0.1" in settings.database_url:
        problems.append("DATABASE_URL points at localhost")
    if settings.qdrant_host in ("localhost", "127.0.0.1"):
        problems.append("QDRANT_HOST points at localhost")
    if "localhost" in settings.redis_url or "127.0.0.1" in settings.redis_url:
        problems.append("REDIS_URL points at localhost")
    return problems
