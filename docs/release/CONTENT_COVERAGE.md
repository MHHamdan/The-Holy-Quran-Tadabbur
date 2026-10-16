# Content coverage and provenance (RG-04, RG-28)

Third (final) release audit. Branch `release/v1-completion-swarm` at `475ae98`, audited 2026-10-16
against the local dev DB (`localhost:19432/tadabbur`), the Qdrant index (`localhost:19633`), the
API on `:19800` and the web app on `:19300`. The second audit (on `4b37193`) graded RG-04 PASS and
RG-28 FAIL.

The numbers come from
`python3 scripts/content_coverage_report.py [--probe-audio] [--no-index] [--out file.json]`.
The script reads the DB, the repo data (TypeScript modules via `npx tsx`), the pinned HF tafsir
dataset from the local HF cache, and the Qdrant `tafseer_chunks` collection, and prints sorted JSON.
Two runs without `--probe-audio` were byte-identical (sha256 `f3216509e235f3c8…`).
This round the script adds: stored tafsir text compared verbatim with the pinned
`riotu-lab/Quran-Tafseers@9ddbdeec` dataset it is credited to; placeholder passages; story-atlas
event refs that resolve to a non-empty, enabled, licensed passage; stale manifest licence notes;
DB `source_url` vs registry `sourceUrl`; and the RAG vector index coverage and staleness per enabled
tafsir source.

## Verdict

Updated after round 5 (HEAD `76e1950`+, script re-run on the dev DB and Qdrant).

| Gate | Grade | Why |
|---|---|---|
| **RG-04** content coverage | **PASS** | Qur'an 114/114 and 6236/6236, byte-identical to Tanzil. All 22 translations are 6236/6236, verbatim with QuranEnc. The 4 servable (enabled, licence-verified) tafsir sources are all at 99% or more (tabari 99.95, baghawi 99.98, ibn_kathir_ar 99.49, qurtubi 99.01). Qur'anic duas 66/66 are cited and exact. i18n parity is 926/926. Audio: 6 reciters x 6236 URLs, probe 30/30. The RAG vector index covers far less (see below); keyword/verse retrieval from Postgres covers every servable source. |
| **RG-28** provenance | **PASS (owner items open)** | Story-atlas events cite only `ibn_kathir_ar` (62/62 resolve). tabari, qurtubi, ibn_kathir_ar and baghawi equal the pinned Apache-2.0 dataset for 100% of passages (ignoring whitespace). Al-Muyassar is on licence hold (`license_verified=0`, migration `r5c1a2b3c4d5`): no endpoint serves its text (all public `/quran/*` tafsir queries now filter on `servable_source_ids()`), RAG never cites it, and the default edition is al-Baghawi. Stale spa5k manifest notes were corrected. The Qdrant index has 0 orphan and 0 placeholder points, and retrieval resolves every hit to the DB row. Owner decisions: confirm or replace the Muyassar licence; KFGQPC text files in the public repo. |

## Tafsir (`tafseer_sources`, `tafseer_chunks`)

Coverage is the set of distinct `(sura, ayah)` covered by non-empty chunk ranges. "Verbatim" compares
each stored passage with the pinned dataset `riotu-lab/Quran-Tafseers@9ddbdeec` (sha256
`0e4172d4…`, verified locally).

| Source | Enabled / visible | Ayat | Coverage | Missing | Verbatim vs dataset (exact / ignoring whitespace) | Manifest | Registry |
|---|---|---|---|---|---|---|---|
| tabari_ar | yes / yes | 6233 | 99.95% | 1:1, 77:16-17 | 5836 / **6233 of 6233** | available | cleared |
| baghawi_ar | yes / yes | 6235 | 99.98% | 1:1 | **6235 / 6235** | available | cleared |
| muyassar_ar | yes / **no (licence hold)** | 6236 | 100.00% | — | 6235 / 6235 (+1:1 not in dataset) | **pending_owner_confirmation** | **restricted** |
| ibn_kathir_ar | yes / yes | 6204 | 99.49% | 32 (1:1, 26:174-180, …) | **6204 / 6204** | available_via_api | cleared |
| qurtubi_ar | yes / yes | 6174 | 99.01% | 62 (1:1, 26:33-49, …) | 6111 / **6174 of 6174** | available | cleared |
| ibn_kathir_en | no / no | 6236 | 100% | — | n/a | pending_user_input | blocked |
| jalalayn_en | no / no | 6236 | 100% | — | n/a | pending_user_input | blocked |

