"""
Tests for M3: Agentic RAG Pipeline

Covers:
- Agent types contracts (serialization, field invariants)
- ConsensusAgent: strong consensus / partial / significant disagreement / single-source
- Validation agent: trusted vs untrusted source IDs
- Orchestrator: multi-hop logic (mock pipeline), consensus integration
- DisagreementObject: adjudication field is always NOT_ADJUDICATED
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rag.agents.types import (
    AgenticPipelineResult,
    ConsensusLevel,
    ConsensusOutput,
    DisagreementObject,
    DisagreementType,
    RetrievedItem,
    RetrieverOutput,
    ReviewStatus,
    ScholarlyPosition,
    ValidatedItem,
    ValidationOutput,
    ValidationStatus,
)
from app.rag.agents.consensus import ConsensusAgent, _items_contradict, _detect_disagreement_type


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_valid_item(
    item_id: str = "chunk_1",
    source_id: str = "ibn_kathir",
    source_name: str = "Ibn Kathir",
    text: str = "This verse means ...",
    score: float = 0.9,
    review_status: ReviewStatus = ReviewStatus.APPROVED,
) -> ValidatedItem:
    ri = RetrievedItem(
        item_id=item_id,
        item_type="tafsir_chunk",
        source_id=source_id,
        text=text,
        score=score,
        review_status=review_status,
        source_name=source_name,
        source_name_ar="",
        evidence_chain_id=item_id,
    )
    return ValidatedItem(
        item_id=item_id,
        validation_status=ValidationStatus.VALID,
        citation_present=True,
        source_id_verified=True,
        text_match_score=score,
        original_item=ri,
    )


def make_rejected_item(item_id: str = "chunk_x", source_id: str = "unknown_src") -> ValidatedItem:
    ri = RetrievedItem(
        item_id=item_id,
        item_type="tafsir_chunk",
        source_id=source_id,
        text="...",
        score=0.3,
        review_status=ReviewStatus.EXPERIMENTAL,
        source_name="Unknown",
        source_name_ar="",
        evidence_chain_id=None,
    )
    return ValidatedItem(
        item_id=item_id,
        validation_status=ValidationStatus.REJECTED,
        citation_present=False,
        source_id_verified=False,
        text_match_score=0.3,
        original_item=ri,
        rejection_reason="source not trusted",
    )


# ─── Agent Type Tests ─────────────────────────────────────────────────────────

class TestAgentTypes:

    def test_retrieved_item_to_dict(self):
        ri = RetrievedItem(
            item_id="c1", item_type="tafsir_chunk", source_id="ibn_kathir",
            text="text", score=0.85, review_status=ReviewStatus.APPROVED,
        )
        d = ri.to_dict()
        assert d["item_id"] == "c1"
        assert d["review_status"] == "approved"
        assert d["score"] == 0.85

    def test_retriever_output_approved_items(self):
        items = [
            RetrievedItem("a", "tafsir_chunk", "s1", "t", 0.9, ReviewStatus.APPROVED),
            RetrievedItem("b", "tafsir_chunk", "s2", "t", 0.7, ReviewStatus.EXPERIMENTAL),
        ]
        ro = RetrieverOutput(retrieved_items=items, total_found=2)
        assert len(ro.approved_items) == 1
        assert ro.approved_items[0].item_id == "a"

    def test_retriever_output_has_sufficient_evidence_false(self):
        items = [
            RetrievedItem("a", "tafsir_chunk", "s1", "t", 0.9, ReviewStatus.APPROVED),
        ]
        ro = RetrieverOutput(retrieved_items=items, total_found=1)
        assert not ro.has_sufficient_evidence

    def test_retriever_output_has_sufficient_evidence_true(self):
        items = [
            RetrievedItem("a", "tafsir_chunk", "s1", "t", 0.9, ReviewStatus.APPROVED),
            RetrievedItem("b", "tafsir_chunk", "s2", "t", 0.8, ReviewStatus.APPROVED),
        ]
        ro = RetrieverOutput(retrieved_items=items, total_found=2)
        assert ro.has_sufficient_evidence

    def test_disagreement_adjudication_is_not_adjudicated(self):
        d = DisagreementObject(
            disagreement_type=DisagreementType.LEXICAL,
            position_a=ScholarlyPosition("s1", "A", "claim a"),
            position_b=ScholarlyPosition("s2", "B", "claim b"),
        )
        assert "NOT_ADJUDICATED" in d.adjudication

    def test_disagreement_to_dict(self):
        d = DisagreementObject(
            disagreement_type=DisagreementType.THEOLOGICAL,
            position_a=ScholarlyPosition("s1", "Ibn Kathir", "interpretation A"),
            position_b=ScholarlyPosition("s2", "Al-Tabari", "interpretation B"),
        )
        out = d.to_dict()
        assert out["disagreement_type"] == "theological"
        assert out["position_a"]["source_id"] == "s1"
        assert "NOT_ADJUDICATED" in out["adjudication"]

    def test_agentic_pipeline_result_to_dict(self):
        result = AgenticPipelineResult(
            answer="The verse means ...",
            citations=[],
            confidence=0.85,
            status="answered",
            answer_language="en",
            hops_used=2,
        )
        d = result.to_dict()
        assert d["agentic"]["hops_used"] == 2
        assert d["answer"] == "The verse means ..."
        assert d["api_version"] == "2.0.0"

    def test_validation_output_valid_items_filter(self):
        vi1 = make_valid_item("c1")
        vi2 = make_rejected_item("c2")
        vo = ValidationOutput(
            validated_items=[vi1, vi2],
            overall_status="partial",
            evidence_sufficiency_score=0.5,
        )
        assert len(vo.valid_items) == 1
        assert vo.valid_items[0].item_id == "c1"

    def test_consensus_output_has_disagreements(self):
        co = ConsensusOutput(
            consensus_level=ConsensusLevel.PARTIAL,
            majority_position=None,
            disagreements=[
                DisagreementObject(
                    DisagreementType.LEXICAL,
                    ScholarlyPosition("s1", "A", "claim"),
                    ScholarlyPosition("s2", "B", "claim"),
                )
            ],
        )
        assert co.has_disagreements

    def test_consensus_output_no_disagreements(self):
        co = ConsensusOutput(
            consensus_level=ConsensusLevel.STRONG,
            majority_position=None,
        )
        assert not co.has_disagreements


# ─── ConsensusAgent Tests ─────────────────────────────────────────────────────

class TestConsensusAgent:

    def setup_method(self):
        self.agent = ConsensusAgent()

    def test_empty_items_returns_single_source(self):
        result = self.agent.analyse([])
        assert result.consensus_level == ConsensusLevel.SINGLE_SOURCE
        assert result.majority_position is None
        assert result.sources_analysed == 0

    def test_single_source_returns_single_source(self):
        items = [make_valid_item("c1", "ibn_kathir", "Ibn Kathir")]
        result = self.agent.analyse(items)
        assert result.consensus_level == ConsensusLevel.SINGLE_SOURCE
        assert result.sources_analysed == 1
        assert result.majority_position is not None
        assert result.majority_position.source_id == "ibn_kathir"

    def test_two_agreeing_sources_returns_strong_consensus(self):
        # Same lead claim → no disagreement
        items = [
            make_valid_item("c1", "ibn_kathir", "Ibn Kathir",
                           text="This verse refers to the mercy of Allah in the same way across all interpretations."),
            make_valid_item("c2", "tabari", "Al-Tabari",
                           text="This verse refers to the mercy of Allah in the same way across all interpretations."),
        ]
        result = self.agent.analyse(items)
        # Identical text → Jaccard ≈ 1.0 → no disagreement
        assert result.consensus_level == ConsensusLevel.STRONG
        assert not result.has_disagreements

    def test_two_disagreeing_sources_returns_partial(self):
        items = [
            make_valid_item("c1", "ibn_kathir", "Ibn Kathir",
                           text="According to Ibn Kathir, this verse means the absolute sovereignty of Allah."),
            make_valid_item("c2", "tabari", "Al-Tabari",
                           text="However, Al-Tabari disputes this. Some scholars say the ruling differs entirely."),
        ]
        result = self.agent.analyse(items)
        assert result.consensus_level in (ConsensusLevel.PARTIAL, ConsensusLevel.SIGNIFICANT)
        assert result.display_warning is not None

    def test_many_disagreeing_sources_returns_significant(self):
        items = [
            make_valid_item("c1", "s1", "Source A",
                           text="The primary interpretation holds that taqwa means fear."),
            make_valid_item("c2", "s2", "Source B",
                           text="However, others say taqwa means love. Scholars dispute this extensively."),
            make_valid_item("c3", "s3", "Source C",
                           text="Whereas the third school views it differently from both: it means consciousness."),
        ]
        result = self.agent.analyse(items)
        assert result.sources_analysed == 3
        # With multiple sources, may be PARTIAL or SIGNIFICANT
        assert result.consensus_level in (ConsensusLevel.PARTIAL, ConsensusLevel.SIGNIFICANT)

    def test_consensus_to_dict_structure(self):
        items = [make_valid_item("c1", "ibn_kathir", "Ibn Kathir")]
        result = self.agent.analyse(items)
        d = result.to_dict()
        assert "consensus_level" in d
        assert "majority_position" in d
        assert "disagreements" in d
        assert "sources_analysed" in d

    def test_rejected_items_excluded_from_consensus(self):
        valid = make_valid_item("c1", "ibn_kathir", "Ibn Kathir")
        rejected = make_rejected_item("c2", "unknown")
        result = self.agent.analyse([valid, rejected])
        # Only 1 valid source
        assert result.consensus_level == ConsensusLevel.SINGLE_SOURCE

    def test_disagreement_type_detection_jurisprudential(self):
        d_type = _detect_disagreement_type(
            "The ruling on this is halal according to ...",
            "However, some scholars consider it haram ...",
        )
        assert d_type == DisagreementType.JURISPRUDENTIAL

    def test_disagreement_type_detection_lexical(self):
        d_type = _detect_disagreement_type(
            "The Arabic word here is from the root ...",
            "The linguistic meaning differs from ...",
        )
        assert d_type == DisagreementType.LEXICAL

    def test_items_contradict_same_text_false(self):
        text = "Allah is the Creator of all things and over all things He is Disposer of affairs."
        assert not _items_contradict(text, text)

    def test_items_contradict_signal_word_true(self):
        assert _items_contradict(
            "The verse means submission.",
            "However, scholars dispute this — others say it means peace.",
        )


# ─── Validation Logic Tests ───────────────────────────────────────────────────

class TestValidationLogic:
    """Tests for the _run_validation function used inside the orchestrator."""

    def test_no_items_requires_safe_refusal(self):
        from app.rag.agents.orchestrator import _run_validation
        ro = RetrieverOutput(retrieved_items=[], total_found=0)
        vo = _run_validation(ro)
        assert vo.safe_refusal_required
        assert vo.overall_status == "fail"
        assert vo.evidence_sufficiency_score == 0.0

    def test_trusted_source_is_valid(self):
        from app.rag.agents.orchestrator import _run_validation
        # Use a known trusted source ID (ibn_kathir is in TAFSIR_CATALOG)
        ri = RetrievedItem(
            item_id="c1", item_type="tafsir_chunk", source_id="ibn_kathir",
            text="...", score=0.9, review_status=ReviewStatus.APPROVED,
            evidence_chain_id="c1",
        )
        ro = RetrieverOutput(retrieved_items=[ri], total_found=1)
        vo = _run_validation(ro)
        assert any(v.validation_status == ValidationStatus.VALID for v in vo.validated_items)

    def test_unknown_source_is_rejected(self):
        from app.rag.agents.orchestrator import _run_validation
        ri = RetrievedItem(
            item_id="cx", item_type="tafsir_chunk", source_id="fake_source_xyz",
            text="...", score=0.9, review_status=ReviewStatus.APPROVED,
            evidence_chain_id="cx",
        )
        ro = RetrieverOutput(retrieved_items=[ri], total_found=1)
        vo = _run_validation(ro)
        assert all(v.validation_status == ValidationStatus.REJECTED for v in vo.validated_items)

    def test_experimental_item_is_uncertain(self):
        from app.rag.agents.orchestrator import _run_validation
        ri = RetrievedItem(
            item_id="cx", item_type="tafsir_chunk", source_id="ibn_kathir",
            text="...", score=0.5, review_status=ReviewStatus.EXPERIMENTAL,
            evidence_chain_id="cx",
        )
        ro = RetrieverOutput(retrieved_items=[ri], total_found=1)
        vo = _run_validation(ro)
        assert any(v.validation_status == ValidationStatus.UNCERTAIN for v in vo.validated_items)

    def test_two_valid_items_pass(self):
        from app.rag.agents.orchestrator import _run_validation
        items = [
            RetrievedItem("c1", "tafsir_chunk", "ibn_kathir", "t", 0.9, ReviewStatus.APPROVED, evidence_chain_id="c1"),
            RetrievedItem("c2", "tafsir_chunk", "tabari", "t", 0.8, ReviewStatus.APPROVED, evidence_chain_id="c2"),
        ]
        ro = RetrieverOutput(retrieved_items=items, total_found=2)
        vo = _run_validation(ro)
        assert vo.overall_status == "pass"
        assert not vo.safe_refusal_required
        assert len(vo.valid_items) == 2


# ─── Orchestrator Tests (mocked pipeline) ─────────────────────────────────────

class TestAgenticOrchestrator:

    def _make_mock_grounded(
        self,
        status: str = "answered",
        n_evidence: int = 3,
        answer: str = "The verse means ...",
    ):
        """Build a minimal mock GroundedResponse."""
        from app.rag.types import (
            GroundedResponse, RetrievedChunk, Citation,
            RelatedVerse, TafsirExplanation,
        )

        evidence = [
            RetrievedChunk(
                chunk_id=f"chunk_{i}",
                source_id="ibn_kathir",
                source_name="Ibn Kathir",
                source_name_ar="ابن كثير",
                verse_reference="2:255",
                sura_no=2,
                aya_start=255,
                aya_end=255,
                content="Evidence text ...",
                relevance_score=0.9,
            )
            for i in range(n_evidence)
        ]

        return GroundedResponse(
            answer=answer,
            citations=[
                Citation(
                    chunk_id="chunk_0",
                    source_id="ibn_kathir",
                    source_name="Ibn Kathir",
                    source_name_ar="ابن كثير",
                    verse_reference="2:255",
                    excerpt="Evidence ...",
                    relevance_score=0.9,
                    reliability_level="canonical",
                    author="Ibn Kathir",
                )
            ],
            confidence=0.85,
            status=status,
            answer_language="en",
            evidence=evidence,
            related_verses=[],
            tafsir_by_source={},
            follow_up_suggestions=[],
            session_id="sess_1",
        )

    @pytest.mark.asyncio
    async def test_orchestrator_single_hop_sufficient(self):
        from app.rag.agents.orchestrator import AgenticRAGOrchestrator

        mock_grounded = self._make_mock_grounded(n_evidence=3)

        with patch("app.rag.agents.orchestrator.RAGPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.query = AsyncMock(return_value=mock_grounded)
            MockPipeline.return_value = mock_pipeline

            orch = AgenticRAGOrchestrator(session=MagicMock(), max_hops=3)
            orch._pipeline_cache = mock_pipeline

            result = await orch.run(question="What is Ayat al-Kursi?", language="en")

        assert result.hops_used == 1
        assert result.answer == "The verse means ..."
        assert result.status == "answered"
        assert result.api_version == "2.0.0"

    @pytest.mark.asyncio
    async def test_orchestrator_result_has_agentic_metadata(self):
        from app.rag.agents.orchestrator import AgenticRAGOrchestrator

        mock_grounded = self._make_mock_grounded(n_evidence=2)

        with patch("app.rag.agents.orchestrator.RAGPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.query = AsyncMock(return_value=mock_grounded)
            MockPipeline.return_value = mock_pipeline

            orch = AgenticRAGOrchestrator(session=MagicMock(), max_hops=1)
            orch._pipeline_cache = mock_pipeline

            result = await orch.run(question="taqwa meaning", language="en")

        d = result.to_dict()
        assert "agentic" in d
        assert "hops_used" in d["agentic"]
        assert "consensus" in d["agentic"]

    @pytest.mark.asyncio
    async def test_orchestrator_no_safe_refusal_on_no_verified_source(self):
        from app.rag.agents.orchestrator import AgenticRAGOrchestrator

        mock_grounded = self._make_mock_grounded(status="no_verified_source", n_evidence=0)

        with patch("app.rag.agents.orchestrator.RAGPipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.query = AsyncMock(return_value=mock_grounded)
            MockPipeline.return_value = mock_pipeline

            orch = AgenticRAGOrchestrator(session=MagicMock(), max_hops=3)
            orch._pipeline_cache = mock_pipeline

            result = await orch.run(question="obscure query", language="en")

        # Status should propagate; hops_used stays 1 (no hop on no_verified_source)
        assert result.status == "no_verified_source"
        assert result.hops_used == 1

    @pytest.mark.asyncio
    async def test_orchestrator_consensus_produced_for_multi_source(self):
        from app.rag.agents.orchestrator import AgenticRAGOrchestrator
        from app.rag.types import GroundedResponse, RetrievedChunk, Citation

        # Build evidence from 2 different sources
        evidence = [
            RetrievedChunk(
                chunk_id="c1", source_id="ibn_kathir", source_name="Ibn Kathir",
                source_name_ar="ابن كثير", verse_reference="2:3", sura_no=2,
                aya_start=3, aya_end=3,
                content="This verse means those who believe in the unseen.",
                relevance_score=0.9,
            ),
            RetrievedChunk(
                chunk_id="c2", source_id="tabari", source_name="Al-Tabari",
                source_name_ar="الطبري", verse_reference="2:3", sura_no=2,
                aya_start=3, aya_end=3,
                content="However, scholars dispute this. Some say it refers to the resurrection.",
                relevance_score=0.85,
            ),
        ]

        mock_grounded = GroundedResponse(
            answer="The verse addresses ...",
            citations=[
                Citation("c1", "ibn_kathir", "Ibn Kathir", "ابن كثير",
                         "2:3", "excerpt...", 0.9, reliability_level="canonical"),
            ],
            confidence=0.8,
            status="answered",
            answer_language="en",
            evidence=evidence,
            related_verses=[],
            tafsir_by_source={},
            follow_up_suggestions=[],
        )

        with patch("app.rag.agents.orchestrator.RAGPipeline"):
            orch = AgenticRAGOrchestrator(session=MagicMock(), max_hops=1)
            orch._pipeline_cache = MagicMock()
            orch._pipeline_cache.query = AsyncMock(return_value=mock_grounded)

            result = await orch.run(question="What is the meaning of 2:3?", language="en")

        assert result.consensus is not None
        assert result.consensus.sources_analysed >= 1
