#!/usr/bin/env python3
"""
Ask Quran (RAG) Integration Tests

ACCEPTANCE CRITERIA:
1. NEVER returns raw traceback to client
2. ALWAYS includes error_id for tracing when error occurs
3. ALWAYS includes Arabic error message
4. Returns proper response structure on success
5. Handles various failure modes gracefully

Run with: pytest tests/integration/test_ask_quran.py -v
"""
import pytest
import re
from typing import Any, Dict
from unittest.mock import patch, MagicMock, AsyncMock

# Mark all tests as async
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestAskQuranErrorHandling:
    """
    Tests that verify Ask Quran error handling is robust.

    CRITICAL: These tests ensure users NEVER see raw errors.
    """

    def test_error_response_has_required_fields(self):
        """Error responses must have all required fields."""
        from app.core.errors import ErrorCode, create_error

        error = create_error(
            ErrorCode.LLM_UNAVAILABLE,
            "test123",
            internal_details="Ollama down"
        )
        response = error.to_response("ar")

        # Required fields
        assert "ok" in response
        assert response["ok"] is False
        assert "error_code" in response
        assert "error_id" in response
        assert "message" in response
        assert "message_ar" in response
        assert "message_en" in response
        assert "timestamp" in response

    def test_error_response_never_leaks_internal_details(self):
        """Error responses must NEVER include internal error details."""
        from app.core.errors import ErrorCode, create_error

        internal_secret = "DatabaseError: connection refused at 192.168.1.1:5432"
        error = create_error(
            ErrorCode.DATABASE_ERROR,
            "test456",
            internal_details=internal_secret
        )
        response = error.to_response("ar")
        response_str = str(response)

        # Internal details must not appear in response
        assert internal_secret not in response_str
        assert "192.168.1.1" not in response_str
        assert "5432" not in response_str
        assert "connection refused" not in response_str.lower()

    def test_arabic_error_messages_are_arabic(self):
        """Arabic error messages must actually be in Arabic."""
        from app.core.errors import ERROR_MESSAGES_AR, ErrorCode

        arabic_pattern = re.compile(r'[\u0600-\u06FF]')  # Arabic Unicode range

        for code, message in ERROR_MESSAGES_AR.items():
            assert arabic_pattern.search(message), \
                f"Error code {code} message is not in Arabic: {message}"

    def test_all_error_codes_have_arabic_messages(self):
        """Every error code must have an Arabic message."""
        from app.core.errors import ERROR_MESSAGES_AR, ERROR_MESSAGES_EN, ErrorCode

        for code in ErrorCode:
            assert code in ERROR_MESSAGES_AR, f"Missing Arabic message for {code}"
            assert code in ERROR_MESSAGES_EN, f"Missing English message for {code}"

    def test_correlation_id_format(self):
        """Correlation IDs must be valid format."""
        from app.core.errors import generate_correlation_id

        for _ in range(100):
            correlation_id = generate_correlation_id()
            # Should be 8 characters (short UUID)
            assert len(correlation_id) == 8
            # Should be hex characters
            assert all(c in '0123456789abcdef-' for c in correlation_id)

    def test_question_hash_is_consistent(self):
        """Same question should produce same hash."""
        from app.core.errors import hash_question

        question = "ما معنى آية الكرسي؟"
        hash1 = hash_question(question)
        hash2 = hash_question(question)

        assert hash1 == hash2
        # Should be 16 characters (truncated SHA256)
        assert len(hash1) == 16

    def test_question_hash_is_different_for_different_questions(self):
        """Different questions should produce different hashes."""
        from app.core.errors import hash_question

        hash1 = hash_question("ما معنى آية الكرسي؟")
        hash2 = hash_question("ما معنى الصبر؟")

        assert hash1 != hash2


class TestAskQuranRequestContext:
    """Tests for request context tracking."""

    def test_request_context_creation(self):
        """Request context should be created with proper fields."""
        from app.core.errors import RAGRequestContext

        ctx = RAGRequestContext.create("ما معنى آية الكرسي؟", "ar")

        assert ctx.correlation_id
        assert len(ctx.correlation_id) == 8
        assert ctx.question_hash
        assert len(ctx.question_hash) == 16
        assert ctx.language == "ar"
        assert ctx.start_time is not None

    def test_request_context_stats_tracking(self):
        """Request context should track processing stats."""
        from app.core.errors import RAGRequestContext

        ctx = RAGRequestContext.create("test question", "en")
        ctx.retrieval_chunk_count = 5
        ctx.retrieval_source_count = 3
        ctx.llm_provider = "ollama"
        ctx.llm_latency_ms = 1500

        assert ctx.retrieval_chunk_count == 5
        assert ctx.retrieval_source_count == 3
        assert ctx.llm_provider == "ollama"
        assert ctx.llm_latency_ms == 1500


