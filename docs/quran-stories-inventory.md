# Quran Stories Inventory
_Tadabbur Al-Quran — Verified Story Index_
_Date: 2026-04-26_

---

## Usage Note

This inventory catalogs all Quranic stories currently in the platform manifest
(`data/manifests/stories.json`). Each story entry reflects the data actually present.

**Important:**
- Stories marked `needs_review` have Quran references but their explanations have NOT been validated against DB tafsir chunks
- Source IDs use short form (`ibn_kathir`, `tabari`, `qurtubi`, `saadi`) matching TAFSIR_CATALOG keys
- Arabic text is never written here; all Arabic titles come from the manifest's `name_ar` field
- Kids and adult summaries do not yet exist for most stories — they are flagged as `missing`

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Present and complete |
| ⚠️ | Present but needs review |
| ❌ | Missing — requires addition |
| 🔍 | Needs human verification before production |

---

## Implementation Status: Batch 1 + Batch 2 + Batch 3 Complete (24 stories)

**24 stories now implemented in `QURAN_STORIES_FIRST_BATCH`.**
All carry `needs_review` / `humanReviewRequired: true`. No segment is approved.
Validator: 3 warnings remaining (irreducible ordering cycles within Batch 1 — cannot be resolved by reordering).

---

## Batch 2 Stories (8 stories — added 2026-04-25)

### 9. Story of Ayyub عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_ayyub` |
| Arabic title | قصة أيوب عليه السلام ✅ |
| English title | Story of Prophet Ayyub (Job) ✅ |
| Main characters | Ayyub, His wife, His family ✅ |
| Quran references | 21:83-84 (Al-Anbiya), 38:41-44 (Sad) ✅ |
| Segments | 2 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review — disagreement note on 38:44 (oath context) |
| resolves warning | `story_yusuf → story_ayyub` now resolved ✅ |

---

### 10. Story of Hud عليه السلام and Aad

| Field | Status |
|-------|--------|
| Story ID | `story_hud` |
| Arabic title | قصة هود عليه السلام ✅ |
| English title | Story of Prophet Hud and the People of Aad ✅ |
| Main characters | Hud, Chiefs of Aad, Believers ✅ |
| Quran references | 7:65-72, 11:50-60, 26:123-140, 46:21-26 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Resolves warning | `story_nuh → story_hud` now resolved ✅ |

---

### 11. Story of Salih عليه السلام and Thamud

| Field | Status |
|-------|--------|
| Story ID | `story_salih` |
| Arabic title | قصة صالح عليه السلام ✅ |
| English title | Story of Prophet Salih and Thamud ✅ |
| Main characters | Salih, Chiefs of Thamud, She-camel (sign) ✅ |
| Quran references | 7:73-79, 11:61-68, 26:141-159, 54:23-31 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Related | `story_hud` (same_event_pattern) ✅ |

---

### 12. Story of Lut عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_lut` |
| Arabic title | قصة لوط عليه السلام ✅ |
| English title | Story of Prophet Lut (Lot) ✅ |
| Main characters | Lut, Angel guests, His wife ✅ |
| Quran references | 7:80-84, 11:77-83, 15:61-77, 26:160-175 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Related | `story_ibrahim` (same_surah — Surah Hud 11:69-83) ✅ |

---

