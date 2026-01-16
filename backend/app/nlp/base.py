"""
Base classes and types for NLP providers.

Provides abstract interface for Arabic text analysis:
- Tokenization
- POS tagging
- Morphological analysis
- Root extraction
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NLPProvider(str, Enum):
    """Available NLP providers."""
    FARASA = "farasa"
    CAMEL = "camel"
    STANZA = "stanza"
    LLM = "llm"
    STATIC = "static"


@dataclass
class TokenResult:
    """Result of tokenizing/analyzing a single word."""
    word: str                           # Original Arabic word
    word_index: int                     # Position in sentence (0-indexed)
    lemma: Optional[str] = None         # Base form (lemma)
    root: Optional[str] = None          # Arabic root (جذر)
    pattern: Optional[str] = None       # Morphological pattern (وزن)
    pos: Optional[str] = None           # Part of speech (Arabic label)
    pos_english: Optional[str] = None   # POS in English (for mapping)
    features: Dict[str, str] = field(default_factory=dict)  # Additional features
    confidence: float = 1.0             # Confidence score (0-1)


@dataclass
class MorphologyResult:
    """Full morphological analysis result."""
    text: str                           # Original input text
    tokens: List[TokenResult]           # Token-by-token analysis
    provider: NLPProvider               # Which provider produced this
    latency_ms: int = 0                 # Processing time
    success: bool = True                # Whether analysis succeeded
    error: Optional[str] = None         # Error message if failed
    cached: bool = False                # Whether result came from cache


# Mapping from English POS tags to Arabic labels
# Used to normalize output from different providers
POS_ENGLISH_TO_ARABIC: Dict[str, str] = {
    # Nouns
    "noun": "اسم",
    "n": "اسم",
    "NOUN": "اسم",
    "proper_noun": "اسم علم",
    "PROPN": "اسم علم",
    "pronoun": "ضمير",
    "PRON": "ضمير",
    "demonstrative": "اسم إشارة",
    "DEM": "اسم إشارة",
    "relative": "اسم موصول",
    "REL": "اسم موصول",
    "interrogative_noun": "اسم استفهام",
    "masdar": "مصدر",
    "verbal_noun": "مصدر",
    # Verbs
    "verb": "فعل",
    "v": "فعل",
    "VERB": "فعل",
    "past_verb": "فعل ماض",
    "present_verb": "فعل مضارع",
    "imperative_verb": "فعل أمر",
    "IMP": "فعل أمر",
    # Particles
    "particle": "حرف",
    "PART": "حرف",
    "preposition": "حرف جر",
    "ADP": "حرف جر",
    "conjunction": "حرف عطف",
    "CONJ": "حرف عطف",
    "CCONJ": "حرف عطف",
    "SCONJ": "حرف عطف",
    "negation": "حرف نفي",
    "NEG": "حرف نفي",
    "interrogative_particle": "حرف استفهام",
    "conditional": "حرف شرط",
    "exception": "حرف استثناء",
    # Other
    "adjective": "صفة",
    "ADJ": "صفة",
    "adverb": "ظرف",
    "ADV": "ظرف",
    "punctuation": "علامة ترقيم",
    "PUNCT": "علامة ترقيم",
    "number": "عدد",
    "NUM": "عدد",
    "unknown": "غير محدد",
    "X": "غير محدد",
}


def normalize_pos_to_arabic(pos: str) -> str:
    """Convert English POS tag to Arabic label."""
    if not pos:
        return "غير محدد"
    # Check if already Arabic
    if any('\u0600' <= c <= '\u06FF' for c in pos):
        return pos
    # Normalize case and lookup
    return POS_ENGLISH_TO_ARABIC.get(pos, POS_ENGLISH_TO_ARABIC.get(pos.upper(), "غير محدد"))


class BaseNLPProvider(ABC):
    """Abstract base class for NLP providers."""

    provider_name: NLPProvider = NLPProvider.STATIC

    @abstractmethod
    async def tokenize(self, text: str) -> List[TokenResult]:
        """
        Tokenize Arabic text into words.

        Args:
            text: Arabic text to tokenize

        Returns:
            List of TokenResult with word positions
        """
        pass

    @abstractmethod
    async def pos_tag(self, text: str) -> List[TokenResult]:
        """
        Perform part-of-speech tagging.

        Args:
            text: Arabic text to analyze

        Returns:
            List of TokenResult with POS tags (Arabic labels)
        """
        pass

    @abstractmethod
    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """
        Full morphological analysis including root extraction.

        Args:
            text: Arabic text to analyze

        Returns:
            MorphologyResult with tokens, roots, patterns
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available and functional.

        Returns:
            True if provider is ready to use
        """
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider metadata for health reporting."""
        return {
            "name": self.provider_name.value,
            "available": False,  # Override in subclasses
        }


class StaticNLPProvider(BaseNLPProvider):
    """
    Static/fallback NLP provider using simple tokenization.

    Provides basic word splitting when other providers fail.
    Does not perform real morphological analysis.
    """

    provider_name = NLPProvider.STATIC

    async def tokenize(self, text: str) -> List[TokenResult]:
        """Simple whitespace tokenization."""
        words = text.split()
        return [
            TokenResult(
                word=word,
                word_index=i,
                confidence=0.5,  # Low confidence for static
            )
            for i, word in enumerate(words)
        ]

    async def pos_tag(self, text: str) -> List[TokenResult]:
        """Return tokens with unknown POS (no real analysis)."""
        tokens = await self.tokenize(text)
        for token in tokens:
            token.pos = "غير محدد"
            token.pos_english = "unknown"
        return tokens

    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """Return basic tokenization without morphology."""
        import time
        start = time.perf_counter()
        tokens = await self.pos_tag(text)
        latency = int((time.perf_counter() - start) * 1000)

        return MorphologyResult(
            text=text,
            tokens=tokens,
            provider=self.provider_name,
            latency_ms=latency,
            success=True,
        )

    async def health_check(self) -> bool:
        """Static provider is always available."""
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": self.provider_name.value,
            "available": True,
            "description": "Static fallback (no real analysis)",
        }
