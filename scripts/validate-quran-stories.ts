/**
 * Quran Stories Validator
 *
 * Imports the story data directly via tsx and validates it.
 *
 * Rules enforced:
 * 1. Every story has a unique storyId
 * 2. Every story has Arabic and English titles
 * 3. Every story has at least one Quran reference
 * 4. Every Quran reference has valid surah (1-114) and ayah numbers
 * 5. Every story segment maps to a valid Quran range
 * 6. Every explanation has at least one sourceId or is marked needs_review
 * 7. Every sourceId exists in TRUSTED_SOURCE_IDS
 * 8. Kids and adult explanations are separate (both must exist)
 * 9. arabicText is NEVER set as a string literal
 * 10. Related stories point to existing storyIds (within batch, warn otherwise)
 * 11. Related stories include relationType from valid set
 * 12. Related stories include evidenceReferences with sourceIds
 * 13. Related stories include Arabic and English explanations
 * 14. No duplicate story slugs
 * 15. Every segment has sunniReview
 * 16. sunniReview.reviewedAgainst must not be empty
 * 17. Every reviewedAgainst sourceId is a valid trusted ID
 * 18. approved status requires matchedEvidence
 * 19. rejected segments are flagged
 *
 * Usage:
 *   npx tsx scripts/validate-quran-stories.ts [--verbose]
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = one or more checks failed
 */

import { resolve } from 'path';

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');

// ---------------------------------------------------------------------------
// Trusted source IDs — matching TAFSIR_CATALOG keys + _ar/_en variants
// ---------------------------------------------------------------------------

const TAFSIR_BASE_IDS = [
  'ibn_kathir', 'tabari', 'qurtubi', 'saadi', 'baghawi', 'zamakhshari',
  'razi', 'ibn_ashur', 'shawkani', 'jalalayn', 'muyassar', 'ala_saadi',
  'tanwir_miqbas', 'kashaf', 'baidawi',
];

const TRUSTED_SOURCE_IDS = new Set<string>([
  ...TAFSIR_BASE_IDS,
  ...TAFSIR_BASE_IDS.map((id) => `${id}_ar`),
  ...TAFSIR_BASE_IDS.map((id) => `${id}_en`),
]);

const VALID_RELATION_TYPES = new Set([
  'same_prophet', 'same_theme', 'same_event_pattern', 'same_moral_lesson',
  'contrast', 'chronological', 'same_surah', 'shared_character',
]);

// Standard ayah counts per surah (1-indexed, position 0 is unused)
const AYAH_COUNTS = [
  0,
  7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99,
  128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
  34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59, 37, 35, 38,
  29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14, 11, 11, 18,
  12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42, 29,
  19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8,
  11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6,
];

function isValidAyah(surah: number, ayah: number): boolean {
  if (surah < 1 || surah > 114) return false;
  return ayah >= 1 && ayah <= AYAH_COUNTS[surah];
}

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------

let _errors: string[] = [];
let _warnings: string[] = [];
let _passed = 0;

function ok(msg: string) {
  _passed++;
  if (VERBOSE) process.stdout.write(`  ✓ ${msg}\n`);
}

function err(msg: string) {
  _errors.push(msg);
  process.stdout.write(`  ✗ ${msg}\n`);
}

function warn(msg: string) {
  _warnings.push(msg);
  process.stdout.write(`  ⚠ ${msg}\n`);
}

// ---------------------------------------------------------------------------
// Main validation
// ---------------------------------------------------------------------------

