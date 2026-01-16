"""
Contextual Semantic Search Service with Advanced Embeddings.

Provides enhanced search capabilities:
1. Cross-sentence contextual embeddings
2. Bilingual query expansion (Arabic ↔ English)
3. Semantic similarity with contextual understanding
4. Query intent detection and optimization
5. Phrase-level and passage-level matching

Arabic: خدمة البحث الدلالي السياقي المتقدم
"""

import logging
import hashlib
import re
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class QueryIntent(str, Enum):
    """Detected query intent types."""
    VERSE_LOOKUP = "verse_lookup"           # Looking for specific verse
    THEMATIC_SEARCH = "thematic_search"     # Searching by theme
    WORD_MEANING = "word_meaning"           # Understanding word meaning
    STORY_SEARCH = "story_search"           # Looking for prophet stories
    RULING_SEARCH = "ruling_search"         # Looking for legal rulings
    COMPARISON = "comparison"               # Comparing concepts
    LIFE_GUIDANCE = "life_guidance"         # Seeking life advice
    GENERAL = "general"                     # General query


class SearchMode(str, Enum):
    """Search execution modes."""
    SEMANTIC = "semantic"           # Meaning-based search
    LEXICAL = "lexical"            # Keyword-based search
    HYBRID = "hybrid"              # Combined approach
    CONTEXTUAL = "contextual"      # Context-aware search


