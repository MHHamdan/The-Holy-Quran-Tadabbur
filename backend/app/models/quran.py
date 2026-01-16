"""
Quran verse and translation models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
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
    hizb_no = Column(Integer, nullable=True)

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
    model_name = Column(String(100), nullable=True)  # e.g., "claude-sonnet-4-20250514"
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
    )

    def __repr__(self):
        return f"<Translation {self.verse_id} - {self.language}/{self.translator}>"
