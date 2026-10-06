# Phase 14: Documentation and production data seeding

## README

The README was rewritten to match the implemented system. It covers:
- architecture and the HF-only AI backend (models, fallbacks)
- every environment variable
- development startup, production startup (Docker) and database migrations
- the data seeding procedure, with a data-availability table
- web, Android and iOS builds
- tests, the live HF smoke test, secret management, limitations and cost, licensing

**Removed:**
- `docker-compose.portable.yml`: pulled third-party images built from an older revision.
- `walkthrough.md`: pre-migration notes with `ANTHROPIC_API_KEY` setup.

**Corrected in the README:**
- The old README said "Quran text is public domain". The repository's own manifest says the licence of the file in use is unverified.
- It said the admin token is stored in localStorage; it is now sessionStorage.
- It listed wrong development ports.
- It used `HF_HF_RERANKER_MODEL` (sic), which is not a real variable.

`.env.example` holds placeholders only and gained the optional settings (`HF_ZERO_SHOT_MODEL`, `HF_TIMEOUT_SECONDS`, `STT_PROVIDER`, `SURREAL_*`, `METRICS_SECRET`).

## The seeding procedure was executed, not just written

The documented commands were run against `docker-compose.prod.yml` on empty volumes, then run a second time on the same database. This dry-run found eight defects that would have broken a real deployment.

| Defect | Effect | Fix |
|---|---|---|
| `seed_quran.py` looked for its source under `assets/`, which was not mounted | Qur'an seeding failed, so stories (which need verses) failed too | `./assets:/assets:ro` mount |
| The reference data was mounted at `/app/data`, but the code resolves the repository root as `/` in the image | Story KG import could not find `stories.json` | Mount at `/data` |
| The backend reads 26 generated JSON files from `frontend/src/data/generated/`, which the image cannot contain | Asma, topics, entities, prophets and story-atlas endpoints returned 503 `data_not_built` | Read-only mount at the resolved path; all return 200 |
| `text_normalized` (text search) was filled only by an inline Makefile snippet with a hard-coded dev URL | Search over production data is unpopulated | Moved into `seed_quran.py`, which uses `DATABASE_URL` |
| `seed_concepts.py` re-runs failed with `uq_association_pair` | Seeding was not repeatable | Upsert on the natural key |
| SurrealDB ran in `memory` mode | The knowledge graph was lost on every restart | RocksDB file storage on a volume |
| KG `init_schema` dropped every statement that followed a comment header (45 of 257, including all tables and both analyzers) | A fresh KG imported 0 stories | Comment lines stripped instead (see the security commit) |
| `create_edge` used `RELATE … CONTENT` | 325 relation errors on typed edge tables | `RELATE … SET` |

The KG work also exposed a **SurrealQL injection** in public graph endpoints. It was fixed and verified in its own commit (`security(kg): …`).

**Tafsir reproducibility.** The tafsir inputs were previously a git-ignored, hand-made export. `backend/scripts/datasets/fetch_hf_tafseers.py` now rebuilds them from `riotu-lab/Quran-Tafseers` at a pinned revision, with a SHA-256 check. Its output is byte-identical to the corpus used in development (31,081 chunks). The seeder records the dataset and revision as provenance, instead of a CDN it never contacted.

## Owner decisions surfaced

These are not defects that can be fixed in code; each needs an owner decision.
- **Qur'an text licence.** The KFGQPC-derived file in use is unverified, and the manifest says it blocks public or commercial deployment. Alternatively, implement a Tanzil (CC BY 3.0) importer.
- **Al-Muyassar licence.** Pending.
- **Unavailable data sets:** English tafsir sources, KG concept tags, and the old 262 MB data bundle.
