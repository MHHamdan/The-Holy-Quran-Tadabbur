/**
 * Quranic Quiz — verified fact-based MCQs + AI-generated questions.
 *
 * Modes:
 *  1. Category Quiz — random session filtered by category
 *  2. By Surah    — static questions indexed to a surah + AI generation
 *
 * Flow: answer → read explanation → click "Next" (no auto-advance).
 * AI questions are grounded in tafsir RAG — no hallucination.
 */

import { useState, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Trophy, RefreshCw, ChevronRight, CheckCircle, XCircle,
  HelpCircle, BookOpen, LayoutGrid, ArrowRight, Sparkles,
  AlertCircle, Loader2, Brain, Zap,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  TRIVIA_QUESTIONS, CATEGORY_META, SURAH_QUESTION_INDEX,
  type TriviaQuestion, type TriviaCategory,
} from '../data/quranicTrivia';
import { SURAH_NAMES } from '../data/surahNames';
import { quizApi, type AIQuizQuestion } from '../lib/api';

const QUESTIONS_PER_SESSION = 10;

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function aiToTrivia(q: AIQuizQuestion): TriviaQuestion {
  const correctIdx = q.options.findIndex((o) => o.isCorrect);
  return {
    id: q.id,
    questionAr: q.question,
    questionEn: q.question,
    options: q.options.map((o) => ({ ar: o.text, en: o.text })),
    correctIndex: correctIdx >= 0 ? correctIdx : 0,
    explanationAr: q.explanation,
    explanationEn: q.explanation,
    surahRef: q.surahRef,
    difficulty: (q.difficulty as 'easy' | 'medium' | 'hard') ?? 'medium',
    category: 'facts' as TriviaCategory,
  };
}

type QuizState = 'selecting' | 'playing' | 'finished';
type SelectMode = 'category' | 'surah';

const OPTION_LETTERS = ['أ', 'ب', 'ج', 'د'];
const OPTION_LETTERS_EN = ['A', 'B', 'C', 'D'];

// ─── Circular progress ring ───────────────────────────────────────────────────

function ScoreRing({ score, total }: { score: number; total: number }) {
  const pct = total > 0 ? (score / total) * 100 : 0;
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 80 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="128" height="128" className="-rotate-90">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="64" cy="64" r={r} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-gray-900">{score}</span>
        <span className="text-xs text-gray-400">/{total}</span>
      </div>
    </div>
  );
}

// ─── Score bar ────────────────────────────────────────────────────────────────

function ScoreBar({ score, total, isRtl }: { score: number; total: number; isRtl: boolean }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const colorClass = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="w-full">
      <div className={clsx('flex justify-between text-xs text-gray-500 mb-1.5', isRtl && 'flex-row-reverse')}>
        <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? 'النتيجة' : 'Score'}</span>
        <span className="font-bold tabular-nums">{score}/{total}</span>
      </div>
      <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-700', colorClass)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Difficulty badge ─────────────────────────────────────────────────────────

function DifficultyBadge({ difficulty, isRtl }: { difficulty: string; isRtl: boolean }) {
  const cfg = {
    easy:   { en: 'Easy',   ar: 'سهل',   cls: 'bg-emerald-100 text-emerald-700' },
    medium: { en: 'Medium', ar: 'متوسط', cls: 'bg-amber-100 text-amber-700' },
    hard:   { en: 'Hard',   ar: 'صعب',   cls: 'bg-red-100 text-red-700' },
  }[difficulty] ?? { en: 'Medium', ar: 'متوسط', cls: 'bg-amber-100 text-amber-700' };

  return (
    <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full font-medium', cfg.cls, isRtl && 'font-arabic')}>
      {isRtl ? cfg.ar : cfg.en}
    </span>
  );
}

// ─── Question card ────────────────────────────────────────────────────────────

