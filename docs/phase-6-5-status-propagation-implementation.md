# Phase 6.5 – Status Propagation Implementation
_Date: 2026-05-05_
_Status: Complete_

---

## 1. Overview

Phase 6.5 propagates approved/rejected/changes_requested review decisions from the Phase 6 admin workflow back into public display state, without modifying Quran text, story summaries, KG edge data, or tafsir notes.

The propagation is additive and overlay-based: a static JSON file (`reviewStatusOverlay.json`) is generated from the decisions log and bundled into the frontend. The overlay never modifies source files.

---

## 2. Why Overlay-Based Propagation

**Problem:** Approved decisions are stored in `review_decisions.json`. The public UI reads status from static TypeScript files (`quranStories.ts`) and the KG JSON. These files still say `needs_review`.

**Options considered:**

| Approach | Risk | Chosen? |
|---|---|---|
| Rewrite `quranStories.ts` directly | High — TypeScript source modification, requires careful merge, risk of regression | No |
| Rewrite `quranKnowledgeGraph.json` | High — requires re-running KG builder | No |
| DB-backed propagation to `verification_queue` | Medium — requires migration pipeline | Deferred |
| Overlay JSON file (additive layer) | Low — read-only frontend, no source modification | **Yes** |

The overlay approach:
- Never touches Quran text, story content, or KG edges
- Can be regenerated idempotently from decisions
- Falls back to `needs_review` if overlay is missing or malformed
- Easy to audit (diff the overlay file)

---

## 3. Overlay File

**Path:** `frontend/src/data/generated/reviewStatusOverlay.json`

**Format:**
```json
{
  "version": "1",
  "generatedAt": "ISO-8601-timestamp",
  "story_segment": {
    "<segmentId>": {
      "status": "approved | rejected | changes_requested | needs_review | partially_reviewed",
      "reviewerId": "...",
      "reviewerName": "...",
      "reviewedAt": "ISO-8601",
      "notesSummary": "First 100 chars of notes",
      "taskId": "rt_...",
      "warnings": []
    }
  },
  "related_story": { "<source__to__target>": { ... } },
  "kg_relation": { "<groupKey>": { ... } },
  "source_evidence": { "<segmentId>": { ... } },
  "disagreement_note": { "<segmentId>": { ... } }
}
```

**Key design choices:**
- Pending tasks are omitted (frontend defaults to `needs_review`)
- Only non-pending decisions create overlay entries
- `partially_reviewed` status emitted when compound conditions partially met

---

## 4. Propagation Rules

Full rules documented in `docs/phase-6-5-status-propagation-policy.md`.

Key compound rules:
1. **story_segment**: approved only if `disagreement_note` and `source_evidence` (for same segmentId) are also approved. Otherwise: `partially_reviewed`.
2. **KG relation**: approved if the `kg_relation` group task is approved.
3. **Similarity path**: approved if all evidence items' KG relation groups are approved.
4. **Story aggregate**: approved if all segments are approved.

---

## 5. Script: propagate-review-status.ts

**Path:** `scripts/propagate-review-status.ts`

**Inputs:**
- `backend/app/data/review_tasks.json` — 914 review tasks
- `backend/app/data/review_decisions.json` — submitted decisions

**Outputs:**
- `frontend/src/data/generated/reviewStatusOverlay.json`
- `docs/generated/review-status-propagation-summary.md`

**Safety rules enforced:**
- Approved entry requires `reviewerId` (non-empty) + `reviewedAt` + `notes` ≥ 10 chars
- If any required field is missing → entry falls back to `needs_review`
- Rejected entries never marked approved
- No Arabic text allowed in any overlay field (detected and stripped with warning)
- Compound rule enforced: segment + disagreement_note + source_evidence must all be approved

**To regenerate:**
```
npx tsx scripts/propagate-review-status.ts
```

---

## 6. Script: validate-review-status-overlay.ts

**Path:** `scripts/validate-review-status-overlay.ts`

10 checks:
1. Overlay file exists and is valid JSON
2. Required top-level keys present
3. No Arabic Quran text in any text field
4. Every `taskId` in overlay exists in `review_tasks.json`
5. Approved entries have `reviewerId`, `reviewedAt`, `notesSummary`
6. Rejected entries are NOT marked approved
7. `changes_requested` entries are NOT marked approved
8. All `status` values are valid enum members
9. All content type keys are valid
10. Warnings present for rejected/changes_requested entries

**To validate:**
```
npx tsx scripts/validate-review-status-overlay.ts
```

---

## 7. Frontend Utility: reviewStatus.ts

**Path:** `frontend/src/utils/reviewStatus.ts`

**Public API:**

