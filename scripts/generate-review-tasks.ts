#!/usr/bin/env npx tsx
/**
 * Phase 6: Review Task Generator
 *
 * Scans static Quran platform data and generates a review task inventory
 * for all content pending scholarly review.
 *
 * Sources scanned:
 *   - frontend/src/data/quranStories.ts  (story segments + related stories)
 *   - frontend/src/data/generated/quranKnowledgeGraph.json  (KG edges)
 *   - data/manifests/stories.json  (raw story connections)
 *
 * Content types generated:
 *   story_segment     — one per segment with needs_review
 *   related_story     — one per inter-story connection with needs_review
 *   kg_relation       — one per unique (storyId, segmentId) combo in KG edges
 *   source_evidence   — one per segment with only 1 evidence source
 *   disagreement_note — one per segment with non-empty disagreementNotes
 *
 * Safety rules enforced:
 *   - No Quran text (Arabic text) in any task — only surah:ayah references
 *   - Task IDs are stable (deterministic from contentType + contentId)
 *   - No duplicates (contentType + contentId uniqueness enforced)
 *   - humanReviewRequired=true for all Quran-sensitive tasks
 *   - No task is auto-approved
 *
 * Output:
 *   backend/app/data/review_tasks.json
 *   docs/generated/review-tasks-summary.md
 *
 * Usage:
 *   npx tsx scripts/generate-review-tasks.ts
 *
 * Exit codes:
 *   0 = generated successfully
 *   1 = critical error
 */

import * as fs from "fs";
import * as path from "path";
import { createHash } from "crypto";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = path.resolve(__dirname, "..");
const STORIES_JSON_PATH = path.join(ROOT, "data", "manifests", "stories.json");
const KG_JSON_PATH = path.join(ROOT, "frontend", "src", "data", "generated", "quranKnowledgeGraph.json");
const TAFSEER_SOURCES_PATH = path.join(ROOT, "data", "manifests", "tafseer_sources.json");
const OUTPUT_PATH = path.join(ROOT, "backend", "app", "data", "review_tasks.json");
const SUMMARY_PATH = path.join(ROOT, "docs", "generated", "review-tasks-summary.md");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ContentType =
  | "story_segment"
  | "related_story"
  | "kg_relation"
  | "source_evidence"
  | "disagreement_note"
  // Phase X — Prophets Atlas review task types
  | "prophet_profile"
  | "prophet_ayah_link"
  | "prophet_relation"
  | "prophet_journey"
  | "prophet_storytelling_stage"
  // Phase X2 — missing-prophet story pages, contextual links, navigation summaries
  | "prophet_story_page"
  | "prophet_story_section"
  | "prophet_contextual_link"
  | "prophet_navigation_summary";

type ReviewStatus = "pending" | "approved" | "rejected" | "changes_requested";
type Priority = "low" | "medium" | "high";

interface QuranRef {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
}

interface ReviewTask {
  id: string;
  contentType: ContentType;
  contentId: string;
  status: ReviewStatus;
  priority: Priority;
  language: "ar" | "en" | "both";
  reviewerId: null;
  reviewerName: null;
  createdAt: string;
  updatedAt: string;
  reviewedAt: null;
  sourceIds: string[];
  quranReferences: QuranRef[];
  decision: null;
  warnings: string[];
  humanReviewRequired: boolean;
  // Extra context (no Quran text)
  summaryEnglish?: string;
  storyId?: string;
  segmentId?: string;
  disagreementNotes?: string[];
}

// ---------------------------------------------------------------------------
// Stable ID generation
// ---------------------------------------------------------------------------

function makeTaskId(contentType: ContentType, contentId: string): string {
  const raw = `${contentType}:${contentId}`;
  const hash = createHash("sha256").update(raw).digest("hex").slice(0, 8);
  return `rt_${contentType.replace(/_/g, "")}_${hash}`;
}

// ---------------------------------------------------------------------------
// Arabic text detector (must not appear in task JSON)
// ---------------------------------------------------------------------------

const ARABIC_REGEX = /[؀-ۿ]{5,}/;

function containsArabicText(s: string): boolean {
  return ARABIC_REGEX.test(s);
}

// ---------------------------------------------------------------------------
// Load JSON helper
// ---------------------------------------------------------------------------

