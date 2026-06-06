import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, AlertCircle, BookOpen } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import {
  entitiesApi,
  type EntityDetail,
  type EntityJourneyOrder,
  type ExplainConnectionResponse,
  type JourneyResponse,
} from '../lib/api';
import { ImplicitConnections } from '../components/entities/ImplicitConnections';

const ORDER_LABELS: Record<EntityJourneyOrder, { ar: string; en: string }> = {
  mushaf: { ar: 'ترتيب المصحف', en: 'Mushaf order' },
  story_world: { ar: 'الترتيب القصصي', en: 'Story-world order' },
  revelation: { ar: 'ترتيب النزول', en: 'Revelation order' },
  thematic: { ar: 'الترتيب الموضوعي', en: 'Thematic order' },
};

const CERTAINTY_LABELS: Record<string, { ar: string; en: string; cls: string }> = {
  high: { ar: 'يقين عالٍ', en: 'high certainty', cls: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
  medium: { ar: 'يقين متوسط', en: 'medium certainty', cls: 'bg-yellow-50 text-yellow-800 border-yellow-200' },
  low: { ar: 'يقين منخفض', en: 'low certainty', cls: 'bg-orange-50 text-orange-800 border-orange-200' },
  disputed: { ar: 'محل خلاف', en: 'disputed', cls: 'bg-red-50 text-red-800 border-red-200' },
};

export function EntityJourneyPage() {
  const { entityId = '' } = useParams<{ entityId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const [order, setOrder] = useState<EntityJourneyOrder>('mushaf');
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Compare-two-mentions UI
  const [picked, setPicked] = useState<Array<{ surahNumber: number; ayahStart: number }>>([]);
  const [explanation, setExplanation] = useState<ExplainConnectionResponse | null>(null);
  const [explLoading, setExplLoading] = useState(false);
  const [explError, setExplError] = useState<string | null>(null);

  useEffect(() => {
    let stale = false;
    setLoading(true);
    entitiesApi
      .get(entityId)
      .then((d) => !stale && setDetail(d))
      .catch((e) => !stale && setError(e?.message || 'Failed to load entity'))
      .finally(() => !stale && setLoading(false));
    return () => {
      stale = true;
    };
  }, [entityId]);

  useEffect(() => {
    let stale = false;
    setJourney(null);
    setError(null);
    entitiesApi
      .journey(entityId, order)
      .then((j) => !stale && setJourney(j))
      .catch((e) => !stale && setError(e?.message || 'Failed to load journey'));
    return () => {
      stale = true;
    };
  }, [entityId, order]);

  function pickAyah(s: number, a: number) {
    const next = [...picked, { surahNumber: s, ayahStart: a }];
    if (next.length > 2) next.shift();
    setPicked(next);
    setExplanation(null);
    setExplError(null);
  }

  async function runExplain() {
    if (picked.length !== 2) return;
    setExplLoading(true);
    setExplError(null);
    try {
      const r = await entitiesApi.explainConnection({
        entityId,
        sourceReference: picked[0],
        targetReference: picked[1],
        relationTypes: ['mentioned_with'],
        sourceIds: [],
        language,
      });
      setExplanation(r);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to explain';
      setExplError(msg);
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
        to={`/entities/${encodeURIComponent(entityId)}`}
        className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:text-emerald-900 mb-3"
      >
        <ArrowLeft className="w-4 h-4" />
        {language === 'ar' ? 'العودة إلى الذات' : 'Back to entity'}
      </Link>

      {detail && (
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          <span dir="ltr">{detail.labelEnglish}</span> —{' '}
          <span dir="rtl" className="font-arabic">{detail.labelArabic}</span>
        </h1>
      )}
      <p className="text-sm text-gray-500 mb-5 flex items-center gap-1">
        <BookOpen className="w-4 h-4" />
        {language === 'ar' ? 'الرحلة القرآنية' : 'Quran journey'}
      </p>

      {/* Order tabs */}
      <div className="mb-5 flex flex-wrap gap-2">
        {(Object.keys(ORDER_LABELS) as EntityJourneyOrder[]).map((o) => (
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
          <div className="mb-4 flex flex-wrap items-center gap-3 text-sm">
            {CERTAINTY_LABELS[journey.certainty] && (
              <span
                className={`px-2 py-0.5 rounded border ${CERTAINTY_LABELS[journey.certainty].cls}`}
              >
                {CERTAINTY_LABELS[journey.certainty][language]}
              </span>
            )}
            <span className="text-gray-500">
              {journey.sections.length}{' '}
              {language === 'ar' ? 'قسم' : 'sections'}
            </span>
          </div>

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
                    {s.ayahReferences.map((r, i) => {
                      const isPicked = picked.some(
                        (p) => p.surahNumber === r.surahNumber && p.ayahStart === r.ayahStart
                      );
                      return (
                        <button
                          key={`${r.surahNumber}:${r.ayahStart}:${i}`}
                          type="button"
                          onClick={() => pickAyah(r.surahNumber, r.ayahStart)}
                          className={`text-xs px-2 py-0.5 rounded border ${
                            isPicked
                              ? 'bg-emerald-600 text-white border-emerald-700'
                              : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
                          }`}
                        >
                          {r.surahNumber}:{r.ayahStart}
                          {r.ayahEnd && r.ayahEnd !== r.ayahStart ? `-${r.ayahEnd}` : ''}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}

      {/* Compare two passages */}
      <div className="mt-8 p-4 bg-emerald-50/40 border border-emerald-200 rounded-lg">
        <h2 className="font-semibold text-gray-900 mb-2">
          {language === 'ar' ? 'لماذا ترتبط هذه الآيات؟' : 'Why are these ayahs connected?'}
        </h2>
        <p className="text-sm text-gray-600 mb-3">
          {language === 'ar'
            ? 'اختر آيتين من القائمة أعلاه ثم اضغط على «اشرح الربط».'
            : 'Pick two ayahs above, then click "Explain connection".'}
        </p>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          {picked.map((p, i) => (
            <span
              key={i}
              className="text-sm px-2 py-1 bg-white border border-emerald-300 rounded"
            >
              {p.surahNumber}:{p.ayahStart}
            </span>
          ))}
          {picked.length < 2 && (
            <span className="text-xs text-gray-500">
              {language === 'ar'
                ? `بحاجة إلى ${2 - picked.length} مرجعًا أكثر`
                : `${2 - picked.length} more needed`}
            </span>
          )}
          <div className="flex-1" />
          <button
            type="button"
            onClick={runExplain}
            disabled={picked.length !== 2 || explLoading}
            className="px-3 py-1.5 text-sm rounded-md bg-emerald-600 text-white disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {explLoading
              ? language === 'ar'
                ? 'جارٍ التحميل...'
                : 'Loading…'
              : language === 'ar'
              ? 'اشرح الربط'
              : 'Explain connection'}
          </button>
          {picked.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setPicked([]);
                setExplanation(null);
                setExplError(null);
              }}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              {language === 'ar' ? 'إعادة' : 'reset'}
            </button>
          )}
        </div>

        {explError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
            {explError}
          </div>
        )}

        {/* Implicit connections panel — Phase U */}
        <div className="mt-6">
          <ImplicitConnections entityId={entityId} />
        </div>

        {explanation && (
          <div className="p-3 bg-white border border-emerald-200 rounded-lg space-y-3">
            <p dir="rtl" className="font-arabic text-gray-800">
              {explanation.explanationArabic}
            </p>
            <p dir="ltr" className="text-gray-800">
              {explanation.explanationEnglish}
            </p>
            {explanation.tafsirEvidence.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-1">
                  {language === 'ar' ? 'مصادر تفسيرية' : 'Tafsir evidence'}
                </h4>
                <ul className="text-xs text-gray-700 space-y-0.5">
                  {explanation.tafsirEvidence.map((t, i) => (
                    <li key={i}>
                      <code>{t.sourceId}</code> — {t.reference} ({t.relationStatus})
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
    </div>
  );
}
