# Store privacy answers (draft for owner review)

Google Play **Data safety** form and App Store Connect **App Privacy** labels,
derived from the code as of 2026-10-16 (refreshed after search history stopped being recorded). These are drafts: the owner submits the
final answers and must decide the items marked **OWNER DECISION**.

Sources of truth that must stay in step with this file:

- In-app policy: `frontend/src/pages/PrivacyPage.tsx` (`/privacy`)
- iOS privacy manifest: `frontend/ios/App/App/PrivacyInfo.xcprivacy`
  (`backend/tests/unit/test_store_privacy_declarations.py` checks that the
  data types below match the manifest)
- Android backup rules: `frontend/android/app/src/main/res/xml/data_extraction_rules.xml`

## What the code does

| Data | Where it goes | Kept | Code |
|---|---|---|---|
| Questions to the AI assistant | Backend, processed by Hugging Face | Conversation up to 24 h (Redis TTL), then deleted; "Delete my data" deletes it sooner | `backend/app/services/conversation_service.py` (`SESSION_TTL_SECONDS`), `frontend/src/lib/dataErasure.ts` |
| Spiritual-guidance message (guidance and its chat mode) | Backend, processed by Hugging Face | Message **not stored**; detected feeling, theme, verse references and any reflection the user saves, without identity, up to 180 days (purged daily). Each session has a server-generated id and a secret token held only by the device (SHA-256 stored); reading, writing and deleting need the token. Legacy rows from before tokens existed (no stored hash) cannot be proved to belong to any device, so they are not deletable on request (an id alone never deletes a row); they expire through the 180-day purge, and `/privacy` says so | `backend/app/api/routes/therapy.py` (`THERAPY_RETENTION_DAYS`, `purge_expired_private_data`, `delete_sessions`) |
| Recitation audio (Tasmeeʿ) | Streamed to the backend, transcribed by Hugging Face | Audio never written to disk; recognised words and possible slips of each session, without identity, up to 90 days (purged daily); token-protected like guidance sessions | `backend/app/api/routes/tasmee.py` (`TASMEE_RETENTION_DAYS`) |
| Feedback | Backend | Message text and page URL; not linked to the device, so not reachable by "Delete my data"; no retention limit yet (**OWNER DECISION**) | `backend/app/api/routes/feedback.py` |
| Search queries | Backend, to run the search (meaning-based search also via Hugging Face) | Processed to serve the request only; the app no longer records searches (`searchHistoryStore.recordSearch` keeps them in page memory only, nothing is persisted on the device or posted to `/quran/history`). Entries that earlier test builds posted sit in server memory under the device's random session key for up to 30 days (daily purge) or until restart; "Delete my data" still clears them | `frontend/src/stores/searchHistoryStore.ts`, `backend/app/services/search_history.py` (`SEARCH_HISTORY_TTL_DAYS`), `backend/app/api/routes/therapy.py` (`purge_expired_search_history`) |
| Dhikr counts | Device only (this version sends nothing) | Older app versions sent anonymous daily totals (date, category, counts; no identifier); the server deletes them after 30 days | `frontend/src/pages/DhikrPage.tsx`, `backend/app/api/routes/adhkar.py` (`DHIKR_RETENTION_DAYS`) |
| Location | Device → AlAdhan, OpenStreetMap (Nominatim, Overpass) directly, rounded to 2 decimals (about 1 km) before it leaves the device; never to our server | Last position cached on the device only (exact value used on the device for the Qibla) | `frontend/src/lib/islamicApis.ts` (`coarsen`), `frontend/src/pages/tools/MosqueFinderPage.tsx` |
| IP address | Backend rate limiter | In memory about a minute; not logged | rate limiting |
| Journal, bookmarks, progress, dhikr counts, reminder time, offline recitations | Device only | Excluded from Android cloud backup and device transfer | WebView storage, `files/audio/` |
| Server backups | Backend host | Daily backups, 7 daily + 4 weekly kept, so deleted rows can remain in a backup for up to about five weeks (stated on `/privacy`) | `scripts/ops/backup_prod.sh` |

No accounts, no device or advertising identifiers, no analytics, no ads, no
tracking, no sale of data.

