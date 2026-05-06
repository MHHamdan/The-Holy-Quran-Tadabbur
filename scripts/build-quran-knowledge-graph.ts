#!/usr/bin/env npx tsx
/**
 * Phase 5: Quran Knowledge Graph Generator
 *
 * Builds a KG JSON file from existing validated project data:
 *   - data/manifests/stories.json (122 stories, 20 inter-story connections)
 *   - data/concepts/curated_concepts.json (60 concepts)
 *   - data/manifests/tafseer_sources.json (source registry)
 *
 * Outputs:
 *   - frontend/src/data/generated/quranKnowledgeGraph.json
 *   - docs/generated/quran-kg-summary.md
 *
 * Rules:
 *   - Never embeds Quran text in the KG; references surah/ayah only
 *   - All story-derived edges are needs_review (story data is pending review)
 *   - Semantic edges are experimental — generated separately
 *   - Every edge must have evidence
 *   - Source IDs must be from approved tafseer_sources.json active list
 */

import * as fs from "fs";
import * as path from "path";

// ---------------------------------------------------------------------------
// Types (aligned with frontend/src/types/quranKnowledgeGraph.ts)
// ---------------------------------------------------------------------------

type RelationStatus = "approved" | "needs_review" | "experimental";
type GeneratedBy =
  | "rule"
  | "tafsir"
  | "story"
  | "semantic_embedding"
  | "manual_review";

interface EdgeEvidence {
  sourceId: string;
  surahNumber?: number;
  ayahNumber?: number;
  tafsirReference?: string;
  storyId?: string;
  segmentId?: string;
  explanationArabic?: string;
  explanationEnglish?: string;
}

interface KGEdge {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: string;
  weight: number;
  evidence: EdgeEvidence[];
  relationStatus: RelationStatus;
  humanReviewRequired: boolean;
  generatedBy: GeneratedBy;
  warnings: string[];
}

interface KGNode {
  id: string;
  type: string;
  [key: string]: unknown;
}

interface QuranKnowledgeGraph {
  version: string;
  generatedAt: string;
  nodeCount: number;
  edgeCount: number;
  nodes: KGNode[];
  edges: KGEdge[];
}

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = path.resolve(__dirname, "..");
const STORIES_PATH = path.join(ROOT, "data", "manifests", "stories.json");
const CONCEPTS_PATH = path.join(ROOT, "data", "concepts", "curated_concepts.json");
const TAFSEER_SOURCES_PATH = path.join(ROOT, "data", "manifests", "tafseer_sources.json");
const OUTPUT_JSON = path.join(ROOT, "frontend", "src", "data", "generated", "quranKnowledgeGraph.json");
const OUTPUT_MD = path.join(ROOT, "docs", "generated", "quran-kg-summary.md");

// ---------------------------------------------------------------------------
// Active source IDs (from tafseer_sources.json enabled list)
// ---------------------------------------------------------------------------

function loadActiveSources(sourcesPath: string): Set<string> {
  if (!fs.existsSync(sourcesPath)) {
    console.warn("tafseer_sources.json not found:", sourcesPath);
    return new Set(["ibn_kathir", "ibn_kathir_ar", "ibn_kathir_en", "muyassar_ar", "saadi_ar", "saadi_en", "sahih_international", "tafheem_en"]);
  }
  const data = JSON.parse(fs.readFileSync(sourcesPath, "utf-8"));
  const sources: string[] = data.sources ?? data.active_sources ?? [];
  const active = sources
    .filter((s: any) => s.is_enabled !== false && !s.license_pending)
    .map((s: any) => s.id ?? s.source_id ?? s);
  return new Set(active.filter(Boolean));
}

// ---------------------------------------------------------------------------
// Load data
// ---------------------------------------------------------------------------

function loadStories() {
  const raw = JSON.parse(fs.readFileSync(STORIES_PATH, "utf-8"));
  return {
    stories: raw.stories as any[],
    interStoryConnections: (raw.inter_story_connections ?? []) as any[],
  };
}