### 13. Story of Yunus عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_yunus` |
| Arabic title | قصة يونس عليه السلام ✅ |
| English title | Story of Prophet Yunus (Jonah) ✅ |
| Main characters | Yunus, The great fish, His people ✅ |
| Quran references | 37:139-148, 21:87-88, 10:98, 68:48-50 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Related | `story_nuh` (contrast — people's response) ✅ |

---

### 14. Story of Dawud عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_dawud` |
| Arabic title | قصة داود عليه السلام ✅ |
| English title | Story of Prophet Dawud (David) ✅ |
| Main characters | Dawud, Two litigants ✅ |
| Quran references | 2:251, 34:10-11, 21:78-80, 38:17-26 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review — disagreement note on 38:21-26 (nature of test) |
| Related | `story_bilqis` (chronological — Sulayman is Dawud's successor, 34:10-12) ✅ |

---

### 15. Story of Talut and Jalut

| Field | Status |
|-------|--------|
| Story ID | `story_talut_jalut` |
| Arabic title | قصة طالوت وجالوت ✅ |
| English title | Story of Talut and Jalut ✅ |
| Main characters | Talut, Jalut, Dawud, Bani Israel ✅ |
| Quran references | 2:246-251 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Related | `story_dawud` (shared_character), `story_musa` (same_theme) ✅ |

---

### 16. Story of Qarun

| Field | Status |
|-------|--------|
| Story ID | `story_qarun` |
| Arabic title | قصة قارون ✅ |
| English title | Story of Qarun (Korah) ✅ |
| Main characters | Qarun, Musa's people ✅ |
| Quran references | 28:76-82, 29:39, 40:24 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Related | `story_musa` (shared_character — 28:76 explicit) ✅ |

---

## Batch 3 Stories (8 stories — added 2026-04-26)

### 17. Story of Dhul-Qarnayn (`story_dhulqarnayn`)

| Field | Status |
|-------|--------|
| Story ID | `story_dhulqarnayn` |
| Arabic title | قصة ذي القرنين ✅ |
| English title | Story of Dhul-Qarnayn ✅ |
| Main characters | Dhul-Qarnayn ✅ |
| Quran references | 18:83-98 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Resolves warning | `story_bilqis → story_dhulqarnayn` now resolved ✅ |
| Notes | The Quran does not name or identify Dhul-Qarnayn — no identity is asserted |

---

### 18. Story of Zakariyya and Yahya (`story_zakariyya_yahya`)

| Field | Status |
|-------|--------|
| Story ID | `story_zakariyya_yahya` |
| Arabic title | قصة زكريا ويحيى عليهما السلام ✅ |
| English title | Story of Zakariyya and Yahya ✅ |
| Main characters | Zakariyya, Yahya, Zakariyya's wife ✅ |
| Quran references | 19:2-15, 3:37-41, 21:89-90 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Resolves warning | `story_maryam → story_zakariyya_yahya` now resolved ✅ |

---

### 19. Parable of the Two Gardens (`story_two_gardens`)

| Field | Status |
|-------|--------|
| Story ID | `story_two_gardens` |
| Arabic title | مثل صاحبي الجنتين ✅ |
| English title | Parable of the Two Gardens ✅ |
| Main characters | The wealthy man, his believing companion ✅ |
| Quran references | 18:32-44 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |
| Notes | Explicitly labeled as مَثَل (parable) in 18:32 — not a named historical figure |

---

### 20. Parable of the Garden Owners (`story_garden_owners`)

| Field | Status |
|-------|--------|
| Story ID | `story_garden_owners` |
| Arabic title | مثل أصحاب الجنة ✅ |
| English title | Parable of the Owners of the Garden ✅ |
| Main characters | The owners of the garden ✅ |
| Quran references | 68:17-33 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |

---

### 21. Story of the Cow (Baqarah) (`story_baqarah_cow`)

| Field | Status |
|-------|--------|
| Story ID | `story_baqarah_cow` |
| Arabic title | قصة البقرة ✅ |
| English title | Story of the Cow (Al-Baqarah) ✅ |
| Main characters | Bani Israel, Musa ✅ |
| Quran references | 2:67-74 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review |

---

### 22. Story of the People of the Elephant (`story_elephant`)

| Field | Status |
|-------|--------|
| Story ID | `story_elephant` |
| Arabic title | قصة أصحاب الفيل ✅ |
| English title | Story of the People of the Elephant ✅ |
| Main characters | The army with the elephant, the birds ✅ |
| Quran references | 105:1-5 ✅ |
| Segments | 1 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review — disagreement note on identity of the commander |
| Notes | The Quran does not name the commander or the city targeted; no identification is asserted |

---

### 23. Story of the Sabbath Breakers (`story_sabbath_breakers`)

| Field | Status |
|-------|--------|
| Story ID | `story_sabbath_breakers` |
| Arabic title | قصة أصحاب السبت ✅ |
| English title | Story of the Sabbath Breakers ✅ |
| Main characters | The community who violated the Sabbath ✅ |
| Quran references | 2:65, 7:163-166 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review — disagreement note on the nature of transformation |
| Notes | Classical scholars differ on the specific nature of the transformation in 2:65 and 7:166 |

---

### 24. Story of the Table Spread (`story_table_spread`)

| Field | Status |
|-------|--------|
| Story ID | `story_table_spread` |
| Arabic title | قصة المائدة ✅ |
| English title | Story of the Table Spread ✅ |
| Main characters | Isa, the Disciples (Hawariyyun) ✅ |
| Quran references | 5:112-115 ✅ |
| Segments | 3 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ✅ Present |
| Adult summary | ✅ Present |
| Sunni review | ⚠️ needs_review — disagreement note on whether table actually descended |
| Notes | Classical scholars differ on whether the table descended after 5:115 — no interpretation asserted |

---

## Priority Batch (8 Stories — First Implementation)

These 8 stories are selected for the first seed data batch. They are:
- Fully traceable to Quran references
- Central to user understanding
- Broadly covered by the four approved tafsir sources

---

### 1. Story of Yusuf عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_yusuf` |
| Arabic title | قصة يوسف عليه السلام ✅ |
| English title | Story of Prophet Yusuf (Joseph) ✅ |
| Main characters | Yusuf, Yaqub, Brothers, Aziz, Zulaykha ✅ |
| Main surah | 12 (Surah Yusuf — complete story) ✅ |
| Quran references | 12:4-6, 12:7-18, 12:19-22, 12:23-35, 12:36-53, 12:54-57, 12:58-87, 12:88-98, 12:99-101 ✅ |
| Segments | 9 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing (only general summary_en exists) |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Complete story in one surah — ideal for first batch |

---

### 2. Story of Musa عليه السلام and Pharaoh

| Field | Status |
|-------|--------|
| Story ID | `story_musa` |
| Arabic title | قصة موسى عليه السلام ✅ |
| English title | Story of Prophet Musa (Moses) ✅ |
| Main characters | Musa, Harun, Firawn, Bani Israel, Asiya ✅ |
| Surahs | 2, 7, 10, 11, 17, 18, 20, 26, 27, 28, 40, 43, 44, 79 ✅ |
| Quran references | Multiple cross-surah references ✅ |
| Segments | 9 ✅ |
| Sources | ibn_kathir, tabari, qurtubi, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Most mentioned prophet in the Quran (28:7-13, 20:9-48, 7:103-137, 26:10-68, 20:56-76, 20:77-98, 7:142-156, 18:60-82) |

---

### 3. Story of People of the Cave

| Field | Status |
|-------|--------|
| Story ID | `story_kahf` |
| Arabic title | قصة أصحاب الكهف ✅ |
| English title | Story of the People of the Cave ✅ |
| Main characters | Seven sleepers, their dog ✅ |
| Main surah | 18 ✅ |
| Quran references | 18:9-26 ✅ |
| Segments | 5 ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Number of sleepers is disputed — multiple scholarly opinions must be noted |

---

### 4. Story of Ibrahim عليه السلام (Idols and Fire)

| Field | Status |
|-------|--------|
| Story ID | `story_ibrahim` (main) + `story_ibrahim_fire` (fire episode) |
| Arabic title | قصة إبراهيم عليه السلام ✅ |
| English title | Story of Prophet Ibrahim ✅ |
| Main characters | Ibrahim, his father Azar, his people, angels ✅ |
| Surahs | 2, 6, 9, 11, 14, 15, 16, 19, 21, 22, 26, 29, 37, 43, 51, 53, 60, 87 ✅ |
| Quran references | 21:51-73 (idols and fire), 2:260 (birds), 37:83-113, 6:74-83, 11:69-76 ✅ |
| Segments | 8 (main story) + 2 (fire episode) ✅ |
| Sources | ibn_kathir, tabari, qurtubi, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Fire miracle is explicit in Quran (21:69); no extra-Quranic details should be added |

---

### 5. Story of Nuh عليه السلام

| Field | Status |
|-------|--------|
| Story ID | `story_nuh` |
| Arabic title | قصة نوح عليه السلام ✅ |
| English title | Story of Prophet Nuh (Noah) ✅ |
| Main characters | Nuh, his wife, his son ✅ |
| Surahs | 7, 10, 11, 21, 23, 26, 37, 54, 71 ✅ |
| Quran references | 71:1-28 (Nuh's full call), 11:25-49 (the ark), 7:59-64, 10:71-73, 23:23-30 ✅ |
| Segments | 6 ✅ |
| Sources | ibn_kathir, tabari ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Story of Nuh's son (story_son_nuh) and wife (story_wife_nuh) are separate entries |

---

### 6. Story of Sulayman عليه السلام and Bilqis

| Field | Status |
|-------|--------|
| Story ID | `story_bilqis` + `story_sulayman` + `story_ant_hoopoe` |
| Arabic title | قصة سليمان وبلقيس ✅ |
| English title | Story of Sulayman and Bilqis ✅ |
| Main characters | Sulayman, Bilqis (Queen of Sheba), Hudhud, Jinn ✅ |
| Main surah | 27 (Surah Al-Naml) ✅ |
| Quran references | 27:15-44 (Bilqis), 27:17-19 (ants/hoopoe), 34:12-13 (Sulayman and Jinn) ✅ |
| Segments | 3 (Bilqis) + 2 (ant/hoopoe) + 6 (main Sulayman) ✅ |
| Sources | ibn_kathir, tabari, qurtubi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Bilqis not named in Quran — title must be labeled appropriately |

---

### 7. Story of Maryam عليها السلام

| Field | Status |
|-------|--------|
| Story ID | `story_maryam` |
| Arabic title | قصة مريم عليها السلام ✅ |
| English title | Story of Maryam (Mary) ✅ |
| Main characters | Maryam, Zakariya, Angels ✅ |
| Surahs | 3, 19, 21, 66 ✅ |
| Quran references | 19:16-34 (Maryam in Surah Maryam), 3:35-47 (family of Imran) ✅ |
| Segments | 6 ✅ |
| Sources | ibn_kathir, tabari ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Birth and early life not fabricated — only what is in Quran |

---

### 8. Story of Luqman's Advice

| Field | Status |
|-------|--------|
| Story ID | `story_luqman` |
| Arabic title | قصة لقمان الحكيم ✅ |
| English title | Story of Luqman's Wisdom ✅ |
| Main characters | Luqman, his son ✅ |
| Main surah | 31 ✅ |
| Quran references | 31:12-19 ✅ |
| Segments | 5 ✅ |
| Sources | ibn_kathir, tabari, saadi ⚠️ (needs_review) |
| Kids summary | ❌ Missing |
| Adult summary | ❌ Missing |
| Lessons | ❌ Missing |
| Sunni review | ❌ Missing |
| Notes | Whether Luqman was a prophet is disputed — must reflect scholarly disagreement |

---

## Full Story Inventory (All 122 Stories)

Stories are listed with key data. All have Quran references in the manifest.
Coverage status reflects presence of kids/adult summaries and sunni review.

| Story ID | Arabic Title | Surahs | Segs | Kids | Adult | Sunni Review |
|----------|-------------|--------|------|------|-------|--------------|
| story_adam | قصة آدم عليه السلام | 2,7,15,17,18,20,38 | 8 | ❌ | ❌ | ❌ |
| story_nuh | قصة نوح عليه السلام | 7,10,11,21,23,26,37,54,71 | 6 | ❌ | ❌ | ❌ |
| story_ibrahim | قصة إبراهيم عليه السلام | 13 surahs | 8 | ❌ | ❌ | ❌ |
| story_musa | قصة موسى عليه السلام | 14 surahs | 9 | ❌ | ❌ | ❌ |
| story_yusuf | قصة يوسف عليه السلام | 12 | 9 | ❌ | ❌ | ❌ |
| story_isa | قصة عيسى عليه السلام | 6 surahs | 7 | ❌ | ❌ | ❌ |
| story_maryam | قصة مريم عليها السلام | 3,19,21,66 | 6 | ❌ | ❌ | ❌ |
| story_zakariyya_yahya | قصة زكريا ويحيى عليهما السلام | 3 surahs | 4 | ❌ | ❌ | ❌ |
| story_sulayman | قصة سليمان عليه السلام | 4 surahs | 6 | ❌ | ❌ | ❌ |
| story_dawud | قصة داود عليه السلام | 5 surahs | 5 | ❌ | ❌ | ❌ |
| story_ayyub | قصة أيوب عليه السلام | 2 surahs | 3 | ❌ | ❌ | ❌ |
| story_yunus | قصة يونس عليه السلام | 4 surahs | 5 | ❌ | ❌ | ❌ |
| story_lut | قصة لوط عليه السلام | 8 surahs | 4 | ❌ | ❌ | ❌ |
| story_shuayb | قصة شعيب عليه السلام | 4 surahs | 4 | ❌ | ❌ | ❌ |
| story_salih | قصة صالح عليه السلام | 6 surahs | 4 | ❌ | ❌ | ❌ |
| story_hud | قصة هود عليه السلام | 7 surahs | 4 | ❌ | ❌ | ❌ |
| story_kahf | قصة أصحاب الكهف | 18 | 5 | ❌ | ❌ | ❌ |
| story_dhulqarnayn | قصة ذي القرنين | 18 | 5 | ❌ | ❌ | ❌ |
| story_luqman | قصة لقمان الحكيم | 31 | 5 | ❌ | ❌ | ❌ |
| story_qarun | قصة قارون | 3 surahs | 5 | ❌ | ❌ | ❌ |
| story_habil_qabil | قصة هابيل وقابيل | 5 | 5 | ❌ | ❌ | ❌ |
| story_elephant | قصة أصحاب الفيل | 105 | 1 | ❌ | ❌ | ❌ |
| story_baqarah_cow | قصة البقرة | 2 | 4 | ❌ | ❌ | ❌ |
| story_talut_jalut | قصة طالوت وجالوت | 2 | 3 | ❌ | ❌ | ❌ |
| story_ismail | قصة إسماعيل عليه السلام | 7 surahs | 3 | ❌ | ❌ | ❌ |
| story_khidr | قصة موسى والخضر | 18 | 5 | ❌ | ❌ | ❌ |
| story_bilqis | قصة بلقيس ملكة سبأ | 27 | 3 | ❌ | ❌ | ❌ |
| story_two_gardens | قصة صاحبي الجنتين | 18 | 4 | ❌ | ❌ | ❌ |
| story_ditch | قصة أصحاب الأخدود | 85 | 1 | ❌ | ❌ | ❌ |
| story_ant_hoopoe | قصة النملة والهدهد | 27 | 2 | ❌ | ❌ | ❌ |
| story_sabbath_breakers | قصة أصحاب السبت | 2 surahs | 4 | ❌ | ❌ | ❌ |
| story_mother_musa | قصة أم موسى | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_asiya | قصة آسية زوجة فرعون | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_magicians | قصة سحرة فرعون | 3 surahs | 4 | ❌ | ❌ | ❌ |
| story_sea_crossing | قصة عبور البحر | 6 surahs | 2 | ❌ | ❌ | ❌ |
| story_ibrahim_fire | قصة إبراهيم والنار | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_yusuf_dream | قصة رؤيا يوسف | 12 | 2 | ❌ | ❌ | ❌ |
| story_yusuf_prison | قصة يوسف في السجن | 12 | 3 | ❌ | ❌ | ❌ |
| story_yusuf_brothers | قصة يوسف وإخوته | 12 | 3 | ❌ | ❌ | ❌ |
| story_isra_miraj | قصة الإسراء والمعراج | 2 surahs | 2 | ❌ | ❌ | ❌ |
| story_badr | غزوة بدر | 2 surahs | 3 | ❌ | ❌ | ❌ |
| story_uhud | غزوة أحد | 3 | 3 | ❌ | ❌ | ❌ |
| story_three_messengers | قصة أصحاب القرية (يس) | 36 | 3 | ❌ | ❌ | ❌ |
| *(remaining 80+ stories)* | … | … | … | ❌ | ❌ | ❌ |

---

## Stories from User Task — Coverage Check

| Requested Story | Manifest ID | Status |
|----------------|-------------|--------|
| Adam عليه السلام | `story_adam` | ⚠️ present, no levels |
| Habil and Qabil | `story_habil_qabil` | ⚠️ present, no levels |
| Nuh عليه السلام | `story_nuh` | ⚠️ present, no levels |
| Hud عليه السلام and Aad | `story_hud` + `story_ad` | ⚠️ present, no levels |
| Salih عليه السلام and Thamud | `story_salih` + `story_thamud` | ⚠️ present, no levels |
| Ibrahim عليه السلام | `story_ibrahim` | ⚠️ present, no levels |
| Ibrahim and the idols | `story_ibrahim` | ⚠️ present (aspect=idols) |
| Ibrahim and the fire | `story_ibrahim_fire` | ⚠️ present, no levels |
| Ibrahim and the guests | `story_ibrahim` (segment) | ⚠️ partial (in main) |
| Lut عليه السلام | `story_lut` | ⚠️ present, no levels |
| Ismail عليه السلام | `story_ismail` | ⚠️ present, no levels |
| Yusuf عليه السلام | `story_yusuf` | ⚠️ present, no levels |
| Yaqub عليه السلام | `story_yaqub` | ⚠️ present (2 segments) |
| Musa عليه السلام | `story_musa` | ⚠️ present, no levels |
| Musa and his mother | `story_mother_musa` | ⚠️ present, no levels |
| Musa and Pharaoh | `story_musa` (segment) | ⚠️ present |
| Musa and the sea | `story_sea_crossing` | ⚠️ present, no levels |
| Musa and Bani Israel | `story_bani_israel` | ⚠️ present, no levels |
| Musa and Al-Khidr | `story_khidr` | ⚠️ present, no levels |
| Harun عليه السلام | Part of `story_musa` | ⚠️ partial |
| Dawud عليه السلام | `story_dawud` | ⚠️ present, no levels |
| Sulayman عليه السلام | `story_sulayman` | ⚠️ present, no levels |
| Sulayman and the ants | `story_ant_hoopoe` | ⚠️ present, no levels |
| Sulayman and the hoopoe | `story_ant_hoopoe` | ⚠️ present |
| Sulayman and Bilqis | `story_bilqis` | ⚠️ present, no levels |
| Ayyub عليه السلام | `story_ayyub` | ⚠️ present, no levels |
| Yunus عليه السلام | `story_yunus` | ⚠️ present, no levels |
| Zakariya عليه السلام | `story_zakariyya_yahya` | ⚠️ present, no levels |
| Yahya عليه السلام | `story_zakariyya_yahya` | ⚠️ part of same |
| Maryam عليها السلام | `story_maryam` | ⚠️ present, no levels |
| Isa عليه السلام | `story_isa` | ⚠️ present, no levels |
| People of the Cave | `story_kahf` | ⚠️ present, no levels |
| Owner of the two gardens | `story_two_gardens` | ⚠️ present, no levels |
| People of the Garden (Qalam) | `story_garden_owners` | ⚠️ present, no levels |
| Dhu al-Qarnayn | `story_dhulqarnayn` | ⚠️ present, no levels |
| Qarun | `story_qarun` | ⚠️ present, no levels |
| Talut and Jalut | `story_talut_jalut` | ⚠️ present, no levels |
| Sabbath breakers | `story_sabbath_breakers` | ⚠️ present, no levels |
| People of the Elephant | `story_elephant` | ⚠️ present (1 segment) |
| Luqman and his advice | `story_luqman` | ⚠️ present, no levels |
| Believers in Surah Yasin | `story_three_messengers` | ⚠️ present, no levels |
| Cow in Surah Al-Baqarah | `story_baqarah_cow` | ⚠️ present, no levels |
| Table spread (Al-Ma'idah) | Not yet found in manifest | 🔍 needs_review |
| Companions of the trench | `story_ditch` | ⚠️ present (1 segment) |

---

## Source Coverage Assessment

All 122 stories use the following tafsir sources (all marked `needs_review`):

| Source ID | Source Name | Reliability |
|-----------|------------|-------------|
| `ibn_kathir` | Tafsir Ibn Kathir | canonical (base form maps to `ibn_kathir_ar`) |
| `tabari` | Tafsir Al-Tabari | canonical (base form maps to `tabari_ar`) |
| `qurtubi` | Tafsir Al-Qurtubi | canonical (base form maps to `qurtubi_ar`) |
| `saadi` | Tafsir Al-Saadi | verified (base form maps to `saadi_ar`) |

All evidence items currently carry `"needs_review": true` meaning:
1. The ayah references are correct (taken from Quran text)
2. The tafsir chunk IDs are placeholder keys — they have not been matched to actual tafsir chunks in the DB
3. No explanation text has been pulled from tafsir sources

This means all story segment summaries in `quranStories.ts` must be marked `needs_review` in sunniReview.

---

## Recommended First Batch Implementation Order

1. `story_yusuf` — Complete surah, clear references, all aspects covered
2. `story_musa` — Most referenced prophet, key segments clear
3. `story_kahf` — Clear surah 18 reference, popular story
4. `story_ibrahim` + `story_ibrahim_fire` — Key fire miracle verse (21:69) is explicit
5. `story_nuh` — Clear cross-surah references
6. `story_bilqis` + `story_ant_hoopoe` — Surah 27 coverage
7. `story_maryam` — Surah 19 and 3 clear
8. `story_luqman` — Surah 31 clear, short and accessible
