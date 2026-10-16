import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { themeTranslations } from '../i18n/translations';

const STORIES = join(__dirname, '..', '..', '..', 'data', 'manifests', 'stories.json');

interface Manifest {
  stories?: { themes?: string[] }[];
  inter_story_connections?: { shared_theme?: string }[];
}

describe('story theme labels', () => {
  it('every story theme and connection shared_theme has a bilingual label (no raw ids like first_humans)', () => {
    const m = JSON.parse(readFileSync(STORIES, 'utf8')) as Manifest;
    const ids = new Set<string>();
    for (const s of m.stories ?? []) for (const t of s.themes ?? []) ids.add(t);
    for (const c of m.inter_story_connections ?? []) if (c.shared_theme) ids.add(c.shared_theme);
    expect(ids.size).toBeGreaterThan(50);
    const missing = [...ids].filter((id) => {
      const l = themeTranslations[id.toLowerCase()];
      return !l || !l.ar.trim() || !l.en.trim() || /[a-z]/i.test(l.ar);
    });
    expect(missing).toEqual([]);
  });
});