function loadConcepts() {
  const raw = JSON.parse(fs.readFileSync(CONCEPTS_PATH, "utf-8"));
  return {
    persons: (raw.persons ?? []) as any[],
    nations: (raw.nations ?? []) as any[],
    places: (raw.places ?? []) as any[],
    miracles: (raw.miracles ?? []) as any[],
    themes: (raw.themes ?? []) as any[],
    moralPatterns: (raw.moral_patterns ?? []) as any[],
  };
}

// ---------------------------------------------------------------------------
// Node builders
// ---------------------------------------------------------------------------

function buildStoryNodes(stories: any[]): KGNode[] {
  return stories.map((s) => ({
    id: `story:${s.id}`,
    type: "story",
    storyId: s.id,
    nameAr: s.name_ar,
    nameEn: s.name_en,
    category: s.category,
    mainFigures: s.main_figures ?? [],
    themes: s.themes ?? [],
    surasmentioned: s.suras_mentioned ?? [],
  }));
}

function buildSegmentNodes(stories: any[]): KGNode[] {
  const nodes: KGNode[] = [];
  const seenIds = new Set<string>();
  for (const story of stories) {
    for (const seg of story.segments ?? []) {
      // Qualify segment ID with story ID to avoid cross-story duplicates
      const nodeId = `story_segment:${story.id}:${seg.id}`;
      if (seenIds.has(nodeId)) continue;
      seenIds.add(nodeId);
      nodes.push({
        id: nodeId,
        type: "story_segment",
        segmentId: seg.id,
        storyId: story.id,
        narrativeOrder: seg.narrative_order ?? 0,
        aspect: seg.aspect ?? "",
        surahNumber: seg.sura_no,
        ayahStart: seg.aya_start,
        ayahEnd: seg.aya_end,
      });
    }
  }
  return nodes;
}

function buildConceptNodes(concepts: ReturnType<typeof loadConcepts>): KGNode[] {
  const nodes: KGNode[] = [];
  for (const p of concepts.persons) {
    nodes.push({ id: `person:${p.slug}`, type: "person", slug: p.slug, labelAr: p.label_ar, labelEn: p.label_en, personKind: "prophet" });
  }
  for (const n of concepts.nations) {
    nodes.push({ id: `concept:${n.slug}`, type: "concept", slug: n.slug, labelAr: n.label_ar, labelEn: n.label_en, conceptCategory: "historical" });
  }
  for (const pl of concepts.places) {
    nodes.push({ id: `concept:${pl.slug}`, type: "concept", slug: pl.slug, labelAr: pl.label_ar, labelEn: pl.label_en, conceptCategory: "historical" });
  }
  for (const m of concepts.miracles) {
    nodes.push({ id: `concept:${m.slug}`, type: "concept", slug: m.slug, labelAr: m.label_ar, labelEn: m.label_en, conceptCategory: "miracle" });
  }
  for (const t of concepts.themes) {
    nodes.push({ id: `theme:${t.slug}`, type: "theme", slug: t.slug, labelAr: t.label_ar, labelEn: t.label_en });
  }
  for (const mp of concepts.moralPatterns) {
    nodes.push({ id: `concept:${mp.slug}`, type: "concept", slug: mp.slug, labelAr: mp.label_ar, labelEn: mp.label_en, conceptCategory: "moral" });
  }
  return nodes;
}

// ---------------------------------------------------------------------------
// Edge builders
// ---------------------------------------------------------------------------

let _edgeSeq = 0;
function edgeId(prefix: string): string {
  return `${prefix}_${(++_edgeSeq).toString().padStart(6, "0")}`;
}

