#!/usr/bin/env npx tsx
/**
 * Validator: quranTopicClusters.json
 *
 * Checks:
 *   - file loads
 *   - every cluster has ≥2 members
 *   - coherenceScore ∈ [0,1]
 *   - every cluster is needs_review
 *   - all member topicIds exist in the atlas
 *   - generatedBy is one of the known methods
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import type {
  QuranTopicAtlasOutput,
  QuranTopicClustersOutput,
  QuranTopicClusterMethod,
} from '../frontend/src/types/quranTopicAtlas';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranTopicClusters.json');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranTopicAtlas.json');

const VALID_METHODS = new Set<QuranTopicClusterMethod>([
  'seed_taxonomy',
  'embedding_clustering',
  'graph_community',
  'entity_story_overlap',
  'tafsir_source',
  'manual_review',
]);

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  if (!existsSync(ATLAS_PATH)) {
    console.error(`Missing: ${ATLAS_PATH}`);
    process.exit(1);
  }
  const atlas = JSON.parse(readFileSync(ATLAS_PATH, 'utf-8')) as QuranTopicAtlasOutput;
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as QuranTopicClustersOutput;
  const errors: string[] = [];
  const topicIds = new Set(atlas.topics.map((t) => t.topicId));

  for (const c of out.clusters) {
    if (!c.memberTopicIds || c.memberTopicIds.length < 2) {
      errors.push(`${c.clusterId}: cluster must have ≥2 member topics`);
    }
    for (const id of c.memberTopicIds) {
      if (!topicIds.has(id)) errors.push(`${c.clusterId}: unknown member topicId "${id}"`);
    }
    if (c.coherenceScore < 0 || c.coherenceScore > 1) {
      errors.push(`${c.clusterId}: coherenceScore out of [0,1] (${c.coherenceScore})`);
    }
    if (!VALID_METHODS.has(c.generatedBy)) errors.push(`${c.clusterId}: unknown generatedBy "${c.generatedBy}"`);
    if (c.reviewStatus !== 'needs_review') errors.push(`${c.clusterId}: must be needs_review`);
    if (c.humanReviewRequired !== true) errors.push(`${c.clusterId}: humanReviewRequired must be true`);
  }
  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors.slice(0, 50)) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — clusters=${out.totalClusters}`);
}

main();
