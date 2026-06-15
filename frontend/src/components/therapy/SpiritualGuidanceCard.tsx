import { useState } from 'react';
import { BookOpen, Lightbulb, HelpCircle, Star, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import type { GuidanceCard } from '../../types/therapy';
import { QuranAudioPlayer } from '../quran/QuranAudioPlayer';
import { getSurahName } from '../../data/surahNames';
import clsx from 'clsx';

interface SpiritualGuidanceCardProps {
  card: GuidanceCard;
  index: number;
}

const THEME_COLORS: Record<string, string> = {
  mercy:      'rose',
  patience:   'amber',
  hope:       'yellow',
  forgiveness:'green',
  gratitude:  'teal',
  healing:    'blue',
  trust:      'indigo',
  strength:   'violet',
};

export function SpiritualGuidanceCard({ card, index }: SpiritualGuidanceCardProps) {
  const { language } = useLanguageStore();
  const [duaOpen, setDuaOpen] = useState(false);
  const isRtl = language === 'ar';
  const surahLink = `/quran/${card.surah}`;

  return (
    <div
      className={clsx(
        'bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden',
        isRtl ? 'border-r-4' : 'border-l-4',
        `${isRtl ? 'border-r' : 'border-l'}-${THEME_COLORS[card.theme] ?? 'emerald'}-400`,
      )}
    >
      {/* Card header */}
      <div className={clsx('px-5 py-3 flex items-center justify-between', `bg-${THEME_COLORS[card.theme] ?? 'emerald'}-50`, isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center text-xs font-bold text-gray-500 shadow-sm">
            {index + 1}
          </span>
          <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full border', `bg-${THEME_COLORS[card.theme] ?? 'emerald'}-100 text-${THEME_COLORS[card.theme] ?? 'emerald'}-700 border-${THEME_COLORS[card.theme] ?? 'emerald'}-200`)}>
            {isRtl ? card.theme_ar : card.theme_en}
          </span>
        </div>
        <Link
          to={surahLink}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
        >
          <span dir={isRtl ? 'rtl' : 'ltr'} className={isRtl ? 'font-arabic' : ''}>
            {getSurahName(card.surah)[isRtl ? 'ar' : 'en']}
          </span>
          <span dir="ltr" className="font-mono">{card.reference}</span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      {/* Verse */}
      <div className="px-5 py-4 bg-gradient-to-b from-gray-50 to-white border-b border-gray-100">
        <div className="flex items-start gap-2 mb-2">
          <BookOpen className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
          <span className={clsx('text-xs uppercase tracking-wide text-gray-400 font-medium', isRtl && 'font-arabic')}>
            {t('therapy_verse', language)}
          </span>
        </div>
        <p
          dir="rtl"
          className="font-arabic text-right text-xl leading-loose text-gray-900 mb-2"
        >
          {card.text_uthmani}
        </p>
        <p dir={isRtl ? 'rtl' : 'ltr'} className={clsx('text-sm text-gray-500 italic mb-3', isRtl && 'font-arabic')}>
          {isRtl ? card.surah_name_ar : card.surah_name_en} ({card.reference})
        </p>
        {/* Compact audio player for verse recitation */}
        <QuranAudioPlayer
          mode="verse"
          suraNo={card.surah}
          ayaNo={card.ayah_start}
          language={language}
          compact={true}
          autoPlay={false}
        />
      </div>

      {/* Lesson */}
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-start gap-2 mb-2">
          <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
          <span className={clsx('text-xs uppercase tracking-wide text-amber-600 font-medium', isRtl && 'font-arabic')}>
            {t('therapy_lesson', language)}
          </span>
        </div>
        <p className={clsx('text-sm text-gray-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl ? card.lesson_ar : card.lesson_en}
        </p>
        {card.prophet_story && (
          <p className={clsx('mt-2 text-xs text-gray-400 italic', isRtl && 'font-arabic text-right')}>
            {card.prophet_story}
          </p>
        )}
      </div>

      {/* Reflection */}
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-start gap-2 mb-2">
          <HelpCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <span className={clsx('text-xs uppercase tracking-wide text-blue-600 font-medium', isRtl && 'font-arabic')}>
            {t('therapy_reflection', language)}
          </span>
        </div>
        <p className={clsx('text-sm text-blue-700 font-medium leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl ? card.reflection_ar : card.reflection_en}
        </p>
      </div>

      {/* Du'a — collapsible */}
      <div className="px-5 py-3">
        <button
          onClick={() => setDuaOpen(v => !v)}
          className={clsx(
            'flex items-center gap-2 text-xs text-emerald-600 hover:text-emerald-700 font-medium',
            isRtl && 'flex-row-reverse font-arabic w-full',
          )}
        >
          <Star className="w-3.5 h-3.5" />
          {t('therapy_dua_suggested', language)}
          {duaOpen ? <ChevronUp className="w-3.5 h-3.5 ms-auto" /> : <ChevronDown className="w-3.5 h-3.5 ms-auto" />}
        </button>

        {duaOpen && (
          <div className="mt-3 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <p dir="rtl" className="font-arabic text-right text-sm text-emerald-800 leading-relaxed mb-2">
              {card.dua_ar}
            </p>
            <p dir="ltr" className="text-xs text-emerald-600 italic leading-relaxed">
              {card.dua_en}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
