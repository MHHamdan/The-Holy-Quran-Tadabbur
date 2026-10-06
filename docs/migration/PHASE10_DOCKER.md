# Phase 10: Production Docker

## Images

| | Backend (`backend/Dockerfile`, target `production`) | Web (`frontend/Dockerfile`, target `production`) |
|---|---|---|
| Base | `python:3.11-slim-bookworm` (`PYTHON_IMAGE` build arg) | `nginxinc/nginx-unprivileged:1.27-alpine` (`NGINX_IMAGE`) |
| Build | builder stage installs the declared dependencies non-editably into `/opt/venv`. Before: `pip install -e .` on an image with `gcc` + `libpq-dev` | `npm ci` → `vite build` → static files only |
| User | `app` (uid 10001); code owned by root, read-only to the app | `nginx` (uid 101), listens on 8080 |
| Command | `uvicorn … --workers $WORKERS --proxy-headers --forwarded-allow-ips $FORWARDED_ALLOW_IPS --no-server-header`; no `--reload` | `nginx -g 'daemon off;'` |
| Health check | Python `urllib` against `/health` (no curl in the image) | `wget /health` |
| Writable paths | `/tmp` (Tasmeeʿ audio), `/var/lib/tadabbur` (review decisions, `REVIEW_STATE_DIR`) | `/tmp` (pid and temp files) |
| Size | 580 MB (venv 268 MB, of which numpy 73 MB) | 85 MB |
| Secrets | none; all config comes from env at run time | none; `VITE_API_URL` is the only build arg and is public |

The `development` stages (with `--reload` / Vite dev server) are still there for local work. They are separate targets and are never used by the production compose file.

### Builds behind a TLS-intercepting proxy

Both Dockerfiles accept an optional BuildKit secret `extra_ca` (a CA bundle). It is mounted only for the `pip install` / `npm ci` step and never written to a layer.

```
docker build --secret id=extra_ca,src=/path/ca.crt --target production -t tadabbur-backend backend/
```

## `docker-compose.prod.yml`

- **Required secrets:** `POSTGRES_PASSWORD`, `SURREAL_PASS`, `HF_TOKEN`, `ADMIN_TOKEN`, `ADMIN_API_KEY`, `KG_ADMIN_TOKEN` and `CORS_ORIGINS` are `${VAR:?}`, so the stack refuses to start without them. None has a default.
- **Where `HF_TOKEN` goes:** it reaches only `migrate` and `backend`.
- **Migrations:** a one-shot `migrate` service runs `alembic upgrade head`. `backend` waits for `service_completed_successfully`, so the API never runs against an un-migrated schema.
- **Health-gated startup:** every service has a health check, and dependants wait for `service_healthy`.
  - SurrealDB now uses `/surreal isready`; its image has no curl, so the old check could never pass.
- **Restart:** `restart: unless-stopped` everywhere except `migrate`.
- **Hardening:**
  - `backend`, `migrate` and `web` run with `read_only: true` root filesystems and a `tmpfs` `/tmp`.
  - All services run with `no-new-privileges`.
  - CPU and memory limits are set for every long-running service, including Redis, which had none before.
  - JSON log rotation: 10 MB × 5.
- **Network exposure:** only `web` publishes a port (`WEB_PORT`, default 8080). Postgres, Redis, Qdrant, SurrealDB and the API are reachable only on the compose network. nginx reaches the API by its Docker DNS name `backend`, not by an IP or localhost.
- **Workers:** `BACKEND_WORKERS` (default 2) replaces the hard-coded `--workers 4`. No model is loaded in-process, so each worker is small: 281 MiB for 2 workers, measured.

### nginx (`frontend/nginx.conf`)

- **Unprivileged:** pid and temp paths are in `/tmp`; `server_tokens off`.
- **Security headers:**
  - `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` (microphone and geolocation `self` only), `Cross-Origin-Opener-Policy`.
  - They live in a snippet included in every location that sets its own `add_header`. nginx does not inherit `add_header` into such locations.
