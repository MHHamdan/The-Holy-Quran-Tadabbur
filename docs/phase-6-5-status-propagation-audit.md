# Phase 6.5 – Status Propagation Audit
_Date: 2026-05-05_

---

## 1. Scope

Phase 6 generated 914 review tasks covering story segments, KG relations, related stories, source evidence, and disagreement notes. When a reviewer approves or rejects a task via the admin dashboard, the decision is stored in `backend/app/data/review_decisions.json`. Phase 6.5 propagates those decisions into a frontend-readable overlay file so public UI can display the correct review state.

---

## 2. How Task IDs Map to Content IDs

| contentType | contentId format | Example | Maps to |
|---|---|---|---|
| `story_segment` | `segmentId` | `adam_creation` | `QuranStory.storySegments[].segmentId` in `quranStories.ts` |
| `disagreement_note` | `segmentId` | `kahf_lessons` | Same segment, disagreement path |
| `source_evidence` | `segmentId` | `luqman_wisdom` | Same segment, evidence path |
| `related_story` | `{source}__to__{target}` | `story_adam__to__story_musa` | `QuranStory.relatedStories[].storyId` pair |
| `kg_relation` | `story:{storyId}:{segmentId}` | `story:story_adam:adam_creation` | `quranKnowledgeGraph.json` edges grouped by story+segment |

Task IDs are stable SHA-256 hashes: `rt_{contenttype}_{8hexchars}`.

---

## 3. Which Content Types Can Be Propagated Now

### Fully propagatable

**`story_segment`** — Direct `segmentId` → `QuranStory.storySegments[].segmentId` match. The overlay can update display status without modifying `quranStories.ts`.

**`disagreement_note`** — Same `segmentId` key. Approval means the scholarly disagreement note has been reviewed; compound with `story_segment` approval.

**`source_evidence`** — Same `segmentId` key. Approval means evidence sufficiency has been confirmed.

**`related_story`** — `source__to__target` format. Compounds across both involved stories' review state.

**`kg_relation`** — GroupKey `story:{storyId}:{segmentId}` maps to KG evidence items in `quranKnowledgeGraph.json`. The `KGRelatedAyah.evidence[].storyId` + `segmentId` fields can be used to look up the overlay.

### Deferred (Phase 6.6+)

None from a propagation perspective — all five content types can be covered by the overlay.

**What remains deferred:**
- Writing back to `quranStories.ts` source file (modifies TypeScript source, higher risk)
- Writing back to `quranKnowledgeGraph.json` source file (re-generation required)
- DB-backed propagation to `verification_queue` PostgreSQL table

---

## 4. Current Public Display Behavior

| Surface | Current behavior | Phase 6.5 target |
|---|---|---|
| `StoryDetailPage` segments | Yellow "Pending Review" banner on every segment | Approved segments show green "Approved" badge with reviewer metadata; banner removed for approved |
| `StoryDetailPage` related stories | Yellow "Pending Review" section header | Approved connections show green badge |
| `KGSimilaritySection` | `needs_review` amber badge on all relations | Approved KG group shows green badge; mixed → `partially_reviewed` |
| `ReviewDashboardPage` | No link to overlay state | Overlay freshness indicator added |

---

## 5. Risks

1. **Stale overlay** — If reviewer approves a task but the propagation script hasn't been re-run, the frontend still shows `needs_review`. Solution: document the re-run requirement; flag stale overlay in admin UI.

2. **Compound state edge case** — A `story_segment` approved but matching `disagreement_note` still pending → show `partially_reviewed`, not `approved`. This is the conservative default.

3. **Overlay does not modify source files** — `quranStories.ts` and `quranKnowledgeGraph.json` still have `needs_review` in their source data. Overlay is an additive layer; removing it reverts display to `needs_review`.

4. **Static import at build time** — Overlay is bundled as a static JSON import. Changes to overlay require a frontend rebuild to take effect. For production, this is acceptable; for real-time review updates, a separate API call should be added.

5. **KG relation grouping** — Individual KG edges (9306) are grouped into 418 review tasks. Approval of a `kg_relation` task covers all edges in that group. If some edges in a group are more controversial than others, the group granularity may be insufficient.

6. **No auth gate** — Review endpoints do not require admin authentication (documented in Phase 6). Decisions could be submitted by any user. This must be fixed before production.

---

## 6. Recommended Propagation Strategy

**Use overlay-based propagation (Phase 6.5):**
- Generate `frontend/src/data/generated/reviewStatusOverlay.json` from `review_tasks.json` + `review_decisions.json`
- Frontend utility reads overlay at module load time (static JSON import)
- Safety default: no overlay entry → `needs_review`
- Approved overlay entry with incomplete metadata → `needs_review` (conservative)
- Rejected overlay entry → never displays as `approved`

**Deferred (Phase 6.6+):**
- Write-back to `quranStories.ts` / `quranKnowledgeGraph.json` source files
- DB-backed propagation
- Real-time overlay refresh without rebuild

---

## 7. Files Requiring Changes

| File | Change | Risk |
|---|---|---|
| `scripts/propagate-review-status.ts` | NEW — generates overlay | Low |
| `scripts/validate-review-status-overlay.ts` | NEW — validates overlay | Low |
| `frontend/src/utils/reviewStatus.ts` | NEW — overlay reader/utility | Low |
| `frontend/src/data/generated/reviewStatusOverlay.json` | NEW — generated overlay | Low |
| `frontend/src/pages/StoryDetailPage.tsx` | Guard approved badge behind overlay check | Low |
| `frontend/src/components/quran/KGSimilaritySection.tsx` | Guard approved state behind overlay | Low |
| `frontend/src/pages/admin/ReviewDashboardPage.tsx` | Add overlay freshness indicator | Low |
| `frontend/src/i18n/translations.ts` | Add ~10 Phase 6.5 keys | Low |
| `backend/tests/unit/test_review_status_propagation.py` | NEW — overlay tests | None |
