# MISSION — Tadabbur-AI: Hugging Face-only, production-ready, Web + Android + iOS

Repository: https://github.com/MHHamdan/The-Holy-Quran-Tadabbur
Working branch: `feat/huggingface-mobile-production` (never commit directly to `main`; never merge automatically)

You are the principal engineer responsible for completing this repository.

## Mission

Turn the existing Tadabbur-AI repository into a self-contained, production-deployable application that does NOT depend on the owner's workstation, Ollama, a local GPU, or any locally hosted LLM.

Hugging Face must become the ONLY AI/model platform.

The final application must be deployable as:

1. Web application
2. Android application
3. iOS application

sharing as much of the existing React/Vite codebase as reasonably possible.

Do not merely prepare a migration plan. Inspect, implement, test, repair and verify.

## Cloud session environment notes

- Hugging Face authentication is injected by a network proxy for `huggingface.co` and `*.huggingface.co`. The `HF_TOKEN` environment variable in this VM is a placeholder; the real token is never visible. Code must still read `HF_TOKEN` from the environment so it works in real deployments.
- NEVER print, log, echo, or write any token value.
- PostgreSQL 16, Redis 7, and Docker are available on the VM but not running by default. Start them as needed (`service postgresql start`, `service redis-server start`, `docker compose up`).
- The VM is Ubuntu 24.04 x86_64 (about 4 vCPU, 16 GB RAM). There is no GPU and no macOS/Xcode.
- The Android SDK is not pre-installed; install it when needed (`dl.google.com` is reachable).

## Non-negotiable target architecture

```
Mobile/Web client (React/Vite + Capacitor)
        |
        | HTTPS
        v
FastAPI backend  (HF_TOKEN stored SERVER SIDE only)
        |
        +--> Hugging Face Inference Providers
        +--> PostgreSQL
        +--> Qdrant
        +--> Redis
```

The Hugging Face token MUST remain on the server. NEVER embed `HF_TOKEN` or any privileged backend secret in:

- Vite environment variables exposed to the browser (never use a `VITE_*` variable for it)
- JavaScript bundles
- Capacitor configuration
- Android resources or Gradle configuration shipped with the app
- iOS Info.plist or native source code
- frontend localStorage
- committed files

The Android/iOS applications must talk to the backend API over HTTPS.

---

## Phase 0 — Repository forensics

Before changing the architecture:

1. Read the complete repository structure.
2. Read README.md and IMPROVEMENT_ROADMAP.md.
3. Inspect the Makefile, all docker-compose files, `.env.example`, and `.gitignore`.
4. Inspect the backend dependency configuration (pyproject.toml or equivalent) and `frontend/package.json`.
5. Inspect all GitHub Actions workflows.
6. Inspect `backend/app/core/config.py` and `backend/app/rag/llm_provider.py`.
7. Trace every invocation of: Ollama, Claude/Anthropic, Hugging Face, transformers, sentence-transformers, embedding models, rerankers, STT models, NLP models.
8. Search the ENTIRE repository case-insensitively for: `ollama`, `localhost:11434`, `qwen2.5`, `anthropic`, `claude`, `nvidia-smi`, GPU-specific model switching, local model assumptions, and subprocess GPU detection.

Do not trust the README as proof of implementation. Code and executable tests are authoritative.

## Phase 1 — Remove Ollama completely

Remove (not merely disable):

- OllamaLLM and the Ollama provider enum/configuration
- `OLLAMA_MODEL`, `OLLAMA_MODEL_FAST`, `OLLAMA_MODEL_CPU_FALLBACK`, `OLLAMA_BASE_URL`
- Ollama-specific max-token settings and `localhost:11434` assumptions
- Ollama health checks and `test_ollama_connection`
- `nvidia-smi` detection used for LLM routing and GPU-vs-CPU model selection
- Docker configuration, Makefile commands, tests, and README instructions that exist only for Ollama

After migration this must return no live application/configuration dependency:

```bash
grep -RniE 'ollama|localhost:11434' --exclude-dir=.git --exclude-dir=node_modules .
```

Historical documentation may mention Ollama only if explicitly marked as historical.

## Phase 2 — Remove Anthropic as a runtime dependency

Hugging Face is the ONLY LLM/model platform. Remove the production dependency on `ANTHROPIC_API_KEY`, the Anthropic SDK, ClaudeLLM, Claude-specific model configuration, and Claude provider selection.

Keep a provider abstraction only if it has real architectural value. The default and production path must be Hugging Face.

## Phase 3 — Implement Hugging Face inference

Use the CURRENT official Hugging Face Inference Providers API, preferably through the official Python `huggingface_hub` client.

Canonical secret: `HF_TOKEN` (optionally also accept `HUGGINGFACE_TOKEN` for compatibility, but document only one).

Configuration:

```
HF_TOKEN=
HF_LLM_MODEL=
HF_LLM_PROVIDER=auto
HF_EMBEDDING_MODEL=
HF_RERANKER_MODEL=
HF_STT_MODEL=
```

