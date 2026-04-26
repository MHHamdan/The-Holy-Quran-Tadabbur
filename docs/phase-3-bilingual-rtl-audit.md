# Phase 3 — Bilingual / RTL-LTR Audit

**Audit Date:** 2026-04-25  
**Scope:** All frontend pages and shared components under `frontend/src/`

---

## Pages Reviewed

| Page | Route | RTL Checked | LTR Checked | Language Switch |
|------|-------|-------------|-------------|-----------------|
| Home | `/` | ✓ | ✓ | ✓ |
| Mushaf | `/mushaf` | ✓ | ✓ | ✓ |
| Ask | `/ask` | ✓ | ✓ | ✓ |
| Search | `/search` | ✓ | ✓ | ✓ |
| Stories | `/stories` | ✓ | ✓ | ✓ |
| Concepts | `/concepts` | ✓ | ✓ | ✓ |
| Themes | `/themes` | ✓ | ✓ | ✓ |
| Similarity | `/similarity` | ✓ | ✓ | ✓ |
| Sources | `/sources` | ✓ | ✓ | ✓ |
| Tasmee | `/tasmee` | ✓ | ✓ | ✓ |
| Tools | `/tools` | ✓ | ✓ | ✓ |
| Status | `/status` | ✓ | ✓ | ✓ |

---

## Issues Found and Fixed in Phase 3

### 1. Hardcoded Arabic in `App.tsx` PageLoader
- **Issue:** `PageLoader` rendered `'جاري التحميل...'` regardless of language.
- **Fix:** Connected `PageLoader` to `useLanguageStore()` and used `t('loading', language)`.

### 2. `SourceBadge` not language-aware
- **Issue:** `SourceBadge` always showed English labels (Canonical, Verified, Supporting, Experimental) even in Arabic mode.
- **Fix:** Added `language` prop. Label now shows Arabic equivalent (متواتر, موثق, مساند, تجريبي) in Arabic mode.

### 3. `SourceAttribution` hardcoded English strings
- **Issue:** "Unverified", "Verified {date}", "Source" link were always English.
- **Fix:** Used `t('source_unverified')`, `t('source_verified_on')`, `t('source_link')`. Added `dir` attribute.

### 4. `MissingSourceWarning` hardcoded strings
- **Issue:** Warning text was inline English/Arabic instead of using translation key.
- **Fix:** Added `missing_source_warning` to translations; applied `dir` attribute.

### 5. `StatusDashboardPage` — `StatusBadge` labels always English
- **Issue:** 'Active', 'Error', 'Checking', 'Warning' hardcoded English regardless of language.
- **Fix:** Added `language` prop; used `t('status_active')` etc. Passed `language` to all four badge call sites.

### 6. `StatusDashboardPage` — table headers used `text-left`
- **Issue:** `<th>` elements used `text-left` which does not reverse in RTL.
- **Fix:** Changed to `text-start` (logical CSS property, direction-aware).

### 7. `ChatMessage.tsx` — aria-labels English-only
- **Issue:** `aria-label="Helpful"` and `aria-label="Not helpful"` were always English.
- **Fix:** Used inline language condition.

### 8. `AskPage.tsx` — suggestion selection border wrong in RTL
- **Issue:** Active suggestion item used `border-l-2` (physical left). In RTL this places the indicator on the wrong side.
- **Fix:** Changed to `border-s-2` (logical inline-start).

### 9. `AskPage.tsx` — loading spinner margin was LTR-specific
- **Issue:** `mr-2` in suggestion loading state.
- **Fix:** Changed to `me-2` (margin-end, logical property).

### 10. `AskPage.tsx` / `SearchHistoryPanel.tsx` — `text-left` on interactive buttons
- **Issue:** Multiple interactive buttons used `text-left` which does not reverse in RTL.
- **Fix:** Changed to `text-start` throughout.

### 11. `TafsirAccordion.tsx` — badge number position LTR-specific
- **Issue:** Source badge number used `-right-1` (physical right). In RTL this places it on the left corner, which is incorrect.
- **Fix:** Changed to `-end-1` (logical property).

