/**
 * Prophet Detail Page — profile view for a single prophet.
 *
 * Phase X. Backed by GET /api/v1/quran/prophets/{prophetId}.
 */

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Loader2, AlertCircle, ArrowRight, ArrowLeft, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { prophetsApi, type ProphetProfile, type ProphetStoryPage } from '../lib/api';

export function ProphetDetailPage() {
  const { prophetId } = useParams<{ prophetId: string }>();
  const { language } = useLanguageStore();
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const ArrowEnd = language === 'ar' ? ArrowLeft : ArrowRight;

  const [data, setData] = useState<ProphetProfile | null>(null);
  const [storyPage, setStoryPage] = useState<ProphetStoryPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!prophetId) return;
    let stale = false;
    setLoading(true);
    setStoryPage(null);
    prophetsApi
      .get(prophetId)
      .then((r) => !stale && setData(r))
      .catch((e) => !stale && setError(e?.message || 'Failed to load prophet'))
      .finally(() => !stale && setLoading(false));
    // Try to load the story page; 404 is acceptable.
    prophetsApi
      .storyPage(prophetId)
      .then((r) => !stale && setStoryPage(r))
      .catch(() => {
        /* no story page for this prophet — UI shows fallback */
      });
    return () => {
      stale = true;
    };
  }, [prophetId]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-emerald-600 animate-spin" />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12" dir={dir}>
        <div className="p-4 border border-red-200 bg-red-50 text-red-800 rounded-md flex items-start gap-2">
          <AlertCircle className="w-5 h-5 mt-0.5" />
          <p>{error ?? 'Prophet not found.'}</p>
        </div>
        <Link to="/prophets" className="mt-4 inline-block text-emerald-700 hover:underline">
          ← {language === 'ar' ? 'العودة إلى الأطلس' : 'Back to atlas'}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8" dir={dir}>
      <Link to="/prophets" className="text-sm text-emerald-700 hover:underline">
        ← {language === 'ar' ? 'الأطلس' : 'Atlas'}
      </Link>

      <header className="mt-3 mb-6">
        <h1 className={clsx('text-3xl font-bold text-gray-900 flex items-center gap-3', language === 'ar' && 'font-arabic')}>
          <BookOpen className="w-7 h-7 text-emerald-600" />
          {language === 'ar' ? data.nameArabic : data.nameEnglish}
        </h1>
        <p className={clsx('text-gray-600 mt-1', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? data.nameEnglish : data.nameArabic}
        </p>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        <Stat label={language === 'ar' ? 'ذكر صريح' : 'Explicit'} value={data.explicitMentions.length} />
        <Stat label={language === 'ar' ? 'سياقي' : 'Contextual'} value={data.contextualMentions.length} />
        <Stat label={language === 'ar' ? 'إحالة' : 'Coreference'} value={data.coreferenceMentions.length} />
        <Stat label={language === 'ar' ? 'سور' : 'Surahs'} value={data.surahCount} />
      </div>

      {storyPage && (
        <div className="mb-4 flex flex-wrap gap-2">
          <CoverageBadge pageType={storyPage.pageType} language={language} />
          <span className="inline-flex items-center px-2 py-0.5 text-xs rounded-full border bg-amber-50 text-amber-700 border-amber-200">
            {storyPage.reviewStatus}
          </span>
        </div>
      )}

      {data.warnings.length > 0 && (
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-md text-sm">
          <p className="font-semibold mb-1">{language === 'ar' ? 'تنبيهات المراجعة' : 'Review warnings'}</p>
          <ul className="list-disc list-inside space-y-1">
            {data.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {storyPage && storyPage.warnings.length > 0 && (
        <div className="mb-6 p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-md text-sm">
          <p className="font-semibold mb-1">
            {language === 'ar' ? 'تنبيهات صفحة القصة' : 'Story-page warnings'}
          </p>
          <ul className="list-disc list-inside space-y-1">
            {storyPage.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {storyPage && storyPage.storySections.length > 0 && (
        <section className="mb-8">
          <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
            {language === 'ar' ? 'السرد القرآني بالشواهد' : 'Quranic Storytelling with Evidence'}
          </h2>
          <ol className="space-y-3">
            {storyPage.storySections.map((s) => (
              <li key={s.sectionId} className="p-3 bg-white border border-gray-200 rounded">
                <h3 className={clsx('font-semibold', language === 'ar' && 'font-arabic')}>
                  {language === 'ar' ? s.labelArabic : s.labelEnglish}
                </h3>
                {s.ayahReferences.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {s.ayahReferences.slice(0, 12).map((r, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-1.5 py-0.5 bg-gray-50 border border-gray-200 rounded"
                      >
                        {r.surahNumber}:{r.ayahStart}
                        {r.ayahEnd ? `-${r.ayahEnd}` : ''}
                      </span>
                    ))}
                    {s.ayahReferences.length > 12 && (
                      <span className="text-xs text-gray-500">
                        +{s.ayahReferences.length - 12}
                      </span>
                    )}
                  </div>
                )}
                {(language === 'ar' ? s.summaryArabic : s.summaryEnglish) && (
                  <p className={clsx('text-sm text-gray-800 mt-2', language === 'ar' && 'font-arabic')}>
                    {language === 'ar' ? s.summaryArabic : s.summaryEnglish}
                  </p>
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
          <p className="text-xs text-gray-500 mt-3">
            {language === 'ar'
              ? 'تصفّح إرشادي وليس تفسيراً. حالة المراجعة: needs_review.'
              : 'Navigation summary, not tafsir. Review status: needs_review.'}
          </p>
        </section>
      )}

      <section className="mb-8">
        <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'الأسماء والألقاب' : 'Names & aliases'}
        </h2>
        <div className="flex flex-wrap gap-2">
          {[...data.aliasesArabic, ...data.aliasesEnglish].map((a) => (
            <span key={a} className="text-xs px-2 py-1 rounded bg-gray-50 border border-gray-200">
              {a}
            </span>
          ))}
        </div>
      </section>

      <section className="mb-8">
        <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'القصص المرتبطة' : 'Related stories'}
        </h2>
        {data.storyIds.length === 0 ? (
          <p className="text-sm text-gray-500">{language === 'ar' ? 'لا توجد قصة منشورة لهذا النبي بعد.' : 'No published story page yet.'}</p>
        ) : (
          <ul className="space-y-1">
            {data.storyIds.map((sid) => (
              <li key={sid}>
                <Link to={`/stories/${sid}`} className="text-emerald-700 hover:underline">
                  {sid}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-8">
        <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'الأنبياء المرتبطون' : 'Related prophets'}
        </h2>
        {data.relatedProphets.length === 0 ? (
          <p className="text-sm text-gray-500">—</p>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {dedupeRelated(data.relatedProphets).map((r) => (
              <li key={`${r.targetProphetId}-${r.relationType}`} className="p-3 bg-white border border-gray-200 rounded text-sm">
                <Link to={`/prophets/${r.targetProphetId}`} className="font-semibold text-emerald-700 hover:underline">
                  {r.targetProphetId.replace(/^prophet_/, '')}
                </Link>
                <p className="text-xs text-gray-600 mt-1">{r.relationType}</p>
                <p className="text-xs text-gray-500 mt-1">{r.evidenceReferences.length} ayah refs</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-8">
        <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'الموضوعات المرتبطة' : 'Related topics'}
        </h2>
        {data.relatedTopics.length === 0 ? (
          <p className="text-sm text-gray-500">—</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {data.relatedTopics.slice(0, 30).map((t) => (
              <span key={t} className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">
                {t.replace(/^topic_/, '')}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="mb-8">
        <h2 className={clsx('text-lg font-semibold mb-2', language === 'ar' && 'font-arabic')}>
          {language === 'ar' ? 'آيات صريحة (أول 12)' : 'Explicit mentions (first 12)'}
        </h2>
        {data.explicitMentions.length === 0 ? (
          <p className="text-sm text-gray-500">—</p>
        ) : (
          <ul className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {data.explicitMentions.slice(0, 12).map((m, idx) => (
              <li key={idx} className="text-xs p-2 rounded bg-gray-50 border border-gray-200 text-center">
                {m.surahNumber}:{m.ayahNumber}
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link
          to={`/prophets/${data.prophetId}/journey`}
          className="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700 text-sm font-medium inline-flex items-center gap-2"
        >
          {language === 'ar' ? 'استكشف الرحلة' : 'Explore journey'} <ArrowEnd className="w-4 h-4" />
        </Link>
        <Link
          to={`/ask?topic=prophet&prophet=${data.prophetId}`}
          className="px-4 py-2 bg-white text-emerald-700 border border-emerald-300 rounded hover:bg-emerald-50 text-sm font-medium"
        >
          {language === 'ar' ? 'اسأل مساعد التفسير' : 'Ask the Tafsir Assistant'}
        </Link>
      </div>
    </div>
  );
}

function CoverageBadge(props: { pageType: string; language: 'ar' | 'en' }) {
  const LABEL: Record<string, { ar: string; en: string; cls: string }> = {
    full_story: { ar: 'قصة كاملة', en: 'Full story', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    compact_profile: { ar: 'ملف موجز', en: 'Compact profile', cls: 'bg-blue-50 text-blue-700 border-blue-200' },
    mission_summary: { ar: 'ملف الرسالة', en: 'Mission summary', cls: 'bg-purple-50 text-purple-700 border-purple-200' },
    limited_quran_mentions: { ar: 'ذكر محدود', en: 'Limited Quran mentions', cls: 'bg-amber-50 text-amber-700 border-amber-200' },
    contextual_mentions: { ar: 'سياقي', en: 'Contextual mentions', cls: 'bg-gray-50 text-gray-700 border-gray-200' },
  };
  const meta = LABEL[props.pageType] ?? { ar: props.pageType, en: props.pageType, cls: 'bg-gray-50 text-gray-700 border-gray-200' };
  return (
    <span className={clsx('inline-block px-2 py-0.5 text-xs rounded-full border', meta.cls)}>
      {props.language === 'ar' ? meta.ar : meta.en}
    </span>
  );
}

function Stat(props: { label: string; value: number }) {
  return (
    <div className="p-3 bg-white border border-gray-200 rounded-md text-center">
      <div className="text-2xl font-bold text-gray-900">{props.value}</div>
      <div className="text-xs text-gray-500 mt-1">{props.label}</div>
    </div>
  );
}

function dedupeRelated<T extends { targetProphetId: string; relationType: string }>(xs: T[]): T[] {
  const seen = new Set<string>();
  const out: T[] = [];
  for (const x of xs) {
    const k = `${x.targetProphetId}::${x.relationType}`;
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(x);
  }
  return out;
}
