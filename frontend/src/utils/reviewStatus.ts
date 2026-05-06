/**
 * Phase 6.5 – Review Status Utility
 *
 * Reads the generated review status overlay and provides safe helpers for
 * determining public display state of story segments, KG relations, and
 * other Quran-sensitive content.
 *
 * Safety rules:
 * - Default status is always "needs_review" (safe default)
 * - Approved status requires valid metadata (reviewerId, reviewedAt, notesSummary)
 * - Rejected entries NEVER return as approved
 * - Missing overlay entry → needs_review
 * - Malformed overlay entry → needs_review
 * - humanReviewRequired is preserved — overlay cannot clear it
 */
import overlayJson from '../data/generated/reviewStatusOverlay.json';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ReviewOverlayStatus =
  | 'approved'
  | 'rejected'
  | 'changes_requested'
  | 'needs_review'
  | 'partially_reviewed';

export type ReviewContentType =
  | 'story_segment'
  | 'related_story'
  | 'kg_relation'
  | 'source_evidence'
  | 'disagreement_note';

export interface ReviewOverlayEntry {
  status: ReviewOverlayStatus;
  reviewerId?: string;
  reviewerName?: string;
  reviewedAt?: string;
  notesSummary?: string;
  taskId: string;
  warnings: string[];
}

export interface ReviewStatusOverlay {
  version: string;
  generatedAt: string;
  story_segment: Record<string, ReviewOverlayEntry>;
  related_story: Record<string, ReviewOverlayEntry>;
  kg_relation: Record<string, ReviewOverlayEntry>;
  source_evidence: Record<string, ReviewOverlayEntry>;
  disagreement_note: Record<string, ReviewOverlayEntry>;
}

// ---------------------------------------------------------------------------
// Loaded overlay (static JSON import — bundled at build time)
// ---------------------------------------------------------------------------

const overlay = overlayJson as unknown as ReviewStatusOverlay;

const VALID_STATUSES = new Set<ReviewOverlayStatus>([
  'approved',
  'rejected',
  'changes_requested',
  'needs_review',
  'partially_reviewed',
]);

// ---------------------------------------------------------------------------
// Core lookup
// ---------------------------------------------------------------------------

/**
 * Look up a content item's review overlay entry.
 * Returns null if not found or invalid.
 */
function getOverlayEntry(
  contentType: ReviewContentType,
  contentId: string
): ReviewOverlayEntry | null {
  try {
    const bucket = overlay[contentType] as Record<string, ReviewOverlayEntry> | undefined;
    if (!bucket) return null;
    const entry = bucket[contentId];
    if (!entry || typeof entry !== 'object') return null;
    return entry;
  } catch {
    return null;
  }
}

/**
 * Validate that an approved entry has all required metadata.
 * Returns false if any required field is missing — forcing a fallback to needs_review.
 */