* The whitespace-only differences (397 tabari, 63 qurtubi) are the seeder's normalisation: the
  dataset glues the quoted verse to the commentary ("مَرَضٌقال"); the DB adds a space.
* 0 placeholder passages ("لا يوجد تفسير") remain in the DB. The 1:1 gap is the dataset's own (it has
  6235 rows per work).
* Manifest `enabled_ids` equals the DB enabled set. `/tafseer/compare/2/255` returns the 4 servable sources (al-Muyassar withheld).
* Reader panel: `/tafseer/external/verse/26/40?edition=qurtubi`, `/1/1?edition=baghawi` and
  `/1/1?edition=tabari` return 404 `NO_PASSAGE_IN_SOURCE`, and `/2/251?edition=ibn_kathir` returns the
  stored passage (`source: tadabbur_library`). No Quran.com proxy and no placeholder. The default edition
  (no `edition` parameter) is `baghawi`; `edition=muyassar` returns 403 `EDITION_NOT_LICENSED`.

### RAG vector index (Qdrant `tafseer_chunks`)

Retrieval resolves every vector hit to its `tafseer_chunks` row (one batched query) and serves the DB
text from enabled, licence-verified sources only; orphan, placeholder and unlicensed hits are dropped.
After round 5 the dev index was pruned of 85 orphan and 14 placeholder points
(`backend/scripts/index/prune_tafseer_index.py --only orphan,placeholder --apply`). Re-embedding the
missing passages needs HF credit (owner).

| Source | Points | Match current passage | Index coverage | Orphan | Placeholder | Stale |
|---|---|---|---|---|---|---|
| tabari_ar | 3215 | 3215 | 51.58% | 0 | 0 | 0 |
| qurtubi_ar | 3116 | 3116 | 50.47% | 0 | 0 | 0 |
| ibn_kathir_ar | 560 | 560 | 9.03% | 0 | 0 | 0 |
| baghawi_ar | 0 | 0 | 0.00% | 0 | 0 | 0 |
| muyassar_ar (licence hold, never retrieved) | 6236 | 6236 | 100.00% | 0 | 0 | 0 |

The disabled `ibn_kathir_en` and `jalalayn_en` hold another 12,472 points, kept deliberately (filtered
inside the Qdrant query and again in the DB join; re-embedding them later would cost HF credit).
Until re-indexing, /ask relies on the Postgres verse-reference and ranked keyword retrieval, which
covers all four servable sources.

## Audio

6 reciters on `everyayah.com/data/<folder>/{SSS}{AAA}.mp3` (5 also have an alquran.cloud fallback).
The verse table covers 114 surahs and 6236 ayat, so 6236 URLs can be built for each reciter (100%).
`--probe-audio`: 30/30 HEAD requests returned 200 `audio/*`. Host licences are still unconfirmed
(`everyayah_audio`, `islamic_network_audio`, `quranicaudio_audio` unverified; `quran_audio_cdn`,
`quran_com_verse_audio` unset).

## Stories

| Metric | Value |
|---|---|
| Stories / with segments | 124 / 124 |
| Segments (valid ayah ref) | 322 (322) |
| Distinct linked ayat | 1283 (20.57%) |
| Segments with evidence chunks | 319 / 322 (99.07%) |
| Segment evidence ids: total / resolve / from enabled sources | 2195 / 2195 / 2195 |
| story_connections | 10, all evidenced; 11 ids, 11 enabled |
| cross_story_connections | 36, all evidenced; 281 ids, 281 enabled |
| event_connections / theme_connections | 54 / 4, none evidenced |
| **story_events (story atlas)** | **62; 62/62 refs cite `ibn_kathir_ar` and resolve to a non-empty, enabled, licensed passage** |

API: all 8 clusters return the same event count as the DB (5+8+8+6+7+5+11+12). Playwright at 390 px on
`/story-atlas/cluster_musa_khidr`: "In tafsir · Tafsir Ibn Kathir (Arabic)" (en) and "في كتب التفسير ·
تفسير ابن كثير" (ar). No "(English)" label.

