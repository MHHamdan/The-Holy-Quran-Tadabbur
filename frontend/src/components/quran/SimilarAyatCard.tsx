import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowRight, Info } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import type { MemorizationLink, ConfusionPair } from '../../types/quranMemorization';

// ---------------------------------------------------------------------------
// Memorization Link Card
// ---------------------------------------------------------------------------

interface MemorizationLinkCardProps {
  link: MemorizationLink;
  /** The "anchor" surah — the one the user is currently viewing */
  currentSurah: number;
}

const LINK_TYPE_LABELS: Record<string, { ar: string; en: string }> = {
  similar_phrase: { ar: 'عبارة مشابهة', en: 'Similar Phrase' },
  same_prophet_different_surah: { ar: 'نبي في سورة أخرى', en: 'Same Prophet, Different Surah' },
  repeated_story: { ar: 'قصة متكررة', en: 'Repeated Story' },
  repeated_dialogue: { ar: 'حوار متكرر', en: 'Repeated Dialogue' },
  similar_opening: { ar: 'افتتاحية مشابهة', en: 'Similar Opening' },
  similar_ending: { ar: 'خاتمة مشابهة', en: 'Similar Ending' },
  near_duplicate_structure: { ar: 'بنية شبه متطابقة', en: 'Near-Duplicate Structure' },
  contrast_pair: { ar: 'زوج تقابلي', en: 'Contrast Pair' },
  chronological_story_sequence: { ar: 'تسلسل قصصي', en: 'Story Sequence' },
  same_dua: { ar: 'دعاء مشترك', en: 'Same Du\'a' },
  same_command: { ar: 'أمر مشترك', en: 'Same Command' },
  same_theme_different_surah: { ar: 'موضوع مشترك في سورة أخرى', en: 'Same Theme, Different Surah' },
  same_warning: { ar: 'تحذير مشترك', en: 'Same Warning' },
  same_reward: { ar: 'مكافأة مشتركة', en: 'Same Reward' },
  same_punishment: { ar: 'عقوبة مشتركة', en: 'Same Punishment' },
};

const RISK_COLOR = {
  high: 'bg-red-50 border-red-200 text-red-700',
  medium: 'bg-amber-50 border-amber-200 text-amber-700',
  low: 'bg-green-50 border-green-200 text-green-700',
};

export function SimilarAyatCard({ link, currentSurah }: MemorizationLinkCardProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const isSource = link.sourceSurah === currentSurah;
  const otherRef = isSource ? link.targetAyah : link.sourceAyah;
  const linkLabel = LINK_TYPE_LABELS[link.linkType] ?? { ar: link.linkType, en: link.linkType };

  return (
    <div className="border rounded-xl p-4 bg-white hover:shadow-sm transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 rounded-full px-2 py-0.5">
          {isAr ? linkLabel.ar : linkLabel.en}
        </span>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full border font-medium', RISK_COLOR[link.riskOfConfusion])}>
          {isAr
            ? link.riskOfConfusion === 'high' ? 'خطر عالٍ' : link.riskOfConfusion === 'medium' ? 'خطر متوسط' : 'خطر منخفض'
            : `${link.riskOfConfusion} confusion risk`}
        </span>
      </div>

      {/* Ayah reference */}
      <div className="text-sm font-medium text-gray-800 mb-2">
        <span className="text-primary-600 font-bold">{otherRef.display}</span>
        {' — '}
        {isAr ? link.similarityReason.ar : link.similarityReason.en}
      </div>

      {/* Memorizer hint */}
      <div className="flex items-start gap-2 text-xs text-gray-600 bg-gray-50 rounded-lg p-2 mb-2">
        <Info size={12} className="mt-0.5 flex-shrink-0 text-blue-500" />
        <span>{isAr ? link.memorizerHint.ar : link.memorizerHint.en}</span>
      </div>

      {/* Difference note */}
      <div className="text-xs text-gray-500 border-t pt-2">
        <span className="font-medium">{isAr ? 'الفرق: ' : 'Difference: '}</span>
        {isAr ? link.differenceNote.ar : link.differenceNote.en}
      </div>

      {/* Review warning */}
      {link.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-1.5 text-xs text-amber-600 mt-2">
          <AlertTriangle size={11} />
          <span>{isAr ? 'قيد المراجعة العلمية' : 'Pending scholarly review'}</span>
        </div>
      )}

      {/* Link to ayah in Mushaf */}
      <Link
        to={`/surah-atlas/${otherRef.surah}`}
        className="mt-2 inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-800 font-medium"
      >
        {isAr ? `أطلس ${otherRef.display}` : `Atlas ${otherRef.display}`}
        <ArrowRight size={11} />
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Confusion Pair Card
// ---------------------------------------------------------------------------

interface ConfusionPairCardProps {
  pair: ConfusionPair;
  currentSurah: number;
}

export function ConfusionPairCard({ pair, currentSurah }: ConfusionPairCardProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const isA = pair.ayahA.surah === currentSurah;
  const thisRef = isA ? pair.ayahA : pair.ayahB;
  const otherRef = isA ? pair.ayahB : pair.ayahA;

  return (
    <div className={clsx('border rounded-xl p-4 bg-white', pair.riskLevel === 'high' && 'border-red-200')}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle size={14} className={clsx(
          pair.riskLevel === 'high' ? 'text-red-500' : pair.riskLevel === 'medium' ? 'text-amber-500' : 'text-yellow-400',
        )} />
        <span className="text-xs font-semibold text-gray-700">
          {isAr ? 'تحذير: لا تخلط' : 'Do Not Confuse'}
        </span>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full border', RISK_COLOR[pair.riskLevel])}>
          {isAr
            ? pair.riskLevel === 'high' ? 'خطر عالٍ' : pair.riskLevel === 'medium' ? 'متوسط' : 'منخفض'
            : `${pair.riskLevel} risk`}
        </span>
      </div>

      {/* Refs */}
      <div className="flex items-center gap-2 text-sm mb-2">
        <span className="font-bold text-primary-600">{thisRef.display}</span>
        <ArrowRight size={12} className="text-gray-400" />
        <Link to={`/surah-atlas/${otherRef.surah}`} className="font-bold text-primary-600 hover:underline">
          {otherRef.display}
        </Link>
      </div>

      {/* Why confused */}
      <p className="text-xs text-gray-600 mb-2">
        {isAr ? pair.confusionReason.ar : pair.confusionReason.en}
      </p>

      {/* Key difference */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2 text-xs text-emerald-800">
        <span className="font-medium">{isAr ? 'الفرق الجوهري: ' : 'Key difference: '}</span>
        {isAr ? pair.keyDifference.ar : pair.keyDifference.en}
      </div>

      {/* Memorizer tip */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-xs text-blue-800 mt-2">
        <span className="font-medium">{isAr ? 'نصيحة للحافظ: ' : 'Memorizer tip: '}</span>
        {isAr ? pair.memorizerTip.ar : pair.memorizerTip.en}
      </div>

      {pair.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-1 text-xs text-amber-600 mt-2">
          <AlertTriangle size={11} />
          <span>{isAr ? 'قيد المراجعة' : 'Pending review'}</span>
        </div>
      )}
    </div>
  );
}
