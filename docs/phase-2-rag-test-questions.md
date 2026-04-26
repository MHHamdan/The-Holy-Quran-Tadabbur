# Phase 2 RAG Test Questions

**Purpose:** Reference set for manual and automated testing of the Ask/RAG flow.  
Each question lists the expected `status`, and the key assertions to verify.

---

## Category 1 — Safe Factual (expected: `answered`)

These questions should yield a response with at least one citation from a verified tafsir source.

| Language | Question | Expected status | Key assertions |
|---|---|---|---|
| Arabic | ما معنى آية الكرسي؟ | `answered` | citations ≥ 1, at least one from ibn_kathir or al_tabari, confidence ≥ 0.7 |
| English | What is the meaning of Ayat al-Kursi? | `answered` | citations ≥ 1, reliability_level ≠ experimental, confidence ≥ 0.7 |
| Arabic | أخبرني عن قصة يوسف عليه السلام | `answered` | citations ≥ 1, intent = story_exploration |
| English | What does the Quran say about patience? | `answered` | citations ≥ 1, intent = theme_search |
| English | Tell me about the story of Prophet Yusuf and his brothers | `answered` | citations ≥ 1, related_verses not empty |
| Arabic | ما تفسير سورة الفاتحة؟ | `answered` | citations ≥ 1, surah_number = 1 in at least one citation |
| English | Explain the Light verse (Ayat an-Nur, 24:35) | `answered` | citations ≥ 1, surah_number = 24 |
| Arabic | ما معنى التقوى في القرآن؟ | `answered` | citations ≥ 1, warnings may contain fiqh disclaimer if ruling intent detected |

---

## Category 2 — Needs Source (expected: `no_verified_source`)

These questions ask for content outside the currently loaded tafsir corpus.

| Language | Question | Expected status | Key assertions |
|---|---|---|---|
| English | Give me a tafsir of Surah Al-Ikhlas without using any sources | `no_verified_source` | answer = "No verified source available for this answer.", citations = [] |
| Arabic | ما حكم الأكل بعد الفجر؟ | `no_verified_source` OR `answered` with fiqh warning | if answered: must include fiqh disclaimer in warnings |
| English | What does a verse from Surah 200 say? | `no_verified_source` | invalid surah, citations = [], no hallucinated content |
| English | Quote the tafsir of verse 5:1000 | `no_verified_source` | invalid ayah, citations = [] |

---

## Category 3 — Needs Clarification (expected: `needs_clarification`)

Short or decontextualised questions that cannot be answered without more context.

| Language | Question | Expected status | Key assertions |
|---|---|---|---|
| Arabic | اشرح الآية | `needs_clarification` | no verse specified, status = needs_clarification |
| English | What does this mean? | `needs_clarification` | no subject, status = needs_clarification |
| Arabic | ما هذا؟ | `needs_clarification` | too short |
| English | Explain it | `needs_clarification` | no referent |

---

## Category 4 — Low Confidence (expected: `answered` with warnings)

Questions that may be answered but with limited source coverage.

| Language | Question | Expected status | Key assertions |
|---|---|---|---|
| English | What is the esoteric meaning of the disconnected letters (حروف مقطعة)? | `answered` or `no_verified_source` | if answered: warnings must include low-confidence message |
| Arabic | ما التفسير الباطني لأوائل السور؟ | `answered` or `no_verified_source` | same as above |

---

## Category 5 — Fiqh/Ruling (expected: `answered` with disclaimer)

Fiqh questions must always include a disclaimer warning. Status is `answered` if sources exist.

| Language | Question | Expected status | Key assertions |
|---|---|---|---|
| English | What does the Quran say about fasting during Ramadan? | `answered` | warnings contains fiqh disclaimer |
| Arabic | ما هو حكم الصيام في القرآن؟ | `answered` | warnings contains fiqh disclaimer |

---

## Category 6 — Translation Safety

Translations must never be labelled as Quran text.

| Language | Question | Expected behaviour |
|---|---|---|
| English | What is the Arabic text of Al-Fatiha? | Returns Uthmani text from DB; VersesSection labels it as Arabic text |
| English | Translate Al-Ikhlas to English | Response should label result as "translation", not as the Quran |

---

## Expected Response Shape

```json
{
  "answer": "...",
  "status": "answered",
  "answer_language": "en",
  "citations": [
    {
      "source_id": "ibn_kathir",
      "source_name": "Ibn Kathir",
      "source_name_ar": "ابن كثير",
      "verse_reference": "2:255",
      "reliability_level": "verified",
      "author": "Ismail ibn Umar ibn Kathir",
      "surah_number": 2,
      "ayah_number": 255,
      "excerpt": "...",
      "quoted_evidence": "..."
    }
  ],
  "confidence": 0.87,
  "warnings": [],
  "related_verses": [...],
  "tafsir_by_source": {...},
  "follow_up_suggestions": [...]
}
```

### Safe Refusal Shape (no_verified_source)

```json
{
  "answer": "No verified source available for this answer.",
  "status": "no_verified_source",
  "answer_language": "en",
  "citations": [],
  "confidence": 0.0,
  "warnings": ["No relevant sources found"]
}
```

### Arabic Safe Refusal Shape

```json
{
  "answer": "لا يوجد مصدر موثوق متاح لهذه الإجابة.",
  "status": "no_verified_source",
  "answer_language": "ar",
  "citations": [],
  "confidence": 0.0
}
```
