import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { tafsirMethodLabel } from '../i18n/translations';

const MANIFEST = join(__dirname, '../../../data/manifests/tafseer_sources.json');

describe('tafsirMethodLabel', () => {
  it('labels every methodology token used by the tafsir manifest, in both languages', () => {
    const tokens = new Set(
      [...readFileSync(MANIFEST, 'utf8').matchAll(/"methodology"\s*:\s*"([a-z_]+)"/g)].map((m) => m[1]),
    );
    expect(tokens.size).toBeGreaterThan(0);
    for (const token of tokens) {
      const ar = tafsirMethodLabel(token, 'ar');
      const en = tafsirMethodLabel(token, 'en');
      expect(ar, token).toBeTruthy();
      expect(en, token).toBeTruthy();
      expect(ar).not.toContain('_');
      expect(en).not.toContain('_');
    }
  });

  it('never returns a raw token', () => {
    expect(tafsirMethodLabel('some_new_token', 'ar')).toBeNull();
    expect(tafsirMethodLabel(undefined, 'en')).toBeNull();
  });
});
