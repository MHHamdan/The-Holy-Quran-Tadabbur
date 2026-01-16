"""
Search Suggestions Service for Auto-Complete and Query Enhancement.

Provides real-time search suggestions for:
- Surah names (Arabic and English)
- Prophet names
- Quranic themes and concepts
- Popular search queries
- Query expansion with synonyms

Arabic: خدمة اقتراحات البحث والإكمال التلقائي
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Types of search suggestions."""
    SURAH = "surah"
    PROPHET = "prophet"
    THEME = "theme"
    CONCEPT = "concept"
    VERSE = "verse"
    RECENT = "recent"
    POPULAR = "popular"


@dataclass
class SearchSuggestion:
    """A single search suggestion."""
    text: str                           # Suggestion text
    text_ar: str                        # Arabic version
    type: SuggestionType                # Category
    relevance: float = 1.0              # Relevance score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# STATIC SUGGESTION DATA
# =============================================================================

# Surah names (Arabic and English) with numbers
SURAH_DATA = [
    (1, "الفاتحة", "Al-Fatiha", "The Opening"),
    (2, "البقرة", "Al-Baqarah", "The Cow"),
    (3, "آل عمران", "Aal-Imran", "Family of Imran"),
    (4, "النساء", "An-Nisa", "The Women"),
    (5, "المائدة", "Al-Ma'idah", "The Table Spread"),
    (6, "الأنعام", "Al-An'am", "The Cattle"),
    (7, "الأعراف", "Al-A'raf", "The Heights"),
    (8, "الأنفال", "Al-Anfal", "The Spoils of War"),
    (9, "التوبة", "At-Tawbah", "The Repentance"),
    (10, "يونس", "Yunus", "Jonah"),
    (11, "هود", "Hud", "Hud"),
    (12, "يوسف", "Yusuf", "Joseph"),
    (13, "الرعد", "Ar-Ra'd", "The Thunder"),
    (14, "إبراهيم", "Ibrahim", "Abraham"),
    (15, "الحجر", "Al-Hijr", "The Rocky Tract"),
    (16, "النحل", "An-Nahl", "The Bee"),
    (17, "الإسراء", "Al-Isra", "The Night Journey"),
    (18, "الكهف", "Al-Kahf", "The Cave"),
    (19, "مريم", "Maryam", "Mary"),
    (20, "طه", "Ta-Ha", "Ta-Ha"),
    (21, "الأنبياء", "Al-Anbiya", "The Prophets"),
    (22, "الحج", "Al-Hajj", "The Pilgrimage"),
    (23, "المؤمنون", "Al-Mu'minun", "The Believers"),
    (24, "النور", "An-Nur", "The Light"),
    (25, "الفرقان", "Al-Furqan", "The Criterion"),
    (26, "الشعراء", "Ash-Shu'ara", "The Poets"),
    (27, "النمل", "An-Naml", "The Ant"),
    (28, "القصص", "Al-Qasas", "The Stories"),
    (29, "العنكبوت", "Al-Ankabut", "The Spider"),
    (30, "الروم", "Ar-Rum", "The Romans"),
    (31, "لقمان", "Luqman", "Luqman"),
    (32, "السجدة", "As-Sajdah", "The Prostration"),
    (33, "الأحزاب", "Al-Ahzab", "The Combined Forces"),
    (34, "سبأ", "Saba", "Sheba"),
    (35, "فاطر", "Fatir", "Originator"),
    (36, "يس", "Ya-Sin", "Ya-Sin"),
    (37, "الصافات", "As-Saffat", "Those Who Set The Ranks"),
    (38, "ص", "Sad", "Sad"),
    (39, "الزمر", "Az-Zumar", "The Troops"),
    (40, "غافر", "Ghafir", "The Forgiver"),
    (41, "فصلت", "Fussilat", "Explained in Detail"),
    (42, "الشورى", "Ash-Shura", "The Consultation"),
    (43, "الزخرف", "Az-Zukhruf", "The Ornaments of Gold"),
    (44, "الدخان", "Ad-Dukhan", "The Smoke"),
    (45, "الجاثية", "Al-Jathiyah", "The Crouching"),
    (46, "الأحقاف", "Al-Ahqaf", "The Wind-Curved Sandhills"),
    (47, "محمد", "Muhammad", "Muhammad"),
    (48, "الفتح", "Al-Fath", "The Victory"),
    (49, "الحجرات", "Al-Hujurat", "The Rooms"),
    (50, "ق", "Qaf", "Qaf"),
    (51, "الذاريات", "Adh-Dhariyat", "The Winnowing Winds"),
    (52, "الطور", "At-Tur", "The Mount"),
    (53, "النجم", "An-Najm", "The Star"),
    (54, "القمر", "Al-Qamar", "The Moon"),
    (55, "الرحمن", "Ar-Rahman", "The Beneficent"),
    (56, "الواقعة", "Al-Waqi'ah", "The Inevitable"),
    (57, "الحديد", "Al-Hadid", "The Iron"),
    (58, "المجادلة", "Al-Mujadila", "The Pleading Woman"),
    (59, "الحشر", "Al-Hashr", "The Exile"),
    (60, "الممتحنة", "Al-Mumtahanah", "She That Is To Be Examined"),
    (61, "الصف", "As-Saf", "The Ranks"),
    (62, "الجمعة", "Al-Jumu'ah", "The Congregation"),
    (63, "المنافقون", "Al-Munafiqun", "The Hypocrites"),
    (64, "التغابن", "At-Taghabun", "The Mutual Disillusion"),
    (65, "الطلاق", "At-Talaq", "The Divorce"),
    (66, "التحريم", "At-Tahrim", "The Prohibition"),
    (67, "الملك", "Al-Mulk", "The Sovereignty"),
    (68, "القلم", "Al-Qalam", "The Pen"),
    (69, "الحاقة", "Al-Haqqah", "The Reality"),
    (70, "المعارج", "Al-Ma'arij", "The Ascending Stairways"),
    (71, "نوح", "Nuh", "Noah"),
    (72, "الجن", "Al-Jinn", "The Jinn"),
    (73, "المزمل", "Al-Muzzammil", "The Enshrouded One"),
    (74, "المدثر", "Al-Muddaththir", "The Cloaked One"),
    (75, "القيامة", "Al-Qiyamah", "The Resurrection"),
    (76, "الإنسان", "Al-Insan", "The Man"),
    (77, "المرسلات", "Al-Mursalat", "The Emissaries"),
    (78, "النبأ", "An-Naba", "The Tidings"),
    (79, "النازعات", "An-Nazi'at", "Those Who Drag Forth"),
    (80, "عبس", "Abasa", "He Frowned"),
    (81, "التكوير", "At-Takwir", "The Overthrowing"),
    (82, "الانفطار", "Al-Infitar", "The Cleaving"),
    (83, "المطففين", "Al-Mutaffifin", "The Defrauding"),
    (84, "الانشقاق", "Al-Inshiqaq", "The Sundering"),
    (85, "البروج", "Al-Buruj", "The Mansions of the Stars"),
    (86, "الطارق", "At-Tariq", "The Nightcommer"),
    (87, "الأعلى", "Al-A'la", "The Most High"),
    (88, "الغاشية", "Al-Ghashiyah", "The Overwhelming"),
    (89, "الفجر", "Al-Fajr", "The Dawn"),
    (90, "البلد", "Al-Balad", "The City"),
    (91, "الشمس", "Ash-Shams", "The Sun"),
    (92, "الليل", "Al-Layl", "The Night"),
    (93, "الضحى", "Ad-Duhaa", "The Morning Hours"),
    (94, "الشرح", "Ash-Sharh", "The Relief"),
    (95, "التين", "At-Tin", "The Fig"),
    (96, "العلق", "Al-Alaq", "The Clot"),
    (97, "القدر", "Al-Qadr", "The Power"),
    (98, "البينة", "Al-Bayyinah", "The Clear Proof"),
    (99, "الزلزلة", "Az-Zalzalah", "The Earthquake"),
    (100, "العاديات", "Al-Adiyat", "The Courser"),
    (101, "القارعة", "Al-Qari'ah", "The Calamity"),
    (102, "التكاثر", "At-Takathur", "The Rivalry in World Increase"),
    (103, "العصر", "Al-Asr", "The Declining Day"),
    (104, "الهمزة", "Al-Humazah", "The Traducer"),
    (105, "الفيل", "Al-Fil", "The Elephant"),
    (106, "قريش", "Quraysh", "Quraysh"),
    (107, "الماعون", "Al-Ma'un", "The Small Kindnesses"),
    (108, "الكوثر", "Al-Kawthar", "The Abundance"),
    (109, "الكافرون", "Al-Kafirun", "The Disbelievers"),
    (110, "النصر", "An-Nasr", "The Divine Support"),
    (111, "المسد", "Al-Masad", "The Palm Fiber"),
    (112, "الإخلاص", "Al-Ikhlas", "The Sincerity"),
    (113, "الفلق", "Al-Falaq", "The Daybreak"),
    (114, "الناس", "An-Nas", "Mankind"),
]

