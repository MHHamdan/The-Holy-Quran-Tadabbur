"""
NLP Fallback Chain Orchestrator.

Manages multiple NLP providers with graceful degradation:
1. Farasa (primary) - Best for Quranic Arabic
2. CAMeL Tools (secondary) - Good dialectal support
3. Stanza (fallback) - General Arabic
4. LLM (final) - Uses Ollama/Claude for analysis
5. Static (last resort) - Simple tokenization

Each provider is tried in order until one succeeds with
acceptable confidence. Results are cached using hybrid L1/L2
(in-memory + Redis) to avoid repeated analysis.
"""
import logging
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from app.nlp.base import (
    BaseNLPProvider,
    NLPProvider,
    TokenResult,
    MorphologyResult,
    StaticNLPProvider,
)
from app.nlp.providers.farasa import FarasaProvider
from app.nlp.providers.camel import CamelProvider
from app.nlp.providers.stanza import StanzaProvider

logger = logging.getLogger(__name__)


@dataclass
class ChainConfig:
    """Configuration for the NLP fallback chain."""
    min_confidence: float = 0.6  # Minimum confidence to accept result
    enable_farasa: bool = True
    enable_camel: bool = True
    enable_stanza: bool = True
    enable_llm: bool = True
    farasa_use_api: bool = False  # Use local library by default
    cache_results: bool = True


class LLMNLPProvider(BaseNLPProvider):
    """
    LLM-based NLP provider using existing grammar_ollama service.

    Uses the same LLM infrastructure as the grammar service
    but returns TokenResult format for chain compatibility.
    """

    provider_name = NLPProvider.LLM

    def __init__(self):
        self._is_available: Optional[bool] = None

    async def tokenize(self, text: str) -> List[TokenResult]:
        """Simple tokenization (LLM not needed for this)."""
        words = text.split()
        return [
            TokenResult(word=w, word_index=i, confidence=0.5)
            for i, w in enumerate(words)
        ]

    async def pos_tag(self, text: str) -> List[TokenResult]:
        """POS tagging using LLM via grammar service."""
        try:
            from app.services.grammar_ollama import GrammarService

            service = GrammarService()
            if not await service.health_check():
                tokens = await self.tokenize(text)
                for t in tokens:
                    t.pos = "غير محدد"
                return tokens

            # Use grammar service for analysis
            analysis = await service.analyze(text)

            tokens = []
            for i, token_data in enumerate(analysis.tokens):
                tokens.append(TokenResult(
                    word=token_data.word,
                    word_index=i,
                    pos=token_data.pos.value if hasattr(token_data.pos, 'value') else str(token_data.pos),
                    root=token_data.root,
                    pattern=token_data.pattern,
                    confidence=token_data.confidence,
                ))

            return tokens

        except Exception as e:
            logger.error(f"LLM POS tagging error: {e}")
            tokens = await self.tokenize(text)
            for t in tokens:
                t.pos = "غير محدد"
            return tokens

    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """Full analysis using LLM."""
        import time
        start = time.perf_counter()

        try:
            tokens = await self.pos_tag(text)
            latency = int((time.perf_counter() - start) * 1000)

            return MorphologyResult(
                text=text,
                tokens=tokens,
                provider=self.provider_name,
                latency_ms=latency,
                success=True,
            )

        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return MorphologyResult(
                text=text,
                tokens=[],
                provider=self.provider_name,
                latency_ms=latency,
                success=False,
                error=str(e),
            )

    async def health_check(self) -> bool:
        """Check if LLM is available."""
        if self._is_available is not None:
            return self._is_available

        try:
            from app.services.grammar_ollama import GrammarService
            service = GrammarService()
            self._is_available = await service.health_check()
        except Exception:
            self._is_available = False

        return self._is_available

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": self.provider_name.value,
            "available": self._is_available or False,
            "description": "LLM-based analysis (Ollama/Qwen2.5)",
        }


