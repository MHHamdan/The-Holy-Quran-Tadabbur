# Phase 15: Completion gates

Evidence was gathered on 2026-10-06 on the final code (branch `feat/huggingface-mobile-production`). The environment was an Ubuntu 24.04 VM: 4 vCPU, no GPU, no macOS. GitHub Actions passes all 5 jobs on the Phase 14 commit (run 37524362458): backend, frontend, mobile, images, security.

| Gate | Status | Evidence |
|---|---|---|
| G1 No production Ollama dependency | **PASS** | 0 matches for `ollama` in `backend/app`, `pyproject.toml`, Dockerfiles, `frontend/src`, `package.json`, Capacitor config, prod compose, `.env.example`, Makefile and dev scripts. 0 Ollama packages in the backend image. |
| G2 No production Anthropic dependency | **PASS** | 0 matches for `anthropic` / `ANTHROPIC_API_KEY` / `claude-` in the same set. 0 `anthropic` packages in the backend image. `walkthrough.md` (old setup notes) deleted. |
| G3 `HF_TOKEN` server-side only | **PASS** | `test_secret_hygiene.py` passes 6/6, covering no secret-bearing `VITE_*`, no HF access in the frontend, and native projects free of credentials. 0 HF-token or HF-endpoint strings in the web `dist/`, the debug APK, the release APK, or the iOS `public/`. |
| G4 Backend boots from a clean environment | **PASS** | Fresh venv from `backend/pyproject.toml` (0 torch/anthropic/ollama/transformers), env vars only, `ENVIRONMENT=production`: `/health` 200, `/ready` 200, `/docs` 404 (disabled), CORS allows `capacitor://localhost` and rejects an unknown origin. The production image also booted healthy in the compose stack. |
| G5 Database migrations complete cleanly | **PASS** | Fresh database: single head `q6r7s8t9u0v1`; `upgrade head`, then `downgrade -1`, then `upgrade head` gives 40 tables. The compose `migrate` service exited 0 on empty volumes. CI repeats this on every push. |
| G6 Backend automated tests pass | **PASS** | Full dev data: **2586 passed, 0 failed**, 37 skipped, 11 deselected (`live_hf`). CI-equivalent (fresh migrate, committed seeds, empty Qdrant): **2561 passed, 0 failed**, 62 skipped. The skips are external-data tests declared with `requires_data` (40), Qdrant-index tests and audio fixtures. |
| G7 Frontend type checking | **PASS** | `tsc --noEmit`: 0 errors (also `tsconfig.node.json`: 0) |
| G8 Frontend lint | **PASS** | `eslint --max-warnings 0`: 0 errors, 0 warnings |
| G9 Frontend production build | **PASS** | `npm run build` succeeds: 104 precache entries, service worker generated |
| G10 Web client uses real backend config, no localhost | **PASS** | 111 page loads (37 routes × EN phone/tablet + AR phone) against the real backend: **0** requests to a loopback API host, RTL/LTR correct on every load, 0 horizontal overflow, 0 blank pages, 0 unnamed buttons. A production build with a loopback `VITE_API_URL` is refused. |
| G11 Controlled HF live smoke test | **NOT MET NOW: blocked by HF credits** | `pytest -m live_hf` today: 1 passed (unknown-model mapping) and 10 skipped, each with "HTTP 402: credits exhausted" (chat, embeddings, rerank, zero-shot, STT, grounded RAG). Before the credits ran out (session 1): 7 passed, 4 skipped on 402. It re-runs as soon as the account has credit. |
| G12 Qur'an/tafsir citation safety tests | **PASS** | Safety suites (Qur'an integrity, citation consistency, Phase 5 grounding, scientific-claim safety, therapy safety, KG query safety): **153 passed**. All 29 test files touching citations/grounding: **866 passed, 0 failed**, 14 skipped. |
| G13 Production Docker builds | **PASS** | Backend and web images rebuilt on the final code. `docker-compose.prod.yml` brought up 6 healthy services plus a successful `migrate`. The documented seeding procedure ran in it and was idempotent. Endpoints returned 200 through nginx: Qur'an, tafsir compare, RAG with 8 citations, KG, atlases. CI `images` job green. |
| G14 Capacitor web assets sync to Android | **PASS** | `cap sync android`: 101 web asset files in the APK's `assets/public/`, plus `capacitor.config.json`. CI `mobile` job green. |
| G15 Android debug APK | **PASS** | `./gradlew clean assembleDebug`: BUILD SUCCESSFUL. `app-debug.apk` is 6,106,793 bytes, package `com.mhamdan.tadabbur`, targetSdk 36. The unsigned release APK also builds. CI builds the debug APK on every push. |
| G16 Capacitor web assets sync to iOS | **PASS** | `npm run ios:sync`: `ios/App/App/public/index.html` and `capacitor.config.json` present. CI `mobile` job green. |
| G17 iOS project/configuration valid | **PASS (configuration)**. **Native build REQUIRES MACOS/XCODE.** | Xcode project parses: one `App` target; bundle ID `com.mhamdan.tadabbur` in Debug and Release; iOS 15; 0 unresolved file references; SPM package present. `Info.plist` parses, has `NSMicrophoneUsageDescription`, and no ATS exceptions. Compile, sign and run were **not** attempted (no macOS). |
| G18 No real secret tracked | **PASS** | gitleaks over all 224 commits: no leaks. Working tree: no leaks. The 2 reviewed false positives are fingerprinted. The only tracked env file is `.env.example` (placeholders). |
| G19 README matches the implemented system | **PASS** | Every repository path, `npm run` script, `make` target and env var named in the README exists, after fixing 1 path. The data-seeding section was executed as written against the production stack. |

## VERIFIED HERE vs REQUIRES FINAL MACOS/XCODE SIGNING VERIFICATION

**VERIFIED HERE (Linux):**
- Web build
- PWA install, offline mode and update flow
- Android debug APK and unsigned release APK
- Android manifest, permissions and network security
- iOS project generation and sync
- iOS project and plist structure
- Microphone behaviour in the WebView code path (Chromium): denial, interruption, background, connection loss, STT quota
- Production Docker stack and data seeding

**REQUIRES MACOS/XCODE (not done):**
- iOS compile, code signing and archive
- WKWebView microphone prompt on a device
- App Store upload

**REQUIRES THE OWNER'S KEYS:**
- Android release signing and Play upload
