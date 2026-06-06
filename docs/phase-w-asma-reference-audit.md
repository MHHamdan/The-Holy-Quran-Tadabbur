# Phase W — Asmā' Allah — Reference Audit

_Last updated: 2026-05-17_

## Purpose

Summarises the external references consulted while designing the Asmā'
Allah al-Ḥusnā Atlas. External material is **inspiration only** —
nothing is ingested unless its `sourceId` already exists in
`frontend/src/data/sourceRegistry.ts`.

## Sources reviewed

| Source | Type | Why we looked at it | License posture |
|---|---|---|---|
| Al-Maqsad al-Asna fi Sharh Asma' Allah al-Husna — Al-Ghazali (d. 505 AH) | Classical Sunni treatise | The canonical source for traditional name interpretation. Used as a meaning-template for the project's existing `allah_names.py` curated module. | Public domain (classical). |
| Tafsir Ibn Kathir (Ibn Kathir, d. 774 AH) | Tafsir bil-ma'thur | Already in `sourceRegistry.ts` as `ibn_kathir` / `ibn_kathir_ar` / `ibn_kathir_en`. Used to cross-reference name occurrences. | Public domain. |
| Tafsir Tabari (al-Tabari, d. 310 AH) | Tafsir | In `sourceRegistry` as `tabari` / `tabari_ar`. | Public domain. |
| Tafsir Qurtubi (al-Qurtubi, d. 671 AH) | Tafsir | In `sourceRegistry` as `qurtubi` / `qurtubi_ar`. | Public domain. |
| Fath al-Bari (Ibn Hajar, d. 852 AH) | Hadith commentary | Used by the project's existing curated meanings; not yet wired into RAG. | Public domain. |
| Quranic Arabic Corpus (corpus.quran.com) | Token-level morphology | Best public ontology for Quranic Arabic; informs normalisation. | GPL — registered as `quranic_arabic_corpus` (experimental). Not ingested. |
| Mu'jam al-Mu'min al-Mufahris li-Alfaz al-Quran (Muhammad Fu'ad Abd al-Baqi) | Concordance of Quran words | Reference concordance for cross-checking lemma counts. | Out of scope for ingestion. |
| Tafsir Center / مركز تفسير | Modern thematic resources | Methodology reference only. | Not ingested. |
| Quran.com / SemanticTafsir UI patterns | UX | Reference for name detail page + evidence list layout. | UI inspiration only. |

## Design ideas extracted

- **Static atlas, not runtime scan**: the Quran is finite. Compute the
  atlas once at build time; the API serves cached JSON.
- **Basmalah exclusion policy** (see
  `docs/asma-basmalah-counting-policy.md`): the recurring opening
  basmalah inflates the count of الله / الرحمن / الرحيم by 113 each;
  classical scholarship treats these as decorative-positional, not
  doctrinal counts.
- **Clitic-prefix handling for "Allah"**: بالله, لله, والله, فلله, etc.
  must all match. We do strict right-side word-boundary checking AND
  whitelist the common Arabic clitic prefixes on the left.
- **Bilingual safe-message contract**: when no verified meaning is
  available, the API returns a fixed bilingual message; the UI surfaces
  it instead of "Loading…" or a blank.
- **Pairings**: classical scholarship highlights pairings like
  العزيز الحكيم, الغفور الرحيم, السميع البصير. The atlas computes
  pairings by co-occurrence in the same ayah, excluding "Allah ↔ X"
  pairings to keep the focus on classical Name-pairings.
- **No meanings in the build artifact**: meanings remain undefined in
  the atlas; they are only attached by scholar reviewers via the review
  workflow. The project's existing curated `allah_names.py` module is
  the reviewer-facing seed source for category labels.

## Data / source licensing concerns

- **The 99 Names list itself**: there is no single authoritative list of
  exactly 99 names; the famous hadith count is well-known but the
  enumeration varies across scholars (Al-Tirmidhi's narration is widely
  cited but disputed). The seed list mirrors the platform's existing
  curated list; reviewers may revisit specific entries.
- **External-website meanings**: many websites publish names with
  meanings. These are **not** in our trusted-source allowlist (Ibn
  Kathir / Tabari / Qurtubi). Reviewers may not paste their meanings
  without first promoting their source to the registry.
- **Quranic Arabic Corpus**: GPL; ingestion would carry redistribution
  obligations. Currently deferred.

## Safe to implement immediately

- Whole-Quran lemma scan using the existing `data/raw/quran_uthmani.json`.
- Basmalah-exclusion policy.
- Static atlas + cached API.
- Bilingual UI page with hero, category tabs, search, name cards,
  detail view, occurrence list with basmalah-excluded badges, pairings,
  related topics.
- Review-task generation for `asma_name`, `asma_meaning`,
  `asma_category`, `asma_occurrence`, `asma_pairing`.

## Requires source-registry integration

- A trusted Asmā' tafsir source dedicated to the names (e.g. Al-Saadi's
  *Tafsir al-Karim al-Rahman fi Asma' Allah al-Husna*) registered in
  `sourceRegistry` would enable meaning approval at scale.
- Audio recitation per Name (per-reciter terms apply).

## Requires scholarly review

- Every emitted occurrence (the atlas defaults all of them to
  `needs_review`).
- Every name's category — the project default classification mirrors the
  existing `allah_names.py` editorial choice, but each category claim
  remains `needs_review`.
- Every meaning — none is emitted by the pipeline; they appear only when
  a reviewer attaches one through the review workflow.

## How this differs from existing pages

| Concern | Old `/themes` Asmā tab | New `/themes/asma` |
|---|---|---|
| Backend | Runtime DB scan per name | Static atlas JSON, cached |
| Counts | Computed from API response (0 while loading) | Computed at build time; never "0 across all categories" |
| Basmalah handling | Implicit / unclear | Explicit policy, documented + tested |
| Per-Name detail | Inline expand | Dedicated route with evidence + pairings + related topics |
| Meaning safety | API may return curated meaning | Atlas never emits meanings; UI shows safe missing-source message |
| Review wiring | None | 5 new content types in review workflow |
| Source attribution | Implicit | `sourceIds` on every record; validated against registry |