# Prophet names with Arabic and English variants
PROPHET_DATA = [
    ("آدم", "Adam", ["آدم عليه السلام"]),
    ("إدريس", "Idris", ["Enoch"]),
    ("نوح", "Nuh", ["Noah", "نوح عليه السلام"]),
    ("هود", "Hud", []),
    ("صالح", "Salih", []),
    ("إبراهيم", "Ibrahim", ["Abraham", "الخليل", "إبراهيم عليه السلام"]),
    ("لوط", "Lut", ["Lot"]),
    ("إسماعيل", "Ismail", ["Ishmael"]),
    ("إسحاق", "Ishaq", ["Isaac"]),
    ("يعقوب", "Yaqub", ["Jacob", "Israel", "إسرائيل"]),
    ("يوسف", "Yusuf", ["Joseph"]),
    ("أيوب", "Ayyub", ["Job"]),
    ("شعيب", "Shu'ayb", ["Jethro"]),
    ("موسى", "Musa", ["Moses", "كليم الله", "موسى عليه السلام"]),
    ("هارون", "Harun", ["Aaron"]),
    ("ذو الكفل", "Dhul-Kifl", ["Ezekiel"]),
    ("داود", "Dawud", ["David"]),
    ("سليمان", "Sulayman", ["Solomon"]),
    ("إلياس", "Ilyas", ["Elijah"]),
    ("اليسع", "Al-Yasa", ["Elisha"]),
    ("يونس", "Yunus", ["Jonah", "ذو النون"]),
    ("زكريا", "Zakariya", ["Zechariah"]),
    ("يحيى", "Yahya", ["John the Baptist"]),
    ("عيسى", "Isa", ["Jesus", "المسيح", "عيسى ابن مريم"]),
    ("محمد", "Muhammad", ["Ahmad", "الرسول", "النبي", "خاتم الأنبياء"]),
]

