/**
 * Phase 6 — Admin Review Dashboard
 *
 * Admin-facing workflow for reviewing Quran-sensitive content.
 *
 * Safety rules enforced in this component:
 * - Warning displayed: "This content is not approved until documented scholarly review is completed."
 * - Approve button is disabled until notes field has ≥ 10 characters
 * - Reject button requires notes
 * - "Approved" badge only shown when backend returns status="approved"
 * - No Quran text is rendered from review tasks (Quran refs only)
 * - All content labeled as "pending scholarly review" until explicitly approved
 * - humanReviewRequired badge shown on every task
 * - Disagreement notes shown prominently with high-priority badge
 */
import { useState, useEffect, useCallback } from 'react';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Filter,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  BookOpen,
  Loader2,
  MessageSquare,
  BarChart3,
  RefreshCw,
  Info,
} from 'lucide-react';
import clsx from 'clsx';
import {
  reviewApi,
  ReviewTask,
  ReviewStatus,
  ReviewContentType,
  ReviewPriority,
  ReviewStatsResponse,
} from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { getOverlayMeta } from '../../utils/reviewStatus';

// =============================================================================
// Constants
// =============================================================================

const CONTENT_TYPE_KEYS: Record<ReviewContentType, string> = {
  story_segment: 'review_type_story_segment',
  related_story: 'review_type_related_story',
  kg_relation: 'review_type_kg_relation',
  source_evidence: 'review_type_source_evidence',
  disagreement_note: 'review_type_disagreement_note',
};

const STATUS_KEYS: Record<ReviewStatus, string> = {
  pending: 'review_status_pending',
  approved: 'review_status_approved',
  rejected: 'review_status_rejected',
  changes_requested: 'review_status_changes_requested',
};

const PRIORITY_KEYS: Record<ReviewPriority, string> = {
  high: 'review_priority_high',
  medium: 'review_priority_medium',
  low: 'review_priority_low',
};

const STATUS_COLORS: Record<ReviewStatus, string> = {
  pending: 'bg-amber-100 text-amber-700 border-amber-200',
  approved: 'bg-green-100 text-green-700 border-green-200',
  rejected: 'bg-red-100 text-red-700 border-red-200',
  changes_requested: 'bg-blue-100 text-blue-700 border-blue-200',
};

const PRIORITY_COLORS: Record<ReviewPriority, string> = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  low: 'bg-gray-100 text-gray-600 border-gray-200',
};

// =============================================================================
// Sub-components
// =============================================================================

function StatusBadge({ status, language }: { status: ReviewStatus; language: 'ar' | 'en' }) {
  const Icon = status === 'approved'
    ? CheckCircle
    : status === 'rejected'
    ? XCircle
    : status === 'changes_requested'
    ? MessageSquare
    : Clock;

  return (
    <span className={clsx('inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border', STATUS_COLORS[status])}>
      <Icon className="w-3 h-3" />
      {t(STATUS_KEYS[status], language)}
    </span>
  );
}

function PriorityBadge({ priority, language }: { priority: ReviewPriority; language: 'ar' | 'en' }) {
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded border', PRIORITY_COLORS[priority])}>
      {t(PRIORITY_KEYS[priority], language)}
    </span>
  );
}

function ContentTypeBadge({ contentType, language }: { contentType: ReviewContentType; language: 'ar' | 'en' }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded border bg-indigo-50 text-indigo-700 border-indigo-200">
      {t(CONTENT_TYPE_KEYS[contentType], language)}
    </span>
  );
}

// =============================================================================
// Stats panel
// =============================================================================

