"""
Grammatical Analyzer - Arabic sentence structure analysis using LLM.

Uses Ollama to analyze:
- Word grammatical roles (فاعل، مفعول، خبر، إلخ)
- Sentence types (جملة فعلية، جملة اسمية، إلخ)
- Morphological analysis

Arabic: محلل نحوي للجمل العربية
"""

import logging
import json
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx

from app.services.quran_search import (
    GrammaticalRole,
    SentenceType,
    GRAMMATICAL_ROLE_AR,
    SENTENCE_TYPE_AR,
    SearchMatch,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:32b"  # Good Arabic support
TIMEOUT_SECONDS = 60


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class GrammaticalAnalysis:
    """Complete grammatical analysis of a word in context."""
    word: str
    verse_text: str
    verse_reference: str

    # Grammatical classification
    role: GrammaticalRole
    role_ar: str
    role_explanation: str

    # Sentence analysis
    sentence_type: SentenceType
    sentence_type_ar: str

    # Morphological details
    root: str = ""           # الجذر
    pattern: str = ""        # الوزن
    word_type: str = ""      # نوع الكلمة (اسم، فعل، حرف)
    gender: str = ""         # الجنس
    number: str = ""         # العدد (مفرد، مثنى، جمع)
    case: str = ""           # الإعراب (مرفوع، منصوب، مجرور)
    tense: str = ""          # الزمن (ماضي، مضارع، أمر)

    # Additional notes
    notes_ar: str = ""
    notes_en: str = ""

    # Raw LLM response
    raw_response: str = ""


@dataclass
class WordInContext:
    """A word with its grammatical analysis in verse context."""
    word: str
    position: int
    role: GrammaticalRole
    role_ar: str
    is_search_target: bool = False


@dataclass
class VerseAnalysis:
    """Complete grammatical analysis of a verse."""
    sura_no: int
    aya_no: int
    text: str
    sentence_type: SentenceType
    sentence_type_ar: str
    words: List[WordInContext]
    parsing_notes: str = ""


# =============================================================================
# LLM PROMPTS
# =============================================================================

WORD_ANALYSIS_PROMPT = """أنت عالم في النحو العربي والإعراب. حلل الكلمة التالية في سياق الآية القرآنية.

الآية: {verse_text}
مرجع الآية: {verse_reference}
الكلمة المطلوب تحليلها: {word}

أجب بصيغة JSON فقط بالشكل التالي:
{{
    "role": "اختر من: subject, object, predicate, verb, noun, adjective, adverb, preposition, particle, pronoun, conjunction, unknown",
    "role_ar": "الدور بالعربية (فاعل، مفعول به، خبر، فعل، اسم، صفة، ظرف، حرف جر، حرف، ضمير، حرف عطف)",
    "role_explanation": "شرح موجز للدور النحوي",
    "sentence_type": "اختر من: verbal, nominal, conditional, interrogative, imperative, unknown",
    "sentence_type_ar": "نوع الجملة (جملة فعلية، جملة اسمية، جملة شرطية، جملة استفهامية، جملة أمرية)",
    "root": "الجذر الثلاثي أو الرباعي",
    "pattern": "الوزن الصرفي",
    "word_type": "اسم أو فعل أو حرف",
    "gender": "مذكر أو مؤنث أو محايد",
    "number": "مفرد أو مثنى أو جمع",
    "case": "مرفوع أو منصوب أو مجرور أو مبني",
    "tense": "ماضي أو مضارع أو أمر (للأفعال فقط)",
    "notes_ar": "ملاحظات إضافية بالعربية",
    "notes_en": "Additional notes in English"
}}

أجب بـ JSON فقط، بدون أي نص إضافي."""


VERSE_PARSING_PROMPT = """أنت عالم في النحو العربي. حلل الآية القرآنية التالية إعرابياً.

الآية: {verse_text}
مرجع الآية: {verse_reference}

حلل كل كلمة في الآية وحدد دورها النحوي.

أجب بصيغة JSON فقط:
{{
    "sentence_type": "verbal أو nominal أو conditional أو interrogative أو imperative أو unknown",
    "sentence_type_ar": "نوع الجملة بالعربية",
    "words": [
        {{
            "word": "الكلمة",
            "position": 0,
            "role": "subject/object/verb/noun/etc",
            "role_ar": "الدور بالعربية"
        }}
    ],
    "parsing_notes": "ملاحظات على الإعراب"
}}

أجب بـ JSON فقط."""


BATCH_CATEGORIZATION_PROMPT = """أنت عالم في النحو العربي. صنّف الكلمة "{word}" حسب دورها النحوي في كل آية من الآيات التالية.

الآيات:
{verses}

لكل آية، حدد:
1. الدور النحوي للكلمة (فاعل، مفعول به، خبر، فعل، اسم، صفة، إلخ)
2. نوع الجملة (فعلية، اسمية، شرطية، إلخ)

أجب بصيغة JSON:
{{
    "analyses": [
        {{
            "verse_ref": "رقم السورة:رقم الآية",
            "role": "subject/object/verb/etc",
            "role_ar": "الدور بالعربية",
            "sentence_type": "verbal/nominal/etc",
            "sentence_type_ar": "نوع الجملة"
        }}
    ]
}}

أجب بـ JSON فقط."""


# =============================================================================
# GRAMMATICAL ANALYZER SERVICE
# =============================================================================

class GrammaticalAnalyzer:
    """
    Arabic grammatical analyzer using Ollama LLM.

    Analyzes:
    - Word roles in sentences (إعراب)
    - Sentence types (أنواع الجمل)
    - Morphological structure (الصرف)
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = DEFAULT_MODEL,
    ):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=TIMEOUT_SECONDS)

    async def analyze_word(
        self,
        word: str,
        verse_text: str,
        verse_reference: str,
    ) -> GrammaticalAnalysis:
        """
        Analyze a word's grammatical role in its verse context.

        Args:
            word: The Arabic word to analyze
            verse_text: Full verse text containing the word
            verse_reference: Verse reference (e.g., "2:255")

        Returns:
            GrammaticalAnalysis with detailed grammatical information
        """
        prompt = WORD_ANALYSIS_PROMPT.format(
            verse_text=verse_text,
            verse_reference=verse_reference,
            word=word,
        )

        try:
            response = await self._call_ollama(prompt)
            parsed = self._parse_json_response(response)

            if not parsed:
                return self._default_analysis(word, verse_text, verse_reference, response)

            return GrammaticalAnalysis(
                word=word,
                verse_text=verse_text,
                verse_reference=verse_reference,
                role=self._parse_role(parsed.get("role", "unknown")),
                role_ar=parsed.get("role_ar", "غير محدد"),
                role_explanation=parsed.get("role_explanation", ""),
                sentence_type=self._parse_sentence_type(parsed.get("sentence_type", "unknown")),
                sentence_type_ar=parsed.get("sentence_type_ar", "غير محددة"),
                root=parsed.get("root", ""),
                pattern=parsed.get("pattern", ""),
                word_type=parsed.get("word_type", ""),
                gender=parsed.get("gender", ""),
                number=parsed.get("number", ""),
                case=parsed.get("case", ""),
                tense=parsed.get("tense", ""),
                notes_ar=parsed.get("notes_ar", ""),
                notes_en=parsed.get("notes_en", ""),
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Error analyzing word '{word}': {e}")
            return self._default_analysis(word, verse_text, verse_reference, str(e))

    async def analyze_verse(
        self,
        verse_text: str,
        verse_reference: str,
        sura_no: int,
        aya_no: int,
    ) -> VerseAnalysis:
        """
        Analyze the complete grammatical structure of a verse.

        Returns VerseAnalysis with each word's role identified.
        """
        prompt = VERSE_PARSING_PROMPT.format(
            verse_text=verse_text,
            verse_reference=verse_reference,
        )

        try:
            response = await self._call_ollama(prompt)
            parsed = self._parse_json_response(response)

            if not parsed:
                return self._default_verse_analysis(
                    sura_no, aya_no, verse_text, response
                )

            words = []
            for w in parsed.get("words", []):
                words.append(WordInContext(
                    word=w.get("word", ""),
                    position=w.get("position", 0),
                    role=self._parse_role(w.get("role", "unknown")),
                    role_ar=w.get("role_ar", "غير محدد"),
                ))

            return VerseAnalysis(
                sura_no=sura_no,
                aya_no=aya_no,
                text=verse_text,
                sentence_type=self._parse_sentence_type(parsed.get("sentence_type", "unknown")),
                sentence_type_ar=parsed.get("sentence_type_ar", "غير محددة"),
                words=words,
                parsing_notes=parsed.get("parsing_notes", ""),
            )

        except Exception as e:
            logger.error(f"Error analyzing verse {verse_reference}: {e}")
            return self._default_verse_analysis(sura_no, aya_no, verse_text, str(e))

    async def categorize_search_results(
        self,
        word: str,
        matches: List[SearchMatch],
        batch_size: int = 10,
    ) -> List[SearchMatch]:
        """
        Categorize search results by grammatical role.

        Updates SearchMatch objects with grammatical analysis.

        Args:
            word: The searched word
            matches: List of SearchMatch objects
            batch_size: Number of verses to analyze per LLM call

        Returns:
            Updated SearchMatch objects with grammatical info
        """
        # Process in batches
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i + batch_size]

            # Format verses for batch prompt
            verses_text = "\n".join([
                f"{m.sura_no}:{m.aya_no}: {m.text_uthmani}"
                for m in batch
            ])

            prompt = BATCH_CATEGORIZATION_PROMPT.format(
                word=word,
                verses=verses_text,
            )

            try:
                response = await self._call_ollama(prompt)
                parsed = self._parse_json_response(response)

                if parsed and "analyses" in parsed:
                    # Map results back to matches
                    for analysis in parsed["analyses"]:
                        verse_ref = analysis.get("verse_ref", "")
                        for match in batch:
                            if f"{match.sura_no}:{match.aya_no}" == verse_ref:
                                match.word_role = self._parse_role(analysis.get("role", "unknown"))
                                match.word_role_ar = analysis.get("role_ar", "غير محدد")
                                match.sentence_type = self._parse_sentence_type(
                                    analysis.get("sentence_type", "unknown")
                                )
                                match.sentence_type_ar = analysis.get("sentence_type_ar", "غير محددة")
                                break

            except Exception as e:
                logger.warning(f"Error in batch categorization: {e}")
                # Continue with defaults for this batch

        return matches

    async def get_role_distribution(
        self,
        matches: List[SearchMatch],
    ) -> Dict[str, int]:
        """
        Get distribution of grammatical roles in search results.

        Returns dict mapping role_ar -> count.
        """
        distribution: Dict[str, int] = {}

        for match in matches:
            role_ar = match.word_role_ar or "غير محدد"
            distribution[role_ar] = distribution.get(role_ar, 0) + 1

        return distribution

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for text generation."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for deterministic output
                        "num_predict": 2000,
                    }
                }
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "")

        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        try:
            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from response
        try:
            # Find JSON block
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        logger.warning(f"Could not parse JSON from response: {response[:200]}...")
        return None

    def _parse_role(self, role_str: str) -> GrammaticalRole:
        """Parse grammatical role from string."""
        role_map = {
            "subject": GrammaticalRole.SUBJECT,
            "object": GrammaticalRole.OBJECT,
            "predicate": GrammaticalRole.PREDICATE,
            "verb": GrammaticalRole.VERB,
            "noun": GrammaticalRole.NOUN,
            "adjective": GrammaticalRole.ADJECTIVE,
            "adverb": GrammaticalRole.ADVERB,
            "preposition": GrammaticalRole.PREPOSITION,
            "particle": GrammaticalRole.PARTICLE,
            "pronoun": GrammaticalRole.PRONOUN,
            "conjunction": GrammaticalRole.CONJUNCTION,
        }
        return role_map.get(role_str.lower(), GrammaticalRole.UNKNOWN)

    def _parse_sentence_type(self, type_str: str) -> SentenceType:
        """Parse sentence type from string."""
        type_map = {
            "verbal": SentenceType.VERBAL,
            "nominal": SentenceType.NOMINAL,
            "conditional": SentenceType.CONDITIONAL,
            "interrogative": SentenceType.INTERROGATIVE,
            "imperative": SentenceType.IMPERATIVE,
        }
        return type_map.get(type_str.lower(), SentenceType.UNKNOWN)

    def _default_analysis(
        self,
        word: str,
        verse_text: str,
        verse_reference: str,
        error_msg: str,
    ) -> GrammaticalAnalysis:
        """Return default analysis when LLM fails."""
        return GrammaticalAnalysis(
            word=word,
            verse_text=verse_text,
            verse_reference=verse_reference,
            role=GrammaticalRole.UNKNOWN,
            role_ar="غير محدد",
            role_explanation="",
            sentence_type=SentenceType.UNKNOWN,
            sentence_type_ar="غير محددة",
            notes_ar=f"خطأ في التحليل: {error_msg[:100]}",
            notes_en=f"Analysis error: {error_msg[:100]}",
            raw_response=error_msg,
        )

    def _default_verse_analysis(
        self,
        sura_no: int,
        aya_no: int,
        verse_text: str,
        error_msg: str,
    ) -> VerseAnalysis:
        """Return default verse analysis when LLM fails."""
        return VerseAnalysis(
            sura_no=sura_no,
            aya_no=aya_no,
            text=verse_text,
            sentence_type=SentenceType.UNKNOWN,
            sentence_type_ar="غير محددة",
            words=[],
            parsing_notes=f"خطأ في التحليل: {error_msg[:100]}",
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def analyze_word_grammar(
    word: str,
    verse_text: str,
    verse_reference: str,
    model: str = DEFAULT_MODEL,
) -> GrammaticalAnalysis:
    """
    Convenience function to analyze a word's grammar.

    Creates temporary analyzer, runs analysis, and closes.
    """
    analyzer = GrammaticalAnalyzer(model=model)
    try:
        return await analyzer.analyze_word(word, verse_text, verse_reference)
    finally:
        await analyzer.close()
