# Surah Memory Atlas — Implementation Documentation

## Purpose

The Surah Memory Atlas is an interactive learning tool at `/tools/surah-memory-atlas` that helps
students remember all 114 surahs of the Quran: their names, order, Makki/Madani status,
ayah counts, page/juz ranges, and first/last ayah references.

---

## Data Model

```typescript
interface SurahMemoryItem {
  surahNumber: number;            // 1–114
  nameArabic: string;             // Uthmani script (from quran_uthmani.json)
  nameTransliteration: string;    // e.g., "Al-Faatiha"
  nameEnglish?: string;           // e.g., "The Opening" (curated, needs_review)
  revelationType: 'makki' | 'madani' | 'unknown';
  ayahCount: number;              // verified from Quran data
  lengthCategory: 'short' | 'medium' | 'long' | 'very_long';
  quranPosition: 'beginning' | 'early' | 'middle' | 'late' | 'ending';
  juzStart: number;               // verified from Quran data
  juzEnd: number;                 // verified from Quran data
  pageStart: number;              // verified from Quran data
  pageEnd: number;                // verified from Quran data
  firstAyahRef: string;           // e.g., "1:1"
  lastAyahRef: string;            // e.g., "1:7"
  firstAyahPreview?: string;      // Uthmani text from Quran data only
  lastAyahPreview?: string;       // Uthmani text from Quran data only
  mainTopicsArabic: string[];     // [] until sourced
  mainTopicsEnglish: string[];    // [] until sourced
  memoryClueArabic?: string;      // absent until sourced
  memoryClueEnglish?: string;     // absent until sourced
  relatedStories: string[];       // [] until KG linkage added
  relatedThemes: string[];        // [] until theme linkage added
  sourceIds: string[];            // registered source IDs only
  reviewStatus: 'verified' | 'needs_review' | 'missing_metadata';
}
```

---

## Metadata Sources

| Field | Source | Status |
|---|---|---|
| Arabic name | `quran_uthmani.json` (`sura_name_ar`) | Canonical |
| Transliteration | `quran_uthmani.json` (`sura_name_en`) | Canonical |
| Ayah count | `quran_uthmani.json` (counted) | Canonical |
| Juz range | `quran_uthmani.json` (`jozz`) | Canonical |
| Page range | `quran_uthmani.json` (`page`) | Canonical |
| First/last ayah text | `quran_uthmani.json` (`aya_text`) | Canonical |
| English meaning | Curated (Al-Suyuti consensus) | `needs_review` |
| Makki/Madani | Curated (Al-Itqan, Al-Suyuti) | `needs_review` |
| Main topics | Not yet available | `missing_metadata` |
| Memory clues | Not yet available | `missing_metadata` |

---

## What Is Verified

- All 114 surah Arabic names and transliterations
- All ayah counts (cross-validated against `quran_uthmani.json`)
- All page ranges (from `quran_uthmani.json` `page` field)
- All juz ranges (from `quran_uthmani.json` `jozz` field)
- All first/last ayah text previews (loaded from `quran_uthmani.json` at generation time)
- First/last ayah references (format: `{surahNumber}:{ayahNumber}`)

---

## What Is Missing / Needs Review

| Field | Why Missing |
|---|---|
| Main topics | No per-surah topic taxonomy exists in current sources |
| Memory clues | Not yet curated from scholarly works |
| Related stories | KG linkage not yet built per-surah |
| Related themes | Theme linkage not yet built per-surah |
| Makki/Madani | Available from curated metadata but needs human scholar verification |
| English meanings | Available from curated metadata but needs human verification |

---

## How the Build Script Works

`scripts/build-surah-memory-atlas.ts`:

1. Reads `data/raw/quran_uthmani.json` (6236 ayahs)
2. Groups ayahs by surah number
3. Calculates ayah count, page range, juz range per surah
4. Extracts first and last ayah text from verified data
5. Computes `lengthCategory` and `quranPosition` from counts/number
6. Looks up `revelationType` from curated Makki/Madani table
7. Looks up `nameEnglish` from curated English meanings table
8. Sets `reviewStatus: 'needs_review'` for all entries
9. Writes `frontend/src/data/generated/surahMemoryAtlas.json`
10. Writes `docs/generated/surah-memory-atlas-summary.md`

---

## How the Validator Works

`scripts/validate-surah-memory-atlas.ts`:

- 16 checks covering structure, counts, duplicates, cross-validation
- Every numeric field is cross-validated against `quran_uthmani.json`
- Every sourceId is checked against the source registry
- Every ayah preview is compared byte-for-byte against Quran data
- Exit code 0 = all checks pass

---

## How Quiz Mode Works

The quiz generates random questions from four types:
1. "What surah comes before [surah]?"
2. "What surah comes after [surah]?"
3. "Is [surah] Makki or Madani?"
4. "How many ayahs approximately? (short/medium/long/very_long)"
5. "What is the number of [surah name]?"
6. "What is surah number [N]?"

The student is shown the question and asked to answer mentally before revealing.
They then self-report correct/incorrect. No server-side scoring.
Score is tracked in component state only (resets on page reload).

---

## UI Features

| Feature | Location |
|---|---|
| Search by name/number/transliteration | List view search bar |
| Filter by revelation type | Filter panel |
| Filter by length | Filter panel |
| Filter by Quran position | Filter panel |
| Surah card with key facts | Left column |
| Detail panel with all metadata | Right column |
| Before/After navigation | Detail panel |
| First/last ayah previews | Detail panel |
| Visual map by Quran position | Map view tab |
| Quiz mode (6 question types) | Quiz tab |
| Link to Quran reader | Detail panel |
| RTL/LTR safe rendering | Throughout |
| Review status badges | All curated metadata |

---

## How Students Can Use This Tool

1. **Browse all 114 surahs** in the list view, search by name or number
2. **Click a surah** to see its details: position, ayahs, pages, Juz, first/last ayah
3. **Use the visual map** to see surahs grouped by their position in the Quran
4. **Use the quiz** to test recall: name, number, before/after, length, type
5. **Link to the Quran reader** to read the full surah
6. **Filter by Makki/Madani** to study revelation context
7. **Filter by length** to find short surahs good for memorization

---

## Future Improvements

- **Main topics per surah** — curate from classical tafsir sources (Ibn Kathir, Tabari)
- **Memory clues** — curate from pedagogical Islamic texts with proper attribution
- **Spaced repetition** — localStorage-based SRS for quiz mode
- **Progress tracking** — track which surahs the student has reviewed
- **Audio recitation** — link to Quran audio for each surah's first ayah
- **Teacher mode** — export surah flashcards
- **Printable sheets** — printable memorization charts
- **Related stories/themes** — link from existing KG and themes data
- **Hizb mapping** — add when available from trusted data source

---

*Created: 2026-05-10*
