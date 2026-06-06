/**
 * Related figures that are NOT prophets.
 *
 * These figures appear in the Quran and are tightly bound to prophetic
 * narratives, but they are NOT prophets in mainstream Sunni scholarship.
 * They appear in the Prophet Atlas only under each prophet's
 * `relatedPeopleOrNations` / `relatedEntities` arrays, never in the
 * 25-prophet list itself.
 *
 * Source: `docs/prophets-atlas-prophet-list-policy.md`.
 */

import type { ProphetRelatedFigure } from '../types/quranProphetAtlas';

export const QURAN_PROPHET_RELATED_FIGURES: ProphetRelatedFigure[] = [
  {
    figureId: 'figure_luqman',
    nameArabic: 'لقمان',
    nameEnglish: 'Luqman',
    policyReason: 'Granted wisdom by Allah (31:12). Prophethood is not asserted by the Quran.',
    ayahReferences: [
      { surahNumber: 31, ayahStart: 12, ayahEnd: 19 },
    ],
    disputed: true,
    disputeNotes:
      'Classical scholars differ: most consider Luqman a wise man (ḥakīm) granted wisdom, not a prophet. The Atlas does not assert prophethood.',
    relatedProphetIds: [],
  },
  {
    figureId: 'figure_dhulqarnayn',
    nameArabic: 'ذو القرنين',
    nameEnglish: 'Dhul-Qarnayn',
    policyReason: 'A righteous king empowered by Allah (18:83-98). Prophethood is not asserted by the Quran.',
    ayahReferences: [
      { surahNumber: 18, ayahStart: 83, ayahEnd: 98 },
    ],
    disputed: true,
    disputeNotes:
      'Classical scholars differ on identity and prophethood. The Atlas keeps Dhul-Qarnayn as a related figure only.',
    relatedProphetIds: [],
  },
  {
    figureId: 'figure_khidr',
    nameArabic: 'الخضر',
    nameEnglish: 'Al-Khidr',
    policyReason: 'A servant of Allah taught from divine knowledge (18:65-82). Prophethood is disputed; the Atlas does not assert it.',
    ayahReferences: [
      { surahNumber: 18, ayahStart: 65, ayahEnd: 82 },
    ],
    disputed: true,
    disputeNotes:
      'Some classical scholars consider Al-Khidr a prophet, others a righteous servant. The Atlas treats him as a related figure.',
    relatedProphetIds: ['prophet_musa'],
  },
  {
    figureId: 'figure_uzayr',
    nameArabic: 'عزير',
    nameEnglish: 'Uzayr (Ezra)',
    policyReason: 'Mentioned at 9:30 in the context of a refuted claim. Prophethood is disputed.',
    ayahReferences: [
      { surahNumber: 9, ayahStart: 30 },
    ],
    disputed: true,
    disputeNotes:
      'Classical scholars differ on whether Uzayr was a prophet. The Atlas does not assert prophethood.',
    relatedProphetIds: [],
  },
  {
    figureId: 'figure_maryam',
    nameArabic: 'مريم بنت عمران',
    nameEnglish: 'Maryam (Mary)',
    policyReason:
      'Highest woman in the Quran; mainstream Sunni view does not classify women as prophets in the messenger/rasul sense. The Atlas honours Maryam as a deeply revered figure tightly bound to the Zakariyya/Yahya/Isa narratives.',
    ayahReferences: [
      { surahNumber: 19, ayahStart: 16, ayahEnd: 36 },
      { surahNumber: 3, ayahStart: 35, ayahEnd: 47 },
    ],
    disputed: false,
    disputeNotes:
      'A minority view considers Maryam a prophet in a non-messenger sense; the Atlas follows the mainstream classification.',
    relatedProphetIds: ['prophet_isa', 'prophet_zakariyya'],
  },
  {
    figureId: 'figure_talut',
    nameArabic: 'طالوت',
    nameEnglish: 'Talut',
    policyReason: 'A king appointed for Bani Israel (2:247-249). Not a prophet.',
    ayahReferences: [
      { surahNumber: 2, ayahStart: 246, ayahEnd: 251 },
    ],
    disputed: false,
    disputeNotes: '',
    relatedProphetIds: ['prophet_dawud'],
  },
  {
    figureId: 'figure_jalut',
    nameArabic: 'جالوت',
    nameEnglish: 'Jalut (Goliath)',
    policyReason: 'The opposing king (2:249-251). Not a prophet.',
    ayahReferences: [
      { surahNumber: 2, ayahStart: 249, ayahEnd: 251 },
    ],
    disputed: false,
    disputeNotes: '',
    relatedProphetIds: ['prophet_dawud'],
  },
  {
    figureId: 'figure_bilqis',
    nameArabic: 'بلقيس (ملكة سبأ)',
    nameEnglish: 'Bilqis (Queen of Sheba)',
    policyReason: 'Queen of Sheba who accepted Sulayman\'s invitation (27:22-44). Not a prophet.',
    ayahReferences: [
      { surahNumber: 27, ayahStart: 22, ayahEnd: 44 },
    ],
    disputed: false,
    disputeNotes: '',
    relatedProphetIds: ['prophet_sulayman'],
  },
];

export const QURAN_PROPHET_RELATED_FIGURE_IDS = new Set(
  QURAN_PROPHET_RELATED_FIGURES.map((f) => f.figureId),
);
