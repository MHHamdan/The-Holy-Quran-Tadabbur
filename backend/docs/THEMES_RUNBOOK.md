# Quranic Themes System - Runbook

This runbook documents how to maintain and validate the Quranic Themes system.

## Overview

The Themes system provides:
- 50 Quranic themes across 7 categories
- 360 verse segments with tafsir evidence
- Graph connectivity between related themes
- Arabic/English bilingual content

## Quick Commands

### Run All Validation (CI Gate)

```bash
cd backend
python scripts/verify/theme_completeness_audit.py --ci --min-verses 3
```

Exit codes:
- `0` = All validations pass
- `1` = Critical errors found

### Run Full Test Suite

```bash
# Theme audit tests
python -m pytest tests/unit/test_theme_completeness_audit.py -v

# Quran integrity tests
python -m pytest tests/unit/test_quran_integrity.py -v

# All tests
python -m pytest tests/unit/test_theme*.py tests/unit/test_quran_integrity.py -v
```

### Generate Audit Reports

```bash
# JSON report
python scripts/verify/theme_completeness_audit.py --json reports/theme_audit.json

# Markdown report
python scripts/verify/theme_completeness_audit.py --markdown reports/theme_audit.md

# Both
python scripts/verify/theme_completeness_audit.py \
    --json reports/theme_audit.json \
    --markdown reports/theme_audit.md
```

## Data Fix Scripts

### 1. Populate Theme Evidence

Assigns tafsir evidence chunks to theme segments.

```bash
# Preview changes (dry run)
python scripts/ingest/populate_theme_evidence.py --dry-run

# Apply changes
python scripts/ingest/populate_theme_evidence.py

# Only specific theme
python scripts/ingest/populate_theme_evidence.py --only theme_tawheed

# Force overwrite existing evidence
python scripts/ingest/populate_theme_evidence.py --force
```

### 2. Fix Arabic Field Leakage

Replaces English placeholders in Arabic fields.

```bash
# Preview changes
python scripts/ingest/fix_theme_arabic_fields.py --dry-run --verbose

# Apply changes
python scripts/ingest/fix_theme_arabic_fields.py

# Only specific theme
python scripts/ingest/fix_theme_arabic_fields.py --only theme_sabr
```

### 3. Fix Theme Graph Connectivity

Adds relationships to isolated themes.

```bash
# Preview changes
python scripts/ingest/fix_theme_graph.py --dry-run --verbose

# Apply changes
python scripts/ingest/fix_theme_graph.py
```

## Full Rebuild Pipeline

To rebuild themes from scratch and ensure CI passes:

```bash
cd backend

# 1. Run migrations
alembic upgrade head

# 2. Seed theme data
python scripts/ingest/seed_themes.py

# 3. Populate evidence
python scripts/ingest/populate_theme_evidence.py --force

# 4. Fix Arabic fields
python scripts/ingest/fix_theme_arabic_fields.py

# 5. Fix graph connectivity
python scripts/ingest/fix_theme_graph.py

# 6. Verify CI passes
python scripts/verify/theme_completeness_audit.py --ci --min-verses 3

# 7. Run tests
python -m pytest tests/unit/test_theme_completeness_audit.py tests/unit/test_quran_integrity.py -v
```

## Validation Rules

### Coverage Rules
- Every theme must have ≥1 segment
- Every theme must have ≥3 unique verses (configurable)

### Tafsir Grounding
- Every segment must have `evidence_chunk_ids`
- Approved sources: Ibn Kathir, Tabari, Qurtubi, Nasafi, Shinqiti, etc.
- Core themes require ≥2 distinct tafsir sources

### Arabic Integrity
- No Latin characters in `*_ar` fields
- No placeholder text (TODO, FIXME, lorem, etc.)
- All Arabic fields must be non-empty

### Consequence Rules
- `muharramat` themes require punishment/warning consequences
- `ibadat`, `akhlaq_fardi`, `akhlaq_ijtima` themes require reward/blessing consequences

### Graph Connectivity
- No isolated themes (all must connect via `related_theme_ids` or `parent_theme_id`)
- No self-loops in connections
- No duplicate edges

### Quran Integrity
- Exactly 114 surahs
- Exactly 6236 verses
- Correct verse counts per surah
- All text_uthmani contains Arabic characters

## Coverage Score Formula

Each theme gets a score from 0-100:

| Criterion | Points |
|-----------|--------|
| Has ≥3 unique verses | +40 |
| Has ≥2 tafsir sources | +20 |
| Has required consequences | +20 |
| Arabic fields clean | +10 |
| Connected in graph | +10 |

## Categories

| Category | Arabic | Description |
|----------|--------|-------------|
| `aqidah` | التوحيد والعقيدة | Theology & Creed |
| `iman` | الإيمان | Pillars of Faith |
| `ibadat` | العبادات | Acts of Worship |
| `akhlaq_fardi` | الأخلاق الفردية | Individual Ethics |
| `akhlaq_ijtima` | الأخلاق الاجتماعية | Social Ethics |
| `muharramat` | المحرمات والكبائر | Prohibitions |
| `sunan_ilahiyyah` | السنن الإلهية | Divine Laws |

## Troubleshooting

### CI Fails with SEGMENT_HAS_EVIDENCE

Segments are missing tafsir evidence. Run:
```bash
python scripts/ingest/populate_theme_evidence.py --force
```

### CI Fails with ARABIC_NO_ENGLISH_LEAK

Arabic fields contain English text. Run:
```bash
python scripts/ingest/fix_theme_arabic_fields.py
```

### CI Fails with THEME_GRAPH_CONNECTED

Theme is isolated in the graph. Run:
```bash
python scripts/ingest/fix_theme_graph.py
```

Or manually add `related_theme_ids` in the database.

### Theme Not Appearing in UI

Check:
1. Theme exists in `quranic_themes` table
2. Theme has segments in `theme_segments` table
3. Run seed script: `python scripts/ingest/seed_themes.py`

## CI Integration

The GitHub Actions workflow (`.github/workflows/theme-audit.yml`) runs:
1. Unit tests for audit script
2. Theme completeness audit in CI mode
3. Uploads JSON/Markdown reports as artifacts

To run locally what CI runs:
```bash
python -m pytest tests/unit/test_theme_completeness_audit.py -v
python scripts/verify/theme_completeness_audit.py --ci --min-verses 3
```

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/verify/theme_completeness_audit.py` | CI validation gate |
| `scripts/ingest/populate_theme_evidence.py` | Evidence assignment |
| `scripts/ingest/fix_theme_arabic_fields.py` | Arabic field fixes |
| `scripts/ingest/fix_theme_graph.py` | Graph connectivity |
| `scripts/ingest/seed_themes.py` | Initial data seeding |
| `tests/unit/test_theme_completeness_audit.py` | Audit unit tests |
| `tests/unit/test_quran_integrity.py` | Quran integrity tests |
| `.github/workflows/theme-audit.yml` | CI workflow |
