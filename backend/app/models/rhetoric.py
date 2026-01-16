"""
Arabic Rhetoric (علم البلاغة) Analysis Models

ONTOLOGY:
=========
Arabic rhetoric is divided into three sciences:
1. علم البيان (ʿIlm al-Bayān) - Clarity/Figures of Speech
   - استعارة (Metaphor), تشبيه (Simile), كناية (Metonymy), مجاز (Trope)

2. علم المعاني (ʿIlm al-Maʿānī) - Semantics
   - إطناب (Amplification), إيجاز (Brevity), تقديم وتأخير (Inversion)
   - استفهام بلاغي (Rhetorical Question)

3. علم البديع (ʿIlm al-Badīʿ) - Embellishment
   - طباق (Antithesis), جناس (Paronomasia), سجع (Rhymed Prose)
   - التفات (Person/Tense Shift)

EPISTEMIC GROUNDING:
===================
All rhetorical device detections MUST be grounded in balagha-focused tafsir sources:
- Al-Zamakhshari (الكشاف) - Primary source for balagha analysis
- Al-Razi (التفسير الكبير) - Philosophical + rhetorical
- Abu Su'ud (إرشاد العقل السليم) - Ottoman rhetorical tradition
- Ibn Ashur (التحرير والتنوير) - Modern linguistic analysis

NO device detection can exist without evidence_chunk_ids pointing to tafsir.

DISCOURSE SEGMENTATION:
======================
Quranic text can be segmented by discourse type:
- NARRATIVE (قصصي): Story narration
- EXHORTATION (وعظي): Moral exhortation
- LEGAL_RULING (تشريعي): Legal rulings
- SUPPLICATION (دعائي): Prayer/supplication
- PROMISE (وعد): Divine promise
- WARNING (وعيد): Warning/threat
- PARABLE (مثلي): Parable/similitude
- ARGUMENTATION (حجاجي): Logical argument

TONE DETECTION:
==============
Emotional tones differ from general sentiment analysis:
- HOPE (رجاء): Emphasis on mercy, forgiveness, reward
- FEAR (خوف): Emphasis on accountability, punishment
- AWE (خشوع): Divine majesty, creation, power
- CONSOLATION (تسلية): Comfort to Prophet/believers
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


# =============================================================================
# ENUMERATIONS
# =============================================================================

class BalaghaCategory(str, Enum):
    """
    Categories of Arabic rhetoric (علم البلاغة).
    The three classical sciences of Arabic rhetorical analysis.
    """
    BAYAAN = "bayaan"      # علم البيان - Figures of speech/clarity
    MAANI = "maani"        # علم المعاني - Semantics/meaning
    BADEEA = "badeea"      # علم البديع - Embellishment/ornamentation


class RhetoricalDeviceKey(str, Enum):
    """
    Keys for rhetorical devices in the Quranic Arabic tradition.
    Each device belongs to one of the three balagha categories.
    """
    # =================================
    # علم البيان (Bayān) - Figures of Speech
    # =================================
    ISTIAARA = "istiaara"                 # استعارة - Metaphor
    ISTIAARA_TASRIHIYYA = "istiaara_tasrihiyya"  # استعارة تصريحية - Explicit metaphor
    ISTIAARA_MAKNIYYA = "istiaara_makniyya"      # استعارة مكنية - Implied metaphor
    TASHBIH = "tashbih"                   # تشبيه - Simile
    TASHBIH_MURSAL = "tashbih_mursal"     # تشبيه مرسل - Explicit simile with particle
    TASHBIH_BALIGH = "tashbih_baligh"     # تشبيه بليغ - Compressed simile
    TASHBIH_TAMTHILI = "tashbih_tamthili" # تشبيه تمثيلي - Extended simile
    KINAYA = "kinaya"                     # كناية - Metonymy
    MAJAZ = "majaz"                       # مجاز - Trope/figurative language
    MAJAZ_MURSAL = "majaz_mursal"         # مجاز مرسل - Metonymic trope
    MAJAZ_AQLI = "majaz_aqli"             # مجاز عقلي - Intellectual trope

    # =================================
    # علم المعاني (Maʿānī) - Semantics
    # =================================
    ITNAAB = "itnaab"                     # إطناب - Amplification
    IJAZ = "ijaz"                         # إيجاز - Brevity/ellipsis
    IJAZ_HAZF = "ijaz_hazf"               # إيجاز بالحذف - Ellipsis
    IJAZ_QISAR = "ijaz_qisar"             # إيجاز بالقصر - Compression
    TAQDIM = "taqdim"                     # تقديم وتأخير - Inversion/fronting
    QASR = "qasr"                         # قصر - Restriction
    FASIL = "fasil"                       # فصل - Asyndeton
    WASIL = "wasil"                       # وصل - Syndeton/polysyndeton
    ISTIFHAM = "istifham"                 # استفهام بلاغي - Rhetorical question
    NIDA = "nida"                         # نداء - Vocative/apostrophe
    TAMANNI = "tamanni"                   # تمني - Optative expression
    AMR = "amr"                           # أمر بلاغي - Rhetorical command
    NAHY = "nahy"                         # نهي بلاغي - Rhetorical prohibition

    # =================================
    # علم البديع (Badīʿ) - Embellishment
    # =================================
    TIBAQ = "tibaq"                       # طباق - Antithesis
    TIBAQ_IJABI = "tibaq_ijabi"           # طباق إيجابي - Positive antithesis
    TIBAQ_SALBI = "tibaq_salbi"           # طباق سلبي - Negative antithesis
    MUQABALA = "muqabala"                 # مقابلة - Parallelism
    JINAS = "jinas"                       # جناس - Paronomasia/wordplay
    JINAS_TAM = "jinas_tam"               # جناس تام - Perfect paronomasia
    JINAS_NAQIS = "jinas_naqis"           # جناس ناقص - Imperfect paronomasia
    SAJ = "saj"                           # سجع - Rhymed prose
    ILTIFAT = "iltifat"                   # التفات - Person/tense shift
    TAWRIYA = "tawriya"                   # تورية - Double entendre
    TAQSIM = "taqsim"                     # تقسيم - Division
    LIFF_WA_NASHR = "liff_wa_nashr"       # لف ونشر - Chiasmus
    TANSIQ_AL_SIFAT = "tansiq_al_sifat"   # تنسيق الصفات - Attribute ordering
    RADD_AL_AJZ = "radd_al_ajz"           # رد العجز على الصدر - Envelope structure


class DiscourseType(str, Enum):
    """
    Types of Quranic discourse segments.
    Used to classify contiguous verse ranges by their communicative function.
    """
    NARRATIVE = "narrative"              # قصصي - Story narration
    EXHORTATION = "exhortation"          # وعظي - Moral exhortation
    LEGAL_RULING = "legal_ruling"        # تشريعي - Legal rulings (ahkam)
    SUPPLICATION = "supplication"        # دعائي - Prayer/supplication
    PROMISE = "promise"                  # وعد - Divine promise
    WARNING = "warning"                  # وعيد - Warning/threat
    PARABLE = "parable"                  # مثلي - Parable/similitude
    ARGUMENTATION = "argumentation"      # حجاجي - Logical argument/debate
    DESCRIPTION = "description"          # وصفي - Description (paradise, hell, etc.)
    DIALOGUE = "dialogue"                # حواري - Dialogue/conversation
    PRAISE = "praise"                    # تحميدي - Praise of Allah
    OATH = "oath"                        # قسمي - Oath/swearing


class ToneType(str, Enum):
    """
    Emotional tones in Quranic text.
    Different from general sentiment - specific to Quranic emotional contexts.
    """
    HOPE = "hope"                        # رجاء - Hope/expectation
    FEAR = "fear"                        # خوف - Fear/reverence
    AWE = "awe"                          # خشوع - Awe/humility before Allah
    ADMONISHMENT = "admonishment"        # تذكير - Reminder/admonishment
    GLAD_TIDINGS = "glad_tidings"        # بشارة - Good news
    WARNING = "warning"                  # تحذير - Warning
    CONSOLATION = "consolation"          # تسلية - Consolation/comfort
    GRATITUDE = "gratitude"              # شكر - Gratitude
    CERTAINTY = "certainty"              # يقين - Certainty/conviction
    URGENCY = "urgency"                  # استعجال - Urgency
    COMPASSION = "compassion"            # رحمة - Compassion/mercy
    REBUKE = "rebuke"                    # تأنيب - Rebuke/reproach


# =============================================================================
# RHETORICAL DEVICE TYPE MODEL
# =============================================================================

class RhetoricalDeviceType(Base):
    """
    Canonical registry of Arabic rhetorical devices (علم البلاغة).

    This table stores the taxonomy of rhetorical devices, organized by
    the three classical sciences of Arabic rhetoric (balagha).
    """
    __tablename__ = "rhetorical_device_types"

    id = Column(String(50), primary_key=True)  # e.g., "istiaara", "tashbih"
    slug = Column(String(50), nullable=False, unique=True, index=True)

    # Bilingual names
    name_ar = Column(String(200), nullable=False)  # Arabic term: استعارة
    name_en = Column(String(200), nullable=False)  # English: Metaphor

    # Category (علم البيان / علم المعاني / علم البديع)
    category = Column(String(50), nullable=False, index=True)  # From BalaghaCategory

    # Definitions
    definition_ar = Column(Text, nullable=True)
    definition_en = Column(Text, nullable=True)

    # Examples from Quran (JSON array)
    # Format: [{"sura_no": 2, "ayah_no": 16, "text_ar": "...", "explanation_ar": "..."}]
    examples_json = Column(JSONB, nullable=True)

    # Sub-types for devices with variations
    # Format: [{"id": "istiaara_tasrihiyya", "name_ar": "استعارة تصريحية", "name_en": "Explicit Metaphor"}]
    sub_types_json = Column(JSONB, nullable=True)

    # Hierarchy (for sub-devices)
    parent_device_id = Column(String(50), ForeignKey("rhetorical_device_types.id"), nullable=True)

    # Display
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("RhetoricalDeviceType", remote_side=[id], backref="sub_devices")
    occurrences = relationship("RhetoricalOccurrence", back_populates="device_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RhetoricalDeviceType {self.id}: {self.name_ar} ({self.name_en})>"

    def to_dict(self, language: str = "en") -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name_ar if language == "ar" else self.name_en,
            "name_ar": self.name_ar,
            "name_en": self.name_en,
            "category": self.category,
            "category_label": BALAGHA_CATEGORY_TRANSLATIONS.get(self.category, {}).get(language, self.category),
            "definition": self.definition_ar if language == "ar" else self.definition_en,
            "examples": self.examples_json,
            "sub_types": self.sub_types_json,
            "parent_device_id": self.parent_device_id,
            "is_active": self.is_active,
        }


# =============================================================================
# RHETORICAL OCCURRENCE MODEL
# =============================================================================

class RhetoricalOccurrence(Base):
    """
    Occurrence of a rhetorical device in the Quran.

    EPISTEMIC REQUIREMENT:
    Every occurrence MUST have evidence_chunk_ids from balagha-focused tafsirs.
    The database has a CHECK constraint enforcing at least one evidence chunk.
    """
    __tablename__ = "rhetorical_occurrences"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to device type
    device_type_id = Column(String(50), ForeignKey("rhetorical_device_types.id"), nullable=False, index=True)

    # Verse location
    sura_no = Column(Integer, nullable=False, index=True)
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)

    # The specific Arabic text exhibiting the device
    text_snippet_ar = Column(Text, nullable=True)

    # Explanation of why this is classified as this device
    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)

    # CRITICAL: Tafsir evidence chunk IDs (MANDATORY)
    # Format: ["zamakhshari:2:16", "razi:2:16"]
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Confidence score (0.0 - 1.0)
    confidence = Column(Float, default=1.0)

    # Source of detection
    # Values: "balagha_tafsir", "curated", "llm_extraction"
    source = Column(String(100), nullable=True)

    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    device_type = relationship("RhetoricalDeviceType", back_populates="occurrences")

    __table_args__ = (
        Index("ix_rhetorical_occ_device", "device_type_id"),
        Index("ix_rhetorical_occ_ayah", "sura_no", "ayah_start"),
        Index("ix_rhetorical_occ_verified", "is_verified"),
        Index("ix_rhetorical_occ_source", "source"),
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_occurrence_has_evidence"
        ),
    )

    def __repr__(self):
        return f"<RhetoricalOccurrence {self.device_type_id} @ {self.sura_no}:{self.ayah_start}>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference string."""
        if self.ayah_end and self.ayah_end != self.ayah_start:
            return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"
        return f"{self.sura_no}:{self.ayah_start}"

    def to_dict(self, language: str = "en") -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            "id": self.id,
            "device_type_id": self.device_type_id,
            "verse_reference": self.verse_reference,
            "sura_no": self.sura_no,
            "ayah_start": self.ayah_start,
            "ayah_end": self.ayah_end,
            "text_snippet_ar": self.text_snippet_ar,
            "explanation": self.explanation_ar if language == "ar" else self.explanation_en,
            "evidence_count": len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0,
            "confidence": self.confidence,
            "source": self.source,
            "is_verified": self.is_verified,
        }


