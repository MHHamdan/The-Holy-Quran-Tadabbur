/**
 * Daily Quranic Challenge — v3
 *
 * One question per day, date-seeded from a pool covering the entire Quran:
 * story quizzes (all batches), verified trivia, and generated surah-metadata
 * questions for all 114 surahs (see utils/challengePool.ts). Categories rotate
 * daily. Tracks streaks, history, accuracy, achievements, and cumulative
 * surah coverage in localStorage.
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import {
  Flame, CheckCircle2, XCircle, ChevronRight, BookOpen,
  Clock, Lightbulb, Share2, Target, Map, Layers,
} from 'lucide-react';
import { QURAN_STORIES_FIRST_BATCH } from '../data/quranStories';
import { SURAH_NAMES } from '../data/surahNames';
import {
  getChallengePool, getPoolSize, getQuestionForDate,
  CATEGORY_META,
} from '../utils/challengePool';
import type { ChallengeQuestion, ChallengeCategory } from '../utils/challengePool';
import { useLanguageStore } from '../stores/languageStore';
import clsx from 'clsx';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DayRecord {
  correct: boolean;
  answered: boolean;
  surah?: number;
  category?: ChallengeCategory;
}

interface DailyState {
  date: string;
  questionId: string;
  answeredIndex: number | null;
  streak: number;
  longestStreak: number;
  totalPlayed: number;
  totalCorrect: number;
  history: Record<string, DayRecord>;
  coveredSurahs: number[];
}

interface Achievement {
  id: string;
  icon: string;
  labelEn: string;
  labelAr: string;
  descEn: string;
  descAr: string;
  unlocked: (s: DailyState) => boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'tadabbur_daily_challenge_v1';

const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_step',
    icon: '🌱',
    labelEn: 'First Step',
    labelAr: 'الخطوة الأولى',
    descEn: 'Answered your first challenge',
    descAr: 'أجبت على تحديك الأول',
    unlocked: (s) => s.totalPlayed >= 1,
  },
  {
    id: 'on_fire',
    icon: '🔥',
    labelEn: 'On Fire',
    labelAr: 'متقد',
    descEn: '3-day correct streak',
    descAr: 'سلسلة ٣ أيام صحيحة',
    unlocked: (s) => s.longestStreak >= 3,
  },
  {
    id: 'weekly',
    icon: '⭐',
    labelEn: 'Weekly Scholar',
    labelAr: 'عالم الأسبوع',
    descEn: '7-day streak',
    descAr: 'سلسلة ٧ أيام',
    unlocked: (s) => s.longestStreak >= 7,
  },
  {
    id: 'sharp_mind',
    icon: '🎯',
    labelEn: 'Sharp Mind',
    labelAr: 'عقل حاد',
    descEn: '10 correct answers',
    descAr: '١٠ إجابات صحيحة',
    unlocked: (s) => s.totalCorrect >= 10,
  },
  {
    id: 'explorer',
    icon: '🗺️',
    labelEn: 'Quran Explorer',
    labelAr: 'مستكشف القرآن',
    descEn: 'Questions from 10 different surahs',
    descAr: 'أسئلة من ١٠ سور مختلفة',
    unlocked: (s) => s.coveredSurahs.length >= 10,
  },
  {
    id: 'devoted',
    icon: '🏆',
    labelEn: 'Devoted',
    labelAr: 'مخلص',
    descEn: '30-day streak',
    descAr: 'سلسلة ٣٠ يوماً',
    unlocked: (s) => s.longestStreak >= 30,
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function yesterdayStr(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

function toAr(n: number): string {
  return n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[+d]);
}

function getSecondsUntilMidnight(): number {
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(24, 0, 0, 0);
  return Math.max(0, Math.floor((midnight.getTime() - now.getTime()) / 1000));
}

function formatCountdown(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
}

function formatTheme(t: string): string {
  return t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function loadState(): DailyState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as DailyState) : null;
  } catch {
    return null;
  }
}

function saveState(state: DailyState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({
  icon, value, labelEn, labelAr, isRtl,
}: {
  icon: ReactNode;
  value: string | number;
  labelEn: string;
  labelAr: string;
  isRtl: boolean;
}) {
  return (
    <div className="flex-1 min-w-0 bg-white rounded-xl border border-gray-100 shadow-sm p-3 flex flex-col items-center gap-1">
      <div className="text-xl leading-none">{icon}</div>
      <div className="text-lg font-bold text-gray-900 tabular-nums">{value}</div>
      <div className={clsx('text-xs text-gray-500 text-center leading-tight', isRtl && 'font-arabic')}>
        {isRtl ? labelAr : labelEn}
      </div>
    </div>
  );
}

function WeekCalendar({
  history, today, isRtl,
}: {
  history: Record<string, DayRecord>;
  today: string;
  isRtl: boolean;
}) {
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    days.push({
      dateStr,
      isToday: dateStr === today,
      record: history[dateStr],
      dayName: d.toLocaleDateString(isRtl ? 'ar-SA' : 'en-US', { weekday: 'short' }),
    });
  }
  if (isRtl) days.reverse();

  return (
    <div className="flex gap-1.5 justify-center">
      {days.map(({ dateStr, isToday, record, dayName }) => {
        const hasRecord = record?.answered;
        const dotBg = hasRecord
          ? record.correct
            ? 'bg-emerald-500 border-emerald-600 text-white'
            : 'bg-red-400 border-red-500 text-white'
          : isToday
            ? 'bg-primary-100 border-primary-400 border-dashed text-primary-600'
            : 'bg-gray-100 border-gray-200 text-gray-300';

        return (
          <div key={dateStr} className="flex flex-col items-center gap-1 flex-1">
            <div className={clsx(
              'w-full aspect-square max-w-[36px] rounded-full border-2 flex items-center justify-center text-xs font-bold',
              dotBg,
            )}>
              {hasRecord ? (record.correct ? '✓' : '✗') : isToday ? '·' : ''}
            </div>
            <span className={clsx('text-[10px] text-gray-400 text-center', isRtl && 'font-arabic')}>
              {dayName}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** GitHub-style 5-week mini heatmap of past activity (35 days ending today). */
