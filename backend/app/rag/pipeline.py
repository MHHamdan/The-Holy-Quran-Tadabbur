"""
RAG Pipeline for grounded Quranic Q&A.

CRITICAL SAFETY RULES:
1. NEVER invent tafseer - LLM may ONLY summarize retrieved evidence
2. Every paragraph MUST include at least one citation
3. Citations MUST be validated against retrieved chunks
4. If evidence is insufficient, return safe refusal
5. For fiqh/rulings: informational summary only, no fatwa language

LANGUAGE POLICY:
================
RAG reasoning is ONLY performed in Arabic (ar) and English (en):
- Semantic search embeddings exist only for ar/en tafseer content
- LLM synthesis uses ar/en source material

Other languages (Urdu, Indonesian, etc.) are DISPLAY-ONLY:
- Verse translations come from the translations table
- NO tafseer retrieval or RAG reasoning in these languages
- Use the /translations endpoint for display languages

RAG SCOPE FREEZE (PROHIBITED BEHAVIORS)
=======================================
This pipeline MUST NOT be extended to:

1. GENERATE explanations beyond retrieved evidence
   - No "creative" interpretation
   - No inference beyond what sources explicitly state
   - No filling gaps with general knowledge

2. TRANSLATE tafseer dynamically
   - No LLM-based translation of Arabic tafseer to English
   - No translating answers to display-only languages
   - Translations must come from pre-verified translated sources only

3. REASON over display-only languages
   - No RAG retrieval in Urdu, Indonesian, Turkish, etc.
   - No embedding search in non-AR/EN content
   - Display-only languages are served from translations table ONLY

4. PROVIDE religious rulings (fatwa)
   - Fiqh content is INFORMATIONAL only
   - Must include disclaimer to consult scholars
   - No personalized religious advice

5. SYNTHESIZE across conflicting sources without disclosure
   - Must indicate when scholars disagree
   - Must not present disputed views as consensus

Any modification to these rules requires:
- Update to this docstring
- Update to app/core/acceptance.py
- Full test suite re-run
- Security review
"""
import re
import time
import logging
from typing import List, Optional, Dict
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.rag.types import (
    QueryIntent,
    RetrievedChunk,
    Citation,
    GroundedResponse,
    RelatedVerse,
    TafsirExplanation,
    SAFE_REFUSAL_INSUFFICIENT,
    SAFE_REFUSAL_NO_SOURCES,
    SAFE_REFUSAL_FIQH,
    RAG_SUPPORTED_LANGUAGES,
)
from app.rag.retrieval import HybridRetriever, extract_verse_reference, FAMOUS_VERSES
from app.rag.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from app.rag.query_expander import expand_query, ExpandedQuery
from app.rag.confidence import confidence_scorer, get_confidence_message, ConfidenceBreakdown
from app.validators.citation_validator import CitationValidator
from app.rag.llm_provider import get_llm, LLMProvider, BaseLLM

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG pipeline for grounded Quranic Q&A.

    Flow:
    1. Classify query intent
    2. Expand query with Islamic terminology
    3. Retrieve relevant chunks (vector + keyword)
    4. Build grounded context
    5. Generate response with strict grounding rules
    6. Validate all citations
    7. Return response with citations or safe refusal
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider = None,
    ):
        self.session = session
        self.retriever = HybridRetriever(session)
        self.validator = CitationValidator(session)

        # Initialize LLM provider (defaults to configured provider)
        if llm_provider is None:
            llm_provider = LLMProvider(settings.llm_provider)

        try:
            # Use fast model for RAG if configured
            ollama_model = None
            if llm_provider == LLMProvider.OLLAMA and settings.ollama_rag_use_fast_model:
                ollama_model = settings.ollama_model_fast
                logger.info(f"RAG Pipeline using fast model: {ollama_model}")

            self.llm = get_llm(provider=llm_provider, ollama_model=ollama_model)
            self.llm_provider = llm_provider
            self.max_tokens = settings.ollama_rag_max_tokens  # Use RAG-specific token limit
            logger.info(f"RAG Pipeline initialized with {llm_provider.value} provider (max_tokens={self.max_tokens})")
        except Exception as e:
            logger.warning(f"Failed to initialize {llm_provider}: {e}")
            self.llm = None
            self.llm_provider = None
            self.max_tokens = 1500  # Default

    async def _try_fast_path_verse_query(
        self,
        question: str,
        language: str,
        preferred_sources: List[str] = None,
        session_id: Optional[str] = None,
    ) -> Optional[GroundedResponse]:
        """
        Fast-path for direct verse queries (e.g., "ما معنى آية الكرسي؟").

        Skips LLM entirely and returns tafsir directly from database.
        This is MUCH faster and avoids hallucination for known verses.

        Returns:
            GroundedResponse if fast-path applicable, None otherwise
        """
        import time
        start_time = time.time()

        # Check if query mentions a famous verse
        verse_ref = extract_verse_reference(question)
        if not verse_ref:
            return None

        sura_no, aya_start, aya_end = verse_ref
        logger.info(f"[FAST-PATH] Detected verse {sura_no}:{aya_start}, attempting fast-path")

        # Direct database lookup
        chunks = await self.retriever._direct_verse_lookup(
            sura_no=sura_no,
            aya_start=aya_start,
            aya_end=aya_end,
            language=language,
            preferred_sources=preferred_sources,
        )

        if not chunks or len(chunks) < 2:
            # Not enough direct results, fall back to full pipeline
            logger.info(f"[FAST-PATH] Only {len(chunks)} chunks, falling back to full pipeline")
            return None

        logger.info(f"[FAST-PATH] Found {len(chunks)} tafsir chunks, building response")

        # Build verse reference string
        verse_ref_str = f"{sura_no}:{aya_start}"
        if aya_end and aya_end != aya_start:
            verse_ref_str = f"{sura_no}:{aya_start}-{aya_end}"

        # Get verse text from database
        related_verses = await self._extract_related_verses(chunks, language)

        # Group tafsir by source
        tafsir_by_source = self._group_tafsir_by_source(chunks, language)

        # Build answer summary from tafsir (no LLM needed)
        answer_parts = []

        # Get verse name if known
        verse_name = None
        for name, ref in FAMOUS_VERSES.items():
            if isinstance(ref, tuple) and len(ref) >= 2:
                if ref[0] == sura_no and ref[1] == aya_start:
                    # Prefer Arabic name for Arabic responses
                    if language == "ar" and any(ord(c) > 0x600 for c in name):
                        verse_name = name
                        break
                    elif language == "en" and not any(ord(c) > 0x600 for c in name):
                        verse_name = name
                        break

        if language == "ar":
            if verse_name:
                answer_parts.append(f"**{verse_name}** هي الآية {aya_start} من سورة البقرة.")
            answer_parts.append(f"\nفيما يلي شروحات العلماء لهذه الآية الكريمة من مصادر التفسير المعتمدة:")
            answer_parts.append(f"\n\n**عدد المصادر المتوفرة:** {len(tafsir_by_source)} تفسير")
        else:
            if verse_name:
                answer_parts.append(f"**{verse_name.replace('-', ' ').title()}** is verse {aya_start} of Surah Al-Baqarah.")
            answer_parts.append(f"\nBelow are scholarly explanations of this noble verse from authentic tafsir sources:")
            answer_parts.append(f"\n\n**Available sources:** {len(tafsir_by_source)} tafsir")

        answer = "".join(answer_parts)

        # Build citations from chunks
        citations = []
        for chunk in chunks[:5]:
            citations.append(Citation(
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                source_name=chunk.source_name,
                source_name_ar=chunk.source_name_ar,
                verse_reference=chunk.verse_reference,
                excerpt=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                relevance_score=chunk.relevance_score,
            ))

        # Generate follow-up suggestions
        follow_ups = []
        if language == "ar":
            follow_ups = [
                f"ما فضل {verse_name or 'هذه الآية'}؟",
                f"ما معنى الحي القيوم؟",
                f"ما هو الكرسي في القرآن؟",
            ]
        else:
            follow_ups = [
                f"What are the virtues of {verse_name or 'this verse'}?",
                "What does Al-Hayy Al-Qayyum mean?",
                "What is the Kursi (Throne) in the Quran?",
            ]

        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"[FAST-PATH] Response built in {processing_time}ms")

        return GroundedResponse(
            answer=answer,
            citations=citations,
            confidence=0.95,  # High confidence for direct lookup
            intent=QueryIntent.VERSE_MEANING.value,
            warnings=[],
            query_expansion=None,
            session_id=session_id,
            related_verses=related_verses,
            tafsir_by_source=tafsir_by_source,
            follow_up_suggestions=follow_ups,
            scholarly_consensus="Direct tafsir lookup - no synthesis required",
            evidence_chunk_count=len(chunks),
            evidence_source_count=len(tafsir_by_source),
            evidence=chunks[:5],  # Include top chunks for transparency
            processing_time_ms=processing_time,
            api_version=settings.api_version,
        )

    async def query(
        self,
        question: str,
        language: str = "en",
        include_scholarly_debate: bool = True,
        preferred_sources: List[str] = None,
        max_sources: int = 5,
        session_id: Optional[str] = None,
        conversation_context: Optional[str] = None,
    ) -> GroundedResponse:
        """
        Process a question and return a grounded response.

        Args:
            question: The user's question
            language: Response language (ar/en ONLY - see LANGUAGE POLICY)
            include_scholarly_debate: Include differing scholarly views
            preferred_sources: List of preferred tafseer source IDs
            max_sources: Maximum number of sources to retrieve
            session_id: Optional session ID for conversation continuity
            conversation_context: Optional context from previous conversation turns

        Returns:
            GroundedResponse with answer, citations, verses, tafsir_by_source, and metadata

        Note:
            RAG reasoning is only supported in Arabic (ar) and English (en).
            Other languages will be coerced to English. For display-only
            translations in other languages, use the /translations endpoint.
        """
        # Validate language - RAG only supports ar/en
        if language not in RAG_SUPPORTED_LANGUAGES:
            language = "en"  # Coerce to English (validation logged in retriever)

        # FAST-PATH: Try direct verse lookup first (skips LLM entirely)
        # This is much faster and avoids hallucination for famous verse queries
        fast_response = await self._try_fast_path_verse_query(
            question=question,
            language=language,
            preferred_sources=preferred_sources,
            session_id=session_id,
        )
        if fast_response:
            logger.info("[FAST-PATH] Returning direct tafsir response (LLM skipped)")
            return fast_response

        # 1. Classify intent
        intent = await self._classify_intent(question)

        # 2. Expand query with Islamic terminology
        expanded = expand_query(question)
        search_query = expanded.combined if expanded.expansion_applied else question

        # 3. Retrieve relevant chunks using expanded query
        chunks = await self.retriever.retrieve(
            query=search_query,
            language=language,
            intent=intent,
            preferred_sources=preferred_sources or [],
            top_k=max_sources * 2,  # Retrieve more, then filter
        )

        # 4. Rerank chunks based on relevance and source reliability
        chunks = self._rerank_chunks(chunks, question, max_sources)

        # 5. Check if we have enough evidence
        if not chunks:
            return GroundedResponse(
                answer=SAFE_REFUSAL_NO_SOURCES,
                citations=[],
                confidence=0.0,
                intent=intent.value,
                warnings=["No relevant sources found"],
                query_expansion=expanded.expansion_applied if expanded.expansion_applied else None,
                session_id=session_id,
                related_verses=[],
                tafsir_by_source={},
                follow_up_suggestions=[],
                api_version=settings.api_version,
            )

        # 6. Build context from retrieved chunks
        context = self._build_context(chunks, language)

        # Add conversation context if provided (for follow-up questions)
        if conversation_context:
            context = conversation_context + "\n\n" + context

        # 7. Generate grounded response
        raw_response, llm_latency_ms = await self._generate_response(
            question=question,
            context=context,
            intent=intent,
            language=language,
            include_scholarly_debate=include_scholarly_debate,
        )

        # 8. Parse and validate response with enhanced confidence scoring
        chunk_ids = [c.chunk_id for c in chunks]
        validated = await self._validate_and_parse_response(
            raw_response=raw_response,
            chunks=chunks,
            chunk_ids=chunk_ids,
            intent=intent,
            query_expansion=expanded,
        )

        # 9. Extract related verses for verse-first display
        related_verses = await self._extract_related_verses(chunks, language)

        # 10. Group tafsir by source for accordion display
        tafsir_by_source = self._group_tafsir_by_source(chunks, language)

        # 11. Generate follow-up suggestions
        follow_up_suggestions = self._generate_follow_up_suggestions(
            question, intent, chunks, language
        )

        # Add new fields to response
        validated.session_id = session_id
        validated.related_verses = related_verses
        validated.tafsir_by_source = tafsir_by_source
        validated.follow_up_suggestions = follow_up_suggestions

        # Add LLM latency to processing time
        validated.processing_time_ms = llm_latency_ms

        return validated

    def _rerank_chunks(
        self,
        chunks: List[RetrievedChunk],
        original_query: str,
        max_results: int,
    ) -> List[RetrievedChunk]:
        """
        Rerank retrieved chunks based on multiple factors.

        Factors:
        1. Relevance score (from retrieval)
        2. Source reliability
        3. Query term coverage
        4. Recency/primary source preference
        """
        if not chunks:
            return []

        query_terms = set(original_query.lower().split())

        scored_chunks = []
        for chunk in chunks:
            # Base score from retrieval
            score = chunk.relevance_score

            # Boost for primary sources
            if getattr(chunk, 'is_primary_source', False):
                score += 0.1

            # Boost for high reliability sources
            reliability = getattr(chunk, 'source_reliability', 0.8)
            score += reliability * 0.1

            # Boost for query term overlap
            content = (chunk.content_en or chunk.content_ar or "").lower()
            content_terms = set(content.split())
            overlap = len(query_terms & content_terms)
            if query_terms:
                overlap_ratio = overlap / len(query_terms)
                score += overlap_ratio * 0.15

            scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Return top results
        return [chunk for score, chunk in scored_chunks[:max_results]]

    async def _classify_intent(self, question: str) -> QueryIntent:
        """
        Classify the query intent using rule-based matching first,
        then LLM if needed.
        """
        q_lower = question.lower()

        # Rule-based classification
        if any(word in q_lower for word in ["meaning", "tafseer", "explain", "معنى", "تفسير"]):
            return QueryIntent.VERSE_MEANING

        if any(word in q_lower for word in ["story", "prophet", "قصة", "نبي"]):
            return QueryIntent.STORY_EXPLORATION

        if any(word in q_lower for word in ["theme", "topic", "about", "موضوع"]):
            return QueryIntent.THEME_SEARCH

        if any(word in q_lower for word in ["compare", "difference", "مقارنة", "فرق"]):
            return QueryIntent.COMPARATIVE

        if any(word in q_lower for word in ["root", "word", "grammar", "جذر", "كلمة"]):
            return QueryIntent.LINGUISTIC

        if any(word in q_lower for word in ["ruling", "halal", "haram", "allowed", "حكم", "حلال", "حرام"]):
            return QueryIntent.RULING

        # Default to verse meaning for Quran-related questions
        return QueryIntent.VERSE_MEANING

    def _build_context(
        self,
        chunks: List[RetrievedChunk],
        language: str,
    ) -> str:
        """
        Build context string from retrieved chunks.

        Groups by source and includes clear attribution.
        """
        context_parts = []

        # Group by reliability (primary vs secondary sources)
        primary = [c for c in chunks if c.relevance_score >= 0.7]
        secondary = [c for c in chunks if c.relevance_score < 0.7]

        if primary:
            context_parts.append("=== PRIMARY SOURCES ===\n")
            for chunk in primary:
                content = chunk.content_en if language == "en" else chunk.content_ar
                if not content:
                    content = chunk.content_ar or chunk.content_en or ""

                context_parts.append(f"""
[Source: {chunk.source_name} | Verse: {chunk.verse_reference} | ID: {chunk.chunk_id}]
{content[:2000]}  # Truncate long content
---
""")

        if secondary:
            context_parts.append("\n=== SECONDARY SOURCES ===\n")
            for chunk in secondary:
                content = chunk.content_en if language == "en" else chunk.content_ar
                if not content:
                    content = chunk.content_ar or chunk.content_en or ""

                context_parts.append(f"""
[Source: {chunk.source_name} | Verse: {chunk.verse_reference} | ID: {chunk.chunk_id}]
{content[:1500]}
---
""")

        return "".join(context_parts)

    async def _extract_related_verses(
        self,
        chunks: List[RetrievedChunk],
        language: str,
    ) -> List[RelatedVerse]:
        """
        Extract unique Quranic verses from retrieved chunks.

        Returns a list of RelatedVerse objects with Arabic text and translation.
        """
        # Collect unique verse references
        verse_refs = {}  # sura_no, aya_no -> chunk with highest relevance
        for chunk in chunks:
            key = (chunk.sura_no, chunk.aya_start)
            if key not in verse_refs or chunk.relevance_score > verse_refs[key].relevance_score:
                verse_refs[key] = chunk

        # Fetch verse texts from database
        related_verses = []
        for (sura_no, aya_no), chunk in sorted(verse_refs.items(), key=lambda x: -x[1].relevance_score)[:5]:
            try:
                # Query for verse text from quran_verses table
                result = await self.session.execute(
                    text("""
                        SELECT v.text_uthmani, v.text_imlaei, v.sura_name_ar, v.sura_name_en,
                               t.text as translation
                        FROM quran_verses v
                        LEFT JOIN translations t ON v.id = t.verse_id AND t.language = 'en'
                        WHERE v.sura_no = :sura_no AND v.aya_no = :aya_no
                        LIMIT 1
                    """),
                    {"sura_no": sura_no, "aya_no": aya_no}
                )
                row = result.fetchone()

                if row:
                    related_verses.append(RelatedVerse(
                        sura_no=sura_no,
                        aya_no=aya_no,
                        verse_reference=f"{sura_no}:{aya_no}",
                        text_ar=row[0] or row[1] or "",  # text_uthmani or text_imlaei
                        text_en=row[4] or "",  # translation (may be empty)
                        sura_name_ar=row[2],
                        sura_name_en=row[3],
                        topic=None,  # Could be enhanced with concept topics
                        relevance_score=chunk.relevance_score,
                    ))
                else:
                    # No verse found, create minimal reference
                    related_verses.append(RelatedVerse(
                        sura_no=sura_no,
                        aya_no=aya_no,
                        verse_reference=f"{sura_no}:{aya_no}",
                        text_ar="",
                        text_en="",
                        relevance_score=chunk.relevance_score,
                    ))
            except Exception as e:
                logger.warning(f"Failed to fetch verse {sura_no}:{aya_no}: {e}")
                # Create verse reference without full text
                related_verses.append(RelatedVerse(
                    sura_no=sura_no,
                    aya_no=aya_no,
                    verse_reference=f"{sura_no}:{aya_no}",
                    text_ar="",
                    text_en="",
                    relevance_score=chunk.relevance_score,
                ))

        return related_verses

    def _group_tafsir_by_source(
        self,
        chunks: List[RetrievedChunk],
        language: str,
    ) -> Dict[str, List[TafsirExplanation]]:
        """
        Group tafsir explanations by source for accordion display.

        Returns a dict mapping source_id to list of TafsirExplanation objects.
        """
        tafsir_by_source: Dict[str, List[TafsirExplanation]] = defaultdict(list)

        for chunk in chunks:
            # Get the appropriate content based on language
            explanation = chunk.content_en if language == "en" else chunk.content_ar
            if not explanation:
                explanation = chunk.content_ar or chunk.content_en or ""

            tafsir = TafsirExplanation(
                source_id=chunk.source_id,
                source_name=chunk.source_name,
                source_name_ar=chunk.source_name_ar or chunk.source_name,
                author_name=None,  # Could be enhanced with source metadata
                methodology=chunk.methodology,
                explanation=explanation[:1500],  # Truncate long explanations
                verse_reference=chunk.verse_reference,
                era="classical" if getattr(chunk, 'is_primary_source', True) else "modern",
                reliability_score=getattr(chunk, 'source_reliability', 0.8),
            )

            tafsir_by_source[chunk.source_id].append(tafsir)

        return dict(tafsir_by_source)

    def _generate_follow_up_suggestions(
        self,
        question: str,
        intent: QueryIntent,
        chunks: List[RetrievedChunk],
        language: str,
    ) -> List[str]:
        """
        Generate follow-up question suggestions based on the query and retrieved content.

        Returns a list of 3-5 suggested follow-up questions.
        """
        suggestions = []

        # Extract verse references mentioned in chunks
        verse_refs = set()
        source_names = set()
        for chunk in chunks[:5]:
            verse_refs.add(chunk.verse_reference)
            source_names.add(chunk.source_name if language == "en" else chunk.source_name_ar)

        # Generate intent-specific suggestions
        if language == "ar":
            if intent == QueryIntent.VERSE_MEANING:
                suggestions.extend([
                    "ما هي الدروس المستفادة من هذه الآية؟",
                    "ما هو سبب نزول هذه الآية؟",
                ])
                if verse_refs:
                    ref = list(verse_refs)[0]
                    suggestions.append(f"ما علاقة الآية {ref} بما قبلها وما بعدها؟")
            elif intent == QueryIntent.STORY_EXPLORATION:
                suggestions.extend([
                    "ما هي العبر من هذه القصة؟",
                    "أين ذُكرت هذه القصة في مواضع أخرى من القرآن؟",
                ])
            elif intent == QueryIntent.THEME_SEARCH:
                suggestions.extend([
                    "ما هي الآيات الأخرى المتعلقة بهذا الموضوع؟",
                    "كيف تناول المفسرون هذا الموضوع؟",
                ])
            else:
                suggestions.extend([
                    "هل هناك آيات أخرى متعلقة؟",
                    "ما رأي العلماء في هذه المسألة؟",
                ])

            # Add source-specific question
            if source_names:
                source = list(source_names)[0]
                suggestions.append(f"ما قال {source} في تفسير هذا؟")

        else:  # English
            if intent == QueryIntent.VERSE_MEANING:
                suggestions.extend([
                    "What lessons can we learn from this verse?",
                    "What is the context (asbab al-nuzul) of this verse?",
                ])
                if verse_refs:
                    ref = list(verse_refs)[0]
                    suggestions.append(f"How does verse {ref} relate to the verses around it?")
            elif intent == QueryIntent.STORY_EXPLORATION:
                suggestions.extend([
                    "What are the lessons from this story?",
                    "Where else is this story mentioned in the Quran?",
                ])
            elif intent == QueryIntent.THEME_SEARCH:
                suggestions.extend([
                    "What other verses relate to this topic?",
                    "How do different scholars interpret this theme?",
                ])
            else:
                suggestions.extend([
                    "Are there other related verses?",
                    "What do scholars say about this?",
                ])

            # Add source-specific question
            if source_names:
                source = list(source_names)[0]
                suggestions.append(f"What does {source} say about this?")

        # Limit to 5 suggestions
        return suggestions[:5]

    async def _generate_response(
        self,
        question: str,
        context: str,
        intent: QueryIntent,
        language: str,
        include_scholarly_debate: bool,
    ) -> tuple[str, int]:
        """
        Generate response using the configured LLM provider.

        Returns:
            Tuple of (response_text, latency_ms)
        """
        if not self.llm:
            return SAFE_REFUSAL_NO_SOURCES, 0

        # Build user prompt
        user_prompt = build_user_prompt(
            question=question,
            context=context,
            language=language,
            include_scholarly_debate=include_scholarly_debate,
            is_fiqh=intent == QueryIntent.RULING,
        )

        try:
            response = await self.llm.generate(
                system_prompt=GROUNDED_SYSTEM_PROMPT,
                user_message=user_prompt,
                max_tokens=self.max_tokens,  # Use configured RAG token limit
                temperature=0.3,  # Lower for factual/grounded responses
            )

            logger.info(
                f"LLM response: provider={self.llm_provider.value}, "
                f"tokens={response.tokens_used}, latency={response.latency_ms}ms"
            )

            return response.content, response.latency_ms

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"Error generating response: {str(e)}", 0

    async def _validate_and_parse_response(
        self,
        raw_response: str,
        chunks: List[RetrievedChunk],
        chunk_ids: List[str],
        intent: QueryIntent,
        query_expansion: Optional[ExpandedQuery] = None,
    ) -> GroundedResponse:
        """
        Validate citations and parse response into structured format
        with enhanced confidence scoring.
        """
        # Extract citations from response
        # Match both Latin (12:4) and Arabic-Indic numerals (١٢:٤)
        citation_pattern = r'\[([^\]]+)[,،]\s*([٠-٩\d]+:[٠-٩\d]+(?:-[٠-٩\d]+)?)\]'
        found_citations = re.findall(citation_pattern, raw_response)
        print(f"[CITATION] Found {len(found_citations)} citation patterns in response")
        print(f"[CITATION] Available chunks source_name: {[c.source_name for c in chunks[:3]]}...")
        print(f"[CITATION] Available chunks source_name_ar: {[getattr(c, 'source_name_ar', 'N/A') for c in chunks[:5]]}...")
        if found_citations:
            print(f"[CITATION] Sample citations: {found_citations[:3]}")

        # Map chunks by ID for quick lookup
        chunk_map = {c.chunk_id: c for c in chunks}

        # Build citation objects
        citations = []
        valid_citation_ids = set()
        invalid_count = 0

        def arabic_to_latin(s: str) -> str:
            """Convert Arabic-Indic numerals to Latin numerals."""
            arabic_nums = '٠١٢٣٤٥٦٧٨٩'
            latin_nums = '0123456789'
            for a, l in zip(arabic_nums, latin_nums):
                s = s.replace(a, l)
            return s

        def parse_verse_ref(ref: str) -> tuple:
            """Parse verse reference like '12:7' or '١٢:٧' into (sura, aya_start, aya_end)."""
            ref = arabic_to_latin(ref)
            if ':' not in ref:
                return (0, 0, 0)
            parts = ref.split(':')
            sura = int(parts[0])
            aya_part = parts[1]
            if '-' in aya_part:
                aya_parts = aya_part.split('-')
                return (sura, int(aya_parts[0]), int(aya_parts[1]))
            return (sura, int(aya_part), int(aya_part))

        def verse_overlaps(cited_ref: tuple, chunk_sura: int, chunk_aya_start: int, chunk_aya_end: int) -> bool:
            """Check if cited verse overlaps with chunk's verse range."""
            cited_sura, cited_aya_start, cited_aya_end = cited_ref
            if cited_sura != chunk_sura:
                return False
            # Check if ranges overlap
            return not (cited_aya_end < chunk_aya_start or cited_aya_start > chunk_aya_end)

        for source_name, verse_ref in found_citations:
            matched = False
            cited_verse = parse_verse_ref(verse_ref)

            # Find matching chunk (check both English and Arabic source names AND verse reference)
            for chunk in chunks:
                chunk_source_ar = getattr(chunk, 'source_name_ar', '') or ''
                # Check match in either English name, source_id, or Arabic name
                source_matches = (
                    source_name.lower() in chunk.source_name.lower() or
                    source_name.lower() in chunk.source_id.lower() or
                    source_name in chunk_source_ar
                )

                # Also check if the verse reference matches
                verse_matches = verse_overlaps(
                    cited_verse,
                    chunk.sura_no,
                    chunk.aya_start,
                    chunk.aya_end
                )

                # Match requires source AND verse to match (or verse is 0:0-0 for invalid parse)
                is_match = source_matches and (verse_matches or cited_verse == (0, 0, 0))

                if is_match:
                    if chunk.chunk_id not in valid_citation_ids:
                        print(f"[CITATION] Matched '{source_name}' verse {verse_ref} to chunk {chunk.chunk_id} ({chunk.verse_reference})")
                        citations.append(Citation(
                            chunk_id=chunk.chunk_id,
                            source_id=chunk.source_id,
                            source_name=chunk.source_name,
                            source_name_ar=getattr(chunk, 'source_name_ar', '') or chunk.source_name,
                            verse_reference=chunk.verse_reference,
                            excerpt=chunk.content[:200] if chunk.content else "",
                            relevance_score=chunk.relevance_score,
                        ))
                        valid_citation_ids.add(chunk.chunk_id)
                    # Count as matched even if chunk was already cited
                    matched = True
                    break

            if not matched:
                print(f"[CITATION] FAILED to match '{source_name}' verse {verse_ref}")
                invalid_count += 1

        # Count paragraphs and those with citations
        paragraphs = [p.strip() for p in raw_response.split('\n\n') if p.strip() and len(p.strip()) > 100]
        paragraphs_with_citations = sum(
            1 for p in paragraphs if re.search(citation_pattern, p)
        )

        # Get source reliability scores
        reliability_scores = [
            getattr(chunk, 'source_reliability', 0.8) for chunk in chunks
        ]
        relevance_scores = [chunk.relevance_score for chunk in chunks]

        # Check for primary sources
        has_primary = any(getattr(c, 'is_primary_source', True) for c in chunks)

        # Extract chunk and source IDs for evidence density calculation
        chunk_ids = [chunk.chunk_id for chunk in chunks if hasattr(chunk, 'chunk_id')]
        source_ids = [chunk.source_id for chunk in chunks if hasattr(chunk, 'source_id')]

        # Calculate enhanced confidence score
        confidence_breakdown = confidence_scorer.calculate(
            total_paragraphs=len(paragraphs),
            paragraphs_with_citations=paragraphs_with_citations,
            valid_citations=len(citations),
            invalid_citations=invalid_count,
            source_reliability_scores=reliability_scores,
            relevance_scores=relevance_scores,
            has_primary_source=has_primary,
            unsupported_claims=0,  # TODO: Implement claim extraction
            chunk_ids=chunk_ids,
            source_ids=source_ids,
        )

        # Build warnings based on confidence
        warnings = []
        if confidence_breakdown.confidence_level == "insufficient":
            warnings.append("This response lacks sufficient scholarly source support.")
        elif confidence_breakdown.confidence_level == "low":
            warnings.append("This response has limited source support. Consider additional verification.")

        if invalid_count > 0:
            warnings.append(f"{invalid_count} citation(s) could not be validated against retrieved sources.")

        if not has_primary:
            warnings.append("No primary scholarly sources were used in this response.")

        # Add evidence density warning
        if not confidence_breakdown.evidence_density.is_sufficient:
            warnings.append(
                f"Limited evidence density: {confidence_breakdown.evidence_density.distinct_chunks} chunks, "
                f"{confidence_breakdown.evidence_density.distinct_sources} sources. "
                "Consider verifying with additional scholarly sources."
            )

        # Add fiqh warning if needed
        if intent == QueryIntent.RULING:
            warnings.append(SAFE_REFUSAL_FIQH)

        # Add confidence message
        confidence_message = get_confidence_message(confidence_breakdown.confidence_level)

        # Determine scholarly consensus if available
        consensus_votes = {}
        for chunk in chunks:
            if hasattr(chunk, 'scholarly_consensus') and chunk.scholarly_consensus:
                consensus_votes[chunk.scholarly_consensus] = (
                    consensus_votes.get(chunk.scholarly_consensus, 0) + 1
                )

        scholarly_consensus = None
        if consensus_votes:
            scholarly_consensus = max(consensus_votes, key=consensus_votes.get)

        return GroundedResponse(
            answer=raw_response,
            citations=citations,
            confidence=confidence_breakdown.final_score,
            confidence_level=confidence_breakdown.confidence_level,
            confidence_message=confidence_message,
            scholarly_consensus=scholarly_consensus,
            warnings=warnings,
            intent=intent.value,
            query_expansion=query_expansion.expansion_applied if query_expansion else None,
            degradation_reasons=confidence_breakdown.degradation_reasons,
            related_queries=[],  # TODO: Generate related queries
            # Evidence density (for user transparency)
            evidence_chunk_count=confidence_breakdown.evidence_density.distinct_chunks,
            evidence_source_count=confidence_breakdown.evidence_density.distinct_sources,
            # Raw evidence for transparency panel
            evidence=chunks,
            # API version for contract compatibility
            api_version=settings.api_version,
        )
