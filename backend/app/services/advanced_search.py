"""
Advanced Search Service for Quranic Studies.

Provides:
1. Cross-story thematic search with query expansion
2. Semantic search with score transparency
3. Root-based morphological expansion
4. Multi-term relevance scoring
5. Search result explanation

Arabic: خدمة البحث المتقدم للدراسات القرآنية
"""

import logging
import re
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# QUERY EXPANSION DATA
# =============================================================================

# Thematic query expansion - maps concepts to related terms
THEMATIC_EXPANSIONS = {
    # Divine Attributes
    "mercy": ["رحمة", "رحيم", "رحمن", "يرحم", "غفور", "عفو", "حليم", "رؤوف"],
    "justice": ["عدل", "قسط", "حق", "ميزان", "إنصاف", "حكم"],
    "power": ["قدرة", "قدير", "قوي", "عزيز", "جبار", "متكبر", "مالك"],
    "wisdom": ["حكمة", "حكيم", "علم", "عليم", "خبير", "بصير"],
    "forgiveness": ["غفر", "مغفرة", "غفور", "عفو", "توبة", "تواب"],

    # Human Qualities
    "patience": ["صبر", "صابر", "صبور", "احتمال", "تحمل", "ثبات"],
    "gratitude": ["شكر", "شاكر", "شكور", "حمد", "نعمة"],
    "trust": ["توكل", "متوكل", "ثقة", "اعتماد", "إيمان"],
    "faith": ["إيمان", "مؤمن", "يقين", "تصديق", "إسلام"],
    "repentance": ["توبة", "تائب", "استغفار", "إنابة", "رجوع"],
    "fear": ["خوف", "خشية", "تقوى", "خائف", "وجل"],
    "hope": ["رجاء", "أمل", "طمع", "رغبة"],
    "love": ["حب", "محبة", "ود", "مودة", "رحمة"],

    # Trials and Tests
    "trial": ["ابتلاء", "امتحان", "فتنة", "اختبار", "محنة", "بلاء"],
    "adversity": ["شدة", "ضيق", "كرب", "مصيبة", "بأساء", "ضراء"],
    "hardship": ["عسر", "شدة", "ضنك", "كد", "نصب"],

    # Consequences
    "punishment": ["عذاب", "عقاب", "نقمة", "جزاء", "سخط", "غضب"],
    "reward": ["ثواب", "أجر", "جزاء", "نعيم", "جنة", "فوز"],
    "paradise": ["جنة", "فردوس", "نعيم", "خلد", "رضوان"],
    "hellfire": ["نار", "جهنم", "سعير", "جحيم", "حميم", "عذاب"],

    # Narratives
    "prophet": ["نبي", "رسول", "مرسل", "أنبياء", "رسل"],
    "story": ["قصة", "نبأ", "خبر", "حديث", "مثل"],
    "miracle": ["آية", "معجزة", "برهان", "سلطان", "بينة"],
    "guidance": ["هدى", "هداية", "رشد", "صراط", "سبيل", "طريق"],

    # Social Themes
    "family": ["أهل", "أسرة", "والد", "ولد", "زوج", "قرابة"],
    "community": ["قوم", "أمة", "جماعة", "ناس", "بشر"],
    "oppression": ["ظلم", "بغي", "عدوان", "طغيان", "جور"],
    "covenant": ["عهد", "ميثاق", "وعد", "عقد"],
}

# English to Arabic concept mapping
CONCEPT_TRANSLATIONS = {
    "mercy": "رحمة",
    "justice": "عدل",
    "patience": "صبر",
    "gratitude": "شكر",
    "trust": "توكل",
    "faith": "إيمان",
    "repentance": "توبة",
    "forgiveness": "مغفرة",
    "punishment": "عذاب",
    "reward": "ثواب",
    "paradise": "جنة",
    "hellfire": "نار",
    "prophet": "نبي",
    "guidance": "هداية",
    "trial": "ابتلاء",
    "wisdom": "حكمة",
    "power": "قدرة",
    "love": "محبة",
    "fear": "خوف",
    "hope": "رجاء",
}