function edgeFromSameSegmentAyahs(
  seg: any,
  storyId: string,
  activeSources: Set<string>,
): KGEdge[] {
  const edges: KGEdge[] = [];
  const ayahs: number[] = [];
  for (let a = seg.aya_start; a <= seg.aya_end; a++) ayahs.push(a);
  if (ayahs.length < 2) return edges;

  // Collect valid evidence source IDs
  const evidence: EdgeEvidence[] = (seg.evidence ?? [])
    .filter((e: any) => activeSources.has(e.source_id))
    .slice(0, 2)
    .map((e: any) => ({
      sourceId: e.source_id,
      surahNumber: seg.sura_no,
      storyId,
      segmentId: seg.id,
      explanationEnglish: seg.summary_en ?? "",
    }));

  if (evidence.length === 0) {
    // Use story id as fallback evidence marker
    evidence.push({
      sourceId: "story_manifest",
      storyId,
      segmentId: seg.id,
      explanationEnglish: seg.summary_en ?? "",
    });
  }

  const warnings = ["Story segment data is pending scholarly review."];

  for (let i = 0; i < ayahs.length; i++) {
    for (let j = i + 1; j < ayahs.length; j++) {
      const srcId = `ayah:${seg.sura_no}:${ayahs[i]}`;
      const tgtId = `ayah:${seg.sura_no}:${ayahs[j]}`;
      edges.push({
        id: edgeId("seg"),
        sourceNodeId: srcId,
        targetNodeId: tgtId,
        edgeType: "SAME_STORY_SEGMENT",
        weight: 0.85,
        evidence,
        relationStatus: "needs_review",
        humanReviewRequired: true,
        generatedBy: "story",
        warnings,
      });
    }
  }
  return edges;
}

function edgesFromSameStoryAcrossSegments(
  story: any,
  activeSources: Set<string>,
): KGEdge[] {
  const edges: KGEdge[] = [];
  const segments: any[] = story.segments ?? [];
  if (segments.length < 2) return edges;

  // Build set of all ayah ranges per segment
  const segRanges = segments.map((seg: any) => ({
    id: seg.id,
    sura: seg.sura_no,
    start: seg.aya_start,
    end: seg.aya_end,
  }));

  const storyEvidence: EdgeEvidence[] = (story.evidence?.primary_sources ?? [])
    .filter((e: any) => activeSources.has(e.source_id))
    .slice(0, 2)
    .map((e: any) => ({
      sourceId: e.source_id,
      storyId: story.id,
    }));

  if (storyEvidence.length === 0) {
    storyEvidence.push({ sourceId: "story_manifest", storyId: story.id });
  }

  const warnings = ["Cross-segment story relations are pending scholarly review."];

  // Connect the representative ayahs of adjacent segments
  for (let i = 0; i < segRanges.length - 1; i++) {
    const a = segRanges[i];
    const b = segRanges[i + 1];
    const srcId = `ayah:${a.sura}:${a.start}`;
    const tgtId = `ayah:${b.sura}:${b.start}`;
    if (srcId === tgtId) continue;
    edges.push({
      id: edgeId("story"),
      sourceNodeId: srcId,
      targetNodeId: tgtId,
      edgeType: "SAME_STORY",
      weight: 0.60,
      evidence: storyEvidence,
      relationStatus: "needs_review",
      humanReviewRequired: true,
      generatedBy: "story",
      warnings,
    });
  }
  return edges;
}

function edgesFromInterStoryConnections(
  connections: any[],
  stories: any[],
  activeSources: Set<string>,
): KGEdge[] {
  const edges: KGEdge[] = [];

  // Build story → first ayah map
  const storyFirstAyah: Record<string, string> = {};
  for (const story of stories) {
    const firstSeg = (story.segments ?? [])[0];
    if (firstSeg) {
      storyFirstAyah[story.id] = `ayah:${firstSeg.sura_no}:${firstSeg.aya_start}`;
    }
  }

  for (const conn of connections) {
    const srcStoryId = conn.source_story_id;
    const tgtStoryId = conn.target_story_id;
    const srcAyah = storyFirstAyah[srcStoryId];
    const tgtAyah = storyFirstAyah[tgtStoryId];
    if (!srcAyah || !tgtAyah || srcAyah === tgtAyah) continue;

    const evidence: EdgeEvidence[] = (conn.evidence_chunk_ids ?? [])
      .slice(0, 2)
      .map((chunkId: string) => {
        const [sourceId] = chunkId.split(":");
        if (!activeSources.has(sourceId)) return null;
        return {
          sourceId,
          storyId: srcStoryId,
          tafsirReference: chunkId,
          explanationEnglish: conn.explanation?.en ?? "",
          explanationArabic: conn.explanation?.ar ?? "",
        };
      })
      .filter(Boolean) as EdgeEvidence[];

    if (evidence.length === 0) {
      evidence.push({
        sourceId: "story_manifest",
        storyId: srcStoryId,
        explanationEnglish: conn.explanation?.en ?? "",
        explanationArabic: conn.explanation?.ar ?? "",
      });
    }

    const connType = (conn.connection_type ?? "continuation").toUpperCase();
    const edgeType =
      connType === "CONTINUATION" ? "SAME_STORY" :
      connType === "CONTRAST" ? "CONTRASTS_WITH" :
      connType === "SHARED_MORAL" ? "SHARED_MORAL_LESSON" :
      connType === "PARALLEL" ? "PARALLEL_EVENT_PATTERN" :
      "SAME_STORY";

    edges.push({
      id: edgeId("inter"),
      sourceNodeId: srcAyah,
      targetNodeId: tgtAyah,
      edgeType,
      weight: 0.55,
      evidence,
      relationStatus: "needs_review",
      humanReviewRequired: true,
      generatedBy: "story",
      warnings: ["Inter-story connection is pending scholarly review."],
    });

    if (conn.bidirectional) {
      edges.push({
        id: edgeId("inter"),
        sourceNodeId: tgtAyah,
        targetNodeId: srcAyah,
        edgeType,
        weight: 0.55,
        evidence,
        relationStatus: "needs_review",
        humanReviewRequired: true,
        generatedBy: "story",
        warnings: ["Inter-story connection is pending scholarly review."],
      });
    }
  }
  return edges;
}

