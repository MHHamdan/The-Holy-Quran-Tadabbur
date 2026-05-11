/**
 * Surah Memory Atlas — /tools/surah-memory-atlas
 *
 * Redesigned: rich grid, linkable verses, Mushaf links, language-pure rendering,
 * intelligent factual memory clues from verified data only.
 *
 * Content policy:
 * - All ayah text comes from surahMemoryAtlas.json (built from quran_uthmani.json)
 * - No ayah text is hardcoded here
 * - Makki/Madani is curated metadata; always shown with needs_review badge
 * - Memory clues are generated from verified numeric data only (no AI-generated Islamic content)
 */

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, BookOpen, Brain, X,
  ExternalLink,
  AlertTriangle, Filter, RotateCcw, LayoutGrid,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';
import atlasData from '../../data/generated/surahMemoryAtlas.json';
import type {
  SurahMemoryItem, RevelationType, LengthCategory, QuranPosition,
} from '../../types/surahMemoryAtlas';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ViewMode = 'grid' | 'quiz';
type FilterRevelation = 'all' | RevelationType;
type FilterLength = 'all' | LengthCategory;
type FilterPosition = 'all' | QuranPosition;

interface QuizQuestion {
  type: 'before' | 'after' | 'type' | 'length' | 'number' | 'name';
  surah: SurahMemoryItem;
  correctAnswer: string;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const SURAHS: SurahMemoryItem[] = (atlasData as { surahs: SurahMemoryItem[] }).surahs;
const MAX_AYAHS = 286; // Al-Baqara — used for relative length bar

// ---------------------------------------------------------------------------
// Pure helpers (no UI)
// ---------------------------------------------------------------------------

const toArabicIndic = (n: number): string =>
  n.toString().replace(/[0-9]/g, d => '٠١٢٣٤٥٦٧٨٩'[+d]);

function displayNum(n: number, lang: 'ar' | 'en'): string {
  return lang === 'ar' ? toArabicIndic(n) : String(n);
}

function revelationGradient(type: RevelationType): string {
  if (type === 'makki') return 'from-amber-500 to-orange-400';
  if (type === 'madani') return 'from-emerald-500 to-teal-400';
  return 'from-slate-500 to-gray-400';
}

function revelationCardRing(type: RevelationType): string {
  if (type === 'makki') return 'ring-amber-400 border-amber-300 shadow-amber-100';
  if (type === 'madani') return 'ring-emerald-400 border-emerald-300 shadow-emerald-100';
  return 'ring-slate-400 border-slate-300 shadow-slate-100';
}

function revelationNumClass(type: RevelationType): string {
  if (type === 'makki') return 'bg-amber-50 text-amber-700';
  if (type === 'madani') return 'bg-emerald-50 text-emerald-700';
  return 'bg-gray-50 text-gray-600';
}

function revelationLabel(type: RevelationType, lang: 'ar' | 'en'): string {
  if (type === 'makki') return t('sma_makki', lang);
  if (type === 'madani') return t('sma_madani', lang);
  return t('sma_unknown', lang);
}

function lengthLabel(cat: LengthCategory, lang: 'ar' | 'en'): string {
  if (cat === 'short') return t('sma_short', lang);
  if (cat === 'medium') return t('sma_medium', lang);
  if (cat === 'long') return t('sma_long', lang);
  return t('sma_very_long', lang);
}

function positionLabel(pos: QuranPosition, lang: 'ar' | 'en'): string {
  if (pos === 'beginning') return t('sma_beginning', lang);
  if (pos === 'early') return t('sma_early', lang);
  if (pos === 'middle') return t('sma_middle', lang);
  if (pos === 'late') return t('sma_late', lang);
  return t('sma_ending', lang);
}

function positionBarColor(pos: QuranPosition): string {
  if (pos === 'beginning') return 'bg-teal-500';
  if (pos === 'early') return 'bg-cyan-500';
  if (pos === 'middle') return 'bg-blue-500';
  if (pos === 'late') return 'bg-indigo-500';
  return 'bg-violet-500';
}

/**
 * Generates a factual memory clue derived exclusively from verified Quran data.
 * No Islamic interpretive content is generated — only structural facts.
 */
function generateIntelligentClue(s: SurahMemoryItem, lang: 'ar' | 'en'): string | null {
  const n = s.surahNumber;

  // Structurally notable surahs — only factual, widely-agreed scholarly notes
  const specials: Record<number, { ar: string; en: string }> = {
    1:   { ar: 'أم الكتاب — أول سورة في المصحف الشريف', en: 'Umm Al-Kitab — the very first surah of the Quran' },
    2:   { ar: `أطول سورة في القرآن الكريم بـ${toArabicIndic(286)} آية`, en: 'Longest surah in the Quran with 286 ayahs' },
    9:   { ar: 'السورة الوحيدة التي لم تُفتتح بالبسملة', en: 'The only surah not prefaced by Bismillah' },
    18:  { ar: 'السورة الوسطى في ترتيب المصحف', en: 'Situated near the middle of the Quran by order' },
    36:  { ar: 'السورة الـ٣٦ — في منتصف المصحف الورقي تقريباً', en: 'Surah 36 — approximately the midpoint of the Mushaf' },
    112: { ar: `${toArabicIndic(4)} آيات فقط — أقصر سورة من حيث الحجم`, en: 'Only 4 ayahs — one of the shortest surahs by size' },
    113: { ar: 'الأولى من المعوذتين (الفلق والناس)', en: 'First of the two refuge surahs (Al-Mu\'awwidhatan)' },
    114: { ar: 'خاتمة المصحف الشريف — آخر سورة في القرآن', en: 'Final surah — the seal of the Holy Quran' },
  };
  if (specials[n]) return lang === 'ar' ? specials[n].ar : specials[n].en;

  // Single-page surah (fits entirely on one Mushaf page)
  if (s.pageStart === s.pageEnd) {
    return lang === 'ar'
      ? `تقع كاملةً في صفحة ${toArabicIndic(s.pageStart)} من المصحف`
      : `Fits entirely on page ${s.pageStart} of the Mushaf`;
  }

  // Very long (spans many pages)
  const pages = s.pageEnd - s.pageStart + 1;
  if (pages >= 15) {
    return lang === 'ar'
      ? `سورة طويلة — تمتد على ${toArabicIndic(pages)} صفحة من المصحف`
      : `Long surah — spans ${pages} pages of the Mushaf`;
  }

  // Entirely within one juz
  if (s.juzStart === s.juzEnd) {
    return lang === 'ar'
      ? `ضمن الجزء ${toArabicIndic(s.juzStart)} كاملاً`
      : `Falls entirely within Juz ${s.juzStart}`;
  }

  return null;
}

function generateQuestion(surahs: SurahMemoryItem[]): QuizQuestion {
  const types: QuizQuestion['type'][] = ['before', 'after', 'type', 'length', 'number', 'name'];
  const type = types[Math.floor(Math.random() * types.length)];
  const idx = Math.floor(Math.random() * surahs.length);
  const surah = surahs[idx];

  let correctAnswer = '';
  if (type === 'before') {
    correctAnswer = surah.surahNumber === 1
      ? 'none'
      : surahs.find(s => s.surahNumber === surah.surahNumber - 1)?.nameTransliteration ?? 'none';
  } else if (type === 'after') {
    correctAnswer = surah.surahNumber === 114
      ? 'none'
      : surahs.find(s => s.surahNumber === surah.surahNumber + 1)?.nameTransliteration ?? 'none';
  } else if (type === 'type') {
    correctAnswer = surah.revelationType;
  } else if (type === 'length') {
    correctAnswer = surah.lengthCategory;
  } else if (type === 'number') {
    correctAnswer = String(surah.surahNumber);
  } else {
    correctAnswer = surah.nameTransliteration;
  }

  return { type, surah, correctAnswer };
}

// ---------------------------------------------------------------------------
// SurahCard — grid tile
// ---------------------------------------------------------------------------

function SurahCard({
  surah, selected, onClick, language,
}: {
  surah: SurahMemoryItem;
  selected: boolean;
  onClick: () => void;
  language: 'ar' | 'en';
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      className={clsx(
        'group relative rounded-xl overflow-hidden cursor-pointer transition-all duration-200',
        'border-2 bg-white focus:outline-none',
        selected
          ? clsx('ring-2 ring-offset-1 shadow-lg', revelationCardRing(surah.revelationType))
          : 'border-gray-100 hover:border-gray-200 hover:shadow-md hover:-translate-y-0.5',
      )}
    >
      {/* Revelation color top bar */}
      <div className={clsx('h-1.5 w-full bg-gradient-to-r', revelationGradient(surah.revelationType))} />

      {/* Card body */}
      <div className="p-2.5 flex flex-col items-center text-center gap-1.5">
        {/* Surah number */}
        <span className={clsx(
          'text-xs font-bold w-7 h-7 rounded-full flex items-center justify-center shrink-0',
          revelationNumClass(surah.revelationType),
        )}>
          {displayNum(surah.surahNumber, language)}
        </span>

        {/* Arabic name */}
        <div className="font-arabic text-base leading-snug text-gray-900 w-full" dir="rtl">
          {surah.nameArabic}
        </div>

        {/* Transliteration — language pure */}
        {language === 'en' && (
          <div className="text-[10px] text-gray-500 truncate w-full" dir="ltr">
            {surah.nameTransliteration}
          </div>
        )}

        {/* Ayah count */}
        <div className="text-[10px] text-gray-400">
          {displayNum(surah.ayahCount, language)} {t('sma_ayahs_short', language)}
        </div>
      </div>

      {/* Hover overlay: first ayah preview */}
      {surah.firstAyahPreview && (
        <div
          className={clsx(
            'absolute inset-0 rounded-xl bg-gradient-to-b',
            surah.revelationType === 'makki'
              ? 'from-amber-900/80 to-amber-950/90'
              : surah.revelationType === 'madani'
                ? 'from-emerald-900/80 to-emerald-950/90'
                : 'from-slate-900/80 to-slate-950/90',
            'opacity-0 group-hover:opacity-100 transition-opacity duration-200',
            'flex flex-col items-center justify-center p-2 gap-2',
          )}
          aria-hidden="true"
        >
          <p className="font-mushaf text-white text-xs leading-relaxed text-center line-clamp-4" dir="rtl">
            {surah.firstAyahPreview}
          </p>
          <Link
            to={`/quran/${surah.surahNumber}`}
            onClick={e => e.stopPropagation()}
            className="flex items-center gap-1 text-white/80 hover:text-white text-[10px] transition-colors"
            dir="ltr"
          >
            <ExternalLink className="w-2.5 h-2.5" />
            {t('sma_read_in_quran', language)}
          </Link>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SurahDetailPanel — rich info sidebar / bottom sheet
// ---------------------------------------------------------------------------

function SurahDetailPanel({
  surah, surahs, onClose, onNavigate, language,
}: {
  surah: SurahMemoryItem;
  surahs: SurahMemoryItem[];
  onClose: () => void;
  onNavigate: (n: number) => void;
  language: 'ar' | 'en';
}) {
  const prevSurah = surahs.find(s => s.surahNumber === surah.surahNumber - 1);
  const nextSurah = surahs.find(s => s.surahNumber === surah.surahNumber + 1);
  const clue = generateIntelligentClue(surah, language);
  const positionPct = ((surah.surahNumber - 1) / 113) * 100;
  const lengthPct = Math.min((surah.ayahCount / MAX_AYAHS) * 100, 100);

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className={clsx(
        'shrink-0 bg-gradient-to-br p-5 text-white relative',
        surah.revelationType === 'makki'
          ? 'from-amber-600 to-orange-500'
          : surah.revelationType === 'madani'
            ? 'from-emerald-600 to-teal-500'
            : 'from-slate-600 to-gray-500',
      )}>
        <button
          onClick={onClose}
          className="absolute top-3 end-3 p-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          aria-label={t('sma_close_panel', language)}
        >
          <X className="w-4 h-4 text-white" />
        </button>

        {/* Surah number badge */}
        <span className="inline-block bg-white/20 text-white text-xs font-bold px-2 py-0.5 rounded-full mb-2">
          {t('sma_surah_prefix', language)} {displayNum(surah.surahNumber, language)}
        </span>

        {/* Arabic name — always RTL, always font-arabic */}
        <div className="font-arabic text-3xl leading-relaxed text-white" dir="rtl">
          {surah.nameArabic}
        </div>

        {/* English/Latin name — only in English mode */}
        {language === 'en' && (
          <div className="text-white/90 text-base mt-0.5" dir="ltr">
            {surah.nameTransliteration}
            {surah.nameEnglish && (
              <span className="text-white/70 text-sm"> · {surah.nameEnglish}</span>
            )}
          </div>
        )}

        {/* Arabic transliteration label in Arabic mode */}
        {language === 'ar' && surah.nameEnglish && (
          <div className="text-white/70 text-sm mt-0.5" dir="ltr">
            {surah.nameTransliteration}
          </div>
        )}

        {/* Revelation badge */}
        <div className="flex items-center gap-2 mt-2">
          <span className="inline-flex items-center gap-1 bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">
            {revelationLabel(surah.revelationType, language)}
          </span>
          <span className="flex items-center gap-1 text-white/70 text-xs">
            <AlertTriangle className="w-3 h-3" />
            {t('sma_review_required', language)}
          </span>
        </div>
      </div>

      {/* Panel body — scrollable */}
      <div className="flex-1 overflow-y-auto">
        {/* Stats grid */}
        <div className="grid grid-cols-3 divide-x divide-gray-100 border-b border-gray-100">
          {[
            { label: t('sma_ayah_count', language), value: displayNum(surah.ayahCount, language) },
            {
              label: t('sma_juz_range_lbl', language),
              value: surah.juzStart === surah.juzEnd
                ? displayNum(surah.juzStart, language)
                : `${displayNum(surah.juzStart, language)}–${displayNum(surah.juzEnd, language)}`,
            },
            {
              label: t('sma_page_lbl', language),
              value: surah.pageStart === surah.pageEnd
                ? displayNum(surah.pageStart, language)
                : `${displayNum(surah.pageStart, language)}–${displayNum(surah.pageEnd, language)}`,
            },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 text-center">
              <div className="text-xs text-gray-500">{label}</div>
              <div className="text-lg font-bold text-gray-900 mt-0.5">{value}</div>
            </div>
          ))}
        </div>

        <div className="p-4 space-y-5">
          {/* Position in Quran — visual bar */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-600">{t('sma_position_in_quran', language)}</span>
              <span className="text-xs text-gray-500">
                {displayNum(surah.surahNumber, language)} / {displayNum(114, language)}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', positionBarColor(surah.quranPosition))}
                style={{ width: `${positionPct}%`, minWidth: '4px' }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {positionLabel(surah.quranPosition, language)}
            </div>
          </div>

          {/* Relative length bar */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs font-medium text-gray-600">{t('sma_relative_length', language)}</span>
              <span className="text-xs text-gray-500">
                {displayNum(surah.ayahCount, language)} {t('sma_ayahs_short', language)}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-400 rounded-full transition-all"
                style={{ width: `${lengthPct}%`, minWidth: '4px' }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {lengthLabel(surah.lengthCategory, language)}
            </div>
          </div>

          {/* Opening verse */}
          {surah.firstAyahPreview && (
            <div>
              <div className="text-xs font-medium text-gray-600 mb-2">
                {t('sma_first_preview', language)}
                <span className="text-gray-400 ms-1.5 font-normal">{surah.firstAyahRef}</span>
              </div>
              <div
                className="font-mushaf text-gray-800 text-lg leading-loose bg-gray-50 rounded-lg p-3 border border-gray-100"
                dir="rtl"
              >
                {surah.firstAyahPreview}
              </div>
              <div className="flex gap-2 mt-2 flex-wrap">
                <Link
                  to={`/quran/${surah.surahNumber}?aya=1`}
                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <BookOpen className="w-3 h-3" />
                  {t('sma_read_verse', language)}
                </Link>
                <Link
                  to={`/mushaf?page=${surah.pageStart}`}
                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                  {t('sma_open_in_mushaf', language)} ({t('sma_pages_abbr', language)}{displayNum(surah.pageStart, language)})
                </Link>
              </div>
            </div>
          )}

          {/* Closing verse */}
          {surah.lastAyahPreview && (
            <div>
              <div className="text-xs font-medium text-gray-600 mb-2">
                {t('sma_last_preview', language)}
                <span className="text-gray-400 ms-1.5 font-normal">{surah.lastAyahRef}</span>
              </div>
              <div
                className="font-mushaf text-gray-800 text-lg leading-loose bg-gray-50 rounded-lg p-3 border border-gray-100"
                dir="rtl"
              >
                {surah.lastAyahPreview}
              </div>
              <div className="flex gap-2 mt-2">
                <Link
                  to={`/quran/${surah.surahNumber}?aya=${surah.ayahCount}`}
                  className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <BookOpen className="w-3 h-3" />
                  {t('sma_read_verse', language)}
                </Link>
              </div>
            </div>
          )}

          {/* Memory aid */}
          {clue && (
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Brain className="w-3.5 h-3.5 text-amber-600" />
                <span className="text-xs font-medium text-amber-800">{t('sma_memory_aid', language)}</span>
              </div>
              <p
                className={clsx('text-sm text-amber-900', language === 'ar' ? 'font-arabic' : '')}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                {clue}
              </p>
            </div>
          )}

          {/* Read full surah CTA */}
          <Link
            to={`/quran/${surah.surahNumber}`}
            className={clsx(
              'flex items-center justify-center gap-2 w-full py-2.5 rounded-lg text-sm font-medium transition-colors',
              surah.revelationType === 'makki'
                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                : surah.revelationType === 'madani'
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-slate-600 hover:bg-slate-700 text-white',
            )}
          >
            <BookOpen className="w-4 h-4" />
            {t('sma_read_full_surah', language)}
          </Link>

          {/* Before / After navigation */}
          <div className="border-t border-gray-100 pt-4">
            <div className="text-xs font-medium text-gray-500 mb-2">{t('sma_before_after', language)}</div>
            <div className="grid grid-cols-2 gap-2">
              {/* Previous */}
              <div>
                <div className="text-[10px] text-gray-400 mb-1">{t('sma_before_surah', language)}</div>
                {prevSurah ? (
                  <button
                    onClick={() => onNavigate(prevSurah.surahNumber)}
                    className="w-full text-start p-2 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all"
                  >
                    <div className="text-xs text-gray-500">
                      {displayNum(prevSurah.surahNumber, language)}
                    </div>
                    <div className="font-arabic text-sm text-gray-800 leading-snug" dir="rtl">
                      {prevSurah.nameArabic}
                    </div>
                    {language === 'en' && (
                      <div className="text-[10px] text-gray-400 truncate" dir="ltr">
                        {prevSurah.nameTransliteration}
                      </div>
                    )}
                  </button>
                ) : (
                  <div className="p-2 rounded-lg border border-dashed border-gray-100 text-center text-[10px] text-gray-300">
                    {t('sma_first_surah', language)}
                  </div>
                )}
              </div>

              {/* Next */}
              <div>
                <div className="text-[10px] text-gray-400 mb-1">{t('sma_after_surah', language)}</div>
                {nextSurah ? (
                  <button
                    onClick={() => onNavigate(nextSurah.surahNumber)}
                    className="w-full text-start p-2 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all"
                  >
                    <div className="text-xs text-gray-500">
                      {displayNum(nextSurah.surahNumber, language)}
                    </div>
                    <div className="font-arabic text-sm text-gray-800 leading-snug" dir="rtl">
                      {nextSurah.nameArabic}
                    </div>
                    {language === 'en' && (
                      <div className="text-[10px] text-gray-400 truncate" dir="ltr">
                        {nextSurah.nameTransliteration}
                      </div>
                    )}
                  </button>
                ) : (
                  <div className="p-2 rounded-lg border border-dashed border-gray-100 text-center text-[10px] text-gray-300">
                    {t('sma_last_surah', language)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Keyboard hint */}
          <div className="text-center text-[10px] text-gray-300 pb-2">
            {t('sma_keyboard_hint', language)}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// QuizPanel
// ---------------------------------------------------------------------------

function QuizPanel({ surahs, language }: { surahs: SurahMemoryItem[]; language: 'ar' | 'en' }) {
  const [question, setQuestion] = useState<QuizQuestion>(() => generateQuestion(surahs));
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  const nextQuestion = useCallback(() => {
    setQuestion(generateQuestion(surahs));
    setRevealed(false);
  }, [surahs]);

  const handleCorrect = useCallback(() => {
    setScore(s => ({ correct: s.correct + 1, total: s.total + 1 }));
    nextQuestion();
  }, [nextQuestion]);

  const handleIncorrect = useCallback(() => {
    setScore(s => ({ ...s, total: s.total + 1 }));
    nextQuestion();
  }, [nextQuestion]);

  function questionText(): string {
    const { type, surah } = question;
    const name = language === 'ar' ? surah.nameArabic : surah.nameTransliteration;

    if (type === 'before') return `${t('sma_quiz_q_before', language)} "${name}"`;
    if (type === 'after') return `${t('sma_quiz_q_after', language)} "${name}"`;
    if (type === 'type') return `"${name}" — ${t('sma_quiz_q_type', language)}`;
    if (type === 'length') return `"${name}" — ${t('sma_quiz_q_length', language)}`;
    if (type === 'number') return `${t('sma_quiz_q_number', language)} "${name}"`;
    return `${t('sma_quiz_q_name', language)} ${displayNum(question.surah.surahNumber, language)}`;
  }

  function answerText(): string {
    const { type, surah, correctAnswer } = question;
    if (type === 'type') return revelationLabel(surah.revelationType, language);
    if (type === 'length') return lengthLabel(surah.lengthCategory, language);
    if (type === 'number') return displayNum(surah.surahNumber, language);
    if (correctAnswer === 'none') return language === 'ar' ? 'لا توجد' : 'None';
    if (type === 'name') {
      return language === 'ar' ? surah.nameArabic : surah.nameTransliteration;
    }
    // before/after — find the actual surah
    const targetNum = type === 'before' ? surah.surahNumber - 1 : surah.surahNumber + 1;
    const target = surahs.find(s => s.surahNumber === targetNum);
    if (!target) return language === 'ar' ? 'لا توجد' : 'None';
    return language === 'ar' ? target.nameArabic : target.nameTransliteration;
  }

  return (
    <div className="max-w-xl mx-auto py-8 px-4">
      {/* Score */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{t('sma_test_yourself', language)}</h2>
        <div className="flex items-center gap-2 bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-sm font-medium">
          <span>{t('sma_score', language)}:</span>
          <span className="font-bold">
            {displayNum(score.correct, language)} / {displayNum(score.total, language)}
          </span>
        </div>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Surah header strip */}
        <div className={clsx(
          'h-1.5 w-full bg-gradient-to-r',
          revelationGradient(question.surah.revelationType),
        )} />

        <div className="p-6">
          <p
            className={clsx(
              'text-lg font-medium text-gray-800 leading-relaxed mb-6',
              language === 'ar' ? 'text-right font-arabic' : 'text-left',
            )}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
          >
            {questionText()}
          </p>

          {!revealed ? (
            <button
              onClick={() => setRevealed(true)}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors"
            >
              {t('sma_show_answer', language)}
            </button>
          ) : (
            <div className="space-y-4">
              {/* Answer display */}
              <div className="bg-gray-50 rounded-xl p-4 text-center">
                <div
                  className={clsx(
                    'text-xl font-bold text-gray-900',
                    question.type === 'before' || question.type === 'after' || question.type === 'name'
                      ? 'font-arabic'
                      : '',
                  )}
                  dir="rtl"
                >
                  {answerText()}
                </div>
              </div>

              {/* Self-report buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleCorrect}
                  className="py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {t('sma_correct', language)}
                </button>
                <button
                  onClick={handleIncorrect}
                  className="py-2.5 rounded-xl bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {t('sma_try_again', language)}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Skip button */}
      <div className="text-center mt-4">
        <button
          onClick={nextQuestion}
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1 mx-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          {t('sma_next_question', language)}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export function SurahMemoryAtlasPage() {
  const { language } = useLanguageStore();
  const lang = language as 'ar' | 'en';
  const isRtl = lang === 'ar';

  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRevelation, setFilterRevelation] = useState<FilterRevelation>('all');
  const [filterLength, setFilterLength] = useState<FilterLength>('all');
  const [filterPosition, setFilterPosition] = useState<FilterPosition>('all');
  const [selectedNum, setSelectedNum] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Compute stats once
  const stats = useMemo(() => {
    const makki = SURAHS.filter(s => s.revelationType === 'makki').length;
    const madani = SURAHS.filter(s => s.revelationType === 'madani').length;
    return { makki, madani, unknown: SURAHS.length - makki - madani };
  }, []);

  // Filtered surahs
  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return SURAHS.filter(s => {
      if (filterRevelation !== 'all' && s.revelationType !== filterRevelation) return false;
      if (filterLength !== 'all' && s.lengthCategory !== filterLength) return false;
      if (filterPosition !== 'all' && s.quranPosition !== filterPosition) return false;
      if (!q) return true;
      const num = String(s.surahNumber);
      return (
        s.nameArabic.includes(q) ||
        s.nameTransliteration.toLowerCase().includes(q) ||
        (s.nameEnglish?.toLowerCase().includes(q) ?? false) ||
        num === q
      );
    });
  }, [searchQuery, filterRevelation, filterLength, filterPosition]);

  const selectedSurah = useMemo(
    () => (selectedNum !== null ? SURAHS.find(s => s.surahNumber === selectedNum) ?? null : null),
    [selectedNum],
  );

  const hasFilters = filterRevelation !== 'all' || filterLength !== 'all' || filterPosition !== 'all' || searchQuery !== '';

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterRevelation('all');
    setFilterLength('all');
    setFilterPosition('all');
  }, []);

  const selectSurah = useCallback((num: number) => {
    setSelectedNum(prev => (prev === num ? null : num));
  }, []);

  const closePanel = useCallback(() => setSelectedNum(null), []);

  // Keyboard navigation inside detail panel
  useEffect(() => {
    if (selectedNum === null) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || (isRtl && e.key === 'ArrowLeft')) {
        const next = SURAHS.find(s => s.surahNumber === selectedNum + 1);
        if (next) setSelectedNum(next.surahNumber);
      } else if (e.key === 'ArrowLeft' || (isRtl && e.key === 'ArrowRight')) {
        const prev = SURAHS.find(s => s.surahNumber === selectedNum - 1);
        if (prev) setSelectedNum(prev.surahNumber);
      } else if (e.key === 'Escape') {
        setSelectedNum(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedNum, isRtl]);

  // Scroll selected card into view
  useEffect(() => {
    if (selectedNum === null) return;
    const el = document.getElementById(`surah-card-${selectedNum}`);
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [selectedNum]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100" dir={isRtl ? 'rtl' : 'ltr'}>
      <div className="max-w-screen-2xl mx-auto px-3 sm:px-6 py-6">

        {/* ── Page header ─────────────────────────────────────────────── */}
        <div className="mb-5">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-indigo-600 rounded-xl text-white shrink-0">
              <LayoutGrid className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h1
                className={clsx('text-xl font-bold text-gray-900', lang === 'ar' ? 'font-arabic' : '')}
                dir={lang === 'ar' ? 'rtl' : 'ltr'}
              >
                {t('sma_title', lang)}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
                {t('sma_description', lang)}
              </p>
            </div>
          </div>

          {/* Stats strip */}
          <div className="flex flex-wrap gap-3 mt-3">
            <span className="text-xs bg-white border border-gray-200 px-2.5 py-1 rounded-full text-gray-600">
              {displayNum(114, lang)} {t('sma_all_114', lang).split(' ').pop()}
            </span>
            <span className="text-xs bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full text-amber-700">
              {displayNum(stats.makki, lang)} {t('sma_makki_label', lang)}
            </span>
            <span className="text-xs bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full text-emerald-700">
              {displayNum(stats.madani, lang)} {t('sma_madani_label', lang)}
            </span>
          </div>
        </div>

        {/* ── View tabs ───────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 mb-4 bg-white border border-gray-200 rounded-xl p-1 w-fit">
          {([
            { mode: 'grid' as ViewMode, label: t('sma_grid_view', lang), Icon: LayoutGrid },
            { mode: 'quiz' as ViewMode, label: t('sma_quiz_mode', lang), Icon: Brain },
          ] as const).map(({ mode, label, Icon }) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={clsx(
                'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                viewMode === mode
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50',
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* ── Quiz view ───────────────────────────────────────────────── */}
        {viewMode === 'quiz' && <QuizPanel surahs={SURAHS} language={lang} />}

        {/* ── Grid view ───────────────────────────────────────────────── */}
        {viewMode === 'grid' && (
          <>
            {/* Search + filter bar */}
            <div className="mb-4 space-y-2">
              <div className="flex gap-2">
                {/* Search */}
                <div className="relative flex-1">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder={t('sma_search_placeholder', lang)}
                    dir={lang === 'ar' ? 'rtl' : 'ltr'}
                    className="w-full ps-9 pe-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
                  />
                </div>

                {/* Filter toggle */}
                <button
                  onClick={() => setShowFilters(f => !f)}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-2.5 rounded-xl border text-sm font-medium transition-colors',
                    showFilters || hasFilters
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50',
                  )}
                >
                  <Filter className="w-4 h-4" />
                  {t('sma_filter_revelation', lang)}
                  {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />}
                </button>

                {/* Clear */}
                {hasFilters && (
                  <button
                    onClick={clearFilters}
                    className="flex items-center gap-1 px-3 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-500 hover:bg-gray-50 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    {t('sma_clear_filters', lang)}
                  </button>
                )}
              </div>

              {/* Expanded filters */}
              {showFilters && (
                <div className="bg-white border border-gray-200 rounded-xl p-3 space-y-3">
                  {/* Revelation type */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_revelation', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['makki', t('sma_makki', lang)] as const,
                        ['madani', t('sma_madani', lang)] as const,
                        ['unknown', t('sma_unknown', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterRevelation(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterRevelation === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Length */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_length', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['short', t('sma_short', lang)] as const,
                        ['medium', t('sma_medium', lang)] as const,
                        ['long', t('sma_long', lang)] as const,
                        ['very_long', t('sma_very_long', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterLength(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterLength === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Position */}
                  <div>
                    <div className="text-xs font-medium text-gray-500 mb-1.5">{t('sma_filter_position', lang)}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {([
                        ['all', t('sma_filter_all', lang)] as const,
                        ['beginning', t('sma_beginning', lang)] as const,
                        ['early', t('sma_early', lang)] as const,
                        ['middle', t('sma_middle', lang)] as const,
                        ['late', t('sma_late', lang)] as const,
                        ['ending', t('sma_ending', lang)] as const,
                      ] as const).map(([v, label]) => (
                        <button
                          key={v}
                          onClick={() => setFilterPosition(v)}
                          className={clsx(
                            'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                            filterPosition === v
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300',
                          )}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Result count */}
              <div className="flex items-center justify-between text-xs text-gray-400 px-0.5">
                <span>
                  {displayNum(filtered.length, lang)} {t('sma_results_count', lang)}
                  {filtered.length < SURAHS.length && (
                    <span className="ms-1 text-gray-300">
                      / {displayNum(SURAHS.length, lang)}
                    </span>
                  )}
                </span>
                {filtered.length === 0 && (
                  <span className="text-gray-400">{t('sma_no_results', lang)}</span>
                )}
              </div>
            </div>

            {/* ── Grid + Detail panel layout ─────────────────────────── */}
            <div className="flex gap-4 items-start">
              {/* Grid */}
              <div className={clsx(
                'flex-1 min-w-0 transition-all duration-300',
                selectedSurah ? 'lg:max-w-[calc(100%-400px)]' : '',
              )}>
                {filtered.length > 0 ? (
                  <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 2xl:grid-cols-10 gap-2">
                    {filtered.map(s => (
                      <div key={s.surahNumber} id={`surah-card-${s.surahNumber}`}>
                        <SurahCard
                          surah={s}
                          selected={selectedNum === s.surahNumber}
                          onClick={() => selectSurah(s.surahNumber)}
                          language={lang}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16 text-gray-400">
                    <Search className="w-8 h-8 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">{t('sma_no_results', lang)}</p>
                    <button
                      onClick={clearFilters}
                      className="mt-3 text-indigo-500 hover:text-indigo-700 text-sm underline"
                    >
                      {t('sma_clear_filters', lang)}
                    </button>
                  </div>
                )}
              </div>

              {/* Desktop detail panel — sticky sidebar */}
              {selectedSurah && (
                <div
                  ref={panelRef}
                  className="hidden lg:flex flex-col w-[380px] flex-shrink-0 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden sticky top-4 max-h-[calc(100vh-5rem)]"
                >
                  <SurahDetailPanel
                    surah={selectedSurah}
                    surahs={SURAHS}
                    onClose={closePanel}
                    onNavigate={setSelectedNum}
                    language={lang}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Mobile bottom sheet ──────────────────────────────────────── */}
      {selectedSurah && viewMode === 'grid' && (
        <>
          {/* Backdrop */}
          <div
            className="lg:hidden fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
            onClick={closePanel}
          />
          {/* Sheet */}
          <div className="lg:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl max-h-[80vh] overflow-hidden flex flex-col">
            {/* Drag handle */}
            <div className="flex justify-center pt-3 pb-1 shrink-0">
              <div className="w-10 h-1 bg-gray-200 rounded-full" />
            </div>
            <div className="flex-1 overflow-y-auto">
              <SurahDetailPanel
                surah={selectedSurah}
                surahs={SURAHS}
                onClose={closePanel}
                onNavigate={setSelectedNum}
                language={lang}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
