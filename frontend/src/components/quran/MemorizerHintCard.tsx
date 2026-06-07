import { Lightbulb, AlertTriangle, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import type { QuranRepeatedPhrase, StoryRecurrenceEntry } from '../../types/quranMemorization';

// ---------------------------------------------------------------------------
// Repeated Phrase Card
// ---------------------------------------------------------------------------

interface RepeatedPhraseCardProps {
  phrase: QuranRepeatedPhrase;
  highlightSurah?: number;
}

export function RepeatedPhraseCard({ phrase, highlightSurah }: RepeatedPhraseCardProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  return (
    <div className="border rounded-xl p-4 bg-white">
      {/* Phrase */}
      <div dir="rtl" className="text-lg font-bold text-gray-900 mb-1 leading-relaxed">
        {phrase.phraseArabic}
      </div>
      {phrase.transliteration && (
        <div dir="ltr" className="text-xs text-gray-500 mb-2 italic">
          {phrase.transliteration}
        </div>
      )}
      <div className="text-sm text-gray-700 mb-3">
        {isAr ? phrase.meaningAr : phrase.meaningEn}
      </div>

      {/* Theme label */}
      <span className="text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-full px-2 py-0.5 mb-3 inline-block">
        {isAr ? phrase.themeLabel.ar : phrase.themeLabel.en}
      </span>

      {/* Occurrences */}
      <div className="mb-3">
        <div className="text-xs font-medium text-gray-600 mb-1.5">
          {isAr ? `يظهر ${phrase.occurrences.length} مرة:` : `Appears ${phrase.occurrences.length} times:`}
        </div>
        <div className="flex flex-wrap gap-1">
          {phrase.occurrences.slice(0, 10).map((ref) => (
            <span
              key={ref.display}
              className={clsx(
                'text-xs px-2 py-0.5 rounded-full font-medium border',
                highlightSurah && ref.surah === highlightSurah
                  ? 'bg-primary-100 text-primary-700 border-primary-300'
                  : 'bg-gray-50 text-gray-600 border-gray-200',
              )}
            >
              {ref.display}
            </span>
          ))}
          {phrase.occurrences.length > 10 && (
            <span className="text-xs text-gray-400 px-2 py-0.5">
              +{phrase.occurrences.length - 10} {isAr ? 'أخرى' : 'more'}
            </span>
          )}
        </div>
      </div>

      {/* Memorizer note */}
      <div className="flex items-start gap-2 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg p-2">
        <Lightbulb size={12} className="mt-0.5 flex-shrink-0" />
        <span>{isAr ? phrase.memorizerNote.ar : phrase.memorizerNote.en}</span>
      </div>

      {phrase.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-1 text-xs text-amber-600 mt-2">
          <AlertTriangle size={11} />
          <span>{isAr ? 'قيد المراجعة' : 'Pending review'}</span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Story Recurrence Card
// ---------------------------------------------------------------------------

interface StoryRecurrenceCardProps {
  recurrence: StoryRecurrenceEntry;
  currentSurah?: number;
}

export function StoryRecurrenceCard({ recurrence, currentSurah }: StoryRecurrenceCardProps) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  return (
    <div className="border rounded-xl p-4 bg-white">
      <div className="flex items-start gap-2 mb-3">
        <RefreshCw size={16} className="mt-0.5 text-primary-500 flex-shrink-0" />
        <div>
          <div className="text-sm font-semibold text-gray-900">
            {isAr ? recurrence.titleAr : recurrence.titleEn}
          </div>
          <div className="text-xs text-gray-500">
            {isAr
              ? `تكرر في ${recurrence.totalOccurrences} موضع`
              : `Appears in ${recurrence.totalOccurrences} places`}
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {recurrence.surahOccurrences.slice(0, 5).map((occ) => (
          <div
            key={occ.surahNumber}
            className={clsx(
              'flex items-start gap-2 text-xs p-2 rounded-lg border',
              currentSurah && occ.surahNumber === currentSurah
                ? 'bg-primary-50 border-primary-200'
                : 'bg-gray-50 border-gray-100',
            )}
          >
            <span className="font-bold text-primary-600 flex-shrink-0">
              {occ.ayahRange.display}
            </span>
            <div>
              <div className="font-medium text-gray-700">{occ.surahName}</div>
              <div className="text-gray-500">
                {isAr ? occ.coverageNote.ar : occ.coverageNote.en}
              </div>
            </div>
          </div>
        ))}
        {recurrence.surahOccurrences.length > 5 && (
          <div className="text-xs text-gray-400 text-center">
            +{recurrence.surahOccurrences.length - 5} {isAr ? 'مزيد من المواضع' : 'more locations'}
          </div>
        )}
      </div>

      {recurrence.reviewStatus === 'needs_review' && (
        <div className="flex items-center gap-1 text-xs text-amber-600 mt-2">
          <AlertTriangle size={11} />
          <span>{isAr ? 'قيد المراجعة' : 'Pending review'}</span>
        </div>
      )}
    </div>
  );
}
