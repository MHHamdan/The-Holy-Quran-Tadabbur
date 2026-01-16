"""
Query expansion for Islamic terminology.

Expands queries with Arabic transliterations, synonyms, and related terms
to improve retrieval accuracy.

CAPS AND LIMITS:
- Max 5 expansion terms per query
- Intent-based expansion (story queries get prophet names, fiqh queries get rulings)
- Always preserves original query terms
"""
import re
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum


class QueryIntent(str, Enum):
    """Query intent categories."""
    VERSE_MEANING = "verse_meaning"
    STORY_EXPLORATION = "story_exploration"
    THEME_SEARCH = "theme_search"
    COMPARATIVE = "comparative"
    LINGUISTIC = "linguistic"
    RULING = "ruling"
    UNKNOWN = "unknown"


@dataclass
class ExpandedQuery:
    """Result of query expansion."""
    original: str
    expanded_terms: List[str]
    arabic_terms: List[str]
    combined: str
    expansion_applied: List[str]
    intent: QueryIntent
    detected_concepts: List[str] = field(default_factory=list)  # Multi-concept detection
    is_multi_concept: bool = False  # Flag for multi-concept queries
    cross_language_terms: List[str] = field(default_factory=list)  # Cross-language matches


# Maximum expansions to add
MAX_EXPANSIONS = 5
MAX_ARABIC_TERMS = 3
MAX_COMBINED_LENGTH = 500  # Characters

# Multi-concept detection patterns (English and Arabic)
MULTI_CONCEPT_PATTERNS = [
    r'\s+and\s+',           # X and Y
    r'\s+with\s+',          # X with Y
    r'\s*\+\s*',            # X + Y
    r'\s*&\s*',             # X & Y
    r'\s+و\s+',             # Arabic "and" (و)
    r'\s+مع\s+',            # Arabic "with" (مع)
    r'\s*،\s*',             # Arabic comma
    r',\s*',                # English comma
    r'\s+between\s+',       # between X and Y
    r'\s+بين\s+',           # Arabic "between"
]

# Story connections for multi-concept expansion
STORY_CONNECTIONS = {
    # Prophet-person connections
    ("solomon", "sheba"): {
        "themes": ["wisdom", "power", "faith"],
        "arabic_pair": ("سليمان", "سبأ"),
        "story_id": "sulaiman_balqis",
    },
    ("solomon", "queen"): {
        "themes": ["wisdom", "power", "faith"],
        "arabic_pair": ("سليمان", "ملكة"),
        "story_id": "sulaiman_balqis",
    },
    ("moses", "pharaoh"): {
        "themes": ["oppression", "liberation", "faith"],
        "arabic_pair": ("موسى", "فرعون"),
        "story_id": "musa_firaun",
    },
    ("moses", "khidr"): {
        "themes": ["knowledge", "wisdom", "patience"],
        "arabic_pair": ("موسى", "الخضر"),
        "story_id": "musa_khidr",
    },
    ("joseph", "brothers"): {
        "themes": ["forgiveness", "patience", "trust"],
        "arabic_pair": ("يوسف", "إخوة"),
        "story_id": "yusuf",
    },
    ("abraham", "ishmael"): {
        "themes": ["sacrifice", "obedience", "faith"],
        "arabic_pair": ("إبراهيم", "إسماعيل"),
        "story_id": "ibrahim_ismail",
    },
    ("abraham", "isaac"): {
        "themes": ["lineage", "promise", "faith"],
        "arabic_pair": ("إبراهيم", "إسحاق"),
        "story_id": "ibrahim",
    },
    ("david", "goliath"): {
        "themes": ["faith", "courage", "victory"],
        "arabic_pair": ("داود", "جالوت"),
        "story_id": "dawud_jalut",
    },
    ("noah", "flood"): {
        "themes": ["patience", "faith", "salvation"],
        "arabic_pair": ("نوح", "طوفان"),
        "story_id": "nuh",
    },
    ("lot", "people"): {
        "themes": ["warning", "punishment", "righteousness"],
        "arabic_pair": ("لوط", "قوم"),
        "story_id": "lut",
    },
    ("mary", "jesus"): {
        "themes": ["miracle", "faith", "chastity"],
        "arabic_pair": ("مريم", "عيسى"),
        "story_id": "maryam_isa",
    },
    ("adam", "eve"): {
        "themes": ["creation", "temptation", "repentance"],
        "arabic_pair": ("آدم", "حواء"),
        "story_id": "adam",
    },
    ("hud", "aad"): {
        "themes": ["warning", "arrogance", "destruction"],
        "arabic_pair": ("هود", "عاد"),
        "story_id": "hud_aad",
    },
    ("saleh", "thamud"): {
        "themes": ["miracle", "disobedience", "destruction"],
        "arabic_pair": ("صالح", "ثمود"),
        "story_id": "saleh_thamud",
    },
}


