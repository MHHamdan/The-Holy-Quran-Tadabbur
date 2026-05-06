# Quran Stories — Batch 3 Plan
_Date: 2026-04-25_

---

## 1. Current State (After Batch 2)

**16 stories in QURAN_STORIES_FIRST_BATCH:**
`story_ayyub`, `story_hud`, `story_salih`, `story_yusuf`, `story_musa`,
`story_kahf`, `story_ibrahim`, `story_lut`, `story_nuh`, `story_bilqis`,
`story_maryam`, `story_luqman`, `story_yunus`, `story_dawud`,
`story_talut_jalut`, `story_qarun`

**Validator output before Batch 3 — 5 warnings, 0 errors:**

| Warning | Type | Resolvable by Batch 3? |
|---------|------|------------------------|
| `story_yusuf → story_musa` | Forward reference (ordering cycle within Batch 1) | No |
| `story_musa → story_ibrahim` | Forward reference (ordering cycle within Batch 1) | No |
| `story_kahf → story_ibrahim` | Forward reference (ordering cycle within Batch 1) | No |
| `story_bilqis → story_dhulqarnayn` | Missing story | **Yes** — adding `story_dhulqarnayn` |
| `story_maryam → story_zakariyya_yahya` | Missing story | **Yes** — adding `story_zakariyya_yahya` |

**Warnings after Batch 3: 3 (down from 5)**

---

## 2. Missing StoryIds to Resolve (Batch 3 Priority)

| Missing storyId | Referenced by | Priority |
|----------------|--------------|----------|
| `story_dhulqarnayn` | `story_bilqis` | High — resolves existing warning |
| `story_zakariyya_yahya` | `story_maryam` | High — resolves existing warning |

---

## 3. Batch 3 Stories

### 1. Story of Dhul-Qarnayn (`story_dhulqarnayn`)
| Field | Value |
|-------|-------|
| Slug | `dhulqarnayn` |
| Arabic title | قصة ذي القرنين |
| English title | Story of Dhul-Qarnayn |
| References | 18:83-98 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | The Quran does not name Dhul-Qarnayn or identify him; his identity is not asserted |

### 2. Story of Zakariyya and Yahya (`story_zakariyya_yahya`)
| Field | Value |
|-------|-------|
| Slug | `zakariyya-yahya` |
| Arabic title | قصة زكريا ويحيى عليهما السلام |
| English title | Story of Zakariyya and Yahya |
| References | 19:2-15, 3:37-41, 21:89-90 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 3. Parable of the Two Gardens (`story_two_gardens`)
| Field | Value |
|-------|-------|
| Slug | `two-gardens` |
| Arabic title | مثل صاحبي الجنتين |
| English title | Parable of the Two Gardens |
| References | 18:32-44 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | Explicitly labeled as parable (مَثَل) in 18:32 — not a named historical figure |

### 4. Parable of the Garden Owners (`story_garden_owners`)
| Field | Value |
|-------|-------|
| Slug | `garden-owners` |
| Arabic title | مثل أصحاب الجنة |
| English title | Parable of the Owners of the Garden |
| References | 68:17-33 |
| Segments | 2 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | Presented as a parable in classical tafsir context — not a named historical figure |

### 5. People of the Sabbath (`story_sabbath_breakers`)
| Field | Value |
|-------|-------|
| Slug | `sabbath-breakers` |
| Arabic title | قصة أصحاب السبت |
| English title | Story of the Sabbath Breakers |
| References | 7:163-166, 2:65-66 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | The nature of the transformation is mentioned in the Quran; scholars discuss whether it was literal or metaphorical — no interpretation is asserted |

### 6. People of the Elephant (`story_elephant`)
| Field | Value |
|-------|-------|
| Slug | `elephant` |
| Arabic title | قصة أصحاب الفيل |
| English title | Story of the Companions of the Elephant |
| References | 105:1-5 |
| Segments | 2 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | The Quran does not name the army commander or specify the target explicitly; classical tafsir provides context |

### 7. The Cow of Bani Israel (`story_baqarah_cow`)
| Field | Value |
|-------|-------|
| Slug | `baqarah-cow` |
| Arabic title | قصة البقرة في سورة البقرة |
| English title | Story of the Cow of Bani Israel |
| References | 2:67-73 |
| Segments | 3 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |

### 8. The Table Spread (`story_table_spread`)
| Field | Value |
|-------|-------|
| Slug | `table-spread` |
| Arabic title | قصة المائدة |
| English title | Story of the Table Spread |
| References | 5:112-115 |
| Segments | 2 |
| Sources | ibn_kathir, tabari, qurtubi |
| Review | needs_review, humanReviewRequired |
| Note | The Quran does not explicitly state that the table descended — classical commentators differ on this |

---

## 4. Array Order for Minimal Warnings

The QURAN_STORIES_FIRST_BATCH array is reordered to place Dhul-Qarnayn before Bilqis
and Zakariyya-Yahya before Maryam:

