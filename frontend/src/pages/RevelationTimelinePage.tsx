/**
 * Revelation Timeline — Quranic surahs in chronological order of revelation.
 *
 * Shows the Quran as it was revealed, not as it is compiled.
 * Helps understand historical context of each surah.
 * No editorial content beyond established seerah scholarship.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Search, ChevronRight, GitCompare, Map } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_NAMES } from '../data/surahNames';
import {
  REVELATION_TIMELINE, PERIOD_META,
  type RevPeriod, type RevelationEntry,
} from '../data/revelationTimeline';

const PERIODS_ORDER: RevPeriod[] = ['early_meccan', 'middle_meccan', 'late_meccan', 'early_medinan', 'late_medinan'];

const PERIOD_COLORS: Record<RevPeriod, { bg: string; border: string; badge: string; dot: string; bar: string }> = {
  early_meccan:  { bg: 'bg-amber-50',   border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700',   dot: 'bg-amber-400',   bar: 'bg-amber-300' },
  middle_meccan: { bg: 'bg-orange-50',  border: 'border-orange-200',  badge: 'bg-orange-100 text-orange-700', dot: 'bg-orange-400',  bar: 'bg-orange-300' },
  late_meccan:   { bg: 'bg-rose-50',    border: 'border-rose-200',    badge: 'bg-rose-100 text-rose-700',     dot: 'bg-rose-400',    bar: 'bg-rose-300' },
  early_medinan: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-400', bar: 'bg-emerald-300' },
  late_medinan:  { bg: 'bg-teal-50',    border: 'border-teal-200',    badge: 'bg-teal-100 text-teal-700',     dot: 'bg-teal-400',    bar: 'bg-teal-300' },
};

function TimelineCard({ entry, isRtl, expanded, onToggle }: {
  entry: RevelationEntry;
  isRtl: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const name = SURAH_NAMES[entry.surah - 1];
  const periodMeta = PERIOD_META[entry.period];
  const colors = PERIOD_COLORS[entry.period];

  return (
    <div
      className={clsx(
        'rounded-xl border transition-shadow cursor-pointer',
        expanded ? `${colors.bg} ${colors.border} shadow-sm` : 'bg-white border-gray-100 hover:shadow-sm'
      )}
      onClick={onToggle}
    >
      <div className={clsx('p-3 flex items-start gap-3', isRtl && 'flex-row-reverse')}>
        {/* Order badge */}
        <div className={clsx(
          'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold',
          colors.badge
        )}>
          {entry.revelationOrder}
        </div>

        <div className="flex-1 min-w-0">
          <div className={clsx('flex items-center gap-2 flex-wrap mb-0.5', isRtl && 'flex-row-reverse')}>
            <span className="font-arabic text-base text-gray-900 leading-none" dir="rtl">
              {name?.ar}
            </span>
            <span className="text-sm text-gray-600">{name?.en}</span>
            <span className="text-xs text-gray-400">#{entry.surah}</span>
          </div>
          <p className={clsx('text-xs text-gray-500', isRtl && 'font-arabic text-right')}>
            {isRtl ? entry.mainThemeAr : entry.mainThemeEn}
          </p>
        </div>

        <ChevronRight className={clsx(
          'w-4 h-4 flex-shrink-0 text-gray-300 transition-transform',
          expanded && 'rotate-90',
          isRtl && 'rotate-180'
        )} />
      </div>

      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-100 pt-3 mt-0.5">
          <div className={clsx('flex items-center gap-2 mb-2', isRtl && 'flex-row-reverse')}>
            <span className={clsx('text-[10px] px-2 py-0.5 rounded-full', colors.badge)}>
              {periodMeta.emoji} {isRtl ? periodMeta.labelAr : periodMeta.labelEn}
            </span>
            {entry.propheticYear && (
              <span className="text-[10px] text-gray-400">
                {isRtl ? `السنة النبوية ${entry.propheticYear}` : `Year ${entry.propheticYear} of prophethood`}
              </span>
            )}
            {entry.hijraYear && (
              <span className="text-[10px] text-gray-400">
                {isRtl ? `${entry.hijraYear} هـ` : `${entry.hijraYear} AH`}
              </span>
            )}
          </div>
          <p className={clsx('text-xs text-gray-600 mb-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? entry.contextAr : entry.contextEn}
          </p>
          <div className={clsx('flex items-center gap-2 flex-wrap', isRtl && 'flex-row-reverse')}>
            <Link
              to={`/quran/${entry.surah}`}
              onClick={e => e.stopPropagation()}
              className={clsx(
                'inline-flex items-center gap-1 text-[10px] text-violet-600 hover:underline',
                isRtl && 'flex-row-reverse'
              )}
            >
              {isRtl ? `افتح السورة ${name?.ar}` : `Open ${name?.en}`}
              <ChevronRight className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
            </Link>
            <Link
              to={`/surah-atlas/${entry.surah}`}
              onClick={e => e.stopPropagation()}
              className={clsx(
                'inline-flex items-center gap-1 text-[10px] text-gray-400 hover:text-teal-600 hover:underline',
                isRtl && 'flex-row-reverse'
              )}
            >
              <Map className="w-2.5 h-2.5" />
              {isRtl ? 'الأطلس' : 'Atlas'}
            </Link>
            <Link
              to={`/compare?a=${entry.surah}`}
              onClick={e => e.stopPropagation()}
              className={clsx(
                'inline-flex items-center gap-1 text-[10px] text-gray-400 hover:text-violet-600 hover:underline',
                isRtl && 'flex-row-reverse'
              )}
            >
              <GitCompare className="w-2.5 h-2.5" />
              {isRtl ? 'مقارنة' : 'Compare'}
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export function RevelationTimelinePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [search, setSearch] = useState('');
  const [periodFilter, setPeriodFilter] = useState<RevPeriod | 'all'>('all');
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null);
  const [showUthmanic, setShowUthmanic] = useState(false);

  const sorted = useMemo(() => {
    let result = [...REVELATION_TIMELINE];
    if (showUthmanic) {
      result.sort((a, b) => a.surah - b.surah);
    }
    if (periodFilter !== 'all') {
      result = result.filter(e => e.period === periodFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(e => {
        const name = SURAH_NAMES[e.surah - 1];
        return (
          name?.en.toLowerCase().includes(q) ||
          name?.ar.includes(q) ||
          e.contextEn.toLowerCase().includes(q) ||
          e.mainThemeEn.toLowerCase().includes(q) ||
          String(e.surah) === q ||
          String(e.revelationOrder) === q
        );
      });
    }
    return result;
  }, [search, periodFilter, showUthmanic]);

  const periodCounts = useMemo(() => {
    const counts: Record<RevPeriod, number> = {
      early_meccan: 0, middle_meccan: 0, late_meccan: 0, early_medinan: 0, late_medinan: 0,
    };
    for (const e of REVELATION_TIMELINE) counts[e.period]++;
    return counts;
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-3', isRtl && 'flex-row-reverse')}>
        <Clock className="w-7 h-7 text-violet-600" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'ترتيب النزول' : 'Revelation Timeline'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${REVELATION_TIMELINE.length} سورة بترتيب النزول التاريخي`
              : `${REVELATION_TIMELINE.length} surahs in chronological order of revelation`}
          </p>
        </div>
      </div>

      {/* Legend bar */}
      <div className="flex rounded-xl overflow-hidden mb-5 h-3">
        {PERIODS_ORDER.map(period => {
          const colors = PERIOD_COLORS[period];
          const count = periodCounts[period];
          const pct = Math.round((count / REVELATION_TIMELINE.length) * 100);
          return (
            <div
              key={period}
              title={PERIOD_META[period].labelEn}
              className={clsx('h-full', colors.bar)}
              style={{ width: `${pct}%` }}
            />
          );
        })}
      </div>

      {/* Period key */}
      <div className={clsx('flex flex-wrap gap-2 mb-4', isRtl && 'flex-row-reverse')}>
        {PERIODS_ORDER.map(period => {
          const meta = PERIOD_META[period];
          const colors = PERIOD_COLORS[period];
          return (
            <span key={period} className={clsx('flex items-center gap-1 text-[10px]', isRtl && 'flex-row-reverse')}>
              <span className={clsx('w-2.5 h-2.5 rounded-full', colors.dot)} />
              <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? meta.labelAr : meta.labelEn} ({periodCounts[period]})</span>
            </span>
          );
        })}
      </div>

      {/* Toggle: chronological vs Uthmanic */}
      <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
        <span className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
          {isRtl ? 'الترتيب:' : 'Order:'}
        </span>
        <button
          onClick={() => setShowUthmanic(false)}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            !showUthmanic ? 'bg-violet-600 text-white border-violet-600' : 'text-gray-500 border-gray-200'
          )}
        >
          {isRtl ? 'الترتيب الزمني' : 'Chronological'}
        </button>
        <button
          onClick={() => setShowUthmanic(true)}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            showUthmanic ? 'bg-violet-600 text-white border-violet-600' : 'text-gray-500 border-gray-200'
          )}
        >
          {isRtl ? 'الترتيب العثماني' : 'Uthmanic Order'}
        </button>
      </div>

      {/* Search */}
      <div className={clsx('flex items-center gap-2 bg-white rounded-xl border border-gray-200 px-3 py-2.5 mb-3', isRtl && 'flex-row-reverse')}>
        <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={isRtl ? 'ابحث بالاسم أو الموضوع…' : 'Search by name or theme…'}
          className={clsx('flex-1 text-sm bg-transparent outline-none text-gray-700', isRtl && 'font-arabic text-right')}
          dir={isRtl ? 'rtl' : 'ltr'}
        />
      </div>

      {/* Period filter */}
      <div className={clsx('flex flex-wrap gap-1.5 mb-5', isRtl && 'flex-row-reverse')}>
        <button
          onClick={() => setPeriodFilter('all')}
          className={clsx(
            'text-xs px-2.5 py-1 rounded-full border transition-colors',
            periodFilter === 'all' ? 'bg-gray-800 text-white border-gray-800' : 'text-gray-500 border-gray-200 hover:bg-gray-50'
          )}
        >
          {isRtl ? 'الكل' : 'All'}
        </button>
        {PERIODS_ORDER.map(period => {
          const meta = PERIOD_META[period];
          const colors = PERIOD_COLORS[period];
          return (
            <button
              key={period}
              onClick={() => setPeriodFilter(period === periodFilter ? 'all' : period)}
              className={clsx(
                'text-xs px-2.5 py-1 rounded-full border transition-colors',
                periodFilter === period ? `${colors.badge} border-transparent` : 'text-gray-500 border-gray-200 hover:bg-gray-50'
              )}
            >
              {meta.emoji} {isRtl ? meta.labelAr : meta.labelEn}
            </button>
          );
        })}
      </div>

      <p className={clsx('text-xs text-gray-400 mb-3', isRtl && 'font-arabic text-right')}>
        {sorted.length} {isRtl ? 'سورة' : sorted.length === 1 ? 'surah' : 'surahs'}
      </p>

      {/* Timeline list */}
      <div className="space-y-2">
        {sorted.map(entry => (
          <TimelineCard
            key={entry.revelationOrder}
            entry={entry}
            isRtl={isRtl}
            expanded={expandedOrder === entry.revelationOrder}
            onToggle={() => setExpandedOrder(
              expandedOrder === entry.revelationOrder ? null : entry.revelationOrder
            )}
          />
        ))}
        {sorted.length === 0 && (
          <p className={clsx('text-center text-gray-400 text-sm py-12', isRtl && 'font-arabic')}>
            {isRtl ? 'لا نتائج' : 'No results'}
          </p>
        )}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'مبني على رواية ابن عباس والطبعة المصرية الرسمية • بعض العلماء يختلفون في ترتيب سور معينة'
          : "Based on Ibn Abbas's narration & Egyptian Standard Edition · Scholars differ on some positions"}
      </p>
    </div>
  );
}
