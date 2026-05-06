#!/usr/bin/env npx tsx
/**
 * Phase 5: Quran Knowledge Graph Validator
 *
 * Validates the generated KG JSON for integrity:
 *   1. All ayah node references use valid sura:aya format
 *   2. All edge endpoints reference existing nodes
 *   3. All sourceIds are from the active tafseer_sources list (or system markers)
 *   4. Every public edge has evidence
 *   5. Semantic-only edges are experimental
 *   6. No approved edge has humanReviewRequired=true
 *   7. Edge weights are in [0, 1]
 *   8. No duplicate edge IDs
 *   9. Story-derived edges reference existing storyIds
 *  10. RelationStatus values are valid
 *  11. GeneratedBy values are valid
 *  12. Warnings exist for needs_review/experimental edges
 *  13. No Quran text embedded in KG
 *
 * Exit code 0 = all checks pass.
 * Exit code 1 = one or more checks failed.
 */

import * as fs from "fs";
import * as path from "path";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = path.resolve(__dirname, "..");
const KG_PATH = path.join(ROOT, "frontend", "src", "data", "generated", "quranKnowledgeGraph.json");
const STORIES_PATH = path.join(ROOT, "data", "manifests", "stories.json");
const TAFSEER_SOURCES_PATH = path.join(ROOT, "data", "manifests", "tafseer_sources.json");

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const VALID_RELATION_STATUSES = new Set(["approved", "needs_review", "experimental"]);
const VALID_GENERATED_BY = new Set(["rule", "tafsir", "story", "semantic_embedding", "manual_review"]);
const SYSTEM_SOURCE_IDS = new Set(["story_manifest", "system:embedding"]);

// Arabic character range detector — flags if Quran text is embedded
const ARABIC_REGEX = /[؀-ۿ]{10,}/;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let errors = 0;
let warnings_count = 0;
const log = (msg: string) => console.log(`  ${msg}`);
const err = (msg: string) => { console.error(`  [ERROR] ${msg}`); errors++; };
const warn = (msg: string) => { console.warn(`  [WARN]  ${msg}`); warnings_count++; };
const ok = (msg: string) => console.log(`  [OK]    ${msg}`);

function check(name: string, fn: () => void): void {
  console.log(`\nChecking: ${name}`);
  fn();
}

// ---------------------------------------------------------------------------
// Load data
// ---------------------------------------------------------------------------

function loadKG(): any {
  if (!fs.existsSync(KG_PATH)) {
    console.error(`KG file not found: ${KG_PATH}`);
    console.error("Run: npx tsx scripts/build-quran-knowledge-graph.ts");
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(KG_PATH, "utf-8"));
}

function loadStoryIds(): Set<string> {
  if (!fs.existsSync(STORIES_PATH)) return new Set();
  const data = JSON.parse(fs.readFileSync(STORIES_PATH, "utf-8"));
  const ids = new Set<string>();
  for (const s of data.stories ?? []) {
    ids.add(s.id);
    for (const seg of s.segments ?? []) ids.add(seg.id);
  }
  return ids;
}

function loadActiveSources(): Set<string> {
  if (!fs.existsSync(TAFSEER_SOURCES_PATH)) {
    warn("tafseer_sources.json not found — using fallback active source list");
    return new Set(["ibn_kathir", "ibn_kathir_ar", "ibn_kathir_en", "muyassar_ar", "saadi_ar", "saadi_en", "sahih_international", "tafheem_en"]);
  }
  const data = JSON.parse(fs.readFileSync(TAFSEER_SOURCES_PATH, "utf-8"));
  const sources: any[] = data.sources ?? data.active_sources ?? [];
  const active = sources
    .filter((s: any) => s.is_enabled !== false && !s.license_pending)
    .map((s: any) => s.id ?? s.source_id ?? s);
  return new Set([...active.filter(Boolean), ...SYSTEM_SOURCE_IDS]);
}

// ---------------------------------------------------------------------------
// Validation checks
// ---------------------------------------------------------------------------

function validateNodeIds(nodes: any[]): void {
  const seen = new Set<string>();
  let dup = 0;
  let badFormat = 0;

  for (const node of nodes) {
    if (seen.has(node.id)) {
      err(`Duplicate node ID: ${node.id}`);
      dup++;
    }
    seen.add(node.id);

    if (node.type === "ayah") {
      const parts = node.id.split(":");
      if (parts.length !== 3 || parts[0] !== "ayah") {
        err(`Ayah node has invalid ID format: ${node.id} (expected ayah:sura:aya)`);
        badFormat++;
      }
    }
  }

  if (dup === 0) ok(`No duplicate node IDs`);
  if (badFormat === 0) ok(`All ayah node IDs have correct format`);
  ok(`Total nodes: ${nodes.length}`);
}

