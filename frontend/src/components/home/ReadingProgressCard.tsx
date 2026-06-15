/**
 * ReadingProgressCard — Khatmah / reading progress widget.
 *
 * Competitive gap: Quranly and Muslim Pro show daily/weekly streaks;
 * Ayat and Quran.com track khatmah. This provides a lightweight
 * equivalent backed purely by localStorage (no auth required).
 */

import { Link } from 'react-router-dom';
import { BookMarked, RotateCcw, ChevronRight, Flame, CalendarCheck } from 'lucide-react';
import clsx from 'clsx';
import { useReadingProgress } from '../../hooks/useReadingProgress';
import { useLanguageStore } from '../../stores/languageStore';

const TOTAL = 114;

export function ReadingProgressCard() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { progress, resetProgress } = useReadingProgress();

  const visited = progress.visited.size;
  const pct = Math.round((visited / TOTAL) * 100);
  const lastRead = progress.lastRead;
  const streak = progress.streak ?? 0;
  const longestStreak = progress.longestStreak ?? 0;

  const handleReset = () => {
    if (window.confirm(isRtl ? 'هل تريد إعادة تعيين تقدم القراءة؟' : 'Reset reading progress?')) {
      resetProgress();
    }
  };

  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-2xl border border-violet-200',
        'bg-gradient-to-br from-violet-50 via-purple-50 to-indigo-50 p-5',
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Decorative orb */}
      <div className="absolute -bottom-6 -left-6 w-28 h-28 rounded-full bg-violet-100/70 blur-2xl pointer-events-none" />

      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-4', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <div className="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center flex-shrink-0">
            <BookMarked className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <p className={clsx('text-xs font-semibold text-violet-700 uppercase tracking-wide', isRtl && 'font-arabic')}>
              {isRtl ? 'تقدم الختمة' : 'Khatmah Progress'}
            </p>
            <p className="text-[10px] text-gray-400">
              {isRtl ? `${visited} من ${TOTAL} سورة` : `${visited} of ${TOTAL} surahs`}
            </p>
          </div>
        </div>
        {visited > 0 && (
          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/60 transition-colors"
            title={isRtl ? 'إعادة تعيين' : 'Reset progress'}
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-[11px] text-gray-500 mb-1">
          <span>{pct}%</span>
          <span className={isRtl ? 'font-arabic' : ''}>
            {isRtl ? 'مكتمل' : 'complete'}
          </span>
        </div>
        <div className="w-full h-2.5 bg-violet-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.max(pct, visited > 0 ? 2 : 0)}%` }}
          />
        </div>
      </div>

      {/* Streak stats */}
      {(streak > 0 || longestStreak > 0) && (
        <div className={clsx('flex items-center gap-3 mb-4', isRtl && 'flex-row-reverse')}>
          <div className={clsx(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg flex-1 justify-center',
            streak >= 3 ? 'bg-orange-100 text-orange-700' : 'bg-white/60 text-gray-600'
          )}>
            <Flame className={clsx('w-3.5 h-3.5 flex-shrink-0', streak >= 3 && 'text-orange-500')} />
            <div className="text-center">
              <p className="text-xs font-bold">{streak}</p>
              <p className={clsx('text-[10px]', isRtl && 'font-arabic')}>
                {isRtl ? 'يوم متتالي' : streak === 1 ? 'day' : 'days'}
              </p>
            </div>
          </div>
          {longestStreak > streak && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/60 text-gray-500 flex-1 justify-center">
              <Flame className="w-3 h-3 text-gray-400" />
              <div className="text-center">
                <p className="text-xs font-bold">{longestStreak}</p>
                <p className={clsx('text-[10px]', isRtl && 'font-arabic')}>
                  {isRtl ? 'أفضل سلسلة' : 'best streak'}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Last read */}
      {lastRead ? (
        <div className="mb-4">
          <p className={clsx('text-[10px] text-gray-400 mb-1', isRtl && 'font-arabic text-right')}>
            {isRtl ? 'آخر قراءة' : 'Last read'}
          </p>
          <Link
            to={`/quran/${lastRead.surah}`}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg',
              'bg-white/60 hover:bg-white/90 border border-violet-100 transition-colors',
              isRtl && 'flex-row-reverse',
            )}
          >
            <div className="w-6 h-6 rounded-md bg-violet-100 flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] font-bold text-violet-600">{lastRead.surah}</span>
            </div>
            <div className={clsx('flex-1 min-w-0', isRtl && 'text-right')}>
              <p className="text-xs font-medium text-gray-800 truncate">{lastRead.nameEn}</p>
              <p className="text-[10px] font-arabic text-gray-500 truncate">{lastRead.nameAr}</p>
            </div>
            <ChevronRight className={clsx('w-3.5 h-3.5 text-violet-400 flex-shrink-0', isRtl && 'rotate-180')} />
          </Link>
        </div>
      ) : (
        <p className={clsx('text-xs text-gray-400 italic mb-4', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'ابدأ القراءة لتتبع تقدمك' : 'Start reading to track your progress'}
        </p>
      )}

      {/* CTAs */}
      <div className="flex gap-2">
        <Link
          to="/quran"
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium flex-1 justify-center',
            'bg-violet-600 text-white hover:bg-violet-700 transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          {isRtl ? 'المصحف' : 'Mushaf'}
          <ChevronRight className={clsx('w-3.5 h-3.5', isRtl && 'rotate-180')} />
        </Link>
        <Link
          to="/reading-plan"
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium flex-1 justify-center',
            'bg-white border border-violet-200 text-violet-700 hover:bg-violet-50 transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <CalendarCheck className="w-3.5 h-3.5" />
          {isRtl ? 'الختمة' : 'Plan'}
        </Link>
      </div>
    </div>
  );
}
