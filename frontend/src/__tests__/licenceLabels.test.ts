import { describe, expect, it } from 'vitest';
import {
  formatCount,
  licenceLabel,
  licenceUnderReview,
  sourceHost,
} from '../components/tafseer/licenceLabels';

const PD = 'Classical Islamic text - public domain due to age (310 AH)';
const KFGQPC =
  'King Fahd Complex: attributed, non-commercial display under docs/distribution-policy.md; KFGQPC terms pending owner confirmation, not cleared';

describe('tafsir comparison licence labels', () => {
  it('shows an Arabic label for known licence classes in the Arabic UI', () => {
    const l = licenceLabel(PD, 'public_domain_classical', 'ar');
    expect(l?.lang).toBe('ar');
    expect(l?.text).not.toMatch(/[A-Za-z]/);
    const k = licenceLabel(KFGQPC, 'publisher_terms_non_commercial', 'ar');
    expect(k?.text).not.toMatch(/[A-Za-z]/);
  });

  it('keeps the full stored licence text in the English UI', () => {
    expect(licenceLabel(PD, 'public_domain_classical', 'en')).toEqual({ text: PD, lang: 'en' });
  });

  it('falls back to the stored text for an unknown class', () => {
    expect(licenceLabel('Custom terms', 'something_new', 'ar')).toEqual({ text: 'Custom terms', lang: 'en' });
    expect(licenceLabel(null, null, 'ar')).toBeNull();
  });

  it('marks unverified or pending licences as under review', () => {
    expect(licenceUnderReview(PD, true)).toBe(false);
    expect(licenceUnderReview(PD, false)).toBe(true);
    // The text itself says the terms are not cleared, even if the flag is true.
    expect(licenceUnderReview(KFGQPC, true)).toBe(true);
  });

  it('uses the host name as link text', () => {
    expect(
      sourceHost('https://huggingface.co/datasets/riotu-lab/Quran-Tafseers/blob/9ddb/Tafseer.json'),
    ).toBe('huggingface.co');
    expect(sourceHost('https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/x')).toBe('cdn.jsdelivr.net');
  });

  it('formats counts with Arabic-Indic digits in Arabic', () => {
    expect(formatCount(6858, 'ar')).toMatch(/^[٠-٩٬]+$/);
    expect(formatCount(6858, 'en')).toBe('6,858');
  });
});
