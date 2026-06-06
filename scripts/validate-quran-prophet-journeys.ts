#!/usr/bin/env npx tsx
/**
 * Phase X — Validate the journey blocks inside the Prophets Atlas.
 *
 * Hard checks:
 *   - every journey has journeyType in the allowed set
 *   - every stage has ≥ 1 ayahReference
 *   - no stage has reviewStatus = "verified" without sourceIds
 *   - certainty is one of {"high", "medium", "low", "disputed"}
 *   - learning_order stage indices are monotonically increasing (1..N)
 *   - story_world_order journeys are not flagged "high" certainty
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranProphetsAtlas.json');

const ALLOWED_JOURNEY_TYPES = new Set([
  'mushaf_order',
  'story_world_order',
  'revelation_order',
  'thematic_order',
  'learning_order',
]);
const ALLOWED_CERTAINTY = new Set(['high', 'medium', 'low', 'disputed']);

const errors: string[] = [];
const warnings: string[] = [];

if (!existsSync(ATLAS_PATH)) {
  console.error(`[FAIL] ${ATLAS_PATH} not found. Run scripts/build-quran-prophets-atlas.ts first.`);
  process.exit(1);
}

const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8'));
let totalStages = 0;

for (const p of atlas.profiles ?? []) {
  for (const j of p.journeys ?? []) {
    if (!ALLOWED_JOURNEY_TYPES.has(j.journeyType)) {
      errors.push(`${p.prophetId} journey ${j.journeyId}: invalid journeyType '${j.journeyType}'.`);
    }
    if (!ALLOWED_CERTAINTY.has(j.certainty)) {
      errors.push(`${p.prophetId} journey ${j.journeyId}: invalid certainty '${j.certainty}'.`);
    }
    if (j.journeyType === 'story_world_order' && j.certainty === 'high') {
      errors.push(
        `${p.prophetId} journey ${j.journeyId}: story_world_order MUST NOT have certainty='high'.`,
      );
    }
    let lastIdx = 0;
    for (const s of j.stages ?? []) {
      totalStages++;
      if (!Array.isArray(s.ayahReferences) || s.ayahReferences.length === 0) {
        errors.push(
          `${p.prophetId} journey ${j.journeyId} stage ${s.stageId}: missing ayahReferences.`,
        );
      }
      if (s.reviewStatus === 'verified' && (!s.sourceIds || s.sourceIds.length === 0)) {
        errors.push(
          `${p.prophetId} stage ${s.stageId}: reviewStatus=verified requires non-empty sourceIds.`,
        );
      }
      if (j.journeyType === 'learning_order') {
        if (typeof s.orderIndex !== 'number' || s.orderIndex !== lastIdx + 1) {
          errors.push(
            `${p.prophetId} journey ${j.journeyId} stage ${s.stageId}: learning_order indices must be monotonic.`,
          );
        }
        lastIdx = s.orderIndex;
      }
    }
  }
}

console.log(`\nProphet Journeys validation`);
console.log(`---------------------------`);
console.log(`Profiles: ${atlas.profiles?.length ?? 0}`);
console.log(`Total stages: ${totalStages}`);
console.log(`Errors:   ${errors.length}`);
console.log(`Warnings: ${warnings.length}`);
if (errors.length > 0) {
  for (const e of errors) console.log(`  - ${e}`);
  process.exit(1);
}
console.log(`\n[OK] Prophet journeys pass all hard checks.`);
process.exit(0);
