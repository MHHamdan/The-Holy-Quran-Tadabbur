/**
 * Prophet Detail Page — profile view for a single prophet.
 *
 * Phase X. Backed by GET /api/v1/quran/prophets/{prophetId}.
 */

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  AlertCircle, ArrowRight, ArrowLeft, BookOpen, Users,
  Hash, Map, Scroll, Star, ChevronRight, ExternalLink,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { Skeleton } from '../components/ui/Skeleton';
import { prophetsApi, type ProphetProfile, type ProphetStoryPage } from '../lib/api';
import { getSurahName } from '../data/surahNames';

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function PageSkeleton({ dir }: { dir: string }) {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-pulse" dir={dir}>
      <Skeleton variant="text" width="10%" height={14} className="mb-6" />
      <div className="flex items-center gap-3 mb-6">
        <Skeleton variant="circular" width={44} height={44} />
        <div>
          <Skeleton variant="text" width={200} height={28} className="mb-1" />
          <Skeleton variant="text" width={120} height={16} />
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="p-4 bg-white border border-gray-200 rounded-xl">
            <Skeleton variant="text" width="60%" height={28} className="mx-auto mb-2" />
            <Skeleton variant="text" width="70%" height={12} className="mx-auto" />
          </div>
        ))}
      </div>
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-4">
        <Skeleton variant="text" width="30%" height={20} className="mb-4" />
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex gap-3 mb-4">
            <Skeleton variant="circular" width={28} height={28} className="flex-shrink-0" />
            <div className="flex-1">
              <Skeleton variant="text" width="50%" height={16} className="mb-1" />
              <Skeleton variant="text" width="90%" height={12} />
              <Skeleton variant="text" width="75%" height={12} className="mt-1" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat box — color coded by magnitude tier
// ---------------------------------------------------------------------------

