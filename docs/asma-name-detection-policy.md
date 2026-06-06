# Asmā' Name Detection Policy

_Last updated: 2026-05-17_

## Scope

Governs `scripts/build-asma-allah-atlas.ts` and the validator
`scripts/validate-asma-allah-atlas.ts`.

## Surface forms

- The scanner reads each alias from `asmaAllahSeeds.ts::aliasesArabic`.
- Each alias and each ayah token is normalised through the same
  `normaliseArabic` pipeline:
  - Strip tashkeel + dagger-alif (`[ً-ٰٟؐ-ؚۖ-ۭـ]`).
  - Unify alif variants (`آأإٱ → ا`).
  - `ى → ي`, `ة → ه`.
  - Drop standalone hamza `ء`.
- After normalisation, aliases shorter than 3 characters are skipped.
- Duplicate aliases (after normalisation) for the same name are deduped
  at table build time so multiple Arabic spellings of the same name do
  not double-count occurrences.

## Word boundary rules

For each alias match at index `i` of length `n`:

1. **Right side**: the character at `i + n` must not be an Arabic letter
   (`[ء-ي]`).
2. **Left side**: the character at `i - 1` must not be an Arabic letter,
   **OR** the alias has `acceptCliticPrefix = true` (only `Allah`), in
   which case the segment between the previous non-letter and `i` must
   be a recognised Arabic clitic prefix from the allowlist:
   ```
   ل, و, ف, ب, ك, س,
   لو, فل, ول, وب, فب, بل, وك
   ```

## matchType assignment

| matchType | When |
|---|---|
| `exact_name` | The alias matched at a strict word boundary AND it is NOT a clitic-prefixed form. |
| `definite_form` | The alias matched after an accepted clitic prefix (only for `Allah`). |
| `name_pairing` | Reserved for two-name compound surface forms. The scanner does not currently emit this; pairings are computed post-hoc. |
| `contextual_attribute` | Reserved for non-string contextual matches (reviewer-driven). |
| `basmalah_excluded` | The match falls inside the surah-opening basmalah prefix. |
| `needs_review` | Reserved for explicit reviewer override. |

## Basmalah exclusion

See `docs/asma-basmalah-counting-policy.md` for the full policy. In
summary:

- For ayah 1 of any surah other than 9, if the ayah text starts with
  the canonical normalised basmalah, the first 38 characters of the
  ayah are the basmalah prefix.
- Any match of `Allah / ar_rahman / ar_raheem` whose start index falls
  inside the basmalah prefix is emitted with:
  - `matchType = "basmalah_excluded"`
  - `isBasmalah = true`
  - `counted = false`
- In-ayah basmalah (e.g. 27:30) is **not** excluded.

## What we do NOT do

- We do **not** strip Quran text out of the corpus.
- We do **not** modify ayah numbering.
- We do **not** emit Quran text into the atlas — only `surahNumber`,
  `ayahNumber`, and a short normalised `matchedForm` (≤80 chars, no
  newlines).
- We do **not** auto-promote any occurrence, name, meaning, category,
  or pairing to `verified`.

## Validator rules (must pass)

- `occurrenceCount` equals the number of `counted=true` occurrences.
- Every basmalah-excluded occurrence has `counted=false` AND
  `isBasmalah=true`.
- Every reference (surahNumber, ayahNumber) is in range.
- All `sourceIds` map to `sourceRegistry.ts`.
- No name is `reviewStatus="verified"` with only `quran_uthmani_cloud`
  as a source — verified status requires a non-Quran scholarly source.
- No meaning is set unless `reviewStatus="verified"`.
- At least one category has `countedOccurrences > 0` (UI safety).
