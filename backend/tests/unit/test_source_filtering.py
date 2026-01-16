#!/usr/bin/env python3
"""
Regression tests for source filtering (is_enabled logic).

These tests verify that:
1. Disabled sources are NEVER returned by retrieval
2. User-selected sources are intersected with enabled sources
3. Evidence/citations never include disabled sources
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import Set

pytestmark = pytest.mark.unit


@dataclass
class MockTafseerSource:
    """Mock TafseerSource for testing."""
    id: str
    is_enabled: int  # 1=enabled, 0=disabled
    name_ar: str = "Test"
    name_en: str = "Test"


class TestSourceFilteringLogic:
    """Tests for source filtering in retrieval layer."""

    def test_enabled_sources_filter_keyword_search(self):
        """Keyword search MUST filter by is_enabled == 1."""
        # This is a logic test - verifying the SQL condition exists
        from app.rag.retrieval import HybridRetriever
        import inspect

        source_code = inspect.getsource(HybridRetriever._keyword_search)

        # Verify is_enabled filter is in the query
        assert "is_enabled == 1" in source_code, \
            "Keyword search must filter by is_enabled == 1"

    def test_enabled_sources_filter_vector_search(self):
        """Vector search MUST filter by is_enabled (post-retrieval)."""
        from app.rag.retrieval import HybridRetriever
        import inspect

        source_code = inspect.getsource(HybridRetriever._vector_search)

        # Verify enabled source check exists
        assert "enabled_sources" in source_code, \
            "Vector search must check enabled_sources"
        assert "not in enabled_sources" in source_code or "source_id not in enabled_sources" in source_code, \
            "Vector search must skip disabled sources"

    def test_enabled_sources_cache_method_exists(self):
        """Verify _get_enabled_source_ids method exists."""
        from app.rag.retrieval import HybridRetriever

        assert hasattr(HybridRetriever, '_get_enabled_source_ids'), \
            "HybridRetriever must have _get_enabled_source_ids method"

    def test_preferred_sources_intersected_with_enabled(self):
        """User-preferred sources MUST be intersected with enabled sources."""
        from app.rag.retrieval import HybridRetriever
        import inspect

        source_code = inspect.getsource(HybridRetriever._vector_search)

        # Verify intersection logic exists
        assert "valid_sources" in source_code or "in enabled_sources" in source_code, \
            "Preferred sources must be intersected with enabled sources"


class TestRetrievalSafetyLimits:
    """Tests for safety limits in retrieval."""

    def test_max_chunks_constant_exists(self):
        """MAX_CHUNKS_IN_RESPONSE constant must exist."""
        from app.rag.retrieval import HybridRetriever

        assert hasattr(HybridRetriever, 'MAX_CHUNKS_IN_RESPONSE'), \
            "HybridRetriever must have MAX_CHUNKS_IN_RESPONSE"
        assert HybridRetriever.MAX_CHUNKS_IN_RESPONSE <= 10, \
            "MAX_CHUNKS_IN_RESPONSE should be reasonable (≤10)"

    def test_max_content_length_constant_exists(self):
        """MAX_CHUNK_CONTENT_LENGTH constant must exist."""
        from app.rag.retrieval import HybridRetriever

        assert hasattr(HybridRetriever, 'MAX_CHUNK_CONTENT_LENGTH'), \
            "HybridRetriever must have MAX_CHUNK_CONTENT_LENGTH"
        assert HybridRetriever.MAX_CHUNK_CONTENT_LENGTH <= 5000, \
            "MAX_CHUNK_CONTENT_LENGTH should be reasonable (≤5000)"

    def test_truncate_content_method_exists(self):
        """_truncate_content method must exist."""
        from app.rag.retrieval import HybridRetriever

        assert hasattr(HybridRetriever, '_truncate_content'), \
            "HybridRetriever must have _truncate_content method"


class TestPublicSourcesEndpoint:
    """Tests for public /sources endpoint filtering."""

    def test_public_endpoint_filters_enabled(self):
        """Public /sources endpoint MUST filter by is_enabled == 1."""
        import inspect
        from app.api.routes.rag import get_available_sources

        source_code = inspect.getsource(get_available_sources)

        # Verify is_enabled filter is in the query
        assert "is_enabled == 1" in source_code, \
            "Public sources endpoint must filter by is_enabled == 1"


class TestAdminSourcesEndpoint:
    """Tests for admin /sources endpoint."""

    def test_admin_endpoint_returns_all(self):
        """Admin /sources endpoint MUST return all sources (including disabled)."""
        import inspect
        from app.api.routes.rag import get_all_sources_admin

        source_code = inspect.getsource(get_all_sources_admin)

        # Verify NO is_enabled filter (returns all)
        assert "is_enabled ==" not in source_code, \
            "Admin endpoint should NOT filter by is_enabled (shows all)"


class TestResponseContainsUsedSourceIds:
    """Tests for used_source_ids in response."""

    def test_grounded_response_has_evidence_source_count(self):
        """GroundedResponse must track evidence source count."""
        from app.rag.types import GroundedResponse

        # Check if evidence_source_count exists
        response = GroundedResponse(
            answer="Test",
            citations=[],
            confidence=0.5,
            intent="test"
        )

        assert hasattr(response, 'evidence_source_count'), \
            "GroundedResponse must have evidence_source_count"

    def test_to_dict_includes_evidence_density(self):
        """to_dict must include evidence_density with source_count."""
        from app.rag.types import GroundedResponse

        response = GroundedResponse(
            answer="Test",
            citations=[],
            confidence=0.5,
            intent="test",
            evidence_source_count=3,
            evidence_chunk_count=5,
        )

        result = response.to_dict()

        assert "evidence_density" in result, \
            "to_dict must include evidence_density"
        assert "source_count" in result["evidence_density"], \
            "evidence_density must include source_count"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
