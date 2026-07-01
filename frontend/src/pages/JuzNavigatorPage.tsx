/**
 * Juz Navigator — Visual overview of all 30 Juz
 *
 * Shows each juz with its surah range, main theme, key topics,
 * and reading progress overlay from the local reading progress store.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen, Search, CheckCircle2, Circle, ChevronRight, Trophy,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { useReadingProgress } from '../hooks/useReadingProgress';
import { JUZ_OVERVIEW, type JuzEntry } from '../data/juzOverview';
import { SURAH_NAMES } from '../data/surahNames';

function juzProgress(juz: JuzEntry, visited: Set<number>): { done: number; total: number } {
  const total = juz.surahRange.length;
  const done = juz.surahRange.filter(s => visited.has(s)).length;
  return { done, total };
}

function JuzCard({ juz, isRtl, visited }: { juz: JuzEntry; isRtl: boolean; visited: Set<number> }) {
  const [expanded, setExpanded] = useState(false);
  const { done, total } = juzProgress(juz, visited);
  const pct = Math.round((done / total) * 100);
  const complete = done === total;

  const startName = SURAH_NAMES[juz.startSurah - 1];
  const endName = SURAH_NAMES[juz.endSurah - 1];

  return (
    <div className={clsx(
      'bg-white rounded-2xl border overflow-hidden transition-shadow hover:shadow-md',
      complete ? 'border-emerald-200' : 'border-gray-100'
    )}>
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full text-start p-4"
      >
        <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
          {/* Juz number */}
          <div className={clsx(
            'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-sm',
            complete ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'
          )}>
            {juz.juz}
          </div>

          <div className="flex-1 min-w-0">
            {/* Surah range */}
            <p className={clsx('text-[11px] text-gray-400 mb-0.5', isRtl && 'font-arabic text-right')}>
              {isRtl
                ? `${startName.ar} ${juz.startSurah}:${juz.startAyah} — ${endName.ar} ${juz.endSurah}:${juz.endAyah}`
                : `${startName.en} ${juz.startSurah}:${juz.startAyah} — ${endName.en} ${juz.endSurah}:${juz.endAyah}`}
            </p>

            {/* Theme */}
            <h3 className={clsx('font-semibold text-gray-800 text-sm leading-snug', isRtl && 'font-arabic text-right')}>
              {isRtl ? juz.mainThemeAr : juz.mainThemeEn}
            </h3>

            {/* Opening word */}
            <p className={clsx('text-[11px] text-gray-400 mt-0.5', isRtl && 'font-arabic text-right')} dir="rtl">
              {juz.openingWordAr}
            </p>
          </div>

          {/* Progress */}
          <div className="flex-shrink-0 text-right flex flex-col items-end gap-1">
            {complete
              ? <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              : <Circle className="w-5 h-5 text-gray-200" />
            }
            <span className={clsx('text-[10px]', complete ? 'text-emerald-500' : 'text-gray-400')}>
              {done}/{total}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        {done > 0 && (
          <div className="mt-2 w-full h-1 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all', complete ? 'bg-emerald-400' : 'bg-violet-400')}
              style={{ width: `${pct}%` }}
            />
          </div>
        )}
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-gray-50 px-4 pb-4 pt-3 space-y-3">
          {/* Key topics */}
          <div>
            <p className={clsx('text-[11px] font-semibold text-gray-500 uppercase mb-2', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'الموضوعات الرئيسية' : 'Key Topics'}
            </p>
            <ul className="space-y-1">
              {(isRtl ? juz.keyTopicsAr : juz.keyTopicsEn).map((topic, i) => (
                <li key={i} className={clsx('text-xs text-gray-600 flex items-start gap-2', isRtl && 'flex-row-reverse')}>
                  <span className="text-violet-400 flex-shrink-0">•</span>
                  <span className={isRtl ? 'font-arabic text-right' : ''}>{topic}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Highlight verse */}
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            <BookOpen className="w-3.5 h-3.5 text-teal-500 flex-shrink-0" />
            <span className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
              {isRtl ? 'آية مميزة' : 'Featured verse'}:
            </span>
            <Link
              to={`/quran/${juz.highlightVerseRef.split(':')[0]}?aya=${juz.highlightVerseRef.split(':')[1]}`}
              className="text-xs text-teal-600 hover:text-teal-800 font-medium transition-colors"
              onClick={e => e.stopPropagation()}
            >
              {juz.highlightVerseRef}
            </Link>
          </div>

          {/* Surah links */}
          <div>
            <p className={clsx('text-[11px] font-semibold text-gray-500 uppercase mb-2', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'السور' : 'Surahs'}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {juz.surahRange.map(s => {
                const name = SURAH_NAMES[s - 1];
                const isRead = visited.has(s);
                return (
                  <Link
                    key={s}
                    to={`/quran/${s}`}
                    onClick={e => e.stopPropagation()}
                    className={clsx(
                      'text-[10px] px-2 py-0.5 rounded-full border transition-colors',
                      isRead
                        ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                        : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-violet-300 hover:text-violet-700'
                    )}
                  >
                    {s}. {isRtl ? name.ar : name.en}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Read first surah CTA */}
          <Link
            to={`/quran/${juz.startSurah}`}
            onClick={e => e.stopPropagation()}
            className={clsx(
              'flex items-center gap-1.5 text-xs text-violet-700 hover:text-violet-900 font-medium transition-colors',
              isRtl && 'flex-row-reverse'
            )}
          >
            <ChevronRight className={clsx('w-3.5 h-3.5', isRtl && 'rotate-180')} />
            {isRtl ? `ابدأ قراءة الجزء ${juz.juz}` : `Start reading Juz ${juz.juz}`}
          </Link>
        </div>
      )}
    </div>
  );
}

export function JuzNavigatorPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { progress } = useReadingProgress();
  const visited = progress.visited;
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return JUZ_OVERVIEW;
    return JUZ_OVERVIEW.filter(j =>
      j.mainThemeEn.toLowerCase().includes(q) ||
      j.mainThemeAr.includes(q) ||
      j.keyTopicsEn.some(t => t.toLowerCase().includes(q)) ||
      j.keyTopicsAr.some(t => t.includes(q)) ||
      String(j.juz) === q
    );
  }, [search]);

  const totalComplete = JUZ_OVERVIEW.filter(j => {
    const { done, total } = juzProgress(j, visited);
    return done === total;
  }).length;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2 mb-1', isRtl && 'font-arabic flex-row-reverse')}>
          <BookOpen className="w-6 h-6 text-violet-600" />
          {isRtl ? 'أجزاء القرآن الكريم' : 'Quran Juz Navigator'}
        </h1>
        <div className={clsx('flex items-center gap-4 text-sm text-gray-500 flex-wrap', isRtl && 'flex-row-reverse')}>
          <span className={isRtl ? 'font-arabic' : ''}>
            {isRtl ? `${totalComplete} من 30 جزء مكتمل` : `${totalComplete} of 30 Juz complete`}
          </span>
          {totalComplete === 30 && (
            <span className="flex items-center gap-1 text-emerald-600 font-semibold">
              <Trophy className="w-4 h-4 text-amber-500" />
              {isRtl ? 'ختمة كاملة!' : 'Full Khatmah!'}
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>{Math.round((totalComplete / 30) * 100)}%</span>
          <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? 'مكتمل' : 'complete'}</span>
        </div>
        <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all"
            style={{ width: `${Math.max((totalComplete / 30) * 100, totalComplete > 0 ? 2 : 0)}%` }}
          />
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-5">
        <Search className={clsx('absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400', isRtl ? 'right-3' : 'left-3')} />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={isRtl ? 'ابحث بالموضوع أو رقم الجزء...' : 'Search by theme or juz number...'}
          className={clsx(
            'w-full border border-gray-200 rounded-xl py-2.5 text-sm focus:ring-2 focus:ring-violet-300 focus:border-violet-400 outline-none bg-white',
            isRtl ? 'pr-9 pl-3 text-right font-arabic' : 'pl-9 pr-3'
          )}
        />
      </div>

      {/* Juz list */}
      <div className="space-y-3">
        {filtered.map(juz => (
          <JuzCard key={juz.juz} juz={juz} isRtl={isRtl} visited={visited} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className={clsx('text-sm', isRtl && 'font-arabic')}>
            {isRtl ? 'لا توجد نتائج' : 'No results found'}
          </p>
        </div>
      )}
    </div>
  );
}
