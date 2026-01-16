"""
Hybrid retrieval combining vector search and keyword search.

LANGUAGE POLICY:
================
This retrieval module ONLY supports Arabic (ar) and English (en) for RAG operations.

- Vector search embeddings are computed for Arabic and English content only
- Keyword search (FTS) operates on Arabic and English tafseer text
- Any other language parameter will be coerced to "en" with a warning

Other languages (Urdu, Indonesian, etc.) are DISPLAY-ONLY and served from
the translations table via separate endpoints, NOT through RAG retrieval.

RETRIEVAL STRATEGY:
===================
1. Parse verse references from query (e.g., "Ayat al-Kursi" -> 2:255)
2. Direct verse lookup if specific verse identified (fastest, most accurate)
3. Vector semantic search for conceptual queries
4. Keyword search as additional signal
5. External API fallback if local results insufficient
"""
import re
import logging
from typing import List, Optional, Tuple

import httpx
from sqlalchemy import select, or_, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tafseer import TafseerChunk, TafseerSource
from app.rag.types import QueryIntent, RetrievedChunk, RAG_SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Famous verse name mappings to verse references
# Note: Arabic names have multiple variations due to Unicode normalization issues
FAMOUS_VERSES = {
    # ===== AYAT AL-KURSI (2:255) - Throne Verse =====
    # English variations
    "ayat al-kursi": (2, 255),
    "ayatul kursi": (2, 255),
    "ayat al kursi": (2, 255),
    "ayat-ul-kursi": (2, 255),
    "aayat al kursi": (2, 255),
    "throne verse": (2, 255),
    "verse of the throne": (2, 255),
    "kursi verse": (2, 255),
    "greatest verse": (2, 255),
    # Arabic variations (with/without diacritics, different alif forms)
    "آية الكرسي": (2, 255),
    "اية الكرسي": (2, 255),  # Without hamza on alif
    "آيه الكرسي": (2, 255),  # With taa marbuta as haa
    "ايه الكرسي": (2, 255),
    "الكرسي": (2, 255),  # Just "the throne"
    "كرسي": (2, 255),  # Just "throne"

    # ===== AL-FATIHA (1:1-7) - The Opening =====
    "al-fatiha": (1, 1, 7),
    "fatiha": (1, 1, 7),
    "alfatiha": (1, 1, 7),
    "opening chapter": (1, 1, 7),
    "the opening": (1, 1, 7),
    "mother of the book": (1, 1, 7),
    "umm al-kitab": (1, 1, 7),
    "الفاتحة": (1, 1, 7),
    "فاتحة": (1, 1, 7),
    "سورة الفاتحة": (1, 1, 7),
    "ام الكتاب": (1, 1, 7),
    "أم الكتاب": (1, 1, 7),

    # ===== AL-IKHLAS (112:1-4) - Sincerity =====
    "surah ikhlas": (112, 1, 4),
    "al-ikhlas": (112, 1, 4),
    "ikhlas": (112, 1, 4),
    "sincerity": (112, 1, 4),
    "surah tawhid": (112, 1, 4),
    "qul huwa allahu ahad": (112, 1, 4),
    "الإخلاص": (112, 1, 4),
    "الاخلاص": (112, 1, 4),  # Without hamza
    "سورة الإخلاص": (112, 1, 4),
    "سورة الاخلاص": (112, 1, 4),
    "قل هو الله أحد": (112, 1, 4),
    "قل هو الله احد": (112, 1, 4),

    # ===== AL-FALAQ (113:1-5) - The Daybreak =====
    "surah falaq": (113, 1, 5),
    "al-falaq": (113, 1, 5),
    "falaq": (113, 1, 5),
    "daybreak": (113, 1, 5),
    "the dawn": (113, 1, 5),
    "الفلق": (113, 1, 5),
    "سورة الفلق": (113, 1, 5),

    # ===== AN-NAS (114:1-6) - Mankind =====
    "surah nas": (114, 1, 6),
    "al-nas": (114, 1, 6),
    "an-nas": (114, 1, 6),
    "nas": (114, 1, 6),
    "mankind": (114, 1, 6),
    "الناس": (114, 1, 6),
    "سورة الناس": (114, 1, 6),

    # ===== AYAT AN-NUR (24:35) - Light Verse =====
    "light verse": (24, 35),
    "ayat an-nur": (24, 35),
    "ayat al-nur": (24, 35),
    "verse of light": (24, 35),
    "noor verse": (24, 35),
    "آية النور": (24, 35),
    "اية النور": (24, 35),
    "النور": (24, 35),

    # ===== AL-BAQARAH 2:286 - End of Baqarah =====
    "last verse of baqarah": (2, 286),
    "end of baqarah": (2, 285, 286),
    "آخر البقرة": (2, 285, 286),

    # ===== AYAT AL-MULK (67:1-30) - The Sovereignty =====
    "surah mulk": (67, 1, 30),
    "al-mulk": (67, 1, 30),
    "tabarak": (67, 1, 30),
    "the sovereignty": (67, 1, 30),
    "الملك": (67, 1, 30),
    "سورة الملك": (67, 1, 30),
    "تبارك": (67, 1, 30),

    # ===== SURAH YASIN (36:1-83) =====
    "surah yasin": (36, 1, 83),
    "yaseen": (36, 1, 83),
    "ya sin": (36, 1, 83),
    "يس": (36, 1, 83),
    "سورة يس": (36, 1, 83),
    "يسين": (36, 1, 83),

    # ===== SURAH AL-KAHF (18:1-110) - The Cave =====
    "surah kahf": (18, 1, 110),
    "al-kahf": (18, 1, 110),
    "the cave": (18, 1, 110),
    "الكهف": (18, 1, 110),
    "سورة الكهف": (18, 1, 110),

    # ===== SURAH AR-RAHMAN (55:1-78) =====
    "surah rahman": (55, 1, 78),
    "ar-rahman": (55, 1, 78),
    "the merciful": (55, 1, 78),
    "الرحمن": (55, 1, 78),
    "سورة الرحمن": (55, 1, 78),

    # ===== SURAH AL-WAQIAH (56:1-96) - The Event =====
    "surah waqiah": (56, 1, 96),
    "al-waqiah": (56, 1, 96),
    "the event": (56, 1, 96),
    "الواقعة": (56, 1, 96),
    "سورة الواقعة": (56, 1, 96),
}


