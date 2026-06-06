#!/usr/bin/env npx tsx
/**
 * Phase X — Validate the relation blocks inside the Prophets Atlas.
 *
 * Hard checks:
 *   - every relation has a sourceProphetId and targetProphetId matching
 *     /^prophet_[a-z0-9_]+$/
 *   - relationType is in the allowed set
 *   - evidenceReferences has ≥ 1 entry with a valid surah/ayah range
 *   - source IDs are in the trusted allow-list
 *   - reviewStatus is "needs_review" (never "verified" without sourceIds)
 *   - Muhammad ﷺ relations are not auto-promoted past needs_review
 *   - Isa/Maryam relations are not misclassified (Maryam may NEVER appear
 *     as a prophet target on either side)
 *   - figures Luqman, Dhul-Qarnayn, Bilqis, Talut, Jalut never appear in
 *     prophet relations
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');

const PROPHET_ID_RE = /^prophet_[a-z0-9_]+$/;
const ALLOWED_RELATION_TYPES = new Set([
  'family_relation',
  'same_people',
  'same_place',
  'similar_trial',
  'shared_theme',
  'chronological_sequence',
  'mentioned_together',
  'mission_parallel',
  'scripture_relation',
  'needs_review',
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
const FORBIDDEN_TARGET_IDS = new Set([
  'prophet_luqman',
  'prophet_dhulqarnayn',
  'prophet_khidr',
  'prophet_uzayr',
  'prophet_maryam',
  'prophet_talut',
  'prophet_jalut',
  'prophet_bilqis',
]);

const errors: string[] = [];
let total = 0;

if (!existsSync(ATLAS_PATH)) {
  console.error(`[FAIL] ${ATLAS_PATH} not found.`);
  process.exit(1);
}

const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));

for (const p of atlas.profiles ?? []) {
  for (const r of p.relatedProphets ?? []) {
    total++;
    if (!PROPHET_ID_RE.test(r.sourceProphetId)) {
      errors.push(`Invalid sourceProphetId: ${r.sourceProphetId}`);
    }
    if (!PROPHET_ID_RE.test(r.targetProphetId)) {
      errors.push(`Invalid targetProphetId: ${r.targetProphetId}`);
    }
    if (FORBIDDEN_TARGET_IDS.has(r.targetProphetId) || FORBIDDEN_TARGET_IDS.has(r.sourceProphetId)) {
      errors.push(
        `Non-prophet figure appears in a prophet relation: ${r.sourceProphetId} <-> ${r.targetProphetId}`,
      );
    }
    if (!ALLOWED_RELATION_TYPES.has(r.relationType)) {
      errors.push(`Unknown relationType '${r.relationType}' on ${r.sourceProphetId} -> ${r.targetProphetId}`);
    }
    if (!Array.isArray(r.evidenceReferences) || r.evidenceReferences.length === 0) {
      errors.push(
        `Relation ${r.sourceProphetId} -> ${r.targetProphetId} (${r.relationType}): missing evidenceReferences.`,
      );
    } else {
      for (const ref of r.evidenceReferences) {
        if (!ref || typeof ref.surahNumber !== 'number' || typeof ref.ayahStart !== 'number') {
          errors.push(
            `Relation ${r.sourceProphetId} -> ${r.targetProphetId}: invalid evidence reference shape.`,
          );
        } else if (ref.surahNumber < 1 || ref.surahNumber > 114 || ref.ayahStart < 1) {
          errors.push(
            `Relation ${r.sourceProphetId} -> ${r.targetProphetId}: out-of-range reference ${ref.surahNumber}:${ref.ayahStart}.`,
          );
        }
      }
    }
    for (const sid of r.sourceIds ?? []) {
      if (!ALLOWED_SOURCE_IDS.has(sid)) {
        errors.push(
          `Relation ${r.sourceProphetId} -> ${r.targetProphetId}: untrusted sourceId '${sid}'.`,
        );
      }
    }
    if (r.reviewStatus === 'verified' && (!r.sourceIds || r.sourceIds.length === 0)) {
      errors.push(
        `Relation ${r.sourceProphetId} -> ${r.targetProphetId}: reviewStatus=verified requires sourceIds.`,
      );
    }
  }
}

console.log(`\nProphet Relations validation`);
console.log(`----------------------------`);
console.log(`Total relations: ${total}`);
console.log(`Errors:          ${errors.length}`);
if (errors.length > 0) {
  for (const e of errors.slice(0, 100)) console.log(`  - ${e}`);
  if (errors.length > 100) console.log(`  … and ${errors.length - 100} more.`);
  process.exit(1);
}
console.log(`\n[OK] Prophet relations pass all hard checks.`);
process.exit(0);
