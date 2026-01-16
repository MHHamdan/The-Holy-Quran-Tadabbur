"""
Quran Search Service - Comprehensive search across all verses.

Features:
1. Exact word/phrase matching with context highlighting
2. Semantic similarity search with related concepts
3. TF-IDF scoring for relevance ranking
4. Word categorization and grammatical analysis
5. Analytics: frequency, distribution by sura/juz

Arabic: خدمة البحث في القرآن الكريم
"""

import re
import math
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum
from collections import defaultdict

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import QuranVerse, Translation
from app.services.quran_text_utils import (
    parse_multi_concept_query,
    expand_bilingual_query,
    get_concept_expansions,
    find_concept_matches,
    preprocess_for_similarity,
    ParsedQuery,
    HighlightedConcept,
    BILINGUAL_CONCEPTS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ARABIC TEXT UTILITIES
# =============================================================================

# Arabic diacritics (tashkeel) for normalization
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670]')

# Alef variants to normalize
ALEF_VARIANTS = {
    '\u0622': '\u0627',  # آ -> ا (Alef with Madda)
    '\u0623': '\u0627',  # أ -> ا (Alef with Hamza Above)
    '\u0625': '\u0627',  # إ -> ا (Alef with Hamza Below)
    '\u0671': '\u0627',  # ٱ -> ا (Alef Wasla)
}

# Ya/Alef Maqsura normalization
YA_VARIANTS = {
    '\u0649': '\u064A',  # ى -> ي (Alef Maqsura to Ya)
}

# Ta Marbuta
TA_MARBUTA = {
    '\u0629': '\u0647',  # ة -> ه
}

# Arabic stop words to exclude from TF-IDF
ARABIC_STOP_WORDS = {
    'في', 'من', 'إلى', 'على', 'عن', 'مع', 'أن', 'إن', 'ما', 'لا',
    'هو', 'هي', 'هم', 'هن', 'أنا', 'نحن', 'أنت', 'أنتم', 'أنتن',
    'هذا', 'هذه', 'ذلك', 'تلك', 'الذي', 'التي', 'الذين', 'اللاتي',
    'كان', 'كانت', 'كانوا', 'يكون', 'تكون', 'يكونون',
    'قال', 'قالوا', 'قل', 'قالت',
    'و', 'ف', 'ب', 'ل', 'ك', 'ثم', 'أو', 'بل', 'لكن', 'حتى',
    'إذ', 'إذا', 'لو', 'لولا', 'كي', 'لئن', 'لقد',
    'قد', 'لم', 'لن', 'سوف', 'س',
    'يا', 'أيها', 'أيتها',
    'كل', 'بعض', 'غير', 'كلا', 'كلتا',
}


def normalize_arabic(text: str, remove_diacritics: bool = True) -> str:
    """
    Normalize Arabic text for search matching.

    - Removes diacritics (tashkeel)
    - Normalizes Alef variants
    - Normalizes Ya/Alef Maqsura
    - Normalizes Ta Marbuta (optional)
    """
    if not text:
        return ""

    result = text

    # Remove diacritics
    if remove_diacritics:
        result = ARABIC_DIACRITICS.sub('', result)

    # Normalize Alef variants
    for variant, normalized in ALEF_VARIANTS.items():
        result = result.replace(variant, normalized)

    # Normalize Ya
    for variant, normalized in YA_VARIANTS.items():
        result = result.replace(variant, normalized)

    return result


def extract_words(text: str) -> List[str]:
    """Extract Arabic words from text, filtering stop words."""
    if not text:
        return []

    # Normalize first
    normalized = normalize_arabic(text)

    # Split on non-Arabic characters
    words = re.findall(r'[\u0600-\u06FF]+', normalized)

    # Filter stop words and short words
    return [w for w in words if w not in ARABIC_STOP_WORDS and len(w) > 1]


# =============================================================================
# THEMATIC DETECTION (for filtering)
# =============================================================================

# Theme keywords for automatic categorization
THEME_KEYWORDS: Dict[str, List[str]] = {
    "tawheed": [
        "الله", "رب", "إله", "واحد", "أحد", "صمد", "خالق", "الرحمن", "الرحيم",
        "عليم", "حكيم", "قدير", "سميع", "بصير", "حي", "قيوم"
    ],
    "prophets": [
        "نبي", "رسول", "محمد", "موسى", "عيسى", "إبراهيم", "نوح", "آدم",
        "يوسف", "داود", "سليمان", "يعقوب", "إسحاق", "إسماعيل", "يونس"
    ],
    "afterlife": [
        "قيامة", "آخرة", "جنة", "نار", "جهنم", "فردوس", "حساب", "بعث",
        "ثواب", "عقاب", "يوم الدين", "صراط", "ميزان"
    ],
    "worship": [
        "صلاة", "زكاة", "صوم", "حج", "عبادة", "سجود", "ركوع", "قيام",
        "دعاء", "ذكر", "تسبيح", "استغفار"
    ],
    "ethics": [
        "صبر", "شكر", "تقوى", "إحسان", "عدل", "صدق", "أمانة", "رحمة",
        "حلم", "تواضع", "كرم", "برّ"
    ],
    "law": [
        "حلال", "حرام", "فريضة", "واجب", "حكم", "قصاص", "حدود", "ميراث",
        "نكاح", "طلاق", "بيع", "ربا"
    ],
    "history": [
        "قوم", "فرعون", "قريش", "بني إسرائيل", "أصحاب", "مدين", "عاد", "ثمود",
        "بدر", "أحد", "الفتح"
    ],
    "nature": [
        "سماء", "أرض", "شمس", "قمر", "نجوم", "ماء", "جبال", "بحر",
        "نبات", "حيوان", "خلق", "آية"
    ],
    "guidance": [
        "هدى", "نور", "سبيل", "صراط", "حق", "باطل", "ضلال", "رشد",
        "علم", "حكمة", "بصيرة"
    ],
    "community": [
        "مؤمن", "مسلم", "كافر", "منافق", "أمة", "قوم", "ناس", "جماعة",
        "أهل", "بني"
    ],
}


