import { describe, expect, it } from 'vitest';
import { placeLabel } from '../lib/islamicApis';

describe('placeLabel', () => {
  const geo = { latitude: 30, longitude: 31, displayName: 'Cairo, Cairo Governorate, Egypt', city: 'Cairo', country: 'Egypt' };

  it('joins city and country with the separator of the UI language', () => {
    expect(placeLabel(geo, 'en')).toBe('Cairo, Egypt');
    expect(placeLabel({ ...geo, city: 'القاهرة', country: 'مصر' }, 'ar')).toBe('القاهرة، مصر');
  });

  it('falls back to the first two parts of the display name', () => {
    expect(placeLabel({ ...geo, city: undefined }, 'en')).toBe('Cairo, Cairo Governorate');
  });
});
