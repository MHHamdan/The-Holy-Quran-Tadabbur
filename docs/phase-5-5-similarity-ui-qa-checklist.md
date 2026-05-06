# Phase 5.5 – Similarity UI QA Checklist

**Date:** 2026-04-27  
**Page:** `/similarity`

---

## Arabic UI (language = ar)

### 2:255 (آية الكرسي)

- [ ] Related ayahs load in KG Relations section
- [ ] Section header shows "الروابط المعرفية" with "قيد المراجعة" badge
- [ ] Global pending-review notice visible in Arabic
- [ ] Experimental toggle shows "إظهار العلاقات التجريبية" label
- [ ] Experimental toggle is OFF by default
- [ ] Relation types visible on cards (Arabic labels)
- [ ] Evidence items visible in expanded card (Arabic labels)
- [ ] "قيد المراجعة" badge visible on each evidence item
- [ ] "يتطلب مراجعة علمية" (human review) warning visible
- [ ] No result shows "معتمد" (approved) label
- [ ] Score shown as percentage (e.g., 46%)
- [ ] "عرض في المصحف" link visible and working
- [ ] RTL layout correct throughout
- [ ] Explanation shown in Arabic (explanationArabic)

### 12:18 (قصة يوسف)

- [ ] Related ayahs load
- [ ] "نفس القصة" or "نفس مقطع القصة" relation type visible
- [ ] Evidence shows story ID (e.g., "yusuf")
- [ ] Score reflects story-based relation weight
- [ ] Needs-review notice shown

### 18:9 (أصحاب الكهف)

- [ ] Related ayahs load
- [ ] Relation types include "نفس القصة"
- [ ] Evidence cards show story references
- [ ] Human review warning shown

### 28:76 (قارون)

- [ ] Related ayahs load (or safe empty state shown)
- [ ] If no results: "لا توجد صلات موثوقة متاحة لهذه الآية حالياً." visible
- [ ] Empty state message is in Arabic

### Invalid input (e.g., "999:999" or "abc")

- [ ] Error message shown for invalid surah number
- [ ] Error message in Arabic
- [ ] No crash or blank screen
- [ ] Supported formats hint shown

---

## English UI (language = en)

### 2:255 (Ayat Al-Kursi)

- [ ] Related ayahs load in KG Relations section
- [ ] Section header shows "Knowledge Graph Relations" with "Needs Review" badge
- [ ] Global pending-review notice visible in English
- [ ] Experimental toggle shows "Show experimental relations" label
- [ ] Experimental toggle is OFF by default
- [ ] Relation types visible on cards (English labels)
- [ ] Evidence items visible in expanded card (English labels)
- [ ] "Needs Review" badge visible on each evidence item
- [ ] "Human Review Required" warning visible
- [ ] No result shows "Approved" label
- [ ] Score shown as percentage
- [ ] "Open in Mushaf" link visible and working
- [ ] LTR layout correct throughout
- [ ] Explanation shown in English (explanationEnglish)

### 12:18 (Story of Yusuf)

- [ ] Related ayahs load
- [ ] "Same Story" or "Same Story Segment" relation type visible
- [ ] Evidence shows story ID
- [ ] Score reflects story-based relation weight

### 18:9 (People of the Cave)

- [ ] Related ayahs load
- [ ] Relation types include "Same Story"
- [ ] Evidence cards show story references

### 28:76 (Qarun)

- [ ] Related ayahs load (or safe empty state)
- [ ] If no results: "No verified related ayahs are available for this ayah yet." visible

### Invalid input

- [ ] Error message shown in English
- [ ] Supported formats hint shown

---

## Experimental Toggle Behavior

- [ ] Toggle starts OFF (default)
- [ ] With toggle OFF, no "Experimental" badges appear in results
- [ ] Turning toggle ON: page re-fetches with `include_experimental=true`
- [ ] After toggle ON: experimental warning visible below toggle label
  - AR: "العلاقات التجريبية مقترحات آلية وليست تفسيراً معتمداً."
  - EN: "Experimental relations are automated suggestions, not approved tafsir."
- [ ] Experimental results now appear with "Experimental" / "تجريبي" badge
- [ ] Experimental badge is gray (distinct from amber "Needs Review")

---

## Advanced Similarity Section (existing)

- [ ] Still loads and displays correctly
- [ ] Score breakdown visible
- [ ] Connection type badges visible
- [ ] Shared words/roots visible in expanded cards
- [ ] KG section appears below (not replacing existing section)

---

## RTL/LTR Layout

- [ ] Arabic UI: all text containers have `dir="rtl"`
- [ ] English UI: all text containers have `dir="ltr"`
- [ ] Mixed containers: no single `dir` set on container holding both languages
- [ ] FuzzyMatchWarning: shows Arabic in AR UI, English in EN UI
- [ ] Evidence cards: labels match language
- [ ] Section header: aligned correctly per language

---

## Review-Status Safety

- [ ] No card ever shows "Approved" / "معتمد" on the current data
- [ ] All cards show "Needs Review" / "قيد المراجعة" as expected
- [ ] Semantic-only results hidden by default (experimental toggle OFF)
- [ ] Semantic-only results, when shown, have "Experimental" badge and warning
- [ ] No text like "Allah means…" or religious interpretation appears in the UI
- [ ] Section header + global notice make it clear all relations are pending review

---

## Navigation Links

- [ ] "Open in Mushaf" / "عرض في المصحف" links to `/quran/{sura}#{aya}`
- [ ] Reference link in card header links to `/quran/{sura}#{aya}`
- [ ] Link opens correct verse in Quran page
- [ ] "Explore More" nav links (Search, Concepts) work

---

## Loading & Error States

- [ ] Loading spinner shows while KG fetch is in progress
- [ ] Loading message is bilingual
- [ ] Error state shows if KG endpoint unavailable
- [ ] Error message is bilingual
- [ ] Error does not crash the page (existing advanced section still shows)

---

## Notes for Reviewer

- All KG relations in the current build have `needs_review` status; no `approved` badges should appear.
- The `pathExplanation` field is defined in types but not yet populated by the backend service; no path explanation section will appear until the service is extended.
- The KG endpoint requires the stories manifest and curated concepts to be loaded. If data files are missing, the section shows "No verified related ayahs available."
