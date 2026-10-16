# Distribution policy

_Owner decision, 2026-10-14._

Tadabbur is distributed **free of charge** on the web, Google Play and the App
Store, with **no advertising, in-app purchases, subscriptions, paid tiers or
donations collected in the app**.

Several content licences depend on this:

| Source | Terms | Why this policy matters |
|---|---|---|
| Al-Tafsir al-Muyassar (King Fahd Complex) | Claimed: educational, non-commercial use with attribution. **Not confirmed at source** | On licence hold since 2026-10-16, not displayed (see below) |
| QuranEnc translations | Republication allowed; no inappropriate advertising | No advertising at all |
| Tanzil Qur'an text (CC BY 3.0) | Any use, verbatim, attributed with a link | Not dependent on this policy |

Changing the business model (ads, purchases, donations, a paid tier) requires,
before release: written permission from the King Fahd Complex for Al-Muyassar
or its removal, and a re-check of every entry in `data/manifests/`.

## Interim status: Al-Muyassar on licence hold (2026-10-16)

The King Fahd Complex (KFGQPC) terms for Al-Tafsir al-Muyassar have not been
confirmed at source, so this policy alone is not treated as a licence. Until
the owner decides:

- `tafseer_sources.muyassar_ar` has `license_verified = 0` (alembic
  `r5c1a2b3c4d5`); the row, `is_enabled` and the stored text are kept, and
  nothing is deleted.
- Nothing that requires a verified licence serves it: the reader and Mushaf
  tafsir, `/tafseer/compare`, `/tafseer/{surah}/{ayah}`, the AI tafsir
  assistant, RAG citations, and story and theme evidence. Requests for it get
  `403 EDITION_NOT_LICENSED`.
- The reader, Mushaf and API default tafsir is Tafsir al-Baghawi (classical,
  public domain; digital text from the Apache-2.0 riotu-lab/Quran-Tafseers
  dataset).
- `data/manifests/tafseer_sources.json` lists it in `licence_hold_ids` with an
  empty `verified_date`; `frontend/src/data/sourceRegistry.ts` marks it
  `unverified`.

To lift the hold the owner either records written KFGQPC terms (then sets
`verified_date` in the manifest and `license_verified = 1`), or switches to the
QuranEnc `arabic_moyassar` edition once QuranEnc confirms its terms cover it
(`backend/scripts/ingest/seed_tafsir_quranenc.py --replace-muyassar`). The
decision is queued in `data/review/owner_review_queue.json`
(`legal-muyassar-and-audio-licences`).
