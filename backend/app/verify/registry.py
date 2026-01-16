"""
QuranStoryRegistry - Canonical registry of ALL Quranic narrative units.

This registry covers:
- قصص الأنبياء (Prophet Stories)
- قصص الأمم (Nation Stories)
- الأمثال (Parables)
- تاريخية (Historical Events)
- الغيب (The Unseen)
- شخصيات مسماة (Named Characters)

GROUNDING RULES:
================
- Every story must have at least one primary_ayah_range
- All ayah ranges must be valid (within surah verse counts)
- Arabic titles and summaries are REQUIRED
- Evidence pointers must reference existing tafsir chunks

CATEGORIES (matching UI requirements):
=====================================
- prophet: قصص الأنبياء
- nation: قصص الأمم / الأمم والشعوب
- parable: الأمثال
- historical: أحداث تاريخية
- unseen: الغيب
- named_char: شخصيات مسماة
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
import json
from pathlib import Path


# =============================================================================
# ENUMERATIONS
# =============================================================================

class StoryCategory(str, Enum):
    """Story categories matching UI requirements."""
    PROPHET = "prophet"           # قصص الأنبياء
    NATION = "nation"             # قصص الأمم
    PARABLE = "parable"           # الأمثال
    HISTORICAL = "historical"     # أحداث تاريخية
    UNSEEN = "unseen"             # الغيب
    NAMED_CHAR = "named_char"     # شخصيات مسماة


class EvidenceBasis(str, Enum):
    """Basis for claims."""
    EXPLICIT = "explicit"    # صريح في القرآن
    INFERRED = "inferred"    # مستنبط من التفسير
    UNKNOWN = "unknown"      # غير محدد


class VerificationStatus(str, Enum):
    """Verification status for audit queue."""
    VERIFIED = "verified"           # تم التحقق
    PENDING_REVIEW = "pending"      # بانتظار المراجعة
    NEEDS_EVIDENCE = "needs_evidence"  # يحتاج أدلة
    FLAGGED = "flagged"             # مُعلَّم للمراجعة


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AyahRange(BaseModel):
    """A range of ayahs within a surah."""
    sura: int = Field(..., ge=1, le=114, description="رقم السورة")
    start: int = Field(..., ge=1, description="بداية الآية")
    end: int = Field(..., ge=1, description="نهاية الآية")

    @field_validator('end')
    @classmethod
    def end_gte_start(cls, v, info):
        if 'start' in info.data and v < info.data['start']:
            raise ValueError('نهاية الآية يجب أن تكون أكبر أو تساوي البداية')
        return v

    @property
    def verse_count(self) -> int:
        return self.end - self.start + 1

    @property
    def reference(self) -> str:
        if self.start == self.end:
            return f"{self.sura}:{self.start}"
        return f"{self.sura}:{self.start}-{self.end}"


class Place(BaseModel):
    """A place mentioned in a story."""
    name_ar: str = Field(..., min_length=1, description="الاسم بالعربية")
    name_en: str = Field(..., min_length=1, description="Name in English")
    basis: EvidenceBasis = Field(default=EvidenceBasis.UNKNOWN)
    ayah_refs: List[str] = Field(default_factory=list, description="مراجع الآيات")


class Person(BaseModel):
    """A person/figure in a story."""
    id: str = Field(..., description="معرف الشخصية")
    name_ar: str = Field(..., min_length=1, description="الاسم بالعربية")
    name_en: str = Field(..., min_length=1, description="Name in English")
    is_prophet: bool = Field(default=False, description="هل هو نبي")
    aliases_ar: List[str] = Field(default_factory=list)
    aliases_en: List[str] = Field(default_factory=list)


class Miracle(BaseModel):
    """A miracle or sign in a story."""
    id: str = Field(..., description="معرف المعجزة")
    name_ar: str = Field(..., min_length=1, description="الاسم بالعربية")
    name_en: str = Field(..., min_length=1, description="Name in English")
    ayah_refs: List[str] = Field(..., min_length=1, description="مراجع الآيات")
    description_ar: Optional[str] = None
    description_en: Optional[str] = None


class EvidencePointer(BaseModel):
    """Pointer to tafsir evidence."""
    source_id: str = Field(..., description="معرف المصدر e.g., ibn_kathir")
    chunk_id: Optional[str] = Field(None, description="معرف المقطع")
    ayah_ref: str = Field(..., description="مرجع الآية e.g., 2:30-33")
    snippet_ar: Optional[str] = Field(None, max_length=500)
    snippet_en: Optional[str] = Field(None, max_length=500)


class StoryEvent(BaseModel):
    """An event within a story (sub-episode)."""
    id: str = Field(..., description="معرف الحدث")
    title_ar: str = Field(..., min_length=1, description="العنوان بالعربية")
    title_en: str = Field(..., min_length=1, description="Title in English")
    narrative_role: str = Field(..., description="الدور السردي")
    chronological_index: int = Field(..., ge=1)
    ayah_range: AyahRange
    summary_ar: str = Field(..., min_length=1, description="الملخص بالعربية")
    summary_en: str = Field(..., min_length=1)
    semantic_tags: List[str] = Field(default_factory=list)
    is_entry_point: bool = Field(default=False)
    evidence: List[EvidencePointer] = Field(default_factory=list)

    @property
    def verse_reference(self) -> str:
        return self.ayah_range.reference


class SecondaryMention(BaseModel):
    """Secondary mention of a story in another location."""
    ayah_range: AyahRange
    mention_type: str = Field(..., description="نوع الإشارة: reference|summary|elaboration")
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    evidence: List[EvidencePointer] = Field(default_factory=list)


class StoryRegistryEntry(BaseModel):
    """A complete story entry in the registry."""

    # Identity
    id: str = Field(..., description="معرف القصة e.g., story_adam")
    slug: str = Field(..., description="الرابط الودي")

    # Titles (Arabic REQUIRED)
    title_ar: str = Field(..., min_length=1, description="العنوان بالعربية - مطلوب")
    title_en: str = Field(..., min_length=1, description="Title in English")
    short_title_ar: Optional[str] = Field(None, max_length=50)
    short_title_en: Optional[str] = Field(None, max_length=50)

    # Classification
    category: StoryCategory = Field(..., description="التصنيف")

    # Coverage
    primary_ayah_ranges: List[AyahRange] = Field(..., min_length=1,
        description="النطاقات الرئيسية للآيات - مطلوب واحد على الأقل")
    secondary_mentions: List[SecondaryMention] = Field(default_factory=list,
        description="الإشارات الثانوية في مواضع أخرى")

    # Entities
    main_persons: List[Person] = Field(default_factory=list)
    places: List[Place] = Field(default_factory=list)
    nations: List[str] = Field(default_factory=list, description="الأمم المذكورة")
    miracles: List[Miracle] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list, description="المواضيع")

    # Content (Arabic REQUIRED)
    summary_ar: str = Field(..., min_length=10, description="الملخص بالعربية - مطلوب")
    summary_en: str = Field(..., min_length=10)
    lessons_ar: List[str] = Field(default_factory=list, description="الدروس بالعربية")
    lessons_en: List[str] = Field(default_factory=list)

    # Events (sub-episodes)
    events: List[StoryEvent] = Field(default_factory=list)

    # Evidence (for summary/claims)
    evidence: List[EvidencePointer] = Field(default_factory=list)

    # Metadata
    era: Optional[str] = Field(None, description="العصر")
    era_basis: EvidenceBasis = Field(default=EvidenceBasis.UNKNOWN)
    verification_status: VerificationStatus = Field(default=VerificationStatus.PENDING_REVIEW)
    is_complete: bool = Field(default=False, description="هل القصة مكتملة")
    needs_review_reason: Optional[str] = Field(None, description="سبب الحاجة للمراجعة")

    @property
    def total_verses(self) -> int:
        """Total verses across all primary ranges."""
        return sum(r.verse_count for r in self.primary_ayah_ranges)

    @property
    def suras_mentioned(self) -> List[int]:
        """All suras where this story appears."""
        suras = set()
        for r in self.primary_ayah_ranges:
            suras.add(r.sura)
        for m in self.secondary_mentions:
            suras.add(m.ayah_range.sura)
        return sorted(suras)

    def has_arabic_content(self) -> bool:
        """Check if all required Arabic content is present."""
        return bool(
            self.title_ar and
            self.summary_ar and
            len(self.summary_ar) >= 10
        )

    def has_evidence(self) -> bool:
        """Check if story has grounding evidence."""
        return len(self.evidence) > 0 or any(e.evidence for e in self.events)


# =============================================================================
# QURAN STORY REGISTRY
# =============================================================================

class QuranStoryRegistry:
    """
    Canonical registry of ALL Quranic narrative units.

    Provides:
    - Loading from JSON manifest
    - Validation of all entries
    - Category enumeration
    - Coverage statistics
    """

    def __init__(self):
        self.stories: Dict[str, StoryRegistryEntry] = {}
        self._quran_metadata: Dict[int, int] = {}  # sura -> ayah_count
        self._load_quran_metadata()

    def _load_quran_metadata(self):
        """Load surah verse counts for validation."""
        # Standard verse counts per surah (Hafs)
        self._quran_metadata = {
            1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75,
            9: 129, 10: 109, 11: 123, 12: 111, 13: 43, 14: 52, 15: 99,
            16: 128, 17: 111, 18: 110, 19: 98, 20: 135, 21: 112, 22: 78,
            23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69,
            30: 60, 31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83,
            37: 182, 38: 88, 39: 75, 40: 85, 41: 54, 42: 53, 43: 89,
            44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
            51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29,
            58: 22, 59: 24, 60: 13, 61: 14, 62: 11, 63: 11, 64: 18,
            65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44, 71: 28,
            72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40,
            79: 46, 80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22,
            86: 17, 87: 19, 88: 26, 89: 30, 90: 20, 91: 15, 92: 21,
            93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
            101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7,
            108: 3, 109: 6, 110: 3, 111: 5, 112: 4, 113: 5, 114: 6
        }

    def get_surah_verse_count(self, sura: int) -> int:
        """Get verse count for a surah."""
        return self._quran_metadata.get(sura, 0)

    def is_valid_ayah_range(self, ayah_range: AyahRange) -> tuple[bool, Optional[str]]:
        """Validate an ayah range against Quran metadata."""
        sura = ayah_range.sura
        if sura < 1 or sura > 114:
            return False, f"سورة غير صالحة: {sura}"

        max_ayah = self.get_surah_verse_count(sura)
        if max_ayah == 0:
            return False, f"لا توجد بيانات للسورة: {sura}"

        if ayah_range.start > max_ayah:
            return False, f"الآية {ayah_range.start} تتجاوز عدد آيات السورة {sura} ({max_ayah})"

        if ayah_range.end > max_ayah:
            return False, f"الآية {ayah_range.end} تتجاوز عدد آيات السورة {sura} ({max_ayah})"

        return True, None

    def add_story(self, story: StoryRegistryEntry) -> None:
        """Add a story to the registry."""
        self.stories[story.id] = story

    def get_story(self, story_id: str) -> Optional[StoryRegistryEntry]:
        """Get a story by ID."""
        return self.stories.get(story_id)

    def get_stories_by_category(self, category: StoryCategory) -> List[StoryRegistryEntry]:
        """Get all stories in a category."""
        return [s for s in self.stories.values() if s.category == category]

    def get_category_counts(self) -> Dict[str, int]:
        """Get count of stories per category."""
        counts = {cat.value: 0 for cat in StoryCategory}
        for story in self.stories.values():
            counts[story.category.value] += 1
        return counts

    def get_empty_categories(self) -> List[StoryCategory]:
        """Get categories with no stories."""
        counts = self.get_category_counts()
        return [StoryCategory(cat) for cat, count in counts.items() if count == 0]

    def validate_all_ranges(self) -> List[Dict[str, Any]]:
        """Validate all ayah ranges in the registry."""
        errors = []
        for story in self.stories.values():
            for i, ayah_range in enumerate(story.primary_ayah_ranges):
                valid, error = self.is_valid_ayah_range(ayah_range)
                if not valid:
                    errors.append({
                        "story_id": story.id,
                        "range_index": i,
                        "range": ayah_range.reference,
                        "error": error,
                        "error_ar": error,
                    })
            for j, mention in enumerate(story.secondary_mentions):
                valid, error = self.is_valid_ayah_range(mention.ayah_range)
                if not valid:
                    errors.append({
                        "story_id": story.id,
                        "mention_index": j,
                        "range": mention.ayah_range.reference,
                        "error": error,
                        "error_ar": error,
                    })
        return errors

    def get_stories_without_arabic(self) -> List[str]:
        """Get story IDs missing Arabic content."""
        return [s.id for s in self.stories.values() if not s.has_arabic_content()]

    def get_stories_without_evidence(self) -> List[str]:
        """Get story IDs missing evidence."""
        return [s.id for s in self.stories.values() if not s.has_evidence()]

    def load_from_manifest(self, manifest_path: Path) -> int:
        """
        Load stories from the stories.json manifest.
        Returns count of stories loaded.
        """
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        loaded = 0
        for story_data in data.get('stories', []):
            try:
                entry = self._convert_manifest_story(story_data)
                self.add_story(entry)
                loaded += 1
            except Exception as e:
                print(f"Error loading story {story_data.get('id', 'unknown')}: {e}")

        return loaded

    def _convert_manifest_story(self, data: Dict[str, Any]) -> StoryRegistryEntry:
        """Convert a manifest story to a registry entry."""

        # Convert segments to ayah ranges
        primary_ranges = []
        events = []

        for seg in data.get('segments', []):
            ayah_range = AyahRange(
                sura=seg['sura_no'],
                start=seg['aya_start'],
                end=seg['aya_end']
            )
            primary_ranges.append(ayah_range)

            # Convert segment evidence
            seg_evidence = []
            for ev in seg.get('evidence', []):
                seg_evidence.append(EvidencePointer(
                    source_id=ev.get('source_id', 'unknown'),
                    chunk_id=ev.get('chunk_id'),
                    ayah_ref=ev.get('ayah_ref', ayah_range.reference),
                    snippet_ar=ev.get('snippet_ar'),
                    snippet_en=ev.get('snippet_en'),
                ))

            # Also create event
            events.append(StoryEvent(
                id=seg['id'],
                title_ar=seg.get('summary_ar', seg.get('summary_en', '')),  # Fallback
                title_en=seg.get('summary_en', ''),
                narrative_role=seg.get('aspect', 'development'),
                chronological_index=seg.get('narrative_order', len(events) + 1),
                ayah_range=ayah_range,
                summary_ar=seg.get('summary_ar', seg.get('summary_en', '')),
                summary_en=seg.get('summary_en', ''),
                semantic_tags=[],
                is_entry_point=(seg.get('narrative_order', 99) == 1),
                evidence=seg_evidence
            ))

        # If no segments, create a default range from suras_mentioned
        if not primary_ranges and data.get('suras_mentioned'):
            # Mark as needing review
            pass

        # Convert main_figures to Person objects
        persons = []
        for fig in data.get('main_figures', []):
            if isinstance(fig, str):
                persons.append(Person(
                    id=fig.lower().replace(' ', '_'),
                    name_ar=fig,  # Will need translation
                    name_en=fig,
                    is_prophet=data.get('category') == 'prophet'
                ))

        # Map category
        category_map = {
            'prophet': StoryCategory.PROPHET,
            'nation': StoryCategory.NATION,
            'parable': StoryCategory.PARABLE,
            'historical': StoryCategory.HISTORICAL,
            'unseen': StoryCategory.UNSEEN,
            'named_char': StoryCategory.NAMED_CHAR,
            'righteous': StoryCategory.NAMED_CHAR,  # Map righteous to named_char
        }
        category = category_map.get(data.get('category', 'historical'), StoryCategory.HISTORICAL)

        # Convert story-level evidence
        story_evidence = []
        for ev in data.get('evidence', []):
            story_evidence.append(EvidencePointer(
                source_id=ev.get('source_id', 'unknown'),
                chunk_id=ev.get('chunk_id'),
                ayah_ref=ev.get('ayah_ref', ''),
                snippet_ar=ev.get('snippet_ar'),
                snippet_en=ev.get('snippet_en'),
            ))

        return StoryRegistryEntry(
            id=data['id'],
            slug=data['id'].replace('story_', ''),
            title_ar=data.get('name_ar', data.get('name_en', 'بدون عنوان')),
            title_en=data.get('name_en', 'Untitled'),
            category=category,
            primary_ayah_ranges=primary_ranges if primary_ranges else [
                AyahRange(sura=1, start=1, end=1)  # Placeholder
            ],
            main_persons=persons,
            themes=data.get('themes', []),
            summary_ar=data.get('summary_ar', data.get('summary_en', 'لا يوجد ملخص')),
            summary_en=data.get('summary_en', 'No summary'),
            events=events,
            evidence=story_evidence,
            verification_status=VerificationStatus.PENDING_REVIEW,
            is_complete=len(events) > 0,
            needs_review_reason="تم الاستيراد من الملف القديم - يحتاج مراجعة" if not data.get('name_ar') else None
        )

    def export_to_json(self, output_path: Path) -> None:
        """Export registry to JSON file."""
        data = {
            "name": "Quran Story Registry",
            "version": "2.0.0",
            "description": "Canonical registry of ALL Quranic narrative units",
            "total_stories": len(self.stories),
            "category_counts": self.get_category_counts(),
            "stories": [s.dict() for s in self.stories.values()]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_audit_queue(self) -> List[StoryRegistryEntry]:
        """Get stories that need review."""
        return [
            s for s in self.stories.values()
            if s.verification_status in (
                VerificationStatus.PENDING_REVIEW,
                VerificationStatus.NEEDS_EVIDENCE,
                VerificationStatus.FLAGGED
            )
        ]

    def get_coverage_stats(self) -> Dict[str, Any]:
        """Get comprehensive coverage statistics."""
        return {
            "total_stories": len(self.stories),
            "category_counts": self.get_category_counts(),
            "empty_categories": [c.value for c in self.get_empty_categories()],
            "stories_without_arabic": len(self.get_stories_without_arabic()),
            "stories_without_evidence": len(self.get_stories_without_evidence()),
            "stories_needing_review": len(self.get_audit_queue()),
            "total_verses_covered": sum(s.total_verses for s in self.stories.values()),
            "suras_with_stories": len(set(
                sura for s in self.stories.values() for sura in s.suras_mentioned
            )),
        }
