/**
 * Prophets Atlas — index page.
 *
 * Phase X. Surfaces the canonical 25 prophets in a search/filterable grid.
 * Backed by GET /api/v1/quran/prophets.
 */

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, AlertCircle, BookOpen, Users, Star, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { Skeleton } from '../components/ui/Skeleton';
import {
  prophetsApi,
  type ProphetListResponse,
  type ProphetMissingCoverageEntry,
  type ProphetSummary,
} from '../lib/api';

type SortKey = 'mushaf' | 'mentions' | 'surahs';

// Proportional bar: shows relative mention weight vs list max
function MentionBar({ value, max, color = 'emerald' }: { value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden mt-1.5">
      <div
        className={`h-full rounded-full bg-${color}-400 transition-all`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function ProphetCardSkeleton() {
  return (
    <div className="p-4 bg-white border border-gray-200 rounded-xl animate-pulse">
      <div className="flex items-baseline justify-between mb-1">
        <Skeleton variant="text" width="55%" height={20} />
        <Skeleton variant="text" width="20%" height={12} />
      </div>
      <Skeleton variant="text" width="40%" height={14} className="mb-3" />
      <div className="grid grid-cols-3 gap-1">
        {[0, 1, 2].map((i) => (
          <div key={i} className="text-center">
            <Skeleton variant="text" width="50%" height={18} className="mx-auto mb-1" />
            <Skeleton variant="text" width="70%" height={10} className="mx-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <Skeleton variant="text" width="40%" height={32} className="mb-2" />
        <Skeleton variant="text" width="70%" height={16} />
      </div>
      <div className="mb-4 flex gap-3">
        <Skeleton variant="rounded" width="100%" height={40} className="flex-1" />
        <Skeleton variant="rounded" width={120} height={40} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" aria-busy="true">
        {Array.from({ length: 12 }).map((_, i) => (
          <ProphetCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

const PAGE_TYPE_META: Record<string, { color: string; label: { ar: string; en: string } }> = {
  full_story:             { color: 'emerald', label: { ar: 'قصة كاملة', en: 'Full story' } },
  compact_profile:        { color: 'blue',    label: { ar: 'ملف موجز', en: 'Profile' } },
  mission_summary:        { color: 'purple',  label: { ar: 'رسالة', en: 'Mission' } },
  limited_quran_mentions: { color: 'amber',   label: { ar: 'ذكر محدود', en: 'Limited' } },
  contextual_mentions:    { color: 'gray',    label: { ar: 'سياقي', en: 'Contextual' } },
};

export function ProphetsPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const dir = isAr ? 'rtl' : 'ltr';

  const [data, setData] = useState<ProphetListResponse | null>(null);
  const [coverageById, setCoverageById] = useState<Record<string, ProphetMissingCoverageEntry>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [filterHasStory, setFilterHasStory] = useState(false);
  const [filterFrequent, setFilterFrequent] = useState(false);
  const [sort, setSort] = useState<SortKey>('mushaf');

  useEffect(() => {
    let stale = false;
    setLoading(true);
    prophetsApi
      .list()
      .then((r) => !stale && setData(r))
      .catch((e) => !stale && setError(e?.message || 'Failed to load Prophets Atlas'))
      .finally(() => !stale && setLoading(false));
    prophetsApi
      .missingCoverage()
      .then((r) => {
        if (stale) return;
        const idx: Record<string, ProphetMissingCoverageEntry> = {};
        for (const c of r.coverage) idx[c.prophetId] = c;
        setCoverageById(idx);
      })
      .catch(() => {/* coverage is optional */});
    return () => { stale = true; };
  }, []);

  const maxMentions = useMemo(() =>
    data ? Math.max(...data.prophets.map((p) => p.explicitMentionCount), 1) : 1,
  [data]);

  const maxSurahs = useMemo(() =>
    data ? Math.max(...data.prophets.map((p) => p.surahCount), 1) : 1,
  [data]);

  const visible: ProphetSummary[] = useMemo(() => {
    if (!data) return [];
    let list = data.prophets.slice();
    if (filterHasStory) list = list.filter((p) => p.storyIdCount > 0);
    if (filterFrequent) list = list.filter((p) => p.explicitMentionCount >= 20);
    if (query) {
      const q = query.toLowerCase();
      list = list.filter((p) =>
        p.nameArabic.includes(query) ||
        p.nameEnglish.toLowerCase().includes(q) ||
        p.transliteration.toLowerCase().includes(q) ||
        p.prophetId.toLowerCase().includes(q),
      );
    }
    if (sort === 'mentions') list.sort((a, b) => b.explicitMentionCount - a.explicitMentionCount);
    else if (sort === 'surahs') list.sort((a, b) => b.surahCount - a.surahCount);
    return list;
  }, [data, query, filterHasStory, filterFrequent, sort]);

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12" dir={dir}>
        <div className="p-4 border border-red-200 bg-red-50 text-red-800 rounded-xl flex items-start gap-2">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8" dir={dir}>
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-emerald-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className={clsx('text-2xl font-bold text-gray-900', isAr && 'font-arabic')}>
              {isAr ? 'أطلس الأنبياء في القرآن' : 'Prophets Atlas'}
            </h1>
            <p className={clsx('text-sm text-gray-500', isAr && 'font-arabic')}>
              {isAr
                ? `${data?.prophets.length ?? 25} نبياً · موثق من القرآن الكريم`
                : `${data?.prophets.length ?? 25} prophets · verified from the Quran`}
            </p>
          </div>
        </div>
        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <p className={isAr ? 'font-arabic' : ''}>
            {isAr
              ? 'هذه القائمة مرجعية وقيد المراجعة العلمية؛ الترتيب القصصي قراءة إرشادية وليس تأريخاً قطعياً.'
              : 'Navigation reference, under scholarly review. Story-world order is guided reading, not definitive chronology.'}
          </p>
        </div>
      </header>

      {/* Summary stats */}
      {data && (
        <div className="grid grid-cols-3 sm:grid-cols-3 gap-3 mb-6">
          {[
            { icon: BookOpen, label: isAr ? 'أنبياء' : 'Prophets', value: data.prophets.length, color: 'emerald' },
            { icon: Star, label: isAr ? 'قصة منشورة' : 'Story pages', value: data.prophets.filter(p => p.storyIdCount > 0).length, color: 'blue' },
            { icon: Users, label: isAr ? 'مذكور ≥20' : 'Mentioned ≥20', value: data.prophets.filter(p => p.explicitMentionCount >= 20).length, color: 'purple' },
          ].map(({ icon: Icon, label, value, color }) => (
            <div key={label} className={`p-3 bg-${color}-50 border border-${color}-200 rounded-xl text-center`}>
              <Icon className={`w-4 h-4 text-${color}-600 mx-auto mb-1`} />
              <div className={`text-xl font-bold text-${color}-700`}>{value}</div>
              <div className={clsx('text-xs text-gray-600', isAr && 'font-arabic')}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className="mb-5 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className={`absolute top-3 ${isAr ? 'right-3' : 'left-3'} w-4 h-4 text-gray-400`} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={isAr ? 'ابحث بالاسم...' : 'Search by name...'}
            className={clsx(
              'w-full py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm',
              isAr ? 'pr-9 pl-3 text-right' : 'pl-9 pr-3',
            )}
            dir={dir}
          />
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
          <input type="checkbox" checked={filterHasStory} onChange={(e) => setFilterHasStory(e.target.checked)} className="rounded" />
          <span className={isAr ? 'font-arabic' : ''}>{isAr ? 'له قصة' : 'Has story'}</span>
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
          <input type="checkbox" checked={filterFrequent} onChange={(e) => setFilterFrequent(e.target.checked)} className="rounded" />
          <span className={isAr ? 'font-arabic' : ''}>{isAr ? 'مذكور ≥20' : 'Frequent (≥20)'}</span>
        </label>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="mushaf">{isAr ? 'ترتيب مرجعي' : 'Reference order'}</option>
          <option value="mentions">{isAr ? 'الأكثر ذكراً' : 'Most mentioned'}</option>
          <option value="surahs">{isAr ? 'الأكثر سوراً' : 'Most surahs'}</option>
        </select>
      </div>

      {/* Grid */}
      {visible.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Search className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className={clsx('text-base font-medium text-gray-500', isAr && 'font-arabic')}>
            {isAr ? 'لا توجد نتائج تطابق البحث' : 'No prophets match the filters'}
          </p>
          <p className="text-sm mt-1">
            {isAr ? 'جرّب تعديل مصطلح البحث أو تصفية المرشحات' : 'Try adjusting the search or filters'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {visible.map((p) => {
            const coverage = coverageById[p.prophetId];
            const ptMeta = coverage?.pageType ? PAGE_TYPE_META[coverage.pageType] : null;
            return (
              <Link
                key={p.prophetId}
                to={`/prophets/${p.prophetId}`}
                className="group p-4 bg-white border border-gray-200 rounded-xl hover:border-emerald-400 hover:shadow-md transition-all"
              >
                {/* Name row */}
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className={clsx('text-base font-bold text-gray-900 group-hover:text-emerald-700 leading-tight', isAr && 'font-arabic')}>
                    {isAr ? p.nameArabic : p.nameEnglish}
                  </h3>
                  <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-emerald-500 flex-shrink-0 mt-0.5 transition-colors" />
                </div>
                <p className={clsx('text-xs text-gray-500 mb-3', isAr && 'font-arabic')}>
                  {isAr ? p.nameEnglish : p.nameArabic}
                </p>

                {/* Stats with proportional bars */}
                <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
                  <div>
                    <div className="font-bold text-gray-800 text-sm">{p.explicitMentionCount}</div>
                    <div className="text-gray-500">{isAr ? 'ذكر' : 'mentions'}</div>
                    <MentionBar value={p.explicitMentionCount} max={maxMentions} color="emerald" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-800 text-sm">{p.surahCount}</div>
                    <div className="text-gray-500">{isAr ? 'سور' : 'surahs'}</div>
                    <MentionBar value={p.surahCount} max={maxSurahs} color="blue" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-800 text-sm">{p.storyIdCount}</div>
                    <div className="text-gray-500">{isAr ? 'قصص' : 'stories'}</div>
                    <MentionBar value={p.storyIdCount} max={5} color="purple" />
                  </div>
                </div>

                {/* Badges */}
                <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                  <span className={clsx(
                    'inline-block px-2 py-0.5 text-[10px] rounded-full border',
                    p.reviewStatus === 'verified'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200',
                  )}>
                    {p.reviewStatus}
                  </span>
                  {ptMeta && (
                    <span className={`inline-block px-2 py-0.5 text-[10px] rounded-full border bg-${ptMeta.color}-50 text-${ptMeta.color}-700 border-${ptMeta.color}-200`}>
                      {isAr ? ptMeta.label.ar : ptMeta.label.en}
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
