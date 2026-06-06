#!/usr/bin/env npx tsx
/**
 * Validator: quranTopicRelationGraph.json
 *
 * Checks:
 *   - file loads
 *   - every edge has at least one evidence ref
 *   - confidence ∈ [0,1]
 *   - all edges are needs_review
 *   - no self-loops
 *   - all source/target node IDs exist in the node list
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import { SOURCE_REGISTRY } from '../frontend/src/data/sourceRegistry';
import type { QuranTopicRelationGraphOutput } from '../frontend/src/types/quranTopicAtlas';

const ROOT = resolve(__dirname, '..');
const PATH = join(ROOT, 'frontend/src/data/generated/quranTopicRelationGraph.json');

function main(): void {
  if (!existsSync(PATH)) {
    console.error(`Missing: ${PATH}`);
    process.exit(1);
  }
  const out = JSON.parse(readFileSync(PATH, 'utf-8')) as QuranTopicRelationGraphOutput;
  const errors: string[] = [];
  const nodeIds = new Set(out.nodes.map((n) => n.id));
  const validSourceIds = new Set(SOURCE_REGISTRY.map((s) => s.sourceId));

  if (out.nodeCount === 0) errors.push('nodeCount=0');
  if (out.edgeCount === 0) errors.push('edgeCount=0');

  let evidenceMissing = 0;
  let confOOB = 0;
  let nonNeedsReview = 0;
  let selfLoops = 0;
  let badNodeRefs = 0;
  let badSourceIds = 0;

  for (const e of out.edges) {
    if (!e.evidenceReferences || e.evidenceReferences.length === 0) evidenceMissing += 1;
    if (e.confidence < 0 || e.confidence > 1) confOOB += 1;
    if (e.reviewStatus !== 'needs_review') nonNeedsReview += 1;
    if (e.sourceNodeId === e.targetNodeId) selfLoops += 1;
    if (!nodeIds.has(e.sourceNodeId) || !nodeIds.has(e.targetNodeId)) badNodeRefs += 1;
    for (const sid of e.sourceIds) {
      if (!validSourceIds.has(sid)) badSourceIds += 1;
    }
  }
  if (evidenceMissing > 0) errors.push(`${evidenceMissing} edges missing evidenceReferences`);
  if (confOOB > 0) errors.push(`${confOOB} edges have confidence out of [0,1]`);
  if (nonNeedsReview > 0) errors.push(`${nonNeedsReview} edges are not needs_review`);
  if (selfLoops > 0) errors.push(`${selfLoops} edges are self-loops`);
  if (badNodeRefs > 0) errors.push(`${badNodeRefs} edges reference unknown nodeIds`);
  if (badSourceIds > 0) errors.push(`${badSourceIds} edge-source IDs are unknown`);

  if (errors.length) {
    console.error(`\nErrors: ${errors.length}`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
  console.log(`OK — nodes=${out.nodeCount}, edges=${out.edgeCount}`);
}

main();
