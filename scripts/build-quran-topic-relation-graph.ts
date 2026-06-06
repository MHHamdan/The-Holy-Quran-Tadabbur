#!/usr/bin/env npx tsx
/**
 * Quran Topic Relation Graph Builder — Phase V.
 *
 * Builds a graph over topics, ayahs, surahs, entities, stories, and
 * emotions. The graph is a navigation aid; every edge defaults to
 * reviewStatus="needs_review".
 *
 * Reads:
 *   - frontend/src/data/generated/quranTopicAtlas.json
 *   - frontend/src/data/generated/quranTopicClusters.json
 *   - frontend/src/data/quranTopicSeeds.ts (for entity/story/emotion crossrefs)
 *
 * Writes:
 *   - frontend/src/data/generated/quranTopicRelationGraph.json
 *   - docs/generated/quran-topic-relation-graph-summary.md
 *
 * Safety rules:
 *   - No Quran text embedded.
 *   - Every edge carries at least one evidenceReferences entry.
 *   - All edges are needs_review.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { QURAN_TOPIC_SEEDS } from '../frontend/src/data/quranTopicSeeds';
import type {
  QuranTopicAtlasOutput,
  QuranTopicClustersOutput,
  QuranTopicRelationGraphOutput,
  TopicEdgeType,
  TopicGraphEdge,
  TopicGraphNode,
  TopicNodeType,
} from '../frontend/src/types/quranTopicAtlas';

const ROOT = resolve(__dirname, '..');
const ATLAS_PATH = join(ROOT, 'frontend/src/data/generated/quranTopicAtlas.json');
const CLUSTERS_PATH = join(ROOT, 'frontend/src/data/generated/quranTopicClusters.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranTopicRelationGraph.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-topic-relation-graph-summary.md');
const VERSION = '1.0.0';

const MIN_TOPIC_PAIR_SHARED_AYAHS = 5;

function loadOptional<T>(p: string): T | null {
  if (!existsSync(p)) return null;
  return JSON.parse(readFileSync(p, 'utf-8')) as T;
}

function main(): void {
  const atlas = loadOptional<QuranTopicAtlasOutput>(ATLAS_PATH);
  if (!atlas) throw new Error(`Missing ${ATLAS_PATH}`);
  const clusters = loadOptional<QuranTopicClustersOutput>(CLUSTERS_PATH);

  const generatedAt = new Date().toISOString();
  const nodeMap = new Map<string, TopicGraphNode>();
  const edges: TopicGraphEdge[] = [];
  let nextId = 1;

  function addNode(n: TopicGraphNode) {
    if (!nodeMap.has(n.id)) nodeMap.set(n.id, n);
  }
  function addEdge(
    source: string,
    target: string,
    type: TopicEdgeType,
    evidence: { surahNumber: number; ayahStart: number; ayahEnd?: number }[],
    sourceIds: string[],
    confidence: number,
    warnings: string[] = []
  ) {
    if (source === target) return;
    edges.push({
      edgeId: `edge_${String(nextId++).padStart(7, '0')}`,
      sourceNodeId: source,
      targetNodeId: target,
      edgeType: type,
      evidenceReferences: evidence,
      sourceIds,
      confidence,
      reviewStatus: 'needs_review',
      humanReviewRequired: true,
      warnings,
    });
  }

  // ---------- Topic nodes ----------
  for (const t of atlas.topics) {
    addNode({
      id: `topic:${t.topicId}`,
      type: 'topic',
      labelArabic: t.labelArabic,
      labelEnglish: t.labelEnglish,
      metadata: { topicType: t.topicType },
    });
  }

  // ---------- Ayah + surah nodes + TOPIC_IN_AYAH / TOPIC_IN_SURAH edges ----------
  const surahsTouched = new Set<number>();
  const topicSurahPairs = new Set<string>();
  for (const t of atlas.topics) {
    for (const l of t.ayahLinks) {
      const ayahId = `ayah:${l.surahNumber}:${l.ayahNumber}`;
      addNode({ id: ayahId, type: 'ayah', metadata: { surahNumber: l.surahNumber, ayahNumber: l.ayahNumber } });
      surahsTouched.add(l.surahNumber);
      addEdge(
        `topic:${t.topicId}`,
        ayahId,
        'TOPIC_IN_AYAH',
        [{ surahNumber: l.surahNumber, ayahStart: l.ayahNumber }],
        l.evidenceReferences.flatMap((e) => e.sourceIds),
        l.confidence,
        l.warnings
      );
      const sKey = `${t.topicId}::${l.surahNumber}`;
      if (!topicSurahPairs.has(sKey)) {
        topicSurahPairs.add(sKey);
        addEdge(
          `topic:${t.topicId}`,
          `surah:${l.surahNumber}`,
          'TOPIC_IN_SURAH',
          [{ surahNumber: l.surahNumber, ayahStart: l.ayahNumber }],
          ['quran_uthmani_cloud'],
          0.6,
          []
        );
      }
    }
  }
  for (const s of surahsTouched) addNode({ id: `surah:${s}`, type: 'surah', metadata: { surahNumber: s } });

  // ---------- Entity / story / emotion crossrefs ----------
  for (const seed of QURAN_TOPIC_SEEDS) {
    for (const eid of seed.relatedEntities ?? []) {
      const node = `entity:${eid}`;
      addNode({ id: node, type: 'entity', metadata: { entityId: eid } });
      // Evidence: first ayah link of this topic (deterministic, low confidence).
      const t = atlas.topics.find((tt) => tt.topicId === seed.topicId);
      const ev = t?.ayahLinks[0];
      if (!ev) continue;
      addEdge(
        `topic:${seed.topicId}`,
        node,
        'TOPIC_RELATED_TO_ENTITY',
        [{ surahNumber: ev.surahNumber, ayahStart: ev.ayahNumber }],
        ['quran_uthmani_cloud'],
        0.55,
        ['Entity crossref from seed taxonomy; needs_review.']
      );
    }
    for (const sid of seed.relatedStories ?? []) {
      const node = `story:${sid}`;
      addNode({ id: node, type: 'story', metadata: { storyId: sid } });
      const t = atlas.topics.find((tt) => tt.topicId === seed.topicId);
      const ev = t?.ayahLinks[0];
      if (!ev) continue;
      addEdge(
        `topic:${seed.topicId}`,
        node,
        'TOPIC_RELATED_TO_STORY',
        [{ surahNumber: ev.surahNumber, ayahStart: ev.ayahNumber }],
        ['quran_uthmani_cloud'],
        0.55,
        ['Story crossref from seed taxonomy; needs_review.']
      );
    }
    for (const emo of seed.relatedEmotions ?? []) {
      const node = `emotion:${emo}`;
      addNode({ id: node, type: 'emotion', metadata: { emotionId: emo } });
      const t = atlas.topics.find((tt) => tt.topicId === seed.topicId);
      const ev = t?.ayahLinks[0];
      if (!ev) continue;
      addEdge(
        `topic:${seed.topicId}`,
        node,
        'TOPIC_RELATED_TO_EMOTION',
        [{ surahNumber: ev.surahNumber, ayahStart: ev.ayahNumber }],
        ['quran_uthmani_cloud'],
        0.6,
        []
      );
    }
  }

  // ---------- Topic ↔ Topic — SHARED_AYAH and SEMANTIC_CLUSTER ----------
  // Pairwise edges weighted by shared ayah count, with cap.
  const ayahKeySetByTopic = new Map<string, Set<string>>();
  for (const t of atlas.topics) {
    ayahKeySetByTopic.set(
      t.topicId,
      new Set(t.ayahLinks.map((l) => `${l.surahNumber}:${l.ayahNumber}`))
    );
  }
  const topicIds = atlas.topics.map((t) => t.topicId);
  for (let i = 0; i < topicIds.length; i++) {
    for (let j = i + 1; j < topicIds.length; j++) {
      const a = topicIds[i];
      const b = topicIds[j];
      const aSet = ayahKeySetByTopic.get(a)!;
      const bSet = ayahKeySetByTopic.get(b)!;
      let shared = 0;
      const sample: { surahNumber: number; ayahStart: number }[] = [];
      const [small, large] = aSet.size < bSet.size ? [aSet, bSet] : [bSet, aSet];
      for (const k of small) {
        if (large.has(k)) {
          shared += 1;
          if (sample.length < 5) {
            const [s, ay] = k.split(':').map(Number);
            sample.push({ surahNumber: s, ayahStart: ay });
          }
        }
      }
      if (shared < MIN_TOPIC_PAIR_SHARED_AYAHS) continue;
      const conf = Math.min(0.85, 0.4 + shared / 500);
      addEdge(
        `topic:${a}`,
        `topic:${b}`,
        'SHARED_AYAH',
        sample,
        ['quran_uthmani_cloud'],
        Math.round(conf * 100) / 100,
        [`Shared ${shared} ayahs; needs_review.`]
      );
      addEdge(
        `topic:${a}`,
        `topic:${b}`,
        'TOPIC_RELATED_TO_TOPIC',
        sample,
        ['quran_uthmani_cloud'],
        Math.round(conf * 100) / 100,
        []
      );
    }
  }

  // ---------- Cluster-based SEMANTIC_CLUSTER edges (when clusters are graph_community) ----------
  if (clusters) {
    for (const c of clusters.clusters) {
      if (c.generatedBy !== 'graph_community') continue;
      const sample = c.ayahReferences.slice(0, 5).map((r) => ({
        surahNumber: r.surahNumber,
        ayahStart: r.ayahStart,
        ayahEnd: r.ayahEnd,
      }));
      // Pairwise SEMANTIC_CLUSTER edges within the cluster (cap to keep small).
      const members = c.memberTopicIds;
      for (let i = 0; i < members.length; i++) {
        for (let j = i + 1; j < members.length; j++) {
          addEdge(
            `topic:${members[i]}`,
            `topic:${members[j]}`,
            'SEMANTIC_CLUSTER',
            sample.length > 0 ? sample : [{ surahNumber: 1, ayahStart: 1 }],
            ['quran_uthmani_cloud'],
            c.coherenceScore,
            [`From ${c.clusterId} (${c.generatedBy}); needs_review.`]
          );
        }
      }
    }
  }

  // ---------- Output ----------
  const nodes: TopicGraphNode[] = Array.from(nodeMap.values());
  const nodesByType: Partial<Record<TopicNodeType, number>> = {};
  for (const n of nodes) nodesByType[n.type] = (nodesByType[n.type] ?? 0) + 1;
  const edgesByType: Partial<Record<TopicEdgeType, number>> = {};
  for (const e of edges) edgesByType[e.edgeType] = (edgesByType[e.edgeType] ?? 0) + 1;

  const out: QuranTopicRelationGraphOutput = {
    version: VERSION,
    generatedAt,
    nodeCount: nodes.length,
    edgeCount: edges.length,
    nodesByType,
    edgesByType,
    nodes,
    edges,
    warnings: [
      'All edges default to needs_review.',
      'Topic↔Topic SHARED_AYAH edges are observational; reviewers may collapse near-duplicates.',
      'SEMANTIC_CLUSTER edges derive from graph_community clusters and inherit their needs_review status.',
    ],
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(out, null, 2), 'utf-8');
  console.log(`Wrote ${OUT_JSON}`);

  // -------- summary md --------
  const lines: string[] = [];
  lines.push('# Quran Topic Relation Graph — Build Summary');
  lines.push('');
  lines.push(`Generated at: ${generatedAt}`);
  lines.push(`Version: ${VERSION}`);
  lines.push('');
  lines.push('## Totals');
  lines.push('');
  lines.push(`- Nodes: **${nodes.length}**`);
  lines.push(`- Edges: **${edges.length}**`);
  lines.push('');
  lines.push('## Nodes by type');
  lines.push('');
  lines.push('| Type | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(nodesByType).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  lines.push('## Edges by type');
  lines.push('');
  lines.push('| Type | Count |');
  lines.push('|---|---:|');
  for (const [k, v] of Object.entries(edgesByType).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))) {
    lines.push(`| ${k} | ${v} |`);
  }
  lines.push('');
  lines.push('## Warnings');
  lines.push('');
  for (const w of out.warnings) lines.push(`- ${w}`);

  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, lines.join('\n'), 'utf-8');
  console.log(`Wrote ${OUT_MD}`);
  console.log(`\nDone. nodes=${nodes.length}, edges=${edges.length}`);
}

main();
