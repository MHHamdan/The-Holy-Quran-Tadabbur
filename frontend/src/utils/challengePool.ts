/**
 * Daily Challenge question pool — covers the entire Quran.
 *
 * Three sources, all factual and repo-derived (no generated religious content):
 *  1. story  — kidsQuiz questions from all story batches (QURAN_STORIES_FIRST_BATCH)
 *  2. trivia — verified TRIVIA_QUESTIONS (structure, prophets, revelation, worship…)
 *  3. surah  — generated from SURAH_ATLAS_DATA metadata for all 114 surahs:
 *              revelation period (makki/madani) and ayah count.
 *
 * Selection is date-seeded and rotates categories day by day so every third
 * challenge touches a different dimension of the Quran.
 */

import { QURAN_STORIES_FIRST_BATCH } from '../data/quranStories';
import { TRIVIA_QUESTIONS } from '../data/quranicTrivia';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';
import { SURAH_NAMES } from '../data/surahNames';

export type ChallengeCategory = 'story' | 'trivia' | 'surah';

export interface ChallengeQuestion {
  questionId: string;
  category: ChallengeCategory;
  /** 1-based surah number this question is about, when known. */
  surahRef?: number;
  storyId?: string;
  sourceLabelEn: string;
  sourceLabelAr: string;
  questionArabic: string;
  questionEnglish: string;
  optionsArabic: string[];
  optionsEnglish: string[];
  correctOptionIndex: number;
  explanationArabic: string;
  explanationEnglish: string;
}

export const CATEGORY_META: Record<ChallengeCategory, {
  labelEn: string; labelAr: string; emoji: string; color: string;
}> = {
  story:  { labelEn: 'Quran Stories',   labelAr: 'قصص القرآن',    emoji: '📖', color: 'bg-amber-400' },
  trivia: { labelEn: 'Quran Knowledge', labelAr: 'معارف قرآنية',  emoji: '💡', color: 'bg-sky-400' },
  surah:  { labelEn: 'Surah Explorer',  labelAr: 'استكشاف السور', emoji: '🕌', color: 'bg-emerald-400' },
};

// ─── Deterministic helpers ─────────────────────────────────────────────────────

function hashStr(s: string): number {
  let h = 5381;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  }
  return h;
}

