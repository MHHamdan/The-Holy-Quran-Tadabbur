# Admin Authentication Audit

**Date:** 2026-05-06  
**Auditor:** Phase Security review

---

## 1. Scope

Routes exposed under `/api/v1/admin/*` in the Tadabbur Al-Quran backend.

---

## 2. Current Admin Route Exposure (pre-auth)

| Method | Path | Sensitive? | Was protected? |
|---|---|---|---|
| `GET` | `/api/v1/admin/review/tasks` | Yes — exposes full review task list | **No** |
| `GET` | `/api/v1/admin/review/tasks/{id}` | Yes — exposes task detail | **No** |
| `POST` | `/api/v1/admin/review/tasks/{id}/decision` | Critical — approves/rejects Quran-sensitive content | **No** |
| `GET` | `/api/v1/admin/review/stats` | Moderate — exposes content review statistics | **No** |
| `GET` | `/api/v1/admin/review/content-types` | Low — only enumerates allowed content type labels | **No** |

**All five endpoints were reachable by any HTTP client without any credentials.** This means any actor who can reach the server could:
- Read all 914 pending review tasks and their associated Quran references
- Approve or reject any piece of Quran-sensitive content (story segments, KG relations, disagreement notes) by sending a POST request
- Read review statistics

---

## 3. Existing Auth Infrastructure (not applied)

`backend/app/core/auth.py` exists with a well-implemented Bearer token system:
- Reads `ADMIN_TOKEN` from environment (already in `config.py`)
- Stores only SHA-256 hash of the token, never the raw value
- Constant-time comparison via `hmac.compare_digest`
- `require_admin` FastAPI dependency raises 401 on failure

**Status: implemented but never applied to any admin route.**

`ADMIN_TOKEN=test_admin_token_dev` was set in `backend/.env` but unused.

---

## 4. Risk Assessment

| Risk | Impact | Likelihood (if server reachable) |
|---|---|---|
| Unauthenticated approval of Quran content | Critical — approved content displays without scholarly review | High |
| Unauthenticated rejection of content | High — could silently remove content from display | High |
| Read exposure of 914 task backlog | Moderate — reveals platform internal state | High |
| Mass auto-approve via scripted POST | Critical | Medium (requires knowing the API shape) |
| Integrity of review workflow undermined | Critical — the entire Phase 6 protection is bypassed | High |

The content at risk includes: story segments with Quranic verse references, KG relations between concepts, source evidence citations, and scholarly disagreement notes — all pending human review before display.

---

## 5. Recommended Minimal Staging Auth

Implemented in Phase Security (`backend/app/core/admin_auth.py`):

- **Header:** `X-Admin-API-Key: <key>`
- **Env var:** `ADMIN_API_KEY`
- **Algorithm:** SHA-256 hash + `hmac.compare_digest` (constant-time)
- **Missing key configured:** 401 (dev) or 503 (production/staging)
- **Missing header:** 401
- **Wrong key:** 403
- **Key never logged or exposed in responses**

Applied at router level — all 5 admin endpoints protected with a single `dependencies=[Depends(require_admin_api_key)]` on the `APIRouter`.

---

## 6. Production Auth Recommendations (future)

The current API-key auth is appropriate for staging but should be replaced before public production:

1. **Session-based reviewer auth** — Issue time-limited JWT tokens to approved scholarly reviewers. Each reviewer has a unique identity, not a shared key.
2. **Separate reviewer portal** — The review dashboard should be a separate authenticated application, not accessible at the same origin as the public platform.
3. **Role-based access control** — Distinguish between read-only reviewer access (view tasks) and write access (submit decisions).
4. **Audit log with reviewer identity** — The current system stores `reviewerId` from the request body (self-reported). With real auth, `reviewerId` should come from the authenticated session.
5. **Rate limiting on decision endpoints** — Prevent bulk approval/rejection by a compromised key.
6. **Key rotation** — Establish a process for rotating the admin API key without downtime.

---

## 7. Non-Admin Routes (unaffected)

All public Quran data endpoints (`/api/v1/quran/*`, `/api/v1/search/*`, `/api/v1/rag/*`, `/api/v1/vocabulary/*`, etc.) are intentionally unauthenticated and serve public Quranic content. The auth change in Phase Security affects only `/api/v1/admin/*`.
