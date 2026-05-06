/**
 * KG Similarity Section – Phase 5.5
 *
 * Displays Knowledge Graph–based verse relations with full safety display rules:
 * - All results shown as "needs_review" (matching KG edge status)
 * - Experimental toggle (default OFF)
 * - Human-review warning on each card
 * - Evidence cards per relation
 * - Bilingual (AR/EN) explanations
 * - RTL/LTR correct containers
 *
 * Safety rules enforced:
 * - Never shows "approved" unless backend explicitly returns it
 * - Hides experimental relations unless toggle is ON
 * - Does not present semantic similarity as tafsir
 * - Does not make religious conclusions from similarity
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Loader2,
  ShieldAlert,
  CheckCircle,
  Info,
  FlaskConical,
  GitBranch,
} from 'lucide-react';
import clsx from 'clsx';
import {
  quranApi,
  KGSimilarityApiResponse,
  KGRelatedAyah,
  KGEvidenceItem,
  KGRelationStatus,
  KGPathExplanation,
  KGPathNode,
} from '../../lib/api';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { getKGRelationStatus, type ReviewOverlayStatus } from '../../utils/reviewStatus';

// =============================================================================
// Relation type metadata
// =============================================================================

const RELATION_TYPE_META: Record<string, { arKey: string; enKey: string; color: string }> = {
  SAME_STORY_SEGMENT:       { arKey: 'similarity_rt_same_story_segment', enKey: 'similarity_rt_same_story_segment', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  SAME_STORY:               { arKey: 'similarity_rt_same_story',         enKey: 'similarity_rt_same_story',         color: 'bg-amber-100 text-amber-700 border-amber-200' },
  SAME_PROPHET_OR_PERSON:   { arKey: 'similarity_rt_same_prophet',       enKey: 'similarity_rt_same_prophet',       color: 'bg-blue-100 text-blue-700 border-blue-200' },
  SAME_THEME:               { arKey: 'similarity_rt_same_theme',         enKey: 'similarity_rt_same_theme',         color: 'bg-purple-100 text-purple-700 border-purple-200' },
  SAME_CONCEPT:             { arKey: 'similarity_rt_same_concept',       enKey: 'similarity_rt_same_concept',       color: 'bg-indigo-100 text-indigo-700 border-indigo-200' },
  SEMANTICALLY_SIMILAR:     { arKey: 'similarity_rt_semantic',           enKey: 'similarity_rt_semantic',           color: 'bg-gray-100 text-gray-600 border-gray-200' },
  SHARED_MORAL_LESSON:      { arKey: 'similarity_rt_shared_moral',       enKey: 'similarity_rt_shared_moral',       color: 'bg-teal-100 text-teal-700 border-teal-200' },
  PARALLEL_EVENT_PATTERN:   { arKey: 'similarity_rt_parallel_event',     enKey: 'similarity_rt_parallel_event',     color: 'bg-cyan-100 text-cyan-700 border-cyan-200' },
  TAFSIR_SUPPORTS_RELATION: { arKey: 'similarity_rt_tafsir_supported',   enKey: 'similarity_rt_tafsir_supported',   color: 'bg-green-100 text-green-700 border-green-200' },
};

// =============================================================================
// Sub-components
// =============================================================================

function ReviewStatusBadge({
  status,
  overlayStatus,
  language,
}: {
  status: KGRelationStatus;
  overlayStatus?: ReviewOverlayStatus;
  language: 'ar' | 'en';
}) {
  // Overlay approved takes priority if relation has been reviewed
  if (overlayStatus === 'approved' || status === 'approved') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">
        <CheckCircle className="w-3 h-3" />
        {t('similarity_approved', language)}
      </span>
    );
  }
  if (overlayStatus === 'partially_reviewed') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
        <Info className="w-3 h-3" />
        {language === 'ar' ? 'مراجعة جزئية' : 'Partially Reviewed'}
      </span>
    );
  }
  if (status === 'experimental') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
        <FlaskConical className="w-3 h-3" />
        {t('similarity_experimental', language)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
      <AlertCircle className="w-3 h-3" />
      {t('similarity_needs_review', language)}
    </span>
  );
}

function HumanReviewWarning({ language }: { language: 'ar' | 'en' }) {
  return (
    <div className="flex items-start gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
      <p className="text-xs text-amber-800" dir={language === 'ar' ? 'rtl' : 'ltr'}>
        {t('similarity_kg_human_review_detail', language)}
      </p>
    </div>
  );
}

function EvidenceCard({
  item,
  language,
}: {
  item: KGEvidenceItem;
  language: 'ar' | 'en';
}) {
  const isArabic = language === 'ar';
  const isExperimental = item.relationStatus === 'experimental';
  const evidenceOverlayStatus = getKGRelationStatus(item.storyId, item.segmentId);

  return (
    <div
      className={clsx(
        'rounded border p-2 text-xs space-y-1',
        isExperimental
          ? 'border-gray-200 bg-gray-50'
          : 'border-blue-100 bg-blue-50/50'
      )}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className="font-medium text-gray-700 truncate max-w-[60%]">
          {isArabic
            ? (item.sourceTitleArabic || item.sourceId)
            : (item.sourceTitleEnglish || item.sourceId)}
        </span>
        <ReviewStatusBadge status={item.relationStatus} overlayStatus={evidenceOverlayStatus} language={language} />
      </div>
      {item.storyId && (
        <div className="text-gray-500" dir={isArabic ? 'rtl' : 'ltr'}>
          <span className="font-medium">{t('similarity_evidence_story', language)}:</span>{' '}
          <span className="text-gray-700">{item.storyId}</span>
        </div>
      )}
      {item.conceptId && (
        <div className="text-gray-500" dir={isArabic ? 'rtl' : 'ltr'}>
          <span className="font-medium">{t('similarity_evidence_concept', language)}:</span>{' '}
          <span className="text-gray-700">{item.conceptId}</span>
        </div>
      )}
      {item.themeId && (
        <div className="text-gray-500" dir={isArabic ? 'rtl' : 'ltr'}>
          <span className="font-medium">{t('similarity_evidence_theme', language)}:</span>{' '}
          <span className="text-gray-700">{item.themeId}</span>
        </div>
      )}
      {item.tafsirReference && (
        <div className="text-gray-500" dir={isArabic ? 'rtl' : 'ltr'}>
          <span className="font-medium">{t('similarity_evidence_tafsir_ref', language)}:</span>{' '}
          <span className="text-gray-700">{item.tafsirReference}</span>
        </div>
      )}
    </div>
  );
}

function RelationTypeBadge({
  relationType,
  language,
}: {
  relationType: string;
  language: 'ar' | 'en';
}) {
  const meta = RELATION_TYPE_META[relationType];
  if (!meta) {
    return (
      <span className="text-xs px-2 py-0.5 rounded border bg-gray-100 text-gray-600 border-gray-200">
        {relationType}
      </span>
    );
  }
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded border', meta.color)}>
      {t(language === 'ar' ? meta.arKey : meta.enKey, language)}
    </span>
  );
}

function PathNodeLabel({
  node,
  language,
}: {
  node: KGPathNode;
  language: 'ar' | 'en';
}) {
  const isArabic = language === 'ar';
  if (node.type === 'ayah') {
    return (
      <span className="font-mono text-xs font-semibold text-primary-700">
        {node.surahNumber}:{node.ayahNumber}
      </span>
    );
  }
  const label = isArabic ? (node.labelArabic || node.labelEnglish || node.id) : (node.labelEnglish || node.id);
  return (
    <span className="text-xs text-gray-700 truncate max-w-[120px]" title={label}>
      {label}
    </span>
  );
}

function PathExplanationCard({
  path,
  language,
}: {
  path: KGPathExplanation;
  language: 'ar' | 'en';
}) {
  const isArabic = language === 'ar';
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-blue-100 bg-blue-50/40 p-3 space-y-2">
      {/* Header row */}
      <button
        type="button"
        className="flex items-center justify-between w-full gap-2 text-left"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span className="text-xs font-medium text-blue-800">
            {t('similarity_path_explanation', language)}
          </span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 border border-amber-200">
            {t('similarity_path_pending_review', language)}
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-blue-500 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-blue-500 flex-shrink-0" />
        )}
      </button>

      {/* Path chain (always visible) */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {path.nodes.map((node, i) => (
          <span key={node.id} className="flex items-center gap-1.5">
            <span
              className={clsx(
                'inline-flex items-center px-2 py-0.5 rounded text-xs border',
                node.type === 'ayah'
                  ? 'bg-primary-50 border-primary-200 text-primary-700'
                  : 'bg-white border-gray-200 text-gray-600'
              )}
            >
              <PathNodeLabel node={node} language={language} />
            </span>
            {i < path.nodes.length - 1 && path.edges[i] && (
              <span className="text-xs text-gray-400 font-mono">
                →
              </span>
            )}
          </span>
        ))}
      </div>

      {/* Bilingual explanation (always visible) */}
      <p className="text-xs text-blue-700 leading-relaxed" dir={isArabic ? 'rtl' : 'ltr'}>
        {isArabic ? path.explanationArabic : path.explanationEnglish}
      </p>

      {/* Expanded: edge details + warnings */}
      {expanded && (
        <div className="space-y-2 pt-1 border-t border-blue-100">
          {path.edges.length > 0 && (
            <div className="space-y-1">
              {path.edges.map((edge, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="font-mono text-gray-400 truncate max-w-[80px]">{edge.sourceNodeId.split(':').slice(-2).join(':')}</span>
                  <span className="text-gray-300">→</span>
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
                    {edge.edgeType.replace(/_/g, ' ')}
                  </span>
                  <span className="text-gray-300">→</span>
                  <span className="font-mono text-gray-400 truncate max-w-[80px]">{edge.targetNodeId.split(':').slice(-2).join(':')}</span>
                </div>
              ))}
            </div>
          )}
          {path.warnings.length > 0 && (
            <div className="space-y-1">
              {path.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded p-1.5">
                  <AlertCircle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{w}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function KGRelatedAyahCard({
  ayah,
  isExpanded,
  onToggle,
  language,
}: {
  ayah: KGRelatedAyah;
  isExpanded: boolean;
  onToggle: () => void;
  language: 'ar' | 'en';
}) {
  const isArabic = language === 'ar';
  const scorePercent = Math.round(ayah.score * 100);
  const hasNeedsReview = ayah.evidence.some(e => e.relationStatus === 'needs_review');
  const hasExperimental = ayah.evidence.some(e => e.relationStatus === 'experimental');
  const evidenceOnly = ayah.evidence.every(e => e.relationStatus === 'experimental');

  // Compute overlay status across all evidence items (compound: all must be approved)
  const evidenceOverlayStatuses = ayah.evidence.map(ev =>
    getKGRelationStatus(ev.storyId, ev.segmentId)
  );
  const allOverlayApproved = evidenceOverlayStatuses.length > 0 &&
    evidenceOverlayStatuses.every(s => s === 'approved');
  const anyOverlayApproved = evidenceOverlayStatuses.some(s => s === 'approved');
  const cardOverlayStatus: ReviewOverlayStatus = allOverlayApproved
    ? 'approved'
    : anyOverlayApproved
    ? 'partially_reviewed'
    : 'needs_review';
  const isCardApproved = cardOverlayStatus === 'approved';

  return (
    <div
      className={clsx(
        'border rounded-xl overflow-hidden transition-all',
        isExpanded
          ? 'ring-2 ring-amber-400 border-amber-300 shadow-lg'
          : 'border-gray-200 hover:border-amber-200 hover:shadow-md'
      )}
    >
      {/* Card header – click to expand */}
      <div className="p-4 cursor-pointer hover:bg-gray-50" onClick={onToggle}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {/* Reference, relation badges, review badge */}
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <Link
                to={`/quran/${ayah.surahNumber}#${ayah.ayahNumber}`}
                className="font-semibold text-primary-700 hover:underline"
                onClick={e => e.stopPropagation()}
              >
                {ayah.surahNumber}:{ayah.ayahNumber}
              </Link>
              {ayah.relationTypes.slice(0, 2).map(rt => (
                <RelationTypeBadge key={rt} relationType={rt} language={language} />
              ))}
              {/* Overlay-aware status badge */}
              {isCardApproved ? (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 border border-green-200">
                  <CheckCircle className="w-3 h-3" />
                  {t('similarity_approved', language)}
                </span>
              ) : cardOverlayStatus === 'partially_reviewed' ? (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
                  <Info className="w-3 h-3" />
                  {language === 'ar' ? 'مراجعة جزئية' : 'Partially Reviewed'}
                </span>
              ) : ayah.humanReviewRequired ? (
                <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                  <AlertCircle className="w-3 h-3" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{t('similarity_under_review', language)}</span>
                </span>
              ) : null}
            </div>

            {/* Explanation (bilingual) */}
            <p className="text-sm text-gray-600 leading-relaxed" dir={isArabic ? 'rtl' : 'ltr'}>
              {isArabic ? ayah.explanationArabic : ayah.explanationEnglish}
            </p>
          </div>

          {/* Score + expand toggle */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="text-center">
              <div className="text-xl font-bold text-amber-600">{scorePercent}%</div>
              <div className="text-xs text-gray-400">
                {t('similarity_relation_label', language)}
              </div>
            </div>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gray-50/50 p-4 space-y-4">
          {/* Human review warning */}
          {/* Human review warning — suppressed when overlay says approved */}
          {ayah.humanReviewRequired && !isCardApproved && <HumanReviewWarning language={language} />}

          {/* Needs-review detail — suppressed when overlay says approved */}
          {hasNeedsReview && !evidenceOnly && !isCardApproved && (
            <div className="flex items-start gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
              <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('similarity_kg_needs_review_detail', language)}
              </p>
            </div>
          )}

          {/* Experimental detail */}
          {hasExperimental && (
            <div className="flex items-start gap-2 p-2 bg-gray-50 border border-gray-200 rounded-lg">
              <FlaskConical className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-gray-600" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('similarity_kg_experimental_detail', language)}
              </p>
            </div>
          )}

          {/* All relation types */}
          {ayah.relationTypes.length > 0 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-2">
                {t('similarity_relation_type', language)}:
              </div>
              <div className="flex flex-wrap gap-2">
                {ayah.relationTypes.map(rt => (
                  <RelationTypeBadge key={rt} relationType={rt} language={language} />
                ))}
              </div>
            </div>
          )}

          {/* Evidence cards */}
          {ayah.evidence.length > 0 && (
            <div>
              <div className="text-xs font-medium text-gray-500 mb-2">
                {t('similarity_evidence', language)}:
              </div>
              <div className="space-y-2">
                {ayah.evidence.map((ev, i) => (
                  <EvidenceCard key={i} item={ev} language={language} />
                ))}
              </div>
            </div>
          )}

          {/* Path explanation (Phase 5.6) */}
          {ayah.pathExplanation && (
            <PathExplanationCard path={ayah.pathExplanation} language={language} />
          )}

          {/* Warnings */}
          {ayah.warnings.length > 0 && (
            <div className="space-y-1">
              {ayah.warnings.map((w, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded p-2"
                >
                  <AlertCircle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <span dir={isArabic ? 'rtl' : 'ltr'}>{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Mushaf link */}
          <Link
            to={`/quran/${ayah.surahNumber}#${ayah.ayahNumber}`}
            className="inline-flex items-center gap-2 text-primary-700 hover:text-primary-800 text-sm font-medium"
          >
            <BookOpen className="w-4 h-4" />
            {t('similarity_open_in_mushaf', language)}
          </Link>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main exported component
// =============================================================================

export function KGSimilaritySection({
  suraNo,
  ayaNo,
}: {
  suraNo: number;
  ayaNo: number;
}) {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [data, setData] = useState<KGSimilarityApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExperimental, setShowExperimental] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setExpandedIdx(null);
      try {
        const resp = await quranApi.getKGSimilarity(suraNo, ayaNo, {
          top_k: 20,
          min_score: 0.10,
          include_experimental: showExperimental,
        });
        if (!cancelled) setData(resp.data);
      } catch {
        if (!cancelled) {
          setError(t('similarity_kg_load_error', language));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [suraNo, ayaNo, showExperimental, language]);

  // Filter: hide experimental-only results unless toggle is ON
  const visibleAyahs = (data?.relatedAyahs ?? []).filter(a => {
    if (showExperimental) return true;
    return a.evidence.some(e => e.relationStatus !== 'experimental');
  });

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-900">
            {t('similarity_kg_title', language)}
          </h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
            {t('similarity_needs_review', language)}
          </span>
        </div>
        {!loading && data && (
          <span className="text-sm text-gray-500">
            {data.totalRelated} {t('similarity_kg_relation_count', language)}
          </span>
        )}
      </div>

      {/* Global needs-review notice */}
      <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div dir={isArabic ? 'rtl' : 'ltr'}>
          <p className="text-sm font-medium text-amber-800">
            {t('similarity_kg_pending_notice_title', language)}
          </p>
          <p className="text-xs text-amber-700 mt-1">
            {t('similarity_kg_pending_notice_body', language)}
          </p>
        </div>
      </div>

      {/* Experimental toggle */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
        <div dir={isArabic ? 'rtl' : 'ltr'} className="flex-1">
          <div className="text-sm font-medium text-gray-700">
            {t('similarity_show_experimental', language)}
          </div>
          {showExperimental && (
            <div className="flex items-center gap-1 mt-1">
              <FlaskConical className="w-3 h-3 text-gray-500" />
              <p className="text-xs text-gray-500">
                {t('similarity_experimental_warning', language)}
              </p>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => setShowExperimental(v => !v)}
          className={clsx(
            'relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1',
            showExperimental ? 'bg-amber-500' : 'bg-gray-300'
          )}
          role="switch"
          aria-checked={showExperimental}
          aria-label={t('similarity_show_experimental', language)}
        >
          <span
            className={clsx(
              'inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform',
              showExperimental ? 'translate-x-6' : 'translate-x-1'
            )}
          />
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-8 gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-amber-600" />
          <span className="text-gray-500 text-sm">
            {t('similarity_kg_searching', language)}
          </span>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700" dir={isArabic ? 'rtl' : 'ltr'}>
            {error}
          </p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && data && (
        <>
          {visibleAyahs.length > 0 ? (
            <div className="space-y-3">
              {visibleAyahs.map((ayah, idx) => (
                <KGRelatedAyahCard
                  key={`${ayah.surahNumber}:${ayah.ayahNumber}`}
                  ayah={ayah}
                  isExpanded={expandedIdx === idx}
                  onToggle={() =>
                    setExpandedIdx(expandedIdx === idx ? null : idx)
                  }
                  language={language}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-10 card">
              <p className="text-gray-500" dir={isArabic ? 'rtl' : 'ltr'}>
                {t('similarity_no_verified_ayahs', language)}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default KGSimilaritySection;
