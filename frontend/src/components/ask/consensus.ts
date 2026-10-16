/**
 * The API's scholarly_consensus is a fixed English phrase or a stored label
 * (tafseer_chunks.scholarly_consensus: agreed | majority | disputed). Show it in
 * the UI language; unknown English text is not shown in the Arabic UI.
 */
const CONSENSUS_LABELS: Record<string, { ar: string; en: string }> = {
  'direct tafsir lookup - no synthesis required': {
    ar: 'نصوص التفسير معروضة كما هي، دون تلخيص',
    en: 'Tafsir passages shown as written, without a summary',
  },
  direct_lookup: {
    ar: 'نصوص التفسير معروضة كما هي، دون تلخيص',
    en: 'Tafsir passages shown as written, without a summary',
  },
  agreed: { ar: 'متفق عليه بين المفسرين المستشهد بهم', en: 'Agreed among the cited commentators' },
  majority: { ar: 'قول أكثر المفسرين المستشهد بهم', en: 'Held by most of the cited commentators' },
  disputed: { ar: 'محل خلاف بين المفسرين', en: 'Disputed among the commentators' },
};

export function consensusLabel(value: string | null | undefined, language: 'ar' | 'en'): string | null {
  if (!value) return null;
  const known = CONSENSUS_LABELS[value.trim().toLowerCase()];
  if (known) return known[language];
  if (language === 'ar' && !/[\u0600-\u06FF]/.test(value)) return null;
  return value;
}