# =============================================================================
# DISCOURSE SEGMENT MODEL
# =============================================================================

class DiscourseSegment(Base):
    """
    Discourse segment classification for contiguous verse ranges.

    Classifies sections of the Quran by their communicative function:
    narrative, legal ruling, exhortation, supplication, etc.
    """
    __tablename__ = "discourse_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Verse range
    sura_no = Column(Integer, nullable=False, index=True)
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)

    # Discourse type (from DiscourseType enum)
    discourse_type = Column(String(50), nullable=False, index=True)

    # Optional sub-classification
    sub_type = Column(String(50), nullable=True)

    # Titles and summaries
    title_ar = Column(String(300), nullable=True)
    title_en = Column(String(300), nullable=True)
    summary_ar = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    # Link to story (for NARRATIVE type)
    linked_story_id = Column(String(100), nullable=True)

    # Story segment IDs for detailed narrative linking
    linked_segment_ids = Column(ARRAY(String), nullable=True)

    # Evidence grounding (MANDATORY)
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Confidence
    confidence = Column(Float, default=1.0)

    # Source and verification
    source = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_discourse_type", "discourse_type"),
        Index("ix_discourse_ayah", "sura_no", "ayah_start"),
        Index("ix_discourse_sura", "sura_no"),
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_discourse_has_evidence"
        ),
    )

    def __repr__(self):
        return f"<DiscourseSegment {self.discourse_type} @ {self.sura_no}:{self.ayah_start}-{self.ayah_end}>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference string."""
        return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"

    def to_dict(self, language: str = "en") -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            "id": self.id,
            "verse_reference": self.verse_reference,
            "sura_no": self.sura_no,
            "ayah_start": self.ayah_start,
            "ayah_end": self.ayah_end,
            "discourse_type": self.discourse_type,
            "type_label": DISCOURSE_TYPE_TRANSLATIONS.get(self.discourse_type, {}).get(language, self.discourse_type),
            "sub_type": self.sub_type,
            "title": self.title_ar if language == "ar" else self.title_en,
            "summary": self.summary_ar if language == "ar" else self.summary_en,
            "linked_story_id": self.linked_story_id,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
        }


