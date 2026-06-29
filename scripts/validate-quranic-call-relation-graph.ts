/**
 * Validator: quranicCallRelationGraph.json
 * Exits 0 if valid, 1 otherwise.
 */
import { readFileSync } from 'fs';
import { resolve, join } from 'path';

const ROOT = resolve(__dirname, '..');
const FILE = join(ROOT, 'frontend/src/data/generated/quranicCallRelationGraph.json');

let errors = 0;

function error(msg: string) { console.error(`  ✗ ERROR: ${msg}`); errors++; }

console.log('Validating quranicCallRelationGraph.json…');

let graph: Record<string, unknown>;
try {
  graph = JSON.parse(readFileSync(FILE, 'utf-8'));
} catch (e) {
  error(`Cannot parse JSON: ${e}`);
  process.exit(1);
}

for (const f of ['version', 'generatedAt', 'totalNodes', 'totalEdges', 'nodes', 'edges', 'summary']) {
  if (!(f in graph)) error(`Missing field: ${f}`);
}

const nodes = (graph.nodes ?? []) as Record<string, unknown>[];
const edges = (graph.edges ?? []) as Record<string, unknown>[];

if (!Array.isArray(nodes)) { error('nodes must be array'); process.exit(1); }
if (!Array.isArray(edges)) { error('edges must be array'); process.exit(1); }
if (nodes.length === 0) error('nodes array is empty');
if (edges.length === 0) error('edges array is empty');

const VALID_NODE_TYPES = new Set(['call','ayah','surah','caller','addressee','topic','prophet','story','entity']);
const VALID_EDGE_TYPES = new Set([
  'CALL_IN_AYAH','CALL_IN_SURAH','CALLER','ADDRESSEE','CALL_FUNCTION','RELATED_TOPIC',
  'RELATED_STORY','RELATED_PROPHET','SAME_ADDRESSEE','SAME_CALL_PATTERN','SAME_FUNCTION','NEEDS_REVIEW',
]);

const nodeIds = new Set<string>();
for (let i = 0; i < nodes.length; i++) {
  const n = nodes[i];
  if (!n.nodeId) error(`node[${i}] missing nodeId`);
  else {
    if (nodeIds.has(n.nodeId as string)) error(`Duplicate nodeId: ${n.nodeId}`);
    nodeIds.add(n.nodeId as string);
  }
  if (!VALID_NODE_TYPES.has(n.nodeType as string)) error(`node[${i}] unknown nodeType: ${n.nodeType}`);
  if (!n.label) error(`node[${i}] missing label`);
}

const edgeIds = new Set<string>();
for (let i = 0; i < edges.length; i++) {
  const e = edges[i];
  if (!e.edgeId) error(`edge[${i}] missing edgeId`);
  else {
    if (edgeIds.has(e.edgeId as string)) error(`Duplicate edgeId: ${e.edgeId}`);
    edgeIds.add(e.edgeId as string);
  }
  if (!VALID_EDGE_TYPES.has(e.edgeType as string)) error(`edge[${i}] unknown edgeType: ${e.edgeType}`);
  if (!nodeIds.has(e.sourceId as string)) error(`edge[${i}] sourceId not in nodes: ${e.sourceId}`);
  if (!nodeIds.has(e.targetId as string)) error(`edge[${i}] targetId not in nodes: ${e.targetId}`);
  if (e.humanReviewRequired !== true) error(`edge[${i}] humanReviewRequired must be true`);
  if (e.reviewStatus !== 'needs_review') error(`edge[${i}] reviewStatus must be needs_review`);
}

console.log(`Validated ${nodes.length} nodes, ${edges.length} edges. Errors: ${errors}`);
if (errors > 0) { console.error('✗ Validation FAILED'); process.exit(1); }
console.log('✓ Validation PASSED');