| Function | Returns | Notes |
|---|---|---|
| `getReviewStatus(contentType, contentId)` | `ReviewOverlayStatus` | Defaults to `needs_review` |
| `isApproved(contentType, contentId)` | `boolean` | Only true with valid metadata |
| `isRejected(contentType, contentId)` | `boolean` | Rejected never appears as approved |
| `isChangesRequested(contentType, contentId)` | `boolean` | Not approved |
| `isPartiallyReviewed(contentType, contentId)` | `boolean` | Compound conditions partially met |
| `getReviewEntry(contentType, contentId)` | `ReviewOverlayEntry \| null` | Full entry or null |
| `getApprovalMetadata(contentType, contentId)` | metadata or null | Only for approved entries |
| `getStoryApprovalStatus(segmentIds[])` | aggregate | Approved / partially_reviewed / needs_review |
| `getKGRelationStatus(storyId, segmentId)` | `ReviewOverlayStatus` | GroupKey lookup |
| `mergeBaseStatusWithOverlay(base, overlay)` | merged status | Safe merge logic |
| `getReviewBadgeLabel(status, language)` | translated string | AR + EN |
| `getOverlayMeta()` | version + generatedAt | Admin dashboard indicator |

**Safety guarantees:**
- Default is always `needs_review`
- Approved entries checked for complete metadata before returning `approved`
- Rejected entries never return as `approved`
- `humanReviewRequired` flag preserved (overlay cannot clear it)

---

## 8. UI Changes

### StoryDetailPage

- Imports `getReviewStatus`, `getApprovalMetadata`, `getStoryApprovalStatus`, `mergeBaseStatusWithOverlay`
- Per-segment: checks overlay for `story_segment/{segmentId}`
  - Approved → green "Approved" badge + reviewer metadata
  - Partially reviewed → blue "Partially Reviewed" badge
  - Needs review → existing yellow banner (unchanged)
  - Rejected → hidden (unchanged)
- Story header: aggregate badge showing "All segments approved" or "N/M segments approved"
- Segment border color: green (approved), blue (partial), yellow (needs review)

### KGSimilaritySection

- Imports `getKGRelationStatus`, `ReviewOverlayStatus`
- Evidence items: compute overlay status per `(storyId, segmentId)` group
- Card header badge: approved / partially_reviewed / needs_review based on compound of all evidence items
- `HumanReviewWarning` suppressed when all evidence overlay-approved
- `ReviewStatusBadge` updated to accept `overlayStatus` prop

### ReviewDashboardPage

- Imports `getOverlayMeta`
- Shows overlay freshness indicator (generated timestamp + approved count)
- If all pending: shows "All tasks pending — no decisions submitted yet."
- If decisions exist: shows stale-overlay reminder

---

## 9. Admin Behavior

The admin dashboard shows:
- Overlay last updated timestamp
- How many approved decisions are reflected in the public UI
- Warning to regenerate overlay after new decisions

Full decision notes remain in the admin dashboard; only `notesSummary` (100 chars) appears in the public approved badge.

---

## 10. Limitations

1. **Static import** — Overlay is bundled at build time. New decisions require: run propagation script → rebuild frontend. For real-time: add a server endpoint returning the overlay.

2. **Phase 6.5 deferred DB propagation** — Decisions still not written back to `quranStories.ts`, `quranKnowledgeGraph.json`, or `verification_queue`. The overlay is an additive display layer, not a source-of-truth update.

3. **KG relation granularity** — 418 review tasks cover grouped edges (not individual edges). Approval of a group covers all edges in that group.

4. **No auth gate** — Admin review API still unprotected. Add `require_admin` decorator before production.

5. **File-backed decisions** — `review_decisions.json` is not concurrent-safe for multi-reviewer scenarios.

---

## 11. Future Migration (Phase 6.6+)

When ready for full propagation:

1. **Write back to `quranStories.ts`**: For approved segments, update `sunniReview.status = 'approved'` and set reviewer metadata. Requires TypeScript AST manipulation or JSON manifest rewrite.

2. **Write back to `quranKnowledgeGraph.json`**: For approved kg_relation groups, update edge `relationStatus = 'approved'`. Requires re-running KG builder with decisions applied.

3. **Migrate to DB**: Copy decisions from `review_decisions.json` → `verification_queue` table using `VerificationWorkflow.submit_review()`. This enables real-time status via API.

4. **Remove overlay file**: Once source files are updated, the overlay becomes redundant.

---

## 12. Files Changed (Phase 6.5)

| File | Change |
|---|---|
| `scripts/propagate-review-status.ts` | NEW — generates overlay |
| `scripts/validate-review-status-overlay.ts` | NEW — validates overlay |
| `frontend/src/data/generated/reviewStatusOverlay.json` | NEW — generated (initially all pending, empty overlay) |
| `frontend/src/utils/reviewStatus.ts` | NEW — overlay utility |
| `frontend/src/pages/StoryDetailPage.tsx` | Updated: overlay-aware segment status display |
| `frontend/src/components/quran/KGSimilaritySection.tsx` | Updated: overlay-aware KG relation status |
| `frontend/src/pages/admin/ReviewDashboardPage.tsx` | Updated: overlay freshness indicator |
| `frontend/src/i18n/translations.ts` | Added ~14 Phase 6.5 keys |
| `backend/tests/unit/test_review_status_propagation.py` | NEW — 42 tests across 8 classes |
| `docs/phase-6-5-status-propagation-audit.md` | NEW — audit |
| `docs/phase-6-5-status-propagation-policy.md` | NEW — policy rules |
| `docs/phase-6-5-status-propagation-implementation.md` | NEW — this file |
| `docs/generated/review-status-propagation-summary.md` | NEW — generated summary |
