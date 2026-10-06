# Phase 7: Frontend

## Gates

| Gate | Command | Result |
|---|---|---|
| G7 typecheck | `npx tsc --noEmit` | **0 errors** |
| G8 lint | `npm run lint` (`--max-warnings 0`) | **0 errors, 0 warnings** (baseline was 21 errors) |
| G9 build | `npm run build` | **succeeds**: 171 JS chunks, 89 precache entries |
| G10 no localhost | browser run + bundle grep | **0** requests to a loopback API host across 111 page loads; **0** `localhost:<port>` strings in `dist/` |

## Fixes

**Real bugs found by lint.**
- `DhikrPage` called hooks after a conditional early return.
- `SurahAtlasDetailPage` declared `useMemo` after its not-found return.

Both changed hook order between renders. Fixed by moving the hooks above the returns.

**Other lint fixes.**
- Literal BOM characters in regexes are now escaped as `﻿`.
- Empty `catch {}` blocks now say why they are empty.
- One `let` is now `const`.
- Stale `eslint-disable` directives removed.

**No feature assumes localhost.**
- `src/lib/config.ts` is the single source of the API origin. `VITE_API_URL` is empty for the web app (same origin, nginx proxies `/api`) or the public HTTPS API origin for Capacitor builds.
- Every raw `fetch` and the axios client now go through `apiUrl()`. Before, five pages called relative `/api/...` paths directly, which breaks on mobile.
- The Tasmeeʿ WebSocket goes through `wsUrl()`.
- `ThemeAdminPage` used to fall back to `http://localhost:8000`; that fallback is removed.
- `vite.config.ts` refuses a production build whose `VITE_API_URL` is a loopback address. Override with `ALLOW_LOCAL_API_URL=true`.
- `.env.example` no longer suggests `http://localhost:8000`.
- The status dashboard printed dev-only URLs (`localhost:3000`, `/api → localhost:8002`, a localhost CORS list, localhost DB strings). It now shows the runtime origin and API, and names the server env vars.
- The microphone help text no longer tells users to open `localhost:3000`.

**HF states rendered.**
- RAG `status: "ai_unavailable"` now shows a quota-specific or outage-specific notice in Ask and Mushaf, with the verbatim tafsir excerpts kept below.
  - Before, the raw code `ai_quota_exceeded` was shown as a warning, plus a misleading "no verified source" banner.
  - The AI disclaimer is no longer attached to fixed notices or refusals.
- `RAGResponse` types now include `answer_kind`, `ai_generated` and `error_code`.
- Tasmeeʿ handles the server's `stt_unavailable` message and close code 4003 with a speech-recognition notice in Arabic and English, instead of a generic "Microphone Error".
- The tafsir AI tools (summary, word explanation, Q&A) carry an "AI-generated, not Qur'an or tafsir" label.

**Backend-unavailable state.** The Qur'an reader showed an empty mushaf ("0 verses") when the API failed. It now shows an error panel with a retry button.

**Responsive and accessibility.**
- `/status` overflowed horizontally on phones; the tab bar now scrolls.
- 73 icon-only buttons on `/dhikr` had no accessible name; they now have `aria-label` and `aria-expanded`.
- The onboarding modal now has `role="dialog"`, `aria-modal`, `aria-labelledby` and closes on Escape.

**Fonts.** A hard-coded `preload` of a versioned Google Fonts file returned 404 on every page. It is removed; the stylesheet link already loads the font.

## Browser verification (Playwright, Chromium, production build against the real backend)

**Route sweep.**
- 37 routes × (EN phone 390×844, EN tablet 820×1180, AR phone) = **111 page loads**.
- No page crashed, rendered blank, timed out or overflowed horizontally.
- `dir`: `rtl` on every Arabic load, `ltr` on every English load.
- Arabic text uses the Noto Naskh / Amiri / Scheherazade stack.
- The only failing request is `/api/v1/quran/asbab/2` (503). The backend fetches asbab from an external host that this sandbox blocks (403), and the page shows its error state.

**Ask (RAG), English and Arabic.** HTTP 200, `status=answered`, 8 citations each.

**AI unavailable (mocked `ai_unavailable` + `ai_quota_exceeded`), EN and AR.**
- The notice is shown.
- The raw code is not shown.
- No false "no verified source" banner.
- The tafsir excerpt is still rendered.

**Search.** Arabic query returns results.

**Backend down (all `/api` requests refused).**
- Ask shows "An error occurred… try again".
- The Qur'an reader shows the error panel and retry.
- Mushaf still renders its bundled text.
- Story atlas shows its error state.
- No uncaught exceptions.

**Offline.** After the service worker installs, `/`, `/quran/1` and `/dhikr` load with the network off (see Phase 9).

## Not verified here

- **Live microphone recitation.** There is no microphone in headless Chromium. The STT path is covered by backend tests and the live HF smoke test.
- **Admin pages.** They need an admin key; they were checked only for rendering.
