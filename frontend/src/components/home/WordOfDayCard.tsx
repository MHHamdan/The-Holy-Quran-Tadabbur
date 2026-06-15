/**
 * Word of the Day card — Quranic vocabulary widget.
 *
 * Displays a daily vocabulary entry with Arabic word, meaning,
 * contextual note, memory hint, and a link to the example verse.
 *
 * Safety: all meanings sourced from classical lexica (Lane's Lexicon,
 * QAC Corpus, Ibn Kathir). No AI-generated definitions.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Lightbulb, ChevronRight, RotateCcw, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { getTodayWord, WORD_OF_DAY_VOCAB } from '../../data/wordOfDayVocab';

function getWordForDate(dateStr: string) {
  return getTodayWord(dateStr);
}

const TODAY = new Date().toISOString().slice(0, 10);

export function WordOfDayCard() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [showHint, setShowHint] = useState(false);
  const [word] = useState(() => getWordForDate(TODAY));

  const totalWords = WORD_OF_DAY_VOCAB.length;

  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-teal-200 bg-gradient-to-br from-teal-50 via-emerald-50 to-cyan-50 p-5"
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Decorative orb */}
      <div className="absolute -top-4 -right-4 w-24 h-24 rounded-full bg-teal-100/70 blur-2xl pointer-events-none" />

      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-4', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <div className="w-7 h-7 rounded-lg bg-teal-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <p className={clsx('text-xs font-semibold text-teal-700 uppercase tracking-wide', isRtl && 'font-arabic')}>
              {isRtl ? 'كلمة اليوم' : 'Word of the Day'}
            </p>
            <p className="text-[10px] text-gray-400">
              {isRtl ? `${totalWords} كلمة قرآنية` : `${totalWords} Quranic words`}
            </p>
          </div>
        </div>
        <span className="text-[10px] text-gray-400 tabular-nums">{TODAY}</span>
      </div>

      {/* Arabic word (large) */}
      <div className={clsx('mb-3', isRtl ? 'text-right' : 'text-left')}>
        <p className="text-4xl font-arabic font-bold text-teal-800 mb-0.5 leading-none" dir="rtl">
          {word.arabic}
        </p>
        <p className="text-sm text-gray-500 mt-1 italic">{word.transliteration}</p>
        <div className={clsx('flex items-center gap-2 mt-1 flex-wrap', isRtl && 'flex-row-reverse')}>
          <span className="text-[10px] bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full font-medium">
            {word.partOfSpeech}
          </span>
          <span className="text-[10px] text-gray-400" dir="rtl">
            {word.root}
          </span>
          <span className="text-[10px] text-gray-400">
            ×{word.frequencyInQuran} {isRtl ? 'في القرآن' : 'in Quran'}
          </span>
        </div>
      </div>

      {/* Meaning */}
      <div className="mb-3 bg-white/60 rounded-xl p-3">
        <p className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic text-right')}>
          {isRtl ? word.simpleMeaningAr : word.simpleMeaningEn}
        </p>
        <p className={clsx('text-xs text-gray-600 mt-1 leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl ? word.contextualNoteAr : word.contextualNoteEn}
        </p>
      </div>

      {/* Memory hint (collapsible) */}
      <div className="mb-3">
        <button
          onClick={() => setShowHint(v => !v)}
          className={clsx(
            'flex items-center gap-1.5 text-xs text-amber-700 hover:text-amber-900 transition-colors w-full',
            isRtl && 'flex-row-reverse'
          )}
        >
          <Lightbulb className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
          <span className={clsx(isRtl && 'font-arabic')}>
            {showHint
              ? isRtl ? 'إخفاء مساعدة الحفظ' : 'Hide memory hint'
              : isRtl ? 'مساعدة على الحفظ' : 'Memory hint'}
          </span>
          <RotateCcw className={clsx('w-3 h-3 ms-auto text-gray-300 transition-transform', showHint && 'rotate-180')} />
        </button>
        {showHint && (
          <p className={clsx(
            'mt-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 leading-relaxed',
            isRtl && 'font-arabic text-right'
          )}>
            {isRtl ? word.memoryHintAr : word.memoryHintEn}
          </p>
        )}
      </div>

      {/* Example verse link */}
      <Link
        to={`/quran/${word.exampleSurah}`}
        className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-lg mb-3',
          'bg-white/60 hover:bg-white/90 border border-teal-100 transition-colors text-xs',
          isRtl && 'flex-row-reverse'
        )}
      >
        <ExternalLink className="w-3 h-3 text-teal-400 flex-shrink-0" />
        <span className={clsx('flex-1 text-gray-700', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? `مثال: ${word.exampleSurahNameAr} (${word.exampleSurah}:${word.exampleAyah})`
            : `Example: ${word.exampleSurahNameEn} ${word.exampleSurah}:${word.exampleAyah}`}
        </span>
        <ChevronRight className={clsx('w-3.5 h-3.5 text-teal-400 flex-shrink-0', isRtl && 'rotate-180')} />
      </Link>

      {/* Source badge */}
      <p className="text-[10px] text-gray-400 text-center">
        {isRtl ? 'المصادر: المعجم الوسيط، QAC، ابن كثير' : "Sources: Lane's Lexicon · QAC Corpus · Ibn Kathir"}
      </p>
    </div>
  );
}
