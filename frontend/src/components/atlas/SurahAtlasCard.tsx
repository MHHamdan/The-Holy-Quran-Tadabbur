import { Link } from 'react-router-dom';
import { BookOpen, AlertTriangle, Users, Map, Layers } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import type { SurahAtlasEntry } from '../../types/surahAtlas';

const AR_JUZ: Record<number, string> = {
  1:'الجزء الأول',2:'الجزء الثاني',3:'الجزء الثالث',4:'الجزء الرابع',5:'الجزء الخامس',
  6:'الجزء السادس',7:'الجزء السابع',8:'الجزء الثامن',9:'الجزء التاسع',10:'الجزء العاشر',
  11:'الجزء الحادي عشر',12:'الجزء الثاني عشر',13:'الجزء الثالث عشر',14:'الجزء الرابع عشر',
  15:'الجزء الخامس عشر',16:'الجزء السادس عشر',17:'الجزء السابع عشر',18:'الجزء الثامن عشر',
  19:'الجزء التاسع عشر',20:'الجزء العشرون',21:'الجزء الحادي والعشرون',22:'الجزء الثاني والعشرون',
  23:'الجزء الثالث والعشرون',24:'الجزء الرابع والعشرون',25:'الجزء الخامس والعشرون',
  26:'الجزء السادس والعشرون',27:'الجزء السابع والعشرون',28:'الجزء الثامن والعشرون',
  29:'الجزء التاسع والعشرون',30:'الجزء الثلاثون',
};

function juzLabel(ref: string, isAr: boolean): string {
  if (!isAr) return ref;
  const n = parseInt(ref.replace('Juz ', ''), 10);
  return AR_JUZ[n] ?? ref;
}

interface SurahAtlasCardProps {
  entry: SurahAtlasEntry;
  compact?: boolean;
}

const REVELATION_BADGE: Record<string, { label: { ar: string; en: string }; color: string }> = {
  makki: { label: { ar: 'مكية', en: 'Makki' }, color: 'bg-amber-100 text-amber-800 border-amber-200' },
  madani: { label: { ar: 'مدنية', en: 'Madani' }, color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  mixed: { label: { ar: 'مختلطة', en: 'Mixed' }, color: 'bg-blue-100 text-blue-800 border-blue-200' },
  disputed: { label: { ar: 'مختلف فيها', en: 'Disputed' }, color: 'bg-orange-100 text-orange-800 border-orange-200' },
  needs_review: { label: { ar: 'قيد المراجعة', en: 'Needs Review' }, color: 'bg-gray-100 text-gray-600 border-gray-200' },
  unknown: { label: { ar: 'غير محدد', en: 'Unknown' }, color: 'bg-gray-100 text-gray-600 border-gray-200' },
};

export function SurahAtlasCard({ entry, compact = false }: SurahAtlasCardProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const revBadge = REVELATION_BADGE[entry.revelationType] ?? REVELATION_BADGE.unknown;
  const storyCount = entry.storiesMentioned?.length ?? 0;
  const prophetCount = entry.prophetsMentioned?.length ?? 0;

  return (
    <Link
      to={`/surah-atlas/${entry.surahNumber}`}
      className={clsx(
        'block rounded-xl border bg-white p-4 shadow-sm',
        'hover:shadow-md hover:border-primary-300 transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-primary-400',
        compact ? 'p-3' : 'p-5',
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <span className="flex-shrink-0 w-9 h-9 rounded-full bg-primary-50 border border-primary-200 flex items-center justify-center text-sm font-bold text-primary-700">
            {entry.surahNumber}
          </span>
          <div>
            <div dir="rtl" className="text-base font-semibold text-gray-900 leading-tight">
              {entry.nameArabic.replace('سُورَةُ ', '').replace('ٱل', 'ال').trim()}
            </div>
            {isAr ? (
              <div dir="ltr" className="text-xs text-gray-400 italic">
                {entry.nameTransliteration}
              </div>
            ) : (
              <div dir="ltr" className="text-xs text-gray-500">
                {entry.nameTransliteration} · {entry.nameEnglishMeaning}
              </div>
            )}
          </div>
        </div>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full border font-medium flex-shrink-0', revBadge.color)}>
          {isAr ? revBadge.label.ar : revBadge.label.en}
        </span>
      </div>

      {/* Stats row */}
      {!compact && (
        <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
          <span className="flex items-center gap-1">
            <BookOpen size={12} />
            {isAr ? `${entry.ayahCount} آية` : `${entry.ayahCount} ayat`}
          </span>
          {storyCount > 0 && (
            <span className="flex items-center gap-1">
              <Layers size={12} />
              {isAr ? `${storyCount} قصة` : `${storyCount} ${storyCount === 1 ? 'story' : 'stories'}`}
            </span>
          )}
          {prophetCount > 0 && (
            <span className="flex items-center gap-1">
              <Users size={12} />
              {isAr ? `${prophetCount} نبي` : `${prophetCount} ${prophetCount === 1 ? 'prophet' : 'prophets'}`}
            </span>
          )}
          {entry.juzRefs.length > 0 && (
            <span className="flex items-center gap-1">
              <Map size={12} />
              {juzLabel(entry.juzRefs[0], isAr)}
            </span>
          )}
        </div>
      )}

      {/* Concepts */}
      {!compact && (isAr ? (entry.keyConceptsAr ?? entry.keyConcepts) : entry.keyConcepts).length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3" dir={isAr ? 'rtl' : 'ltr'}>
          {(isAr ? (entry.keyConceptsAr ?? entry.keyConcepts) : entry.keyConcepts).slice(0, 3).map((c) => (
            <span key={c} className="text-xs bg-gray-50 border border-gray-200 rounded-full px-2 py-0.5 text-gray-600">
              {c}
            </span>
          ))}
        </div>
      )}

      {/* Review warning */}
      {entry.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1.5">
          <AlertTriangle size={11} className="flex-shrink-0" />
          <span>{isAr ? 'قيد المراجعة العلمية' : 'Pending scholarly review'}</span>
        </div>
      )}
    </Link>
  );
}
