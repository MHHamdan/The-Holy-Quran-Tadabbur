# Story Atlas — QA Checklist

Use this before shipping any change to `/story-atlas`, `/stories`, or
the story registry generators.

## Data integrity

- [ ] `npx tsx scripts/build-quran-story-registry.ts` exits 0
- [ ] `npx tsx scripts/validate-quran-story-registry.ts` exits 0
- [ ] `npx tsx scripts/build-quran-story-atlas-connections.ts` exits 0
- [ ] `npx tsx scripts/validate-quran-stories.ts` exits 0
- [ ] `npx tsx scripts/validate-quran-integrity.ts` exits 0
- [ ] `npx tsx scripts/validate-quran-prophets-atlas.ts` exits 0

## Backend

- [ ] `python -m pytest backend/tests/unit/test_quran_story_registry.py` passes
- [ ] `GET /api/v1/quran/story-atlas` returns `total > 0`
- [ ] `GET /api/v1/quran/story-atlas/categories` matches the registry enum
- [ ] `GET /api/v1/quran/story-atlas/{story_id}` returns 404 for unknown IDs
- [ ] `GET /api/v1/story-atlas` (legacy) returns 200 (regression test on
      `summary_ar` fix)

## Frontend

- [ ] `/story-atlas` renders a non-zero count
- [ ] Category buttons match the registry enum (no orphans)
- [ ] Each category button shows the correct count
- [ ] Search by title, prophet, entity, or surah number returns matches
- [ ] Filtered-empty state appears only when filters yield no rows
- [ ] Registry-missing state appears only when the JSON is missing
- [ ] Coverage dashboard shows 8 stats
- [ ] Review-warning banner is bilingual

## Cross-page correlation

- [ ] `/stories` count ≤ `/story-atlas` count
- [ ] A story visible on `/stories` is also visible on `/story-atlas`
- [ ] Both pages use the same Arabic / English category labels

## Safety

- [ ] No Quran text embedded in any generated JSON
- [ ] All generated entries are `reviewStatus: needs_review`
- [ ] No registry entry is `verified` while `humanReviewRequired: true`
- [ ] Muhammad ﷺ page carries the "not full biography" warning
- [ ] Dhul-Kifl and Al-Yasa entries are `compact_profile`
