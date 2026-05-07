"""
Admin Authentication — Phase S test index.

All 41 admin authentication tests are in:
  backend/tests/unit/test_admin_auth_phase_security.py

They cover:
  - Missing X-Admin-API-Key header → 401
  - Wrong key → 403
  - Correct key → 200 (or handler response)
  - ADMIN_API_KEY not configured → 401 (dev) or 503 (production/staging)
  - POST review decision endpoint is protected
  - All 5 admin endpoints (tasks list, task detail, decision, stats, content-types)
  - Public non-admin routes still work without auth
  - Key value never exposed in error response body
  - Constant-time comparison unit tests (_verify_key)
  - _get_configured_key_hash unit tests
  - Bilingual error response structure (401, 403, 503)

Run with:
  python -m pytest backend/tests/unit/test_admin_auth_phase_security.py -v
"""
# No test classes here — see test_admin_auth_phase_security.py above.