function loadJson(filePath: string): unknown {
  if (!fs.existsSync(filePath)) {
    console.error(`[ERROR] File not found: ${filePath}`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

// ---------------------------------------------------------------------------
// Priority logic
// ---------------------------------------------------------------------------

function computePriority(
  contentType: ContentType,
  hasDisagreement: boolean,
  sourceCount: number,
): Priority {
  if (hasDisagreement) return "high";
  if (contentType === "disagreement_note") return "high";
  if (contentType === "source_evidence") return "high";
  if (contentType === "story_segment" && sourceCount < 2) return "high";
  if (contentType === "story_segment") return "medium";
  if (contentType === "related_story") return "medium";
  if (contentType === "kg_relation") return "low";
  // Phase X prophet review priorities
  if (contentType === "prophet_storytelling_stage") return "high";
  if (contentType === "prophet_journey") return "high";
  if (contentType === "prophet_relation") return "high";
  if (contentType === "prophet_profile") return "high";
  if (contentType === "prophet_ayah_link") return "low";
  // Phase X2 priorities
  if (contentType === "prophet_navigation_summary") return "high";
  if (contentType === "prophet_story_page") return "medium";
  if (contentType === "prophet_story_section") return "medium";
  if (contentType === "prophet_contextual_link") return "high";
  return "medium";
}

// ---------------------------------------------------------------------------
// Main generation
// ---------------------------------------------------------------------------

const tasks: ReviewTask[] = [];
const seenContentIds = new Map<string, string>(); // "contentType:contentId" → taskId
let errors = 0;

const NOW = new Date().toISOString();

function addTask(task: ReviewTask): void {
  const key = `${task.contentType}:${task.contentId}`;
  if (seenContentIds.has(key)) {
    // Duplicate — skip silently (idempotent re-generation)
    return;
  }
  // Safety: reject any task with Arabic text in text fields
  const textFields = [task.summaryEnglish ?? "", ...(task.warnings ?? []), ...(task.disagreementNotes ?? [])];
  for (const tf of textFields) {
    if (containsArabicText(tf)) {
      console.error(`[ERROR] Task ${task.id} contains Arabic text in a text field. Skipping.`);
      errors++;
      return;
    }
  }
  seenContentIds.set(key, task.id);
  tasks.push(task);
}

// ---------------------------------------------------------------------------
// 1. Story segments + disagreement notes from quranStories.ts
//    We read from the raw JSON manifest (stories.json) since quranStories.ts
//    is TypeScript and we want a scriptable source of truth.
// ---------------------------------------------------------------------------

console.log("\n[1] Scanning story segments from stories.json …");

const storiesData = loadJson(STORIES_JSON_PATH) as {
  stories?: Array<{
    id: string;
    name_en?: string;
    segments?: Array<{
      id: string;
      sura_no?: number;
      aya_start?: number;
      aya_end?: number;
      summary_en?: string;
      needs_review?: boolean;
      evidence?: Array<{ source_id: string; needs_review?: boolean }>;
    }>;
    connections?: Array<{
      source: string;
      target: string;
      type: string;
      evidence_chunk_ids?: string[];
    }>;
  }>;
};

const storiesList = storiesData.stories ?? [];

// Disagreement notes come from quranStories.ts (TypeScript data).
// We cannot `require()` TypeScript directly in tsx without bundling.
// We extract them from the raw review report or hard-code the known 7.
// For deterministic generation, we embed the 7 known disagreement segment IDs
// extracted from quranStories.ts lines 442, 903, 1032, 1614, 2349, 2430, 2623.
const DISAGREEMENT_SEGMENTS: Record<string, string[]> = {
  // segmentId → disagreementNotes[]
  // Segment IDs match data/manifests/stories.json + frontend/src/data/quranStories.ts
  "kahf_lessons": [
    "Scholars disagree on the number of sleepers — Quran itself says knowledge is with Allah (18:22)",
  ],
  "luqman_wisdom": [
    "Scholars differ on whether Luqman was a prophet or a wise man — Quran does not specify. Do not assert prophethood.",
  ],
  "ayyub_patience": [
    "Verse 38:44 references an oath that Ayyub apparently made; classical scholars differ on context — do not assert a specific interpretation.",
  ],
  "dawud_test": [
    "Classical commentators differ significantly on the nature of Dawud's lapse in 38:21-26 — do not assert a specific interpretation without scholarly verification.",
  ],
  "bani_israel_covenant": [
    "Classical scholars discuss the specific nature of the transformation referenced in 2:65 and 7:166 — no interpretation is asserted pending scholarly review.",
  ],
  "jalut_battle": [
    "The Quran itself does not name the commander or the target; classical tafsir contextualizes but the Quran is intentionally sparse — no identification is asserted.",
  ],
  "isa_table": [
    "Classical scholars differ on whether the table actually descended after the divine conditional response in 5:115 — no interpretation is asserted pending scholarly review.",
  ],
};

let storySegmentCount = 0;
let relatedStoryCount = 0;
let sourceEvidenceCount = 0;
let disagreementNoteCount = 0;

for (const story of storiesList) {
  const storyId = story.id;

  // Story segments
  for (const seg of story.segments ?? []) {
    const segId = seg.id;
    const needsReview = seg.needs_review !== false; // default true
    if (!needsReview) continue;

    const sourceIds = [...new Set((seg.evidence ?? []).map((e) => e.source_id).filter(Boolean))];
    const hasDisagreement = segId in DISAGREEMENT_SEGMENTS;
    const priority = computePriority("story_segment", hasDisagreement, sourceIds.length);

    const ref: QuranRef = {
      surahNumber: seg.sura_no ?? 0,
      ayahStart: seg.aya_start ?? 0,
      ayahEnd: seg.aya_end,
    };

    const warnings: string[] = [
      "Story segment data is pending scholarly review.",
    ];
    if (sourceIds.length < 2) {
      warnings.push("Only one source in evidence — additional scholarly source verification required.");
    }

    const summaryEn = seg.summary_en ?? "";

    addTask({
      id: makeTaskId("story_segment", segId),
      contentType: "story_segment",
      contentId: segId,
      status: "pending",
      priority,
      language: "both",
      reviewerId: null,
      reviewerName: null,
      createdAt: NOW,
      updatedAt: NOW,
      reviewedAt: null,
      sourceIds,
      quranReferences: ref.surahNumber > 0 ? [ref] : [],
      decision: null,
      warnings,
      humanReviewRequired: true,
      summaryEnglish: summaryEn,
      storyId,
      segmentId: segId,
    });
    storySegmentCount++;

    // Source evidence task for weak evidence
    if (sourceIds.length < 2) {
      addTask({
        id: makeTaskId("source_evidence", segId),
        contentType: "source_evidence",
        contentId: segId,
        status: "pending",
        priority: "high",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds,
        quranReferences: ref.surahNumber > 0 ? [ref] : [],
        decision: null,
        warnings: [
          "Segment has fewer than 2 canonical sources — requires additional scholarly evidence verification.",
        ],
        humanReviewRequired: true,
        summaryEnglish: `Evidence review for: ${summaryEn}`,
        storyId,
        segmentId: segId,
      });
      sourceEvidenceCount++;
    }

    // Disagreement note task
    const dNotes = DISAGREEMENT_SEGMENTS[segId];
    if (dNotes && dNotes.length > 0) {
      addTask({
        id: makeTaskId("disagreement_note", segId),
        contentType: "disagreement_note",
        contentId: segId,
        status: "pending",
        priority: "high",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds,
        quranReferences: ref.surahNumber > 0 ? [ref] : [],
        decision: null,
        warnings: [
          "This segment contains scholarly disagreement notes — human scholarly review required before any public display.",
        ],
        humanReviewRequired: true,
        summaryEnglish: `Disagreement review for: ${summaryEn}`,
        storyId,
        segmentId: segId,
        disagreementNotes: dNotes,
      });
      disagreementNoteCount++;
    }
  }

  // Story connections (related_story)
  for (const conn of story.connections ?? []) {
    const connId = `${conn.source}__to__${conn.target}`;
    const sourceIds = [
      ...new Set((conn.evidence_chunk_ids ?? []).map((cid) => {
        const parts = cid.split(":");
        return parts[0];
      }).filter(Boolean))
    ];

    addTask({
      id: makeTaskId("related_story", connId),
      contentType: "related_story",
      contentId: connId,
      status: "pending",
      priority: "medium",
      language: "both",
      reviewerId: null,
      reviewerName: null,
      createdAt: NOW,
      updatedAt: NOW,
      reviewedAt: null,
      sourceIds,
      quranReferences: [],
      decision: null,
      warnings: [
        "Inter-story connection is pending scholarly review.",
      ],
      humanReviewRequired: true,
      summaryEnglish: `Story connection: ${conn.source} → ${conn.target} (${conn.type})`,
      storyId: conn.source,
    });
    relatedStoryCount++;
  }
}

console.log(`  story_segment: ${storySegmentCount}`);
console.log(`  source_evidence: ${sourceEvidenceCount}`);
console.log(`  disagreement_note: ${disagreementNoteCount}`);
console.log(`  related_story: ${relatedStoryCount}`);

// ---------------------------------------------------------------------------
// 2. KG relations — grouped by (storyId, segmentId) to keep task count manageable
// ---------------------------------------------------------------------------

console.log("\n[2] Scanning KG edges …");

interface KGEdge {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: string;
  relationStatus: string;
  humanReviewRequired?: boolean;
  evidence?: Array<{
    sourceId: string;
    storyId?: string;
    segmentId?: string;
    conceptId?: string;
    themeId?: string;
  }>;
  warnings?: string[];
}

const kgData = loadJson(KG_JSON_PATH) as { edges: KGEdge[] };
const kgEdges = kgData.edges ?? [];

// Group by unique (storyId, segmentId) or (conceptId) or (themeId)
const kgGroups = new Map<string, {
  edgeCount: number;
  edgeTypes: Set<string>;
  sourceNodeIds: Set<string>;
  targetNodeIds: Set<string>;
  sourceIds: Set<string>;
  storyId?: string;
  segmentId?: string;
  conceptId?: string;
  themeId?: string;
}>();

for (const edge of kgEdges) {
  if (edge.relationStatus !== "needs_review") continue;

  for (const ev of edge.evidence ?? []) {
    let groupKey: string;
    let storyId: string | undefined;
    let segmentId: string | undefined;
    let conceptId: string | undefined;
    let themeId: string | undefined;

    if (ev.storyId && ev.segmentId) {
      groupKey = `story:${ev.storyId}:${ev.segmentId}`;
      storyId = ev.storyId;
      segmentId = ev.segmentId;
    } else if (ev.storyId) {
      groupKey = `story:${ev.storyId}`;
      storyId = ev.storyId;
    } else if (ev.conceptId) {
      groupKey = `concept:${ev.conceptId}`;
      conceptId = ev.conceptId;
    } else if (ev.themeId) {
      groupKey = `theme:${ev.themeId}`;
      themeId = ev.themeId;
    } else {
      groupKey = `edge:${edge.edgeType}`;
    }

    if (!kgGroups.has(groupKey)) {
      kgGroups.set(groupKey, {
        edgeCount: 0,
        edgeTypes: new Set(),
        sourceNodeIds: new Set(),
        targetNodeIds: new Set(),
        sourceIds: new Set(),
        storyId,
        segmentId,
        conceptId,
        themeId,
      });
    }
    const g = kgGroups.get(groupKey)!;
    g.edgeCount++;
    g.edgeTypes.add(edge.edgeType);
    g.sourceNodeIds.add(edge.sourceNodeId);
    g.targetNodeIds.add(edge.targetNodeId);
    if (ev.sourceId) g.sourceIds.add(ev.sourceId);
  }
}

let kgRelationCount = 0;

for (const [groupKey, group] of kgGroups) {
  const edgeTypes = [...group.edgeTypes].join(",");
  const summaryEn = group.segmentId
    ? `KG relations for story segment: ${group.segmentId} (${edgeTypes}, ${group.edgeCount} edges)`
    : group.conceptId
    ? `KG relations for concept: ${group.conceptId} (${edgeTypes}, ${group.edgeCount} edges)`
    : `KG relations: ${groupKey} (${edgeTypes}, ${group.edgeCount} edges)`;

  addTask({
    id: makeTaskId("kg_relation", groupKey),
    contentType: "kg_relation",
    contentId: groupKey,
    status: "pending",
    priority: "low",
    language: "both",
    reviewerId: null,
    reviewerName: null,
    createdAt: NOW,
    updatedAt: NOW,
    reviewedAt: null,
    sourceIds: [...group.sourceIds],
    quranReferences: [],
    decision: null,
    warnings: [
      "Knowledge graph relations derived from story/concept data are pending scholarly review.",
    ],
    humanReviewRequired: true,
    summaryEnglish: summaryEn,
    storyId: group.storyId,
    segmentId: group.segmentId,
  });
  kgRelationCount++;
}

console.log(`  kg_relation groups: ${kgRelationCount}`);
console.log(`  total KG edges scanned: ${kgEdges.length}`);

// ---------------------------------------------------------------------------
// 2.5. Phase X — Prophets Atlas review tasks
// ---------------------------------------------------------------------------

const PROPHETS_ATLAS_PATH = path.join(
  ROOT,
  "frontend",
  "src",
  "data",
  "generated",
  "quranProphetsAtlas.json",
);

let prophetProfileCount = 0;
let prophetAyahLinkCount = 0;
let prophetRelationCount = 0;
let prophetJourneyCount = 0;
let prophetStorytellingStageCount = 0;

if (fs.existsSync(PROPHETS_ATLAS_PATH)) {
  console.log("\n[2.5] Scanning Prophets Atlas …");
  const atlas = JSON.parse(fs.readFileSync(PROPHETS_ATLAS_PATH, "utf-8")) as {
    profiles: Array<{
      prophetId: string;
      nameEnglish: string;
      reviewStatus: string;
      humanReviewRequired: boolean;
      explicitMentions: Array<{ surahNumber: number; ayahNumber: number; linkType: string; sourceIds: string[]; warnings: string[] }>;
      contextualMentions: Array<{ surahNumber: number; ayahNumber: number; linkType: string; sourceIds: string[]; warnings: string[] }>;
      coreferenceMentions: Array<{ surahNumber: number; ayahNumber: number; linkType: string; sourceIds: string[]; warnings: string[] }>;
      relatedProphets: Array<{ sourceProphetId: string; targetProphetId: string; relationType: string; evidenceReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }>; sourceIds: string[]; reviewStatus: string }>;
      journeys: Array<{ journeyId: string; journeyType: string; certainty: string; reviewStatus: string; stages: Array<{ stageId: string; orderIndex: number; ayahReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }>; sourceIds: string[]; storytellingArabic?: string; storytellingEnglish?: string; reviewStatus: string }>; warnings: string[] }>;
      warnings: string[];
    }>;
  };

  for (const p of atlas.profiles) {
    // prophet_profile task
    addTask({
      id: makeTaskId("prophet_profile", p.prophetId),
      contentType: "prophet_profile",
      contentId: p.prophetId,
      status: "pending",
      priority: computePriority("prophet_profile", false, 1),
      language: "both",
      reviewerId: null,
      reviewerName: null,
      createdAt: NOW,
      updatedAt: NOW,
      reviewedAt: null,
      sourceIds: ["quran_uthmani_cloud"],
      quranReferences: [],
      decision: null,
      warnings: p.warnings ?? [],
      humanReviewRequired: true,
      summaryEnglish: `Prophet profile review: ${p.nameEnglish}`,
    });
    prophetProfileCount++;

    // prophet_ayah_link tasks — emit one per non-explicit (riskier) link;
    // explicit-name links are low-risk and not individually queued (the
    // overall profile task covers them).
    const riskyLinks = [
      ...p.contextualMentions.map((m) => ({ ...m, _bucket: "contextual" })),
      ...p.coreferenceMentions.map((m) => ({ ...m, _bucket: "coreference" })),
    ];
    for (const m of riskyLinks) {
      const cid = `${p.prophetId}:${m.surahNumber}:${m.ayahNumber}:${m.linkType}`;
      addTask({
        id: makeTaskId("prophet_ayah_link", cid),
        contentType: "prophet_ayah_link",
        contentId: cid,
        status: "pending",
        priority: "low",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds: m.sourceIds ?? ["quran_uthmani_cloud"],
        quranReferences: [
          { surahNumber: m.surahNumber, ayahStart: m.ayahNumber },
        ],
        decision: null,
        warnings: m.warnings ?? [],
        humanReviewRequired: true,
        summaryEnglish: `Ayah link review for ${p.nameEnglish} at ${m.surahNumber}:${m.ayahNumber} (${m.linkType}).`,
      });
      prophetAyahLinkCount++;
    }

    // prophet_relation tasks — dedupe by (target, type)
    const relSeen = new Set<string>();
    for (const r of p.relatedProphets) {
      const k = `${r.sourceProphetId}::${r.targetProphetId}::${r.relationType}`;
      if (relSeen.has(k)) continue;
      relSeen.add(k);
      const refs = r.evidenceReferences.slice(0, 5);
      addTask({
        id: makeTaskId("prophet_relation", k),
        contentType: "prophet_relation",
        contentId: k,
        status: "pending",
        priority: "high",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds: r.sourceIds ?? ["quran_uthmani_cloud"],
        quranReferences: refs,
        decision: null,
        warnings: [],
        humanReviewRequired: true,
        summaryEnglish: `Prophet relation review: ${r.sourceProphetId} ↔ ${r.targetProphetId} (${r.relationType}).`,
      });
      prophetRelationCount++;
    }

    // prophet_journey tasks — one per journey type
    for (const j of p.journeys) {
      addTask({
        id: makeTaskId("prophet_journey", j.journeyId),
        contentType: "prophet_journey",
        contentId: j.journeyId,
        status: "pending",
        priority: j.certainty === "high" ? "medium" : "high",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds: ["quran_uthmani_cloud"],
        quranReferences: [],
        decision: null,
        warnings: j.warnings ?? [],
        humanReviewRequired: true,
        summaryEnglish: `Prophet journey review: ${p.nameEnglish} — ${j.journeyType} (certainty=${j.certainty}).`,
      });
      prophetJourneyCount++;

      // prophet_storytelling_stage tasks — only when the stage carries a
      // storytelling field. The build script does not emit storytelling by
      // default; storytelling is generated on demand by the backend.
      for (const st of j.stages) {
        if (!st.storytellingArabic && !st.storytellingEnglish) continue;
        addTask({
          id: makeTaskId("prophet_storytelling_stage", st.stageId),
          contentType: "prophet_storytelling_stage",
          contentId: st.stageId,
          status: "pending",
          priority: "high",
          language: "both",
          reviewerId: null,
          reviewerName: null,
          createdAt: NOW,
          updatedAt: NOW,
          reviewedAt: null,
          sourceIds: st.sourceIds ?? ["quran_uthmani_cloud"],
          quranReferences: st.ayahReferences.slice(0, 5),
          decision: null,
          warnings: ["AI-assisted storytelling defaults to needs_review until reviewed."],
          humanReviewRequired: true,
          summaryEnglish: `Storytelling stage review: ${p.nameEnglish} stage ${st.orderIndex} (${j.journeyType}).`,
        });
        prophetStorytellingStageCount++;
      }
    }
  }
  console.log(`  prophet_profile: ${prophetProfileCount}`);
  console.log(`  prophet_ayah_link: ${prophetAyahLinkCount}`);
  console.log(`  prophet_relation: ${prophetRelationCount}`);
  console.log(`  prophet_journey: ${prophetJourneyCount}`);
  console.log(`  prophet_storytelling_stage: ${prophetStorytellingStageCount}`);
} else {
  console.log(
    "\n[2.5] quranProphetsAtlas.json not found — skipping prophet review tasks.",
  );
}

// ---------------------------------------------------------------------------
// 2.6. Phase X2 — story pages + contextual links
// ---------------------------------------------------------------------------

const STORY_PAGES_PATH = path.join(
  ROOT,
  "frontend",
  "src",
  "data",
  "generated",
  "quranProphetStoryPages.json",
);
const CONTEXTUAL_LINKS_PATH = path.join(
  ROOT,
  "frontend",
  "src",
  "data",
  "generated",
  "quranProphetContextualLinks.json",
);

let prophetStoryPageCount = 0;
let prophetStorySectionCount = 0;
let prophetContextualLinkCount = 0;

if (fs.existsSync(STORY_PAGES_PATH)) {
  console.log("\n[2.6] Scanning prophet story pages …");
  const sp = JSON.parse(fs.readFileSync(STORY_PAGES_PATH, "utf-8")) as {
    pages: Array<{
      storyPageId: string;
      prophetId: string;
      titleEnglish: string;
      pageType: string;
      sourceIds: string[];
      reviewStatus: string;
      warnings: string[];
      storySections: Array<{
        sectionId: string;
        labelEnglish: string;
        sectionType: string;
        ayahReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }>;
        sourceIds: string[];
        warnings: string[];
      }>;
    }>;
  };
  for (const page of sp.pages) {
    // Filter Arabic warnings — review tasks are English-only per policy.
    const pageWarningsEn = (page.warnings ?? []).filter((w) => !containsArabicText(w));
    addTask({
      id: makeTaskId("prophet_story_page", page.storyPageId),
      contentType: "prophet_story_page",
      contentId: page.storyPageId,
      status: "pending",
      priority: page.prophetId === "prophet_muhammad" ? "high" : "medium",
      language: "both",
      reviewerId: null,
      reviewerName: null,
      createdAt: NOW,
      updatedAt: NOW,
      reviewedAt: null,
      sourceIds: page.sourceIds ?? ["quran_uthmani_cloud"],
      quranReferences: [],
      decision: null,
      warnings: pageWarningsEn,
      humanReviewRequired: true,
      summaryEnglish: `Prophet story-page review (${page.pageType}): ${page.titleEnglish}.`,
    });
    prophetStoryPageCount++;
    for (const sec of page.storySections) {
      const sectionWarningsEn = (sec.warnings ?? []).filter((w) => !containsArabicText(w));
      addTask({
        id: makeTaskId("prophet_story_section", sec.sectionId),
        contentType: "prophet_story_section",
        contentId: sec.sectionId,
        status: "pending",
        priority:
          sec.sectionType === "summary_only" || sec.sectionType === "limited_mentions"
            ? "low"
            : "medium",
        language: "both",
        reviewerId: null,
        reviewerName: null,
        createdAt: NOW,
        updatedAt: NOW,
        reviewedAt: null,
        sourceIds: sec.sourceIds ?? ["quran_uthmani_cloud"],
        quranReferences: sec.ayahReferences.slice(0, 5),
        decision: null,
        warnings: sectionWarningsEn,
        humanReviewRequired: true,
        summaryEnglish: `Story-section review: ${page.titleEnglish} — ${sec.labelEnglish}.`,
      });
      prophetStorySectionCount++;
    }
  }
  console.log(`  prophet_story_page: ${prophetStoryPageCount}`);
  console.log(`  prophet_story_section: ${prophetStorySectionCount}`);
} else {
  console.log("\n[2.6] quranProphetStoryPages.json not found — skipping.");
}