def detect_theme(text: str) -> Set[str]:
    """Detect thematic categories in text."""
    normalized = normalize_arabic(text)
    detected: Set[str] = set()

    for theme_id, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if normalize_arabic(keyword) in normalized:
                detected.add(theme_id)
                break

    return detected


# =============================================================================
# ARABIC ROOT EXTRACTION (جذور الكلمات العربية)
# =============================================================================

# Common Arabic roots and their derived forms
# Format: root -> [derived words that share this root]
ARABIC_ROOTS: Dict[str, List[str]] = {
    # الرحمة
    "رحم": ["رحمة", "رحيم", "رحمن", "رحمتك", "رحمته", "يرحم", "ارحم", "مرحوم", "رحماء", "رحمات"],
    # الصبر
    "صبر": ["صبر", "صابر", "صبور", "صابرين", "اصبر", "يصبر", "صابرون", "مصابر"],
    # الإيمان
    "امن": ["إيمان", "مؤمن", "مؤمنون", "مؤمنين", "آمن", "آمنوا", "يؤمن", "أمان", "أمين", "مأمون"],
    # العلم
    "علم": ["علم", "عالم", "عليم", "علماء", "يعلم", "معلوم", "معلم", "تعلم", "علمنا", "علمك"],
    # الهداية
    "هدى": ["هدى", "هادي", "هداية", "يهدي", "اهدنا", "مهتدي", "مهتدون", "هداهم"],
    # التوبة
    "توب": ["توبة", "تائب", "تائبين", "تابوا", "يتوب", "توب", "متاب"],
    # الحكمة
    "حكم": ["حكمة", "حكيم", "حاكم", "حكم", "يحكم", "محكم", "حكماء", "أحكام"],
    # الصلاة
    "صلى": ["صلاة", "صلوات", "صلى", "يصلي", "مصلى", "مصلين", "صلوا"],
    # الزكاة
    "زكى": ["زكاة", "زكي", "تزكية", "يزكي", "زكى", "أزكى"],
    # الخلق
    "خلق": ["خلق", "خالق", "خلق", "مخلوق", "يخلق", "خلقكم", "خلقنا"],
    # السمع
    "سمع": ["سمع", "سميع", "سامع", "يسمع", "استمع", "مسموع", "أسماع"],
    # البصر
    "بصر": ["بصر", "بصير", "أبصار", "يبصر", "بصيرة", "مبصر", "أبصر"],
    # الكفر
    "كفر": ["كفر", "كافر", "كافرون", "كافرين", "كفروا", "يكفر", "مكفر"],
    # الشكر
    "شكر": ["شكر", "شاكر", "شكور", "شاكرين", "يشكر", "اشكر", "مشكور"],
    # القول
    "قول": ["قول", "قال", "قالوا", "قل", "يقول", "قائل", "قولهم", "أقوال"],
    # الحياة
    "حيي": ["حياة", "حي", "يحيي", "أحياء", "محيي", "حية", "استحياء"],
    # الموت
    "موت": ["موت", "ميت", "يموت", "ميتة", "موتى", "أمات", "مميت"],
    # الجنة
    "جنن": ["جنة", "جنات", "جنان", "مجنون", "جن"],
    # النار
    "نور": ["نور", "أنوار", "منير", "نار", "نيران", "أنار", "ينير"],
    # الحق
    "حقق": ["حق", "حقيقة", "يحق", "حاق", "محق", "أحق", "حقوق"],
    # الباطل
    "بطل": ["باطل", "أبطل", "يبطل", "بطلان"],
    # الظلم
    "ظلم": ["ظلم", "ظالم", "ظالمون", "ظالمين", "ظلموا", "يظلم", "مظلوم"],
    # العدل
    "عدل": ["عدل", "عادل", "يعدل", "معدلة", "عدالة"],
    # الذكر
    "ذكر": ["ذكر", "ذاكر", "يذكر", "ذكرى", "مذكور", "تذكرة", "اذكر"],
    # الدعاء
    "دعو": ["دعاء", "دعوة", "يدعو", "ادع", "داع", "مدعو"],
    # الغفر
    "غفر": ["غفر", "غفور", "مغفرة", "يغفر", "استغفر", "غافر", "غفران"],
    # العذاب
    "عذب": ["عذاب", "معذب", "يعذب", "عذبه", "معذبين"],
    # الأرض
    "ارض": ["أرض", "أرضين"],
    # السماء
    "سمو": ["سماء", "سماوات", "سما", "يسمو"],
    # الفلاح
    "فلح": ["فلاح", "مفلح", "مفلحون", "يفلح", "أفلح"],
}


def extract_root(word: str) -> Optional[str]:
    """
    Extract the probable Arabic root from a word.

    Uses pattern matching and a root dictionary for common words.
    Returns the 3-letter root if found.

    Arabic: استخراج الجذر العربي من الكلمة
    """
    normalized = normalize_arabic(word)

    # Check if word matches any known derived forms
    for root, derived_words in ARABIC_ROOTS.items():
        for derived in derived_words:
            if normalize_arabic(derived) == normalized or normalized in normalize_arabic(derived):
                return root

    # Simple extraction: remove common prefixes and suffixes
    # This is a heuristic approach
    stripped = normalized

    # Remove common prefixes
    prefixes = ['ال', 'و', 'ف', 'ب', 'ل', 'ك', 'س', 'است', 'ت', 'ي', 'ن', 'ا']
    for prefix in prefixes:
        if stripped.startswith(prefix) and len(stripped) > 3:
            stripped = stripped[len(prefix):]
            break

    # Remove common suffixes
    suffixes = ['ون', 'ين', 'ات', 'ان', 'ة', 'ه', 'ها', 'هم', 'نا', 'كم', 'ي']
    for suffix in suffixes:
        if stripped.endswith(suffix) and len(stripped) > 3:
            stripped = stripped[:-len(suffix)]
            break

    # Return first 3 letters as probable root (if long enough)
    if len(stripped) >= 3:
        return stripped[:3]

    return None


