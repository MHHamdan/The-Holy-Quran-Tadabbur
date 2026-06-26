/**
 * Quranic Quiz — verified fact-based multiple choice questions.
 *
 * Two modes:
 *  1. Category Quiz — random session filtered by category
 *  2. By Surah    — all questions indexed to a specific surah
 *
 * Flow change: answer → read explanation → click "Next" (no auto-advance).
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Trophy, RefreshCw, ChevronRight, CheckCircle, XCircle,
  HelpCircle, BookOpen, LayoutGrid, ArrowRight,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  TRIVIA_QUESTIONS, CATEGORY_META, SURAH_QUESTION_INDEX,
  type TriviaQuestion, type TriviaCategory,
} from '../data/quranicTrivia';
import { SURAH_NAMES } from '../data/surahNames';

const QUESTIONS_PER_SESSION = 10;

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

type QuizState = 'selecting' | 'playing' | 'finished';
type SelectMode = 'category' | 'surah';

// ─── Score bar ────────────────────────────────────────────────────────────────

function ScoreBar({ score, total, isRtl }: { score: number; total: number; isRtl: boolean }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const colorClass = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="w-full">
      <div className={clsx('flex justify-between text-xs text-gray-500 mb-1', isRtl && 'flex-row-reverse')}>
        <span>{isRtl ? 'النتيجة' : 'Score'}</span>
        <span className="font-bold">{score}/{total}</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all duration-500', colorClass)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ─── Question card — waits for explicit "Next" click ─────────────────────────

function QuestionCard({
  question, questionNumber, total, isRtl, onNext,
}: {
  question: TriviaQuestion;
  questionNumber: number;
  total: number;
  isRtl: boolean;
  onNext: (chosenIndex: number) => void;
}) {
  const [chosen, setChosen] = useState<number | null>(null);
  const answered = chosen !== null;
  const isLast = questionNumber === total;
  const catMeta = CATEGORY_META[question.category];

  function pick(i: number) {
    if (answered) return;
    setChosen(i);
    // No auto-advance — user must click "Next" to proceed
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4">
      {/* Meta row */}
      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-700">
          {catMeta.emoji} {isRtl ? catMeta.labelAr : catMeta.labelEn}
        </span>
        {question.surahRef && (
          <Link
            to={`/quran/${question.surahRef}`}
            className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 hover:bg-emerald-100 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            {isRtl ? `سورة ${SURAH_NAMES[question.surahRef - 1]?.ar ?? question.surahRef}` : `Surah ${SURAH_NAMES[question.surahRef - 1]?.en ?? question.surahRef}`}
          </Link>
        )}
        <span className="text-[10px] text-gray-400 ms-auto">
          {isRtl ? `${questionNumber} من ${total}` : `${questionNumber} of ${total}`}
        </span>
      </div>

      {/* Progress dots */}
      <div className="flex gap-1">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={clsx(
              'h-1 flex-1 rounded-full transition-colors',
              i < questionNumber - 1 ? 'bg-violet-400' :
              i === questionNumber - 1 ? 'bg-violet-600' :
              'bg-gray-100'
            )}
          />
        ))}
      </div>

      {/* Question */}
      <p className={clsx('text-base font-semibold text-gray-900 leading-relaxed', isRtl && 'font-arabic text-right')}>
        {isRtl ? question.questionAr : question.questionEn}
      </p>

      {/* Options */}
      <div className="space-y-2.5">
        {question.options.map((opt, i) => {
          const isCorrect = i === question.correctIndex;
          const isChosen = chosen === i;
          return (
            <button
              key={i}
              onClick={() => pick(i)}
              disabled={answered}
              dir={isRtl ? 'rtl' : 'ltr'}
              className={clsx(
                'w-full flex items-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium text-left transition-all',
                isRtl && 'flex-row-reverse text-right font-arabic',
                !answered && 'border-gray-200 hover:border-violet-300 hover:bg-violet-50 cursor-pointer',
                answered && isCorrect && 'border-emerald-400 bg-emerald-50 text-emerald-800',
                answered && isChosen && !isCorrect && 'border-red-400 bg-red-50 text-red-700',
                answered && !isCorrect && !isChosen && 'border-gray-100 bg-gray-50 text-gray-400',
              )}
            >
              {answered && isCorrect && <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />}
              {answered && isChosen && !isCorrect && <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />}
              {(!answered || (!isCorrect && !isChosen)) && (
                <span className="w-4 h-4 flex-shrink-0 inline-flex items-center justify-center rounded-full border border-gray-300 text-[10px] text-gray-400">
                  {String.fromCharCode(65 + i)}
                </span>
              )}
              {isRtl ? opt.ar : opt.en}
            </button>
          );
        })}
      </div>

      {/* Explanation + Next button — shown only after answering */}
      {answered && (
        <div className="space-y-3">
          <div className={clsx('p-3 rounded-xl bg-violet-50 border border-violet-100', isRtl && 'text-right')}>
            <p className={clsx('text-xs text-violet-800 leading-relaxed', isRtl && 'font-arabic')}>
              {isRtl ? question.explanationAr : question.explanationEn}
            </p>
          </div>
          <button
            onClick={() => onNext(chosen!)}
            className={clsx(
              'w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-colors',
              chosen === question.correctIndex
                ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-violet-600 text-white hover:bg-violet-700',
              isRtl && 'flex-row-reverse'
            )}
          >
            {isLast
              ? (isRtl ? 'عرض النتائج' : 'View Results')
              : (isRtl ? 'السؤال التالي' : 'Next Question')}
            <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Results screen ───────────────────────────────────────────────────────────

function ResultsScreen({
  score, total, isRtl, onRestart,
}: {
  score: number; total: number; isRtl: boolean; onRestart: () => void;
}) {
  const pct = Math.round((score / total) * 100);
  const grade = pct >= 90 ? '🏆' : pct >= 70 ? '⭐' : pct >= 50 ? '👍' : '📖';
  const msgEn = pct >= 90 ? "Excellent! Masha'Allah!" : pct >= 70 ? 'Very good!' : pct >= 50 ? 'Good effort!' : 'Keep learning!';
  const msgAr = pct >= 90 ? 'ممتاز! ماشاء الله!' : pct >= 70 ? 'جيد جداً!' : pct >= 50 ? 'جهد رائع!' : 'استمر في التعلم!';

  return (
    <div className="text-center py-8 space-y-4">
      <span className="text-6xl block">{grade}</span>
      <h2 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
        {isRtl ? msgAr : msgEn}
      </h2>
      <p className="text-4xl font-bold text-violet-600">{score}/{total}</p>
      <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic')}>
        {isRtl ? `أصبت ${pct}% من الأسئلة` : `${pct}% correct`}
      </p>
      <div className="max-w-xs mx-auto">
        <ScoreBar score={score} total={total} isRtl={isRtl} />
      </div>
      <button
        onClick={onRestart}
        className={clsx(
          'inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 transition-colors',
          isRtl && 'flex-row-reverse'
        )}
      >
        <RefreshCw className="w-4 h-4" />
        {isRtl ? 'العب مجدداً' : 'Play Again'}
      </button>
    </div>
  );
}

// ─── Surah grid ───────────────────────────────────────────────────────────────

function SurahGrid({
  onSelect, isRtl,
}: {
  onSelect: (surah: number) => void;
  isRtl: boolean;
}) {
  return (
    <div>
      <p className={clsx('text-xs text-gray-400 mb-3', isRtl ? 'text-right font-arabic' : '')}>
        {isRtl
          ? 'السور باللون الأخضر لها أسئلة — اضغط للبدء'
          : 'Green surahs have questions — tap to start'}
      </p>
      <div className="grid grid-cols-4 sm:grid-cols-6 gap-1.5">
        {SURAH_NAMES.map((s, i) => {
          const num = i + 1;
          const count = SURAH_QUESTION_INDEX[num]?.length ?? 0;
          const hasQ = count > 0;
          return (
            <button
              key={num}
              onClick={() => hasQ && onSelect(num)}
              disabled={!hasQ}
              title={isRtl ? s.ar : s.en}
              className={clsx(
                'relative flex flex-col items-center justify-center rounded-xl p-1.5 text-center transition-all',
                hasQ
                  ? 'bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 hover:border-emerald-400 cursor-pointer'
                  : 'bg-gray-50 border border-gray-100 cursor-not-allowed opacity-50'
              )}
            >
              <span className={clsx('text-[10px] font-bold', hasQ ? 'text-emerald-700' : 'text-gray-400')}>
                {num}
              </span>
              <span className={clsx('text-[9px] leading-tight truncate w-full text-center', hasQ ? 'text-emerald-800 font-arabic' : 'text-gray-400 font-arabic')}>
                {s.ar}
              </span>
              {hasQ && (
                <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center rounded-full bg-emerald-500 text-white text-[8px] font-bold">
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <p className={clsx('text-[10px] text-gray-400 mt-3 text-center', isRtl && 'font-arabic')}>
        {isRtl
          ? `${Object.keys(SURAH_QUESTION_INDEX).length} سورة مغطاة من أصل 114 — قيد التوسع`
          : `${Object.keys(SURAH_QUESTION_INDEX).length} of 114 surahs covered — expanding soon`}
      </p>
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

  const cats = Object.keys(CATEGORY_META) as TriviaCategory[];

  const categoryPool = useMemo(() => {
    let all = [...TRIVIA_QUESTIONS];
    if (catFilter !== 'all') all = all.filter(q => q.category === catFilter);
    return all;
  }, [catFilter]);

  function startCategoryQuiz() {
    const shuffled = shuffle(categoryPool).slice(0, QUESTIONS_PER_SESSION);
    setQuestions(shuffled);
    setCurrent(0);
    setScore(0);
    setActiveSurah(null);
    setState('playing');
  }

  function startSurahQuiz(surahNum: number) {
    const qs = shuffle([...(SURAH_QUESTION_INDEX[surahNum] ?? [])]);
    if (!qs.length) return;
    setQuestions(qs);
    setCurrent(0);
    setScore(0);
    setActiveSurah(surahNum);
    setState('playing');
  }

  function handleNext(chosenIndex: number) {
    if (chosenIndex === questions[current].correctIndex) setScore(s => s + 1);
    if (current + 1 >= questions.length) {
      setState('finished');
    } else {
      setCurrent(c => c + 1);
    }
  }

  const surahName = activeSurah ? (isRtl ? SURAH_NAMES[activeSurah - 1]?.ar : SURAH_NAMES[activeSurah - 1]?.en) : null;

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <Trophy className="w-7 h-7 text-amber-500 flex-shrink-0" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'اختبار قرآني' : 'Quranic Quiz'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl ? `${TRIVIA_QUESTIONS.length} سؤالاً موثقاً` : `${TRIVIA_QUESTIONS.length} verified questions`}
          </p>
        </div>
      </div>

      {/* ── SELECTING ── */}
      {state === 'selecting' && (
        <div className="space-y-5">
          {/* Mode tabs */}
          <div className="flex rounded-xl border border-gray-200 bg-gray-50 p-1 gap-1">
            {([
              { key: 'category', labelEn: 'By Category', labelAr: 'حسب الفئة', Icon: LayoutGrid },
              { key: 'surah',    labelEn: 'By Surah',    labelAr: 'حسب السورة', Icon: BookOpen },
            ] as const).map(({ key, labelEn, labelAr, Icon }) => (
              <button
                key={key}
                onClick={() => setSelectMode(key)}
                className={clsx(
                  'flex-1 flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium transition-all',
                  selectMode === key
                    ? 'bg-white shadow text-violet-700'
                    : 'text-gray-500 hover:text-gray-700'
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
              <p className={clsx('text-sm font-semibold text-gray-700', isRtl && 'font-arabic')}>
                {isRtl ? 'اختر الفئة:' : 'Choose category:'}
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {([
                  ['all', { labelEn: 'All', labelAr: 'الكل', emoji: '🎯' }],
                  ...cats.map(c => [c, CATEGORY_META[c]] as const),
                ] as [string, { labelEn: string; labelAr: string; emoji: string }][]).map(([cat, meta]) => (
                  <button
                    key={cat}
                    onClick={() => setCatFilter(cat as TriviaCategory | 'all')}
                    className={clsx(
                      'flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition-all',
                      catFilter === cat
                        ? 'bg-violet-600 text-white border-violet-600'
                        : 'bg-white text-gray-700 border-gray-200 hover:border-violet-300'
                    )}
                  >
                    <span className="text-2xl">{meta.emoji}</span>
                    <span className={clsx('text-xs font-medium leading-tight', isRtl && 'font-arabic')}>
                      {isRtl ? meta.labelAr : meta.labelEn}
                    </span>
                  </button>
                ))}
              </div>

              <div className="bg-violet-50 rounded-2xl border border-violet-100 p-4">
                <div className={clsx('flex items-center gap-2 mb-2', isRtl && 'flex-row-reverse')}>
                  <HelpCircle className="w-4 h-4 text-violet-600" />
                  <p className={clsx('text-sm font-semibold text-violet-800', isRtl && 'font-arabic')}>
                    {isRtl ? 'كيف تلعب' : 'How to play'}
                  </p>
                </div>
                <ul className={clsx('text-xs text-violet-700 space-y-1', isRtl && 'font-arabic text-right')}>
                  <li>• {isRtl ? `${Math.min(QUESTIONS_PER_SESSION, categoryPool.length)} أسئلة عشوائية` : `${Math.min(QUESTIONS_PER_SESSION, categoryPool.length)} random questions`}</li>
                  <li>• {isRtl ? 'اختر الإجابة ثم اضغط "السؤال التالي"' : 'Pick an answer, then tap "Next Question"'}</li>
                  <li>• {isRtl ? 'كل الأسئلة من مصادر علمية موثقة' : 'All questions from verified scholarly sources'}</li>
                </ul>
              </div>

              <button
                onClick={startCategoryQuiz}
                disabled={categoryPool.length === 0}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 py-3 rounded-2xl text-base font-semibold transition-colors',
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
          {selectMode === 'surah' && (
            <SurahGrid onSelect={startSurahQuiz} isRtl={isRtl} />
          )}
        </div>
      )}

      {/* ── PLAYING ── */}
      {state === 'playing' && questions[current] && (
        <div className="space-y-4">
          {/* Surah context banner */}
          {activeSurah && surahName && (
            <div className={clsx('flex items-center gap-2 text-sm text-emerald-700 font-medium', isRtl && 'flex-row-reverse font-arabic')}>
              <BookOpen className="w-4 h-4" />
              {isRtl ? `أسئلة سورة ${surahName}` : `Questions for Surah ${surahName}`}
              <Link to={`/quran/${activeSurah}`} className={clsx('ms-auto flex items-center gap-1 text-xs text-gray-400 hover:text-emerald-600 transition-colors', isRtl && 'flex-row-reverse')}>
                {isRtl ? 'اقرأ السورة' : 'Read surah'}
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
        />
      )}

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'جميع الإجابات موثقة من المصادر الإسلامية الكلاسيكية'
          : 'All answers verified from classical Islamic scholarship'}
      </p>
    </div>
  );
}
