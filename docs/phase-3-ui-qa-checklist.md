# Phase 3 — Manual UI QA Checklist

Use this checklist before any release after Phase 3 changes. Cover all four test configurations.

---

## Test Configurations

| Config | Language | Viewport | Notes |
|--------|----------|----------|-------|
| **DEN** | English | Desktop (1280×800) | Default |
| **DAR** | Arabic | Desktop (1280×800) | Switch via Globe button |
| **MEN** | English | Mobile (375×812) | Chrome DevTools iPhone 12 |
| **MAR** | Arabic | Mobile (375×812) | Switch via Globe button |

---

## Global (All Pages)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| G1 | Page title in header shows correct language | ✓ | ✓ | ✓ | ✓ |
| G2 | All navigation labels show correct language | | | | |
| G3 | Globe toggle button visible and clickable | | | | |
| G4 | After language switch, all labels update (no English labels in Arabic mode) | | | | |
| G5 | Language preference persists on page reload | | | | |
| G6 | `dir` attribute on `<html>` is `ltr` in English, `rtl` in Arabic | | | | |
| G7 | Footer disclaimer shows in correct language | | | | |
| G8 | Loading spinner text shows correct language | | | | |
| G9 | No visible placeholder text (`[missing_key]` or raw key name) on any page | | | | |
| G10 | Numbers and verse references (2:255) display LTR inside Arabic text | | | | |

---

## Navbar

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| N1 | All nav icon tooltips show correct language | | | | |
| N2 | Active nav item highlighted correctly | | | | |
| N3 | Mobile scroll bar shows all nav items | | | | |
| N4 | In Arabic mode, nav text is right-aligned and icons are on correct side | | | | |
| N5 | Globe toggle shows opposite-language label (Taddabur vs تدبر) | | | | |

---

## Ask Page (`/ask`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| A1 | Page title "Ask About the Quran" / "اسأل عن القرآن" shows correctly | | | | |
| A2 | Search input placeholder shows correct language | | | | |
| A3 | Input text direction is `rtl` in Arabic mode | | | | |
| A4 | Search icon is on the correct side (right in Arabic, left in English) | | | | |
| A5 | Suggestion dropdown entries highlight on the correct side (start-side border) | | | | |
| A6 | Keyboard hint (↑↓ ↵ Esc) is visible on desktop, hidden on mobile | | | | |
| A7 | Ask button label shows correct language | | | | |
| A8 | Source selector labels ("Tafseer Sources" / "مصادر التفسير") correct | | | | |
| A9 | Source checkboxes show Arabic names in Arabic mode | | | | |
| A10 | Empty state question cards display `dir` correctly | | | | |
| A11 | Empty state category tabs show Arabic labels in Arabic mode | | | | |
| A12 | After asking, answer card shows "ملخص الإجابة" / "Answer Summary" | | | | |
| A13 | Confidence badge shows Arabic level label (ممتاز / متوسط / منخفض) in Arabic mode | | | | |
| A14 | Copy button shows "نسخ" / "Copy" correctly | | | | |
| A15 | Share button shows "مشاركة" / "Share" correctly | | | | |
| A16 | "Helpful?" / "مفيدة؟" feedback label shows correctly | | | | |
| A17 | Feedback thumbs up/down have correct aria-labels in both languages | | | | |
| A18 | MissingSourceWarning shows Arabic text in Arabic mode, English in English | | | | |
| A19 | MissingSourceWarning alert renders with correct `dir` attribute | | | | |
| A20 | NeedsClarificationNotice renders in correct language | | | | |
| A21 | CitationCards reliability badges show Arabic labels in Arabic mode | | | | |
| A22 | CitationCard excerpt text direction is correct (RTL for Arabic content) | | | | |
| A23 | TafsirAccordion source number badge is in the correct corner (end-side) | | | | |
| A24 | TafsirAccordion expand button is aligned to start | | | | |
| A25 | Tafsir explanation text uses larger line-height in Arabic mode | | | | |
| A26 | Processing time and citation count labels show correct language | | | | |
| A27 | Related verses panel shows Arabic verse text with `dir="rtl"` | | | | |
| A28 | "Go to Verse" arrow icon is flipped correctly in Arabic mode | | | | |
| A29 | "Clear chat" / "مسح المحادثة" label shows correctly | | | | |
| A30 | Follow-up suggestion chips display correctly in both directions | | | | |

---

## Search Page (`/search`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| S1 | Page title and subtitle show correct language | | | | |
| S2 | Search input placeholder shows correct language | | | | |
| S3 | Sample words show correct language | | | | |
| S4 | Search results header ("Search Results" / "نتائج البحث") correct | | | | |
| S5 | Arabic verse text in results has `dir="rtl"` | | | | |
| S6 | Surah/verse reference numbers are LTR in Arabic context | | | | |

