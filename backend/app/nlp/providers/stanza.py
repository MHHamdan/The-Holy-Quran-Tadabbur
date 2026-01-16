"""
Stanza NLP Provider for Arabic text analysis.

Stanza is Stanford's Python NLP library with neural models.
Provides general Arabic support as a fallback when specialized
tools (Farasa, CAMeL) are unavailable.

Installation:
    pip install stanza
    python -c "import stanza; stanza.download('ar')"

Documentation:
    https://stanfordnlp.github.io/stanza/
"""
import time
import logging
from typing import List, Optional, Dict, Any

from app.nlp.base import (
    BaseNLPProvider,
    NLPProvider,
    TokenResult,
    MorphologyResult,
    normalize_pos_to_arabic,
)

logger = logging.getLogger(__name__)

# Universal Dependencies POS tag mapping to Arabic
UD_POS_MAP: Dict[str, str] = {
    # Universal POS tags
    "NOUN": "اسم",
    "PROPN": "اسم علم",
    "PRON": "ضمير",
    "VERB": "فعل",
    "AUX": "فعل مساعد",
    "ADJ": "صفة",
    "ADV": "ظرف",
    "ADP": "حرف جر",
    "CCONJ": "حرف عطف",
    "SCONJ": "حرف عطف",
    "DET": "أداة تعريف",
    "NUM": "عدد",
    "PART": "حرف",
    "INTJ": "اسم صوت",
    "PUNCT": "علامة ترقيم",
    "SYM": "رمز",
    "X": "غير محدد",
}


class StanzaProvider(BaseNLPProvider):
    """
    Stanza NLP provider as general Arabic fallback.

    Uses Stanford's neural NLP models for Arabic.
    Slower but more accurate than rule-based systems.

    Args:
        processors: Stanza processors to load (default: tokenize,pos,lemma)
        use_gpu: Whether to use GPU acceleration if available
    """

    provider_name = NLPProvider.STANZA

    def __init__(
        self,
        processors: str = "tokenize,pos,lemma",
        use_gpu: bool = False,
    ):
        self.processors = processors
        self.use_gpu = use_gpu
        self._nlp = None
        self._is_available: Optional[bool] = None

    def _init_library(self) -> bool:
        """Initialize Stanza library with Arabic model."""
        if self._nlp is not None:
            return True

        try:
            import stanza

            # Download model if needed (only once)
            try:
                stanza.download("ar", processors=self.processors, verbose=False)
            except Exception:
                pass  # Model already downloaded

            # Initialize pipeline
            self._nlp = stanza.Pipeline(
                "ar",
                processors=self.processors,
                use_gpu=self.use_gpu,
                verbose=False,
            )

            logger.info("Stanza Arabic model initialized successfully")
            return True

        except ImportError:
            logger.warning("stanza not installed. Use: pip install stanza")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Stanza: {e}")
            return False

    async def tokenize(self, text: str) -> List[TokenResult]:
        """Tokenize Arabic text using Stanza."""
        if not self._init_library():
            words = text.split()
            return [
                TokenResult(word=w, word_index=i, confidence=0.5)
                for i, w in enumerate(words)
            ]

        try:
            doc = self._nlp(text)
            tokens = []
            idx = 0
            for sentence in doc.sentences:
                for word in sentence.words:
                    tokens.append(TokenResult(
                        word=word.text,
                        word_index=idx,
                        lemma=word.lemma,
                        confidence=0.8,
                    ))
                    idx += 1
            return tokens

        except Exception as e:
            logger.error(f"Stanza tokenization error: {e}")
            words = text.split()
            return [
                TokenResult(word=w, word_index=i, confidence=0.5)
                for i, w in enumerate(words)
            ]

    async def pos_tag(self, text: str) -> List[TokenResult]:
        """POS tagging using Stanza."""
        start = time.perf_counter()

        if not self._init_library():
            tokens = await self.tokenize(text)
            for t in tokens:
                t.pos = "غير محدد"
            return tokens

        try:
            doc = self._nlp(text)
            tokens = []
            idx = 0

            for sentence in doc.sentences:
                for word in sentence.words:
                    pos_tag = word.upos or "X"
                    pos_arabic = UD_POS_MAP.get(pos_tag, normalize_pos_to_arabic(pos_tag))

                    # Extract features from morphological features
                    features = {}
                    if word.feats:
                        for feat in word.feats.split("|"):
                            if "=" in feat:
                                k, v = feat.split("=", 1)
                                features[k] = v

                    tokens.append(TokenResult(
                        word=word.text,
                        word_index=idx,
                        pos=pos_arabic,
                        pos_english=pos_tag,
                        lemma=word.lemma,
                        features=features,
                        confidence=0.8,
                    ))
                    idx += 1

            latency = int((time.perf_counter() - start) * 1000)
            logger.debug(f"Stanza POS tagging took {latency}ms for {len(tokens)} tokens")
            return tokens

        except Exception as e:
            logger.error(f"Stanza POS tagging error: {e}")
            tokens = await self.tokenize(text)
            for t in tokens:
                t.pos = "غير محدد"
            return tokens

    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """Full morphological analysis with Stanza."""
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
            logger.error(f"Stanza morphology analysis error: {e}")
            return MorphologyResult(
                text=text,
                tokens=[],
                provider=self.provider_name,
                latency_ms=latency,
                success=False,
                error=str(e),
            )

    async def health_check(self) -> bool:
        """Check if Stanza is available."""
        if self._is_available is not None:
            return self._is_available

        self._is_available = self._init_library()
        return self._is_available

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": self.provider_name.value,
            "available": self._is_available or False,
            "processors": self.processors,
            "use_gpu": self.use_gpu,
            "description": "Stanza Arabic NLP (Stanford)",
        }
