import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { LocationFallback, locationProblemOf } from '../pages/tools/LocationFallback';
import { minutesInTimeZone } from '../pages/tools/PrayerTimesPage';

const purpose = { ar: 'غرض', en: 'Purpose' };
const noop = () => {};

describe('LocationFallback (geolocation denied / unavailable)', () => {
  it('maps W3C geolocation error codes', () => {
    expect(locationProblemOf({ code: 1 })).toBe('denied');
    expect(locationProblemOf({ code: 2 })).toBe('unavailable');
    expect(locationProblemOf({ code: 3 })).toBe('timeout');
    expect(locationProblemOf(new Error('Geolocation is not supported'))).toBe('unsupported');
    expect(locationProblemOf(null)).toBe('unsupported');
  });

  it('offers a city search and a retry, in English', () => {
    const html = renderToStaticMarkup(
      <LocationFallback isArabic={false} problem="denied" purpose={purpose} onChoose={noop} onRetry={noop} />
    );
    expect(html).toContain('Location access was denied');
    expect(html).toContain('Search for a city');
    expect(html).toContain('Try my location again');
    expect(html).toContain('dir="ltr"');
    // Makkah is never offered unless the page asks for it, and never applied silently.
    expect(html).not.toContain('Makkah');
  });

  it('renders Arabic copy right-to-left, with the explicit Makkah choice when offered', () => {
    const html = renderToStaticMarkup(
      <LocationFallback isArabic problem="timeout" purpose={purpose} onChoose={noop} onRetry={noop} onUseMakkah={noop} />
    );
    expect(html).toContain('dir="rtl"');
    expect(html).toContain('اختر موقعك');
    expect(html).toContain('ابحث عن مدينة');
    expect(html).toContain('استخدم مكة المكرمة مؤقتاً');
    expect(html).not.toMatch(/Search for a city|Location access/);
  });
});

describe('minutesInTimeZone (countdown uses the prayer location clock)', () => {
  const t = new Date('2026-01-15T12:30:00Z');
  it('converts to the location time zone', () => {
    expect(minutesInTimeZone(t, 'Asia/Riyadh')).toBe(15 * 60 + 30);
    expect(minutesInTimeZone(t, 'UTC')).toBe(12 * 60 + 30);
    expect(minutesInTimeZone(t, 'America/New_York')).toBe(7 * 60 + 30);
  });
  it('falls back to the device clock for an unknown zone', () => {
    expect(minutesInTimeZone(t, 'Not/AZone')).toBe(t.getHours() * 60 + t.getMinutes());
    expect(minutesInTimeZone(t, undefined)).toBe(t.getHours() * 60 + t.getMinutes());
  });
});