---

## Sources Page (`/sources`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| SR1 | Page title shows correct language | | | | |
| SR2 | Reliability badge labels show Arabic in Arabic mode | | | | |
| SR3 | "Unverified" / "غير موثق" shows in correct language | | | | |
| SR4 | "Verified [date]" / "موثق بتاريخ [date]" shows correctly | | | | |
| SR5 | Source language code (AR/EN) stays LTR in Arabic mode | | | | |
| SR6 | "Source" external link label shows correct language | | | | |
| SR7 | Source title shows Arabic title in Arabic mode | | | | |

---

## Stories Page (`/stories`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| ST1 | Page title and subtitle show correct language | | | | |
| ST2 | Category labels (Prophets / Parables) show correct language | | | | |
| ST3 | Story cards display in correct direction | | | | |
| ST4 | "View All" / "عرض الكل" button shows correct language | | | | |

---

## Concepts Page (`/concepts`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| C1 | Page title shows correct language | | | | |
| C2 | Concept cards align correctly in both directions | | | | |
| C3 | Verse references stay LTR in Arabic mode | | | | |

---

## Themes Page (`/themes`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| T1 | Page title "Quranic Themes" / "المحاور القرآنية" shows correctly | | | | |
| T2 | Theme cards align correctly | | | | |
| T3 | "Explore Theme" / "استكشاف المحور" button shows correctly | | | | |

---

## Similarity Page (`/similarity`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| SM1 | Page title "Verse Connections" / "صلة الآيات" shows correctly | | | | |
| SM2 | Search input direction correct | | | | |
| SM3 | Popular verses section header shows correct language | | | | |
| SM4 | Similarity score labels show correct language | | | | |
| SM5 | Arabic verse text displays with `dir="rtl"` | | | | |

---

## Tasmee Page (`/tasmee`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| TS1 | Page title "Tasmeeʿ" / "التسميع" shows correctly | | | | |
| TS2 | Surah selector shows Arabic names in Arabic mode | | | | |
| TS3 | "Start Session" / "ابدأ التسميع" button shows correctly | | | | |
| TS4 | Recording state label shows correct language | | | | |
| TS5 | Progress indicators and accuracy labels show correct language | | | | |
| TS6 | Arabic Quran text in practice area has `dir="rtl"` | | | | |
| TS7 | Reveal mode labels show correct language | | | | |
| TS8 | Mistakes list shows correct language | | | | |
| TS9 | Microphone error message shows correct language | | | | |

---

## Tools Pages (`/tools/*`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| TL1 | Tools hub page labels show correct language | | | | |
| TL2 | Prayer Times page — time labels in correct language | | | | |
| TL3 | Hijri Calendar — month names in correct language | | | | |
| TL4 | Zakat Calculator — field labels in correct language | | | | |
| TL5 | Mosque Finder — search input direction correct | | | | |
| TL6 | Islamic Books — titles and descriptions in correct language | | | | |
| TL7 | Hajj/Umrah Guide — content in correct direction | | | | |

---

## Status Dashboard (`/status`)

| # | Check | DEN | DAR | MEN | MAR |
|---|-------|-----|-----|-----|-----|
| SD1 | Page title "Platform Status Dashboard" / "لوحة حالة المنصة" correct | | | | |
| SD2 | Tab labels (Frontend / Backend / Database) show correct language | | | | |
| SD3 | StatusBadge labels (Active/Error/Checking/Warning) show Arabic in Arabic mode | | | | |
| SD4 | Table headers are start-aligned (flip in RTL) | | | | |
| SD5 | Route/path code values stay LTR in Arabic mode | | | | |
| SD6 | Section card titles show correct language | | | | |

---

## Frontend Unit Test Setup Recommendation

No Vitest/Jest unit test framework is currently configured. Recommended setup:

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

Add to `vite.config.ts`:
```ts
test: {
  environment: 'jsdom',
  globals: true,
  setupFiles: './src/test/setup.ts',
}
```

Suggested test cases to add:
- `translations.test.ts`: All keys exist in both `ar` and `en`; `t()` never returns the bare key
- `LanguageStore.test.ts`: `setLanguage('ar')` sets `dir="rtl"` on `document.documentElement`
- `SourceBadge.test.tsx`: Arabic mode renders Arabic label; English mode renders English label
- `ChatMessage.test.tsx`: `aria-label` on feedback buttons matches current language
- `MissingSourceWarning.test.tsx`: Arabic mode renders Arabic text and `dir="rtl"`
- `StatusBadge.test.tsx`: All four status values render correct label in both languages
