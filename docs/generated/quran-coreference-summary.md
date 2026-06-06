# Quran Coreference — Scan Summary

Generated at: 2026-05-17T03:57:32.324Z
Scanner version: 1.0.0

## Totals

- Coreference mention candidates: **67**
- Coreference chains: **29**
- Zero-match entities improved by implicit candidates: **4**

## Mentions by surfaceType

| Surface | Count |
|---|---:|
| family_reference | 44 |
| possessive_pronoun | 10 |
| title | 9 |
| implicit_context | 2 |
| role_reference | 2 |

## Mentions by resolutionMethod

| Method | Count |
|---|---:|
| rule_pattern | 53 |
| story_segment_context | 14 |

## Patterns triggered

| Pattern | Hits |
|---|---:|
| `maryam_ibn_maryam_family` | 22 |
| `isa_ibn_maryam_link` | 22 |
| `maryam_pronoun_mother_isa_anchor` | 0 |
| `maryam_direct_address_walidatuka` | 0 |
| `isa_masih_title` | 9 |
| `zakariyya_kafala_aal_imran` | 1 |
| `musa_staff_asaa_h` | 3 |
| `musa_staff_asaa_k` | 3 |
| `musa_sea_crossing` | 1 |
| `kahf_kalbuhum_dog` | 2 |
| `kahf_alfityah` | 1 |
| `bilqis_arshuha_throne` | 2 |
| `bilqis_implicit_imratan_tamlikuhum` | 1 |
| `bilqis_malikat_saba_title` | 0 |
| `adam_zawjuhu_hawwa` | 0 |

## Chains by type

| Type | Count |
|---|---:|
| surah_level | 9 |
| local_passage | 17 |
| cross_surah_candidate | 3 |

## Featured-entity coreference summary

| Entity | Coreference mentions | Chains |
|---|---:|---:|
| Maryam | 22 | 12 |
| Musa | 0 | 0 |
| People of the Cave | 1 | 0 |
| Dog of the Cave | 2 | 1 |
| Staff of Musa | 6 | 3 |
| Throne of Bilqis | 2 | 1 |
| Bilqis | 1 | 0 |
| Hawwa | 0 | 0 |

## Warnings

- All coreference mentions default to needs_review.
- Cross-surah chains are always needs_review.
- No Quran text is embedded; only short normalised surface tokens are kept.

All implicit links default to `needs_review` and `humanReviewRequired: true`. No tafsir is generated.