# Islamic term mappings: English -> (Arabic, transliterations, synonyms, intents)
# intents: list of QueryIntent values this term is relevant to
ISLAMIC_TERM_MAPPINGS = {
    # Core concepts (all intents)
    "patience": ("صبر", ["sabr", "sabir", "sabireen"], ["steadfastness", "endurance"], None),
    "prayer": ("صلاة", ["salah", "salat"], ["worship"], None),
    "fasting": ("صوم", ["sawm", "siyam"], [], None),
    "charity": ("زكاة", ["zakah", "zakat", "sadaqah"], ["alms"], ["ruling"]),
    "pilgrimage": ("حج", ["hajj", "haj"], [], ["ruling"]),
    "faith": ("إيمان", ["iman", "imaan"], ["belief"], None),
    "trust": ("توكل", ["tawakkul"], ["reliance"], ["verse_meaning"]),
    "repentance": ("توبة", ["tawbah", "tawba"], ["seeking forgiveness"], None),
    "monotheism": ("توحيد", ["tawhid", "tawheed"], ["oneness of God"], None),
    "god-consciousness": ("تقوى", ["taqwa"], ["piety", "righteousness"], None),
    "gratitude": ("شكر", ["shukr"], ["thankfulness"], None),
    "remembrance": ("ذكر", ["dhikr", "zikr"], ["mention of Allah"], None),

    # Prophets (story_exploration intent)
    "adam": ("آدم", ["aadam"], ["first man"], ["story_exploration"]),
    "noah": ("نوح", ["nuh", "nooh"], ["prophet of the flood"], ["story_exploration"]),
    "abraham": ("إبراهيم", ["ibrahim", "ibraheem"], ["khalilullah"], ["story_exploration"]),
    "moses": ("موسى", ["musa", "moosa"], ["kalimullah"], ["story_exploration"]),
    "jesus": ("عيسى", ["isa", "eesa"], ["messiah"], ["story_exploration"]),
    "muhammad": ("محمد", ["mohammad", "mohammed"], ["prophet", "rasulullah"], ["story_exploration"]),
    "joseph": ("يوسف", ["yusuf", "yousuf"], [], ["story_exploration"]),
    "david": ("داود", ["dawud", "dawood"], [], ["story_exploration"]),
    "solomon": ("سليمان", ["sulayman", "sulaiman"], ["wise king"], ["story_exploration"]),
    "jonah": ("يونس", ["yunus", "younus"], [], ["story_exploration"]),
    "job": ("أيوب", ["ayyub", "ayub"], ["patient one"], ["story_exploration"]),
    "mary": ("مريم", ["maryam", "mariam"], ["mother of isa"], ["story_exploration"]),

    # Quranic terms (verse_meaning, theme_search)
    "verse": ("آية", ["ayah", "aya"], ["sign"], ["verse_meaning"]),
    "chapter": ("سورة", ["surah", "sura"], [], ["verse_meaning"]),
    "revelation": ("وحي", ["wahy", "wahi"], [], ["verse_meaning"]),
    "guidance": ("هداية", ["hidaya", "hidayah"], ["right path"], ["verse_meaning", "theme_search"]),
    "mercy": ("رحمة", ["rahma", "rahmah"], ["compassion"], ["verse_meaning", "theme_search"]),
    "punishment": ("عذاب", ["adhab", "azab"], ["torment"], ["verse_meaning"]),
    "paradise": ("جنة", ["jannah", "janna"], ["heaven"], ["theme_search"]),
    "hellfire": ("جهنم", ["jahannam"], ["hell"], ["theme_search"]),
    "angel": ("ملك", ["malak", "malaika"], [], ["verse_meaning"]),
    "jinn": ("جن", ["djinn"], ["unseen beings"], ["verse_meaning"]),
    "devil": ("شيطان", ["shaytan", "shaitan"], ["satan"], ["story_exploration"]),

    # Story-related (story_exploration)
    "story": ("قصة", ["qissa", "qissah"], ["narrative"], ["story_exploration"]),
    "pharaoh": ("فرعون", ["firawn", "firaun"], ["king of egypt"], ["story_exploration"]),
    "children of israel": ("بني إسرائيل", ["bani israel"], ["israelites"], ["story_exploration"]),
    "ark": ("سفينة", ["safinah"], ["ship"], ["story_exploration"]),
    "flood": ("طوفان", ["tufan"], ["deluge"], ["story_exploration"]),
    "cave": ("كهف", ["kahf"], [], ["story_exploration"]),

    # Fiqh/Rulings (ruling intent)
    "halal": ("حلال", ["halaal"], ["permissible"], ["ruling"]),
    "haram": ("حرام", ["haraam"], ["forbidden"], ["ruling"]),
    "obligatory": ("فرض", ["fard", "wajib"], [], ["ruling"]),
    "recommended": ("مستحب", ["mustahab", "sunnah"], [], ["ruling"]),
    "ruling": ("حكم", ["hukm"], ["decree"], ["ruling"]),
    "witness": ("شهادة", ["shahada", "shahadah"], [], ["ruling"]),

    # Linguistic (linguistic intent)
    "root": ("جذر", ["jadhr"], [], ["linguistic"]),
    "word": ("كلمة", ["kalima", "kalimah"], [], ["linguistic"]),
    "grammar": ("نحو", ["nahw"], [], ["linguistic"]),
    "meaning": ("معنى", ["maana", "ma'na"], [], ["linguistic", "verse_meaning"]),

    # Actions and concepts
    "worship": ("عبادة", ["ibadah", "ibadat"], ["devotion"], None),
    "sin": ("ذنب", ["dhanb", "zunub"], ["transgression"], None),
    "forgiveness": ("مغفرة", ["maghfirah"], ["pardon"], None),
    "test": ("ابتلاء", ["ibtila", "fitna"], ["trial"], None),
    "reward": ("أجر", ["ajr", "thawab"], ["recompense"], None),

    # Additional prophets for comprehensive coverage
    "ishmael": ("إسماعيل", ["ismail", "ismael"], ["son of ibrahim"], ["story_exploration"]),
    "isaac": ("إسحاق", ["ishaq", "ishak"], ["son of ibrahim"], ["story_exploration"]),
    "jacob": ("يعقوب", ["yaqub", "yacoub"], ["israel"], ["story_exploration"]),
    "lot": ("لوط", ["lut"], [], ["story_exploration"]),
    "shuaib": ("شعيب", ["shoaib"], ["prophet of madyan"], ["story_exploration"]),
    "saleh": ("صالح", ["salih"], ["prophet of thamud"], ["story_exploration"]),
    "hud": ("هود", ["hood"], ["prophet of aad"], ["story_exploration"]),
    "idris": ("إدريس", ["idrees"], [], ["story_exploration"]),
    "elijah": ("إلياس", ["ilyas", "elias"], [], ["story_exploration"]),
    "elisha": ("اليسع", ["al-yasa"], [], ["story_exploration"]),
    "zechariah": ("زكريا", ["zakariya", "zakaria"], [], ["story_exploration"]),
    "john": ("يحيى", ["yahya"], ["john the baptist"], ["story_exploration"]),
    "aaron": ("هارون", ["harun", "haroun"], ["brother of musa"], ["story_exploration"]),
    "dhul-qarnayn": ("ذو القرنين", ["zulqarnayn"], ["two-horned one"], ["story_exploration"]),
    "luqman": ("لقمان", ["loqman"], ["wise sage"], ["story_exploration"]),
    "khidr": ("الخضر", ["al-khidr", "khizr"], ["green one"], ["story_exploration"]),

    # Nations and peoples
    "aad": ("عاد", ["'ad"], ["people of hud"], ["story_exploration"]),
    "thamud": ("ثمود", ["samud"], ["people of saleh"], ["story_exploration"]),
    "madyan": ("مدين", ["midian"], ["people of shuaib"], ["story_exploration"]),
    "people of lot": ("قوم لوط", ["qawm lut"], ["sodom and gomorrah"], ["story_exploration"]),
    "quraysh": ("قريش", ["quraish"], ["tribe of prophet"], ["story_exploration"]),

    # Important Quranic themes
    "justice": ("عدل", ["adl", "'adl"], ["fairness", "equity"], ["theme_search"]),
    "oppression": ("ظلم", ["zulm", "dhulm"], ["injustice", "tyranny"], None),
    "truth": ("حق", ["haq", "haqq"], ["reality"], None),
    "falsehood": ("باطل", ["batil"], ["vanity"], None),
    "knowledge": ("علم", ["ilm", "'ilm"], ["learning"], None),
    "wisdom": ("حكمة", ["hikma", "hikmah"], [], None),
    "light": ("نور", ["nur", "noor"], [], ["verse_meaning"]),
    "darkness": ("ظلمات", ["zulumat", "dhulumaat"], [], ["verse_meaning"]),
    "heart": ("قلب", ["qalb", "galb"], [], ["verse_meaning"]),
    "soul": ("نفس", ["nafs"], [], ["verse_meaning"]),
    "spirit": ("روح", ["ruh", "rooh"], [], ["verse_meaning"]),
    "covenant": ("عهد", ["ahd", "'ahd"], ["promise"], None),
    "creation": ("خلق", ["khalq"], [], None),
    "resurrection": ("بعث", ["ba'th"], ["day of rising"], None),
    "judgment": ("حساب", ["hisab"], ["reckoning"], None),
    "deed": ("عمل", ["amal", "'amal"], ["action"], None),

    # Tafsir terminology
    "interpretation": ("تفسير", ["tafsir", "tafseer"], ["exegesis"], ["verse_meaning"]),
    "commentary": ("شرح", ["sharh"], [], ["verse_meaning"]),
    "context": ("سياق", ["siyaq"], ["occasion of revelation"], ["verse_meaning"]),
    "abrogation": ("نسخ", ["naskh"], ["mansukh"], ["verse_meaning", "ruling"]),
    "reason for revelation": ("سبب النزول", ["asbab al-nuzul", "sabab nuzul"], [], ["verse_meaning"]),

    # Famous verses (expand to verse reference terms)
    "ayat al-kursi": ("آية الكرسي", ["ayatul kursi", "throne verse", "2:255"], ["greatest verse"], ["verse_meaning"]),
    "throne verse": ("آية الكرسي", ["ayat al-kursi", "kursi", "2:255"], [], ["verse_meaning"]),
    "الكرسي": ("آية الكرسي", ["ayat al-kursi", "2:255"], ["throne"], ["verse_meaning"]),
    "al-fatiha": ("الفاتحة", ["fatiha", "opening"], ["1:1-7"], ["verse_meaning"]),
    "al-ikhlas": ("الإخلاص", ["ikhlas", "sincerity", "112:1-4"], [], ["verse_meaning"]),
    "light verse": ("آية النور", ["ayat an-nur", "24:35"], [], ["verse_meaning"]),
    "yasin": ("يس", ["yaseen", "ya sin", "36:1-83"], ["heart of quran"], ["verse_meaning"]),
    "al-kahf": ("الكهف", ["kahf", "cave", "18:1-110"], ["friday surah"], ["verse_meaning"]),
    "ar-rahman": ("الرحمن", ["rahman", "55:1-78"], ["merciful"], ["verse_meaning"]),
    "al-mulk": ("الملك", ["mulk", "tabarak", "67:1-30"], ["sovereignty"], ["verse_meaning"]),

    # Additional fiqh terms
    "purification": ("طهارة", ["tahara", "taharah"], ["cleanliness"], ["ruling"]),
    "ablution": ("وضوء", ["wudu", "wudhu"], [], ["ruling"]),
    "ritual bath": ("غسل", ["ghusl"], [], ["ruling"]),
    "inheritance": ("ميراث", ["mirath"], ["inheritance law"], ["ruling"]),
    "marriage": ("نكاح", ["nikah", "nikaah"], ["wedding"], ["ruling"]),
    "divorce": ("طلاق", ["talaq"], [], ["ruling"]),
    "usury": ("ربا", ["riba"], ["interest"], ["ruling"]),
    "contract": ("عقد", ["aqd", "'aqd"], [], ["ruling"]),
}


