"""
CAMeL Tools NLP Provider for Arabic text analysis.

CAMeL Tools provides comprehensive Arabic NLP including:
- Morphological analysis
- POS tagging
- Dialectal Arabic support
- Disambiguation

Installation:
    pip install camel-tools
    camel_data -i disambig-mle-calima-msa-r13

Documentation:
    https://camel-tools.readthedocs.io/
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

# CAMeL POS tag mapping to Arabic
CAMEL_POS_MAP: Dict[str, str] = {
    # Nouns
    "noun": "اسم",
    "noun_prop": "اسم علم",
    "noun_num": "عدد",
    "noun_quant": "اسم",
    "pron": "ضمير",
    "pron_dem": "اسم إشارة",
    "pron_rel": "اسم موصول",
    "pron_interrog": "اسم استفهام",
    # Verbs
    "verb": "فعل",
    "verb_pseudo": "فعل",
    # Particles
    "part": "حرف",
    "part_neg": "حرف نفي",
    "part_interrog": "حرف استفهام",
    "part_voc": "حرف نداء",
    "part_det": "أداة تعريف",
    "prep": "حرف جر",
    "conj": "حرف عطف",
    "conj_sub": "حرف عطف",
    # Adjectives/Adverbs
    "adj": "صفة",
    "adj_comp": "صفة",
    "adj_num": "عدد",
    "adv": "ظرف",
    "adv_interrog": "ظرف استفهام",
    "adv_rel": "ظرف موصول",
    # Other
    "abbrev": "اختصار",
    "punc": "علامة ترقيم",
    "digit": "رقم",
    "foreign": "أجنبي",
    "interj": "اسم صوت",
}


class CamelProvider(BaseNLPProvider):
    """
    CAMeL Tools NLP provider for Arabic analysis.

    Uses the CAMeL Tools library for morphological analysis.
    Requires downloading models via camel_data command.

    Args:
        model: Analyzer model to use (default: calima-msa-r13)
        use_disambiguator: Use MLE disambiguator for better accuracy
    """

    provider_name = NLPProvider.CAMEL

    def __init__(
        self,
        model: str = "calima-msa-r13",
        use_disambiguator: bool = True,
    ):
        self.model = model
        self.use_disambiguator = use_disambiguator
        self._analyzer = None
        self._disambiguator = None
        self._is_available: Optional[bool] = None

    def _init_library(self) -> bool:
        """Initialize CAMeL Tools library."""
        if self._analyzer is not None:
            return True

        try:
            from camel_tools.morphology.database import MorphologyDB
            from camel_tools.morphology.analyzer import Analyzer

            # Load morphology database
            db = MorphologyDB.builtin_db()
            self._analyzer = Analyzer(db)

            # Optionally load disambiguator
            if self.use_disambiguator:
                try:
                    from camel_tools.disambig.mle import MLEDisambiguator
                    self._disambiguator = MLEDisambiguator.pretrained()
                except Exception as e:
                    logger.warning(f"CAMeL disambiguator not available: {e}")

            logger.info("CAMeL Tools initialized successfully")
            return True

        except ImportError:
            logger.warning("camel-tools not installed. Use: pip install camel-tools")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize CAMeL Tools: {e}")
            return False

    async def tokenize(self, text: str) -> List[TokenResult]:
        """Tokenize Arabic text using CAMeL Tools."""
        if not self._init_library():
            # Fallback to simple tokenization
            words = text.split()
            return [
                TokenResult(word=w, word_index=i, confidence=0.5)
                for i, w in enumerate(words)
            ]

        try:
            from camel_tools.tokenizers.word import simple_word_tokenize
            words = simple_word_tokenize(text)
            return [
                TokenResult(word=w, word_index=i, confidence=0.9)
                for i, w in enumerate(words)
            ]
        except Exception as e:
            logger.error(f"CAMeL tokenization error: {e}")
            words = text.split()
            return [
                TokenResult(word=w, word_index=i, confidence=0.5)
                for i, w in enumerate(words)
            ]

    async def pos_tag(self, text: str) -> List[TokenResult]:
        """POS tagging using CAMeL Tools."""
        start = time.perf_counter()

        if not self._init_library():
            tokens = await self.tokenize(text)
            for t in tokens:
                t.pos = "غير محدد"
            return tokens

        try:
            from camel_tools.tokenizers.word import simple_word_tokenize

            words = simple_word_tokenize(text)
            tokens = []

            if self._disambiguator:
                # Use disambiguator for better accuracy
                disamb_result = self._disambiguator.disambiguate(words)
                for i, (word, analysis) in enumerate(zip(words, disamb_result)):
                    if analysis.analyses:
                        best = analysis.analyses[0]
                        pos_tag = best.get("pos", "noun")
                        root = best.get("root", None)
                        pattern = best.get("form_gen", None)
                    else:
                        pos_tag = "noun"
                        root = None
                        pattern = None

                    pos_arabic = CAMEL_POS_MAP.get(
                        pos_tag.lower(),
                        normalize_pos_to_arabic(pos_tag)
                    )

                    tokens.append(TokenResult(
                        word=word,
                        word_index=i,
                        pos=pos_arabic,
                        pos_english=pos_tag,
                        root=root,
                        pattern=pattern,
                        confidence=0.85,
                    ))
            else:
                # Use analyzer without disambiguation
                for i, word in enumerate(words):
                    analyses = self._analyzer.analyze(word)
                    if analyses:
                        best = analyses[0]
                        pos_tag = best.get("pos", "noun")
                        root = best.get("root", None)
                    else:
                        pos_tag = "noun"
                        root = None

                    pos_arabic = CAMEL_POS_MAP.get(
                        pos_tag.lower(),
                        normalize_pos_to_arabic(pos_tag)
                    )

                    tokens.append(TokenResult(
                        word=word,
                        word_index=i,
                        pos=pos_arabic,
                        pos_english=pos_tag,
                        root=root,
                        confidence=0.75,
                    ))

            latency = int((time.perf_counter() - start) * 1000)
            logger.debug(f"CAMeL POS tagging took {latency}ms for {len(tokens)} tokens")
            return tokens

        except Exception as e:
            logger.error(f"CAMeL POS tagging error: {e}")
            tokens = await self.tokenize(text)
            for t in tokens:
                t.pos = "غير محدد"
            return tokens

    async def morphological_analysis(self, text: str) -> MorphologyResult:
        """Full morphological analysis with CAMeL Tools."""
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
            logger.error(f"CAMeL morphology analysis error: {e}")
            return MorphologyResult(
                text=text,
                tokens=[],
                provider=self.provider_name,
                latency_ms=latency,
                success=False,
                error=str(e),
            )

    async def health_check(self) -> bool:
        """Check if CAMeL Tools is available."""
        if self._is_available is not None:
            return self._is_available

        self._is_available = self._init_library()
        return self._is_available

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": self.provider_name.value,
            "available": self._is_available or False,
            "model": self.model,
            "disambiguator": self.use_disambiguator and self._disambiguator is not None,
            "description": "CAMeL Tools Arabic NLP (NYU Abu Dhabi)",
        }
