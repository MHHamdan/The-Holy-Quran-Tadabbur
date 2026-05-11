# Surah Memory Atlas — QA Checklist

## Data Generation

- [ ] `npx tsx scripts/build-surah-memory-atlas.ts` exits with code 0
- [ ] `npx tsx scripts/validate-surah-memory-atlas.ts` exits with code 0 (16 checks)
- [ ] `frontend/src/data/generated/surahMemoryAtlas.json` exists
- [ ] Atlas JSON has exactly 114 entries
- [ ] `docs/generated/surah-memory-atlas-summary.md` was generated

## Data Integrity

- [ ] Al-Fatiha: surahNumber=1, ayahCount=7, pageStart=1, pageEnd=1, juzStart=1
- [ ] Al-Baqara: surahNumber=2, ayahCount=286, juzStart=1, juzEnd=3
- [ ] Al-Baqara: revelationType='madani'
- [ ] Al-Ikhlas: surahNumber=112, ayahCount=4, pageStart=604
- [ ] An-Nas: surahNumber=114, ayahCount=6, quranPosition='ending'
- [ ] All 114 surahs have firstAyahPreview from verified Quran data
- [ ] All 114 surahs have lastAyahPreview from verified Quran data
- [ ] No surah has mainTopicsArabic or mainTopicsEnglish non-empty
- [ ] All reviewStatus values are 'verified', 'needs_review', or 'missing_metadata'
- [ ] All sourceIds are in sourceRegistry.ts

## Source Registry

- [ ] `surah_atlas_metadata` entry exists in sourceRegistry.ts
- [ ] Entry has reliabilityLevel: 'supporting' (not 'canonical' or 'verified')
- [ ] Notes say "needs_review badge" is required

## Integrity Scripts

- [ ] `npx tsx scripts/validate-quran-integrity.ts` still passes
- [ ] `npx tsx scripts/validate-quran-stories.ts` still passes
- [ ] `npx tsx scripts/validate-quran-knowledge-graph.ts` still passes

## Frontend: Route

- [ ] Route `/tools/surah-memory-atlas` is registered in `App.tsx`
- [ ] `SurahMemoryAtlasPage` is lazy-loaded in `App.tsx`
- [ ] Page loads without errors at `/tools/surah-memory-atlas`

## Frontend: ToolsPage Card

- [ ] Card appears on `/tools` page
- [ ] Arabic name: "تذكّر ترتيب السور"
- [ ] English name: "Surah Memory Atlas"
- [ ] Card links to `/tools/surah-memory-atlas`
- [ ] Card shows correctly in both Arabic and English UI modes

## Frontend: List View

- [ ] All 114 surahs appear in list by default
- [ ] Search by Arabic name works
- [ ] Search by transliteration works
- [ ] Search by surah number works
- [ ] Filter by Makki filters correctly
- [ ] Filter by Madani filters correctly
- [ ] Filter by short/medium/long/very_long filters correctly
- [ ] Filter by beginning/early/middle/late/ending filters correctly
- [ ] Result count updates correctly
- [ ] Clear filters button appears when filters active
- [ ] "No results" message shown when no matches

## Frontend: Detail Panel

- [ ] Clicking a surah shows detail panel
- [ ] Surah number displayed
- [ ] Arabic name displayed with RTL dir
- [ ] English transliteration displayed
- [ ] English meaning displayed (with needs_review badge)
- [ ] Revelation type displayed with color badge
- [ ] Ayah count displayed
- [ ] Length category displayed
- [ ] Quran position displayed
- [ ] Juz range displayed (single or range)
- [ ] Page range displayed
- [ ] First ayah reference (e.g., "1:1") displayed
- [ ] Last ayah reference (e.g., "1:7") displayed
- [ ] First ayah preview in Arabic (RTL, font-arabic) displayed
- [ ] Last ayah preview in Arabic (RTL, font-arabic) displayed
- [ ] "Needs review" notice shown for curated metadata
- [ ] Previous surah name/number shown
- [ ] Next surah name/number shown
- [ ] "Read surah" link goes to /quran/{surahNumber}

## Frontend: Visual Map

- [ ] Map view tab works
- [ ] 5 position groups shown (beginning/early/middle/late/ending)
- [ ] Each surah shown as a small colored tile
- [ ] Clicking a tile selects the surah and shows detail
- [ ] Color coding reflects revelation type
- [ ] Map respects active filters

## Frontend: Quiz Mode

- [ ] Quiz tab loads
- [ ] Question is displayed
- [ ] "Show Answer" button reveals the answer
- [ ] "Correct" button increments score and loads next question
- [ ] "Try Again" loads next question without incrementing score
- [ ] Score counter shown (X/Y format)
- [ ] "Different question" button generates new question
- [ ] All 6 question types can appear
- [ ] Quiz works in Arabic mode (RTL)

## Frontend: Bilingual

- [ ] All UI elements display correctly in Arabic mode
- [ ] All UI elements display correctly in English mode
- [ ] Arabic text uses dir="rtl"
- [ ] English text uses dir="ltr"
- [ ] Mixed content uses explicit dir attributes per element
- [ ] No layout breakage in RTL mode

## Frontend: Safety Badges

- [ ] "Needs review" badge shown on all curated metadata (Makki/Madani, English meaning)
- [ ] "Needs review" message shown in detail panel
- [ ] No data displayed as "verified" unless it comes from quran_uthmani.json

## Python Tests

- [ ] `python -m pytest backend/tests/unit/test_surah_memory_atlas.py -v` → 34 passed
- [ ] No new test failures introduced

## Build

- [ ] `npm run typecheck` passes with 0 errors
- [ ] `npm run lint` passes with 0 warnings
- [ ] `npm run build` completes successfully
- [ ] SurahMemoryAtlasPage appears in build output

---

*QA Checklist created: 2026-05-10*
