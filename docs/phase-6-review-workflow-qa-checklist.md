# Phase 6 – Review Workflow QA Checklist
_Date: 2026-05-05_

Manual QA checklist for the review workflow.

---

## 1. Review Dashboard Loads

- [ ] Navigate to `/admin/review`
- [ ] Page loads without error
- [ ] Stats panel shows 6 KPI cards with non-zero total
- [ ] Task list displays tasks ordered by priority (high first)
- [ ] Safety notice visible: "لا يعتمد هذا المحتوى إلا بعد مراجعة علمية موثقة."
- [ ] Language toggle switches between AR and EN labels correctly

---

## 2. Filters Work

- [ ] Filter by status "Pending" → shows only pending tasks
- [ ] Filter by status "Approved" → empty list (all initially pending)
- [ ] Filter by content type "Story Segment" → shows story_segment tasks only
- [ ] Filter by priority "High" → shows high-priority tasks only (should include disagreement_note tasks)
- [ ] Toggle "Disagreement Notes Only" → shows 8 tasks with disagreement notes
- [ ] Clear all filters → shows all 914 tasks

---

## 3. Task Card Opens

- [ ] Click a task card → expands to show details
- [ ] Quran references shown in surah:ayah format (no Arabic Quran text)
- [ ] Source IDs listed as code badges
- [ ] Warnings shown in amber boxes
- [ ] Disagreement notes show orange "Disagreement Notes" badge
- [ ] `humanReviewRequired` badge visible
- [ ] Click again → collapses

---

## 4. Disagreement Note Task Detail

- [ ] Open a `disagreement_note` task (filter by content type)
- [ ] Disagreement note text visible in orange box
- [ ] Decision form present (pending task)
- [ ] Note text is in English (no Arabic Quran text)

---

## 5. Approval Blocked Without Notes

- [ ] Open any pending task
- [ ] Decision form visible
- [ ] Notes field empty → Submit button disabled (grayed out)
- [ ] Type < 10 characters in notes → button still disabled, validation message shown
- [ ] Type ≥ 10 characters in notes + enter reviewer ID → button enabled
- [ ] Leave reviewer ID empty → button remains disabled

---

## 6. Rejection Blocked Without Notes

- [ ] Select "Reject" in decision form
- [ ] Leave notes empty → Submit button disabled
- [ ] Add notes (≥ 10 chars) + reviewer ID → Submit enabled
- [ ] Submit rejection → task status changes to "Rejected" (red badge)
- [ ] Rejected task must NOT show green "Approved" badge

---

## 7. Approved Status Only After Valid Decision

- [ ] Select "Approve" in decision form
- [ ] Fill reviewer ID + ≥ 10 char notes
- [ ] Submit → task shows green "Approved" badge
- [ ] Stats panel updates: approved count increases by 1, pending decreases by 1
- [ ] Reload page → decision persists (file-backed)

---

## 8. Arabic/English Labels

- [ ] Switch UI to Arabic → all labels in Arabic (direction RTL)
- [ ] Review task list labels in Arabic
- [ ] Safety notice in Arabic
- [ ] Decision form labels in Arabic
- [ ] Switch back to English → all labels in English (direction LTR)

---

## 9. No Quran Text Mutation

- [ ] Approve a task → verify summaryEnglish field unchanged in API response
- [ ] Verify quranReferences unchanged after approval
- [ ] Verify sourceIds unchanged after approval
- [ ] Run `npx tsx scripts/validate-review-tasks.ts` → 0 errors

---

## 10. Generated Tasks Validate

- [ ] `npx tsx scripts/generate-review-tasks.ts` exits 0
- [ ] `npx tsx scripts/validate-review-tasks.ts` exits 0, 0 errors, 0 warnings
- [ ] `npx tsx scripts/validate-quran-integrity.ts` → 16 passed, 0 failed
- [ ] `npx tsx scripts/validate-quran-knowledge-graph.ts` → all checks pass
- [ ] `python -m pytest` → 1209 passed, 0 failed

---

## 11. API Endpoints Functional (optional — requires backend running)

- [ ] `GET /api/v1/admin/review/tasks` returns 200 with task list
- [ ] `GET /api/v1/admin/review/tasks?status=pending` returns only pending
- [ ] `GET /api/v1/admin/review/tasks?content_type=story_segment` returns story segments
- [ ] `GET /api/v1/admin/review/tasks?priority=high` returns high priority tasks
- [ ] `GET /api/v1/admin/review/stats` returns stats object with all fields
- [ ] `GET /api/v1/admin/review/tasks/{valid_id}` returns 200
- [ ] `GET /api/v1/admin/review/tasks/nonexistent` returns 404
- [ ] `POST /api/v1/admin/review/tasks/{id}/decision` with empty notes returns 422
- [ ] `POST /api/v1/admin/review/tasks/{id}/decision` with 5-char notes returns 422
- [ ] `POST /api/v1/admin/review/tasks/{id}/decision` with valid body returns 200

---

## 12. Remaining Risks

1. File-backed decisions are not concurrent-safe — lock file or migrate to DB for production
2. No auth gate on review endpoints — add `require_admin` before production
3. Phase 6.5 propagation not yet implemented — approved tasks don't update KG or story data
4. `isa_table` appears in two stories — two separate review tasks (correct behavior, intended)
5. `related_story` tasks have empty `quranReferences` — connections don't carry explicit ayah ranges
