/**
 * Quranic Trivia Quiz — verified fact-based multiple choice questions.
 *
 * Static data only — no AI-generated content.
 * Score tracked per session (not persisted).
 */

import { useState, useMemo } from 'react';
import { Trophy, RefreshCw, ChevronRight, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  TRIVIA_QUESTIONS, CATEGORY_META,
  type TriviaQuestion, type TriviaCategory,
} from '../data/quranicTrivia';

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
        <div className={clsx('h-full rounded-full transition-all', colorClass)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function QuestionCard({
  question, questionNumber, total, isRtl, onAnswer,
}: {
  question: TriviaQuestion;
  questionNumber: number;
  total: number;
  isRtl: boolean;
  onAnswer: (chosenIndex: number) => void;
}) {
  const [chosen, setChosen] = useState<number | null>(null);
  const revealed = chosen !== null;

  function pick(i: number) {
    if (revealed) return;
    setChosen(i);
    setTimeout(() => onAnswer(i), 900);
  }

  const catMeta = CATEGORY_META[question.category];

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5">
      {/* Header */}
      <div className={clsx('flex items-center gap-2 mb-4', isRtl && 'flex-row-reverse')}>
        <span className={clsx('text-[10px] px-2 py-0.5 rounded-full bg-violet-100 text-violet-700')}>
          {catMeta.emoji} {isRtl ? catMeta.labelAr : catMeta.labelEn}
        </span>
        <span className="text-[10px] text-gray-400 ms-auto">
          {isRtl ? `${questionNumber} من ${total}` : `${questionNumber} of ${total}`}
        </span>
      </div>

      {/* Question */}
      <p className={clsx('text-base font-semibold text-gray-900 mb-5', isRtl && 'font-arabic text-right leading-relaxed')}>
        {isRtl ? question.questionAr : question.questionEn}
      </p>

      {/* Options */}
      <div className="space-y-2.5">
        {question.options.map((opt, i) => {
          const isCorrect = i === question.correctIndex;
          const isChosen = chosen === i;
          let classes = 'border rounded-xl px-4 py-3 text-sm font-medium transition-all w-full text-left';
          if (!revealed) {
            classes += ' border-gray-200 hover:border-violet-300 hover:bg-violet-50 cursor-pointer';
          } else if (isCorrect) {
            classes += ' border-emerald-400 bg-emerald-50 text-emerald-800';
          } else if (isChosen) {
            classes += ' border-red-400 bg-red-50 text-red-700';
          } else {
            classes += ' border-gray-100 bg-gray-50 text-gray-400';
          }
          return (
            <button
              key={i}
              onClick={() => pick(i)}
              disabled={revealed}
              className={clsx(classes, isRtl && 'text-right font-arabic')}
              dir={isRtl ? 'rtl' : 'ltr'}
            >
              <span className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
                {revealed && isCorrect && <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />}
                {revealed && isChosen && !isCorrect && <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />}
                {(!revealed || (!isCorrect && !isChosen)) && <span className="w-4 h-4 flex-shrink-0" />}
                {isRtl ? opt.ar : opt.en}
              </span>
            </button>
          );
        })}
      </div>

      {/* Explanation (shown after answer) */}
      {revealed && (
        <div className={clsx('mt-4 p-3 rounded-xl bg-violet-50 border border-violet-100', isRtl && 'text-right')}>
          <p className={clsx('text-xs text-violet-800 leading-relaxed', isRtl && 'font-arabic')}>
            {isRtl ? question.explanationAr : question.explanationEn}
          </p>
        </div>
      )}
    </div>
  );
}

function ResultsScreen({
  score, total, isRtl, onRestart,
}: {
  score: number; total: number; isRtl: boolean; onRestart: () => void;
}) {
  const pct = Math.round((score / total) * 100);
  const grade = pct >= 90 ? '🏆' : pct >= 70 ? '⭐' : pct >= 50 ? '👍' : '📖';
  const msgEn = pct >= 90 ? 'Excellent! Masha\'Allah!' : pct >= 70 ? 'Very good!' : pct >= 50 ? 'Good effort!' : 'Keep learning!';
  const msgAr = pct >= 90 ? 'ممتاز! ماشاء الله!' : pct >= 70 ? 'جيد جداً!' : pct >= 50 ? 'جهد رائع!' : 'استمر في التعلم!';

  return (
    <div className="text-center py-8">
      <span className="text-6xl block mb-4">{grade}</span>
      <h2 className={clsx('text-2xl font-bold text-gray-900 mb-2', isRtl && 'font-arabic')}>
        {isRtl ? msgAr : msgEn}
      </h2>
      <p className="text-4xl font-bold text-violet-600 mb-1">{score}/{total}</p>
      <p className={clsx('text-sm text-gray-500 mb-6', isRtl && 'font-arabic')}>
        {isRtl ? `أصبت ${pct}% من الأسئلة` : `${pct}% correct`}
      </p>
      <ScoreBar score={score} total={total} isRtl={isRtl} />
      <button
        onClick={onRestart}
        className={clsx(
          'mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 transition-colors',
          isRtl && 'flex-row-reverse'
        )}
      >
        <RefreshCw className="w-4 h-4" />
        {isRtl ? 'العب مجدداً' : 'Play Again'}
      </button>
    </div>
  );
}

