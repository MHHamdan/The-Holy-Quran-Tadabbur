"""
LLM Provider abstraction for RAG response generation.

Supports both Claude API (Anthropic) and local Ollama models.
This allows cost-effective local inference with Qwen2.5 while
maintaining the option to use Claude for production.
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import time
import logging
import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    CLAUDE = "claude"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: Optional[int] = None
    latency_ms: int = 0


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is available."""
        pass


class OllamaLLM(BaseLLM):
    """
    Local Ollama LLM provider.

    Optimized for Qwen2.5:32b on multi-GPU setup.
    Uses lower temperature for factual responses.
    """

    def __init__(
        self,
        model: str = "qwen2.5:32b",
        base_url: str = "http://localhost:11434",
        timeout: float = 180.0,  # 3 minutes for large models
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """
        Generate response using Ollama API.

        Uses the /api/chat endpoint for proper system/user message handling.
        """
        start_time = time.perf_counter()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "top_p": 0.9,
                            "repeat_penalty": 1.1,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()

                latency_ms = int((time.perf_counter() - start_time) * 1000)

                return LLMResponse(
                    content=data["message"]["content"],
                    model=self.model,
                    provider=LLMProvider.OLLAMA,
                    tokens_used=data.get("eval_count"),
                    latency_ms=latency_ms,
                )

            except httpx.TimeoutException:
                logger.error(f"Ollama request timed out after {self.timeout}s")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Ollama error: {e}")
                raise

    async def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return self.model in models
                return False
        except Exception:
            return False


class ClaudeLLM(BaseLLM):
    """
    Anthropic Claude API provider.

    Uses the official anthropic SDK for API calls.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Generate response using Claude API."""
        start_time = time.perf_counter()

        try:
            # Note: anthropic SDK is sync, but we can use it in async context
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            latency_ms = int((time.perf_counter() - start_time) * 1000)

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider=LLMProvider.CLAUDE,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Claude API is accessible."""
        try:
            # Simple validation - just check if key format is valid
            return bool(self.client.api_key and len(self.client.api_key) > 10)
        except Exception:
            return False


def get_llm(
    provider: LLMProvider = None,
    ollama_model: str = None,
    ollama_base_url: str = None,
) -> BaseLLM:
    """
    Factory function to get the configured LLM provider.

    Reads from settings if parameters not provided.
    Defaults to Ollama for cost-effective local inference.
    """
    from app.core.config import settings

    # Determine provider
    if provider is None:
        provider_str = getattr(settings, 'llm_provider', 'ollama')
        provider = LLMProvider(provider_str)

    if provider == LLMProvider.OLLAMA:
        return OllamaLLM(
            model=ollama_model or getattr(settings, 'ollama_model', 'qwen2.5:32b'),
            base_url=ollama_base_url or getattr(settings, 'ollama_base_url', 'http://localhost:11434'),
        )

    elif provider == LLMProvider.CLAUDE:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        return ClaudeLLM(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


async def test_ollama_connection(model: str = "qwen2.5:32b") -> dict:
    """
    Test Ollama connection and model availability.

    Returns status information for diagnostics.
    """
    llm = OllamaLLM(model=model)

    result = {
        "provider": "ollama",
        "model": model,
        "available": False,
        "response_test": None,
        "latency_ms": None,
    }

    # Check if model is available
    if not await llm.health_check():
        result["error"] = f"Model {model} not found in Ollama"
        return result

    result["available"] = True

    # Test with a simple prompt
    try:
        response = await llm.generate(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Bismillah' in Arabic and English. Keep it brief.",
            max_tokens=100,
        )
        result["response_test"] = response.content[:200]
        result["latency_ms"] = response.latency_ms
        result["tokens_used"] = response.tokens_used
    except Exception as e:
        result["error"] = str(e)

    return result
