"""
NLP Provider abstraction for Arabic grammar analysis.

Supports multiple NLP backends with graceful fallback:
- Farasa (primary, Quranic Arabic optimized)
- CAMeL Tools (secondary, dialectal support)
- Stanza (fallback, general Arabic)
- LLM (final fallback via Ollama)
"""
from app.nlp.base import (
    NLPProvider,
    TokenResult,
    MorphologyResult,
    BaseNLPProvider,
)
from app.nlp.fallback_chain import NLPFallbackChain, get_nlp_chain

__all__ = [
    "NLPProvider",
    "TokenResult",
    "MorphologyResult",
    "BaseNLPProvider",
    "NLPFallbackChain",
    "get_nlp_chain",
]
