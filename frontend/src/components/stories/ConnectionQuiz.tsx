/**
 * ConnectionQuiz — small in-page quiz that uses only explicit, ayah-verified
 * entity occurrences from the scan.
 *
 * Question types:
 *   1) Which surah is this prophet mentioned in?
 *   2) Which entity is associated with this story?
 *
 * Rules:
 *   - Questions are generated from `scan.entityIndex` and `relatedStories`.
 *   - No interpretive questions — only "where mentioned" / "linked to".
 *   - Every quiz item carries a "needs_review" badge in the explanation.
 */

import { useMemo, useState } from 'react';
import { CheckCircle2, RefreshCw, XCircle } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import scanData from '../../data/generated/quranStoryConnections.json';
import { QURAN_STORY_ENTITY_SEEDS } from '../../data/quranStoryEntitySeeds';
import type { ScanOutput } from '../../types/quranStoryConnection';

const scan = scanData as ScanOutput;

interface QuizQuestion {
  prompt: { ar: string; en: string };
  options: Array<{ label: { ar: string; en: string }; isCorrect: boolean }>;
  explanation: { ar: string; en: string };
}

function pickRandom<T>(arr: T[], n: number): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, n);
}

function generateSurahQuestion(): QuizQuestion | null {
  const candidates = scan.entityIndex.filter((e) => {
    const seed = QURAN_STORY_ENTITY_SEEDS.find((s) => s.entityId === e.entityId);
    return !!seed && (seed.type === 'prophet' || seed.type === 'person') && e.occurrences.length >= 2;
  });
  if (candidates.length === 0) return null;
  const target = candidates[Math.floor(Math.random() * candidates.length)];
  const seed = QURAN_STORY_ENTITY_SEEDS.find((s) => s.entityId === target.entityId)!;
  const correctSurah = target.occurrences[0].surahNumber;
  const correctName = scan.surahs.find((s) => s.surahNumber === correctSurah);
  const otherSurahs = pickRandom(
    scan.surahs.filter((s) => !target.occurrences.some((o) => o.surahNumber === s.surahNumber)),
    3
  );
  const options = [
    { label: { ar: `سورة ${correctName?.surahNameArabic ?? correctSurah}`, en: `Surah ${correctName?.surahNameEnglish ?? correctSurah}` }, isCorrect: true },
    ...otherSurahs.map((s) => ({
      label: { ar: `سورة ${s.surahNameArabic}`, en: `Surah ${s.surahNameEnglish ?? s.surahNameArabic}` },
      isCorrect: false,
    })),
  ];
  // Shuffle options
  for (let i = options.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [options[i], options[j]] = [options[j], options[i]];
  }
  return {
    prompt: {
      ar: `في أيّ سورة وردت قصة ${seed.labelArabic}؟`,
      en: `In which surah is ${seed.labelEnglish} mentioned?`,
    },
    options,
    explanation: {
      ar: `${seed.labelArabic} مذكور في ${target.occurrences.length} موضعًا في القرآن (مرشّحات بحاجة للمراجعة).`,
      en: `${seed.labelEnglish} appears in ${target.occurrences.length} positions in the Quran (candidates pending review).`,
    },
  };
}

function generateAnimalObjectQuestion(): QuizQuestion | null {
  const animalObjects = QURAN_STORY_ENTITY_SEEDS.filter(
    (e) => (e.type === 'animal' || e.type === 'object') && e.relatedStories.length > 0
  );
  if (animalObjects.length < 4) return null;
  const target = animalObjects[Math.floor(Math.random() * animalObjects.length)];
  const correctStoryId = target.relatedStories[0];
  const otherEntities = pickRandom(animalObjects.filter((e) => e.entityId !== target.entityId), 3);
  const options = [
    { label: { ar: target.labelArabic, en: target.labelEnglish }, isCorrect: true },
    ...otherEntities.map((e) => ({ label: { ar: e.labelArabic, en: e.labelEnglish }, isCorrect: false })),
  ];
  for (let i = options.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [options[i], options[j]] = [options[j], options[i]];
  }
  return {
    prompt: {
      ar: `أيّ من هذه الكيانات يرتبط بقصة ${correctStoryId}؟`,
      en: `Which of these entities belongs to the story ${correctStoryId}?`,
    },
    options,
    explanation: {
      ar: `${target.labelArabic} مرتبط بقصة ${correctStoryId} في القاموس الأوّلي (بحاجة للمراجعة).`,
      en: `${target.labelEnglish} is associated with ${correctStoryId} in the seed dictionary (needs review).`,
    },
  };
}

export function ConnectionQuiz() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [question, setQuestion] = useState<QuizQuestion | null>(() => generateSurahQuestion());
  const [picked, setPicked] = useState<number | null>(null);

  const reset = () => {
    const next = Math.random() > 0.5 ? generateSurahQuestion() : generateAnimalObjectQuestion();
    setQuestion(next ?? generateSurahQuestion());
    setPicked(null);
  };

  const correctIdx = useMemo(() => {
    if (!question) return -1;
    return question.options.findIndex((o) => o.isCorrect);
  }, [question]);

  if (!question) {
    return <div className="text-sm text-gray-500">{isArabic ? 'لا توجد بيانات كافية للاختبار.' : 'Not enough data to generate a quiz.'}</div>;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-sm">{isArabic ? 'اختبار الروابط' : 'Connection quiz'}</h4>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
          {isArabic ? 'مرشّحات' : 'candidates'}
        </span>
      </div>
      <p className="mb-3">{isArabic ? question.prompt.ar : question.prompt.en}</p>
      <div className="space-y-2 mb-3">
        {question.options.map((o, i) => {
          const isPicked = picked === i;
          const reveal = picked !== null;
          return (
            <button
              key={i}
              disabled={reveal}
              onClick={() => setPicked(i)}
              className={
                'w-full text-left px-3 py-2 rounded border transition ' +
                (reveal
                  ? o.isCorrect
                    ? 'bg-emerald-50 border-emerald-300'
                    : isPicked
                      ? 'bg-red-50 border-red-300'
                      : 'bg-white border-gray-200'
                  : 'bg-white border-gray-200 hover:bg-gray-50')
              }
            >
              <span className="flex items-center justify-between">
                <span>{isArabic ? o.label.ar : o.label.en}</span>
                {reveal && o.isCorrect && <CheckCircle2 className="w-4 h-4 text-emerald-700" />}
                {reveal && !o.isCorrect && isPicked && <XCircle className="w-4 h-4 text-red-700" />}
              </span>
            </button>
          );
        })}
      </div>
      {picked !== null && (
        <div className="text-xs text-gray-600 mb-2">
          {picked === correctIdx
            ? (isArabic ? 'إجابة صحيحة ✔' : 'Correct ✔')
            : (isArabic ? 'إجابة غير صحيحة. ' : 'Incorrect. ')}
          {isArabic ? question.explanation.ar : question.explanation.en}
        </div>
      )}
      <button onClick={reset} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700">
        <RefreshCw className="w-3 h-3" />
        {isArabic ? 'سؤال جديد' : 'New question'}
      </button>
    </div>
  );
}

export default ConnectionQuiz;
