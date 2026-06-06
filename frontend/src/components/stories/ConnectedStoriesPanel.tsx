import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Network, Loader2, ArrowRight } from 'lucide-react';
import clsx from 'clsx';
import {
  storyAtlasRegistryApi,
  type StoryCrossRefEdge,
  type StoryCrossRefEvidence,
  type StoryCrossRefRelation,
} from '../../lib/api';

interface ConnectedStoriesPanelProps {
  storyId: string;
  language: 'ar' | 'en';
  /** Optional: get a story's display title from the registry adapter. */
  resolveTitle?: (storyId: string) => string | undefined;
  /** Where the "open story" link should point — defaults to /stories/{id}. */
  resolveDetailRoute?: (storyId: string) => string | undefined;
}

const RELATION_LABELS: Record<StoryCrossRefRelation, { ar: string; en: string }> = {
  same_prophet: { ar: 'نبيٌّ مشترك', en: 'Same prophet' },
  same_figure: { ar: 'شخصية مشتركة', en: 'Same figure' },
  same_surah: { ar: 'سورة مشتركة', en: 'Same surah' },
  same_theme: { ar: 'موضوع مشترك', en: 'Same theme' },
  same_topic: { ar: 'محور مشترك', en: 'Same topic' },
  overlapping_ayahs: { ar: 'تداخل في الآيات', en: 'Overlapping ayahs' },
};

const RELATION_COLOR: Record<StoryCrossRefRelation, string> = {
  same_prophet: 'bg-amber-50 text-amber-700 border-amber-200',
  same_figure: 'bg-rose-50 text-rose-700 border-rose-200',
  same_surah: 'bg-blue-50 text-blue-700 border-blue-200',
  same_theme: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  same_topic: 'bg-violet-50 text-violet-700 border-violet-200',
  overlapping_ayahs: 'bg-primary-50 text-primary-700 border-primary-200',
};

/**
 * Renders the cross-references graph for a single story.
 *
 * Each peer story shows the strongest evidence chips (shared prophet,
 * overlapping ayahs, shared surah, …) so the connection is visually
 * justified. All edges are needs_review until scholarly approval.
 */
export function ConnectedStoriesPanel({
  storyId,
  language,
  resolveTitle,
  resolveDetailRoute,
}: ConnectedStoriesPanelProps) {
  const isRtl = language === 'ar';
  const dir = isRtl ? 'rtl' : 'ltr';

  const { data, isLoading, error } = useQuery({
    queryKey: ['story-cross-refs', storyId],
    queryFn: () => storyAtlasRegistryApi.getCrossReferences(storyId).then(r => r.data),
    staleTime: 60 * 60 * 1000,
    gcTime: 4 * 60 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 py-2" dir={dir}>
        <Loader2 className="w-3 h-3 animate-spin" />
        {isRtl ? 'جاري تحميل القصص المرتبطة…' : 'Loading connected stories…'}
      </div>
    );
  }

  if (error || !data) {
    return (
      <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2" dir={dir}>
        {isRtl
          ? 'تعذّر تحميل القصص المرتبطة. شغّل scripts/build-quran-story-cross-references.ts.'
          : 'Could not load cross-references. Run scripts/build-quran-story-cross-references.ts.'}
      </p>
    );
  }

  if (data.total === 0) {
    return (
      <p className="text-xs text-gray-500" dir={dir}>
        {isRtl
          ? 'لا توجد قصص مرتبطة بأدلة واضحة بعد.'
          : 'No evidence-backed connected stories yet.'}
      </p>
    );
  }

  // The edges include the story on either side. Normalise so the
  // "other" id is always on the right.
  const peers = data.edges.map(e => normalisePeer(e, storyId)).slice(0, 8);

  return (
    <section className="space-y-2" aria-label={isRtl ? 'القصص المرتبطة' : 'Connected stories'} dir={dir}>
      <header className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2 text-sm font-medium text-gray-700', isRtl && 'flex-row-reverse font-arabic')}>
          <Network className="w-4 h-4 text-primary-600" />
          {isRtl ? 'قصص مرتبطة عبر القرآن' : 'Connected across the Quran'}
        </div>
        <span className={clsx('text-[10px] uppercase tracking-wide text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded', isRtl && 'font-arabic')}>
          {isRtl ? 'تحتاج مراجعة' : 'needs review'}
        </span>
      </header>

      <ul className="space-y-2">
        {peers.map(({ otherStoryId, edge }) => {
          const title = resolveTitle?.(otherStoryId) ?? otherStoryId;
          const detailRoute = resolveDetailRoute?.(otherStoryId) ?? `/stories/${otherStoryId}`;
          return (
            <li
              key={`${storyId}-${otherStoryId}`}
              className="border border-gray-200 rounded-lg p-2.5 bg-white"
              dir={dir}
            >
              <div className={clsx('flex items-center gap-2 mb-1.5', isRtl && 'flex-row-reverse')}>
                <Link
                  to={detailRoute}
                  className={clsx(
                    'flex items-center gap-1 text-sm font-medium text-primary-700 hover:underline',
                    isRtl && 'flex-row-reverse font-arabic',
                  )}
                >
                  {title}
                  <ArrowRight className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
                </Link>
                <span className="text-[10px] text-gray-400 font-mono tabular-nums">
                  {edge.score.toFixed(1)}
                </span>
              </div>
              <ul className={clsx('flex flex-wrap gap-1', isRtl && 'justify-end')}>
                {edge.evidence.map((ev, i) => (
                  <li key={`${ev.relation}-${i}`}>
                    <EvidenceChip evidence={ev} language={language} />
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function normalisePeer(edge: StoryCrossRefEdge, anchorId: string) {
  const otherStoryId = edge.sourceStoryId === anchorId ? edge.targetStoryId : edge.sourceStoryId;
  return { otherStoryId, edge };
}

function EvidenceChip({
  evidence,
  language,
}: {
  evidence: StoryCrossRefEvidence;
  language: 'ar' | 'en';
}) {
  const isRtl = language === 'ar';
  const labels = RELATION_LABELS[evidence.relation] ?? { ar: evidence.relation, en: evidence.relation };
  const color = RELATION_COLOR[evidence.relation] ?? 'bg-gray-50 text-gray-700 border-gray-200';
  // Show up to 3 sample values so chips stay short.
  const sample = evidence.values.slice(0, 3).join(isRtl ? '، ' : ', ');
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded border',
        color,
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
      title={evidence.values.join(', ')}
    >
      <span className={clsx('font-medium', isRtl && 'font-arabic')}>{isRtl ? labels.ar : labels.en}</span>
      {sample && <span className="opacity-75">{sample}</span>}
    </span>
  );
}
