/**
 * Phase G — Admin Feedback Dashboard
 *
 * Displays user-submitted feedback in a sortable, filterable list.
 * Admins can update status and add review notes inline.
 *
 * Route: /admin/feedback
 * Auth: requires VITE_ADMIN_API_KEY to be set (same as review dashboard).
 */
import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Loader2,
  MessageSquare,
  Filter,
  Save,
} from 'lucide-react';
import clsx from 'clsx';
import {
  feedbackApi,
  FeedbackItem,
  FeedbackStatus,
  FeedbackCategory,
  FeedbackStatsResponse,
} from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<FeedbackStatus, string> = {
  open: 'bg-amber-100 text-amber-700 border-amber-200',
  in_review: 'bg-blue-100 text-blue-700 border-blue-200',
  resolved: 'bg-green-100 text-green-700 border-green-200',
  dismissed: 'bg-zinc-100 text-zinc-500 border-zinc-200',
};

const PRIORITY_COLORS: Record<number, string> = {
  1: 'text-red-600 font-bold',
  2: 'text-orange-500 font-semibold',
  3: 'text-amber-500',
  5: 'text-zinc-400',
};

const STATUS_OPTIONS: FeedbackStatus[] = ['open', 'in_review', 'resolved', 'dismissed'];

const CATEGORY_OPTIONS: (FeedbackCategory | '')[] = [
  '',
  'translation_issue',
  'source_missing',
  'tafsir_error',
  'quran_ref_error',
  'ui_feedback',
  'inappropriate',
  'other',
];

function StatusIcon({ status }: { status: FeedbackStatus }) {
  if (status === 'resolved') return <CheckCircle2 className="h-4 w-4" />;
  if (status === 'dismissed') return <XCircle className="h-4 w-4" />;
  if (status === 'in_review') return <Clock className="h-4 w-4" />;
  return <AlertTriangle className="h-4 w-4" />;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatsBar({ stats }: { stats: FeedbackStatsResponse }) {
  const { language } = useLanguageStore();
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      <StatCard
        label={t('admin_feedback_total', language)}
        value={stats.total}
        icon={<BarChart3 className="h-5 w-5 text-zinc-400" />}
      />
      <StatCard
        label={t('admin_feedback_open_high', language)}
        value={stats.open_high_priority}
        icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
        highlight={stats.open_high_priority > 0}
      />
      <StatCard
        label={t('admin_feedback_status_open', language)}
        value={stats.by_status['open'] ?? 0}
        icon={<MessageSquare className="h-5 w-5 text-amber-400" />}
      />
      <StatCard
        label={t('admin_feedback_status_resolved', language)}
        value={(stats.by_status['resolved'] ?? 0) + (stats.by_status['dismissed'] ?? 0)}
        icon={<CheckCircle2 className="h-5 w-5 text-green-400" />}
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  highlight,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={clsx(
        'rounded-xl border p-4 bg-white',
        highlight ? 'border-red-200 bg-red-50' : 'border-zinc-200'
      )}
    >
      <div className="flex items-center justify-between mb-1">
        {icon}
        <span className={clsx('text-2xl font-bold', highlight ? 'text-red-600' : 'text-zinc-800')}>
          {value}
        </span>
      </div>
      <p className="text-xs text-zinc-500">{label}</p>
    </div>
  );
}

