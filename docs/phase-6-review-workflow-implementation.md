# Phase 6 – Review Workflow Implementation
_Date: 2026-05-05_
_Status: Complete_

---

## 1. Overview

Phase 6 introduces a controlled Review & Approval Workflow for all Quran-sensitive content pending scholarly verification.

The workflow surfaces the **914-task backlog** of story segments, KG relations, and disagreement notes in an admin dashboard, allowing qualified reviewers to inspect, approve, reject, or request changes with full audit trails.

---

## 2. Content Types Reviewed

| contentType | Source | Count |
|---|---|---|
| `story_segment` | `data/manifests/stories.json` | 321 |
| `related_story` | `data/manifests/stories.json` connections | 73 |
| `kg_relation` | KG edges grouped by (storyId, segmentId) | 418 |
| `source_evidence` | Segments with < 2 canonical sources | 167 |
| `disagreement_note` | Segments with scholarly disagreement notes | 8 |
| **Total** | | **914** |

---

## 3. Task Generation Logic

**Script:** `scripts/generate-review-tasks.ts`

1. Reads `data/manifests/stories.json` for all segments, connections, and evidence
2. Reads `frontend/src/data/generated/quranKnowledgeGraph.json` for KG edges
3. For each content item with `needs_review: true`, generates one task with:
   - Stable SHA-256 task ID (deterministic from `contentType:contentId`)
   - Quran references (surahNumber + ayahStart/End — no text)
   - Source IDs from evidence metadata
   - Warnings from content type rules
   - `humanReviewRequired: true` for all tasks
   - `status: "pending"` (never auto-approved)
4. Deduplicates on `(contentType, contentId)` for idempotent re-generation
5. KG edges grouped by `(storyId, segmentId)` combo — not individual edges — to keep task count manageable
6. `disagreement_note` tasks carry the scholarly disagreement text (English only, no Arabic Quran text)

**Output:**
- `backend/app/data/review_tasks.json` — 914 tasks
- `docs/generated/review-tasks-summary.md`

---

## 4. Validation Rules

**Script:** `scripts/validate-review-tasks.ts`

15 checks enforced:
1. Task file non-empty
2. Each task has valid `id`, `contentType`, `contentId`, `status`
3. Priority and language are valid enums
4. No duplicate `(contentType, contentId)` pairs
5. No duplicate task IDs
6. Quran references: surahNumber 1–114, ayahStart ≥ 1
7. Source IDs from known tafseer sources (warnings for unknowns)
8. Approved tasks must have `decision.reviewerId`, `decision.reviewedAt`, `decision.notes`
9. Rejected tasks must have `decision.notes`
10. No Arabic Quran text in any text field (5+ char Arabic sequence = fail)
11. `humanReviewRequired=true` for all pending tasks
12. `disagreement_note` tasks have non-empty `disagreementNotes`
13. ISO 8601 timestamps on `createdAt`/`updatedAt`
14. Status enum validation
15. Unique task IDs

---

## 5. Approval Rules

- Approval requires `reviewerId` (non-empty) + `notes` (min 10 chars)
- Rejection requires `notes` (min 10 chars)
- Changes requested requires `notes` (min 10 chars)
- Decision only updates review metadata fields:
  - `status`, `reviewedAt`, `reviewerId`, `reviewerName`, `decision`
  - **Never modifies**: `summaryEnglish`, `quranReferences`, `sourceIds`, `storyId`, `segmentId`, `disagreementNotes`
- `humanReviewRequired` flag preserved in all responses (set by content source, not clearable via decision API)
- Every decision is timestamped and audit-logged to `backend/app/data/review_decisions.json`

---

## 6. Rejection Rules

- Rejected tasks have `status: "rejected"` — never `"approved"`
- Decision form prevents submitting "approved" and "rejected" simultaneously
- Frontend shows "Rejected" badge (red) — never green "Approved" badge for rejected items
- Rejected content must not appear in "approved" filter

---

## 7. Auditability

Every review decision is persisted to `backend/app/data/review_decisions.json`:

```json
{
  "rt_storysegment_aabbccdd": {
    "status": "approved",
    "notes": "Reviewed against Ibn Kathir and Tabari. Summary is accurate.",
    "reviewerId": "scholar_001",
    "reviewerName": "Dr. Ahmad",
    "reviewedAt": "2026-05-05T12:34:56.789Z"
  }
}
```

On server restart, decisions are merged back into tasks from the decisions file, ensuring persistence across restarts.

---

## 8. Status Propagation Rules

**Phase 6 implements:** Review task status updates (pending → approved/rejected/changes_requested).

