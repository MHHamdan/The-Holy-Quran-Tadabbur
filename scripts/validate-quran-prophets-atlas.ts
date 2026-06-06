#!/usr/bin/env npx tsx
/**
 * Phase X — Validate the generated Quran Prophets Atlas.
 *
 * Hard checks (exit 1 if any fails):
 *   - exactly 25 prophet profiles
 *   - no non-prophet figure (Luqman, Dhul-Qarnayn, Maryam, Bilqis, Khidr,
 *     Uzayr, Talut, Jalut) appears as a prophet
 *   - every profile has a prophetId matching /^prophet_[a-z0-9_]+$/
 *   - every profile has a non-empty nameArabic and nameEnglish
 *   - every storytelling field defaults to needs_review (never verified)
 *   - every relation has evidenceReferences (if any are present)
 *   - reviewStatus on the profile is "needs_review" or "verified" or "missing_source"
 *   - all sourceIds appear in the trusted source allow-list
 *   - the canonical seed list and the atlas profile list match exactly
 *
 * Soft checks (warnings only):
 *   - prophet has zero explicit mentions
 *   - prophet missing a curated story page
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import {
  QURAN_PROPHET_SEEDS,
  QURAN_PROPHET_COUNT_CANONICAL,
} from '../frontend/src/data/quranProphetSeeds';

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');

const FORBIDDEN_PROPHET_IDS = new Set([
  'prophet_luqman',
  'prophet_dhulqarnayn',
  'prophet_khidr',
  'prophet_uzayr',
  'prophet_maryam',
  'prophet_talut',
  'prophet_jalut',
  'prophet_bilqis',
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

const PROPHET_ID_RE = /^prophet_[a-z0-9_]+$/;

const errors: string[] = [];
const warnings: string[] = [];

function err(msg: string): void {
  errors.push(msg);
}
function warn(msg: string): void {
  warnings.push(msg);
}

if (!existsSync(ATLAS_PATH)) {
  console.error(`[FAIL] ${ATLAS_PATH} not found. Run scripts/build-quran-prophets-atlas.ts first.`);
  process.exit(1);
}

const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));
const profiles: any[] = atlas.profiles ?? [];

// 1. Exactly 25 profiles ----------------------------------------------------
if (profiles.length !== QURAN_PROPHET_COUNT_CANONICAL) {
  err(`Expected exactly ${QURAN_PROPHET_COUNT_CANONICAL} prophet profiles, got ${profiles.length}.`);
}

// 2. Match seed list exactly ------------------------------------------------
const atlasIds = new Set(profiles.map((p) => p.prophetId));
const seedIds = new Set(QURAN_PROPHET_SEEDS.map((s) => s.prophetId));
for (const sid of seedIds) {
  if (!atlasIds.has(sid)) err(`Atlas is missing seeded prophet: ${sid}`);
}
for (const aid of atlasIds) {
  if (!seedIds.has(aid)) err(`Atlas contains unseeded prophet: ${aid}`);
}

// 3. Forbidden prophet IDs (non-prophet figures) ----------------------------
for (const p of profiles) {
  if (FORBIDDEN_PROPHET_IDS.has(p.prophetId)) {
    err(`Non-prophet figure appears as a prophet: ${p.prophetId}`);
  }
}

// 4. Structural validation --------------------------------------------------
for (const p of profiles) {
  if (!PROPHET_ID_RE.test(p.prophetId)) err(`Invalid prophetId format: ${p.prophetId}`);
  if (!p.nameArabic || !p.nameEnglish) err(`Profile missing nameArabic/nameEnglish: ${p.prophetId}`);
  if (typeof p.surahCount !== 'number') err(`Profile missing surahCount: ${p.prophetId}`);

  // storytelling never auto-verified
  if (p.storytellingSummaryArabic || p.storytellingSummaryEnglish) {
    if (p.reviewStatus === 'verified') {
      err(`Profile ${p.prophetId} has auto-verified storytelling — must remain needs_review.`);
    }
  }

  // reviewStatus must be one of three
  if (!['verified', 'needs_review', 'missing_source'].includes(p.reviewStatus)) {
    err(`Profile ${p.prophetId} has invalid reviewStatus: ${p.reviewStatus}`);
  }

  // every relation must have evidenceReferences
  for (const r of p.relatedProphets ?? []) {
    if (!Array.isArray(r.evidenceReferences) || r.evidenceReferences.length === 0) {
      err(
        `Relation ${r.sourceProphetId} -> ${r.targetProphetId} (${r.relationType}) has no evidenceReferences.`,
      );
    }
    for (const sid of r.sourceIds ?? []) {
      if (!ALLOWED_SOURCE_IDS.has(sid)) {
        err(`Relation ${r.sourceProphetId} -> ${r.targetProphetId}: untrusted sourceId '${sid}'.`);
      }
    }
  }

  // Source IDs at profile level
  for (const sid of p.sourceIds ?? []) {
    if (!ALLOWED_SOURCE_IDS.has(sid)) {
      err(`Profile ${p.prophetId}: untrusted sourceId '${sid}'.`);
    }
  }

  // Soft checks
  if ((p.explicitMentions ?? []).length === 0) {
    warn(`${p.prophetId}: no explicit-name mentions found.`);
  }
  if ((p.storyIds ?? []).length === 0) {
    warn(`${p.prophetId}: no curated story page references this prophet.`);
  }
}

// 5. Related figures must not be tagged as prophets -------------------------
const figureIds = new Set((atlas.relatedFigures ?? []).map((f: any) => f.figureId));
for (const id of figureIds) {
  if (typeof id === 'string' && id.startsWith('prophet_')) {
    err(`Related figure has prophet_ prefix (forbidden): ${id}`);
  }
}

// Report --------------------------------------------------------------------

console.log(`\nProphets Atlas validation`);
console.log(`-------------------------`);
console.log(`Profiles checked: ${profiles.length}`);
console.log(`Errors:   ${errors.length}`);
console.log(`Warnings: ${warnings.length}`);
if (warnings.length > 0) {
  console.log(`\nWarnings:`);
  for (const w of warnings.slice(0, 50)) console.log(`  - ${w}`);
}
if (errors.length > 0) {
  console.log(`\nErrors:`);
  for (const e of errors) console.log(`  - ${e}`);
  process.exit(1);
}

console.log(`\n[OK] Prophets Atlas passes all hard checks.`);
process.exit(0);
