import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { translations } from '../i18n/translations';

const SRC = join(__dirname, '..');

/** Keys still referenced on this branch whose caller is removed by another
 *  workstream. therapy_intro_verse: the paraphrased "verse" was deleted from
 *  translations.ts; WS3 replaces its TherapyPage caller with the canonical
 *  17:82 (LiveVerse). Delete this entry once WS3's TherapyPage is merged. */
const PENDING_REMOVAL = new Set(['therapy_intro_verse']);

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) return name === '__tests__' ? [] : sourceFiles(p);
    return /\.(ts|tsx)$/.test(name) ? [p] : [];
  });
}

describe('translation keys', () => {
  it("every literal t('key') used in src exists in translations.ts", () => {
    const missing: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const text = readFileSync(file, 'utf8');
      for (const m of text.matchAll(/\bt\(\s*['"]([A-Za-z0-9_.]+)['"]/g)) {
        const key = m[1];
        if (!(key in translations) && !PENDING_REMOVAL.has(key)) {
          missing.push(`${file.slice(SRC.length + 1)}: ${key}`);
        }
      }
    }
    expect(missing).toEqual([]);
  });
});
