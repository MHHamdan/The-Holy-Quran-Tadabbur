# Whole-Quran Story Connection — QA Checklist

Run this checklist before promoting any reviewer-approved connections to
production or before merging changes that touch the connection layer.

---

## A. Data integrity

- [ ] `npx tsx scripts/validate-quran-integrity.ts` exits 0.
- [ ] `npx tsx scripts/validate-quran-stories.ts` exits 0.
- [ ] `npx tsx scripts/validate-quran-knowledge-graph.ts` exits 0.
- [ ] `npx tsx scripts/validate-quran-story-connections.ts` exits 0.
- [ ] `npx tsx scripts/validate-quran-story-connection-graph.ts` exits 0.
- [ ] `npx tsx scripts/validate-quran-story-chronology.ts` exits 0.
- [ ] `python -m pytest backend/tests/unit/test_quran_story_connections.py`
      passes all assertions.

## B. Frontend integrity

- [ ] `cd frontend && npm run typecheck` exits 0.
- [ ] `cd frontend && npm run lint` exits 0.
- [ ] `cd frontend && npm run build` succeeds.
- [ ] `/story-atlas/connections` renders without console errors in both
      Arabic (RTL) and English (LTR) modes.
- [ ] All 5 tabs (surahs, entities, graph, repeated, chronology) load on
      first paint without network requests beyond static JSON.

## C. Reviewer policy

- [ ] No edge with `reviewStatus: 'verified'` lacks `evidenceReferences`.
- [ ] No edge claims `verified` while `humanReviewRequired = true`.
- [ ] No revelation-order entry claims `verified` (those must go through the
      reviewer workflow in `/admin/review`).
- [ ] No new chronology-group `itemId` was added without an entity referencing
      it.

## D. Content policy

- [ ] No Quran text was added to any TypeScript or JSON file under
      `frontend/src/data/`.
- [ ] No new sourceId was added without a matching entry in
      `frontend/src/data/sourceRegistry.ts`.
- [ ] No chronology entry uses an absolute year or claims certainty above
      the Sunni-mainstream agreement level.

## E. UX correctness

- [ ] Surah explorer lists all 114 surahs.
- [ ] Entity explorer search returns expected results for "Musa", "Ibrahim",
      "Maryam", "موسى", "إبراهيم" in both languages.
- [ ] Graph view shows the `needs_review` filter working.
- [ ] Repeated narrative view shows ≥ 20 cross-surah candidates.
- [ ] Chronology view shows the dispute banner in both languages.

## F. Memory + regression

- [ ] No previously-passing test is now failing.
- [ ] `backend/tests/unit/test_quran_integrity.py` still passes.
- [ ] `backend/tests/unit/test_story_atlas.py` still passes.
- [ ] No new files appear under `frontend/src/data/generated/` that are not
      committed.