# Islamic terminology expansion glossary
TERM_GLOSSARY = {
    # English to Arabic equivalents
    "patience": ["sabr", "صبر"],
    "trust": ["tawakkul", "توكل"],
    "faith": ["iman", "إيمان"],
    "prayer": ["salah", "salat", "صلاة"],
    "fasting": ["sawm", "siyam", "صوم", "صيام"],
    "charity": ["zakat", "sadaqah", "زكاة", "صدقة"],
    "pilgrimage": ["hajj", "حج"],
    "god": ["allah", "الله"],
    "messenger": ["rasul", "رسول"],
    "prophet": ["nabi", "نبي"],
    "angels": ["malaika", "ملائكة"],
    "heaven": ["jannah", "جنة"],
    "hell": ["jahannam", "نار", "جهنم"],
    "quran": ["qur'an", "القرآن"],
    "verse": ["ayah", "آية"],
    "chapter": ["surah", "سورة"],
    # Arabic to English
    "صبر": ["patience", "sabr"],
    "توكل": ["trust", "reliance", "tawakkul"],
    "إيمان": ["faith", "belief", "iman"],
}


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for matching.
    Removes diacritics and normalizes alif variants.
    """
    import unicodedata
    # Normalize to NFD (decomposed form)
    text = unicodedata.normalize('NFD', text)
    # Remove Arabic diacritics (tashkeel)
    diacritics = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065A\u065B\u065C\u065D\u065E\u065F'
    text = ''.join(c for c in text if c not in diacritics)
    # Normalize back to NFC (composed form)
    text = unicodedata.normalize('NFC', text)
    # Normalize alif variants
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ٱ', 'ا')
    # Normalize taa marbuta and haa
    text = text.replace('ة', 'ه')
    # Normalize yaa variants
    text = text.replace('ى', 'ي').replace('ئ', 'ي')
    return text


def extract_verse_reference(query: str) -> Optional[Tuple[int, int, Optional[int]]]:
    """
    Extract verse reference from a query.

    Returns:
        Tuple of (sura_no, aya_start, aya_end) or None if no reference found.
        aya_end is None for single verse references.

    Examples:
        "What is the meaning of 2:255?" -> (2, 255, None)
        "Explain Ayat al-Kursi" -> (2, 255, None)
        "Tell me about Surah Fatiha" -> (1, 1, 7)
        "ما معنى آية الكرسي؟" -> (2, 255, None)
    """
    query_lower = query.lower()
    query_normalized = normalize_arabic(query)

    # 1. Check famous verse names first (with normalization)
    for name, ref in FAMOUS_VERSES.items():
        # Check in original query (lowercased for English)
        if name.lower() in query_lower:
            if len(ref) == 2:
                return (ref[0], ref[1], None)
            else:
                return (ref[0], ref[1], ref[2])

        # Check in normalized query (for Arabic)
        name_normalized = normalize_arabic(name)
        if name_normalized in query_normalized:
            if len(ref) == 2:
                return (ref[0], ref[1], None)
            else:
                return (ref[0], ref[1], ref[2])

    # 2. Check for explicit verse reference patterns
    # Pattern: X:Y or X:Y-Z (with various separators)
    patterns = [
        r'\b(\d{1,3})\s*[:：]\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\b',  # 2:255 or 2:255-260
        r'\bsurah?\s+(\d{1,3})\s*(?:verse|ayah?|aya)?\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\b',  # surah 2 verse 255
        r'\b(\d{1,3})\s*[,،]\s*(\d{1,3})\b',  # 2,255 or 2،255 (Arabic comma)
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            sura = int(match.group(1))
            aya_start = int(match.group(2))
            aya_end = int(match.group(3)) if match.group(3) else None

            # Validate sura number
            if 1 <= sura <= 114:
                return (sura, aya_start, aya_end)

    return None


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. Direct verse lookup (for specific verse queries)
    2. Vector search in Qdrant (semantic matching)
    3. Keyword search in PostgreSQL (FTS)
    4. Reciprocal Rank Fusion for merging results
    5. External API fallback (alquran.cloud)

    SAFETY: Only retrieves from ENABLED sources (is_enabled=True).
    """

    # Safety limits for evidence content
    MAX_CHUNK_CONTENT_LENGTH = 2000  # Max chars per chunk for display
    MAX_CHUNKS_IN_RESPONSE = 8  # Max evidence chunks to return

    def __init__(self, session: AsyncSession):
        self.session = session
        # Use HTTP API directly to avoid qdrant-client version issues
        self.qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"
        self.embedding_model = None  # Lazy-loaded
        self._enabled_sources_cache: set = None  # Cache enabled source IDs
        self._tafseer_client = None  # Lazy-loaded external API client

    async def _get_enabled_source_ids(self) -> set:
        """
        Get set of enabled source IDs from the database.
        Cached per retriever instance to avoid repeated queries.
        """
        if self._enabled_sources_cache is not None:
            return self._enabled_sources_cache

        result = await self.session.execute(
            select(TafseerSource.id).where(TafseerSource.is_enabled == 1)
        )
        self._enabled_sources_cache = {row[0] for row in result.fetchall()}
        logger.info(f"Cached {len(self._enabled_sources_cache)} enabled sources")
        return self._enabled_sources_cache

    def _truncate_content(self, content: str, max_length: int = None) -> str:
        """Truncate content to max length with ellipsis if needed."""
        if max_length is None:
            max_length = self.MAX_CHUNK_CONTENT_LENGTH
        if content and len(content) > max_length:
            return content[:max_length - 3] + "..."
        return content or ""

    async def retrieve(
        self,
        query: str,
        language: str = "en",
        intent: QueryIntent = QueryIntent.VERSE_MEANING,
        preferred_sources: List[str] = None,
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks using hybrid search.

        Args:
            query: The search query
            language: Response language (ar/en ONLY - see LANGUAGE POLICY)
            intent: Query intent for filtering
            preferred_sources: List of preferred tafseer source IDs
            top_k: Maximum number of chunks to return

        Returns:
            List of RetrievedChunk objects with tafseer content

        Note:
            Language MUST be 'ar' or 'en'. Other languages are display-only
            and served from the translations table, not RAG retrieval.
        """
        # Validate and coerce language to RAG-supported language
        if language not in RAG_SUPPORTED_LANGUAGES:
            logger.warning(
                f"Language '{language}' not supported for RAG retrieval. "
                f"Coercing to 'en'. Supported: {RAG_SUPPORTED_LANGUAGES}"
            )
            language = "en"

        # 0. FIRST: Check for specific verse reference in query
        verse_ref = extract_verse_reference(query)
        direct_results = []

        if verse_ref:
            sura_no, aya_start, aya_end = verse_ref
            print(f"[RETRIEVAL] Detected verse reference: {sura_no}:{aya_start}{f'-{aya_end}' if aya_end else ''}")

            # Direct database lookup - fastest and most accurate
            direct_results = await self._direct_verse_lookup(
                sura_no=sura_no,
                aya_start=aya_start,
                aya_end=aya_end,
                language=language,
                preferred_sources=preferred_sources,
            )
            print(f"[RETRIEVAL] Direct verse lookup returned: {len(direct_results)} results")

            # If we found good results, prioritize them
            if len(direct_results) >= 3:
                # We have sufficient direct results, use them as primary
                # Still do a quick semantic search to add related context
                pass

        # 1. Expand query with Islamic terminology
        expanded_terms = self._expand_query(query)
        expanded_query = query + " " + " ".join(expanded_terms)
        print(f"[RETRIEVAL] Query: {query[:50]}..., Expanded terms: {expanded_terms}")

        # 2. Vector search (unless we have enough direct results)
        vector_results = []
        if len(direct_results) < top_k:
            vector_results = await self._vector_search(
                query=expanded_query,
                language=language,
                preferred_sources=preferred_sources,
                top_k=top_k,
            )
            print(f"[RETRIEVAL] Vector search returned: {len(vector_results)} results")

        # 3. Keyword search
        keyword_results = await self._keyword_search(
            query=query,
            expanded_terms=expanded_terms,
            language=language,
            preferred_sources=preferred_sources,
            top_k=top_k,
        )
        print(f"[RETRIEVAL] Keyword search returned: {len(keyword_results)} results")

        # 4. Merge results with RRF (direct results get highest priority)
        # Boost direct results by adding them with high scores
        boosted_direct = []
        for i, chunk in enumerate(direct_results):
            chunk.relevance_score = 0.95 - (i * 0.02)  # High scores: 0.95, 0.93, 0.91...
            boosted_direct.append(chunk)

        merged = self._reciprocal_rank_fusion(
            boosted_direct + vector_results,
            keyword_results,
            k=60,  # RRF constant
        )
        print(f"[RETRIEVAL] Merged results: {len(merged)}, returning top {top_k}")

        # 5. Rerank with cross-encoder for better relevance
        max_results = min(top_k, self.MAX_CHUNKS_IN_RESPONSE)
        reranked_results, rerank_info = self._rerank_results(query, merged, max_results)
        print(f"[RETRIEVAL] Reranked with method: {rerank_info.method}")

        # 6. If results are insufficient, try external API fallback
        if len(reranked_results) < 3 and verse_ref and settings.feature_external_tafseer:
            print(f"[RETRIEVAL] Insufficient results, trying external API fallback...")
            external_results = await self._external_api_fallback(
                sura_no=verse_ref[0],
                aya_no=verse_ref[1],
                language=language,
            )
            # Add external results with moderate relevance
            for chunk in external_results:
                chunk.relevance_score = 0.75
            reranked_results.extend(external_results)
            print(f"[RETRIEVAL] Added {len(external_results)} results from external API")

        # 7. Truncate content for safety (prevent huge payloads)
        for chunk in reranked_results:
            chunk.content = self._truncate_content(chunk.content)
            if chunk.content_ar:
                chunk.content_ar = self._truncate_content(chunk.content_ar)
            if chunk.content_en:
                chunk.content_en = self._truncate_content(chunk.content_en)

        return reranked_results

    async def _direct_verse_lookup(
        self,
        sura_no: int,
        aya_start: int,
        aya_end: Optional[int],
        language: str,
        preferred_sources: List[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Direct database lookup for tafseer of a specific verse.

        This is the fastest and most accurate method for verse-specific queries.
        """
        try:
            # Get enabled sources for filtering
            enabled_sources = await self._get_enabled_source_ids()
            if not enabled_sources:
                return []

            # Build query for exact verse match
            if aya_end:
                # Range query
                conditions = [
                    TafseerChunk.sura_no == sura_no,
                    TafseerChunk.aya_start <= aya_end,
                    TafseerChunk.aya_end >= aya_start,
                ]
            else:
                # Single verse
                conditions = [
                    TafseerChunk.sura_no == sura_no,
                    TafseerChunk.aya_start <= aya_start,
                    TafseerChunk.aya_end >= aya_start,
                ]

            stmt = (
                select(TafseerChunk, TafseerSource)
                .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
                .where(and_(*conditions))
                .where(TafseerSource.is_enabled == 1)
            )

            # Filter by preferred sources if specified
            if preferred_sources:
                valid_sources = [s for s in preferred_sources if s in enabled_sources]
                if valid_sources:
                    stmt = stmt.where(TafseerChunk.source_id.in_(valid_sources))

            # Order by reliability and whether content matches language
            stmt = stmt.order_by(TafseerSource.reliability_score.desc())
            stmt = stmt.limit(10)

            result = await self.session.execute(stmt)
            rows = result.all()

            chunks = []
            for chunk, source in rows:
                # Determine content based on language preference
                content = chunk.content_en if language == "en" else chunk.content_ar
                if not content:
                    content = chunk.content_ar or chunk.content_en or ""

                # Skip empty content
                if not content or len(content.strip()) < 20:
                    continue

                verse_ref = f"{chunk.sura_no}:{chunk.aya_start}"
                if chunk.aya_end and chunk.aya_end != chunk.aya_start:
                    verse_ref = f"{chunk.sura_no}:{chunk.aya_start}-{chunk.aya_end}"

                chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk.chunk_id,
                        source_id=chunk.source_id,
                        source_name=source.name_en,
                        source_name_ar=source.name_ar,
                        verse_reference=verse_ref,
                        sura_no=chunk.sura_no,
                        aya_start=chunk.aya_start,
                        aya_end=chunk.aya_end,
                        content=content,
                        content_ar=chunk.content_ar,
                        content_en=chunk.content_en,
                        relevance_score=0.95,  # High score for direct match
                        scholarly_consensus=chunk.scholarly_consensus,
                    )
                )

            return chunks

        except Exception as e:
            logger.error(f"Direct verse lookup error: {e}")
            return []

    async def _external_api_fallback(
        self,
        sura_no: int,
        aya_no: int,
        language: str,
    ) -> List[RetrievedChunk]:
        """
        Fallback to external alquran.cloud API when local results are insufficient.
        """
        try:
            # Lazy-load the tafseer client
            if self._tafseer_client is None:
                from app.services.tafseer_api import get_tafseer_client
                self._tafseer_client = get_tafseer_client()

            # Get tafseer from external API
            editions = ["ar.muyassar", "en.sahih"] if language == "en" else ["ar.muyassar"]
            response = await self._tafseer_client.get_tafseer(sura_no, aya_no, editions)

            if not response.success:
                return []

            chunks = []
            for tafseer in response.tafasir:
                metadata = self._tafseer_client.get_edition_metadata(tafseer.edition)

                content_ar = tafseer.text if tafseer.language == "ar" else None
                content_en = tafseer.text if tafseer.language == "en" else None

                chunks.append(
                    RetrievedChunk(
                        chunk_id=f"external_{tafseer.edition}_{sura_no}_{aya_no}",
                        source_id=f"alquran_cloud_{tafseer.edition}",
                        source_name=metadata.get("name_en", tafseer.edition_name),
                        source_name_ar=metadata.get("name_ar", tafseer.edition_name),
                        verse_reference=f"{sura_no}:{aya_no}",
                        sura_no=sura_no,
                        aya_start=aya_no,
                        aya_end=aya_no,
                        content=tafseer.text,
                        content_ar=content_ar,
                        content_en=content_en,
                        relevance_score=0.75,  # Moderate score for external
                        scholarly_consensus=None,
                    )
                )

            return chunks

        except Exception as e:
            logger.error(f"External API fallback error: {e}")
            return []

    def _rerank_results(self, query: str, chunks: List[RetrievedChunk], top_k: int):
        """
        Rerank retrieved chunks using cross-encoder or fallback.

        Uses cross-encoder model for more accurate relevance scoring,
        falls back to keyword overlap if model unavailable.
        """
        from app.rag.reranker import rerank_chunks, RERANKER_CONFIG

        if not RERANKER_CONFIG.get("enabled", True):
            # Reranking disabled, just return top_k
            from app.rag.reranker import RerankResult
            return chunks[:top_k], RerankResult(reranked=False, method="none", scores=[])

        return rerank_chunks(
            query=query,
            chunks=chunks,
            top_k=top_k,
            use_cross_encoder=RERANKER_CONFIG.get("use_cross_encoder", True),
        )

    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with Islamic terminology equivalents.
        """
        expanded = []
        query_lower = query.lower()

        for term, equivalents in TERM_GLOSSARY.items():
            if term.lower() in query_lower:
                expanded.extend(equivalents)

        return list(set(expanded))

    def _get_embedding_model(self):
        """Lazy-load the embedding model."""
        if self.embedding_model is None:
            import os
            import torch
            from sentence_transformers import SentenceTransformer

            # Use GPU if available, otherwise CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            # Allow override via environment variable
            device = os.environ.get("EMBEDDING_DEVICE", device)

            logger.info(f"Loading embedding model on device: {device}")
            self.embedding_model = SentenceTransformer(
                settings.embedding_model_multilingual,
                device=device,
            )
        return self.embedding_model

    async def _vector_search(
        self,
        query: str,
        language: str,
        preferred_sources: List[str],
        top_k: int,
    ) -> List[RetrievedChunk]:
        """
        Search using vector embeddings in Qdrant via HTTP API.

        SAFETY: Filters results to only include ENABLED sources.
        """
        try:
            # Get enabled sources for filtering
            enabled_sources = await self._get_enabled_source_ids()
            if not enabled_sources:
                logger.warning("No enabled sources found - returning empty results")
                return []

            # Generate query embedding
            model = self._get_embedding_model()
            # E5 models need "query: " prefix for queries
            query_text = f"query: {query}"
            query_vector = model.encode(query_text).tolist()

            # Build search request - fetch extra to account for filtering
            search_body = {
                "vector": query_vector,
                "limit": top_k * 2,  # Fetch extra to account for disabled source filtering
                "with_payload": True,
            }

            # Add filter if preferred sources specified (intersect with enabled)
            if preferred_sources:
                # Only include preferred sources that are also enabled
                valid_sources = [s for s in preferred_sources if s in enabled_sources]
                if not valid_sources:
                    logger.warning("None of the preferred sources are enabled")
                    return []
                search_body["filter"] = {
                    "must": [
                        {
                            "key": "source_id",
                            "match": {"any": valid_sources},
                        }
                    ]
                }

            # Execute search via HTTP
            logger.info(f"Vector search: querying Qdrant with {len(query_vector)} dim vector")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/{settings.qdrant_collection_tafseer}/points/search",
                    json=search_body,
                )
                response.raise_for_status()
                data = response.json()

            if data.get("status") != "ok":
                logger.warning(f"Qdrant search failed: {data}")
                return []

            logger.info(f"Vector search returned {len(data.get('result', []))} results")

            # Parse results and filter by enabled sources
            chunks = []
            filtered_count = 0
            for result in data.get("result", []):
                payload = result.get("payload", {})
                source_id = payload.get("source_id", "")

                # SAFETY: Skip results from disabled sources
                if source_id not in enabled_sources:
                    filtered_count += 1
                    continue

                score = result.get("score", 0.0)
                if len(chunks) < 3:  # Log first 3 scores
                    print(f"[VECTOR] Raw Qdrant score: {score}")

                chunks.append(
                    RetrievedChunk(
                        chunk_id=payload.get("chunk_id", ""),
                        source_id=source_id,
                        source_name=payload.get("source_name", ""),
                        source_name_ar=payload.get("source_name_ar", ""),
                        verse_reference=payload.get("verse_reference", ""),
                        sura_no=payload.get("sura_no", 0),
                        aya_start=payload.get("aya_start", 0),
                        aya_end=payload.get("aya_end", 0),
                        content=payload.get(f"content_{language}", ""),
                        content_ar=payload.get("content_ar"),
                        content_en=payload.get("content_en"),
                        relevance_score=result.get("score", 0.0),
                        scholarly_consensus=payload.get("scholarly_consensus"),
                    )
                )

                # Stop once we have enough results
                if len(chunks) >= top_k:
                    break

            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} results from disabled sources")

            return chunks

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def _keyword_search(
        self,
        query: str,
        expanded_terms: List[str],
        language: str,
        preferred_sources: List[str],
        top_k: int,
    ) -> List[RetrievedChunk]:
        """
        Search using PostgreSQL keyword matching.

        SAFETY: Only searches ENABLED sources.
        """
        # Extract meaningful keywords from query (filter out common words)
        stop_words = {
            'عن', 'في', 'من', 'إلى', 'على', 'ما', 'هل', 'كيف', 'ماذا', 'لماذا',
            'أخبرني', 'حدثني', 'اشرح', 'وضح', 'قصة', 'قصص',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why',
            'tell', 'me', 'about', 'explain', 'story', 'of'
        }

        # Split query into words and filter
        words = query.replace('؟', '').replace('?', '').split()
        keywords = [w for w in words if w.lower() not in stop_words and len(w) > 2]

        # Add expanded terms
        all_keywords = keywords + expanded_terms

        if not all_keywords:
            logger.warning(f"No keywords extracted from query: {query}")
            return []

        logger.info(f"Keyword search with terms: {all_keywords}")

        # Build query - search for each keyword with OR
        content_column = TafseerChunk.content_en if language == "en" else TafseerChunk.content_ar

        # Build OR conditions for each keyword
        conditions = []
        for keyword in all_keywords:
            conditions.append(content_column.ilike(f"%{keyword}%"))

        stmt = (
            select(TafseerChunk, TafseerSource)
            .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
            .where(or_(*conditions))
            # SAFETY: Only include enabled sources (is_enabled is INTEGER: 1=enabled, 0=disabled)
            .where(TafseerSource.is_enabled == 1)
        )

        if preferred_sources:
            stmt = stmt.where(TafseerChunk.source_id.in_(preferred_sources))

        stmt = stmt.limit(top_k)

        result = await self.session.execute(stmt)
        rows = result.all()

        chunks = []
        for chunk, source in rows:
            content = chunk.content_en if language == "en" else chunk.content_ar
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    source_name=source.name_en,
                    source_name_ar=source.name_ar,
                    verse_reference=chunk.verse_reference,
                    sura_no=chunk.sura_no,
                    aya_start=chunk.aya_start,
                    aya_end=chunk.aya_end,
                    content=content or "",
                    content_ar=chunk.content_ar,
                    content_en=chunk.content_en,
                    relevance_score=0.5,  # Base score for keyword matches
                    scholarly_consensus=chunk.scholarly_consensus,
                )
            )

        return chunks

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[RetrievedChunk],
        keyword_results: List[RetrievedChunk],
        k: int = 60,
    ) -> List[RetrievedChunk]:
        """
        Merge results using Reciprocal Rank Fusion.

        RRF score = sum(1 / (k + rank)) for each list where document appears
        """
        chunk_scores = {}
        chunk_map = {}
        original_scores = {}  # Keep track of original vector search scores

        # Score vector results
        for rank, chunk in enumerate(vector_results, start=1):
            chunk_id = chunk.chunk_id
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + 1 / (k + rank)
            chunk_map[chunk_id] = chunk
            # Keep original vector score if higher
            if chunk_id not in original_scores:
                original_scores[chunk_id] = chunk.relevance_score
            else:
                original_scores[chunk_id] = max(original_scores[chunk_id], chunk.relevance_score)

        # Score keyword results
        for rank, chunk in enumerate(keyword_results, start=1):
            chunk_id = chunk.chunk_id
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0) + 1 / (k + rank)
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = chunk
            # Keep original keyword score if higher
            if chunk_id not in original_scores:
                original_scores[chunk_id] = chunk.relevance_score
            else:
                original_scores[chunk_id] = max(original_scores[chunk_id], chunk.relevance_score)

        # Sort by RRF score
        sorted_ids = sorted(chunk_scores.keys(), key=lambda x: chunk_scores[x], reverse=True)

        # Calculate max RRF score for normalization
        # Max possible = 1/(k+1) + 1/(k+1) = 2/(k+1) if doc appears at rank 1 in both lists
        max_rrf = 2 / (k + 1)

        # Update relevance scores and return
        result = []
        for chunk_id in sorted_ids:
            chunk = chunk_map[chunk_id]
            # Normalize RRF score to 0-1 range, then blend with original score
            rrf_normalized = min(chunk_scores[chunk_id] / max_rrf, 1.0)
            original_score = original_scores.get(chunk_id, 0.5)
            # Use max of normalized RRF and original score, but boost if in both lists
            in_both_lists = chunk_scores[chunk_id] > 1 / (k + 1)  # More than single list contribution
            if in_both_lists:
                # Boost score for appearing in both lists
                chunk.relevance_score = min((rrf_normalized + original_score) / 2 + 0.3, 1.0)
            else:
                # Use max of the two
                chunk.relevance_score = max(rrf_normalized, original_score)
            result.append(chunk)

        return result