Deletion: the "Delete my data" button on `/privacy` deletes, on the server,
every guidance and chat session (with reflections) and every Tasmeeʿ session
this device created, the device's recent searches and its AI-assistant
conversation; then it erases all app data on the device. If the server cannot
be reached, the device keeps only the keys to what is still on the server and
retries automatically (next launch / back online); the page says which parts
are still pending. Feedback messages and server backups are outside its reach,
and the page says so.

## Google Play — Data safety

- **Does your app collect or share any of the required user data types?** Yes.
- **Is all of the user data collected by your app encrypted in transit?** Yes,
  provided the production API is served over HTTPS only (the release build
  refuses non-HTTPS API URLs and Android release builds forbid cleartext).
- **Do you provide a way for users to request that their data is deleted?** Yes
  (in-app, `/privacy` → "Delete my data").

| Category → type | Collected | Shared | Ephemeral | Required / optional | Purpose |
|---|---|---|---|---|---|
| Location → Approximate location | Yes | Yes (AlAdhan, OpenStreetMap) | No | Optional | App functionality |
| Location → Precise location | **OWNER DECISION** (see below) | | | Optional | App functionality |
| Audio → Voice or sound recordings | Yes | No (Hugging Face is a service provider) | Yes | Optional | App functionality |
| App activity → In-app search history | Yes | No | Yes | Optional | App functionality |
| App activity → Other user-generated content (questions, reflections, feedback) | Yes | No | No | Optional | App functionality |

Search history is **ephemeral** in Play's sense: queries are processed in
memory only for as long as it takes to serve the request, and the app keeps no
search list on the device or the server. It is still declared as collected,
conservatively, because the query text reaches our backend and Hugging Face.

Play treats data sent to a service provider that processes it on the
developer's behalf (Hugging Face) as not "shared". Data the device sends
directly to AlAdhan / OpenStreetMap at the user's request is listed as shared
to be conservative; **OWNER DECISION** whether Play's "user-initiated transfer"
exemption applies.

## App Store Connect — App Privacy

Matches `PrivacyInfo.xcprivacy` (`NSPrivacyCollectedDataTypes`):

| Data type | Linked to the user | Used for tracking | Purpose |
|---|---|---|---|
| Audio Data | No | No | App Functionality |
| Other User Content | No | No | App Functionality |
| Search History | No | No | App Functionality |
| Coarse Location | No | No | App Functionality |

Search History is declared conservatively: queries reach the backend to be
served, though nothing is stored for later use. **OWNER DECISION** whether to
drop it (it would then also come out of `PrivacyInfo.xcprivacy`).

Required-reason API declared: File Timestamp, reason C617.1
(`@capacitor/filesystem`).

## Open questions — OWNER DECISION

1. **Precise vs approximate location.** Coordinates are rounded to about
   1 km (`coarsen()`) before they reach AlAdhan or OpenStreetMap, so
   "Approximate" / Coarse Location matches what leaves the device. The Android
   manifest still requests `ACCESS_FINE_LOCATION` (the exact fix is used on
   the device for the Qibla direction); decide whether to drop it or to keep
   it and confirm Play accepts the Approximate declaration.
2. **Sensitive information.** The spiritual-guidance feature stores a detected
   feeling (for example sadness or anxiety) with verse references for up to 180
   days, without identity. Decide whether this counts as Apple "Sensitive Info"
   or Play "Health info"; this draft does not assume either way.
3. **Feedback retention.** Feedback messages have no retention limit yet;
   decide one and state it on `/privacy`.
4. **Privacy contact.** Set the `PRIVACY_CONTACT` repository variable (release
   tags fail without it); the address appears on `/privacy` and in the store
   listings.
5. **Public privacy URL.** `fastlane/metadata/ios/{en-US,ar}/privacy_url.txt`
   still hold the `https://REPLACE_WITH_PUBLIC_WEB_HOST/privacy` placeholder.
   Set the real public web host (the page is `/privacy`) before submitting;
   the release guard must refuse a `v*` tag while any `REPLACE_WITH`
   placeholder remains under `fastlane/metadata`.
