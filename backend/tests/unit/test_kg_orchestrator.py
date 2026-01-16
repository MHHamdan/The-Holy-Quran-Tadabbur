"""
Unit tests for Ingestion Orchestrator.

Tests:
- Run creation and tracking
- Step execution and completion
- Idempotent record processing
- Resume capability
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.ingest.orchestrator import (
    IngestOrchestrator,
    StepName,
    StepResult,
)
from app.kg.models import IngestRun, IngestStatus, StepStatus


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_kg_client():
    """Create a mock KG client."""
    client = MagicMock()
    client.upsert = AsyncMock(return_value={"id": "test"})
    client.get = AsyncMock(return_value=None)
    client.update = AsyncMock(return_value={"id": "test"})
    client.select = AsyncMock(return_value=[])
    client.query = AsyncMock(return_value=[])
    return client


@pytest.fixture
def orchestrator(mock_kg_client):
    """Create orchestrator with mock client."""
    return IngestOrchestrator(kg_client=mock_kg_client)


def run_async(coro):
    """Helper to run async code in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# =============================================================================
# RUN ID GENERATION TESTS
# =============================================================================

class TestRunIdGeneration:
    """Tests for run ID generation."""

    def test_run_id_format(self, orchestrator):
        """Run ID should follow timestamp_hash format."""
        run_id = orchestrator._generate_run_id()
        parts = run_id.split("_")
        assert len(parts) == 3  # YYYYMMDD_HHMMSS_hash

    def test_run_id_uniqueness(self, orchestrator):
        """Consecutive run IDs should be unique."""
        ids = [orchestrator._generate_run_id() for _ in range(10)]
        assert len(set(ids)) == len(ids)


# =============================================================================
# CONFIG HASH TESTS
# =============================================================================

