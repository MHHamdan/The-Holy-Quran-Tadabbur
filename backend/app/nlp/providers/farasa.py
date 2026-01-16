"""
Farasa NLP Provider for Arabic text analysis.

Farasa is optimized for Modern Standard Arabic and Quranic text.
Supports both REST API and local farasapy library.

Installation:
    pip install farasapy

Or use the QCRI REST API (requires internet):
    https://farasa.qcri.org/webapi/
"""
import time
import logging
from typing import List, Optional, Dict, Any
import httpx

from app.nlp.base import (
    BaseNLPProvider,
    NLPProvider,
    TokenResult,
    MorphologyResult,
    normalize_pos_to_arabic,
)

logger = logging.getLogger(__name__)

# Farasa POS tag mapping to Arabic
FARASA_POS_MAP: Dict[str, str] = {
    # Nouns
    "NOUN": "اسم",
    "NOUN_PROP": "اسم علم",
    "NOUN_NUM": "عدد",
    "NOUN_QUANT": "اسم",
    "NOUN_VN": "مصدر",
    "PRON": "ضمير",
    "PRON_DEM": "اسم إشارة",
    "PRON_REL": "اسم موصول",
    "PRON_INTERROG": "اسم استفهام",
    # Verbs
    "V": "فعل",
    "VERB": "فعل",
    "VERB_PAST": "فعل ماض",
    "VERB_PRES": "فعل مضارع",
    "VERB_IMP": "فعل أمر",
    "IV": "فعل مضارع",
    "PV": "فعل ماض",
    "CV": "فعل أمر",
    # Particles
    "PART": "حرف",
    "PREP": "حرف جر",
    "CONJ": "حرف عطف",
    "CONJ_SUB": "حرف عطف",
    "NEG": "حرف نفي",
    "INTERROG": "حرف استفهام",
    "COND": "حرف شرط",
    "EXCEPT": "حرف استثناء",
    # Adjectives/Adverbs
    "ADJ": "صفة",
    "ADJ_COMP": "صفة",
    "ADJ_NUM": "عدد",
    "ADV": "ظرف",
    # Other
    "ABBREV": "اختصار",
    "PUNC": "علامة ترقيم",
    "FOREIGN": "أجنبي",
    "DET": "أداة تعريف",
    "EMOT": "رمز",
}


class FarasaProvider(BaseNLPProvider):
    """
    Farasa NLP provider for Arabic morphological analysis.

    Supports two modes:
    1. Local library (farasapy) - default, no network needed
    2. REST API - uses QCRI web service

    Args:
        use_api: If True, use REST API instead of local library
        api_url: Custom API URL (default: QCRI public API)
        timeout: Request timeout in seconds
    """

    provider_name = NLPProvider.FARASA

    def __init__(
        self,
        use_api: bool = False,
        api_url: str = "https://farasa.qcri.org/webapi",
        timeout: float = 30.0,
    ):
        self.use_api = use_api
        self.api_url = api_url
        self.timeout = timeout
        self._segmenter = None
        self._pos_tagger = None
        self._is_available: Optional[bool] = None

    def _init_local_library(self) -> bool:
        """Initialize local farasapy library."""
        if self._segmenter is not None:
            return True

        try:
            from farasapy import FarasaSegmenter, FarasaPOSTagger
            self._segmenter = FarasaSegmenter(interactive=True)
            self._pos_tagger = FarasaPOSTagger(interactive=True)
            logger.info("Farasa local library initialized successfully")
            return True
        except ImportError:
            logger.warning("farasapy not installed. Use: pip install farasapy")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Farasa: {e}")
            return False

    async def _call_api(self, endpoint: str, text: str) -> Dict[str, Any]:
        """Call Farasa REST API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/{endpoint}",
                data={"text": text},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def tokenize(self, text: str) -> List[TokenResult]:
        """Tokenize Arabic text using Farasa segmenter."""
        if self.use_api:
            try:
                result = await self._call_api("segmentation", text)
                words = result.get("text", text).split()
            except Exception as e:
                logger.error(f"Farasa API segmentation error: {e}")
                words = text.split()
        else:
            if not self._init_local_library():
                words = text.split()
            else:
                try:
                    segmented = self._segmenter.segment(text)
                    words = segmented.split()
                except Exception as e:
                    logger.error(f"Farasa segmentation error: {e}")
                    words = text.split()

        return [
            TokenResult(
                word=word.replace("+", ""),  # Remove morpheme markers
                word_index=i,
                confidence=0.9,
            )
            for i, word in enumerate(words)
        ]

    async def pos_tag(self, text: str) -> List[TokenResult]:
        """POS tagging using Farasa."""
        start = time.perf_counter()

        if self.use_api:
            try:
                result = await self._call_api("postagger", text)
                tagged_text = result.get("text", "")
                tokens = self._parse_pos_output(tagged_text)
            except Exception as e:
                logger.error(f"Farasa API POS error: {e}")
                tokens = await self.tokenize(text)
                for t in tokens:
                    t.pos = "غير محدد"
        else:
            if not self._init_local_library():
                tokens = await self.tokenize(text)
                for t in tokens:
                    t.pos = "غير محدد"
            else:
                try:
                    tagged = self._pos_tagger.tag(text)
                    tokens = self._parse_pos_output(tagged)
                except Exception as e:
                    logger.error(f"Farasa POS error: {e}")
                    tokens = await self.tokenize(text)
                    for t in tokens:
                        t.pos = "غير محدد"

        latency = int((time.perf_counter() - start) * 1000)
        logger.debug(f"Farasa POS tagging took {latency}ms for {len(tokens)} tokens")
        return tokens

    def _parse_pos_output(self, tagged: str) -> List[TokenResult]:
        """Parse Farasa POS tagger output (word/TAG format)."""
        tokens = []
        parts = tagged.split()
        for i, part in enumerate(parts):
            if "/" in part:
                word, tag = part.rsplit("/", 1)
            else:
                word = part
                tag = "NOUN"  # Default

            pos_arabic = FARASA_POS_MAP.get(tag, normalize_pos_to_arabic(tag))

            tokens.append(TokenResult(
                word=word,
                word_index=i,
                pos=pos_arabic,
                pos_english=tag,
                confidence=0.85,
            ))

        return tokens

    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """Full morphological analysis with Farasa."""
        start = time.perf_counter()

        try:
            # Get POS tags first
            tokens = await self.pos_tag(text)

            # If using local library, try to get roots
            if not self.use_api and self._init_local_library():
                try:
                    from farasapy import FarasaStemmer
                    stemmer = FarasaStemmer(interactive=True)
                    stems = stemmer.stem(text).split()

                    # Add stems as roots to tokens
                    for i, token in enumerate(tokens):
                        if i < len(stems):
                            token.root = stems[i]
                except Exception as e:
                    logger.warning(f"Farasa stemming error: {e}")

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
            logger.error(f"Farasa morphology analysis error: {e}")
            return MorphologyResult(
                text=text,
                tokens=[],
                provider=self.provider_name,
                latency_ms=latency,
                success=False,
                error=str(e),
            )

    async def health_check(self) -> bool:
        """Check if Farasa is available."""
        if self._is_available is not None:
            return self._is_available

        if self.use_api:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.api_url}/")
                    self._is_available = response.status_code < 500
            except Exception:
                self._is_available = False
        else:
            self._is_available = self._init_local_library()

        return self._is_available

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": self.provider_name.value,
            "available": self._is_available or False,
            "mode": "api" if self.use_api else "local",
            "api_url": self.api_url if self.use_api else None,
            "description": "Farasa Arabic NLP (QCRI)",
        }
