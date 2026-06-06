# Quran Entity Mentions — Scan Summary

Generated at: 2026-05-17T23:46:32.749Z
Scanner version: 1.0.0

## Totals

- Entities seeded: **90**
- Total mentions detected: **1115**
- Surahs scanned: **114** (of 114)
- Entities with zero detections: **6**

## Mentions by entity type

| Type | Mentions |
|---|---:|
| prophet | 576 |
| people_or_nation | 168 |
| person | 112 |
| scripture | 105 |
| woman | 54 |
| object | 32 |
| place | 30 |
| jinn | 11 |
| angel | 10 |
| animal | 9 |
| event | 7 |
| family_relation | 1 |

## Top 10 entities by mention count

| Entity | Type | Mentions |
|---|---|---:|
| Musa (Moses) | prophet | 131 |
| The Quran | scripture | 75 |
| Firawn (Pharaoh) | person | 67 |
| Salih | prophet | 64 |
| Ibrahim (Abraham) | prophet | 51 |
| Maryam (Mary) | woman | 51 |
| Nuh (Noah) | prophet | 43 |
| Children of Israel | people_or_nation | 40 |
| People of Aad | people_or_nation | 35 |
| Isa (Jesus) | prophet | 33 |

## Maryam mention map

- entityId: `entity_person_maryam`
- Total mentions: **51**
- Surahs containing Maryam mentions: **12** (2, 3, 4, 5, 9, 19, 23, 33, 43, 57, 61, 66)

Mention-type breakdown:
- `explicit_name`: 31
- `pronoun_context`: 20

First 25 mentions:
| Surah | Ayah | Type | Conf | Matched |
|---:|---:|---|---:|---|
| 2 | 87 | explicit_name | 0.95 | مريم |
| 2 | 128 | pronoun_context | 0.35 | أمه |
| 2 | 134 | pronoun_context | 0.35 | أمه |
| 2 | 141 | pronoun_context | 0.35 | أمه |
| 2 | 143 | pronoun_context | 0.35 | أمه |
| 2 | 213 | pronoun_context | 0.35 | أمه |
| 2 | 221 | pronoun_context | 0.35 | أمه |
| 2 | 253 | explicit_name | 0.95 | مريم |
| 3 | 36 | explicit_name | 0.95 | مريم |
| 3 | 37 | explicit_name | 0.95 | مريم |
| 3 | 42 | explicit_name | 0.95 | مريم |
| 3 | 43 | explicit_name | 0.95 | مريم |
| 3 | 44 | explicit_name | 0.95 | مريم |
| 3 | 45 | explicit_name | 0.95 | مريم |
| 3 | 104 | pronoun_context | 0.35 | أمه |
| 3 | 110 | pronoun_context | 0.35 | أمه |
| 3 | 113 | pronoun_context | 0.35 | أمه |
| 4 | 11 | pronoun_context | 0.35 | أمه |
| 4 | 41 | pronoun_context | 0.35 | أمه |
| 4 | 156 | explicit_name | 0.95 | مريم |
| 4 | 157 | explicit_name | 0.95 | مريم |
| 4 | 171 | explicit_name | 0.95 | مريم |
| 5 | 17 | explicit_name | 0.95 | مريم |
| 5 | 46 | explicit_name | 0.95 | مريم |
| 5 | 48 | pronoun_context | 0.35 | أمه |

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