class TestConfigHash:
    """Tests for configuration hashing."""

    def test_same_config_same_hash(self, orchestrator):
        """Same config should produce same hash."""
        config = {"model": "e5", "batch_size": 100}
        hash1 = orchestrator._compute_config_hash(config)
        hash2 = orchestrator._compute_config_hash(config)
        assert hash1 == hash2

    def test_different_config_different_hash(self, orchestrator):
        """Different config should produce different hash."""
        config1 = {"model": "e5", "batch_size": 100}
        config2 = {"model": "e5", "batch_size": 200}
        hash1 = orchestrator._compute_config_hash(config1)
        hash2 = orchestrator._compute_config_hash(config2)
        assert hash1 != hash2

    def test_key_order_independent(self, orchestrator):
        """Hash should be independent of key order."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 2, "a": 1}
        hash1 = orchestrator._compute_config_hash(config1)
        hash2 = orchestrator._compute_config_hash(config2)
        assert hash1 == hash2

    def test_hash_length(self, orchestrator):
        """Hash should be truncated to 16 chars."""
        config = {"test": "value"}
        hash_val = orchestrator._compute_config_hash(config)
        assert len(hash_val) == 16


# =============================================================================
# STEP HANDLER REGISTRATION
# =============================================================================

class TestStepHandlerRegistration:
    """Tests for step handler registration."""

    def test_default_handlers_registered(self, orchestrator):
        """All default step names should have handlers."""
        for step in StepName:
            assert step.value in orchestrator._step_handlers

    def test_register_custom_handler(self, orchestrator):
        """Custom handlers can be registered."""
        async def custom_handler(kg, run_id, config):
            return StepResult(success=True, records_processed=10)

        orchestrator.register_step("custom_step", custom_handler)
        assert "custom_step" in orchestrator._step_handlers

    def test_override_default_handler(self, orchestrator):
        """Default handlers can be overridden."""
        async def my_handler(kg, run_id, config):
            return StepResult(success=True, records_created=5)

        orchestrator.register_step(StepName.EMBED_CHUNKS.value, my_handler)
        assert orchestrator._step_handlers[StepName.EMBED_CHUNKS.value] == my_handler


# =============================================================================
# RUN CREATION TESTS
# =============================================================================

class TestRunCreation:
    """Tests for creating ingestion runs."""

    def test_create_run_basic(self, orchestrator, mock_kg_client):
        """Basic run creation should work."""
        run = run_async(orchestrator.create_run(
            steps=["embed_chunks", "upsert_qdrant"],
            config={"batch_size": 100},
        ))

        assert run.run_id is not None
        assert run.status == IngestStatus.RUNNING
        assert run.steps_planned == ["embed_chunks", "upsert_qdrant"]
        assert run.steps_completed == []
        mock_kg_client.upsert.assert_called_once()

    def test_create_run_default_config(self, orchestrator, mock_kg_client):
        """Run with no config should use empty dict."""
        run = run_async(orchestrator.create_run(steps=["embed_chunks"]))
        assert run.metrics == {"config": {}}

    def test_create_run_records_start_time(self, orchestrator):
        """Run should record start time."""
        before = datetime.utcnow()
        run = run_async(orchestrator.create_run(steps=["embed_chunks"]))
        after = datetime.utcnow()

        assert before <= run.started_at <= after


# =============================================================================
# STEP TRACKING TESTS
# =============================================================================

class TestStepTracking:
    """Tests for step tracking."""

    def test_start_step(self, orchestrator, mock_kg_client):
        """Starting a step should create record."""
        step = run_async(orchestrator.start_step("run_123", "embed_chunks"))

        assert step.run_id == "run_123"
        assert step.step_name == "embed_chunks"
        assert step.status == StepStatus.RUNNING
        mock_kg_client.upsert.assert_called_once()

    def test_complete_step_success(self, orchestrator, mock_kg_client):
        """Completing successful step should update record."""
        result = StepResult(
            success=True,
            records_processed=100,
            records_created=50,
            records_updated=30,
            records_skipped=20,
        )

        step = run_async(orchestrator.complete_step("run_123", "embed_chunks", result))

        assert step.status == StepStatus.COMPLETED
        assert step.records_processed == 100
        mock_kg_client.update.assert_called_once()

    def test_complete_step_failure(self, orchestrator, mock_kg_client):
        """Failing step should record error."""
        result = StepResult(
            success=False,
            error_message="Connection timeout",
        )

        step = run_async(orchestrator.complete_step("run_123", "embed_chunks", result))

        assert step.status == StepStatus.FAILED
        assert step.error_message == "Connection timeout"


# =============================================================================
# IDEMPOTENCY TESTS
# =============================================================================

class TestIdempotency:
    """Tests for idempotent record processing."""

    def test_should_skip_new_record(self, orchestrator, mock_kg_client):
        """New record should not be skipped."""
        mock_kg_client.get.return_value = None

        should_skip = run_async(orchestrator.should_skip_record(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="abc123",
            step_name="embed_chunks",
        ))

        assert should_skip is False

    def test_should_skip_unchanged_processed(self, orchestrator, mock_kg_client):
        """Unchanged and processed record should be skipped."""
        mock_kg_client.get.return_value = {
            "content_hash": "abc123",
            "steps": {
                "embed_chunks": {"status": "completed"},
            },
        }

        should_skip = run_async(orchestrator.should_skip_record(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="abc123",  # Same hash
            step_name="embed_chunks",
        ))

        assert should_skip is True

    def test_should_not_skip_changed_content(self, orchestrator, mock_kg_client):
        """Changed content should not be skipped."""
        mock_kg_client.get.return_value = {
            "content_hash": "old_hash",
            "steps": {
                "embed_chunks": {"status": "completed"},
            },
        }

        should_skip = run_async(orchestrator.should_skip_record(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="new_hash",  # Different hash
            step_name="embed_chunks",
        ))

        assert should_skip is False

    def test_should_not_skip_unprocessed_step(self, orchestrator, mock_kg_client):
        """Record not processed by this step should not be skipped."""
        mock_kg_client.get.return_value = {
            "content_hash": "abc123",
            "steps": {
                "other_step": {"status": "completed"},
            },
        }

        should_skip = run_async(orchestrator.should_skip_record(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="abc123",
            step_name="embed_chunks",  # Different step
        ))

        assert should_skip is False


# =============================================================================
# RECORD STATE TESTS
# =============================================================================

class TestRecordState:
    """Tests for record state updates."""

    def test_update_new_record_state(self, orchestrator, mock_kg_client):
        """New record state should be created."""
        mock_kg_client.get.return_value = None

        run_async(orchestrator.update_record_state(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="abc123",
            run_id="run_456",
            step_name="embed_chunks",
            status="completed",
        ))

        call_args = mock_kg_client.upsert.call_args
        assert call_args[0][1] == "chunk_123"  # record_id
        state_data = call_args[0][2]
        assert state_data["content_hash"] == "abc123"
        assert "embed_chunks" in state_data["steps"]

    def test_update_existing_record_state(self, orchestrator, mock_kg_client):
        """Existing record state should be updated."""
        mock_kg_client.get.return_value = {
            "content_hash": "old_hash",
            "steps": {
                "other_step": {"status": "completed"},
            },
        }

        run_async(orchestrator.update_record_state(
            record_id="chunk_123",
            record_type="tafsir_chunk",
            content_hash="new_hash",
            run_id="run_456",
            step_name="embed_chunks",
            status="completed",
        ))

        call_args = mock_kg_client.upsert.call_args
        state_data = call_args[0][2]
        assert state_data["content_hash"] == "new_hash"
        assert "other_step" in state_data["steps"]
        assert "embed_chunks" in state_data["steps"]


# =============================================================================
# STEP RESULT TESTS
# =============================================================================

class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_defaults(self):
        """StepResult should have sensible defaults."""
        result = StepResult(success=True)
        assert result.records_processed == 0
        assert result.records_created == 0
        assert result.error_message is None
        assert result.metrics == {}

    def test_step_result_with_metrics(self):
        """StepResult should accept custom metrics."""
        result = StepResult(
            success=True,
            records_processed=100,
            metrics={
                "avg_embedding_time": 0.05,
                "batch_count": 10,
            },
        )
        assert result.metrics["avg_embedding_time"] == 0.05


# =============================================================================
# DRY RUN TESTS
# =============================================================================

class TestDryRun:
    """Tests for dry run mode."""

    def test_dry_run_returns_none(self, orchestrator, mock_kg_client):
        """Dry run should return None."""
        result = run_async(orchestrator.execute_run(
            steps=["embed_chunks"],
            dry_run=True,
        ))

        assert result is None

    def test_dry_run_no_db_writes(self, orchestrator, mock_kg_client):
        """Dry run should not write to database."""
        run_async(orchestrator.execute_run(
            steps=["embed_chunks", "upsert_qdrant"],
            dry_run=True,
        ))

        mock_kg_client.upsert.assert_not_called()
        mock_kg_client.update.assert_not_called()


# =============================================================================
# STEP NAME ENUM TESTS
# =============================================================================

class TestStepNameEnum:
    """Tests for StepName enum."""

    def test_all_steps_have_values(self):
        """All step names should have string values."""
        for step in StepName:
            assert isinstance(step.value, str)
            assert len(step.value) > 0

    def test_expected_steps_exist(self):
        """Expected pipeline steps should exist."""
        expected = [
            "ingest_sources",
            "normalize_ayah",
            "chunk_tafsir",
            "embed_chunks",
            "upsert_qdrant",
            "build_kg_edges",
            "build_story_events",
            "validate_constraints",
        ]
        actual = [s.value for s in StepName]
        for step in expected:
            assert step in actual


# =============================================================================
# SINGLETON TESTS
# =============================================================================

class TestSingleton:
    """Tests for orchestrator singleton."""

    def test_get_orchestrator_returns_same_instance(self):
        """get_orchestrator should return singleton."""
        from app.ingest.orchestrator import get_orchestrator
        import app.ingest.orchestrator as orch_module

        # Reset singleton for test
        orch_module._orchestrator = None

        orch1 = get_orchestrator()
        orch2 = get_orchestrator()

        assert orch1 is orch2
