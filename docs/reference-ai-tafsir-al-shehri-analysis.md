# Reference Analysis — AI and Quranic Tafsir
## Based on: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
### Prof. Dr. Abdulrahman Al-Shehri

**Analyzed for:** Tadabbur Al-Quran Platform  
**Analysis date:** 2026-05-05  
**Purpose:** Translate academic reference principles into platform architecture decisions

---

## 1. Key Principles Extracted

### 1.1 AI Is an Assistant, Not a Scholar
AI cannot replace the mufassir, mufti, or qualified human reviewer. Its role is to search, summarize, classify, simplify, and compare verified scholarly content — not to issue religious opinions or generate independent tafsir.

### 1.2 Tafsir Requires Evidence and Discipline
Quranic interpretation is a regulated religious science. Every claim requires a chain of evidence (isnad), scholarly authority, and methodological consistency. An AI output that lacks evidence attribution is disqualified from serving as tafsir regardless of how fluent it sounds.

### 1.3 Hallucination (الاختلاق) Is a Critical Danger
AI systems can:
- Fabricate ayah references (non-existent surah:ayah)
- Invent scholar names or book titles
- Misattribute quotes to wrong sources
- Generate fluent but theologically incorrect interpretations

These failures are invisible to most users and may spread as if authentic. The platform must prevent all of them at the technical level.

### 1.4 A Closed Trusted Corpus Is Safer Than General AI Memory
Open-ended AI queries answered from general training data are unsafe for Quranic content. A platform restricted to a curated, verified Quranic corpus (text, tafsir, vocabulary, morphology) — where AI only searches and summarizes — is far safer for public use.

### 1.5 Prompt Quality Determines Output Quality
The quality, precision, and constraints of prompts directly determine the safety and accuracy of AI outputs. Poorly constrained prompts produce more hallucination. The platform must maintain strict system prompts and never allow user prompts to override grounding constraints.

### 1.6 AI Must Be Supervised by Qualified Reviewers
All AI-assisted outputs on Quranic content must pass through a scholarly review workflow before reaching production display. Review status must be visible to users. Nothing marked `needs_review` should be presented as authoritative.

### 1.7 Scientific Miracle Claims Require Special Caution
The reference explicitly warns against forcing modern scientific theories onto Quranic ayahs. Such claims require both scholarly and scientific review and must not be presented as definitive tafsir.

---

## 2. AI Opportunities Identified in the Reference

| Opportunity | Arabic Term | Description |
|---|---|---|
| Vocabulary explanation | غريب القرآن | Explaining difficult or uncommon Quranic words |
| Morphology | التصريف | Word forms, roots, patterns |
| Grammatical analysis | الإعراب | Syntactic parsing of Quranic words |
| Tafsir summary | ملخص التفسير | Condensing long tafsir passages |
| Tafsir comparison | المقارنة التفسيرية | Comparing multiple scholars on one ayah |
| Thematic tafsir | التفسير الموضوعي | Grouping ayahs by theme (patience, mercy, etc.) |
| Contextual relations | المناسبة | Relationships between adjacent or connected ayahs |
| Asbab al-nuzul | أسباب النزول | Contexts of revelation (from verified sources) |
| Research assistance | مساعدة البحث | Organizing evidence for scholarly research |
| Children's Quran education | تعليم القرآن للأطفال | Age-appropriate Quranic learning content |
| Audio/video script | إعداد النص الإعلامي | Script drafts for media based on approved content |
| Multilingual outreach | التوعية متعددة اللغات | Translating and adapting approved content |
| UI/UX design support | دعم تصميم الواجهة | Improving platform usability |
| User feedback analysis | تحليل ملاحظات المستخدمين | Categorizing and responding to user reports |
| Marketing and analytics | التسويق والتحليلات | Audience engagement improvement |

---

## 3. AI Risks Identified in the Reference

| Risk | Severity | Mechanism |
|---|---|---|
| Hallucinated ayah references | Critical | AI invents surah:ayah pairs that don't exist |
| Invented source names | Critical | AI fabricates scholar names or book titles |
| Wrong attribution | Critical | AI assigns a quote to the wrong scholar |
| Unsupervised tafsir generation | Critical | AI produces tafsir from general knowledge without corpus |
| Fatwa-like answers | Critical | AI issues religious rulings it has no authority to give |
| Scientific miracle overclaiming | High | AI presents scientific theories as definitive Quranic truth |
| User over-reliance | High | Non-specialists treat AI output as scholarly authority |
| General AI tool use by public | High | Users query ChatGPT/etc. for tafsir without corpus restriction |
| Public cannot detect errors | High | Fluent hallucinations pass undetected by most readers |
| Unsupported thematic claims | Medium | AI invents theme groupings without source evidence |
| Translation treated as Quran | Medium | AI translation mistaken for the Arabic rasm |

