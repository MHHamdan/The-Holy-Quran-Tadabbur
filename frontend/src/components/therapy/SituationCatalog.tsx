import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Heart, ExternalLink, ChevronDown, ChevronUp, Loader2, Stethoscope, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { therapyApi } from '../../lib/api';
import type { SituationSummary, SituationDetail } from '../../types/therapy';

interface SituationCatalogProps {
  language: 'ar' | 'en';
  /** Called when the user picks a situation — typically prefills the
   *  emotional-input panel with the situation's description. */
  onSelect?: (situation: SituationSummary) => void;
}

/**
 * SituationCatalog — browseable list of ~25 curated life situations.
 * Each card lazily fetches its detail (du'as + hadith citations) when
 * expanded; the list itself is small (~9KB) and 1h-cached.
 */
export function SituationCatalog({ language, onSelect }: SituationCatalogProps) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const isRtl = language === 'ar';

  const { data, isLoading } = useQuery({
    queryKey: ['therapy', 'situations'],
    queryFn: () => therapyApi.getSituations(),
    staleTime: 60 * 60 * 1000,
    gcTime: 4 * 60 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-6">
        <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (!data || data.situations.length === 0) return null;

  return (
    <section className="space-y-3" dir={isRtl ? 'rtl' : 'ltr'}>
      <header>
        <h2 className={clsx('text-sm font-semibold text-gray-700 flex items-center gap-2', isRtl && 'font-arabic flex-row-reverse')}>
          <Heart className="w-4 h-4 text-rose-500" />
          {isRtl ? 'المواقف الحياتية' : 'Life situations'}
        </h2>
        <p className={clsx('text-xs text-gray-500 mt-0.5', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? 'اختر موقفاً قريباً مما تشعر به، وستجد دعاءً نبوياً واستشهاداً من السنة.'
            : 'Pick the closest situation to find a prophetic du\'a and authentic hadith citations.'}
        </p>
      </header>

      <ul className="grid sm:grid-cols-2 gap-2">
        {data.situations.map(s => (
          <li key={s.key}>
            <SituationCard
              summary={s}
              language={language}
              isExpanded={expanded === s.key}
              onToggle={() => setExpanded(expanded === s.key ? null : s.key)}
              onSelect={onSelect}
            />
          </li>
        ))}
      </ul>

      <p className={clsx('text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2', isRtl && 'font-arabic text-right')}>
        {isRtl ? data.disclaimer_ar : data.disclaimer_en}
      </p>
    </section>
  );
}

interface SituationCardProps {
  summary: SituationSummary;
  language: 'ar' | 'en';
  isExpanded: boolean;
  onToggle: () => void;
  onSelect?: (situation: SituationSummary) => void;
}

function SituationCard({ summary, language, isExpanded, onToggle, onSelect }: SituationCardProps) {
  const isRtl = language === 'ar';

  const { data: detail, isLoading } = useQuery<SituationDetail>({
    queryKey: ['therapy', 'situation', summary.key],
    queryFn: () => therapyApi.getSituation(summary.key),
    enabled: isExpanded,
    staleTime: 60 * 60 * 1000,
    gcTime: 4 * 60 * 60 * 1000,
  });

  return (
    <article
      className={clsx(
        'border border-gray-200 rounded-xl bg-white text-sm transition-shadow',
        isExpanded && 'shadow-md',
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      <button
        type="button"
        onClick={onToggle}
        className={clsx(
          'w-full flex items-start justify-between gap-2 px-3 py-2.5 text-start',
          isRtl && 'flex-row-reverse',
        )}
        aria-expanded={isExpanded}
      >
        <div className="flex-1 min-w-0">
          <p className={clsx('font-medium text-gray-900', isRtl && 'font-arabic text-right')}>
            {isRtl ? summary.label_ar : summary.label_en}
          </p>
          <p className={clsx('text-xs text-gray-500 mt-0.5 line-clamp-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? summary.description_ar : summary.description_en}
          </p>
          {summary.refer_to_professional && (
            <span className={clsx('inline-flex items-center gap-1 mt-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-700', isRtl && 'font-arabic')}>
              <Stethoscope className="w-3 h-3" />
              {isRtl ? 'يُنصح بالاستعانة بمختص' : 'Consider a professional too'}
            </span>
          )}
        </div>
        {isExpanded
          ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
          : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-100 pt-3 space-y-3">
          {onSelect && (
            <button
              type="button"
              onClick={() => onSelect(summary)}
              className={clsx(
                'w-full text-xs font-medium py-2 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors',
                isRtl && 'font-arabic',
              )}
            >
              {isRtl ? 'استخدم هذا الموقف للبحث عن توجيه' : 'Use this situation to seek guidance'}
            </button>
          )}

          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-gray-500 py-2">
              <Loader2 className="w-3 h-3 animate-spin" />
              {isRtl ? 'جاري التحميل…' : 'Loading…'}
            </div>
          )}

          {detail?.duas && detail.duas.length > 0 && (
            <div>
              <p className={clsx('text-[11px] font-semibold text-gray-600 mb-1.5', isRtl && 'font-arabic text-right')}>
                {isRtl ? 'دعاء مأثور' : 'Prophetic du\'a'}
              </p>
              {detail.duas.map(d => (
                <blockquote
                  key={d.key}
                  className="rounded-lg bg-emerald-50 border-s-4 border-emerald-300 px-3 py-2 mb-2 text-sm leading-loose"
                >
                  <p className="font-arabic text-base text-gray-900" dir="rtl" lang="ar">
                    {d.arabic}
                  </p>
                  <p className="text-[11px] italic text-gray-500 mt-1" dir="ltr" lang="en">
                    {d.transliteration}
                  </p>
                  <p className="text-xs text-gray-700 mt-1" dir={isRtl ? 'rtl' : 'ltr'}>
                    {isRtl ? d.translation_ar : d.translation_en}
                  </p>
                </blockquote>
              ))}
            </div>
          )}

          {detail?.hadith_refs && detail.hadith_refs.length > 0 && (
            <div>
              <p className={clsx('text-[11px] font-semibold text-gray-600 mb-1.5 flex items-center gap-1', isRtl && 'flex-row-reverse font-arabic text-right')}>
                <BookOpen className="w-3 h-3" />
                {isRtl ? 'استشهاد من السنة' : 'Hadith citation'}
              </p>
              <ul className="space-y-1">
                {detail.hadith_refs.map(h => (
                  <li
                    key={`${h.collection}:${h.number}`}
                    className={clsx('flex items-start gap-2 text-xs', isRtl && 'flex-row-reverse text-right')}
                  >
                    <a
                      href={h.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-emerald-700 hover:underline whitespace-nowrap font-mono"
                    >
                      {h.collection}:{h.number}
                    </a>
                    <span className={clsx('text-gray-600', isRtl && 'font-arabic')}>
                      {isRtl ? h.note_ar : h.note_en}
                    </span>
                    <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