if (fs.existsSync(CONTEXTUAL_LINKS_PATH)) {
  console.log("\n[2.7] Scanning prophet contextual links …");
  const ctx = JSON.parse(fs.readFileSync(CONTEXTUAL_LINKS_PATH, "utf-8")) as {
    links: Array<{
      prophetId: string;
      surahNumber: number;
      ayahNumber: number;
      linkType: string;
      sourceIds: string[];
      evidenceReferences: Array<{ surahNumber: number; ayahStart: number; ayahEnd?: number }>;
      warnings: string[];
      rationale: string;
    }>;
  };
  // Group by (prophet, surah, linkType) so we don't explode the task count;
  // each group lists one representative link.
  const groups = new Map<string, {
    prophetId: string;
    surahNumber: number;
    linkType: string;
    count: number;
    sample: typeof ctx.links[number];
  }>();
  for (const l of ctx.links) {
    const k = `${l.prophetId}:${l.surahNumber}:${l.linkType}`;
    if (!groups.has(k)) {
      groups.set(k, { prophetId: l.prophetId, surahNumber: l.surahNumber, linkType: l.linkType, count: 0, sample: l });
    }
    groups.get(k)!.count++;
  }
  for (const [k, g] of groups) {
    addTask({
      id: makeTaskId("prophet_contextual_link", k),
      contentType: "prophet_contextual_link",
      contentId: k,
      status: "pending",
      priority: "high",
      language: "both",
      reviewerId: null,
      reviewerName: null,
      createdAt: NOW,
      updatedAt: NOW,
      reviewedAt: null,
      sourceIds: g.sample.sourceIds ?? ["quran_uthmani_cloud"],
      quranReferences: g.sample.evidenceReferences.slice(0, 3),
      decision: null,
      warnings: (g.sample.warnings ?? []).filter((w) => !containsArabicText(w)),
      humanReviewRequired: true,
      summaryEnglish: `Contextual link group: ${g.prophetId} surah ${g.surahNumber} (${g.linkType}) — ${g.count} link(s).`,
    });
    prophetContextualLinkCount++;
  }
  console.log(`  prophet_contextual_link groups: ${prophetContextualLinkCount}`);
} else {
  console.log("\n[2.7] quranProphetContextualLinks.json not found — skipping.");
}

