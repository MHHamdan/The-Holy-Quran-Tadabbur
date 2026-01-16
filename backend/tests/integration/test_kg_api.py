"""
Integration tests for Knowledge Graph API endpoints.

Tests:
- Story cluster endpoints
- Graph visualization endpoints
- Hybrid search
- Health check

Note: These tests require SurrealDB to be running.
Skip with: pytest -m "not integration"
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def run_async(coro):
    """Helper to run async code in sync tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_kg_client():
    """Create a comprehensive mock KG client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.select = AsyncMock()
    client.query = AsyncMock()
    client.get_edges = AsyncMock()
    client.health_check = AsyncMock()
    client.init_schema = AsyncMock()
    return client


@pytest.fixture
def sample_cluster():
    """Sample story cluster data."""
    return {
        "id": "story_cluster:dhul_qarnayn",
        "slug": "dhul_qarnayn",
        "title_ar": "قصة ذي القرنين",
        "title_en": "Story of Dhul-Qarnayn",
        "short_title_ar": "ذو القرنين",
        "short_title_en": "Dhul-Qarnayn",
        "category": "prophetic_narrative",
        "era": "ancient",
        "main_persons": ["person:dhul_qarnayn"],
        "summary_ar": "قصة الملك الصالح ذي القرنين",
        "summary_en": "Story of the righteous king Dhul-Qarnayn",
        "lessons_ar": ["التوكل على الله", "العدل في الحكم"],
        "lessons_en": ["Trust in Allah", "Justice in ruling"],
        "ayah_spans": [{"sura": 18, "start": 83, "end": 98}],
        "total_verses": 16,
        "is_complete": True,
    }


@pytest.fixture
def sample_events():
    """Sample story events."""
    return [
        {
            "id": "story_event:dhul_qarnayn:journey_west",
            "cluster_id": "story_cluster:dhul_qarnayn",
            "chronological_index": 1,
            "title_ar": "رحلته إلى المغرب",
            "title_en": "Journey to the West",
            "narrative_role": "exposition",
            "verse_reference": "18:83-86",
            "summary_ar": "سافر ذو القرنين إلى مغرب الشمس",
            "summary_en": "Dhul-Qarnayn traveled to the setting of the sun",
            "memorization_cue_ar": "مغرب الشمس - عين حمئة",
            "memorization_cue_en": "Setting sun - murky spring",
            "semantic_tags": ["travel", "justice"],
            "is_entry_point": True,
        },
        {
            "id": "story_event:dhul_qarnayn:journey_east",
            "cluster_id": "story_cluster:dhul_qarnayn",
            "chronological_index": 2,
            "title_ar": "رحلته إلى المشرق",
            "title_en": "Journey to the East",
            "narrative_role": "rising_action",
            "verse_reference": "18:89-90",
            "summary_ar": "ثم سافر إلى مطلع الشمس",
            "summary_en": "Then he traveled to the rising of the sun",
            "semantic_tags": ["travel", "exploration"],
            "is_entry_point": False,
        },
        {
            "id": "story_event:dhul_qarnayn:wall_construction",
            "cluster_id": "story_cluster:dhul_qarnayn",
            "chronological_index": 3,
            "title_ar": "بناء السد",
            "title_en": "Building the Wall",
            "narrative_role": "climax",
            "verse_reference": "18:93-97",
            "summary_ar": "بنى ذو القرنين السد لحماية القوم من يأجوج ومأجوج",
            "summary_en": "Dhul-Qarnayn built the wall to protect people from Gog and Magog",
            "semantic_tags": ["construction", "protection", "divine_help"],
            "is_entry_point": False,
        },
    ]


@pytest.fixture
def sample_next_edges():
    """Sample NEXT edges between events."""
    return [
        {
            "in": "story_event:dhul_qarnayn:journey_west",
            "out": "story_event:dhul_qarnayn:journey_east",
            "gap_type": "immediate",
        },
        {
            "in": "story_event:dhul_qarnayn:journey_east",
            "out": "story_event:dhul_qarnayn:wall_construction",
            "gap_type": "time_skip",
        },
    ]


# =============================================================================
# STORY CLUSTER ENDPOINT TESTS
# =============================================================================

class TestStoryClusterEndpoint:
    """Tests for GET /kg/story/{cluster_id}."""

    def test_get_story_cluster_arabic(
        self, mock_kg_client, sample_cluster, sample_events, sample_next_edges
    ):
        """Should return cluster with Arabic labels."""
        mock_kg_client.get.return_value = sample_cluster
        mock_kg_client.select.return_value = sample_events
        mock_kg_client.get_edges.side_effect = [
            [sample_next_edges[0]],  # First event
            [sample_next_edges[1]],  # Second event
            [],  # Third event
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_cluster

            result = run_async(get_story_cluster("dhul_qarnayn", lang="ar"))

            assert result["cluster"]["title"] == "قصة ذي القرنين"
            assert len(result["events"]) == 3
            assert result["events"][0]["title"] == "رحلته إلى المغرب"
            assert len(result["timeline"]) == 2

    def test_get_story_cluster_english(
        self, mock_kg_client, sample_cluster, sample_events
    ):
        """Should return cluster with English labels."""
        mock_kg_client.get.return_value = sample_cluster
        mock_kg_client.select.return_value = sample_events
        mock_kg_client.get_edges.return_value = []

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_cluster

            result = run_async(get_story_cluster("dhul_qarnayn", lang="en"))

            assert result["cluster"]["title"] == "Story of Dhul-Qarnayn"
            assert result["events"][0]["title"] == "Journey to the West"

    def test_get_story_cluster_not_found(self, mock_kg_client):
        """Should return 404 for non-existent cluster."""
        mock_kg_client.get.return_value = None

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_cluster
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_story_cluster("nonexistent"))

            assert exc_info.value.status_code == 404
            assert "cluster_not_found" in str(exc_info.value.detail)


# =============================================================================
# STORY GRAPH ENDPOINT TESTS
# =============================================================================

class TestStoryGraphEndpoint:
    """Tests for GET /kg/story/{cluster_id}/graph."""

    def test_get_story_graph_timeline_mode(
        self, mock_kg_client, sample_events, sample_next_edges
    ):
        """Should return graph in timeline mode."""
        mock_kg_client.select.return_value = sample_events
        mock_kg_client.get_edges.side_effect = [
            [sample_next_edges[0]],
            [sample_next_edges[1]],
            [],
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_graph

            result = run_async(get_story_graph("dhul_qarnayn", mode="timeline"))

            assert result.layout_mode == "timeline"
            assert len(result.nodes) == 3
            assert len(result.edges) == 2
            assert result.is_valid_dag is True

            # Check node positions for timeline
            assert result.nodes[0].position is not None
            assert result.nodes[0].position["x"] == 0

    def test_get_story_graph_concept_mode(
        self, mock_kg_client, sample_events, sample_next_edges
    ):
        """Should include thematic links in concept mode."""
        thematic_edge = {
            "in": "story_event:dhul_qarnayn:journey_west",
            "out": "story_event:dhul_qarnayn:wall_construction",
            "reason": "Both show divine guidance",
            "reason_ar": "كلاهما يظهر الهداية الإلهية",
            "strength": 0.7,
            "confidence": 0.8,
        }

        mock_kg_client.select.return_value = sample_events
        # First 3 calls for NEXT edges, next 3 for thematic
        mock_kg_client.get_edges.side_effect = [
            [sample_next_edges[0]],  # NEXT for event 1
            [sample_next_edges[1]],  # NEXT for event 2
            [],  # NEXT for event 3
            [thematic_edge],  # Thematic for event 1
            [],  # Thematic for event 2
            [],  # Thematic for event 3
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_graph

            result = run_async(get_story_graph("dhul_qarnayn", mode="concept"))

            assert result.layout_mode == "concept"
            # Should have both NEXT and thematic edges
            edge_types = [e.type for e in result.edges]
            assert "next" in edge_types
            assert "thematic_link" in edge_types

    def test_get_story_graph_detects_cycle(self, mock_kg_client, sample_events):
        """Should detect cycles in graph."""
        # Create a cycle: A -> B -> C -> A
        cyclic_edges = [
            {"in": sample_events[0]["id"], "out": sample_events[1]["id"]},
            {"in": sample_events[1]["id"], "out": sample_events[2]["id"]},
            {"in": sample_events[2]["id"], "out": sample_events[0]["id"]},  # Cycle!
        ]

        mock_kg_client.select.return_value = sample_events
        mock_kg_client.get_edges.side_effect = [
            [cyclic_edges[0]],
            [cyclic_edges[1]],
            [cyclic_edges[2]],
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_graph

            result = run_async(get_story_graph("dhul_qarnayn", mode="timeline"))

            assert result.is_valid_dag is False

    def test_get_story_graph_entry_point(
        self, mock_kg_client, sample_events, sample_next_edges
    ):
        """Should identify entry point correctly."""
        mock_kg_client.select.return_value = sample_events
        mock_kg_client.get_edges.side_effect = [
            [sample_next_edges[0]],
            [sample_next_edges[1]],
            [],
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_graph

            result = run_async(get_story_graph("dhul_qarnayn", mode="timeline", lang="ar"))

            # First event is marked as entry point
            assert result.entry_node_id == sample_events[0]["id"]


# =============================================================================
# TIMELINE ENDPOINT TESTS
# =============================================================================

class TestTimelineEndpoint:
    """Tests for GET /kg/story/{cluster_id}/timeline."""

    def test_get_timeline(
        self, mock_kg_client, sample_cluster, sample_events
    ):
        """Should return chronological timeline."""
        mock_kg_client.get.return_value = sample_cluster
        mock_kg_client.select.return_value = sample_events

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import get_story_timeline

            result = run_async(get_story_timeline("dhul_qarnayn"))

            assert result.cluster_id == "dhul_qarnayn"
            assert result.title_ar == "قصة ذي القرنين"
            assert len(result.events) == 3
            # Events should be in chronological order
            indices = [e.index for e in result.events]
            assert indices == sorted(indices)


# =============================================================================
# SEARCH ENDPOINT TESTS
# =============================================================================

class TestSearchEndpoint:
    """Tests for GET /kg/search."""

    def test_hybrid_search_arabic(self, mock_kg_client, sample_cluster):
        """Should search with Arabic query."""
        mock_kg_client.query.side_effect = [
            [sample_cluster],  # Clusters
            [],  # Events
            [],  # Persons
            [],  # Concepts
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import hybrid_search

            result = run_async(hybrid_search(q="القرنين", lang="ar", limit=10))

            assert len(result["clusters"]) == 1
            assert result["clusters"][0]["title_ar"] == "قصة ذي القرنين"

    def test_search_returns_all_types(self, mock_kg_client):
        """Should return results from all entity types."""
        mock_kg_client.query.side_effect = [
            [{"id": "cluster:1", "title_ar": "قصة"}],
            [{"id": "event:1", "title_ar": "حدث"}],
            [{"id": "person:1", "name_ar": "شخص"}],
            [{"id": "concept:1", "label_ar": "مفهوم"}],
        ]

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import hybrid_search

            result = run_async(hybrid_search(q="test", lang="ar", limit=10))

            assert len(result["clusters"]) == 1
            assert len(result["events"]) == 1
            assert len(result["persons"]) == 1
            assert len(result["concepts"]) == 1


# =============================================================================
# DEBUG ENDPOINT TESTS
# =============================================================================

class TestDebugEndpoint:
    """Tests for GET /kg/debug/evidence."""

    def test_debug_evidence_with_chunk_ids(self, mock_kg_client):
        """Should trace evidence for chunk IDs."""
        mock_bridge = MagicMock()
        mock_bridge.hybrid_retrieve = AsyncMock(return_value=MagicMock(
            vector_hits=[],
            graph_expanded_ids=["expanded:1"],
            final_evidence=[],
            debug_info={"traversal_count": 5},
        ))

        with patch("app.api.routes.kg.get_vector_graph_bridge", return_value=mock_bridge):
            from app.api.routes.kg import debug_evidence

            result = run_async(debug_evidence(chunk_ids="chunk:abc,chunk:def"))

            assert result["input_chunk_ids"] == ["chunk:abc", "chunk:def"]
            assert result["debug_info"]["traversal_count"] == 5

    def test_debug_evidence_requires_params(self):
        """Should require either request_id or chunk_ids."""
        from app.api.routes.kg import debug_evidence
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            run_async(debug_evidence(request_id=None, chunk_ids=None))

        assert exc_info.value.status_code == 400


# =============================================================================
# HEALTH ENDPOINT TESTS
# =============================================================================

class TestHealthEndpoint:
    """Tests for GET /kg/health."""

    def test_kg_health_ok(self, mock_kg_client):
        """Should return healthy status."""
        mock_kg_client.health_check.return_value = {
            "status": "ok",
            "host": "localhost",
            "port": 8000,
            "namespace": "tadabbur",
            "database": "quran_kg",
        }

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import kg_health

            result = run_async(kg_health())

            assert result["status"] == "ok"
            assert result["message_ar"] == "قاعدة المعرفة متاحة"
            assert result["message_en"] == "Knowledge Graph available"

    def test_kg_health_unavailable(self, mock_kg_client):
        """Should return unavailable status."""
        mock_kg_client.health_check.return_value = {
            "status": "error",
            "host": "localhost",
            "port": 8000,
        }

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import kg_health

            result = run_async(kg_health())

            assert result["status"] == "error"
            assert result["message_en"] == "Knowledge Graph unavailable"


# =============================================================================
# SCHEMA INIT ENDPOINT TESTS
# =============================================================================

class TestSchemaInitEndpoint:
    """Tests for POST /kg/init-schema."""

    def test_init_schema_success(self, mock_kg_client):
        """Should initialize schema successfully."""
        mock_kg_client.init_schema.return_value = None

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import init_kg_schema

            result = run_async(init_kg_schema())

            assert result["status"] == "ok"
            mock_kg_client.init_schema.assert_called_once()

    def test_init_schema_failure(self, mock_kg_client):
        """Should handle schema init failure."""
        mock_kg_client.init_schema.side_effect = Exception("Connection refused")

        with patch("app.api.routes.kg.get_kg_client", return_value=mock_kg_client):
            from app.api.routes.kg import init_kg_schema
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                run_async(init_kg_schema())

            assert exc_info.value.status_code == 500
            assert "schema_init_failed" in str(exc_info.value.detail)