**Phase 6.5 (complete):** Overlay-based propagation — approved decisions flow into a static overlay JSON file that the frontend reads at bundle time. Source files (`quranStories.ts`, `quranKnowledgeGraph.json`) are NOT modified. See: `docs/phase-6-5-status-propagation-implementation.md`.

**Phase 6.5 propagates:**
- `reviewStatusOverlay.json` → `story_segment`, `related_story`, `kg_relation`, `source_evidence`, `disagreement_note` approved/rejected/changes_requested status
- `StoryDetailPage`: approved segments show green badge + reviewer metadata
- `KGSimilaritySection`: approved KG groups show green badge
- `ReviewDashboardPage`: overlay freshness indicator

**Phase 6.6 (deferred):** Full write-back to source files:
- `stories.json` segment `needs_review` flag → clear when approved
- `quranKnowledgeGraph.json` edge `relationStatus` → change to `"approved"` when approved
- `quranStories.ts` `sunniReview.status` → change to `"approved"` when approved
- DB migration: `review_decisions.json` → `verification_queue` PostgreSQL table

**Rationale for continued deferral of write-back:** Rewriting TypeScript and JSON source files requires careful merge logic and re-running the KG builder. The overlay-based approach achieves safe public display without touching source files, deferring the more complex write-back to Phase 6.6.

---

## 9. Persistence Model

| Store | Type | Purpose |
|---|---|---|
| `backend/app/data/review_tasks.json` | File-backed read-only | Generated tasks (source of truth for review backlog) |
| `backend/app/data/review_decisions.json` | File-backed read-write | Decision audit log |
| `verification_queue` (PostgreSQL) | DB-backed | Dynamic user-flagged content (existing system, Phase 1–5) |

**Production migration path:** Copy decisions from `review_decisions.json` into `verification_queue` using existing `VerificationWorkflow.flag_content()` + `submit_review()` methods. The file-backed store is clearly documented as a development/review workflow stub.

---

## 10. API Endpoints

All endpoints at prefix `/api/v1/admin`:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/review/tasks` | List tasks with filters |
| `GET` | `/review/tasks/{task_id}` | Task detail |
| `POST` | `/review/tasks/{task_id}/decision` | Submit decision |
| `GET` | `/review/stats` | Dashboard statistics |
| `GET` | `/review/content-types` | Valid content types with labels |

**Filters on GET /review/tasks:**
- `content_type`, `status`, `priority`, `source_id`
- `has_disagreement` (bool), `human_review_required` (bool), `story_id`
- `limit`, `offset` (pagination)

**Decision body:**
```json
{
  "status": "approved | rejected | changes_requested",
  "notes": "required, min 10 chars",
  "reviewerId": "required",
  "reviewerName": "optional"
}
```

---

## 11. Admin UI

**Route:** `/admin/review`  
**Component:** `frontend/src/pages/admin/ReviewDashboardPage.tsx`

Features:
- Stats panel (6 KPI cards: total, pending, approved, rejected, high-priority, disagreements)
- Filter panel (status, content type, priority, disagreement toggle)
- Task list with priority-first ordering
- Per-task expandable card showing: content type, status, priority, Quran refs, source IDs, warnings, disagreement notes
- Decision form with reviewer ID, reviewer name, decision status, notes (required, 10 char min)
- Submit button disabled until notes ≥ 10 chars
- Arabic/English bilingual (RTL/LTR correct)
- Safety notice displayed on every page load

---

## 12. Authentication (Phase Security — updated 2026-05-06)

All admin routes are now protected by `X-Admin-API-Key` header authentication.

| Header | Value |
|---|---|
| `X-Admin-API-Key` | Value of `ADMIN_API_KEY` environment variable |

**Reviewers accessing the dashboard in staging** must:
1. Obtain the `ADMIN_API_KEY` value from the platform administrator (never shared publicly).
2. Set `VITE_ADMIN_API_KEY` in the frontend `.env` to the same value before building.
3. Alternatively, use `curl -H "X-Admin-API-Key: <key>"` for direct API access.

See `docs/admin-authentication-implementation.md` for full setup instructions.

---

## 13. Limitations

1. **File-backed decisions** — not suitable for multi-reviewer concurrent access at scale
2. **Phase 6.5 propagation deferred** — approved tasks don't yet update KG/stories data files
3. **Shared admin key** — all reviewers use the same key; replace with per-reviewer JWT before production
4. **Decisions file grows unbounded** — add periodic archival in production
5. **isa_table appears in multiple stories** — `story_isa` and `story_isa_miracles` both have `isa_table` segment → two review tasks generated (this is correct — each story+segment combo is a separate task)