class NLPFallbackChain:
    """
    Orchestrates multiple NLP providers with fallback logic.

    Tries providers in order of quality/specialization:
    1. Farasa - Optimized for MSA/Quranic Arabic
    2. CAMeL - Good general Arabic with dialectal support
    3. Stanza - Neural models, slower but robust
    4. LLM - Uses existing grammar_ollama service
    5. Static - Simple tokenization (always available)

    Results are cached using hybrid L1/L2 caching (in-memory + Redis)
    to avoid repeated expensive NLP operations.
    """

    def __init__(self, config: ChainConfig = None):
        self.config = config or ChainConfig()
        self._providers: List[BaseNLPProvider] = []
        self._initialized = False
        self._cache = None

        # Initialize hybrid cache if caching enabled
        if self.config.cache_results:
            try:
                from app.services.redis_cache import get_hybrid_cache
                self._cache = get_hybrid_cache()
            except Exception as e:
                logger.warning(f"Failed to initialize NLP cache: {e}")

    def _init_providers(self):
        """Initialize providers based on config."""
        if self._initialized:
            return

        if self.config.enable_farasa:
            self._providers.append(FarasaProvider(
                use_api=self.config.farasa_use_api
            ))

        if self.config.enable_camel:
            self._providers.append(CamelProvider())

        if self.config.enable_stanza:
            self._providers.append(StanzaProvider())

        if self.config.enable_llm:
            self._providers.append(LLMNLPProvider())

        # Static is always available as last resort
        self._providers.append(StaticNLPProvider())

        self._initialized = True
        logger.info(f"NLP chain initialized with {len(self._providers)} providers")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for NLP analysis."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"nlp:analysis:{text_hash}"

    async def _get_cached(self, text: str) -> Optional[MorphologyResult]:
        """Get cached analysis result."""
        if not self._cache:
            return None

        try:
            cache_key = self._get_cache_key(text)
            cached = await self._cache.get(cache_key)
            if cached:
                # Reconstruct MorphologyResult from cached dict
                tokens = [TokenResult(**t) for t in cached.get("tokens", [])]
                return MorphologyResult(
                    text=cached.get("text", text),
                    tokens=tokens,
                    provider=NLPProvider(cached.get("provider", "static")),
                    latency_ms=0,  # Cached, so no latency
                    success=cached.get("success", True),
                    error=cached.get("error"),
                    cached=True,
                )
        except Exception as e:
            logger.debug(f"NLP cache get error: {e}")
        return None

    async def _set_cached(self, text: str, result: MorphologyResult) -> None:
        """Cache analysis result."""
        if not self._cache or not result.success:
            return

        try:
            cache_key = self._get_cache_key(text)
            cache_value = {
                "text": result.text,
                "tokens": [
                    {
                        "word": t.word,
                        "word_index": t.word_index,
                        "pos": t.pos,
                        "pos_english": t.pos_english,
                        "root": t.root,
                        "pattern": t.pattern,
                        "confidence": t.confidence,
                    }
                    for t in result.tokens
                ],
                "provider": result.provider.value,
                "success": result.success,
                "error": result.error,
            }
            # L1: 5 min, L2: 1 hour (NLP results are stable)
            await self._cache.set(cache_key, cache_value, l1_ttl=300, l2_ttl=3600)
        except Exception as e:
            logger.debug(f"NLP cache set error: {e}")

    async def analyze(self, text: str) -> MorphologyResult:
        """
        Analyze text using the fallback chain.

        Checks cache first, then tries each provider in order
        until one succeeds with acceptable confidence.

        Args:
            text: Arabic text to analyze

        Returns:
            MorphologyResult from cache or first successful provider
        """
        self._init_providers()

        # Check cache first
        cached_result = await self._get_cached(text)
        if cached_result:
            logger.debug(f"NLP cache hit for text (hash: {self._get_cache_key(text)[-8:]})")
            return cached_result

        for provider in self._providers:
            try:
                # Check if provider is available
                if not await provider.health_check():
                    logger.debug(f"Provider {provider.provider_name.value} not available, skipping")
                    continue

                # Try analysis
                result = await provider.morphological_analysis(text)

                if not result.success:
                    logger.debug(f"Provider {provider.provider_name.value} failed: {result.error}")
                    continue

                # Check confidence
                if result.tokens:
                    avg_confidence = sum(t.confidence for t in result.tokens) / len(result.tokens)
                    if avg_confidence < self.config.min_confidence:
                        logger.debug(
                            f"Provider {provider.provider_name.value} confidence {avg_confidence:.2f} "
                            f"< {self.config.min_confidence}, trying next"
                        )
                        continue

                logger.info(
                    f"NLP analysis successful with {provider.provider_name.value} "
                    f"({len(result.tokens)} tokens, {result.latency_ms}ms)"
                )

                # Cache successful result
                await self._set_cached(text, result)

                return result

            except Exception as e:
                logger.warning(f"Provider {provider.provider_name.value} error: {e}")
                continue

        # Should never reach here due to static fallback
        logger.error("All NLP providers failed")
        return MorphologyResult(
            text=text,
            tokens=[],
            provider=NLPProvider.STATIC,
            success=False,
            error="All providers failed",
        )

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers."""
        self._init_providers()

        status = {
            "chain_size": len(self._providers),
            "providers": [],
        }

        for provider in self._providers:
            available = await provider.health_check()
            info = provider.get_provider_info()
            info["available"] = available
            status["providers"].append(info)

        # Overall status
        available_count = sum(1 for p in status["providers"] if p["available"])
        status["available_count"] = available_count
        status["status"] = "ok" if available_count > 1 else "degraded" if available_count == 1 else "unavailable"

        return status


# Singleton instance
_chain_instance: Optional[NLPFallbackChain] = None


def get_nlp_chain(config: ChainConfig = None) -> NLPFallbackChain:
    """
    Get the NLP fallback chain instance.

    Uses singleton pattern for efficiency.

    Args:
        config: Optional config to use (only on first call)

    Returns:
        NLPFallbackChain instance
    """
    global _chain_instance

    if _chain_instance is None:
        _chain_instance = NLPFallbackChain(config)

    return _chain_instance


async def test_nlp_chain() -> Dict[str, Any]:
    """
    Test the NLP chain with sample Arabic text.

    Returns diagnostic information about each provider.
    """
    chain = get_nlp_chain()

    test_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

    result = {
        "test_text": test_text,
        "health_status": await chain.get_health_status(),
        "analysis": None,
    }

    try:
        analysis = await chain.analyze(test_text)
        result["analysis"] = {
            "provider": analysis.provider.value,
            "success": analysis.success,
            "token_count": len(analysis.tokens),
            "latency_ms": analysis.latency_ms,
            "tokens": [
                {
                    "word": t.word,
                    "pos": t.pos,
                    "root": t.root,
                    "confidence": t.confidence,
                }
                for t in analysis.tokens[:5]  # First 5 tokens
            ],
        }
    except Exception as e:
        result["analysis"] = {"error": str(e)}

    return result