# Root-based morphological expansions
ROOT_EXPANSIONS = {
    "ص-ب-ر": ["صبر", "صابر", "صبور", "صابرين", "اصبر", "اصبروا", "صبرا", "مصابرة"],
    "ر-ح-م": ["رحمة", "رحيم", "رحمن", "رحماء", "ارحم", "يرحم", "راحم", "مرحوم"],
    "ع-د-ل": ["عدل", "عادل", "معدلة", "اعدلوا", "يعدل", "عدالة"],
    "ح-ك-م": ["حكم", "حكيم", "حاكم", "محكم", "حكمة", "يحكم", "حاكمين"],
    "ت-و-ب": ["توبة", "تائب", "تواب", "توبوا", "يتوب", "متاب"],
    "غ-ف-ر": ["غفر", "غفور", "غافر", "مغفرة", "استغفر", "يغفر", "غفران"],
    "ش-ك-ر": ["شكر", "شاكر", "شكور", "شاكرين", "اشكروا", "يشكر"],
    "ع-ل-م": ["علم", "عليم", "عالم", "علماء", "يعلم", "معلوم", "تعليم"],
    "ه-د-ي": ["هدى", "هادي", "مهتدي", "هداية", "يهدي", "اهدنا"],
    "أ-م-ن": ["إيمان", "مؤمن", "مؤمنين", "آمنوا", "يؤمن", "أمان", "أمين"],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class SimilarityType(str, Enum):
    """Types of similarity in search results."""
    LEXICAL = "lexical"          # Direct word match
    SEMANTIC = "semantic"        # Meaning-based similarity
    THEMATIC = "thematic"        # Theme-based connection
    ROOT_BASED = "root_based"    # Arabic root similarity
    CONCEPTUAL = "conceptual"    # Concept overlap
    STRUCTURAL = "structural"    # Grammatical similarity


@dataclass
class SearchExplanation:
    """Explanation of why a result matched."""
    similarity_types: List[SimilarityType]
    matched_terms: List[str]
    expanded_terms: List[str]
    thematic_connections: List[str]
    score_breakdown: Dict[str, float]
    explanation_ar: str
    explanation_en: str


@dataclass
class ExpandedQuery:
    """Query with expanded terms."""
    original_query: str
    expanded_terms_ar: List[str]
    expanded_terms_en: List[str]
    detected_themes: List[str]
    detected_roots: List[str]
    expansion_strategy: str


@dataclass
class SearchResult:
    """A search result with full explanation."""
    verse_id: int
    sura_no: int
    aya_no: int
    verse_reference: str
    text_uthmani: str
    total_score: float
    explanation: SearchExplanation
    related_themes: List[str]
    prophet_connections: List[str]


# =============================================================================
# ADVANCED SEARCH SERVICE
# =============================================================================

class AdvancedSearchService:
    """
    Advanced search service with query expansion and score transparency.

    Features:
    - Multi-term query expansion
    - Root-based morphological search
    - Thematic connection discovery
    - Score transparency and explanations
    - Cross-story search capabilities
    """

    def __init__(self):
        self._thematic_expansions = THEMATIC_EXPANSIONS
        self._concept_translations = CONCEPT_TRANSLATIONS
        self._root_expansions = ROOT_EXPANSIONS

    def expand_query(self, query: str, language: str = "auto") -> ExpandedQuery:
        """
        Expand a search query with related terms.

        Arabic: توسيع استعلام البحث بمصطلحات ذات صلة
        """
        query_lower = query.lower().strip()
        expanded_ar = []
        expanded_en = []
        detected_themes = []
        detected_roots = []

        # Detect language
        is_arabic = bool(re.search(r'[\u0600-\u06FF]', query))

        if is_arabic:
            # Arabic query - find thematic expansions
            for theme, terms in self._thematic_expansions.items():
                if any(term in query for term in terms):
                    detected_themes.append(theme)
                    expanded_ar.extend(terms)

            # Find root expansions
            for root, forms in self._root_expansions.items():
                if any(form in query for form in forms):
                    detected_roots.append(root)
                    expanded_ar.extend(forms)

            # Add original query terms
            expanded_ar.append(query)

        else:
            # English query - translate to Arabic concepts
            for en_term, ar_term in self._concept_translations.items():
                if en_term in query_lower:
                    expanded_en.append(en_term)
                    expanded_ar.append(ar_term)

                    # Get thematic expansions for this concept
                    if en_term in self._thematic_expansions:
                        detected_themes.append(en_term)
                        expanded_ar.extend(self._thematic_expansions[en_term])

        # Remove duplicates while preserving order
        expanded_ar = list(dict.fromkeys(expanded_ar))
        expanded_en = list(dict.fromkeys(expanded_en))

        return ExpandedQuery(
            original_query=query,
            expanded_terms_ar=expanded_ar,
            expanded_terms_en=expanded_en,
            detected_themes=detected_themes,
            detected_roots=detected_roots,
            expansion_strategy="thematic_and_root" if detected_roots else "thematic",
        )

    async def search_with_expansion(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 20,
        include_explanation: bool = True,
        theme_filter: Optional[str] = None,
        prophet_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search with query expansion and detailed explanations.

        Arabic: البحث مع توسيع الاستعلام وشرح مفصل
        """
        from app.models.quran import QuranVerse
        from app.services.cross_story_themes import cross_story_service

        # Expand query
        expanded = self.expand_query(query)

        # Build search terms
        search_terms = expanded.expanded_terms_ar + [query]

        # Search for verses containing any of the expanded terms
        conditions = []
        for term in search_terms[:15]:  # Limit to prevent too broad search
            conditions.append(QuranVerse.text_uthmani.ilike(f"%{term}%"))

        if not conditions:
            return {
                "query": query,
                "expanded_query": expanded,
                "results": [],
                "count": 0,
            }

        # Execute search
        result = await session.execute(
            select(QuranVerse).where(or_(*conditions)).limit(limit * 2)
        )
        verses = result.scalars().all()

        # Score and rank results
        scored_results = []
        for verse in verses:
            score, explanation = self._calculate_score_with_explanation(
                verse, query, expanded, search_terms
            )

            # Apply filters
            if theme_filter:
                verse_themes = self._detect_verse_themes(verse.text_uthmani)
                if theme_filter not in verse_themes:
                    continue

            # Get related themes and prophets
            verse_themes = self._detect_verse_themes(verse.text_uthmani)
            prophet_connections = self._detect_prophet_mentions(verse.text_uthmani)

            if prophet_filter and prophet_filter not in prophet_connections:
                continue

            scored_results.append(SearchResult(
                verse_id=verse.id,
                sura_no=verse.sura_no,
                aya_no=verse.aya_no,
                verse_reference=f"{verse.sura_no}:{verse.aya_no}",
                text_uthmani=verse.text_uthmani,
                total_score=score,
                explanation=explanation,
                related_themes=verse_themes,
                prophet_connections=prophet_connections,
            ))

        # Sort by score
        scored_results.sort(key=lambda x: x.total_score, reverse=True)
        scored_results = scored_results[:limit]

        return {
            "query": query,
            "expanded_query": {
                "original": expanded.original_query,
                "expanded_terms_ar": expanded.expanded_terms_ar[:10],
                "detected_themes": expanded.detected_themes,
                "detected_roots": expanded.detected_roots,
                "expansion_strategy": expanded.expansion_strategy,
            },
            "results": [
                {
                    "verse_id": r.verse_id,
                    "sura_no": r.sura_no,
                    "aya_no": r.aya_no,
                    "verse_reference": r.verse_reference,
                    "text_uthmani": r.text_uthmani,
                    "total_score": round(r.total_score, 4),
                    "explanation": {
                        "similarity_types": [t.value for t in r.explanation.similarity_types],
                        "matched_terms": r.explanation.matched_terms,
                        "score_breakdown": r.explanation.score_breakdown,
                        "explanation_ar": r.explanation.explanation_ar,
                        "explanation_en": r.explanation.explanation_en,
                    } if include_explanation else None,
                    "related_themes": r.related_themes,
                    "prophet_connections": r.prophet_connections,
                }
                for r in scored_results
            ],
            "count": len(scored_results),
            "total_expanded_terms": len(expanded.expanded_terms_ar),
        }

    def _calculate_score_with_explanation(
        self,
        verse: Any,
        original_query: str,
        expanded: ExpandedQuery,
        search_terms: List[str],
    ) -> Tuple[float, SearchExplanation]:
        """Calculate similarity score with detailed explanation."""
        text = verse.text_uthmani
        text_lower = text.lower()

        score = 0.0
        similarity_types = []
        matched_terms = []
        score_breakdown = {}

        # 1. Direct match score
        if original_query in text:
            score += 0.4
            similarity_types.append(SimilarityType.LEXICAL)
            matched_terms.append(original_query)
            score_breakdown["lexical_direct"] = 0.4

        # 2. Expanded terms match
        expanded_match_score = 0.0
        for term in expanded.expanded_terms_ar:
            if term in text:
                expanded_match_score += 0.05
                matched_terms.append(term)

        expanded_match_score = min(expanded_match_score, 0.3)
        if expanded_match_score > 0:
            score += expanded_match_score
            similarity_types.append(SimilarityType.THEMATIC)
            score_breakdown["thematic_expansion"] = round(expanded_match_score, 3)

        # 3. Root-based scoring
        root_score = 0.0
        for root, forms in self._root_expansions.items():
            matches = sum(1 for form in forms if form in text)
            if matches > 0:
                root_score += 0.02 * matches
                if SimilarityType.ROOT_BASED not in similarity_types:
                    similarity_types.append(SimilarityType.ROOT_BASED)

        root_score = min(root_score, 0.2)
        if root_score > 0:
            score += root_score
            score_breakdown["root_based"] = round(root_score, 3)

        # 4. Theme detection bonus
        verse_themes = self._detect_verse_themes(text)
        theme_overlap = set(verse_themes) & set(expanded.detected_themes)
        if theme_overlap:
            theme_bonus = 0.1 * len(theme_overlap)
            score += min(theme_bonus, 0.2)
            similarity_types.append(SimilarityType.CONCEPTUAL)
            score_breakdown["theme_overlap"] = round(min(theme_bonus, 0.2), 3)

        # Generate explanation
        explanation_parts_ar = []
        explanation_parts_en = []

        if SimilarityType.LEXICAL in similarity_types:
            explanation_parts_ar.append("تطابق مباشر مع مصطلح البحث")
            explanation_parts_en.append("Direct match with search term")

        if SimilarityType.THEMATIC in similarity_types:
            explanation_parts_ar.append(f"تطابق موضوعي مع {len(matched_terms)} مصطلحات")
            explanation_parts_en.append(f"Thematic match with {len(matched_terms)} terms")

        if SimilarityType.ROOT_BASED in similarity_types:
            explanation_parts_ar.append("تطابق جذري في اللغة العربية")
            explanation_parts_en.append("Arabic root-based match")

        if SimilarityType.CONCEPTUAL in similarity_types:
            explanation_parts_ar.append(f"تداخل في المواضيع: {', '.join(theme_overlap)}")
            explanation_parts_en.append(f"Theme overlap: {', '.join(theme_overlap)}")

        return score, SearchExplanation(
            similarity_types=similarity_types,
            matched_terms=matched_terms[:10],
            expanded_terms=expanded.expanded_terms_ar[:5],
            thematic_connections=list(theme_overlap) if theme_overlap else [],
            score_breakdown=score_breakdown,
            explanation_ar=" | ".join(explanation_parts_ar) if explanation_parts_ar else "نتيجة بحث عامة",
            explanation_en=" | ".join(explanation_parts_en) if explanation_parts_en else "General search result",
        )

    def _detect_verse_themes(self, text: str) -> List[str]:
        """Detect themes present in verse text."""
        themes = []
        for theme, terms in self._thematic_expansions.items():
            if any(term in text for term in terms):
                themes.append(theme)
        return themes[:5]

    def _detect_prophet_mentions(self, text: str) -> List[str]:
        """Detect prophet names mentioned in verse."""
        prophets = {
            "إبراهيم": "Ibrahim",
            "موسى": "Musa",
            "عيسى": "Isa",
            "محمد": "Muhammad",
            "نوح": "Nuh",
            "يوسف": "Yusuf",
            "يعقوب": "Ya'qub",
            "داود": "Dawud",
            "سليمان": "Sulayman",
            "أيوب": "Ayyub",
            "يونس": "Yunus",
            "هود": "Hud",
            "صالح": "Salih",
            "لوط": "Lut",
            "شعيب": "Shu'ayb",
            "آدم": "Adam",
            "إسماعيل": "Ismail",
        }

        found = []
        for ar_name, en_name in prophets.items():
            if ar_name in text:
                found.append(ar_name)
        return found

    async def cross_story_search(
        self,
        theme: str,
        prophets: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None,
        limit: int = 30,
    ) -> Dict[str, Any]:
        """
        Search across stories for a specific theme.

        Arabic: البحث عبر القصص لموضوع معين
        """
        from app.services.cross_story_themes import cross_story_service

        # Get theme details
        theme_details = cross_story_service.get_theme_details(theme)

        results_by_prophet = {}

        if theme_details:
            for prophet_data in theme_details.get("prophets", []):
                prophet_name = prophet_data["name"]

                # Filter by prophets if specified
                if prophets and prophet_name not in prophets:
                    continue

                results_by_prophet[prophet_name] = {
                    "prophet_name": prophet_name,
                    "relevance": prophet_data["relevance"],
                    "aspect": prophet_data["aspect"],
                    "key_verses": prophet_data["key_verses"],
                    "suras": prophet_data.get("suras", []),
                }

        # Get related themes
        related_themes = theme_details.get("related_themes", []) if theme_details else []

        # Get moral lessons
        moral_lessons = theme_details.get("moral_lessons", {}) if theme_details else {}

        return {
            "theme": theme,
            "theme_ar": theme_details.get("name_ar", "") if theme_details else "",
            "theme_en": theme_details.get("name_en", "") if theme_details else theme,
            "category": theme_details.get("category", "") if theme_details else "",
            "results_by_prophet": results_by_prophet,
            "prophet_count": len(results_by_prophet),
            "related_themes": related_themes,
            "moral_lessons": moral_lessons,
        }

    async def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Get search suggestions based on partial query.

        Arabic: الحصول على اقتراحات البحث
        """
        suggestions = []
        partial_lower = partial_query.lower()

        # Check English concepts
        for en_term, ar_term in self._concept_translations.items():
            if en_term.startswith(partial_lower) or partial_lower in en_term:
                suggestions.append({
                    "term_en": en_term,
                    "term_ar": ar_term,
                    "type": "concept",
                })

        # Check themes
        for theme in self._thematic_expansions.keys():
            if theme.startswith(partial_lower) or partial_lower in theme:
                suggestions.append({
                    "term_en": theme,
                    "term_ar": self._concept_translations.get(theme, ""),
                    "type": "theme",
                })

        return suggestions[:limit]

    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Get list of available search themes."""
        themes = []
        for theme, terms in self._thematic_expansions.items():
            ar_term = self._concept_translations.get(theme, terms[0] if terms else "")
            themes.append({
                "theme_id": theme,
                "theme_ar": ar_term,
                "theme_en": theme.replace("_", " ").title(),
                "term_count": len(terms),
                "sample_terms": terms[:3],
            })
        return themes

    def get_available_roots(self) -> List[Dict[str, Any]]:
        """Get list of available Arabic roots for search."""
        roots = []
        for root, forms in self._root_expansions.items():
            roots.append({
                "root": root,
                "forms": forms[:5],
                "form_count": len(forms),
            })
        return roots


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

advanced_search_service = AdvancedSearchService()
