/**
 * Reading Stats Dashboard — personal Quran reading analytics.
 *
 * Visualises data from localStorage (useReadingProgress) with no backend.
 * Shows: surah coverage grid, juz completion bars, streaks, category split.
 */

import { Link } from 'react-router-dom';
import { BarChart2, Flame, BookOpen, TrendingUp, Calendar, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { useReadingProgress } from '../hooks/useReadingProgress';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_NAMES } from '../data/surahNames';
import { JUZ_OVERVIEW } from '../data/juzOverview';

// Meccan / Medinan classification for all 114 surahs (1-indexed)
// Source: standard scholarly classification (majority of classical references)
const SURAH_TYPE: ('M' | 'K')[] = [
  'M','M','M','M','M','M','M','M','M','M',
  'M','M','M','M','M','M','M','M','K','M',
  'M','M','M','K','K','M','M','M','M','M',
  'M','M','M','M','M','M','M','M','M','M',
  'M','M','M','K','K','K','K','K','K','M',
  'M','M','M','M','K','K','K','M','K','M',
  'K','K','M','K','M','K','M','K','M','M',
  'M','M','M','M','K','M','M','M','M','M',
  'M','K','M','M','M','M','M','M','M','M',
  'M','M','M','M','M','M','M','M','M','M',
  'M','M','M','M','M','K','M','M','K','K',
  'M','M','M','M',
]; // index 0 = surah 1, length 114

// Approximate page counts (King Fahd Mushaf, 15-line) for coverage estimate
const SURAH_PAGES: readonly number[] = [
  1,49,20,29,24,13,20,20,21,21,
  12,18,20,27,8,12,12,8,18,8,
  8,8,14,9,22,11,93,26,7,8,
  10,29,17,31,12,9,8,14,12,8,
  11,6,7,23,24,26,14,18,29,9,
  7,10,7,8,22,8,7,8,7,8,
  5,11,7,5,8,5,6,7,7,7,
  11,5,4,7,5,6,4,8,6,5,
  4,6,5,4,5,5,5,4,3,4,
  5,3,5,4,3,4,3,3,3,3,
  3,3,3,3,3,3,3,2,3,3,
  2,2,2,2,
];

function formatNumber(n: number): string {
  return n.toLocaleString();
}

function StatCard({
  icon: Icon, value, label, sublabel, color,
}: {
  icon: React.ElementType;
  value: string | number;
  label: string;
  sublabel?: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-4 flex items-start gap-3">
      <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0', color)}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900 leading-none">{value}</p>
        <p className="text-sm text-gray-700 mt-0.5">{label}</p>
        {sublabel && <p className="text-xs text-gray-400 mt-0.5">{sublabel}</p>}
      </div>
    </div>
  );
}

