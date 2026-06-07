import { AlertTriangle, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import type { SurahAtlasEntry } from '../../types/surahAtlas';

interface SurahAtlasHeroProps {
  entry: SurahAtlasEntry;
}

const REVELATION_BADGE: Record<string, { label: { ar: string; en: string }; color: string }> = {
  makki: { label: { ar: 'مكية', en: 'Makki' }, color: 'bg-amber-100 text-amber-800 border-amber-300' },
  madani: { label: { ar: 'مدنية', en: 'Madani' }, color: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  mixed: { label: { ar: 'مختلطة', en: 'Mixed' }, color: 'bg-blue-100 text-blue-800 border-blue-300' },
  disputed: { label: { ar: 'مختلف فيها', en: 'Disputed' }, color: 'bg-orange-100 text-orange-800 border-orange-300' },
  unknown: { label: { ar: 'غير محدد', en: 'Unknown' }, color: 'bg-gray-100 text-gray-600 border-gray-300' },
  needs_review: { label: { ar: 'قيد المراجعة', en: 'Under Review' }, color: 'bg-gray-100 text-gray-600 border-gray-300' },
};

export function SurahAtlasHero({ entry }: SurahAtlasHeroProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const revBadge = REVELATION_BADGE[entry.revelationType] ?? REVELATION_BADGE.unknown;

  return (
    <div className="bg-gradient-to-br from-primary-700 to-primary-900 rounded-2xl p-6 md:p-8 text-white mb-6">
      {/* Surah number + name */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-2xl font-bold">
            {entry.surahNumber}
          </div>
          <div>
            <div dir="rtl" className="text-2xl font-bold mb-1">
              {entry.nameArabic}
            </div>
            <div dir="ltr" className="text-primary-200 text-sm">
              {entry.nameTransliteration} · {entry.nameEnglishMeaning}
            </div>
          </div>
        </div>
        <span className={clsx('text-xs px-3 py-1 rounded-full border font-medium', revBadge.color)}>
          {isAr ? revBadge.label.ar : revBadge.label.en}
        </span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-white/10 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold">{entry.ayahCount}</div>
          <div className="text-xs text-primary-200">{isAr ? 'آية' : 'Ayat'}</div>
        </div>
        <div className="bg-white/10 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold">{entry.juzRefs[0] ?? '—'}</div>
          <div className="text-xs text-primary-200">{isAr ? 'الجزء' : 'Juz'}</div>
        </div>
        <div className="bg-white/10 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold">{entry.storiesMentioned?.length ?? 0}</div>
          <div className="text-xs text-primary-200">{isAr ? 'قصص' : 'Stories'}</div>
        </div>
        <div className="bg-white/10 rounded-xl p-3 text-center">
          <div className="text-2xl font-bold">{entry.prophetsMentioned?.length ?? 0}</div>
          <div className="text-xs text-primary-200">{isAr ? 'أنبياء' : 'Prophets'}</div>
        </div>
      </div>

      {/* Read in Mushaf */}
      {entry.pageStart && (
        <Link
          to={`/mushaf?page=${entry.pageStart}`}
          className="inline-flex items-center gap-1.5 text-xs text-white/80 hover:text-white bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg px-3 py-1.5 mb-3 transition-colors"
        >
          <ExternalLink size={12} />
          {isAr ? `اقرأ في المصحف — صفحة ${entry.pageStart}` : `Read in Mushaf — Page ${entry.pageStart}`}
        </Link>
      )}

      {/* Review status warning */}
      {entry.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-2 text-xs text-amber-200 bg-amber-900/30 border border-amber-600/40 rounded-lg px-3 py-2">
          <AlertTriangle size={13} className="flex-shrink-0" />
          <span>
            {isAr
              ? 'محتوى هذه السورة في الأطلس قيد المراجعة العلمية. الملخصات نصوص مؤقتة وتتطلب مراجعة.'
              : 'This surah\'s atlas content is pending scholarly review. Summaries are placeholders.'}
          </span>
        </div>
      )}
    </div>
  );
}