# =============================================================================
# VERSE TONE MODEL
# =============================================================================

class VerseTone(Base):
    """
    Emotional tone annotation for verse ranges.

    Tags verses with emotional context grounded in tafsir interpretation.
    Multiple tones can coexist in the same verse range.
    """
    __tablename__ = "verse_tones"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Verse range
    sura_no = Column(Integer, nullable=False, index=True)
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)

    # Tone type (from ToneType enum)
    tone_type = Column(String(50), nullable=False, index=True)

    # Intensity (0.0 - 1.0 scale)
    intensity = Column(Float, default=0.5)

    # Explanations
    explanation_ar = Column(Text, nullable=True)
    explanation_en = Column(Text, nullable=True)

    # Evidence grounding (MANDATORY)
    evidence_chunk_ids = Column(ARRAY(String), nullable=False)

    # Confidence
    confidence = Column(Float, default=1.0)

    # Source and verification
    source = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tone_type", "tone_type"),
        Index("ix_tone_ayah", "sura_no", "ayah_start"),
        Index("ix_tone_sura", "sura_no"),
        Index("ix_tone_intensity", "intensity"),
        CheckConstraint(
            "array_length(evidence_chunk_ids, 1) >= 1",
            name="ck_tone_has_evidence"
        ),
    )

    def __repr__(self):
        return f"<VerseTone {self.tone_type} @ {self.sura_no}:{self.ayah_start}>"

    @property
    def verse_reference(self) -> str:
        """Get verse reference string."""
        if self.ayah_end and self.ayah_end != self.ayah_start:
            return f"{self.sura_no}:{self.ayah_start}-{self.ayah_end}"
        return f"{self.sura_no}:{self.ayah_start}"

    def to_dict(self, language: str = "en") -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            "id": self.id,
            "verse_reference": self.verse_reference,
            "sura_no": self.sura_no,
            "ayah_start": self.ayah_start,
            "ayah_end": self.ayah_end,
            "tone_type": self.tone_type,
            "tone_label": TONE_TYPE_TRANSLATIONS.get(self.tone_type, {}).get(language, self.tone_type),
            "intensity": self.intensity,
            "explanation": self.explanation_ar if language == "ar" else self.explanation_en,
            "evidence_count": len(self.evidence_chunk_ids) if self.evidence_chunk_ids else 0,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
        }


