"""
Quran verse and translation models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class QuranVerse(Base):
    """
    Quran verse model - stores the complete Quran text.

    Total verses: 6,236
    """
    __tablename__ = "quran_verses"

    id = Column(Integer, primary_key=True)  # Global verse ID (1-6236)
    sura_no = Column(Integer, nullable=False, index=True)
    sura_name_ar = Column(String(100), nullable=False)
    sura_name_en = Column(String(100), nullable=False)
    aya_no = Column(Integer, nullable=False)

    # Text variants
    text_uthmani = Column(Text, nullable=False)  # Standard Uthmani script with diacritics
    text_imlaei = Column(Text, nullable=False)  # Imlaei script (still has diacritics)
    text_normalized = Column(Text, nullable=True)  # Normalized for search (no diacritics)

    # Mushaf positioning
    page_no = Column(Integer, nullable=False, index=True)
    juz_no = Column(Integer, nullable=False, index=True)
    hizb_no = Column(Integer, nullable=True)  # 1-60
    rub_no = Column(Integer, nullable=True)  # hizb quarter, 1-240 (quran_structure_markers.json)

    # Line positioning (for display)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)

    # Sajda indicator
    sajda_type = Column(String(20), nullable=True)  # None, "recommended", "obligatory"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    translations = relationship("Translation", back_populates="verse", lazy="select")  # Changed from selectin to avoid eager loading

    __table_args__ = (
        UniqueConstraint("sura_no", "aya_no", name="uq_sura_aya"),
        Index("ix_verse_sura_aya", "sura_no", "aya_no"),
        Index("ix_verse_page", "page_no"),
        Index("ix_verse_juz", "juz_no"),
    )

    def __repr__(self):
        return f"<Verse {self.sura_no}:{self.aya_no}>"

    @property
    def reference(self) -> str:
        """Get verse reference string."""
        return f"{self.sura_no}:{self.aya_no}"

    @property
    def full_reference(self) -> str:
        """Get full verse reference with sura name."""
        return f"{self.sura_name_en} {self.sura_no}:{self.aya_no}"


class Translation(Base):
    """
    Verse translations in multiple languages.
    """
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verse_id = Column(Integer, ForeignKey("quran_verses.id"), nullable=False, index=True)

    language = Column(String(10), nullable=False, index=True)  # "en", "ar", "ur", etc.
    translator = Column(String(100), nullable=False)  # "sahih_international", "pickthall", "llm"
    text = Column(Text, nullable=False)

    # For LLM translations
    model_name = Column(String(100), nullable=True)  # e.g., "meta-llama/Llama-3.3-70B-Instruct"

    # Provenance for ingested editions (QuranEnc requires version + footnotes to be kept)
    source_id = Column(String(50), nullable=True)  # e.g. "quranenc"
    edition_version = Column(String(32), nullable=True)
    footnotes = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256 of source text
    confidence = Column(Integer, nullable=True)  # 0-100
    needs_review = Column(Integer, default=0)  # 0=ok, 1=needs_review

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    verse = relationship("QuranVerse", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("verse_id", "language", "translator", name="uq_verse_lang_translator"),
        Index("ix_translation_lang", "language"),
        Index("ix_translation_translator", "translator"),
    )


class TranslationEdition(Base):
    """
    One ingested translation edition, with the licence and attribution that
    must be shown wherever its text is displayed.
    """
    __tablename__ = "translation_editions"

    key = Column(String(100), primary_key=True)  # matches Translation.translator
    language = Column(String(10), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    translator_name = Column(String(255), nullable=True)
    version = Column(String(32), nullable=False)
    source_id = Column(String(50), nullable=False)
    source_url = Column(String(500), nullable=False)
    license = Column(String(255), nullable=False)
    attribution = Column(Text, nullable=False)
    verse_count = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Translation {self.verse_id} - {self.language}/{self.translator}>"
