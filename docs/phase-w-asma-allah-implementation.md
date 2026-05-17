# Phase W — Asmā' Allah Atlas — Implementation Notes

_Last updated: 2026-05-17_

## What Phase W ships

- A **100-entry seed list** (99 traditional names + Allah).
- A **whole-Quran atlas builder** that detects occurrences with strict
  right-side word-boundary checking and Arabic-clitic-prefix handling
  for "Allah".
- A **basmalah-counting policy** (documented in
  `asma-basmalah-counting-policy.md`) that excludes the 113
  surah-opening basmalahs from name counts (3 × 113 = **339** excluded
  occurrences, kept visible as `counted=false` records).
- A static atlas at `frontend/src/data/generated/asmaAllahAtlas.json`
  with **3,164 counted occurrences** spread across **55 names with
  Quran evidence** and **45 names with zero explicit evidence**.
- **6 backend API endpoints** under `/api/v1/quran/asma/*` with cache
  headers, all reading the static atlas.
- **2 React routes** (`/themes/asma`, `/themes/asma/:nameId`) with hero,
  category tabs (with non-zero counts), search, filters, beautiful Name
  cards, detail view, occurrences list with basmalah badges, pairings,
  related topics.
- **5 new review-task content types** (`asma_name`, `asma_meaning`,
  `asma_category`, `asma_occurrence`, `asma_pairing`) — **3,620 new
  tasks** added to the workflow.

## Detection method

The build script (`scripts/build-asma-allah-atlas.ts`) uses the same
normalisation pipeline as every other Phase scanner:

```ts
function normaliseArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')   // strip tashkeel + dagger-alif
    .replace(/[آأإٱ]/g, 'ا')           // unify alif variants
    .replace(/ى/g, 'ي')                // alif-maqsura → ya
    .replace(/ة/g, 'ه')                // ta-marbuta → ha
    .replace(/ء/g, '')                 // drop stand-alone hamza
    .trim();
}
```

For each alias, the script finds occurrences with:

1. Right-side word boundary: the character after the match must not be
   an Arabic letter.
2. Left-side word boundary: either a non-letter, OR (for `الله` only) a
   recognised Arabic clitic prefix from the allowlist:
   `[ل, و, ف, ب, ك, س, لو, فل, ول, وب, فب, بل, وك]`.

This makes `الله` match in `بالله / لله / والله / فلله / كالله` — but
NOT inside arbitrary substrings.

## Match types

| matchType | Meaning |
|---|---|
| `exact_name` | The alias matched at a word boundary and is not a clitic-prefixed form. |
| `definite_form` | The alias matched after an accepted Arabic clitic prefix (only for `Allah`). |
| `name_pairing` | Reserved for two-name compound forms (e.g. `مالك الملك`). |
| `contextual_attribute` | Reserved for attribute-style contextual matches (reviewer-promoted). |
| `basmalah_excluded` | The occurrence falls inside the surah-opening basmalah and is excluded from the count. |
| `needs_review` | Reserved for ambiguous / reviewer-triaged matches. |

## Categories

The five traditional categories (mirroring `backend/app/data/allah_names.py`):

- `dhat` (الذات)
- `jamal` (الجمال)
- `jalal` (الجلال)
- `kamal` (الكمال)
- `afaal` (الأفعال)

Plus `unknown` for any unclassified entries. Categories travel with seed
entries but the **atlas marks them as `needs_review`** until a verified
source is attached.

## Meaning / source policy

The atlas **never emits meanings**. Meanings remain undefined in the
generated JSON. The API returns a bilingual safe message when no meaning
is set:

- Arabic: `لا يتوفر معنى موثوق لهذا الاسم حالياً.`
- English: `No verified meaning is available for this Name yet.`

Reviewers attach meanings via the review workflow; the validator rejects
any name that is marked `verified` without a non-Quran source attached.

## Pairings

The build script records every pair of distinct counted names co-occurring
in the same ayah, then sorts pairings by count. The pairing pool excludes
`Allah ↔ X` pairings (Allah co-occurs with nearly everything; including
those would dominate the list). Result:

| Pairing | Count |
|---|---:|
| al_aziz ↔ al_hakim (العزيز الحكيم) | 29 |
| al_alim ↔ as_sami (السميع العليم) | 15 |
| al_aziz ↔ ar_raheem (العزيز الرحيم) | 13 |
| al_ghafur ↔ ar_raheem (الغفور الرحيم) | 8 |
| ar_raheem ↔ ar_rahman (الرحمن الرحيم) | 5 |
| ... | ... |

## Review workflow

| contentType | Default priority | Notes |
|---|---|---|
| `asma_name` | medium (high for dhat/jalal) | Name-level approval. |
| `asma_meaning` | high | Meaning claims require a trusted source. |
| `asma_category` | medium | Reviewer confirms the category. |
| `asma_occurrence` | low (medium for contextual) | Each counted occurrence. |
| `asma_pairing` | medium | Each pairing. |

## Limitations

- The atlas does not cover hadith-only names (`القابض / الباسط /
  الخافض / الباعث / الواجد / الماجد / المقدم / المؤخر / المقسط / المغني
  / المانع / الضار / النافع / الصبور / المعز / المذل / المحصي / المبدئ
  / المعيد / المميت`) — these are seeded with warnings and show
  `occurrenceCount = 0`.
- Some Quranic names overlap with non-divine usages (e.g. `العزيز`
  appears as Aziz of Egypt in Surah Yusuf, `الملك` as "the dominion").
  The atlas surfaces every match; reviewers decide which occurrences are
  divine-name usages.
- The atlas relies on surface-form matching; future work can integrate
  morphological tags to filter occurrences by case + definiteness.

## Future improvements

- Trusted Asmā' source integration (e.g. As-Saadi's *Tafsir al-Karim
  al-Rahman fi Asma' Allah al-Husna*) registered in
  `sourceRegistry.ts` to enable meaning approval at scale.
- Tafsir-based meaning display via the `/api/v1/tafseer` RAG path.
- Audio recitation per Name (subject to per-reciter terms).
- Printable memorization sheets and classroom mode.
- Asma' as a Phase V topic sub-taxonomy under `topic_allah`.

## Source code map

- Types: `frontend/src/types/asmaAllah.ts`
- Seeds: `frontend/src/data/asmaAllahSeeds.ts`
- Builder: `scripts/build-asma-allah-atlas.ts`
- Validator: `scripts/validate-asma-allah-atlas.ts`
- Backend: `backend/app/api/routes/asma.py`
- UI: `frontend/src/pages/AsmaAllahPage.tsx` + `AsmaAllahDetailPage.tsx`
- Review tasks: `scripts/generate-review-tasks.ts` (Phase W section)
- Tests: `backend/tests/unit/test_asma_allah_atlas.py`
- Docs:
  - `docs/phase-w-asma-allah-audit.md`
  - `docs/phase-w-asma-reference-audit.md`
  - this file
  - `docs/phase-w-asma-allah-qa-checklist.md`
  - `docs/asma-name-detection-policy.md`
  - `docs/asma-basmalah-counting-policy.md`
  - `docs/asma-review-guide.md`
