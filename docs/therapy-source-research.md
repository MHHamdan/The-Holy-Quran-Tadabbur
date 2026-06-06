# Therapy Page — Source Research (2026-05-18)

Compiled from web research for the situation-atlas / ruqyah / crisis
layers. Every URL below is the canonical citation used by the therapy
backend.

---

## Quranic healing verses (shifaʾ)

Primary verses already in the Quran corpus (no text duplicated here —
the platform fetches Arabic from the DB):

| Reference | Theme |
|---|---|
| 17:82 | Quran as healing & mercy for believers |
| 10:57 | Healing for what is in the hearts |
| 41:44 | Quran as guidance and healing |

Citation source for tafsir interpretation:
[Tafsir Surah Yunus 10:57 — Quran.com / Maarif-ul-Quran](https://quran.com/en/10:57/tafsirs/en-tafsir-maarif-ul-quran).

## Authentic hadith on ruqyah / prophetic healing

| Hadith | Narrator | URL |
|---|---|---|
| Bukhari 5735 | ʿĀʾisha — Prophet ﷺ recited Mu'awwidhat (al-Falaq + an-Nas) and blew on himself during illness | https://sunnah.com/bukhari:5735 |
| Bukhari 5016 | ʿĀʾisha — Mu'awwidhat for sickness | https://sunnah.com/bukhari:5016 |
| Bukhari 5017 | ʿĀʾisha — al-Ikhlas + al-Falaq + an-Nas at bedtime | https://sunnah.com/bukhari:5017 |
| Bukhari 2276 | Abu Saʿid al-Khudri — Surah al-Fatihah ruqyah for snake/scorpion bite | https://sunnah.com/bukhari:2276 |
| Bukhari 5743 | Anas — Ruqyah of the Messenger: *Allahumma Rabban-naas, mudh-hibal ba's…* | https://sunnah.com/bukhari:5743 |
| Bukhari 5742 | Anas — variant of the same du'a | https://sunnah.com/bukhari:5742 |

Compilation index: [sunnah.com — Book of Medicine (76)](https://sunnah.com/bukhari/76);
[Book of Patients (75)](https://sunnah.com/bukhari/75).

## Crisis hotlines

| Region | Number | Source |
|---|---|---|
| United States | 988 (call, text, chat) | https://988lifeline.org |
| United Kingdom & Ireland | Samaritans — 116 123 | https://befrienders.org |
| Saudi Arabia | 920033360 — National Center for Mental Health Promotion | https://icarewellbeing.com/crisis-hotline-mental-health-uae/ |
| UAE / GCC directory | varies by country | https://icarewellbeing.com/crisis-hotline-mental-health-uae/ |
| International (175+ countries) | language + country search | https://findahelpline.com |
| Global directory | volunteer crisis lines | https://befrienders.org |
| Wikipedia index | for cross-check | https://en.wikipedia.org/wiki/List_of_suicide_crisis_lines |

## Muslim-specific mental-health resources

- **Khalil Center** — Islamic-integrated tele-therapy:
  https://khalilcenter.com (counseling services:
  https://khalilcenter.com/mental-health-services/counseling-services).
- **Naseeha Muslim Youth Helpline** — confidential phone/text/chat,
  referenced via https://muslimspace.org/mentalhealth.
- **Yaqeen Institute** — Islamic mental-health research:
  https://yaqeeninstitute.org/what-islam-says-about/islam-and-mental-health-and-wellness;
  *Responding to Suicide* podcast series:
  https://yaqeeninstitute.org/watch/series/responding-to-suicide-doubletake-podcast.
- **Institute for Muslim Mental Health** — suicide postvention summary:
  https://muslimmentalhealth.com/suicide-postvention-crisis-response-summary/.
- **Stanford Muslim Mental Health & Islamic Psychology Lab**:
  https://med.stanford.edu/mmhip/projects.html.
- **MARISTAN** — Muslim mental-health resources:
  https://maristan.org/resources/.

## Validation guarantees applied to the implementation

- Every situation-atlas entry cites either an existing tafsir-chunk
  source (via `source_id`) or one of the URLs above.
- Every ruqyah hadith cites a sunnah.com URL.
- Crisis classifier ships with a static hotline table derived from
  `findahelpline.com` + 988, Samaritans, KSA 920033360.
- Yaqeen / Khalil URLs are surfaced in the crisis banner as
  Muslim-specific fallback resources alongside the generic hotlines.
- Nothing here promotes a substitute-for-medical-care interpretation.
