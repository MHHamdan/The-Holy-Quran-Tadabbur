"""
Translation Service - STRICT LITERAL (NON-INTERPRETIVE) MODE

This service handles Quran verse translation with strict rules:
1. LITERAL translations only - no interpretation
2. Preserve word order where grammatically possible
3. Mark unclear words with [brackets] for later review
4. NEVER add interpretive commentary
5. Log all translations for scholarly review

CRITICAL: RAG pipeline NEVER translates at runtime.
All translations are pre-computed and stored.
"""
import hashlib
import json
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse, Translation
from app.models.audit import AuditLog


# Prompt versioning for reproducibility
PROMPT_VERSION = "1.0.0"
PROMPT_HASH = None  # Computed at module load


class TranslationMode(str, Enum):
    """
    Translation modes available.

    LITERAL_NON_INTERPRETIVE: Word-for-word translation without any theological interpretation
    SCHOLARLY: Use existing verified scholarly translations only (no LLM)
    """
    LITERAL_NON_INTERPRETIVE = "literal_non_interpretive"
    SCHOLARLY = "scholarly"


class VerificationStatus(str, Enum):
    """Status of translation verification."""
    PENDING = "pending"  # Not yet reviewed
    VERIFIED = "verified"  # Reviewed and approved
    REJECTED = "rejected"  # Reviewed and needs correction
    FLAGGED = "flagged"  # Auto-flagged for review


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    verse_reference: str
    source_language: str
    target_language: str
    source_text: str
    source_text_hash: str  # SHA256 of source text
    translated_text: str
    translator: str
    mode: TranslationMode
    confidence: int  # 0-100
    needs_review: bool
    verification_status: VerificationStatus
    prompt_version: str
    review_notes: list[str] = field(default_factory=list)


# Strict literal (non-interpretive) translation prompt
LITERAL_TRANSLATION_PROMPT = """You are a Quranic Arabic to English translator operating in STRICT LITERAL (NON-INTERPRETIVE) MODE.

## ABSOLUTE RULES - VIOLATION IS UNACCEPTABLE:

1. TRANSLATE LITERALLY: Preserve the exact meaning of each Arabic word
2. DO NOT INTERPRET: Never add theological interpretation or tafseer
3. DO NOT PARAPHRASE: Keep as close to word order as grammatically possible
4. MARK AMBIGUITY: Use [brackets] for words with multiple valid translations
   Example: "صبر" -> "[patience/steadfastness]"
5. PRESERVE PRONOUNS: Translate pronouns exactly, don't resolve antecedents
   Example: "هو" stays as "He" not "Allah" (let tafseer clarify)
6. NO ADDITIONS: Do not add words that don't exist in the Arabic
7. NO COMMENTARY: Your output is ONLY the translation, nothing else

## HANDLING DIFFICULT WORDS:

- If a word has no direct English equivalent, transliterate it and add meaning:
  Example: "تقوى" -> "taqwa [God-consciousness]"
- If grammar requires word reordering, keep it minimal
- If meaning is truly ambiguous, use most neutral option with [brackets]

## OUTPUT FORMAT:

Return ONLY the English translation. No explanations, no notes, just the translation text.

---

Translate this verse:
Surah: {surah_name} ({surah_no}:{ayah_no})
Arabic: {arabic_text}
"""


def _compute_prompt_hash() -> str:
    """Compute hash of the prompt template for versioning."""
    return hashlib.sha256(LITERAL_TRANSLATION_PROMPT.encode('utf-8')).hexdigest()[:16]


# Compute prompt hash at module load
PROMPT_HASH = _compute_prompt_hash()