def get_words_by_root(root: str) -> List[str]:
    """
    Get all words derived from a specific root.

    Arabic: الحصول على جميع الكلمات المشتقة من جذر معين
    """
    root_normalized = normalize_arabic(root)

    if root_normalized in ARABIC_ROOTS:
        return ARABIC_ROOTS[root_normalized]

    # Also check if any root contains this substring
    results = []
    for r, words in ARABIC_ROOTS.items():
        if root_normalized in r or r in root_normalized:
            results.extend(words)

    return results


def expand_by_root(word: str) -> Set[str]:
    """
    Expand a search word by finding related words from the same root.

    Arabic: توسيع البحث بالكلمات المشتقة من نفس الجذر
    """
    root = extract_root(word)
    if not root:
        return set()

    derived = get_words_by_root(root)
    return set(derived)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class GrammaticalRole(str, Enum):
    """Arabic grammatical roles (إعراب)."""
    SUBJECT = "subject"           # فاعل
    OBJECT = "object"             # مفعول به
    PREDICATE = "predicate"       # خبر
    VERB = "verb"                 # فعل
    NOUN = "noun"                 # اسم
    ADJECTIVE = "adjective"       # صفة
    ADVERB = "adverb"             # ظرف
    PREPOSITION = "preposition"   # حرف جر
    PARTICLE = "particle"         # حرف
    PRONOUN = "pronoun"           # ضمير
    CONJUNCTION = "conjunction"   # حرف عطف
    UNKNOWN = "unknown"           # غير محدد


class SentenceType(str, Enum):
    """Arabic sentence types."""
    VERBAL = "verbal"         # جملة فعلية
    NOMINAL = "nominal"       # جملة اسمية
    CONDITIONAL = "conditional"  # جملة شرطية
    INTERROGATIVE = "interrogative"  # جملة استفهامية
    IMPERATIVE = "imperative"  # جملة أمرية
    UNKNOWN = "unknown"


# Arabic labels
GRAMMATICAL_ROLE_AR = {
    GrammaticalRole.SUBJECT: "فاعل",
    GrammaticalRole.OBJECT: "مفعول به",
    GrammaticalRole.PREDICATE: "خبر",
    GrammaticalRole.VERB: "فعل",
    GrammaticalRole.NOUN: "اسم",
    GrammaticalRole.ADJECTIVE: "صفة",
    GrammaticalRole.ADVERB: "ظرف",
    GrammaticalRole.PREPOSITION: "حرف جر",
    GrammaticalRole.PARTICLE: "حرف",
    GrammaticalRole.PRONOUN: "ضمير",
    GrammaticalRole.CONJUNCTION: "حرف عطف",
    GrammaticalRole.UNKNOWN: "غير محدد",
}

SENTENCE_TYPE_AR = {
    SentenceType.VERBAL: "جملة فعلية",
    SentenceType.NOMINAL: "جملة اسمية",
    SentenceType.CONDITIONAL: "جملة شرطية",
    SentenceType.INTERROGATIVE: "جملة استفهامية",
    SentenceType.IMPERATIVE: "جملة أمرية",
    SentenceType.UNKNOWN: "غير محددة",
}


@dataclass
class SearchMatch:
    """A single search match with context and metadata."""
    verse_id: int
    sura_no: int
    sura_name_ar: str
    sura_name_en: str
    aya_no: int
    text_uthmani: str
    text_imlaei: str
    page_no: int
    juz_no: int

    # Match details
    match_positions: List[Tuple[int, int]] = field(default_factory=list)  # (start, end) positions
    highlighted_text: str = ""  # Text with matches highlighted
    context_before: str = ""  # Words before the match
    context_after: str = ""   # Words after the match

    # Scoring
    relevance_score: float = 0.0
    tfidf_score: float = 0.0
    exact_match: bool = False

    # Grammatical analysis (populated by LLM)
    word_role: Optional[GrammaticalRole] = None
    word_role_ar: str = ""
    sentence_type: Optional[SentenceType] = None
    sentence_type_ar: str = ""
    grammatical_notes: str = ""


@dataclass
class SearchResult:
    """Complete search result with statistics."""
    query: str
    query_normalized: str
    total_matches: int
    matches: List[SearchMatch]

    # Distribution statistics
    sura_distribution: Dict[int, int] = field(default_factory=dict)  # sura_no -> count
    juz_distribution: Dict[int, int] = field(default_factory=dict)   # juz_no -> count
    page_distribution: Dict[int, int] = field(default_factory=dict)  # page_no -> count

    # Related terms found
    related_terms: List[str] = field(default_factory=list)

    # Timing
    search_time_ms: float = 0.0


@dataclass
class WordAnalytics:
    """Analytics for word occurrence patterns."""
    word: str
    word_normalized: str
    total_occurrences: int

    # Distribution by sura
    by_sura: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # sura_no -> {count, sura_name, percentage}

    # Distribution by juz
    by_juz: Dict[int, int] = field(default_factory=dict)

    # Top verses (highest frequency context)
    top_verses: List[Dict[str, Any]] = field(default_factory=list)

    # Co-occurring words
    co_occurring_words: List[Tuple[str, int]] = field(default_factory=list)

    # Themes/categories
    themes: List[str] = field(default_factory=list)


