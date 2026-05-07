# Phase S Security Hardening — Implementation Record

**Platform:** Tadabbur Al-Quran  
**Phase:** S — Security Hardening  
**Date:** 2026-05-07  
**Status:** Complete

---

## Changes Applied

### 1. Fix Timing Attack in `rag.py` admin token comparison

**File:** `backend/app/api/routes/rag.py`

**Before (vulnerable):**
```python
if x_admin_token != settings.admin_token:
    raise HTTPException(status_code=401, detail="Invalid admin token")
```

**After (secure):**
```python
import hashlib, hmac
provided_hash = hashlib.sha256(x_admin_token.encode()).hexdigest()
configured_hash = hashlib.sha256(settings.admin_token.encode()).hexdigest()
if not hmac.compare_digest(provided_hash, configured_hash):
    raise HTTPException(status_code=403, detail="Invalid admin token")
```

Status code also changed from 401 to 403 (wrong credentials vs. missing credentials).

---

### 2. Fix Timing Attack in `kg.py` admin token comparison

**File:** `backend/app/api/routes/kg.py`

Same fix as `rag.py`: replaced direct `!=` with SHA-256 hash + `hmac.compare_digest`.

---

### 3. Add Rate Limiting Module

**File:** `backend/app/core/rate_limit.py` (new)

Implements:
- `InMemoryRateLimiter(max_requests, window_seconds)` — sliding window, thread-safe
- `_get_client_ip(request)` — respects `X-Forwarded-For`
- Named FastAPI dependency functions (overrideable in tests via `app.dependency_overrides`)

Per-endpoint limits:

| Dependency | Limit | Endpoint |
|---|---|---|
| `rag_rate_limit` | 20 req/min | `POST /api/v1/rag/ask`, `/ask/followup`, `/ask/expand` |
| `admin_decision_rate_limit` | 10 req/min | `POST /api/v1/admin/review/tasks/{id}/decision` |
| `search_rate_limit` | 60 req/min | (available for use in search routes) |
| `vocab_rate_limit` | 60 req/min | `GET /api/v1/vocabulary/lookup` |

---

### 4. Rate Limit Applied to RAG Endpoints

**File:** `backend/app/api/routes/rag.py`

Added `_rate: None = Depends(rag_rate_limit)` to:
- `POST /api/v1/rag/ask`
- `POST /api/v1/rag/ask/followup`
- `POST /api/v1/rag/ask/expand`

---

### 5. Rate Limit Applied to Vocabulary Endpoint

**File:** `backend/app/api/routes/vocabulary.py`

Added `_rate: None = Depends(vocab_rate_limit)` to:
- `GET /api/v1/vocabulary/lookup`

---

### 6. Rate Limit Applied to Review Decision Endpoint

**File:** `backend/app/api/routes/review_tasks.py`

Added `_rate: None = Depends(admin_decision_rate_limit)` to:
- `POST /api/v1/admin/review/tasks/{id}/decision`

Note: Auth check (`require_admin_api_key`) runs at router level before any route handler, so auth is checked before rate limit.

---

### 7. Tests Added

- `backend/tests/unit/test_admin_authentication_phase_s.py` — 27 tests
  - Missing header → 401
  - Wrong key → 403
  - Correct key → 200
  - Fail-closed in production/staging (503)
  - Key not leaked in error bodies
  - Public routes unaffected
  - `_verify_key` unit tests
  - `compare_digest` structural tests for `rag.py` and `kg.py`
  - Decision endpoint auth checked before rate limit

- `backend/tests/unit/test_rate_limiting_phase_s.py` — 22 tests
  - `InMemoryRateLimiter` unit tests
  - `_get_client_ip` tests
  - RAG /ask 429 integration (via `dependency_overrides`)
  - Vocabulary /lookup 429 integration
  - Admin decision 429 integration
  - Module-level limiter configuration assertions

**Total Phase S tests:** 49

---

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `ADMIN_API_KEY` | X-Admin-API-Key auth for Phase 6 review workflow | Yes — staging/prod |
| `ADMIN_TOKEN` | Bearer auth for legacy verification queue (`admin.py`) | Optional |
| `KG_ADMIN_TOKEN` | X-Admin-Token for KG init/import endpoints | Set to strong value in prod |
| `VITE_ADMIN_API_KEY` | Frontend reads this to send the X-Admin-API-Key header | Dev/staging only |

---

## Production Limitations

1. **Single-process rate limiting**: The `InMemoryRateLimiter` stores state in process memory. Multiple uvicorn workers (`--workers N`) or multiple instances do NOT share rate limit state. For distributed deployments, use Redis-backed rate limiting.

2. **`VITE_ADMIN_API_KEY` in the frontend bundle**: Vite bakes environment variables into the compiled JS at build time. Anyone who inspects the bundle can read the key. This is acceptable for local development and private staging environments. For public production:
   - Use server-side authentication (session cookies, OAuth, SSO)
   - Or keep the admin dashboard on a separate, access-controlled domain/URL
   - Never use `VITE_ADMIN_API_KEY` in a publicly accessible production build

3. **No audit log table**: Decisions are logged via `logger.info` but not persisted to a structured database audit table. For compliance-sensitive deployments, add a PostgreSQL `review_audit_log` table.

4. **Two auth mechanisms**: Phase 6 uses `X-Admin-API-Key`; the legacy verification queue uses Bearer `ADMIN_TOKEN`. These should eventually be unified.

---

## What Is NOT Changed

Per Phase S safety rules, the following were explicitly NOT modified:

- Quran text files (`data/raw/quran_uthmani.json`)
- Tafsir content files
- Review task validation logic (`SubmitDecisionRequest` validators unchanged)
- Source registry and validation
- Story validation
- Knowledge graph validation
- The `humanReviewRequired` safeguard in review tasks
- Approval/rejection logic — decisions still require `reviewerId` + notes ≥ 10 chars