function FeedbackRow({ item, onUpdated }: { item: FeedbackItem; onUpdated: () => void }) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState<FeedbackStatus>(item.status);
  const [notes, setNotes] = useState(item.admin_notes ?? '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await feedbackApi.adminUpdate(item.id, { status, admin_notes: notes });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      onUpdated();
    } finally {
      setSaving(false);
    }
  }

  const priorityColor = PRIORITY_COLORS[item.priority] ?? PRIORITY_COLORS[5];
  const label = isRtl ? item.category_label_ar : item.category_label_en;
  const createdDate = new Date(item.created_at).toLocaleDateString(
    language === 'ar' ? 'ar-SA' : 'en-GB'
  );

  return (
    <div className="border border-zinc-200 rounded-xl overflow-hidden bg-white">
      {/* Summary row */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-zinc-50 transition-colors"
      >
        <span className={clsx('text-xs mt-0.5 font-mono', priorityColor)}>P{item.priority}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span
              className={clsx(
                'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium',
                STATUS_COLORS[item.status]
              )}
            >
              <StatusIcon status={item.status} />
              {t(`admin_feedback_status_${item.status}`, language)}
            </span>
            <span className="text-xs text-zinc-500 bg-zinc-100 rounded-full px-2 py-0.5">
              {label}
            </span>
            {item.entity_type && (
              <span className="text-xs text-zinc-400">
                {item.entity_type}
                {item.entity_id ? ` / ${item.entity_id}` : ''}
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-700 truncate">{item.message}</p>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2 text-xs text-zinc-400">
          <span>{createdDate}</span>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div dir={isRtl ? 'rtl' : 'ltr'} className="border-t border-zinc-100 p-4 space-y-4 bg-zinc-50">
          <div>
            <p className="text-xs text-zinc-500 mb-1">
              {item.page_url && (
                <span className="font-mono bg-zinc-100 px-1 rounded">{item.page_url}</span>
              )}
            </p>
            <p className="text-sm text-zinc-700 whitespace-pre-wrap">{item.message}</p>
          </div>

          {/* Status selector */}
          <div className="flex flex-wrap gap-3 items-start">
            <div>
              <label className="block text-xs font-medium text-zinc-500 mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as FeedbackStatus)}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {t(`admin_feedback_status_${s}`, language)}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 min-w-40">
              <label className="block text-xs font-medium text-zinc-500 mb-1">
                {t('admin_feedback_notes_label', language)}
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="Add review notes…"
              />
            </div>

            <button
              onClick={save}
              disabled={saving}
              className={clsx(
                'self-end flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
                saved
                  ? 'bg-green-600 text-white'
                  : 'bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-60'
              )}
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : saved ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {saved ? 'Saved' : t('admin_feedback_save', language)}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function AdminFeedbackPage() {
  const { language } = useLanguageStore();

  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [stats, setStats] = useState<FeedbackStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<FeedbackStatus | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<FeedbackCategory | ''>('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const PAGE_SIZE = 20;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, statsRes] = await Promise.all([
        feedbackApi.adminList({
          ...(statusFilter ? { status: statusFilter } : {}),
          ...(categoryFilter ? { category: categoryFilter } : {}),
          page,
          page_size: PAGE_SIZE,
        }),
        feedbackApi.adminStats(),
      ]);
      setItems(listRes.data.items);
      setTotal(listRes.data.total);
      setStats(statsRes.data);
    } catch {
      setError('Failed to load feedback. Check that VITE_ADMIN_API_KEY is set.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, categoryFilter, page]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className={clsx('text-2xl font-bold text-zinc-900', language === 'ar' && 'font-arabic')}>
            {t('admin_feedback_title', language)}
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            {total} {total === 1 ? 'report' : 'reports'} total
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-600 hover:bg-zinc-50 transition-colors"
        >
          <RefreshCw className={clsx('h-4 w-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && <StatsBar stats={stats} />}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-zinc-400" />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value as FeedbackStatus | ''); setPage(1); }}
            className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">{t('admin_feedback_filter_all', language)} (status)</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{t(`admin_feedback_status_${s}`, language)}</option>
            ))}
          </select>
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => { setCategoryFilter(e.target.value as FeedbackCategory | ''); setPage(1); }}
          className="rounded-lg border border-zinc-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <option value="">{t('admin_feedback_filter_all', language)} (category)</option>
          {CATEGORY_OPTIONS.filter(Boolean).map((c) => (
            <option key={c} value={c}>{t(`feedback_cat_${c}`, language)}</option>
          ))}
        </select>
      </div>

      {/* Content */}
      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && !error && (
        <div className="flex items-center justify-center py-16 text-zinc-400">
          <Loader2 className="h-6 w-6 animate-spin me-2" />
          Loading…
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="text-center py-16 text-zinc-400">
          <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-40" />
          {t('admin_feedback_no_items', language)}
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <FeedbackRow key={item.id} item={item} onUpdated={load} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-zinc-200 px-4 py-2 text-sm disabled:opacity-40 hover:bg-zinc-50"
          >
            Previous
          </button>
          <span className="text-sm text-zinc-500">
            Page {page} of {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button
            disabled={page >= Math.ceil(total / PAGE_SIZE)}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-zinc-200 px-4 py-2 text-sm disabled:opacity-40 hover:bg-zinc-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
