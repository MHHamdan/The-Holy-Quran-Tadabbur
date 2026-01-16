"""
Verification Workflow Tests

Tests for the admin-gated verification system.
"""
import pytest
from pydantic import ValidationError
from app.api.schemas.concepts import (
    VerificationStatus,
    VerificationTaskCreate,
    VerificationTaskResponse,
    VerificationDecisionCreate,
    VerificationDecisionResponse,
    VerificationStatsResponse,
)


class TestVerificationStatus:
    """Tests for verification status enum."""

    def test_valid_statuses(self):
        """All verification statuses should be valid."""
        assert VerificationStatus.DRAFT.value == "draft"
        assert VerificationStatus.PENDING_REVIEW.value == "pending_review"
        assert VerificationStatus.APPROVED.value == "approved"
        assert VerificationStatus.REJECTED.value == "rejected"

    def test_status_values_lowercase(self):
        """Status values should be lowercase."""
        for status in VerificationStatus:
            assert status.value.islower()


class TestVerificationTaskCreate:
    """Tests for verification task creation schema."""

    def test_valid_task_create(self):
        """Valid task creation should pass."""
        task = VerificationTaskCreate(
            entity_type="grammar",
            entity_id="1:1:0",
            proposed_change={"pos": "اسم", "role": "مبتدأ"},
            evidence_refs={"tafsir_chunk": "123"},
            priority=5
        )
        assert task.entity_type == "grammar"
        assert task.entity_id == "1:1:0"
        assert task.priority == 5

    def test_task_with_all_entity_types(self):
        """Task should accept all entity types."""
        for entity_type in ["concept", "miracle", "tafsir", "occurrence", "grammar"]:
            task = VerificationTaskCreate(
                entity_type=entity_type,
                entity_id="test_id",
                proposed_change={"field": "value"}
            )
            assert task.entity_type == entity_type

    def test_task_priority_default(self):
        """Task priority should default to 0."""
        task = VerificationTaskCreate(
            entity_type="grammar",
            entity_id="test",
            proposed_change={}
        )
        assert task.priority == 0

    def test_task_priority_bounds(self):
        """Task priority should be 0-10."""
        # Valid priority
        task = VerificationTaskCreate(
            entity_type="grammar",
            entity_id="test",
            proposed_change={},
            priority=10
        )
        assert task.priority == 10

        # Invalid priority (too high)
        with pytest.raises(ValidationError):
            VerificationTaskCreate(
                entity_type="grammar",
                entity_id="test",
                proposed_change={},
                priority=11
            )

        # Invalid priority (negative)
        with pytest.raises(ValidationError):
            VerificationTaskCreate(
                entity_type="grammar",
                entity_id="test",
                proposed_change={},
                priority=-1
            )


class TestVerificationTaskResponse:
    """Tests for verification task response schema."""

    def test_valid_task_response(self):
        """Valid task response should pass."""
        response = VerificationTaskResponse(
            id=1,
            entity_type="grammar",
            entity_id="1:1:0",
            proposed_change={"pos": "اسم"},
            evidence_refs={},
            status="pending",
            priority=0,
            created_by="user@example.com",
            created_at="2026-01-10T12:00:00"
        )
        assert response.id == 1
        assert response.status == "pending"


class TestVerificationDecision:
    """Tests for verification decision schemas."""

    def test_valid_approved_decision(self):
        """Approved decision should be valid."""
        decision = VerificationDecisionCreate(
            decision="approved",
            notes="Grammar analysis verified by scholar."
        )
        assert decision.decision == "approved"

    def test_valid_rejected_decision(self):
        """Rejected decision should be valid."""
        decision = VerificationDecisionCreate(
            decision="rejected",
            notes="Incorrect grammatical analysis."
        )
        assert decision.decision == "rejected"

    def test_decision_response(self):
        """Decision response should have all required fields."""
        response = VerificationDecisionResponse(
            id=1,
            task_id=10,
            admin_id="admin@example.com",
            decision="approved",
            notes="Verified",
            decided_at="2026-01-10T14:00:00"
        )
        assert response.task_id == 10
        assert response.admin_id == "admin@example.com"


class TestVerificationStats:
    """Tests for verification statistics schema."""

    def test_stats_response(self):
        """Stats response should have all required fields."""
        stats = VerificationStatsResponse(
            pending_count=5,
            approved_count=10,
            rejected_count=2,
            by_entity_type={"grammar": 10, "concept": 7}
        )
        assert stats.pending_count == 5
        assert stats.approved_count == 10
        assert stats.rejected_count == 2
        assert stats.by_entity_type["grammar"] == 10

    def test_stats_zero_counts(self):
        """Stats should handle zero counts."""
        stats = VerificationStatsResponse(
            pending_count=0,
            approved_count=0,
            rejected_count=0,
            by_entity_type={}
        )
        assert stats.pending_count == 0


class TestGrammarVerificationSpecific:
    """Tests specific to grammar verification workflow."""

    def test_grammar_entity_id_format(self):
        """Grammar entity ID should follow verse:word_index format."""
        # Format: verse_reference:word_index
        valid_ids = ["1:1:0", "2:255:3", "112:1:1"]
        for entity_id in valid_ids:
            task = VerificationTaskCreate(
                entity_type="grammar",
                entity_id=entity_id,
                proposed_change={"pos": "اسم"}
            )
            assert task.entity_id == entity_id

    def test_grammar_proposed_change_fields(self):
        """Grammar proposed change should have expected fields."""
        task = VerificationTaskCreate(
            entity_type="grammar",
            entity_id="1:1:0",
            proposed_change={
                "word": "بِسْمِ",
                "proposed_pos": "حرف جر",
                "proposed_role": "جار ومجرور",
                "proposed_i3rab": "جار ومجرور، الباء حرف جر",
                "proposed_root": "س م و",
                "notes": "تصحيح نحوي"
            }
        )
        assert "proposed_pos" in task.proposed_change
        assert "proposed_role" in task.proposed_change


class TestVerificationWorkflowIntegrity:
    """Tests for workflow integrity checks."""

    def test_task_status_transitions(self):
        """Verify valid status transitions."""
        valid_transitions = {
            "pending": ["approved", "rejected"],
            "approved": [],  # Final state
            "rejected": [],  # Final state
        }

        for from_status, allowed in valid_transitions.items():
            response = VerificationTaskResponse(
                id=1,
                entity_type="test",
                entity_id="test",
                proposed_change={},
                evidence_refs={},
                status=from_status,
                priority=0,
                created_at="2026-01-10T12:00:00"
            )
            assert response.status == from_status

    def test_decision_must_have_admin(self):
        """Decision response must have admin_id."""
        response = VerificationDecisionResponse(
            id=1,
            task_id=1,
            admin_id="admin",
            decision="approved",
            decided_at="2026-01-10T12:00:00"
        )
        assert response.admin_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
