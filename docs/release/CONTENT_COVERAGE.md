# Content coverage and provenance (RG-04, RG-28)

Branch `release/v1-completion-swarm` at `c6b5875`, audited 2026-10-14 against the
local dev DB (`localhost:19432/tadabbur`) and the API on `:19800`.

Numbers come from `python3 scripts/content_coverage_report.py [--probe-audio] [--out file.json]`.
The script reads the DB and the repo data (TypeScript modules via `npx tsx`) and prints
sorted JSON. Two runs without `--probe-audio` gave byte-identical output (sha256 `7eda0bb1…`
before the evidence-resolution counters were added; re-checked identical after).

## Verdict

| Gate | Grade | Why |
|---|---|---|
| **RG-04** content coverage | **PASS** (on its stated targets) | Qur'an 100%, all 22 translations 100%, all 4 enabled tafsir sources ≥ 99%, Qur'anic duas 66/66 cited and exact, i18n parity 926/926. Themes and concepts are thin (see P2 items), but they have no RG-04 target. |
| **RG-28** provenance | **FAIL** | The reader's tafsir panel shows 3 works with no recorded licence, one of them (Sa'di) marked `pending_verification` in the manifest. Al-Muyassar is enabled while its manifest entry is still `pending_user_input` with `license_url: NEED_VERIFICATION`. Public evidence cites the disabled, unlicensed `ibn_kathir_en`. |

## Qur'an text

| Metric | Value |
|---|---|
| Canonical file | `data/raw/quran_tanzil.json` (Tanzil Uthmani, CC BY 3.0) |
| Surahs (canonical / DB) | 114 / 114 |
| Ayat (canonical / DB) | 6236 / 6236 |
| DB `text_uthmani` equal to canonical, byte for byte | 6236 / 6236 (100%) |
| Empty verse texts | 0 |
| `npx tsx scripts/validate-quran-integrity.ts` | exit 0: 21 passed, 0 failed, 2 warnings |

## Translations (`translation_editions`, `translations`)

All 22 editions come from QuranEnc. The manifest `data/manifests/translation_sources.json`
has `license_status: verified` (2026-10-13) and lists the republication terms.

| Edition | Lang | Ayat | Coverage |
|---|---|---|---|
| bosnian_rwwad, chinese_suliman, dutch_center, english_hilali_khan, english_rwwad, english_saheeh, french_montada, german_bubenheim, hausa_gummi, hindi_omari, indonesian_affairs, japanese_saeedsato, malayalam_kunhi, persian_ih, portuguese_nasr, somali_yacob, spanish_montada_eu, swahili_barawani, tamil_baqavi, turkish_rwwad, urdu_junagarhi, uzbek_mansour | bs zh nl en en en fr de ha hi id ja ml fa pt so sw ta tr ur uz | 6236 each | **100% each (22/22)** |

There are no orphan translator keys and no manifest editions missing from the DB. Every
edition row has a title, translator, version, source URL and licence.

## Tafsir: DB sources (`tafseer_sources`, `tafseer_chunks`)

Coverage counts the distinct valid ayat inside chunk ranges `sura_no:aya_start..aya_end`
that have non-empty content.

| Source | Enabled | User-visible | Ayat | Coverage | DB licence | Manifest status / licence type |
|---|---|---|---|---|---|---|
| tabari_ar | yes | yes | 6236 | 100.00% | public domain (classical) | available / public_domain_classical |
| muyassar_ar | yes | yes | 6236 | 100.00% | "educational and non-commercial use", `license_verified=1` | **pending_user_input / publisher_terms_non_commercial, license_url NEED_VERIFICATION, no provenance block** |
| ibn_kathir_ar | yes | yes | 6197 | 99.37% (39 missing) | public domain (classical) | available_via_api / public_domain_classical |
| qurtubi_ar | yes | yes | 6176 | 99.04% (60 missing, incl. 26:33–49) | public domain (classical) | available / public_domain_classical |
| ibn_kathir_en | no | no (DB routes) | 6236 | 100% | permission required | pending_user_input / pending_verification |
| jalalayn_en | no | no (DB routes) | 6236 | 100% | permission required | pending_user_input / pending_verification |

- All 4 enabled full-Qur'an sources are at or above the 99% target.
- The manifest `enabled_ids` includes `baghawi_ar`, which has no DB row and no chunks.
- `tafseer_sources.source_url` is NULL for all 6 rows. The source location is only in the manifest.

### Tafsir: reader panel (external proxy, `/tafseer/external/verse`)

`TafsirPanel` (QuranPage, StoryDetailPage) fetches these editions live from quran.com,
read.tafsir.one or quran-tafseer.com. Its footer's licence line comes from `sourceRegistry` via `db_source_id`.

| Edition | Host | Registry licence shown | Manifest |
|---|---|---|---|
| muyassar, ibn_kathir, tabari, qurtubi | quran_com | yes | as above |
| **saadi** | quran_com / tafsir.one | **"not yet recorded"** | `saadi_ar`: pending_user_input / pending_verification |
| **baghawi** | quran_com | **"not yet recorded"** (registry has `baghawi_ar`, but the edition has no `db_source_id`) | `baghawi_ar`: public_domain_classical |
| **jalalayn** (Arabic) | quran_tafseer | **"not yet recorded"** | no `jalalayn_ar` entry |

Live check: `GET /api/v1/tafseer/external/verse/2/255?edition=saadi` returns 200 with the Sa'di text.

## Audio

