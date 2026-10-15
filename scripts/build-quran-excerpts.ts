/**
 * Build frontend/src/data/generated/quranExcerpts.json from the canonical text.
 *
 * Content that quotes the Qur'an (stories, guidance cards, quizzes, adhkar)
 * must never carry hand-typed Qur'an text. It refers to a passage by key and
 * renders quranExcerpt(key) (frontend/src/utils/quranExcerpt.ts), whose text
 * this script copies verbatim from data/raw/quran_tanzil.json.
 *
 * Keys (collected from every quranExcerpt('...') call under frontend/src):
 *   's:a'           one whole verse
 *   's:a-b'         consecutive verses of one surah, joined by a space
 *   's:a#w1-w2'     words w1..w2 (1-based, inclusive) of one verse
 *   's:a#w1-'       word w1 to the end of the verse
 * Words are the whitespace-separated tokens of the Tanzil simple text
 * (aya_text_emlaey), the vowelled imla'i script these excerpts appear in.
 * Pause-mark tokens at either edge of an excerpt are dropped.
 *
 * The Tanzil copyright notice is copied into the output, as its licence
 * requires for files containing a portion of the text.
 *
 * Usage:
 *   npx tsx scripts/build-quran-excerpts.ts          # write the file
 *   npx tsx scripts/build-quran-excerpts.ts --check  # exit 1 if it is stale
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, resolve, extname } from 'path';

const ROOT = resolve(__dirname, '..');
const TANZIL = join(ROOT, 'data/raw/quran_tanzil.json');
const SRC = join(ROOT, 'frontend/src');
const OUT = join(ROOT, 'frontend/src/data/generated/quranExcerpts.json');

const KEY_CALL = /quranExcerpt\(\s*['"`](\d{1,3}:\d{1,3}(?:-\d{1,3})?(?:#\d{1,3}-(?:\d{1,3})?)?)['"`]\s*\)/g;
const PAUSE_ONLY = /^[ۖ-ۭ۞۩]+$/;

interface Verse {
  sura_no: number;
  aya_no: number;
  aya_text: string;
  aya_text_emlaey: string;
}

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name === 'generated') continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (['.ts', '.tsx'].includes(extname(p))) out.push(p);
  }
  return out;
}

export function collectKeys(files: string[]): string[] {
  const keys = new Set<string>();
  for (const f of files) {
    for (const m of readFileSync(f, 'utf-8').matchAll(KEY_CALL)) keys.add(m[1]);
  }
  return [...keys].sort((a, b) => a.localeCompare(b, 'en', { numeric: true }));
}

function trimPause(tokens: string[]): string[] {
  let a = 0;
  let b = tokens.length;
  while (a < b && PAUSE_ONLY.test(tokens[a])) a++;
  while (b > a && PAUSE_ONLY.test(tokens[b - 1])) b--;
  return tokens.slice(a, b);
}

export function resolveKey(key: string, verses: Map<string, Verse>): string {
  const m = /^(\d+):(\d+)(?:-(\d+))?(?:#(\d+)-(\d+)?)?$/.exec(key);
  if (!m) throw new Error(`Malformed excerpt key: ${key}`);
  const sura = Number(m[1]);
  const start = Number(m[2]);
  const end = m[3] ? Number(m[3]) : start;
  const get = (a: number) => {
    const v = verses.get(`${sura}:${a}`);
    if (!v) throw new Error(`Excerpt key ${key}: no verse ${sura}:${a}`);
    return v;
  };
  if (m[4]) {
    if (end !== start) throw new Error(`Excerpt key ${key}: word ranges apply to one verse only`);
    const tokens = get(start).aya_text_emlaey.split(/\s+/);
    const w1 = Number(m[4]);
    const w2 = m[5] ? Number(m[5]) : tokens.length;
    if (w1 < 1 || w2 < w1 || w2 > tokens.length) {
      throw new Error(`Excerpt key ${key}: verse has ${tokens.length} words`);
    }
    return trimPause(tokens.slice(w1 - 1, w2)).join(' ');
  }
  const parts: string[] = [];
  for (let a = start; a <= end; a++) parts.push(get(a).aya_text_emlaey);
  return parts.join(' ');
}

function build(): string {
  const tanzil = JSON.parse(readFileSync(TANZIL, 'utf-8'));
  const verses = new Map<string, Verse>(
    (tanzil.verses as Verse[]).map((v) => [`${v.sura_no}:${v.aya_no}`, v]),
  );
  const keys = collectKeys(walk(SRC));
  const excerpts: Record<string, string> = {};
  for (const key of keys) excerpts[key] = resolveKey(key, verses);
  const payload = {
    _generated: 'By scripts/build-quran-excerpts.ts from data/raw/quran_tanzil.json. Do not edit by hand.',
    script: 'Tanzil Quran Text (Simple, Version 1.1): aya_text_emlaey, verbatim',
    quranTextCopyright: tanzil.copyright.simple,
    quranTextAttribution: tanzil.copyright.attribution,
    count: keys.length,
    excerpts,
  };
  return `${JSON.stringify(payload, null, 2)}\n`;
}

function main(): void {
  const content = build();
  if (process.argv.includes('--check')) {
    const current = existsSync(OUT) ? readFileSync(OUT, 'utf-8') : '';
    if (current !== content) {
      console.error(`${OUT} is stale: run npx tsx scripts/build-quran-excerpts.ts`);
      process.exit(1);
    }
    console.log('quranExcerpts.json is up to date');
    return;
  }
  writeFileSync(OUT, content, 'utf-8');
  console.log(`Wrote ${JSON.parse(content).count} excerpts to ${OUT}`);
}

if (require.main === module) main();
