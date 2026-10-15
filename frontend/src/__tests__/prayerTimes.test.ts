import { describe, expect, it } from 'vitest';
import { formatRemaining } from '../pages/tools/PrayerTimesPage';

describe('formatRemaining (prayer countdown)', () => {
  it('uses Arabic plural forms and Arabic-Indic digits', () => {
    expect(formatRemaining(1, 0, true)).toBe('ساعة');
    expect(formatRemaining(2, 0, true)).toBe('ساعتان');
    expect(formatRemaining(9, 46, true)).toBe('٩ ساعات و٤٦ دقيقة');
    expect(formatRemaining(0, 5, true)).toBe('٥ دقائق');
    expect(formatRemaining(11, 0, true)).toBe('١١ ساعة');
  });

  it('keeps the compact English form', () => {
    expect(formatRemaining(9, 46, false)).toBe('9h 46m');
    expect(formatRemaining(0, 5, false)).toBe('5m');
  });
});