| Metric | Value |
|---|---|
| Reciters (`backend/app/services/audio_service.py`) | 6: abdul_basit (mujawwad), husary, maher_muaiqly, minshawi (mujawwad), mishary_afasy, saud_shuraim |
| URL scheme | `https://everyayah.com/data/{folder}/{SSS}{AAA}.mp3`, with a same-reciter fallback on cdn.islamic.network for 5 of 6 (none for Abdul Basit mujawwad) |
| Verse table | 114 surahs, 6236 ayat, so URLs can be built for 6236/6236 per reciter (100%) |
| Stream probe (`--probe-audio`; 1:1, 2:255, 2:286, 18:110, 114:6 for each reciter) | 30/30 HEAD 200 `audio/*` |
| Host licences in the registry | everyayah, islamic.network and quranicaudio are all `unverified` |

## Stories

| Metric | Value |
|---|---|
| Stories / with segments | 124 / 124 |
| Segments / with a valid ayah reference | 322 / 322 |
| Distinct linked ayat | 1283 (20.57% of the Qur'an) |
| Segments with evidence chunks | 319 / 322 (99.07%) |
| Segment evidence chunk ids (distinct / resolve / from an enabled source / from a disabled source) | 3490 / 3490 / 2197 / **1293** |
| `evidence_sources` citations | tabari_ar 4, qurtubi_ar 3, **ibn_kathir_en 8** |
| story_connections with evidence | 10/10 rows, but **0/11 ids resolve**; 10 are `ibn_kathir_en:…` strings returned by `GET /stories/{id}/connections` |
| cross_story_connections with evidence | 36/36 rows; 568 ids, all resolve, **only 283 to enabled sources** |
| event_connections with evidence | 0 / 54 |
| story_events with evidence | 62 / 62 |

## Themes

| Metric | Value |
|---|---|
| Qur'anic themes (published by `/themes`) | 50 |
| Themes with at least one segment | **6 / 50 (12%)** |
| Theme segments / sourced / verified | 10 / 10 / 0 |
| Theme evidence ids resolving to a chunk | **0 / 13** (`ibn_kathir:112:1`-style ids, not chunk ids) |
| Distinct ayat covered | 17 (0.27%) |
| theme_connections with evidence | 0 / 4 |

## Concepts

| Metric | Value |
|---|---|
| Concepts (DB) / curated file | 60 / 10 |
| Concepts with occurrences | 33 / 60 |
| Relationships (associations) / with sufficient evidence / with ayah refs | 126 / **0** / **0** |
| Occurrences / with ayah ref / with evidence chunks / verified | 179 / 5 / 0 / 0 |
| Citation coverage (occurrences with an ayah ref or evidence) | **2.79%** |

## Duas and adhkar

| Set | Total | Qur'anic | Non-Qur'anic | Citation | Exact match vs Tanzil |
|---|---|---|---|---|---|
| `QURANIC_DUAS` (DuasPage, `/duas` API) | 66 | 66 | 0 | 66/66 (100%) | **66/66 (100%)**: 12 full-verse, 54 word-aligned excerpts |
| `backend/app/data/duas.json` vs frontend | 66 | | | | 0 text mismatches |
| `ADHKAR` | 73 | 21 | 52 | 52/52 have `sourceRef`; 51/52 name a collection and number (`salawat` cites Qur'an 33:56 as its basis) | Qur'anic 21/21 |
| Therapy `PropheticDuasPanel` | 22 | 7 (rendered from canonical text by reference) | 15 | 0/15 structured hadith, so all 15 stay hidden by design | n/a |

## UI i18n (`frontend/src/i18n/translations.ts`)

| Dictionary | Keys | Missing ar/en | Empty ar/en |
|---|---|---|---|
| translations | 926 | 0 / 0 | 0 / 0 |
| themeTranslations | 447 | 0 / 0 | 0 / 0 |
| aspectTranslations | 165 | 0 / 0 | 0 / 0 |
| figureTranslations | 155 | 0 / 0 | 0 / 0 |
| categoryTranslations | 6 | 0 / 0 | 0 / 0 |

- Parity is 100%. There are no duplicate keys, and all 445 literal `t('…')` keys used in `src` are defined.
- Some values look wrong to the checker but are intended: `lang_toggle_en`, an ar value with no Arabic letters, is the "English" toggle label. `lang_toggle_ar`, `vocab_about_gharib` and `vocab_search_placeholder` are en values that quote Arabic terms on purpose.

## Provenance check (title, author, language, source, licence, licence verified)

There are 39 checked entries: enabled DB tafsir sources, manifest `enabled_ids`, the 22
translation editions, Qur'an text, and the reader-panel editions. **4 have issues (89.74% complete):**

| Entry | Problem |
|---|---|
| muyassar_ar (enabled DB) | Manifest `status: pending_user_input`, `license_url: NEED_VERIFICATION` and no provenance block, but the DB has `license_verified=1`. The registry says "waqf … no restrictive terms located", while the manifest and DB say non-commercial. That is 3 different licence statements. |
| saadi (reader panel) | No registry entry, so the footer shows "Licence: not yet recorded". The manifest says `pending_verification`. |
| baghawi (reader panel) | No `db_source_id`, so the footer shows "not yet recorded" even though `baghawi_ar` is in the registry. |
| jalalayn (reader panel, Arabic) | No manifest entry and no registry entry. |

Religious entries in the registry by licence status: cleared 28, restricted 3,
unverified 6, blocked 3, unset 8.