async function main() {
  process.stdout.write('\n=== Quran Stories Validator ===\n\n');

  // Dynamically import the story data
  const storyFilePath = resolve(__dirname, '../frontend/src/data/quranStories.ts');
  process.stdout.write(`Loading: ${storyFilePath}\n\n`);

  // Use dynamic import — tsx resolves TypeScript paths
  const mod = await import(storyFilePath) as { QURAN_STORIES_FIRST_BATCH: import('../frontend/src/types/quranStory').QuranStory[] };
  const stories = mod.QURAN_STORIES_FIRST_BATCH;

  if (!stories || stories.length === 0) {
    err('QURAN_STORIES_FIRST_BATCH is empty or not exported');
    process.exit(1);
  }

  process.stdout.write(`Loaded ${stories.length} stories\n\n`);

  const storyIds = new Set<string>();
  const slugs = new Set<string>();

  for (const story of stories) {
    const ctx = `[${story.storyId}]`;

    // 1. Unique storyId
    if (storyIds.has(story.storyId)) {
      err(`${ctx} Duplicate storyId`);
    } else {
      storyIds.add(story.storyId);
      ok(`${ctx} Unique storyId`);
    }

    // 2. Unique slug
    if (!story.slug) {
      err(`${ctx} Missing slug`);
    } else if (slugs.has(story.slug)) {
      err(`${ctx} Duplicate slug: "${story.slug}"`);
    } else {
      slugs.add(story.slug);
      ok(`${ctx} Unique slug`);
    }

    // 3. Titles
    if (!story.titleArabic?.trim()) {
      err(`${ctx} Missing titleArabic`);
    } else { ok(`${ctx} Has titleArabic`); }

    if (!story.titleEnglish?.trim()) {
      err(`${ctx} Missing titleEnglish`);
    } else { ok(`${ctx} Has titleEnglish`); }

    // 4. At least one Quran reference
    if (!story.quranReferences?.length) {
      err(`${ctx} No quranReferences`);
    } else {
      ok(`${ctx} Has ${story.quranReferences.length} quranReference(s)`);

      for (const ref of story.quranReferences) {
        if (ref.surahNumber < 1 || ref.surahNumber > 114) {
          err(`${ctx} Invalid surah ${ref.surahNumber}`);
        } else if (!isValidAyah(ref.surahNumber, ref.ayahStart)) {
          err(`${ctx} Invalid ayahStart ${ref.ayahStart} in surah ${ref.surahNumber}`);
        } else if (!isValidAyah(ref.surahNumber, ref.ayahEnd)) {
          err(`${ctx} Invalid ayahEnd ${ref.ayahEnd} in surah ${ref.surahNumber}`);
        } else if (ref.ayahEnd < ref.ayahStart) {
          err(`${ctx} ayahEnd < ayahStart in ${ref.surahNumber}:${ref.ayahStart}-${ref.ayahEnd}`);
        } else {
          ok(`${ctx} Valid ref ${ref.surahNumber}:${ref.ayahStart}-${ref.ayahEnd}`);
        }

        // arabicText must never be set
        if ((ref as Record<string, unknown>)['arabicText'] !== undefined) {
          err(`${ctx} arabicText must never be a string literal — fetch from Quran DB instead`);
        }

        // tafsirSourceIds
        for (const sid of ref.tafsirSourceIds ?? []) {
          if (!TRUSTED_SOURCE_IDS.has(sid)) {
            err(`${ctx} Unknown tafsirSourceId: "${sid}"`);
          }
        }
      }
    }

    // 5. Story-level sourceIds
    if (!story.sourceIds?.length) {
      err(`${ctx} No story-level sourceIds`);
    } else {
      for (const sid of story.sourceIds) {
        if (!sid?.trim()) {
          err(`${ctx} Empty sourceId`);
        } else if (!TRUSTED_SOURCE_IDS.has(sid)) {
          err(`${ctx} Unknown sourceId: "${sid}"`);
        } else {
          ok(`${ctx} Valid sourceId: ${sid}`);
        }
      }
    }

    // 6. Audience levels
    const levels = story.audienceLevels ?? [];
    if (!levels.includes('kids') || !levels.includes('adults')) {
      err(`${ctx} audienceLevels must include both "kids" and "adults"`);
    } else {
      ok(`${ctx} Has both audience levels`);
    }

    // 7. Segments
    if (!story.storySegments?.length) {
      warn(`${ctx} No storySegments`);
    } else {
      const segIds = new Set<string>();

      for (const seg of story.storySegments) {
        const sctx = `${ctx}[${seg.segmentId}]`;

        // Unique segment ID
        if (segIds.has(seg.segmentId)) {
          err(`${sctx} Duplicate segmentId`);
        } else {
          segIds.add(seg.segmentId);
          ok(`${sctx} Unique segmentId`);
        }

        // Valid surah/ayah (if set)
        if (seg.surahNumber && seg.ayahStart && seg.ayahEnd) {
          if (!isValidAyah(seg.surahNumber, seg.ayahStart) || !isValidAyah(seg.surahNumber, seg.ayahEnd)) {
            err(`${sctx} Invalid surah/ayah range: ${seg.surahNumber}:${seg.ayahStart}-${seg.ayahEnd}`);
          } else {
            ok(`${sctx} Valid range ${seg.surahNumber}:${seg.ayahStart}-${seg.ayahEnd}`);
          }
        }

        // Kids summaries
        if (!seg.summaryKidsArabic?.trim() || !seg.summaryKidsEnglish?.trim()) {
          err(`${sctx} Missing kids summary`);
        } else { ok(`${sctx} Has kids summary`); }

        // Adult summaries
        if (!seg.summaryAdultsArabic?.trim() || !seg.summaryAdultsEnglish?.trim()) {
          err(`${sctx} Missing adults summary`);
        } else { ok(`${sctx} Has adults summary`); }

        // Segment sourceIds
        if (!seg.sourceIds?.length) {
          const markedReview = seg.warnings?.some((w) => w.toLowerCase().includes('review'));
          if (!markedReview) {
            err(`${sctx} No sourceIds and not marked for review`);
          } else {
            warn(`${sctx} No sourceIds — marked needs_review (acceptable)`);
          }
        } else {
          for (const sid of seg.sourceIds) {
            if (!sid?.trim()) {
              err(`${sctx} Empty sourceId`);
            } else if (!TRUSTED_SOURCE_IDS.has(sid)) {
              err(`${sctx} Unknown sourceId: "${sid}"`);
            } else {
              ok(`${sctx} Valid sourceId: ${sid}`);
            }
          }
        }

        // sunniReview
        if (!seg.sunniReview) {
          err(`${sctx} Missing sunniReview`);
        } else {
          ok(`${sctx} Has sunniReview`);

          if (!seg.sunniReview.reviewedAgainst?.length) {
            err(`${sctx} sunniReview.reviewedAgainst is empty`);
          } else {
            for (const sid of seg.sunniReview.reviewedAgainst) {
              if (!TRUSTED_SOURCE_IDS.has(sid)) {
                err(`${sctx} Unknown reviewedAgainst sourceId: "${sid}"`);
              }
            }
            ok(`${sctx} reviewedAgainst has ${seg.sunniReview.reviewedAgainst.length} source(s)`);
          }

          if (seg.sunniReview.status === 'approved' && !seg.sunniReview.matchedEvidence?.length) {
            err(`${sctx} approved status requires matchedEvidence`);
          }

          if (seg.sunniReview.status === 'needs_review' && !seg.sunniReview.humanReviewRequired) {
            warn(`${sctx} needs_review but humanReviewRequired=false`);
          }

          if (seg.sunniReview.status === 'rejected') {
            warn(`${sctx} REJECTED — must not be displayed as normal content`);
          }
        }

        // Lessons exist
        if (!seg.lessonsArabic?.length || !seg.lessonsEnglish?.length) {
          warn(`${sctx} No lessons defined`);
        } else { ok(`${sctx} Has lessons`); }
      }
    }

    // 8. Related stories
    for (const rel of story.relatedStories ?? []) {
      const rctx = `${ctx}[→${rel.storyId}]`;

      if (!VALID_RELATION_TYPES.has(rel.relationType)) {
        err(`${rctx} Invalid relationType: "${rel.relationType}"`);
      } else { ok(`${rctx} Valid relationType`); }

      if (!rel.explanationArabic?.trim() || !rel.explanationEnglish?.trim()) {
        err(`${rctx} Missing Arabic or English explanation`);
      } else { ok(`${rctx} Has explanations`); }

      if (!rel.evidenceReferences?.length) {
        err(`${rctx} No evidenceReferences`);
      } else {
        for (const ev of rel.evidenceReferences) {
          if (ev.surahNumber < 1 || ev.surahNumber > 114) {
            err(`${rctx} Invalid surah ${ev.surahNumber} in evidence`);
          }
          if (!ev.sourceIds?.length) {
            err(`${rctx} evidenceReference has no sourceIds`);
          } else {
            for (const sid of ev.sourceIds) {
              if (!TRUSTED_SOURCE_IDS.has(sid)) {
                err(`${rctx} Unknown evidenceReference sourceId: "${sid}"`);
              }
            }
          }
        }
        ok(`${rctx} Has ${rel.evidenceReferences.length} evidenceReference(s)`);
      }

      // Warn if related story not in this batch (may be in DB)
      if (!storyIds.has(rel.storyId)) {
        warn(`${rctx} Story not in current batch — must exist in DB`);
      }
    }
  }

  // Final report
  process.stdout.write(`\n--- Results ---\n`);
  process.stdout.write(`  Passed: ${_passed}\n`);
  process.stdout.write(`  Warnings: ${_warnings.length}\n`);
  process.stdout.write(`  Errors: ${_errors.length}\n\n`);

  if (_errors.length > 0) {
    process.stdout.write('VALIDATION FAILED\n\n');
    process.exit(1);
  } else {
    process.stdout.write('VALIDATION PASSED\n\n');
    process.exit(0);
  }
}

main().catch((err) => {
  process.stderr.write(`Fatal: ${err}\n`);
  process.exit(1);
});