export function ReadingStatsPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { progress, resetProgress } = useReadingProgress();
  const { visited, streak, longestStreak, lastRead } = progress;

  const totalVisited = visited.size;
  const pct = Math.round((totalVisited / 114) * 100);

  // Estimated pages
  const estPages = Array.from(visited).reduce((sum, s) => sum + (SURAH_PAGES[s - 1] ?? 0), 0);

  // Meccan / Medinan counts
  let meccanDone = 0;
  let medinanDone = 0;
  let meccanTotal = 0;
  let medinanTotal = 0;
  for (let i = 1; i <= 114; i++) {
    if (SURAH_TYPE[i - 1] === 'M') {
      meccanTotal++;
      if (visited.has(i)) meccanDone++;
    } else {
      medinanTotal++;
      if (visited.has(i)) medinanDone++;
    }
  }

  // Per-juz completion
  const juzStats = JUZ_OVERVIEW.map(j => {
    const total = j.surahRange.length;
    const done = j.surahRange.filter(s => visited.has(s)).length;
    return { juz: j.juz, total, done, pct: total > 0 ? Math.round((done / total) * 100) : 0 };
  });

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <BarChart2 className="w-7 h-7 text-violet-600" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'إحصائيات القراءة' : 'Reading Stats'}
          </h1>
          {lastRead && (
            <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
              {isRtl ? `آخر قراءة: ${lastRead.nameAr}` : `Last read: ${lastRead.nameEn}`}
            </p>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <StatCard
          icon={BookOpen}
          value={totalVisited}
          label={isRtl ? 'سورة مقروءة' : 'Surahs Read'}
          sublabel={`${pct}% ${isRtl ? 'من القرآن' : 'of Quran'}`}
          color="bg-emerald-500"
        />
        <StatCard
          icon={Flame}
          value={streak}
          label={isRtl ? 'أيام متتالية' : 'Day Streak'}
          sublabel={`${isRtl ? 'أعلى:' : 'Best:'} ${longestStreak}`}
          color="bg-orange-500"
        />
        <StatCard
          icon={TrendingUp}
          value={formatNumber(estPages)}
          label={isRtl ? 'صفحة تقريباً' : 'Est. Pages'}
          sublabel={isRtl ? 'مصحف المدينة' : 'King Fahd Mushaf'}
          color="bg-blue-500"
        />
        <StatCard
          icon={Calendar}
          value={longestStreak}
          label={isRtl ? 'أطول سلسلة' : 'Longest Streak'}
          sublabel={isRtl ? 'يوماً' : 'days'}
          color="bg-violet-500"
        />
      </div>

      {/* Overall khatmah progress */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-5">
        <div className={clsx('flex items-center justify-between mb-2', isRtl && 'flex-row-reverse')}>
          <h2 className={clsx('text-sm font-semibold text-gray-700', isRtl && 'font-arabic')}>
            {isRtl ? 'تقدم الختمة' : 'Khatmah Progress'}
          </h2>
          <span className="text-sm font-bold text-emerald-600">{pct}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className={clsx('text-xs text-gray-400 mt-1.5', isRtl && 'font-arabic text-right')}>
          {totalVisited}/114 {isRtl ? 'سورة' : 'surahs'} · {114 - totalVisited} {isRtl ? 'باقية' : 'remaining'}
        </p>
      </div>

      {/* 114-surah coverage grid */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-5">
        <h2 className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic')}>
          {isRtl ? 'خريطة السور' : 'Surah Coverage Map'}
        </h2>
        <div className="flex flex-wrap gap-1">
          {Array.from({ length: 114 }, (_, i) => i + 1).map(s => {
            const name = SURAH_NAMES[s - 1];
            const isVisited = visited.has(s);
            const isMeccan = SURAH_TYPE[s - 1] === 'M';
            return (
              <Link
                key={s}
                to={`/quran/${s}`}
                title={`${s}. ${isRtl ? name.ar : name.en}`}
                className={clsx(
                  'w-6 h-6 rounded text-[9px] font-bold flex items-center justify-center transition-opacity hover:opacity-80',
                  isVisited
                    ? isMeccan
                      ? 'bg-emerald-500 text-white'
                      : 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-400'
                )}
              >
                {s}
              </Link>
            );
          })}
        </div>
        {/* Legend */}
        <div className={clsx('flex items-center gap-4 mt-3', isRtl && 'flex-row-reverse')}>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
            <span className="text-[10px] text-gray-500">{isRtl ? 'مكية مقروءة' : 'Meccan (read)'}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-blue-500 inline-block" />
            <span className="text-[10px] text-gray-500">{isRtl ? 'مدنية مقروءة' : 'Medinan (read)'}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-gray-100 inline-block" />
            <span className="text-[10px] text-gray-500">{isRtl ? 'لم تُقرأ' : 'Unread'}</span>
          </span>
        </div>
      </div>

      {/* Meccan / Medinan split */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-white rounded-2xl border border-gray-100 p-4">
          <p className={clsx('text-xs text-gray-500 mb-1', isRtl && 'font-arabic')}>
            {isRtl ? 'السور المكية' : 'Meccan Surahs'}
          </p>
          <p className="text-xl font-bold text-emerald-600">
            {meccanDone}
            <span className="text-sm font-normal text-gray-400">/{meccanTotal}</span>
          </p>
          <div className="w-full h-1.5 bg-gray-100 rounded-full mt-2 overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${meccanTotal > 0 ? Math.round((meccanDone / meccanTotal) * 100) : 0}%` }}
            />
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-4">
          <p className={clsx('text-xs text-gray-500 mb-1', isRtl && 'font-arabic')}>
            {isRtl ? 'السور المدنية' : 'Medinan Surahs'}
          </p>
          <p className="text-xl font-bold text-blue-600">
            {medinanDone}
            <span className="text-sm font-normal text-gray-400">/{medinanTotal}</span>
          </p>
          <div className="w-full h-1.5 bg-gray-100 rounded-full mt-2 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${medinanTotal > 0 ? Math.round((medinanDone / medinanTotal) * 100) : 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Juz completion bars */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-5">
        <h2 className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic')}>
          {isRtl ? 'إتمام الأجزاء' : 'Juz Completion'}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
          {juzStats.map(j => (
            <div key={j.juz} className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 w-8 text-right flex-shrink-0">
                {isRtl ? `ج${j.juz}` : `J${j.juz}`}
              </span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={clsx(
                    'h-full rounded-full transition-all',
                    j.pct === 100 ? 'bg-emerald-500' : j.pct > 0 ? 'bg-violet-400' : 'bg-gray-200'
                  )}
                  style={{ width: `${j.pct}%` }}
                />
              </div>
              <span className="text-[10px] text-gray-400 w-8 flex-shrink-0">
                {j.done}/{j.total}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Empty state hint */}
      {totalVisited === 0 && (
        <div className="text-center py-6 bg-amber-50 rounded-2xl border border-amber-100">
          <BookOpen className="w-10 h-10 text-amber-400 mx-auto mb-2" />
          <p className={clsx('text-sm text-amber-700', isRtl && 'font-arabic')}>
            {isRtl
              ? 'ابدأ القراءة في المصحف لتظهر إحصائياتك هنا'
              : 'Start reading in the Mushaf to see your stats here'}
          </p>
          <Link to="/mushaf" className="mt-3 inline-block text-xs text-amber-600 underline">
            {isRtl ? 'افتح المصحف' : 'Open Mushaf'}
          </Link>
        </div>
      )}

      {/* Reset */}
      {totalVisited > 0 && (
        <div className="text-center mt-4">
          <button
            onClick={() => {
              if (window.confirm(isRtl ? 'إعادة تعيين كل بيانات القراءة؟' : 'Reset all reading data?')) {
                resetProgress();
              }
            }}
            className={clsx('flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-500 transition-colors mx-auto', isRtl && 'flex-row-reverse')}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {isRtl ? 'إعادة التعيين' : 'Reset Progress'}
          </button>
        </div>
      )}
    </div>
  );
}
