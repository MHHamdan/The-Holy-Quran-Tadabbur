/**
 * Display helpers for the tafsir comparison attribution footer: bilingual
 * licence-class labels, the under-review marker rule, host-name link text and
 * one numeral style per UI language.
 */

/** One numeral style per UI language: Arabic-Indic digits in Arabic. */
export function formatCount(n: number, uiLanguage: 'ar' | 'en'): string {
  return n.toLocaleString(uiLanguage === 'ar' ? 'ar-EG' : 'en-US');
}

/**
 * Bilingual labels for the licence classes the API reports (license_type).
 * The full licence text is stored in English; the Arabic UI shows the class
 * label instead, and an unknown class falls back to the stored text.
 */
const LICENCE_LABELS: Record<string, { ar: string; en: string }> = {
  public_domain_classical: {
    ar: 'نص تراثي في الملك العام لقِدَمه',
    en: 'Classical text, public domain by age',
  },
  publisher_terms_non_commercial: {
    ar: 'بشروط الناشر: عرض غير تجاري مع نسبة المصدر',
    en: 'Publisher terms: attributed, non-commercial display',
  },
  creative_commons: { ar: 'رخصة المشاع الإبداعي', en: 'Creative Commons licence' },
  pending_verification: { ar: 'الترخيص لم يُتحقَّق منه بعد', en: 'Licence not yet verified' },
};

export function licenceLabel(
  licence: string | null | undefined,
  licenceType: string | null | undefined,
  uiLanguage: 'ar' | 'en',
): { text: string; lang: 'ar' | 'en' } | null {
  const mapped = licenceType ? LICENCE_LABELS[licenceType] : undefined;
  if (uiLanguage === 'ar' && mapped) return { text: mapped.ar, lang: 'ar' };
  if (licence) return { text: licence, lang: 'en' };
  if (mapped) return { text: mapped[uiLanguage], lang: uiLanguage };
  return null;
}

/**
 * A licence is shown as under review when the API says it is unverified, or
 * when its own text says the terms are still pending / not cleared.
 */
export function licenceUnderReview(licence: string | null | undefined, verified: boolean): boolean {
  return !verified || /pending|not cleared|unverified/i.test(licence ?? '');
}

/** Host name of a source URL, used as the link text instead of the raw URL. */
export function sourceHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url.replace(/^https?:\/\//, '').split('/')[0];
  }
}