- **WebSocket:** the `Connection` header is now set only for real upgrade requests (via `map`). Before, it was forced to `upgrade` on every API request.
- **Uploads:** `client_max_body_size 25m` for recitation uploads.
- **Caching:** cache headers as set in Phase 9.

### Other fixes found while containerising

- `review_tasks.py` resolved its data directory to `app/app/data`, which does not exist, so review tasks never loaded. It now resolves to `app/data`. One previously skipped test now runs and passes.
- Review decisions are written to `REVIEW_STATE_DIR` (a volume) instead of the read-only code directory.
- `docker-compose.portable.yml` is labelled local-demo-only: it pulls prebuilt third-party images built from an older revision.

## Verification (G13)

- **Builds:** `docker build --target production` succeeded for **2/2** images (backend 48 s, web 66 s). They were built with `--build-arg …=mirror.gcr.io/…` because Docker Hub returned 429 to this sandbox; the defaults are the Docker Hub images.
- **Stack start:** `docker compose -f docker-compose.prod.yml up -d --wait` with throwaway random secrets and a placeholder `HF_TOKEN`:
  - **6/6** long-running services `healthy`
  - `migrate` exited 0, leaving 40 tables at alembic head `q6r7s8t9u0v1`
- **Through the web container:**
  - `/` returns 200 with the security headers.
  - `sw.js` returns `no-cache`; hashed assets return `immutable`.
  - SPA deep link `/quran/1` returns 200.
  - `/api/v1/quran/suras/1` reaches the backend: 404 "Sura 1 not found", because the database is empty until seeded.
  - WebSocket `/api/v1/tasmee/ws/1` returns **101 Switching Protocols**.
  - Backend `/ready` returns 200; `/health/detailed` returns 503 (disabled in production).
- **Restart:** sending SIGTERM to the backend's PID 1 → container restarted (`RestartCount` 1) and was healthy again.
- **Image contents:**
  - backend runs as `uid=10001`; `/app` is not writable (`touch` fails).
  - `import app.main` works.
  - web runs as `uid=101`; no `localhost:<port>`, `HF_TOKEN` or `hf_…` string in the served files.

## (b) Audit: torch, faster-whisper and model weights

| Place | torch | faster-whisper / CTranslate2 | Model weights |
|---|---|---|---|
| `backend/pyproject.toml` default dependencies | no | no (only in the opt-in `stt-local` extra) | no |
| `backend/Dockerfile` (production and development) | no | no (`.[dev]` only, never `stt-local`) | none downloaded or copied |
| Built backend image (`pip list`, 68 packages) | **0** of torch / transformers / sentence-transformers / onnxruntime / tensorflow / faster-whisper / ctranslate2 | **0** | **0** files `*.safetensors/bin/onnx/pt/gguf/ckpt` > 1 MB on the filesystem |
| `frontend/package.json` and full `npm ls` tree | no ML runtime (0 matches for onnxruntime, transformers.js, tfjs, whisper) | — | none; the only >1 MB asset is the story-graph data chunk |
| `frontend/Dockerfile` | — | — | none |
| `docker-compose.prod.yml` | — | — | no model volumes or download steps |
| `backend/serving/` (TorchServe cross-encoder: `pytorch/torchserve` base, installed `transformers` + `sentence-transformers`, packaged weights) | **yes** | — | **yes** |

`backend/serving/` was an orphan: nothing in the app referenced it, because the reranker has run on HF since Phase 4. **It is deleted on this branch.** After that, no Dockerfile or default dependency installs torch, faster-whisper or model weights.

Other files that still mention these:
- `faster-whisper`: the opt-in `FasterWhisperProvider` (lazy import, selected only by `STT_PROVIDER=faster-whisper`).
- Tests that mock it.
- Historical docs.

The root `requirements.txt` is the Streamlit demo's list (`streamlit`, `httpx`).
