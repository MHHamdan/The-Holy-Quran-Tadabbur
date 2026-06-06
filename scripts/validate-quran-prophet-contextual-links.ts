#!/usr/bin/env npx tsx
/**
 * Phase X2 — Validate quranProphetContextualLinks.json.
 *
 * Hard checks:
 *   - Every link has ≥ 1 evidenceReferences entry.
 *   - All reviewStatus values are exactly "needs_review".
 *   - All humanReviewRequired values are exactly true.
 *   - All sourceIds are in the trusted allow-list.
 *   - Every surahNumber is 1..114 and ayahStart ≥ 1.
 *   - Link types are in the allowed set.
 *   - No prophet appears as a contextual link target that is not in
 *     the prophet seeds.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_PROPHET_BY_ID } from '../frontend/src/data/quranProphetSeeds';

const ROOT = resolve(__dirname, '..');
const LINKS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetContextualLinks.json');

const ALLOWED_LINK_TYPES = new Set([
  'same_passage',
  'related_entity_window',
  'coreference_window',
  'story_segment',
  'topic_overlap',
  'family_neighbor',
]);

const ALLOWED_SOURCE_IDS = new Set([
  'quran_uthmani_cloud',
  'stories_manifest',
  'ibn_kathir',
  'ibn_kathir_ar',
  'ibn_kathir_en',
  'tabari',
  'tabari_ar',
  'tabari_en',
  'qurtubi',
  'qurtubi_ar',
  'qurtubi_en',
]);

const errors: string[] = [];

if (!existsSync(LINKS_PATH)) {
  console.error(`[FAIL] ${LINKS_PATH} not found. Run scripts/build-prophet-contextual-links.ts first.`);
  process.exit(1);
}
const file = JSON.parse(readFileSync(LINKS_PATH, 'utf-8'));

let linkCount = 0;
for (const l of file.links ?? []) {
  linkCount++;
  if (!(l.prophetId in QURAN_PROPHET_BY_ID)) {
    errors.push(`Link references unknown prophet '${l.prophetId}'.`);
  }
  if (!ALLOWED_LINK_TYPES.has(l.linkType)) {
    errors.push(`Link ${l.prophetId} @${l.surahNumber}:${l.ayahNumber}: invalid linkType '${l.linkType}'.`);
  }
  if (!Array.isArray(l.evidenceReferences) || l.evidenceReferences.length === 0) {
    errors.push(
      `Link ${l.prophetId} @${l.surahNumber}:${l.ayahNumber}: missing evidenceReferences.`,
    );
  }
  for (const ref of l.evidenceReferences ?? []) {
    if (!Number.isInteger(ref.surahNumber) || ref.surahNumber < 1 || ref.surahNumber > 114) {
      errors.push(
        `Link ${l.prophetId}: evidence with out-of-range surahNumber ${ref.surahNumber}.`,
      );
    }
    if (!Number.isInteger(ref.ayahStart) || ref.ayahStart < 1) {
      errors.push(
        `Link ${l.prophetId}: evidence with bad ayahStart ${ref.ayahStart}.`,
      );
    }
  }
  if (l.reviewStatus !== 'needs_review') {
    errors.push(
      `Link ${l.prophetId} @${l.surahNumber}:${l.ayahNumber}: reviewStatus must be 'needs_review', got '${l.reviewStatus}'.`,
    );
  }
  if (l.humanReviewRequired !== true) {
    errors.push(
      `Link ${l.prophetId} @${l.surahNumber}:${l.ayahNumber}: humanReviewRequired must be true.`,
    );
  }
  for (const sid of l.sourceIds ?? []) {
    if (!ALLOWED_SOURCE_IDS.has(sid)) {
      errors.push(`Link ${l.prophetId}: untrusted sourceId '${sid}'.`);
    }
  }
}

console.log(`\nProphet Contextual Links validation`);
console.log(`-----------------------------------`);
console.log(`Total links: ${linkCount}`);
console.log(`Errors: ${errors.length}`);
if (errors.length > 0) {
  for (const e of errors.slice(0, 50)) console.log(`  - ${e}`);
  if (errors.length > 50) console.log(`  … and ${errors.length - 50} more.`);
  process.exit(1);
}
console.log(`\n[OK] All Phase X2 contextual-link checks pass.`);
process.exit(0);
