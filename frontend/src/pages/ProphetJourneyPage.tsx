/**
 * Prophet Journey Page — tabbed journey view (Mushaf, story-world, thematic,
 * learning) with optional storytelling-with-evidence mode.
 *
 * Phase X. Backed by GET /api/v1/quran/prophets/{id}/journey and the optional
 * POST /storytelling endpoint.
 */

import { useEffect, useState, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, AlertCircle, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  prophetsApi,
  type ProphetJourney,
  type ProphetStorytellingResponse,
} from '../lib/api';

type Order = 'mushaf' | 'story_world' | 'thematic' | 'learning' | 'revelation';
const ORDER_TO_JOURNEY: Record<Order, ProphetStorytellingResponse extends never ? never : string> = {
  mushaf: 'mushaf_order',
  story_world: 'story_world_order',
  thematic: 'thematic_order',
  learning: 'learning_order',
  revelation: 'revelation_order',
};

const ORDER_TABS: { id: Order; ar: string; en: string }[] = [
  { id: 'mushaf', ar: 'الترتيب المصحفي', en: 'Mushaf order' },
  { id: 'story_world', ar: 'الترتيب القصصي', en: 'Story-world' },
  { id: 'thematic', ar: 'الترتيب الموضوعي', en: 'Thematic' },
  { id: 'learning', ar: 'ترتيب تعلّمي', en: 'Learning' },
  { id: 'revelation', ar: 'النزولي', en: 'Revelation' },
];