Never hard-code a token.

For chat/LLM generation:

- use HF Inference Providers
- preserve system/user message separation, temperature, and max tokens
- return model/provider information and token usage when available
- implement timeout handling
- map upstream failures to controlled backend errors
- never leak HF response internals or token values

Model selection — do NOT just replace `qwen2.5:32b` with Qwen on HF. Benchmark a SMALL set of candidates against real Tadabbur prompts and choose based on:

1. Arabic capability
2. English capability
3. instruction following
4. ability to obey strict RAG citation requirements
5. latency
6. availability through HF Inference Providers
7. cost / free-tier practicality (consider the `:cheapest` routing policy)
8. license compatibility

Model IDs MUST remain environment-configurable. Use HF provider routing rather than tying the app to one underlying vendor. Handle exhausted HF quota/credits gracefully.

## Phase 4 — Audit all AI/ML components

LLM generation is only part of the migration. Determine whether each of these runs locally: embeddings, semantic search encoding, reranking, query expansion, NLP/grammar analysis, emotion classification, speech-to-text, AI verification, agents, theme extraction, concept extraction, story analysis, and any transformers pipeline.

Objective: THE DEPLOYED BACKEND MUST NOT REQUIRE A LOCAL GPU.

For each component choose:

- A. Hugging Face hosted inference
- B. a lightweight CPU implementation suitable for the server
- C. a deterministic non-ML implementation

Do NOT turn every small NLP operation into a remote LLM request. No feature may depend on a GPU or on model files that exist only on the owner's computer. Document and justify every remaining local CPU model.

## Phase 5 — Preserve the Quranic safety architecture

Correctness and provenance take priority over creative AI behavior. Preserve and strengthen:

1. The model must NEVER fabricate Qur'anic text.
2. The model must NEVER invent tafseer.
3. Qur'an text must come only from verified, stored canonical data.
4. Tafseer content must come only from approved retrieved sources.
5. AI-generated synthesis must be visibly and structurally distinct from Qur'an, translation, tafseer, and scholarly quotations.
6. RAG answers must cite actual retrieved chunk IDs.
7. Citations not present in the retrieved evidence must be rejected.
8. Insufficient evidence must produce the existing safe fallback, not invented content.
9. Fiqh responses must not be presented as personalized fatwas.
10. Prompt-injected source text must never override application safety instructions.

Add regression tests for these properties.

## Phase 6 — Verify and repair the complete backend

Run the application and repair genuine defects. Verify: FastAPI startup, configuration validation, database connection, migrations, PostgreSQL schemas, Redis, Qdrant, SurrealDB (only if still genuinely required), data ingestion, Quran data integrity, tafseer ingestion, vector indexing, RAG retrieval, the citation validator, story graph, concept graph, thematic analysis, verification workflow, NLP endpoints, Tasmee/STT, health endpoints, admin authentication, rate limiting, CORS, production security, and frontend/backend API compatibility.

Remove infrastructure that is demonstrably dead. Do NOT remove a service merely because setup is inconvenient.

## Phase 7 — Frontend completion

Run the repository's canonical equivalents of:

```bash
npm install
npm run typecheck
npm run lint
npm run build
```

Repair all legitimate errors. Then exercise every user-facing feature against the real backend: Arabic RTL, English LTR, Arabic fonts, Quran rendering, surah/ayah navigation, search, RAG questions, citations, tafseer display, story atlas, graph visualizations, theme/concept views, Tasmee/audio, loading states, empty states, backend-unavailable state, HF-unavailable/quota state, offline behavior where supported, responsive layouts, accessibility, and phone- and tablet-sized layouts.

No user-facing feature may assume localhost.

## Phase 8 — Android + iOS

Avoid a React Native rewrite unless repository evidence proves it necessary. Evaluate Capacitor first; if viable, implement it properly:

- add `@capacitor/core`, `@capacitor/cli`, `@capacitor/android`, `@capacitor/ios`
- create `android/` and `ios/` projects
- configure: app/bundle ID, app name, production backend URL, deep links if required, safe areas, status bar, keyboard behavior, Android network security, iOS App Transport Security, orientation, icons/splash (existing assets or placeholders)
- request permissions only where genuinely required

If Tasmee uses the microphone: configure the Android microphone permission and iOS `NSMicrophoneUsageDescription`, and test permission denial, interrupted recording, and upload/backend errors.

The API URL must be environment-aware (local backend in development, public HTTPS backend in production). Never ship localhost as the production API URL.

## Phase 9 — PWA

The repository already depends on `vite-plugin-pwa`. Audit and, where useful, complete: manifest, icons, service worker, cache strategy, installability, offline shell, and update flow.

Do NOT cache mutable RAG responses indefinitely. Canonical Quran/static content may use a more aggressive but safe caching strategy.

## Phase 10 — Production backend deployment

The backend must deploy to ordinary cloud infrastructure without depending on the owner's PC, WSL, Ollama, a local GPU, hard-coded IP addresses, or localhost-only service discovery.