const AYAH_ID_PATTERN = /^ayah:\d{1,3}:\d{1,3}$/;

function isValidAyahId(nodeId: string): boolean {
  if (!AYAH_ID_PATTERN.test(nodeId)) return false;
  const [, sura, aya] = nodeId.split(":").map(Number);
  return sura >= 1 && sura <= 114 && aya >= 1 && aya <= 286;
}

function validateEdgeEndpoints(edges: any[], nodeIds: Set<string>): void {
  // Ayah nodes live in the database, not in the KG JSON file.
  // We validate ayah node IDs by format rather than set membership.
  // Non-ayah endpoints must exist in the node set.
  let missing = 0;
  let badAyah = 0;

  for (const edge of edges) {
    for (const endpointKey of ["sourceNodeId", "targetNodeId"]) {
      const nid: string = edge[endpointKey];
      if (nid.startsWith("ayah:")) {
        if (!isValidAyahId(nid)) {
          err(`Edge ${edge.id}: ${endpointKey} "${nid}" has invalid ayah format (ayah:sura:aya, sura 1–114)`);
          badAyah++;
        }
      } else {
        if (!nodeIds.has(nid)) {
          err(`Edge ${edge.id}: ${endpointKey} "${nid}" not in node set`);
          missing++;
        }
      }
    }
  }

  if (missing === 0 && badAyah === 0) ok(`All edge endpoints are valid`);
  else if (badAyah > 0) ok(`Non-ayah endpoints: ${missing} missing (ayah nodes live in DB)`);
}

function validateEdgeWeights(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (typeof edge.weight !== "number" || edge.weight < 0 || edge.weight > 1) {
      err(`Edge ${edge.id}: weight ${edge.weight} is outside [0, 1]`);
      bad++;
    }
  }
  if (bad === 0) ok(`All edge weights are in [0, 1]`);
}

function validateEdgeIds(edges: any[]): void {
  const seen = new Set<string>();
  let dup = 0;
  for (const edge of edges) {
    if (seen.has(edge.id)) {
      err(`Duplicate edge ID: ${edge.id}`);
      dup++;
    }
    seen.add(edge.id);
  }
  if (dup === 0) ok(`No duplicate edge IDs`);
}

function validateRelationStatus(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (!VALID_RELATION_STATUSES.has(edge.relationStatus)) {
      err(`Edge ${edge.id}: invalid relationStatus "${edge.relationStatus}"`);
      bad++;
    }
  }
  if (bad === 0) ok(`All edges have valid relationStatus`);
}

function validateGeneratedBy(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (!VALID_GENERATED_BY.has(edge.generatedBy)) {
      err(`Edge ${edge.id}: invalid generatedBy "${edge.generatedBy}"`);
      bad++;
    }
  }
  if (bad === 0) ok(`All edges have valid generatedBy`);
}

function validateNoApprovedWithHumanReview(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (edge.relationStatus === "approved" && edge.humanReviewRequired === true) {
      err(`Edge ${edge.id}: approved status conflicts with humanReviewRequired=true`);
      bad++;
    }
  }
  if (bad === 0) ok(`No approved edges have humanReviewRequired=true`);
}

function validatePublicEdgesHaveEvidence(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (edge.relationStatus !== "experimental") {
      if (!Array.isArray(edge.evidence) || edge.evidence.length === 0) {
        err(`Edge ${edge.id} (${edge.relationStatus}): has no evidence items`);
        bad++;
      }
    }
  }
  if (bad === 0) ok(`All public edges have at least one evidence item`);
}

function validateSemanticOnlyAreExperimental(edges: any[]): void {
  let bad = 0;
  for (const edge of edges) {
    if (edge.edgeType === "SEMANTICALLY_SIMILAR" && edge.relationStatus !== "experimental") {
      err(`Edge ${edge.id}: SEMANTICALLY_SIMILAR edge must be experimental, got "${edge.relationStatus}"`);
      bad++;
    }
  }
  if (bad === 0) ok(`All SEMANTICALLY_SIMILAR edges are experimental`);
}

function validateSourceIds(edges: any[], activeSources: Set<string>): void {
  let bad = 0;
  for (const edge of edges) {
    for (const ev of edge.evidence ?? []) {
      const sid = ev.sourceId ?? "";
      if (sid && !activeSources.has(sid)) {
        err(`Edge ${edge.id}: evidence has unknown sourceId "${sid}"`);
        bad++;
      }
    }
  }
  if (bad === 0) ok(`All evidence sourceIds are in the approved/system source list`);
}