class QueryExpander:
    """
    Expands queries with Islamic terminology to improve retrieval.

    Features:
    - Caps expansion to MAX_EXPANSIONS terms
    - Intent-based expansion (only adds relevant terms)
    - Preserves original query
    - Multi-concept detection (e.g., "Solomon + Queen of Sheba")
    - Cross-language expansion (Arabic ↔ English)
    """

    def __init__(self):
        self.mappings = ISLAMIC_TERM_MAPPINGS
        self.story_connections = STORY_CONNECTIONS
        self._build_reverse_index()
        self._build_arabic_to_english_index()

    def _build_reverse_index(self):
        """Build reverse index from all terms to canonical English."""
        self.reverse_index = {}

        for english, (arabic, translits, synonyms, intents) in self.mappings.items():
            # Map Arabic to English
            self.reverse_index[arabic] = english

            # Map transliterations to English
            for translit in translits:
                self.reverse_index[translit.lower()] = english

            # Map synonyms to English
            for synonym in synonyms:
                self.reverse_index[synonym.lower()] = english

            # Map English to itself
            self.reverse_index[english.lower()] = english

    def _build_arabic_to_english_index(self):
        """Build Arabic to English index for cross-language expansion."""
        self.arabic_to_english = {}
        self.english_to_arabic = {}

        for english, (arabic, translits, synonyms, intents) in self.mappings.items():
            self.arabic_to_english[arabic] = english
            self.english_to_arabic[english.lower()] = arabic

    def detect_multi_concept(self, query: str) -> Tuple[bool, List[str], Optional[dict]]:
        """
        Detect if query contains multiple concepts.

        Returns:
            Tuple of (is_multi_concept, detected_concepts, connection_info)
        """
        query_lower = query.lower()
        detected_concepts = []
        connection_info = None

        # Check for multi-concept patterns
        for pattern in MULTI_CONCEPT_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                # Split by pattern and extract concepts
                parts = re.split(pattern, query_lower)
                for part in parts:
                    part = part.strip()
                    if part:
                        # Try to find concepts in this part
                        for word in part.split():
                            clean_word = re.sub(r'[^\w\u0600-\u06FF]', '', word)
                            if clean_word in self.reverse_index:
                                canonical = self.reverse_index[clean_word]
                                if canonical not in detected_concepts:
                                    detected_concepts.append(canonical)

                if len(detected_concepts) >= 2:
                    # Check for known story connections
                    for i, concept1 in enumerate(detected_concepts):
                        for concept2 in detected_concepts[i+1:]:
                            # Check both orderings
                            conn_key = (concept1.lower(), concept2.lower())
                            if conn_key in self.story_connections:
                                connection_info = self.story_connections[conn_key]
                                break
                            conn_key = (concept2.lower(), concept1.lower())
                            if conn_key in self.story_connections:
                                connection_info = self.story_connections[conn_key]
                                break
                        if connection_info:
                            break

                    return True, detected_concepts, connection_info

        # Check for implicit multi-concept (e.g., "story of Solomon and the Queen")
        for (concept1, concept2), info in self.story_connections.items():
            if concept1 in query_lower or concept2 in query_lower:
                # Check if both concepts appear
                arabic1, arabic2 = info["arabic_pair"]
                c1_present = concept1 in query_lower or arabic1 in query
                c2_present = concept2 in query_lower or arabic2 in query

                if c1_present and c2_present:
                    detected_concepts = [concept1, concept2]
                    return True, detected_concepts, info

        return False, detected_concepts, None

    def expand_cross_language(self, query: str) -> List[str]:
        """
        Detect language and provide cross-language expansion.

        Returns list of terms in the other language.
        """
        cross_terms = []

        # Check for Arabic characters
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', query))

        if has_arabic:
            # Arabic query -> expand with English terms
            for arabic_term in re.findall(r'[\u0600-\u06FF]+', query):
                if arabic_term in self.arabic_to_english:
                    english = self.arabic_to_english[arabic_term]
                    if english not in cross_terms:
                        cross_terms.append(english)
        else:
            # English query -> expand with Arabic terms
            for word in query.lower().split():
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word in self.english_to_arabic:
                    arabic = self.english_to_arabic[clean_word]
                    if arabic not in cross_terms:
                        cross_terms.append(arabic)

        return cross_terms[:MAX_ARABIC_TERMS]

    def classify_intent(self, query: str) -> QueryIntent:
        """Classify query intent from query text."""
        q_lower = query.lower()

        # Verse meaning patterns (Arabic and English)
        verse_meaning_patterns = [
            # English
            "meaning", "tafseer", "tafsir", "explain", "interpretation",
            "what is", "what does", "tell me about",
            # Arabic - common question patterns
            "معنى", "تفسير", "شرح", "ما هو", "ما هي", "ماذا",
            "ما معنى", "معني", "فسر", "اشرح",
            # Famous verse detection
            "آية", "سورة", "ayah", "surah", "verse", "chapter",
        ]
        if any(pattern in q_lower for pattern in verse_meaning_patterns):
            return QueryIntent.VERSE_MEANING

        # Story patterns
        story_patterns = [
            "story", "prophet", "narrative", "قصة", "قصص", "نبي", "أنبياء",
            "حكاية", "رواية", "سيرة",
        ]
        if any(pattern in q_lower for pattern in story_patterns):
            return QueryIntent.STORY_EXPLORATION

        # Theme patterns
        theme_patterns = [
            "theme", "topic", "about", "موضوع", "مواضيع", "عن",
        ]
        if any(pattern in q_lower for pattern in theme_patterns):
            return QueryIntent.THEME_SEARCH

        # Comparative patterns
        comparative_patterns = [
            "compare", "difference", "between", "مقارنة", "فرق", "بين",
            "الفرق", "مقابل", "versus", "vs",
        ]
        if any(pattern in q_lower for pattern in comparative_patterns):
            return QueryIntent.COMPARATIVE

        # Linguistic patterns
        linguistic_patterns = [
            "root", "word", "grammar", "جذر", "كلمة", "نحو",
            "لغة", "صرف", "اعراب", "etymology",
        ]
        if any(pattern in q_lower for pattern in linguistic_patterns):
            return QueryIntent.LINGUISTIC

        # Ruling patterns
        ruling_patterns = [
            "ruling", "halal", "haram", "allowed", "forbidden", "permissible",
            "حكم", "أحكام", "حلال", "حرام", "جائز", "محرم",
            "فتوى", "فقه", "شرعي",
        ]
        if any(pattern in q_lower for pattern in ruling_patterns):
            return QueryIntent.RULING

        return QueryIntent.VERSE_MEANING  # Default for Quranic questions

    def _is_relevant_for_intent(self, term: str, intent: QueryIntent) -> bool:
        """Check if a term is relevant for the given intent."""
        if term not in self.mappings:
            return True  # Unknown terms are always relevant

        _, _, _, term_intents = self.mappings[term]

        # None means relevant to all intents
        if term_intents is None:
            return True

        return intent.value in term_intents

    def expand(self, query: str, intent: Optional[QueryIntent] = None) -> ExpandedQuery:
        """
        Expand a query with related Islamic terms.

        Args:
            query: Original user query
            intent: Optional intent (auto-classified if not provided)

        Returns:
            ExpandedQuery with capped expansion terms
        """
        original = query
        query_lower = query.lower()

        # Classify intent if not provided
        if intent is None:
            intent = self.classify_intent(query)

        # Multi-concept detection
        is_multi_concept, detected_concepts, connection_info = self.detect_multi_concept(query)

        # Cross-language expansion
        cross_language_terms = self.expand_cross_language(query)

        # Extract words
        words = query_lower.split()

        expanded_terms = set()
        arabic_terms = set()
        expansions_applied = []

        # If multi-concept query with story connection, add thematic terms
        if is_multi_concept and connection_info:
            for theme in connection_info.get("themes", [])[:2]:  # Add up to 2 themes
                if theme in self.mappings:
                    arabic, _, _, _ = self.mappings[theme]
                    expanded_terms.add(theme)
                    arabic_terms.add(arabic)
                    expansions_applied.append(f"theme:{theme}")

            # Add Arabic pair from connection
            ar1, ar2 = connection_info.get("arabic_pair", ("", ""))
            if ar1:
                arabic_terms.add(ar1)
            if ar2:
                arabic_terms.add(ar2)

        # Check each word against mappings
        for word in words:
            # Clean word
            clean_word = re.sub(r'[^\w\u0600-\u06FF]', '', word)

            # Check if word is in reverse index
            if clean_word in self.reverse_index:
                canonical = self.reverse_index[clean_word]

                # Check if relevant for intent
                if not self._is_relevant_for_intent(canonical, intent):
                    continue

                if canonical in self.mappings:
                    arabic, translits, synonyms, _ = self.mappings[canonical]

                    # Add only the most relevant expansions
                    if len(expanded_terms) < MAX_EXPANSIONS:
                        expanded_terms.add(canonical)

                        # Add first transliteration only
                        if translits and len(expanded_terms) < MAX_EXPANSIONS:
                            expanded_terms.add(translits[0])

                        # Add first synonym only
                        if synonyms and len(expanded_terms) < MAX_EXPANSIONS:
                            expanded_terms.add(synonyms[0])

                    # Add Arabic term (limited)
                    if len(arabic_terms) < MAX_ARABIC_TERMS:
                        arabic_terms.add(arabic)

                    expansions_applied.append(f"{clean_word} -> {canonical}")

            # Check multi-word phrases
            for phrase, (arabic, translits, synonyms, term_intents) in self.mappings.items():
                if phrase in query_lower and len(phrase.split()) > 1:
                    # Check intent relevance
                    if term_intents is not None and intent.value not in term_intents:
                        continue

                    if len(expanded_terms) < MAX_EXPANSIONS:
                        expanded_terms.add(phrase)
                    if len(arabic_terms) < MAX_ARABIC_TERMS:
                        arabic_terms.add(arabic)
                    expansions_applied.append(f"{phrase} expanded")

        # Build combined query
        combined_parts = [original]

        # Add significant expanded terms (avoid duplicates)
        terms_added = 0
        for term in expanded_terms:
            if term.lower() not in query_lower and terms_added < MAX_EXPANSIONS:
                combined_parts.append(term)
                terms_added += 1

        # Add Arabic terms
        arabic_added = 0
        for arabic in arabic_terms:
            if arabic not in query and arabic_added < MAX_ARABIC_TERMS:
                combined_parts.append(arabic)
                arabic_added += 1

        combined = " ".join(combined_parts)

        # Enforce max length
        if len(combined) > MAX_COMBINED_LENGTH:
            combined = combined[:MAX_COMBINED_LENGTH].rsplit(' ', 1)[0]

        return ExpandedQuery(
            original=original,
            expanded_terms=list(expanded_terms)[:MAX_EXPANSIONS],
            arabic_terms=list(arabic_terms)[:MAX_ARABIC_TERMS],
            combined=combined,
            expansion_applied=expansions_applied,
            intent=intent,
            detected_concepts=detected_concepts,
            is_multi_concept=is_multi_concept,
            cross_language_terms=cross_language_terms,
        )

    def get_all_variants(self, term: str) -> Set[str]:
        """Get all variants of a term (Arabic, transliterations, synonyms)."""
        variants = set()
        term_lower = term.lower()

        # Check if term is a key
        if term_lower in self.mappings:
            arabic, translits, synonyms, _ = self.mappings[term_lower]
            variants.add(term_lower)
            variants.add(arabic)
            variants.update(t.lower() for t in translits)
            variants.update(s.lower() for s in synonyms)

        # Check reverse index
        elif term_lower in self.reverse_index:
            canonical = self.reverse_index[term_lower]
            return self.get_all_variants(canonical)

        return variants