# Quranic themes and concepts
THEME_DATA = [
    # Faith & Worship
    ("الإيمان", "Faith", "iman", ["الإيمان بالله", "التصديق"]),
    ("التوحيد", "Monotheism", "tawhid", ["وحدانية الله", "الإله الواحد"]),
    ("العبادة", "Worship", "ibadah", ["الصلاة", "العبادات"]),
    ("الصلاة", "Prayer", "salah", ["الصلوات", "إقامة الصلاة"]),
    ("الزكاة", "Charity", "zakah", ["الصدقة", "الإنفاق"]),
    ("الصيام", "Fasting", "siyam", ["رمضان", "الصوم"]),
    ("الحج", "Pilgrimage", "hajj", ["العمرة", "الكعبة", "مكة"]),
    # Morality & Ethics
    ("الصبر", "Patience", "sabr", ["الصابرين", "الاحتمال"]),
    ("الشكر", "Gratitude", "shukr", ["الحمد", "الشاكرين"]),
    ("التقوى", "Piety", "taqwa", ["الخوف من الله", "الورع"]),
    ("العدل", "Justice", "adl", ["الإنصاف", "القسط"]),
    ("الرحمة", "Mercy", "rahmah", ["الرحمن", "الرحيم"]),
    ("التوبة", "Repentance", "tawbah", ["الاستغفار", "الرجوع إلى الله"]),
    ("الصدق", "Truthfulness", "sidq", ["الأمانة", "الصادقين"]),
    # Life & Death
    ("الموت", "Death", "mawt", ["الوفاة", "الأجل"]),
    ("البعث", "Resurrection", "ba'th", ["يوم القيامة", "الآخرة"]),
    ("الجنة", "Paradise", "jannah", ["الفردوس", "النعيم"]),
    ("النار", "Hellfire", "nar", ["جهنم", "العذاب"]),
    ("الحساب", "Judgment", "hisab", ["يوم الدين", "الميزان"]),
    # Guidance
    ("الهداية", "Guidance", "hidayah", ["الصراط المستقيم", "النور"]),
    ("القرآن", "Quran", "quran", ["الكتاب", "الذكر", "الفرقان"]),
    ("الوحي", "Revelation", "wahy", ["التنزيل", "الإنزال"]),
    # Social
    ("الأسرة", "Family", "usrah", ["الوالدين", "الأولاد", "الأقربين"]),
    ("الزواج", "Marriage", "nikah", ["الأزواج", "النكاح"]),
    ("المعاملات", "Transactions", "muamalat", ["التجارة", "البيع"]),
]

