# Asmā' Allah — Basmalah Counting Policy

_Last updated: 2026-05-17_

## Purpose

Defines how the Asmā' Allah al-Ḥusnā Atlas counts occurrences of the names
`الله`, `الرحمن`, and `الرحيم` that appear inside repeated surah-opening
basmalah lines. The policy affects **statistics only** — it never modifies
Quran text or Mushaf numbering.

## Hard constraints

- The Quran text in `data/raw/quran_uthmani.json` is never modified.
- The Mushaf display and ayah numbering are never changed.
- The policy applies **only** to the Asmā' Atlas's `occurrenceCount`,
  `surahCount`, `firstOccurrence`, `lastOccurrence`, and category counts.

## Settings (defaults)

| Setting | Default | Meaning |
|---|---|---|
| `countBasmalaInFatihah` | `false` | The basmalah in Al-Fatihah 1:1 is treated as a surah-opening line. Excluded from name counts by default. |
| `excludeRepeatedSurahOpeningBasmalah` | `true` | The basmalah occurring as the opening line of every surah (except At-Tawbah) is excluded from name counts. |

These are atlas-level settings exposed in
`asmaAllahAtlas.json::basmalahPolicy`.

## Detection of "basmalah" occurrence

An occurrence is treated as basmalah when **all** of the following hold:

1. The ayah's normalised text exactly equals the canonical basmalah string
   (`بسم الله الرحمن الرحيم`, normalised by stripping tashkeel/hamza and
   unifying alif/ya/ta-marbuta).
2. The ayah number equals `1` (the surah's opening).
3. The matched name is one of `الله / الرحمن / الرحيم`.

When all three hold, the occurrence is emitted with:

- `isBasmalah = true`
- `counted = false`
- `matchType = "basmalah_excluded"`
- The occurrence remains visible in the per-name detail view so reviewers
  can see it was detected and intentionally excluded.

## In-ayah basmalah (e.g. 27:30)

Surah An-Naml 27:30 contains the basmalah **inside** Sulayman's letter to
Bilqis:

> إِنَّهُۥ مِنۢ سُلَيْمَـٰنَ وَإِنَّهُۥ بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ

This is **not** a surah-opening line. By policy, the occurrences inside
27:30 are counted normally (the basmalah-exclusion rule does **not** apply
to in-ayah basmalah text). Each name appearing here is emitted with:

- `isBasmalah = false`
- `counted = true`
- `matchType = "exact_name"` (or `"definite_form"` depending on the alias)

## Surah-opening basmalah in Al-Fatihah (1:1)

The canonical Quran-text file `data/raw/quran_uthmani.json` treats
`بسم الله الرحمن الرحيم` as **Al-Fatihah 1:1**. The atlas honours the
default `countBasmalaInFatihah = false`: this verse's name occurrences are
excluded from name counts in the same way as every other surah's
basmalah.

If a future policy decision flips the setting, the script regenerates the
atlas with the new policy attached as metadata.

## At-Tawbah (Surah 9)

Surah 9 has no basmalah. No exclusion applies; the scanner naturally
counts whatever names appear in its ayahs starting from 9:1.

## Reporting

Every atlas summary file reports both numbers:

- `totalCountedOccurrences` — sum of `counted=true` occurrences across all
  names.
- `totalExcludedBasmalahOccurrences` — sum of `counted=false` /
  `matchType="basmalah_excluded"` occurrences.

Reviewers can spot-check the exclusion ratio by dividing
`totalExcludedBasmalahOccurrences` by the expected basmalah count
(roughly 113 × number-of-names-in-basmalah = 113 × 3 = **339** excluded
occurrences if every surah-opening basmalah is matched).

## Why we excluded basmalah from name counts (by default)

The traditional scholarly counts of أسماء الله الحسنى in the Quran
(Ibn Kathir, Tabari, etc.) typically refer to **substantive** mentions —
e.g. "اسم الله ورد كذا مرة في القرآن" — and treat the recurring
opening basmalah as decorative-positional, not as a doctrinal count.
Counting it 113 extra times for each of three names would inflate the
statistic and mislead readers.

Reviewers may revisit this setting per the project's editorial policy.
