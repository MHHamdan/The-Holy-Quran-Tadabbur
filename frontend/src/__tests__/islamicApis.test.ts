import { describe, expect, it } from 'vitest';
import { coarsen, formatPrayerTime, getMetalPrices, manualMetalPrices, NO_LIVE_PRICES } from '../lib/islamicApis';

describe('coarsen (location privacy)', () => {
  it('rounds to 2 decimals (~1.1 km)', () => {
    expect(coarsen(21.422487)).toBe(21.42);
    expect(coarsen(39.826206)).toBe(39.83);
    expect(coarsen(-33.868820)).toBe(-33.87);
    expect(String(coarsen(21.422487))).not.toContain('21.4224');
  });
});

describe('metal prices', () => {
  it('never returns stale prices as if they were live', async () => {
    const prices = await getMetalPrices();
    expect(prices).toEqual(NO_LIVE_PRICES);
    expect(prices.source).toBe('unavailable');
    expect(prices.goldPerGram).toBe(0);
  });

  it('builds manual prices from what the user typed', () => {
    const p = manualMetalPrices(100, 1.2);
    expect(p.source).toBe('manual');
    expect(p.goldPerGram).toBe(100);
    expect(p.silverPerGram).toBe(1.2);
  });
});

describe('formatPrayerTime', () => {
  it('formats English 12-hour time', () => {
    expect(formatPrayerTime('05:15', false, 'en')).toBe('5:15 AM');
    expect(formatPrayerTime('17:05 (+03)', false, 'en')).toBe('5:05 PM');
  });

  it('formats Arabic with Arabic-Indic digits and no AM/PM', () => {
    const t = formatPrayerTime('05:15', false, 'ar');
    expect(t).toMatch(/[٠-٩]+:[٠-٩]+/);
    expect(t).toMatch(/[صم]/);
    expect(t).not.toMatch(/AM|PM/);
  });

  it('formats 24-hour time', () => {
    expect(formatPrayerTime('17:05', true, 'en')).toBe('17:05');
  });

  it('returns unparseable input unchanged', () => {
    expect(formatPrayerTime('n/a', false, 'en')).toBe('n/a');
  });
});