function ActivityHeatmap({
  history, today, isRtl,
}: {
  history: Record<string, DayRecord>;
  today: string;
  isRtl: boolean;
}) {
  const cells = [];
  for (let i = 34; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    cells.push({ dateStr, record: history[dateStr], isToday: dateStr === today });
  }

  return (
    <div>
      <div className={clsx('flex items-center justify-between mb-2', isRtl && 'flex-row-reverse')}>
        <span className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
          {isRtl ? 'آخر ٣٥ يوماً' : 'Last 35 days'}
        </span>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-gray-100" />
          <span className="w-2 h-2 rounded-sm bg-red-300" />
          <span className="w-2 h-2 rounded-sm bg-emerald-400" />
          <span className={clsx('text-[10px] text-gray-400 ms-1', isRtl && 'font-arabic')}>
            {isRtl ? 'خطأ / صواب' : 'wrong / correct'}
          </span>
        </div>
      </div>
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', direction: isRtl ? 'rtl' : 'ltr' }}
      >
        {cells.map(({ dateStr, record, isToday }) => (
          <div
            key={dateStr}
            title={dateStr}
            className={clsx(
              'aspect-square rounded-[4px]',
              record?.answered
                ? record.correct ? 'bg-emerald-400' : 'bg-red-300'
                : 'bg-gray-100',
              isToday && 'ring-2 ring-primary-400 ring-offset-1',
            )}
          />
        ))}
      </div>
    </div>
  );
}

