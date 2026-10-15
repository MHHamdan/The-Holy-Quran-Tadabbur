# Content rating answers (draft for owner review)

Draft answers for the Google Play IARC questionnaire and the App Store age
rating, derived from the app as of 2026-10-14. The owner submits the final
answers; items marked **OWNER DECISION** are not settled here.

## App summary for the questionnaires

- Category: Books / Education (reference). Free, no ads, no in-app purchases,
  no accounts (`docs/distribution-policy.md`).
- Content: the Qur'an text (Tanzil), classical Arabic tafsir, translations of
  the meanings, Qur'anic stories and study tools.
- AI features: an assistant that answers questions **only from cited tafsir
  sources** and refuses when no source is available; a spiritual-guidance
  feature that suggests verses for a described feeling. Both run on the server
  through Hugging Face; neither shows content from other users.
- Users cannot message or see each other. Feedback goes to the developer only.

## Google Play (IARC)

| Question | Draft answer |
|---|---|
| Violence, blood, gore | No. (Qur'anic narratives mention events such as battles or the flood as text, without depiction.) |
| Sexual content or nudity | No |
| Profanity or crude humour | No |
| Controlled substances (drugs, alcohol, tobacco) | No promotion. Rulings mentioned in source texts appear as text only. |
| Gambling or simulated gambling | No |
| Fear / horror | No |
| Users can interact or exchange content | No |
| Shares the user's location with other users | No |
| Allows purchases of digital goods | No |
| Unrestricted internet access (web browser) | No |
| Generative AI | **Yes**: text answers grounded in cited sources. Users report problems through the feedback button (category "inappropriate"). |

## App Store age rating

| Item | Draft answer |
|---|---|
| Cartoon or fantasy violence | None |
| Realistic violence | None |
| Sexual content / nudity | None |
| Profanity or crude humour | None |
| Alcohol, tobacco or drug use or references | None |
| Mature or suggestive themes | None |
| Horror / fear themes | None |
| Medical or treatment information | **OWNER DECISION**: the guidance feature offers spiritual support, not treatment, and points to professional help in crisis wording. Answer "Infrequent/Mild" if Apple's reviewer could read it as health advice, otherwise "None". |
| Gambling / contests | None |
| Unrestricted web access | No |
| User-generated content shown to others | No |

**OWNER DECISION — age rating:** 4+ fits the content, but App Store review may
ask for a higher rating for an app with an open-ended AI chat. Choose 4+ or 9+
(or the corresponding bracket in the current questionnaire) after reviewing
the assistant's refusal behaviour.

## Not claimed anywhere in store copy

- That the AI gives religious rulings (fatwa) or is a scholarly authority.
- Any endorsement by a scholar, institution or the King Fahd Complex.
