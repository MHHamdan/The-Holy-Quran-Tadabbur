# Surah Memory Atlas — Data Audit

## Overview

This document audits all available Quran metadata for the Surah Memory Atlas tool.
Conducted against the current state of the Tadabbur Al-Quran repository.

---

## Available Metadata (from `data/raw/quran_uthmani.json`)

| Field | Available | Notes |
|---|---|---|
| Surah number (1–114) | ✓ | `sura_no` — all 114 surahs present |
| Arabic name | ✓ | `sura_name_ar` — Uthmani format with diacritics |
| English transliteration | ✓ | `sura_name_en` — e.g., "Al-Faatiha", "Al-Baqara" |
| Ayah count | ✓ | Derivable by counting ayahs per surah |
| First ayah reference | ✓ | Derivable: `{sura_no}:1` |
| Last ayah reference | ✓ | Derivable: `{sura_no}:{max_aya_no}` |
| First ayah text preview | ✓ | `aya_text` where `aya_no == 1` — from verified Quran data |
| Last ayah text preview | ✓ | `aya_text` where `aya_no == max` — from verified Quran data |
| Page start / end | ✓ | `page` field — all 114 surahs have page data |
| Juz start / end | ✓ | `jozz` field — all 114 surahs have juz data |

## Missing Metadata (not in current data files)

| Field | Status | Plan |
|---|---|---|
| Makki / Madani | ✗ Not in data files | Include as curated metadata, mark `needs_review` |
| English name meaning | ✗ Not in data files | Include as curated metadata, mark `needs_review` |
| Main topics (per surah) | ✗ Not per-surah | Mark `missing_metadata` |
| Memory clues | ✗ Not available | Mark `missing_metadata` |
| Related stories | ✗ Not mapped per-surah | Mark `missing_metadata` (future: link from KG) |
| Related themes | ✗ Not mapped per-surah | Mark `missing_metadata` (future: link from themes) |
| Hizb mapping | ✗ Not in data | Omit |

---

## Derivable Computed Fields

| Field | How Computed |
|---|---|
| `lengthCategory` | short (1–20), medium (21–80), long (81–180), very_long (181+) |
| `quranPosition` | beginning (1–10), early (11–30), middle (31–70), late (71–100), ending (101–114) |
| `juzStart` / `juzEnd` | min/max of `jozz` per surah — trusted |
| `pageStart` / `pageEnd` | min/max of `page` per surah — trusted |
| `firstAyahRef` | `"{surahNo}:1"` |
| `lastAyahRef` | `"{surahNo}:{ayahCount}"` |

---

## Data Source Assessment

| Source ID | Reliability | Used For |
|---|---|---|
| `quran_hafs_local` | canonical | All ayah text, page, juz data |
| `surah_atlas_metadata` | needs_review | Makki/Madani classification, English meanings |

The `surah_atlas_metadata` source ID will be added to `sourceRegistry.ts`.
It references classical Islamic scholarship (Al-Itqan by Suyuti, standard Quran sciences works).
All entries from this source must display a `needs_review` badge.

---

## Page Count Assessment

- Page data is available for all 114 surahs from `data/raw/quran_uthmani.json`.
- The page field maps to Mushaf Al-Madinah Al-Nabawiyyah layout (standard 604-page Mushaf).
- Page range can be safely derived as `min(page)` to `max(page)` per surah.
- This is trusted data — no guessing required.

---

## Juz Range Assessment

- Juz data is available for all 114 surahs from `data/raw/quran_uthmani.json`.
- Juz values range 1–30 as expected.
- Can be safely derived as `min(jozz)` to `max(jozz)` per surah.

---

## First/Last Ayah Preview Safety

- The `aya_text` field contains Uthmani script with diacritics from verified data.
- Previews must be loaded from this field only, never hardcoded.
- The build script reads them at generation time; the generated JSON carries them.
- The validator confirms these match the source file.

---

## Makki/Madani Classification

**Status: NOT in current data files.**

The standard classification from classical Islamic scholarship (primarily Al-Suyuti's Al-Itqan fi Ulum al-Quran) is included in the build script as curated metadata. This is the accepted scholarly consensus but:
- There are 7 disputed surahs (scholars differ on their classification)
- Disputed surahs are marked `revelationType: "unknown"` with a note
- All Makki/Madani entries are marked `needs_review` until a human scholar verifies

---

## Risks

| Risk | Mitigation |
|---|---|
| AI-generated topics | No AI-generated topics included; missing_metadata shown instead |
| Invented ayah text | All ayah text loaded from `data/raw/quran_uthmani.json` only |
| Incorrect Makki/Madani | Disputed surahs marked unknown; all marked needs_review |
| Page count guessing | Page data loaded from trusted Quran file, not guessed |
| Memory clues without source | Not included; missing_metadata shown |

---

## Implementation Plan

1. Add `surah_atlas_metadata` to `sourceRegistry.ts`
2. Create TypeScript type `SurahMemoryItem`
3. Build `scripts/build-surah-memory-atlas.ts` — generates JSON from quran_uthmani.json
4. Build `scripts/validate-surah-memory-atlas.ts`
5. Run build script → `frontend/src/data/generated/surahMemoryAtlas.json`
6. Build frontend page at `/tools/surah-memory-atlas`
7. Wire route and ToolsPage card
8. Add bilingual translation keys
9. Add tests

---

*Audited: 2026-05-10*
