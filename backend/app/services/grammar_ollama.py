"""
Arabic Grammar Analysis Service using Local Ollama.

This service provides إعراب (grammatical analysis) for Quranic text
using local Ollama with Qwen2.5 model.

GROUNDING RULES:
================
1. LLM must ONLY output from predefined Arabic label sets
2. LLM must include confidence scores for each token
3. If uncertain, LLM must use "غير محدد" label
4. Output must be valid JSON with Arabic labels
5. Never hallucinate grammatical rules

PROMPT DESIGN:
==============
- System prompt defines the constrained label set
- User prompt provides tokenized text
- Force JSON output schema
- Include examples for few-shot learning
"""
import json
import logging
import re
from typing import List, Optional, Dict, Any
import httpx

from app.core.config import settings
from app.models.grammar import (
    TokenAnalysis,
    GrammarAnalysis,
    POSTag,
    GrammaticalRole,
    SentenceType,
    CaseEnding,
    VALID_POS_TAGS,
    VALID_ROLES,
    VALID_SENTENCE_TYPES,
    validate_grammar_output,
)

logger = logging.getLogger(__name__)


# System prompt for grammar analysis (Arabic-first)
GRAMMAR_SYSTEM_PROMPT = """أنت مساعد متخصص في النحو والصرف العربي، خاصة نحو القرآن الكريم.

## مهمتك:
تحليل إعراب النص العربي وتصنيف كل كلمة نحوياً.

## قواعد صارمة:
1. استخدم فقط التصنيفات المحددة أدناه - لا تخترع تصنيفات جديدة
2. إذا لم تكن متأكداً، استخدم "غير محدد"
3. أعطِ درجة ثقة (0-1) لكل تحليل
4. لا تخمّن - إن لم تتأكد قل "غير محدد"
5. الإخراج يجب أن يكون JSON صالح فقط

## أقسام الكلام (pos):
- اسم، فعل، حرف
- اسم علم، ضمير، اسم إشارة، اسم موصول، اسم استفهام، مصدر
- فعل ماض، فعل مضارع، فعل أمر
- حرف جر، حرف عطف، حرف نفي، حرف استفهام، حرف شرط
- غير محدد

## الدور النحوي (role):
- مبتدأ، خبر
- فاعل، نائب فاعل، مفعول به، مفعول لأجله، مفعول فيه، مفعول مطلق
- حال، تمييز، مستثنى
- مضاف، مضاف إليه، جار ومجرور، مجرور
- نعت، منعوت، بدل، معطوف، معطوف عليه، توكيد
- منادى
- خبر كان، اسم إن، خبر إن
- غير محدد

## نوع الجملة (sentence_type):
- جملة اسمية
- جملة فعلية
- شبه جملة
- غير محدد

## مثال للإخراج:
```json
{
  "sentence_type": "جملة اسمية",
  "tokens": [
    {"w": "اللهُ", "pos": "اسم علم", "role": "مبتدأ", "i3rab": "مبتدأ مرفوع وعلامة رفعه الضمة", "confidence": 0.95},
    {"w": "لا", "pos": "حرف نفي", "role": "غير محدد", "i3rab": "حرف نفي للجنس", "confidence": 0.9}
  ],
  "notes_ar": "جملة اسمية مبدوءة بلفظ الجلالة"
}
```

أجب بـ JSON فقط، بدون أي نص آخر."""


def build_grammar_prompt(text: str, verse_ref: Optional[str] = None) -> str:
    """Build the user prompt for grammar analysis."""
    words = text.split()
    word_list = "، ".join([f'"{w}"' for w in words])

    prompt = f"""حلل إعراب النص التالي:

النص: {text}
"""
    if verse_ref:
        prompt += f"المرجع: سورة {verse_ref}\n"

    prompt += f"""
الكلمات: [{word_list}]

أعطني تحليلاً نحوياً لكل كلمة بصيغة JSON."""

    return prompt


