# Phase W — Asmā' Allah QA Checklist

_Run before every release that touches the Asmā' atlas._

## 1. Build / generate

- [ ] `npx tsx scripts/build-asma-allah-atlas.ts` succeeds.
- [ ] `npx tsx scripts/generate-review-tasks.ts` succeeds and reports
      the Phase W content types.

## 2. Validators (all must exit 0)

- [ ] `npx tsx scripts/validate-asma-allah-atlas.ts`
- [ ] `npx tsx scripts/validate-review-tasks.ts`
- [ ] All Phase ECN/U/V validators still pass.

## 3. Tests

- [ ] `pytest backend/tests/unit/test_asma_allah_atlas.py -q` (19 tests).
- [ ] No regressions in `test_quran_entity_graph.py`,
      `test_quran_coreference.py`, `test_quran_topic_atlas.py`.

## 4. Manual spot checks

- [ ] `GET /api/v1/quran/asma` returns `total=100` and at least one
      category with `countedOccurrences > 0`.
- [ ] `GET /api/v1/quran/asma/categories` includes the bilingual
      category labels and the basmalah policy.
- [ ] `GET /api/v1/quran/asma/allah` returns
      `occurrenceCount > 1500` (after basmalah exclusion).
- [ ] `GET /api/v1/quran/asma/allah/occurrences` returns
      `excludedBasmalahCount = 113`.
- [ ] `GET /api/v1/quran/asma/al_aziz` returns the missing-meaning
      bilingual message (no meaning is set yet).

## 5. UI

- [ ] `/themes/asma` renders the hero + category tabs with non-zero
      counts.
- [ ] Each Name card shows Arabic + transliteration + English + counts.
- [ ] `/themes/asma/:nameId` renders the detail view with first/last
      occurrence, pairings, and the basmalah-excluded badge on excluded
      occurrences.
- [ ] The `/themes` Asmā tab now navigates to `/themes/asma`.
- [ ] Arabic labels render with `dir="rtl"`; English with `dir="ltr"`.

## 6. Safety gates

- [ ] No `asma_name` is `reviewStatus="verified"` automatically.
- [ ] No meaning is set by the build script.
- [ ] All `sourceIds` map to `sourceRegistry.ts`.
- [ ] The 113 basmalah-opening occurrences for `Allah` are present as
      `counted=false`.
- [ ] No Quran-text-length string appears in any atlas field.

## 7. Performance

- [ ] Atlas builder completes in <10s on the full Quran.
- [ ] `GET /api/v1/quran/asma` p95 < 100ms (cached).
- [ ] `GET /api/v1/quran/asma/allah/occurrences` p95 < 200ms.