## Themes

50 themes. 6 (12%) have segments: 10 segments covering 17 ayat (0.27%). All 10 segments are sourced and
13/13 evidence ids resolve. 0 are verified. The "analytical study aid" label and the withholding are
unchanged.

## Concepts

60 concepts, 33 with occurrences. 126 relationships: 0 with sufficient evidence, so every explanation is
withheld. 179 occurrences: 5 have an ayah ref and 0 have evidence chunks. Citation coverage is 2.79%.

## Duas and adhkar

| Set | Total | Citation | Exact match vs canonical |
|---|---|---|---|
| Qur'anic duas (`quranicDuas.ts`) | 66 | 66/66 (100%) | 66/66 (100%): 12 full verses, 54 word-aligned excerpts |
| `backend/app/data/duas.json` vs frontend | 66 | — | 0 mismatches |
| Adhkar, Qur'anic | 21 | 21/21 | 21/21 |
| Adhkar, non-Qur'anic | 52 | 52/52 sourceRef; 51/52 name a collection and number | n/a |
| Therapy prophetic-dua panel | 22 (7 Qur'anic, 15 hadith) | 0/15 hadith structured, so all 15 are hidden | n/a |

Totals: 161 entries; 94 Qur'anic (all exact) and 67 non-Qur'anic.

## UI i18n (`frontend/src/i18n/translations.ts`)

| Dictionary | Keys | Missing ar/en | Empty ar/en |
|---|---|---|---|
| translations | 926 | 0 / 0 | 0 / 0 |
| themeTranslations | 462 | 0 / 0 | 0 / 0 |
| aspectTranslations | 165 | 0 / 0 | 0 / 0 |
| figureTranslations | 155 | 0 / 0 | 0 / 0 |
| categoryTranslations | 6 | 0 / 0 | 0 / 0 |

Parity 100%, 0 duplicate keys, 0 of the 445 used `t('…')` keys undefined. The "Run seed_*.py" strings
are gone. The only Latin text in an Arabic value is `lang_toggle_en` ("English"), which is intentional.

## Provenance check (RG-28)

The check covers every enabled DB tafsir source, the manifest `enabled_ids`, the 22 translation
editions, the Qur'an text, the reader-panel editions, and the sources cited by story-atlas events.
39 entries were checked and 32 are clean (87.18%; it was 84.62%).

| Entry | Problem |
|---|---|
| muyassar_ar (DB and manifest) | Licence `pending_owner_confirmation`, registry `restricted`, yet `license_verified=1`, enabled, and the reader default. DB `source_url` is still the spa5k CDN, although the text is identical to the HF dataset. |
| tabari_ar, qurtubi_ar, ibn_kathir_ar (manifest) | `license.notes` still say "the stored digital copy was seeded from the spa5k tafsir_api CDN … the registry marks it unverified". Both statements are false now. |

8 religious registry entries have no `licenseStatus`: 6 lexicons, `quran_audio_cdn` and `quran_com_verse_audio`.

## Status of second-audit problems

| Second-audit problem | Status |
|---|---|
| P1 Story-atlas events cite the blocked `ibn_kathir_en` | **FIXED**. DB 62/62 `ibn_kathir_ar`, all resolving. There is a read-time filter (`story_atlas_evidence.filter_licensed_evidence`), and the UI label is checked in en and ar. `seed_story_atlas.py` has 0 `ibn_kathir_en` refs. `add_missing_events.py` still writes 27 (P3). |
| P1 Al-Muyassar served while its licence is pending | **NOT FIXED (owner)**. |
| P2 Footer credits HF for spa5k-seeded text | **FIXED**. All 3 works are verbatim with the pinned dataset, ignoring whitespace. Leftover: stale manifest notes (P3). |
| P2 Reader proxies Quran.com and shows its placeholder | **FIXED** in the DB and the reader routes. **NOT FIXED in the Qdrant index**: 99 placeholder points and 85 orphans (P2). |
| P3 "Run seed_*.py" shown to users | **FIXED**. |
| P3 Audio host licences | **NOT FIXED (owner)**. |
| P3 Registry lexicon/audio `licenseStatus` unset; event/theme connections unevidenced | **NOT FIXED**. |