Provide production Docker configuration with: health checks, restart behavior, explicit production commands, sensible resource handling, non-root execution where practical, no development reload, and no development secrets. All configuration comes from environment variables/secrets. Secrets must not exist in images or Git.

## Phase 11 — Secret hygiene

- Inspect Git tracking and the history available in the checkout for accidental secrets.
- `.env` must remain untracked. `.gitignore` must cover `.env` and `.env.*`, with deliberate exceptions such as `.env.example`.
- Never print `HF_TOKEN`, never put it in test output, never put it in frontend environment variables.
- If a real token has EVER been committed to Git history, report it as P0 and instruct the owner to revoke/rotate it. Do not try to hide a leaked credential by only deleting the current file.

## Phase 12 — Testing

- Normal unit/CI tests must use mocks and must NOT consume Hugging Face inference.
- Create separately marked live tests that run only when explicitly enabled:
  - `pytest -m "not live_hf"` for normal runs
  - `pytest -m live_hf` for live smoke tests (minimal and cheap)
- Cover: valid response, timeout, 401, 403, 429/quota, unavailable model, malformed upstream response, network outage, citation validation, Arabic answer, English answer.

## Phase 13 — CI

GitHub Actions on pushes/PRs must verify:

- Backend: dependency install, formatting/lint where used, type checks where used, unit tests, migration sanity
- Frontend: `npm ci`, typecheck, lint, build
- Security: obvious secret leakage, dependency audit where practical

Normal PR CI must not require `HF_TOKEN`, and secrets must never be exposed to untrusted PRs.

## Phase 14 — Documentation

After implementation is verified, rewrite stale documentation. README must document: architecture, the HF-only AI backend, required environment variables, development startup, production startup, web build, Android build, iOS build, backend deployment, database migration, tests, the live-HF smoke test, secret management, and limitations/cost considerations.

Delete obsolete Ollama/Anthropic setup instructions. Update `.env.example` with placeholders only.

## Phase 15 — Completion gates

Compiling is not completion. Prove each applicable gate with evidence:

| Gate | Requirement |
|---|---|
| G1 | No production Ollama dependency remains |
| G2 | No production Anthropic dependency remains |
| G3 | `HF_TOKEN` is server-side only |
| G4 | Backend boots from a clean environment |
| G5 | Database migrations complete cleanly |
| G6 | Backend automated tests pass |
| G7 | Frontend type checking passes |
| G8 | Frontend lint passes |
| G9 | Frontend production build passes |
| G10 | Web client uses real backend configuration without localhost assumptions |
| G11 | A controlled HF live smoke test succeeds when credentials/credits are available |
| G12 | Quran/tafseer citation safety tests pass |
| G13 | Production Docker configuration builds (if Docker is available) |
| G14 | Capacitor web assets sync to Android |
| G15 | Android project builds at least a debug APK (when the Android SDK is available) |
| G16 | Capacitor web assets sync to iOS |
| G17 | iOS project/configuration is valid |
| G18 | No real secret is tracked |
| G19 | README matches the implemented system |

Do not claim an iOS native build succeeded without macOS/Xcode. Clearly separate **VERIFIED HERE** from **REQUIRES FINAL MACOS/XCODE SIGNING VERIFICATION**.

---

## Autonomy rules

Work autonomously through recoverable technical problems. Do not stop to ask questions that can be answered from the repository, official documentation, running tests, or current Hugging Face/Capacitor documentation. When several approaches are reasonable: evaluate them, choose the least complex production-quality option, record the rationale, and continue.

Do NOT:

- rewrite the entire application unnecessarily
- introduce microservices without need
- rewrite React in React Native merely for mobile distribution
- introduce paid APIs other than infrastructure the owner explicitly selected
- silently remove major working features
- fabricate passing tests or suppress failing tests to get a green build
- weaken Quran citation/safety validation
- store secrets in source control

## Change management

- Work on `feat/huggingface-mobile-production`.
- Make coherent commits by phase (no "fix stuff" commits).
- Before every commit: inspect `git diff`, make sure no credential is included, and run the relevant tests.
- Push the branch and prepare it for owner review. Do not merge to `main`.

## Final report (at the end of each session, covering the phases done so far)

1. Executive summary
2. Architecture before vs after
3. Every Ollama component removed
4. Every Anthropic component removed
5. Hugging Face models selected and rationale
6. AI components still executed locally on CPU, if any, and why
7. Backend fixes
8. Frontend fixes
9. Android status
10. iOS status
11. PWA status
12. Security findings
13. Quranic-content integrity verification
14. Tests run, with exact pass/fail counts
15. Commands used
16. Files changed
17. Remaining blockers
18. Items requiring owner action
19. Deployment procedure
20. Explicit final classification: NOT DEPLOYABLE / DEPLOYABLE WITH BLOCKERS / RELEASE CANDIDATE / PRODUCTION READY

Do not use PRODUCTION READY unless every relevant completion gate is supported by evidence.
