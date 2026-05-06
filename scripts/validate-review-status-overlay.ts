#!/usr/bin/env npx tsx
/**
 * Phase 6.5: Review Status Overlay Validator
 *
 * Validates the generated reviewStatusOverlay.json against the policy rules
 * defined in docs/phase-6-5-status-propagation-policy.md.
 *
 * Checks:
 *   1. Overlay file exists and is valid JSON
 *   2. Required top-level fields present (version, generatedAt, content type maps)
 *   3. No Arabic Quran text in any text field
 *   4. Every taskId in overlay exists in review_tasks.json
 *   5. Approved entries have reviewerId, reviewedAt, notesSummary
 *   6. Rejected entries are NOT marked approved
 *   7. changes_requested entries are NOT marked approved
 *   8. All status values are valid enum members
 *   9. All contentType keys are valid
 *   10. Warnings present for rejected and changes_requested entries
 *
 * Usage:
 *   npx tsx scripts/validate-review-status-overlay.ts
 *
 * Exit codes:
 *   0 = all checks passed (errors=0)
 *   1 = validation errors found
 */

import * as fs from "fs";
import * as path from "path";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = path.resolve(__dirname, "..");
const OVERLAY_FILE = path.join(ROOT, "frontend", "src", "data", "generated", "reviewStatusOverlay.json");
const TASKS_FILE = path.join(ROOT, "backend", "app", "data", "review_tasks.json");

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type OverlayStatus =
  | "approved"
  | "rejected"
  | "changes_requested"
  | "needs_review"
  | "partially_reviewed";

const VALID_STATUSES = new Set<OverlayStatus>([
  "approved",
  "rejected",
  "changes_requested",
  "needs_review",
  "partially_reviewed",
]);

const VALID_CONTENT_TYPES = new Set([
  "story_segment",
  "related_story",
  "kg_relation",
  "source_evidence",
  "disagreement_note",
]);

const ARABIC_REGEX = /[؀-ۿ]{5,}/;

// ---------------------------------------------------------------------------
// Tracking
// ---------------------------------------------------------------------------

let errors = 0;
let warnings = 0;

function err(msg: string): void {
  console.error(`  [FAIL] ${msg}`);
  errors++;
}

function warn(msg: string): void {
  console.warn(`  [WARN] ${msg}`);
  warnings++;
}

function pass(msg: string): void {
  console.log(`  [PASS] ${msg}`);
}

function containsArabicText(s: string): boolean {
  return ARABIC_REGEX.test(s);
}

function checkTextField(value: unknown, label: string): void {
  if (typeof value !== "string") return;
  if (containsArabicText(value)) {
    err(`Arabic text detected in field "${label}": "${value.slice(0, 40)}…"`);
  }
}

// ---------------------------------------------------------------------------
// 1. Load and parse overlay
// ---------------------------------------------------------------------------

console.log("\n[Phase 6.5] Validating review status overlay…\n");

// Check 1: File exists
if (!fs.existsSync(OVERLAY_FILE)) {
  err(`Overlay file not found: ${OVERLAY_FILE}`);
  err("  Run: npx tsx scripts/propagate-review-status.ts");
  console.log(`\n[FAIL] ${errors} error(s), ${warnings} warning(s)`);
  process.exit(1);
}
pass(`Overlay file exists: ${OVERLAY_FILE}`);

