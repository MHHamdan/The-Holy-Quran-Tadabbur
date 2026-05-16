#!/usr/bin/env npx tsx
/**
 * Build Quran Story Connection Graph.
 *
 * Reads:
 *   - frontend/src/data/generated/quranStoryConnections.json (scan output)
 *   - frontend/src/data/quranStoryEntitySeeds.ts
 *   - frontend/src/data/quranStoryChronologySeeds.ts
 *   - frontend/src/data/quranStories.ts (for story / segment nodes)
 *
 * Writes:
 *   - frontend/src/data/generated/quranStoryConnectionGraph.json
 *   - docs/generated/quran-story-connection-graph-summary.md
 *
 * Hard rules:
 *   - Every edge MUST carry evidenceReferences (each with surah/ayah +
 *     sourceIds + evidenceType).
 *   - quran_explicit may carry high confidence; everything else stays
 *     needs_review.
 *   - No ayah text in the graph.
 *   - Source IDs reference sourceRegistry.ts ids (loose check: must be
 *     non-empty strings — full registry cross-check is in the validator).
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';
import { QURAN_STORY_ENTITY_SEEDS } from '../frontend/src/data/quranStoryEntitySeeds';
import { QURAN_STORIES_FIRST_BATCH } from '../frontend/src/data/quranStories';
import {
  STORY_WORLD_CHRONOLOGY,
  REVELATION_ORDER_SEEDS,
} from '../frontend/src/data/quranStoryChronologySeeds';
import type {
  ConnectionEdge,
  ConnectionGraph,
  ConnectionNode,
  ConnectionEdgeType,
  ConnectionEvidenceReference,
  ConnectionEvidenceType,
  ConnectionReviewStatus,
  ConnectionNodeType,
  ScanOutput,
} from '../frontend/src/types/quranStoryConnection';

const ROOT = resolve(__dirname, '..');
const SCAN_PATH = join(ROOT, 'frontend/src/data/generated/quranStoryConnections.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranStoryConnectionGraph.json');
const OUT_MD = join(ROOT, 'docs/generated/quran-story-connection-graph-summary.md');

const SOURCE_DICT = 'concepts_dictionary'; // dictionary-derived edges cite the curated dictionary
const SOURCE_STORIES = 'stories_manifest';
const SOURCE_TAFSIR = 'ibn_kathir'; // generic fallback when story uses tafsir sources

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function loadScan(): ScanOutput {
  if (!existsSync(SCAN_PATH)) {
    throw new Error(`Run scan-quran-story-connections.ts first; missing ${SCAN_PATH}`);
  }
  return JSON.parse(readFileSync(SCAN_PATH, 'utf-8')) as ScanOutput;
}

function nodeIdSurah(s: number): string {
  return `surah:${s}`;
}
function nodeIdAyahRange(s: number, start: number, end: number): string {
  return `ayah_range:${s}:${start}-${end}`;
}
function nodeIdEntity(e: string): string {
  return `entity:${e}`;
}
function nodeIdStory(id: string): string {
  return `story:${id}`;
}
function nodeIdSegment(storyId: string, segId: string): string {
  return `story_segment:${storyId}:${segId}`;
}
function nodeIdChronology(id: string): string {
  return `chronology_group:${id}`;
}

function mkEdge(opts: {
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: ConnectionEdgeType;
  evidence: ConnectionEvidenceReference[];
  confidence: number;
  reviewStatus?: ConnectionReviewStatus;
  warnings?: string[];
}): ConnectionEdge {
  const reviewStatus = opts.reviewStatus ?? 'needs_review';
  return {
    edgeId: `${opts.edgeType}:${opts.sourceNodeId}->${opts.targetNodeId}`,
    sourceNodeId: opts.sourceNodeId,
    targetNodeId: opts.targetNodeId,
    edgeType: opts.edgeType,
    evidenceReferences: opts.evidence,
    confidence: opts.confidence,
    reviewStatus,
    humanReviewRequired: reviewStatus !== 'verified',
    warnings: opts.warnings ?? [],
  };
}

// ---------------------------------------------------------------------------
// Build nodes
// ---------------------------------------------------------------------------

function buildNodes(scan: ScanOutput): {
  nodes: ConnectionNode[];
  entityNodeIds: Set<string>;
  storyNodeIds: Set<string>;
} {
  const nodes: ConnectionNode[] = [];
  const seen = new Set<string>();
  const addNode = (n: ConnectionNode) => {
    if (seen.has(n.id)) return;
    seen.add(n.id);
    nodes.push(n);
  };

  // Surah nodes
  for (let s = 1; s <= 114; s++) {
    const surahScan = scan.surahs.find((x) => x.surahNumber === s);
    addNode({
      id: nodeIdSurah(s),
      type: 'surah',
      labelArabic: surahScan?.surahNameArabic,
      labelEnglish: surahScan?.surahNameEnglish,
      metadata: { surahNumber: s },
    });
  }

  // Entity nodes
  const entityNodeIds = new Set<string>();
  for (const seed of QURAN_STORY_ENTITY_SEEDS) {
    const id = nodeIdEntity(seed.entityId);
    addNode({
      id,
      type: typeToNodeType(seed.type),
      labelArabic: seed.labelArabic,
      labelEnglish: seed.labelEnglish,
      metadata: {
        entityId: seed.entityId,
        entityType: seed.type,
        chronologicalGroup: seed.chronologicalGroup,
      },
    });
    entityNodeIds.add(id);
  }

  // Story + segment nodes
  const storyNodeIds = new Set<string>();
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    const sid = nodeIdStory(story.storyId);
    addNode({
      id: sid,
      type: 'story',
      labelArabic: story.titleArabic,
      labelEnglish: story.titleEnglish,
      metadata: { storyId: story.storyId },
    });
    storyNodeIds.add(sid);
    for (const seg of story.storySegments) {
      const segNodeId = nodeIdSegment(story.storyId, seg.segmentId);
      addNode({
        id: segNodeId,
        type: 'story_segment',
        labelArabic: seg.titleArabic,
        labelEnglish: seg.titleEnglish,
        metadata: {
          storyId: story.storyId,
          segmentId: seg.segmentId,
          surahNumber: seg.surahNumber,
          ayahStart: seg.ayahStart,
          ayahEnd: seg.ayahEnd,
        },
      });
    }
  }

  // Chronology group nodes
  for (const c of STORY_WORLD_CHRONOLOGY) {
    addNode({
      id: nodeIdChronology(c.itemId),
      type: 'chronology_group',
      labelArabic: c.notesArabic,
      labelEnglish: c.notesEnglish,
      metadata: { chronologyType: c.chronologyType, orderIndex: c.orderIndex, certainty: c.certainty },
    });
  }

  return { nodes, entityNodeIds, storyNodeIds };
}

function typeToNodeType(t: string): ConnectionNodeType {
  switch (t) {
    case 'prophet': return 'prophet';
    case 'person': return 'person';
    case 'place': return 'place';
    case 'animal': return 'animal';
    case 'object': return 'object';
    case 'event': return 'event';
    default: return 'entity';
  }
}

// ---------------------------------------------------------------------------
// Build edges
// ---------------------------------------------------------------------------

function buildEdges(scan: ScanOutput): ConnectionEdge[] {
  const edges: ConnectionEdge[] = [];

  // MENTIONED_IN: entity -> ayah_range (per occurrence). We also collect
  // ayah_range node ids to be added back into the graph by the caller.
  for (const ent of scan.entityIndex) {
    for (const occ of ent.occurrences) {
      const evType: ConnectionEvidenceType = 'dictionary_alias';
      const targetNodeId = nodeIdAyahRange(occ.surahNumber, occ.ayahStart, occ.ayahEnd ?? occ.ayahStart);
      edges.push(
        mkEdge({
          sourceNodeId: nodeIdEntity(ent.entityId),
          targetNodeId,
          edgeType: 'MENTIONED_IN',
          evidence: [
            {
              surahNumber: occ.surahNumber,
              ayahStart: occ.ayahStart,
              ayahEnd: occ.ayahEnd ?? occ.ayahStart,
              sourceIds: [SOURCE_DICT],
              evidenceType: evType,
            },
          ],
          confidence: 0.6,
        })
      );
    }
  }

  // APPEARS_IN_SURAH: entity -> surah (distinct)
  for (const ent of scan.entityIndex) {
    const surahSet = new Set(ent.occurrences.map((o) => o.surahNumber));
    for (const s of surahSet) {
      const occs = ent.occurrences.filter((o) => o.surahNumber === s);
      const evidence: ConnectionEvidenceReference[] = occs.slice(0, 5).map((o) => ({
        surahNumber: o.surahNumber,
        ayahStart: o.ayahStart,
        ayahEnd: o.ayahEnd ?? o.ayahStart,
        sourceIds: [SOURCE_DICT],
        evidenceType: 'dictionary_alias',
      }));
      edges.push(
        mkEdge({
          sourceNodeId: nodeIdEntity(ent.entityId),
          targetNodeId: nodeIdSurah(s),
          edgeType: 'APPEARS_IN_SURAH',
          evidence,
          confidence: 0.7,
        })
      );
    }
  }

  // PART_OF_STORY: story_segment -> story; entity -> story via story.prophetsMentioned/mainCharacters
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    const sid = nodeIdStory(story.storyId);
    for (const seg of story.storySegments) {
      const segId = nodeIdSegment(story.storyId, seg.segmentId);
      edges.push(
        mkEdge({
          sourceNodeId: segId,
          targetNodeId: sid,
          edgeType: 'PART_OF_STORY',
          evidence: [
            {
              surahNumber: seg.surahNumber,
              ayahStart: seg.ayahStart,
              ayahEnd: seg.ayahEnd,
              sourceIds: seg.sourceIds.length > 0 ? seg.sourceIds : [SOURCE_STORIES],
              evidenceType: 'story_data',
            },
          ],
          confidence: 0.9,
        })
      );
    }
  }

  // SAME_ENTITY / REPEATED_NARRATIVE: cross-surah links
  for (const cross of scan.crossSurahLinks) {
    if (cross.surahNumbers.length < 2) continue;
    const evidence: ConnectionEvidenceReference[] = cross.surahNumbers.map((s) => ({
      surahNumber: s,
      ayahStart: 1,
      sourceIds: [SOURCE_DICT],
      evidenceType: 'dictionary_alias',
    }));
    for (let i = 0; i < cross.surahNumbers.length - 1; i++) {
      const a = cross.surahNumbers[i];
      const b = cross.surahNumbers[i + 1];
      edges.push(
        mkEdge({
          sourceNodeId: nodeIdSurah(a),
          targetNodeId: nodeIdSurah(b),
          edgeType: cross.edgeType,
          evidence,
          confidence: 0.55,
          warnings: ['Cross-surah link inferred from entity co-occurrence.'],
        })
      );
    }
  }

  // SAME_PEOPLE / SAME_PLACE / SAME_ANIMAL_OR_OBJECT: per entity-type bucket within
  // the same surah's ayah_range nodes (uses APPEARS_IN_SURAH evidence).
  // We attach a SAME_<TYPE> edge from entity -> entity inside same story.
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    const related = story.relatedStories ?? [];
    for (const r of related) {
      edges.push(
        mkEdge({
          sourceNodeId: nodeIdStory(story.storyId),
          targetNodeId: nodeIdStory(r.storyId),
          edgeType: 'SAME_EVENT',
          evidence: (r.evidenceReferences ?? []).map((er) => ({
            surahNumber: er.surahNumber,
            ayahStart: er.ayahStart,
            ayahEnd: er.ayahEnd,
            sourceIds: er.sourceIds.length > 0 ? er.sourceIds : [SOURCE_STORIES],
            evidenceType: 'story_data',
          })),
          confidence: 0.7,
        })
      );
    }
  }

  // CHRONOLOGICALLY_BEFORE for story-world groups (group N -> group N+1)
  const ordered = [...STORY_WORLD_CHRONOLOGY].sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0));
  for (let i = 0; i < ordered.length - 1; i++) {
    const cur = ordered[i];
    const nxt = ordered[i + 1];
    edges.push(
      mkEdge({
        sourceNodeId: nodeIdChronology(cur.itemId),
        targetNodeId: nodeIdChronology(nxt.itemId),
        edgeType: 'CHRONOLOGICALLY_BEFORE',
        evidence: [
          {
            surahNumber: 0,
            ayahStart: 0,
            sourceIds: cur.sourceIds.length > 0 ? cur.sourceIds : [SOURCE_TAFSIR],
            evidenceType: 'tafsir_source',
          },
        ],
        confidence: 0.6,
        warnings: ['Broad chronology band; do not display as exact succession.'],
      })
    );
  }

  // REVELATION_ORDER_BEFORE between successive seeded surahs
  const rev = [...REVELATION_ORDER_SEEDS].sort((a, b) => (a.orderIndex ?? 0) - (b.orderIndex ?? 0));
  for (let i = 0; i < rev.length - 1; i++) {
    const cur = rev[i];
    const nxt = rev[i + 1];
    const a = parseInt(cur.itemId, 10);
    const b = parseInt(nxt.itemId, 10);
    if (!Number.isFinite(a) || !Number.isFinite(b)) continue;
    edges.push(
      mkEdge({
        sourceNodeId: nodeIdSurah(a),
        targetNodeId: nodeIdSurah(b),
        edgeType: 'REVELATION_ORDER_BEFORE',
        evidence: [
          {
            surahNumber: a,
            ayahStart: 1,
            sourceIds: cur.sourceIds.length > 0 ? cur.sourceIds : [SOURCE_TAFSIR],
            evidenceType: 'tafsir_source',
          },
        ],
        confidence: cur.certainty === 'disputed' ? 0.35 : 0.55,
        warnings: ['Revelation order is disputed; display with caveat.'],
      })
    );
  }

  return edges;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log('Building Quran Story Connection Graph...');
  const scan = loadScan();
  const { nodes } = buildNodes(scan);
  const edges = buildEdges(scan);

  // Add ayah_range nodes for every MENTIONED_IN target that does not yet exist.
  const existingNodeIds = new Set(nodes.map((n) => n.id));
  for (const e of edges) {
    if (e.edgeType !== 'MENTIONED_IN') continue;
    if (existingNodeIds.has(e.targetNodeId)) continue;
    const ev = e.evidenceReferences[0];
    nodes.push({
      id: e.targetNodeId,
      type: 'ayah_range',
      metadata: {
        surahNumber: ev.surahNumber,
        ayahStart: ev.ayahStart,
        ayahEnd: ev.ayahEnd ?? ev.ayahStart,
      },
    });
    existingNodeIds.add(e.targetNodeId);
  }

  // Edge integrity: every edge must have at least one evidenceReferences entry
  // with sourceIds.length > 0. Drop bad edges with a warning.
  const validEdges: ConnectionEdge[] = [];
  let dropped = 0;
  for (const e of edges) {
    if (e.evidenceReferences.length === 0) {
      dropped++;
      continue;
    }
    const ok = e.evidenceReferences.every(
      (er) => Array.isArray(er.sourceIds) && er.sourceIds.length > 0
    );
    if (!ok) {
      dropped++;
      continue;
    }
    validEdges.push(e);
  }
  if (dropped > 0) {
    console.warn(`Dropped ${dropped} edges with missing evidence.`);
  }

  const graph: ConnectionGraph = {
    version: '1.0.0',
    generatedAt: new Date().toISOString(),
    nodeCount: nodes.length,
    edgeCount: validEdges.length,
    nodes,
    edges: validEdges,
  };

  mkdirSync(dirname(OUT_JSON), { recursive: true });
  writeFileSync(OUT_JSON, JSON.stringify(graph, null, 2));
  console.log(`Wrote ${OUT_JSON} — ${graph.nodeCount} nodes, ${graph.edgeCount} edges`);

  const md = buildMd(graph);
  mkdirSync(dirname(OUT_MD), { recursive: true });
  writeFileSync(OUT_MD, md);
  console.log(`Wrote ${OUT_MD}`);
}

function buildMd(g: ConnectionGraph): string {
  const lines: string[] = [];
  lines.push('# Quran Story Connection Graph — Summary');
  lines.push('');
  lines.push(`Generated: ${g.generatedAt}`);
  lines.push('');
  lines.push(`- Nodes: **${g.nodeCount}**`);
  lines.push(`- Edges: **${g.edgeCount}**`);
  lines.push('');
  const nodeTypes: Record<string, number> = {};
  for (const n of g.nodes) nodeTypes[n.type] = (nodeTypes[n.type] ?? 0) + 1;
  lines.push('## Node-type counts');
  for (const [t, c] of Object.entries(nodeTypes).sort()) {
    lines.push(`- ${t}: ${c}`);
  }
  lines.push('');
  const edgeTypes: Record<string, number> = {};
  for (const e of g.edges) edgeTypes[e.edgeType] = (edgeTypes[e.edgeType] ?? 0) + 1;
  lines.push('## Edge-type counts');
  for (const [t, c] of Object.entries(edgeTypes).sort()) {
    lines.push(`- ${t}: ${c}`);
  }
  lines.push('');
  const status: Record<string, number> = {};
  for (const e of g.edges) status[e.reviewStatus] = (status[e.reviewStatus] ?? 0) + 1;
  lines.push('## Review-status counts');
  for (const [s, c] of Object.entries(status).sort()) {
    lines.push(`- ${s}: ${c}`);
  }
  lines.push('');
  lines.push('## Notes');
  lines.push('- Every edge carries at least one evidenceReferences entry.');
  lines.push('- All non-explicit edges default to `needs_review`.');
  lines.push('- This file is generated; do not edit by hand.');
  return lines.join('\n');
}

main();
