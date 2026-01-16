"""
Quran Text Utilities for Similarity and Search Processing.

Provides:
1. Bismillah exclusion for similarity computations
2. Multi-concept query parsing
3. Bilingual query expansion with comprehensive synonyms
4. Arabic-English concept mapping

Arabic: أدوات معالجة النص القرآني للتشابه والبحث
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# BISMILLAH HANDLING
# =============================================================================

# Bismillah patterns (various forms with and without diacritics)
BISMILLAH_PATTERNS = [
    # Full form with Uthmani diacritics (using alef wasla ٱ)
    "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
    # Full form with standard diacritics
    "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
    "بِسْمِ اللهِ الرَّحْمنِ الرَّحِيمِ",
    "بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ",
    # Without diacritics (normalized)
    "بسم الله الرحمن الرحيم",
    "بسم الله الرحمان الرحيم",
    # Partial forms (for edge cases)
    "بسم الله",
]

# Arabic diacritics (tashkeel) to remove for normalization
ARABIC_DIACRITICS = re.compile(
    r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]',
    re.UNICODE
)


def _normalize_arabic_for_bismillah(text: str) -> str:
    """
    Normalize Arabic text for Bismillah matching.

    Removes diacritics and normalizes special characters.
    """
    if not text:
        return ""

    # Remove diacritics
    result = ARABIC_DIACRITICS.sub('', text)

    # Normalize alef variants (alef wasla ٱ -> alef ا)
    result = result.replace('ٱ', 'ا')

    # Normalize alef with hamza variants
    result = result.replace('أ', 'ا')
    result = result.replace('إ', 'ا')
    result = result.replace('آ', 'ا')

    # Normalize teh marbuta to heh
    result = result.replace('ة', 'ه')

    # Normalize multiple spaces to single space
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


# Compiled regex for efficient matching (after normalization)
BISMILLAH_REGEX = re.compile(
    r'^بسم\s+الله\s+الرحم[اآ]?ن\s+الرحيم',
    re.UNICODE
)

# Simpler normalized pattern (without diacritics)
BISMILLAH_NORMALIZED_REGEX = re.compile(
    r'بسم\s+الله\s+الرحم[اا]?ن\s+الرحيم',
    re.UNICODE
)

# Normalized Bismillah for exact matching
BISMILLAH_NORMALIZED = "بسم الله الرحمن الرحيم"


def remove_bismillah(text: str, preserve_content: bool = True) -> str:
    """
    Remove Bismillah phrase from text for similarity computation.

    Args:
        text: Arabic verse text
        preserve_content: If True, only remove Bismillah at start;
                         if False, remove all occurrences

    Returns:
        Text with Bismillah removed

    Arabic: إزالة البسملة من النص لحساب التشابه
    """
    if not text:
        return text

    result = text.strip()

    # First, try exact pattern matching with original text
    for pattern in BISMILLAH_PATTERNS:
        if result.startswith(pattern):
            result = result[len(pattern):].strip()
            return result if result else text  # Return original if nothing left

    # Normalize text for matching
    normalized = _normalize_arabic_for_bismillah(result)

    # Check if normalized text starts with Bismillah
    bismillah_match = BISMILLAH_REGEX.match(normalized)
    if bismillah_match:
        # Find where Bismillah ends in original text
        # Count characters in normalized Bismillah match
        match_len = bismillah_match.end()

        # Map back to original text by counting non-diacritic characters
        orig_pos = 0
        norm_pos = 0
        while norm_pos < match_len and orig_pos < len(result):
            char = result[orig_pos]
            # Check if character is a diacritic
            if not ARABIC_DIACRITICS.match(char):
                norm_pos += 1
            orig_pos += 1

        result = result[orig_pos:].strip()
        # Remove any leading diacritics that might be left over
        while result and ARABIC_DIACRITICS.match(result[0]):
            result = result[1:]
        result = result.strip()

    if not preserve_content:
        # Remove all occurrences (for special cases like 27:30)
        normalized = _normalize_arabic_for_bismillah(result)
        if BISMILLAH_NORMALIZED_REGEX.search(normalized):
            # Find and remove embedded Bismillah
            for pattern in BISMILLAH_PATTERNS:
                result = result.replace(pattern, '').strip()
            # Clean up extra spaces
            result = re.sub(r'\s+', ' ', result).strip()

    return result if result else text


def is_bismillah_verse(text: str) -> bool:
    """
    Check if a verse is primarily the Bismillah.

    Returns True if the verse is essentially just Bismillah
    (like Sura Al-Fatiha verse 1).

    Arabic: التحقق مما إذا كانت الآية هي البسملة فقط
    """
    if not text:
        return False

    # Normalize and check for exact Bismillah match
    normalized = _normalize_arabic_for_bismillah(text)

    # Check if it's exactly the Bismillah (with possible whitespace variations)
    if normalized == BISMILLAH_NORMALIZED:
        return True

    # Check if normalized text matches Bismillah pattern exactly
    if BISMILLAH_REGEX.match(normalized):
        # Check if there's significant content after Bismillah
        remaining = BISMILLAH_REGEX.sub('', normalized).strip()
        # If no content remains, it's a Bismillah verse
        # Note: We use character count because some meaningful content like "الم"
        # is short but significant (Muqatta'at letters)
        return len(remaining) == 0

    return False


def is_first_verse_with_bismillah(sura_no: int, aya_no: int) -> bool:
    """
    Check if this verse position typically contains Bismillah prefix.

    First verse (aya 1) of all suras except Sura 9 (At-Tawbah)
    typically has Bismillah prefixed in the database.

    Arabic: التحقق مما إذا كانت هذه الآية تحتوي على البسملة
    """
    # Sura 9 (At-Tawbah) has no Bismillah
    if sura_no == 9:
        return False

    # First verse of any other sura
    return aya_no == 1


def is_sura_opening_verse(sura_no: int, aya_no: int) -> bool:
    """
    Check if this is the opening verse of a sura (where Bismillah typically appears).

    Note: Sura 9 (At-Tawbah) is the only sura without Bismillah.

    Arabic: التحقق مما إذا كانت هذه الآية الافتتاحية للسورة
    """
    if aya_no != 1:
        return False

    # Sura 9 (At-Tawbah) doesn't have Bismillah
    if sura_no == 9:
        return False

    return True


def preprocess_for_similarity(
    text: str,
    sura_no: Optional[int] = None,
    aya_no: Optional[int] = None,
    exclude_bismillah: bool = True
) -> str:
    """
    Preprocess verse text for similarity computation.

    - Removes Bismillah from sura openings
    - Normalizes Arabic text
    - Handles edge cases

    Args:
        text: Original verse text
        sura_no: Sura number (optional, for context)
        aya_no: Aya number (optional, for context)
        exclude_bismillah: Whether to exclude Bismillah

    Returns:
        Preprocessed text suitable for similarity computation

    Arabic: معالجة مسبقة للنص لحساب التشابه
    """
    if not text:
        return ""

    result = text.strip()

    if exclude_bismillah:
        # Always try to remove Bismillah from start
        result = remove_bismillah(result, preserve_content=True)

        # Special handling for first verse of suras
        if sura_no and aya_no == 1 and sura_no != 9:
            # Additional cleanup for sura openings
            result = remove_bismillah(result, preserve_content=False)

    return result


# =============================================================================
# MULTI-CONCEPT QUERY PARSING
# =============================================================================

# Query connectors (words that join multiple concepts)
QUERY_CONNECTORS = {
    # English connectors
    'and', 'or', 'with', '&', '+',
    # Arabic connectors
    'و', 'أو', 'مع',
}

# Phrase delimiters
PHRASE_DELIMITERS = ['"', "'", '«', '»', '"', '"']


@dataclass
class ParsedQuery:
    """Parsed multi-concept query."""
    original: str
    concepts: List[str]
    connector_type: str  # 'and', 'or'
    is_multi_concept: bool
    language: str  # 'ar', 'en', 'mixed'


def parse_multi_concept_query(query: str) -> ParsedQuery:
    """
    Parse a query that may contain multiple concepts.

    Examples:
        "Solomon and the Queen of Sheba" -> ['solomon', 'queen of sheba']
        "موسى و فرعون" -> ['موسى', 'فرعون']
        "patience and gratitude" -> ['patience', 'gratitude']

    Args:
        query: User search query

    Returns:
        ParsedQuery with extracted concepts

    Arabic: تحليل استعلام متعدد المفاهيم
    """
    if not query:
        return ParsedQuery(
            original=query,
            concepts=[],
            connector_type='and',
            is_multi_concept=False,
            language='en'
        )

    query = query.strip()

    # Detect language
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', query))
    has_english = bool(re.search(r'[a-zA-Z]', query))

    if has_arabic and has_english:
        language = 'mixed'
    elif has_arabic:
        language = 'ar'
    else:
        language = 'en'

    # Determine connector type
    connector_type = 'and'
    if ' or ' in query.lower() or ' أو ' in query:
        connector_type = 'or'

    # Split by connectors
    concepts = []

    # Try splitting by various connectors
    split_patterns = [
        r'\s+and\s+',
        r'\s+or\s+',
        r'\s+with\s+',
        r'\s+و\s+',
        r'\s+أو\s+',
        r'\s+مع\s+',
        r'\s*&\s*',
        r'\s*\+\s*',
    ]

    parts = [query]
    for pattern in split_patterns:
        new_parts = []
        for part in parts:
            split_result = re.split(pattern, part, flags=re.IGNORECASE)
            new_parts.extend(split_result)
        parts = new_parts

    # Clean up concepts
    for part in parts:
        concept = part.strip()
        # Remove quotes if present
        for delim in PHRASE_DELIMITERS:
            concept = concept.strip(delim)
        if concept:
            concepts.append(concept)

    is_multi_concept = len(concepts) > 1

    return ParsedQuery(
        original=query,
        concepts=concepts,
        connector_type=connector_type,
        is_multi_concept=is_multi_concept,
        language=language
    )


# =============================================================================
# BILINGUAL CONCEPT MAPPING AND SYNONYMS
# =============================================================================

# Comprehensive bilingual concept mapping
# Format: concept_key -> {ar: [Arabic terms], en: [English terms], related: [related concepts]}
BILINGUAL_CONCEPTS = {
    # ==========================================================================
    # PROPHETS (الأنبياء)
    # ==========================================================================
    "solomon": {
        "ar": ["سليمان", "سُلَيْمَان", "سليمن"],
        "en": ["solomon", "sulayman", "sulaiman", "prophet solomon"],
        "related": ["david", "queen_of_sheba", "jinn", "ants", "hoopoe"],
    },
    "queen_of_sheba": {
        "ar": ["ملكة سبأ", "بلقيس", "سبأ", "ملكة سبا"],
        "en": ["queen of sheba", "bilqis", "bilquis", "sheba", "saba"],
        "related": ["solomon"],
    },
    "moses": {
        "ar": ["موسى", "مُوسَى", "موسي"],
        "en": ["moses", "musa", "prophet moses"],
        "related": ["pharaoh", "aaron", "israelites", "red_sea"],
    },
    "pharaoh": {
        "ar": ["فرعون", "فِرْعَوْن"],
        "en": ["pharaoh", "firaun", "fir'awn"],
        "related": ["moses", "egypt"],
    },
    "abraham": {
        "ar": ["إبراهيم", "ابراهيم", "إِبْرَاهِيم"],
        "en": ["abraham", "ibrahim", "prophet abraham"],
        "related": ["ishmael", "isaac", "fire_trial", "sacrifice"],
    },
    "ishmael": {
        "ar": ["إسماعيل", "اسماعيل", "إِسْمَاعِيل"],
        "en": ["ishmael", "ismail", "prophet ishmael"],
        "related": ["abraham", "sacrifice", "kaaba"],
    },
    "isaac": {
        "ar": ["إسحاق", "اسحاق", "إِسْحَاق"],
        "en": ["isaac", "ishaq", "prophet isaac"],
        "related": ["abraham", "jacob"],
    },
    "jacob": {
        "ar": ["يعقوب", "يَعْقُوب"],
        "en": ["jacob", "yaqub", "prophet jacob", "israel"],
        "related": ["joseph", "isaac"],
    },
    "joseph": {
        "ar": ["يوسف", "يُوسُف"],
        "en": ["joseph", "yusuf", "prophet joseph"],
        "related": ["jacob", "brothers", "egypt", "dream"],
    },
    "noah": {
        "ar": ["نوح", "نُوح"],
        "en": ["noah", "nuh", "prophet noah"],
        "related": ["ark", "flood", "son_of_noah"],
    },
    "jesus": {
        "ar": ["عيسى", "عِيسَى", "المسيح"],
        "en": ["jesus", "isa", "prophet jesus", "messiah", "christ"],
        "related": ["mary", "disciples", "miracles"],
    },
    "mary": {
        "ar": ["مريم", "مَرْيَم"],
        "en": ["mary", "maryam"],
        "related": ["jesus", "zakariya"],
    },
    "david": {
        "ar": ["داود", "دَاوُود", "داوود"],
        "en": ["david", "dawud", "prophet david"],
        "related": ["solomon", "psalms", "goliath"],
    },
    "muhammad": {
        "ar": ["محمد", "مُحَمَّد", "أحمد", "النبي", "الرسول"],
        "en": ["muhammad", "mohammad", "prophet muhammad", "ahmed", "the prophet"],
        "related": ["quraysh", "mecca", "medina"],
    },
    "adam": {
        "ar": ["آدم", "ءَادَم"],
        "en": ["adam", "prophet adam"],
        "related": ["eve", "creation", "paradise", "iblis"],
    },
    "job": {
        "ar": ["أيوب", "أَيُّوب"],
        "en": ["job", "ayyub", "prophet job"],
        "related": ["patience", "trials"],
    },
    "jonah": {
        "ar": ["يونس", "يُونُس", "ذو النون"],
        "en": ["jonah", "yunus", "prophet jonah", "dhul-nun"],
        "related": ["whale", "ninawa"],
    },
    "lot": {
        "ar": ["لوط", "لُوط"],
        "en": ["lot", "lut", "prophet lot"],
        "related": ["sodom", "destruction"],
    },
    "aaron": {
        "ar": ["هارون", "هَارُون"],
        "en": ["aaron", "harun", "prophet aaron"],
        "related": ["moses"],
    },
    "shuayb": {
        "ar": ["شعيب", "شُعَيْب"],
        "en": ["shuayb", "jethro", "prophet shuayb"],
        "related": ["midian", "justice"],
    },
    "hud": {
        "ar": ["هود", "هُود"],
        "en": ["hud", "prophet hud"],
        "related": ["aad"],
    },
    "salih": {
        "ar": ["صالح", "صَالِح"],
        "en": ["salih", "saleh", "prophet salih"],
        "related": ["thamud", "she_camel"],
    },
    "zakariya": {
        "ar": ["زكريا", "زَكَرِيَّا"],
        "en": ["zakariya", "zechariah", "prophet zakariya"],
        "related": ["john", "mary"],
    },
    "john": {
        "ar": ["يحيى", "يَحْيَى"],
        "en": ["john", "yahya", "prophet yahya", "john the baptist"],
        "related": ["zakariya"],
    },

    # ==========================================================================
    # VIRTUES AND CONCEPTS (الفضائل والمفاهيم)
    # ==========================================================================
    "patience": {
        "ar": ["صبر", "الصبر", "صَبْر", "صابر", "صابرين", "اصبر"],
        "en": ["patience", "sabr", "patient", "perseverance", "endurance"],
        "related": ["trials", "reward"],
    },
    "gratitude": {
        "ar": ["شكر", "الشكر", "شُكْر", "شاكر", "شاكرين", "شكور"],
        "en": ["gratitude", "thankfulness", "shukr", "grateful"],
        "related": ["blessings", "praise"],
    },
    "trust": {
        "ar": ["توكل", "التوكل", "تَوَكُّل", "متوكل", "وكيل"],
        "en": ["trust", "reliance", "tawakkul", "trust in allah"],
        "related": ["faith", "patience"],
    },
    "mercy": {
        "ar": ["رحمة", "الرحمة", "رَحْمَة", "رحيم", "رحمن", "يرحم"],
        "en": ["mercy", "rahmah", "merciful", "compassion"],
        "related": ["forgiveness", "love"],
    },
    "forgiveness": {
        "ar": ["مغفرة", "غفر", "غَفَرَ", "غفور", "استغفر", "عفو"],
        "en": ["forgiveness", "maghfirah", "pardon", "forgiving"],
        "related": ["mercy", "repentance"],
    },
    "repentance": {
        "ar": ["توبة", "التوبة", "تَوْبَة", "تاب", "تائب", "تائبين"],
        "en": ["repentance", "tawbah", "repent", "turning back"],
        "related": ["forgiveness", "sin"],
    },
    "faith": {
        "ar": ["إيمان", "الإيمان", "إِيمَان", "مؤمن", "مؤمنين", "آمن"],
        "en": ["faith", "iman", "belief", "believer", "believing"],
        "related": ["islam", "guidance"],
    },
    "guidance": {
        "ar": ["هداية", "الهداية", "هِدَايَة", "هدى", "يهدي", "مهتدين"],
        "en": ["guidance", "hidayah", "guide", "guided"],
        "related": ["faith", "light"],
    },
    "justice": {
        "ar": ["عدل", "العدل", "عَدْل", "عادل", "قسط", "إنصاف"],
        "en": ["justice", "adl", "fairness", "equity", "just"],
        "related": ["truth", "balance"],
    },
    "truth": {
        "ar": ["حق", "الحق", "حَقّ", "صدق", "حقيقة"],
        "en": ["truth", "haqq", "reality", "true"],
        "related": ["justice", "falsehood"],
    },
    "prayer": {
        "ar": ["صلاة", "الصلاة", "صَلَاة", "صلى", "يصلي", "مصلين"],
        "en": ["prayer", "salah", "salat", "praying"],
        "related": ["worship", "prostration"],
    },
    "worship": {
        "ar": ["عبادة", "العبادة", "عِبَادَة", "عبد", "يعبد", "عابدين"],
        "en": ["worship", "ibadah", "worshipping"],
        "related": ["prayer", "devotion"],
    },

    # ==========================================================================
    # PLACES AND EVENTS (الأماكن والأحداث)
    # ==========================================================================
    "paradise": {
        "ar": ["جنة", "الجنة", "جَنَّة", "جنات", "فردوس", "نعيم"],
        "en": ["paradise", "jannah", "heaven", "garden"],
        "related": ["reward", "afterlife"],
    },
    "hellfire": {
        "ar": ["نار", "النار", "نَار", "جهنم", "سعير", "جحيم"],
        "en": ["hellfire", "jahannam", "hell", "fire"],
        "related": ["punishment", "afterlife"],
    },
    "day_of_judgment": {
        "ar": ["يوم القيامة", "القيامة", "قِيَامَة", "يوم الدين", "الساعة", "البعث"],
        "en": ["day of judgment", "qiyamah", "resurrection", "judgment day", "the hour"],
        "related": ["afterlife", "reckoning"],
    },
    "mecca": {
        "ar": ["مكة", "مَكَّة", "بكة", "أم القرى"],
        "en": ["mecca", "makkah", "bakkah"],
        "related": ["kaaba", "hajj"],
    },
    "kaaba": {
        "ar": ["كعبة", "الكعبة", "كَعْبَة", "البيت الحرام", "البيت العتيق"],
        "en": ["kaaba", "kabah", "sacred house"],
        "related": ["mecca", "hajj", "abraham"],
    },
}


def get_concept_expansions(concept: str, language: str = 'both') -> Set[str]:
    """
    Get all expansions for a concept (synonyms, translations).

    Args:
        concept: The concept to expand
        language: 'ar', 'en', or 'both'

    Returns:
        Set of expanded terms

    Arabic: الحصول على جميع توسيعات المفهوم
    """
    expansions = set()
    concept_lower = concept.lower().strip()

    # Check if concept matches any key directly
    for key, data in BILINGUAL_CONCEPTS.items():
        # Check if concept matches the key
        if concept_lower == key:
            if language in ('ar', 'both'):
                expansions.update(data.get('ar', []))
            if language in ('en', 'both'):
                expansions.update(data.get('en', []))
            continue

        # Check if concept matches any Arabic term
        for ar_term in data.get('ar', []):
            if concept_lower == ar_term.lower() or concept == ar_term:
                if language in ('ar', 'both'):
                    expansions.update(data.get('ar', []))
                if language in ('en', 'both'):
                    expansions.update(data.get('en', []))
                break

        # Check if concept matches any English term
        for en_term in data.get('en', []):
            if concept_lower == en_term.lower():
                if language in ('ar', 'both'):
                    expansions.update(data.get('ar', []))
                if language in ('en', 'both'):
                    expansions.update(data.get('en', []))
                break

    # Add original concept
    expansions.add(concept)

    return expansions


def expand_bilingual_query(query: str) -> Tuple[Set[str], Dict[str, Set[str]]]:
    """
    Expand a query with bilingual synonyms and related concepts.

    Args:
        query: Search query (may be multi-concept)

    Returns:
        Tuple of:
        - Set of all expanded terms
        - Dict mapping original concepts to their expansions

    Arabic: توسيع استعلام ثنائي اللغة
    """
    parsed = parse_multi_concept_query(query)

    all_expansions = set()
    concept_map = {}

    for concept in parsed.concepts:
        expansions = get_concept_expansions(concept, 'both')
        all_expansions.update(expansions)
        concept_map[concept] = expansions

    return all_expansions, concept_map


def get_related_concepts(concept: str) -> List[str]:
    """
    Get concepts related to the given concept.

    Args:
        concept: Concept key or term

    Returns:
        List of related concept keys

    Arabic: الحصول على المفاهيم ذات الصلة
    """
    concept_lower = concept.lower().strip()

    for key, data in BILINGUAL_CONCEPTS.items():
        # Check key match
        if concept_lower == key:
            return data.get('related', [])

        # Check term matches
        all_terms = data.get('ar', []) + data.get('en', [])
        for term in all_terms:
            if concept_lower == term.lower():
                return data.get('related', [])

    return []


# =============================================================================
# SEARCH RESULT HIGHLIGHTING
# =============================================================================

@dataclass
class HighlightedConcept:
    """Information about a highlighted concept in search results."""
    concept: str
    matched_terms: List[str]
    positions: List[Tuple[int, int]]


def find_concept_matches(
    text: str,
    concepts: List[str],
    include_expansions: bool = True
) -> List[HighlightedConcept]:
    """
    Find all concept matches in text with positions.

    Args:
        text: Text to search in
        concepts: List of concepts to find
        include_expansions: Whether to include expanded terms

    Returns:
        List of HighlightedConcept with match information

    Arabic: إيجاد تطابق المفاهيم في النص
    """
    results = []
    text_lower = text.lower()

    for concept in concepts:
        matched_terms = []
        positions = []

        # Get terms to search for
        if include_expansions:
            terms = get_concept_expansions(concept, 'both')
        else:
            terms = {concept}

        for term in terms:
            term_lower = term.lower()
            start = 0
            while True:
                pos = text_lower.find(term_lower, start)
                if pos == -1:
                    break
                positions.append((pos, pos + len(term)))
                if term not in matched_terms:
                    matched_terms.append(term)
                start = pos + 1

        if matched_terms:
            results.append(HighlightedConcept(
                concept=concept,
                matched_terms=matched_terms,
                positions=sorted(positions)
            ))

    return results