function edgesFromThemes(stories: any[], concepts: ReturnType<typeof loadConcepts>): KGEdge[] {
  // Group story representative ayahs by shared theme
  const themeToAyahs: Map<string, string[]> = new Map();

  for (const story of stories) {
    const firstSeg = (story.segments ?? [])[0];
    if (!firstSeg) continue;
    const ayahId = `ayah:${firstSeg.sura_no}:${firstSeg.aya_start}`;
    for (const theme of story.themes ?? []) {
      if (!themeToAyahs.has(theme)) themeToAyahs.set(theme, []);
      themeToAyahs.get(theme)!.push(ayahId);
    }
  }

  const edges: KGEdge[] = [];
  for (const [theme, ayahs] of themeToAyahs.entries()) {
    const unique = [...new Set(ayahs)];
    if (unique.length < 2) continue;
    const themeId = `theme:${theme}`;
    const evidence: EdgeEvidence[] = [{ sourceId: "story_manifest", themeId }];
    const warnings = ["Theme-based relation derived from story manifest. Pending scholarly review."];

    // Only connect up to 5 representative pairs per theme to avoid explosion
    const pairs = Math.min(unique.length - 1, 4);
    for (let i = 0; i < pairs; i++) {
      if (unique[i] === unique[i + 1]) continue;
      edges.push({
        id: edgeId("theme"),
        sourceNodeId: unique[i],
        targetNodeId: unique[i + 1],
        edgeType: "SAME_THEME",
        weight: 0.40,
        evidence,
        relationStatus: "needs_review",
        humanReviewRequired: true,
        generatedBy: "rule",
        warnings,
      });
    }
  }
  return edges;
}

// ---------------------------------------------------------------------------
// Main build
// ---------------------------------------------------------------------------

function buildKnowledgeGraph(): QuranKnowledgeGraph {
  console.log("Loading data sources...");
  const { stories, interStoryConnections } = loadStories();
  const concepts = loadConcepts();
  const activeSources = loadActiveSources(TAFSEER_SOURCES_PATH);

  console.log(`  Stories: ${stories.length}, Inter-story connections: ${interStoryConnections.length}`);
  console.log(`  Concepts: persons=${concepts.persons.length}, themes=${concepts.themes.length}, miracles=${concepts.miracles.length}`);
  console.log(`  Active tafsir sources: ${activeSources.size}`);

  // Build nodes
  console.log("\nBuilding nodes...");
  const nodes: KGNode[] = [
    ...buildStoryNodes(stories),
    ...buildSegmentNodes(stories),
    ...buildConceptNodes(concepts),
  ];

  // Build edges
  console.log("Building edges...");
  const edges: KGEdge[] = [];

  // 1. SAME_STORY_SEGMENT: ayahs within the same segment
  for (const story of stories) {
    for (const seg of story.segments ?? []) {
      edges.push(...edgeFromSameSegmentAyahs(seg, story.id, activeSources));
    }
  }
  console.log(`  Story segment edges: ${edges.length}`);

  // 2. SAME_STORY: cross-segment representative ayah connections
  const prevCount = edges.length;
  for (const story of stories) {
    edges.push(...edgesFromSameStoryAcrossSegments(story, activeSources));
  }
  console.log(`  Same-story cross-segment edges: ${edges.length - prevCount}`);

  // 3. Inter-story connections
  const prev2 = edges.length;
  edges.push(...edgesFromInterStoryConnections(interStoryConnections, stories, activeSources));
  console.log(`  Inter-story connection edges: ${edges.length - prev2}`);

  // 4. SAME_THEME from story themes
  const prev3 = edges.length;
  edges.push(...edgesFromThemes(stories, concepts));
  console.log(`  Theme-based edges: ${edges.length - prev3}`);

  return {
    version: "5.0.0",
    generatedAt: new Date().toISOString(),
    nodeCount: nodes.length,
    edgeCount: edges.length,
    nodes,
    edges,
  };
}