function StatBox({ label, value, icon: Icon, max = 150 }: {
  label: string;
  value: number;
  icon: React.ElementType;
  max?: number;
}) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const tier = pct > 60 ? 'high' : pct > 25 ? 'mid' : 'low';
  const cls = {
    high: { bg: 'bg-emerald-50', border: 'border-emerald-200', num: 'text-emerald-700', bar: 'bg-emerald-400' },
    mid:  { bg: 'bg-blue-50',    border: 'border-blue-200',    num: 'text-blue-700',    bar: 'bg-blue-400' },
    low:  { bg: 'bg-gray-50',    border: 'border-gray-200',    num: 'text-gray-700',    bar: 'bg-gray-300' },
  }[tier];

  return (
    <div className={clsx('p-4 rounded-xl border flex flex-col items-center gap-1', cls.bg, cls.border)}>
      <Icon className={clsx('w-4 h-4 mb-1', cls.num)} />
      <div className={clsx('text-2xl font-bold', cls.num)}>{value}</div>
      <div className="text-xs text-gray-500 text-center leading-tight">{label}</div>
      <div className="w-full h-1.5 bg-white rounded-full mt-1 overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', cls.bar)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Story timeline section
// ---------------------------------------------------------------------------

function StoryTimeline({ sections, language }: {
  sections: ProphetStoryPage['storySections'];
  language: 'ar' | 'en';
}) {
  const isAr = language === 'ar';
  return (
    <div className="relative">
      {/* vertical guide line */}
      <div className={clsx('absolute top-4 bottom-0 w-px bg-emerald-100', isAr ? 'right-[18px]' : 'left-[18px]')} />
      <ol className="space-y-4 relative">
        {sections.map((s, idx) => (
          <li key={s.sectionId} className={clsx('flex gap-4', isAr && 'flex-row-reverse')}>
            {/* step circle */}
            <div className="w-9 h-9 flex-shrink-0 rounded-full bg-emerald-100 border-2 border-emerald-300 flex items-center justify-center text-xs font-bold text-emerald-700 z-10">
              {idx + 1}
            </div>
            {/* content */}
            <div className="flex-1 pb-2">
              <div className={clsx('bg-white border border-gray-200 rounded-xl p-4 hover:border-emerald-200 transition-colors', isAr && 'text-right')}>
                <h3 className={clsx('font-semibold text-gray-900 text-sm mb-1', isAr && 'font-arabic')}>
                  {isAr ? s.labelArabic : s.labelEnglish}
                </h3>
                {s.ayahReferences.length > 0 && (
                  <div className={clsx('flex flex-wrap gap-1 mb-2', isAr && 'justify-end')}>
                    {s.ayahReferences.slice(0, 10).map((r, i) => (
                      <Link
                        key={i}
                        to={`/quran/${r.surahNumber}`}
                        className="text-[10px] px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full hover:bg-emerald-100 transition-colors"
                        title={getSurahName(r.surahNumber)[isAr ? 'ar' : 'en']}
                      >
                        {getSurahName(r.surahNumber)[isAr ? 'ar' : 'en']} {r.surahNumber}:{r.ayahStart}{r.ayahEnd ? `–${r.ayahEnd}` : ''}
                      </Link>
                    ))}
                    {s.ayahReferences.length > 10 && (
                      <span className="text-[10px] px-2 py-0.5 bg-gray-50 text-gray-500 border border-gray-200 rounded-full">
                        +{s.ayahReferences.length - 10}
                      </span>
                    )}
                  </div>
                )}
                {(isAr ? s.summaryArabic : s.summaryEnglish) && (
                  <p className={clsx('text-sm text-gray-700 leading-relaxed', isAr && 'font-arabic')}>
                    {isAr ? s.summaryArabic : s.summaryEnglish}
                  </p>
                )}
                {s.warnings.length > 0 && (
                  <ul className="mt-2 text-xs text-amber-700 list-disc list-inside space-y-0.5">
                    {s.warnings.map((w) => <li key={w}>{w}</li>)}
                  </ul>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Coverage badge
// ---------------------------------------------------------------------------

const COVERAGE_META: Record<string, { ar: string; en: string; cls: string }> = {
  full_story:             { ar: 'قصة كاملة', en: 'Full story',      cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  compact_profile:        { ar: 'ملف موجز',  en: 'Compact profile', cls: 'bg-blue-50 text-blue-700 border-blue-200' },
  mission_summary:        { ar: 'رسالة',     en: 'Mission summary', cls: 'bg-purple-50 text-purple-700 border-purple-200' },
  limited_quran_mentions: { ar: 'ذكر محدود', en: 'Limited',         cls: 'bg-amber-50 text-amber-700 border-amber-200' },
  contextual_mentions:    { ar: 'سياقي',     en: 'Contextual',      cls: 'bg-gray-50 text-gray-700 border-gray-200' },
};

function CoverageBadge({ pageType, language }: { pageType: string; language: 'ar' | 'en' }) {
  const m = COVERAGE_META[pageType] ?? { ar: pageType, en: pageType, cls: 'bg-gray-50 text-gray-700 border-gray-200' };
  return (
    <span className={clsx('inline-block px-2.5 py-0.5 text-xs rounded-full border font-medium', m.cls)}>
      {language === 'ar' ? m.ar : m.en}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function ProphetDetailPage() {
  const { prophetId } = useParams<{ prophetId: string }>();
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const dir = isAr ? 'rtl' : 'ltr';
  const ArrowEnd = isAr ? ArrowLeft : ArrowRight;

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
    prophetsApi
      .storyPage(prophetId)
      .then((r) => !stale && setStoryPage(r))
      .catch(() => { /* no story page — UI falls back */ });
    return () => { stale = true; };
  }, [prophetId]);

  if (loading) return <PageSkeleton dir={dir} />;

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12" dir={dir}>
        <div className="p-4 border border-red-200 bg-red-50 text-red-800 rounded-xl flex items-start gap-2">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <p>{error ?? 'Prophet not found.'}</p>
        </div>
        <Link to="/prophets" className="mt-4 inline-flex items-center gap-1 text-emerald-700 hover:underline text-sm">
          <ArrowLeft className="w-4 h-4" /> {isAr ? 'العودة إلى الأطلس' : 'Back to atlas'}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8" dir={dir}>
      {/* Breadcrumb */}
      <Link to="/prophets" className="inline-flex items-center gap-1.5 text-sm text-emerald-700 hover:text-emerald-900 mb-5">
        <ArrowLeft className={clsx('w-4 h-4', isAr && 'rotate-180')} />
        {isAr ? 'الأطلس' : 'Prophets Atlas'}
      </Link>

      {/* Hero header */}
      <header className="flex items-start gap-4 mb-7">
        <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
          <BookOpen className="w-6 h-6 text-emerald-700" />
        </div>
        <div>
          <h1 className={clsx('text-3xl font-bold text-gray-900', isAr && 'font-arabic')}>
            {isAr ? data.nameArabic : data.nameEnglish}
          </h1>
          <p className={clsx('text-gray-500 mt-0.5', isAr && 'font-arabic')}>
            {isAr ? data.nameEnglish : data.nameArabic}
          </p>
        </div>
      </header>

      {/* Stat row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-7">
        <StatBox icon={Star}   label={isAr ? 'ذكر صريح'  : 'Explicit'}     value={data.explicitMentions.length}    max={150} />
        <StatBox icon={Hash}   label={isAr ? 'سياقي'     : 'Contextual'}   value={data.contextualMentions.length}  max={80}  />
        <StatBox icon={Users}  label={isAr ? 'إحالة'     : 'Coreference'}  value={data.coreferenceMentions.length} max={50}  />
        <StatBox icon={Map}    label={isAr ? 'سور'        : 'Surahs'}       value={data.surahCount}                 max={30}  />
      </div>

      {/* Coverage / review badges */}
      {(storyPage || data.warnings.length > 0) && (
        <div className="mb-5 flex flex-wrap gap-2">
          {storyPage && <CoverageBadge pageType={storyPage.pageType} language={language} />}
          {storyPage && (
            <span className="inline-flex items-center px-2.5 py-0.5 text-xs rounded-full border bg-amber-50 text-amber-700 border-amber-200">
              {storyPage.reviewStatus}
            </span>
          )}
        </div>
      )}

      {/* Warnings */}
      {data.warnings.length > 0 && (
        <div className="mb-5 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-sm">
          <p className="font-semibold mb-1">{isAr ? 'تنبيهات المراجعة' : 'Review warnings'}</p>
          <ul className="list-disc list-inside space-y-1">
            {data.warnings.map((w) => <li key={w}>{w}</li>)}
          </ul>
        </div>
      )}

      {storyPage?.warnings && storyPage.warnings.length > 0 && (
        <div className="mb-5 p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-xl text-sm">
          <p className="font-semibold mb-1">{isAr ? 'تنبيهات صفحة القصة' : 'Story-page warnings'}</p>
          <ul className="list-disc list-inside space-y-1">
            {storyPage.warnings.map((w) => <li key={w}>{w}</li>)}
          </ul>
        </div>
      )}

      {/* Story timeline */}
      {storyPage && storyPage.storySections.length > 0 && (
        <section className="mb-8 bg-white rounded-2xl border p-5">
          <div className="flex items-center gap-2 mb-5">
            <Scroll className="w-4 h-4 text-emerald-600" />
            <h2 className={clsx('text-base font-bold text-gray-900', isAr && 'font-arabic')}>
              {isAr ? 'السرد القرآني' : 'Quranic Narrative'}
            </h2>
            <span className="ml-auto text-xs text-gray-400">{storyPage.storySections.length} sections</span>
          </div>
          <StoryTimeline sections={storyPage.storySections} language={language} />
          <p className="text-xs text-gray-400 mt-4 italic">
            {isAr
              ? 'تصفّح إرشادي وليس تفسيراً. حالة المراجعة: needs_review.'
              : 'Navigation summary, not tafsir. Review status: needs_review.'}
          </p>
        </section>
      )}

      {/* Two-column layout for secondary info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {/* Names & aliases */}
        <section className="bg-white rounded-2xl border p-5">
          <h2 className={clsx('text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide', isAr && 'font-arabic')}>
            {isAr ? 'الأسماء والألقاب' : 'Names & Aliases'}
          </h2>
          {[...data.aliasesArabic, ...data.aliasesEnglish].length === 0 ? (
            <p className="text-sm text-gray-400">—</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {[...data.aliasesArabic, ...data.aliasesEnglish].map((a) => (
                <span key={a} className="text-xs px-2.5 py-1 rounded-full bg-gray-50 border border-gray-200 text-gray-700">
                  {a}
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Related topics */}
        <section className="bg-white rounded-2xl border p-5">
          <h2 className={clsx('text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide', isAr && 'font-arabic')}>
            {isAr ? 'الموضوعات' : 'Topics'}
          </h2>
          {data.relatedTopics.length === 0 ? (
            <p className="text-sm text-gray-400">—</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {data.relatedTopics.slice(0, 24).map((t) => (
                <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                  {t.replace(/^topic_/, '')}
                </span>
              ))}
              {data.relatedTopics.length > 24 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                  +{data.relatedTopics.length - 24}
                </span>
              )}
            </div>
          )}
        </section>
      </div>

      {/* Related stories */}
      <section className="bg-white rounded-2xl border p-5 mb-5">
        <h2 className={clsx('text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide', isAr && 'font-arabic')}>
          {isAr ? 'القصص المرتبطة' : 'Related Stories'}
        </h2>
        {data.storyIds.length === 0 ? (
          <p className="text-sm text-gray-400">
            {isAr ? 'لا توجد قصة منشورة بعد.' : 'No published story page yet.'}
          </p>
        ) : (
          <ul className="space-y-1.5">
            {data.storyIds.map((sid) => (
              <li key={sid}>
                <Link
                  to={`/stories/${sid}`}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-100 hover:border-emerald-200 hover:bg-emerald-50 transition-colors text-sm text-emerald-700 group"
                >
                  <BookOpen className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="flex-1">{sid.replace(/^story_/, '').replace(/_/g, ' ')}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-emerald-500 transition-colors" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Related prophets */}
      {data.relatedProphets.length > 0 && (
        <section className="bg-white rounded-2xl border p-5 mb-5">
          <h2 className={clsx('text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide', isAr && 'font-arabic')}>
            {isAr ? 'الأنبياء المرتبطون' : 'Related Prophets'}
          </h2>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {dedupeRelated(data.relatedProphets).map((r) => (
              <li key={`${r.targetProphetId}-${r.relationType}`}>
                <Link
                  to={`/prophets/${r.targetProphetId}`}
                  className="flex items-center gap-3 p-3 rounded-xl border hover:border-emerald-200 hover:bg-emerald-50 transition-colors group"
                >
                  <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Users className="w-4 h-4 text-emerald-700" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-sm text-emerald-700 group-hover:text-emerald-900">
                      {r.targetProphetId.replace(/^prophet_/, '')}
                    </div>
                    <div className="text-xs text-gray-500 truncate">{r.relationType}</div>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-emerald-500" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Explicit mentions grid */}
      {data.explicitMentions.length > 0 && (
        <section className="bg-white rounded-2xl border p-5 mb-7">
          <h2 className={clsx('text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide', isAr && 'font-arabic')}>
            {isAr ? `آيات صريحة (${Math.min(12, data.explicitMentions.length)} من ${data.explicitMentions.length})` : `Explicit mentions (first ${Math.min(12, data.explicitMentions.length)} of ${data.explicitMentions.length})`}
          </h2>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
            {data.explicitMentions.slice(0, 12).map((m, idx) => (
              <Link
                key={idx}
                to={`/quran/${m.surahNumber}`}
                className="text-xs p-2 rounded-lg bg-gray-50 border border-gray-200 text-center hover:bg-emerald-50 hover:border-emerald-200 transition-colors text-gray-600 hover:text-emerald-700"
                title={getSurahName(m.surahNumber)[isAr ? 'ar' : 'en']}
              >
                <span className={isAr ? 'font-arabic block text-[10px]' : 'block text-[10px] truncate'}>
                  {getSurahName(m.surahNumber)[isAr ? 'ar' : 'en']}
                </span>
                <span className="font-mono">{m.surahNumber}:{m.ayahNumber}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        <Link
          to={`/prophets/${data.prophetId}/journey`}
          className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 text-sm font-semibold inline-flex items-center gap-2 transition-colors"
        >
          {isAr ? 'استكشف الرحلة' : 'Explore journey'} <ArrowEnd className="w-4 h-4" />
        </Link>
        <Link
          to={`/ask?topic=prophet&prophet=${data.prophetId}`}
          className="px-5 py-2.5 bg-white text-emerald-700 border border-emerald-300 rounded-xl hover:bg-emerald-50 text-sm font-semibold transition-colors"
        >
          {isAr ? 'اسأل مساعد التفسير' : 'Ask the Tafsir Assistant'}
        </Link>
      </div>
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
