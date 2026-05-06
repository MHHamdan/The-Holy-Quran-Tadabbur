#!/usr/bin/env npx tsx
/**
 * Phase 6.5: Review Status Propagation Script
 *
 * Reads approved/rejected/changes_requested decisions from review_decisions.json
 * and generates a frontend-readable overlay file (reviewStatusOverlay.json).
 *
 * The overlay is an additive layer — it never modifies Quran text, story summaries,
 * KG edge data, or tafsir notes. It only carries review metadata.
 *
 * Safety rules enforced:
 *   - Approved entry requires: reviewerId, reviewedAt, notes (≥10 chars)
 *   - If any required field is missing → entry falls back to needs_review
 *   - Rejected entries are never marked approved
 *   - changes_requested entries are never marked approved
 *   - Pending tasks are omitted (frontend defaults to needs_review)
 *   - No Arabic Quran text in any overlay field
 *   - Compound rule: story_segment approved only if disagreement_note also approved (if exists)
 *   - Compound rule: story_segment approved only if source_evidence also approved (if exists)
 *
 * Inputs:
 *   backend/app/data/review_tasks.json
 *   backend/app/data/review_decisions.json (optional — if missing, overlay will be empty)
 *
 * Outputs:
 *   frontend/src/data/generated/reviewStatusOverlay.json
 *   docs/generated/review-status-propagation-summary.md
 *
 * Usage:
 *   npx tsx scripts/propagate-review-status.ts
 *
 * Exit codes:
 *   0 = success
 *   1 = critical error
 */

import * as fs from "fs";
import * as path from "path";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = path.resolve(__dirname, "..");
const TASKS_FILE = path.join(ROOT, "backend", "app", "data", "review_tasks.json");
const DECISIONS_FILE = path.join(ROOT, "backend", "app", "data", "review_decisions.json");
const OVERLAY_FILE = path.join(ROOT, "frontend", "src", "data", "generated", "reviewStatusOverlay.json");
const SUMMARY_FILE = path.join(ROOT, "docs", "generated", "review-status-propagation-summary.md");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type OverlayStatus =
  | "approved"
  | "rejected"
  | "changes_requested"
  | "needs_review"
  | "partially_reviewed";

interface OverlayEntry {
  status: OverlayStatus;
  reviewerId?: string;
  reviewerName?: string;
  reviewedAt?: string;
  notesSummary?: string;
  taskId: string;
  warnings: string[];
}

interface ReviewOverlay {
  version: string;
  generatedAt: string;
  story_segment: Record<string, OverlayEntry>;
  related_story: Record<string, OverlayEntry>;
  kg_relation: Record<string, OverlayEntry>;
  source_evidence: Record<string, OverlayEntry>;
  disagreement_note: Record<string, OverlayEntry>;
}

interface ReviewTask {
  id: string;
  contentType: string;
  contentId: string;
  status: string;
  storyId?: string;
  segmentId?: string;
  decision?: {
    status: string;
    notes: string;
    reviewerId: string;
    reviewerName?: string;
    reviewedAt: string;
  } | null;
}

// ---------------------------------------------------------------------------
// Arabic text safety check
// ---------------------------------------------------------------------------

const ARABIC_REGEX = /[؀-ۿ]{5,}/;

function containsArabicText(s: string): boolean {
  return ARABIC_REGEX.test(s);
}

function safeText(s: string | undefined): string {
  if (!s) return "";
  if (containsArabicText(s)) {
    console.error(`[SAFETY] Arabic text detected in overlay field — stripping: "${s.slice(0, 30)}…"`);
    return "[redacted: arabic text]";
  }
  return s;
}

// ---------------------------------------------------------------------------
// Load helpers
// ---------------------------------------------------------------------------

function loadJsonOrNull(filePath: string): unknown {
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf-8"));
}

// ---------------------------------------------------------------------------
// Decision validation
// ---------------------------------------------------------------------------

function isValidApprovedDecision(decision: ReviewTask["decision"]): boolean {
  if (!decision) return false;
  if (decision.status !== "approved") return false;
  if (!decision.reviewerId || !decision.reviewerId.trim()) return false;
  if (!decision.reviewedAt) return false;
  if (!decision.notes || decision.notes.trim().length < 10) return false;
  return true;
}

