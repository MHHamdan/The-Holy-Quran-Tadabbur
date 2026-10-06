"""
LLM generation through Hugging Face Inference Providers.

Hugging Face is the only LLM platform. ``BaseLLM`` is kept as a thin seam so
tests (and the verification assistant) can inject a fake model without
network access; production always uses ``HuggingFaceLLM``.

Requests go to the HF router's OpenAI-compatible chat endpoint. The model id
carries the provider-routing suffix (``model:cheapest``, ``model:novita``…),
so the app is not tied to a single upstream vendor and the model stays
environment-configurable (``HF_LLM_MODEL`` / ``HF_LLM_PROVIDER``).

Failures surface as ``HFInferenceError`` with a controlled ``kind``; callers
map that to their own user-facing error. Upstream response bodies and the
token never leave this module.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.ai.hf_client import (
    HFErrorKind,
    HFInferenceError,
    classify_exception,
    hf_configured,
    router_chat_client,
)

logger = logging.getLogger(__name__)

PROVIDER_NAME = "huggingface"

# Reasoning models may emit a hidden chain of thought; it must never reach users.
_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    provider: str = PROVIDER_NAME
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: int = 0
    # Upstream inference provider that served the request, when reported.
    upstream_provider: Optional[str] = None
    finish_reason: Optional[str] = None


class BaseLLM(ABC):
    """Interface for chat-style generation."""

    model: str = ""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a response. Raises ``HFInferenceError`` on failure."""

    @abstractmethod
    async def health_check(self) -> bool:
        """True when the provider is configured (no paid call is made)."""


class HuggingFaceLLM(BaseLLM):
    """Chat generation via HF Inference Providers (router, OpenAI-compatible)."""

    def __init__(
        self,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 1,
    ):
        from app.core.config import settings

        self.model = model or settings.hf_llm_model_id
        self.timeout = timeout or settings.hf_timeout_seconds
        self.max_retries = max_retries

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> LLMResponse:
        start = time.perf_counter()
        # System and user content stay in separate messages so retrieved
        # source text can never be promoted to system-level instructions.
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs = dict(
            messages=messages,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        attempt = 0
        while True:
            attempt += 1
            try:
                async with router_chat_client(async_=True) as client:
                    output = await asyncio.wait_for(
                        client.chat_completion(**kwargs), timeout=self.timeout
                    )
                return self._to_response(output, start)
            except Exception as exc:  # noqa: BLE001 - classified below
                if isinstance(exc, asyncio.TimeoutError):
                    err = HFInferenceError(HFErrorKind.TIMEOUT, "chat")
                else:
                    err = classify_exception(exc, "chat")
                # json_mode is optional for some providers — retry once without it.
                if json_mode and err.kind == HFErrorKind.BAD_REQUEST and "response_format" in kwargs:
                    kwargs.pop("response_format")
                    continue
                retryable = err.kind in (HFErrorKind.NETWORK, HFErrorKind.UPSTREAM)
                if retryable and attempt <= self.max_retries:
                    await asyncio.sleep(0.5 * attempt)
                    continue
                logger.warning("LLM generation failed: %s (model=%s)", err, self.model)
                raise err from None

    def _to_response(self, output, start: float) -> LLMResponse:
        try:
            choice = output.choices[0]
            content = choice.message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise HFInferenceError(HFErrorKind.MALFORMED, "chat") from exc
        if not isinstance(content, str) or not content.strip():
            raise HFInferenceError(HFErrorKind.MALFORMED, "chat")

        content = _THINK_BLOCK.sub("", content).strip()
        if not content:
            raise HFInferenceError(HFErrorKind.MALFORMED, "chat")

        usage = getattr(output, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total = getattr(usage, "total_tokens", None)
        if total is None and prompt_tokens is not None and completion_tokens is not None:
            total = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            model=getattr(output, "model", None) or self.model,
            tokens_used=total,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=int((time.perf_counter() - start) * 1000),
            upstream_provider=getattr(output, "provider", None),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def health_check(self) -> bool:
        return hf_configured()


def get_llm(model: Optional[str] = None) -> BaseLLM:
    """Return the configured LLM (Hugging Face)."""
    return HuggingFaceLLM(model=model)


def llm_configured() -> bool:
    """True when the server has an HF token. Makes no network call."""
    return hf_configured()
