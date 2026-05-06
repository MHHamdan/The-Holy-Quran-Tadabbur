# Admin Authentication Implementation

**Phase:** Security (pre-staging requirement)  
**Date:** 2026-05-06  
**Status:** Complete — all `/api/v1/admin/*` endpoints protected

---

## 1. How It Works

All admin endpoints require a header:

```
X-Admin-API-Key: <your-key>
```

The backend:
1. Reads the key from the `ADMIN_API_KEY` environment variable at request time.
2. Computes a SHA-256 hash of the provided header value.
3. Compares (constant-time, `hmac.compare_digest`) against the SHA-256 hash of the configured key.
4. Returns 401 (missing), 403 (wrong key), or 503 (misconfiguration in production) on failure.
5. Never stores, logs, or returns the raw key value.

The dependency is applied at router level in `review_tasks.py`:
```python
router = APIRouter(dependencies=[Depends(require_admin_api_key)])
```

This means all 5 admin endpoints are protected automatically:
- `GET /api/v1/admin/review/tasks`
- `GET /api/v1/admin/review/tasks/{id}`
- `POST /api/v1/admin/review/tasks/{id}/decision`
- `GET /api/v1/admin/review/stats`
- `GET /api/v1/admin/review/content-types`

---

## 2. Environment Variables

### Backend

| Variable | Required | Description |
|---|---|---|
| `ADMIN_API_KEY` | Yes (for staging/prod) | The admin API key. In dev, if unset, all admin endpoints return 401. |

### Frontend

| Variable | Required | Description |
|---|---|---|
| `VITE_ADMIN_API_KEY` | Yes (for dev/staging dashboard) | Must match `ADMIN_API_KEY`. Used only for local dev and staging. |

---

## 3. Local Development Setup

**Step 1 — Generate a dev key:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Example output: 7b3e2a4f8c1d6b9e0a5f3c7d2e4b8a1f...
```

**Step 2 — Set in backend:**

```bash
# backend/.env
ADMIN_API_KEY=your-generated-key-here
```

**Step 3 — Set in frontend:**

```bash
# frontend/.env  (local only — never commit a real key)
VITE_ADMIN_API_KEY=your-generated-key-here
```

**Step 4 — Test the endpoint:**

```bash
curl -H "X-Admin-API-Key: your-key" http://localhost:8000/api/v1/admin/review/stats
```

A `dev-admin-key-change-before-staging` placeholder is pre-set in `backend/.env` and `frontend/.env` for development convenience. **Change this before any staging deployment.**

---

## 4. Staging Setup

1. Generate a strong random key: `python3 -c "import secrets; print(secrets.token_hex(32))"`
2. Set `ADMIN_API_KEY` as a CI/CD environment secret (not in a committed file).
3. Set `VITE_ADMIN_API_KEY` as a CI/CD build secret for the staging frontend build.
4. Set `ENVIRONMENT=staging` in backend config.
5. In staging mode, if `ADMIN_API_KEY` is unset, all admin endpoints return **503** (fail closed) rather than 401.

---

## 5. Auth Error Behavior

| Scenario | HTTP Status | Reason |
|---|---|---|
| `ADMIN_API_KEY` not set, `ENVIRONMENT=development` | 401 | Instruction to set the variable |
| `ADMIN_API_KEY` not set, `ENVIRONMENT=staging/production` | **503** | Fail closed — misconfiguration is surfaced loudly |
| `X-Admin-API-Key` header missing | 401 | No credentials |
| `X-Admin-API-Key` header wrong | 403 | Bad credentials |
| `X-Admin-API-Key` header correct | 200 (or handler status) | Authenticated |

---

## 6. Frontend Error Display

The `ReviewDashboardPage` detects 401/403 errors from the API and shows a bilingual lock screen:

- **Arabic:** "يتطلب الوصول إلى لوحة المراجعة صلاحية إدارية."
- **English:** "Access to the review dashboard requires admin authorization."

If `VITE_ADMIN_API_KEY` is not set in the frontend environment, the dashboard additionally shows:

- **Arabic:** "لم يتم تهيئة مفتاح المصادقة الإدارية. قم بتعيين متغير البيئة VITE_ADMIN_API_KEY."
- **English:** "Admin API key is not configured. Set the VITE_ADMIN_API_KEY environment variable."

---

## 7. Security Properties

| Property | Status |
|---|---|
| Constant-time comparison (prevents timing attacks) | ✓ (`hmac.compare_digest`) |
| Key stored as hash only | ✓ (SHA-256; raw value never in memory beyond request lifecycle) |
| Key not logged on failure | ✓ (only pass/fail is logged) |
| Key not returned in error responses | ✓ (verified by tests) |
| Key not in frontend bundle unless explicitly set | ✓ (Vite replaces `import.meta.env.VITE_*` at build time) |
| Fail closed when misconfigured in production | ✓ (503 if `ADMIN_API_KEY` not set) |
| Public routes unaffected | ✓ (auth only on `APIRouter` with the dependency) |

---

## 8. Production Limitation

The current implementation uses a **shared static API key**. This means:
- All reviewers share the same key — there is no per-reviewer identity at the auth layer.
- Reviewer identity is still captured in the `reviewerId` field of each decision (submitted in the request body).
- If the key is compromised, all admin access must be revoked by rotating the key.

**This is acceptable for staging** with a small known set of scholarly reviewers.

**Before public production**, replace with:
- Time-limited JWT tokens issued per-reviewer
- Or server-side session auth (NextAuth, Auth0, Clerk, etc.)
- Separate the review portal from the public platform origin

---

## 9. Files Changed

| File | Change |
|---|---|
| `backend/app/core/admin_auth.py` | Created — `require_admin_api_key` dependency |
| `backend/app/core/config.py` | Added `admin_api_key: Optional[str] = None` |
| `backend/app/api/routes/review_tasks.py` | Router-level `Depends(require_admin_api_key)` |
| `backend/.env` | Added `ADMIN_API_KEY` placeholder |
| `frontend/.env` | Added `VITE_ADMIN_API_KEY` placeholder |
| `.env.example` | Added both vars with documentation |
| `frontend/src/lib/api.ts` | `reviewApi` passes `X-Admin-API-Key` header from `VITE_ADMIN_API_KEY` |
| `frontend/src/pages/admin/ReviewDashboardPage.tsx` | Auth error state + bilingual lock screen |
| `frontend/src/i18n/translations.ts` | 5 new auth error translation keys |
| `docs/admin-authentication-audit.md` | Created — pre-auth state audit |
| `docs/admin-authentication-implementation.md` | Created (this file) |
| `backend/tests/unit/test_admin_auth_phase_security.py` | Created — 33 auth tests |