export function ProphetJourneyPage() {
  const { prophetId } = useParams<{ prophetId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';

  const [order, setOrder] = useState<Order>('mushaf');
  const [journey, setJourney] = useState<ProphetJourney | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [storytelling, setStorytelling] = useState<ProphetStorytellingResponse | null>(null);
  const [storytellingLoading, setStorytellingLoading] = useState(false);

  useEffect(() => {
    if (!prophetId) return;
    let stale = false;
    setLoading(true);
    setStorytelling(null);
    prophetsApi
      .journey(prophetId, order)
      .then((r) => !stale && setJourney(r))
      .catch((e) => !stale && setError(e?.message || 'Failed to load journey'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [prophetId, order]);

  const requestStorytelling = useCallback(async () => {
    if (!journey || !prophetId) return;
    setStorytellingLoading(true);
    try {
      const ayahReferences = journey.stages
        .flatMap((s) => s.ayahReferences)
        .slice(0, 30);
      const r = await prophetsApi.storytelling(prophetId, {
        journeyType: ORDER_TO_JOURNEY[order] as never,
        ayahReferences,
        language,
      });
      setStorytelling(r);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed';
      setError(msg);
    } finally {
      setStorytellingLoading(false);
    }
  }, [journey, prophetId, order, language]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-emerald-600 animate-spin" />
      </div>
    );
  }
  if (error || !journey) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12" dir={dir}>
        <div className="p-4 border border-red-200 bg-red-50 text-red-800 rounded-md flex items-start gap-2">
          <AlertCircle className="w-5 h-5 mt-0.5" />
          <p>{error ?? 'Journey not available.'}</p>
        </div>
        <Link to={`/prophets/${prophetId}`} className="mt-4 inline-block text-emerald-700 hover:underline">
          ← {language === 'ar' ? 'العودة إلى الملف' : 'Back to profile'}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8" dir={dir}>
      <Link to={`/prophets/${prophetId}`} className="text-sm text-emerald-700 hover:underline">
        ← {language === 'ar' ? 'الملف' : 'Profile'}
      </Link>

      <header className="mt-3 mb-6">
        <h1 className={clsx('text-2xl font-bold text-gray-900 flex items-center gap-2', language === 'ar' && 'font-arabic')}>
          <BookOpen className="w-6 h-6 text-emerald-600" />
          {language === 'ar' ? 'رحلة ' : 'Journey — '}
          {prophetId?.replace(/^prophet_/, '')}
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          {language === 'ar' ? 'حالة المراجعة: ' : 'Review status: '}
          <span className="font-medium">{journey.reviewStatus}</span> · {journey.certainty}
        </p>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        {ORDER_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setOrder(t.id)}
            className={clsx(
              'px-3 py-1.5 text-sm rounded border',
              order === t.id
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white text-gray-700 border-gray-200 hover:border-emerald-300',
            )}
          >
            {language === 'ar' ? t.ar : t.en}
          </button>
        ))}
      </div>

      {order === 'story_world' && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded text-sm">
          {language === 'ar'
            ? 'ترتيب القراءة الإرشادي ليس تأريخاً قطعياً. هذا تصفّح، وليس تفسيراً.'
            : 'Guided reading order, not a definitive historical chronology.'}
        </div>
      )}

      <ol className="space-y-3">
        {journey.stages.map((s) => (
          <li key={s.stageId} className="p-4 bg-white border border-gray-200 rounded">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className={clsx('text-base font-semibold text-gray-900', language === 'ar' && 'font-arabic')}>
                {s.orderIndex}. {language === 'ar' ? s.labelArabic : s.labelEnglish}
              </h3>
              <span className="text-xs px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 rounded">
                {s.reviewStatus}
              </span>
            </div>
            {s.ayahReferences.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {s.ayahReferences.slice(0, 16).map((r, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-gray-50 border border-gray-200 rounded">
                    {r.surahNumber}:{r.ayahStart}
                    {r.ayahEnd ? `-${r.ayahEnd}` : ''}
                  </span>
                ))}
                {s.ayahReferences.length > 16 && (
                  <span className="text-xs text-gray-500">+{s.ayahReferences.length - 16}</span>
                )}
              </div>
            )}
            {s.relatedTopics.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {s.relatedTopics.map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded">
                    {t}
                  </span>
                ))}
              </div>
            )}
            {s.warnings.length > 0 && (
              <ul className="mt-2 text-xs text-amber-700 list-disc list-inside">
                {s.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>

      <div className="mt-8 p-4 bg-gradient-to-br from-emerald-50 to-white border border-emerald-100 rounded">
        <h2 className={clsx('text-lg font-semibold mb-2 text-emerald-800', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'السرد القرآني بالشواهد' : 'Storytelling with evidence'}
        </h2>
        <p className="text-xs text-gray-600 mb-3">
          {language === 'ar'
            ? 'تصفّح إرشادي وليس تفسيراً. يحتاج التفصيل إلى مصادر معتمدة.'
            : 'Navigation summary, not tafsir. Detail requires verified sources.'}
        </p>
        {!storytelling && (
          <button
            type="button"
            disabled={storytellingLoading}
            onClick={requestStorytelling}
            className="px-4 py-1.5 bg-emerald-600 text-white text-sm rounded hover:bg-emerald-700 disabled:opacity-50"
          >
            {storytellingLoading
              ? language === 'ar'
                ? 'جاري التحميل...'
                : 'Generating…'
              : language === 'ar'
                ? 'احصل على السرد'
                : 'Generate storytelling'}
          </button>
        )}
        {storytelling && (
          <div className="space-y-3">
            <p className={clsx('text-sm text-gray-800', language === 'ar' && 'font-arabic')}>
              {language === 'ar' ? storytelling.summaryArabic : storytelling.summaryEnglish}
            </p>
            <div className="text-xs text-amber-700">
              <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200">
                {storytelling.reviewStatus}
              </span>
            </div>
            <details>
              <summary className="cursor-pointer text-xs text-emerald-700">
                {language === 'ar' ? 'مراحل السرد' : 'Storytelling stages'} ({storytelling.stages.length})
              </summary>
              <ul className="mt-2 space-y-2">
                {storytelling.stages.map((st) => (
                  <li key={st.stageId} className="p-2 bg-white border border-gray-200 rounded text-sm">
                    <p className={clsx(language === 'ar' && 'font-arabic')}>
                      {language === 'ar' ? st.explanationArabic : st.explanationEnglish}
                    </p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {st.ayahReferences.slice(0, 8).map((r, i) => (
                        <span key={i} className="text-[10px] px-1.5 py-0.5 bg-gray-50 border border-gray-200 rounded">
                          {r.surahNumber}:{r.ayahStart}
                        </span>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </details>
            <details>
              <summary className="cursor-pointer text-xs text-emerald-700">
                {language === 'ar' ? 'أسئلة للمتابعة' : 'Follow-up questions'}
              </summary>
              <ul className="mt-2 text-sm list-disc list-inside">
                {(language === 'ar'
                  ? storytelling.followUpQuestionsArabic
                  : storytelling.followUpQuestionsEnglish
                ).map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
