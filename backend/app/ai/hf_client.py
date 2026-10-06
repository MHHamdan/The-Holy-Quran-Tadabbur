"""
Shared Hugging Face Inference Providers plumbing.

- Token resolution (``HF_TOKEN``; ``HUGGINGFACE_TOKEN`` accepted for compatibility)
- Client construction for the OpenAI-compatible router (chat) and for
  task endpoints on the ``hf-inference`` provider (embeddings, reranking,
  ASR, zero-shot classification)
- Mapping of upstream failures to a small set of controlled error kinds

SECURITY: the token is held in a pydantic ``SecretStr`` and is only ever handed
to the HTTP client. Error messages produced here never include the token,
request headers, or raw upstream response bodies.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class HFErrorKind(str, Enum):
    """Controlled failure categories for upstream HF calls."""

    NOT_CONFIGURED = "not_configured"      # no token on the server
    AUTH = "auth"                          # 401 — token invalid/revoked
    FORBIDDEN = "forbidden"                # 403 — token lacks permission / gated model
    QUOTA = "quota"                        # 402 / 429 — credits exhausted or rate limited
    MODEL_UNAVAILABLE = "model_unavailable"  # 404 / 503 / no provider serves the model
    TIMEOUT = "timeout"
    NETWORK = "network"                    # DNS / connection failure
    BAD_REQUEST = "bad_request"            # 400 / 422 — our request was rejected
    MALFORMED = "malformed"                # 2xx with an unusable body
    UPSTREAM = "upstream"                  # other 5xx


# Kinds worth retrying later (as opposed to configuration problems)
TRANSIENT_KINDS = frozenset({
    HFErrorKind.QUOTA, HFErrorKind.MODEL_UNAVAILABLE, HFErrorKind.TIMEOUT,
    HFErrorKind.NETWORK, HFErrorKind.UPSTREAM,
})


class HFInferenceError(Exception):
    """
    A Hugging Face call failed in a controlled, classified way.

    ``str(err)`` is safe to log: it contains the kind, the task and the HTTP
    status, never the token or the upstream body.
    """

    def __init__(self, kind: HFErrorKind, task: str, status_code: Optional[int] = None):
        self.kind = kind
        self.task = task
        self.status_code = status_code
        status = f" (HTTP {status_code})" if status_code else ""
        super().__init__(f"Hugging Face {task} failed: {kind.value}{status}")

    @property
    def transient(self) -> bool:
        return self.kind in TRANSIENT_KINDS


def get_hf_token() -> Optional[str]:
    """Return the server-side HF token, or None when not configured."""
    from app.core.config import settings

    secret = settings.hf_token
    if secret is None:
        return None
    value = secret.get_secret_value().strip()
    return value or None


def require_hf_token(task: str) -> str:
    token = get_hf_token()
    if not token:
        raise HFInferenceError(HFErrorKind.NOT_CONFIGURED, task)
    return token


def hf_configured() -> bool:
    return get_hf_token() is not None


def _status_to_kind(status: int) -> HFErrorKind:
    if status == 401:
        return HFErrorKind.AUTH
    if status == 403:
        return HFErrorKind.FORBIDDEN
    if status in (402, 429):
        return HFErrorKind.QUOTA
    if status in (404, 410, 503):
        return HFErrorKind.MODEL_UNAVAILABLE
    if status in (400, 413, 422):
        return HFErrorKind.BAD_REQUEST
    if status in (408, 504):
        return HFErrorKind.TIMEOUT
    return HFErrorKind.UPSTREAM


_NO_PROVIDER = "not supported by any provider"


def _is_transport(exc: BaseException, base_name: str) -> bool:
    """
    True when ``exc`` derives from an httpx-style class named ``base_name``.

    huggingface_hub 2.x ships its own vendored ``httpx2`` package, whose
    exception classes are distinct from ``httpx``'s, so match by class name
    within modules named httpx*.
    """
    return any(
        cls.__name__ == base_name and cls.__module__.split(".")[0].startswith("httpx")
        for cls in type(exc).__mro__
    )


def classify_exception(exc: BaseException, task: str) -> HFInferenceError:
    """Map any exception raised by an HF call to an ``HFInferenceError``."""
    if isinstance(exc, HFInferenceError):
        return exc

    message = str(exc).lower()
    # huggingface_hub wraps HTTP failures; its errors expose ``.response``.
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        if status == 400 and _NO_PROVIDER in message:
            # The router answers 400 when no enabled provider serves the model.
            return HFInferenceError(HFErrorKind.MODEL_UNAVAILABLE, task, status)
        return HFInferenceError(_status_to_kind(status), task, status)

    try:
        from huggingface_hub.errors import InferenceTimeoutError
        if isinstance(exc, InferenceTimeoutError):
            return HFInferenceError(HFErrorKind.TIMEOUT, task)
    except ImportError:  # pragma: no cover - huggingface_hub is a hard dependency
        pass

    if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or _is_transport(exc, "TimeoutException"):
        return HFInferenceError(HFErrorKind.TIMEOUT, task)
    if isinstance(exc, (httpx.TransportError, ConnectionError, OSError)) or _is_transport(exc, "TransportError"):
        return HFInferenceError(HFErrorKind.NETWORK, task)
    if isinstance(exc, (KeyError, IndexError, TypeError, ValueError, AttributeError)):
        return HFInferenceError(HFErrorKind.MALFORMED, task)

    if "no provider" in message or _NO_PROVIDER in message:
        return HFInferenceError(HFErrorKind.MODEL_UNAVAILABLE, task)
    return HFInferenceError(HFErrorKind.UPSTREAM, task)


def _timeout() -> float:
    from app.core.config import settings
    return settings.hf_timeout_seconds


def router_chat_client(async_: bool = True):
    """
    Client for chat completion through the HF router's OpenAI-compatible API.

    Provider routing is expressed in the model id suffix (``model:provider``,
    ``model:cheapest``, ``model:fastest``) so the app is never tied to one
    upstream vendor.
    """
    from huggingface_hub import AsyncInferenceClient, InferenceClient
    from app.core.config import settings

    token = require_hf_token("chat")
    cls = AsyncInferenceClient if async_ else InferenceClient
    return cls(base_url=settings.hf_router_url, api_key=token, timeout=_timeout())


def task_client(task: str, async_: bool = False, timeout: Optional[float] = None):
    """Client for task endpoints served by the ``hf-inference`` provider."""
    from huggingface_hub import AsyncInferenceClient, InferenceClient

    token = require_hf_token(task)
    cls = AsyncInferenceClient if async_ else InferenceClient
    return cls(provider="hf-inference", api_key=token, timeout=timeout or _timeout())