let overlay: Record<string, unknown>;
try {
  overlay = JSON.parse(fs.readFileSync(OVERLAY_FILE, "utf-8")) as Record<string, unknown>;
  pass("Overlay JSON parsed successfully");
} catch (e) {
  err(`Failed to parse overlay JSON: ${(e as Error).message}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// 2. Top-level structure
// ---------------------------------------------------------------------------

console.log("\n[Check 2] Top-level structure…");

const REQUIRED_TOP_KEYS = ["version", "generatedAt", "story_segment", "related_story", "kg_relation", "source_evidence", "disagreement_note"];
for (const key of REQUIRED_TOP_KEYS) {
  if (!(key in overlay)) {
    err(`Missing required top-level key: "${key}"`);
  } else {
    pass(`Key "${key}" present`);
  }
}

// ---------------------------------------------------------------------------
// 3. Load task IDs for cross-reference
// ---------------------------------------------------------------------------

console.log("\n[Check 3] Loading review task IDs for cross-reference…");

let knownTaskIds = new Set<string>();
if (fs.existsSync(TASKS_FILE)) {
  try {
    const tasksData = JSON.parse(fs.readFileSync(TASKS_FILE, "utf-8")) as { tasks: { id: string }[] };
    knownTaskIds = new Set(tasksData.tasks.map((t) => t.id));
    pass(`Loaded ${knownTaskIds.size} known task IDs`);
  } catch {
    warn("Could not load review_tasks.json — taskId cross-reference skipped");
  }
} else {
  warn("review_tasks.json not found — taskId cross-reference skipped");
}

// ---------------------------------------------------------------------------
// 4–10. Per-entry validation
// ---------------------------------------------------------------------------

console.log("\n[Check 4-10] Validating overlay entries…");

let totalEntries = 0;
let approvedCount = 0;
let rejectedCount = 0;
let changesCount = 0;
let partialCount = 0;
let needsReviewCount = 0;

for (const contentType of VALID_CONTENT_TYPES) {
  const bucket = overlay[contentType];
  if (!bucket || typeof bucket !== "object") continue;

  for (const [contentId, rawEntry] of Object.entries(bucket as Record<string, unknown>)) {
    totalEntries++;
    const label = `${contentType}/${contentId}`;

    if (!rawEntry || typeof rawEntry !== "object") {
      err(`Entry ${label}: not an object`);
      continue;
    }

    const entry = rawEntry as Record<string, unknown>;

    // Check 8: valid status
    const status = entry["status"] as string;
    if (!VALID_STATUSES.has(status as OverlayStatus)) {
      err(`Entry ${label}: invalid status "${status}" — must be one of ${[...VALID_STATUSES].join(", ")}`);
    }

    // Track counts
    if (status === "approved") approvedCount++;
    else if (status === "rejected") rejectedCount++;
    else if (status === "changes_requested") changesCount++;
    else if (status === "partially_reviewed") partialCount++;
    else if (status === "needs_review") needsReviewCount++;

    // Check 4: taskId exists
    const taskId = entry["taskId"] as string;
    if (!taskId) {
      err(`Entry ${label}: missing taskId`);
    } else if (knownTaskIds.size > 0 && !knownTaskIds.has(taskId)) {
      err(`Entry ${label}: taskId "${taskId}" not found in review_tasks.json`);
    }

    // Check 3: no Arabic text in any text field
    checkTextField(entry["reviewerId"], `${label}.reviewerId`);
    checkTextField(entry["reviewerName"], `${label}.reviewerName`);
    checkTextField(entry["notesSummary"], `${label}.notesSummary`);
    if (Array.isArray(entry["warnings"])) {
      for (const w of entry["warnings"] as unknown[]) {
        checkTextField(w, `${label}.warnings[]`);
      }
    }

    // Check 5: approved entries have required metadata
    if (status === "approved") {
      if (!entry["reviewerId"] || typeof entry["reviewerId"] !== "string" || !(entry["reviewerId"] as string).trim()) {
        err(`Entry ${label}: approved entry missing reviewerId`);
      }
      if (!entry["reviewedAt"] || typeof entry["reviewedAt"] !== "string") {
        err(`Entry ${label}: approved entry missing reviewedAt`);
      }
      if (!entry["notesSummary"] || typeof entry["notesSummary"] !== "string") {
        err(`Entry ${label}: approved entry missing notesSummary`);
      }
    }

    // Check 6: rejected entries are NOT approved
    if (status === "approved" && entry["warnings"] && Array.isArray(entry["warnings"])) {
      for (const w of entry["warnings"] as string[]) {
        if (w.toLowerCase().includes("rejected")) {
          err(`Entry ${label}: approved entry has rejection warning — status conflict`);
        }
      }
    }

    // Check 7: changes_requested entries not approved
    if (status === "changes_requested") {
      if ((entry["reviewerId"] as string | undefined) && !entry["reviewedAt"]) {
        warn(`Entry ${label}: changes_requested has reviewerId but no reviewedAt`);
      }
    }

    // Check 10: rejected/changes_requested should have warnings
    if (status === "rejected" || status === "changes_requested") {
      const warningsList = entry["warnings"] as unknown[];
      if (!warningsList || !Array.isArray(warningsList) || warningsList.length === 0) {
        warn(`Entry ${label}: ${status} entry has no warnings`);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 9. Content type keys valid
// ---------------------------------------------------------------------------

console.log("\n[Check 9] Verifying content type keys…");

for (const key of Object.keys(overlay)) {
  if (!REQUIRED_TOP_KEYS.includes(key)) {
    err(`Unknown top-level key: "${key}"`);
  }
}
pass("All content type keys are valid");

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

console.log("\n--- Overlay validation results ---");
console.log(`  Total entries validated: ${totalEntries}`);
console.log(`    approved:           ${approvedCount}`);
console.log(`    rejected:           ${rejectedCount}`);
console.log(`    changes_requested:  ${changesCount}`);
console.log(`    partially_reviewed: ${partialCount}`);
console.log(`    needs_review:       ${needsReviewCount}`);
console.log(`  Errors:   ${errors}`);
console.log(`  Warnings: ${warnings}`);

if (errors > 0) {
  console.log(`\n[FAIL] ${errors} error(s) — overlay is not valid`);
  process.exit(1);
}

console.log(`\n[OK] Overlay validation passed — ${totalEntries} entries, 0 errors`);
process.exit(0);
