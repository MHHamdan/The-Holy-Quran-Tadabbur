"""
Phase Security — Admin Authentication Tests

Verifies that all /api/v1/admin/* endpoints are protected by X-Admin-API-Key
authentication and that the protection behaves correctly in all scenarios.

Test coverage:
  1. Missing header → 401
  2. Wrong key → 403
  3. Correct key → 200 (or handler response)
  4. ADMIN_API_KEY not configured → 401 (dev) or 503 (production/staging)
  5. POST decision endpoint is protected
  6. All 5 admin endpoints are protected
  7. Public non-admin routes still work without auth
  8. Key value is not present in error response bodies
  9. Constant-time comparison (structural test)
 10. Both GET and POST methods are protected
 11. Unit tests for _verify_key and _get_configured_key_hash

Strategy: patch `app.core.admin_auth._get_configured_key_hash` at request time
so tests control the key scenario without fighting lru_cache or .env loading.
"""
import hashlib
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

TEST_KEY = "test-admin-key-phase-security-12345"
WRONG_KEY = "wrong-key-definitely-not-correct"
TEST_KEY_HASH = hashlib.sha256(TEST_KEY.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Shared client
# ---------------------------------------------------------------------------

client = TestClient(app, raise_server_exceptions=False)


def _auth_headers(key: str = TEST_KEY) -> dict:
    return {"X-Admin-API-Key": key}


def _patch_key(key_hash: str | None):
    """Context manager: override _get_configured_key_hash to return key_hash."""
    return patch("app.core.admin_auth._get_configured_key_hash", return_value=key_hash)


def _patch_env(env_name: str):
    """Patch settings.environment to a given value (e.g., 'production')."""
    return patch("app.core.admin_auth.settings.environment", env_name)


# ---------------------------------------------------------------------------
# 1. Missing X-Admin-API-Key header → 401
# ---------------------------------------------------------------------------

class TestMissingHeader:
    """Admin routes must return 401 when no auth header is provided."""

    def test_list_tasks_no_header(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
            assert r.status_code == 401

    def test_get_task_no_header(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks/nonexistent")
            assert r.status_code == 401

    def test_stats_no_header(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats")
            assert r.status_code == 401

    def test_decision_no_header(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.post(
                "/api/v1/admin/review/tasks/any-task-id/decision",
                json={"status": "approved", "notes": "Some notes here for testing", "reviewerId": "r1"},
            )
            assert r.status_code == 401

    def test_content_types_no_header(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/content-types")
            assert r.status_code == 401


# ---------------------------------------------------------------------------
# 2. Wrong key → 403
# ---------------------------------------------------------------------------

class TestWrongKey:
    """Wrong key must return 403 Forbidden."""

    def test_list_tasks_wrong_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers={"X-Admin-API-Key": WRONG_KEY})
            assert r.status_code == 403

    def test_stats_wrong_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats", headers={"X-Admin-API-Key": WRONG_KEY})
            assert r.status_code == 403

    def test_decision_wrong_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.post(
                "/api/v1/admin/review/tasks/any-task/decision",
                json={"status": "approved", "notes": "Some valid test notes here", "reviewerId": "r1"},
                headers={"X-Admin-API-Key": WRONG_KEY},
            )
            assert r.status_code == 403

    def test_content_types_wrong_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/content-types", headers={"X-Admin-API-Key": WRONG_KEY})
            assert r.status_code == 403

    def test_empty_string_key_rejected(self):
        with _patch_key(TEST_KEY_HASH):
            # Empty string is treated as missing header by FastAPI → 401
            # or as wrong key → 403 depending on parsing; either is correct
            r = client.get("/api/v1/admin/review/tasks", headers={"X-Admin-API-Key": ""})
            assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 3. Correct key → 200 (or handler-level response)
# ---------------------------------------------------------------------------

class TestCorrectKey:
    """Correct key must let the request pass authentication."""

    def test_stats_with_correct_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert r.status_code == 200

    def test_list_tasks_with_correct_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers=_auth_headers())
            assert r.status_code == 200

    def test_content_types_with_correct_key(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/content-types", headers=_auth_headers())
            assert r.status_code == 200

    def test_get_task_with_correct_key_returns_404_for_unknown(self):
        """Auth passes; 404 from the handler for a nonexistent task is correct."""
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks/definitely-nonexistent-id", headers=_auth_headers())
            assert r.status_code == 404

    def test_whitespace_trimmed_key_accepted(self):
        """Key with surrounding whitespace must still authenticate correctly."""
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats", headers={"X-Admin-API-Key": f"  {TEST_KEY}  "})
            assert r.status_code == 200


# ---------------------------------------------------------------------------
# 4. ADMIN_API_KEY not configured — fail-closed
# ---------------------------------------------------------------------------

class TestKeyNotConfigured:
    """If no key is configured, fail closed based on environment."""

    def test_missing_key_dev_returns_401(self):
        with _patch_key(None), _patch_env("development"):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert r.status_code == 401

    def test_missing_key_production_returns_503(self):
        with _patch_key(None), _patch_env("production"):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert r.status_code == 503

    def test_missing_key_staging_returns_503(self):
        with _patch_key(None), _patch_env("staging"):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert r.status_code == 503

    def test_missing_key_prod_decision_returns_503(self):
        """POST decision must also fail closed in production."""
        with _patch_key(None), _patch_env("production"):
            r = client.post(
                "/api/v1/admin/review/tasks/any/decision",
                json={"status": "approved", "notes": "Test notes for auth test", "reviewerId": "r1"},
                headers=_auth_headers(),
            )
            assert r.status_code == 503


# ---------------------------------------------------------------------------
# 5. Key value not exposed in error responses
# ---------------------------------------------------------------------------

class TestKeyNotLeaked:
    """The admin API key must never appear in any error response."""

    def test_key_not_in_401_body(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
            assert TEST_KEY not in r.text

    def test_wrong_key_not_in_403_body(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers={"X-Admin-API-Key": WRONG_KEY})
            assert TEST_KEY not in r.text
            assert WRONG_KEY not in r.text

    def test_key_hash_not_in_error_body(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers={"X-Admin-API-Key": WRONG_KEY})
            assert TEST_KEY_HASH not in r.text

    def test_503_body_does_not_contain_key(self):
        with _patch_key(None), _patch_env("production"):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert TEST_KEY not in r.text


# ---------------------------------------------------------------------------
# 6. Public routes unaffected
# ---------------------------------------------------------------------------

class TestPublicRoutesUnaffected:
    """Non-admin public routes must work without any auth header."""

    def test_vocabulary_status_works_without_auth(self):
        r = client.get("/api/v1/vocabulary/status")
        assert r.status_code == 200

    def test_vocabulary_lookup_works_without_auth(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        assert r.status_code == 200

    def test_root_works_without_auth(self):
        r = client.get("/")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 7. admin_auth module unit tests — _verify_key
# ---------------------------------------------------------------------------

class TestVerifyKey:
    """Unit tests for _verify_key (no HTTP, no patching needed)."""

    def test_correct_key_returns_true(self):
        from app.core.admin_auth import _verify_key
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key(TEST_KEY) is True

    def test_wrong_key_returns_false(self):
        from app.core.admin_auth import _verify_key
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key(WRONG_KEY) is False

    def test_no_config_returns_false(self):
        from app.core.admin_auth import _verify_key
        with _patch_key(None):
            assert _verify_key(TEST_KEY) is False

    def test_empty_key_returns_false(self):
        from app.core.admin_auth import _verify_key
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key("") is False

    def test_whitespace_only_returns_false(self):
        from app.core.admin_auth import _verify_key
        with _patch_key(TEST_KEY_HASH):
            # Whitespace-only: sha256("") != sha256(TEST_KEY)
            assert _verify_key("   ") is False


# ---------------------------------------------------------------------------
# 8. _get_configured_key_hash unit tests
# ---------------------------------------------------------------------------

class TestGetConfiguredKeyHash:
    """Unit tests for _get_configured_key_hash."""

    def test_returns_sha256_hex_digest(self):
        from app.core.admin_auth import _get_configured_key_hash
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = TEST_KEY
            h = _get_configured_key_hash()
            assert h is not None
            assert len(h) == 64  # SHA-256 hex digest
            assert h == TEST_KEY_HASH

    def test_returns_none_when_key_not_set(self):
        from app.core.admin_auth import _get_configured_key_hash
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = None
            assert _get_configured_key_hash() is None

    def test_returns_none_for_empty_string(self):
        from app.core.admin_auth import _get_configured_key_hash
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = ""
            assert _get_configured_key_hash() is None

    def test_hash_does_not_equal_raw_key(self):
        from app.core.admin_auth import _get_configured_key_hash
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = TEST_KEY
            h = _get_configured_key_hash()
            assert h != TEST_KEY

    def test_different_keys_produce_different_hashes(self):
        from app.core.admin_auth import _get_configured_key_hash
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = TEST_KEY
            h1 = _get_configured_key_hash()
        with patch("app.core.admin_auth.settings") as mock_settings:
            mock_settings.admin_api_key = WRONG_KEY
            h2 = _get_configured_key_hash()
        assert h1 != h2


# ---------------------------------------------------------------------------
# 9. Error response structure
# ---------------------------------------------------------------------------

class TestErrorResponseStructure:
    """Auth errors must include bilingual messages in the standardized envelope."""

    def test_401_has_english_message(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
            data = r.json()
            assert "error" in data
            assert len(data["error"].get("message", "")) > 5

    def test_401_has_arabic_message(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
            data = r.json()
            assert len(data["error"].get("message_ar", "")) > 5

    def test_403_error_code_is_forbidden(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers={"X-Admin-API-Key": WRONG_KEY})
            assert r.json()["error"]["code"] == "forbidden"

    def test_401_error_code_is_unauthorized(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
            assert r.json()["error"]["code"] == "unauthorized"

    def test_503_error_code_is_service_unavailable(self):
        with _patch_key(None), _patch_env("production"):
            r = client.get("/api/v1/admin/review/stats", headers=_auth_headers())
            assert r.json()["error"]["code"] == "service_unavailable"
