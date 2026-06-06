# Quran Entity Relations — Build Summary

Generated at: 2026-05-17T23:46:46.112Z
Builder version: 1.0.0

## Totals

- Total relations: **1705**
- Entities involved: **79**

## Relations by type

| Type | Count |
|---|---:|
| same_surah_context | 1066 |
| mentioned_with | 478 |
| same_story | 118 |
| mother_of | 9 |
| son_of | 9 |
| family_of | 8 |
| father_of | 7 |
| wife_of | 2 |
| husband_of | 2 |
| theological_discussion | 2 |
| brother_of | 2 |
| daughter_of | 1 |
| guardian_of | 1 |

## Maryam–Isa connections

| Source | Target | Type | Conf | Evidence count | Review |
|---|---|---|---:|---:|---|
| entity_person_maryam | entity_prophet_isa | mentioned_with | 0.7 | 22 | needs_review |
| entity_person_maryam | entity_prophet_isa | mother_of | 0.85 | 1 | needs_review |
| entity_person_maryam | entity_prophet_isa | same_story | 0.7 | 1 | needs_review |
| entity_person_maryam | entity_prophet_isa | same_surah_context | 0.55 | 36 | needs_review |
| entity_person_maryam | entity_prophet_isa | theological_discussion | 0.55 | 4 | needs_review |
| entity_prophet_isa | entity_person_maryam | mentioned_with | 0.7 | 22 | needs_review |
| entity_prophet_isa | entity_person_maryam | same_story | 0.7 | 1 | needs_review |
| entity_prophet_isa | entity_person_maryam | same_surah_context | 0.55 | 36 | needs_review |
| entity_prophet_isa | entity_person_maryam | son_of | 0.85 | 1 | needs_review |
| entity_prophet_isa | entity_person_maryam | theological_discussion | 0.55 | 4 | needs_review |

## Maryam–Zakariyya connections

| Source | Target | Type | Conf | Evidence count |
|---|---|---|---:|---:|
| entity_person_maryam | entity_prophet_zakariyya | family_of | 0.85 | 1 |
| entity_person_maryam | entity_prophet_zakariyya | mentioned_with | 0.7 | 1 |
| entity_person_maryam | entity_prophet_zakariyya | same_surah_context | 0.55 | 4 |
| entity_prophet_zakariyya | entity_person_maryam | family_of | 0.85 | 1 |
| entity_prophet_zakariyya | entity_person_maryam | guardian_of | 0.85 | 1 |
| entity_prophet_zakariyya | entity_person_maryam | mentioned_with | 0.7 | 1 |
| entity_prophet_zakariyya | entity_person_maryam | same_surah_context | 0.55 | 4 |

## Warnings

- All relations default to reviewStatus=needs_review. No relation is auto-verified.
- Same-ayah co-mention edges are observational, not interpretive.
- Family/title edges depend on the seed dictionary, which is reviewedDictionary=false until a specialist signs off.

All edges are `needs_review` and `humanReviewRequired: true`.