# Global instance
query_expander = QueryExpander()


def expand_query(query: str, intent: Optional[QueryIntent] = None) -> ExpandedQuery:
    """Convenience function to expand a query."""
    return query_expander.expand(query, intent)


# Golden test cases for regression testing
GOLDEN_TESTS = [
    {
        "query": "What is the story of Moses?",
        "expected_intent": QueryIntent.STORY_EXPLORATION,
        "expected_terms": ["moses", "musa"],
        "max_expansions": MAX_EXPANSIONS,
    },
    {
        "query": "Is eating pork halal?",
        "expected_intent": QueryIntent.RULING,
        "expected_terms": ["halal"],
        "max_expansions": MAX_EXPANSIONS,
    },
    {
        "query": "Explain the meaning of sabr",
        "expected_intent": QueryIntent.VERSE_MEANING,
        "expected_terms": ["patience", "sabr"],
        "max_expansions": MAX_EXPANSIONS,
    },
    {
        "query": "What is the root of the word taqwa?",
        "expected_intent": QueryIntent.LINGUISTIC,
        "expected_terms": ["taqwa"],
        "max_expansions": MAX_EXPANSIONS,
    },
    {
        "query": "Theme of mercy in Quran",
        "expected_intent": QueryIntent.THEME_SEARCH,
        "expected_terms": ["mercy"],
        "max_expansions": MAX_EXPANSIONS,
    },
]

