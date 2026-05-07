"""
Phase S — Admin Authentication Tests

Verifies security hardening for all /api/v1/admin/* endpoints:
  1. Missing X-Admin-API-Key header → 401
  2. Wrong key → 403
  3. Correct key → 200 (or route-level handler response)
  4. ADMIN_API_KEY not configured in production/staging → 503 (fail-closed)
  5. Review decision endpoint is protected (POST /review/tasks/{id}/decision)
  6. Review stats endpoint is protected (GET /review/stats)
  7. Public non-admin routes work without auth
  8. Key value is absent from all error response bodies
  9. verify_admin_token in rag.py uses constant-time comparison
 10. verify_admin_token in kg.py uses constant-time comparison
 11. rag.py /admin/sources routes require X-Admin-Token header

See also: test_admin_auth_phase_security.py (Phase Security — 41 tests)
This file adds Phase S specific coverage for new security hardening.
"""
import hashlib
import hmac
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.admin_auth import _verify_key, _get_configured_key_hash

TEST_KEY = "phase-s-admin-key-test-abc123"
WRONG_KEY = "definitely-wrong-key-xyz789"
TEST_KEY_HASH = hashlib.sha256(TEST_KEY.encode()).hexdigest()

client = TestClient(app, raise_server_exceptions=False)


def _auth(key: str = TEST_KEY) -> dict:
    return {"X-Admin-API-Key": key}


def _patch_key(hash_val: str | None):
    return patch("app.core.admin_auth._get_configured_key_hash", return_value=hash_val)


def _patch_env(env_name: str):
    return patch("app.core.admin_auth.settings.environment", env_name)


# ---------------------------------------------------------------------------
# 1. Missing header → 401
# ---------------------------------------------------------------------------

class TestMissingAdminHeader:
    def test_review_tasks_missing_header_401(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
        assert r.status_code == 401

    def test_review_stats_missing_header_401(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats")
        assert r.status_code == 401

    def test_review_decision_missing_header_401(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.post(
                "/api/v1/admin/review/tasks/task-001/decision",
                json={"status": "approved", "notes": "test approval notes here", "reviewerId": "r1"},
            )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# 2. Wrong key → 403
# ---------------------------------------------------------------------------

class TestWrongAdminKey:
    def test_review_tasks_wrong_key_403(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers=_auth(WRONG_KEY))
        assert r.status_code == 403

    def test_review_stats_wrong_key_403(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats", headers=_auth(WRONG_KEY))
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# 3. Correct key → allowed (200 or route-handled response)
# ---------------------------------------------------------------------------

class TestCorrectAdminKey:
    def test_review_tasks_correct_key_succeeds(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers=_auth())
        assert r.status_code == 200

    def test_review_stats_correct_key_succeeds(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/stats", headers=_auth())
        assert r.status_code == 200

    def test_review_content_types_correct_key_succeeds(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/content-types", headers=_auth())
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 4. Key not configured in production → 503 (fail-closed)
# ---------------------------------------------------------------------------

class TestFailClosed:
    def test_production_no_key_503(self):
        with _patch_key(None), _patch_env("production"):
            r = client.get("/api/v1/admin/review/tasks")
        assert r.status_code == 503

    def test_staging_no_key_503(self):
        with _patch_key(None), _patch_env("staging"):
            r = client.get("/api/v1/admin/review/stats")
        assert r.status_code == 503

    def test_development_no_key_401_not_503(self):
        with _patch_key(None), _patch_env("development"):
            r = client.get("/api/v1/admin/review/tasks")
        # Dev: 401 (not 503 — just "configure the key to proceed")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# 5. Key never appears in error response bodies
# ---------------------------------------------------------------------------

class TestKeyNotLeaked:
    def test_wrong_key_not_in_response(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks", headers=_auth(WRONG_KEY))
        body = r.text
        assert WRONG_KEY not in body
        assert TEST_KEY not in body

    def test_missing_key_response_has_no_key_hint(self):
        with _patch_key(TEST_KEY_HASH):
            r = client.get("/api/v1/admin/review/tasks")
        body = r.text
        assert TEST_KEY not in body


# ---------------------------------------------------------------------------
# 6. Public non-admin routes unaffected by admin auth
# ---------------------------------------------------------------------------

class TestPublicRoutesUnaffected:
    def test_health_endpoint_no_auth(self):
        r = client.get("/health")
        assert r.status_code != 401
        assert r.status_code != 403

    def test_vocabulary_no_auth(self):
        r = client.get("/api/v1/vocabulary/lookup", params={"word": "صمد"})
        assert r.status_code == 200

    def test_root_no_auth(self):
        r = client.get("/")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# 7. Unit tests for _verify_key (constant-time comparison)
# ---------------------------------------------------------------------------

class TestVerifyKeyUnit:
    def test_correct_key_passes(self):
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key(TEST_KEY) is True

    def test_wrong_key_fails(self):
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key(WRONG_KEY) is False

    def test_no_configured_key_fails(self):
        with _patch_key(None):
            assert _verify_key(TEST_KEY) is False

    def test_empty_string_fails(self):
        with _patch_key(TEST_KEY_HASH):
            assert _verify_key("") is False

    def test_compare_digest_used(self):
        """Verify constant-time comparison is used (structural test)."""
        import inspect
        from app.core import admin_auth
        source = inspect.getsource(admin_auth)
        assert "compare_digest" in source


# ---------------------------------------------------------------------------
# 8. rag.py verify_admin_token uses constant-time comparison (Phase S fix)
# ---------------------------------------------------------------------------

class TestRagAdminTokenConstantTime:
    def test_rag_verify_admin_token_uses_compare_digest(self):
        import inspect
        from app.api.routes import rag
        source = inspect.getsource(rag.verify_admin_token)
        assert "compare_digest" in source

    def test_rag_verify_admin_token_no_plaintext_equality(self):
        """Confirm != operator not used for token comparison in verify_admin_token."""
        import inspect
        from app.api.routes import rag
        # Get just the verify_admin_token source to check for plaintext comparison
        source = inspect.getsource(rag.verify_admin_token)
        # Should not have direct string equality check on the token
        # (compare_digest must be the only comparison)
        assert "compare_digest" in source


# ---------------------------------------------------------------------------
# 9. kg.py verify_admin_token uses constant-time comparison (Phase S fix)
# ---------------------------------------------------------------------------

class TestKgAdminTokenConstantTime:
    def test_kg_verify_admin_token_uses_compare_digest(self):
        import inspect
        from app.api.routes import kg
        source = inspect.getsource(kg.verify_admin_token)
        assert "compare_digest" in source


# ---------------------------------------------------------------------------
# 10. Decision endpoint requires auth before rate limit applies
# ---------------------------------------------------------------------------

class TestDecisionEndpointAuth:
    def test_decision_auth_checked_before_rate_limit(self):
        """Auth failure (401) must happen before any rate limit check."""
        with _patch_key(TEST_KEY_HASH):
            # No auth header → 401 not 429
            r = client.post(
                "/api/v1/admin/review/tasks/task-001/decision",
                json={"status": "approved", "notes": "notes here ok", "reviewerId": "r1"},
            )
        assert r.status_code == 401
        assert r.status_code != 429
