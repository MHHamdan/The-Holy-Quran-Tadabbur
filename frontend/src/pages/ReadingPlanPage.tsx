/**
 * Reading Plan — Khatmah Planner
 *
 * Allows users to:
 * 1. See a 114-surah completion grid (color-coded: read / unread)
 * 2. Set a target completion date → calculates daily pages needed
 * 3. View how many surahs remain and whether they're on schedule
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BookMarked, Target, CalendarCheck, Flame, CheckCircle2,
  Circle, ChevronRight, Trophy,
} from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { useReadingProgress } from '../hooks/useReadingProgress';
import { SURAH_NAMES } from '../data/surahNames';
import clsx from 'clsx';

// Approximate page counts per surah (King Fahd Madinah Mushaf 604-page edition)
// Derived from standard juz boundaries. Each surah starts at its first aya.
const SURAH_PAGE_COUNT: Record<number, number> = {
  1: 1, 2: 22, 3: 10, 4: 10, 5: 8, 6: 11, 7: 12, 8: 5, 9: 10, 10: 8,
  11: 8, 12: 8, 13: 5, 14: 4, 15: 4, 16: 9, 17: 7, 18: 8, 19: 6, 20: 7,
  21: 7, 22: 6, 23: 5, 24: 6, 25: 5, 26: 8, 27: 6, 28: 8, 29: 5, 30: 5,
  31: 3, 32: 2, 33: 8, 34: 5, 35: 4, 36: 5, 37: 6, 38: 4, 39: 8, 40: 8,
  41: 5, 42: 5, 43: 6, 44: 3, 45: 4, 46: 4, 47: 4, 48: 4, 49: 3, 50: 3,
  51: 3, 52: 3, 53: 3, 54: 3, 55: 4, 56: 3, 57: 5, 58: 4, 59: 4, 60: 3,
  61: 2, 62: 2, 63: 2, 64: 2, 65: 3, 66: 3, 67: 3, 68: 3, 69: 3, 70: 2,
  71: 2, 72: 2, 73: 2, 74: 2, 75: 2, 76: 2, 77: 2, 78: 2, 79: 2, 80: 2,
  81: 1, 82: 1, 83: 2, 84: 1, 85: 1, 86: 1, 87: 1, 88: 1, 89: 2, 90: 1,
  91: 1, 92: 1, 93: 1, 94: 1, 95: 1, 96: 1, 97: 1, 98: 1, 99: 1, 100: 1,
  101: 1, 102: 1, 103: 1, 104: 1, 105: 1, 106: 1, 107: 1, 108: 1, 109: 1, 110: 1,
  111: 1, 112: 1, 113: 1, 114: 1,
};

const PLAN_KEY = 'tadabbur_reading_plan_v1';

interface PlanGoal {
  targetDate: string;   // YYYY-MM-DD
  setDate: string;      // when goal was set
}

function loadGoal(): PlanGoal | null {
  try {
    const raw = localStorage.getItem(PLAN_KEY);
    return raw ? JSON.parse(raw) as PlanGoal : null;
  } catch { return null; }
}

function saveGoal(g: PlanGoal | null) {
  if (g) localStorage.setItem(PLAN_KEY, JSON.stringify(g));
  else localStorage.removeItem(PLAN_KEY);
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function daysBetween(from: string, to: string): number {
  return Math.ceil((new Date(to).getTime() - new Date(from).getTime()) / 86400000);
}

function toAr(n: number): string {
  return n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[+d]);
}

export function ReadingPlanPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const { progress, resetProgress } = useReadingProgress();

  const [goal, setGoalState] = useState<PlanGoal | null>(loadGoal);
  const [dateInput, setDateInput] = useState(goal?.targetDate ?? '');
  const [editingGoal, setEditingGoal] = useState(!goal);

  const visited = progress.visited;
  const remaining = 114 - visited.size;

  // Compute remaining page count
  const remainingPages = useMemo(() => {
    let total = 0;
    for (let s = 1; s <= 114; s++) {
      if (!visited.has(s)) total += SURAH_PAGE_COUNT[s] ?? 1;
    }
    return total;
  }, [visited]);

  // Days remaining and daily target
  const today = todayStr();
  const daysLeft = goal ? Math.max(0, daysBetween(today, goal.targetDate)) : null;
  const dailyPages = daysLeft && daysLeft > 0 ? Math.ceil(remainingPages / daysLeft) : null;
  const onSchedule = dailyPages !== null && dailyPages <= 2;  // ≤2 pages/day = comfortable

  function handleSetGoal() {
    if (!dateInput || dateInput <= today) return;
    const g: PlanGoal = { targetDate: dateInput, setDate: today };
    saveGoal(g);
    setGoalState(g);
    setEditingGoal(false);
  }

  function handleClearGoal() {
    saveGoal(null);
    setGoalState(null);
    setEditingGoal(true);
    setDateInput('');
  }

  const streak = progress.streak;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2', isRtl && 'font-arabic')}>
            <BookMarked className="w-6 h-6 text-violet-600" />
            {isRtl ? 'خطة الختمة' : 'Khatmah Reading Plan'}
          </h1>
          <p className={clsx('text-sm text-gray-500 mt-1', isRtl && 'font-arabic')}>
            {isRtl
              ? `${toAr(visited.size)} من ${toAr(114)} سورة مكتملة`
              : `${visited.size} of 114 surahs completed`}
          </p>
        </div>
        {streak > 0 && (
          <div className="flex items-center gap-1.5 bg-orange-50 text-orange-700 border border-orange-200 px-3 py-1.5 rounded-xl text-sm font-semibold">
            <Flame className="w-4 h-4 text-orange-500" />
            {isRtl ? `${toAr(streak)} يوم متواصل` : `${streak}-day streak`}
          </div>
        )}
      </div>

      {/* Goal setter */}
      <div className={clsx(
        'rounded-2xl border p-5 mb-6',
        goal && !editingGoal
          ? 'bg-violet-50 border-violet-200'
          : 'bg-white border-gray-200'
      )}>
        {goal && !editingGoal ? (
          <div className="flex items-start gap-3 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className={clsx('flex items-center gap-2 mb-1', isRtl && 'flex-row-reverse')}>
                <Target className="w-4 h-4 text-violet-600" />
                <span className={clsx('font-semibold text-violet-800 text-sm', isRtl && 'font-arabic')}>
                  {isRtl ? 'هدفك' : 'Your Goal'}
                </span>
              </div>
              <p className={clsx('text-base font-bold text-gray-800 mb-1', isRtl && 'font-arabic')}>
                {new Date(goal.targetDate).toLocaleDateString(isRtl ? 'ar-SA' : 'en-US', {
                  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                })}
              </p>
              {daysLeft !== null && (
                <div className={clsx('flex flex-wrap gap-4 mt-2', isRtl && 'flex-row-reverse')}>
                  <div className={clsx('text-center', isRtl && 'text-right')}>
                    <p className="text-xl font-bold text-violet-700">{isRtl ? toAr(daysLeft) : daysLeft}</p>
                    <p className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>{isRtl ? 'يوم متبقي' : 'days left'}</p>
                  </div>
                  {dailyPages !== null && (
                    <div className={clsx('text-center', isRtl && 'text-right')}>
                      <p className="text-xl font-bold text-violet-700">{isRtl ? toAr(dailyPages) : dailyPages}</p>
                      <p className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>{isRtl ? 'صفحة / يوم' : 'pages / day'}</p>
                    </div>
                  )}
                  <div className={clsx('text-center', isRtl && 'text-right')}>
                    <p className="text-xl font-bold text-violet-700">{isRtl ? toAr(remaining) : remaining}</p>
                    <p className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>{isRtl ? 'سورة متبقية' : 'surahs left'}</p>
                  </div>
                  {onSchedule && (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-medium">
                      <CalendarCheck className="w-3.5 h-3.5" />
                      <span className={clsx(isRtl && 'font-arabic')}>{isRtl ? 'في الموعد' : 'On schedule'}</span>
                    </div>
                  )}
                </div>
              )}
              {daysLeft === 0 && (
                <p className={clsx('text-sm text-amber-700 font-semibold mt-1', isRtl && 'font-arabic')}>
                  {isRtl ? 'اليوم هو يوم الهدف! 🏆' : 'Today is your target day! 🏆'}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setEditingGoal(true)}
                className="text-xs text-violet-600 hover:text-violet-800 transition-colors px-3 py-1.5 border border-violet-200 rounded-lg"
              >
                {isRtl ? 'تعديل' : 'Edit'}
              </button>
              <button
                onClick={handleClearGoal}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors px-3 py-1.5 border border-gray-200 rounded-lg"
              >
                {isRtl ? 'حذف' : 'Clear'}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <p className={clsx('text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5', isRtl && 'font-arabic flex-row-reverse')}>
              <Target className="w-4 h-4 text-violet-500" />
              {isRtl ? 'حدد تاريخاً لإكمال الختمة' : 'Set a Khatmah completion date'}
            </p>
            <div className="flex gap-3 items-center flex-wrap">
              <input
                type="date"
                value={dateInput}
                min={todayStr()}
                onChange={(e) => setDateInput(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-300 focus:border-violet-400 outline-none"
              />
              <button
                onClick={handleSetGoal}
                disabled={!dateInput || dateInput <= todayStr()}
                className={clsx(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  dateInput && dateInput > todayStr()
                    ? 'bg-violet-600 text-white hover:bg-violet-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                )}
              >
                {isRtl ? 'حفظ الهدف' : 'Set Goal'}
              </button>
              {goal && (
                <button
                  onClick={() => setEditingGoal(false)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  {isRtl ? 'إلغاء' : 'Cancel'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 114 Surah grid */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <div className={clsx('flex items-center justify-between mb-4 flex-wrap gap-2', isRtl && 'flex-row-reverse')}>
          <h2 className={clsx('font-semibold text-gray-800 text-sm flex items-center gap-2', isRtl && 'font-arabic flex-row-reverse')}>
            <Trophy className="w-4 h-4 text-amber-500" />
            {isRtl ? 'خريطة السور' : 'Surah Map'}
          </h2>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              {isRtl ? 'مقروءة' : 'Read'}
            </span>
            <span className="flex items-center gap-1">
              <Circle className="w-3.5 h-3.5 text-gray-300" />
              {isRtl ? 'لم تُقرأ' : 'Unread'}
            </span>
            {visited.size > 0 && (
              <button
                onClick={() => {
                  if (window.confirm(isRtl ? 'إعادة تعيين كل التقدم؟' : 'Reset all progress?')) {
                    resetProgress();
                  }
                }}
                className="text-red-400 hover:text-red-600 transition-colors"
              >
                {isRtl ? 'إعادة تعيين' : 'Reset'}
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-1.5">
          {Array.from({ length: 114 }, (_, i) => {
            const surahNo = i + 1;
            const isRead = visited.has(surahNo);
            const name = SURAH_NAMES[i];
            return (
              <Link
                key={surahNo}
                to={`/quran/${surahNo}`}
                className={clsx(
                  'relative flex flex-col items-center justify-center p-1.5 rounded-lg transition-all text-center group',
                  isRead
                    ? 'bg-emerald-100 border border-emerald-200 hover:bg-emerald-200'
                    : 'bg-gray-50 border border-gray-100 hover:bg-violet-50 hover:border-violet-200'
                )}
                title={`${surahNo}. ${name.en} / ${name.ar}`}
              >
                <span className={clsx(
                  'text-[10px] font-bold leading-none',
                  isRead ? 'text-emerald-700' : 'text-gray-500 group-hover:text-violet-600'
                )}>
                  {surahNo}
                </span>
                {isRead && (
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-500 absolute bottom-0.5 right-0.5" />
                )}
              </Link>
            );
          })}
        </div>

        {/* Quick mark as read (for surahs you've read outside the app) */}
        <p className={clsx('text-xs text-gray-400 mt-4 text-center', isRtl && 'font-arabic')}>
          {isRtl
            ? 'تتبع تقدمك تلقائياً عند تصفح أي سورة — أو اضغط عليها لفتحها'
            : 'Progress is tracked automatically when you browse any surah'}
        </p>
      </div>

      {/* CTA to start reading */}
      {visited.size === 0 && (
        <div className="mt-6 text-center">
          <Link
            to="/mushaf"
            className="inline-flex items-center gap-2 px-6 py-3 bg-violet-600 text-white rounded-xl hover:bg-violet-700 transition-colors font-semibold"
          >
            <BookMarked className="w-4 h-4" />
            {isRtl ? 'ابدأ القراءة الآن' : 'Start Reading Now'}
            <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          </Link>
        </div>
      )}

      {visited.size === 114 && (
        <div className="mt-6 bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center">
          <Trophy className="w-12 h-12 text-amber-500 mx-auto mb-3" />
          <h3 className={clsx('text-lg font-bold text-emerald-800 mb-2', isRtl && 'font-arabic')}>
            {isRtl ? 'ألف مبروك! أتممت الختمة 🎉' : 'Congratulations! Khatmah Complete 🎉'}
          </h3>
          <p className={clsx('text-sm text-emerald-600 mb-4', isRtl && 'font-arabic')}>
            {isRtl ? 'وفقك الله وبارك في عملك' : 'May Allah bless your efforts'}
          </p>
          <button
            onClick={() => {
              if (window.confirm(isRtl ? 'ابدأ ختمة جديدة؟' : 'Start a new Khatmah?')) {
                resetProgress();
                handleClearGoal();
              }
            }}
            className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors text-sm font-semibold"
          >
            {isRtl ? 'ابدأ ختمة جديدة' : 'Start New Khatmah'}
          </button>
        </div>
      )}

      {/* Stats footer */}
      <div className={clsx('mt-6 grid grid-cols-3 gap-3 text-center', isRtl && 'font-arabic')}>
        <div className="bg-white rounded-xl border border-gray-100 p-3">
          <p className="text-xl font-bold text-violet-700">{isRtl ? toAr(visited.size) : visited.size}</p>
          <p className="text-xs text-gray-500">{isRtl ? 'سورة مكتملة' : 'surahs done'}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-3">
          <p className="text-xl font-bold text-gray-700">{isRtl ? toAr(remaining) : remaining}</p>
          <p className="text-xs text-gray-500">{isRtl ? 'سورة متبقية' : 'surahs left'}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-3">
          <p className="text-xl font-bold text-amber-600">{isRtl ? toAr(streak) : streak}</p>
          <p className="text-xs text-gray-500">{isRtl ? 'أيام متواصلة' : 'day streak'}</p>
        </div>
      </div>
    </div>
  );
}
