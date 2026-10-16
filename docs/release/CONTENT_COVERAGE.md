# Content coverage and provenance (RG-04, RG-28)

Second release audit. Branch `release/v1-completion-swarm` at `4b37193`, audited 2026-10-15
against the local dev DB (`localhost:19432/tadabbur`, alembic head `r3d1a2b3c4d5`) and the
API on `:19800`. The first audit (on `c6b5875`) graded RG-04 PASS and RG-28 FAIL.

The numbers come from `python3 scripts/content_coverage_report.py [--probe-audio] [--out file.json]`.
The script reads the DB and the repo data (TypeScript modules via `npx tsx`) and prints sorted
JSON. Two runs without `--probe-audio` were byte-identical (sha256 `ec5087d022610adf…`).
This round the script adds four checks: translations compared verbatim with the QuranEnc cache,
the licence status and stored-copy origin of each tafsir source, the evidence sources of
story-atlas events, and Latin words inside Arabic UI strings.

## Verdict

| Gate | Grade | Why |
|---|---|---|
| **RG-04** content coverage | **PASS** | Qur'an 100%. All 22 translations 100%, and their text and footnotes match the QuranEnc cache exactly. All 5 enabled tafsir sources are at 99% or more. Qur'anic duas 66/66 are cited and match the canonical text exactly. i18n parity is 926/926. Themes and concepts are thin, but they have no RG-04 target, are now labelled as a study aid, and withhold claims that have no source. |
| **RG-28** provenance | **FAIL** (improved) | Fixed since the first audit: Sa'di and Jalalayn-ar are no longer served, Baghawi is seeded from its licensed dataset, `enabled_ids` matches the DB, `source_url` is set on every row, and story and theme evidence resolve to enabled sources. Still failing: (1) all 62 story-atlas events cite the disabled, blocked `ibn_kathir_en`, and the page shows it as "Tafsir Ibn Kathir (English)". (2) The footer credits the HF Apache-2.0 dataset for tabari, qurtubi and ibn_kathir, but the stored text was seeded from the spa5k CDN, whose terms are not recorded. (3) Al-Muyassar is enabled while its licence is "pending owner confirmation, not cleared". 33/39 checked entries are complete (84.62%). |

## Qur'an text

| Metric | Value |
|---|---|
| Canonical file | `data/raw/quran_tanzil.json` (Tanzil Uthmani, CC BY 3.0) |
| Surahs (canonical / DB) | 114 / 114 |
| Ayat (canonical / DB) | 6236 / 6236 |
| DB `text_uthmani` byte-identical to canonical | 6236 / 6236 (100%) |
| Empty verse texts | 0 |
| `npx tsx scripts/validate-quran-integrity.ts` | exit 0: 21 passed, 0 failed, 1 warning |

## Translations

All 22 editions come from QuranEnc. `data/manifests/translation_sources.json` has
`license_status: verified` (2026-10-13), and every edition is `cleared` in the source registry.

| Check | Result |
|---|---|
| Editions with 6236/6236 non-empty verses | 22 / 22 |
| DB text identical to the cached QuranEnc file (verbatim term) | 6236/6236 in each of the 22 editions |
| Footnotes identical to the cache | 6236/6236 in each of the 22 editions |
| DB `edition_version` equal to the cache version | 22 / 22 |
| Orphan translator keys / manifest editions missing in DB | 0 / 0 |

## Tafsir (`tafseer_sources`, `tafseer_chunks`)

Coverage is the set of distinct `(sura, ayah)` covered by non-empty chunk ranges.

