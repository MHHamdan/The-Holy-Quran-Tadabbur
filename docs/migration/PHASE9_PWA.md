# Phase 9: PWA

## Findings and fixes

| Area | Before | Now |
|---|---|---|
| Icons | The manifest's only icon (`/favicon.svg`) did not exist; the app was **not installable** | `favicon.svg`, 192/512 PNG, 512 maskable (safe-zone glyph), 180 apple-touch-icon; manifest `id`/`scope` set; theme colour matches the app (`#0284c7`) |
| API cache | One rule cached **461 GET routes** for 24 h (everything under `/api/v1/quran`, `/tafseer`, `/dhikr`, …), including per-user bookmarks/history/progress, search, stats and admin dashboards | Allow-list of canonical content only (below); everything else under `/api` is network-only |
| Static JSON | `CacheFirst` for any URL ending `.json` (any origin), so updated data could be stale for 7 days | Same-origin, non-API `.json` only, `StaleWhileRevalidate` |
| Offline fonts | Google Fonts not cached; Arabic text fell back to system fonts offline | Stylesheet `StaleWhileRevalidate`, font files `CacheFirst` (1 year) |
| Navigation fallback | `index.html` served for **every** navigation, including `/api/*`, `/docs`, `/health` | `navigateFallbackDenylist` for those paths |
| Update flow | `autoUpdate` + `skipWaiting`: a new service worker took control under a running page; old lazy chunks could then 404 mid-session | `registerType: 'prompt'`: the new build downloads in the background; an in-app banner (AR/EN) offers **Reload**. Checks for updates hourly. A `vite:preloadError` handler reloads once (rate-limited to once per 30 s) if a stale tab hits a missing chunk |
| nginx | `sw.js` matched the `*.js` rule → `Cache-Control: immutable, max-age=1y`, which delays update detection | `sw.js` and `manifest.json` are `no-cache`; only content-hashed `/assets/*` and `workbox-<hash>.js` are immutable; unhashed icons/JSON get 1 day. `/api/` is a `^~` prefix, so the regex rules can't capture `/api/...json` |
| Offline notice | none | A banner explains that saved Qur'an/tafsir pages work offline and AI features need a connection |
| Admin tokens | `SourcesPage` and `ThemeAdminPage` kept the admin token in **localStorage** (persists across sessions, readable by any script on the origin) | `sessionStorage` (this tab only), like the admin API key since Phase 11; guarded by `test_admin_credentials_are_not_persisted_in_local_storage` |

## Cache strategy

| Content | Strategy | Lifetime |
|---|---|---|
| App shell (hashed JS/CSS, `index.html`, icons) | Precache, versioned per build, outdated caches cleaned | until next build |
| Canonical API: `quran/{suras,verses,page,juz,tafseer,asbab,asma,allah-names,topics}`, `quran/metadata`, `quran/tafsir/{sources,verse,compare}`, `tafseer/{s}/{a}`, `tafseer/{surah,compare,editions}`, `duas`, `vocabulary/{verse,by-ref,lookup,sources}`, `quranic-calls/{list,detail,by-surah,graph}` | `StaleWhileRevalidate`, GET only, 200 only | 30 days, 3,000 entries |
| RAG answers, tafsir LLM output, quiz, search, similarity, per-user data, stats, admin, health | **Not cached** (network-only) | — |
| Google Fonts | CSS: `StaleWhileRevalidate`; files: `CacheFirst` | 1 year |

The Qur'an text and tafsir are fixed content and can be cached aggressively. AI answers depend on the model and the account's quota state, so they are never cached by the service worker. The backend's own Redis RAG cache (1 h TTL, confidence ≥ 0.3) is unchanged.

## Verification (Chromium, production build served by `vite preview`, real backend)

- **Installability:**
  - `Page.getInstallabilityErrors` → **0 errors**
  - `Page.getAppManifest` → **0 manifest errors**
- **Cache contents** after reading `/quran/1`, `/quran/2` and `/tafsir/compare/2/255`, then requesting bookmarks, history, search and a RAG POST:
  - `api-canonical-v2` held only `quran/suras/1`, `quran/suras/2`, `quran/verses/3/139`, `quran/metadata`, `tafseer/compare/2/255`.
  - **0** bookmark, history, search or RAG entries.
- **Offline** (network disabled):
  - `/quran/2` rendered the full surah (49,643 Arabic characters).
  - `/quran/1` and `/ask` rendered the shell.
  - All three showed the offline banner and no error panel.
- **Update flow:** a rebuild with a changed `index.html` gave:
  - the existing tab showed "A new version of the app is available"
  - **Reload** activated the new build (build marker `v2` present)
  - the banner did not reappear
- `nginx -t` passes with the new location blocks.

## Not covered

- iOS Safari install (Add to Home Screen) and Android TWA were not run on devices here. The manifest and apple-touch-icon are in place for both.
- Native Capacitor builds do not use the service worker: they ship the assets in the app bundle.
