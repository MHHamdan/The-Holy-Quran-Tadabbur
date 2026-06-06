# Phase W.2 — Asmā' Allah al-Ḥusnā Count Fix (100 → 99)

**Status**: complete
**Date**: 2026-05-17

## Root cause

`frontend/src/data/asmaAllahSeeds.ts` was seeding **100 entries**:

- 1 entry for the Divine Name `allah` (line 27, "اللَّه")
- 99 entries for the traditional Asmā' al-Ḥusnā (lines 39–137, `ar_rahman` … `as_sabur`)

`scripts/build-asma-allah-atlas.ts` emitted `totalNames = 100`, the backend
`/api/v1/quran/asma` returned `total = 100`, and `frontend/src/pages/AsmaAllahPage.tsx`
built the "All" tab from `data.total`, producing the confusing label `الكل (100)`.

This conflated two distinct lists:

1. The **99 traditional Beautiful Names** that Muslims learn (أسماء الله الحسنى)
2. The **Divine Name "Allah"** (اسم الجلالة) — the supreme Name that the 99 describe

Traditionally these are not the same list. Allah is the Name that *has* 99
beautiful descriptors; it is not itself one of them.

## Selected policy

Keep the primary Asmā' learning list at exactly **99 names** and show the
Divine Name "Allah" in a **separate hero panel** above the grid.

- Main "All" tab label: **الكل (99)** — never 100.
- Category totals (الذات / الجمال / الجلال / الكمال / الأفعال) sum to **99**.
- A separate hero section above the grid renders اسم الجلالة with its Quran
  occurrence summary and a clear note:
  - Arabic: *"اسم الجلالة منفصل عن قائمة الأسماء الـ99"*
  - English: *"The Divine Name Allah is shown separately from the 99 Names list."*
- Quran occurrence evidence for Allah is preserved untouched (≈ 2 539 counted
  occurrences after the surah-opening basmalah exclusion) — the atlas exposes
  it via `divineNameAllah` and the detail route `/asma/allah` still works.

## Files changed

| Path | Change |
|---|---|
| `frontend/src/types/asmaAllah.ts` | Added `inTraditional99?: boolean` to `AsmaAllahSeed`; added `traditionalNamesCount`, `divineNameAllahIncluded`, `allDisplayCount`, `quranEvidenceNamesCount`, `zeroExactOccurrenceNamesCount`, `duplicateNamesRemoved`, `divineNameAllah` fields to `AsmaAtlasOutput`. |
| `frontend/src/data/asmaAllahSeeds.ts` | Tagged the `allah` seed with `inTraditional99: false` and a clarifying warning. |
| `scripts/build-asma-allah-atlas.ts` | Partitions output: `names` array holds the 99 traditional names; `divineNameAllah` carries the standalone Allah record. Throws if the 99 list is not exactly 99 or categories don't sum to 99. Detects duplicate `nameId` and duplicate normalised Arabic forms. Updated summary md. |
| `scripts/validate-asma-allah-atlas.ts` | Added checks: `traditionalNamesCount === 99`, `allDisplayCount !== 100`, no duplicate `nameId`, no duplicate normalised Arabic name, category totals sum to 99, `allah` never inside the 99 list (when `divineNameAllahIncluded` is false), `divineNameAllah` payload present, allah appears at most once when bundled. |
| `backend/app/api/routes/asma.py` | Added `AsmaDivineNameOut`; widened `AsmaListResponse` / `AsmaCategoriesResponse` with the new fields; `_name_index` includes the standalone `divineNameAllah` so `/asma/allah` still resolves; search also matches the divine name. |
| `frontend/src/lib/api.ts` | Mirror new fields in `AsmaListResponse` / `AsmaCategoriesResponse`; added `AsmaDivineName`. |
| `frontend/src/pages/AsmaAllahPage.tsx` | "All" tab now derives its count from `data.allDisplayCount` (= 99) instead of `data.total`; added a separate Divine Name hero panel above the grid with the policy note. |
| `backend/tests/unit/test_asma_allah_atlas.py` | Replaced `total == 100` assertions with `total == 99`; added tests for duplicate nameIds, normalised name dedup, category sum = 99, divine name exposure, the `الكل (100)` regression guard, and the seed `inTraditional99: false` flag. |
| `docs/phase-w2-asma-count-fix.md` | This document. |

## Generated summary additions

The atlas JSON now includes:

```
{
  "traditionalNamesCount": 99,
  "divineNameAllahIncluded": false,
  "allDisplayCount": 99,
  "quranEvidenceNamesCount": 54,
  "zeroExactOccurrenceNamesCount": 45,
  "duplicateNamesRemoved": []
}
```

The `divineNameAllah` field carries the standalone Quran occurrence record
for "الله" (≈ 2 539 counted occurrences, 113 surah-opening basmalah
exclusions, 1 in-ayah basmalah at 27:30 still counted).

## Validation result

```
$ npx tsx scripts/build-asma-allah-atlas.ts
Done. traditional-99=99, allDisplayCount=99, divineNameAllahIncluded=false,
counted=3164, excluded=339, with-occ=54, zero-occ=45, allah-occ=2539

$ npx tsx scripts/validate-asma-allah-atlas.ts
OK — names=99, counted=3164, excluded=339, with-occ=54, zero-occ=45
```

