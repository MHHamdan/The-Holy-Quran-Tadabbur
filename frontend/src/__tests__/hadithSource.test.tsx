import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  HadithPendingReviewNote,
  hadithSourceLine,
  hasVerifiableHadithSource,
} from '../components/therapy/hadithSource';

describe('hasVerifiableHadithSource', () => {
  it('needs both a collection and a number', () => {
    expect(hasVerifiableHadithSource(undefined)).toBe(false);
    expect(hasVerifiableHadithSource({ collection: 'Sahih Muslim' })).toBe(false);
    expect(hasVerifiableHadithSource({ number: '918' })).toBe(false);
    expect(hasVerifiableHadithSource({ collection: '  ', number: '918' })).toBe(false);
    expect(hasVerifiableHadithSource({ collection: 'Sahih Muslim', number: '' })).toBe(false);
    expect(hasVerifiableHadithSource({ collection: 'Sahih Muslim', number: '918' })).toBe(true);
    expect(hasVerifiableHadithSource({ collection: 'Sahih Muslim', number: 918 })).toBe(true);
  });
});

describe('hadithSourceLine', () => {
  it('shows a grade only when the grader is named', () => {
    expect(hadithSourceLine({ collection: 'Abu Dawud', number: '1', grade: 'sahih' })).toBe('Abu Dawud 1');
    expect(hadithSourceLine({ collection: 'Abu Dawud', number: '1', grade: 'sahih', grader: 'X' }))
      .toBe('Abu Dawud 1 · sahih — X');
  });
});

describe('HadithPendingReviewNote', () => {
  it('renders Arabic right-to-left and English left-to-right', () => {
    const ar = renderToStaticMarkup(<HadithPendingReviewNote isRtl />);
    const en = renderToStaticMarkup(<HadithPendingReviewNote isRtl={false} />);
    expect(ar).toContain('dir="rtl"');
    expect(ar).toContain('يتحقق منها أهل الاختصاص');
    expect(en).toContain('dir="ltr"');
    expect(en).toContain('hidden until a scholar verifies');
  });
});

// Free-text hadith in these views has no reviewed collection + number, so the
// views must render it only behind hasVerifiableHadithSource.
describe('therapy views gate free-text hadith', () => {
  const SRC = join(__dirname, '..');
  const files: Array<[string, RegExp]> = [
    ['pages/EmotionalGuidancePage.tsx', /selected\.hadith(Ar|En)/],
    ['components/therapy/RuqyahGuide.tsx', /chapter\.hadith_(ar|en)/],
    ['components/therapy/DailyPracticesPanel.tsx', /p\.benefit_(ar|en)/],
  ];
  for (const [file, use] of files) {
    it(`${file} renders hadith text only after the provenance check`, () => {
      const text = readFileSync(join(SRC, file), 'utf8');
      const firstUse = text.search(use);
      const gate = text.indexOf('hasVerifiableHadithSource(');
      expect(firstUse).toBeGreaterThan(-1);
      expect(gate).toBeGreaterThan(-1);
      expect(gate).toBeLessThan(firstUse);
    });
  }
  it('no Hadith Qudsi citation is left in the guidance prose', () => {
    const text = readFileSync(join(SRC, 'pages/EmotionalGuidancePage.tsx'), 'utf8');
    for (const line of text.split('\n').filter((l) => l.includes('quranResponse'))) {
      expect(line).not.toMatch(/Bukhari|Muslim \d|Tirmidhi|البخاري|مسلم \d|الترمذي/);
    }
  });
});