| Source | Enabled | User-visible | Ayat | Coverage | DB licence type | Manifest status | Registry | Stored text origin |
|---|---|---|---|---|---|---|---|---|
| tabari_ar | yes | yes | 6236 | 100.00% | public_domain_classical | available | cleared | spa5k CDN (footer says HF dataset) |
| muyassar_ar | yes | yes | 6236 | 100.00% | publisher_terms_non_commercial | **pending_owner_confirmation** | **restricted** | spa5k CDN (identical to HF for all 6235 verses) |
| baghawi_ar | yes | yes | 6235 | 99.98% (missing 1:1) | public_domain_classical | available | cleared | HF riotu-lab@9ddbdeec, sha checked |
| ibn_kathir_ar | yes | yes | 6197 | 99.37% (39 missing) | public_domain_classical | available_via_api | cleared | spa5k CDN (560/6197 identical to HF) |
| qurtubi_ar | yes | yes | 6176 | 99.04% (60 missing, incl. 26:33-49) | public_domain_classical | available | cleared | spa5k CDN (3177/6176 identical to HF) |
| ibn_kathir_en | no | no | 6236 | 100% | pending_verification | pending_user_input | blocked | — |
| jalalayn_en | no | no | 6236 | 100% | pending_verification | pending_user_input | blocked | — |

* `enabled_ids` in the manifest is `[ibn_kathir_ar, tabari_ar, qurtubi_ar, baghawi_ar, muyassar_ar]`, the same set as the DB.
* `/tafseer/compare/2/255` returns these 5 sources. `/tafseer/external/verse/2/255?edition=saadi` and `?edition=jalalayn` return 404.
* Reader panel: the stored passage is served first (`source: tadabbur_library`). For ayat with no stored passage (ibn_kathir 39, qurtubi 60, baghawi 1) the text is still proxied from Quran.com, whose terms are not recorded. For 26:40 the proxy returns Quran.com's placeholder "لا يوجد تفسير لهذه الأية" as if it were Qurtubi's text, under Qurtubi's licence footer.

## Audio

6 reciters. The primary scheme is `everyayah.com/data/<folder>/{SSS}{AAA}.mp3` (5 of them also
have an alquran.cloud fallback). The verse table covers 114 surahs and 6236 ayat, so all 6236 URLs
can be built for each reciter (100%). `--probe-audio` sent HEAD requests for 5 sample ayat per
reciter, and 30/30 returned 200 `audio/*`. The host licences in the registry are still unconfirmed:
`everyayah_audio`, `islamic_network_audio` and `quranicaudio_audio` are unverified, and
`quran_audio_cdn` and `quran_com_verse_audio` have no status.

## Stories

| Metric | Value |
|---|---|
| Stories / with segments | 124 / 124 |
| Segments (valid ayah ref) | 322 (322) |
| Distinct linked ayat | 1283 (20.57%) |
| Segments with evidence chunks | 319 / 322 (99.07%) |
| Segment evidence ids, resolving / from enabled sources | 2197 / 2197 / 2197 (was 3490, 1293 disabled) |
| `evidence_sources` citations | ibn_kathir_ar 8, tabari_ar 4, qurtubi_ar 3 (no `ibn_kathir_en`) |
| story_connections | 10, all with evidence; 11 ids, 11 resolve to enabled sources (was 0/11) |
| cross_story_connections | 36, all with evidence; 283 ids, 283 enabled |
| event_connections / theme_connections | 54 / 4, none with evidence |
| **story_events (story atlas)** | **62, all citing `ibn_kathir_en` (62/62 refs from a disabled, blocked source)** |

## Themes

50 themes. 6 of them (12%) have segments: 10 segments covering 17 ayat (0.27%). All 10 segments
are sourced, and 13/13 evidence ids now resolve (0/13 before). 0 segments are verified. Theme and
concept pages carry the bilingual notice "analytical study aid, not tafsir". Summaries without real
evidence are withheld, and so are the 6 consequences.

## Concepts

60 concepts, 33 of them with occurrences. 126 relationships: 0 with sufficient evidence and 0 with
ayah refs, so the API withholds every explanation (checked on `/concepts/person_musa/associations`).
179 occurrences: 5 with an ayah ref, 0 with evidence chunks, 0 verified. Citation coverage is 2.79%.

## Duas and adhkar

