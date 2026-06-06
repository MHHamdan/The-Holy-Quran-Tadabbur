#!/usr/bin/env npx tsx
/**
 * Validator: quranCoreferenceChains.json
 *
 * Checks:
 *   - file loads, totalChains > 0
 *   - every chain has at least 2 mentions
 *   - every chain has surahScope, ayahRangeStart, ayahRangeEnd
 *   - cross_surah_candidate chains are always needs_review
 *   - confidence ∈ [0,1]
 *   - all entityIds exist in the seed dictionary
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { QURAN_ENTITY_SEEDS } from '../frontend/src/data/quranEntitySeeds';
import type { CoreferenceChainsOutput } from '../frontend/src/types/quranCoreference';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranCoreferenceChains.json');

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as CoreferenceChainsOutput;
  const errors: string[] = [];
  const seedIds = new Set(QURAN_ENTITY_SEEDS.map((s) => s.entityId));

  if (out.totalChains === 0) errors.push('totalChains=0');

  for (const c of out.chains) {
    if (!seedIds.has(c.entityId)) errors.push(`${c.chainId}: unknown entityId "${c.entityId}"`);
    if (!c.mentions || c.mentions.length < 2) {
      errors.push(`${c.chainId}: chain must have ≥2 mentions (got ${c.mentions?.length ?? 0})`);
    }
    if (!c.surahScope || c.surahScope.length === 0) errors.push(`${c.chainId}: empty surahScope`);
    if (!c.ayahRangeStart || !c.ayahRangeEnd) errors.push(`${c.chainId}: missing ayahRange`);
    if (typeof c.confidence !== 'number' || c.confidence < 0 || c.confidence > 1) {
      errors.push(`${c.chainId}: confidence out of [0,1]`);
    }
    if (c.chainType === 'cross_surah_candidate' && c.reviewStatus !== 'needs_review') {
      errors.push(`${c.chainId}: cross_surah_candidate must be needs_review`);
    }
    if (c.humanReviewRequired !== true) {
      errors.push(`${c.chainId}: humanReviewRequired must be true`);
    }
  }

  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — chains=${out.totalChains}`);
}

main();
