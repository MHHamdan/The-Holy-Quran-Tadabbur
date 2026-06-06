#!/usr/bin/env npx tsx
/**
 * Quran Topic Cluster Discovery — Phase V.
 *
 * Local-only, deterministic discovery: we do NOT assume any embedding model
 * is available. The script produces candidate clusters from three observable
 * signals:
 *
 *   1. seed_taxonomy — topics that share a parentTopicId (Topic-type bucket).
 *   2. entity_story_overlap — pairs/sets of topics whose `relatedEntities`
 *      sets overlap by ≥1 entity.
 *   3. graph_community — connected components over the bipartite
 *      (topic ↔ ayah) co-occurrence graph: any two topics sharing ≥N ayah
 *      links land in the same community.
 *
 * If embeddings ever become available, we add a fourth method
 * (`embedding_clustering`) without changing the output schema.
 *
 * Reads:
 *   - frontend/src/data/generated/quranTopicAtlas.json
 *   - frontend/src/data/quranTopicSeeds.ts (entity/story overlap)
 *
 * Writes:
 *   - frontend/src/data/generated/quranTopicClusters.json
 *   - docs/generated/quran-topic-clusters-summary.md
 *
 * Safety rules:
 *   - All clusters default to reviewStatus="needs_review".
 *   - Labels are heuristic; we never claim a cluster is tafsir.
 *   - coherenceScore is a transparent 0–1 fraction; reviewers see how it
 *     was computed.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { QURAN_TOPIC_SEEDS } from '../frontend/src/data/quranTopicSeeds';
import { TOPIC_TYPE_META } from '../frontend/src/types/quranTopicAtlas';
import type {
  QuranTopicAtlasOutput,
  QuranTopicCluster,
  QuranTopicClusterMethod,
  QuranTopicClustersOutput,
} from '../frontend/src/types/quranTopicAtlas';
import type { QuranReference } from '../frontend/src/types/quranEntityGraph';

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranTopicAtlas.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranTopicClusters.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-topic-clusters-summary.md');
const VERSION = '1.0.0';

const MIN_SHARED_AYAHS = 8;
const EMBEDDING_AVAILABLE = false;

interface TopicMeta {
  topicId: string;
  topicType: string;
  labelArabic: string;
  labelEnglish: string;
  relatedEntities: Set<string>;
  ayahKeys: Set<string>;
}

function loadAtlas(): QuranTopicAtlasOutput {
  if (!existsSync(ATLAS_PATH)) {
    throw new Error(`Missing ${ATLAS_PATH}; run scan-quran-topic-links.ts first.`);
  }
  return JSON.parse(readFileSync(ATLAS_PATH, 'utf-8')) as QuranTopicAtlasOutput;
}

function ayahKey(s: number, a: number): string {
  return `${s}:${a}`;
}

function parseAyahKey(k: string): QuranReference {
  const [s, a] = k.split(':').map(Number);
  return { surahNumber: s, ayahStart: a };
}

function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let inter = 0;
  for (const x of a) if (b.has(x)) inter += 1;
  const union = a.size + b.size - inter;
  return union === 0 ? 0 : inter / union;
}

// Union-Find (for graph_community)
class UnionFind {
  parent = new Map<string, string>();
  add(x: string): void {
    if (!this.parent.has(x)) this.parent.set(x, x);
  }
  find(x: string): string {
    let p = this.parent.get(x) ?? x;
    while (p !== this.parent.get(p)) {
      const gp = this.parent.get(p)!;
      this.parent.set(p, this.parent.get(gp) ?? gp);
      p = this.parent.get(p)!;
    }
    return p;
  }
  union(a: string, b: string): void {
    this.add(a);
    this.add(b);
    const ra = this.find(a);
    const rb = this.find(b);
    if (ra !== rb) this.parent.set(ra, rb);
  }
  components(): Map<string, string[]> {
    const out = new Map<string, string[]>();
    for (const k of this.parent.keys()) {
      const r = this.find(k);
      const arr = out.get(r) ?? [];
      arr.push(k);
      out.set(r, arr);
    }
    return out;
  }
}

function main(): void {
  const atlas = loadAtlas();
  const generatedAt = new Date().toISOString();

  // Per-topic meta from atlas
  const topics = new Map<string, TopicMeta>();
  for (const t of atlas.topics) {
    const seed = QURAN_TOPIC_SEEDS.find((s) => s.topicId === t.topicId);
    topics.set(t.topicId, {
      topicId: t.topicId,
      topicType: t.topicType,
      labelArabic: t.labelArabic,
      labelEnglish: t.labelEnglish,
      relatedEntities: new Set(seed?.relatedEntities ?? []),
      ayahKeys: new Set(t.ayahLinks.map((l) => ayahKey(l.surahNumber, l.ayahNumber))),
    });
  }

  const clusters: QuranTopicCluster[] = [];
  const byMethod: Partial<Record<QuranTopicClusterMethod, number>> = {};

  function addCluster(c: QuranTopicCluster) {
    clusters.push(c);
    byMethod[c.generatedBy] = (byMethod[c.generatedBy] ?? 0) + 1;
  }

  let nextId = 1;

  // ---------- Method 1: seed_taxonomy — group by topicType ----------
  const byType = new Map<string, string[]>();
  for (const t of topics.values()) {
    const arr = byType.get(t.topicType) ?? [];
    arr.push(t.topicId);
    byType.set(t.topicType, arr);
  }
  for (const [type, ids] of byType.entries()) {
    if (ids.length < 2) continue;
    const ayahKeys = new Set<string>();
    for (const id of ids) for (const k of topics.get(id)!.ayahKeys) ayahKeys.add(k);
    const refs = Array.from(ayahKeys).map(parseAyahKey).slice(0, 1000);
    const coverage = ayahKeys.size;
    const coherence = ids.length > 0 ? Math.min(1, coverage / (ids.length * 200)) : 0;
    addCluster({
      clusterId: `cluster_${String(nextId++).padStart(6, '0')}`,
      labelArabic: TOPIC_TYPE_META[type as keyof typeof TOPIC_TYPE_META]?.labelAr ?? type,
      labelEnglish: TOPIC_TYPE_META[type as keyof typeof TOPIC_TYPE_META]?.labelEn ?? type,
      memberTopicIds: [...ids],
      ayahReferences: refs,
      generatedBy: 'seed_taxonomy',
      coherenceScore: Math.round(coherence * 100) / 100,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: ['Seed-taxonomy cluster — grouped by topicType only; not a tafsir claim.'],
    });
  }

  // ---------- Method 2: entity_story_overlap ----------
  // For every pair of topics with shared `relatedEntities`, create one cluster.
  const topicList = Array.from(topics.values());
  for (let i = 0; i < topicList.length; i++) {
    for (let j = i + 1; j < topicList.length; j++) {
      const a = topicList[i];
      const b = topicList[j];
      const overlap = [...a.relatedEntities].filter((x) => b.relatedEntities.has(x));
      if (overlap.length === 0) continue;
      const jac = jaccard(a.relatedEntities, b.relatedEntities);
      if (jac < 0.05) continue;
      // Combined ayah keys (cap to 1000 references).
      const combined = new Set<string>();
      for (const k of a.ayahKeys) combined.add(k);
      for (const k of b.ayahKeys) combined.add(k);
      const refs = Array.from(combined).map(parseAyahKey).slice(0, 1000);
      addCluster({
        clusterId: `cluster_${String(nextId++).padStart(6, '0')}`,
        labelArabic: `${a.labelArabic} ↔ ${b.labelArabic}`,
        labelEnglish: `${a.labelEnglish} ↔ ${b.labelEnglish}`,
        memberTopicIds: [a.topicId, b.topicId],
        ayahReferences: refs,
        generatedBy: 'entity_story_overlap',
        coherenceScore: Math.round(jac * 100) / 100,
        reviewStatus: 'needs_review',
        humanReviewRequired: true,
        warnings: [`Shared entities: ${overlap.join(', ')}; needs_review.`],
      });
    }
  }

  // ---------- Method 3: graph_community over shared-ayah co-occurrence ----------
  // Build a graph where edge weight = |ayahKeys(a) ∩ ayahKeys(b)|;
  // union-find topics with weight >= MIN_SHARED_AYAHS.
  const uf = new UnionFind();
  for (const t of topicList) uf.add(t.topicId);
  for (let i = 0; i < topicList.length; i++) {
    for (let j = i + 1; j < topicList.length; j++) {
      const a = topicList[i];
      const b = topicList[j];
      let shared = 0;
      // Iterate the smaller set.
      const [small, large] = a.ayahKeys.size < b.ayahKeys.size ? [a.ayahKeys, b.ayahKeys] : [b.ayahKeys, a.ayahKeys];
      for (const k of small) {
        if (large.has(k)) {
          shared += 1;
          if (shared >= MIN_SHARED_AYAHS) break;
        }
      }
      if (shared >= MIN_SHARED_AYAHS) uf.union(a.topicId, b.topicId);
    }
  }
  const components = uf.components();
  for (const ids of components.values()) {
    if (ids.length < 2) continue;
    const ayahKeys = new Set<string>();
    let pairScoreSum = 0;
    let pairCount = 0;
    for (const id of ids) {
      const k = topics.get(id)!.ayahKeys;
      for (const x of k) ayahKeys.add(x);
    }
    // coherence: average pairwise Jaccard over ayahKeys
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        pairScoreSum += jaccard(topics.get(ids[i])!.ayahKeys, topics.get(ids[j])!.ayahKeys);
        pairCount += 1;
      }
    }
    const coherence = pairCount > 0 ? pairScoreSum / pairCount : 0;
    addCluster({
      clusterId: `cluster_${String(nextId++).padStart(6, '0')}`,
      labelArabic: `مجموعة قرآنية — ${ids.length} موضوعًا`,
      labelEnglish: `Quranic community — ${ids.length} topics`,
      memberTopicIds: [...ids].sort(),
      ayahReferences: Array.from(ayahKeys).map(parseAyahKey).slice(0, 1000),
      generatedBy: 'graph_community',
      coherenceScore: Math.round(coherence * 100) / 100,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings: [
        `Connected community over shared-ayah co-occurrence (threshold ${MIN_SHARED_AYAHS}); needs_review.`,
      ],
    });
  }

  // ---------- Method 4: embedding_clustering (deferred if model unavailable) ----------
  const warnings: string[] = [];
  if (!EMBEDDING_AVAILABLE) {
    warnings.push(
      'embedding_clustering deferred — no embedding model wired in this build. Re-enable by setting EMBEDDING_AVAILABLE=true.'
    );
  }

  // ---------- Emit ----------
  const out: QuranTopicClustersOutput = {
    version: VERSION,
    generatedAt,
    totalClusters: clusters.length,
    clustersByMethod: byMethod,
    clusters,
    warnings: [
      'All clusters default to needs_review. No tafsir is generated.',
      'Cluster labels are heuristic; reviewers may re-label.',
      ...warnings,
    ],
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(out, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push('# Quran Topic Clusters — Discovery Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Total clusters: **${clusters.length}**`);
  lines.push('');
  lines.push('## Clusters by method');
  lines.push('');
  lines.push('| Method | Count |');
  lines.push('|---|---:|');
  for (const [m, c] of Object.entries(byMethod)) lines.push(`| ${m} | ${c} |`);
  lines.push('');
  lines.push('## Sample clusters');
  lines.push('');
  for (const c of clusters.slice(0, 30)) {
    lines.push(`### ${c.labelEnglish}`);
    lines.push(`- method: \`${c.generatedBy}\``);
    lines.push(`- coherenceScore: ${c.coherenceScore}`);
    lines.push(`- members: ${c.memberTopicIds.join(', ')}`);
    lines.push(`- ayahReferences: ${c.ayahReferences.length}`);
    lines.push('');
  }
  lines.push('## Warnings');
  lines.push('');
  for (const w of out.warnings) lines.push(`- ${w}`);

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);
  console.log(`\nDone. clusters=${clusters.length}`);
}

main();