// ---------------------------------------------------------------------------
// 3. Final output
// ---------------------------------------------------------------------------

console.log(`\n[3] Total review tasks generated: ${tasks.length}`);

// Ensure output directory exists
const outputDir = path.dirname(OUTPUT_PATH);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.writeFileSync(
  OUTPUT_PATH,
  JSON.stringify({
    version: "1",
    generatedAt: NOW,
    totalTasks: tasks.length,
    tasks,
  }, null, 2),
  "utf-8",
);

console.log(`  Written: ${OUTPUT_PATH}`);

// ---------------------------------------------------------------------------
// 4. Summary document
// ---------------------------------------------------------------------------

const byType = new Map<ContentType, number>();
const byPriority = new Map<Priority, number>();
const bySource = new Map<string, number>();
let highDisagreementCount = 0;
let missingEvidenceCount = 0;

for (const task of tasks) {
  byType.set(task.contentType, (byType.get(task.contentType) ?? 0) + 1);
  byPriority.set(task.priority, (byPriority.get(task.priority) ?? 0) + 1);
  for (const src of task.sourceIds) {
    bySource.set(src, (bySource.get(src) ?? 0) + 1);
  }
  if ((task.disagreementNotes ?? []).length > 0) highDisagreementCount++;
  if (task.warnings.some((w) => w.includes("fewer than 2"))) missingEvidenceCount++;
}

