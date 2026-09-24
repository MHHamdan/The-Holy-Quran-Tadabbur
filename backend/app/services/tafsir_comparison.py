"""
Multi-source tafsir comparison — reads the seeded corpus, not an external API.

Why this exists alongside enhanced_tafsir_comparison_service.py: that module is
backed by a hardcoded fixture covering three verses (1:1, 1:2, 2:255). This one
reads `tafseer_chunks`, which carries all six seeded sources across all 6,236
verses, and joins the scholarly metadata in TAFSIR_CATALOG so each source can be
presented with its author, era, death year and methodology.

CONTENT POLICY
==============
This service never interprets. It retrieves stored tafsir verbatim and reports
*descriptive* facts about the retrieved texts: how long they are, what
methodology each source follows, and how much vocabulary two same-language texts
share. Lexical overlap is a string statistic, NOT a claim that two scholars
agree or disagree — conveying it as agreement would be an interpretive claim
this project does not make. The wording that ships to the UI says so, and the
response carries that disclaimer inline so it cannot be dropped downstream.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse
from app.models.tafseer import TafseerChunk, TafseerSource
from app.services.tafsir_sources import TAFSIR_CATALOG

# ---------------------------------------------------------------------------
# Presentation vocabulary
# ---------------------------------------------------------------------------

# Methodology labels. Keys cover both the values stored in tafseer_sources and
# the TafsirMethodology enum names used by the catalogue.
METHODOLOGY_LABELS: Dict[str, Tuple[str, str]] = {
    "bil_mathur": ("بالمأثور", "Narration-based (bil-ma'thūr)"),
    "bil_ray": ("بالرأي", "Reason-based (bil-ra'y)"),
    "comprehensive": ("جامع", "Comprehensive"),
    "fiqh_focused": ("فقهي", "Jurisprudential (aḥkām)"),
    "fiqhi": ("فقهي", "Jurisprudential (aḥkām)"),
    "concise": ("وجيز", "Concise"),
    "simplified": ("ميسّر", "Simplified"),
    "linguistic": ("لغوي", "Linguistic"),
    "adabi": ("أدبي", "Literary"),
    "ishari": ("إشاري", "Spiritual (ishārī)"),
    "ilmi": ("علمي", "Scientific"),
    "ijtimaayi": ("اجتماعي", "Social"),
    "mixed": ("مختلط", "Mixed"),
}

ERA_LABELS: Dict[str, Tuple[str, str]] = {
    "companion": ("عصر الصحابة", "Companion era"),
    "tabiin": ("عصر التابعين", "Successor era"),
    "classical": ("كلاسيكي", "Classical"),
    "medieval": ("وسيط", "Medieval"),
    "modern": ("حديث", "Modern"),
    "contemporary": ("معاصر", "Contemporary"),
}

# Shown verbatim in the UI next to any overlap figure.
OVERLAP_DISCLAIMER_AR = (
    "نسبة التشابه اللفظي تقيس الألفاظ المشتركة بين النصين فقط، "
    "وليست حكمًا على اتفاق العلماء أو اختلافهم."
)
OVERLAP_DISCLAIMER_EN = (
    "Lexical overlap measures shared wording between two texts only. "
    "It is not a judgement that the scholars agree or disagree."
)

# Arabic normalisation for token comparison: without stripping diacritics the
# overlap figure is dominated by tashkeel rather than by vocabulary.
_AR_DIACRITICS = re.compile("[ً-ْٰـ]")
_AR_ALEF = re.compile("[آأإٱ]")
_NON_WORD = re.compile(r"[^\w؀-ۿ]+")

# Function words carry no comparative signal and are frequent enough to inflate
# any overlap measure, so they are excluded from the token sets.
_AR_STOPWORDS = {
    "من", "الى", "على", "في", "عن", "ان", "انه", "او", "ثم", "قد", "كان", "هو",
    "هي", "ما", "لا", "الا", "هذا", "هذه", "ذلك", "التي", "الذي", "وهو", "وهي",
    "به", "له", "لهم", "بها", "اي", "قال", "قوله", "تعالى", "وقال", "يعني",
}
_EN_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "that", "this",
    "for", "as", "with", "was", "were", "be", "been", "are", "he", "she", "they",
    "his", "her", "their", "them", "who", "which", "from", "by", "on", "at",
    "said", "says", "say", "not", "but", "has", "have", "had", "will", "would",
}


def _normalise_tokens(text: str, language: str) -> set[str]:
    """Token set used for lexical overlap. Never used for display."""
    if not text:
        return set()
    lowered = text.lower()
    if language == "ar":
        lowered = _AR_DIACRITICS.sub("", lowered)
        lowered = _AR_ALEF.sub("ا", lowered)
        stopwords = _AR_STOPWORDS
    else:
        stopwords = _EN_STOPWORDS
    tokens = {t for t in _NON_WORD.split(lowered) if len(t) > 2}
    return tokens - stopwords


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = len(a | b)
    return round(len(a & b) / union, 4) if union else 0.0


def _catalog_entry(source_id: str) -> Dict[str, Any]:
    """Look up catalogue metadata for a DB source id.

    DB ids carry a language suffix (`tabari_ar`); catalogue keys do not
    (`tabari`). Falls back to an empty dict so a source missing from the
    catalogue still renders, just without the scholarly framing.
    """
    base = re.sub(r"_(ar|en)$", "", source_id)
    return TAFSIR_CATALOG.get(base) or TAFSIR_CATALOG.get(source_id) or {}


def _enum_value(value: Any) -> Optional[str]:
    """Catalogue fields hold enums; DB fields hold plain strings."""
    if value is None:
        return None
    return str(getattr(value, "value", value)).lower()


@dataclass
class ComparisonEntry:
    """One source's tafsir for the requested verse, with its provenance."""

    source_id: str
    name_ar: str
    name_en: str
    author_ar: Optional[str]
    author_en: Optional[str]
    language: str
    era: Optional[str]
    era_label_ar: Optional[str]
    era_label_en: Optional[str]
    death_year_hijri: Optional[int]
    death_year_ce: Optional[int]
    methodology: Optional[str]
    methodology_label_ar: Optional[str]
    methodology_label_en: Optional[str]
    description_ar: Optional[str]
    description_en: Optional[str]
    strengths: List[str]
    reliability_score: Optional[float]
    license_type: Optional[str]
    license_verified: bool
    chunk_id: str
    text: str
    word_count: int
    char_count: int
    scholarly_consensus: Optional[str]
    covers_ayat: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name_ar": self.name_ar,
            "name_en": self.name_en,
            "author_ar": self.author_ar,
            "author_en": self.author_en,
            "language": self.language,
            "era": self.era,
            "era_label_ar": self.era_label_ar,
            "era_label_en": self.era_label_en,
            "death_year_hijri": self.death_year_hijri,
            "death_year_ce": self.death_year_ce,
            "methodology": self.methodology,
            "methodology_label_ar": self.methodology_label_ar,
            "methodology_label_en": self.methodology_label_en,
            "description_ar": self.description_ar,
            "description_en": self.description_en,
            "strengths": self.strengths,
            "reliability_score": self.reliability_score,
            "license_type": self.license_type,
            "license_verified": self.license_verified,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "scholarly_consensus": self.scholarly_consensus,
            "covers_ayat": self.covers_ayat,
        }