function buildEntry(task: ReviewTask, decision: ReviewTask["decision"]): OverlayEntry | null {
  if (!decision) return null;
  if (decision.status === "pending") return null;

  const decStatus = decision.status;

  if (decStatus === "approved") {
    if (!isValidApprovedDecision(decision)) {
      console.warn(
        `[WARN] Task ${task.id} has status=approved but missing required metadata — treating as needs_review`
      );
      return {
        status: "needs_review",
        taskId: task.id,
        warnings: ["Approved status has incomplete metadata — treated as needs_review"],
      };
    }

    const rawNotes = decision.notes ?? "";
    const notesSummary = safeText(rawNotes.length > 100 ? rawNotes.slice(0, 100) + "…" : rawNotes);

    return {
      status: "approved",
      reviewerId: safeText(decision.reviewerId),
      reviewerName: decision.reviewerName ? safeText(decision.reviewerName) : undefined,
      reviewedAt: decision.reviewedAt,
      notesSummary,
      taskId: task.id,
      warnings: [],
    };
  }

  if (decStatus === "rejected") {
    return {
      status: "rejected",
      reviewerId: safeText(decision.reviewerId),
      reviewerName: decision.reviewerName ? safeText(decision.reviewerName) : undefined,
      reviewedAt: decision.reviewedAt,
      notesSummary: decision.notes ? safeText(decision.notes.slice(0, 100)) : undefined,
      taskId: task.id,
      warnings: ["Content rejected — do not display as approved."],
    };
  }

  if (decStatus === "changes_requested") {
    return {
      status: "changes_requested",
      reviewerId: safeText(decision.reviewerId),
      reviewerName: decision.reviewerName ? safeText(decision.reviewerName) : undefined,
      reviewedAt: decision.reviewedAt,
      notesSummary: decision.notes ? safeText(decision.notes.slice(0, 100)) : undefined,
      taskId: task.id,
      warnings: ["Changes requested — content not yet approved."],
    };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

console.log("\n[Phase 6.5] Propagating review status to overlay…\n");

// 1. Load tasks
const tasksData = loadJsonOrNull(TASKS_FILE) as {
  tasks: ReviewTask[];
  version: string;
} | null;

if (!tasksData || !Array.isArray(tasksData.tasks)) {
  console.error(`[ERROR] Could not load review tasks from ${TASKS_FILE}`);
  console.error("        Run: npx tsx scripts/generate-review-tasks.ts");
  process.exit(1);
}

const tasks = tasksData.tasks;
console.log(`  Loaded ${tasks.length} review tasks`);

// 2. Load decisions
const decisionsData = loadJsonOrNull(DECISIONS_FILE) as Record<
  string,
  { status: string; notes: string; reviewerId: string; reviewerName?: string; reviewedAt: string }
> | null;

const decisions = decisionsData ?? {};
const decisionCount = Object.keys(decisions).length;
console.log(`  Loaded ${decisionCount} decisions from ${DECISIONS_FILE}`);

// 3. Merge decisions into tasks
const taskMap = new Map<string, ReviewTask>();
for (const task of tasks) {
  const merged = { ...task } as ReviewTask;
  const dec = decisions[task.id];
  if (dec) {
    merged.decision = dec;
    merged.status = dec.status;
  }
  taskMap.set(task.id, merged);
}

// 4. Build content-type lookup maps
// Map segmentId → task for compound rule checking
const segmentTasks = new Map<string, { story_segment?: ReviewTask; disagreement_note?: ReviewTask; source_evidence?: ReviewTask }>();

for (const task of taskMap.values()) {
  const segId = task.segmentId ?? task.contentId;
  if (task.contentType === "story_segment" || task.contentType === "disagreement_note" || task.contentType === "source_evidence") {
    if (!segmentTasks.has(segId)) segmentTasks.set(segId, {});
    const entry = segmentTasks.get(segId)!;
    if (task.contentType === "story_segment") entry.story_segment = task;
    if (task.contentType === "disagreement_note") entry.disagreement_note = task;
    if (task.contentType === "source_evidence") entry.source_evidence = task;
  }
}

// 5. Build overlay
const overlay: ReviewOverlay = {
  version: "1",
  generatedAt: new Date().toISOString(),
  story_segment: {},
  related_story: {},
  kg_relation: {},
  source_evidence: {},
  disagreement_note: {},
};

let stats = {
  total: tasks.length,
  pending: 0,
  approved: 0,
  rejected: 0,
  changes_requested: 0,
  partially_reviewed: 0,
  invalid: 0,
  omitted: 0,
};

for (const task of taskMap.values()) {
  const effectiveStatus = task.decision ? task.decision.status : task.status;

  if (!task.decision || effectiveStatus === "pending") {
    stats.pending++;
    stats.omitted++;
    continue; // omit pending — frontend defaults to needs_review
  }

  let entry = buildEntry(task, task.decision);
  if (!entry) {
    stats.omitted++;
    continue;
  }

  // Compound rule for story_segment: check disagreement_note and source_evidence
  if (task.contentType === "story_segment" && entry.status === "approved") {
    const segId = task.segmentId ?? task.contentId;
    const related = segmentTasks.get(segId);

    let compoundOk = true;
    const compoundWarnings: string[] = [];

    if (related?.disagreement_note) {
      const dTask = related.disagreement_note;
      const dDec = dTask.decision;
      if (!dDec || dDec.status !== "approved" || !isValidApprovedDecision(dDec)) {
        compoundOk = false;
        compoundWarnings.push("Disagreement note task not yet approved — awaiting scholarly review.");
      }
    }

    if (related?.source_evidence) {
      const sTask = related.source_evidence;
      const sDec = sTask.decision;
      if (!sDec || sDec.status !== "approved" || !isValidApprovedDecision(sDec)) {
        compoundOk = false;
        compoundWarnings.push("Source evidence task not yet approved — additional verification pending.");
      }
    }

    if (!compoundOk) {
      entry = {
        ...entry,
        status: "partially_reviewed",
        warnings: [...entry.warnings, ...compoundWarnings],
      };
      stats.partially_reviewed++;
    } else {
      stats.approved++;
    }
  } else if (entry.status === "approved") {
    stats.approved++;
  } else if (entry.status === "rejected") {
    stats.rejected++;
  } else if (entry.status === "changes_requested") {
    stats.changes_requested++;
  } else if (entry.status === "needs_review") {
    stats.invalid++;
  }

  // Write to correct content type bucket
  const ct = task.contentType as keyof typeof overlay;
  if (ct in overlay && ct !== "version" && ct !== "generatedAt") {
    (overlay[ct] as Record<string, OverlayEntry>)[task.contentId] = entry;
  }
}

// 6. Write overlay file
const outputDir = path.dirname(OVERLAY_FILE);
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.writeFileSync(OVERLAY_FILE, JSON.stringify(overlay, null, 2), "utf-8");
console.log(`\n  Written: ${OVERLAY_FILE}`);

// 7. Summary
const overlayCounts = {
  story_segment: Object.keys(overlay.story_segment).length,
  related_story: Object.keys(overlay.related_story).length,
  kg_relation: Object.keys(overlay.kg_relation).length,
  source_evidence: Object.keys(overlay.source_evidence).length,
  disagreement_note: Object.keys(overlay.disagreement_note).length,
};
const totalOverlayEntries = Object.values(overlayCounts).reduce((a, b) => a + b, 0);

const summaryMd = `# Review Status Propagation Summary
_Generated: ${overlay.generatedAt}_

## Overview

| Metric | Count |
|---|---|
| Total review tasks | ${stats.total} |
| Pending (omitted from overlay) | ${stats.omitted} |
| Approved | ${stats.approved} |
| Rejected | ${stats.rejected} |
| Changes Requested | ${stats.changes_requested} |
| Partially Reviewed (compound) | ${stats.partially_reviewed} |
| Invalid / fallback to needs_review | ${stats.invalid} |

## Overlay Entries by Content Type

| Content Type | Entries in Overlay |
|---|---|
| story_segment | ${overlayCounts.story_segment} |
| related_story | ${overlayCounts.related_story} |
| kg_relation | ${overlayCounts.kg_relation} |
| source_evidence | ${overlayCounts.source_evidence} |
| disagreement_note | ${overlayCounts.disagreement_note} |
| **Total** | **${totalOverlayEntries}** |

## Safety Notes

- No Quran text is embedded in overlay entries — only review metadata
- All approved entries required: reviewerId, reviewedAt, notes ≥ 10 chars
- Rejected entries are never marked approved
- Pending tasks omitted — frontend defaults to needs_review for all missing entries
- Compound rule enforced: story_segment approved only if disagreement_note and source_evidence also approved (where applicable)

## Overlay File

Output: \`frontend/src/data/generated/reviewStatusOverlay.json\`

To regenerate after new decisions: \`npx tsx scripts/propagate-review-status.ts\`
Then run: \`npx tsx scripts/validate-review-status-overlay.ts\`
`;

const summaryDir = path.dirname(SUMMARY_FILE);
if (!fs.existsSync(summaryDir)) fs.mkdirSync(summaryDir, { recursive: true });
fs.writeFileSync(SUMMARY_FILE, summaryMd, "utf-8");
console.log(`  Written: ${SUMMARY_FILE}`);

console.log(`\n[OK] Overlay generated: ${totalOverlayEntries} entries (${stats.approved} approved, ${stats.rejected} rejected, ${stats.changes_requested} changes_requested, ${stats.partially_reviewed} partially_reviewed)`);
console.log(`     ${stats.omitted} pending tasks omitted — frontend defaults to needs_review`);
process.exit(0);