function QuestionCard({
  question, questionNumber, total, isRtl, onNext, isAI,
}: {
  question: TriviaQuestion;
  questionNumber: number;
  total: number;
  isRtl: boolean;
  onNext: (chosenIndex: number) => void;
  isAI?: boolean;
}) {
  const [chosen, setChosen] = useState<number | null>(null);
  const answered = chosen !== null;
  const isLast = questionNumber === total;
  const catMeta = CATEGORY_META[question.category];
  const letters = isRtl ? OPTION_LETTERS : OPTION_LETTERS_EN;

  function pick(i: number) {
    if (answered) return;
    setChosen(i);
  }

  return (
    <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">

      {/* Progress strip + meta */}
      <div className="bg-gradient-to-r from-violet-600 to-violet-500 px-5 pt-4 pb-3">
        {/* Step track */}
        <div className="flex gap-1 mb-3">
          {Array.from({ length: total }, (_, i) => (
            <div
              key={i}
              className={clsx(
                'h-1 flex-1 rounded-full transition-all duration-500',
                i < questionNumber - 1 ? 'bg-white/70' :
                i === questionNumber - 1 ? 'bg-white' :
                'bg-white/20'
              )}
            />
          ))}
        </div>

        {/* Top row */}
        <div className={clsx('flex items-center justify-between', isRtl && 'flex-row-reverse')}>
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            {isAI ? (
              <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white font-semibold">
                <Brain className="w-2.5 h-2.5" />
                {isRtl ? 'ذكاء اصطناعي' : 'AI'}
              </span>
            ) : (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white">
                {catMeta.emoji} {isRtl ? catMeta.labelAr : catMeta.labelEn}
              </span>
            )}
            <DifficultyBadge difficulty={question.difficulty} isRtl={isRtl} />
          </div>
          <span className="text-[11px] text-white/80 font-medium tabular-nums">
            {isRtl ? `${questionNumber} / ${total}` : `${questionNumber} / ${total}`}
          </span>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Question number + text */}
        <div className={clsx('flex gap-3', isRtl && 'flex-row-reverse')}>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center">
            <span className="text-xs font-bold text-violet-700">{questionNumber}</span>
          </div>
          <p
            className={clsx('text-base font-semibold text-gray-900 leading-relaxed pt-1 flex-1', isRtl && 'font-arabic text-right')}
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            {isRtl ? question.questionAr : question.questionEn}
          </p>
        </div>

        {/* Surah chip */}
        {question.surahRef && (
          <div className={clsx('flex', isRtl ? 'justify-end' : 'justify-start')}>
            <Link
              to={`/quran/${question.surahRef}`}
              onClick={(e) => e.stopPropagation()}
              className={clsx(
                'inline-flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100 hover:bg-emerald-100 transition-colors',
                isRtl && 'flex-row-reverse font-arabic'
              )}
            >
              <BookOpen className="w-3 h-3" />
              {isRtl
                ? `سورة ${SURAH_NAMES[question.surahRef - 1]?.ar ?? question.surahRef}`
                : `Surah ${SURAH_NAMES[question.surahRef - 1]?.en ?? question.surahRef}`}
            </Link>
          </div>
        )}

        {/* Options */}
        <div className="space-y-2">
          {question.options.map((opt, i) => {
            const isCorrect = i === question.correctIndex;
            const isChosen = chosen === i;
            const showCorrect = answered && isCorrect;
            const showWrong = answered && isChosen && !isCorrect;
            const isDimmed = answered && !isCorrect && !isChosen;

            return (
              <button
                key={i}
                onClick={() => pick(i)}
                disabled={answered}
                dir={isRtl ? 'rtl' : 'ltr'}
                className={clsx(
                  'w-full flex items-center gap-3 rounded-2xl border-2 px-4 py-3 text-sm font-medium transition-all duration-200',
                  isRtl && 'flex-row-reverse text-right',
                  !answered && 'border-gray-100 hover:border-violet-300 hover:bg-violet-50 hover:shadow-sm active:scale-[0.99] cursor-pointer',
                  showCorrect && 'border-emerald-400 bg-emerald-50 text-emerald-800 shadow-sm',
                  showWrong && 'border-red-400 bg-red-50 text-red-700',
                  isDimmed && 'border-gray-100 bg-gray-50 text-gray-400 opacity-60',
                )}
              >
                {/* Letter indicator */}
                <span className={clsx(
                  'w-7 h-7 flex-shrink-0 inline-flex items-center justify-center rounded-full text-xs font-bold transition-all',
                  !answered && 'border-2 border-gray-200 text-gray-500',
                  showCorrect && 'bg-emerald-500 text-white border-emerald-500',
                  showWrong && 'bg-red-500 text-white border-red-500',
                  isDimmed && 'border-2 border-gray-100 text-gray-300',
                )}>
                  {showCorrect ? <CheckCircle className="w-4 h-4" /> :
                   showWrong  ? <XCircle className="w-4 h-4" /> :
                   letters[i]}
                </span>

                <span className={clsx('flex-1', isRtl && 'font-arabic')}>{isRtl ? opt.ar : opt.en}</span>
              </button>
            );
          })}
        </div>

        {/* Explanation + Next */}
        {answered && (
          <div className="space-y-3 pt-1">
            <div className={clsx(
              'rounded-2xl p-4 border',
              chosen === question.correctIndex
                ? 'bg-emerald-50 border-emerald-100'
                : 'bg-violet-50 border-violet-100'
            )}>
              <div className={clsx('flex items-start gap-2 mb-1.5', isRtl && 'flex-row-reverse')}>
                <HelpCircle className={clsx(
                  'w-4 h-4 flex-shrink-0 mt-0.5',
                  chosen === question.correctIndex ? 'text-emerald-600' : 'text-violet-500'
                )} />
                <span className={clsx(
                  'text-xs font-semibold',
                  chosen === question.correctIndex ? 'text-emerald-700' : 'text-violet-700',
                  isRtl && 'font-arabic'
                )}>
                  {isRtl ? 'التفسير' : 'Explanation'}
                </span>
              </div>
              <p
                className={clsx(
                  'text-xs leading-relaxed',
                  chosen === question.correctIndex ? 'text-emerald-800' : 'text-violet-800',
                  isRtl && 'font-arabic text-right'
                )}
                dir={isRtl ? 'rtl' : 'ltr'}
              >
                {isRtl ? question.explanationAr : question.explanationEn}
              </p>
            </div>

            <button
              onClick={() => onNext(chosen!)}
              className={clsx(
                'w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-sm transition-all active:scale-[0.98] shadow-sm',
                chosen === question.correctIndex
                  ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                  : 'bg-violet-600 hover:bg-violet-700 text-white',
                isRtl && 'flex-row-reverse'
              )}
            >
              {isLast ? (isRtl ? 'عرض النتائج' : 'View Results') : (isRtl ? 'السؤال التالي' : 'Next Question')}
              <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Results screen ───────────────────────────────────────────────────────────

function ResultsScreen({
  score, total, isRtl, onRestart, activeSurah, onGenerateAI,
}: {
  score: number;
  total: number;
  isRtl: boolean;
  onRestart: () => void;
  activeSurah: number | null;
  onGenerateAI?: (surah: number) => void;
}) {
  const pct = Math.round((score / total) * 100);
  const tier =
    pct >= 90 ? { emoji: '🏆', en: "Excellent! Masha'Allah!", ar: 'ممتاز! ماشاء الله!', color: 'text-emerald-600' } :
    pct >= 70 ? { emoji: '⭐', en: 'Very good!', ar: 'جيد جداً!', color: 'text-amber-500' } :
    pct >= 50 ? { emoji: '👍', en: 'Good effort!', ar: 'جهد رائع!', color: 'text-blue-500' } :
                { emoji: '📖', en: 'Keep learning!', ar: 'استمر في التعلم!', color: 'text-violet-500' };

  return (
    <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header band */}
      <div className="bg-gradient-to-r from-violet-600 to-violet-500 px-6 py-5 text-center">
        <p className={clsx('text-white/80 text-sm font-medium', isRtl && 'font-arabic')}>
          {isRtl ? 'انتهى الاختبار' : 'Quiz Complete'}
        </p>
      </div>

      <div className="px-6 py-8 text-center space-y-5">
        {/* Score ring */}
        <div className="flex flex-col items-center gap-3">
          <ScoreRing score={score} total={total} />
          <div>
            <span className="text-4xl">{tier.emoji}</span>
            <h2 className={clsx('text-xl font-bold mt-1', tier.color, isRtl && 'font-arabic')}>
              {isRtl ? tier.ar : tier.en}
            </h2>
            <p className={clsx('text-sm text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
              {isRtl ? `أصبت ${pct}% من الأسئلة` : `${pct}% correct`}
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: isRtl ? 'صحيح' : 'Correct',   value: score,         color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: isRtl ? 'خطأ' : 'Wrong',       value: total - score, color: 'text-red-500',     bg: 'bg-red-50'     },
            { label: isRtl ? 'النسبة' : 'Score',    value: `${pct}%`,     color: 'text-violet-600',  bg: 'bg-violet-50'  },
          ].map((s) => (
            <div key={s.label} className={clsx('rounded-2xl py-3', s.bg)}>
              <p className={clsx('text-xl font-bold', s.color)}>{s.value}</p>
              <p className={clsx('text-[10px] text-gray-500 mt-0.5', isRtl && 'font-arabic')}>{s.label}</p>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-2.5 pt-1">
          <button
            onClick={onRestart}
            className={clsx(
              'flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-violet-600 text-white text-sm font-semibold hover:bg-violet-700 transition-colors shadow-sm',
              isRtl && 'flex-row-reverse'
            )}
          >
            <RefreshCw className="w-4 h-4" />
            {isRtl ? 'العب مجدداً' : 'Play Again'}
          </button>
          {activeSurah && onGenerateAI && (
            <button
              onClick={() => onGenerateAI(activeSurah)}
              className={clsx(
                'flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-violet-50 text-violet-700 text-sm font-semibold hover:bg-violet-100 transition-colors border border-violet-200',
                isRtl && 'flex-row-reverse'
              )}
            >
              <Sparkles className="w-4 h-4" />
              {isRtl ? 'أسئلة بالذكاء الاصطناعي' : 'AI Questions'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Surah grid ───────────────────────────────────────────────────────────────

function SurahGrid({ onSelect, onAISelect, isRtl }: {
  onSelect: (surah: number) => void;
  onAISelect: (surah: number) => void;
  isRtl: boolean;
}) {
  return (
    <div className="space-y-3">
      {/* Legend */}
      <div className={clsx('flex items-center gap-4 text-[10px] text-gray-400', isRtl ? 'flex-row-reverse justify-end font-arabic' : '')}>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block" />{isRtl ? 'أسئلة ثابتة' : 'Static questions'}</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-violet-400 inline-block" />{isRtl ? 'بالذكاء الاصطناعي' : 'AI-generated'}</span>
      </div>

      <div className="grid grid-cols-5 sm:grid-cols-7 gap-1.5">
        {SURAH_NAMES.map((s, i) => {
          const num = i + 1;
          const count = SURAH_QUESTION_INDEX[num]?.length ?? 0;
          const hasQ = count > 0;
          return (
            <button
              key={num}
              onClick={() => hasQ ? onSelect(num) : onAISelect(num)}
              title={`${num}. ${isRtl ? s.ar : s.en}`}
              className={clsx(
                'relative flex flex-col items-center justify-center rounded-xl p-1.5 text-center transition-all duration-150',
                hasQ
                  ? 'bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 hover:border-emerald-400 hover:shadow-sm active:scale-95'
                  : 'bg-white border border-gray-100 hover:bg-violet-50 hover:border-violet-200 hover:shadow-sm active:scale-95 opacity-75 hover:opacity-100'
              )}
            >
              <span className={clsx('text-[9px] font-bold leading-none', hasQ ? 'text-emerald-700' : 'text-gray-400')}>
                {num}
              </span>
              <span className={clsx('text-[8px] leading-tight truncate w-full text-center mt-0.5 font-arabic', hasQ ? 'text-emerald-800' : 'text-gray-300')}>
                {s.ar}
              </span>
              {/* Badge */}
              <span className={clsx(
                'absolute -top-1.5 -right-1.5 w-3.5 h-3.5 flex items-center justify-center rounded-full text-white text-[6px] font-bold leading-none',
                hasQ ? 'bg-emerald-500' : 'bg-violet-400'
              )}>
                {hasQ ? count : '✦'}
              </span>
            </button>
          );
        })}
      </div>

      <p className={clsx('text-[10px] text-gray-400 text-center', isRtl && 'font-arabic')}>
        {isRtl
          ? `${Object.keys(SURAH_QUESTION_INDEX).length} سورة بأسئلة ثابتة — باقي السور بالذكاء الاصطناعي`
          : `${Object.keys(SURAH_QUESTION_INDEX).length} surahs with static questions — all others via AI`}
      </p>
    </div>
  );
}

// ─── AI Generator Panel ───────────────────────────────────────────────────────

function AIGeneratorPanel({ initialSurah, isRtl, onGenerated, onCancel }: {
  initialSurah: number;
  isRtl: boolean;
  onGenerated: (questions: TriviaQuestion[], surah: number) => void;
  onCancel: () => void;
}) {
  const [surah, setSurah] = useState(initialSurah);
  const [count, setCount] = useState(3);
  const { language } = useLanguageStore();
  const lang = language as 'ar' | 'en';

  const mutation = useMutation({
    mutationFn: () => quizApi.generateQuestions(surah, count, lang),
    onSuccess: (data) => {
      const triviaQs = data.questions.map(aiToTrivia);
      if (triviaQs.length > 0) onGenerated(triviaQs, surah);
    },
  });

  const surahName = isRtl ? SURAH_NAMES[surah - 1]?.ar : SURAH_NAMES[surah - 1]?.en;

  return (
    <div className="rounded-3xl overflow-hidden border border-violet-200 shadow-sm">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-violet-500 px-5 py-4">
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div className={isRtl ? 'text-right' : ''}>
            <h3 className={clsx('font-bold text-white text-sm', isRtl && 'font-arabic')}>
              {isRtl ? 'أسئلة بالذكاء الاصطناعي' : 'AI-Generated Questions'}
            </h3>
            <p className={clsx('text-[10px] text-white/70 mt-0.5', isRtl && 'font-arabic')}>
              {isRtl ? 'مستندة إلى التفسير — لا توليد عشوائي' : 'Grounded in tafsir — not hallucinated'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-violet-50 px-5 py-4 space-y-4">
        {/* Controls */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={clsx('block text-[10px] text-violet-600 mb-1.5 font-semibold uppercase tracking-wide', isRtl && 'text-right font-arabic')}>
              {isRtl ? 'السورة' : 'Surah'}
            </label>
            <select
              value={surah}
              onChange={(e) => setSurah(Number(e.target.value))}
              dir={isRtl ? 'rtl' : 'ltr'}
              className="w-full text-xs rounded-xl border border-violet-200 bg-white px-3 py-2.5 focus:outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100 shadow-sm"
            >
              {SURAH_NAMES.map((s, i) => (
                <option key={i + 1} value={i + 1}>{i + 1}. {isRtl ? s.ar : s.en}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={clsx('block text-[10px] text-violet-600 mb-1.5 font-semibold uppercase tracking-wide', isRtl && 'text-right font-arabic')}>
              {isRtl ? 'العدد' : 'Count'}
            </label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  onClick={() => setCount(n)}
                  className={clsx(
                    'flex-1 py-2 rounded-xl text-xs font-bold transition-all',
                    count === n
                      ? 'bg-violet-600 text-white shadow-sm'
                      : 'bg-white border border-violet-200 text-violet-500 hover:border-violet-400'
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Selected surah preview */}
        <div className={clsx('flex items-center gap-2 text-xs text-violet-700 bg-white rounded-xl px-3 py-2 border border-violet-100', isRtl && 'flex-row-reverse')}>
          <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={isRtl ? 'font-arabic' : ''}>
            {isRtl ? `سورة ${surahName}` : `Surah ${surahName}`}
          </span>
          <span className="ms-auto text-violet-400">→ {count} {isRtl ? 'أسئلة' : 'questions'}</span>
        </div>

        {/* Error */}
        {mutation.isError && (
          <div className={clsx('flex items-center gap-2 text-xs text-red-600 bg-red-50 rounded-xl px-3 py-2.5 border border-red-100', isRtl && 'flex-row-reverse')}>
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span className={isRtl ? 'font-arabic' : ''}>
              {isRtl ? 'فشل التوليد — يُرجى المحاولة مجدداً' : 'Generation failed — please try again'}
            </span>
          </div>
        )}

        {/* Buttons */}
        <div className={clsx('flex gap-2', isRtl && 'flex-row-reverse')}>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl text-sm font-bold transition-all shadow-sm active:scale-[0.98]',
              mutation.isPending
                ? 'bg-violet-300 text-violet-100 cursor-not-allowed'
                : 'bg-violet-600 text-white hover:bg-violet-700',
              isRtl && 'flex-row-reverse'
            )}
          >
            {mutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /><span className={isRtl ? 'font-arabic' : ''}>{isRtl ? 'جارٍ التوليد...' : 'Generating...'}</span></>
            ) : (
              <><Zap className="w-4 h-4" /><span className={isRtl ? 'font-arabic' : ''}>{isRtl ? 'ولِّد الأسئلة' : 'Generate'}</span></>
            )}
          </button>
          <button
            onClick={onCancel}
            disabled={mutation.isPending}
            className="px-4 py-3 rounded-2xl border border-violet-200 bg-white text-violet-600 text-sm font-medium hover:bg-violet-50 transition-colors"
          >
            {isRtl ? 'إلغاء' : 'Cancel'}
          </button>
        </div>

        <p className={clsx('text-[9px] text-violet-400 text-center flex items-center justify-center gap-1', isRtl && 'flex-row-reverse font-arabic')}>
          <Zap className="w-2.5 h-2.5" />
          {isRtl ? 'قد يستغرق التوليد 10-30 ثانية' : 'Generation may take 10–30 seconds'}
        </p>
      </div>
    </div>
  );
}

// ─── Hero header ──────────────────────────────────────────────────────────────

function QuizHero({ isRtl, totalQ }: { isRtl: boolean; totalQ: number }) {
  return (
    <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-violet-700 via-violet-600 to-indigo-600 px-6 py-7 mb-6 shadow-md">
      {/* Decorative circles */}
      <div className="absolute -top-6 -right-6 w-28 h-28 rounded-full bg-white/5" />
      <div className="absolute -bottom-8 -left-4 w-36 h-36 rounded-full bg-white/5" />

      <div className={clsx('relative flex items-center gap-4', isRtl && 'flex-row-reverse')}>
        <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center flex-shrink-0 shadow-inner">
          <Trophy className="w-7 h-7 text-amber-300" />
        </div>
        <div className={isRtl ? 'text-right' : ''}>
          <h1 className={clsx('text-2xl font-bold text-white', isRtl && 'font-arabic')}>
            {isRtl ? 'اختبار قرآني' : 'Quranic Quiz'}
          </h1>
          <p className={clsx('text-sm text-white/70 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? `${totalQ} سؤالاً موثقاً · أسئلة ذكاء اصطناعي لكل سورة`
              : `${totalQ} verified questions · AI generation for any surah`}
          </p>
        </div>
      </div>

      {/* Stat pills */}
      <div className={clsx('relative flex gap-2 mt-5 flex-wrap', isRtl && 'flex-row-reverse')}>
        {[
          { icon: '📐', label: isRtl ? '6 فئات' : '6 Categories' },
          { icon: '🕌', label: isRtl ? '114 سورة' : '114 Surahs' },
          { icon: '🤖', label: isRtl ? 'مدعوم بالذكاء الاصطناعي' : 'AI-Powered' },
        ].map((p) => (
          <span key={p.label} className={clsx('inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 text-white text-[11px] font-medium', isRtl && 'font-arabic flex-row-reverse')}>
            <span>{p.icon}</span>
            {p.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function QuizPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [state, setState] = useState<QuizState>('selecting');
  const [selectMode, setSelectMode] = useState<SelectMode>('category');
  const [catFilter, setCatFilter] = useState<TriviaCategory | 'all'>('all');
  const [activeSurah, setActiveSurah] = useState<number | null>(null);
  const [questions, setQuestions] = useState<TriviaQuestion[]>([]);
  const [current, setCurrent] = useState(0);
  const [score, setScore] = useState(0);
  const [isAISession, setIsAISession] = useState(false);
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [aiTargetSurah, setAITargetSurah] = useState(1);

  const cats = Object.keys(CATEGORY_META) as TriviaCategory[];

  const categoryPool = useMemo(() => {
    let all = [...TRIVIA_QUESTIONS];
    if (catFilter !== 'all') all = all.filter(q => q.category === catFilter);
    return all;
  }, [catFilter]);

  function startCategoryQuiz() {
    setQuestions(shuffle(categoryPool).slice(0, QUESTIONS_PER_SESSION));
    setCurrent(0); setScore(0); setActiveSurah(null);
    setIsAISession(false); setShowAIPanel(false); setState('playing');
  }

  function startSurahQuiz(surahNum: number) {
    const qs = shuffle([...(SURAH_QUESTION_INDEX[surahNum] ?? [])]);
    if (!qs.length) return;
    setQuestions(qs); setCurrent(0); setScore(0); setActiveSurah(surahNum);
    setIsAISession(false); setShowAIPanel(false); setState('playing');
  }

  function startAIQuiz(aiQuestions: TriviaQuestion[], surahNum: number) {
    setQuestions(aiQuestions); setCurrent(0); setScore(0); setActiveSurah(surahNum);
    setIsAISession(true); setShowAIPanel(false); setState('playing');
  }

  function handleAISelect(surahNum: number) {
    setAITargetSurah(surahNum); setShowAIPanel(true);
  }

  function handleNext(chosenIndex: number) {
    if (chosenIndex === questions[current].correctIndex) setScore(s => s + 1);
    current + 1 >= questions.length ? setState('finished') : setCurrent(c => c + 1);
  }

  function triggerAIFromResults(surahNum: number) {
    setAITargetSurah(surahNum); setShowAIPanel(true);
    setState('selecting'); setSelectMode('surah');
  }

  const surahName = activeSurah
    ? (isRtl ? SURAH_NAMES[activeSurah - 1]?.ar : SURAH_NAMES[activeSurah - 1]?.en)
    : null;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>

      {/* ── SELECTING ── */}
      {state === 'selecting' && (
        <>
          <QuizHero isRtl={isRtl} totalQ={TRIVIA_QUESTIONS.length} />

          <div className="space-y-5">
            {/* Mode tabs */}
            <div className="flex rounded-2xl border border-gray-200 bg-gray-50 p-1 gap-1">
              {([
                { key: 'category', labelEn: 'By Category', labelAr: 'حسب الفئة', Icon: LayoutGrid },
                { key: 'surah',    labelEn: 'By Surah',    labelAr: 'حسب السورة', Icon: BookOpen  },
              ] as const).map(({ key, labelEn, labelAr, Icon }) => (
                <button
                  key={key}
                  onClick={() => { setSelectMode(key); setShowAIPanel(false); }}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition-all',
                    selectMode === key
                      ? 'bg-white shadow text-violet-700'
                      : 'text-gray-400 hover:text-gray-600'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className={isRtl ? 'font-arabic' : ''}>{isRtl ? labelAr : labelEn}</span>
                </button>
              ))}
            </div>

            {/* ── Category mode ── */}
            {selectMode === 'category' && (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {([
                    ['all', { labelEn: 'All', labelAr: 'الكل', emoji: '🎯' }],
                    ...cats.map(c => [c, CATEGORY_META[c]] as const),
                  ] as [string, { labelEn: string; labelAr: string; emoji: string }][]).map(([cat, meta]) => (
                    <button
                      key={cat}
                      onClick={() => setCatFilter(cat as TriviaCategory | 'all')}
                      className={clsx(
                        'flex flex-col items-center gap-1.5 py-3 px-2 rounded-2xl border-2 text-center transition-all',
                        catFilter === cat
                          ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
                          : 'bg-white text-gray-600 border-gray-100 hover:border-violet-200 hover:bg-violet-50'
                      )}
                    >
                      <span className="text-2xl">{meta.emoji}</span>
                      <span className={clsx('text-xs font-semibold leading-tight', isRtl && 'font-arabic')}>
                        {isRtl ? meta.labelAr : meta.labelEn}
                      </span>
                    </button>
                  ))}
                </div>

                {/* How to play */}
                <div className="bg-violet-50 rounded-2xl border border-violet-100 p-4">
                  <div className={clsx('flex items-center gap-2 mb-2', isRtl && 'flex-row-reverse')}>
                    <HelpCircle className="w-4 h-4 text-violet-500" />
                    <span className={clsx('text-sm font-semibold text-violet-800', isRtl && 'font-arabic')}>
                      {isRtl ? 'كيف تلعب' : 'How to play'}
                    </span>
                  </div>
                  <ul className={clsx('text-xs text-violet-700 space-y-1.5', isRtl && 'font-arabic text-right')}>
                    <li>• {isRtl ? `${Math.min(QUESTIONS_PER_SESSION, categoryPool.length)} أسئلة عشوائية` : `${Math.min(QUESTIONS_PER_SESSION, categoryPool.length)} random questions`}</li>
                    <li>• {isRtl ? 'اختر الإجابة ثم اضغط "السؤال التالي"' : 'Pick an answer, then tap "Next Question"'}</li>
                    <li>• {isRtl ? 'كل الأسئلة من مصادر علمية موثقة' : 'All questions from verified scholarly sources'}</li>
                  </ul>
                </div>

                <button
                  onClick={startCategoryQuiz}
                  disabled={categoryPool.length === 0}
                  className={clsx(
                    'w-full flex items-center justify-center gap-2 py-4 rounded-2xl text-base font-bold transition-all shadow-sm active:scale-[0.98]',
                    categoryPool.length > 0
                      ? 'bg-violet-600 text-white hover:bg-violet-700'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed',
                    isRtl && 'flex-row-reverse'
                  )}
                >
                  {isRtl ? 'ابدأ الاختبار' : 'Start Quiz'}
                  <ChevronRight className={clsx('w-5 h-5', isRtl && 'rotate-180')} />
                </button>
              </>
            )}

            {/* ── Surah mode ── */}
            {selectMode === 'surah' && !showAIPanel && (
              <SurahGrid onSelect={startSurahQuiz} onAISelect={handleAISelect} isRtl={isRtl} />
            )}

            {/* ── AI Panel ── */}
            {selectMode === 'surah' && showAIPanel && (
              <AIGeneratorPanel
                initialSurah={aiTargetSurah}
                isRtl={isRtl}
                onGenerated={(qs, s) => startAIQuiz(qs, s)}
                onCancel={() => setShowAIPanel(false)}
              />
            )}
          </div>
        </>
      )}

      {/* ── PLAYING ── */}
      {state === 'playing' && questions[current] && (
        <div className="space-y-4">
          {/* Session banner */}
          {activeSurah && surahName && (
            <div className={clsx(
              'flex items-center gap-2 px-4 py-2.5 rounded-2xl text-sm font-medium',
              isAISession
                ? 'bg-violet-50 text-violet-700 border border-violet-100'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-100',
              isRtl && 'flex-row-reverse'
            )}>
              {isAISession ? <Brain className="w-4 h-4 flex-shrink-0" /> : <BookOpen className="w-4 h-4 flex-shrink-0" />}
              <span className={isRtl ? 'font-arabic' : ''}>
                {isRtl
                  ? `${isAISession ? 'أسئلة ذكاء اصطناعي — سورة' : 'أسئلة سورة'} ${surahName}`
                  : `${isAISession ? 'AI — Surah' : 'Surah'} ${surahName}`}
              </span>
              <Link
                to={`/quran/${activeSurah}`}
                className={clsx('ms-auto flex items-center gap-1 text-xs opacity-60 hover:opacity-100 transition-opacity', isRtl && 'flex-row-reverse')}
              >
                {isRtl ? 'اقرأ' : 'Read'}
                <ArrowRight className={clsx('w-3 h-3', isRtl && 'rotate-180')} />
              </Link>
            </div>
          )}

          <ScoreBar score={score} total={current} isRtl={isRtl} />

          <QuestionCard
            key={current}
            question={questions[current]}
            questionNumber={current + 1}
            total={questions.length}
            isRtl={isRtl}
            onNext={handleNext}
            isAI={isAISession}
          />
        </div>
      )}

      {/* ── FINISHED ── */}
      {state === 'finished' && (
        <ResultsScreen
          score={score}
          total={questions.length}
          isRtl={isRtl}
          onRestart={() => setState('selecting')}
          activeSurah={activeSurah}
          onGenerateAI={triggerAIFromResults}
        />
      )}

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl ? 'جميع الإجابات موثقة من المصادر الإسلامية الكلاسيكية' : 'All answers verified from classical Islamic scholarship'}
      </p>
    </div>
  );
}
