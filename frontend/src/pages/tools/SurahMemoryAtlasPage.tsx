/**
 * Surah Memory Atlas — /tools/surah-memory-atlas
 *
 * Helps students remember the 114 surahs: their names, order, Makki/Madani
 * status, ayah counts, page ranges, and first/last ayah references.
 *
 * Content policy:
 * - All ayah text comes from surahMemoryAtlas.json (generated from quran_uthmani.json)
 * - No ayah text is hardcoded here
 * - Makki/Madani is from curated metadata; always shown with needs_review badge
 * - Topics and clues not shown when unavailable (missing_metadata)
 */

import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Search, BookOpen, ArrowLeft,
  AlertTriangle, CheckCircle, Info, RotateCcw, Brain,
  Map, List, X, Filter,
} from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';
import atlasData from '../../data/generated/surahMemoryAtlas.json';
import type { SurahMemoryItem, ReviewStatus, RevelationType, LengthCategory, QuranPosition } from '../../types/surahMemoryAtlas';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ViewMode = 'list' | 'map' | 'quiz';

interface QuizQuestion {
  type: 'before' | 'after' | 'type' | 'length' | 'number' | 'name';
  surah: SurahMemoryItem;
  correctAnswer: string;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const SURAHS: SurahMemoryItem[] = (atlasData as { surahs: SurahMemoryItem[] }).surahs;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function revelationColor(type: RevelationType) {
  if (type === 'makki') return { bg: 'bg-amber-100', text: 'text-amber-800', border: 'border-amber-200' };
  if (type === 'madani') return { bg: 'bg-emerald-100', text: 'text-emerald-800', border: 'border-emerald-200' };
  return { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200' };
}

function lengthColor(cat: LengthCategory) {
  if (cat === 'short') return 'bg-sky-100 text-sky-800';
  if (cat === 'medium') return 'bg-violet-100 text-violet-800';
  if (cat === 'long') return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
}

function positionColor(pos: QuranPosition) {
  if (pos === 'beginning') return 'bg-teal-100 text-teal-800';
  if (pos === 'early') return 'bg-cyan-100 text-cyan-800';
  if (pos === 'middle') return 'bg-blue-100 text-blue-800';
  if (pos === 'late') return 'bg-indigo-100 text-indigo-800';
  return 'bg-purple-100 text-purple-800';
}

function reviewStatusBadge(status: ReviewStatus, language: 'ar' | 'en') {
  if (status === 'verified') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
        <CheckCircle className="w-3 h-3" />
        {t('sma_verified', language)}
      </span>
    );
  }
  if (status === 'needs_review') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
        <AlertTriangle className="w-3 h-3" />
        {t('sma_review_required', language)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
      <Info className="w-3 h-3" />
      {t('sma_data_missing', language)}
    </span>
  );
}

function labelRevelationType(type: RevelationType, language: 'ar' | 'en'): string {
  if (type === 'makki') return t('sma_makki', language);
  if (type === 'madani') return t('sma_madani', language);
  return t('sma_unknown', language);
}

function labelLength(cat: LengthCategory, language: 'ar' | 'en'): string {
  if (cat === 'short') return t('sma_short', language);
  if (cat === 'medium') return t('sma_medium', language);
  if (cat === 'long') return t('sma_long', language);
  return t('sma_very_long', language);
}

