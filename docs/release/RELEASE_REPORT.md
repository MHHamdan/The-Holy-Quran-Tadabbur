# Tadabbur v1 release report

Branch `release/v1-completion-swarm`. Evidence comes from three independent release audits and five implementation rounds, each with an adversarial review. After the last round, an independent read-only verifier checked the work and I fixed what it found. Every number below was re-measured at HEAD. Builder claims were not taken on trust.

## Classification: **RELEASE CANDIDATE**

**Not STORE READY.** Production hosting, the store assets, the real privacy URL and live Hugging Face verification are still owner actions. Signing is not the only gap.

**Not PRODUCTION READY.** No production infrastructure exists, and HF has not been verified live.

There is no open non-owner P0 or P1.

---

## 1–2. Commits

| | SHA |
|---|---|
| Start (main after PR #39) | `7acd5a5` |
| Final | `ef50f51` + this report |
| Range | 245 commits, 671 files changed |
| Last CI-verified commit | `c83563b` (the rest are docs-only) |

## 3. Architecture

**Backend:** FastAPI (`backend/app`) with:
- Postgres for Qur'an, translations, tafsir, stories, KG tables and user data;
- Qdrant for tafsir and verse vectors;
- Redis for cache and rate limiting;
- optional SurrealDB for the knowledge graph.

**Hosted AI:** all AI runs on Hugging Face Inference Providers: chat, `multilingual-e5-large` embeddings, rerank, zero-shot and STT.
- The token is server-only, a `SecretStr`.
- Ollama, Anthropic, local GPU and other local-inference paths: 0 runtime hits.

**RAG answers:**
- The flow is retrieval, then generation, then the citation validator, then the deterministic answer guard (`backend/app/safety/`), then the response.
- Answers are refused or reduced to a verbatim "source digest" when the evidence is missing.

**Frontend:**
- React, Vite and Tailwind, with i18n for ar and en and correct RTL.
- PWA via Workbox.
- Capacitor 8 Android and iOS shells built from the same bundle.

**Deployment:**
- `docker-compose.prod.yml`: non-root backend, unprivileged nginx web container, migrate-then-start.
- `release-images.yml` pushes GHCR images on `v*` tags.

**Migrations:** 38 alembic revisions with a single head, `r5c1a2b3c4d5`. CI round-trips them on a fresh DB.

## 4. Features (web, Android, iOS)

- **Reader:** list and Mushaf views (604 pages), Uthmani and simple script, verse actions, bookmarks, reading plan.
- **Translations:** 22 translations of the meanings (QuranEnc), with footnotes.
- **Audio:** 6 reciters, gapless playback, offline handling.
- **Offline:** the full Qur'an offline (114 surahs precached, sha256 manifest).
- **Tafsir:** reader (default al-Baghawi) and side-by-side comparison of 4 classical sources.
- **Ask (RAG):** cited answers, refusal or source digest when unsupported, bilingual.
- **Stories:** stories (124), story atlas (8 clusters), prophets, themes (labelled as a study aid), concepts (explanations withheld when unevidenced), Surah atlas.
- **Duas and adhkar:** 66 Qur'anic duas, verbatim and cited.
- **Tasmee:** recitation check via STT; degrades when STT is unavailable.
- **Learning tools:** memorisation, quiz, flashcards, daily challenge, roots, names of Allah.
- **Tools:** prayer times, qibla, calendar.
- **Search:** lexical, plus semantic when HF is available.
- **Privacy:** privacy page and in-app "Delete my data".

## 5. Content inventory

| Data | Count |
|---|---|
| Qur'an | 114 surahs, 6236 ayat, 112 bismillah, 15 sajda, 30 juz, 604 pages, 60 hizb, 240 rub |
| Translations | 22 editions × 6236 verses |
| Tafsir passages (servable) | baghawi 6235, tabari 6233, ibn_kathir_ar 6204, qurtubi 6174 |
| Tafsir held (not served) | muyassar 6236 (licence hold), ibn_kathir_en and jalalayn_en (disabled) |
| Stories | 124 stories, 322 segments, 1283 ayat (20.6%); 62 story-atlas events |
| Themes / concepts | 50 themes / 60 concepts |
| Duas and adhkar | 161 entries (94 Qur'anic, all exact) |
| Audio | 6 reciters × 6236 URLs |
| UI strings | 926 keys at ar/en parity |

## 6. Qur'an integrity: PASS (RG-01, RG-02)

- **Text layers:** 6236/6236 verses are byte-equal to Tanzil in all four layers: JSON, DB, API and offline bundle.
- **Excerpts:** 337/337 embedded excerpts are verbatim.
- **Offline files:** 114/114 sha256 match.
- **Negative controls:** corrupting 2:255 or 114:6 is detected in every layer.
- **Validator:** `npx tsx scripts/validate-quran-integrity.ts` gives 21 passed, 0 failed.
- **Text edits:** no canonical text was changed in this release.
- **Mushaf deviation:** one documented deviation from Tanzil: the rub boundary 15:50 → 15:49 follows the Madinah Mushaf.

## 7. Translation coverage

- 22/22 editions at 100%.
- Text and footnotes are verbatim against the QuranEnc cache (22 × 6236).
- Version and attribution are shown on every verse.

## 8. Tafsir coverage

**Passage coverage:** tabari 99.95%, baghawi 99.98%, ibn_kathir_ar 99.49%, qurtubi 99.01%.

**Provenance:** all four are identical, ignoring whitespace, to the pinned Apache-2.0 dataset `riotu-lab/Quran-Tafseers@9ddbdeec`.

**Al-Muyassar is on licence hold** (`license_verified=0`):
- No endpoint serves its text. `edition=muyassar` returns 403.
- RAG never cites it.
- It is not a default anywhere.

**Vector index** (what semantic retrieval can reach):

| Source | Indexed |
|---|---|
| tabari | 51.6% |
| qurtubi | 50.5% |
| ibn_kathir_ar | 9.0% |
| baghawi | 0% |

The index has 0 orphan and 0 placeholder points. Postgres verse-reference and ranked keyword retrieval cover all four sources until the index is rebuilt with HF credit.

## 9. Stories, themes and concepts

**Stories:** 319/322 segments carry evidence; 2195/2195 evidence ids resolve to enabled sources. All 62/62 story-atlas events cite `ibn_kathir_ar` and resolve.

**Themes:** 6/50 have segments (17 ayat). They are shown as an analytical study aid.

**Concepts:** 0 of 126 relationships have sufficient evidence, so those explanations are withheld rather than generated. Citation coverage is 2.79%.

**Unevidenced connections:** 54 event connections and 4 theme connections (P3).

## 10. Dua coverage

| Set | Result |
|---|---|
| Qur'anic duas | 66/66 cited and exact (12 full verses, 54 word-aligned excerpts) |
| Backend copy vs frontend | 0 mismatches |
| Qur'anic adhkar | 21/21 exact |
| Non-Qur'anic adhkar | 52/52 carry a sourceRef; 51/52 name a collection and number |
| Unstructured hadith duas | 15, hidden (not shown without a verifiable reference) |
| Dua explanations | al-Baghawi and Ibn Kathir |

## 11. RAG and citation results

**Answer guard** (deterministic; `prompts.py` untouched):

| Set | Result |
|---|---|
| Frozen round-5 held-out | EN legit 49/50 accepted + 1 digest, 0 withheld; AR the same; malicious 43/43 neutralised |
| Audit harnesses h1–h6 | malicious 211/211 neutralised; legit h1 45/45, h2 27/29, h3 39/39, h4 8/8, h5 50/50, h6 EN 11/12 and AR 6/8 |
| Independent verifier set (real al-Baghawi and al-Tabari chunks) | EN 5/5, AR 5/5, malicious 10/10 |
| Ordinary questions falsely pre-blocked | 0/90 |
| Personal-fiqh questions pre-blocked | 8/8 |
| Planted instructions reaching the prompt | 0/5 |

All but one h2/h6 residual withhold are fail-closed by design (an inferred number, a "لا يجوز" ruling, a hadith-report paraphrase); `ar-2:184` is a borderline ruling question pre-blocked at intake.

**Retrieval:**
- Every vector hit is resolved to its DB row.
- Only enabled, licence-verified sources are served.
- Short verse references ("Explain 2:255", "39:53", "اشرح ٢:٢٥٥") go to the verse path.

**Test suites:** 1302 guard and RAG tests pass.

## 12. Hugging Face status: NOT VERIFIABLE (RG-06)

- The owner's HF credits are exhausted. Only degraded mode was exercised.
- Degraded mode returns bilingual `ai_unavailable` states, 0 tracebacks, and source digests in place of synthesis.
- `pytest -m live_hf` has not run.
- The token never reaches clients: 0 hits in the web and mobile bundles, including `.gz` files.

## 13. Frontend

| Check | Result |
|---|---|
| tsc | 0 errors |
| eslint (`--max-warnings 0`) | 0 |
| vitest | 125/125 (23 files) |
| Production build | OK, 0 source maps |

- **Layout:** 168 journey steps OK and 0 overflow across 76 route, viewport and language combinations.
- **Tap targets:** primary controls 44 px, inline links at least 24 px.
- **Secrets:** the build refuses secret-looking `VITE_*` names.

## 14. Android

- CI builds the debug APK (9.6 MB) and the release AAB (7.6 MB, versionCode from CI, bundletool checks).
- No cleartext traffic and no `server.url` in release builds.
- Network exceptions are debug-only.
- No signing material is in the repo.
- **The AAB is UNSIGNED** until the owner adds the upload-key secrets.

## 15. iOS

- Xcode 26.3 unsigned device build: `BUILD SUCCEEDED`, 0 warnings.
- CI checks the privacy manifest, Arabic strings and permission keys.
- Archive and App Store Connect upload are gated on the owner's Apple secrets.
- Not tested on a physical device; there is no evidence of device-only behaviour.

## 16. PWA: PASS

- 0 installability errors.
- 231 precache entries, duplicates removed.
- The service worker caches no AI, user or cross-origin responses.
- A never-opened surah renders offline in ar and en.

## 17. Security: PASS (RG-15, RG-29)

| Check | Result |
|---|---|
| gitleaks | 0 leaks (437+ commits) |
| pip-audit / npm audit | 0 / 0 |
| Working PoCs found by the red team | 0 |
| Admin endpoints | fail closed (6/6) |
| SQL | parameterised, including the new f-string sites |

- **Fixed:** the therapy IDOR and legacy NULL-hash delete.
- **Fixed:** public `/quran/*` tafsir endpoints redistributed unlicensed text; they are now gated, with a test.

## 18. Privacy: PASS (RG-25, RG-26)

**Search history:** no longer recorded. `/privacy` (en and ar), `docs/store/data-safety.md` and `PrivacyInfo.xcprivacy` match the code.

**End-to-end "Delete my data":**
- All 6/6 server copies are removed.
- Deletion completes after an outage or while offline, once reconnected.
- Local storage, caches and IndexedDB are cleared.

**Retention:**
- Therapy 180 days, Tasmee 90 days, dhikr 30 days.
- 0 rows past retention.
- The Tasmee key cap was removed.

## 19. Licensing

| Content | Status |
|---|---|
| Qur'an text | Tanzil, CC BY 3.0; in-content tanzil.net credit on 16/16 surfaces in both languages |
| Translations | QuranEnc republication terms |
| al-Baghawi, al-Tabari, al-Qurtubi, Ibn Kathir | Classical public domain, digital text Apache-2.0 |
| al-Muyassar | Licence hold (owner) |
| English Ibn Kathir, Jalalayn | Blocked |
| Audio hosts | Licences are an owner item |

**Owner decision:** the KFGQPC text files (`assets/hafs_smart_v8.json`, `data/raw/quran_uthmani.json`) are still in the public repo.

## 20. Accessibility: PARTIAL → mostly fixed (RG-20)

- 44 px targets: reader nav and toggles, verse actions, Mushaf nav and toolbar, surah index, stories.
- Stories sub-filter chips are 26 px tall, which meets the 24 px AA minimum.
- `role=alert` permission messages.
- The Mushaf "/ 604" total keeps Latin digits on purpose, to match its numeric input.

## 21. Performance

- Web build: 31.5 s, 14 MB.
- Keyword fallback: 3.27 s → 0.02 s (bare-column trigram matching).
- Degraded `/ask`: about 60 ms.
- Lazy chunks and the PWA 2 MiB chunk limit are respected.

## 22. Tests (exact)

| Suite | Passed | Skipped | Deselected | Failed |
|---|---|---|---|---|
| Backend, local dev DB (`-m "not live_hf"`) | **4097** | 20 | 11 | **0** |
| Backend, CI fresh DB (run 38871171743, `c83563b`) | **4015** | 158 | 11 | **0** |
| Frontend vitest | **125** (23 files) | 0 | — | **0** |
| Data validators `scripts/validate-*.ts` | **35/35** | — | — | **0** |
| Qur'an integrity validator | **21** | — | — | **0** |

CI on `c83563b`: Backend, Frontend, Mobile, Security and Production images all succeeded, and Mobile release succeeded.

## 23. Failed and skipped tests

**Failed:** none.

**Skipped locally (20):**
- 6: `test_audio_range` network checks (`RUN_NETWORK_TESTS=1`).
- 5: `test_quran_resolve` needs a running server fixture.
- 2: `test_theme_quality_distribution` (integration-only).
- 1: `httpx2` absent.
- 1: maintenance endpoint (`DEBUG=true`).
- 1: tafsir corpus not fully loaded (vector-ranking test).
- 1: no placeholder rows left (already migrated).
- 1: QuranEnc tafsir cache absent.
- 1: `test_tafseer_llm_cache_key` (al-Muyassar not seeded as servable).
- 1: `requires_data tafsir:1:1`. The dataset has no 1:1 passage for the servable sources.

**Skipped in CI (158):**
- The same environmental skips.
- `@pytest.mark.requires_data` tests: the CI DB is seeded with reference data only, so the ingested corpora (tafsir, vocabulary, translations, verse vectors) are absent.
- These tests run against the dev DB, where they pass.

No test was disabled or loosened to reach green. Tests changed this release assert the corrected behaviour, with the reason in each commit.

## 24. Store readiness: NOT READY (RG-27 FAIL, owner)

**Ready:**
- Metadata within limits (en and ar).
- Data-safety and content-rating answers.
- Privacy manifest.
- A release guard that refuses a `v*` tag without `PRODUCTION_API_URL`, `PRIVACY_CONTACT` and the signing secrets, or with `REPLACE_WITH` placeholders.

**Missing:**
- Screenshots (`scripts/store/screenshots.py` exists).
- Play feature graphic.
- Review notes.
- Support URL.
- Release notes.
- The real `privacy_url`.

## 25. Owner-only actions (in order)

1. Host the backend over HTTPS (`docker-compose.prod.yml` behind TLS), and configure proxy headers for the rate limiter.
2. Set the repository variables `PRODUCTION_API_URL`, `PRIVACY_CONTACT` and `PUBLIC_WEB_URL`.
3. Add CORS for the domain, `https://localhost` and `capacitor://localhost`.
4. Add HF credit, then:
   - run `pytest -m live_hf tests/live`;
   - re-index tafsir (`python scripts/index/index_tafseer.py`);
   - run a funded red-team pass.
5. Add the Play upload-key secrets (`ANDROID_UPLOAD_*`).
6. Add the Apple Developer and App Store Connect secrets (`APPLE_TEAM_ID`, `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`).
7. Complete the store assets (§24), and set `fastlane/metadata/ios/*/privacy_url.txt` to the real host.
8. **Licences:**
   - confirm the al-Muyassar KFGQPC terms, or switch to QuranEnc `arabic_moyassar`;
   - decide whether to remove the KFGQPC files from the repo and history;
   - confirm the audio-host licences.
9. Work through `data/review/owner_review_queue.json` (19 items: hadith review, chronology, memorisation pairs, the 2:251 summary wording, …).
10. Decide on `ACCESS_FINE_LOCATION`.
11. Test background audio, the mic and location prompts, and reminders on physical devices.

## 26. Remaining problems

**P0:** none.

**P1 (owner):**
- The KFGQPC text is in the public repo.
- The al-Muyassar licence decision.
- Unsigned builds against the placeholder API URL.

**P2 (owner):**
- Store package (§24).
- Live HF unverified, and the vector index is partial (al-Baghawi has 0 vectors).

**P3:**
- Guard residuals, all fail-closed by design (§11).
- The frozen held-out fixture cites al-Muyassar chunks. They still test the guard logic, but no longer match what is served.
- `services/semantic_search.semantic_vector_search` serves payload text directly. It has 0 callers; delete it or gate it.
- There is no production check for per-source index coverage.
- `madhab_validator.APPROVED_SOURCES` still lists the blocked sources. This is latent: the evidence SQL now gates them.
- `confidence_level` is not derived from `confidence` in `GroundedResponse`.
- 54 event connections and 4 theme connections are unevidenced.
- Concept citation coverage is 2.79%.
- Play keywords in Arabic are at 137 bytes.

## 27. Deployment commands

```bash
cp .env.example .env   # strong unique POSTGRES_PASSWORD, SURREAL_PASS, HF_TOKEN, ADMIN_TOKEN,
                       # ADMIN_API_KEY, KG_ADMIN_TOKEN, CORS_ORIGINS
docker compose -f docker-compose.prod.yml up -d --build      # migrate runs alembic upgrade head first
# or, from released images:
export TAG=v1.0.0
docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d
# data: see README "Data seeding (production)"; then (HF credit) re-index:
$RUN python scripts/index/index_tafseer.py
curl -X POST -H "X-Admin-API-Key: $ADMIN_API_KEY" https://<host>/api/v1/quran/search/semantic/index
# rollback: pg_dump first, set TAG to the previous release, pull + up -d
```

## 28. Android release procedure

1. Create the upload key with `keytool` (see `frontend/android/keystore.properties.example`).
2. Add the secrets `ANDROID_UPLOAD_KEYSTORE_BASE64`, `ANDROID_UPLOAD_STORE_PASSWORD`, `ANDROID_UPLOAD_KEY_ALIAS` and `ANDROID_UPLOAD_KEY_PASSWORD`.
3. Set `PRODUCTION_API_URL` (https) and `PRIVACY_CONTACT`.
4. Replace the `REPLACE_WITH` placeholders in `fastlane/metadata`.
5. Merge to main and push a `v1.0.0` tag. `mobile-release.yml` builds the signed AAB, using `scripts/store/release_version.sh` for versionCode and versionName, and verifies it with bundletool.
6. Download the AAB artifact and upload it manually to Play Console, internal testing first. Fill in data safety from `docs/store/data-safety.md` and content rating from `docs/store/content-rating.md`. Nothing is auto-published.

## 29. iOS release procedure

1. Enrol in the Apple Developer Program.
2. Create the App ID `com.mhamdan.tadabbur` and the App Store Connect app record.
3. Create an ASC API key (App Manager), and add the secrets `APPLE_TEAM_ID`, `ASC_KEY_ID`, `ASC_ISSUER_ID` and `ASC_KEY_P8_BASE64`.
4. Push the `v*` tag. The `ios-upload` job archives and signs the app (`frontend/ios/ExportOptions.plist`) and uploads it to TestFlight.
5. In App Store Connect, set the privacy labels per `PrivacyInfo.xcprivacy` and `docs/store/data-safety.md`, the privacy URL `https://<web domain>/privacy`, and category Books or Education (free, no ads, no purchases).
6. Test on a device via TestFlight, then submit for review manually.