# Multi-concept test cases
MULTI_CONCEPT_TESTS = [
    {
        "query": "Solomon and Queen of Sheba",
        "expected_multi": True,
        "expected_concepts": ["solomon"],
    },
    {
        "query": "Moses + Pharaoh story",
        "expected_multi": True,
        "expected_concepts": ["moses", "pharaoh"],
    },
    {
        "query": "Abraham and Ishmael",
        "expected_multi": True,
        "expected_concepts": ["abraham", "ishmael"],
    },
    {
        "query": "قصة موسى وفرعون",  # Arabic: Story of Moses and Pharaoh
        "expected_multi": True,
        "expected_concepts": ["moses", "pharaoh"],
    },
]


def run_multi_concept_tests() -> list[dict]:
    """Run multi-concept detection tests."""
    results = []
    expander = QueryExpander()

    for test in MULTI_CONCEPT_TESTS:
        query = test["query"]
        expected_multi = test["expected_multi"]
        expected_concepts = test.get("expected_concepts", [])

        is_multi, concepts, connection = expander.detect_multi_concept(query)

        passed = is_multi == expected_multi
        if expected_concepts:
            passed = passed and all(c in concepts for c in expected_concepts)

        results.append({
            "query": query,
            "is_multi_concept": is_multi,
            "expected_multi": expected_multi,
            "detected_concepts": concepts,
            "expected_concepts": expected_concepts,
            "has_connection": connection is not None,
            "passed": passed,
        })

    return results


def run_golden_tests() -> list[dict]:
    """Run golden tests and return results."""
    results = []

    for test in GOLDEN_TESTS:
        query = test["query"]
        expected_intent = test["expected_intent"]
        expected_terms = test["expected_terms"]
        max_exp = test["max_expansions"]

        result = expand_query(query)

        # Check intent
        intent_match = result.intent == expected_intent

        # Check terms found
        all_terms = result.expanded_terms + result.arabic_terms + [result.original]
        all_terms_lower = [t.lower() for t in all_terms]
        terms_found = all(any(exp.lower() in t for t in all_terms_lower) for exp in expected_terms)

        # Check expansion cap
        under_cap = len(result.expanded_terms) <= max_exp

        results.append({
            "query": query,
            "intent_match": intent_match,
            "expected_intent": expected_intent.value,
            "actual_intent": result.intent.value,
            "terms_found": terms_found,
            "expected_terms": expected_terms,
            "actual_terms": result.expanded_terms,
            "under_cap": under_cap,
            "expansion_count": len(result.expanded_terms),
            "passed": intent_match and terms_found and under_cap,
        })

    return results