/** Deterministic in-place-free shuffle of a small array, seeded by `seed`. */
function seededShuffle<T>(items: T[], seed: number): T[] {
  const arr = [...items];
  let s = seed >>> 0;
  for (let i = arr.length - 1; i > 0; i--) {
    s = (s * 1103515245 + 12345) >>> 0;
    const j = s % (i + 1);
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ─── Source 1: story kidsQuiz ─────────────────────────────────────────────────

function buildStoryQuestions(): ChallengeQuestion[] {
  const out: ChallengeQuestion[] = [];
  for (const story of QURAN_STORIES_FIRST_BATCH) {
    if (!story.kidsQuiz) continue;
    const surahRef = story.quranReferences[0]?.surahNumber;
    for (const q of story.kidsQuiz) {
      out.push({
        questionId: q.questionId,
        category: 'story',
        surahRef,
        storyId: story.storyId,
        sourceLabelEn: story.titleEnglish,
        sourceLabelAr: story.titleArabic,
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

// ─── Source 2: verified trivia ────────────────────────────────────────────────

function buildTriviaQuestions(): ChallengeQuestion[] {
  return TRIVIA_QUESTIONS.map((q) => ({
    questionId: q.id,
    category: 'trivia' as const,
    surahRef: q.surahRef,
    sourceLabelEn: 'Quran Knowledge',
    sourceLabelAr: 'معارف قرآنية',
    questionArabic: q.questionAr,
    questionEnglish: q.questionEn,
    optionsArabic: q.options.map((o) => o.ar),
    optionsEnglish: q.options.map((o) => o.en),
    correctOptionIndex: q.correctIndex,
    explanationArabic: q.explanationAr,
    explanationEnglish: q.explanationEn,
  }));
}

// ─── Source 3: generated surah metadata questions (all 114 surahs) ────────────

/** Plausible, distinct, positive ayah-count distractors around the real count. */
function ayahCountOptions(count: number, seed: number): { options: number[]; correctIndex: number } {
  const spread = Math.max(2, Math.round(count * 0.18));
  const candidates = new Set<number>([count]);
  const deltas = [spread, -spread, spread * 2, -Math.max(1, Math.round(spread / 2)), spread + 3];
  for (const d of deltas) {
    if (candidates.size >= 4) break;
    const v = count + d;
    if (v >= 1 && !candidates.has(v)) candidates.add(v);
  }
  // Fallback fill for tiny surahs where deltas collide
  let bump = 1;
  while (candidates.size < 4) {
    const v = count + spread * 2 + bump;
    if (!candidates.has(v)) candidates.add(v);
    bump++;
  }
  const options = seededShuffle([...candidates].slice(0, 4), seed);
  return { options, correctIndex: options.indexOf(count) };
}

function buildSurahQuestions(): ChallengeQuestion[] {
  const out: ChallengeQuestion[] = [];

  for (const s of SURAH_ATLAS_DATA) {
    const n = s.surahNumber;
    const nameAr = `سورة ${SURAH_NAMES[n - 1]?.ar ?? s.nameArabic}`;
    const nameEn = SURAH_NAMES[n - 1]?.en ?? s.nameTransliteration;
    const isMakki = s.revelationType === 'makki';

    // Q1 — revelation period
    {
      const correctIndex = isMakki ? 0 : 1;
      out.push({
        questionId: `surah_${n}_revelation`,
        category: 'surah',
        surahRef: n,
        sourceLabelEn: `Surah ${nameEn} (${n})`,
        sourceLabelAr: `${nameAr} (${n})`,
        questionArabic: `${nameAr} — هل هي سورة مكية أم مدنية؟`,
        questionEnglish: `Surah ${nameEn} (${n}) — was it revealed in the Makkan or Madinan period?`,
        optionsArabic: ['مكية', 'مدنية'],
        optionsEnglish: ['Makki (Makkan period)', 'Madani (Madinan period)'],
        correctOptionIndex: correctIndex,
        explanationArabic: isMakki
          ? `${nameAr} من السور المكية، نزلت قبل الهجرة.`
          : `${nameAr} من السور المدنية، نزلت بعد الهجرة.`,
        explanationEnglish: isMakki
          ? `Surah ${nameEn} is a Makki surah, revealed before the Hijrah.`
          : `Surah ${nameEn} is a Madani surah, revealed after the Hijrah.`,
      });
    }

    // Q2 — ayah count
    {
      const { options, correctIndex } = ayahCountOptions(s.ayahCount, hashStr(`ayah_${n}`));
      out.push({
        questionId: `surah_${n}_ayahs`,
        category: 'surah',
        surahRef: n,
        sourceLabelEn: `Surah ${nameEn} (${n})`,
        sourceLabelAr: `${nameAr} (${n})`,
        questionArabic: `كم عدد آيات ${nameAr}؟`,
        questionEnglish: `How many ayahs are in Surah ${nameEn} (${n})?`,
        optionsArabic: options.map(String),
        optionsEnglish: options.map(String),
        correctOptionIndex: correctIndex,
        explanationArabic: `عدد آيات ${nameAr} هو ${s.ayahCount} آية، وتقع في ${s.juzRefs.join(' و')}.`,
        explanationEnglish: `Surah ${nameEn} has ${s.ayahCount} ayahs and spans ${s.juzRefs.join(', ')}.`,
      });
    }
  }

  return out;
}

// ─── Pool assembly + daily selection ──────────────────────────────────────────

let cachedPool: Record<ChallengeCategory, ChallengeQuestion[]> | null = null;

export function getChallengePool(): Record<ChallengeCategory, ChallengeQuestion[]> {
  if (!cachedPool) {
    cachedPool = {
      story: buildStoryQuestions(),
      trivia: buildTriviaQuestions(),
      surah: buildSurahQuestions(),
    };
  }
  return cachedPool;
}

export function getPoolSize(): number {
  const p = getChallengePool();
  return p.story.length + p.trivia.length + p.surah.length;
}

const CATEGORY_ROTATION: ChallengeCategory[] = ['story', 'surah', 'trivia'];

/**
 * Date-seeded daily pick. Categories rotate day by day (story → surah → trivia)
 * so consecutive days always explore different dimensions; the question within
 * a category is chosen by a date hash.
 */
export function getQuestionForDate(dateStr: string): ChallengeQuestion {
  const pool = getChallengePool();
  const dayIndex = Math.floor(Date.parse(`${dateStr}T00:00:00Z`) / 86_400_000);
  const category = CATEGORY_ROTATION[((dayIndex % 3) + 3) % 3];
  const bucket = pool[category];
  return bucket[hashStr(dateStr) % bucket.length];
}
