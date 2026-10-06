> **Superseded (HF migration, Phase 11):** `VITE_ADMIN_API_KEY` was removed. The
> admin key is no longer compiled into the frontend; administrators enter it at
> runtime and it is kept in `sessionStorage` for the tab only.

# Phase S Security Hardening Audit

**Platform:** Tadabbur Al-Quran  
**Phase:** S — Security Hardening  
**Audited:** 2026-05-07  
**Auditor:** Claude Code (AI-assisted audit, requires human review before production)

---

## Scope

- All `/api/v1/admin/*` routes
- Review decision endpoints
- Sensitive public endpoints (RAG/Ask, Search, Vocabulary, Similarity)
- Frontend admin dashboard
- Existing authentication patterns

---

## 1. Admin Route Exposure (Before Phase S)

| Route | Method | Auth | Risk |
|---|---|---|---|
| `/api/v1/admin/review/tasks` | GET | ✅ `X-Admin-API-Key` | Protected |
| `/api/v1/admin/review/tasks/{id}` | GET | ✅ `X-Admin-API-Key` | Protected |
| `/api/v1/admin/review/tasks/{id}/decision` | POST | ✅ `X-Admin-API-Key` | Protected |
| `/api/v1/admin/review/stats` | GET | ✅ `X-Admin-API-Key` | Protected |
| `/api/v1/admin/review/content-types` | GET | ✅ `X-Admin-API-Key` | Protected |
| `/api/v1/admin/flag` | POST | ❌ None (intentional) | Low — user reporting |
| `/api/v1/admin/verification/queue` | GET | ✅ Bearer `ADMIN_TOKEN` | Protected |
| `/api/v1/admin/verification/queue/{id}` | GET | ✅ Bearer `ADMIN_TOKEN` | Protected |
| `/api/v1/admin/verification/queue/{id}/review` | POST | ✅ Bearer `ADMIN_TOKEN` | Protected |
| `/api/v1/admin/verification/stats` | GET | ✅ Bearer `ADMIN_TOKEN` | Protected |
| `/api/v1/admin/verification/flag-types` | GET | ❌ None | Low — static data |
| `/api/v1/admin/verification/entity-types` | GET | ❌ None | Low — static data |
| `/api/v1/admin/verification/statuses` | GET | ❌ None | Low — static data |
| `/api/v1/admin/verification/decisions` | GET | ❌ None | Low — static data |
| `/api/v1/rag/admin/sources` | GET | ✅ `X-Admin-Token` (plaintext!) | **HIGH — timing attack** |
| `/api/v1/rag/admin/sources/{id}/toggle` | PUT | ✅ `X-Admin-Token` (plaintext!) | **HIGH — timing attack** |
| `/api/v1/kg/init-schema` | POST | ✅ `X-Admin-Token` (plaintext!) | **HIGH — timing attack** |
| `/api/v1/kg/import-stories` | POST | ✅ `X-Admin-Token` (plaintext!) | **HIGH — timing attack** |

---

## 2. Public Endpoint Exposure (Before Phase S)

| Route | Rate Limited | Risk |
|---|---|---|
| `POST /api/v1/rag/ask` | ❌ None | **HIGH — LLM calls, cost abuse** |
| `POST /api/v1/rag/ask/followup` | ❌ None | **HIGH — LLM calls** |
| `POST /api/v1/rag/ask/expand` | ❌ None | **HIGH — LLM calls** |
| `GET /api/v1/vocabulary/lookup` | ❌ None | Medium — safe-refusal only |
| `GET /api/v1/search/suggestions` | ❌ None | Medium — DB read |
| `GET /api/v1/search/expand` | ❌ None | Medium — DB read |
| `GET /api/v1/quran/resolve` | ✅ 30/min | Already protected |

---

## 3. Authentication Status (Before Phase S)

**Two parallel auth mechanisms exist:**

| Mechanism | Used By | Header | Algorithm |
|---|---|---|---|
| `X-Admin-API-Key` | Phase 6 review workflow (`review_tasks.py`) | `X-Admin-API-Key` | SHA-256 + `hmac.compare_digest` ✅ |
| Bearer ADMIN_TOKEN | Legacy verification queue (`admin.py`) | `Authorization: Bearer` | SHA-256 + `hmac.compare_digest` ✅ |
| `X-Admin-Token` (inline) | `rag.py` admin sources | `X-Admin-Token` | Plaintext `!=` ❌ |
| `X-Admin-Token` (inline) | `kg.py` admin endpoints | `X-Admin-Token` | Plaintext `!=` ❌ |

**Critical finding:** `rag.py` and `kg.py` used direct string equality (`!=`) for token comparison, which is vulnerable to timing attacks. This was fixed in Phase S.

---

## 4. Rate Limiting Status (Before Phase S)

| Category | Status |
|---|---|
| Config `rate_limit_per_minute = 30` | Exists but NOT ENFORCED on any route |
| `/api/v1/quran/resolve` | Protected (in-memory, 30/min) |
| All other public endpoints | **NOT PROTECTED** |
| Admin endpoints | **NOT PROTECTED** (auth prevents most abuse) |

---

## 5. Frontend Admin Dashboard

- Admin dashboard (`ReviewDashboardPage.tsx`) reads `VITE_ADMIN_API_KEY` from `.env` at build time
- Auth errors (401, 403) are handled with bilingual error messages (Lock icon, Arabic + English)
- `VITE_ADMIN_API_KEY` is **never hardcoded** in source — loaded via env var
- **WARNING:** Vite env vars are bundled into the frontend build. In a real staging/production deployment, this means the API key is visible in the compiled JS. This is acceptable ONLY for a temporary local/staging setup.
- **Production recommendation:** Use a proper authentication flow (session-based, OAuth, or SSO) where the key never appears in the frontend bundle.

---

## 6. Highest Risks (Before Phase S)

1. **CRITICAL — Timing attack on admin token comparison** (`rag.py`, `kg.py`): Plaintext `!=` comparison allows a timing oracle to discover the token character by character. Fixed in Phase S.

2. **HIGH — No rate limiting on RAG/Ask**: An attacker can issue unlimited LLM calls, causing uncontrolled API costs. Fixed in Phase S (20/min per IP).

3. **MEDIUM — No rate limiting on vocabulary/search**: Can cause DB load spikes. Fixed in Phase S (60/min per IP).

4. **LOW — Reference endpoints under /api/v1/admin/ have no auth**: `/flag-types`, `/entity-types`, `/statuses`, `/decisions` return only static enumeration data with no user content. Risk is informational only.

5. **LOW — VITE_ADMIN_API_KEY in frontend bundle**: In staging deployments, the admin key is visible in the compiled JS. Acceptable for dev/staging; must be replaced with proper auth for public production.

---

## 7. Recommendations Not Implemented in Phase S

- **Redis-backed rate limiting** for distributed deployments (current: in-memory, single-process only)
- **Full audit logging** with reviewer identity, IP, and timestamp for all admin decisions (decisions are logged via `logger.info` but not to a structured audit table)
- **Proper auth for production**: Replace `VITE_ADMIN_API_KEY` with server-side session/OAuth
- **Consolidate admin auth**: The two-mechanism system (X-Admin-API-Key vs. Bearer ADMIN_TOKEN) should eventually be unified
- **Add auth to public reference endpoints** (`/flag-types`, `/entity-types`) if they are moved to a sensitive context

---

## Phase S Changes Applied

See `docs/phase-s-security-hardening.md` for the full implementation record.