class TafsirComparisonService:
    """Assembles a side-by-side view of every seeded tafsir for one verse."""

    async def compare_verse(
        self,
        session: AsyncSession,
        surah: int,
        ayah: int,
        source_ids: Optional[Sequence[str]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return every stored tafsir for `surah:ayah`, with provenance.

        Args:
            source_ids: restrict to these sources; None means all enabled ones.
            language: 'ar' or 'en' to restrict; None means both.
        """
        verse = (
            await session.execute(
                select(QuranVerse).where(
                    QuranVerse.sura_no == surah, QuranVerse.aya_no == ayah
                )
            )
        ).scalar_one_or_none()

        # A chunk may explain a range, so match ranges containing this ayah
        # rather than requiring aya_start == ayah.
        chunk_q = select(TafseerChunk).where(
            TafseerChunk.sura_no == surah,
            TafseerChunk.aya_start <= ayah,
            TafseerChunk.aya_end >= ayah,
        )
        if source_ids:
            chunk_q = chunk_q.where(TafseerChunk.source_id.in_(list(source_ids)))
        chunk_q = chunk_q.order_by(TafseerChunk.source_id, TafseerChunk.chunk_order)
        chunks = (await session.execute(chunk_q)).scalars().all()

        sources = {
            s.id: s
            for s in (await session.execute(select(TafseerSource))).scalars().all()
        }

        entries: List[ComparisonEntry] = []
        for chunk in chunks:
            source = sources.get(chunk.source_id)
            if source is not None and source.is_enabled == 0:
                continue

            lang = (source.language if source else None) or (
                "ar" if chunk.content_ar else "en"
            )
            if language and lang != language:
                continue

            text = (chunk.content_ar if lang == "ar" else chunk.content_en) or ""
            if not text.strip():
                # Fall back to whichever column is populated — some sources
                # store English content while declaring a language of 'en'
                # only in the source row.
                text = (chunk.content_ar or chunk.content_en or "").strip()
            if not text:
                continue

            cat = _catalog_entry(chunk.source_id)
            era = _enum_value(source.era if source else None) or _enum_value(cat.get("era"))
            methodology = _enum_value(source.methodology if source else None) or _enum_value(
                cat.get("methodology")
            )
            era_ar, era_en = ERA_LABELS.get(era or "", (None, None))
            meth_ar, meth_en = METHODOLOGY_LABELS.get(methodology or "", (None, None))

            entries.append(
                ComparisonEntry(
                    source_id=chunk.source_id,
                    name_ar=(source.name_ar if source else cat.get("name_ar", "")) or "",
                    name_en=(source.name_en if source else cat.get("name_en", "")) or "",
                    author_ar=(source.author_ar if source else None) or cat.get("author_ar"),
                    author_en=(source.author_en if source else None) or cat.get("author_en"),
                    language=lang,
                    era=era,
                    era_label_ar=era_ar,
                    era_label_en=era_en,
                    # death_year_hijri is NULL in tafseer_sources for every
                    # seeded row, so the catalogue is the real source here.
                    death_year_hijri=(source.death_year_hijri if source else None)
                    or cat.get("death_year_hijri"),
                    death_year_ce=cat.get("death_year_ce"),
                    methodology=methodology,
                    methodology_label_ar=meth_ar,
                    methodology_label_en=meth_en,
                    description_ar=cat.get("description_ar"),
                    description_en=cat.get("description_en"),
                    strengths=list(cat.get("strengths") or []),
                    reliability_score=source.reliability_score if source else None,
                    license_type=source.license_type if source else None,
                    license_verified=bool(source.license_verified) if source else False,
                    chunk_id=chunk.chunk_id,
                    text=text,
                    word_count=chunk.word_count or len(text.split()),
                    char_count=chunk.char_count or len(text),
                    scholarly_consensus=chunk.scholarly_consensus,
                    covers_ayat=(
                        f"{chunk.aya_start}"
                        if chunk.aya_start == chunk.aya_end
                        else f"{chunk.aya_start}-{chunk.aya_end}"
                    ),
                )
            )

        # Oldest first: reading Tabari before Ibn Kathir before al-Muyassar
        # follows how the tradition itself builds, and keeps ordering stable.
        entries.sort(
            key=lambda e: (
                e.death_year_hijri if e.death_year_hijri is not None else 9999,
                e.source_id,
            )
        )

        return {
            "ok": True,
            "verse_key": f"{surah}:{ayah}",
            "surah": surah,
            "ayah": ayah,
            "verse": {
                "text_uthmani": verse.text_uthmani if verse else None,
                "sura_name_ar": getattr(verse, "sura_name_ar", None) if verse else None,
                "sura_name_en": getattr(verse, "sura_name_en", None) if verse else None,
            },
            "sources_returned": len(entries),
            "entries": [e.to_dict() for e in entries],
            "comparison": self._describe(entries),
        }

    def _describe(self, entries: List[ComparisonEntry]) -> Dict[str, Any]:
        """Descriptive statistics over the retrieved texts. No interpretation."""
        if not entries:
            return {
                "methodology_groups": {},
                "length": {},
                "lexical_overlap": [],
                "disclaimer_ar": OVERLAP_DISCLAIMER_AR,
                "disclaimer_en": OVERLAP_DISCLAIMER_EN,
            }

        groups: Dict[str, List[str]] = {}
        for entry in entries:
            groups.setdefault(entry.methodology or "unspecified", []).append(entry.source_id)

        by_words = sorted(entries, key=lambda e: e.word_count)

        # Only same-language pairs: token overlap between Arabic and English
        # text is meaningless.
        tokens = {e.source_id: _normalise_tokens(e.text, e.language) for e in entries}
        overlap: List[Dict[str, Any]] = []
        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                if a.language != b.language:
                    continue
                overlap.append(
                    {
                        "a": a.source_id,
                        "b": b.source_id,
                        "language": a.language,
                        "jaccard": _jaccard(tokens[a.source_id], tokens[b.source_id]),
                    }
                )
        overlap.sort(key=lambda o: o["jaccard"], reverse=True)

        return {
            "methodology_groups": groups,
            "length": {
                "shortest_source_id": by_words[0].source_id,
                "shortest_word_count": by_words[0].word_count,
                "longest_source_id": by_words[-1].source_id,
                "longest_word_count": by_words[-1].word_count,
                "total_word_count": sum(e.word_count for e in entries),
            },
            "lexical_overlap": overlap,
            "disclaimer_ar": OVERLAP_DISCLAIMER_AR,
            "disclaimer_en": OVERLAP_DISCLAIMER_EN,
        }


tafsir_comparison_service = TafsirComparisonService()
