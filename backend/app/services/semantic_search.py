"""
Enhanced Semantic Search Service.

Provides advanced semantic search capabilities:
- Vector-based semantic search
- Query intent understanding
- Concept expansion
- Confidence scoring
- Multi-modal search (text, concept, theme)
- Embedding caching for performance
- Arabic text normalization

Arabic: خدمة البحث الدلالي المحسن
"""
import logging
import hashlib
import time
import re
import threading
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

import httpx

from app.core.config import settings
from app.kg.client import get_kg_client, KGClient
from app.services.search_suggestions import get_suggestions_service, SuggestionType

logger = logging.getLogger(__name__)

# =============================================================================
# Embedding Cache Configuration
# =============================================================================

EMBEDDING_CACHE_CONFIG = {
    "max_size": int(os.getenv("EMBEDDING_CACHE_SIZE", "5000")),
    "ttl_seconds": int(os.getenv("EMBEDDING_CACHE_TTL", "3600")),
}

# Arabic text normalization patterns
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670]')
ARABIC_NORMALIZATION = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ى': 'ي', 'ئ': 'ي',
    'ؤ': 'و',
    'ة': 'ه',
}


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for better matching."""
    if not text:
        return text
    # Remove diacritics
    text = ARABIC_DIACRITICS.sub('', text)
    # Normalize letters
    for old, new in ARABIC_NORMALIZATION.items():
        text = text.replace(old, new)
    return text


@dataclass
class EmbeddingCacheEntry:
    """Cached embedding with timestamp."""
    embedding: List[float]
    created_at: float
    access_count: int = 0


class EmbeddingCache:
    """Thread-safe LRU cache for embeddings."""

    def __init__(self, max_size: int = 5000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, EmbeddingCacheEntry] = {}
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0}

    def _make_key(self, text: str) -> str:
        """Generate cache key from text."""
        normalized = normalize_arabic_text(text.lower().strip())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available and not expired."""
        key = self._make_key(text)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry.created_at < self.ttl_seconds:
                    entry.access_count += 1
                    self._stats["hits"] += 1
                    return entry.embedding
                else:
                    del self._cache[key]
            self._stats["misses"] += 1
        return None

    def set(self, text: str, embedding: List[float]):
        """Cache an embedding."""
        key = self._make_key(text)
        with self._lock:
            # Evict least accessed if full
            if len(self._cache) >= self.max_size:
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: (x[1].access_count, x[1].created_at)
                )
                for k, _ in sorted_items[:self.max_size // 4]:
                    del self._cache[k]

            self._cache[key] = EmbeddingCacheEntry(
                embedding=embedding,
                created_at=time.time()
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": round(hit_rate, 3),
            }


# Global embedding cache
_embedding_cache = EmbeddingCache(
    max_size=EMBEDDING_CACHE_CONFIG["max_size"],
    ttl_seconds=EMBEDDING_CACHE_CONFIG["ttl_seconds"]
)


class SearchIntent(str, Enum):
    """Types of search intents."""
    VERSE_MEANING = "verse_meaning"
    THEME_SEARCH = "theme_search"
    STORY_SEARCH = "story_search"
    CONCEPT_SEARCH = "concept_search"
    PERSON_SEARCH = "person_search"
    GENERAL = "general"


class ThematicCategory(str, Enum):
    """Thematic categories for search filtering."""
    # Core Theological Themes
    TAWHEED = "tawheed"
    PROPHETS = "prophets"
    AFTERLIFE = "afterlife"
    WORSHIP = "worship"
    ETHICS = "ethics"
    LAW = "law"
    HISTORY = "history"
    NATURE = "nature"
    GUIDANCE = "guidance"
    COMMUNITY = "community"
    # Emotional & Spiritual Themes
    PATIENCE = "patience"
    GRATITUDE = "gratitude"
    TRUST = "trust"
    TRIALS = "trials"
    GRIEF = "grief"
    HOPE = "hope"
    FEAR = "fear"
    LOVE = "love"
    REPENTANCE = "repentance"
    CONTENTMENT = "contentment"
    # Divine Attributes Themes
    DIVINE_MERCY = "divine_mercy"
    DIVINE_JUSTICE = "divine_justice"
    DIVINE_POWER = "divine_power"
    DIVINE_WISDOM = "divine_wisdom"
    DIVINE_KNOWLEDGE = "divine_knowledge"
    DIVINE_FORGIVENESS = "divine_forgiveness"
    # Consequence Themes
    PUNISHMENT = "punishment"
    REWARD = "reward"
    PUNISHMENT_REWARD = "punishment_reward"
    HELLFIRE = "hellfire"
    PARADISE = "paradise"
    # Social & Moral Themes
    FAMILY = "family"
    JUSTICE = "justice"
    CHARITY = "charity"
    HONESTY = "honesty"
    HUMILITY = "humility"
    BROTHERHOOD = "brotherhood"
    # Narrative Themes
    CREATION = "creation"
    RESURRECTION = "resurrection"
    COVENANT = "covenant"
    SALVATION = "salvation"
    SUBMISSION = "submission"


# Arabic labels for thematic categories
THEME_LABELS_AR = {
    # Core Theological Themes
    "tawheed": "التوحيد",
    "prophets": "الأنبياء",
    "afterlife": "الآخرة",
    "worship": "العبادات",
    "ethics": "الأخلاق",
    "law": "الأحكام",
    "history": "التاريخ",
    "nature": "الكون",
    "guidance": "الهداية",
    "community": "المجتمع",
    # Emotional & Spiritual Themes
    "patience": "الصبر",
    "gratitude": "الشكر",
    "trust": "التوكل",
    "trials": "الابتلاء",
    "grief": "الحزن",
    "hope": "الرجاء",
    "fear": "الخوف",
    "love": "المحبة",
    "repentance": "التوبة",
    "contentment": "الرضا",
    # Divine Attributes Themes
    "divine_mercy": "الرحمة الإلهية",
    "divine_justice": "العدل الإلهي",
    "divine_power": "القدرة الإلهية",
    "divine_wisdom": "الحكمة الإلهية",
    "divine_knowledge": "العلم الإلهي",
    "divine_forgiveness": "المغفرة",
    # Consequence Themes
    "punishment": "العقاب",
    "reward": "الثواب",
    "punishment_reward": "الجزاء",
    "hellfire": "النار",
    "paradise": "الجنة",
    # Social & Moral Themes
    "family": "الأسرة",
    "justice": "العدالة",
    "charity": "الصدقة",
    "honesty": "الصدق",
    "humility": "التواضع",
    "brotherhood": "الأخوة",
    # Narrative Themes
    "creation": "الخلق",
    "resurrection": "البعث",
    "covenant": "العهد",
    "salvation": "النجاة",
    "submission": "الإسلام",
}


@dataclass
class SearchHit:
    """A single search result."""
    id: str
    type: str
    title: str
    title_ar: str
    content: str
    content_ar: str
    score: float
    confidence: float
    verse_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Complete search result with metadata."""
    query: str
    expanded_query: str
    intent: SearchIntent
    hits: List[SearchHit]
    total_found: int
    related_concepts: List[Dict[str, Any]] = field(default_factory=list)
    suggested_queries: List[str] = field(default_factory=list)
    search_time_ms: int = 0


SEMANTIC_GLOSSARY = {
    "patience": ["صبر", "sabr", "perseverance"],
    "صبر": ["patience", "sabr", "perseverance"],
    "trust": ["توكل", "tawakkul", "reliance"],
    "توكل": ["trust", "tawakkul", "reliance"],
    "faith": ["إيمان", "iman", "belief"],
    "إيمان": ["faith", "iman", "belief"],
    "repentance": ["توبة", "tawbah"],
    "توبة": ["repentance", "tawbah"],
    "mercy": ["رحمة", "rahmah", "compassion"],
    "رحمة": ["mercy", "rahmah", "compassion"],
    "moses": ["موسى", "musa"],
    "موسى": ["moses", "musa"],
    "abraham": ["إبراهيم", "ibrahim"],
    "إبراهيم": ["abraham", "ibrahim"],
}


@dataclass
class SimilarVerseResult:
    """Result of similar verse search."""
    verses: List[Dict[str, Any]]
    source_themes: List[str]
    search_method: str


@dataclass
class ThematicConnection:
    """Thematic connection between verses."""
    verse_id: int
    sura_no: int
    aya_no: int
    reference: str
    text_uthmani: str
    text_imlaei: str
    themes: List[str]
    connection_type: str
    similarity_score: float


@dataclass
class ThematicConnectionResult:
    """Result of thematic connection search."""
    connections: List[ThematicConnection]
    dominant_themes: List[str]


@dataclass
class ConceptOccurrence:
    """Occurrence of a concept in a verse."""
    sura_no: int
    aya_no: int
    reference: str
    text_snippet: str
    context: str
    frequency: int


@dataclass
class ConceptEvolutionResult:
    """Result of concept evolution analysis."""
    concept: str
    concept_normalized: str
    total_occurrences: int
    occurrences_by_period: Dict[str, int]
    occurrences: List[ConceptOccurrence]
    related_concepts: List[Dict[str, Any]]
    evolution_pattern: str


class SemanticSearchService:
    """Enhanced semantic search with concept expansion.

    Supports both KG-based search (for graph.py) and database-based search (for quran.py).
    """

    def __init__(self, session=None, kg_client: KGClient = None):
        """Initialize with optional session for database operations or kg_client for graph operations."""
        self.session = session
        self.kg = kg_client or (get_kg_client() if kg_client is None and session is None else None)
        if settings:
            self.qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        else:
            self.qdrant_url = "http://localhost:6333"
        self._embedding_model = None
        self._similarity_service = None

    def _get_similarity_service(self):
        """Lazy load the similarity service."""
        if self._similarity_service is None and self.session is not None:
            from app.services.advanced_similarity import AdvancedSimilarityService
            self._similarity_service = AdvancedSimilarityService(self.session)
        return self._similarity_service

    async def search(
        self,
        query: str,
        language: str = "ar",
        intent: SearchIntent = None,
        expand_concepts: bool = True,
        include_related: bool = True,
        limit: int = 20,
        min_confidence: float = 0.3,
    ) -> SearchResult:
        """Perform enhanced semantic search."""
        import time
        start_time = time.time()

        if intent is None:
            intent = self._detect_intent(query)

        expanded_terms = self._expand_query(query) if expand_concepts else []
        expanded_query = query
        if expanded_terms:
            expanded_query = f"{query} {' '.join(expanded_terms)}"

        hits: List[SearchHit] = []

        if intent == SearchIntent.STORY_SEARCH:
            hits = await self._search_stories(expanded_query, language, limit)
        elif intent == SearchIntent.THEME_SEARCH:
            hits = await self._search_themes(expanded_query, language, limit)
        elif intent == SearchIntent.PERSON_SEARCH:
            hits = await self._search_persons(expanded_query, language, limit)
        else:
            hits = await self._general_search(expanded_query, language, limit)

        hits = [h for h in hits if h.confidence >= min_confidence]

        related_concepts = []
        if include_related and hits:
            related_concepts = await self._get_related_concepts(query, limit=5)

        suggested_queries = self._generate_suggestions(query, hits)

        search_time_ms = int((time.time() - start_time) * 1000)

        return SearchResult(
            query=query,
            expanded_query=expanded_query,
            intent=intent,
            hits=hits,
            total_found=len(hits),
            related_concepts=related_concepts,
            suggested_queries=suggested_queries,
            search_time_ms=search_time_ms,
        )

    def _detect_intent(self, query: str) -> SearchIntent:
        """Detect search intent from query."""
        query_lower = query.lower()

        story_indicators = ["story", "قصة", "حكاية", "tale"]
        if any(ind in query_lower for ind in story_indicators):
            return SearchIntent.STORY_SEARCH

        person_indicators = ["prophet", "نبي", "رسول", "who is", "من هو"]
        if any(ind in query_lower for ind in person_indicators):
            return SearchIntent.PERSON_SEARCH

        theme_indicators = ["theme", "موضوع", "concept", "مفهوم"]
        if any(ind in query_lower for ind in theme_indicators):
            return SearchIntent.THEME_SEARCH

        return SearchIntent.GENERAL

    def _expand_query(self, query: str) -> List[str]:
        """Expand query with semantic equivalents."""
        expanded = set()
        query_lower = query.lower()

        for term, equivalents in SEMANTIC_GLOSSARY.items():
            if term.lower() in query_lower or term in query:
                expanded.update(equivalents)

        try:
            suggestions_service = get_suggestions_service()
            suggestions_terms = suggestions_service.expand_query(query)
            expanded.update(suggestions_terms)
        except Exception as e:
            logger.debug(f"Suggestions expansion failed: {e}")

        query_words = set(query_lower.split())
        expanded = {e for e in expanded if e.lower() not in query_words}

        return list(expanded)[:10]

    async def _search_stories(self, query: str, language: str, limit: int) -> List[SearchHit]:
        """Search for stories using slug match and text search."""
        hits: List[SearchHit] = []
        seen_ids = set()

        try:
            title_field = "title_ar" if language == "ar" else "title_en"
            summary_field = "summary_ar" if language == "ar" else "summary_en"

            # Split query into individual terms and search each
            terms = query.lower().split()

            for term in terms:
                if len(hits) >= limit:
                    break

                # Search by slug (partial match)
                term_slug = term.replace(" ", "_")
                slug_results = await self.kg.query(
                    f"SELECT * FROM story_cluster WHERE slug CONTAINS $q LIMIT {limit};",
                    {"q": term_slug}
                )

                for result in slug_results:
                    rid = result.get("id", "")
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        hits.append(SearchHit(
                            id=rid,
                            type="story",
                            title=result.get("title_en", ""),
                            title_ar=result.get("title_ar", ""),
                            content=result.get("summary_en", ""),
                            content_ar=result.get("summary_ar", ""),
                            score=1.0,
                            confidence=0.95,
                            metadata={"category": result.get("category"), "slug": result.get("slug")},
                        ))

            # Search by title/summary (case-insensitive) for first 3 terms
            if len(hits) < limit:
                for term in terms[:3]:
                    if len(hits) >= limit:
                        break
                    text_results = await self.kg.query(
                        f"SELECT * FROM story_cluster WHERE string::lowercase({title_field}) CONTAINS string::lowercase($q) OR string::lowercase({summary_field}) CONTAINS string::lowercase($q) LIMIT {limit};",
                        {"q": term}
                    )

                    for i, result in enumerate(text_results):
                        rid = result.get("id", "")
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            score = 0.8 - (i / max(len(text_results), 1)) * 0.3
                            hits.append(SearchHit(
                                id=rid,
                                type="story",
                                title=result.get("title_en", ""),
                                title_ar=result.get("title_ar", ""),
                                content=result.get("summary_en", ""),
                                content_ar=result.get("summary_ar", ""),
                                score=score,
                                confidence=self._score_to_confidence(score),
                                metadata={"category": result.get("category"), "slug": result.get("slug")},
                            ))

            # Also search stories by their tags
            if len(hits) < limit:
                for term in terms:
                    if len(hits) >= limit:
                        break
                    term_tag = term.replace(" ", "_")
                    tag_results = await self.kg.query(
                        f"SELECT * FROM story_cluster WHERE $q IN tags LIMIT {limit};",
                        {"q": term_tag}
                    )

                    for result in tag_results:
                        rid = result.get("id", "")
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            hits.append(SearchHit(
                                id=rid,
                                type="story",
                                title=result.get("title_en", ""),
                                title_ar=result.get("title_ar", ""),
                                content=result.get("summary_en", ""),
                                content_ar=result.get("summary_ar", ""),
                                score=0.7,
                                confidence=0.7,
                                metadata={"category": result.get("category"), "slug": result.get("slug"), "matched_via": "tag"},
                            ))

            # Search stories via tagged_with edges (concept links)
            if len(hits) < limit:
                for term in terms:
                    if len(hits) >= limit:
                        break
                    term_key = term.replace(" ", "_")
                    # Find stories linked to concepts matching this term
                    edge_results = await self.kg.query(
                        f"""SELECT in.* FROM tagged_with
                            WHERE out.key = $q
                            AND in IS NOT NONE
                            LIMIT {limit};""",
                        {"q": term_key}
                    )

                    for result in edge_results:
                        rid = result.get("id", "")
                        if rid and rid not in seen_ids:
                            seen_ids.add(rid)
                            hits.append(SearchHit(
                                id=rid,
                                type="story",
                                title=result.get("title_en", ""),
                                title_ar=result.get("title_ar", ""),
                                content=result.get("summary_en", ""),
                                content_ar=result.get("summary_ar", ""),
                                score=0.85,
                                confidence=0.85,
                                metadata={"category": result.get("category"), "slug": result.get("slug"), "matched_via": "concept_link"},
                            ))

        except Exception as e:
            logger.error(f"Story search error: {e}")

        return hits[:limit]

    async def _search_themes(self, query: str, language: str, limit: int) -> List[SearchHit]:
        """Search for themes using key match and text search."""
        hits: List[SearchHit] = []
        seen_ids = set()

        try:
            label_field = "label_ar" if language == "ar" else "label_en"

            # Split query into individual terms and search each
            terms = query.lower().split()

            for term in terms:
                if len(hits) >= limit:
                    break

                # Normalize term for key matching (replace spaces with underscores)
                term_key = term.replace(" ", "_")

                # Try exact key match first
                key_results = await self.kg.query(
                    f"SELECT * FROM concept_tag WHERE key = $q LIMIT {limit};",
                    {"q": term_key}
                )

                for result in key_results:
                    rid = result.get("id", "")
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        hits.append(SearchHit(
                            id=rid,
                            type="theme",
                            title=result.get("label_en", ""),
                            title_ar=result.get("label_ar", ""),
                            content=result.get("description_en", ""),
                            content_ar=result.get("description_ar", ""),
                            score=1.0,  # Exact match gets highest score
                            confidence=0.95,
                            metadata={"category": result.get("category"), "key": result.get("key")},
                        ))

                # Also try partial key match (CONTAINS)
                if len(hits) < limit:
                    partial_results = await self.kg.query(
                        f"SELECT * FROM concept_tag WHERE key CONTAINS $q LIMIT {limit};",
                        {"q": term_key}
                    )

                    for result in partial_results:
                        rid = result.get("id", "")
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            hits.append(SearchHit(
                                id=rid,
                                type="theme",
                                title=result.get("label_en", ""),
                                title_ar=result.get("label_ar", ""),
                                content=result.get("description_en", ""),
                                content_ar=result.get("description_ar", ""),
                                score=0.9,
                                confidence=0.9,
                                metadata={"category": result.get("category"), "key": result.get("key")},
                            ))

            # Then search by label text (case-insensitive partial match)
            if len(hits) < limit:
                for term in terms[:3]:  # Limit label searches to first 3 terms
                    if len(hits) >= limit:
                        break
                    label_results = await self.kg.query(
                        f"SELECT * FROM concept_tag WHERE string::lowercase({label_field}) CONTAINS string::lowercase($q) LIMIT {limit};",
                        {"q": term}
                    )

                    for i, result in enumerate(label_results):
                        rid = result.get("id", "")
                        if rid not in seen_ids:
                            seen_ids.add(rid)
                            score = 0.8 - (i / max(len(label_results), 1)) * 0.3
                            hits.append(SearchHit(
                                id=rid,
                                type="theme",
                                title=result.get("label_en", ""),
                                title_ar=result.get("label_ar", ""),
                                content=result.get("description_en", ""),
                                content_ar=result.get("description_ar", ""),
                                score=score,
                                confidence=self._score_to_confidence(score),
                                metadata={"category": result.get("category"), "key": result.get("key")},
                            ))

        except Exception as e:
            logger.error(f"Theme search error: {e}")

        return hits[:limit]

    async def _search_persons(self, query: str, language: str, limit: int) -> List[SearchHit]:
        """Search for persons."""
        hits: List[SearchHit] = []
        try:
            suggestions_service = get_suggestions_service()
            suggestions = suggestions_service.get_suggestions(
                query, limit=limit, types=[SuggestionType.PROPHET]
            )
            for suggestion in suggestions:
                hits.append(SearchHit(
                    id=suggestion.metadata.get("key", ""),
                    type="person",
                    title=suggestion.text,
                    title_ar=suggestion.text_ar,
                    content="",
                    content_ar="",
                    score=suggestion.relevance,
                    confidence=suggestion.relevance,
                    metadata=suggestion.metadata,
                ))
        except Exception as e:
            logger.error(f"Person search error: {e}")
        return hits

    async def _general_search(self, query: str, language: str, limit: int) -> List[SearchHit]:
        """Perform general search."""
        all_hits: List[SearchHit] = []
        per_type_limit = max(5, limit // 3)
        stories = await self._search_stories(query, language, per_type_limit)
        themes = await self._search_themes(query, language, per_type_limit)
        persons = await self._search_persons(query, language, per_type_limit)
        all_hits.extend(stories)
        all_hits.extend(themes)
        all_hits.extend(persons)
        all_hits.sort(key=lambda h: h.score, reverse=True)
        return all_hits[:limit]

    async def _get_related_concepts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get related concepts."""
        related = []
        try:
            suggestions_service = get_suggestions_service()
            suggestions = suggestions_service.get_suggestions(query, limit=limit)
            for suggestion in suggestions:
                related.append({
                    "id": suggestion.metadata.get("key", ""),
                    "label_ar": suggestion.text_ar,
                    "label_en": suggestion.text,
                    "type": suggestion.type.value,
                    "relevance": suggestion.relevance,
                })
        except Exception as e:
            logger.debug(f"Related concepts error: {e}")
        return related

    def _generate_suggestions(self, query: str, hits: List[SearchHit]) -> List[str]:
        """Generate query suggestions."""
        suggestions = []
        if hits:
            primary_type = hits[0].type
            if primary_type == "story":
                suggestions.append(f"lessons from {query}")
        expanded = self._expand_query(query)
        for term in expanded[:3]:
            suggestions.append(term)
        return suggestions[:5]

    def _score_to_confidence(self, score: float) -> float:
        """Convert score to confidence."""
        if score >= 0.8:
            return 0.95
        elif score >= 0.6:
            return 0.8
        elif score >= 0.4:
            return 0.6
        else:
            return max(0.3, score)

    # ==========================================================================
    # Database-backed methods for quran.py compatibility
    # ==========================================================================

    async def find_similar_verses(
        self,
        verse_text: str,
        top_k: int = 20,
        theme_filter: Optional[ThematicCategory] = None,
        exclude_sura: Optional[int] = None,
    ) -> SimilarVerseResult:
        """Find verses similar to the given verse text.

        Used by quran.py for verse similarity search.
        """
        similarity_service = self._get_similarity_service()
        if similarity_service is not None:
            try:
                result = await similarity_service.find_similar_verses(
                    verse_text=verse_text,
                    top_k=top_k,
                    theme_filter=theme_filter.value if theme_filter else None,
                    exclude_same_sura=exclude_sura is not None,
                )
                return SimilarVerseResult(
                    verses=[{
                        "verse_id": m.verse_id,
                        "sura_no": m.sura_no,
                        "aya_no": m.aya_no,
                        "reference": m.reference,
                        "text_uthmani": m.text_uthmani,
                        "text_imlaei": m.text_imlaei,
                        "combined_score": m.combined_score,
                        "connection_type": m.connection_type.value if hasattr(m.connection_type, 'value') else str(m.connection_type),
                        "themes": m.shared_themes,
                    } for m in result.matches],
                    source_themes=result.source_themes,
                    search_method=result.search_method,
                )
            except Exception as e:
                logger.error(f"Similarity service error: {e}")

        return SimilarVerseResult(verses=[], source_themes=[], search_method="fallback")

    async def find_thematic_connections(
        self,
        sura_no: int,
        aya_no: int,
        theme: Optional[ThematicCategory] = None,
        top_k: int = 10,
    ) -> ThematicConnectionResult:
        """Find thematic connections for a verse.

        Used by quran.py for thematic verse connections.
        """
        similarity_service = self._get_similarity_service()
        connections = []
        dominant_themes = []

        if similarity_service is not None:
            try:
                result = await similarity_service.find_similar_verses(
                    sura_no=sura_no,
                    aya_no=aya_no,
                    top_k=top_k,
                    theme_filter=theme.value if theme else None,
                )
                for m in result.matches:
                    connections.append(ThematicConnection(
                        verse_id=m.verse_id,
                        sura_no=m.sura_no,
                        aya_no=m.aya_no,
                        reference=m.reference,
                        text_uthmani=m.text_uthmani,
                        text_imlaei=m.text_imlaei,
                        themes=m.shared_themes,
                        connection_type=m.connection_type.value if hasattr(m.connection_type, 'value') else str(m.connection_type),
                        similarity_score=m.combined_score,
                    ))
                dominant_themes = result.source_themes[:5]
            except Exception as e:
                logger.error(f"Thematic connections error: {e}")

        return ThematicConnectionResult(
            connections=connections,
            dominant_themes=dominant_themes,
        )

    async def get_concept_evolution(
        self,
        concept: str,
        include_related: bool = True,
    ) -> ConceptEvolutionResult:
        """Get evolution of a concept across the Quran.

        Used by quran.py for concept evolution tracking.
        """
        normalized = concept.lower().strip()
        occurrences = []
        related_concepts = []

        if self.session is not None:
            try:
                from sqlalchemy import text
                query = text("""
                    SELECT v.sura_no, v.aya_no, v.text_imlaei, s.name_ar
                    FROM quran_ayah v
                    JOIN quran_surah s ON v.sura_no = s.number
                    WHERE v.text_imlaei LIKE :pattern
                    ORDER BY v.sura_no, v.aya_no
                    LIMIT 100
                """)
                result = await self.session.execute(query, {"pattern": f"%{concept}%"})
                rows = result.fetchall()

                for row in rows:
                    occurrences.append(ConceptOccurrence(
                        sura_no=row[0],
                        aya_no=row[1],
                        reference=f"{row[0]}:{row[1]}",
                        text_snippet=row[2][:200] if row[2] else "",
                        context=row[3] or "",
                        frequency=1,
                    ))
            except Exception as e:
                logger.error(f"Concept evolution query error: {e}")

        if include_related and normalized in SEMANTIC_GLOSSARY:
            for related in SEMANTIC_GLOSSARY[normalized]:
                related_concepts.append({
                    "concept": related,
                    "relationship": "semantic_equivalent",
                })

        occurrences_by_period = {
            "meccan_early": 0,
            "meccan_late": 0,
            "medinan": 0,
        }
        meccan_suras = set(range(1, 87))
        for occ in occurrences:
            if occ.sura_no in meccan_suras:
                if occ.sura_no <= 50:
                    occurrences_by_period["meccan_early"] += 1
                else:
                    occurrences_by_period["meccan_late"] += 1
            else:
                occurrences_by_period["medinan"] += 1

        if occurrences_by_period["meccan_early"] > occurrences_by_period["medinan"]:
            evolution_pattern = "early_emphasis"
        elif occurrences_by_period["medinan"] > occurrences_by_period["meccan_early"]:
            evolution_pattern = "late_emphasis"
        else:
            evolution_pattern = "consistent"

        return ConceptEvolutionResult(
            concept=concept,
            concept_normalized=normalized,
            total_occurrences=len(occurrences),
            occurrences_by_period=occurrences_by_period,
            occurrences=occurrences,
            related_concepts=related_concepts,
            evolution_pattern=evolution_pattern,
        )


_semantic_search: Optional[SemanticSearchService] = None


def get_semantic_search() -> SemanticSearchService:
    """Get semantic search singleton."""
    global _semantic_search
    if _semantic_search is None:
        _semantic_search = SemanticSearchService()
    return _semantic_search


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache."""
    return _embedding_cache


def get_embedding_cache_stats() -> Dict[str, Any]:
    """Get embedding cache statistics."""
    return _embedding_cache.get_stats()


def precompute_embedding(text: str, model=None) -> List[float]:
    """
    Compute or retrieve cached embedding for text.

    Used for precomputing embeddings during cache warming.
    """
    # Check cache first
    cached = _embedding_cache.get(text)
    if cached:
        return cached

    # Compute embedding
    if model is None:
        import torch
        from sentence_transformers import SentenceTransformer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(settings.embedding_model_multilingual, device=device)

    # Normalize Arabic text
    normalized_text = normalize_arabic_text(text)

    # Add E5 query prefix for multilingual-e5 models
    if "e5" in settings.embedding_model_multilingual.lower():
        normalized_text = f"query: {normalized_text}"

    embedding = model.encode(normalized_text, convert_to_numpy=True).tolist()

    # Cache result
    _embedding_cache.set(text, embedding)

    return embedding


async def semantic_vector_search(
    query: str,
    language: str = "en",
    top_k: int = 10,
    source_filter: Optional[List[str]] = None,
    score_threshold: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Perform optimized semantic vector search with caching.

    Args:
        query: Search query
        language: Language filter (ar/en)
        top_k: Number of results
        source_filter: Filter by source IDs
        score_threshold: Minimum similarity score

    Returns:
        List of search results with scores
    """
    import torch
    from sentence_transformers import SentenceTransformer

    # Normalize query
    normalized_query = normalize_arabic_text(query)

    # Check embedding cache
    embedding = _embedding_cache.get(normalized_query)

    if embedding is None:
        # Compute embedding
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(settings.embedding_model_multilingual, device=device)

        # Add E5 query prefix
        if "e5" in settings.embedding_model_multilingual.lower():
            normalized_query = f"query: {normalized_query}"

        embedding = model.encode(normalized_query, convert_to_numpy=True).tolist()

        # Cache embedding
        _embedding_cache.set(query, embedding)

    # Build Qdrant search request
    qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"

    search_params = {
        "hnsw_ef": 128,  # Higher for better recall
    }

    request_body = {
        "vector": embedding,
        "limit": top_k,
        "with_payload": True,
        "with_vector": False,
        "params": search_params,
        "score_threshold": score_threshold,
    }

    # Add filters
    filters = {"must": []}
    if source_filter:
        filters["must"].append({
            "key": "source_id",
            "match": {"any": source_filter}
        })
    if language == "ar":
        filters["must"].append({
            "key": "has_arabic",
            "match": {"value": True}
        })

    if filters["must"]:
        request_body["filter"] = filters

    # Execute search
    results = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{qdrant_url}/collections/tafseer_chunks/points/search",
                json=request_body,
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                for hit in data.get("result", []):
                    payload = hit.get("payload", {})
                    results.append({
                        "chunk_id": str(hit.get("id", "")),
                        "source_id": payload.get("source_id", ""),
                        "score": hit.get("score", 0.0),
                        "verse_reference": payload.get("verse_reference", ""),
                        "content": payload.get("content", ""),
                        "content_ar": payload.get("content_ar", ""),
                        "content_en": payload.get("content_en", ""),
                    })
    except Exception as e:
        logger.error(f"Vector search error: {e}")

    return results
