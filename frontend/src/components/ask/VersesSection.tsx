import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, ExternalLink, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';
import type { RelatedVerse } from '../../lib/api';
import { translationLabel } from './answerText';
import { QuranTextAttribution } from '../quran/QuranTextAttribution';

const INITIAL_VERSE_COUNT = 3;

interface VersesSectionProps {
  verses: RelatedVerse[];
  language: 'ar' | 'en';
}

export function VersesSection({ verses, language }: VersesSectionProps) {
  const [showAll, setShowAll] = useState(false);
  if (verses.length === 0) return null;

  const displayed = showAll ? verses : verses.slice(0, INITIAL_VERSE_COUNT);
  const hidden = verses.length - INITIAL_VERSE_COUNT;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-emerald-600" />
        {language === 'ar' ? 'الآيات القرآنية ذات الصلة' : 'Related Quranic Verses'}
        <span className="text-xs font-normal text-gray-500">
          ({verses.length})
        </span>
      </h3>
      <div className="space-y-4">
        {displayed.map((verse, idx) => (
          <VerseCard key={`${verse.sura_no}-${verse.aya_no}-${idx}`} verse={verse} language={language} />
        ))}
      </div>
      {verses.length > INITIAL_VERSE_COUNT && (
        <button
          onClick={() => setShowAll(v => !v)}
          className="w-full flex items-center justify-center gap-1.5 py-2 min-h-11 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
        >
          {showAll ? (
            <>
              <ChevronUp className="w-3.5 h-3.5" />
              {language === 'ar' ? 'إخفاء الآيات' : 'Show fewer verses'}
            </>
          ) : (
            <>
              <ChevronDown className="w-3.5 h-3.5" />
              {language === 'ar' ? `عرض ${hidden} آية إضافية` : `Show ${hidden} more verse${hidden !== 1 ? 's' : ''}`}
            </>
          )}
        </button>
      )}
      {/* The Qur'an text above is Tanzil's (CC BY 3.0): the licence requires the
          source to be named, with a link, wherever the text is shown. */}
      <QuranTextAttribution language={language} className="text-center" />
    </div>
  );
}

function VerseCard({ verse, language }: { verse: RelatedVerse; language: 'ar' | 'en' }) {
  const suraName = language === 'ar' ? verse.sura_name_ar : verse.sura_name_en;
  const quranLink = `/quran/${verse.sura_no}?aya=${verse.aya_no}&highlight=true`;

  return (
    <div className="group relative bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 rounded-xl border-2 border-emerald-200 hover:border-emerald-400 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden">
      {/* Decorative accent */}
      <div className="absolute top-0 start-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500" />

      {/* Header with verse reference and link */}
      <div className="px-4 pt-4 pb-2 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Surah name badge */}
          <span className="inline-flex items-center gap-1.5 text-sm font-semibold bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full">
            <BookOpen className="w-3.5 h-3.5" />
            {suraName || `${language === 'ar' ? 'السورة' : 'Surah'} ${verse.sura_no}`}
          </span>
          {/* Topic badge */}
          {verse.topic && (
            <span className="text-xs text-teal-700 bg-teal-100 px-2 py-1 rounded-full">
              {verse.topic}
            </span>
          )}
        </div>

        {/* Direct link to Quran page - PROMINENT */}
        <Link
          to={quranLink}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-lg shadow-md hover:shadow-lg transition-all duration-200 group-hover:scale-105"
        >
          <span>{verse.verse_reference}</span>
          <ExternalLink className="w-4 h-4" />
          <span className="hidden sm:inline">
            {language === 'ar' ? 'اذهب للآية' : 'Go to Verse'}
          </span>
          <ArrowRight className={clsx('w-4 h-4', language === 'ar' && 'rotate-180')} />
        </Link>
      </div>

      {/* Arabic verse text - HIGHLIGHTED (omitted when the API had no text) */}
      {verse.text_ar && (
      <div className="px-4 py-4 mx-4 my-2 bg-white/80 rounded-xl border border-emerald-100 shadow-inner">
        <p
          className="text-xl leading-loose text-gray-900 font-arabic text-center"
          dir="rtl"
          style={{ lineHeight: '2.5' }}
        >
          <span className="text-emerald-700">﴿</span>
          {verse.text_ar}
          <span className="text-emerald-700">﴾</span>
        </p>
        {/* Verse reference in Arabic numerals */}
        <p className="text-center text-sm text-emerald-600 mt-2 font-medium">
          [<bdi dir="ltr">{verse.verse_reference}</bdi>]
        </p>
      </div>
      )}

      {/* Translation: labelled with its edition; the English text is always LTR */}
      {verse.text_en && (
        <div className="px-4 pb-4">
          <div className="bg-white/50 rounded-lg p-3 border border-gray-100">
            <p
              className="text-xs text-gray-600 font-medium mb-1"
              dir={language === 'ar' ? 'rtl' : 'ltr'}
            >
              {translationLabel(verse.translation_edition, language)}
            </p>
            <p className="text-sm text-gray-700 leading-relaxed text-left" dir="ltr" lang="en">
              {verse.text_en}
            </p>
          </div>
        </div>
      )}

      {/* Footer with relevance and quick link */}
      <div className="px-4 pb-3 flex items-center justify-between text-xs">
        {verse.relevance_score > 0 && (
          <span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
            {Math.round(verse.relevance_score * 100)}% {language === 'ar' ? 'صلة بالسؤال' : 'relevance'}
          </span>
        )}
        <Link
          to={quranLink}
          className="text-emerald-600 hover:text-emerald-800 hover:underline inline-flex items-center gap-1 min-h-6 py-1"
        >
          {language === 'ar' ? 'قراءة في السياق' : 'Read in context'}
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
