import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, BookOpen, AlertCircle } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  topicsApi,
  type ExplainTopicLinkResponse,
  type TopicDetailResponse,
  type TopicJourneyOrder,
  type TopicJourneyResponse,
} from '../lib/api';

const ORDER_LABELS: Record<TopicJourneyOrder, { ar: string; en: string }> = {
  mushaf: { ar: 'ترتيب المصحف', en: 'Mushaf order' },
  surah: { ar: 'حسب السورة', en: 'By surah' },
  story: { ar: 'حسب القصة', en: 'By story link' },
  entity: { ar: 'حسب الذوات', en: 'By entity' },
  emotional: { ar: 'تأمل وجداني', en: 'Emotional reflection' },
};

export function TopicJourneyPage() {
  const { topicId = '' } = useParams<{ topicId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [order, setOrder] = useState<TopicJourneyOrder>('mushaf');
  const [detail, setDetail] = useState<TopicDetailResponse | null>(null);
  const [journey, setJourney] = useState<TopicJourneyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [explainFor, setExplainFor] = useState<{ s: number; a: number } | null>(null);
  const [explanation, setExplanation] = useState<ExplainTopicLinkResponse | null>(null);
  const [explLoading, setExplLoading] = useState(false);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    topicsApi
      .get(topicId)
      .then((d) => !stale && setDetail(d))
      .catch((e) => !stale && setError(e?.message || 'Failed to load topic'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [topicId]);

  useEffect(() => {
    let stale = false;
    setJourney(null);
    topicsApi
      .journey(topicId, order)
      .then((j) => !stale && setJourney(j))
      .catch((e) => !stale && setError(e?.message || 'Failed to load journey'));
    return () => {
      stale = true;
    };
  }, [topicId, order]);

  async function openExplain(s: number, a: number) {
    setExplainFor({ s, a });
    setExplanation(null);
    setExplLoading(true);
    try {
      const r = await topicsApi.explainLink({
        topicId,
        surahNumber: s,
        ayahNumber: a,
        language,
        sourceIds: [],
      });
      setExplanation(r);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to explain';
      setExplanation({
        explanationArabic: msg,
        explanationEnglish: msg,
        topicId,
        surahNumber: s,
        ayahNumber: a,
        sourceIds: [],
        warnings: [msg],
        reviewStatus: 'needs_review',
      });
    } finally {
      setExplLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="max-w-3xl mx-auto py-10 px-4">
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">{error}</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6" dir={dir}>
      <Link
        to={`/topics/${encodeURIComponent(topicId)}`}
        className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-3"
      >
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'العودة' : 'Back to topic'}
      </Link>

      {detail && (
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          <span dir="ltr">{detail.labelEnglish}</span> —{' '}
          <span dir="rtl" className="font-arabic">
            {detail.labelArabic}
          </span>
        </h1>
      )}
      <p className="text-sm text-gray-500 mb-5 flex items-center gap-1">
        <BookOpen className="w-4 h-4" />
        {language === 'ar' ? 'الرحلة الموضوعية' : 'Topic journey'}
      </p>

      <div className="mb-5 flex flex-wrap gap-2">
        {(Object.keys(ORDER_LABELS) as TopicJourneyOrder[]).map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => setOrder(o)}
            className={`px-3 py-1.5 text-sm rounded-md border ${
              order === o
                ? 'bg-emerald-600 text-white border-emerald-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {ORDER_LABELS[o][language]}
          </button>
        ))}
      </div>

      {!journey && (
        <div className="py-10 flex justify-center">
          <Loader2 className="w-6 h-6 text-emerald-600 animate-spin" />
        </div>
      )}

      {journey && (
        <>
          {journey.warnings.length > 0 && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <ul className="text-sm text-amber-800 space-y-1">
                {journey.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <ol className="relative border-s-2 border-emerald-200 ms-3 space-y-5">
            {journey.sections.map((s) => (
              <li key={s.sectionId} className="ms-4">
                <div className="absolute w-3 h-3 bg-emerald-600 rounded-full -start-[7px] mt-2" />
                <div className="p-3 bg-white border border-gray-200 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {language === 'ar' ? s.labelArabic : s.labelEnglish}
                  </h3>
                  {s.warnings.length > 0 && (
                    <p className="text-xs text-amber-700 mb-2">{s.warnings[0]}</p>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {s.ayahReferences.map((r, i) => (
                      <button
                        key={`${r.surahNumber}:${r.ayahStart}:${i}`}
                        type="button"
                        onClick={() => openExplain(r.surahNumber, r.ayahStart)}
                        className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                      >
                        {r.surahNumber}:{r.ayahStart}
                      </button>
                    ))}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}

      {explainFor && (
        <div className="mt-6 p-3 bg-emerald-50/40 border border-emerald-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold">
              {language === 'ar'
                ? `لماذا الآية ${explainFor.s}:${explainFor.a} مرتبطة بالموضوع؟`
                : `Why is ayah ${explainFor.s}:${explainFor.a} linked to this topic?`}
            </h4>
            <button
              type="button"
              onClick={() => {
                setExplainFor(null);
                setExplanation(null);
              }}
              className="text-xs text-gray-500"
            >
              {language === 'ar' ? 'إغلاق' : 'close'}
            </button>
          </div>
          {explLoading && <Loader2 className="w-4 h-4 text-emerald-700 animate-spin" />}
          {explanation && (
            <div className="space-y-2">
              <p dir="rtl" className="font-arabic text-gray-800 text-sm">
                {explanation.explanationArabic}
              </p>
              <p dir="ltr" className="text-gray-800 text-sm">
                {explanation.explanationEnglish}
              </p>
              {explanation.warnings.length > 0 && (
                <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">
                  <ul className="list-disc list-inside space-y-0.5">
                    {explanation.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
