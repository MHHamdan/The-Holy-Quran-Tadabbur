# Therapy Page — Safety Contract

This document defines what the therapy page **does and does not claim**
about Quranic healing, and the safeguards that gate every response. Read
this before changing any therapy code.

---

## What we say

Quran is a **spiritual healing (`shifaʾ`)** for the heart, mind, and soul.
This is grounded in three explicit verses:

- **17:82** — *"And We send down of the Quran that which is healing and a mercy to the believers."*
- **10:57** — *"…and a healing for what is in the hearts."*
- **41:44** — *"Say: it is, for those who believe, a guidance and a healing."*

Quranic recitation (ruqyah) is a Sunnah practice attested in Bukhari and
Muslim — used for spiritual comfort, blessings, and a request for cure.
Source attributions are mandatory on every claim.

## What we do NOT say

- We **never** claim the Quran cures specific medical conditions or
  replaces clinical care. The "Quran heals everyone in every condition"
  framing is bounded to *spiritual healing* and is paired with an
  explicit "this is not a substitute for medical/mental-health care"
  banner on every response.
- We **never** invent tafsir, dua chains, or hadith. Every hadith
  citation must include a sunnah.com URL or equivalent classical-source
  reference. Every verse meaning must come from a verified tafsir chunk
  or be marked `needs_review`.
- We **never** suggest stopping prescribed medication, ignoring symptoms,
  or skipping a doctor's visit because of Quranic recitation.
- We **never** diagnose mental-health conditions from user text.
  The emotion classifier is for *content selection*, not diagnosis.

## Crisis-safety override

If the user's input contains signals of suicidal ideation, self-harm,
abuse, or other acute crisis, the therapy response is **gated** by a
classifier (`CrisisClassifier`) that:

1. Prepends a bilingual crisis banner with regional hotline numbers (US
   988, UK Samaritans 116 123, KSA 920033360, plus
   `findahelpline.com/i?lang=en` as the international fallback).
2. Surfaces only calming/reassuring verses (rahmah, hope), never
   verses about punishment, hell, or accountability.
3. Includes a "please contact a professional" message in both Arabic
   and English.
4. Logs the trigger for review (no PII; only correlation ID).

Crisis signals are detected by **keyword + emotion-severity stacking**.
False positives are acceptable; false negatives are not. The classifier
errors on the side of showing the safety banner.

## Source attribution rules

Every therapy artifact must carry one or more of:

- `source_id` referencing `data/manifests/tafseer_sources.json`
- `hadith_ref` with collection (e.g. `bukhari:5735`) + sunnah.com URL
- `mental_health_org` for clinical references (Khalil Center,
  Yaqeen Institute, Naseeha, etc.) with an explicit URL

No therapy response without sources can be marked `verified`.

## Disclaimer mandate

Every guidance card, situation entry, and chat response must include —
either inline or via the response envelope — both Arabic and English
versions of:

> Spiritual support from the Quran is meaningful, but it is not a
> substitute for professional medical or mental-health care. If you are
> in crisis, please reach out to a qualified professional.

> الدعم الروحي من القرآن مفيد، لكنه ليس بديلاً عن الرعاية الطبية أو
> النفسية المتخصصة. إذا كنت في أزمة، فاطلب المساعدة من مختص.

## Audit log

The `humanReviewRequired: true` flag remains set on every newly-generated
entry until a scholarly reviewer approves it. The validator script
(`scripts/validate-therapy-content.ts`, T6) refuses to release any entry
without sources or without the disclaimer block.