function isApprovedEntryValid(entry: ReviewOverlayEntry): boolean {
  if (entry.status !== 'approved') return false;
  if (!entry.reviewerId || !entry.reviewerId.trim()) return false;
  if (!entry.reviewedAt) return false;
  if (!entry.notesSummary || !entry.notesSummary.trim()) return false;
  if (!entry.taskId) return false;
  return true;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Get the effective review status for a content item.
 *
 * Safety: defaults to 'needs_review' if:
 * - No overlay entry exists
 * - Entry is malformed
 * - Approved entry is missing required metadata
 */
export function getReviewStatus(
  contentType: ReviewContentType,
  contentId: string
): ReviewOverlayStatus {
  const entry = getOverlayEntry(contentType, contentId);
  if (!entry) return 'needs_review';

  // Validate status is a known enum value
  if (!VALID_STATUSES.has(entry.status)) return 'needs_review';

  // Approved requires full metadata
  if (entry.status === 'approved' && !isApprovedEntryValid(entry)) {
    return 'needs_review';
  }

  return entry.status;
}

/**
 * Returns true only if the content item is fully approved with valid metadata.
 * Rejected, pending, partially_reviewed → false.
 */
export function isApproved(
  contentType: ReviewContentType,
  contentId: string
): boolean {
  return getReviewStatus(contentType, contentId) === 'approved';
}

/**
 * Returns true if the content item is rejected.
 * A rejected item must never display as approved.
 */
export function isRejected(
  contentType: ReviewContentType,
  contentId: string
): boolean {
  return getReviewStatus(contentType, contentId) === 'rejected';
}

/**
 * Returns true if changes were requested for this content item.
 * Changes requested ≠ approved.
 */
export function isChangesRequested(
  contentType: ReviewContentType,
  contentId: string
): boolean {
  return getReviewStatus(contentType, contentId) === 'changes_requested';
}

/**
 * Returns true if the item is partially reviewed (compound conditions partially met).
 */
export function isPartiallyReviewed(
  contentType: ReviewContentType,
  contentId: string
): boolean {
  return getReviewStatus(contentType, contentId) === 'partially_reviewed';
}

/**
 * Get the full overlay entry for a content item, or null.
 * Only returns entry if it is valid (approved entries checked for complete metadata).
 */
export function getReviewEntry(
  contentType: ReviewContentType,
  contentId: string
): ReviewOverlayEntry | null {
  const entry = getOverlayEntry(contentType, contentId);
  if (!entry) return null;
  if (!VALID_STATUSES.has(entry.status)) return null;
  if (entry.status === 'approved' && !isApprovedEntryValid(entry)) return null;
  return entry;
}

/**
 * Merge the base status from static content with the overlay status.
 *
 * The overlay can upgrade needs_review → approved (if valid).
 * The overlay CANNOT downgrade approved → needs_review without explicit rejection.
 * However, for safety: base humanReviewRequired overrides overlay for public display
 * (overlay cannot clear the humanReviewRequired flag).
 *
 * Note: "approved" from base static data (quranStories.ts) without an overlay entry
 * is preserved — these may represent pre-Phase 6 manual approvals.
 */
export function mergeBaseStatusWithOverlay(
  baseStatus: 'approved' | 'needs_review' | 'rejected',
  overlayStatus: ReviewOverlayStatus
): ReviewOverlayStatus {
  // Rejected base is never overridden
  if (baseStatus === 'rejected') return 'rejected';

  // Overlay rejected takes priority
  if (overlayStatus === 'rejected') return 'rejected';

  // If overlay has a definitive non-pending status, use it
  if (
    overlayStatus === 'approved' ||
    overlayStatus === 'partially_reviewed' ||
    overlayStatus === 'changes_requested'
  ) {
    return overlayStatus;
  }

  // Base was already approved (pre-Phase 6 manual approval) → preserve
  if (baseStatus === 'approved' && overlayStatus === 'needs_review') {
    return 'approved';
  }

  return overlayStatus;
}

/**
 * Get the aggregate review status across a set of segments for a story.
 *
 * - All approved → 'approved'
 * - Mixed approved/pending → 'partially_reviewed'
 * - Any rejected → 'rejected'
 * - None approved → 'needs_review'
 */
export function getStoryApprovalStatus(
  segmentIds: string[]
): { status: ReviewOverlayStatus; approvedCount: number; totalCount: number } {
  if (segmentIds.length === 0) return { status: 'needs_review', approvedCount: 0, totalCount: 0 };

  let approvedCount = 0;
  let rejectedCount = 0;

  for (const segId of segmentIds) {
    const s = getReviewStatus('story_segment', segId);
    if (s === 'approved') approvedCount++;
    if (s === 'rejected') rejectedCount++;
  }

  if (rejectedCount > 0) return { status: 'rejected', approvedCount, totalCount: segmentIds.length };
  if (approvedCount === segmentIds.length) return { status: 'approved', approvedCount, totalCount: segmentIds.length };
  if (approvedCount > 0) return { status: 'partially_reviewed', approvedCount, totalCount: segmentIds.length };
  return { status: 'needs_review', approvedCount: 0, totalCount: segmentIds.length };
}

/**
 * Get review status for a KG relation group by storyId + segmentId.
 * The group key format is "story:{storyId}:{segmentId}" or "story:{storyId}".
 */
export function getKGRelationStatus(
  storyId: string | undefined,
  segmentId: string | undefined
): ReviewOverlayStatus {
  if (!storyId) return 'needs_review';
  const groupKey = segmentId
    ? `story:${storyId}:${segmentId}`
    : `story:${storyId}`;
  return getReviewStatus('kg_relation', groupKey);
}

/**
 * Get translated label for a review status badge.
 */
export function getReviewBadgeLabel(
  status: ReviewOverlayStatus,
  language: 'ar' | 'en'
): string {
  const labels: Record<ReviewOverlayStatus, { ar: string; en: string }> = {
    approved: { ar: 'معتمد', en: 'Approved' },
    rejected: { ar: 'مرفوض', en: 'Rejected' },
    changes_requested: { ar: 'يحتاج تعديلات', en: 'Changes Requested' },
    needs_review: { ar: 'بانتظار المراجعة', en: 'Needs Review' },
    partially_reviewed: { ar: 'مراجعة جزئية', en: 'Partially Reviewed' },
  };
  return labels[status]?.[language] ?? (language === 'ar' ? 'بانتظار المراجعة' : 'Needs Review');
}

/**
 * Get the overlay metadata for display (reviewer name/date).
 * Returns null if no valid approved entry exists.
 */
export function getApprovalMetadata(
  contentType: ReviewContentType,
  contentId: string
): { reviewerName: string; reviewedAt: string; notesSummary?: string } | null {
  const entry = getReviewEntry(contentType, contentId);
  if (!entry || entry.status !== 'approved') return null;
  return {
    reviewerName: entry.reviewerName ?? entry.reviewerId ?? '',
    reviewedAt: entry.reviewedAt ?? '',
    notesSummary: entry.notesSummary,
  };
}

/**
 * Metadata about the overlay itself — for admin dashboard freshness indicator.
 */
export function getOverlayMeta(): { version: string; generatedAt: string } {
  return {
    version: overlay.version ?? 'unknown',
    generatedAt: overlay.generatedAt ?? '',
  };
}