function labelPosition(pos: QuranPosition, language: 'ar' | 'en'): string {
  if (pos === 'beginning') return t('sma_beginning', language);
  if (pos === 'early') return t('sma_early', language);
  if (pos === 'middle') return t('sma_middle', language);
  if (pos === 'late') return t('sma_late', language);
  return t('sma_ending', language);
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
// Sub-components
// ---------------------------------------------------------------------------

function ReviewNotice({ status, language }: { status: ReviewStatus; language: 'ar' | 'en' }) {
  if (status === 'verified') return null;
  const isRtl = language === 'ar';
  return (
    <div
      className={clsx(
        'flex items-start gap-2 rounded-lg border px-3 py-2 text-sm',
        status === 'needs_review'
          ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
          : 'bg-gray-50 border-gray-200 text-gray-600'
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{status === 'needs_review' ? t('sma_needs_review', language) : t('sma_metadata_unavailable', language)}</span>
    </div>
  );
}

function SurahCard({
  surah,
  selected,
  onClick,
  language,
}: {
  surah: SurahMemoryItem;
  selected: boolean;
  onClick: () => void;
  language: 'ar' | 'en';
}) {
  const rev = revelationColor(surah.revelationType);
  const isRtl = language === 'ar';
  return (
    <button
      onClick={onClick}
      dir={isRtl ? 'rtl' : 'ltr'}
      className={clsx(
        'w-full text-start rounded-lg border-2 p-2 transition-all hover:shadow-md cursor-pointer',
        selected ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 bg-white hover:border-emerald-300'
      )}
    >
      <div className="flex items-center gap-2">
        <span className="w-7 h-7 shrink-0 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-700">
          {surah.surahNumber}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-gray-900 truncate font-arabic leading-tight" dir="rtl">
            {surah.nameArabic.replace(/^سُورَةُ\s+/, '').replace(/^سورة\s+/, '')}
          </p>
          <p className="text-xs text-gray-500 truncate">{surah.nameTransliteration}</p>
        </div>
        <span className={clsx('text-xs px-1.5 py-0.5 rounded border shrink-0', rev.bg, rev.text, rev.border)}>
          {labelRevelationType(surah.revelationType, language).split(' ')[0]}
        </span>
      </div>
    </button>
  );
}

function DetailPanel({ surah, language }: { surah: SurahMemoryItem; language: 'ar' | 'en' }) {
  const isRtl = language === 'ar';
  const prevSurah = SURAHS.find(s => s.surahNumber === surah.surahNumber - 1);
  const nextSurah = SURAHS.find(s => s.surahNumber === surah.surahNumber + 1);
  const rev = revelationColor(surah.revelationType);

  return (
    <div className="space-y-4" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">
              {t('sma_surah_number', language)}: {surah.surahNumber}
            </p>
            <h2 className="text-2xl font-bold text-gray-900 font-arabic leading-tight" dir="rtl">
              {surah.nameArabic}
            </h2>
            <p className="text-base text-gray-600 mt-0.5">{surah.nameTransliteration}</p>
            {surah.nameEnglish && (
              <p className="text-sm text-gray-500 italic" dir="ltr">"{surah.nameEnglish}"</p>
            )}
          </div>
          {reviewStatusBadge(surah.reviewStatus, language)}
        </div>
        <ReviewNotice status={surah.reviewStatus} language={language} />
      </div>

      {/* Key facts */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_revelation_type', language)}</p>
          <span className={clsx('inline-block text-sm font-medium px-2 py-0.5 rounded border', rev.bg, rev.text, rev.border)}>
            {labelRevelationType(surah.revelationType, language)}
          </span>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_ayah_count', language)}</p>
          <p className="text-sm font-semibold text-gray-900">{surah.ayahCount}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_length', language)}</p>
          <span className={clsx('inline-block text-xs font-medium px-2 py-0.5 rounded', lengthColor(surah.lengthCategory))}>
            {labelLength(surah.lengthCategory, language)}
          </span>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_quran_position', language)}</p>
          <span className={clsx('inline-block text-xs font-medium px-2 py-0.5 rounded', positionColor(surah.quranPosition))}>
            {labelPosition(surah.quranPosition, language)}
          </span>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_juz', language)}</p>
          <p className="text-sm font-semibold text-gray-900">
            {surah.juzStart === surah.juzEnd
              ? surah.juzStart
              : `${surah.juzStart} ${t('sma_to', language)} ${surah.juzEnd}`}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-500 mb-1">{t('sma_page_range', language)}</p>
          <p className="text-sm font-semibold text-gray-900">
            {surah.pageStart === surah.pageEnd
              ? `${t('sma_page', language)} ${surah.pageStart}`
              : `${t('sma_page', language)} ${surah.pageStart} ${t('sma_to', language)} ${surah.pageEnd}`}
          </p>
        </div>
      </div>

      {/* Ayah previews */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">{t('sma_first_ayah', language)} — {surah.firstAyahRef}</h3>
        {surah.firstAyahPreview ? (
          <p className="text-base font-arabic leading-loose text-gray-900 bg-gray-50 rounded-lg p-3" dir="rtl">
            {surah.firstAyahPreview}
          </p>
        ) : (
          <p className="text-sm text-gray-400 italic">{t('sma_data_missing', language)}</p>
        )}
        <h3 className="text-sm font-semibold text-gray-700">{t('sma_last_ayah', language)} — {surah.lastAyahRef}</h3>
        {surah.lastAyahPreview ? (
          <p className="text-base font-arabic leading-loose text-gray-900 bg-gray-50 rounded-lg p-3" dir="rtl">
            {surah.lastAyahPreview}
          </p>
        ) : (
          <p className="text-sm text-gray-400 italic">{t('sma_data_missing', language)}</p>
        )}
      </div>

      {/* Memory helpers */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">{t('sma_position_clue', language)}</h3>
        <p className="text-sm text-gray-700">
          {language === 'ar'
            ? `هي السورة رقم ${surah.surahNumber} في القرآن الكريم — موضعها: ${labelPosition(surah.quranPosition, language)}`
            : `Surah #${surah.surahNumber} of 114 — Position: ${labelPosition(surah.quranPosition, language)}`}
        </p>
        <h3 className="text-sm font-semibold text-gray-700 mt-2">{t('sma_length_clue', language)}</h3>
        <p className="text-sm text-gray-700">
          {language === 'ar'
            ? `تتكون من ${surah.ayahCount} آية — ${labelLength(surah.lengthCategory, language)}`
            : `${surah.ayahCount} ayahs — ${labelLength(surah.lengthCategory, language)}`}
        </p>
        {(surah.mainTopicsArabic.length > 0 || surah.mainTopicsEnglish.length > 0) && (
          <>
            <h3 className="text-sm font-semibold text-gray-700 mt-2">{t('sma_topic_clue', language)}</h3>
            <div className="flex flex-wrap gap-1">
              {(language === 'ar' ? surah.mainTopicsArabic : surah.mainTopicsEnglish).map((topic, i) => (
                <span key={i} className="px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 text-xs">{topic}</span>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Before / After */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('sma_before_after', language)}</h3>
        <div className="flex gap-3">
          <div className="flex-1 text-center">
            <p className="text-xs text-gray-500 mb-1">{t('sma_previous_surah', language)}</p>
            {prevSurah ? (
              <p className="text-sm font-semibold text-gray-900">
                {prevSurah.surahNumber}. {prevSurah.nameTransliteration}
              </p>
            ) : (
              <p className="text-sm text-gray-400">—</p>
            )}
          </div>
          <div className="w-px bg-gray-200" />
          <div className="flex-1 text-center">
            <p className="text-xs text-gray-500 mb-1">{t('sma_next_surah', language)}</p>
            {nextSurah ? (
              <p className="text-sm font-semibold text-gray-900">
                {nextSurah.surahNumber}. {nextSurah.nameTransliteration}
              </p>
            ) : (
              <p className="text-sm text-gray-400">—</p>
            )}
          </div>
        </div>
      </div>

      {/* Link to Quran reader */}
      <Link
        to={`/quran/${surah.surahNumber}`}
        className="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-colors"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <BookOpen className="w-4 h-4" />
        {language === 'ar' ? `اقرأ سورة ${surah.nameArabic.replace(/^سُورَةُ\s+/, '')}` : `Read ${surah.nameTransliteration}`}
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Visual Map Section
// ---------------------------------------------------------------------------

const POSITION_GROUPS: { key: QuranPosition; label_ar: string; label_en: string }[] = [
  { key: 'beginning', label_ar: 'البداية (١–١٠)', label_en: 'Beginning (1–10)' },
  { key: 'early', label_ar: 'أوائل (١١–٣٠)', label_en: 'Early (11–30)' },
  { key: 'middle', label_ar: 'وسط (٣١–٧٠)', label_en: 'Middle (31–70)' },
  { key: 'late', label_ar: 'أواخر (٧١–١٠٠)', label_en: 'Late (71–100)' },
  { key: 'ending', label_ar: 'الخواتيم (١٠١–١١٤)', label_en: 'Ending (101–114)' },
];

function VisualMapView({
  surahs,
  selected,
  onSelect,
  language,
}: {
  surahs: SurahMemoryItem[];
  selected: SurahMemoryItem | null;
  onSelect: (s: SurahMemoryItem) => void;
  language: 'ar' | 'en';
}) {
  const isRtl = language === 'ar';
  return (
    <div className="space-y-6" dir={isRtl ? 'rtl' : 'ltr'}>
      {POSITION_GROUPS.map(group => {
        const groupSurahs = surahs.filter(s => s.quranPosition === group.key);
        if (groupSurahs.length === 0) return null;
        return (
          <div key={group.key}>
            <div className="flex items-center gap-2 mb-2">
              <span className={clsx('px-2 py-0.5 rounded text-xs font-semibold', positionColor(group.key))}>
                {language === 'ar' ? group.label_ar : group.label_en}
              </span>
              <span className="text-xs text-gray-400">{groupSurahs.length}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {groupSurahs.map(surah => {
                const rev = revelationColor(surah.revelationType);
                return (
                  <button
                    key={surah.surahNumber}
                    onClick={() => onSelect(surah)}
                    title={`${surah.surahNumber}. ${surah.nameTransliteration}`}
                    className={clsx(
                      'flex flex-col items-center justify-center rounded-lg border-2 p-1.5 transition-all hover:shadow-md w-16 h-16',
                      selected?.surahNumber === surah.surahNumber
                        ? 'border-emerald-500 bg-emerald-50'
                        : clsx('border', rev.border, rev.bg, 'hover:border-emerald-300')
                    )}
                  >
                    <span className="text-xs font-bold text-gray-700">{surah.surahNumber}</span>
                    <span className="text-xs font-arabic text-center leading-tight truncate w-full" dir="rtl" style={{ fontSize: '10px' }}>
                      {surah.nameArabic.replace(/^سُورَةُ\s+/, '').replace(/^سورة\s+/, '')}
                    </span>
                    <span className="text-xs text-gray-500 leading-tight" style={{ fontSize: '9px' }}>
                      {surah.ayahCount}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quiz Mode
// ---------------------------------------------------------------------------

function QuizMode({ language }: { language: 'ar' | 'en' }) {
  const isRtl = language === 'ar';
  const [question, setQuestion] = useState<QuizQuestion>(() => generateQuestion(SURAHS));
  const [revealed, setRevealed] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  const nextQuestion = useCallback(() => {
    setQuestion(generateQuestion(SURAHS));
    setRevealed(false);
  }, []);

  const handleResult = useCallback((correct: boolean) => {
    setScore(prev => ({
      correct: prev.correct + (correct ? 1 : 0),
      total: prev.total + 1,
    }));
    setRevealed(true);
  }, []);

  const surahLabel = language === 'ar'
    ? question.surah.nameArabic
    : question.surah.nameTransliteration;

  function questionText() {
    switch (question.type) {
      case 'before': return `${t('sma_quiz_q_before', language)} [${surahLabel}]`;
      case 'after': return `${t('sma_quiz_q_after', language)} [${surahLabel}]`;
      case 'type': return `[${surahLabel}] — ${t('sma_quiz_q_type', language)}`;
      case 'length': return `[${surahLabel}] — ${t('sma_quiz_q_length', language)}`;
      case 'number': return `${t('sma_quiz_q_name', language)} [${surahLabel}]?`;
      case 'name': return `${t('sma_quiz_q_number', language)} [${question.surah.surahNumber}]?`;
    }
  }

  function answerLabel() {
    if (question.type === 'type') return labelRevelationType(question.correctAnswer as RevelationType, language);
    if (question.type === 'length') return labelLength(question.correctAnswer as LengthCategory, language);
    if (question.type === 'name') return SURAHS.find(s => s.surahNumber === question.surah.surahNumber)?.nameTransliteration ?? '';
    if (question.correctAnswer === 'none') return language === 'ar' ? 'لا توجد' : 'None';
    return question.correctAnswer;
  }

  return (
    <div className="max-w-lg mx-auto" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Score */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">{t('sma_quiz_mode', language)}</h2>
        {score.total > 0 && (
          <span className="text-sm text-gray-600">
            {t('sma_score', language)}: {score.correct}/{score.total}
          </span>
        )}
      </div>

      {/* Question card */}
      <div className="bg-white rounded-xl border-2 border-gray-200 p-6 shadow-sm">
        <p className="text-xs font-medium text-gray-500 mb-2">{t('sma_test_yourself', language)}</p>
        <p className="text-lg font-semibold text-gray-900 mb-6 leading-relaxed">{questionText()}</p>

        {!revealed ? (
          <div className="space-y-2">
            <button
              onClick={() => handleResult(true)}
              className="w-full py-2.5 rounded-lg bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 transition-colors"
            >
              {t('sma_show_answer', language)}
            </button>
            <p className="text-xs text-center text-gray-400">
              {language === 'ar' ? 'حاول تذكّر الإجابة قبل الكشف' : 'Try to recall the answer before revealing'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-center">
              <p className="text-xs text-emerald-700 mb-1">{language === 'ar' ? 'الإجابة' : 'Answer'}</p>
              <p className="text-base font-bold text-emerald-900">{answerLabel()}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { handleResult(false); nextQuestion(); }}
                className="flex-1 py-2 rounded-lg border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                {t('sma_try_again', language)}
              </button>
              <button
                onClick={() => { handleResult(true); nextQuestion(); }}
                className="flex-1 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-colors"
              >
                {t('sma_correct', language)} → {t('sma_next_question', language)}
              </button>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={nextQuestion}
        className="mt-3 w-full flex items-center justify-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <RotateCcw className="w-3 h-3" /> {language === 'ar' ? 'سؤال آخر' : 'Different question'}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export function SurahMemoryAtlasPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [query, setQuery] = useState('');
  const [filterRev, setFilterRev] = useState<'all' | RevelationType>('all');
  const [filterLen, setFilterLen] = useState<'all' | LengthCategory>('all');
  const [filterPos, setFilterPos] = useState<'all' | QuranPosition>('all');
  const [selected, setSelected] = useState<SurahMemoryItem | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  const filtered = useMemo(() => {
    return SURAHS.filter(s => {
      if (filterRev !== 'all' && s.revelationType !== filterRev) return false;
      if (filterLen !== 'all' && s.lengthCategory !== filterLen) return false;
      if (filterPos !== 'all' && s.quranPosition !== filterPos) return false;
      if (query.trim()) {
        const q = query.toLowerCase();
        const num = s.surahNumber.toString();
        const translit = s.nameTransliteration.toLowerCase();
        const nameEn = (s.nameEnglish ?? '').toLowerCase();
        const nameAr = s.nameArabic;
        if (
          !num.includes(q) &&
          !translit.includes(q) &&
          !nameEn.includes(q) &&
          !nameAr.includes(query)
        ) return false;
      }
      return true;
    });
  }, [query, filterRev, filterLen, filterPos]);

  const hasFilters = query || filterRev !== 'all' || filterLen !== 'all' || filterPos !== 'all';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <Link to="/tools" className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
            <ArrowLeft className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
            {language === 'ar' ? 'الأدوات' : 'Tools'}
          </Link>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          {t('sma_title', language)}
        </h1>
        <p className="text-gray-500 mt-1 text-sm">{t('sma_description', language)}</p>
      </div>

      {/* View mode tabs */}
      <div className="flex items-center gap-2 mb-5 border-b border-gray-200">
        {[
          { key: 'list' as ViewMode, icon: List, label: t('sma_list_view', language) },
          { key: 'map' as ViewMode, icon: Map, label: t('sma_map_view', language) },
          { key: 'quiz' as ViewMode, icon: Brain, label: t('sma_quiz_mode', language) },
        ].map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            onClick={() => setViewMode(key)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              viewMode === key
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Quiz mode */}
      {viewMode === 'quiz' && <QuizMode language={language} />}

      {/* List / Map mode */}
      {viewMode !== 'quiz' && (
        <div className="flex flex-col lg:flex-row gap-5">
          {/* Left panel: search + list/map */}
          <div className="lg:w-96 shrink-0 space-y-3">
            {/* Search */}
            <div className="relative">
              <Search className={clsx('absolute top-2.5 w-4 h-4 text-gray-400', isRtl ? 'right-3' : 'left-3')} />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder={t('sma_search_placeholder', language)}
                dir={isRtl ? 'rtl' : 'ltr'}
                className={clsx(
                  'w-full rounded-lg border border-gray-300 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500',
                  isRtl ? 'pr-9 pl-3' : 'pl-9 pr-3'
                )}
              />
            </div>

            {/* Filters */}
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-3 space-y-2">
              <div className="flex items-center gap-1 text-xs font-semibold text-gray-600 mb-1">
                <Filter className="w-3 h-3" />
                {language === 'ar' ? 'تصفية' : 'Filters'}
                {hasFilters && (
                  <button onClick={() => { setQuery(''); setFilterRev('all'); setFilterLen('all'); setFilterPos('all'); }} className="text-emerald-600 hover:text-emerald-800 flex items-center gap-0.5">
                    <X className="w-3 h-3" /> {t('sma_clear_filters', language)}
                  </button>
                )}
              </div>

              {/* Revelation type filter */}
              <div>
                <p className="text-xs text-gray-500 mb-1">{t('sma_filter_revelation', language)}</p>
                <div className="flex flex-wrap gap-1">
                  {(['all', 'makki', 'madani', 'unknown'] as const).map(v => (
                    <button
                      key={v}
                      onClick={() => setFilterRev(v)}
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium border transition-colors',
                        filterRev === v
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-emerald-400'
                      )}
                    >
                      {v === 'all' ? t('sma_filter_all', language) :
                       v === 'makki' ? t('sma_makki', language) :
                       v === 'madani' ? t('sma_madani', language) :
                       t('sma_unknown', language)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Length filter */}
              <div>
                <p className="text-xs text-gray-500 mb-1">{t('sma_filter_length', language)}</p>
                <div className="flex flex-wrap gap-1">
                  {(['all', 'short', 'medium', 'long', 'very_long'] as const).map(v => (
                    <button
                      key={v}
                      onClick={() => setFilterLen(v)}
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium border transition-colors',
                        filterLen === v
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-emerald-400'
                      )}
                    >
                      {v === 'all' ? t('sma_filter_all', language) :
                       v === 'short' ? t('sma_short', language) :
                       v === 'medium' ? t('sma_medium', language) :
                       v === 'long' ? t('sma_long', language) :
                       t('sma_very_long', language)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Position filter */}
              <div>
                <p className="text-xs text-gray-500 mb-1">{t('sma_filter_position', language)}</p>
                <div className="flex flex-wrap gap-1">
                  {(['all', 'beginning', 'early', 'middle', 'late', 'ending'] as const).map(v => (
                    <button
                      key={v}
                      onClick={() => setFilterPos(v)}
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium border transition-colors',
                        filterPos === v
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-emerald-400'
                      )}
                    >
                      {v === 'all' ? t('sma_filter_all', language) :
                       v === 'beginning' ? t('sma_beginning', language) :
                       v === 'early' ? t('sma_early', language) :
                       v === 'middle' ? t('sma_middle', language) :
                       v === 'late' ? t('sma_late', language) :
                       t('sma_ending', language)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Result count */}
            <p className="text-xs text-gray-500">
              {filtered.length} {t('sma_results_count', language)}
            </p>

            {/* List / map content */}
            {viewMode === 'list' && (
              <div className="space-y-1.5 max-h-[60vh] overflow-y-auto pr-1">
                {filtered.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-6">{t('sma_no_results', language)}</p>
                ) : (
                  filtered.map(s => (
                    <SurahCard
                      key={s.surahNumber}
                      surah={s}
                      selected={selected?.surahNumber === s.surahNumber}
                      onClick={() => setSelected(s)}
                      language={language}
                    />
                  ))
                )}
              </div>
            )}
          </div>

          {/* Right panel: detail or map */}
          <div className="flex-1 min-w-0">
            {viewMode === 'map' ? (
              <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 overflow-auto max-h-[80vh]">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">{t('sma_visual_map_title', language)}</h2>
                <VisualMapView
                  surahs={filtered}
                  selected={selected}
                  onSelect={setSelected}
                  language={language}
                />
              </div>
            ) : selected ? (
              <DetailPanel surah={selected} language={language} />
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center text-gray-400">
                <BookOpen className="w-12 h-12 mb-3 opacity-30" />
                <p className="text-sm">{t('sma_select_surah_prompt', language)}</p>
              </div>
            )}

            {/* Detail panel when map view and surah selected */}
            {viewMode === 'map' && selected && (
              <div className="mt-4">
                <DetailPanel surah={selected} language={language} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