# Bilingual concept mappings with contextual synonyms
BILINGUAL_CONCEPTS = {
    # Core theological concepts
    "patience": {
        "ar_primary": "صبر",
        "ar_synonyms": ["صابر", "صبور", "تصبر", "اصطبار", "احتمال", "تحمل", "مصابرة", "صبرا"],
        "en_synonyms": ["endurance", "perseverance", "steadfastness", "resilience", "forbearance"],
        "context_phrases_ar": ["الصبر على البلاء", "الصبر الجميل", "اصبروا وصابروا"],
        "context_phrases_en": ["patience in adversity", "beautiful patience", "be patient"],
        "related_themes": ["trial", "trust", "reward"],
    },
    "mercy": {
        "ar_primary": "رحمة",
        "ar_synonyms": ["رحيم", "رحمن", "رأفة", "رحماء", "يرحم", "ترحم", "مرحوم"],
        "en_synonyms": ["compassion", "kindness", "grace", "clemency", "benevolence"],
        "context_phrases_ar": ["رحمة الله", "أرحم الراحمين", "رحمة للعالمين"],
        "context_phrases_en": ["mercy of Allah", "most merciful", "mercy to the worlds"],
        "related_themes": ["forgiveness", "love", "kindness"],
    },
    "guidance": {
        "ar_primary": "هداية",
        "ar_synonyms": ["هدى", "هادي", "اهتدى", "رشد", "صراط", "سبيل", "طريق"],
        "en_synonyms": ["direction", "path", "way", "leading", "enlightenment"],
        "context_phrases_ar": ["الصراط المستقيم", "اهدنا", "يهدي من يشاء"],
        "context_phrases_en": ["straight path", "guide us", "guides whom He wills"],
        "related_themes": ["faith", "truth", "light"],
    },
    "forgiveness": {
        "ar_primary": "مغفرة",
        "ar_synonyms": ["غفور", "غفار", "عفو", "غافر", "استغفار", "يغفر", "مغفرة"],
        "en_synonyms": ["pardon", "absolution", "clemency", "amnesty", "remission"],
        "context_phrases_ar": ["استغفر الله", "غفران الذنوب", "يغفر لكم"],
        "context_phrases_en": ["seek forgiveness", "forgive sins", "He forgives"],
        "related_themes": ["repentance", "mercy", "sin"],
    },
    "faith": {
        "ar_primary": "إيمان",
        "ar_synonyms": ["مؤمن", "يقين", "تصديق", "توحيد", "عقيدة", "آمن", "مؤمنون"],
        "en_synonyms": ["belief", "trust", "conviction", "creed", "certitude"],
        "context_phrases_ar": ["آمنوا بالله", "المؤمنون", "أركان الإيمان"],
        "context_phrases_en": ["believe in Allah", "the believers", "pillars of faith"],
        "related_themes": ["tawhid", "islam", "righteous"],
    },
    "prayer": {
        "ar_primary": "صلاة",
        "ar_synonyms": ["صلوات", "مصلي", "يصلي", "سجود", "ركوع", "قيام", "تهجد"],
        "en_synonyms": ["worship", "salah", "prostration", "devotion", "supplication"],
        "context_phrases_ar": ["أقيموا الصلاة", "الصلاة والسلام", "حافظوا على الصلوات"],
        "context_phrases_en": ["establish prayer", "maintain prayers", "pray on time"],
        "related_themes": ["worship", "remembrance", "connection"],
    },
    "justice": {
        "ar_primary": "عدل",
        "ar_synonyms": ["عادل", "قسط", "إنصاف", "حكم", "ميزان", "قاسط"],
        "en_synonyms": ["fairness", "equity", "righteousness", "impartiality"],
        "context_phrases_ar": ["العدل والإحسان", "الحكم بالعدل", "القسط"],
        "context_phrases_en": ["justice and kindness", "judge fairly", "equitable"],
        "related_themes": ["truth", "rights", "equality"],
    },
    "gratitude": {
        "ar_primary": "شكر",
        "ar_synonyms": ["شاكر", "شكور", "حمد", "ثناء", "نعمة", "يشكر"],
        "en_synonyms": ["thankfulness", "appreciation", "gratefulness", "acknowledgment"],
        "context_phrases_ar": ["الشكر لله", "لئن شكرتم", "الحمد لله"],
        "context_phrases_en": ["thanks to Allah", "if you are grateful", "praise to Allah"],
        "related_themes": ["blessing", "contentment", "worship"],
    },
    "trial": {
        "ar_primary": "ابتلاء",
        "ar_synonyms": ["فتنة", "امتحان", "اختبار", "محنة", "بلاء", "مصيبة"],
        "en_synonyms": ["test", "tribulation", "hardship", "affliction", "challenge"],
        "context_phrases_ar": ["نبلوكم بالخير والشر", "الابتلاء بالنعم", "الصبر على المحن"],
        "context_phrases_en": ["test you with good and evil", "trials of life", "patience in hardship"],
        "related_themes": ["patience", "faith", "reward"],
    },
    "repentance": {
        "ar_primary": "توبة",
        "ar_synonyms": ["تائب", "تاب", "إنابة", "استغفار", "رجوع", "أناب"],
        "en_synonyms": ["return", "remorse", "contrition", "penitence", "atonement"],
        "context_phrases_ar": ["تابوا إلى الله", "التوبة النصوح", "باب التوبة"],
        "context_phrases_en": ["repent to Allah", "sincere repentance", "door of repentance"],
        "related_themes": ["forgiveness", "sin", "change"],
    },
    "paradise": {
        "ar_primary": "جنة",
        "ar_synonyms": ["فردوس", "نعيم", "خلد", "رضوان", "جنات", "دار السلام"],
        "en_synonyms": ["heaven", "garden", "bliss", "eternal abode", "reward"],
        "context_phrases_ar": ["جنات النعيم", "جنات تجري من تحتها الأنهار", "دار الخلد"],
        "context_phrases_en": ["gardens of bliss", "gardens beneath which rivers flow", "eternal home"],
        "related_themes": ["reward", "afterlife", "righteousness"],
    },
    "hellfire": {
        "ar_primary": "نار",
        "ar_synonyms": ["جهنم", "سعير", "جحيم", "حميم", "سقر", "لظى"],
        "en_synonyms": ["fire", "hell", "punishment", "torment", "inferno"],
        "context_phrases_ar": ["نار جهنم", "عذاب النار", "أصحاب النار"],
        "context_phrases_en": ["fire of hell", "punishment of fire", "companions of fire"],
        "related_themes": ["punishment", "warning", "disbelief"],
    },
}

