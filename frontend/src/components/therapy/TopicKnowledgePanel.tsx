import { useState, useEffect } from 'react';
import { BookMarked, Quote, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { therapyApi } from '../../lib/api';
import type { TopicResourcesResponse, TopicHadith, TopicWisePhrase } from '../../types/therapy';
import clsx from 'clsx';

interface Props {
  topicKey: string;
}

function HadithCard({ hadith, isRtl }: { hadith: TopicHadith; isRtl: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white rounded-xl border border-teal-100 overflow-hidden">
      <div className="p-4 space-y-2">
        <p dir="rtl" className="font-arabic text-right text-base leading-loose text-gray-900">
          {hadith.arabic}
        </p>
        <p dir="ltr" className="text-xs text-gray-400 italic">{hadith.transliteration}</p>
        <p className={clsx('text-sm text-gray-700', isRtl && 'font-arabic text-right')}>
          {isRtl ? hadith.translation_ar : hadith.translation_en}
        </p>
        <button
          onClick={() => setOpen(o => !o)}
          className={clsx('flex items-center gap-1 text-xs text-teal-600 hover:text-teal-800 transition-colors', isRtl && 'flex-row-reverse font-arabic')}
        >
          {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {isRtl ? 'المصدر والشرح' : 'Source & Commentary'}
        </button>
        {open && (
          <p className={clsx('text-xs text-gray-500 leading-relaxed border-t border-gray-100 pt-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? hadith.source_ar : hadith.source_en}
          </p>
        )}
      </div>
    </div>
  );
}

function WisePhraseCard({ phrase, isRtl }: { phrase: TopicWisePhrase; isRtl: boolean }) {
  return (
    <div className="bg-amber-50 rounded-xl border border-amber-100 p-4 space-y-2">
      <p className={clsx('text-sm leading-relaxed text-gray-800 italic', isRtl && 'font-arabic text-right')}>
        {isRtl ? `"${phrase.text_ar}"` : `"${phrase.text_en}"`}
      </p>
      <div className={clsx('flex items-center gap-1.5 text-xs text-amber-700', isRtl && 'flex-row-reverse font-arabic')}>
        <span className="font-medium">{isRtl ? phrase.scholar_ar : phrase.scholar_en}</span>
        <span className="text-amber-400">·</span>
        <span className="text-amber-600">{isRtl ? phrase.source_ar : phrase.source_en}</span>
      </div>
    </div>
  );
}

export function TopicKnowledgePanel({ topicKey }: Props) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [data, setData] = useState<TopicResourcesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showHadith, setShowHadith] = useState(true);
  const [showPhrases, setShowPhrases] = useState(true);

  useEffect(() => {
    if (!topicKey) return;
    setLoading(true);
    setData(null);
    therapyApi.getTopicResources(topicKey)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [topicKey]);

  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Loader2 className="w-5 h-5 text-teal-400 animate-spin" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
        <div className="w-1 h-5 bg-teal-500 rounded-full" />
        <h3 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
          {isRtl ? `المصادر الإسلامية — ${data.topic_ar}` : `Islamic Resources — ${data.topic_en}`}
        </h3>
      </div>

      {/* Intro */}
      <p className={clsx('text-xs text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
        {isRtl ? data.intro_ar : data.intro_en}
      </p>

      {/* Hadith section */}
      {data.hadith.length > 0 && (
        <div>
          <button
            onClick={() => setShowHadith(o => !o)}
            className={clsx(
              'w-full flex items-center justify-between p-3 rounded-xl border transition-colors',
              'bg-teal-50 border-teal-200',
              isRtl && 'flex-row-reverse',
            )}
          >
            <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
              <BookMarked className="w-4 h-4 text-teal-600" />
              <span className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
                {isRtl ? `الأحاديث النبوية (${data.hadith.length})` : `Prophetic Hadith (${data.hadith.length})`}
              </span>
            </div>
            {showHadith ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
          </button>
          {showHadith && (
            <div className="mt-3 space-y-3">
              {data.hadith.map((h, i) => (
                <HadithCard key={i} hadith={h} isRtl={isRtl} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Wise phrases section */}
      {data.wise_phrases.length > 0 && (
        <div>
          <button
            onClick={() => setShowPhrases(o => !o)}
            className={clsx(
              'w-full flex items-center justify-between p-3 rounded-xl border transition-colors',
              'bg-amber-50 border-amber-200',
              isRtl && 'flex-row-reverse',
            )}
          >
            <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
              <Quote className="w-4 h-4 text-amber-600" />
              <span className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
                {isRtl ? `حكم العلماء (${data.wise_phrases.length})` : `Scholar Wisdom (${data.wise_phrases.length})`}
              </span>
            </div>
            {showPhrases ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
          </button>
          {showPhrases && (
            <div className="mt-3 space-y-3">
              {data.wise_phrases.map((p, i) => (
                <WisePhraseCard key={i} phrase={p} isRtl={isRtl} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
