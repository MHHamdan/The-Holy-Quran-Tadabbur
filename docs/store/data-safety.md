# Store privacy answers (draft for owner review)

Google Play **Data safety** form and App Store Connect **App Privacy** labels,
derived from the code as of 2026-10-14. These are drafts: the owner submits the
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
| Questions to the AI assistant | Backend, processed by Hugging Face | Conversation up to 24 h (Redis TTL), then deleted | `backend/app/services/conversation_service.py` (`SESSION_TTL_SECONDS`) |
| Spiritual-guidance message | Backend, processed by Hugging Face | Message **not stored**; detected feeling, theme, verse references and any reflection the user saves, without identity, up to 180 days | `backend/app/api/routes/therapy.py` (`THERAPY_RETENTION_DAYS`) |
| Recitation audio (Tasmeeʿ) | Streamed to the backend, transcribed by Hugging Face | Audio never written to disk; session accuracy kept without identity | `backend/app/api/routes/tasmee.py` |
| Feedback | Backend | Message text and page URL; no retention limit yet | `backend/app/api/routes/feedback.py` |
| Search queries | Backend (meaning-based search also via Hugging Face) | Transient; recent searches may sit in server memory until restart | search routes |
| Location | Device → AlAdhan, OpenStreetMap (Nominatim, Overpass) directly; never to our server | Last position cached on the device only | `frontend/src/hooks/useGeolocation.ts` |
| IP address | Backend rate limiter | In memory about a minute; not logged | rate limiting |
| Journal, bookmarks, progress, reminder time, offline recitations | Device only | Excluded from Android cloud backup and device transfer | WebView storage, `files/audio/` |

No accounts, no device or advertising identifiers, no analytics, no ads, no
tracking, no sale of data. Deletion: the "Delete my data" button on `/privacy`
erases guidance sessions and reflections on the server and all app data on the
device.

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

Required-reason API declared: File Timestamp, reason C617.1
(`@capacitor/filesystem`).

## Open questions — OWNER DECISION

1. **Precise vs approximate location.** The app requests fine location on
   Android and currently sends the device's coordinates unrounded to AlAdhan and
   OpenStreetMap. Either round the coordinates before they leave the device
   (then "Approximate" / Coarse Location is accurate), or declare Precise
   Location in both stores and add `NSPrivacyCollectedDataTypePreciseLocation`
   to the privacy manifest.
2. **Sensitive information.** The spiritual-guidance feature stores a detected
   feeling (for example sadness or anxiety) with verse references for up to 180
   days, without identity. Decide whether this counts as Apple "Sensitive Info"
   or Play "Health info"; this draft does not assume either way.
3. **Feedback retention.** Feedback messages have no retention limit yet;
   decide one and state it on `/privacy`.
4. **Privacy contact.** Set the `PRIVACY_CONTACT` repository variable (release
   tags fail without it); the address appears on `/privacy` and in the store
   listings.