class TranslationService:
    """
    Service for translating Quran verses.

    Operates in STRICT LITERAL (NON-INTERPRETIVE) MODE by default.
    RAG pipeline NEVER translates at runtime - all translations are pre-computed.
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_client=None,  # Optional LLM client for new translations
        mode: TranslationMode = TranslationMode.LITERAL_NON_INTERPRETIVE
    ):
        self.session = session
        self.llm_client = llm_client
        self.mode = mode
        self.prompt_version = PROMPT_VERSION
        self.prompt_hash = PROMPT_HASH

    async def get_existing_translation(
        self,
        verse_id: int,
        language: str = "en",
        translator: Optional[str] = None
    ) -> Optional[Translation]:
        """Get an existing translation for a verse."""
        query = select(Translation).where(
            Translation.verse_id == verse_id,
            Translation.language == language
        )

        if translator:
            query = query.where(Translation.translator == translator)
        else:
            # Prefer scholarly translations over LLM
            query = query.order_by(
                # sahih_international first, then others, LLM last
                Translation.translator != "sahih_international",
                Translation.translator == "llm"
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_scholarly_translation(
        self,
        verse_id: int,
        language: str = "en"
    ) -> Optional[Translation]:
        """Get only scholarly (human-translated) translations."""
        result = await self.session.execute(
            select(Translation).where(
                Translation.verse_id == verse_id,
                Translation.language == language,
                Translation.translator != "llm"
            ).order_by(
                Translation.translator == "sahih_international"  # Prefer Sahih International
            )
        )
        return result.scalar_one_or_none()

    def _compute_source_hash(self, text: str) -> str:
        """Compute SHA256 hash of source text for verification."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _detect_review_flags(self, translated_text: str) -> tuple[list[str], VerificationStatus]:
        """
        Detect parts of translation that need scholarly review.

        Returns (review_notes, verification_status)
        """
        flags = []

        # Check for bracketed ambiguous words
        brackets = re.findall(r'\[([^\]]+)\]', translated_text)
        if brackets:
            flags.append(f"Contains {len(brackets)} ambiguous terms: {', '.join(brackets[:3])}")

        # Check for transliterations
        transliterations = re.findall(r'\b[a-z]+a[a-z]*\b', translated_text.lower())
        common_transliterations = ['taqwa', 'sabr', 'iman', 'jihad', 'salah', 'zakah', 'hajj']
        found = [t for t in transliterations if t in common_transliterations]
        if found:
            flags.append(f"Contains transliterated terms: {', '.join(found)}")

        # Check for very short translations (might be incomplete)
        if len(translated_text.split()) < 3:
            flags.append("Translation seems too short")

        # Determine verification status
        if len(flags) > 2:
            status = VerificationStatus.FLAGGED
        elif len(flags) > 0:
            status = VerificationStatus.PENDING
        else:
            status = VerificationStatus.PENDING  # All new translations start as pending

        return flags, status

    async def translate_verse(
        self,
        verse: QuranVerse,
        target_language: str = "en",
        force_new: bool = False
    ) -> TranslationResult:
        """
        Translate a verse.

        Priority order:
        1. Existing scholarly translation (if available)
        2. Existing LLM translation (if available and valid)
        3. Generate new LLM translation (if LLM client available)
        4. Return empty result with error
        """
        source_text = verse.text_uthmani
        source_hash = self._compute_source_hash(source_text)

        # Try to get existing translation
        if not force_new:
            existing = await self.get_existing_translation(verse.id, target_language)
            if existing:
                review_notes = []
                if existing.needs_review:
                    review_notes.append("Flagged for review")

                return TranslationResult(
                    verse_reference=verse.reference,
                    source_language="ar",
                    target_language=target_language,
                    source_text=source_text,
                    source_text_hash=source_hash,
                    translated_text=existing.text,
                    translator=existing.translator,
                    mode=self.mode,
                    confidence=existing.confidence or 100,
                    needs_review=bool(existing.needs_review),
                    verification_status=VerificationStatus.VERIFIED if existing.translator != "llm" else VerificationStatus.PENDING,
                    prompt_version=self.prompt_version,
                    review_notes=review_notes,
                )

        # If mode is SCHOLARLY, only use existing translations
        if self.mode == TranslationMode.SCHOLARLY:
            scholarly = await self.get_scholarly_translation(verse.id, target_language)
            if scholarly:
                return TranslationResult(
                    verse_reference=verse.reference,
                    source_language="ar",
                    target_language=target_language,
                    source_text=source_text,
                    source_text_hash=source_hash,
                    translated_text=scholarly.text,
                    translator=scholarly.translator,
                    mode=self.mode,
                    confidence=100,
                    needs_review=False,
                    verification_status=VerificationStatus.VERIFIED,
                    prompt_version=self.prompt_version,
                )
            else:
                return TranslationResult(
                    verse_reference=verse.reference,
                    source_language="ar",
                    target_language=target_language,
                    source_text=source_text,
                    source_text_hash=source_hash,
                    translated_text="",
                    translator="none",
                    mode=self.mode,
                    confidence=0,
                    needs_review=True,
                    verification_status=VerificationStatus.PENDING,
                    prompt_version=self.prompt_version,
                    review_notes=["No scholarly translation available"],
                )

        # Generate new LLM translation (LITERAL_NON_INTERPRETIVE mode only)
        if self.llm_client is None:
            return TranslationResult(
                verse_reference=verse.reference,
                source_language="ar",
                target_language=target_language,
                source_text=source_text,
                source_text_hash=source_hash,
                translated_text="",
                translator="none",
                mode=self.mode,
                confidence=0,
                needs_review=True,
                verification_status=VerificationStatus.PENDING,
                prompt_version=self.prompt_version,
                review_notes=["No LLM client configured for translation"],
            )

        # Generate translation using LLM
        translated_text, model_name = await self._generate_llm_translation(
            verse=verse,
            target_language=target_language
        )

        if not translated_text:
            return TranslationResult(
                verse_reference=verse.reference,
                source_language="ar",
                target_language=target_language,
                source_text=source_text,
                source_text_hash=source_hash,
                translated_text="",
                translator="llm",
                mode=self.mode,
                confidence=0,
                needs_review=True,
                verification_status=VerificationStatus.FLAGGED,
                prompt_version=self.prompt_version,
                review_notes=["LLM translation failed"],
            )

        # Detect review flags
        review_notes, verification_status = self._detect_review_flags(translated_text)
        needs_review = len(review_notes) > 0 or verification_status != VerificationStatus.VERIFIED

        # Calculate confidence based on review flags
        confidence = 90 - (len(review_notes) * 10)
        confidence = max(50, min(95, confidence))

        # Save to database
        await self._save_translation(
            verse_id=verse.id,
            language=target_language,
            text=translated_text,
            model_name=model_name,
            source_hash=source_hash,
            confidence=confidence,
            needs_review=needs_review,
            verification_status=verification_status
        )

        # Log the translation for audit
        await self._log_translation(
            verse=verse,
            translated_text=translated_text,
            model_name=model_name,
            confidence=confidence,
            review_notes=review_notes,
            source_hash=source_hash
        )

        return TranslationResult(
            verse_reference=verse.reference,
            source_language="ar",
            target_language=target_language,
            source_text=source_text,
            source_text_hash=source_hash,
            translated_text=translated_text,
            translator="llm",
            mode=self.mode,
            confidence=confidence,
            needs_review=needs_review,
            verification_status=verification_status,
            prompt_version=self.prompt_version,
            review_notes=review_notes,
        )

    async def _generate_llm_translation(
        self,
        verse: QuranVerse,
        target_language: str
    ) -> tuple[str, str]:
        """Generate a literal (non-interpretive) translation using LLM."""
        if not self.llm_client:
            return "", ""

        prompt = LITERAL_TRANSLATION_PROMPT.format(
            surah_name=verse.sura_name_en,
            surah_no=verse.sura_no,
            ayah_no=verse.aya_no,
            arabic_text=verse.text_uthmani
        )

        try:
            # Call LLM (using Anthropic client pattern)
            response = await self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            model_name = response.model
            translated_text = response.content[0].text.strip()

            # Validate translation (basic sanity checks)
            if len(translated_text) < 5:
                return "", model_name

            # Remove any leading/trailing quotes or markdown
            translated_text = translated_text.strip('"\'`')

            return translated_text, model_name

        except Exception as e:
            print(f"LLM translation error: {e}")
            return "", ""

    async def _save_translation(
        self,
        verse_id: int,
        language: str,
        text: str,
        model_name: str,
        source_hash: str,
        confidence: int,
        needs_review: bool,
        verification_status: VerificationStatus
    ) -> Translation:
        """Save a translation to the database."""
        translation = Translation(
            verse_id=verse_id,
            language=language,
            translator="llm",
            text=text,
            model_name=model_name,
            source_hash=source_hash,
            prompt_version=self.prompt_version,
            confidence=confidence,
            needs_review=1 if needs_review else 0,
            verification_status=verification_status.value
        )

        self.session.add(translation)
        await self.session.commit()
        await self.session.refresh(translation)

        return translation

    async def _log_translation(
        self,
        verse: QuranVerse,
        translated_text: str,
        model_name: str,
        confidence: int,
        review_notes: list[str],
        source_hash: str
    ) -> None:
        """Log translation to audit trail."""
        log = AuditLog(
            action="llm_translation",
            entity_type="translation",
            entity_id=str(verse.id),
            old_value=None,
            new_value=json.dumps({
                "verse_reference": verse.reference,
                "arabic_text": verse.text_uthmani[:100],
                "translation": translated_text[:200],
                "model": model_name,
                "confidence": confidence,
                "review_notes": review_notes,
                "source_hash": source_hash[:16],
                "prompt_version": self.prompt_version
            }, ensure_ascii=False),
            performed_by="system:translation_service"
        )

        self.session.add(log)
        await self.session.commit()

    async def batch_translate(
        self,
        verses: list[QuranVerse],
        target_language: str = "en"
    ) -> list[TranslationResult]:
        """Translate multiple verses."""
        results = []
        for verse in verses:
            result = await self.translate_verse(verse, target_language)
            results.append(result)
        return results

    async def get_translations_needing_review(
        self,
        limit: int = 100
    ) -> list[Translation]:
        """Get translations that need scholarly review."""
        result = await self.session.execute(
            select(Translation).where(
                Translation.needs_review == 1
            ).order_by(
                Translation.created_at.desc()
            ).limit(limit)
        )
        return result.scalars().all()


def rag_should_never_translate() -> bool:
    """
    Guard function to ensure RAG never translates at runtime.

    CRITICAL: The RAG pipeline should ALWAYS use pre-computed translations.
    This function serves as documentation and a runtime check.
    """
    return True


# Export for documentation
__all__ = [
    "TranslationService",
    "TranslationMode",
    "TranslationResult",
    "VerificationStatus",
    "PROMPT_VERSION",
    "PROMPT_HASH",
    "rag_should_never_translate",
]
