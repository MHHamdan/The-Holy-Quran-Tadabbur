import { describe, expect, it } from 'vitest';
import { formatRemaining, qiblaForLocation } from '../pages/tools/PrayerTimesPage';
import { qiblaBearing } from '../lib/qibla';

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

describe('qiblaForLocation', () => {
  it('gives no Qibla bearing for the Makkah stand-in (it is not the user position)', () => {
    expect(qiblaForLocation({ lat: 21.4225, lng: 39.8262, name: 'Makkah', source: 'makkah' })).toBeNull();
    expect(qiblaForLocation(null)).toBeNull();
  });

  it("computes the bearing from the user's own device position or chosen city", () => {
    const london = qiblaForLocation({ lat: 51.5074, lng: -0.1278, name: 'London', source: 'manual' });
    expect(london).not.toBeNull();
    expect(london!).toBeCloseTo(qiblaBearing(51.5074, -0.1278), 6);
    expect(london!).toBeGreaterThan(115);
    expect(london!).toBeLessThan(121);
    expect(qiblaForLocation({ lat: -6.2, lng: 106.8, name: 'Jakarta', source: 'device' })).not.toBeNull();
  });
});
