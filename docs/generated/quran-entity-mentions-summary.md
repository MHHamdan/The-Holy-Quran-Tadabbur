# Quran Entity Mentions — Scan Summary

Generated at: 2026-10-15T01:19:31.376Z
Scanner version: 2.1.0

## Totals

- Entities seeded: **90**
- Total mentions detected: **964**
- Surahs scanned: **114** (of 114)
- Entities with zero detections: **6**

## Mentions by entity type

| Type | Mentions |
|---|---:|
| prophet | 505 |
| people_or_nation | 145 |
| scripture | 107 |
| person | 91 |
| woman | 34 |
| place | 31 |
| object | 14 |
| jinn | 11 |
| angel | 10 |
| animal | 9 |
| event | 6 |
| family_relation | 1 |

## Top 10 entities by mention count

| Entity | Type | Mentions |
|---|---|---:|
| Musa (Moses) | prophet | 131 |
| The Quran | scripture | 77 |
| Firawn (Pharaoh) | person | 67 |
| Ibrahim (Abraham) | prophet | 63 |
| Nuh (Noah) | prophet | 43 |
| Children of Israel | people_or_nation | 40 |
| Isa (Jesus) | prophet | 33 |
| Maryam (Mary) | woman | 31 |
| Lut (Lot) | prophet | 27 |
| Yusuf (Joseph) | prophet | 26 |

## Maryam mention map

- entityId: `entity_person_maryam`
- Total mentions: **31**
- Surahs containing Maryam mentions: **12** (2, 3, 4, 5, 9, 19, 23, 33, 43, 57, 61, 66)

Mention-type breakdown:
- `explicit_name`: 31

First 25 mentions:
| Surah | Ayah | Type | Conf | Matched |
|---:|---:|---|---:|---|
| 2 | 87 | explicit_name | 0.95 | مريم |
| 2 | 253 | explicit_name | 0.95 | مريم |
| 3 | 36 | explicit_name | 0.95 | مريم |
| 3 | 37 | explicit_name | 0.95 | مريم |
| 3 | 42 | explicit_name | 0.95 | مريم |
| 3 | 43 | explicit_name | 0.95 | مريم |
| 3 | 44 | explicit_name | 0.95 | مريم |
| 3 | 45 | explicit_name | 0.95 | مريم |
| 4 | 156 | explicit_name | 0.95 | مريم |
| 4 | 157 | explicit_name | 0.95 | مريم |
| 4 | 171 | explicit_name | 0.95 | مريم |
| 5 | 17 | explicit_name | 0.95 | مريم |
| 5 | 46 | explicit_name | 0.95 | مريم |
| 5 | 72 | explicit_name | 0.95 | مريم |
| 5 | 75 | explicit_name | 0.95 | مريم |
| 5 | 78 | explicit_name | 0.95 | مريم |
| 5 | 110 | explicit_name | 0.95 | مريم |
| 5 | 112 | explicit_name | 0.95 | مريم |
| 5 | 114 | explicit_name | 0.95 | مريم |
| 5 | 116 | explicit_name | 0.95 | مريم |
| 9 | 31 | explicit_name | 0.95 | مريم |
| 19 | 16 | explicit_name | 0.95 | مريم |
| 19 | 27 | explicit_name | 0.95 | مريم |
| 19 | 34 | explicit_name | 0.95 | مريم |
| 23 | 50 | explicit_name | 0.95 | مريم |

## Entities with zero detections

- `entity_person_bilqis`
- `entity_person_hawwa`
- `entity_person_aziz`
- `entity_animal_dog_cave`
- `entity_object_staff_musa`
- `entity_object_throne_bilqis`

## Ambiguous aliases (downgraded)

- `entity_scripture_quran` — alias `الفرقان` — Generic / common-word alias — confidence downgraded.
- `entity_scripture_quran` — alias `الذكر` — Generic / common-word alias — confidence downgraded.
- `entity_place_cave` — alias `الكهف` — Generic / common-word alias — confidence downgraded.
- `entity_animal_ants` — alias `النمل` — Generic / common-word alias — confidence downgraded.
- `entity_place_makkah` — alias `البلد الأمين` — Generic / common-word alias — confidence downgraded.
- `entity_animal_elephant` — alias `الفيل` — Generic / common-word alias — confidence downgraded.

## Warnings

- 6 seeded entities had zero detections — review aliases or expected scope.

---

All mentions default to `needs_review` and `humanReviewRequired: true`. No tafsir or interpretation is generated. Quran text is not embedded in the output JSON.