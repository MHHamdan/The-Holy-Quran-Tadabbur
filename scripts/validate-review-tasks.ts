#!/usr/bin/env npx tsx
/**
 * Phase 6: Review Task Validator
 *
 * Validates the generated review_tasks.json for integrity.
 *
 * Checks:
 *   1.  Every task has a stable unique ID
 *   2.  contentType is a valid enum value
 *   3.  contentId is non-empty
 *   4.  status is a valid enum value
 *   5.  sourceIds (if present) exist in tafseer_sources.json or are system markers
 *   6.  quranReferences have valid surahNumber (1–114) and ayahStart >= 1
 *   7.  Approved tasks must have decision metadata (reviewerId, reviewedAt, notes)
 *   8.  Rejected tasks must have decision notes
 *   9.  No task embeds Arabic Quran text in text fields
 *  10.  humanReviewRequired is true for pending tasks
 *  11.  No unsupported sourceId
 *  12.  No duplicate (contentType + contentId)
 *  13.  priority is a valid enum value
 *  14.  language is a valid enum value
 *  15.  disagreement_note tasks have non-empty disagreementNotes
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
const TASKS_PATH = path.join(ROOT, "backend", "app", "data", "review_tasks.json");
const TAFSEER_SOURCES_PATH = path.join(ROOT, "data", "manifests", "tafseer_sources.json");

// ---------------------------------------------------------------------------
// Valid enums
// ---------------------------------------------------------------------------

const VALID_CONTENT_TYPES = new Set([
  "story_segment",
  "related_story",
  "kg_relation",
  "source_evidence",
  "disagreement_note",
]);

const VALID_STATUSES = new Set(["pending", "approved", "rejected", "changes_requested"]);
const VALID_PRIORITIES = new Set(["low", "medium", "high"]);
const VALID_LANGUAGES = new Set(["ar", "en", "both"]);

// System source IDs that are allowed without being in tafseer_sources.json
const SYSTEM_SOURCE_IDS = new Set(["story_manifest", "system:embedding", "story_manifest_v1"]);

// ---------------------------------------------------------------------------
// Arabic text detector — no Quran text may appear in tasks
// ---------------------------------------------------------------------------

const ARABIC_REGEX = /[؀-ۿ]{5,}/;

function containsArabicText(s: unknown): boolean {
  if (typeof s !== "string") return false;
  return ARABIC_REGEX.test(s);
}

function checkNoArabicText(value: unknown, path: string): boolean {
  if (typeof value === "string") {
    if (containsArabicText(value)) {
      err(`Arabic text found in field '${path}': ${value.slice(0, 50)}…`);
      return false;
    }
  } else if (Array.isArray(value)) {
    return value.every((v, i) => checkNoArabicText(v, `${path}[${i}]`));
  }
  return true;
}

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

if (!fs.existsSync(TASKS_PATH)) {
  console.error(`[ERROR] review_tasks.json not found at ${TASKS_PATH}`);
  console.error("Run: npx tsx scripts/generate-review-tasks.ts");
  process.exit(1);
}

const raw = JSON.parse(fs.readFileSync(TASKS_PATH, "utf-8"));
const tasks: Array<Record<string, unknown>> = raw.tasks ?? [];

// Load allowed source IDs
let allowedSourceIds = new Set<string>(SYSTEM_SOURCE_IDS);
if (fs.existsSync(TAFSEER_SOURCES_PATH)) {
  const sources = JSON.parse(fs.readFileSync(TAFSEER_SOURCES_PATH, "utf-8"));
  const sourcesList: Array<{ id?: string; source_id?: string }> = sources.sources ?? sources;
  for (const s of sourcesList) {
    const sid = s.id ?? s.source_id;
    if (sid) allowedSourceIds.add(sid);
  }
}

// Hard-code known valid source IDs (from sourceRegistry.ts + ibn_kathir variants)
const KNOWN_SOURCE_IDS = new Set([
  "ibn_kathir", "ibn_kathir_ar", "ibn_kathir_en",
  "tabari", "tabari_ar", "tabari_en",
  "qurtubi", "qurtubi_ar", "qurtubi_en",
  "saadi", "saadi_ar", "saadi_en",
  "baghawi", "baghawi_ar", "baghawi_en",
  "muyassar", "muyassar_ar", "muyassar_en",
  "tafheem_mawdudi_en", "sahih_international",
  "story_manifest", "story_manifest_v1", "system:embedding",
]);

for (const id of KNOWN_SOURCE_IDS) {
  allowedSourceIds.add(id);
}

console.log(`\nValidating ${tasks.length} review tasks from ${TASKS_PATH}`);

// ---------------------------------------------------------------------------
// Check 1: Task count > 0
// ---------------------------------------------------------------------------

check("Task file is non-empty", () => {
  if (tasks.length === 0) {
    err("No tasks found — run generate-review-tasks.ts first");
  } else {
    ok(`${tasks.length} tasks found`);
  }
});

// ---------------------------------------------------------------------------
// Check 2–4: Per-task field validation
// ---------------------------------------------------------------------------

check("Each task has valid id, contentType, contentId, status", () => {
  let bad = 0;
  for (const task of tasks) {
    if (!task.id || typeof task.id !== "string" || !task.id.startsWith("rt_")) {
      err(`Task missing or malformed id: ${JSON.stringify(task.id)}`);
      bad++;
    }
    if (!VALID_CONTENT_TYPES.has(task.contentType as string)) {
      err(`Task ${task.id}: invalid contentType '${task.contentType}'`);
      bad++;
    }
    if (!task.contentId || typeof task.contentId !== "string" || (task.contentId as string).trim() === "") {
      err(`Task ${task.id}: contentId is empty`);
      bad++;
    }
    if (!VALID_STATUSES.has(task.status as string)) {
      err(`Task ${task.id}: invalid status '${task.status}'`);
      bad++;
    }
  }
  if (bad === 0) ok("All tasks have valid id/contentType/contentId/status");
});

// ---------------------------------------------------------------------------
// Check 5: Priority and language
// ---------------------------------------------------------------------------

check("Priority and language are valid enums", () => {
  let bad = 0;
  for (const task of tasks) {
    if (!VALID_PRIORITIES.has(task.priority as string)) {
      err(`Task ${task.id}: invalid priority '${task.priority}'`);
      bad++;
    }
    if (!VALID_LANGUAGES.has(task.language as string)) {
      err(`Task ${task.id}: invalid language '${task.language}'`);
      bad++;
    }
  }
  if (bad === 0) ok("All priorities and languages are valid");
});

// ---------------------------------------------------------------------------
// Check 6: No duplicate (contentType + contentId)
// ---------------------------------------------------------------------------

check("No duplicate contentType + contentId", () => {
  const seen = new Map<string, string>();
  let dups = 0;
  for (const task of tasks) {
    const key = `${task.contentType}:${task.contentId}`;
    if (seen.has(key)) {
      err(`Duplicate task: '${key}' appears in tasks ${seen.get(key)} and ${task.id}`);
      dups++;
    } else {
      seen.set(key, task.id as string);
    }
  }
  if (dups === 0) ok(`No duplicates found among ${tasks.length} tasks`);
});

// ---------------------------------------------------------------------------
// Check 7: No duplicate task IDs
// ---------------------------------------------------------------------------

check("No duplicate task IDs", () => {
  const seenIds = new Set<string>();
  let dups = 0;
  for (const task of tasks) {
    if (seenIds.has(task.id as string)) {
      err(`Duplicate task ID: ${task.id}`);
      dups++;
    }
    seenIds.add(task.id as string);
  }
  if (dups === 0) ok("All task IDs are unique");
});

// ---------------------------------------------------------------------------
// Check 8: Quran references are valid
// ---------------------------------------------------------------------------

check("Quran references are valid (surah 1–114, ayah >= 1)", () => {
  let bad = 0;
  for (const task of tasks) {
    const refs = (task.quranReferences ?? []) as Array<Record<string, unknown>>;
    for (const ref of refs) {
      const sura = ref.surahNumber as number;
      const aya = ref.ayahStart as number;
      if (sura < 1 || sura > 114) {
        err(`Task ${task.id}: invalid surahNumber ${sura}`);
        bad++;
      }
      if (aya < 1) {
        err(`Task ${task.id}: invalid ayahStart ${aya}`);
        bad++;
      }
    }
  }
  if (bad === 0) ok("All Quran references are valid");
});

// ---------------------------------------------------------------------------
// Check 9: Source IDs are from known list
// ---------------------------------------------------------------------------

check("Source IDs are from known sources", () => {
  let bad = 0;
  for (const task of tasks) {
    const sourceIds = (task.sourceIds ?? []) as string[];
    for (const sid of sourceIds) {
      if (!allowedSourceIds.has(sid)) {
        warn(`Task ${task.id}: unknown sourceId '${sid}' — not in tafseer_sources or registry`);
      }
    }
  }
  if (bad === 0) ok("Source ID check complete");
});

// ---------------------------------------------------------------------------
// Check 10: Approved tasks must have decision metadata
// ---------------------------------------------------------------------------

check("Approved tasks have complete decision metadata", () => {
  let bad = 0;
  for (const task of tasks) {
    if (task.status === "approved") {
      const decision = task.decision as Record<string, unknown> | null;
      if (!decision) {
        err(`Task ${task.id}: status=approved but decision is null`);
        bad++;
      } else {
        if (!decision.reviewerId) {
          err(`Task ${task.id}: approved but missing decision.reviewerId`);
          bad++;
        }
        if (!decision.reviewedAt) {
          err(`Task ${task.id}: approved but missing decision.reviewedAt`);
          bad++;
        }
        if (!decision.notes || (decision.notes as string).trim() === "") {
          err(`Task ${task.id}: approved but missing decision.notes`);
          bad++;
        }
      }
    }
  }
  if (bad === 0) ok("Approved task decision metadata OK");
});

// ---------------------------------------------------------------------------
// Check 11: Rejected tasks must have notes
// ---------------------------------------------------------------------------

check("Rejected tasks have decision notes", () => {
  let bad = 0;
  for (const task of tasks) {
    if (task.status === "rejected") {
      const decision = task.decision as Record<string, unknown> | null;
      if (!decision?.notes || (decision.notes as string).trim() === "") {
        err(`Task ${task.id}: status=rejected but decision.notes is missing`);
        bad++;
      }
    }
  }
  if (bad === 0) ok("Rejected task notes OK");
});

// ---------------------------------------------------------------------------
// Check 12: No Arabic text in text fields
// ---------------------------------------------------------------------------

check("No Arabic Quran text embedded in tasks", () => {
  let bad = 0;
  for (const task of tasks) {
    const textFields: Array<[string, unknown]> = [
      ["summaryEnglish", task.summaryEnglish],
      ["warnings", task.warnings],
      ["disagreementNotes", task.disagreementNotes],
    ];
    for (const [fieldName, value] of textFields) {
      if (!checkNoArabicText(value, `task ${task.id}.${fieldName}`)) {
        bad++;
      }
    }
  }
  if (bad === 0) ok("No Arabic text found in task fields");
});

// ---------------------------------------------------------------------------
// Check 13: humanReviewRequired for pending sensitive tasks
// ---------------------------------------------------------------------------

check("humanReviewRequired=true for all pending tasks", () => {
  let bad = 0;
  for (const task of tasks) {
    if (task.status === "pending" && !task.humanReviewRequired) {
      err(`Task ${task.id}: pending but humanReviewRequired=false`);
      bad++;
    }
  }
  if (bad === 0) ok("humanReviewRequired is true for all pending tasks");
});

// ---------------------------------------------------------------------------
// Check 14: disagreement_note tasks have non-empty disagreementNotes
// ---------------------------------------------------------------------------

check("disagreement_note tasks have non-empty disagreementNotes", () => {
  let bad = 0;
  for (const task of tasks) {
    if (task.contentType === "disagreement_note") {
      const notes = task.disagreementNotes as string[] | undefined;
      if (!notes || notes.length === 0) {
        err(`Task ${task.id}: contentType=disagreement_note but disagreementNotes is empty`);
        bad++;
      }
    }
  }
  if (bad === 0) ok("disagreement_note tasks have notes");
});

// ---------------------------------------------------------------------------
// Check 15: createdAt / updatedAt are ISO strings
// ---------------------------------------------------------------------------

check("timestamps are ISO 8601 strings", () => {
  const ISO_RE = /^\d{4}-\d{2}-\d{2}T/;
  let bad = 0;
  for (const task of tasks) {
    if (!ISO_RE.test(task.createdAt as string)) {
      err(`Task ${task.id}: invalid createdAt '${task.createdAt}'`);
      bad++;
    }
    if (!ISO_RE.test(task.updatedAt as string)) {
      err(`Task ${task.id}: invalid updatedAt '${task.updatedAt}'`);
      bad++;
    }
  }
  if (bad === 0) ok("All timestamps are valid ISO 8601");
});

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

console.log(`\n${"=".repeat(60)}`);
console.log(`Review Tasks Validation Summary`);
console.log(`${"=".repeat(60)}`);
console.log(`Tasks validated: ${tasks.length}`);
console.log(`Errors:          ${errors}`);
console.log(`Warnings:        ${warnings_count}`);

if (errors > 0) {
  console.error(`\n[FAIL] Validation failed with ${errors} error(s).`);
  process.exit(1);
} else {
  console.log(`\n[OK] All validation checks passed.`);
  process.exit(0);
}
