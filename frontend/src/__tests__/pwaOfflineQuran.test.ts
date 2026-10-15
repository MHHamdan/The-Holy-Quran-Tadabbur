import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const FRONTEND = join(__dirname, '..', '..');

describe("PWA precache of the bundled Qur'an text", () => {
  it('workbox globPatterns include public/offline-quran/*.json', () => {
    const cfg = readFileSync(join(FRONTEND, 'vite.config.ts'), 'utf8');
    const m = /globPatterns:\s*\[([^\]]*)\]/.exec(cfg);
    expect(m).not.toBeNull();
    expect(m![1]).toContain("'offline-quran/*.json'");
  });

  it('every offline-quran file fits the 2 MiB workbox per-file precache limit', () => {
    const dir = join(FRONTEND, 'public', 'offline-quran');
    const files = readdirSync(dir).filter((n) => n.endsWith('.json'));
    expect(files.length).toBe(115); // manifest + 114 surahs
    for (const f of files) expect(statSync(join(dir, f)).size).toBeLessThan(2 * 1024 * 1024);
  });
});
