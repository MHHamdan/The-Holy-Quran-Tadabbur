# Asmā' Allah — Reviewer Guide

_Last updated: 2026-05-17_

For scholars and editors reviewing the Phase W Asmā' atlas via the
admin review dashboard.

## What you are reviewing

Phase W emits 5 new content types into the review queue:

| contentType | What it represents | Default priority |
|---|---|---|
| `asma_name` | A name's atlas record (label, transliteration, category) | medium (high for dhat / jalal) |
| `asma_meaning` | A meaning claim for the name | **high** |
| `asma_category` | The name's category assignment | medium |
| `asma_occurrence` | A single counted Quran occurrence of the name | low (medium for contextual) |
| `asma_pairing` | A pair of names co-occurring in the same ayah | medium |

## Workflow

1. Open `/admin/review` and filter by `contentType` ∈
   {`asma_name`, `asma_meaning`, `asma_category`, `asma_occurrence`,
   `asma_pairing`}.
2. Sort by `priority` (high first).
3. For each task, follow the steps below.
4. Submit your decision with bilingual notes.

## How to review an `asma_name`

1. Confirm the Arabic name renders correctly and the transliteration is
   accurate.
2. Confirm the seed list correctly includes this name.
3. Decide: **approve** / **changes_requested** / **reject**.

## How to review an `asma_meaning`

This is the highest-priority work in Phase W.

1. Confirm a **trusted scholarly source** supports the meaning you want
   to attach. Trusted sources are listed in
   `frontend/src/data/sourceRegistry.ts` with reliabilityLevel
   `canonical` or `verified`.
2. Compose a short, bilingual meaning that does NOT exceed the source's
   own wording.
3. Submit the meaning + sourceId(s) via the review dashboard.
4. The atlas remains `needs_review` until the meaning is promoted to
   `verified`.

## How to review an `asma_category`

1. Confirm the category (`dhat / jamal / jalal / kamal / afaal`)
   matches the classical classification.
2. Decide.

## How to review an `asma_occurrence`

1. Open the Mushaf at the cited ayah.
2. Confirm the matched form is genuinely the divine name in context
   (some forms are also personal-name titles, common nouns, or
   participle adjectives).
3. Decide.

## How to review an `asma_pairing`

1. Open the cited ayah.
2. Confirm both names co-occur and the pairing is meaningful (e.g.
   `العزيز الحكيم` is classical).
3. Decide.

## What you must NOT do

- Do not paste meanings from random websites. Use only sources from the
  `sourceRegistry.ts` allowlist.
- Do not edit Quran text.
- Do not promote `asma_occurrence` to verified for names that overlap
  with non-divine usages (e.g. `العزيز` in Surah Yusuf) unless the
  specific occurrence is clearly divine-name usage.
- Do not promote `asma_meaning` to verified without attaching at least
  one trusted source.

## Trusted source allowlist

`ibn_kathir`, `tabari`, `qurtubi` (plus `_ar` / `_en` variants).

Project-curated metadata in `backend/app/data/allah_names.py` is the
**reviewer-facing seed source**. Reviewers may use it as a starting
point but must cite an external scholarly source before promoting
meanings to verified.

## Priority bands

| Priority | Examples |
|---|---|
| High | Meaning claims; dhat / jalal category names; theological |
| Medium | Category confirmation; pairings; contextual occurrences |
| Low | Exact-string occurrences for unambiguous names |

## Example walkthrough — `al_aziz`

1. Task: `asma_occurrence` for `al_aziz::2:209::exact_name`.
2. Open the Mushaf at 2:209: `…وَٱعْلَمُوٓا۟ أَنَّ ٱللَّهَ عَزِيزٌ
   حَكِيمٌۭ`. The word `عَزِيزٌ` here is clearly a divine-name usage
   (predicated of Allah). Approve.
3. Task: `asma_occurrence` for `al_aziz::12:30::exact_name`. Open
   12:30: `…نِسْوَةٌۭ فِى ٱلْمَدِينَةِ ٱمْرَأَتُ ٱلْعَزِيزِ`. Here
   `ٱلْعَزِيزِ` refers to Aziz of Egypt (the personal-name title in
   the Yusuf story), NOT the divine name. Reject (or flag as
   non-divine-context).

Reviewer notes drive the eventual labels users see in the UI.
