"""
Agentic RAG Orchestrator — M3 Implementation

Wraps the existing single-pass RAGPipeline with:
1. Multi-hop retrieval (up to MAX_HOPS=3): if the first pass produces
   insufficient evidence, generate follow-up queries from initial results
   and retrieve again.
2. Agent 2: Validation — verifies source_ids against TRUSTED_SOURCE_IDS
   and checks evidence sufficiency before synthesis.
3. Agent 3: Consensus / Disagreement — detects scholarly disagreement
   across retrieved chunks and produces structured DisagreementObject instances.

The existing RAGPipeline handles:
- Safety classification (pre-generation)
- LLM synthesis with strict grounding rules
- Citation validation (post-generation)
- Confidence scoring

This orchestrator adds the multi-hop + consensus layer WITHOUT modifying
the existing pipeline (backward-compatible: old code paths still work).

Latency target: P95 ≤ 2 s total (hop 1 target ≤ 700 ms, each extra hop ≤ 400 ms).
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.agents.types import (
    AgenticPipelineResult,
    ConsensusOutput,
    RetrievedItem,
    RetrieverOutput,
    ReviewStatus,
    ValidatedItem,
    ValidationOutput,
    ValidationStatus,
)
from app.rag.agents.consensus import consensus_agent
from app.rag.pipeline import RAGPipeline
from app.rag.types import GroundedResponse
from app.rag.source_validator import source_validator

logger = logging.getLogger(__name__)

MAX_HOPS = 3
MIN_EVIDENCE_ITEMS = 2
EVIDENCE_SUFFICIENCY_THRESHOLD = 0.6


# ─── Hop-query generator ─────────────────────────────────────────────────────

def _generate_follow_up_queries(
    original_query: str,
    first_hop_chunks: list,
    language: str,
) -> List[str]:
    """
    Generate up to 2 follow-up queries from the first-hop results.

    Strategy:
    - Extract unique verse references from retrieved chunks
    - For each verse that the first hop retrieved, form a more specific sub-query
    - Add a thematic expansion query using the most common concept in results
    """
    follow_ups: List[str] = []

    if not first_hop_chunks:
        return follow_ups

    # Collect verse references from first hop
    refs_seen: set = set()
    for chunk in first_hop_chunks[:5]:
        sura = getattr(chunk, "sura_no", None)
        aya = getattr(chunk, "aya_start", None)
        if sura and aya:
            refs_seen.add((sura, aya))

    # Build sub-queries for unaddressed verse ranges
    for sura, aya in list(refs_seen)[:2]:
        if language == "ar":
            follow_ups.append(f"تفسير الآية {sura}:{aya} — {original_query}")
        else:
            follow_ups.append(f"tafsir {sura}:{aya} — {original_query}")

    # Add a broader thematic follow-up using first chunk's content keywords
    if first_hop_chunks and len(follow_ups) < 2:
        snippet = getattr(first_hop_chunks[0], "content", "")[:100]
        if language == "ar":
            follow_ups.append(f"المعنى والدلالة: {snippet}")
        else:
            follow_ups.append(f"thematic meaning: {snippet}")

    return follow_ups[:2]


# ─── Validation Agent (Agent 2) ───────────────────────────────────────────────

def _run_validation(retriever_output: RetrieverOutput) -> ValidationOutput:
    """
    Validate retrieved items against TRUSTED_SOURCE_IDS.

    For each item:
    - Check source_id is in trusted set
    - Check evidence_chain_id is present (required by contract)
    - Mark APPROVED items as VALID, EXPERIMENTAL as UNCERTAIN, others REJECTED
    """
    validated: List[ValidatedItem] = []

    for item in retriever_output.retrieved_items:
        source_verified = source_validator.is_trusted_source_id(item.source_id)
        chain_present = item.evidence_chain_id is not None or item.item_id != ""

        if item.review_status == ReviewStatus.EXPERIMENTAL:
            status = ValidationStatus.UNCERTAIN
            reason = "experimental source — requires review before use"
        elif not source_verified:
            status = ValidationStatus.REJECTED
            reason = f"source_id '{item.source_id}' not in TRUSTED_SOURCE_IDS"
        elif not chain_present:
            status = ValidationStatus.REJECTED
            reason = "missing evidence_chain_id"
        else:
            status = ValidationStatus.VALID
            reason = None

        validated.append(
            ValidatedItem(
                item_id=item.item_id,
                validation_status=status,
                citation_present=True,
                source_id_verified=source_verified,
                text_match_score=item.score,
                original_item=item,
                rejection_reason=reason,
            )
        )

    n_valid = sum(1 for v in validated if v.validation_status == ValidationStatus.VALID)
    n_total = len(validated)

    if n_total == 0:
        overall = "fail"
        score = 0.0
        safe_refusal = True
    elif n_valid == 0:
        overall = "fail"
        score = 0.0
        safe_refusal = True
    elif n_valid < MIN_EVIDENCE_ITEMS:
        overall = "partial"
        score = n_valid / max(n_total, 1)
        safe_refusal = False
    else:
        overall = "pass"
        score = n_valid / max(n_total, 1)
        safe_refusal = False

    return ValidationOutput(
        validated_items=validated,
        overall_status=overall,
        evidence_sufficiency_score=score,
        safe_refusal_required=safe_refusal,
    )


# ─── Adapter: GroundedResponse → RetrievedItem list ──────────────────────────

def _grounded_to_retrieved_items(grounded: GroundedResponse) -> List[RetrievedItem]:
    """Convert evidence chunks from GroundedResponse to RetrievedItem."""
    items: List[RetrievedItem] = []
    for e in grounded.evidence:
        items.append(
            RetrievedItem(
                item_id=e.chunk_id,
                item_type="tafsir_chunk",
                source_id=e.source_id,
                text=e.content or "",
                score=e.relevance_score,
                review_status=ReviewStatus.APPROVED,  # pipeline already validated
                sura_no=e.sura_no,
                aya_start=e.aya_start,
                aya_end=e.aya_end,
                source_name=e.source_name,
                source_name_ar=e.source_name_ar,
                methodology=e.methodology,
                evidence_chain_id=e.chunk_id,  # chunk_id is the chain anchor
            )
        )
    return items


# ─── Main Orchestrator ────────────────────────────────────────────────────────

class AgenticRAGOrchestrator:
    """
    Orchestrates the full agentic RAG pipeline for one query.

    Usage:
        orchestrator = AgenticRAGOrchestrator(session)
        result = await orchestrator.run(question="...", language="en")
        response_dict = result.to_dict()
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_provider=None,
        max_hops: int = MAX_HOPS,
    ):
        self.session = session
        self.llm_provider = llm_provider
        self.max_hops = max_hops
        self._pipeline_cache: Optional[RAGPipeline] = None

    def _get_pipeline(self) -> RAGPipeline:
        if self._pipeline_cache is None:
            self._pipeline_cache = RAGPipeline(
                session=self.session,
                llm_provider=self.llm_provider,
            )
        return self._pipeline_cache

    async def run(
        self,
        question: str,
        language: str = "en",
        preferred_sources: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        answer_mode: Optional[str] = None,
    ) -> AgenticPipelineResult:
        """
        Execute the full agentic pipeline.

        Returns AgenticPipelineResult with structured consensus + disagreement data
        on top of the standard GroundedResponse content.
        """
        start_ms = int(time.time() * 1000)
        pipeline = self._get_pipeline()

        # ── Hop 1: standard pipeline ──────────────────────────────────────────
        grounded = await asyncio.wait_for(
            pipeline.query(
                question=question,
                language=language,
                preferred_sources=preferred_sources,
                session_id=session_id,
            ),
            timeout=10.0,
        )

        hops_used = 1
        retrieved_items = _grounded_to_retrieved_items(grounded)

        # ── Multi-hop: if evidence insufficient, try follow-up queries ────────
        if (
            grounded.status not in ("no_verified_source",)
            and len(retrieved_items) < MIN_EVIDENCE_ITEMS
            and self.max_hops > 1
        ):
            follow_ups = _generate_follow_up_queries(
                original_query=question,
                first_hop_chunks=grounded.evidence,
                language=language,
            )

            for follow_up in follow_ups:
                if hops_used >= self.max_hops:
                    break
                if len(retrieved_items) >= MIN_EVIDENCE_ITEMS:
                    break

                try:
                    hop_result = await asyncio.wait_for(
                        pipeline.run(
                            question=follow_up,
                            language=language,
                            preferred_sources=preferred_sources,
                            session_id=session_id,
                        ),
                        timeout=8.0,
                    )
                    new_items = _grounded_to_retrieved_items(hop_result)
                    # Merge without duplicates (by item_id)
                    existing_ids = {i.item_id for i in retrieved_items}
                    for item in new_items:
                        if item.item_id not in existing_ids:
                            retrieved_items.append(item)
                            existing_ids.add(item.item_id)
                    hops_used += 1
                    logger.info(
                        f"[Orchestrator] Hop {hops_used}: +{len(new_items)} items "
                        f"(total {len(retrieved_items)})"
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[Orchestrator] Hop {hops_used + 1} timed out")
                    break
                except Exception as e:
                    logger.warning(f"[Orchestrator] Hop {hops_used + 1} failed: {e}")
                    break

        # ── Agent 2: Validation ───────────────────────────────────────────────
        retriever_output = RetrieverOutput(
            retrieved_items=retrieved_items,
            total_found=len(retrieved_items),
            hop=hops_used,
        )
        validation_output = _run_validation(retriever_output)

        logger.info(
            f"[Orchestrator] Validation: {validation_output.overall_status} "
            f"({len(validation_output.valid_items)} valid / {len(retrieved_items)} total)"
        )

        # ── Agent 3: Consensus / Disagreement ────────────────────────────────
        consensus: Optional[ConsensusOutput] = None
        disagreement_warning = grounded.disagreement_warning

        if len(validation_output.valid_items) >= 2:
            try:
                consensus = consensus_agent.analyse(
                    validated_items=validation_output.validated_items,
                    query_focus=question,
                )
                if consensus.display_warning and not disagreement_warning:
                    disagreement_warning = consensus.display_warning
            except Exception as e:
                logger.warning(f"[ConsensusAgent] Failed: {e}")

        elapsed = int(time.time() * 1000) - start_ms

        # ── Build AgenticPipelineResult ───────────────────────────────────────
        return AgenticPipelineResult(
            answer=grounded.answer,
            citations=[
                {
                    "chunk_id": c.chunk_id,
                    "source_id": c.source_id,
                    "source_name": c.source_name,
                    "source_name_ar": c.source_name_ar,
                    "verse_reference": c.verse_reference,
                    "excerpt": c.excerpt,
                    "relevance_score": c.relevance_score,
                    "reliability_level": c.reliability_level,
                    "author": c.author,
                    "surah_number": c.surah_number,
                    "ayah_number": c.ayah_number,
                    "quoted_evidence": c.quoted_evidence,
                    "explanation": c.explanation,
                }
                for c in grounded.citations
            ],
            confidence=grounded.confidence,
            status=grounded.status,
            answer_language=grounded.answer_language,
            hops_used=hops_used,
            consensus=consensus,
            validation_output=validation_output,
            answer_mode=grounded.answer_mode,
            disagreement_warning=disagreement_warning,
            ai_summary_disclaimer=grounded.ai_summary_disclaimer,
            related_verses=[v.to_dict() for v in grounded.related_verses],
            tafsir_by_source={
                sid: [t.to_dict() for t in exps]
                for sid, exps in grounded.tafsir_by_source.items()
            },
            follow_up_suggestions=grounded.follow_up_suggestions,
            warnings=grounded.warnings,
            confidence_level=grounded.confidence_level,
            confidence_message=grounded.confidence_message,
            scholarly_consensus=grounded.scholarly_consensus,
            evidence=[
                {
                    "chunk_id": e.chunk_id,
                    "source_id": e.source_id,
                    "source_name": e.source_name,
                    "verse_reference": e.verse_reference,
                    "sura_no": e.sura_no,
                    "aya_start": e.aya_start,
                    "aya_end": e.aya_end,
                    "content": e.content,
                    "relevance_score": e.relevance_score,
                }
                for e in grounded.evidence
            ],
            session_id=grounded.session_id,
            processing_time_ms=elapsed,
        )
