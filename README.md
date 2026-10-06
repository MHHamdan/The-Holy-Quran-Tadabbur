# Tadabbur-AI

A Qur'an study platform for the web, Android and iOS. It answers questions using retrieved tafsir only, with citations that must point to that evidence. It also covers story and theme atlases, a mushaf reader and Tasmeeʿ (recitation practice).

All AI runs on **Hugging Face Inference Providers** from the backend. No GPU, local model files, Ollama or Anthropic API are needed. The HF token never leaves the server.

## Safety rules (enforced in code and tests)

1. The model may only summarise retrieved tafsir; it never invents tafsir. A refusal is the fallback.
2. Every citation must reference a retrieved `chunk_id`; citations outside the evidence are removed.
3. Qur'an quotations in AI output are verified against the stored text; unverifiable quotations are stripped.
4. Questions about rulings get an informational summary only, never fatwa language.
5. AI-generated text is labelled as such in the UI. When the AI is unavailable or out of quota, the app shows the sources verbatim, labelled.

## Architecture

```
 Web (React/Vite PWA)   Android / iOS (Capacitor shell, same React build)
            \                  /
             \  HTTPS (VITE_API_URL; same origin on the web)
              v              v
     nginx (web container: static app + /api proxy, unprivileged)
                     |
                     v
     FastAPI backend (HF_TOKEN lives ONLY here)
        |-- Hugging Face Inference Providers: chat, embeddings, reranker, zero-shot, speech-to-text
        |-- PostgreSQL  (Qur'an, tafsir chunks, stories, themes, sessions)
        |-- Qdrant      (tafsir + verse vectors, 1024-d multilingual-e5-large)
        |-- Redis       (cache, rate limiting)
        `-- SurrealDB   (story knowledge graph)
