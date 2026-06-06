# Missing Prophet Story / Profile Policy

The Quran names 25 prophets unanimously. Some have rich narratives
(Yusuf, Musa, Ibrahim, etc.) and full authored stories in
`quranStories.ts`. Others are mentioned only briefly. This policy
defines how the platform handles prophets without rich Quranic detail.

## Categories of coverage

| Category | Prophet examples | Policy |
|---|---|---|
| **Rich narrative** | Adam, Nuh, Ibrahim, Yusuf, Musa, Maryam-Isa, Sulayman | Full authored story in `quranStories.ts` |
| **Connector profile** | Ishaq, Yaqub, Harun, Ilyas, Al-Yasa, Sulayman, Ismail | `quranProphetStoryPages.json` → page type `full_story` (when ≥ 3 unique ayah groups) or `compact_profile` |
| **Compact profile** | Dhul-Kifl, Al-Yasa | `compact_profile` with `LIMITED_QURAN_MENTIONS_WARNING` (no full narrative; ≤ 2 explicit ayahs) |
| **Mission summary** | Muhammad ﷺ | `mission_summary` with `NOT_FULL_BIOGRAPHY_WARNING` (Quranic evidence only — never a full sīrah) |

## Hard rules

1. **Never invent narrative.** If the Quran does not contain a detail,
   the profile must omit it. Tafsir interpretation is out-of-scope for
   the registry layer.
2. **Every section cites ayahs.** Each `storySections[*]` carries
   `ayahReferences` from the prophet's atlas profile — no free text
   without a citation.
3. **Compact profiles stay compact.** Adding speculative narrative to a
   compact profile is a policy violation and will fail the validator.
4. **Muhammad ﷺ is special.** Even though his Quranic presence is
   extensive, the page is a *mission summary*, not a sīrah. Detailed
   biography lives in a separate module subject to scholarly review.
5. **All entries start `needs_review`.** Promotion to `verified`
   requires scholarly sign-off and clears `humanReviewRequired`
   simultaneously.

## Cross-link suggestions

For each connector profile we publish the related prophets / nations /
places below:

- **Ishaq** — Ibrahim (father), Yaqub (son)
- **Yaqub** — Ibrahim, Ishaq, Yusuf
- **Harun** — Musa, Bani Israil, Pharaoh
- **Sulayman** — Dawud, Bilqis/Saba, hoopoe, ants
- **Ismail** — Ibrahim, Hagar (related figure), Makkah

These are encoded in `relatedProphets` / `relatedFigures` /
`relatedNations` / `relatedPlaces` arrays on each page.

## Regeneration

```bash
npx tsx scripts/build-missing-prophet-story-pages.ts
npx tsx scripts/build-quran-prophets-atlas.ts   # refresh missing-list flag
npx tsx scripts/build-quran-story-registry.ts
```

Run the validators after each regeneration:

```bash
npx tsx scripts/validate-quran-prophet-story-pages.ts
npx tsx scripts/validate-quran-prophets-atlas.ts
npx tsx scripts/validate-quran-story-registry.ts
```