/** 114-cell map of the Quran — fills in as questions touch each surah. */
function QuranCoverageMap({
  covered, todaySurah, isRtl,
}: {
  covered: Set<number>;
  todaySurah?: number;
  isRtl: boolean;
}) {
  return (
    <div>
      <div
        className="grid gap-[3px]"
        style={{ gridTemplateColumns: 'repeat(19, minmax(0, 1fr))', direction: isRtl ? 'rtl' : 'ltr' }}
      >
        {SURAH_NAMES.map((name, idx) => {
          const surahNo = idx + 1;
          const isCovered = covered.has(surahNo);
          const isToday = surahNo === todaySurah;
          return (
            <Link
              key={surahNo}
              to={`/surah-atlas/${surahNo}`}
              title={`${surahNo}. ${isRtl ? name.ar : name.en}`}
              className={clsx(
                'aspect-square rounded-[3px] transition-colors',
                isToday
                  ? 'bg-amber-400 ring-2 ring-amber-500 ring-offset-1 animate-pulse'
                  : isCovered
                    ? 'bg-emerald-500 hover:bg-emerald-600'
                    : 'bg-gray-100 hover:bg-gray-200',
              )}
            />
          );
        })}
      </div>
      <div className={clsx('flex items-center gap-4 mt-3 justify-center', isRtl && 'font-arabic')}>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
          <span className="text-xs text-gray-400">{isRtl ? 'سورة مغطاة' : 'Covered'}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-amber-400" />
          <span className="text-xs text-gray-400">{isRtl ? 'سؤال اليوم' : "Today's surah"}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-gray-100 border border-gray-200" />
          <span className="text-xs text-gray-400">{isRtl ? 'لم تُغطَّ بعد' : 'Not yet'}</span>
        </div>
      </div>
    </div>
  );
}

