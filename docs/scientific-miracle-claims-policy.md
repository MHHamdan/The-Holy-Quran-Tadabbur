# Scientific Miracle Claims Policy

**Platform:** Tadabbur Al-Quran  
**Phase:** K — Scientific Miracle Safety Audit  
**Effective:** Phase K implementation  
**Reference:** "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي" — Prof. Dr. Abdulrahman Al-Shehri

---

## Scope

This policy governs how the platform handles queries and AI-generated answers that assert
or explore connections between Quranic verses and modern scientific theories.

---

## The Problem

The Quran is the primary source of Islamic theology. Modern AI models, when asked to connect
Quranic verses to scientific theories, may:

- Assert a **definitive causal or semantic link** between a verse and a theory that is
  contested by scholars
- Present a **contemporary reflection** as if it were an established tafsir position
- Generate text that implies the Quran "proves" or "predicted" a specific scientific theory,
  which conflates distinct epistemological domains (revelation and empirical science)

This is not a question of whether Islam and science are compatible — it is a question of
**scholarly rigour**: asserting definitiveness where scholars disagree is itself a form of
intellectual harm.

---

## Classification (Pre-Generation Gate)

The `QuranQuestionClassifier` detects scientific miracle queries and returns:

```python
intent = "scientific_miracle_claim"
allowed_to_generate = True   # not hard-blocked at input
caution_required = True      # platform must attach caution
```

Detected patterns include (non-exhaustive):

| Language | Example patterns |
|---|---|
| English | "does the Quran prove", "scientific miracle", "expanding universe", "mountains as pegs", "embryology", "big bang" |
| Arabic | "الإعجاز العلمي", "يثبت العلم", "علم الأجنة", "توسع الكون", "الجبال أوتاد", "هل القرآن يثبت" |

---

## Validation (Post-Generation Guard)

The `QuranAnswerGuard` applies two distinct checks to scientific content:

### 5a. Definitive Claim Hard-Block

Phrases that assert a **definitive link** between a verse and a scientific theory are
**hard-blocked** (answer is replaced with a safe refusal, not returned to the user):

```
"this verse proves modern science"
"the quran definitively refers to"
"science has confirmed the tafsir"
"proves the big bang"
"definitively proves"
"تثبت هذه الآية نظرية"
"يثبت القرآن نظرية"
"أثبت العلم صحة تفسير"
```

When triggered, `GuardResult.passed = False` and `hard_block_reason` contains a bilingual
explanation. The caller must substitute a safe refusal response.

### 5b. Soft Scientific Content — Mandatory Caution Labels

Answers that mention scientific terminology without making a definitive claim are **allowed**
but must carry mandatory labels and bilingual warnings:

**Required labels:**
- `scientific_reflection_needs_review`
- `needs_scholarly_and_scientific_review`
- `contemporary_reflection_not_tafsir`

**Bilingual warning (attached to response):**

> EN: "Connecting an ayah to scientific theories requires specialized scholarly and scientific
> review. This is presented as a contemporary reflection, not a definitive tafsir position."
>
> AR: "الربط بين الآية والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة.
> هذا الطرح تأمل معاصر وليس موقفًا تفسيريًا قطعيًا."

---

## Frontend Display

When `scientific_reflection_needs_review` is in `required_labels`, or when the `intent` is
`scientific_miracle_claim`, the UI **must** display the `ScientificCautionCard` component:

- **Color:** orange (`border-orange-300`, `bg-orange-50`)
- **Icon:** FlaskConical (lucide-react)
- **Visibility:** always visible — **cannot be hidden behind expand/collapse**
- **Position:** before the generic answer card
- **Text:** sourced from `t('scientific_caution_title', language)` and
  `t('scientific_caution_body', language)`

The caution card is distinct from the generic amber warning box. It appears alongside (not
instead of) other validation warnings.

---

## What Is Not Blocked

This policy does not block:

- Historical accounts of scholars reflecting on scientific themes in the Quran, properly
  attributed and labeled as `contemporary_reflection_not_tafsir`
- Questions about the Quran's themes of nature, creation, or the cosmos when framed as
  tafsir (not as scientific proof)
- Asking what classical scholars said about a verse, even if the verse touches on natural
  phenomena

---

## Scholarly Review Requirement

Any answer with `scientific_reflection_needs_review` must enter the scholarly review workflow
(Phase 6) before it can be marked as `approved`. The `needs_review` status is set
automatically; no manual intervention is needed to add the flag.

---

## References

- `backend/app/safety/quran_question_classifier.py` — pre-generation gate
- `backend/app/safety/quran_answer_guard.py` — post-generation guard
- `frontend/src/components/ask/ChatMessage.tsx` — `ScientificCautionCard`
- `frontend/src/pages/tools/PromptGuidePage.tsx` — public-facing guide
- `docs/closed-corpus-quran-ai-policy.md` — parent content policy
- `docs/reference-ai-tafsir-al-shehri-analysis.md` — academic reference