class GrammarService:
    """
    Service for Arabic grammar analysis using Ollama.
    """

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: float = 60.0,
    ):
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self.timeout = timeout

    async def analyze(
        self,
        text: str,
        verse_reference: Optional[str] = None,
    ) -> GrammarAnalysis:
        """
        Analyze Arabic text and return grammatical analysis.

        Args:
            text: Arabic text to analyze
            verse_reference: Optional verse reference (e.g., "2:255")

        Returns:
            GrammarAnalysis object with token-by-token analysis
        """
        # Build prompts
        user_prompt = build_grammar_prompt(text, verse_reference)

        try:
            # Call Ollama
            raw_response = await self._call_ollama(
                system_prompt=GRAMMAR_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            # Parse and validate JSON response
            parsed = self._parse_response(raw_response)

            # Validate against allowed labels
            validation_errors = validate_grammar_output(parsed)
            if validation_errors:
                logger.warning(f"Grammar output validation errors: {validation_errors}")

            # Convert to GrammarAnalysis
            return self._to_grammar_analysis(parsed, text, verse_reference)

        except Exception as e:
            logger.error(f"Grammar analysis failed: {e}")
            # Return fallback with unknown labels
            return self._create_fallback_analysis(text, verse_reference, str(e))

    async def _call_ollama(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Call Ollama API and return raw response."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Very low for consistency
                        "top_p": 0.9,
                    },
                    "format": "json",  # Request JSON output
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        # Try to extract JSON from response
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {raw[:200]}")

    def _to_grammar_analysis(
        self,
        parsed: Dict[str, Any],
        original_text: str,
        verse_reference: Optional[str],
    ) -> GrammarAnalysis:
        """Convert parsed LLM output to GrammarAnalysis object."""
        tokens = []

        for i, token_data in enumerate(parsed.get("tokens", [])):
            # Map string values to enums, with fallback to UNKNOWN
            pos_str = token_data.get("pos", "غير محدد")
            role_str = token_data.get("role", "غير محدد")

            pos = self._get_pos_tag(pos_str)
            role = self._get_role(role_str)

            tokens.append(TokenAnalysis(
                word=token_data.get("w", ""),
                word_index=i,
                pos=pos,
                role=role,
                i3rab=token_data.get("i3rab", ""),
                confidence=float(token_data.get("confidence", 0.5)),
                notes_ar=token_data.get("notes", ""),
            ))

        sentence_type_str = parsed.get("sentence_type", "غير محدد")
        sentence_type = self._get_sentence_type(sentence_type_str)

        # Calculate overall confidence
        overall_confidence = sum(t.confidence for t in tokens) / len(tokens) if tokens else 0.5

        return GrammarAnalysis(
            verse_reference=verse_reference or "",
            text=original_text,
            sentence_type=sentence_type,
            tokens=tokens,
            notes_ar=parsed.get("notes_ar", ""),
            overall_confidence=overall_confidence,
            source="llm",
        )

    def _get_pos_tag(self, value: str) -> POSTag:
        """Convert string to POSTag enum."""
        for tag in POSTag:
            if tag.value == value:
                return tag
        return POSTag.UNKNOWN

    def _get_role(self, value: str) -> GrammaticalRole:
        """Convert string to GrammaticalRole enum."""
        for role in GrammaticalRole:
            if role.value == value:
                return role
        return GrammaticalRole.UNKNOWN

    def _get_sentence_type(self, value: str) -> SentenceType:
        """Convert string to SentenceType enum."""
        for st in SentenceType:
            if st.value == value:
                return st
        return SentenceType.UNKNOWN

    def _create_fallback_analysis(
        self,
        text: str,
        verse_reference: Optional[str],
        error: str,
    ) -> GrammarAnalysis:
        """Create fallback analysis when LLM fails."""
        words = text.split()
        tokens = [
            TokenAnalysis(
                word=word,
                word_index=i,
                pos=POSTag.UNKNOWN,
                role=GrammaticalRole.UNKNOWN,
                confidence=0.0,
                notes_ar="تعذّر التحليل",
            )
            for i, word in enumerate(words)
        ]

        return GrammarAnalysis(
            verse_reference=verse_reference or "",
            text=text,
            sentence_type=SentenceType.UNKNOWN,
            tokens=tokens,
            notes_ar=f"تعذّر التحليل: {error}",
            overall_confidence=0.0,
            source="fallback",
        )

    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
_grammar_service: Optional[GrammarService] = None


def get_grammar_service() -> GrammarService:
    """Get or create the grammar service singleton."""
    global _grammar_service
    if _grammar_service is None:
        _grammar_service = GrammarService()
    return _grammar_service