/** Stacked bar showing how the question pool spans stories / knowledge / surahs. */
function PoolCompositionBar({ isRtl }: { isRtl: boolean }) {
  const pool = getChallengePool();
  const total = getPoolSize();
  const segments = (Object.keys(CATEGORY_META) as ChallengeCategory[]).map((cat) => ({
    cat,
    count: pool[cat].length,
    pct: (pool[cat].length / total) * 100,
    ...CATEGORY_META[cat],
  }));

  return (
    <div>
      <div
        className="flex h-2.5 rounded-full overflow-hidden"
        style={{ direction: isRtl ? 'rtl' : 'ltr' }}
      >
        {segments.map((s) => (
          <div key={s.cat} className={s.color} style={{ width: `${s.pct}%` }} />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 justify-center">
        {segments.map((s) => (
          <div key={s.cat} className="flex items-center gap-1.5">
            <span className={clsx('w-2.5 h-2.5 rounded-sm', s.color)} />
            <span className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
              {isRtl ? s.labelAr : s.labelEn}
              {' '}
              <span className="text-gray-400 tabular-nums">
                ({isRtl ? toAr(s.count) : s.count})
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function DailyChallengePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const today = todayStr();
  const poolSize = useMemo(() => getPoolSize(), []);
  const todayQuestion = useMemo<ChallengeQuestion>(() => getQuestionForDate(today), [today]);
  const categoryMeta = CATEGORY_META[todayQuestion.category];

  const storyData = useMemo(
    () => todayQuestion.storyId
      ? QURAN_STORIES_FIRST_BATCH.find((s) => s.storyId === todayQuestion.storyId)
      : undefined,
    [todayQuestion.storyId],
  );

  const [daily, setDaily] = useState<DailyState>(() => {
    const saved = loadState();
    if (saved && saved.date === today && saved.questionId === todayQuestion.questionId) {
      return {
        ...saved,
        totalPlayed: saved.totalPlayed ?? 0,
        totalCorrect: saved.totalCorrect ?? 0,
        history: saved.history ?? {},
        coveredSurahs: saved.coveredSurahs ?? [],
      };
    }
    const prevStreak =
      saved && saved.date === yesterdayStr() && saved.answeredIndex !== null
        ? saved.streak
        : 0;
    return {
      date: today,
      questionId: todayQuestion.questionId,
      answeredIndex: null,
      streak: prevStreak,
      longestStreak: saved?.longestStreak ?? 0,
      totalPlayed: saved?.totalPlayed ?? 0,
      totalCorrect: saved?.totalCorrect ?? 0,
      history: saved?.history ?? {},
      coveredSurahs: saved?.coveredSurahs ?? [],
    };
  });

  const [selected, setSelected] = useState<number | null>(daily.answeredIndex);
  const [copied, setCopied] = useState(false);
  const [countdown, setCountdown] = useState(getSecondsUntilMidnight());

  const answered = selected !== null;
  const isCorrect = answered && selected === todayQuestion.correctOptionIndex;
  const accuracy =
    daily.totalPlayed > 0 ? Math.round((daily.totalCorrect / daily.totalPlayed) * 100) : 0;
  const coveredSet = useMemo(() => new Set(daily.coveredSurahs), [daily.coveredSurahs]);

  // Countdown ticks once per second after answering
  useEffect(() => {
    if (!answered) return;
    const timer = setInterval(() => setCountdown(getSecondsUntilMidnight()), 1000);
    return () => clearInterval(timer);
  }, [answered]);

  const handleSelect = useCallback(
    (idx: number) => {
      if (answered) return;
      const correct = idx === todayQuestion.correctOptionIndex;
      const newStreak = correct ? daily.streak + 1 : 0;
      const newLongest = Math.max(newStreak, daily.longestStreak);
      const surah = todayQuestion.surahRef;
      const next: DailyState = {
        ...daily,
        answeredIndex: idx,
        streak: newStreak,
        longestStreak: newLongest,
        totalPlayed: daily.totalPlayed + 1,
        totalCorrect: daily.totalCorrect + (correct ? 1 : 0),
        history: {
          ...daily.history,
          [today]: { correct, answered: true, surah, category: todayQuestion.category },
        },
        coveredSurahs:
          surah && !daily.coveredSurahs.includes(surah)
            ? [...daily.coveredSurahs, surah]
            : daily.coveredSurahs,
      };
      setSelected(idx);
      setDaily(next);
      saveState(next);
    },
    [answered, daily, today, todayQuestion],
  );

  const handleShare = useCallback(() => {
    const emoji = isCorrect ? '✅' : '❌';
    const coverage = `${coveredSet.size}/114`;
    const text = isRtl
      ? `${emoji} أجبت على تحدي القرآن اليوم!\nالسلسلة: ${daily.streak} يوم 🔥\nتغطية السور: ${coverage} 🗺️\n#تدبر`
      : `${emoji} I completed today's Quran Challenge!\nStreak: ${daily.streak} days 🔥\nSurah coverage: ${coverage} 🗺️\n#Tadabbur`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [isCorrect, isRtl, daily.streak, coveredSet.size]);

  // First lesson from the story for the post-answer insight
  const storyLesson = useMemo(() => {
    if (!storyData) return null;
    for (const seg of storyData.storySegments) {
      const lessons = isRtl ? seg.lessonsArabic : seg.lessonsEnglish;
      if (lessons?.length) return lessons[0];
    }
    return null;
  }, [storyData, isRtl]);

  const options = isRtl ? todayQuestion.optionsArabic : todayQuestion.optionsEnglish;
  const surahName = todayQuestion.surahRef
    ? SURAH_NAMES[todayQuestion.surahRef - 1]
    : undefined;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* ── Header ── */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center flex-shrink-0">
          <Flame className="w-5 h-5" />
        </div>
        <div>
          <h1 className={clsx('text-xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'تحدي اليوم' : "Today's Challenge"}
          </h1>
          <p className="text-xs text-gray-400">
            {new Date(today).toLocaleDateString(isRtl ? 'ar-SA' : 'en-US', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            })}
          </p>
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="flex gap-2 mb-5">
        <StatCard icon="🔥" value={isRtl ? toAr(daily.streak) : daily.streak}
          labelEn="Streak" labelAr="السلسلة" isRtl={isRtl} />
        <StatCard icon="🏆" value={isRtl ? toAr(daily.longestStreak) : daily.longestStreak}
          labelEn="Best" labelAr="الأفضل" isRtl={isRtl} />
        <StatCard icon="🎯" value={`${isRtl ? toAr(accuracy) : accuracy}%`}
          labelEn="Accuracy" labelAr="الدقة" isRtl={isRtl} />
        <StatCard icon="🗺️" value={isRtl ? `${toAr(coveredSet.size)}/${toAr(114)}` : `${coveredSet.size}/114`}
          labelEn="Surahs" labelAr="السور" isRtl={isRtl} />
      </div>

      {/* ── Activity: week + heatmap ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 mb-5">
        <div className={clsx('text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide', isRtl && 'font-arabic')}>
          {isRtl ? 'تقدم هذا الأسبوع' : 'This Week'}
        </div>
        <WeekCalendar history={daily.history} today={today} isRtl={isRtl} />
        <div className="border-t border-gray-50 mt-4 pt-4">
          <ActivityHeatmap history={daily.history} today={today} isRtl={isRtl} />
        </div>
      </div>

      {/* ── Question source context ── */}
      <div className="bg-gradient-to-br from-primary-50 via-white to-emerald-50 border border-primary-100 rounded-2xl px-5 py-4 mb-4">
        <div className={clsx('flex items-center justify-between mb-2')}>
          <div className={clsx('text-[11px] font-semibold text-primary-500 uppercase tracking-widest', isRtl && 'font-arabic')}>
            {isRtl ? 'مصدر السؤال' : 'Question Source'}
          </div>
          <span className={clsx(
            'text-[11px] font-semibold rounded-full px-2.5 py-0.5 bg-white border border-primary-200 text-primary-700',
            isRtl && 'font-arabic',
          )}>
            {categoryMeta.emoji} {isRtl ? categoryMeta.labelAr : categoryMeta.labelEn}
          </span>
        </div>
        <div className={clsx('font-semibold text-gray-800 text-sm mb-1', isRtl && 'font-arabic')}>
          {isRtl ? todayQuestion.sourceLabelAr : todayQuestion.sourceLabelEn}
        </div>

        {storyData && storyData.quranReferences.length > 0 && (
          <div className={clsx('text-xs text-gray-500 mb-2.5', isRtl && 'font-arabic')}>
            {storyData.quranReferences.slice(0, 2).map((ref) => ref.referenceLabel).join(' · ')}
          </div>
        )}

        <div className="flex flex-wrap gap-2 mt-1.5">
          {todayQuestion.surahRef && surahName && (
            <Link
              to={`/surah-atlas/${todayQuestion.surahRef}`}
              className={clsx(
                'text-xs bg-white border border-primary-200 text-primary-700 rounded-full px-2.5 py-1 font-medium hover:bg-primary-50 transition-colors',
                isRtl && 'font-arabic',
              )}
            >
              📖 {isRtl ? `سورة ${surahName.ar}` : `Surah ${surahName.en}`} ({todayQuestion.surahRef})
            </Link>
          )}
          {storyData?.prophetsMentioned?.slice(0, 2).map((p) => (
            <span key={p} className="text-xs bg-amber-50 border border-amber-200 text-amber-700 rounded-full px-2.5 py-1">
              ﷺ {p}
            </span>
          ))}
          {storyData?.themes.slice(0, 3).map((t) => (
            <span key={t} className="text-xs bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-full px-2.5 py-1 capitalize">
              {formatTheme(t)}
            </span>
          ))}
        </div>
      </div>

      {/* ── Question Card ── */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-4">
        {/* Source label bar */}
        <div className={clsx(
          'px-5 py-2.5 text-xs font-medium bg-primary-50 text-primary-700 border-b border-primary-100 flex items-center gap-2',
          isRtl && 'font-arabic',
        )}>
          <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
          {isRtl ? todayQuestion.sourceLabelAr : todayQuestion.sourceLabelEn}
        </div>

        <div className="px-5 py-5">
          <p className={clsx('text-base font-semibold text-gray-800 leading-relaxed mb-5', isRtl && 'font-arabic')}>
            {isRtl ? todayQuestion.questionArabic : todayQuestion.questionEnglish}
          </p>

          <div className="space-y-2.5">
            {options.map((opt, i) => {
              let stateClass =
                'border-gray-200 hover:border-primary-300 hover:bg-primary-50 cursor-pointer';
              if (answered) {
                if (i === todayQuestion.correctOptionIndex) {
                  stateClass = 'border-emerald-400 bg-emerald-50 cursor-default';
                } else if (i === selected) {
                  stateClass = 'border-red-400 bg-red-50 cursor-default';
                } else {
                  stateClass = 'border-gray-100 bg-gray-50 opacity-60 cursor-default';
                }
              }

              return (
                <button
                  key={i}
                  onClick={() => handleSelect(i)}
                  disabled={answered}
                  className={clsx(
                    'w-full flex items-center gap-3 px-4 py-3.5 rounded-xl border-2 transition-all text-start',
                    stateClass,
                  )}
                >
                  <span className={clsx(
                    'w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold flex-shrink-0',
                    answered && i === todayQuestion.correctOptionIndex
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : answered && i === selected
                        ? 'border-red-500 bg-red-500 text-white'
                        : 'border-gray-300 text-gray-500',
                  )}>
                    {answered
                      ? i === todayQuestion.correctOptionIndex
                        ? <CheckCircle2 className="w-4 h-4" />
                        : i === selected
                          ? <XCircle className="w-4 h-4" />
                          : ['أ', 'ب', 'ج', 'د'][i]
                      : isRtl
                        ? ['أ', 'ب', 'ج', 'د'][i]
                        : String.fromCharCode(65 + i)}
                  </span>
                  <span className={clsx('text-sm text-gray-700 leading-snug', isRtl && 'font-arabic')}>
                    {opt}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Result + explanation */}
        {answered && (
          <div className={clsx(
            'px-5 py-4 border-t',
            isCorrect ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100',
          )}>
            <div className={clsx(
              'flex items-center gap-2 font-semibold text-sm mb-2',
              isCorrect ? 'text-emerald-700' : 'text-red-700',
            )}>
              {isCorrect ? (
                <><CheckCircle2 className="w-4 h-4" />
                  <span className={clsx(isRtl && 'font-arabic')}>
                    {isRtl ? 'أحسنت! إجابة صحيحة' : 'Correct!'}
                  </span></>
              ) : (
                <><XCircle className="w-4 h-4" />
                  <span className={clsx(isRtl && 'font-arabic')}>
                    {isRtl ? 'إجابة خاطئة' : 'Incorrect'}
                  </span></>
              )}
            </div>
            <p className={clsx('text-sm text-gray-700 leading-relaxed', isRtl && 'font-arabic')}>
              {isRtl ? todayQuestion.explanationArabic : todayQuestion.explanationEnglish}
            </p>
          </div>
        )}
      </div>

      {/* ── Post-answer panels ── */}
      {answered && (
        <>
          {/* Lesson from the story */}
          {storyLesson && (
            <div className="bg-amber-50 border border-amber-100 rounded-2xl px-5 py-4 mb-4">
              <div className={clsx(
                'flex items-center gap-2 text-xs font-semibold text-amber-700 mb-2',
                isRtl && 'font-arabic',
              )}>
                <Lightbulb className="w-4 h-4 flex-shrink-0" />
                {isRtl ? 'درس من القصة' : 'Lesson from this Story'}
              </div>
              <p className={clsx('text-sm text-amber-900 leading-relaxed', isRtl && 'font-arabic')}>
                {storyLesson}
              </p>
            </div>
          )}

          {/* Countdown + Share */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-white border border-gray-100 rounded-2xl px-4 py-4 flex flex-col items-center gap-1 shadow-sm">
              <Clock className="w-4 h-4 text-primary-400 mb-0.5" />
              <div className="text-xl font-mono font-bold text-gray-800 tabular-nums tracking-wider">
                {formatCountdown(countdown)}
              </div>
              <div className={clsx('text-xs text-gray-400 text-center', isRtl && 'font-arabic')}>
                {isRtl ? 'حتى التحدي القادم' : 'until next challenge'}
              </div>
            </div>
            <button
              onClick={handleShare}
              className="bg-white border border-gray-100 rounded-2xl px-4 py-4 flex flex-col items-center gap-1 shadow-sm hover:bg-gray-50 active:scale-95 transition-all"
            >
              <Share2 className="w-4 h-4 text-primary-400 mb-0.5" />
              <div className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
                {copied
                  ? (isRtl ? '✓ تم النسخ!' : '✓ Copied!')
                  : (isRtl ? 'شارك نتيجتك' : 'Share Result')}
              </div>
              <div className={clsx('text-xs text-gray-400 text-center', isRtl && 'font-arabic')}>
                {isRtl ? 'انسخ للحافظة' : 'copy to clipboard'}
              </div>
            </button>
          </div>

          {/* Streak milestone banner */}
          {isCorrect && daily.streak > 0 && daily.streak % 3 === 0 && (
            <div className="bg-gradient-to-r from-orange-400 to-amber-400 text-white rounded-2xl px-5 py-3.5 mb-4 flex items-center gap-3">
              <span className="text-2xl">🔥</span>
              <div>
                <div className={clsx('font-bold text-sm', isRtl && 'font-arabic')}>
                  {isRtl
                    ? `رائع! ${toAr(daily.streak)} أيام متواصلة`
                    : `Amazing! ${daily.streak}-day streak!`}
                </div>
                <div className={clsx('text-xs text-orange-100', isRtl && 'font-arabic')}>
                  {isRtl ? 'واصل الاستمرار كل يوم' : 'Keep going, one day at a time'}
                </div>
              </div>
            </div>
          )}

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-3 mb-6">
            {storyData ? (
              <Link
                to={`/stories/${storyData.storyId}`}
                className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-amber-50 text-amber-800 border border-amber-200 text-sm rounded-xl hover:bg-amber-100 transition-colors font-medium"
              >
                <BookOpen className="w-4 h-4 flex-shrink-0" />
                <span className={clsx(isRtl && 'font-arabic')}>
                  {isRtl ? 'اقرأ القصة كاملة' : 'Read Full Story'}
                </span>
              </Link>
            ) : todayQuestion.surahRef && surahName ? (
              <Link
                to={`/surah-atlas/${todayQuestion.surahRef}`}
                className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-amber-50 text-amber-800 border border-amber-200 text-sm rounded-xl hover:bg-amber-100 transition-colors font-medium"
              >
                <Layers className="w-4 h-4 flex-shrink-0" />
                <span className={clsx(isRtl && 'font-arabic')}>
                  {isRtl ? `استكشف سورة ${surahName.ar}` : `Explore Surah ${surahName.en}`}
                </span>
              </Link>
            ) : null}
            <Link
              to={todayQuestion.category === 'story' ? '/stories' : '/quiz'}
              className="flex-1 flex items-center justify-center gap-2 px-5 py-3 bg-primary-700 text-white text-sm rounded-xl hover:bg-primary-800 transition-colors font-medium"
            >
              <span className={clsx(isRtl && 'font-arabic')}>
                {todayQuestion.category === 'story'
                  ? (isRtl ? 'استكشف القصص' : 'Explore Stories')
                  : (isRtl ? 'المزيد من الأسئلة' : 'More Questions')}
              </span>
              <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
            </Link>
          </div>
        </>
      )}

      {/* ── Quran coverage map ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 mb-5">
        <div className="flex items-center justify-between mb-3">
          <div className={clsx('flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wide', isRtl && 'font-arabic')}>
            <Map className="w-3.5 h-3.5 text-emerald-500" />
            {isRtl ? 'خريطة تغطية القرآن' : 'Quran Coverage Map'}
          </div>
          <span className={clsx('text-xs font-bold text-emerald-600 tabular-nums', isRtl && 'font-arabic')}>
            {isRtl ? `${toAr(coveredSet.size)} / ${toAr(114)} سورة` : `${coveredSet.size} / 114 surahs`}
          </span>
        </div>
        <QuranCoverageMap
          covered={coveredSet}
          todaySurah={todayQuestion.surahRef}
          isRtl={isRtl}
        />
        <p className={clsx('text-[11px] text-gray-400 text-center mt-3', isRtl && 'font-arabic')}>
          {isRtl
            ? 'كل إجابة تضيء السورة التي يدور حولها السؤال — اضغط على أي مربع لاستكشاف السورة'
            : 'Each answer lights up the surah it covers — tap any cell to explore that surah'}
        </p>
      </div>

      {/* ── Achievements ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 mb-5">
        <div className={clsx('text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3', isRtl && 'font-arabic')}>
          {isRtl ? 'الإنجازات' : 'Achievements'}
        </div>
        <div className="flex gap-2 flex-wrap">
          {ACHIEVEMENTS.map((ach) => {
            const isUnlocked = ach.unlocked(daily);
            return (
              <div
                key={ach.id}
                title={isRtl ? ach.descAr : ach.descEn}
                className={clsx(
                  'flex flex-col items-center gap-1 p-3 rounded-xl border flex-1 min-w-[56px] transition-all',
                  isUnlocked
                    ? 'bg-amber-50 border-amber-200 shadow-sm'
                    : 'bg-gray-50 border-gray-200 opacity-40 grayscale',
                )}
              >
                <span className="text-2xl">{ach.icon}</span>
                <span className={clsx(
                  'text-[10px] font-semibold text-center leading-tight mt-0.5',
                  isRtl && 'font-arabic',
                  isUnlocked ? 'text-amber-800' : 'text-gray-400',
                )}>
                  {isRtl ? ach.labelAr : ach.labelEn}
                </span>
              </div>
            );
          })}
        </div>
        {ACHIEVEMENTS.every((a) => !a.unlocked(daily)) && (
          <p className={clsx('text-xs text-gray-400 text-center mt-3', isRtl && 'font-arabic')}>
            {isRtl
              ? 'أجب على تحدي اليوم لتفتح أول إنجاز!'
              : 'Answer today\'s challenge to unlock your first achievement!'}
          </p>
        )}
      </div>

      {/* ── Pool info + progress ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm px-5 py-4 mb-2">
        <div className="flex items-center justify-between mb-2">
          <div className={clsx('text-xs font-semibold text-gray-500 uppercase tracking-wide', isRtl && 'font-arabic')}>
            {isRtl ? 'مستواك' : 'Your Progress'}
          </div>
          <div className="flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-primary-400" />
            <span className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
              {isRtl
                ? `${toAr(daily.totalPlayed)} من ${toAr(poolSize)}`
                : `${daily.totalPlayed} of ${poolSize}`}
            </span>
          </div>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden mb-1">
          <div
            className="bg-gradient-to-r from-primary-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, (daily.totalPlayed / poolSize) * 100)}%` }}
          />
        </div>
        <div className={clsx('flex justify-between text-[10px] text-gray-400 mb-4', isRtl && 'font-arabic')}>
          <span>{isRtl ? 'مبتدئ' : 'Beginner'}</span>
          <span>{isRtl ? 'عالم' : 'Scholar'}</span>
        </div>
        <PoolCompositionBar isRtl={isRtl} />
      </div>

      <p className={clsx('text-center text-xs text-gray-400 mt-4', isRtl && 'font-arabic')}>
        {isRtl
          ? `${toAr(poolSize)} سؤال تغطي القرآن كاملاً • سؤال جديد كل يوم`
          : `${poolSize} questions covering the entire Quran · new question every day`}
      </p>
    </div>
  );
}
