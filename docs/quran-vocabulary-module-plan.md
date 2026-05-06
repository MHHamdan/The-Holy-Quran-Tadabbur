# Phase F — Quranic Vocabulary / Gharib Al-Quran Module

**Status:** Placeholder — no verified data source available yet  
**Created:** 2026-05-06  
**Related policy:** `docs/closed-corpus-quran-ai-policy.md` §4 (Source Category Gaps)

---

## 1. Purpose

Quranic vocabulary (غريب القرآن / Gharib Al-Quran) refers to rare, unusual, or technically precise words in
the Quran whose meanings require classical Arabic lexicography and scholarly tradition to explain accurately.

This module will allow users to look up individual words and receive:
- Root (جذر) and morphological family
- Classical lexical meaning from a verified source
- Example verses that use the word or its root
- Source attribution (required on every result)

---

## 2. Audit Finding — No Verified Data Exists

The following audit (2026-05-06) confirmed no word-level vocabulary data exists on the platform:

| Path | Checked | Finding |
|---|---|---|
| `db/schema.sql` | ✓ | No vocabulary or lexicon tables |
| `backend/app/models/` | ✓ | No VocabEntry model (grammar.py has POS tags but not word meanings) |
| `data/raw/quran_uthmani.json` | ✓ | Verse-level only — no word-by-word data |
| `data/raw/hafs_smart_v8.json` | ✓ | Verse-level only |
| `data/raw/tafsir_*.json` | ✓ | Verse-level tafsir, not lexicons |
| `backend/app/api/routes/vocabulary.py` | ✓ | Did not exist (created in Phase F) |

**Decision:** Create schema, documentation, and safe placeholder per Phase F policy.
AI must NOT generate word meanings from general knowledge alone.

---

## 3. Planned Verified Sources

All sources below require license verification before integration:

| Source | Arabic Name | Notes |
|---|---|---|
| Lisan Al-Arab | لسان العرب (ابن منظور) | Classical Arabic lexicon; public domain (d. 711 AH) |
| Mufradat Al-Raghib | مفردات ألفاظ القرآن (الراغب الأصفهاني) | Specialized Quranic vocabulary; public domain (d. 502 AH) |
| Al-Qamus Al-Muhit | القاموس المحيط (الفيروزآبادي) | Classical lexicon; public domain (d. 817 AH) |
| Lane's Arabic Lexicon | — | English-Arabic; public domain (19th century) |

All must be added to `sourceRegistry.ts` with `reliabilityLevel: 'verified'` before displaying to users.

---

## 4. Database Schema (Planned)

```sql
-- Planned — not yet created
CREATE TABLE vocabulary_entries (
    id          SERIAL PRIMARY KEY,
    word_ar     TEXT NOT NULL,          -- The Quranic word (without diacritics for indexing)
    word_ar_full TEXT NOT NULL,         -- With full diacritics
    root_ar     TEXT,                   -- Trilateral/quadrilateral root
    pattern_ar  TEXT,                   -- Arabic morphological pattern (وزن)
    meaning_ar  TEXT NOT NULL,          -- Classical Arabic meaning
    meaning_en  TEXT,                   -- English gloss
    source_id   TEXT NOT NULL           -- REFERENCES trusted_sources
                REFERENCES trusted_sources(source_id),
    verse_refs  TEXT[],                 -- e.g. ['2:255', '24:35']
    created_at  TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewer_id TEXT
);

CREATE INDEX idx_vocab_word ON vocabulary_entries (word_ar);
CREATE INDEX idx_vocab_root ON vocabulary_entries (root_ar);
```

---

## 5. API Design (Planned)

### GET /api/v1/vocabulary/lookup?word={word}

**Current behavior (placeholder):** Returns `status: "no_verified_source"` with safe bilingual message.

**Future behavior (when data exists):** Returns:

```json
{
  "word": "صمد",
  "status": "found",
  "root": "ص م د",
  "meaning_ar": "السيد الذي يُصمد إليه في الحوائج",
  "meaning_en": "The Self-Sufficient Master Whom all creatures need",
  "source_id": "mufradat_al_raghib",
  "source_title": "مفردات ألفاظ القرآن",
  "example_verses": ["112:2"],
  "message_en": null,
  "message_ar": null
}
```

### GET /api/v1/vocabulary/status

Returns module availability, planned sources, and safe-refusal message.

---

## 6. Safety Rules

These rules must be enforced by the implementation and tests:

1. **Never generate meaning from AI alone.** Every meaning must have a `source_id` pointing to a verified lexicon.
2. **No fatwa implications.** Vocabulary meanings are definitional, not legal rulings. Never phrase meanings as Islamic rulings.
3. **No morphology speculation.** If root is unknown or disputed, return `root: null` with a note rather than guessing.
4. **Source required on every result.** Even if a word is found, `source_id` must always be returned.
5. **Safe refusal for unknown words.** If word is not in the database, return `status: "no_verified_source"` — not a generated guess.

---

## 7. Frontend Integration (Placeholder)

Page: `/tools/vocabulary`

**Phase F (current):** Displays search input + safe-refusal state with bilingual message explaining the feature is planned but no verified data is available yet.

**Future:** Displays results with source attribution, root, meaning, and example verses.

---

## 8. Phases for Full Implementation

| Phase | Task | Prerequisite |
|---|---|---|
| F (current) | Safe placeholder API + frontend UI shell | None |
| F.1 | License verification for Mufradat Al-Raghib | Human review |
| F.2 | Ingest Mufradat data into vocabulary_entries table | F.1 |
| F.3 | Connect lookup endpoint to DB | F.2 |
| F.4 | Add root-based search and verse cross-reference | F.3 |
| F.5 | Human review workflow for each vocabulary entry | Phase 6 review system |