export function QuizPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [state, setState] = useState<QuizState>('selecting');
  const [catFilter, setCatFilter] = useState<TriviaCategory | 'all'>('all');
  const [questions, setQuestions] = useState<TriviaQuestion[]>([]);
  const [current, setCurrent] = useState(0);
  const [score, setScore] = useState(0);

  const cats = Object.keys(CATEGORY_META) as TriviaCategory[];

  const pool = useMemo(() => {
    let all = [...TRIVIA_QUESTIONS];
    if (catFilter !== 'all') all = all.filter(q => q.category === catFilter);
    return all;
  }, [catFilter]);

  function startQuiz() {
    const shuffled = shuffle(pool).slice(0, QUESTIONS_PER_SESSION);
    setQuestions(shuffled);
    setCurrent(0);
    setScore(0);
    setState('playing');
  }

  function handleAnswer(chosenIndex: number) {
    const q = questions[current];
    if (chosenIndex === q.correctIndex) setScore(s => s + 1);
    if (current + 1 >= questions.length) {
      setState('finished');
    } else {
      setCurrent(c => c + 1);
    }
  }

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <Trophy className="w-7 h-7 text-amber-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'اختبار قرآني' : 'Quranic Quiz'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl ? `${TRIVIA_QUESTIONS.length} سؤالاً موثقاً` : `${TRIVIA_QUESTIONS.length} verified questions`}
          </p>
        </div>
      </div>

      {state === 'selecting' && (
        <div>
          {/* Category selector */}
          <p className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic')}>
            {isRtl ? 'اختر الفئة:' : 'Choose category:'}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-6">
            {([['all', { labelEn: 'All Categories', labelAr: 'كل الفئات', emoji: '🎯' }], ...cats.map(c => [c, CATEGORY_META[c]])] as [string, { labelEn: string; labelAr: string; emoji: string }][]).map(([cat, meta]) => (
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

          <div className="bg-violet-50 rounded-2xl border border-violet-100 p-4 mb-6">
            <div className={clsx('flex items-center gap-2 mb-2', isRtl && 'flex-row-reverse')}>
              <HelpCircle className="w-4 h-4 text-violet-600" />
              <p className={clsx('text-sm font-semibold text-violet-800', isRtl && 'font-arabic')}>
                {isRtl ? 'كيف تلعب' : 'How to play'}
              </p>
            </div>
            <ul className={clsx('text-xs text-violet-700 space-y-1', isRtl && 'font-arabic text-right')}>
              <li>• {isRtl ? `${Math.min(QUESTIONS_PER_SESSION, pool.length)} أسئلة لكل جلسة` : `${Math.min(QUESTIONS_PER_SESSION, pool.length)} questions per session`}</li>
              <li>• {isRtl ? 'اضغط على الإجابة الصحيحة' : 'Tap the correct answer'}</li>
              <li>• {isRtl ? 'كل الأسئلة من مصادر علمية موثقة' : 'All questions from verified scholarly sources'}</li>
            </ul>
          </div>

          <button
            onClick={startQuiz}
            disabled={pool.length === 0}
            className={clsx(
              'w-full flex items-center justify-center gap-2 py-3 rounded-2xl text-base font-semibold transition-colors',
              pool.length > 0
                ? 'bg-violet-600 text-white hover:bg-violet-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            {isRtl ? 'ابدأ الاختبار' : 'Start Quiz'}
            <ChevronRight className={clsx('w-5 h-5', isRtl && 'rotate-180')} />
          </button>
        </div>
      )}

      {state === 'playing' && questions[current] && (
        <div>
          <div className="mb-4">
            <ScoreBar score={score} total={current} isRtl={isRtl} />
          </div>
          <QuestionCard
            key={current}
            question={questions[current]}
            questionNumber={current + 1}
            total={questions.length}
            isRtl={isRtl}
            onAnswer={handleAnswer}
          />
        </div>
      )}

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