# Query synonyms for expansion
QUERY_SYNONYMS: Dict[str, List[str]] = {
    # Arabic synonyms
    "الله": ["رب", "الإله", "الرحمن", "الرب"],
    "الرسول": ["النبي", "محمد", "أحمد"],
    "الجنة": ["الفردوس", "النعيم", "دار السلام"],
    "النار": ["جهنم", "السعير", "الحطمة"],
    "الصلاة": ["الصلوات", "العبادة"],
    "موسى": ["كليم الله", "Moses"],
    "عيسى": ["المسيح", "ابن مريم", "Jesus"],
    # English synonyms
    "god": ["allah", "lord", "deity"],
    "prophet": ["messenger", "rasul", "nabi"],
    "heaven": ["paradise", "jannah", "garden"],
    "hell": ["hellfire", "jahannam", "fire"],
    "prayer": ["salah", "worship"],
    "moses": ["musa", "موسى"],
    "jesus": ["isa", "messiah", "عيسى"],
    "abraham": ["ibrahim", "إبراهيم"],
    "joseph": ["yusuf", "يوسف"],
    "mary": ["maryam", "مريم"],
}


# =============================================================================
# SEARCH SUGGESTIONS SERVICE
# =============================================================================

class SearchSuggestionsService:
    """
    Service for providing search auto-complete suggestions.

    Supports bilingual (Arabic/English) suggestions for:
    - Surah names
    - Prophet names
    - Themes and concepts
    - Recent/popular searches
    """

    def __init__(self):
        self._surah_index = self._build_surah_index()
        self._prophet_index = self._build_prophet_index()
        self._theme_index = self._build_theme_index()
        self._recent_searches: List[str] = []
        self._popular_searches: Dict[str, int] = defaultdict(int)

    def _build_surah_index(self) -> Dict[str, List[SearchSuggestion]]:
        """Build searchable index of surah names."""
        index = defaultdict(list)

        for num, ar_name, en_name, en_meaning in SURAH_DATA:
            suggestion = SearchSuggestion(
                text=en_name,
                text_ar=ar_name,
                type=SuggestionType.SURAH,
                relevance=1.0,
                metadata={"number": num, "meaning": en_meaning}
            )

            # Index by Arabic name
            index[self._normalize(ar_name)].append(suggestion)

            # Index by English name
            index[en_name.lower()].append(suggestion)

            # Index by English meaning
            for word in en_meaning.lower().split():
                if len(word) > 2:
                    index[word].append(suggestion)

            # Index by number
            index[str(num)].append(suggestion)

        return index

    def _build_prophet_index(self) -> Dict[str, List[SearchSuggestion]]:
        """Build searchable index of prophet names."""
        index = defaultdict(list)

        for ar_name, en_name, aliases in PROPHET_DATA:
            suggestion = SearchSuggestion(
                text=en_name,
                text_ar=ar_name,
                type=SuggestionType.PROPHET,
                relevance=1.0,
                metadata={"aliases": aliases}
            )

            # Index by Arabic name
            index[self._normalize(ar_name)].append(suggestion)

            # Index by English name
            index[en_name.lower()].append(suggestion)

            # Index by aliases
            for alias in aliases:
                index[self._normalize(alias)].append(suggestion)
                index[alias.lower()].append(suggestion)

        return index

    def _build_theme_index(self) -> Dict[str, List[SearchSuggestion]]:
        """Build searchable index of themes and concepts."""
        index = defaultdict(list)

        for ar_name, en_name, key, related in THEME_DATA:
            suggestion = SearchSuggestion(
                text=en_name,
                text_ar=ar_name,
                type=SuggestionType.THEME,
                relevance=1.0,
                metadata={"key": key, "related": related}
            )

            # Index by Arabic name
            index[self._normalize(ar_name)].append(suggestion)

            # Index by English name
            index[en_name.lower()].append(suggestion)

            # Index by key
            index[key.lower()].append(suggestion)

            # Index by related terms
            for term in related:
                index[self._normalize(term)].append(suggestion)

        return index

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ""
        # Remove diacritics
        diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        result = diacritics.sub('', text)
        # Normalize alef
        result = result.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        return result.lower().strip()

    def get_suggestions(
        self,
        query: str,
        limit: int = 10,
        types: Optional[List[SuggestionType]] = None,
    ) -> List[SearchSuggestion]:
        """
        Get search suggestions for a query.

        Args:
            query: Search query (partial or full)
            limit: Maximum suggestions to return
            types: Filter by suggestion types

        Returns:
            List of SearchSuggestion objects
        """
        if not query or len(query) < 1:
            return []

        normalized = self._normalize(query)
        suggestions = []
        seen = set()

        # Search all indices
        indices = [
            (self._surah_index, SuggestionType.SURAH),
            (self._prophet_index, SuggestionType.PROPHET),
            (self._theme_index, SuggestionType.THEME),
        ]

        for index, default_type in indices:
            if types and default_type not in types:
                continue

            for key, items in index.items():
                if key.startswith(normalized) or normalized in key:
                    for item in items:
                        # Deduplicate
                        item_key = f"{item.type}:{item.text}"
                        if item_key in seen:
                            continue
                        seen.add(item_key)

                        # Calculate relevance
                        if key.startswith(normalized):
                            item.relevance = 1.0 - (len(key) - len(normalized)) * 0.05
                        else:
                            item.relevance = 0.7

                        suggestions.append(item)

        # Sort by relevance
        suggestions.sort(key=lambda x: x.relevance, reverse=True)

        return suggestions[:limit]

    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms.

        Args:
            query: Original search query

        Returns:
            List of expanded terms including original
        """
        terms = [query]
        normalized = self._normalize(query)
        query_lower = query.lower()

        # Check synonyms
        if normalized in QUERY_SYNONYMS:
            terms.extend(QUERY_SYNONYMS[normalized])
        if query_lower in QUERY_SYNONYMS:
            terms.extend(QUERY_SYNONYMS[query_lower])

        # Check individual words
        words = query.split()
        for word in words:
            word_norm = self._normalize(word)
            word_lower = word.lower()
            if word_norm in QUERY_SYNONYMS:
                terms.extend(QUERY_SYNONYMS[word_norm])
            if word_lower in QUERY_SYNONYMS:
                terms.extend(QUERY_SYNONYMS[word_lower])

        return list(set(terms))

    def record_search(self, query: str) -> None:
        """Record a search query for recent/popular tracking."""
        normalized = self._normalize(query)
        if not normalized:
            return

        # Update recent searches
        if normalized in self._recent_searches:
            self._recent_searches.remove(normalized)
        self._recent_searches.insert(0, normalized)
        self._recent_searches = self._recent_searches[:100]  # Keep last 100

        # Update popularity
        self._popular_searches[normalized] += 1

    def get_recent_searches(self, limit: int = 10) -> List[str]:
        """Get recent search queries."""
        return self._recent_searches[:limit]

    def get_popular_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular search queries."""
        sorted_searches = sorted(
            self._popular_searches.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_searches[:limit]

    def get_trending_themes(self) -> List[SearchSuggestion]:
        """Get trending themes (static for now, can be dynamic later)."""
        trending = [
            ("الصبر", "Patience"),
            ("الرحمة", "Mercy"),
            ("التقوى", "Piety"),
            ("الهداية", "Guidance"),
            ("التوبة", "Repentance"),
        ]

        suggestions = []
        for ar, en in trending:
            results = self.get_suggestions(ar, limit=1, types=[SuggestionType.THEME])
            if results:
                suggestions.append(results[0])

        return suggestions


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_suggestions_service: Optional[SearchSuggestionsService] = None


def get_suggestions_service() -> SearchSuggestionsService:
    """Get the search suggestions service singleton."""
    global _suggestions_service
    if _suggestions_service is None:
        _suggestions_service = SearchSuggestionsService()
    return _suggestions_service