```
Position  Story                 Resolves
1         story_ayyub           (referenced by story_yusuf at pos 4)
2         story_hud             (referenced by story_nuh at pos 9)
3         story_salih
4         story_yusuf           (yusuf→musa: unavoidable cycle)
5         story_musa            (musa→ibrahim: unavoidable cycle)
6         story_kahf            (kahf→ibrahim: unavoidable cycle)
7         story_ibrahim
8         story_lut
9         story_nuh
10        story_dhulqarnayn     ← NEW (resolves bilqis→dhulqarnayn warning!)
11        story_bilqis          → bilqis→dhulqarnayn: RESOLVED
12        story_zakariyya_yahya ← NEW (resolves maryam→zakariyya_yahya warning!)
13        story_maryam          → maryam→zakariyya_yahya: RESOLVED
14        story_luqman
15        story_yunus
16        story_dawud
17        story_talut_jalut
18        story_qarun
19        story_two_gardens     (refs story_kahf pos 6 ✓, story_qarun pos 18 ✓)
20        story_garden_owners   (refs story_two_gardens pos 19 ✓)
21        story_baqarah_cow     (refs story_musa pos 5 ✓)
22        story_elephant        (no relatedStories)
23        story_sabbath_breakers (refs story_musa pos 5 ✓, story_salih pos 3 ✓)
24        story_table_spread    (refs story_maryam pos 13 ✓)
```

---

## 5. Evidence-Backed Cross-Story Connections Added in Batch 3

| Connection | relationType | Evidence | New warning? |
|-----------|-------------|---------|-------------|
| dhulqarnayn → story_kahf | same_surah | 18:83-98 (dhulqarnayn), 18:9-26 (kahf) | No (kahf pos 6 before dhulqarnayn pos 10) |
| zakariyya_yahya → story_ibrahim | same_surah | 21:89-90 (zakariyya), 21:51-73 (ibrahim) | No (ibrahim pos 7 before zakariyya pos 12) |
| two_gardens → story_kahf | same_surah | 18:32-44 (two gardens), 18:9-26 (kahf) | No (kahf pos 6 before two_gardens pos 19) |
| two_gardens → story_qarun | same_moral_lesson | 18:32-44, 28:76-82 | No (qarun pos 18 before two_gardens pos 19) |
| garden_owners → story_two_gardens | same_moral_lesson | 68:17-33, 18:32-44 | No (two_gardens pos 19 before garden_owners pos 20) |
| baqarah_cow → story_musa | shared_character | 2:67-73 | No (musa pos 5 before baqarah_cow pos 21) |
| sabbath_breakers → story_musa | shared_character | 7:163-166, 2:65-66 | No (musa pos 5 before sabbath_breakers pos 23) |
| sabbath_breakers → story_salih | same_event_pattern | 7:73-79, 7:163-166 | No (salih pos 3 before sabbath_breakers pos 23) |
| table_spread → story_maryam | shared_character | 5:112-115, 19:16-34 | No (maryam pos 13 before table_spread pos 24) |

---

## 6. Source Requirements

All Batch 3 stories use:
- `ibn_kathir` (canonical)
- `tabari` (canonical)
- `qurtubi` (canonical)

These match TRUSTED_SOURCE_IDS.

---

## 7. Human Review Status

All Batch 3 stories carry:
- `sunniReview.status = 'needs_review'`
- `sunniReview.humanReviewRequired = true`
- `sunniReview.matchedEvidence = []`

No Batch 3 story is marked `approved`.

---

## 8. Expected Validation Results After Batch 3

| Check | Before | After |
|-------|--------|-------|
| Stories | 16 | 24 |
| Segments | 51 | ~72 |
| Warnings | 5 | 3 |
| Errors | 0 | 0 |

Remaining 3 warnings are all ordering cycles within Batch 1 (unavoidable):
1. yusuf→musa (yusuf pos 4, musa pos 5)
2. musa→ibrahim (musa pos 5, ibrahim pos 7)
3. kahf→ibrahim (kahf pos 6, ibrahim pos 7)

These are resolvable only by restructuring Batch 1 data — not planned.

---

## 9. Special Content Notes

### Parables (not historical narratives)
- `story_two_gardens` (18:32-44): The Quran explicitly introduces this with "وَاضْرِبْ لَهُم مَّثَلًا" (18:32)
- `story_garden_owners` (68:17-33): Classical tafsir treats this as a parable

Neither parable names any person. Summaries and titles are labeled accordingly.

### Uncertainty about Dhul-Qarnayn's identity
The Quran does not name or identify Dhul-Qarnayn. No identification is asserted in any segment.

### The Sabbath transformation
Verse 2:65 references a transformation (Quranic language). Classical scholars discuss whether it was literal or metaphorical. No interpretation is asserted; adult summaries flag the disagreement.

### The Table Spread descent
The Quran (5:115) states Allah's conditional acceptance. Whether the table actually descended is discussed by classical scholars. No assertion is made in the summaries.