# =============================================================================
# SEMANTIC EXPANSION - RELATED CONCEPTS
# =============================================================================

# Islamic concept synonyms and related terms
CONCEPT_EXPANSIONS = {
    # Names of Allah
    "الله": ["الرب", "الرحمن", "الرحيم", "الملك", "القدوس", "السلام", "المؤمن"],
    "رب": ["الله", "الرب", "رب العالمين", "رب السماوات"],

    # Praise/Thanks
    "حمد": ["شكر", "ثناء", "مجد", "سبح"],
    "شكر": ["حمد", "ثناء", "نعم"],

    # Patience
    "صبر": ["احتمال", "تحمل", "صابر", "صابرين"],

    # Prayer
    "صلاة": ["صلى", "يصلون", "مصلين", "ركوع", "سجود"],
    "صلى": ["صلاة", "يصلي", "صل"],

    # Faith
    "إيمان": ["مؤمن", "مؤمنون", "آمن", "آمنوا", "يؤمن", "تصديق"],
    "ايمان": ["مؤمن", "مؤمنون", "آمن", "آمنوا", "يؤمن", "تصديق"],  # Without hamza
    "آمن": ["إيمان", "مؤمن", "يؤمن", "تصديق"],

    # Guidance
    "هدى": ["هداية", "يهدي", "مهتدين", "رشد", "سبيل"],
    "هدي": ["هداية", "يهدي", "مهتدين", "رشد", "سبيل"],  # Normalized form
    "هداية": ["هدى", "يهدي", "صراط مستقيم"],

    # Mercy
    "رحمة": ["رحيم", "رحمن", "يرحم", "راحم"],
    "رحيم": ["رحمة", "رحمن"],

    # Forgiveness
    "غفر": ["مغفرة", "غفور", "يغفر", "استغفر", "تاب"],
    "مغفرة": ["غفر", "غفور", "عفو"],
    "تاب": ["توبة", "تائب", "يتوب", "غفر"],

    # Knowledge
    "علم": ["عالم", "عليم", "يعلم", "معلوم", "علماء"],
    "عليم": ["علم", "عالم", "يعلم"],

    # Truth
    "حق": ["صدق", "حقيقة", "صادق", "حقا"],
    "صدق": ["حق", "صادق", "صديق"],

    # Fear of Allah
    "تقوى": ["خوف", "خشية", "متقين", "اتقوا"],
    "خوف": ["تقوى", "خشية", "يخاف"],

    # Day of Judgment
    "قيامة": ["يوم القيامة", "آخرة", "بعث", "حساب", "يوم الدين"],
    "آخرة": ["قيامة", "يوم القيامة", "جنة", "نار"],

    # Paradise
    "جنة": ["فردوس", "نعيم", "خلد", "جنات"],

    # Hell
    "نار": ["جهنم", "سعير", "عذاب", "حريق"],
    "جهنم": ["نار", "سعير", "عذاب"],

    # Prophets
    "نبي": ["رسول", "مرسل", "أنبياء"],
    "رسول": ["نبي", "مرسل", "رسل"],

    # Worship
    "عبادة": ["عبد", "يعبد", "عابد", "عابدين"],
    "عبد": ["عبادة", "يعبد", "عباد"],

    # Sin
    "ذنب": ["إثم", "خطيئة", "سيئة", "معصية"],
    "إثم": ["ذنب", "خطيئة", "سيئة"],

    # Good deeds
    "حسنة": ["خير", "صالح", "بر", "معروف"],
    "خير": ["حسنة", "صالح", "بر"],
}


def expand_query(
    query: str,
    include_roots: bool = True,
    include_bilingual: bool = True
) -> Set[str]:
    """
    Expand query with related Islamic concepts, root-derived words, and bilingual synonyms.

    Args:
        query: The search query
        include_roots: Whether to expand by Arabic roots (default True)
        include_bilingual: Whether to expand with bilingual synonyms (default True)

    Returns set of related terms to include in search.

    Arabic: توسيع الاستعلام مع المفاهيم الإسلامية والجذور والمترادفات ثنائية اللغة
    """
    normalized = normalize_arabic(query)
    words = extract_words(query)

    expanded = {normalized}

    for word in words:
        expanded.add(word)

        # Add related concepts from expansion dictionary
        if word in CONCEPT_EXPANSIONS:
            expanded.update(CONCEPT_EXPANSIONS[word])

        # Add root-derived words (morphological expansion)
        if include_roots:
            root_words = expand_by_root(word)
            if root_words:
                expanded.update(root_words)

    # Add bilingual expansions (Arabic <-> English synonyms)
    if include_bilingual:
        bilingual_expansions, _ = expand_bilingual_query(query)
        expanded.update(bilingual_expansions)

    return expanded


