import { Link } from 'react-router-dom';
import { BookOpen, ExternalLink, ArrowRight } from 'lucide-react';
import clsx from 'clsx';
import { RelatedVerse } from '../../lib/api';

interface VersesSectionProps {
  verses: RelatedVerse[];
  language: 'ar' | 'en';
}

export function VersesSection({ verses, language }: VersesSectionProps) {
  if (verses.length === 0) return null;

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
        {verses.map((verse, idx) => (
          <VerseCard key={`${verse.sura_no}-${verse.aya_no}-${idx}`} verse={verse} language={language} />
        ))}
      </div>
    </div>
  );
}

function VerseCard({ verse, language }: { verse: RelatedVerse; language: 'ar' | 'en' }) {
  const suraName = language === 'ar' ? verse.sura_name_ar : verse.sura_name_en;
  const quranLink = `/quran/${verse.sura_no}?aya=${verse.aya_no}&highlight=true`;

  return (
    <div className="group relative bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 rounded-xl border-2 border-emerald-200 hover:border-emerald-400 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden">
      {/* Decorative accent */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500" />

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

      {/* Arabic verse text - HIGHLIGHTED */}
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
          [{verse.verse_reference}]
        </p>
      </div>

      {/* Translation */}
      <div className="px-4 pb-4">
        <p
          className={clsx(
            'text-sm text-gray-700 leading-relaxed bg-white/50 rounded-lg p-3 border border-gray-100',
            language === 'ar' ? 'text-right' : 'text-left'
          )}
          dir={language === 'ar' ? 'rtl' : 'ltr'}
        >
          <span className="text-gray-500 font-medium">
            {language === 'ar' ? 'الترجمة: ' : 'Translation: '}
          </span>
          {verse.text_en}
        </p>
      </div>

      {/* Footer with relevance and quick link */}
      <div className="px-4 pb-3 flex items-center justify-between text-xs">
        {verse.relevance_score > 0 && (
          <span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
            {Math.round(verse.relevance_score * 100)}% {language === 'ar' ? 'صلة بالسؤال' : 'relevance'}
          </span>
        )}
        <Link
          to={quranLink}
          className="text-emerald-600 hover:text-emerald-800 hover:underline inline-flex items-center gap-1"
        >
          {language === 'ar' ? 'قراءة في السياق' : 'Read in context'}
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