function StatsPanel({
  stats,
  language,
}: {
  stats: ReviewStatsResponse;
  language: 'ar' | 'en';
}) {
  const cards = [
    { key: 'review_stats_total', value: stats.total, color: 'bg-gray-50 border-gray-200' },
    { key: 'review_stats_pending', value: stats.pending, color: 'bg-amber-50 border-amber-200' },
    { key: 'review_stats_approved', value: stats.approved, color: 'bg-green-50 border-green-200' },
    { key: 'review_stats_rejected', value: stats.rejected, color: 'bg-red-50 border-red-200' },
    { key: 'review_stats_high_priority', value: stats.high_priority, color: 'bg-red-50 border-red-200' },
    { key: 'review_stats_disagreement', value: stats.with_disagreement_notes, color: 'bg-orange-50 border-orange-200' },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((c) => (
        <div key={c.key} className={clsx('rounded-lg border p-3 text-center', c.color)}>
          <div className="text-2xl font-bold text-gray-800">{c.value}</div>
          <div className="text-xs text-gray-500 mt-1" dir={language === 'ar' ? 'rtl' : 'ltr'}>
            {t(c.key, language)}
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Decision form
// =============================================================================

function DecisionForm({
  task,
  language,
  onDecision,
}: {
  task: ReviewTask;
  language: 'ar' | 'en';
  onDecision: (taskId: string, status: 'approved' | 'rejected' | 'changes_requested', notes: string, reviewerId: string, reviewerName?: string) => Promise<void>;
}) {
  const isArabic = language === 'ar';
  const [decisionStatus, setDecisionStatus] = useState<'approved' | 'rejected' | 'changes_requested'>('approved');
  const [notes, setNotes] = useState('');
  const [reviewerId, setReviewerId] = useState('');
  const [reviewerName, setReviewerName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = notes.trim().length >= 10 && reviewerId.trim().length > 0 && !submitting;

  async function handleSubmit() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await onDecision(task.id, decisionStatus, notes.trim(), reviewerId.trim(), reviewerName.trim() || undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-3 p-4 bg-white border border-gray-200 rounded-xl">
      {/* Scholarly review notice */}
      <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800 font-medium" dir={isArabic ? 'rtl' : 'ltr'}>
          {t('review_not_approved_notice', language)}
        </p>
      </div>

      {/* Decision buttons */}
      <div className="flex gap-2 flex-wrap">
        {(['approved', 'rejected', 'changes_requested'] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setDecisionStatus(s)}
            className={clsx(
              'text-xs px-3 py-1.5 rounded-full border font-medium transition-all',
              decisionStatus === s
                ? STATUS_COLORS[s] + ' ring-2 ring-offset-1 ring-current'
                : 'bg-gray-100 text-gray-500 border-gray-200 hover:bg-gray-200'
            )}
          >
            {s === 'approved' ? t('review_decision_approve', language)
              : s === 'rejected' ? t('review_decision_reject', language)
              : t('review_decision_request_changes', language)}
          </button>
        ))}
      </div>

      {/* Reviewer ID */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
            {t('review_reviewer_id', language)} *
          </label>
          <input
            type="text"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            placeholder="reviewer-id"
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:ring-1 focus:ring-amber-400 focus:outline-none"
            dir="ltr"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
            {t('review_reviewer_name', language)}
          </label>
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            placeholder="Scholar Name"
            className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:ring-1 focus:ring-amber-400 focus:outline-none"
            dir={isArabic ? 'rtl' : 'ltr'}
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="text-xs font-medium text-gray-600 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
          {t('review_decision_notes', language)} * ({notes.trim().length}/10 min)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('review_decision_notes_placeholder', language)}
          rows={3}
          className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:ring-1 focus:ring-amber-400 focus:outline-none resize-none"
          dir={isArabic ? 'rtl' : 'ltr'}
        />
        {notes.trim().length > 0 && notes.trim().length < 10 && (
          <p className="text-xs text-red-600 mt-1" dir={isArabic ? 'rtl' : 'ltr'}>
            {t('review_decision_notes_required', language)}
          </p>
        )}
      </div>

      {/* Error */}
      {error && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}

      {/* Submit */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={clsx(
          'w-full py-2 px-4 rounded-lg text-sm font-medium transition-all',
          canSubmit
            ? decisionStatus === 'approved'
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : decisionStatus === 'rejected'
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        )}
        dir={isArabic ? 'rtl' : 'ltr'}
      >
        {submitting ? (
          <span className="flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            {t('review_submitting', language)}
          </span>
        ) : (
          t('review_submit_decision', language)
        )}
      </button>
    </div>
  );
}

// =============================================================================
// Task card
// =============================================================================

function ReviewTaskCard({
  task,
  isExpanded,
  onToggle,
  language,
  onDecision,
}: {
  task: ReviewTask;
  isExpanded: boolean;
  onToggle: () => void;
  language: 'ar' | 'en';
  onDecision: (taskId: string, status: 'approved' | 'rejected' | 'changes_requested', notes: string, reviewerId: string, reviewerName?: string) => Promise<void>;
}) {
  const isArabic = language === 'ar';
  const hasDisagreement = (task.disagreementNotes?.length ?? 0) > 0;

  return (
    <div
      className={clsx(
        'border rounded-xl overflow-hidden transition-all',
        isExpanded
          ? 'ring-2 ring-amber-400 border-amber-300 shadow-lg'
          : 'border-gray-200 hover:border-amber-200 hover:shadow-md',
        hasDisagreement && !isExpanded && 'border-orange-200 bg-orange-50/30',
      )}
    >
      {/* Card header */}
      <div className="p-4 cursor-pointer hover:bg-gray-50/50" onClick={onToggle}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0 space-y-1.5">
            {/* Badges row */}
            <div className="flex flex-wrap gap-1.5 items-center">
              <ContentTypeBadge contentType={task.contentType} language={language} />
              <StatusBadge status={task.status} language={language} />
              <PriorityBadge priority={task.priority} language={language} />
              {task.humanReviewRequired && (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                  <ShieldAlert className="w-3 h-3" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{t('review_human_review_required', language)}</span>
                </span>
              )}
              {hasDisagreement && (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 border border-orange-200">
                  <AlertCircle className="w-3 h-3" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{t('review_disagreement_notes', language)}</span>
                </span>
              )}
            </div>

            {/* Content ID + Quran refs */}
            <div className="flex flex-wrap items-center gap-3">
              <code className="text-xs font-mono text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
                {task.contentId}
              </code>
              {task.quranReferences.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  <BookOpen className="w-3 h-3 text-primary-600" />
                  {task.quranReferences.map((ref, i) => (
                    <span key={i} className="text-xs text-primary-700 font-medium">
                      {ref.surahNumber}:{ref.ayahStart}
                      {ref.ayahEnd && ref.ayahEnd !== ref.ayahStart ? `–${ref.ayahEnd}` : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Summary */}
            {task.summaryEnglish && (
              <p className="text-xs text-gray-500 truncate" dir="ltr">
                {task.summaryEnglish}
              </p>
            )}
          </div>

          {/* Expand toggle */}
          <div className="flex-shrink-0">
            {isExpanded
              ? <ChevronUp className="w-5 h-5 text-gray-400" />
              : <ChevronDown className="w-5 h-5 text-gray-400" />
            }
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gray-50/50 p-4 space-y-4">
          {/* Quran refs */}
          {task.quranReferences.length > 0 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-1">{t('review_quran_references', language)}:</div>
              <div className="flex flex-wrap gap-2">
                {task.quranReferences.map((ref, i) => (
                  <span key={i} className="text-sm font-mono text-primary-700 bg-primary-50 border border-primary-100 px-2 py-1 rounded">
                    {ref.surahNumber}:{ref.ayahStart}
                    {ref.ayahEnd && ref.ayahEnd !== ref.ayahStart ? `–${ref.ayahEnd}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source IDs */}
          {task.sourceIds.length > 0 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-1">{t('review_source_ids', language)}:</div>
              <div className="flex flex-wrap gap-1">
                {task.sourceIds.map((s) => (
                  <span key={s} className="text-xs font-mono bg-blue-50 text-blue-700 border border-blue-100 px-1.5 py-0.5 rounded">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {task.warnings.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-gray-500">{t('review_warnings', language)}:</div>
              {task.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded p-2">
                  <AlertCircle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Disagreement notes */}
          {hasDisagreement && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-orange-700 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {t('review_disagreement_notes', language)}:
              </div>
              {task.disagreementNotes!.map((note, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-orange-800 bg-orange-50 border border-orange-200 rounded p-2">
                  <Info className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span dir="ltr">{note}</span>
                </div>
              ))}
            </div>
          )}

          {/* Existing decision */}
          {task.decision && (
            <div className="p-3 bg-white border border-gray-200 rounded-lg space-y-2">
              <div className="flex items-center gap-2">
                <StatusBadge status={task.decision.status as ReviewStatus} language={language} />
                <span className="text-xs text-gray-500">{t('review_reviewer', language)}: {task.decision.reviewerId}</span>
                {task.decision.reviewerName && (
                  <span className="text-xs text-gray-500">({task.decision.reviewerName})</span>
                )}
              </div>
              <p className="text-xs text-gray-700 bg-gray-50 p-2 rounded" dir="ltr">{task.decision.notes}</p>
              <p className="text-xs text-gray-400">{t('review_reviewed_at', language)}: {task.decision.reviewedAt}</p>
            </div>
          )}

          {/* Decision form — only for pending/changes_requested */}
          {(task.status === 'pending' || task.status === 'changes_requested') && (
            <DecisionForm
              task={task}
              language={language}
              onDecision={onDecision}
            />
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main page
// =============================================================================

export function ReviewDashboardPage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<ReviewStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const LIMIT = 25;

  // Filters
  const [filterStatus, setFilterStatus] = useState<ReviewStatus | ''>('');
  const [filterType, setFilterType] = useState<ReviewContentType | ''>('');
  const [filterPriority, setFilterPriority] = useState<ReviewPriority | ''>('');
  const [filterDisagreement, setFilterDisagreement] = useState(false);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await reviewApi.listTasks({
        status: filterStatus || undefined,
        content_type: filterType || undefined,
        priority: filterPriority || undefined,
        has_disagreement: filterDisagreement ? true : undefined,
        limit: LIMIT,
        offset,
      });
      setTasks(resp.data.tasks);
      setTotal(resp.data.total);
    } catch {
      setError(t('review_load_error', language));
    } finally {
      setLoading(false);
    }
  }, [filterStatus, filterType, filterPriority, filterDisagreement, offset, language]);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const resp = await reviewApi.getStats();
      setStats(resp.data);
    } catch {
      // Stats are non-critical — fail silently
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTasks();
    loadStats();
  }, [loadTasks, loadStats]);

  async function handleDecision(
    taskId: string,
    status: 'approved' | 'rejected' | 'changes_requested',
    notes: string,
    reviewerId: string,
    reviewerName?: string,
  ) {
    await reviewApi.submitDecision(taskId, { status, notes, reviewerId, reviewerName });
    // Reload after decision
    await loadTasks();
    await loadStats();
    setExpandedId(null);
  }

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">

        {/* Page header */}
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div dir={isArabic ? 'rtl' : 'ltr'}>
            <h1 className="text-2xl font-bold text-gray-900">
              {t('review_dashboard_title', language)}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {t('review_dashboard_subtitle', language)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => { loadTasks(); loadStats(); }}
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800 bg-white border border-gray-200 rounded-lg px-3 py-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Safety notice */}
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div dir={isArabic ? 'rtl' : 'ltr'}>
            <p className="text-sm font-semibold text-amber-800">
              {t('review_not_approved_notice', language)}
            </p>
          </div>
        </div>

        {/* Phase 6.5 — Overlay freshness indicator */}
        {(() => {
          const overlayMeta = getOverlayMeta();
          const approvedCount = stats?.approved ?? 0;
          const generatedAt = overlayMeta.generatedAt;
          const isOverlayGenerated = !!generatedAt;
          const isAllPending = (stats?.approved ?? 0) === 0 && (stats?.rejected ?? 0) === 0;

          return (
            <div className={`flex items-start gap-3 p-3 rounded-lg border text-sm ${isAllPending ? 'bg-gray-50 border-gray-200' : 'bg-blue-50 border-blue-200'}`}>
              <Info className={`w-4 h-4 flex-shrink-0 mt-0.5 ${isAllPending ? 'text-gray-400' : 'text-blue-500'}`} />
              <div dir={isArabic ? 'rtl' : 'ltr'} className="flex-1">
                <span className={`font-medium ${isAllPending ? 'text-gray-600' : 'text-blue-700'}`}>
                  {t('review_overlay_freshness_label', language)}
                </span>{' '}
                <span className={isAllPending ? 'text-gray-500' : 'text-blue-600'}>
                  {isOverlayGenerated
                    ? new Date(generatedAt).toLocaleString(language === 'ar' ? 'ar-SA' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' })
                    : t('review_overlay_not_generated', language)}
                </span>
                {approvedCount > 0 && (
                  <span className="ml-3 text-green-700 font-medium">
                    {approvedCount} {language === 'ar' ? 'قرار معتمد مُنشر' : 'approved decision(s) reflected in public UI'}
                  </span>
                )}
                {isAllPending && isOverlayGenerated && (
                  <span className="ml-2 text-gray-400">
                    — {t('review_overlay_all_pending', language)}
                  </span>
                )}
                {!isAllPending && (
                  <div className="mt-1 text-xs text-blue-500">
                    {t('review_overlay_stale_warning', language)}
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {/* Stats */}
        {statsLoading ? (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading stats…
          </div>
        ) : stats ? (
          <StatsPanel stats={stats} language={language} />
        ) : null}

        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filters</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {/* Status filter */}
            <div>
              <label className="text-xs text-gray-500 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('review_filter_status', language)}
              </label>
              <select
                value={filterStatus}
                onChange={(e) => { setFilterStatus(e.target.value as ReviewStatus | ''); setOffset(0); }}
                className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
              >
                <option value="">{t('review_all_statuses', language)}</option>
                <option value="pending">{t('review_status_pending', language)}</option>
                <option value="approved">{t('review_status_approved', language)}</option>
                <option value="rejected">{t('review_status_rejected', language)}</option>
                <option value="changes_requested">{t('review_status_changes_requested', language)}</option>
              </select>
            </div>

            {/* Content type filter */}
            <div>
              <label className="text-xs text-gray-500 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('review_filter_type', language)}
              </label>
              <select
                value={filterType}
                onChange={(e) => { setFilterType(e.target.value as ReviewContentType | ''); setOffset(0); }}
                className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
              >
                <option value="">{t('review_all_types', language)}</option>
                <option value="story_segment">{t('review_type_story_segment', language)}</option>
                <option value="related_story">{t('review_type_related_story', language)}</option>
                <option value="kg_relation">{t('review_type_kg_relation', language)}</option>
                <option value="source_evidence">{t('review_type_source_evidence', language)}</option>
                <option value="disagreement_note">{t('review_type_disagreement_note', language)}</option>
              </select>
            </div>

            {/* Priority filter */}
            <div>
              <label className="text-xs text-gray-500 block mb-1" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('review_filter_priority', language)}
              </label>
              <select
                value={filterPriority}
                onChange={(e) => { setFilterPriority(e.target.value as ReviewPriority | ''); setOffset(0); }}
                className="w-full text-xs border border-gray-300 rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
              >
                <option value="">{t('review_all_priorities', language)}</option>
                <option value="high">{t('review_priority_high', language)}</option>
                <option value="medium">{t('review_priority_medium', language)}</option>
                <option value="low">{t('review_priority_low', language)}</option>
              </select>
            </div>

            {/* Disagreement toggle */}
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filterDisagreement}
                  onChange={(e) => { setFilterDisagreement(e.target.checked); setOffset(0); }}
                  className="w-3.5 h-3.5 rounded text-amber-500"
                />
                <span className="text-xs text-gray-600" dir={isArabic ? 'rtl' : 'ltr'}>
                  {t('review_filter_disagreement', language)}
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Task list */}
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">
                {t('review_tasks', language)} ({total})
              </span>
            </div>
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-12 gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-amber-600" />
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-xl">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700" dir={isArabic ? 'rtl' : 'ltr'}>{error}</p>
            </div>
          )}

          {/* Tasks */}
          {!loading && !error && tasks.length === 0 && (
            <div className="text-center py-12 text-gray-500 bg-white border border-gray-200 rounded-xl">
              <p dir={isArabic ? 'rtl' : 'ltr'}>{t('review_no_tasks_found', language)}</p>
            </div>
          )}

          {!loading && !error && tasks.map((task) => (
            <ReviewTaskCard
              key={task.id}
              task={task}
              isExpanded={expandedId === task.id}
              onToggle={() => setExpandedId(expandedId === task.id ? null : task.id)}
              language={language}
              onDecision={handleDecision}
            />
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className="text-sm px-3 py-1.5 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
            >
              ← Prev
            </button>
            <span className="text-sm text-gray-600">
              {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setOffset(offset + LIMIT)}
              className="text-sm px-3 py-1.5 border border-gray-200 rounded disabled:opacity-40 hover:bg-gray-50"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReviewDashboardPage;
