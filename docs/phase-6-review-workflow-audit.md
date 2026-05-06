# Phase 6 – Review Workflow Audit
_Date: 2026-05-05_
_Status: Completed — Implementation ready_

---

## 1. Existing Review Infrastructure

### 1.1 Database-backed Verification Queue

**File:** `backend/app/models/verification.py`

The platform already has a full DB-backed verification queue (`VerificationQueue` table) for **dynamic user-flagged content**:

| Field | Purpose |
|---|---|
| `entity_type` | Enum: concept, story, segment, tafseer, etc. |
| `entity_id` | String ID of flagged entity |
| `flag_type` | Enum: accuracy, source, translation, etc. |
| `status` | pending → in_review → approved/rejected/deferred |
| `reviewed_by` | Reviewer ID |
| `review_decision` | approve/reject/revise/defer/escalate |
| `review_notes` | Bilingual review notes |
| `context_snapshot` | JSONB snapshot at flag time |
| `ai_analysis` | AI assistant result |

**Gap:** This queue handles live user reports. It does not cover the **pre-generated review backlog** — the 321 story segments and 9306 KG edges already flagged as `needs_review` in static data files.

### 1.2 Verification Workflow Service

**File:** `backend/app/verify/workflow.py`

`VerificationWorkflow` class provides: `flag_content()`, `assign_reviewer()`, `submit_review()`, `get_queue()`, `get_stats()`.

**Gap:** No method for bulk-loading or querying pre-generated static review tasks.

### 1.3 Admin API Routes

**File:** `backend/app/api/routes/admin.py`  
**Prefix:** `/api/v1/admin`

Existing endpoints:
- `POST /flag` — flag content (public)
- `GET /verification/queue` — list queue (admin-gated)
- `GET /verification/queue/{id}` — task detail
- `POST /verification/queue/{id}/assign` — assign reviewer
- `POST /verification/queue/{id}/review` — submit decision
- `GET /verification/stats` — queue stats
- `POST /verification/queue/{id}/ai-analyze` — AI analysis

**Gap:** No `/review/tasks` endpoints for the Quran-specific content backlog.

### 1.4 Pydantic Schemas

**File:** `backend/app/api/schemas/concepts.py`

Has `VerificationStatus`, `VerificationTaskCreate`, `VerificationTaskResponse`, `VerificationDecisionCreate`, `VerificationDecisionResponse`, `VerificationStatsResponse`.

These are generic; no Quran-specific content types (`story_segment`, `kg_relation`, etc.).

---

## 2. Content Currently Needing Review

### 2.1 Story Segments (from `frontend/src/data/quranStories.ts`)

| Metric | Count |
|---|---|
| Total story segments | 321+ |
| Segments with `needs_review` | All 321 |
| Segments with disagreement notes | 7 |
| Segments with `humanReviewRequired=true` | All 321 |

Segments with scholarly disagreements (line refs in `quranStories.ts`):
- Kahf sleepers count (18:22)
- Luqman prophethood status
- Ayyub's oath (38:44)
- Dawud's lapse (38:21-26)
- Bani Israel transformation (2:65, 7:166)
- Unnamed army commander
- Ma'idah descent (5:115)

### 2.2 Story Connections (from `data/manifests/stories.json`)

- 73 inter-story connections across 64 stories
- All require review before being shown as authoritative

### 2.3 KG Relations (from `frontend/src/data/generated/quranKnowledgeGraph.json`)

| Edge Type | Count |
|---|---|
| SAME_STORY_SEGMENT | 8,909 |
| SAME_STORY | 231 |
| SAME_THEME | 166 |
| **Total** | **9,306** |

All 9,306 edges have `relationStatus: "needs_review"` and `humanReviewRequired: true`.

Grouped by unique (storyId, segmentId) pair: **261 unique combos** — used as task granularity.

### 2.4 Scholarly Disagreements

7 segments carry explicit `disagreementNotes[]` in `quranStories.ts`. These require priority "high" review tasks.

---

## 3. Gaps Before Phase 6

| Gap | Impact |
|---|---|
| No pre-generated review task inventory | Reviewers can't discover the 321 backlog |
| No Quran-specific content types in entity type enum | story_segment, kg_relation, etc. not representable |
| No review decisions persisted for static tasks | Approvals not tracked anywhere |
| No admin review UI for story/KG content | No workflow surface for reviewers |
| No review status propagation | Approval can't flow to `approved` badge in KG UI |
| No validation of generated review tasks | No CI check on task integrity |

---

## 4. Phase 6 Design

### 4.1 Architecture

```
data/manifests/stories.json              ┐
frontend/src/data/quranStories.ts        │── [generate-review-tasks.ts] ──► backend/app/data/review_tasks.json
frontend/src/data/generated/             ┘
  quranKnowledgeGraph.json

backend/app/data/review_tasks.json ──► backend API (/api/v1/admin/review/tasks)
backend/app/data/review_decisions.json ← POST /decision
                                  │
                                  └──► frontend/src/pages/admin/ReviewDashboardPage.tsx
```

### 4.2 Content Types

| contentType | Source | Est. Task Count |
|---|---|---|
| `story_segment` | quranStories.ts | 321 |
| `related_story` | quranStories.ts relatedStories | 73 |
| `kg_relation` | quranKnowledgeGraph.json edges (grouped by story+segment) | 261 |
| `source_evidence` | segments with < 2 evidence sources | ~30 |
| `disagreement_note` | segments with non-empty disagreementNotes | 7 |

### 4.3 Persistence Model

- **Generated tasks**: `backend/app/data/review_tasks.json` — generated at build time, read-only
- **Review decisions**: `backend/app/data/review_decisions.json` — file-backed stub, written by API
- **Production note**: In production, decisions should migrate to the PostgreSQL `verification_queue` table

### 4.4 Status Propagation (Phase 6.5)

Full status propagation is deferred to Phase 6.5. Phase 6 implements the review task dashboard and decision workflow. Phase 6.5 will propagate decisions back to the KG edge `relationStatus` and story segment `sunniReview.status`.

---

## 5. Safe Implementation Plan

1. Write `scripts/generate-review-tasks.ts` — scans static data, emits stable JSON
2. Write `scripts/validate-review-tasks.ts` — 15+ integrity checks
3. Add `backend/app/api/routes/review_tasks.py` — file-backed REST API
4. Add route to `backend/app/main.py`
5. Write `frontend/src/pages/admin/ReviewDashboardPage.tsx`
6. Add route `/admin/review` to `App.tsx`
7. Add i18n keys to `translations.ts`
8. Write `backend/tests/unit/test_review_workflow_phase6.py`
9. Write implementation + QA docs

**Safety invariants preserved throughout:**
- No Quran text in review task JSON (Quran refs only)
- No auto-approval
- Decision requires reviewerId + notes
- Rejected content never shown as approved
- All existing `needs_review` / `humanReviewRequired` safeguards untouched