// ---------------------------------------------------------------------------
// Count helpers for summary
// ---------------------------------------------------------------------------

function countByField<T extends object>(items: T[], key: keyof T): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const item of items) {
    const val = String(item[key] ?? "unknown");
    counts[val] = (counts[val] ?? 0) + 1;
  }
  return counts;
}

function formatTable(rows: [string, number][]): string {
  return rows.map(([k, v]) => `| ${k} | ${v} |`).join("\n");
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

function main() {
  console.log("=== Phase 5: Quran Knowledge Graph Builder ===\n");

  const kg = buildKnowledgeGraph();

  // Ensure output directories exist
  const outputDir = path.dirname(OUTPUT_JSON);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  const docsDir = path.dirname(OUTPUT_MD);
  if (!fs.existsSync(docsDir)) {
    fs.mkdirSync(docsDir, { recursive: true });
  }

  // Write KG JSON
  fs.writeFileSync(OUTPUT_JSON, JSON.stringify(kg, null, 2), "utf-8");
  console.log(`\nWritten: ${OUTPUT_JSON}`);

  // Compute summary statistics
  const nodeTypeCounts = countByField(kg.nodes, "type" as keyof KGNode);
  const edgeTypeCounts = countByField(kg.edges, "edgeType" as keyof KGEdge);
  const statusCounts = countByField(kg.edges, "relationStatus" as keyof KGEdge);
  const generatorCounts = countByField(kg.edges, "generatedBy" as keyof KGEdge);

  // Write summary markdown
  const md = `# Quran Knowledge Graph — Build Summary

**Generated:** ${kg.generatedAt}
**Version:** ${kg.version}

## Totals

| Metric | Count |
|---|---|
| Total nodes | ${kg.nodeCount} |
| Total edges | ${kg.edgeCount} |

## Node Counts

| Node Type | Count |
|---|---|
${formatTable(Object.entries(nodeTypeCounts).sort(([,a],[,b]) => b-a) as [string, number][])}

## Edge Counts by Type

| Edge Type | Count |
|---|---|
${formatTable(Object.entries(edgeTypeCounts).sort(([,a],[,b]) => b-a) as [string, number][])}

## Edge Counts by Status

| Status | Count |
|---|---|
${formatTable(Object.entries(statusCounts).sort(([,a],[,b]) => b-a) as [string, number][])}

## Edge Counts by Generator

| Generator | Count |
|---|---|
${formatTable(Object.entries(generatorCounts).sort(([,a],[,b]) => b-a) as [string, number][])}

## Notes

- All story-derived edges are \`needs_review\` (story data awaits scholarly verification)
- No \`approved\` edges exist yet — human review required
- Semantic embedding edges not included — generated separately when Qdrant is populated
- No Quran text embedded in this file — ayahs referenced by surah:ayah only
`;

  fs.writeFileSync(OUTPUT_MD, md, "utf-8");
  console.log(`Written: ${OUTPUT_MD}`);

  console.log("\n=== Build Complete ===");
  console.log(`Nodes: ${kg.nodeCount}`);
  console.log(`Edges: ${kg.edgeCount}`);
  console.log(`Status distribution:`, statusCounts);
}

main();