# =============================================================================
# SIMILARITY ALGORITHMS
# =============================================================================

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.

    Jaccard = |A ∩ B| / |A ∪ B|

    Returns value between 0 (no overlap) and 1 (identical sets).
    """
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def cosine_similarity_words(words1: List[str], words2: List[str]) -> float:
    """
    Compute cosine similarity between two word lists.

    Uses word frequency vectors.

    Cosine = (A · B) / (||A|| * ||B||)
    """
    if not words1 or not words2:
        return 0.0

    # Build frequency vectors
    all_words = set(words1) | set(words2)
    freq1 = {w: words1.count(w) for w in all_words}
    freq2 = {w: words2.count(w) for w in all_words}

    # Compute dot product and magnitudes
    dot_product = sum(freq1[w] * freq2[w] for w in all_words)
    magnitude1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    magnitude2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def concept_overlap_score(query_concepts: Set[str], verse_text: str) -> float:
    """
    Compute concept overlap score.

    Measures how many of the expanded query concepts appear in the verse.
    """
    verse_words = set(extract_words(verse_text))
    verse_normalized = {normalize_arabic(w) for w in verse_words}

    # Expand verse words to include related concepts
    verse_concepts = set()
    for word in verse_words:
        verse_concepts.add(normalize_arabic(word))
        if word in CONCEPT_EXPANSIONS:
            verse_concepts.update(normalize_arabic(c) for c in CONCEPT_EXPANSIONS[word])

    # Compute overlap
    overlap = len(query_concepts & verse_concepts)
    total = len(query_concepts)

    return overlap / total if total > 0 else 0.0


def compute_combined_relevance(
    query: str,
    verse_text: str,
    tf_idf_score: float,
    exact_match: bool,
    query_concepts: Set[str],
) -> float:
    """
    Compute combined relevance score using multiple algorithms.

    Combines:
    - TF-IDF score (40%)
    - Jaccard similarity (20%)
    - Cosine similarity (20%)
    - Concept overlap (20%)
    - Exact match bonus (+20%)
    """
    query_words = extract_words(query)
    verse_words = extract_words(verse_text)

    # Normalize words
    query_set = {normalize_arabic(w) for w in query_words}
    verse_set = {normalize_arabic(w) for w in verse_words}

    # Compute individual scores
    jaccard = jaccard_similarity(query_set, verse_set)
    cosine = cosine_similarity_words(
        [normalize_arabic(w) for w in query_words],
        [normalize_arabic(w) for w in verse_words]
    )
    concept = concept_overlap_score(query_concepts, verse_text)

    # Weighted combination
    combined = (
        tf_idf_score * 0.4 +
        jaccard * 0.2 +
        cosine * 0.2 +
        concept * 0.2
    )

    # Exact match bonus
    if exact_match:
        combined = min(combined + 0.2, 1.0)

    return min(combined, 1.0)


# =============================================================================
# TF-IDF SCORING
# =============================================================================

class TFIDFScorer:
    """
    TF-IDF scorer for Quranic verse relevance.

    TF = Term Frequency in verse
    IDF = Inverse Document Frequency across all verses
    """

    def __init__(self):
        self.document_count = 6236  # Total verses in Quran
        self.document_frequencies: Dict[str, int] = {}  # word -> count of verses containing it
        self._initialized = False

    async def initialize(self, session: AsyncSession):
        """Initialize document frequencies from database."""
        if self._initialized:
            return

        # This would ideally be precomputed and cached
        # For now, we'll compute on-demand for searched terms
        self._initialized = True

    async def compute_idf(self, word: str, session: AsyncSession) -> float:
        """Compute IDF for a word."""
        if word not in self.document_frequencies:
            # Count verses containing this word
            normalized = normalize_arabic(word)
            result = await session.execute(
                select(func.count(QuranVerse.id)).where(
                    QuranVerse.text_imlaei.ilike(f'%{normalized}%')
                )
            )
            count = result.scalar() or 0
            self.document_frequencies[word] = max(count, 1)

        df = self.document_frequencies[word]
        # IDF = log(N / df) where N is total documents
        return math.log(self.document_count / df) if df > 0 else 0

    def compute_tf(self, word: str, verse_text: str) -> float:
        """Compute TF for a word in a verse."""
        normalized_word = normalize_arabic(word)
        normalized_text = normalize_arabic(verse_text)

        # Count occurrences
        count = normalized_text.lower().count(normalized_word.lower())

        # Normalize by verse length
        words_in_verse = len(extract_words(verse_text))
        return count / max(words_in_verse, 1)

    async def compute_tfidf(self, word: str, verse_text: str, session: AsyncSession) -> float:
        """Compute TF-IDF score."""
        tf = self.compute_tf(word, verse_text)
        idf = await self.compute_idf(word, session)
        return tf * idf


# =============================================================================
# MAIN SEARCH SERVICE
# =============================================================================

class QuranSearchService:
    """
    Comprehensive Quran search service.

    Features:
    - Exact and fuzzy matching
    - Semantic expansion
    - TF-IDF relevance scoring
    - Context highlighting
    - Word frequency analytics
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tfidf_scorer = TFIDFScorer()

    async def search(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        sura_filter: Optional[int] = None,
        juz_filter: Optional[int] = None,
        include_semantic: bool = True,
        include_grammar: bool = False,
        theme_filter: Optional[str] = None,
    ) -> SearchResult:
        """
        Search for a word or phrase across the entire Quran.

        Args:
            query: Arabic word or phrase to search
            limit: Maximum results to return
            offset: Pagination offset
            sura_filter: Filter to specific sura
            juz_filter: Filter to specific juz
            include_semantic: Include semantically related terms
            include_grammar: Include grammatical analysis (slower)
            theme_filter: Filter by thematic category (e.g., 'tawheed', 'prophets')

        Returns:
            SearchResult with matches and statistics
        """
        import time
        start_time = time.time()

        # Normalize query
        query_normalized = normalize_arabic(query)

        # Build search terms
        search_terms = {query_normalized}
        if include_semantic:
            search_terms = expand_query(query)

        # Build query conditions - use normalized column for diacritic-free search
        conditions = []
        for term in search_terms:
            # Use text_normalized for search (no diacritics)
            conditions.append(QuranVerse.text_normalized.ilike(f'%{term}%'))

        # Build main query
        stmt = select(QuranVerse).where(or_(*conditions))

        # Apply filters
        if sura_filter:
            stmt = stmt.where(QuranVerse.sura_no == sura_filter)
        if juz_filter:
            stmt = stmt.where(QuranVerse.juz_no == juz_filter)

        # Order by sura and ayah for consistent results
        stmt = stmt.order_by(QuranVerse.sura_no, QuranVerse.aya_no)

        # Execute query
        result = await self.session.execute(stmt)
        verses = result.scalars().all()

        # Process matches
        matches = []
        sura_dist = defaultdict(int)
        juz_dist = defaultdict(int)
        page_dist = defaultdict(int)

        for verse in verses:
            # Find match positions
            positions = self._find_match_positions(verse.text_imlaei, search_terms)
            if not positions:
                continue

            # Apply theme filter if specified
            if theme_filter:
                verse_themes = detect_theme(verse.text_imlaei)
                if theme_filter not in verse_themes:
                    continue

            # Compute TF-IDF score
            tfidf_score = await self.tfidf_scorer.compute_tfidf(
                query_normalized, verse.text_imlaei, self.session
            )

            # Create highlighted text
            highlighted = self._highlight_matches(verse.text_uthmani, positions)

            # Extract context
            context_before, context_after = self._extract_context(
                verse.text_uthmani, positions[0] if positions else (0, 0)
            )

            # Check for exact match
            exact_match = query_normalized in normalize_arabic(verse.text_imlaei)

            # Compute combined relevance using multiple algorithms
            combined_relevance = compute_combined_relevance(
                query=query,
                verse_text=verse.text_imlaei,
                tf_idf_score=tfidf_score,
                exact_match=exact_match,
                query_concepts=search_terms,
            )

            match = SearchMatch(
                verse_id=verse.id,
                sura_no=verse.sura_no,
                sura_name_ar=verse.sura_name_ar,
                sura_name_en=verse.sura_name_en,
                aya_no=verse.aya_no,
                text_uthmani=verse.text_uthmani,
                text_imlaei=verse.text_imlaei,
                page_no=verse.page_no,
                juz_no=verse.juz_no,
                match_positions=positions,
                highlighted_text=highlighted,
                context_before=context_before,
                context_after=context_after,
                relevance_score=combined_relevance,
                tfidf_score=tfidf_score,
                exact_match=exact_match,
            )

            matches.append(match)

            # Update distributions
            sura_dist[verse.sura_no] += 1
            juz_dist[verse.juz_no] += 1
            page_dist[verse.page_no] += 1

        # Sort by relevance score
        matches.sort(key=lambda m: m.relevance_score, reverse=True)

        # Apply pagination
        total_matches = len(matches)
        matches = matches[offset:offset + limit]

        # Build result
        search_time = (time.time() - start_time) * 1000

        return SearchResult(
            query=query,
            query_normalized=query_normalized,
            total_matches=total_matches,
            matches=matches,
            sura_distribution=dict(sura_dist),
            juz_distribution=dict(juz_dist),
            page_distribution=dict(page_dist),
            related_terms=list(search_terms - {query_normalized}),
            search_time_ms=search_time,
        )

    async def get_word_analytics(self, word: str) -> WordAnalytics:
        """
        Get comprehensive analytics for a word's usage in the Quran.

        Returns frequency, distribution, co-occurrence patterns.
        """
        normalized = normalize_arabic(word)

        # Get all verses containing the word
        result = await self.session.execute(
            select(QuranVerse).where(
                QuranVerse.text_imlaei.ilike(f'%{normalized}%')
            ).order_by(QuranVerse.sura_no, QuranVerse.aya_no)
        )
        verses = result.scalars().all()

        # Compute distributions
        by_sura: Dict[str, Dict[str, Any]] = {}
        by_juz: Dict[int, int] = defaultdict(int)
        co_occurring: Dict[str, int] = defaultdict(int)
        total = 0

        for verse in verses:
            # Count occurrences in this verse
            count = normalize_arabic(verse.text_imlaei).count(normalized)
            total += count

            # Sura distribution
            sura_key = str(verse.sura_no)
            if sura_key not in by_sura:
                by_sura[sura_key] = {
                    "count": 0,
                    "sura_name_ar": verse.sura_name_ar,
                    "sura_name_en": verse.sura_name_en,
                }
            by_sura[sura_key]["count"] += count

            # Juz distribution
            by_juz[verse.juz_no] += count

            # Co-occurring words
            words = extract_words(verse.text_imlaei)
            for w in words:
                if w != normalized and len(w) > 2:
                    co_occurring[w] += 1

        # Calculate percentages
        for sura_key in by_sura:
            by_sura[sura_key]["percentage"] = round(
                by_sura[sura_key]["count"] / max(total, 1) * 100, 2
            )

        # Top co-occurring words
        top_co_occurring = sorted(
            co_occurring.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # Top verses by occurrence count
        top_verses = []
        for verse in verses[:10]:
            top_verses.append({
                "sura_no": verse.sura_no,
                "aya_no": verse.aya_no,
                "sura_name_ar": verse.sura_name_ar,
                "text_uthmani": verse.text_uthmani,
                "reference": f"{verse.sura_no}:{verse.aya_no}",
            })

        return WordAnalytics(
            word=word,
            word_normalized=normalized,
            total_occurrences=total,
            by_sura=by_sura,
            by_juz=dict(by_juz),
            top_verses=top_verses,
            co_occurring_words=top_co_occurring,
        )

    async def search_phrase(
        self,
        phrase: str,
        exact: bool = True,
        limit: int = 50,
    ) -> SearchResult:
        """
        Search for an exact phrase in the Quran.

        Args:
            phrase: Arabic phrase to search
            exact: If True, match exact phrase; otherwise fuzzy
            limit: Maximum results
        """
        normalized = normalize_arabic(phrase)

        if exact:
            # Exact phrase match
            stmt = select(QuranVerse).where(
                QuranVerse.text_imlaei.ilike(f'%{normalized}%')
            ).order_by(QuranVerse.sura_no, QuranVerse.aya_no).limit(limit)
        else:
            # All words must appear (any order)
            words = extract_words(phrase)
            conditions = [
                QuranVerse.text_imlaei.ilike(f'%{w}%')
                for w in words
            ]
            stmt = select(QuranVerse).where(
                and_(*conditions)
            ).order_by(QuranVerse.sura_no, QuranVerse.aya_no).limit(limit)

        result = await self.session.execute(stmt)
        verses = result.scalars().all()

        matches = []
        for verse in verses:
            positions = self._find_match_positions(verse.text_imlaei, {normalized})
            highlighted = self._highlight_matches(verse.text_uthmani, positions)

            match = SearchMatch(
                verse_id=verse.id,
                sura_no=verse.sura_no,
                sura_name_ar=verse.sura_name_ar,
                sura_name_en=verse.sura_name_en,
                aya_no=verse.aya_no,
                text_uthmani=verse.text_uthmani,
                text_imlaei=verse.text_imlaei,
                page_no=verse.page_no,
                juz_no=verse.juz_no,
                match_positions=positions,
                highlighted_text=highlighted,
                exact_match=True,
            )
            matches.append(match)

        return SearchResult(
            query=phrase,
            query_normalized=normalized,
            total_matches=len(matches),
            matches=matches,
        )

    async def get_sura_word_frequency(
        self,
        sura_no: int,
        top_n: int = 50,
    ) -> List[Tuple[str, int]]:
        """
        Get word frequency for a specific sura.

        Returns list of (word, count) tuples.
        """
        result = await self.session.execute(
            select(QuranVerse.text_imlaei).where(
                QuranVerse.sura_no == sura_no
            )
        )
        verses = result.scalars().all()

        word_counts: Dict[str, int] = defaultdict(int)
        for verse_text in verses:
            words = extract_words(verse_text)
            for word in words:
                word_counts[word] += 1

        # Sort by frequency
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_words[:top_n]

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _find_match_positions(
        self,
        text: str,
        search_terms: Set[str],
    ) -> List[Tuple[int, int]]:
        """Find all positions where search terms match in text."""
        positions = []
        normalized_text = normalize_arabic(text).lower()

        for term in search_terms:
            normalized_term = normalize_arabic(term).lower()
            start = 0
            while True:
                pos = normalized_text.find(normalized_term, start)
                if pos == -1:
                    break
                positions.append((pos, pos + len(normalized_term)))
                start = pos + 1

        # Sort by position and merge overlapping
        positions.sort()
        return positions

    def _highlight_matches(
        self,
        text: str,
        positions: List[Tuple[int, int]],
        highlight_start: str = "【",
        highlight_end: str = "】",
    ) -> str:
        """
        Highlight matches in text using markers.

        Maps positions from normalized text back to original text
        by building a character-by-character mapping.
        """
        if not positions:
            return text

        # Build mapping from normalized positions to original positions
        # This accounts for diacritics that exist in original but not normalized
        norm_to_orig = []  # norm_to_orig[norm_idx] = orig_idx
        orig_idx = 0

        for char in text:
            # Check if this character would be removed during normalization
            is_diacritic = '\u064B' <= char <= '\u065F' or char == '\u0670'
            if not is_diacritic:
                norm_to_orig.append(orig_idx)
            orig_idx += 1

        # Add end position
        norm_to_orig.append(len(text))

        # Merge overlapping positions
        merged = []
        for start, end in sorted(positions):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        # Build highlighted text
        result = []
        last_orig_end = 0

        for norm_start, norm_end in merged:
            # Map normalized positions to original positions
            if norm_start >= len(norm_to_orig):
                continue
            orig_start = norm_to_orig[min(norm_start, len(norm_to_orig) - 1)]
            orig_end = norm_to_orig[min(norm_end, len(norm_to_orig) - 1)]

            # Extend to include trailing diacritics
            while orig_end < len(text):
                char = text[orig_end]
                is_diacritic = '\u064B' <= char <= '\u065F' or char == '\u0670'
                if is_diacritic:
                    orig_end += 1
                else:
                    break

            # Skip if positions are invalid
            if orig_start >= len(text) or orig_start < last_orig_end:
                continue

            result.append(text[last_orig_end:orig_start])
            result.append(highlight_start)
            result.append(text[orig_start:orig_end])
            result.append(highlight_end)
            last_orig_end = orig_end

        result.append(text[last_orig_end:])
        return ''.join(result)

    def _extract_context(
        self,
        text: str,
        position: Tuple[int, int],
        context_words: int = 5,
    ) -> Tuple[str, str]:
        """Extract words before and after a match position."""
        words = text.split()
        total_words = len(words)

        # Find which word contains the position
        char_count = 0
        word_idx = 0
        for i, word in enumerate(words):
            if char_count + len(word) >= position[0]:
                word_idx = i
                break
            char_count += len(word) + 1  # +1 for space

        # Extract context
        start_idx = max(0, word_idx - context_words)
        end_idx = min(total_words, word_idx + context_words + 1)

        context_before = ' '.join(words[start_idx:word_idx])
        context_after = ' '.join(words[word_idx + 1:end_idx])

        return context_before, context_after

    # =========================================================================
    # MULTI-CONCEPT SEARCH
    # =========================================================================

    async def search_multi_concept(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        sura_filter: Optional[int] = None,
        connector_type: str = 'or',  # 'and' requires all concepts, 'or' requires any
    ) -> Dict[str, Any]:
        """
        Search for multiple concepts in a single query.

        Handles queries like "Solomon and the Queen of Sheba" by finding
        verses connected to either concept and highlighting which concepts
        match in each verse.

        Args:
            query: Multi-concept query string
            limit: Maximum results to return
            offset: Pagination offset
            sura_filter: Filter to specific sura
            connector_type: 'and' (all concepts required) or 'or' (any concept matches)

        Returns:
            Dict with:
            - parsed_query: ParsedQuery with extracted concepts
            - total_matches: Total number of matching verses
            - matches: List of verse matches with concept highlighting
            - concept_distribution: Count of matches per concept
            - search_time_ms: Search execution time

        Arabic: البحث متعدد المفاهيم
        """
        import time
        start_time = time.time()

        # Parse the multi-concept query
        parsed = parse_multi_concept_query(query)

        if not parsed.concepts:
            return {
                "parsed_query": parsed,
                "total_matches": 0,
                "matches": [],
                "concept_distribution": {},
                "search_time_ms": 0,
            }

        # Use connector type from parsed query if available
        if parsed.is_multi_concept:
            connector_type = parsed.connector_type

        # Get bilingual expansions for each concept
        all_search_terms = set()
        concept_expansions_map = {}

        for concept in parsed.concepts:
            expansions = get_concept_expansions(concept, 'both')
            concept_expansions_map[concept] = expansions
            all_search_terms.update(expansions)

        # Build search conditions for each term
        conditions = []
        for term in all_search_terms:
            conditions.append(QuranVerse.text_normalized.ilike(f'%{normalize_arabic(term)}%'))

        if not conditions:
            return {
                "parsed_query": parsed,
                "total_matches": 0,
                "matches": [],
                "concept_distribution": {},
                "search_time_ms": 0,
            }

        # Build query
        stmt = select(QuranVerse).where(or_(*conditions))

        if sura_filter:
            stmt = stmt.where(QuranVerse.sura_no == sura_filter)

        stmt = stmt.order_by(QuranVerse.sura_no, QuranVerse.aya_no)

        # Execute query
        result = await self.session.execute(stmt)
        verses = result.scalars().all()

        # Process matches and find concept highlights
        matches = []
        concept_dist = {c: 0 for c in parsed.concepts}

        for verse in verses:
            # Find which concepts match in this verse
            concept_highlights = find_concept_matches(
                verse.text_imlaei,
                parsed.concepts,
                include_expansions=True
            )

            if not concept_highlights:
                continue

            # For 'and' mode, require all concepts to be present
            if connector_type == 'and':
                matched_concepts = {h.concept for h in concept_highlights}
                if len(matched_concepts) < len(parsed.concepts):
                    continue

            # Calculate relevance score based on concept matches
            relevance_score = len(concept_highlights) / len(parsed.concepts)

            # Build highlighted text with all concept positions
            all_positions = []
            for highlight in concept_highlights:
                all_positions.extend(highlight.positions)
                concept_dist[highlight.concept] += 1

            highlighted_text = self._highlight_matches(
                verse.text_uthmani,
                all_positions
            )

            match_data = {
                "verse_id": verse.id,
                "sura_no": verse.sura_no,
                "sura_name_ar": verse.sura_name_ar,
                "sura_name_en": verse.sura_name_en,
                "aya_no": verse.aya_no,
                "text_uthmani": verse.text_uthmani,
                "text_imlaei": verse.text_imlaei,
                "page_no": verse.page_no,
                "juz_no": verse.juz_no,
                "reference": f"{verse.sura_no}:{verse.aya_no}",
                "highlighted_text": highlighted_text,
                "relevance_score": relevance_score,
                "matched_concepts": [
                    {
                        "concept": h.concept,
                        "matched_terms": h.matched_terms,
                        "positions": h.positions,
                    }
                    for h in concept_highlights
                ],
            }

            matches.append(match_data)

        # Sort by relevance (more concepts matched = higher score)
        matches.sort(key=lambda m: m["relevance_score"], reverse=True)

        # Apply pagination
        total_matches = len(matches)
        matches = matches[offset:offset + limit]

        search_time = (time.time() - start_time) * 1000

        return {
            "parsed_query": {
                "original": parsed.original,
                "concepts": parsed.concepts,
                "connector_type": connector_type,
                "is_multi_concept": parsed.is_multi_concept,
                "language": parsed.language,
            },
            "total_matches": total_matches,
            "matches": matches,
            "concept_distribution": concept_dist,
            "concept_expansions": {
                c: list(exps)[:10]  # Limit to 10 for response size
                for c, exps in concept_expansions_map.items()
            },
            "search_time_ms": round(search_time, 2),
        }

    async def get_concept_suggestions(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get auto-suggestions for concept search.

        Returns matching concepts from the bilingual concept database
        with their Arabic and English forms.

        Args:
            query: Partial query to match against concepts
            limit: Maximum suggestions to return

        Returns:
            List of concept suggestions with bilingual terms

        Arabic: الحصول على اقتراحات المفاهيم
        """
        query_lower = query.lower().strip()
        suggestions = []

        for key, data in BILINGUAL_CONCEPTS.items():
            # Check if query matches key or any term
            match_score = 0

            if query_lower in key:
                match_score = 2 if key.startswith(query_lower) else 1

            # Check English terms
            for en_term in data.get('en', []):
                if query_lower in en_term.lower():
                    if en_term.lower().startswith(query_lower):
                        match_score = max(match_score, 2)
                    else:
                        match_score = max(match_score, 1)

            # Check Arabic terms
            for ar_term in data.get('ar', []):
                if query in ar_term or normalize_arabic(query) in normalize_arabic(ar_term):
                    match_score = max(match_score, 2)

            if match_score > 0:
                suggestions.append({
                    "key": key,
                    "ar": data.get('ar', [])[:3],  # Top 3 Arabic terms
                    "en": data.get('en', [])[:3],  # Top 3 English terms
                    "related": data.get('related', [])[:5],
                    "match_score": match_score,
                })

        # Sort by match score, then alphabetically
        suggestions.sort(key=lambda x: (-x["match_score"], x["key"]))

        return suggestions[:limit]