function validateStoryReferences(edges: any[], storyIds: Set<string>): void {
  let bad = 0;
  for (const edge of edges) {
    for (const ev of edge.evidence ?? []) {
      const sid = ev.storyId;
      if (sid && !storyIds.has(sid)) {
        err(`Edge ${edge.id}: evidence references unknown storyId "${sid}"`);
        bad++;
      }
      const segId = ev.segmentId;
      if (segId && !storyIds.has(segId)) {
        err(`Edge ${edge.id}: evidence references unknown segmentId "${segId}"`);
        bad++;
      }
    }
  }
  if (bad === 0) ok(`All story/segment IDs in evidence reference existing stories`);
}

function validateWarningsForNonApproved(edges: any[]): void {
  let missing = 0;
  for (const edge of edges) {
    if (edge.relationStatus !== "approved") {
      if (!Array.isArray(edge.warnings) || edge.warnings.length === 0) {
        warn(`Edge ${edge.id} (${edge.relationStatus}): no warnings — consider adding a review note`);
        missing++;
      }
    }
  }
  if (missing === 0) ok(`All non-approved edges have warning messages`);
}

function validateNoQuranText(kg: any): void {
  const jsonStr = JSON.stringify(kg);
  const matches = jsonStr.match(ARABIC_REGEX);
  if (matches && matches.length > 0) {
    // Allow Arabic in labels (short strings), but flag long Arabic text
    let found = false;
    for (const node of kg.nodes ?? []) {
      const nodeStr = JSON.stringify(node);
      const m = nodeStr.match(/[؀-ۿ]{30,}/);
      if (m) {
        warn(`Possible long Arabic text in node ${node.id}: "${m[0].substring(0, 40)}..."`);
        found = true;
      }
    }
    for (const edge of kg.edges ?? []) {
      for (const ev of edge.evidence ?? []) {
        const evStr = JSON.stringify(ev);
        const m = evStr.match(/[؀-ۿ]{30,}/);
        if (m) {
          warn(`Possible long Arabic text in edge evidence ${edge.id}: "${m[0].substring(0, 40)}..."`);
          found = true;
        }
      }
    }
    if (!found) ok(`No suspicious long Arabic text detected in KG`);
  } else {
    ok(`No Arabic text embedded in KG`);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main(): void {
  console.log("=== Phase 5: Quran Knowledge Graph Validator ===\n");

  const kg = loadKG();
  const storyIds = loadStoryIds();
  const activeSources = loadActiveSources();

  console.log(`KG version: ${kg.version}`);
  console.log(`Generated: ${kg.generatedAt}`);
  console.log(`Nodes: ${kg.nodeCount}, Edges: ${kg.edgeCount}`);

  const nodes: any[] = kg.nodes ?? [];
  const edges: any[] = kg.edges ?? [];
  const nodeIds = new Set(nodes.map((n: any) => n.id));

  check("Node IDs", () => validateNodeIds(nodes));
  check("Edge endpoint references", () => validateEdgeEndpoints(edges, nodeIds));
  check("Edge weights in [0,1]", () => validateEdgeWeights(edges));
  check("Unique edge IDs", () => validateEdgeIds(edges));
  check("Valid relationStatus values", () => validateRelationStatus(edges));
  check("Valid generatedBy values", () => validateGeneratedBy(edges));
  check("No approved + humanReviewRequired conflict", () => validateNoApprovedWithHumanReview(edges));
  check("Public edges have evidence", () => validatePublicEdgesHaveEvidence(edges));
  check("Semantic-only edges are experimental", () => validateSemanticOnlyAreExperimental(edges));
  check("Source IDs are in approved list", () => validateSourceIds(edges, activeSources));
  check("Story/segment IDs exist", () => validateStoryReferences(edges, storyIds));
  check("Non-approved edges have warnings", () => validateWarningsForNonApproved(edges));
  check("No Quran text embedded", () => validateNoQuranText(kg));

  console.log("\n=== Validation Summary ===");
  console.log(`Errors:   ${errors}`);
  console.log(`Warnings: ${warnings_count}`);

  if (errors > 0) {
    console.error(`\nValidation FAILED with ${errors} error(s).`);
    process.exit(1);
  } else {
    console.log(`\nValidation PASSED.`);
    process.exit(0);
  }
}

main();
