#!/usr/bin/env npx tsx
/**
 * Build cross-Quran story correlations.
 *
 * For every pair of stories in the canonical registry, compute a
 * similarity score derived ONLY from data already present in the
 * registry / manifest. We do not invent narrative, themes, or ayah
 * references — we only join on:
 *
 *   - shared prophets / main figures
 *   - shared surahs
 *   - shared themes
 *   - shared ayah-range overlaps (within the same surah)
 *   - shared topics (via quranTopicAtlas if available)
 *
 * Output:
 *   frontend/src/data/generated/quranStoryCrossReferences.json
 *   docs/generated/quran-story-cross-references-summary.md
 *
 * Safety:
 *   - No Quran text embedded.
 *   - Every pair carries `evidence` listing exactly which signals matched.
 *   - All pairs default to `reviewStatus: "needs_review"` and
 *     `humanReviewRequired: true`.
 *   - Pairs with no shared signal are NOT emitted (no speculative links).
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import type {
  QuranStoryRegistryFile,
  RegistryStoryEntry,
  RegistryQuranReference,
} from '../frontend/src/types/quranStoryRegistry';

const ROOT = resolve(__dirname, '..');
const REGISTRY = join(ROOT, 'frontend/src/data/generated/quranStoryRegistry.json');
const MANIFEST = join(ROOT, 'data/manifests/stories.json');
const TOPIC_ATLAS = join(ROOT, 'frontend/src/data/generated/quranTopicAtlas.json');
const OUT_JSON = join(
  ROOT,
  'frontend/src/data/generated/quranStoryCrossReferences.json',
);
const OUT_MD = join(
  ROOT,
  'docs/generated/quran-story-cross-references-summary.md',
);
const VERSION = '1.0.0';

if (!existsSync(REGISTRY)) {
  throw new Error('Run scripts/build-quran-story-registry.ts first.');
}

const registry = JSON.parse(readFileSync(REGISTRY, 'utf-8')) as QuranStoryRegistryFile;
const manifest = JSON.parse(readFileSync(MANIFEST, 'utf-8')) as {
  stories: Array<{
    id: string;
    main_figures?: string[];
    themes?: string[];
    suras_mentioned?: number[];
  }>;
};

// Per-story signal index built from manifest + registry data.
interface StorySignals {
  storyId: string;
  prophets: Set<string>;       // canonical prophetId from registry.relatedProphets
  figures: Set<string>;        // raw figure names from the manifest (Musa, Fir'awn, …)
  surahs: Set<number>;
  themes: Set<string>;         // raw theme strings from manifest
  topics: Set<string>;
  ranges: RegistryQuranReference[];
}

const signalsById = new Map<string, StorySignals>();

const manifestById = new Map<string, (typeof manifest.stories)[number]>();
for (const m of manifest.stories) manifestById.set(m.id, m);

for (const entry of registry.stories) {
  const m = manifestById.get(entry.storyId);
  const prophets = new Set<string>(entry.relatedProphets);
  const figures = new Set<string>();
  for (const f of m?.main_figures || []) figures.add(f.toLowerCase());
  const surahs = new Set<number>();
  for (const r of entry.quranReferences) surahs.add(r.surahNumber);
  for (const s of m?.suras_mentioned || []) surahs.add(s);
  const themes = new Set<string>((m?.themes || []).map(t => t.toLowerCase()));
  const topics = new Set<string>(entry.relatedTopics);
  signalsById.set(entry.storyId, {
    storyId: entry.storyId,
    prophets,
    figures,
    surahs,
    themes,
    topics,
    ranges: entry.quranReferences,
  });
}

// ---------------------------------------------------------------------------
// Pair scoring
// ---------------------------------------------------------------------------

type CrossRefRelation =
  | 'same_prophet'
  | 'same_figure'
  | 'same_surah'
  | 'same_theme'
  | 'same_topic'
  | 'overlapping_ayahs';

interface CrossRefEvidence {
  relation: CrossRefRelation;
  values: string[];          // e.g. ['Musa', 'Fir'awn'] or ['7']
}

interface CrossRefEdge {
  sourceStoryId: string;
  targetStoryId: string;
  score: number;
  evidence: CrossRefEvidence[];
  reviewStatus: 'verified' | 'needs_review';
  humanReviewRequired: boolean;
}

const WEIGHTS: Record<CrossRefRelation, number> = {
  same_prophet: 4.0,
  same_figure: 2.0,
  overlapping_ayahs: 3.0,
  same_surah: 1.0,
  same_theme: 1.2,
  same_topic: 1.4,
};

function intersect<T>(a: Set<T>, b: Set<T>): T[] {
  const out: T[] = [];
  for (const v of a) if (b.has(v)) out.push(v);
  return out;
}

function rangesOverlap(
  a: RegistryQuranReference,
  b: RegistryQuranReference,
): boolean {
  if (a.surahNumber !== b.surahNumber) return false;
  const aEnd = a.ayahEnd ?? a.ayahStart;
  const bEnd = b.ayahEnd ?? b.ayahStart;
  return a.ayahStart <= bEnd && b.ayahStart <= aEnd;
}

function scorePair(a: StorySignals, b: StorySignals): {
  score: number;
  evidence: CrossRefEvidence[];
} {
  const evidence: CrossRefEvidence[] = [];
  let score = 0;

  const sharedProphets = intersect(a.prophets, b.prophets);
  if (sharedProphets.length > 0) {
    evidence.push({ relation: 'same_prophet', values: sharedProphets });
    score += WEIGHTS.same_prophet * sharedProphets.length;
  }

  const sharedFigures = intersect(a.figures, b.figures);
  if (sharedFigures.length > 0) {
    evidence.push({ relation: 'same_figure', values: sharedFigures });
    score += WEIGHTS.same_figure * sharedFigures.length;
  }

  const overlaps: string[] = [];
  for (const ra of a.ranges) {
    for (const rb of b.ranges) {
      if (rangesOverlap(ra, rb)) {
        const tag = `${ra.surahNumber}:${ra.ayahStart}-${ra.ayahEnd ?? ra.ayahStart}↔${rb.ayahStart}-${rb.ayahEnd ?? rb.ayahStart}`;
        overlaps.push(tag);
      }
    }
  }
  if (overlaps.length > 0) {
    evidence.push({ relation: 'overlapping_ayahs', values: overlaps.slice(0, 5) });
    score += WEIGHTS.overlapping_ayahs * Math.min(overlaps.length, 5);
  }

  const sharedSurahs = intersect(a.surahs, b.surahs);
  if (sharedSurahs.length > 0) {
    evidence.push({
      relation: 'same_surah',
      values: sharedSurahs.map(String).slice(0, 8),
    });
    score += WEIGHTS.same_surah * Math.min(sharedSurahs.length, 8);
  }

  const sharedThemes = intersect(a.themes, b.themes);
  if (sharedThemes.length > 0) {
    evidence.push({ relation: 'same_theme', values: sharedThemes.slice(0, 6) });
    score += WEIGHTS.same_theme * sharedThemes.length;
  }

  const sharedTopics = intersect(a.topics, b.topics);
  if (sharedTopics.length > 0) {
    evidence.push({ relation: 'same_topic', values: sharedTopics.slice(0, 6) });
    score += WEIGHTS.same_topic * sharedTopics.length;
  }

  return { score, evidence };
}

// ---------------------------------------------------------------------------
// Build edges
// ---------------------------------------------------------------------------

const edges: CrossRefEdge[] = [];
const allIds: string[] = registry.stories.map(s => s.storyId);

// Minimum score to emit a pair: must have at least one strong signal
// (shared prophet, shared figure, or overlapping ayahs). Avoids creating
// edges from same-theme-only or same-surah-only noise.
const MIN_SCORE = 2.0;
const STRONG_RELATIONS = new Set<CrossRefRelation>([
  'same_prophet',
  'same_figure',
  'overlapping_ayahs',
]);

for (let i = 0; i < allIds.length; i++) {
  for (let j = i + 1; j < allIds.length; j++) {
    const a = signalsById.get(allIds[i]);
    const b = signalsById.get(allIds[j]);
    if (!a || !b) continue;
    const { score, evidence } = scorePair(a, b);
    if (score < MIN_SCORE) continue;
    const hasStrong = evidence.some(e => STRONG_RELATIONS.has(e.relation));
    if (!hasStrong) continue;
    edges.push({
      sourceStoryId: a.storyId,
      targetStoryId: b.storyId,
      score: Math.round(score * 100) / 100,
      evidence,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
    });
  }
}

edges.sort((x, y) => y.score - x.score);

// ---------------------------------------------------------------------------
// Per-story top-N neighbours
// ---------------------------------------------------------------------------

const TOP_PER_STORY = 8;
const neighboursByStory: Record<string, Array<{ storyId: string; score: number }>> = {};
for (const e of edges) {
  for (const [src, tgt] of [
    [e.sourceStoryId, e.targetStoryId],
    [e.targetStoryId, e.sourceStoryId],
  ]) {
    if (!neighboursByStory[src]) neighboursByStory[src] = [];
    if (neighboursByStory[src].length < TOP_PER_STORY) {
      neighboursByStory[src].push({ storyId: tgt, score: e.score });
    }
  }
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

const stats = {
  totalPairs: edges.length,
  pairsBySignal: {} as Record<string, number>,
  storiesWithAtLeastOneNeighbour: Object.keys(neighboursByStory).length,
  averageNeighboursPerStory:
    edges.length === 0
      ? 0
      : Math.round(
          (Object.values(neighboursByStory).reduce((a, n) => a + n.length, 0) /
            allIds.length) *
            100,
        ) / 100,
  storiesWithNoNeighbour: allIds.filter(id => !neighboursByStory[id]).length,
};
for (const e of edges) {
  for (const ev of e.evidence) {
    stats.pairsBySignal[ev.relation] =
      (stats.pairsBySignal[ev.relation] || 0) + 1;
  }
}

const out = {
  version: VERSION,
  generatedAt: new Date().toISOString(),
  weights: WEIGHTS,
  minScore: MIN_SCORE,
  stats,
  edges,
  neighboursByStory,
  warnings: [
    'All cross-references are needs_review until scholarly approval.',
    'Edges are derived purely from registry signals (shared prophets / figures / surahs / themes / topics / ayah overlaps) — no interpretive content.',
  ],
};

mkdirSync(dirname(OUT_JSON), { recursive: true });
writeFileSync(OUT_JSON, JSON.stringify(out, null, 2));
console.log(`Wrote ${OUT_JSON} (${edges.length} edges).`);

// Optional topic atlas presence note
void TOPIC_ATLAS;

const md: string[] = [];
md.push('# Quran Story Cross-References — Summary');
md.push('');
md.push(`- Version: ${VERSION}`);
md.push(`- Generated: ${out.generatedAt}`);
md.push(`- Min score: ${MIN_SCORE}`);
md.push(`- Total pairs: ${stats.totalPairs}`);
md.push(`- Stories with at least one neighbour: ${stats.storiesWithAtLeastOneNeighbour} / ${allIds.length}`);
md.push(`- Stories with NO neighbour: ${stats.storiesWithNoNeighbour}`);
md.push(`- Average neighbours per story (cap ${TOP_PER_STORY}): ${stats.averageNeighboursPerStory}`);
md.push('');
md.push('## Signal counts');
md.push('');
for (const [k, v] of Object.entries(stats.pairsBySignal)) md.push(`- ${k}: ${v}`);
md.push('');
md.push('## Top 10 strongest edges');
md.push('');
md.push('| Source | Target | Score | Evidence |');
md.push('| --- | --- | ---: | --- |');
for (const e of edges.slice(0, 10)) {
  const ev = e.evidence
    .map(x => `${x.relation}(${x.values.slice(0, 3).join(', ')})`)
    .join(' · ');
  md.push(`| ${e.sourceStoryId} | ${e.targetStoryId} | ${e.score} | ${ev} |`);
}
mkdirSync(dirname(OUT_MD), { recursive: true });
writeFileSync(OUT_MD, md.join('\n') + '\n');
console.log(`Wrote ${OUT_MD}`);
