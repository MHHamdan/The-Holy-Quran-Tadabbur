#!/usr/bin/env npx tsx
/**
 * Check frontend/src/utils/userWarnings.ts against the warnings that the
 * generated story / prophet / calls / asma data actually carries.
 *
 * - Known pipeline strings map to the expected user-facing code.
 * - Arabic output contains no Latin letters and no internal tokens.
 * - Every warning string found in the generated files the pages render is
 *   classified (unclassified ones would be silently dropped in production).
 *
 * Exit 0 on success, 1 on failure.
 */
import { readFileSync } from 'fs';
import { join, resolve } from 'path';
import { classifyWarning, isInternalWarning, toUserWarnings } from '../frontend/src/utils/userWarnings';

const ROOT = resolve(__dirname, '..');
const GEN = join(ROOT, 'frontend/src/data/generated');
const errors: string[] = [];

const SAMPLES: Array<[string, string]> = [
  ['From cluster_000012 (graph_community); needs_review.', 'inferred_link'],
  ['Generic alias — downgraded confidence.', 'inferred_link'],
  ['Low-confidence pattern match (0.55). Context review required.', 'inferred_link'],
  ['Story-world order is a navigation aid, not a chronology claim. Verified chronology requires scholarly source.', 'approx_order'],
  ['AI-assisted summary; needs scholarly review.', 'pending_review'],
  ['The Quran does not narrate this prophet in detail; this is a compact profile.', 'compact_profile'],
  ['Not in Quran as an explicit divine name; from hadith traditions.', 'not_quran_name'],
];
for (const [w, code] of SAMPLES) {
  const got = classifyWarning(w);
  if (got !== code) errors.push(`"${w}" -> ${got}, expected ${code}`);
}

// Files rendered by StoryAtlasPage, StoryAtlasConnectionsPage, ProphetJourneyPage,
// ProphetDetailPage, QuranicCallsAtlasPage and AsmaAllahDetailPage.
const FILES = [
  'quranStoryRegistry.json',
  'quranStoryConnections.json',
  'quranProphetsAtlas.json',
  'quranProphetStoryPages.json',
  'quranicCallsAtlas.json',
  'asmaAllahAtlas.json',
];
const seen = new Set<string>();
function walk(x: unknown): void {
  if (Array.isArray(x)) {
    x.forEach(walk);
  } else if (x && typeof x === 'object') {
    for (const [k, v] of Object.entries(x as Record<string, unknown>)) {
      if (k === 'warnings' && Array.isArray(v)) v.forEach((w) => typeof w === 'string' && seen.add(w));
      else walk(v);
    }
  }
}
for (const f of FILES) {
  try {
    walk(JSON.parse(readFileSync(join(GEN, f), 'utf-8')));
  } catch {
    errors.push(`cannot read ${f}`);
  }
}
const unclassified = [...seen].filter((w) => !classifyWarning(w) && !isInternalWarning(w));
if (unclassified.length) {
  errors.push(`${unclassified.length} warning strings are not classified, e.g. ${JSON.stringify(unclassified.slice(0, 5))}`);
}
const ar = toUserWarnings([...seen], 'ar', { showUnmatched: false });
for (const w of ar) {
  if (/[A-Za-z_]/.test(w.text)) errors.push(`Arabic user warning contains Latin text: ${w.text}`);
}

if (errors.length) {
  console.error('userWarnings checks FAILED:');
  for (const e of errors) console.error('  -', e);
  process.exit(1);
}
console.log(`userWarnings checks passed: ${seen.size} distinct warnings classified into ${new Set(ar.map((w) => w.code)).size} codes.`);
