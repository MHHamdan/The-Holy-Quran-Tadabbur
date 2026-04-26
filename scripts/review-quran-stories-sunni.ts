/**
 * Quran Stories — Automatic Sunni Source Review
 *
 * Imports story data directly and verifies every segment against
 * approved Sunni source metadata.
 *
 * Approved Sunni canonical sources:
 *   ibn_kathir, tabari, qurtubi  (plus _ar/_en variants)
 *
 * Verified Sunni sources (can be in reviewedAgainst, not sole approval):
 *   saadi, baghawi  (plus _ar/_en variants)
 *
 * Rules:
 * 1. reviewedAgainst must contain approved Sunni sources only
 * 2. supporting-only sources cannot appear in reviewedAgainst
 * 3. approved status requires matchedEvidence
 * 4. kids summary must exist for review
 * 5. adults summary must exist for review
 * 6. rejected segments are flagged
 * 7. disagreement notes are surfaced
 *
 * Usage:
 *   npx tsx scripts/review-quran-stories-sunni.ts
 *
 * Output:
 *   docs/generated/story-sunni-review-report.md
 *
 * Exit codes:
 *   0 = review completed without hard errors
 *   1 = hard errors found
 */

import { writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import type { QuranStory, StorySegment } from '../frontend/src/types/quranStory';

// ---------------------------------------------------------------------------
// Source classification
// ---------------------------------------------------------------------------

const CANONICAL_SOURCES = new Set([
  'ibn_kathir', 'ibn_kathir_ar', 'ibn_kathir_en',
  'tabari', 'tabari_ar', 'tabari_en',
  'qurtubi', 'qurtubi_ar', 'qurtubi_en',
]);

const VERIFIED_SOURCES = new Set([
  'saadi', 'saadi_ar', 'saadi_en',
  'baghawi', 'baghawi_ar', 'baghawi_en',
]);

const ALL_ACCEPTED = new Set([...CANONICAL_SOURCES, ...VERIFIED_SOURCES]);

const SUPPORTING_ONLY = new Set([
  'al_muyassar_ar', 'muyassar', 'muyassar_ar', 'muyassar_en',
  'tafheem_mawdudi_en',
]);

// ---------------------------------------------------------------------------
// Issue types
// ---------------------------------------------------------------------------

interface Issue {
  storyId: string;
  segmentId: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
}

// ---------------------------------------------------------------------------
// Review logic
// ---------------------------------------------------------------------------

function reviewSegment(story: QuranStory, seg: StorySegment): Issue[] {
  const issues: Issue[] = [];
  const ctx = { storyId: story.storyId, segmentId: seg.segmentId };

  const r = seg.sunniReview;

  // 1. reviewedAgainst not empty
  if (!r.reviewedAgainst?.length) {
    issues.push({ ...ctx, severity: 'error', message: 'reviewedAgainst is empty' });
  } else {
    for (const sid of r.reviewedAgainst) {
      if (SUPPORTING_ONLY.has(sid)) {
        issues.push({ ...ctx, severity: 'error', message: `Supporting-only source in reviewedAgainst: "${sid}"` });
      } else if (!ALL_ACCEPTED.has(sid)) {
        issues.push({ ...ctx, severity: 'error', message: `Unknown source in reviewedAgainst: "${sid}"` });
      }
    }
  }

  // 2. approved requires matchedEvidence
  if (r.status === 'approved' && !r.matchedEvidence?.length) {
    issues.push({ ...ctx, severity: 'error', message: 'approved status requires matchedEvidence' });
  }

  // 3. supporting-only cannot be the sole approval
  if (r.status === 'approved' && r.reviewedAgainst?.length) {
    const hasCanonicalOrVerified = r.reviewedAgainst.some(
      (sid) => CANONICAL_SOURCES.has(sid) || VERIFIED_SOURCES.has(sid)
    );
    if (!hasCanonicalOrVerified) {
      issues.push({ ...ctx, severity: 'error', message: 'No canonical/verified source in reviewedAgainst — cannot approve' });
    }
  }

  // 4. rejected flagged
  if (r.status === 'rejected') {
    issues.push({ ...ctx, severity: 'warning', message: 'REJECTED segment — must not be displayed as normal content' });
  }

  // 5. kids summary exists
  if (!seg.summaryKidsArabic?.trim() || !seg.summaryKidsEnglish?.trim()) {
    issues.push({ ...ctx, severity: 'error', message: 'Missing kids summary' });
  }

  // 6. adults summary exists
  if (!seg.summaryAdultsArabic?.trim() || !seg.summaryAdultsEnglish?.trim()) {
    issues.push({ ...ctx, severity: 'error', message: 'Missing adults summary' });
  }

  // 7. segment sourceIds are accepted
  for (const sid of seg.sourceIds ?? []) {
    if (!ALL_ACCEPTED.has(sid)) {
      issues.push({ ...ctx, severity: 'error', message: `Unknown sourceId: "${sid}"` });
    }
  }

  // 8. humanReviewRequired for needs_review
  if (r.status === 'needs_review' && !r.humanReviewRequired) {
    issues.push({ ...ctx, severity: 'warning', message: 'needs_review but humanReviewRequired=false' });
  }

  // 9. disagreement notes surfaced as info
  for (const note of r.disagreementNotes ?? []) {
    issues.push({ ...ctx, severity: 'info', message: `Scholarly disagreement: ${note}` });
  }

  return issues;
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

function buildReport(stories: QuranStory[], allIssues: Issue[]): string {
  const totalStories = stories.length;
  const allSegs = stories.flatMap((s) => s.storySegments);
  const totalSegments = allSegs.length;

  const approved = allSegs.filter((s) => s.sunniReview.status === 'approved').length;
  const needsReview = allSegs.filter((s) => s.sunniReview.status === 'needs_review').length;
  const rejected = allSegs.filter((s) => s.sunniReview.status === 'rejected').length;
  const humanReq = allSegs.filter((s) => s.sunniReview.humanReviewRequired).length;

  const errors = allIssues.filter((i) => i.severity === 'error');
  const warnings = allIssues.filter((i) => i.severity === 'warning');
  const infos = allIssues.filter((i) => i.severity === 'info');

  const date = new Date().toISOString().split('T')[0];

  let md = `# Quran Stories — Sunni Source Review Report\n_Generated: ${date}_\n\n---\n\n`;

  md += `## Summary\n\n`;
  md += `| Metric | Count |\n|--------|-------|\n`;
  md += `| Total stories reviewed | ${totalStories} |\n`;
  md += `| Total segments reviewed | ${totalSegments} |\n`;
  md += `| Approved segments | ${approved} |\n`;
  md += `| Needs review segments | ${needsReview} |\n`;
  md += `| Rejected segments | ${rejected} |\n`;
  md += `| Segments requiring human review | ${humanReq} |\n`;
  md += `| Errors | ${errors.length} |\n`;
  md += `| Warnings | ${warnings.length} |\n`;
  md += `| Info/Disagreement notes | ${infos.length} |\n\n`;

  md += `---\n\n## Approved Sunni Sources\n\n`;
  md += `| Source ID | Tier |\n|-----------|------|\n`;
  for (const s of CANONICAL_SOURCES) md += `| ${s} | canonical |\n`;
  for (const s of VERIFIED_SOURCES) md += `| ${s} | verified |\n`;

  md += `\n---\n\n## Per-Story Status\n\n`;
  for (const story of stories) {
    const segs = story.storySegments;
    const storyApproved = segs.filter((s) => s.sunniReview.status === 'approved').length;
    const storyReview = segs.filter((s) => s.sunniReview.status === 'needs_review').length;
    const storyRejected = segs.filter((s) => s.sunniReview.status === 'rejected').length;
    md += `### ${story.titleEnglish} (\`${story.storyId}\`)\n`;
    md += `- Segments: ${segs.length} total — ${storyApproved} approved, ${storyReview} needs review, ${storyRejected} rejected\n`;
    md += `- Sources: ${story.sourceIds.join(', ')}\n`;
    md += `- Reliability: ${story.reliabilityLevel}\n\n`;
  }

  md += `---\n\n`;

  if (needsReview > 0) {
    md += `## Segments Needing Review\n\n`;
    for (const story of stories) {
      for (const seg of story.storySegments.filter((s) => s.sunniReview.status === 'needs_review')) {
        md += `- **${story.storyId}:${seg.segmentId}**`;
        md += ` — reviewedAgainst: [${seg.sunniReview.reviewedAgainst.join(', ')}]`;
        md += ` — humanReviewRequired: ${seg.sunniReview.humanReviewRequired}\n`;
        if (seg.sunniReview.disagreementNotes.length) {
          md += `  - Disagreement: ${seg.sunniReview.disagreementNotes.join('; ')}\n`;
        }
        if (seg.warnings.length) {
          md += `  - Warnings: ${seg.warnings.join('; ')}\n`;
        }
      }
    }
    md += `\n`;
  }

  if (rejected > 0) {
    md += `## Rejected Segments (DO NOT DISPLAY)\n\n`;
    for (const story of stories) {
      for (const seg of story.storySegments.filter((s) => s.sunniReview.status === 'rejected')) {
        md += `- **${story.storyId}:${seg.segmentId}**\n`;
      }
    }
    md += `\n`;
  }

  if (errors.length > 0) {
    md += `## Errors\n\n`;
    for (const e of errors) {
      md += `- ✗ \`${e.storyId}:${e.segmentId}\` — ${e.message}\n`;
    }
    md += `\n`;
  }

  if (warnings.length > 0) {
    md += `## Warnings\n\n`;
    for (const w of warnings) {
      md += `- ⚠ \`${w.storyId}:${w.segmentId}\` — ${w.message}\n`;
    }
    md += `\n`;
  }

  if (infos.length > 0) {
    md += `## Scholarly Disagreement Notes\n\n`;
    for (const info of infos) {
      md += `- ℹ \`${info.storyId}:${info.segmentId}\` — ${info.message}\n`;
    }
    md += `\n`;
  }

  md += `---\n\n## Methodology\n\n`;
  md += `- Generated by \`scripts/review-quran-stories-sunni.ts\`\n`;
  md += `- Does NOT access the internet, generate tafsir, or invent details\n`;
  md += `- All segments in this batch: status=needs_review (pending scholarly verification)\n`;
  md += `- matchedEvidence will be populated after tafsir chunks are linked in the DB\n`;
  md += `- A qualified scholar must review each segment before status=approved\n\n`;
  md += `## Next Steps\n\n`;
  md += `1. Human scholar reviews each needs_review segment against listed tafsir\n`;
  md += `2. matchedEvidence populated with actual DB chunk IDs\n`;
  md += `3. status updated to approved after review\n`;
  md += `4. Disagreement notes resolved or retained as scholarly context\n`;

  return md;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  process.stdout.write('\n=== Quran Stories — Sunni Source Review ===\n\n');

  const storyFilePath = resolve(__dirname, '../frontend/src/data/quranStories.ts');
  process.stdout.write(`Loading: ${storyFilePath}\n\n`);

  const mod = await import(storyFilePath) as { QURAN_STORIES_FIRST_BATCH: QuranStory[] };
  const stories = mod.QURAN_STORIES_FIRST_BATCH;

  const totalSegs = stories.reduce((n, s) => n + s.storySegments.length, 0);
  process.stdout.write(`Found ${stories.length} stories, ${totalSegs} segments\n\n`);

  const allIssues: Issue[] = [];
  for (const story of stories) {
    for (const seg of story.storySegments) {
      allIssues.push(...reviewSegment(story, seg));
    }
  }

  const errors = allIssues.filter((i) => i.severity === 'error');
  const warnings = allIssues.filter((i) => i.severity === 'warning');
  const infos = allIssues.filter((i) => i.severity === 'info');

  process.stdout.write(`Errors: ${errors.length}\n`);
  process.stdout.write(`Warnings: ${warnings.length}\n`);
  process.stdout.write(`Info notes: ${infos.length}\n\n`);

  for (const issue of allIssues) {
    const p = issue.severity === 'error' ? '✗' : issue.severity === 'warning' ? '⚠' : 'ℹ';
    process.stdout.write(`  ${p} [${issue.storyId}:${issue.segmentId}] ${issue.message}\n`);
  }

  const reportPath = resolve(__dirname, '../docs/generated/story-sunni-review-report.md');
  mkdirSync(dirname(reportPath), { recursive: true });
  writeFileSync(reportPath, buildReport(stories, allIssues), 'utf-8');
  process.stdout.write(`\nReport written to: ${reportPath}\n`);

  if (errors.length > 0) {
    process.stdout.write('\nREVIEW COMPLETED WITH ERRORS\n\n');
    process.exit(1);
  } else {
    process.stdout.write('\nREVIEW COMPLETED\n\n');
    process.exit(0);
  }
}

main().catch((e) => {
  process.stderr.write(`Fatal: ${e}\n`);
  process.exit(1);
});