```

| Component | Hugging Face model (env var) | When HF is unavailable |
|---|---|---|
| Answer synthesis, tafsir summary/explain, quiz | `meta-llama/Llama-3.3-70B-Instruct` (`HF_LLM_MODEL`, routed by `HF_LLM_PROVIDER`) | `status: ai_unavailable`; sources shown verbatim |
| Embeddings (query + index) | `intfloat/multilingual-e5-large` (`HF_EMBEDDING_MODEL`) | keyword / database retrieval |
| Reranking | `BAAI/bge-reranker-v2-m3` (`HF_RERANKER_MODEL`) | BM25 + keyword overlap |
| Emotion classification (guidance) | `facebook/bart-large-mnli` (`HF_ZERO_SHOT_MODEL`) | keyword classifier |
| Tasmeeʿ speech-to-text | `openai/whisper-large-v3-turbo` (`HF_STT_MODEL`) | "speech recognition unavailable" notice |

Model choice, benchmarks and the evaluation of CPU embeddings: `docs/migration/` (PHASE3, PHASE4, EMBEDDING_CPU_VS_HOSTED).

## Repository layout

```
backend/            FastAPI app (app/), Alembic migrations, seed/index scripts, tests
frontend/           React + Vite app, Capacitor projects (android/, ios/), nginx config
data/               manifests, curated concepts, Qur'an text copy; data/raw/* inputs are git-ignored
assets/             hafs_smart_v8.json (Qur'an text source, see Licensing)
docker-compose.prod.yml   production stack
scripts/            dev stack (Podman) start/stop, ports.env, data-bundle tools, TS data builders
docs/migration/     per-phase engineering notes and verification evidence
```

## Configuration

Copy `.env.example` to `.env` (git-ignored) and fill it in. Everything is configured through environment variables; no secret is ever committed.

| Variable | Where | Required | Purpose |
|---|---|---|---|
| `HF_TOKEN` | backend | yes, for AI | Fine-grained HF token with "Make calls to Inference Providers". **Server only.** |
| `HF_LLM_MODEL`, `HF_LLM_PROVIDER`, `HF_EMBEDDING_MODEL`, `HF_RERANKER_MODEL`, `HF_ZERO_SHOT_MODEL`, `HF_STT_MODEL`, `HF_TIMEOUT_SECONDS` | backend | no | Model selection (defaults above), 60 s request timeout |
| `STT_PROVIDER` | backend | no | `huggingface` (default) or `faster-whisper` (opt-in, local; `pip install ".[stt-local]"`) |
| `DATABASE_URL`, `REDIS_URL`, `QDRANT_HOST`, `QDRANT_PORT`, `SURREAL_HOST/PORT/USER/PASS` | backend | yes | Datastores |
| `ENVIRONMENT` | backend | yes in prod | `production` disables `/docs`, forces `DEBUG` off, rejects wildcard CORS, logs config problems at startup |
| `CORS_ORIGINS` | backend | yes in prod | Comma-separated web origin(s) **plus** `https://localhost` (Android app) and `capacitor://localhost` (iOS app) |
| `ADMIN_TOKEN` | backend | prod | `X-Admin-Token` for RAG source administration |
| `ADMIN_API_KEY` | backend | prod | `X-Admin-API-Key` for `/api/v1/admin/*`, cost-incurring endpoints (re-indexing, cache warming) |
| `KG_ADMIN_TOKEN` | backend | prod | `X-Admin-Token` for `/api/v1/kg/init-schema` and `/import-stories`; unset means 503 |
| `METRICS_SECRET` | backend | no | Enables `/metrics`, `/health/detailed` (`X-Metrics-Secret`) in production |
| `VITE_API_URL` | frontend build | mobile: yes | **Public** API origin compiled into the bundle. Web: empty (same origin). Never a secret. |

Admin keys typed into the web UI are kept in `sessionStorage` for that tab only.

## Development

Prerequisites: Python 3.11, Node 22, and Podman (the dev stack script) or Docker.

```bash
cp .env.example .env                      # set HF_TOKEN for AI features
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e "./backend[dev]"
(cd frontend && npm ci)

make start            # Podman: Postgres, Qdrant, Redis, SurrealDB + backend + frontend (ports in scripts/ports.env)
make migrate          # alembic upgrade head
make seed             # reference data (see "Data seeding")
```

- **Frontend:** `http://localhost:19300`. The Vite dev server proxies `/api` to the backend.
- **Backend:** `http://localhost:19800`. API docs are at `/docs` in development only.
- **Run the pieces yourself:** `make dev-backend` (`uvicorn --reload`) and `make dev-frontend`.
- **Without Podman:** point `DATABASE_URL`, `REDIS_URL`, `QDRANT_*` and `SURREAL_*` at any running instances.

## Production deployment (Docker)

```bash
cp .env.example .env    # set POSTGRES_PASSWORD, SURREAL_PASS, HF_TOKEN, ADMIN_TOKEN,
                        # ADMIN_API_KEY, KG_ADMIN_TOKEN, CORS_ORIGINS (all strong, unique)
docker compose -f docker-compose.prod.yml up -d --build
```

- **Startup order:** `migrate` runs `alembic upgrade head` once; `backend` starts only after it succeeds. All services have health checks and `restart: unless-stopped`.
- **Exposure:** only the `web` container publishes a port (`WEB_PORT`, default 8080). Put a TLS-terminating reverse proxy or load balancer in front of it; the mobile apps require HTTPS.
- **Images:**
  - Backend: non-root uid 10001, read-only root filesystem, no compiler, no torch, no model weights.
  - Web: `nginx-unprivileged` with security headers.
  - Both images: `no-new-privileges`, CPU and memory limits, rotated JSON logs.
- **Mounts:** `data/`, `assets/` and `frontend/src/data/generated/` are mounted read-only into the backend (reference data the API reads).
- **Behind a TLS-intercepting proxy:** builds take an optional `extra_ca` BuildKit secret (`--secret id=extra_ca,src=ca.crt`); it is never stored in a layer.
- **Details and verification:** `docs/migration/PHASE10_DOCKER.md`.

### Database migrations

`alembic upgrade head` (from `backend/`, or the `migrate` service). There is a single head; CI checks upgrade, then downgrade -1, then upgrade on a fresh Postgres.

## Data seeding (production)

The commands below were run against `docker-compose.prod.yml` on an empty stack. Every step was then **re-run on the same database to confirm it is idempotent**. Run them in order after the stack is up:

```bash
DC="docker compose -f docker-compose.prod.yml"
RUN="$DC run --rm --no-deps backend"

# 1. Qur'an text (6,236 verses + search normalisation)          -- from assets/hafs_smart_v8.json
$RUN python scripts/ingest/seed_quran.py

# 2. Tafsir: fetch 5 Arabic works from the HF dataset riotu-lab/Quran-Tafseers (Apache-2.0,
#    pinned revision, SHA-256 checked) into data/raw/, then seed them (31,081 chunks).
#    Run the fetch on the host checkout (it writes data/raw/; needs huggingface.co access):
python backend/scripts/datasets/fetch_hf_tafseers.py            # add --exclude muyassar_ar, see Licensing
$RUN python scripts/ingest/seed_tafseer.py ibn_kathir_ar tabari_ar qurtubi_ar baghawi_ar muyassar_ar

# 3. Stories, story atlas and graphs, concepts, themes, rhetorical devices (committed data)
for s in seed_stories seed_story_atlas seed_story_graphs seed_concepts seed_themes seed_rhetorical_devices; do
  $RUN python scripts/ingest/$s.py
done

# 4. Knowledge graph (SurrealDB, persistent volume)
curl -X POST -H "X-Admin-Token: $KG_ADMIN_TOKEN" https://<host>/api/v1/kg/init-schema
curl -X POST -H "X-Admin-Token: $KG_ADMIN_TOKEN" https://<host>/api/v1/kg/import-stories

# 5. Vector indexes (Hugging Face embeddings; costs HF credit; resumable)
$RUN python scripts/index/index_tafseer.py                       # tafsir chunks -> Qdrant
curl -X POST -H "X-Admin-API-Key: $ADMIN_API_KEY" https://<host>/api/v1/quran/search/semantic/index   # verse index

# 6. Mushaf word layout (needs api.qurancdn.com)
$RUN python scripts/ingest/seed_mushaf_words.py
```

Results of steps 1–4 on the production stack:

| Data set | Count |
|---|---|
| verses | 6,236 (all normalised) |
| tafsir chunks | 31,081 from 5 sources |
| stories | 124 |
| concepts | 60 |
| concept associations | 126 |
| themes | 50 |
| knowledge graph | 124 stories, 325 events, 104 persons, 1,164 edges, 0 errors |

The step-1–4 data then served `/quran/*`, `/tafseer/compare/*`, `/rag/ask` (8 citations), `/kg/*` and the atlas endpoints with HTTP 200.

### Data availability

| Data | Status |
|---|---|
| Qur'an text (Hafs, Uthmani) | **Available, licence unverified.** The primary source `assets/hafs_smart_v8.json` is derived from KFGQPC output, and its redistribution terms are unconfirmed (see `data/manifests/quran_hafs.json`). The licence-verified alternative (Tanzil, CC BY 3.0) is listed in the manifest but has no importer yet. |
| Arabic tafsir: Ibn Kathir, al-Tabari, al-Qurtubi, al-Baghawi | Available (HF dataset above; classical, public domain). |
| Al-Tafsir al-Muyassar | Available technically. **Licence pending** (King Fahd Complex, "educational and non-commercial"; manifest status `pending_user_input`). |
| English tafsir (Ibn Kathir EN, al-Jalalayn, Tafheem, al-Saʿdi EN) | **Not available.** The CDN/API downloaders exist (`make download-tafseer`) but were not verified. Several of these are marked pending licence verification. |
| Tafsir and verse vector indexes | Reproducible with HF credit (step 5). Not rebuilt here: the account's HF credits are exhausted. Without them, retrieval falls back to keyword search. |
| Mushaf word layout, QAC vocabulary (`seed_mushaf_words.py`, `scripts/seed_vocabulary_complete.py`) | Depend on `api.qurancdn.com`. **Not verified**: the host was unreachable from the build environment. |
| Knowledge-graph concept tags | **Not available:** no importer exists (the earlier data bundle contained 60). Thematic graph endpoints return empty results until one is written. |
| Generated atlas/graph JSON (26 files) | Available (committed under `frontend/src/data/generated/`). |
| Earlier full data bundle (`data/BUNDLE.lock`, 262 MB) | **Not available:** no release asset is published. |

## Web build

```bash
cd frontend && npm ci && npm run build     # dist/: PWA (service worker, offline Qur'an/tafsir cache)
```

`VITE_API_URL` empty means the app calls `/api` on its own origin (nginx proxies it). A loopback `VITE_API_URL` fails the build.

## Android and iOS (Capacitor)

The apps ship the same React build inside the app package. They have no remote code, no service worker, and talk to the API over HTTPS. App ID `com.mhamdan.tadabbur`, name "Tadabbur".

**The production API URL is not decided yet.** Copy `frontend/mobile.env.example` to `frontend/.env.mobile` and set `VITE_API_URL`. `npm run build:mobile` refuses to build if the URL is unset, still the placeholder, not `https://`, or a loopback address.

```bash
cd frontend
# Android debug APK against a development backend (emulator reaches the host at 10.0.2.2):
export ANDROID_HOME=/path/to/android-sdk          # platform 36, build-tools 36, JDK 21
VITE_API_URL=http://10.0.2.2:8000 npm run android:debug   # -> android/app/build/outputs/apk/debug/app-debug.apk

# Android release (needs the owner's upload keystore, not in the repository):
npm run android:release                            # bundleRelease (sign with your keystore)

# iOS (macOS + Xcode 16 required):
npm run ios:sync && npx cap open ios               # set signing team, archive, upload
```

- **Permissions:** only the microphone, for Tasmeeʿ, requested when recording starts.
- **Network security:** release builds allow HTTPS only. Debug builds allow cleartext only to `10.0.2.2` and `localhost`. iOS keeps App Transport Security defaults.
- **Details:** `docs/migration/PHASE8_MOBILE.md`.

## Tests

| Command | Scope |
|---|---|
| `cd backend && pytest -m "not live_hf"` | All backend tests. They never call Hugging Face (the token is cleared per test). Tests needing externally ingested data declare `@pytest.mark.requires_data(...)` and skip when it is absent; set `REQUIRE_DATA_BUNDLE=1` to make that a failure. |
| `cd frontend && npm run typecheck && npm run lint && npm run build` | Frontend gates |
| `node frontend/e2e/tasmee-microphone.e2e.cjs` | Microphone behaviour (needs a served build and a running backend) |
| CI (`.github/workflows/ci.yml`) | On every push/PR, with no secrets: backend (lint, mypy on the HF layer, migrations, seeded tests), frontend, mobile (APK + iOS sync + API-URL guard), production image builds, gitleaks, pip-audit, npm audit |

### Live Hugging Face smoke test

```bash
cd backend && HF_TOKEN=... pytest -m live_hf tests/live -v
```

These tests spend a little HF credit. They cover chat (Arabic and English), embeddings, reranking, zero-shot classification, speech-to-text on a recitation fixture, and grounded RAG with citation checks. With exhausted credits (HTTP 402/429) they skip with that reason.

## Secret management

- `HF_TOKEN` and all admin credentials exist only in the backend environment. They are held as `SecretStr` and never logged or returned in errors.
- Nothing secret goes into `VITE_*`, the JS bundle, Capacitor config, Android resources or iOS plists. `tests/unit/test_secret_hygiene.py` enforces this, including for the native projects.
- `.env` files are git-ignored. CI scans the full history with gitleaks.
- Rotate a leaked HF token at huggingface.co → Settings → Access Tokens, then update the server environment.

## Limitations and cost

- **HF costs:** every AI answer, embedding, rerank and transcription is billed to the HF account's Inference Providers credits.
  - When credits run out (HTTP 402), the app degrades as described in the Architecture table.
  - Hosted embedding latency was about 0.2 s warm; a CPU ONNX option is evaluated in `docs/migration/EMBEDDING_CPU_VS_HOSTED.md`.
- **External runtime APIs:**
  - Some optional features call external APIs at runtime: asbab al-nuzul and external tafsir editions (`FEATURE_EXTERNAL_TAFSEER`).
  - They return a clean 503 when those hosts are unreachable.
- **Licensing:** content licensing must be resolved before a public or commercial release (see Data availability).

## Licensing

Code: see repository licence. Content licences are tracked per source in `data/manifests/`. The Qur'an text currently used (`assets/hafs_smart_v8.json`) and Al-Muyassar **have unverified redistribution licences**; the manifest marks the Qur'an file as blocking public or commercial deployment until KFGQPC confirms the terms in writing.
