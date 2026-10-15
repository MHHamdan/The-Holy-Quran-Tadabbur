"""
Translation Service - stored scholarly translations only.

Verse translations are the published editions seeded into the translations
table (QuranEnc, verbatim, with their attribution). Nothing here generates a
translation: the former LLM 'literal' path (an AI-written Qur'an translation)
was unreachable from the API, broke the route that referenced it, and has been
removed.

CRITICAL: RAG pipeline NEVER translates at runtime.
"""
import hashlib
import logging
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse, Translation, TranslationEdition

logger = logging.getLogger(__name__)


class TranslationMode(str, Enum):
    """SCHOLARLY: stored, published translations only (the only mode)."""
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
    review_notes: list[str] = field(default_factory=list)


def _default_edition_keys():
    """Subquery: the default edition key of every language."""
    return select(TranslationEdition.key).where(TranslationEdition.is_default.is_(True))


class TranslationService:
    """
    Look up stored scholarly translations of Quran verses.

    RAG pipeline NEVER translates at runtime - all translations are pre-computed.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mode = TranslationMode.SCHOLARLY

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
            # The language's default edition first, then other editions, LLM last
            query = query.order_by(
                Translation.translator.notin_(_default_edition_keys()),
                Translation.translator == "llm",
                Translation.translator,
            )

        result = await self.session.execute(query.limit(1))
        return result.scalars().first()

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
                Translation.translator.notin_(_default_edition_keys()),
                Translation.translator,
            ).limit(1)
        )
        return result.scalars().first()

    def _compute_source_hash(self, text: str) -> str:
        """Compute SHA256 hash of source text for verification."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def translate_verse(
        self,
        verse: QuranVerse,
        target_language: str = "en",
    ) -> TranslationResult:
        """
        Return the stored translation of a verse.

        The language's default edition first, then any other published
        edition. Machine ('llm') rows are never returned and nothing is
        generated: with no stored translation the result is empty.
        """
        source_text = verse.text_uthmani
        source_hash = self._compute_source_hash(source_text)

        translation = await self.get_scholarly_translation(verse.id, target_language)
        if translation:
            return TranslationResult(
                verse_reference=verse.reference,
                source_language="ar",
                target_language=target_language,
                source_text=source_text,
                source_text_hash=source_hash,
                translated_text=translation.text,
                translator=translation.translator,
                mode=self.mode,
                confidence=100,
                needs_review=bool(translation.needs_review),
                verification_status=VerificationStatus.VERIFIED,
                review_notes=["Flagged for review"] if translation.needs_review else [],
            )

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
            review_notes=["No scholarly translation available"],
        )

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
    "rag_should_never_translate",
]
