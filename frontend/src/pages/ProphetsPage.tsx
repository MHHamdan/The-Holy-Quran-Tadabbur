/**
 * Prophets Atlas — index page.
 *
 * Phase X. Surfaces the canonical 25 prophets in a search/filterable grid.
 * Backed by GET /api/v1/quran/prophets.
 */

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Search, AlertCircle, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  prophetsApi,
  type ProphetListResponse,
  type ProphetMissingCoverageEntry,
  type ProphetSummary,
} from '../lib/api';

type SortKey = 'mushaf' | 'mentions' | 'surahs';

export function ProphetsPage() {
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

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
      .catch(() => {
        /* coverage is optional — UI falls back to plain badges */
      });
    return () => {
      stale = true;
    };
  }, []);

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
    // mushaf order: preserve API order (seed order ≈ canonical mushaf-era reading order)
    return list;
  }, [data, query, filterHasStory, filterFrequent, sort]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-emerald-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12" dir={dir}>
        <div className="p-4 border border-red-200 bg-red-50 text-red-800 rounded-md flex items-start gap-2">
          <AlertCircle className="w-5 h-5 mt-0.5" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8" dir={dir}>
      <header className="mb-8">
        <h1 className={clsx('text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3', language === 'ar' && 'font-arabic')}>
          <BookOpen className="w-8 h-8 text-emerald-600" />
          {language === 'ar' ? 'أطلس الأنبياء في القرآن' : 'Prophets Atlas'}
        </h1>
        <p className={clsx('text-gray-600 max-w-3xl', language === 'ar' && 'font-arabic')}>
          {language === 'ar'
            ? 'تعرف على الأنبياء الخمسة والعشرين الذين سُمّوا في القرآن وروابطهم وقصصهم وموضوعاتهم.'
            : 'Explore the 25 prophets named in the Quran — their ayahs, stories, related figures, and themes.'}
        </p>
        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-800 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <p>
            {language === 'ar'
              ? 'هذه القائمة مرجعية وقيد المراجعة العلمية؛ الترتيب القصصي قراءة إرشادية وليس تأريخاً قطعياً.'
              : 'This list is a navigation reference and remains under scholarly review. The story-world order is a guided reading, not a definitive chronology.'}
          </p>
        </div>
      </header>

      <div className="mb-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className={`absolute top-3 ${language === 'ar' ? 'right-3' : 'left-3'} w-4 h-4 text-gray-400`} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={language === 'ar' ? 'ابحث بالاسم...' : 'Search by name...'}
            className={clsx(
              'w-full py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500',
              language === 'ar' ? 'pr-9 pl-3 text-right' : 'pl-9 pr-3',
            )}
          />
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={filterHasStory} onChange={(e) => setFilterHasStory(e.target.checked)} />
          {language === 'ar' ? 'له قصة' : 'Has story page'}
        </label>
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={filterFrequent} onChange={(e) => setFilterFrequent(e.target.checked)} />
          {language === 'ar' ? 'مذكور كثيراً' : 'Frequent (≥20)'}
        </label>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="px-3 py-2 border border-gray-200 rounded-md text-sm"
        >
          <option value="mushaf">{language === 'ar' ? 'ترتيب مرجعي' : 'Reference order'}</option>
          <option value="mentions">{language === 'ar' ? 'الأكثر ذكراً' : 'Most mentioned'}</option>
          <option value="surahs">{language === 'ar' ? 'الأكثر سوراً' : 'Most surahs'}</option>
        </select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {visible.map((p) => (
          <Link
            key={p.prophetId}
            to={`/prophets/${p.prophetId}`}
            className="group p-4 bg-white border border-gray-200 rounded-md hover:border-emerald-400 hover:shadow-sm transition"
          >
            <div className="flex items-baseline justify-between gap-2">
              <h3 className={clsx('text-lg font-semibold text-gray-900 group-hover:text-emerald-700', language === 'ar' && 'font-arabic')}>
                {language === 'ar' ? p.nameArabic : p.nameEnglish}
              </h3>
              <span className="text-xs text-gray-400">{p.prophetId.replace(/^prophet_/, '')}</span>
            </div>
            <p className={clsx('text-xs text-gray-500 mt-1', language === 'ar' && 'font-arabic')}>
              {language === 'ar' ? p.nameEnglish : p.nameArabic}
            </p>
            <div className="mt-3 grid grid-cols-3 gap-1 text-center text-xs text-gray-600">
              <div>
                <div className="font-semibold text-gray-800">{p.explicitMentionCount}</div>
                <div>{language === 'ar' ? 'ذكر' : 'mentions'}</div>
              </div>
              <div>
                <div className="font-semibold text-gray-800">{p.surahCount}</div>
                <div>{language === 'ar' ? 'سور' : 'surahs'}</div>
              </div>
              <div>
                <div className="font-semibold text-gray-800">{p.storyIdCount}</div>
                <div>{language === 'ar' ? 'قصص' : 'stories'}</div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <span
                className={clsx(
                  'inline-block px-2 py-0.5 text-[10px] rounded-full border',
                  p.reviewStatus === 'verified'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200',
                )}
              >
                {p.reviewStatus}
              </span>
              {coverageById[p.prophetId]?.pageType && (
                <span
                  className={clsx(
                    'inline-block px-2 py-0.5 text-[10px] rounded-full border',
                    coverageById[p.prophetId].pageType === 'full_story'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : coverageById[p.prophetId].pageType === 'compact_profile'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : coverageById[p.prophetId].pageType === 'mission_summary'
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : 'bg-gray-50 text-gray-700 border-gray-200',
                  )}
                >
                  {coverageById[p.prophetId].pageType}
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>

      {visible.length === 0 && (
        <p className="text-center text-gray-500 mt-12">
          {language === 'ar' ? 'لا توجد نتائج' : 'No prophets match the filters.'}
        </p>
      )}
    </div>
  );
}
