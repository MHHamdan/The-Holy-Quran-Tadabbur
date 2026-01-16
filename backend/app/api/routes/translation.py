"""
Translation API routes.

Provides endpoints for verse translation in STRICT LITERAL MODE.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.database import get_async_session
from app.models.quran import QuranVerse, Translation
from app.services.translation import TranslationService, TranslationMode

router = APIRouter(prefix="/translation", tags=["translation"])


class TranslationResponse(BaseModel):
    """Translation response model."""
    verse_reference: str
    source_language: str = "ar"
    target_language: str
    source_text: str
    translated_text: str
    translator: str
    mode: str
    confidence: int = Field(ge=0, le=100)
    needs_review: bool
    review_notes: list[str] = []


class TranslationListResponse(BaseModel):
    """List of translations response."""
    translations: list[TranslationResponse]
    total: int


class TranslationReviewItem(BaseModel):
    """Translation needing review."""
    translation_id: int
    verse_reference: str
    arabic_text: str
    translation_text: str
    translator: str
    confidence: int
    created_at: str


class TranslationReviewListResponse(BaseModel):
    """List of translations needing review."""
    items: list[TranslationReviewItem]
    total: int


@router.get("/verse/{surah}/{ayah}", response_model=TranslationResponse)
async def get_verse_translation(
    surah: int,
    ayah: int,
    language: str = Query("en", description="Target language code"),
    translator: Optional[str] = Query(None, description="Specific translator to use"),
    mode: str = Query("scholarly", description="Translation mode: 'scholarly' or 'literal'"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get translation for a specific verse.

    Modes:
    - scholarly: Only return existing scholarly translations (Sahih International, etc.)
    - literal: May generate new literal translations if not available (requires LLM)
    """
    # Get the verse
    result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == surah,
            QuranVerse.aya_no == ayah
        )
    )
    verse = result.scalar_one_or_none()

    if not verse:
        raise HTTPException(
            status_code=404,
            detail=f"Verse {surah}:{ayah} not found"
        )

    # Get translation
    translation_mode = TranslationMode.SCHOLARLY if mode == "scholarly" else TranslationMode.LITERAL
    service = TranslationService(
        session=session,
        llm_client=None,  # Don't generate new translations via API by default
        mode=translation_mode
    )

    translation_result = await service.translate_verse(
        verse=verse,
        target_language=language
    )

    if not translation_result.translated_text:
        raise HTTPException(
            status_code=404,
            detail=f"No {language} translation available for {surah}:{ayah}"
        )

    return TranslationResponse(
        verse_reference=translation_result.verse_reference,
        source_language=translation_result.source_language,
        target_language=translation_result.target_language,
        source_text=translation_result.source_text,
        translated_text=translation_result.translated_text,
        translator=translation_result.translator,
        mode=translation_result.mode.value,
        confidence=translation_result.confidence,
        needs_review=translation_result.needs_review,
        review_notes=translation_result.review_notes
    )


@router.get("/surah/{surah}", response_model=TranslationListResponse)
async def get_surah_translations(
    surah: int,
    language: str = Query("en", description="Target language code"),
    translator: Optional[str] = Query(None, description="Specific translator to use"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all translations for a surah."""
    # Get all verses in surah
    result = await session.execute(
        select(QuranVerse).where(
            QuranVerse.sura_no == surah
        ).order_by(QuranVerse.aya_no)
    )
    verses = result.scalars().all()

    if not verses:
        raise HTTPException(
            status_code=404,
            detail=f"Surah {surah} not found"
        )

    service = TranslationService(
        session=session,
        mode=TranslationMode.SCHOLARLY
    )

    translations = []
    for verse in verses:
        trans_result = await service.translate_verse(
            verse=verse,
            target_language=language
        )
        if trans_result.translated_text:
            translations.append(TranslationResponse(
                verse_reference=trans_result.verse_reference,
                source_language=trans_result.source_language,
                target_language=trans_result.target_language,
                source_text=trans_result.source_text,
                translated_text=trans_result.translated_text,
                translator=trans_result.translator,
                mode=trans_result.mode.value,
                confidence=trans_result.confidence,
                needs_review=trans_result.needs_review,
                review_notes=trans_result.review_notes
            ))

    return TranslationListResponse(
        translations=translations,
        total=len(translations)
    )


@router.get("/review", response_model=TranslationReviewListResponse)
async def get_translations_needing_review(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get list of translations that need scholarly review.

    These are typically LLM-generated translations that contain
    ambiguous terms or transliterations.
    """
    service = TranslationService(session=session)
    translations = await service.get_translations_needing_review(limit=limit)

    items = []
    for trans in translations:
        # Get the verse for context
        result = await session.execute(
            select(QuranVerse).where(QuranVerse.id == trans.verse_id)
        )
        verse = result.scalar_one_or_none()

        if verse:
            items.append(TranslationReviewItem(
                translation_id=trans.id,
                verse_reference=verse.reference,
                arabic_text=verse.text_uthmani,
                translation_text=trans.text,
                translator=trans.translator,
                confidence=trans.confidence or 0,
                created_at=trans.created_at.isoformat() if trans.created_at else ""
            ))

    return TranslationReviewListResponse(
        items=items,
        total=len(items)
    )


@router.get("/available-translators")
async def get_available_translators(
    language: str = Query("en", description="Language code"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get list of available translators for a language."""
    result = await session.execute(
        select(Translation.translator)
        .where(Translation.language == language)
        .distinct()
    )
    translators = result.scalars().all()

    return {
        "language": language,
        "translators": list(translators),
        "recommended": "sahih_international" if "sahih_international" in translators else (
            translators[0] if translators else None
        )
    }
