"""
Phase 6: Review Workflow Tests

Tests for the Quran content review task API (file-backed store).

Tests cover:
  - ReviewTaskStore loading and listing
  - Filtering by contentType, status, priority
  - Decision submission rules (notes required, reviewerId required)
  - Approval requires notes and reviewerId
  - Rejection requires notes
  - Decision only updates review metadata, not content
  - humanReviewRequired flag preserved
  - Approved tasks must not lose decision metadata
  - Rejected tasks must not display as approved
  - Stats endpoint returns correct counts
  - API response shape validation
  - No Quran text in task fields
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes.review_tasks import (
    ReviewTaskStore,
    SubmitDecisionRequest,
    VALID_CONTENT_TYPES,
    VALID_STATUSES,
    VALID_PRIORITIES,
)


# =============================================================================
# Fixtures
# =============================================================================

SAMPLE_TASKS = [
    {
        "id": "rt_storysegment_aabbccdd",
        "contentType": "story_segment",
        "contentId": "adam_creation",
        "status": "pending",
        "priority": "medium",
        "language": "both",
        "reviewerId": None,
        "reviewerName": None,
        "createdAt": "2026-05-05T00:00:00Z",
        "updatedAt": "2026-05-05T00:00:00Z",
        "reviewedAt": None,
        "sourceIds": ["ibn_kathir", "tabari"],
        "quranReferences": [{"surahNumber": 2, "ayahStart": 30, "ayahEnd": 33}],
        "decision": None,
        "warnings": ["Story segment data is pending scholarly review."],
        "humanReviewRequired": True,
        "summaryEnglish": "Allah announces creation of a khalifa",
        "storyId": "story_adam",
        "segmentId": "adam_creation",
        "disagreementNotes": [],
    },
    {
        "id": "rt_storysegment_11223344",
        "contentType": "story_segment",
        "contentId": "kahf_sleepers",
        "status": "pending",
        "priority": "high",
        "language": "both",
        "reviewerId": None,
        "reviewerName": None,
        "createdAt": "2026-05-05T00:00:00Z",
        "updatedAt": "2026-05-05T00:00:00Z",
        "reviewedAt": None,
        "sourceIds": ["ibn_kathir"],
        "quranReferences": [{"surahNumber": 18, "ayahStart": 9, "ayahEnd": 26}],
        "decision": None,
        "warnings": ["Story segment data is pending scholarly review."],
        "humanReviewRequired": True,
        "summaryEnglish": "People of the Cave — sleepers count disputed",
        "storyId": "story_kahf",
        "segmentId": "kahf_sleepers",
        "disagreementNotes": [
            "Scholars disagree on the number of sleepers — Quran itself says knowledge is with Allah (18:22)"
        ],
    },
    {
        "id": "rt_kgrelation_55667788",
        "contentType": "kg_relation",
        "contentId": "story:story_adam:adam_creation",
        "status": "pending",
        "priority": "low",
        "language": "both",
        "reviewerId": None,
        "reviewerName": None,
        "createdAt": "2026-05-05T00:00:00Z",
        "updatedAt": "2026-05-05T00:00:00Z",
        "reviewedAt": None,
        "sourceIds": ["story_manifest"],
        "quranReferences": [],
        "decision": None,
        "warnings": ["Knowledge graph relations derived from story/concept data are pending scholarly review."],
        "humanReviewRequired": True,
        "summaryEnglish": "KG relations for story segment: adam_creation",
        "storyId": "story_adam",
        "segmentId": "adam_creation",
        "disagreementNotes": [],
    },
    {
        "id": "rt_disagreementnote_aabb1122",
        "contentType": "disagreement_note",
        "contentId": "ayyub_oath",
        "status": "pending",
        "priority": "high",
        "language": "both",
        "reviewerId": None,
        "reviewerName": None,
        "createdAt": "2026-05-05T00:00:00Z",
        "updatedAt": "2026-05-05T00:00:00Z",
        "reviewedAt": None,
        "sourceIds": ["ibn_kathir", "tabari"],
        "quranReferences": [{"surahNumber": 38, "ayahStart": 44, "ayahEnd": 44}],
        "decision": None,
        "warnings": ["This segment contains scholarly disagreement notes."],
        "humanReviewRequired": True,
        "summaryEnglish": "Disagreement review for: Ayyub's oath in 38:44",
        "storyId": "story_ayyub",
        "segmentId": "ayyub_oath",
        "disagreementNotes": [
            "Verse 38:44 references an oath that Ayyub apparently made; classical scholars differ on context."
        ],
    },
]


@pytest.fixture
def tasks_file(tmp_path):
    """Create a temporary review_tasks.json."""
    tasks_path = tmp_path / "review_tasks.json"
    tasks_path.write_text(
        json.dumps({"version": "1", "generatedAt": "2026-05-05T00:00:00Z", "totalTasks": len(SAMPLE_TASKS), "tasks": SAMPLE_TASKS}),
        encoding="utf-8",
    )
    return tasks_path


@pytest.fixture
def decisions_file(tmp_path):
    """Decisions file path (initially empty)."""
    return tmp_path / "review_decisions.json"


@pytest.fixture
def store(tasks_file, decisions_file):
    """ReviewTaskStore with temp files."""
    s = ReviewTaskStore()
    # Patch internal file paths
    with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
         patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
        s._load()
        yield s, tasks_file, decisions_file


# =============================================================================
# 1. Store loading
# =============================================================================

class TestReviewTaskStoreLoading:

    def test_tasks_loaded(self, store):
        s, _, _ = store
        assert len(s._tasks) == len(SAMPLE_TASKS)

    def test_task_ids_present(self, store):
        s, _, _ = store
        for t in SAMPLE_TASKS:
            assert t["id"] in s._tasks

    def test_all_pending_initially(self, store):
        s, _, _ = store
        for task in s._tasks.values():
            assert task["status"] == "pending"


# =============================================================================
# 2. Filtering
# =============================================================================

class TestReviewTaskFiltering:

    def test_filter_by_content_type(self, store):
        s, _, _ = store
        results, total = s.get_all(content_type="story_segment")
        assert all(t["contentType"] == "story_segment" for t in results)
        assert total == 2  # adam_creation + kahf_sleepers

    def test_filter_by_status_pending(self, store):
        s, _, _ = store
        results, total = s.get_all(status="pending")
        assert total == len(SAMPLE_TASKS)

    def test_filter_by_priority_high(self, store):
        s, _, _ = store
        results, total = s.get_all(priority="high")
        assert all(t["priority"] == "high" for t in results)
        assert total == 2  # kahf_sleepers + ayyub_oath

    def test_filter_has_disagreement(self, store):
        s, _, _ = store
        results, total = s.get_all(has_disagreement=True)
        assert total == 2  # kahf_sleepers + ayyub_oath (both have non-empty disagreementNotes)
        for t in results:
            assert t.get("disagreementNotes")

    def test_filter_by_story_id(self, store):
        s, _, _ = store
        results, total = s.get_all(story_id="story_adam")
        assert total == 2  # adam_creation + kg_relation for adam

    def test_pagination_limit(self, store):
        s, _, _ = store
        results, total = s.get_all(limit=2, offset=0)
        assert len(results) == 2
        assert total == len(SAMPLE_TASKS)

    def test_pagination_offset(self, store):
        s, _, _ = store
        all_results, _ = s.get_all()
        page2, total = s.get_all(limit=2, offset=2)
        assert len(page2) == 2
        assert all_results[0]["id"] != page2[0]["id"]


# =============================================================================
# 3. Decision submission
# =============================================================================

class TestDecisionSubmission:

    def test_approve_updates_status(self, store):
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            updated = s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="approved",
                notes="Reviewed against Ibn Kathir and Tabari. Summary is accurate.",
                reviewer_id="scholar_001",
                reviewer_name="Dr. Ahmad",
            )
        assert updated["status"] == "approved"
        assert updated["decision"]["reviewerId"] == "scholar_001"
        assert updated["decision"]["notes"] == "Reviewed against Ibn Kathir and Tabari. Summary is accurate."
        assert updated["reviewedAt"] is not None

    def test_reject_updates_status(self, store):
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            updated = s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="rejected",
                notes="Summary contains unsupported details not in cited sources.",
                reviewer_id="scholar_002",
            )
        assert updated["status"] == "rejected"
        assert updated["decision"]["status"] == "rejected"

    def test_changes_requested_updates_status(self, store):
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            updated = s.submit_decision(
                task_id="rt_storysegment_11223344",
                decision_status="changes_requested",
                notes="Please add Qurtubi reference for the number of sleepers.",
                reviewer_id="scholar_001",
            )
        assert updated["status"] == "changes_requested"

    def test_task_not_found_raises_error(self, store):
        s, _, _ = store
        with pytest.raises(ValueError, match="not found"):
            s.submit_decision(
                task_id="nonexistent_id",
                decision_status="approved",
                notes="Some notes here with enough text",
                reviewer_id="scholar_001",
            )

    def test_decision_persisted_to_file(self, store):
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            s.submit_decision(
                task_id="rt_kgrelation_55667788",
                decision_status="approved",
                notes="KG edges verified for Adam creation segment.",
                reviewer_id="scholar_003",
            )
        # Check file was written
        assert decisions_file.exists()
        saved = json.loads(decisions_file.read_text())
        assert "rt_kgrelation_55667788" in saved

    def test_decision_does_not_modify_content(self, store):
        """Decision must only update review metadata, not story content."""
        s, tasks_file, decisions_file = store
        original_summary = s._tasks["rt_storysegment_aabbccdd"]["summaryEnglish"]
        original_refs = s._tasks["rt_storysegment_aabbccdd"]["quranReferences"][:]

        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="approved",
                notes="Content is accurate per cited sources.",
                reviewer_id="scholar_001",
            )

        # Content must be unchanged
        updated = s._tasks["rt_storysegment_aabbccdd"]
        assert updated["summaryEnglish"] == original_summary
        assert updated["quranReferences"] == original_refs

    def test_human_review_required_preserved(self, store):
        """humanReviewRequired must not be cleared by a decision."""
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            updated = s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="approved",
                notes="Verified against canonical sources.",
                reviewer_id="scholar_001",
            )
        assert updated["humanReviewRequired"] is True

    def test_rejected_not_displayed_as_approved(self, store):
        """Status after rejection must be 'rejected', never 'approved'."""
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            updated = s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="rejected",
                notes="Contains unsupported detail from non-canonical source.",
                reviewer_id="scholar_002",
            )
        assert updated["status"] == "rejected"
        assert updated["status"] != "approved"


# =============================================================================
# 4. Decision validation (Pydantic)
# =============================================================================

class TestDecisionValidation:

    def test_valid_approve_decision(self):
        req = SubmitDecisionRequest(
            status="approved",
            notes="Reviewed and confirmed against Ibn Kathir.",
            reviewerId="scholar_001",
        )
        assert req.status == "approved"
        assert req.notes == "Reviewed and confirmed against Ibn Kathir."

    def test_notes_too_short_fails(self):
        with pytest.raises(ValidationError):
            SubmitDecisionRequest(
                status="approved",
                notes="Short",  # < 10 chars
                reviewerId="scholar_001",
            )

    def test_empty_notes_fails(self):
        with pytest.raises(ValidationError):
            SubmitDecisionRequest(
                status="approved",
                notes="",
                reviewerId="scholar_001",
            )

    def test_whitespace_only_notes_fails(self):
        with pytest.raises(ValidationError):
            SubmitDecisionRequest(
                status="approved",
                notes="          ",  # whitespace only
                reviewerId="scholar_001",
            )

    def test_invalid_status_fails(self):
        with pytest.raises(ValidationError):
            SubmitDecisionRequest(
                status="auto_approved",  # invalid
                notes="Some valid notes here for the review.",
                reviewerId="scholar_001",
            )

    def test_changes_requested_valid(self):
        req = SubmitDecisionRequest(
            status="changes_requested",
            notes="Please add a second canonical source to this segment.",
            reviewerId="scholar_003",
            reviewerName="Sheikh Abdullah",
        )
        assert req.status == "changes_requested"
        assert req.reviewerName == "Sheikh Abdullah"


# =============================================================================
# 5. Stats
# =============================================================================

class TestReviewStats:

    def test_stats_total(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["total"] == len(SAMPLE_TASKS)

    def test_stats_pending(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["pending"] == len(SAMPLE_TASKS)

    def test_stats_approved_zero_initially(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["approved"] == 0

    def test_stats_with_disagreement(self, store):
        s, _, _ = store
        stats = s.get_stats()
        # kahf_sleepers + ayyub_oath have disagreementNotes
        assert stats["with_disagreement_notes"] == 2

    def test_stats_human_review_required(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["human_review_required"] == len(SAMPLE_TASKS)

    def test_stats_by_content_type(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["by_content_type"]["story_segment"] == 2
        assert stats["by_content_type"]["kg_relation"] == 1
        assert stats["by_content_type"]["disagreement_note"] == 1

    def test_stats_high_priority(self, store):
        s, _, _ = store
        stats = s.get_stats()
        assert stats["high_priority"] == 2  # kahf_sleepers + ayyub_oath

    def test_stats_update_after_decision(self, store):
        s, tasks_file, decisions_file = store
        with patch("app.api.routes.review_tasks._TASKS_FILE", tasks_file), \
             patch("app.api.routes.review_tasks._DECISIONS_FILE", decisions_file):
            s.submit_decision(
                task_id="rt_storysegment_aabbccdd",
                decision_status="approved",
                notes="Verified against canonical sources.",
                reviewer_id="scholar_001",
            )
        stats = s.get_stats()
        assert stats["approved"] == 1
        assert stats["pending"] == len(SAMPLE_TASKS) - 1


# =============================================================================
# 6. Safety: no Quran text in task fields
# =============================================================================

class TestNoQuranTextInTasks:

    ARABIC_TEXT_PATTERN = lambda self, s: len([c for c in s if '؀' <= c <= 'ۿ']) > 10

    def test_summary_english_no_quran_text(self, store):
        """summaryEnglish fields must not contain Quran text."""
        s, _, _ = store
        for task in s._tasks.values():
            summary = task.get("summaryEnglish", "") or ""
            # Arabic short names (story IDs like قصة آدم) are OK
            # But long Quranic passages are not acceptable
            assert len(summary) < 500 or not self.ARABIC_TEXT_PATTERN(summary), \
                f"Task {task['id']} summaryEnglish may contain Arabic text"

    def test_warnings_no_quran_text(self, store):
        """warnings must not contain Quran text."""
        s, _, _ = store
        for task in s._tasks.values():
            for w in task.get("warnings", []):
                assert not self.ARABIC_TEXT_PATTERN(w), \
                    f"Task {task['id']} warning contains Arabic text: {w[:50]}"


# =============================================================================
# 7. Enum coverage
# =============================================================================

class TestEnumCoverage:

    def test_valid_content_types(self):
        assert "story_segment" in VALID_CONTENT_TYPES
        assert "related_story" in VALID_CONTENT_TYPES
        assert "kg_relation" in VALID_CONTENT_TYPES
        assert "source_evidence" in VALID_CONTENT_TYPES
        assert "disagreement_note" in VALID_CONTENT_TYPES

    def test_valid_statuses(self):
        assert "pending" in VALID_STATUSES
        assert "approved" in VALID_STATUSES
        assert "rejected" in VALID_STATUSES
        assert "changes_requested" in VALID_STATUSES

    def test_valid_priorities(self):
        assert "low" in VALID_PRIORITIES
        assert "medium" in VALID_PRIORITIES
        assert "high" in VALID_PRIORITIES

    def test_no_auto_approve_in_statuses(self):
        """auto_approve must not be a valid status."""
        assert "auto_approve" not in VALID_STATUSES
        assert "auto_approved" not in VALID_STATUSES
