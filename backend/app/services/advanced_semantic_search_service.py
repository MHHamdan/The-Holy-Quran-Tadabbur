"""
Advanced Semantic Search Service

Provides deep semantic understanding of Quranic content using:
- AraBERT-style embeddings for Arabic text understanding
- TF-IDF scoring for lexical similarity
- Semantic embeddings for context-based searches
- 15+ important Quranic themes with synonyms and expansions
- Cross-language expansions (Arabic/English)
- Multiple similarity metrics (Cosine, Jaccard, BM25)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import math
import re
from collections import Counter
from datetime import datetime


class SimilarityMetric(Enum):
    """Available similarity metrics"""
    COSINE = "cosine"
    JACCARD = "jaccard"
    BM25 = "bm25"
    COMBINED = "combined"


class SearchMode(Enum):
    """Search modes available"""
    LEXICAL = "lexical"  # TF-IDF based
    SEMANTIC = "semantic"  # Embedding based
    HYBRID = "hybrid"  # Combined approach


@dataclass
class SemanticVector:
    """Represents a semantic embedding vector"""
    dimensions: Dict[str, float]
    magnitude: float = 0.0

    def __post_init__(self):
        if self.dimensions:
            self.magnitude = math.sqrt(sum(v ** 2 for v in self.dimensions.values()))


@dataclass
class ThemeExpansion:
    """Represents a Quranic theme with semantic expansions"""
    theme_id: str
    name_english: str
    name_arabic: str
    primary_terms_arabic: List[str]
    primary_terms_english: List[str]
    related_concepts: List[str]
    root_words: List[str]  # Arabic root words
    synonyms_arabic: List[str]
    synonyms_english: List[str]
    antonyms: List[str]
    related_themes: List[str]
    sample_verses: List[Dict[str, Any]]
    embedding: Optional[SemanticVector] = None


@dataclass
class SearchResult:
    """Represents a search result with relevance scores"""
    verse_id: str
    surah: int
    ayah: int
    text_arabic: str
    text_english: str
    lexical_score: float
    semantic_score: float
    combined_score: float
    matched_themes: List[str]
    matched_terms: List[str]
    highlight_positions: List[Tuple[int, int]]


@dataclass
class TFIDFIndex:
    """TF-IDF index for lexical search"""
    term_frequencies: Dict[str, Dict[str, float]]  # term -> {doc_id: tf}
    document_frequencies: Dict[str, int]  # term -> df
    inverse_document_frequencies: Dict[str, float]  # term -> idf
    document_lengths: Dict[str, int]  # doc_id -> length
    avg_document_length: float
    total_documents: int


class AdvancedSemanticSearchService:
    """
    Advanced semantic search service for Quranic content.
    Combines AraBERT-style embeddings with TF-IDF for hybrid search.
    """

    def __init__(self):
        self.themes: Dict[str, ThemeExpansion] = {}
        self.verse_embeddings: Dict[str, SemanticVector] = {}
        self.tfidf_index: Optional[TFIDFIndex] = None
        self.verses: Dict[str, Dict[str, Any]] = {}
        self.arabic_roots: Dict[str, List[str]] = {}  # root -> derived words
        self._initialize_quranic_themes()
        self._initialize_arabic_roots()
        self._initialize_sample_verses()
        self._build_tfidf_index()

    def _initialize_quranic_themes(self):
        """Initialize 15+ important Quranic themes with expansions"""
        themes_data = [
            # 1. Mercy (الرحمة)
            ThemeExpansion(
                theme_id="mercy",
                name_english="Mercy",
                name_arabic="الرحمة",
                primary_terms_arabic=["رحمة", "رحيم", "رحمن", "رحماء"],
                primary_terms_english=["mercy", "merciful", "compassion", "compassionate"],
                related_concepts=["forgiveness", "kindness", "grace", "blessing"],
                root_words=["ر-ح-م"],
                synonyms_arabic=["عفو", "غفران", "لطف", "رأفة", "حنان"],
                synonyms_english=["clemency", "leniency", "benevolence", "tenderness"],
                antonyms=["punishment", "wrath", "severity"],
                related_themes=["forgiveness", "love", "patience"],
                sample_verses=[
                    {"surah": 1, "ayah": 1},
                    {"surah": 6, "ayah": 54},
                    {"surah": 21, "ayah": 107}
                ]
            ),
            # 2. Justice (العدل)
            ThemeExpansion(
                theme_id="justice",
                name_english="Justice",
                name_arabic="العدل",
                primary_terms_arabic=["عدل", "قسط", "ميزان", "حق"],
                primary_terms_english=["justice", "equity", "fairness", "balance"],
                related_concepts=["equality", "rights", "judgment", "truth"],
                root_words=["ع-د-ل", "ق-س-ط"],
                synonyms_arabic=["إنصاف", "مساواة", "حكم"],
                synonyms_english=["righteousness", "impartiality", "integrity"],
                antonyms=["oppression", "injustice", "tyranny"],
                related_themes=["truth", "judgment", "rights"],
                sample_verses=[
                    {"surah": 4, "ayah": 135},
                    {"surah": 16, "ayah": 90},
                    {"surah": 5, "ayah": 8}
                ]
            ),
            # 3. Patience (الصبر)
            ThemeExpansion(
                theme_id="patience",
                name_english="Patience",
                name_arabic="الصبر",
                primary_terms_arabic=["صبر", "صابر", "صبور", "صابرين"],
                primary_terms_english=["patience", "patient", "perseverance", "steadfastness"],
                related_concepts=["endurance", "resilience", "fortitude", "constancy"],
                root_words=["ص-ب-ر"],
                synonyms_arabic=["تحمل", "جلد", "ثبات", "احتمال"],
                synonyms_english=["forbearance", "tolerance", "composure", "persistence"],
                antonyms=["impatience", "hastiness", "despair"],
                related_themes=["trust", "trials", "reward"],
                sample_verses=[
                    {"surah": 2, "ayah": 153},
                    {"surah": 3, "ayah": 200},
                    {"surah": 39, "ayah": 10}
                ]
            ),
            # 4. Gratitude (الشكر)
            ThemeExpansion(
                theme_id="gratitude",
                name_english="Gratitude",
                name_arabic="الشكر",
                primary_terms_arabic=["شكر", "شاكر", "شكور", "حمد"],
                primary_terms_english=["gratitude", "thankfulness", "appreciation", "praise"],
                related_concepts=["blessing", "recognition", "acknowledgment"],
                root_words=["ش-ك-ر", "ح-م-د"],
                synonyms_arabic=["امتنان", "تقدير", "ثناء"],
                synonyms_english=["gratefulness", "recognition", "thanksgiving"],
                antonyms=["ingratitude", "ungratefulness", "denial"],
                related_themes=["blessings", "worship", "remembrance"],
                sample_verses=[
                    {"surah": 14, "ayah": 7},
                    {"surah": 31, "ayah": 12},
                    {"surah": 2, "ayah": 152}
                ]
            ),
            # 5. Forgiveness (المغفرة)
            ThemeExpansion(
                theme_id="forgiveness",
                name_english="Forgiveness",
                name_arabic="المغفرة",
                primary_terms_arabic=["غفر", "غفور", "مغفرة", "عفو", "توبة"],
                primary_terms_english=["forgiveness", "pardon", "absolution", "repentance"],
                related_concepts=["mercy", "redemption", "atonement"],
                root_words=["غ-ف-ر", "ع-ف-و", "ت-و-ب"],
                synonyms_arabic=["صفح", "تجاوز", "إعفاء"],
                synonyms_english=["clemency", "remission", "amnesty"],
                antonyms=["punishment", "vengeance", "retribution"],
                related_themes=["mercy", "repentance", "salvation"],
                sample_verses=[
                    {"surah": 39, "ayah": 53},
                    {"surah": 4, "ayah": 110},
                    {"surah": 3, "ayah": 135}
                ]
            ),
            # 6. Trust in Allah (التوكل)
            ThemeExpansion(
                theme_id="tawakkul",
                name_english="Trust in Allah",
                name_arabic="التوكل",
                primary_terms_arabic=["توكل", "وكيل", "متوكل", "اعتماد"],
                primary_terms_english=["trust", "reliance", "dependence", "confidence"],
                related_concepts=["faith", "submission", "certainty"],
                root_words=["و-ك-ل"],
                synonyms_arabic=["اتكال", "ثقة", "إيمان"],
                synonyms_english=["reliance", "faith", "assurance"],
                antonyms=["doubt", "despair", "self-reliance"],
                related_themes=["faith", "patience", "certainty"],
                sample_verses=[
                    {"surah": 3, "ayah": 159},
                    {"surah": 65, "ayah": 3},
                    {"surah": 8, "ayah": 2}
                ]
            ),
            # 7. Guidance (الهداية)
            ThemeExpansion(
                theme_id="guidance",
                name_english="Guidance",
                name_arabic="الهداية",
                primary_terms_arabic=["هدى", "هداية", "هادي", "مهتدي", "صراط"],
                primary_terms_english=["guidance", "guide", "path", "direction"],
                related_concepts=["truth", "light", "straight path", "righteousness"],
                root_words=["ه-د-ي"],
                synonyms_arabic=["إرشاد", "توجيه", "دلالة", "نور"],
                synonyms_english=["direction", "instruction", "enlightenment"],
                antonyms=["misguidance", "error", "deviation"],
                related_themes=["truth", "light", "knowledge"],
                sample_verses=[
                    {"surah": 1, "ayah": 6},
                    {"surah": 2, "ayah": 2},
                    {"surah": 6, "ayah": 125}
                ]
            ),
            # 8. Fear of Allah (التقوى)
            ThemeExpansion(
                theme_id="taqwa",
                name_english="God-consciousness",
                name_arabic="التقوى",
                primary_terms_arabic=["تقوى", "متقي", "اتقوا", "خشية"],
                primary_terms_english=["piety", "god-consciousness", "righteousness", "fear of Allah"],
                related_concepts=["awareness", "mindfulness", "obedience"],
                root_words=["و-ق-ي", "خ-ش-ي"],
                synonyms_arabic=["ورع", "خوف", "إيمان"],
                synonyms_english=["devoutness", "reverence", "godliness"],
                antonyms=["heedlessness", "disobedience", "sinfulness"],
                related_themes=["faith", "obedience", "righteousness"],
                sample_verses=[
                    {"surah": 2, "ayah": 197},
                    {"surah": 49, "ayah": 13},
                    {"surah": 3, "ayah": 102}
                ]
            ),
            # 9. Knowledge (العلم)
            ThemeExpansion(
                theme_id="knowledge",
                name_english="Knowledge",
                name_arabic="العلم",
                primary_terms_arabic=["علم", "عالم", "علماء", "معرفة", "فقه"],
                primary_terms_english=["knowledge", "wisdom", "understanding", "learning"],
                related_concepts=["wisdom", "insight", "comprehension", "study"],
                root_words=["ع-ل-م", "ف-ق-ه"],
                synonyms_arabic=["حكمة", "فهم", "إدراك", "بصيرة"],
                synonyms_english=["enlightenment", "awareness", "scholarship"],
                antonyms=["ignorance", "foolishness", "unawareness"],
                related_themes=["wisdom", "guidance", "truth"],
                sample_verses=[
                    {"surah": 96, "ayah": 1},
                    {"surah": 58, "ayah": 11},
                    {"surah": 20, "ayah": 114}
                ]
            ),
            # 10. Unity (الوحدة)
            ThemeExpansion(
                theme_id="unity",
                name_english="Unity",
                name_arabic="الوحدة",
                primary_terms_arabic=["وحدة", "جماعة", "أخوة", "اعتصموا"],
                primary_terms_english=["unity", "brotherhood", "community", "togetherness"],
                related_concepts=["harmony", "solidarity", "cooperation"],
                root_words=["و-ح-د", "أ-خ-و"],
                synonyms_arabic=["اتحاد", "تضامن", "تعاون"],
                synonyms_english=["solidarity", "cohesion", "fellowship"],
                antonyms=["division", "discord", "separation"],
                related_themes=["brotherhood", "community", "cooperation"],
                sample_verses=[
                    {"surah": 3, "ayah": 103},
                    {"surah": 49, "ayah": 10},
                    {"surah": 8, "ayah": 46}
                ]
            ),
            # 11. Charity (الصدقة)
            ThemeExpansion(
                theme_id="charity",
                name_english="Charity",
                name_arabic="الصدقة",
                primary_terms_arabic=["صدقة", "زكاة", "إنفاق", "إحسان"],
                primary_terms_english=["charity", "alms", "giving", "generosity"],
                related_concepts=["generosity", "kindness", "purification"],
                root_words=["ص-د-ق", "ز-ك-و", "ن-ف-ق"],
                synonyms_arabic=["عطاء", "بذل", "كرم", "جود"],
                synonyms_english=["donation", "philanthropy", "benevolence"],
                antonyms=["greed", "miserliness", "hoarding"],
                related_themes=["generosity", "purification", "social responsibility"],
                sample_verses=[
                    {"surah": 2, "ayah": 261},
                    {"surah": 9, "ayah": 103},
                    {"surah": 2, "ayah": 274}
                ]
            ),
            # 12. Truth (الحق)
            ThemeExpansion(
                theme_id="truth",
                name_english="Truth",
                name_arabic="الحق",
                primary_terms_arabic=["حق", "صدق", "صادق", "يقين"],
                primary_terms_english=["truth", "truthfulness", "certainty", "reality"],
                related_concepts=["honesty", "sincerity", "authenticity"],
                root_words=["ح-ق-ق", "ص-د-ق"],
                synonyms_arabic=["واقع", "حقيقة", "صحيح"],
                synonyms_english=["veracity", "factual", "genuine"],
                antonyms=["falsehood", "lies", "deception"],
                related_themes=["justice", "honesty", "guidance"],
                sample_verses=[
                    {"surah": 17, "ayah": 81},
                    {"surah": 2, "ayah": 147},
                    {"surah": 10, "ayah": 32}
                ]
            ),
            # 13. Remembrance (الذكر)
            ThemeExpansion(
                theme_id="remembrance",
                name_english="Remembrance",
                name_arabic="الذكر",
                primary_terms_arabic=["ذكر", "تذكر", "ذاكرين", "تسبيح"],
                primary_terms_english=["remembrance", "mention", "mindfulness", "glorification"],
                related_concepts=["worship", "contemplation", "awareness"],
                root_words=["ذ-ك-ر", "س-ب-ح"],
                synonyms_arabic=["تدبر", "تفكر", "عبادة"],
                synonyms_english=["recollection", "meditation", "reflection"],
                antonyms=["forgetfulness", "heedlessness", "negligence"],
                related_themes=["worship", "prayer", "gratitude"],
                sample_verses=[
                    {"surah": 13, "ayah": 28},
                    {"surah": 2, "ayah": 152},
                    {"surah": 33, "ayah": 41}
                ]
            ),
            # 14. Trials (الابتلاء)
            ThemeExpansion(
                theme_id="trials",
                name_english="Trials",
                name_arabic="الابتلاء",
                primary_terms_arabic=["ابتلاء", "فتنة", "امتحان", "بلاء"],
                primary_terms_english=["trials", "tests", "tribulations", "afflictions"],
                related_concepts=["patience", "perseverance", "growth"],
                root_words=["ب-ل-و", "ف-ت-ن"],
                synonyms_arabic=["اختبار", "محنة", "شدة"],
                synonyms_english=["hardship", "difficulty", "challenge"],
                antonyms=["ease", "comfort", "prosperity"],
                related_themes=["patience", "trust", "reward"],
                sample_verses=[
                    {"surah": 2, "ayah": 155},
                    {"surah": 29, "ayah": 2},
                    {"surah": 67, "ayah": 2}
                ]
            ),
            # 15. Tawhid (التوحيد)
            ThemeExpansion(
                theme_id="tawhid",
                name_english="Monotheism",
                name_arabic="التوحيد",
                primary_terms_arabic=["توحيد", "واحد", "أحد", "لا إله إلا الله"],
                primary_terms_english=["monotheism", "oneness", "unity of God", "tawhid"],
                related_concepts=["worship", "devotion", "submission"],
                root_words=["و-ح-د", "أ-ل-ه"],
                synonyms_arabic=["وحدانية", "إفراد", "إخلاص"],
                synonyms_english=["oneness", "uniqueness", "singularity"],
                antonyms=["shirk", "polytheism", "idolatry"],
                related_themes=["worship", "faith", "submission"],
                sample_verses=[
                    {"surah": 112, "ayah": 1},
                    {"surah": 2, "ayah": 163},
                    {"surah": 21, "ayah": 25}
                ]
            ),
            # 16. Prayer (الصلاة)
            ThemeExpansion(
                theme_id="prayer",
                name_english="Prayer",
                name_arabic="الصلاة",
                primary_terms_arabic=["صلاة", "مصلي", "سجود", "ركوع", "قيام"],
                primary_terms_english=["prayer", "worship", "prostration", "devotion"],
                related_concepts=["worship", "connection", "supplication"],
                root_words=["ص-ل-و", "س-ج-د", "ر-ك-ع"],
                synonyms_arabic=["عبادة", "دعاء", "تضرع"],
                synonyms_english=["salat", "devotion", "supplication"],
                antonyms=["negligence", "abandonment"],
                related_themes=["worship", "remembrance", "taqwa"],
                sample_verses=[
                    {"surah": 2, "ayah": 43},
                    {"surah": 29, "ayah": 45},
                    {"surah": 20, "ayah": 14}
                ]
            ),
            # 17. Repentance (التوبة)
            ThemeExpansion(
                theme_id="repentance",
                name_english="Repentance",
                name_arabic="التوبة",
                primary_terms_arabic=["توبة", "تائب", "استغفار", "إنابة"],
                primary_terms_english=["repentance", "return", "seeking forgiveness", "turning back"],
                related_concepts=["forgiveness", "mercy", "redemption"],
                root_words=["ت-و-ب", "غ-ف-ر", "ن-و-ب"],
                synonyms_arabic=["رجوع", "إقلاع", "ندم"],
                synonyms_english=["remorse", "contrition", "penitence"],
                antonyms=["persistence in sin", "stubbornness"],
                related_themes=["forgiveness", "mercy", "salvation"],
                sample_verses=[
                    {"surah": 66, "ayah": 8},
                    {"surah": 4, "ayah": 17},
                    {"surah": 25, "ayah": 70}
                ]
            ),
            # 18. Paradise (الجنة)
            ThemeExpansion(
                theme_id="paradise",
                name_english="Paradise",
                name_arabic="الجنة",
                primary_terms_arabic=["جنة", "فردوس", "نعيم", "جنات"],
                primary_terms_english=["paradise", "garden", "heaven", "bliss"],
                related_concepts=["reward", "eternal life", "blessing"],
                root_words=["ج-ن-ن", "ف-ر-د-س"],
                synonyms_arabic=["دار السلام", "دار الخلد", "نعيم"],
                synonyms_english=["heaven", "garden of Eden", "eternal abode"],
                antonyms=["hellfire", "punishment"],
                related_themes=["reward", "afterlife", "righteousness"],
                sample_verses=[
                    {"surah": 3, "ayah": 133},
                    {"surah": 55, "ayah": 46},
                    {"surah": 9, "ayah": 72}
                ]
            ),
        ]

        for theme in themes_data:
            # Generate embedding for theme
            theme.embedding = self._generate_theme_embedding(theme)
            self.themes[theme.theme_id] = theme

    def _initialize_arabic_roots(self):
        """Initialize Arabic root word dictionary for morphological analysis"""
        self.arabic_roots = {
            "ر-ح-م": ["رحمة", "رحيم", "رحمن", "رحماء", "يرحم", "ارحم", "مرحوم"],
            "ع-د-ل": ["عدل", "عادل", "يعدل", "معدول", "عدالة"],
            "ص-ب-ر": ["صبر", "صابر", "صبور", "صابرين", "يصبر", "اصبر"],
            "ش-ك-ر": ["شكر", "شاكر", "شكور", "يشكر", "اشكر", "شاكرين"],
            "غ-ف-ر": ["غفر", "غفور", "غفار", "مغفرة", "يغفر", "استغفر"],
            "ت-و-ب": ["توبة", "تائب", "يتوب", "توبوا", "تواب"],
            "و-ك-ل": ["توكل", "وكيل", "متوكل", "يتوكل", "توكلوا"],
            "ه-د-ي": ["هدى", "هداية", "هادي", "مهتدي", "يهدي", "اهدنا"],
            "و-ق-ي": ["تقوى", "متقي", "اتقوا", "يتقي", "متقين"],
            "ع-ل-م": ["علم", "عالم", "علماء", "يعلم", "معلوم", "علمنا"],
            "ذ-ك-ر": ["ذكر", "ذاكر", "تذكر", "يذكر", "ذاكرين", "اذكر"],
            "ص-ل-و": ["صلاة", "مصلي", "يصلي", "صلوا", "مصلين"],
            "س-ج-د": ["سجود", "ساجد", "يسجد", "اسجدوا", "ساجدين"],
            "ح-ق-ق": ["حق", "حقيقة", "حقا", "محق", "يحق"],
            "ص-د-ق": ["صدق", "صادق", "صدقة", "يصدق", "صديق"],
            "ن-ف-ق": ["إنفاق", "منفق", "ينفق", "أنفقوا", "منفقين"],
            "ب-ل-و": ["ابتلاء", "بلاء", "يبتلي", "ابتليناهم", "مبتلى"],
        }

    def _initialize_sample_verses(self):
        """Index a small set of verse references by theme.

        Only references and theme tags live here. Verse text is never written
        into code: routes hydrate ``text_arabic`` from ``quran_verses`` (and
        ``text_english`` from the default English edition) with
        :func:`hydrate_canonical_text`.
        """
        sample_verses = [
            {
                "id": "1:1",
                "surah": 1,
                "ayah": 1,
                "themes": ["mercy", "tawhid"]
            },
            {
                "id": "1:6",
                "surah": 1,
                "ayah": 6,
                "themes": ["guidance"]
            },
            {
                "id": "2:153",
                "surah": 2,
                "ayah": 153,
                "themes": ["patience", "prayer"]
            },
            {
                "id": "2:155",
                "surah": 2,
                "ayah": 155,
                "themes": ["trials", "patience"]
            },
            {
                "id": "3:103",
                "surah": 3,
                "ayah": 103,
                "themes": ["unity"]
            },
            {
                "id": "4:135",
                "surah": 4,
                "ayah": 135,
                "themes": ["justice"]
            },
            {
                "id": "13:28",
                "surah": 13,
                "ayah": 28,
                "themes": ["remembrance"]
            },
            {
                "id": "14:7",
                "surah": 14,
                "ayah": 7,
                "themes": ["gratitude"]
            },
            {
                "id": "39:53",
                "surah": 39,
                "ayah": 53,
                "themes": ["mercy", "forgiveness", "repentance"]
            },
            {
                "id": "65:3",
                "surah": 65,
                "ayah": 3,
                "themes": ["tawakkul"]
            },
            {
                "id": "112:1",
                "surah": 112,
                "ayah": 1,
                "themes": ["tawhid"]
            },
            {
                "id": "96:1",
                "surah": 96,
                "ayah": 1,
                "themes": ["knowledge"]
            },
        ]

        for verse in sample_verses:
            self.verses[verse["id"]] = verse
            # Generate embedding for verse
            self.verse_embeddings[verse["id"]] = self._generate_verse_embedding(verse)

    def _generate_theme_embedding(self, theme: ThemeExpansion) -> SemanticVector:
        """Generate semantic embedding for a theme (AraBERT-style simulation)"""
        dimensions = {}

        # Primary terms contribute most
        for term in theme.primary_terms_arabic + theme.primary_terms_english:
            dimensions[term.lower()] = 1.0

        # Synonyms contribute less
        for term in theme.synonyms_arabic + theme.synonyms_english:
            dimensions[term.lower()] = 0.7

        # Related concepts
        for concept in theme.related_concepts:
            dimensions[concept.lower()] = 0.5

        # Related themes
        for related in theme.related_themes:
            dimensions[related.lower()] = 0.3

        return SemanticVector(dimensions=dimensions)

    def _generate_verse_embedding(self, verse: Dict[str, Any]) -> SemanticVector:
        """Generate semantic embedding for a verse"""
        dimensions = {}

        # Tokenize and process Arabic text
        arabic_tokens = self._tokenize_arabic(verse.get("text_arabic", ""))
        for token in arabic_tokens:
            dimensions[token] = dimensions.get(token, 0) + 1.0

        # Process English text
        english_tokens = self._tokenize_english(verse.get("text_english", ""))
        for token in english_tokens:
            dimensions[token] = dimensions.get(token, 0) + 0.8

        # Add theme dimensions
        for theme_id in verse.get("themes", []):
            if theme_id in self.themes:
                theme = self.themes[theme_id]
                for term in theme.primary_terms_arabic + theme.primary_terms_english:
                    dimensions[term.lower()] = dimensions.get(term.lower(), 0) + 0.5

        return SemanticVector(dimensions=dimensions)

    def _tokenize_arabic(self, text: str) -> List[str]:
        """Tokenize Arabic text"""
        # Remove diacritics for matching
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        # Split on whitespace and punctuation
        tokens = re.findall(r'[\u0600-\u06FF]+', text)
        return [t.lower() for t in tokens if len(t) > 1]

    def _tokenize_english(self, text: str) -> List[str]:
        """Tokenize English text"""
        # Convert to lowercase and split
        tokens = re.findall(r'[a-zA-Z]+', text.lower())
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'and', 'in', 'that', 'it', 'for', 'on', 'with'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _build_tfidf_index(self):
        """Build TF-IDF index for lexical search"""
        term_frequencies: Dict[str, Dict[str, float]] = {}
        document_frequencies: Dict[str, int] = {}
        document_lengths: Dict[str, int] = {}

        for verse_id, verse in self.verses.items():
            tokens = (self._tokenize_arabic(verse.get("text_arabic", "")) +
                      self._tokenize_english(verse.get("text_english", "")))

            document_lengths[verse_id] = len(tokens)
            token_counts = Counter(tokens)

            seen_terms = set()
            for token, count in token_counts.items():
                # Term frequency (normalized)
                tf = count / len(tokens) if tokens else 0
                if token not in term_frequencies:
                    term_frequencies[token] = {}
                term_frequencies[token][verse_id] = tf

                # Document frequency
                if token not in seen_terms:
                    document_frequencies[token] = document_frequencies.get(token, 0) + 1
                    seen_terms.add(token)

        # Calculate IDF
        total_docs = len(self.verses)
        inverse_document_frequencies = {}
        for term, df in document_frequencies.items():
            inverse_document_frequencies[term] = math.log((total_docs + 1) / (df + 1)) + 1

        avg_doc_length = sum(document_lengths.values()) / len(document_lengths) if document_lengths else 0

        self.tfidf_index = TFIDFIndex(
            term_frequencies=term_frequencies,
            document_frequencies=document_frequencies,
            inverse_document_frequencies=inverse_document_frequencies,
            document_lengths=document_lengths,
            avg_document_length=avg_doc_length,
            total_documents=total_docs
        )

    def _compute_cosine_similarity(self, vec1: SemanticVector, vec2: SemanticVector) -> float:
        """Compute cosine similarity between two vectors"""
        if vec1.magnitude == 0 or vec2.magnitude == 0:
            return 0.0

        dot_product = sum(
            vec1.dimensions.get(k, 0) * vec2.dimensions.get(k, 0)
            for k in set(vec1.dimensions.keys()) | set(vec2.dimensions.keys())
        )

        return dot_product / (vec1.magnitude * vec2.magnitude)

    def _compute_jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Compute Jaccard similarity between two sets"""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _compute_bm25_score(self, query_tokens: List[str], doc_id: str, k1: float = 1.5, b: float = 0.75) -> float:
        """Compute BM25 score for a document"""
        if not self.tfidf_index:
            return 0.0

        score = 0.0
        doc_length = self.tfidf_index.document_lengths.get(doc_id, 0)

        for token in query_tokens:
            if token not in self.tfidf_index.term_frequencies:
                continue

            tf = self.tfidf_index.term_frequencies[token].get(doc_id, 0)
            idf = self.tfidf_index.inverse_document_frequencies.get(token, 0)

            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / self.tfidf_index.avg_document_length))

            score += idf * (numerator / denominator) if denominator > 0 else 0

        return score

    def expand_query(self, query: str, include_arabic: bool = True, include_english: bool = True) -> Dict[str, Any]:
        """
        Expand query using semantic expansions.
        Returns expanded terms based on themes and root words.
        """
        query_lower = query.lower()
        expanded_terms = {
            "original": query,
            "arabic_expansions": [],
            "english_expansions": [],
            "related_themes": [],
            "root_expansions": []
        }

        # Check if query matches any theme
        for theme_id, theme in self.themes.items():
            # Check primary terms
            all_terms = (theme.primary_terms_arabic + theme.primary_terms_english +
                         theme.synonyms_arabic + theme.synonyms_english)

            for term in all_terms:
                if query_lower in term.lower() or term.lower() in query_lower:
                    expanded_terms["related_themes"].append({
                        "theme_id": theme_id,
                        "name_english": theme.name_english,
                        "name_arabic": theme.name_arabic
                    })

                    if include_arabic:
                        expanded_terms["arabic_expansions"].extend(theme.primary_terms_arabic)
                        expanded_terms["arabic_expansions"].extend(theme.synonyms_arabic)

                    if include_english:
                        expanded_terms["english_expansions"].extend(theme.primary_terms_english)
                        expanded_terms["english_expansions"].extend(theme.synonyms_english)
                    break

        # Check Arabic root expansions
        for root, derived_words in self.arabic_roots.items():
            for word in derived_words:
                if query_lower in word or word in query_lower:
                    expanded_terms["root_expansions"].append({
                        "root": root,
                        "derived_words": derived_words
                    })
                    if include_arabic:
                        expanded_terms["arabic_expansions"].extend(derived_words)
                    break

        # Remove duplicates
        expanded_terms["arabic_expansions"] = list(set(expanded_terms["arabic_expansions"]))
        expanded_terms["english_expansions"] = list(set(expanded_terms["english_expansions"]))

        return expanded_terms

    def semantic_search(
            self,
            query: str,
            mode: SearchMode = SearchMode.HYBRID,
            metric: SimilarityMetric = SimilarityMetric.COMBINED,
            expand_query: bool = True,
            limit: int = 10,
            min_score: float = 0.1
    ) -> Dict[str, Any]:
        """
        Perform semantic search on Quranic verses.

        Args:
            query: Search query (Arabic or English)
            mode: Search mode (lexical, semantic, or hybrid)
            metric: Similarity metric to use
            expand_query: Whether to expand query using themes
            limit: Maximum results to return
            min_score: Minimum score threshold

        Returns:
            Search results with relevance scores
        """
        results = []

        # Expand query if requested
        expansions = self.expand_query(query) if expand_query else {"original": query}

        # Tokenize query
        query_tokens = self._tokenize_arabic(query) + self._tokenize_english(query)

        # Add expanded terms to query tokens
        if expand_query:
            for term in expansions.get("arabic_expansions", [])[:5]:
                query_tokens.extend(self._tokenize_arabic(term))
            for term in expansions.get("english_expansions", [])[:5]:
                query_tokens.extend(self._tokenize_english(term))

        # Create query embedding
        query_embedding = SemanticVector(dimensions={t: 1.0 for t in query_tokens})

        for verse_id, verse in self.verses.items():
            lexical_score = 0.0
            semantic_score = 0.0

            # Lexical scoring (TF-IDF/BM25)
            if mode in [SearchMode.LEXICAL, SearchMode.HYBRID]:
                if metric == SimilarityMetric.BM25:
                    lexical_score = self._compute_bm25_score(query_tokens, verse_id)
                else:
                    # TF-IDF based scoring
                    for token in query_tokens:
                        if self.tfidf_index and token in self.tfidf_index.term_frequencies:
                            tf = self.tfidf_index.term_frequencies[token].get(verse_id, 0)
                            idf = self.tfidf_index.inverse_document_frequencies.get(token, 0)
                            lexical_score += tf * idf

            # Semantic scoring (embedding similarity)
            if mode in [SearchMode.SEMANTIC, SearchMode.HYBRID]:
                verse_embedding = self.verse_embeddings.get(verse_id)
                if verse_embedding:
                    if metric == SimilarityMetric.JACCARD:
                        semantic_score = self._compute_jaccard_similarity(
                            set(query_embedding.dimensions.keys()),
                            set(verse_embedding.dimensions.keys())
                        )
                    else:
                        semantic_score = self._compute_cosine_similarity(query_embedding, verse_embedding)

            # Combined score
            if mode == SearchMode.HYBRID:
                combined_score = 0.4 * lexical_score + 0.6 * semantic_score
            elif mode == SearchMode.LEXICAL:
                combined_score = lexical_score
            else:
                combined_score = semantic_score

            if combined_score >= min_score:
                # Find matched terms
                verse_tokens = set(self._tokenize_arabic(verse.get("text_arabic", "")) +
                                   self._tokenize_english(verse.get("text_english", "")))
                matched_terms = list(set(query_tokens) & verse_tokens)

                results.append({
                    "verse_id": verse_id,
                    "surah": verse["surah"],
                    "ayah": verse["ayah"],
                    "lexical_score": round(lexical_score, 4),
                    "semantic_score": round(semantic_score, 4),
                    "combined_score": round(combined_score, 4),
                    "matched_themes": verse.get("themes", []),
                    "matched_terms": matched_terms
                })

        # Sort by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "query": query,
            "mode": mode.value,
            "metric": metric.value,
            "total_results": len(results[:limit]),
            "query_expansions": expansions,
            "results": results[:limit]
        }

    def search_by_theme(self, theme_id: str, limit: int = 20) -> Dict[str, Any]:
        """Search verses by a specific theme"""
        if theme_id not in self.themes:
            return {"error": f"Theme '{theme_id}' not found"}

        theme = self.themes[theme_id]
        results = []

        for verse_id, verse in self.verses.items():
            if theme_id in verse.get("themes", []):
                results.append({
                    "verse_id": verse_id,
                    "surah": verse["surah"],
                    "ayah": verse["ayah"],
                    "themes": verse.get("themes", [])
                })

        return {
            "theme": {
                "id": theme_id,
                "name_english": theme.name_english,
                "name_arabic": theme.name_arabic,
                "related_themes": theme.related_themes
            },
            "total_results": len(results),
            "results": results[:limit],
            "sample_verses_from_theme": theme.sample_verses
        }

    def find_similar_verses(self, verse_id: str, limit: int = 5) -> Dict[str, Any]:
        """Find verses similar to a given verse"""
        if verse_id not in self.verses:
            return {"error": f"Verse '{verse_id}' not found"}

        source_verse = self.verses[verse_id]
        source_embedding = self.verse_embeddings.get(verse_id)

        if not source_embedding:
            return {"error": "No embedding found for verse"}

        similarities = []
        for other_id, other_embedding in self.verse_embeddings.items():
            if other_id != verse_id:
                similarity = self._compute_cosine_similarity(source_embedding, other_embedding)
                if similarity > 0.1:
                    similarities.append({
                        "verse_id": other_id,
                        "similarity": round(similarity, 4),
                        "verse": self.verses[other_id]
                    })

        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "source_verse": source_verse,
            "similar_verses": similarities[:limit]
        }

    def get_theme_connections(self, theme_id: str) -> Dict[str, Any]:
        """Get connections between themes"""
        if theme_id not in self.themes:
            return {"error": f"Theme '{theme_id}' not found"}

        theme = self.themes[theme_id]
        connections = []

        for related_id in theme.related_themes:
            if related_id in self.themes:
                related = self.themes[related_id]
                # Calculate semantic similarity
                if theme.embedding and related.embedding:
                    similarity = self._compute_cosine_similarity(theme.embedding, related.embedding)
                else:
                    similarity = 0.5

                connections.append({
                    "theme_id": related_id,
                    "name_english": related.name_english,
                    "name_arabic": related.name_arabic,
                    "similarity": round(similarity, 4)
                })

        return {
            "theme": {
                "id": theme_id,
                "name_english": theme.name_english,
                "name_arabic": theme.name_arabic
            },
            "connections": connections
        }

    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Get all available themes"""
        return [
            {
                "id": t.theme_id,
                "name_english": t.name_english,
                "name_arabic": t.name_arabic,
                "primary_terms_arabic": t.primary_terms_arabic,
                "primary_terms_english": t.primary_terms_english,
                "related_themes": t.related_themes,
                "verse_count": len([v for v in self.verses.values() if t.theme_id in v.get("themes", [])])
            }
            for t in self.themes.values()
        ]

    def get_theme_details(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a theme"""
        if theme_id not in self.themes:
            return None

        theme = self.themes[theme_id]
        return {
            "id": theme.theme_id,
            "name_english": theme.name_english,
            "name_arabic": theme.name_arabic,
            "primary_terms_arabic": theme.primary_terms_arabic,
            "primary_terms_english": theme.primary_terms_english,
            "synonyms_arabic": theme.synonyms_arabic,
            "synonyms_english": theme.synonyms_english,
            "related_concepts": theme.related_concepts,
            "root_words": theme.root_words,
            "antonyms": theme.antonyms,
            "related_themes": theme.related_themes,
            "sample_verses": theme.sample_verses
        }

    def get_arabic_roots(self) -> Dict[str, List[str]]:
        """Get all Arabic root words and their derivatives"""
        return self.arabic_roots

    def analyze_verse_themes(self, verse_id: str) -> Dict[str, Any]:
        """Analyze themes present in a verse"""
        if verse_id not in self.verses:
            return {"error": f"Verse '{verse_id}' not found"}

        verse = self.verses[verse_id]
        theme_analysis = []

        for theme_id in verse.get("themes", []):
            if theme_id in self.themes:
                theme = self.themes[theme_id]
                theme_analysis.append({
                    "theme_id": theme_id,
                    "name_english": theme.name_english,
                    "name_arabic": theme.name_arabic,
                    "related_concepts": theme.related_concepts,
                    "related_themes": theme.related_themes
                })

        return {
            "verse": verse,
            "theme_analysis": theme_analysis
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get search service statistics"""
        return {
            "total_themes": len(self.themes),
            "total_verses_indexed": len(self.verses),
            "total_embeddings": len(self.verse_embeddings),
            "total_arabic_roots": len(self.arabic_roots),
            "total_terms_in_index": len(self.tfidf_index.term_frequencies) if self.tfidf_index else 0,
            "search_modes": [m.value for m in SearchMode],
            "similarity_metrics": [m.value for m in SimilarityMetric],
            "themes_list": [t.name_english for t in self.themes.values()]
        }


# Create singleton instance
advanced_semantic_search_service = AdvancedSemanticSearchService()


def _collect_refs(node: Any, out: set) -> None:
    if isinstance(node, dict):
        s, a = node.get("surah"), node.get("ayah")
        if isinstance(s, int) and isinstance(a, int):
            out.add((s, a))
        for v in node.values():
            _collect_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_refs(v, out)


def _apply_texts(node: Any, texts: Dict[Tuple[int, int], Dict[str, Any]]) -> None:
    if isinstance(node, dict):
        s, a = node.get("surah"), node.get("ayah")
        if isinstance(s, int) and isinstance(a, int):
            row = texts.get((s, a))
            node["text_arabic"] = row["text_uthmani"] if row else None
            node["text_english"] = row["text_english"] if row else None
            node["translation_edition"] = row["translation_edition"] if row else None
        for v in node.values():
            _apply_texts(v, texts)
    elif isinstance(node, list):
        for v in node:
            _apply_texts(v, texts)


async def hydrate_canonical_text(payload: Any, session) -> Any:
    """Fill ``text_arabic`` / ``text_english`` for every {surah, ayah} dict in
    ``payload`` from the database, in one query.

    ``text_arabic`` is the canonical Tanzil ``text_uthmani``; ``text_english``
    is the default English edition (``translation_edition`` names it so the UI
    can attribute it). A reference that is not in the database gets None.
    """
    refs: set = set()
    _collect_refs(payload, refs)
    if not refs:
        return payload

    from sqlalchemy import select, tuple_, and_
    from app.models.quran import QuranVerse, Translation, TranslationEdition

    default_en = (await session.execute(
        select(TranslationEdition.key).where(
            TranslationEdition.language == "en", TranslationEdition.is_default.is_(True)
        )
    )).scalars().first()

    stmt = select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani, Translation.text)
    if default_en:
        stmt = stmt.outerjoin(
            Translation,
            and_(Translation.verse_id == QuranVerse.id, Translation.translator == default_en),
        )
    else:
        stmt = select(QuranVerse.sura_no, QuranVerse.aya_no, QuranVerse.text_uthmani)
    stmt = stmt.where(tuple_(QuranVerse.sura_no, QuranVerse.aya_no).in_(sorted(refs)))

    texts: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for row in (await session.execute(stmt)).all():
        en = row[3] if default_en and len(row) > 3 else None
        texts[(row[0], row[1])] = {
            "text_uthmani": row[2],
            "text_english": en,
            "translation_edition": default_en if en else None,
        }
    _apply_texts(payload, texts)
    return payload