| Set | Total | Citation | Exact match vs canonical |
|---|---|---|---|
| Qur'anic duas (`quranicDuas.ts`) | 66 | 66/66 (100%) | 66/66 (100%): 12 full verses, 54 word-aligned excerpts |
| `backend/app/data/duas.json` vs frontend | 66 | — | 0 text mismatches |
| Adhkar, Qur'anic | 21 | 21/21 | 21/21 |
| Adhkar, non-Qur'anic | 52 | 52/52 sourceRef; 51/52 name a collection and number | n/a |
| Therapy prophetic-dua panel | 22 (7 Qur'anic, 15 hadith) | 0/15 hadith structured, so all 15 are hidden by design | n/a |

## UI i18n (`frontend/src/i18n/translations.ts`)

| Dictionary | Keys | Missing ar/en | Empty ar/en |
|---|---|---|---|
| translations | 926 | 0 / 0 | 0 / 0 |
| themeTranslations | 462 | 0 / 0 | 0 / 0 |
| aspectTranslations | 165 | 0 / 0 | 0 / 0 |
| figureTranslations | 155 | 0 / 0 | 0 / 0 |
| categoryTranslations | 6 | 0 / 0 | 0 / 0 |

Parity is 100%, with 0 duplicate keys. All 445 literal `t('…')` keys used in the code are defined.
Arabic values that contain Latin words: `lang_toggle_en` (intentional), `themes_run_seed` and
`stories_run_seed`. The last two are developer instructions ("Run seed_themes.py") that
ThemesPage shows to users in its empty state.

## Provenance check (RG-28)

The check covers every enabled DB tafsir source, the manifest `enabled_ids`, the 22 translation
editions, the Qur'an text, the reader-panel editions, and every tafsir source cited by story-atlas
events. Each must have a title, author, language, source and licence, and the licence must be
verified. 39 entries were checked and 33 are complete (84.62%).

| Entry | Problem |
|---|---|
| muyassar_ar (DB and manifest) | Licence `pending_owner_confirmation`; registry `restricted`. Enabled and shown. |
| tabari_ar, qurtubi_ar, ibn_kathir_ar | Stored text was seeded from the spa5k CDN, whose terms are unrecorded, but the footer credits the HF dataset (Apache-2.0). |
| ibn_kathir_en (story-atlas events) | Disabled and blocked ("DO NOT DISPLAY"), yet named as the tafsir source on 62 public events. |

Religious registry entries with no `licenseStatus`: 6 lexicons (gharib, mufradat, lisan, qamus,
nihaya, lane), `quran_audio_cdn` and `quran_com_verse_audio`.

## Status of first-audit problems

| First-audit problem | Status |
|---|---|
| P1 Reader panel serves Sa'di, Jalalayn-ar, Baghawi with no licence | **FIXED**. Sa'di and Jalalayn return 404. Baghawi is served from the DB with an HF Apache-2.0 provenance. |
| P1 Muyassar enabled while licence unverified; statements disagree | **PARTIAL (owner)**. DB, manifest and registry now agree, but the licence is still not cleared and the source is still enabled. |
| P1 Public story evidence cites `ibn_kathir_en` / unresolved ids | **PARTIAL**. Fixed for `/stories` segments, connections and cross-connections. **Not fixed for `/story-atlas/{cluster}` events (62/62 cite `ibn_kathir_en`, shown in the UI).** |
| P2 Themes/concepts almost entirely unsourced | **FIXED (mitigated)**. Study-aid label shown, unsourced claims withheld, theme evidence resolves 13/13. Coverage is still thin. |
| P2 `baghawi_ar` in enabled_ids but not in DB; `source_url` NULL | **FIXED**. |
| P2 Proxied footer shows HF licence while text comes from quran.com/tafsir.one | **PARTIAL**. The proxy is now used only for the 100 ayat without a stored passage. The stored-copy origin (spa5k) also disagrees with the footer. |
| P3 Audio host licences unverified | **NOT FIXED (owner)**. |
| P3 Qurtubi 60 / Ibn Kathir 39 missing ayat | **NOT FIXED**. Above target. The gap is filled by the proxy, which shows a placeholder string as tafsir text. |
