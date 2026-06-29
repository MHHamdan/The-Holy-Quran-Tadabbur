/**
 * Quranic Calls Atlas — Relation Graph Builder
 *
 * Reads quranicCallsClassified.json and builds a lightweight relation graph:
 *   - Nodes: calls, surahs, addressee-types, caller-types, topics, prophets
 *   - Edges: CALL_IN_SURAH, CALLER, ADDRESSEE, RELATED_TOPIC, RELATED_PROPHET,
 *            SAME_ADDRESSEE (within same surah), SAME_CALL_PATTERN
 *
 * IMPORTANT:
 *   - All edges: reviewStatus = needs_review, humanReviewRequired = true
 *   - No Quran text is written into node metadata beyond minimal references
 *
 * Outputs:
 *   frontend/src/data/generated/quranicCallRelationGraph.json
 *
 * Usage:
 *   npx tsx scripts/build-quranic-call-relation-graph.ts
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const IN_JSON = join(ROOT, 'frontend/src/data/generated/quranicCallsClassified.json');
const OUT_JSON = join(ROOT, 'frontend/src/data/generated/quranicCallRelationGraph.json');

interface ClassifiedCall {
  callId: string;
  surahNumber: number;
  ayahNumber: number;
  ayahReference: string;
  surahNameAr: string;
  surahNameEn: string;
  callPattern: string;
  caller: { callerType: string; labelArabic?: string; labelEnglish?: string };
  addressee: { addresseeType: string; labelArabic: string; labelEnglish: string };
  callFunction: string;
  tone: string;
  relatedTopics: string[];
  relatedProphets: string[];
  confidence: number;
}

interface ClassifiedAtlas { totalClassified: number; calls: ClassifiedCall[] }

interface GraphNode {
  nodeId: string;
  nodeType: string;
  label: string;
  labelAr?: string;
  metadata: Record<string, unknown>;
}

interface GraphEdge {
  edgeId: string;
  edgeType: string;
  sourceId: string;
  targetId: string;
  confidence: number;
  reviewStatus: string;
  humanReviewRequired: boolean;
  evidenceReferences: unknown[];
  warnings: string[];
}

console.log('Loading classified data...');
const data: ClassifiedAtlas = JSON.parse(readFileSync(IN_JSON, 'utf-8'));
console.log(`Loaded ${data.totalClassified} calls`);

const nodesMap = new Map<string, GraphNode>();
const edges: GraphEdge[] = [];
let edgeIdx = 0;

function addNode(node: GraphNode): void {
  if (!nodesMap.has(node.nodeId)) nodesMap.set(node.nodeId, node);
}

function addEdge(type: string, source: string, target: string, confidence: number, refs: unknown[] = []): void {
  const edgeId = `edge_${edgeIdx++}`;
  edges.push({
    edgeId,
    edgeType: type,
    sourceId: source,
    targetId: target,
    confidence,
    reviewStatus: 'needs_review',
    humanReviewRequired: true,
    evidenceReferences: refs,
    warnings: confidence < 0.5 ? ['Low-confidence edge — needs review'] : [],
  });
}

// Track for SAME_ADDRESSEE edges (within-surah)
const surahAddresseeMap = new Map<string, string[]>(); // `${surah}_${addresseeType}` → callIds[]

for (const call of data.calls) {
  // ── Call node ──────────────────────────────────────────────────────────────
  const callNodeId = `call::${call.callId}`;
  addNode({
    nodeId: callNodeId,
    nodeType: 'call',
    label: `${call.ayahReference} — ${call.callPattern}`,
    metadata: {
      callId: call.callId,
      surahNumber: call.surahNumber,
      ayahNumber: call.ayahNumber,
      ayahReference: call.ayahReference,
      callPattern: call.callPattern,
      callFunction: call.callFunction,
      tone: call.tone,
      confidence: call.confidence,
      reviewStatus: 'needs_review',
    },
  });

  // ── Surah node ─────────────────────────────────────────────────────────────
  const surahNodeId = `surah::${call.surahNumber}`;
  addNode({
    nodeId: surahNodeId,
    nodeType: 'surah',
    label: call.surahNameEn,
    labelAr: call.surahNameAr,
    metadata: { surahNumber: call.surahNumber },
  });
  addEdge('CALL_IN_SURAH', callNodeId, surahNodeId, 1.0, [{ surahNumber: call.surahNumber, ayahStart: call.ayahNumber, sourceIds: ['quran_text'], evidenceType: 'quran_text_pattern' }]);

  // ── Caller node ────────────────────────────────────────────────────────────
  const callerType = call.caller.callerType;
  const callerNodeId = `caller::${callerType}`;
  addNode({
    nodeId: callerNodeId,
    nodeType: 'caller',
    label: call.caller.labelEnglish ?? callerType,
    labelAr: call.caller.labelArabic,
    metadata: { callerType, reviewStatus: 'needs_review' },
  });
  addEdge('CALLER', callNodeId, callerNodeId, call.confidence * 0.8);

  // ── Addressee node ─────────────────────────────────────────────────────────
  const addresseeType = call.addressee.addresseeType;
  const addresseeNodeId = `addressee::${addresseeType}`;
  addNode({
    nodeId: addresseeNodeId,
    nodeType: 'addressee',
    label: call.addressee.labelEnglish,
    labelAr: call.addressee.labelArabic,
    metadata: { addresseeType, reviewStatus: 'needs_review' },
  });
  addEdge('ADDRESSEE', callNodeId, addresseeNodeId, call.confidence);

  // ── Topic nodes ────────────────────────────────────────────────────────────
  for (const topic of call.relatedTopics) {
    const topicNodeId = `topic::${topic}`;
    addNode({ nodeId: topicNodeId, nodeType: 'topic', label: topic, labelAr: topic, metadata: { topic } });
    addEdge('RELATED_TOPIC', callNodeId, topicNodeId, 0.65);
  }

  // ── Prophet nodes ──────────────────────────────────────────────────────────
  for (const prophetId of call.relatedProphets) {
    const prophetNodeId = `prophet::${prophetId}`;
    addNode({ nodeId: prophetNodeId, nodeType: 'prophet', label: prophetId, metadata: { prophetId, reviewStatus: 'needs_review' } });
    addEdge('RELATED_PROPHET', callNodeId, prophetNodeId, 0.75);
  }

  // ── Track same-addressee within surah ─────────────────────────────────────
  const saKey = `${call.surahNumber}_${addresseeType}`;
  if (!surahAddresseeMap.has(saKey)) surahAddresseeMap.set(saKey, []);
  surahAddresseeMap.get(saKey)!.push(callNodeId);

  // ── Same call-pattern edges via pattern node ───────────────────────────────
  const patternNodeId = `pattern::${call.callPattern}`;
  addNode({ nodeId: patternNodeId, nodeType: 'entity', label: call.callPattern, metadata: { callPattern: call.callPattern } });
  addEdge('SAME_CALL_PATTERN', callNodeId, patternNodeId, 0.9);
}

// ── SAME_ADDRESSEE edges within each surah (pair-wise, capped at 20 per group) ──
for (const [, callIds] of surahAddresseeMap.entries()) {
  if (callIds.length < 2) continue;
  const limited = callIds.slice(0, 20);
  for (let i = 0; i < limited.length - 1; i++) {
    addEdge('SAME_ADDRESSEE', limited[i], limited[i + 1], 0.70);
  }
}

const nodes = Array.from(nodesMap.values());

const nodesByType: Record<string, number> = {};
const edgesByType: Record<string, number> = {};
for (const n of nodes) nodesByType[n.nodeType] = (nodesByType[n.nodeType] ?? 0) + 1;
for (const e of edges) edgesByType[e.edgeType] = (edgesByType[e.edgeType] ?? 0) + 1;

const graph = {
  version: '1.0.0-phase-y',
  generatedAt: new Date().toISOString(),
  totalNodes: nodes.length,
  totalEdges: edges.length,
  nodes,
  edges,
  summary: {
    nodesByType,
    edgesByType,
    needsReview: edges.length,
  },
};

writeFileSync(OUT_JSON, JSON.stringify(graph, null, 2), 'utf-8');
console.log(`\n✓ Written: ${OUT_JSON}`);

console.log('\n' + '='.repeat(60));
console.log('RELATION GRAPH COMPLETE');
console.log('='.repeat(60));
console.log(`Total nodes: ${nodes.length}`);
console.log(`Total edges: ${edges.length}`);
console.log('\nNodes by type:');
Object.entries(nodesByType).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('\nEdges by type:');
Object.entries(edgesByType).sort(([,a],[,b])=>b-a).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
console.log('='.repeat(60));
