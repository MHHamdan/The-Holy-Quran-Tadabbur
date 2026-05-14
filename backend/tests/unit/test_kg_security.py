"""
Unit tests for KG route security guards.

Covers:
1. cluster_id injection guard (_validate_cluster_id)
2. Valid cluster_id formats pass
3. Malicious cluster_id formats are rejected with 400
"""
import pytest
from fastapi import HTTPException

from app.api.routes.kg import _validate_cluster_id


class TestClusterIdValidation:
    def test_numeric_id_passes(self):
        """Simple numeric IDs are allowed."""
        _validate_cluster_id("123")

    def test_alphanumeric_id_passes(self):
        """Alphanumeric slug IDs are allowed."""
        _validate_cluster_id("adam_paradise_expulsion")

    def test_surreal_record_id_passes(self):
        """SurrealDB colon-separated record IDs are allowed."""
        _validate_cluster_id("story_cluster:42")

    def test_hyphenated_id_passes(self):
        """Hyphenated slugs are allowed."""
        _validate_cluster_id("ibrahim-fire")

    def test_semicolon_injection_rejected(self):
        """Semicolon-separated injection is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("1; DROP TABLE story_cluster")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error_code"] == "invalid_cluster_id"

    def test_space_injection_rejected(self):
        """Spaces in cluster_id are not allowed."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("adam eve")
        assert exc_info.value.status_code == 400

    def test_single_quote_injection_rejected(self):
        """Single quotes are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("1' OR '1'='1")
        assert exc_info.value.status_code == 400

    def test_parenthesis_injection_rejected(self):
        """Parentheses are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("1)--")
        assert exc_info.value.status_code == 400

    def test_slash_injection_rejected(self):
        """Forward slashes are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("../../../etc/passwd")
        assert exc_info.value.status_code == 400

    def test_newline_injection_rejected(self):
        """Newline characters are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("adam\nDROP TABLE story_cluster")
        assert exc_info.value.status_code == 400

    def test_empty_string_rejected(self):
        """Empty string is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_cluster_id("")
        assert exc_info.value.status_code == 400

    def test_mixed_valid_chars_pass(self):
        """Mixed alphanumeric, hyphens, underscores, colons pass."""
        _validate_cluster_id("story_cluster:adam-paradise_001")
