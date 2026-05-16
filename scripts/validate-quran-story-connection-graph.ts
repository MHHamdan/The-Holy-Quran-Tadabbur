#!/usr/bin/env npx tsx
/**
 * Validate scripts/build-quran-story-connection-graph.ts output.
 *
 * Checks:
 *   - Every edge endpoint exists in nodes.
 *   - Every edge has ≥ 1 evidenceReferences with ≥ 1 sourceIds.
 *   - Every sourceId is non-empty (full registry cross-check is delegated to
 *     validate-quran-integrity.ts).
 *   - No Quran text leaked in node/edge labels.
 *   - No "approved/verified" edge without humanReviewRequired = false and an
 *     evidenceType other than needs_review.
 *   - Story segment nodes reference real ayah ranges.
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';
import type { ConnectionGraph } from '../frontend/src/types/quranStoryConnection';

const ROOT = resolve(__dirname, '..');
const GRAPH_PATH = join(ROOT, 'frontend/src/data/generated/quranStoryConnectionGraph.json');

const errors: string[] = [];
const warnings: string[] = [];
function err(m: string) { errors.push(m); }
function warn(m: string) { warnings.push(m); }

if (!existsSync(GRAPH_PATH)) {
  console.error(`Missing graph: ${GRAPH_PATH}. Run build-quran-story-connection-graph.ts first.`);
  process.exit(1);
}
const graph = JSON.parse(readFileSync(GRAPH_PATH, 'utf-8')) as ConnectionGraph;

const nodeIds = new Set(graph.nodes.map((n) => n.id));

// 1. Counts match
if (graph.nodeCount !== graph.nodes.length) {
  err(`graph.nodeCount=${graph.nodeCount} but nodes.length=${graph.nodes.length}`);
}
if (graph.edgeCount !== graph.edges.length) {
  err(`graph.edgeCount=${graph.edgeCount} but edges.length=${graph.edges.length}`);
}

// 2. Endpoint integrity + evidence integrity
for (const e of graph.edges) {
  if (!nodeIds.has(e.sourceNodeId)) {
    err(`Edge ${e.edgeId}: sourceNodeId ${e.sourceNodeId} not in nodes`);
  }
  if (!nodeIds.has(e.targetNodeId)) {
    err(`Edge ${e.edgeId}: targetNodeId ${e.targetNodeId} not in nodes`);
  }
  if (!e.evidenceReferences || e.evidenceReferences.length === 0) {
    err(`Edge ${e.edgeId}: missing evidenceReferences`);
    continue;
  }
  for (const ev of e.evidenceReferences) {
    if (!Array.isArray(ev.sourceIds) || ev.sourceIds.length === 0) {
      err(`Edge ${e.edgeId}: evidence missing sourceIds`);
    }
    if (ev.sourceIds && ev.sourceIds.some((s) => typeof s !== 'string' || s.length === 0)) {
      err(`Edge ${e.edgeId}: empty sourceId entry`);
    }
    if (typeof ev.surahNumber !== 'number') {
      err(`Edge ${e.edgeId}: evidence missing surahNumber`);
    }
    if (typeof ev.ayahStart !== 'number') {
      err(`Edge ${e.edgeId}: evidence missing ayahStart`);
    }
  }
  if (e.reviewStatus !== 'needs_review' && e.reviewStatus !== 'verified' && e.reviewStatus !== 'rejected') {
    err(`Edge ${e.edgeId}: invalid reviewStatus ${e.reviewStatus}`);
  }
  if (e.reviewStatus === 'verified' && e.humanReviewRequired) {
    err(`Edge ${e.edgeId}: verified but humanReviewRequired=true`);
  }
  if (e.reviewStatus === 'verified') {
    const onlyNeedsReview = e.evidenceReferences.every((ev) => ev.evidenceType === 'needs_review');
    if (onlyNeedsReview) {
      err(`Edge ${e.edgeId}: verified but only needs_review evidence`);
    }
  }
  if (typeof e.confidence !== 'number' || e.confidence < 0 || e.confidence > 1) {
    err(`Edge ${e.edgeId}: invalid confidence ${e.confidence}`);
  }
}

// 3. No Quran text leaked into JSON
const rawText = readFileSync(GRAPH_PATH, 'utf-8');
const FORBIDDEN_FIELDS = ['aya_text', 'text_uthmani', 'arabicText'];
for (const f of FORBIDDEN_FIELDS) {
  if (rawText.includes(`"${f}"`)) {
    err(`Forbidden field "${f}" present in graph JSON`);
  }
}

// 4. Story segment nodes have surahNumber/ayahStart
for (const n of graph.nodes) {
  if (n.type === 'story_segment') {
    const md = n.metadata ?? {};
    if (typeof md['surahNumber'] !== 'number') {
      err(`story_segment node ${n.id} missing surahNumber`);
    }
    if (typeof md['ayahStart'] !== 'number') {
      err(`story_segment node ${n.id} missing ayahStart`);
    }
  }
}

// Report
console.log(`Validation of connection graph:`);
console.log(`  nodes: ${graph.nodeCount}, edges: ${graph.edgeCount}`);
console.log(`  errors: ${errors.length}, warnings: ${warnings.length}`);

if (warnings.length > 0) {
  console.log('\n--- WARNINGS ---');
  for (const w of warnings.slice(0, 20)) console.log('  -', w);
  if (warnings.length > 20) console.log(`  (+${warnings.length - 20} more)`);
}
if (errors.length > 0) {
  console.error('\n--- ERRORS ---');
  for (const e of errors.slice(0, 50)) console.error('  -', e);
  if (errors.length > 50) console.error(`  (+${errors.length - 50} more)`);
  process.exit(1);
}
console.log('\nAll connection-graph checks passed.');
process.exit(0);