# =============================================================================
# TRANSLATION DICTIONARIES
# =============================================================================

BALAGHA_CATEGORY_TRANSLATIONS = {
    "bayaan": {"ar": "علم البيان", "en": "Figures of Speech"},
    "maani": {"ar": "علم المعاني", "en": "Semantics"},
    "badeea": {"ar": "علم البديع", "en": "Embellishment"},
}

DISCOURSE_TYPE_TRANSLATIONS = {
    "narrative": {"ar": "قصصي", "en": "Narrative"},
    "exhortation": {"ar": "وعظي", "en": "Exhortation"},
    "legal_ruling": {"ar": "تشريعي", "en": "Legal Ruling"},
    "supplication": {"ar": "دعائي", "en": "Supplication"},
    "promise": {"ar": "وعد", "en": "Promise"},
    "warning": {"ar": "وعيد", "en": "Warning"},
    "parable": {"ar": "مثلي", "en": "Parable"},
    "argumentation": {"ar": "حجاجي", "en": "Argumentation"},
    "description": {"ar": "وصفي", "en": "Description"},
    "dialogue": {"ar": "حواري", "en": "Dialogue"},
    "praise": {"ar": "تحميدي", "en": "Praise"},
    "oath": {"ar": "قسمي", "en": "Oath"},
}