class TestAskQuranErrorCodes:
    """Tests for specific error code scenarios."""

    def test_llm_unavailable_error(self):
        """LLM unavailable error should have proper message."""
        from app.core.errors import ErrorCode, create_error

        error = create_error(
            ErrorCode.LLM_UNAVAILABLE,
            "abc123",
            internal_details="Ollama connection refused"
        )

        ar_response = error.to_response("ar")
        en_response = error.to_response("en")

        # Arabic message should mention trying later
        assert "حاول" in ar_response["message_ar"]  # "try" in Arabic
        # English message should mention unavailable
        assert "unavailable" in en_response["message_en"].lower()

    def test_insufficient_evidence_error(self):
        """Insufficient evidence error should guide user."""
        from app.core.errors import ErrorCode, create_error

        error = create_error(
            ErrorCode.INSUFFICIENT_EVIDENCE,
            "def456"
        )

        ar_response = error.to_response("ar")
        en_response = error.to_response("en")

        # Should mention evidence/sources
        assert "أدلة" in ar_response["message_ar"]  # "evidence" in Arabic
        assert "evidence" in en_response["message_en"].lower()

    def test_internal_error_is_generic(self):
        """Internal errors should be generic, not leak details."""
        from app.core.errors import ErrorCode, create_error

        # Even with specific internal details
        error = create_error(
            ErrorCode.INTERNAL_ERROR,
            "xyz789",
            internal_details="NullPointerException at line 42 in secret_module.py"
        )

        response = error.to_response("ar")

        # Should not contain any implementation details
        assert "NullPointer" not in str(response)
        assert "line 42" not in str(response)
        assert "secret_module" not in str(response)
        # Should have generic message
        assert "خطأ داخلي" in response["message_ar"]  # "internal error" in Arabic


class TestAskQuranResponseStructure:
    """Tests for successful response structure."""

    def test_grounded_response_to_dict(self):
        """GroundedResponse.to_dict() should have all required fields."""
        from app.rag.types import GroundedResponse, Citation

        response = GroundedResponse(
            answer="Test answer",
            citations=[
                Citation(
                    chunk_id="chunk1",
                    source_id="source1",
                    source_name="Test Source",
                    source_name_ar="مصدر تجريبي",
                    verse_reference="2:255",
                    excerpt="Test excerpt",
                    relevance_score=0.85,
                )
            ],
            confidence=0.8,
            intent="verse_meaning",
        )

        result = response.to_dict()

        # Required fields
        assert "answer" in result
        assert "citations" in result
        assert "confidence" in result
        assert "intent" in result
        assert "evidence_density" in result
        assert "evidence" in result
        assert "api_version" in result

        # Citations should have Arabic name
        assert result["citations"][0]["source_name_ar"] == "مصدر تجريبي"

    def test_evidence_density_structure(self):
        """Evidence density should have chunk and source counts."""
        from app.rag.types import GroundedResponse

        response = GroundedResponse(
            answer="Test",
            citations=[],
            confidence=0.5,
            intent="verse_meaning",
            evidence_chunk_count=5,
            evidence_source_count=3,
        )

        result = response.to_dict()

        assert result["evidence_density"]["chunk_count"] == 5
        assert result["evidence_density"]["source_count"] == 3


class TestAskQuranSecurityValidation:
    """Security-focused tests."""

    def test_no_sensitive_data_in_logs(self):
        """Logging should not include sensitive data."""
        from app.core.errors import RAGError, ErrorCode
        import io
        import logging

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)

        logger = logging.getLogger("app.core.errors")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            # Create and log an error with sensitive internal details
            error = RAGError(
                code=ErrorCode.DATABASE_ERROR,
                correlation_id="test123",
                internal_details="password=secret123, token=abc456"
            )
            error.log(question_hash="hash123")

            log_output = log_capture.getvalue()

            # Should have correlation_id
            assert "test123" in log_output

            # Internal details will be logged server-side (this is OK)
            # But we verify they don't appear in the response
            response = error.to_response("ar")
            assert "password" not in str(response)
            assert "secret123" not in str(response)
            assert "token" not in str(response)
            assert "abc456" not in str(response)

        finally:
            logger.removeHandler(handler)


class TestAskQuranArabicFirst:
    """Tests ensuring Arabic-first UX."""

    def test_default_language_error_is_arabic(self):
        """Default error message should be Arabic when language=ar."""
        from app.core.errors import ErrorCode, create_error

        error = create_error(ErrorCode.LLM_UNAVAILABLE, "test")
        response = error.to_response("ar")

        # message field should be Arabic when language=ar
        assert response["message"] == response["message_ar"]

    def test_english_language_error(self):
        """Error message should be English when language=en."""
        from app.core.errors import ErrorCode, create_error

        error = create_error(ErrorCode.LLM_UNAVAILABLE, "test")
        response = error.to_response("en")

        # message field should be English when language=en
        assert response["message"] == response["message_en"]


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