let md = `# Review Tasks Summary\n_Generated: ${NOW}_\n\n`;
md += `## Totals\n\n`;
md += `| Metric | Count |\n|---|---|\n`;
md += `| Total review tasks | ${tasks.length} |\n`;
md += `| Pending | ${tasks.filter((t) => t.status === "pending").length} |\n`;
md += `| Tasks with disagreement notes | ${highDisagreementCount} |\n`;
md += `| Tasks with missing evidence | ${missingEvidenceCount} |\n`;
md += `| Tasks requiring scholar review | ${tasks.filter((t) => t.humanReviewRequired).length} |\n\n`;

md += `## By Content Type\n\n`;
md += `| Content Type | Count |\n|---|---|\n`;
for (const [ct, n] of [...byType.entries()].sort((a, b) => b[1] - a[1])) {
  md += `| ${ct} | ${n} |\n`;
}

md += `\n## By Priority\n\n`;
md += `| Priority | Count |\n|---|---|\n`;
for (const p of ["high", "medium", "low"] as Priority[]) {
  md += `| ${p} | ${byPriority.get(p) ?? 0} |\n`;
}

md += `\n## By Source\n\n`;
md += `| Source ID | Tasks Referencing |\n|---|---|\n`;
for (const [src, n] of [...bySource.entries()].sort((a, b) => b[1] - a[1]).slice(0, 15)) {
  md += `| ${src} | ${n} |\n`;
}

