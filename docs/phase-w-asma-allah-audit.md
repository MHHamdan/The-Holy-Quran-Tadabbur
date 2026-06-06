# Phase W — Asmā' Allah Page — Pre-Build Audit

_Last updated: 2026-05-17_

## Symptom

The existing "أسماء الله الحسنى" tab inside `/themes` rendered:

```
الكل (0)
الذات (0)
الجمال (0)
الجلال (0)
الكمال (0)
الأفعال (0)
جاري التحميل...
```

## Root cause

The tab is implemented in `frontend/src/pages/ThemesPage.tsx::AllahNamesTab`.
It calls `quranApi.getAllahNames({ lang, include_verses: true, max_verses_per_name: 5 })`
which hits the backend at `GET /api/v1/quran/allah-names`
(`backend/app/api/routes/quran.py::get_allah_names`). That route:

1. Loads the canonical 99-names list from `backend/app/data/allah_names.py`
   (1,166 lines — already curated with meanings + categories).
2. For each name, runs a `SELECT * FROM quran_verse` against the DB and
   filters in Python by alias substring.
3. Highlights and returns the matched verses.

Why the page shows zeros:

- The **counts** are computed in the UI as `names.filter(n => n.category === cat).length` — these counts are 0 while `names = []` (loading state).
- The API call is **slow** (it scans the full 6,236-verse table per name)
  and may **time out** or **fail silently** in environments where the DB
  isn't populated (no Quran data ingest).
- The UI doesn't surface the API error; it stays on "جاري التحميل..."
  indefinitely, so categories stay at 0.

In short: the page **never receives any names** because the runtime DB
scan is the wrong architecture. The fix is to switch to a **static atlas**
built ahead of time from `data/raw/quran_uthmani.json`.

## Existing data available

- `data/raw/quran_uthmani.json` — 6,236 ayahs of canonical Uthmani text.
- `backend/app/data/allah_names.py` — 99 names with categories +
  curated meanings (project's own editorial — already source-traceable to
  Al-Ghazali / Ibn Kathir / Ibn Hajar).
- `frontend/src/data/generated/quranTopicAtlas.json::topic_allah` —
  1,916 ayahs already linked to `topic_allah`. This is a useful Phase V
  cross-reference but is NOT a per-Name breakdown.
- `frontend/src/data/sourceRegistry.ts` — `quran_uthmani_cloud` registered
  as canonical source.

## What's missing

- A per-Name ayah catalogue with surah numbers, ayah numbers, and matched
  surface form (no Quran text embedded).
- A documented basmalah-counting policy (113 surah-opening basmalahs
  should NOT inflate the counts of الله / الرحمن / الرحيم).
- Backend API that returns precomputed counts so the UI never depends on a
  runtime DB scan.
- Frontend page that uses those counts and gracefully handles missing
  meanings (the bilingual safe message).
- Validators that enforce no-Quran-text-in-atlas, occurrenceCount integrity,
  source allowlist, and no-auto-verified-meaning.
- Review-workflow integration so meanings/categories cannot become
  "verified" without scholar sign-off.

## Implementation plan (Phase W)

1. **Types** (`frontend/src/types/asmaAllah.ts`) — defined.
2. **Seed list** (`frontend/src/data/asmaAllahSeeds.ts`) — 100 entries (99
   names + Allah), with conservative aliases and per-name warnings where
   the name is rare/contextual.
3. **Basmalah policy** (`docs/asma-basmalah-counting-policy.md`) —
   documents the surah-opening exclusion rule.
4. **Extraction script** (`scripts/build-asma-allah-atlas.ts`) — scans the
   canonical Quran data, detects occurrences with strict word boundaries +
   clitic-prefix handling for "Allah", excludes basmalah, computes
   pairings.
5. **Validator** (`scripts/validate-asma-allah-atlas.ts`) — enforces the
   atlas safety contract.
6. **Backend API** (`backend/app/api/routes/asma.py`) — 6 endpoints
   reading the static JSON; no DB scan.
7. **Frontend** (`frontend/src/pages/AsmaAllahPage.tsx` +
   `AsmaAllahDetailPage.tsx`) — new pages at `/themes/asma` and
   `/themes/asma/:nameId`. The existing "Names of Allah" tab in
   `ThemesPage.tsx` is updated to **link** to the new page rather than
   render the broken loader.
8. **Review workflow** (`scripts/generate-review-tasks.ts` extended with
   `asma_name`, `asma_meaning`, `asma_category`, `asma_occurrence`,
   `asma_pairing`).
9. **Tests** (`backend/tests/unit/test_asma_allah_atlas.py`).
10. **Docs** (this file + 4 others).

## What we deliberately don't change

- The existing `/api/v1/quran/allah-names` endpoint stays, used by older
  callers; the new `/api/v1/quran/asma/*` endpoints are additive.
- The existing `backend/app/data/allah_names.py` curated module stays as
  a reviewer-facing source of category labels.
- The `themes` page tab navigates to the new page rather than rendering
  in-tab content; this keeps the URL space clean (`/themes/asma`).