# Prophet story keywords for intent detection
PROPHET_KEYWORDS = {
    "إبراهيم": ["ibrahim", "abraham", "khalil", "خليل"],
    "موسى": ["musa", "moses", "كليم"],
    "عيسى": ["isa", "jesus", "مسيح"],
    "يوسف": ["yusuf", "joseph"],
    "نوح": ["nuh", "noah"],
    "داود": ["dawud", "david"],
    "سليمان": ["sulayman", "solomon"],
    "أيوب": ["ayyub", "job"],
    "يعقوب": ["yaqub", "jacob"],
    "محمد": ["muhammad", "ahmad", "نبي", "رسول"],
}

# Intent detection patterns
INTENT_PATTERNS = {
    QueryIntent.VERSE_LOOKUP: [
        r"\d+:\d+",  # Verse reference like 2:255
        r"آية", r"verse", r"ayah",
        r"سورة .+", r"surah .+",
    ],
    QueryIntent.THEMATIC_SEARCH: [
        r"موضوع", r"theme", r"topic",
        r"عن الـ?", r"about",
        r"آيات عن", r"verses about",
    ],
    QueryIntent.STORY_SEARCH: [
        r"قصة", r"story", r"stories",
        r"نبي", r"prophet",
    ] + list(PROPHET_KEYWORDS.keys()),
    QueryIntent.RULING_SEARCH: [
        r"حكم", r"حلال", r"حرام",
        r"ruling", r"permissible", r"forbidden",
        r"فرض", r"واجب", r"سنة",
    ],
    QueryIntent.LIFE_GUIDANCE: [
        r"كيف", r"how to", r"how do",
        r"نصيحة", r"advice",
        r"ماذا أفعل", r"what should",
        r"عند", r"when facing",
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ExpandedQuery:
    """A query expanded with contextual information."""
    original: str
    detected_language: str
    intent: QueryIntent
    primary_terms: List[str]
    expanded_arabic: List[str]
    expanded_english: List[str]
    context_phrases: List[str]
    related_themes: List[str]
    confidence: float
    explanation: Dict[str, str]


@dataclass
class ContextualResult:
    """A search result with contextual information."""
    verse_id: int
    sura_no: int
    aya_no: int
    verse_reference: str
    text_uthmani: str
    # Scoring
    semantic_score: float
    lexical_score: float
    contextual_score: float
    combined_score: float
    # Context
    matched_concepts: List[str]
    matched_phrases: List[str]
    context_explanation: Dict[str, str]
    # Related content
    related_verses: List[str]
    suggested_themes: List[str]


# =============================================================================
# CONTEXTUAL SEARCH SERVICE
# =============================================================================

class ContextualSearchService:
    """
    Advanced contextual semantic search service.

    Features:
    - Cross-sentence context understanding
    - Bilingual query expansion
    - Intent detection and optimization
    - Phrase-level matching
    - Contextual result explanations
    """

    def __init__(self):
        self._model = None
        self._model_name = None
        self._initialized = False
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._bilingual_concepts = BILINGUAL_CONCEPTS

    async def initialize(self) -> bool:
        """Initialize the contextual embedding model."""
        if self._initialized:
            return self._model is not None

        try:
            from sentence_transformers import SentenceTransformer

            # Use multilingual model for cross-language understanding
            self._model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self._model_name = "paraphrase-multilingual-MiniLM-L12-v2"
            logger.info(f"Loaded contextual model: {self._model_name}")

        except ImportError:
            logger.warning("sentence-transformers not installed")
            self._model = None

        self._initialized = True
        return self._model is not None

    def detect_query_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Detect the intent behind a user query.

        Arabic: اكتشاف نية البحث
        """
        query_lower = query.lower()

        # Check for verse reference
        if re.search(r"\d+:\d+", query):
            return QueryIntent.VERSE_LOOKUP, 0.95

        # Check intent patterns
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent, 0.85

        # Check for prophet names
        for prophet_ar, aliases in PROPHET_KEYWORDS.items():
            if prophet_ar in query or any(alias in query_lower for alias in aliases):
                return QueryIntent.STORY_SEARCH, 0.9

        # Check for concept keywords
        for concept, data in self._bilingual_concepts.items():
            if (data["ar_primary"] in query or
                concept in query_lower or
                any(syn in query for syn in data["ar_synonyms"]) or
                any(syn in query_lower for syn in data["en_synonyms"])):
                return QueryIntent.THEMATIC_SEARCH, 0.8

        return QueryIntent.GENERAL, 0.5

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))

        if arabic_chars > latin_chars:
            return "ar"
        elif latin_chars > arabic_chars:
            return "en"
        return "mixed"

    def expand_query_contextually(self, query: str) -> ExpandedQuery:
        """
        Expand query with contextual understanding.

        Arabic: توسيع الاستعلام مع الفهم السياقي
        """
        query_lower = query.lower()
        language = self.detect_language(query)
        intent, confidence = self.detect_query_intent(query)

        primary_terms = []
        expanded_arabic = []
        expanded_english = []
        context_phrases = []
        related_themes = set()

        # Add original query terms
        if language == "ar":
            primary_terms.append(query)
            expanded_arabic.append(query)
        else:
            primary_terms.append(query)
            expanded_english.append(query)

        # Find matching concepts and expand
        for concept, data in self._bilingual_concepts.items():
            matched = False

            # Check if query matches this concept
            if data["ar_primary"] in query:
                matched = True
            elif concept in query_lower:
                matched = True
            elif any(syn in query for syn in data["ar_synonyms"]):
                matched = True
            elif any(syn in query_lower for syn in data["en_synonyms"]):
                matched = True

            if matched:
                # Add all Arabic synonyms
                expanded_arabic.extend([data["ar_primary"]] + data["ar_synonyms"])
                # Add English synonyms
                expanded_english.extend([concept] + data["en_synonyms"])
                # Add context phrases
                context_phrases.extend(data["context_phrases_ar"])
                context_phrases.extend(data["context_phrases_en"])
                # Add related themes
                related_themes.update(data.get("related_themes", []))

        # Expand related themes
        for theme in list(related_themes):
            if theme in self._bilingual_concepts:
                theme_data = self._bilingual_concepts[theme]
                expanded_arabic.append(theme_data["ar_primary"])
                expanded_english.append(theme)

        # Remove duplicates while preserving order
        expanded_arabic = list(dict.fromkeys(expanded_arabic))
        expanded_english = list(dict.fromkeys(expanded_english))
        context_phrases = list(dict.fromkeys(context_phrases))

        return ExpandedQuery(
            original=query,
            detected_language=language,
            intent=intent,
            primary_terms=primary_terms,
            expanded_arabic=expanded_arabic[:20],
            expanded_english=expanded_english[:15],
            context_phrases=context_phrases[:10],
            related_themes=list(related_themes),
            confidence=confidence,
            explanation={
                "ar": f"تم توسيع البحث ليشمل {len(expanded_arabic)} مصطلح عربي و{len(expanded_english)} مصطلح إنجليزي",
                "en": f"Query expanded to include {len(expanded_arabic)} Arabic terms and {len(expanded_english)} English terms",
            },
        )

    async def compute_embedding(self, text: str) -> np.ndarray:
        """Compute contextual embedding for text."""
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        if not self._initialized:
            await self.initialize()

        if self._model is not None:
            embedding = self._model.encode(text, convert_to_numpy=True)
        else:
            # Fallback embedding
            embedding = self._compute_fallback_embedding(text)

        self._embedding_cache[cache_key] = embedding
        return embedding

    def _compute_fallback_embedding(self, text: str) -> np.ndarray:
        """Compute fallback embedding when model unavailable."""
        embedding = np.zeros(384)  # MiniLM dimension

        words = text.split()
        for i, word in enumerate(words):
            word_hash = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            positions = [
                word_hash % 384,
                (word_hash * 7) % 384,
                (word_hash * 13) % 384,
            ]
            weight = 1.0 / (i + 1)
            for pos in positions:
                embedding[pos] += weight

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _compute_lexical_score(self, text: str, terms: List[str]) -> float:
        """Compute lexical matching score."""
        if not terms:
            return 0.0

        matches = sum(1 for term in terms if term in text)
        return min(matches / len(terms), 1.0)

    def _compute_phrase_score(self, text: str, phrases: List[str]) -> float:
        """Compute phrase matching score."""
        if not phrases:
            return 0.0

        matches = sum(1 for phrase in phrases if phrase in text)
        return min(matches / len(phrases), 1.0) * 1.2  # Boost for phrase matches

    async def contextual_search(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 20,
        min_score: float = 0.25,
        search_mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """
        Perform contextual semantic search.

        Arabic: البحث الدلالي السياقي
        """
        from app.models.quran import QuranVerse

        # Expand query
        expanded = self.expand_query_contextually(query)

        # Build search terms
        all_terms = expanded.expanded_arabic + [query]

        # Compute query embedding (combine primary terms)
        query_text = " ".join(expanded.primary_terms + expanded.expanded_arabic[:5])
        query_embedding = await self.compute_embedding(query_text)

        # Search for candidate verses
        conditions = []
        for term in all_terms[:15]:
            conditions.append(QuranVerse.text_uthmani.ilike(f"%{term}%"))

        if not conditions:
            return {
                "query": query,
                "expanded": self._expanded_to_dict(expanded),
                "results": [],
                "count": 0,
            }

        result = await session.execute(
            select(QuranVerse).where(or_(*conditions)).limit(limit * 3)
        )
        verses = result.scalars().all()

        # Score results
        results = []
        for verse in verses:
            # Compute scores
            verse_embedding = await self.compute_embedding(verse.text_uthmani)

            # Semantic similarity
            semantic_score = float(np.dot(query_embedding, verse_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(verse_embedding) + 1e-8
            ))

            # Lexical score
            lexical_score = self._compute_lexical_score(
                verse.text_uthmani,
                expanded.expanded_arabic
            )

            # Phrase score
            phrase_score = self._compute_phrase_score(
                verse.text_uthmani,
                expanded.context_phrases
            )

            # Contextual score (combines phrase and theme relevance)
            contextual_score = (phrase_score * 0.6 + lexical_score * 0.4)

            # Combined score based on search mode
            if search_mode == "semantic":
                combined_score = semantic_score
            elif search_mode == "lexical":
                combined_score = lexical_score
            elif search_mode == "contextual":
                combined_score = contextual_score
            else:  # hybrid
                combined_score = (
                    semantic_score * 0.4 +
                    lexical_score * 0.3 +
                    contextual_score * 0.3
                )

            if combined_score >= min_score:
                # Find matched concepts
                matched_concepts = []
                for concept, data in self._bilingual_concepts.items():
                    if any(term in verse.text_uthmani for term in [data["ar_primary"]] + data["ar_synonyms"]):
                        matched_concepts.append(concept)

                # Find matched phrases
                matched_phrases = [
                    phrase for phrase in expanded.context_phrases
                    if phrase in verse.text_uthmani
                ]

                results.append(ContextualResult(
                    verse_id=verse.id,
                    sura_no=verse.sura_no,
                    aya_no=verse.aya_no,
                    verse_reference=f"{verse.sura_no}:{verse.aya_no}",
                    text_uthmani=verse.text_uthmani,
                    semantic_score=semantic_score,
                    lexical_score=lexical_score,
                    contextual_score=contextual_score,
                    combined_score=combined_score,
                    matched_concepts=matched_concepts,
                    matched_phrases=matched_phrases,
                    context_explanation={
                        "ar": self._generate_explanation_ar(matched_concepts, matched_phrases),
                        "en": self._generate_explanation_en(matched_concepts, matched_phrases),
                    },
                    related_verses=[],
                    suggested_themes=expanded.related_themes[:3],
                ))

        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        results = results[:limit]

        return {
            "query": query,
            "expanded": self._expanded_to_dict(expanded),
            "search_mode": search_mode,
            "results": [self._result_to_dict(r) for r in results],
            "count": len(results),
            "model_used": self._model_name or "fallback",
        }

    def _expanded_to_dict(self, expanded: ExpandedQuery) -> Dict[str, Any]:
        """Convert ExpandedQuery to dict."""
        return {
            "original": expanded.original,
            "detected_language": expanded.detected_language,
            "intent": expanded.intent.value,
            "primary_terms": expanded.primary_terms,
            "expanded_arabic": expanded.expanded_arabic,
            "expanded_english": expanded.expanded_english,
            "context_phrases": expanded.context_phrases,
            "related_themes": expanded.related_themes,
            "confidence": round(expanded.confidence, 2),
            "explanation": expanded.explanation,
        }

    def _result_to_dict(self, result: ContextualResult) -> Dict[str, Any]:
        """Convert ContextualResult to dict."""
        return {
            "verse_id": result.verse_id,
            "sura_no": result.sura_no,
            "aya_no": result.aya_no,
            "verse_reference": result.verse_reference,
            "text_uthmani": result.text_uthmani,
            "scores": {
                "semantic": round(result.semantic_score, 4),
                "lexical": round(result.lexical_score, 4),
                "contextual": round(result.contextual_score, 4),
                "combined": round(result.combined_score, 4),
            },
            "matched_concepts": result.matched_concepts,
            "matched_phrases": result.matched_phrases,
            "context_explanation": result.context_explanation,
            "suggested_themes": result.suggested_themes,
        }

    def _generate_explanation_ar(
        self,
        concepts: List[str],
        phrases: List[str],
    ) -> str:
        """Generate Arabic explanation for match."""
        if concepts and phrases:
            return f"تطابق مع المفاهيم: {', '.join(concepts[:3])} والعبارات السياقية"
        elif concepts:
            return f"تطابق مع المفاهيم: {', '.join(concepts[:3])}"
        elif phrases:
            return "تطابق مع عبارات سياقية"
        return "تطابق نصي"

    def _generate_explanation_en(
        self,
        concepts: List[str],
        phrases: List[str],
    ) -> str:
        """Generate English explanation for match."""
        if concepts and phrases:
            return f"Matches concepts: {', '.join(concepts[:3])} and contextual phrases"
        elif concepts:
            return f"Matches concepts: {', '.join(concepts[:3])}"
        elif phrases:
            return "Matches contextual phrases"
        return "Lexical match"

    def get_available_concepts(self) -> List[Dict[str, Any]]:
        """Get all available bilingual concepts."""
        return [
            {
                "concept": concept,
                "ar_primary": data["ar_primary"],
                "ar_synonyms": data["ar_synonyms"],
                "en_synonyms": data["en_synonyms"],
                "related_themes": data.get("related_themes", []),
            }
            for concept, data in self._bilingual_concepts.items()
        ]

    def get_search_modes(self) -> List[Dict[str, str]]:
        """Get available search modes with descriptions."""
        return [
            {
                "mode": SearchMode.SEMANTIC.value,
                "ar": "البحث الدلالي",
                "en": "Semantic Search",
                "description_ar": "يبحث بناءً على المعنى والسياق",
                "description_en": "Searches based on meaning and context",
            },
            {
                "mode": SearchMode.LEXICAL.value,
                "ar": "البحث اللفظي",
                "en": "Lexical Search",
                "description_ar": "يبحث بناءً على الكلمات المطابقة",
                "description_en": "Searches based on matching words",
            },
            {
                "mode": SearchMode.HYBRID.value,
                "ar": "البحث المختلط",
                "en": "Hybrid Search",
                "description_ar": "يجمع بين البحث الدلالي واللفظي",
                "description_en": "Combines semantic and lexical search",
            },
            {
                "mode": SearchMode.CONTEXTUAL.value,
                "ar": "البحث السياقي",
                "en": "Contextual Search",
                "description_ar": "يركز على العبارات والسياق",
                "description_en": "Focuses on phrases and context",
            },
        ]


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

contextual_search_service = ContextualSearchService()
