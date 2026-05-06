# Phase 6.5 – Status Propagation Policy
_Date: 2026-05-05_

This document defines the rules governing how review decisions propagate into public display state for the Tadabbur Al-Quran platform.

---

## 1. Approval Propagation Rules

A content item may display the **approved** status in public UI only when ALL of the following are true:

1. The matching review task `status` = `"approved"`
2. The task `decision.status` = `"approved"`
3. `decision.reviewerId` exists and is non-empty
4. `decision.reviewedAt` exists and is a valid ISO 8601 timestamp
5. `decision.notes` exists and is non-empty (≥ 10 characters)

If any condition fails, the item displays as `needs_review` regardless of task status.

Approval **only changes** the following fields in the overlay:
- `status` (review metadata field)
- `reviewerId`, `reviewerName`, `reviewedAt`, `notesSummary` (audit metadata)

Approval **never modifies**:
- Quran text in any form
- Story summaries (`summaryKidsArabic`, `summaryAdultsArabic`, etc.)
- KG edge data (`edgeType`, `sourceNodeId`, `targetNodeId`)
- Tafsir notes or disagreement notes
- `sourceIds` or evidence references
- Any Arabic text field

---

## 2. Rejection Propagation Rules

1. A rejected item **must not display as approved** — ever.
2. In public UI, rejected content is either:
   - **Hidden** (if the content is a story segment: `isRejected = true` → `return null` in UI), or
   - Shown only in admin views with a clear `rejected` badge
3. Rejected content must not appear in "approved" filters.
4. The overlay entry for a rejected task: `status = "rejected"`.
5. The frontend utility `isApproved()` returns `false` for rejected entries.
6. Rejected items retain all safety warnings for admin visibility.

---

## 3. Changes Requested Rules

1. `changes_requested` means the task is **not approved**.
2. Public UI continues to show `needs_review` or `humanReviewRequired` state.
3. Admin UI shows the reviewer's notes indicating what changes are required.
4. The overlay entry for a `changes_requested` task: `status = "changes_requested"`.
5. The utility `isApproved()` returns `false`; `isChangesRequested()` returns `true`.

---

## 4. Compound Relation Rules

### Story segment approval

A story segment entry in the overlay may show `approved` only if:
- Its `story_segment` task is approved (with valid metadata), **AND**
- If a `disagreement_note` task exists for the same `segmentId`, it is also approved, **AND**
- If a `source_evidence` task exists for the same `segmentId`, it is also approved

If `story_segment` is approved but `disagreement_note` for the same segment is still pending → overlay status = `"partially_reviewed"`.

If `story_segment` is approved but `source_evidence` for the same segment is still pending → overlay status = `"partially_reviewed"`.

### Related story approval

A related story entry may show `approved` only if:
- Its `related_story` task is approved with valid metadata.
- There is no additional compound requirement (connections don't carry segment-level review state).

### KG relation approval

A KG relation group may show `approved` only if:
- Its `kg_relation` task for the `(storyId, segmentId)` groupKey is approved with valid metadata.
- Individual edge approval is not tracked (grouped by story+segment combo).

### Similarity path approval

A KG similarity path between two ayahs may show `approved` only if:
- All path edges map to approved `kg_relation` entries in the overlay.
- If any path edge's evidence item maps to a `needs_review` or pending KG relation → path remains `needs_review`.
- Mixed → `partially_reviewed`.

### Story-level aggregate

A story detail page may show a "Fully Reviewed" indicator only if:
- Every visible segment has an approved `story_segment` overlay entry.
- Every visible segment's `disagreement_note` and `source_evidence` (if they exist) are also approved.
- If partial: show "Partially reviewed" with segment count (e.g., "3 of 5 segments reviewed").

---

## 5. Auditability

The public approved badge **should display**:
- `reviewerName` if available, otherwise `reviewerId`
- `reviewedAt` date (formatted by locale)
- `notesSummary` (first 100 chars of notes) — optional, admin-controlled

Full decision notes remain in the admin dashboard only.

---

## 6. Safety Default

| Scenario | Display state |
|---|---|
| No review task exists for this content | `needs_review` |
| Task exists but is `pending` | `needs_review` |
| Task `approved` but `reviewerId` missing | `needs_review` |
| Task `approved` but `reviewedAt` missing | `needs_review` |
| Task `approved` but `notes` empty | `needs_review` |
| Overlay file missing | `needs_review` |
| Overlay entry malformed | `needs_review` |
| Task `rejected` | `rejected` (never `approved`) |
| Task `changes_requested` | `changes_requested` |
| Compound: segment approved, disagreement pending | `partially_reviewed` |
| Compound: all conditions met | `approved` |

**The safety default is always `needs_review`.** The overlay can only move a status toward `approved` if all required metadata is present and valid. It can never remove a `humanReviewRequired` flag.

---

## 7. Implementation Boundaries

| Allowed | Not Allowed |
|---|---|
| Overlay adds review metadata to display | Overlay modifies Quran text |
| Overlay changes `status` field for display | Overlay rewrites segment summaries |
| Overlay shows reviewer name and date | Overlay removes source attribution |
| Overlay marks rejected items as rejected | Overlay marks rejected items as approved |
| Overlay marks pending as needs_review | Overlay auto-approves any content |
| Admin dashboard shows overlay freshness | Admin dashboard weakens review requirement |

---

## 8. Re-generation Trigger

The overlay must be regenerated whenever:

1. A review decision is submitted via `POST /api/v1/admin/review/tasks/{id}/decision`
2. After any change to `backend/app/data/review_decisions.json`

**Re-generation command:** `npx tsx scripts/propagate-review-status.ts`

After re-generation, a frontend rebuild is required for the new overlay to take effect in the browser bundle. For production: automate the re-generation + rebuild pipeline.

---

## 9. Validation Requirements

The overlay is considered valid only if:

1. Overlay JSON is parseable
2. No Arabic Quran text (5+ char Arabic sequence) in any text field
3. Every `taskId` in overlay exists in `review_tasks.json`
4. Approved entries have `reviewerId`, `reviewedAt`, `notesSummary`
5. Rejected entries do not have `status = "approved"`
6. `changes_requested` entries do not have `status = "approved"`
7. All `status` values are valid enum members
8. Compound path approval requires all edge tasks approved (if path overlay implemented)

Validation command: `npx tsx scripts/validate-review-status-overlay.ts`