### 12. `TafsirAccordion.tsx` — expand button `text-left`
- **Issue:** Accordion header button used `text-left`.
- **Fix:** Changed to `text-start`.

### 13. `VersesSection.tsx` — decorative accent `left-0`
- **Issue:** Top border accent used `left-0` (physical). In RTL mode this still starts from the physical left.
- **Fix:** Changed to `start-0` (logical inline-start).

### 14. `VersesSection.tsx` — translation block `text-left`/`text-right` toggle
- **Issue:** Used a language ternary to switch between `text-left` and `text-right`.
- **Fix:** Replaced with `text-start` which handles direction automatically via the parent `dir` attribute.

### 15. `globals.css` — `[dir="rtl"]` font override too broad
- **Issue:** `[dir="rtl"] { font-family: 'Noto Naskh Arabic'... }` applied Arabic font to ALL elements including navigation links, English source IDs, code, and technical labels.
- **Fix:** Scoped to specific Arabic content selectors (`.font-arabic`, `.arabic-text`, `.verse-text`, `.font-mushaf`, `p:lang(ar)`, `span:lang(ar)`).

### 16. `globals.css` — `slideIn` animation wrong direction in RTL
- **Issue:** `slideIn` used `translateX(-10px)` which slides from the right in RTL (incorrect — should enter from the right side which is the start in RTL).
- **Fix:** Added `[dir="rtl"] .animate-slideIn` override using `translateX(10px)`.

---

## Missing Translation Keys (Added)

| Key | Arabic | English |
|-----|--------|---------|
| `status_active` | نشط | Active |
| `status_error` | خطأ | Error |
| `status_checking` | جارٍ التحقق | Checking |
| `status_warning` | تحذير | Warning |
| `source_unverified` | غير موثق | Unverified |
| `source_verified_on` | موثق بتاريخ | Verified |
| `source_link` | المصدر | Source |
| `aria_helpful` | مفيد | Helpful |
| `aria_not_helpful` | غير مفيد | Not helpful |
| `missing_source_warning` | لا يوجد مصدر موثق... | No verified source... |
| `tafsir_explanations_header` | شروحات التفسير | Tafsir Explanations |
| `citation_sources_used` | المصادر المستخدمة | Sources Used |
| `answer_summary` | ملخص الإجابة | Answer Summary |

---

## Typography Improvements

- **`tafsir-text` CSS class** added for Arabic tafsir prose: `font-family: Noto Naskh Arabic`, `line-height: 2.2`, `direction: rtl`, applied in `TafsirAccordion`.
- **`[dir="rtl"] .prose` / `.leading-relaxed`** override: bumps line-height to `2.1` for better Arabic readability.
- **`verse-ref` / `source-id` / `code`** classes: force `direction: ltr; unicode-bidi: embed` so numbers, references, and source IDs always display LTR regardless of surrounding direction.

---

## Remaining Risks / Items for Human Review

| Risk | Severity | Notes |
|------|----------|-------|
| Playwright e2e tests cover English only | Medium | All e2e tests check English content. Consider adding Arabic-mode test passes. |
| `TafsirPanel.tsx` has `text-left` at line 521 | Low | Used inside an LTR-explicit container; low risk but could be cleaned up. |
| `ZakatCalculatorPage.tsx` ternary for text alignment | Low | Uses `isArabic ? 'text-right' : 'text-left'` — works correctly but could use `text-start`. |
| Arabic font loaded from CDN | Medium | If Noto Naskh Arabic / Amiri fonts fail to load, Arabic text falls back to system serif which may lack full Unicode Arabic coverage. Consider hosting fonts locally. |
| `methodology` field in TafsirAccordion | Low | `firstExplanation.methodology` is displayed without translation (raw string from database). |
| RTL `<table>` column ordering | Low | In Arabic mode, table cell order is not mirrored (column order stays LTR). This is acceptable for data tables but may feel unnatural. |
| No Vitest/Jest unit tests in frontend | Medium | Only Playwright e2e exists. Unit tests for language switching and `dir` attribute cannot run without a unit test runner. See Phase 3 QA checklist for recommended setup. |