TONE_TYPE_TRANSLATIONS = {
    "hope": {"ar": "رجاء", "en": "Hope"},
    "fear": {"ar": "خوف", "en": "Fear"},
    "awe": {"ar": "خشوع", "en": "Awe"},
    "admonishment": {"ar": "تذكير", "en": "Admonishment"},
    "glad_tidings": {"ar": "بشارة", "en": "Glad Tidings"},
    "warning": {"ar": "تحذير", "en": "Warning"},
    "consolation": {"ar": "تسلية", "en": "Consolation"},
    "gratitude": {"ar": "شكر", "en": "Gratitude"},
    "certainty": {"ar": "يقين", "en": "Certainty"},
    "urgency": {"ar": "استعجال", "en": "Urgency"},
    "compassion": {"ar": "رحمة", "en": "Compassion"},
    "rebuke": {"ar": "تأنيب", "en": "Rebuke"},
}

RHETORICAL_DEVICE_TRANSLATIONS = {
    # Bayaan
    "istiaara": {"ar": "استعارة", "en": "Metaphor"},
    "tashbih": {"ar": "تشبيه", "en": "Simile"},
    "kinaya": {"ar": "كناية", "en": "Metonymy"},
    "majaz": {"ar": "مجاز", "en": "Trope"},
    # Maani
    "itnaab": {"ar": "إطناب", "en": "Amplification"},
    "ijaz": {"ar": "إيجاز", "en": "Brevity"},
    "taqdim": {"ar": "تقديم وتأخير", "en": "Inversion"},
    "istifham": {"ar": "استفهام بلاغي", "en": "Rhetorical Question"},
    # Badeea
    "tibaq": {"ar": "طباق", "en": "Antithesis"},
    "jinas": {"ar": "جناس", "en": "Paronomasia"},
    "saj": {"ar": "سجع", "en": "Rhymed Prose"},
    "iltifat": {"ar": "التفات", "en": "Person Shift"},
}