md += `\n## Disagreement Notes\n\nThe following segments have scholarly disagreements requiring priority review:\n\n`;
for (const task of tasks.filter((t) => (t.disagreementNotes ?? []).length > 0)) {
  md += `- **${task.contentId}** (${task.quranReferences.map((r) => `${r.surahNumber}:${r.ayahStart}`).join(", ")})\n`;
  for (const note of task.disagreementNotes ?? []) {
    md += `  - ${note}\n`;
  }
}

md += `\n## Safety Notes\n\n`;
md += `- No Quran text is embedded in review tasks — only surah:ayah references\n`;
md += `- All tasks have \`humanReviewRequired: true\`\n`;
md += `- No task is auto-approved\n`;
md += `- Task IDs are stable (SHA-256 of contentType:contentId)\n`;
md += `- Duplicate prevention: ${tasks.length} unique tasks\n`;

const summaryDir = path.dirname(SUMMARY_PATH);
if (!fs.existsSync(summaryDir)) {
  fs.mkdirSync(summaryDir, { recursive: true });
}
fs.writeFileSync(SUMMARY_PATH, md, "utf-8");
console.log(`  Written: ${SUMMARY_PATH}`);

// ---------------------------------------------------------------------------
// 5. Exit
// ---------------------------------------------------------------------------

if (errors > 0) {
  console.error(`\n[FAIL] ${errors} error(s) during generation.`);
  process.exit(1);
}

console.log(`\n[OK] Review task generation complete.`);
console.log(`     ${storySegmentCount} story_segment + ${relatedStoryCount} related_story + ${kgRelationCount} kg_relation + ${sourceEvidenceCount} source_evidence + ${disagreementNoteCount} disagreement_note`);
console.log(`     + ${prophetProfileCount} prophet_profile + ${prophetAyahLinkCount} prophet_ayah_link + ${prophetRelationCount} prophet_relation + ${prophetJourneyCount} prophet_journey + ${prophetStorytellingStageCount} prophet_storytelling_stage`);
console.log(`     + ${prophetStoryPageCount} prophet_story_page + ${prophetStorySectionCount} prophet_story_section + ${prophetContextualLinkCount} prophet_contextual_link groups`);
process.exit(0);