Quran integrity validator (`scripts/validate-quran-integrity.ts`) and the
Python test suite both pass — see PR description for the full check report.

## Quran-content safety

- No Quran text was modified.
- No Names were added or removed; the 99 traditional list is unchanged.
- "Allah" occurrence evidence (≈ 2 539 counted occurrences) is preserved
  exactly as before — only the *presentation* changed.
- All occurrence records remain `needs_review` with `humanReviewRequired: true`.
- The Divine Name policy is documented and surfaced to the UI via
  `divineNameAllah.separateFromListNoteArabic` / `separateFromListNoteEnglish`.

## Phase W.3 — Curated Quranic references + audio player

Extends Phase W.2 with three additions:

1. **Curated Tirmidhi primary references.** A new data file
   `frontend/src/data/asmaAllahQuranicReferences.ts` maps every one of the 99
   Names to its canonical Quranic verse(s) from the Tirmidhi tradition
   (cross-referenced against Wikipedia's *Names of God in Islam* article and
   verified surah:ayah ranges against the local mushaf table). Each entry is
   `needs_review` and carries optional short notes for Names whose lemma is
   hadith-only (e.g. `al_qabid`, `al_baith`). The builder attaches these as
   `primaryQuranicReferences` on every Name and adds `tirmidhi_asma_husna_list`
   to the Name's `sourceIds`.

2. **Source registry entries.** Two new trusted sources added:
   - `tirmidhi_asma_husna_list` — curated Tirmidhi 99-Names reference list.
   - `quran_com_verse_audio` — Mishary Rashid Alafasy per-ayah audio from
     `verses.quran.com/Alafasy/mp3/{SSS}{AAA}.mp3` (Quran.com CDN).

3. **Audio player on the Asmā' page.** A new component
   `frontend/src/components/quran/AsmaAudioPlayer.tsx` streams the primary
   verse of each Name from the Quran.com CDN (reciter attribution required
   and rendered). Play / pause / prev / next with auto-advance through the
   99-Name playlist. The player renders **only** the Name and surah:ayah
   reference — never the Quran text itself.

4. **Light refactor of the builder.** Extracted helpers (`buildNameMap`,
   `basmalahPrefixEnd`, `classifyHit`, `finaliseOccurrenceStats`,
   `attachPrimaryReferences`, `detectSeedDuplicates`, `aggregateCategoryCounts`)
   with no behaviour change. Atlas counts are byte-identical to Phase W.2:
   `traditional-99=99, allDisplayCount=99, counted=3164, excluded=339,
   with-occ=54, zero-occ=45, allah-occ=2539`.

### Validator additions

- Every traditional Name must carry `primaryQuranicReferences.length ≥ 1`.
- Each primary reference must be a valid surah:ayah inside the mushaf.
- No duplicate (surah:ayah) inside a Name's references.
- Names with attached references must list `tirmidhi_asma_husna_list` in `sourceIds`.
- Notes ≤ 250 chars and free of newlines.

### Test additions (`backend/tests/unit/test_asma_allah_atlas.py`)

- All 99 names carry primary refs.
- Primary refs attach the Tirmidhi sourceId.
- Primary refs never carry Quran text (forbidden-key guard).
- `GET /asma/al_ahad` returns 112:1 in its `primaryQuranicReferences`.
- `GET /asma` carries `primaryQuranicReferences` on the row schema.
- Source registry includes both new sources.
- Audio player uses the Quran.com CDN URL pattern and credits the reciter.
- Audio player does not use `dangerouslySetInnerHTML` or reference ayah text.

### Source attribution

- **Tirmidhi list compilation**: based on [Names of God in Islam — Wikipedia](https://en.wikipedia.org/wiki/Names_of_God_in_Islam), which compiles the al-Walīd ibn Muslim / Jāmiʿ al-Tirmidhī 3507 list with its widely-cited verse references.
- **Audio**: per-verse MP3 stream from `verses.quran.com/Alafasy/mp3/` — Mishary Rashid Alafasy, served by [Quran.com](https://quran.com/) via BunnyCDN. Reciter attribution is rendered in the player chrome.

### Final check results

| Check | Result |
|---|---|
| `npx tsx scripts/build-asma-allah-atlas.ts` | OK — 99 names, 240 primary refs attached |
| `npx tsx scripts/validate-asma-allah-atlas.ts` | OK — names=99 |
| `npx tsx scripts/validate-quran-integrity.ts` | 16 passed, 0 failed |
| `npm run typecheck` | clean |
| `npm run build` | built in 21.02s |
| `pytest tests/unit/test_asma_allah_atlas.py` | **34/34 passed** |
| Pure-unit sweep (asma, entity_graph, topic_atlas, coreference, citation_consistency, source_validation, classifier, scientific_safety) | **268/268 passed** |

The 266 failures from the full backend sweep are all DB-dependent tests
(`test_vocabulary_phase_h.py`, etc.) failing because Postgres was not running
in the test environment — unrelated to these changes.
