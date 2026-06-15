/**
 * Daily Quranic Challenge
 *
 * Picks one question per day (date-seeded) from all kidsQuiz entries across
 * QURAN_STORIES_FIRST_BATCH. Tracks daily answers and streak in localStorage.
 */

import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Flame, CheckCircle2, XCircle, ChevronRight, Trophy, BookOpen } from 'lucide-react';
import { QURAN_STORIES_FIRST_BATCH } from '../data/quranStories';
import { useLanguageStore } from '../stores/languageStore';
import clsx from 'clsx';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChallengeQuestion {
  questionId: string;
  storyTitleEn: string;
  storyTitleAr: string;
  questionArabic: string;
  questionEnglish: string;
  optionsArabic: string[];
  optionsEnglish: string[];
  correctOptionIndex: number;
  explanationArabic: string;
  explanationEnglish: string;
}

interface DailyState {
  date: string;          // YYYY-MM-DD
  questionId: string;
  answeredIndex: number | null;  // null = unanswered
  streak: number;
  longestStreak: number;
}

const STORAGE_KEY = 'tadabbur_daily_challenge_v1';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function yesterdayStr(): string {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

function dateHash(dateStr: string): number {
  // Simple djb2-like hash of the date string for deterministic picking
  let h = 5381;
  for (let i = 0; i < dateStr.length; i++) {
    h = ((h << 5) + h + dateStr.charCodeAt(i)) >>> 0;
  }
  return h;
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

// ─── Collect all questions ─────────────────────────────────────────────────────

function getAllQuestions(): ChallengeQuestion[] {
  const out: ChallengeQuestion[] = [];
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    if (!story.kidsQuiz) continue;
    for (const q of story.kidsQuiz) {
      out.push({
        questionId: q.questionId,
        storyTitleEn: story.titleEnglish,
        storyTitleAr: story.titleArabic,
        questionArabic: q.questionArabic,
        questionEnglish: q.questionEnglish,
        optionsArabic: q.optionsArabic,
        optionsEnglish: q.optionsEnglish,
        correctOptionIndex: q.correctOptionIndex,
        explanationArabic: q.explanationArabic,
        explanationEnglish: q.explanationEnglish,
      });
    }
  }
  return out;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function DailyChallengePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const allQuestions = useMemo(() => getAllQuestions(), []);

  // Pick today's question deterministically
  const today = todayStr();
  const todayQuestion = useMemo<ChallengeQuestion>(() => {
    const idx = dateHash(today) % allQuestions.length;
    return allQuestions[idx];
  }, [today, allQuestions]);

  // Load / init daily state
  const [daily, setDaily] = useState<DailyState>(() => {
    const saved = loadState();
    if (saved && saved.date === today && saved.questionId === todayQuestion.questionId) {
      return saved;
    }
    // Carry forward streak only if yesterday was answered (any answer continues the chain)
    const prevStreak = saved && saved.date === yesterdayStr() && saved.answeredIndex !== null
      ? saved.streak
      : 0;
    return {
      date: today,
      questionId: todayQuestion.questionId,
      answeredIndex: null,
      streak: prevStreak,
      longestStreak: saved?.longestStreak ?? 0,
    };
  });

  const [selected, setSelected] = useState<number | null>(daily.answeredIndex);
  const answered = selected !== null;
  const isCorrect = answered && selected === todayQuestion.correctOptionIndex;

  const handleSelect = useCallback((idx: number) => {
    if (answered) return;
    const correct = idx === todayQuestion.correctOptionIndex;
    const newStreak = correct ? daily.streak + 1 : 0;
    const newLongest = Math.max(newStreak, daily.longestStreak);
    const next: DailyState = {
      ...daily,
      answeredIndex: idx,
      streak: newStreak,
      longestStreak: newLongest,
    };
    setSelected(idx);
    setDaily(next);
    saveState(next);
  }, [answered, daily, todayQuestion.correctOptionIndex]);

  const options = isRtl ? todayQuestion.optionsArabic : todayQuestion.optionsEnglish;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center">
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

        {/* Streak bar */}
        <div className="flex items-center gap-3 mt-3 bg-orange-50 border border-orange-100 rounded-xl px-4 py-3">
          <Flame className="w-5 h-5 text-orange-500 flex-shrink-0" />
          <div className="flex-1">
            <div className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
              {isRtl
                ? `${toAr(daily.streak)} يوم متواصل`
                : `${daily.streak}-day streak`}
            </div>
            <div className={clsx('text-xs text-gray-500', isRtl && 'font-arabic')}>
              {isRtl
                ? `أعلى سلسلة: ${toAr(daily.longestStreak)} يوم`
                : `Best: ${daily.longestStreak} days`}
            </div>
          </div>
          <Trophy className="w-4 h-4 text-amber-400" />
        </div>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-4">
        {/* Story label */}
        <div className={clsx(
          'px-5 py-2.5 text-xs font-medium bg-primary-50 text-primary-700 border-b border-primary-100 flex items-center gap-2',
          isRtl && 'font-arabic'
        )}>
          <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
          {isRtl ? todayQuestion.storyTitleAr : todayQuestion.storyTitleEn}
        </div>

        {/* Question */}
        <div className="px-5 py-5">
          <p className={clsx('text-base font-semibold text-gray-800 leading-relaxed mb-5', isRtl && 'font-arabic')}>
            {isRtl ? todayQuestion.questionArabic : todayQuestion.questionEnglish}
          </p>

          {/* Options */}
          <div className="space-y-2.5">
            {options.map((opt, i) => {
              let stateClass = 'border-gray-200 hover:border-primary-300 hover:bg-primary-50 cursor-pointer';
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
                    stateClass
                  )}
                >
                  <span className={clsx(
                    'w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold flex-shrink-0',
                    answered && i === todayQuestion.correctOptionIndex
                      ? 'border-emerald-500 bg-emerald-500 text-white'
                      : answered && i === selected
                        ? 'border-red-500 bg-red-500 text-white'
                        : 'border-gray-300 text-gray-500'
                  )}>
                    {answered
                      ? i === todayQuestion.correctOptionIndex
                        ? <CheckCircle2 className="w-4 h-4" />
                        : i === selected
                          ? <XCircle className="w-4 h-4" />
                          : ['أ', 'ب', 'ج', 'د'][i]
                      : isRtl
                        ? ['أ', 'ب', 'ج', 'د'][i]
                        : String.fromCharCode(65 + i)
                    }
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
            isCorrect ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'
          )}>
            <div className={clsx(
              'flex items-center gap-2 font-semibold text-sm mb-2',
              isCorrect ? 'text-emerald-700' : 'text-red-700'
            )}>
              {isCorrect
                ? <><CheckCircle2 className="w-4 h-4" /><span className={clsx(isRtl && 'font-arabic')}>{isRtl ? 'أحسنت! إجابة صحيحة' : 'Correct!'}</span></>
                : <><XCircle className="w-4 h-4" /><span className={clsx(isRtl && 'font-arabic')}>{isRtl ? 'إجابة خاطئة' : 'Incorrect'}</span></>
              }
            </div>
            <p className={clsx('text-sm text-gray-700 leading-relaxed', isRtl && 'font-arabic')}>
              {isRtl ? todayQuestion.explanationArabic : todayQuestion.explanationEnglish}
            </p>
          </div>
        )}
      </div>

      {/* CTA after answering */}
      {answered && (
        <div className="flex flex-col sm:flex-row gap-3">
          <div className={clsx(
            'flex-1 text-center text-sm rounded-xl py-3 px-4',
            isCorrect ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800',
            isRtl && 'font-arabic'
          )}>
            {isRtl
              ? 'تعال غداً لتحدي جديد 🌙'
              : 'Come back tomorrow for a new challenge 🌙'}
          </div>
          <Link
            to="/stories"
            className="flex items-center justify-center gap-2 px-5 py-3 bg-primary-700 text-white text-sm rounded-xl hover:bg-primary-800 transition-colors font-medium"
          >
            {isRtl ? 'استكشف القصص' : 'Explore Stories'}
            <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          </Link>
        </div>
      )}

      {/* Question counter */}
      <p className="text-center text-xs text-gray-400 mt-6">
        {isRtl
          ? `${toAr(allQuestions.length)} سؤال في المجموعة`
          : `${allQuestions.length} questions in the pool`}
      </p>
    </div>
  );
}

function toAr(n: number): string {
  return n.toString().replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[+d]);
}