---

## 4. Platform Design Implications

| Reference Principle | Tadabbur Platform Requirement |
|---|---|
| AI must not replace the mufassir | All RAG answers are labeled "AI-assisted summary, not independent tafsir" |
| Every claim requires evidence | Every RAG answer must cite source_id, author, and verse reference |
| Hallucination must be prevented | QuranAnswerGuard validates all ayah references and source IDs before display |
| Closed corpus is safer | SourceValidator blocks any answer citing unknown or unregistered sources |
| Prompt quality determines safety | System prompt in `rag/prompts.py` enforces strict grounding; never overridden by users |
| Scholarly review required | Review workflow (Phase 6) gates all story, KG, and tafsir content |
| Scientific claims need caution | Scientific miracle claims return special caution label and needs_review status |
| Fatwa must not be issued | Queries classified as fatwa_like are redirected with a refusal message |
| Translation must be labeled | All translation content carries translator field; never presented as Quran itself |
| Review status must be visible | UI shows human_review_required badge on all unreviewed content |

---

## 5. Gap Analysis

| Reference Principle | Current Platform Support | Gap | Priority | Suggested Implementation |
|---|---|---|---|---|
| AI is helper, not mufassir | RAG disclaimer exists in prompts | Disclaimer not consistently shown in UI | High | Add "AI-assisted summary" label to all RAG answer cards |
| Hallucination prevention | Citation validator + source validator | No ayah-reference validation (invented surah:ayah) | Critical | Implement `QuranAnswerGuard` in `backend/app/safety/` |
| Closed trusted corpus | Source registry + TRUSTED_SOURCE_IDS | Missing source categories: vocabulary, i'rab, morphology, asbab, munasabah | High | Add placeholder source entries; refuse queries requiring missing categories |
| Fatwa must be refused | Ruling intent → warning appended | No classifier detecting fatwa-like intent before RAG call | High | Add `QuestionTypeClassifier` with fatwa_like detection |
| Scientific miracle caution | None | No detection or special handling for scientific miracle queries | High | Add `scientific_miracle_claim` intent classification + caution label |
| Tafsir comparison | RAG retrieves multiple sources | No dedicated "compare tafsir" UI mode | Medium | Plan tafsir comparison mode in future phase |
| Thematic tafsir | Themes + KG exist | Themes not surfaced as a thematic tafsir module | Medium | Plan thematic tafsir enhancement (Phase I) |
| Vocabulary / غريب القرآن | Source registry has no vocabulary source | No vocabulary data or route | Medium | Create vocabulary module plan (Phase F) |
| I'rab / grammar | No i'rab data | No i'rab route or data | Medium | Create i'rab module plan (Phase G) |
| Morphology | No morphology data | No morphology route or data | Medium | Create morphology module plan (Phase H) |
| Munasabah | KG has some relations | KG relations are all needs_review; no dedicated munasabah policy | Medium | Create munasabah policy (Phase J) |
| Children's education | No kids mode | No age-appropriate content mode | Low | Plan kids learning mode (Phase N) |
| Media/script generation | None | No media content policy | Low | Create media policy (Phase O) |
| User feedback/reporting | None | No user feedback form | Low | Create feedback system (Phase P) |
| Review status visible | Stories + KG show badge | Admin quality dashboard lacks scientific/fatwa stats | Low | Enhance admin dashboard (Phase Q) |
| Multilingual outreach | Translation table exists | No multilingual content policy for AI-assisted content | Low | Create multilingual policy (Phase O) |

---

## 6. Immediate Action Items (Phase A Output)

The gap analysis identifies three **critical** items requiring immediate implementation:

### Critical-1: QuranAnswerGuard (Phase D)
Create `backend/app/safety/quran_answer_guard.py` to validate:
- Ayah references exist in the canonical 114-surah, 6236-ayah corpus
- Source IDs are in the trusted registry
- No fatwa-like answers pass without explicit refusal
- Scientific miracle claims return caution label
- Translation is always labeled, never presented as Quran

### Critical-2: Closed Corpus Policy Document (Phase B)
Create `docs/closed-corpus-quran-ai-policy.md` formalizing why general AI memory is unsafe and how the platform enforces a trusted corpus boundary.

### Critical-3: Source Category Gap
The source registry is missing entire categories required to support the reference's recommended AI use cases:
- vocabulary / غريب القرآن
- i'rab / الإعراب
- morphology / التصريف
- asbab al-nuzul / أسباب النزول
- munasabah / المناسبة
- qira'at / القراءات

These must be added as `status: planned` placeholder entries before any feature implementing these categories is built.

---

*This analysis document is static reference material. It does not contain Quranic text, tafsir, or AI-generated religious content.*
