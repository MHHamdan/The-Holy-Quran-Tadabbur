#!/usr/bin/env npx tsx
/**
 * Validate quranStoryCrossReferences.json against the registry.
 *
 * Checks:
 *   - file exists and parses
 *   - every edge has both source and target IDs that resolve in the
 *     registry
 *   - no self-loops
 *   - every edge has at least one evidence kind from the strong set
 *     (same_prophet, same_figure, overlapping_ayahs)
 *   - every edge defaults to needs_review with humanReviewRequired=true
 *   - neighboursByStory keys match registry IDs
 *   - score is ≥ minScore for every edge
 *
 * Exit code 0 on pass, 1 on failure.
 */
import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const REGISTRY = join(ROOT, 'frontend/src/data/generated/quranStoryRegistry.json');
const CROSS_REFS = join(
  ROOT,
  'frontend/src/data/generated/quranStoryCrossReferences.json',
);

const failures: string[] = [];
const fail = (m: string) => failures.push(m);

if (!existsSync(CROSS_REFS)) {
  console.error('Missing quranStoryCrossReferences.json.');
  console.error('Run scripts/build-quran-story-cross-references.ts first.');
  process.exit(1);
}

const registry = JSON.parse(readFileSync(REGISTRY, 'utf-8'));
const crossRefs = JSON.parse(readFileSync(CROSS_REFS, 'utf-8'));

const registryIds = new Set<string>(registry.stories.map((s: any) => s.storyId));

const STRONG = new Set(['same_prophet', 'same_figure', 'overlapping_ayahs']);

const minScore: number = typeof crossRefs.minScore === 'number' ? crossRefs.minScore : 2;
const edges: any[] = crossRefs.edges || [];
if (edges.length === 0) fail('No edges in cross-references file.');

const seen = new Set<string>();
for (const e of edges) {
  if (!e.sourceStoryId || !e.targetStoryId) {
    fail(`Edge missing source/target: ${JSON.stringify(e).slice(0, 80)}`);
    continue;
  }
  if (e.sourceStoryId === e.targetStoryId) {
    fail(`Self-loop edge: ${e.sourceStoryId}`);
  }
  if (!registryIds.has(e.sourceStoryId)) {
    fail(`source not in registry: ${e.sourceStoryId}`);
  }
  if (!registryIds.has(e.targetStoryId)) {
    fail(`target not in registry: ${e.targetStoryId}`);
  }
  const pairKey = [e.sourceStoryId, e.targetStoryId].sort().join('|');
  if (seen.has(pairKey)) {
    fail(`Duplicate undirected edge: ${pairKey}`);
  }
  seen.add(pairKey);
  if (!Array.isArray(e.evidence) || e.evidence.length === 0) {
    fail(`No evidence on edge ${pairKey}`);
    continue;
  }
  if (!e.evidence.some((ev: any) => STRONG.has(ev.relation))) {
    fail(`No strong-signal evidence on edge ${pairKey} (evidence kinds: ${e.evidence.map((ev: any) => ev.relation).join(',')})`);
  }
  if (typeof e.score !== 'number' || e.score < minScore) {
    fail(`Edge ${pairKey} has score ${e.score} < minScore ${minScore}`);
  }
  if (e.reviewStatus === 'verified' && e.humanReviewRequired !== false) {
    fail(`Edge ${pairKey} is verified but humanReviewRequired is still true`);
  }
  if (e.reviewStatus !== 'verified' && e.reviewStatus !== 'needs_review') {
    fail(`Edge ${pairKey} has invalid reviewStatus ${e.reviewStatus}`);
  }
}

// neighboursByStory
const nbm: Record<string, any[]> = crossRefs.neighboursByStory || {};
for (const id of Object.keys(nbm)) {
  if (!registryIds.has(id)) {
    fail(`neighboursByStory key not in registry: ${id}`);
  }
  for (const peer of nbm[id]) {
    if (!registryIds.has(peer.storyId)) {
      fail(`neighbour storyId not in registry: ${peer.storyId}`);
    }
    if (peer.storyId === id) {
      fail(`Self-neighbour for ${id}`);
    }
  }
}

if (failures.length > 0) {
  console.error('Cross-references validation FAILED:');
  for (const f of failures) console.error('  - ' + f);
  process.exit(1);
}

console.log(
  `Cross-refs OK: ${edges.length} edges, ${Object.keys(nbm).length} stories with neighbours.`,
);
