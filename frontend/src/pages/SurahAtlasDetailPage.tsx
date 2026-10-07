/**
 * Surah Atlas Detail Page
 *
 * Shows the full atlas entry for a single surah:
 * - Hero with stats
 * - Quick understanding section
 * - Structure map
 * - Stories in this surah
 * - Themes and concepts
 * - Memorization section
 * - Evidence panel
 *
 * Safety: Review warnings shown for all unverified content.
 */

import { useParams, Link } from 'react-router-dom';
import { useMemo } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  AlertTriangle,
  Layers,
  ChevronRight,
  RefreshCw,
  type LucideIcon,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { getSurahAtlasEntry, SURAH_ATLAS_DATA } from '../data/surahAtlas';
import { SurahAtlasHero } from '../components/atlas/SurahAtlasHero';
import {
  getMemorizationLinksForSurah,
  getConfusionPairsForSurah,
  STORY_RECURRENCES,
} from '../data/quranMemorizationLinks';

const STORY_TITLE_MAP = Object.fromEntries(
  STORY_RECURRENCES.map((r) => [r.storyId, { en: r.titleEn, ar: r.titleAr }]),
);

function storyTitle(storyId: string, isAr: boolean): string {
  const t = STORY_TITLE_MAP[storyId];
  if (t) return isAr ? t.ar : t.en;
  return storyId.replace('story_', '').replace(/_/g, ' ');
}
import { getRareWordsBySurah } from '../data/quranRareWords';
import { SimilarAyatCard, ConfusionPairCard } from '../components/quran/SimilarAyatCard';
import { StoryRecurrenceCard } from '../components/quran/MemorizerHintCard';

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------

function Section({ title, icon: Icon, children, className }: {
  title: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={clsx('bg-white rounded-2xl border p-5 mb-4', className)}>
      <div className="flex items-center gap-2 mb-4">
        {Icon && <Icon size={18} className="text-primary-600" />}
        <h2 className="text-base font-bold text-gray-900">{title}</h2>
      </div>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Review warning
// ---------------------------------------------------------------------------

function ReviewWarning({ isAr }: { isAr: boolean }) {
  return (
    <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3">
      <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
      <span>
        {isAr
          ? 'هذا المحتوى قيد المراجعة العلمية ولا ينبغي اعتباره تفسيراً موثوقاً.'
          : 'This content is pending scholarly review and should not be taken as authoritative tafsir.'}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function SurahAtlasDetailPage() {
  const { surahNumber: surahParam } = useParams<{ surahNumber: string }>();
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const surahNum = parseInt(surahParam ?? '0', 10);
  const entry = useMemo(() => getSurahAtlasEntry(surahNum), [surahNum]);

  const memLinks = useMemo(() => getMemorizationLinksForSurah(surahNum), [surahNum]);
  const confusionPairs = useMemo(() => getConfusionPairsForSurah(surahNum), [surahNum]);
  const rareWords = useMemo(() => getRareWordsBySurah(surahNum), [surahNum]);
  const storyRecurrences = useMemo(
    () => STORY_RECURRENCES.filter((r) =>
      r.surahOccurrences.some((o) => o.surahNumber === surahNum),
    ),
    [surahNum],
  );

  // Declared before the not-found return so hooks run in the same order on every render.
  const prevEntry = useMemo(() => surahNum > 1 ? getSurahAtlasEntry(surahNum - 1) : null, [surahNum]);
  const nextEntry = useMemo(() => surahNum < 114 ? getSurahAtlasEntry(surahNum + 1) : null, [surahNum]);

  if (!entry || surahNum < 1 || surahNum > 114) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle size={40} className="mx-auto mb-4 text-amber-500" />
          <h1 className="text-lg font-bold text-gray-900 mb-2">
            {isAr ? 'السورة غير موجودة' : 'Surah not found'}
          </h1>
          <Link to="/surah-atlas" className="text-primary-600 hover:underline text-sm">
            {isAr ? '← العودة إلى أطلس السور' : '← Back to Surah Atlas'}
          </Link>
        </div>
      </div>
    );
  }

  const indexedCount = SURAH_ATLAS_DATA.filter((s) => s.structure.length > 0).length;

  return (
    <div className={clsx('min-h-screen bg-gray-50', isAr ? 'font-arabic' : '')}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Back navigation */}
        <Link
          to="/surah-atlas"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={14} />
          {isAr ? 'أطلس السور' : 'Surah Atlas'}
        </Link>

        {/* Hero */}
        <SurahAtlasHero entry={entry} />

        {/* Two-column layout on large screens */}
        <div className="lg:grid lg:grid-cols-2 lg:gap-4">
          {/* LEFT column */}
          <div>
            {/* Section A — Quick Understanding */}
            <Section title={isAr ? 'فهم سريع' : 'Quick Understanding'} icon={BookOpen}>
              <ReviewWarning isAr={isAr} />
              <div className="mt-4 space-y-3">
                <div className="bg-gray-50 rounded-xl p-4">
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">
                    {isAr ? 'الملخص القصير' : 'Short Summary'}
                  </h3>
                  <p className="text-sm text-gray-800 leading-relaxed" dir={isAr ? 'rtl' : 'ltr'}>
                    {isAr ? entry.summary.short.ar : entry.summary.short.en}
                  </p>
                  {entry.summarySource && (
                    <p className="text-xs text-gray-400 mt-2 italic" dir="ltr">
                      {isAr ? 'المصدر: ' : 'Source: '}{entry.summarySource}
                    </p>
                  )}
                </div>
                {(isAr ? (entry.keyConceptsAr ?? entry.keyConcepts) : entry.keyConcepts).length > 0 && (
                  <div>
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">
                      {isAr ? 'المفاهيم الرئيسية' : 'Key Concepts'}
                    </h3>
                    <div className="flex flex-wrap gap-2" dir={isAr ? 'rtl' : 'ltr'}>
                      {(isAr ? (entry.keyConceptsAr ?? entry.keyConcepts) : entry.keyConcepts).map((c) => (
                        <span key={c} className="text-xs bg-primary-50 text-primary-700 border border-primary-200 rounded-full px-2.5 py-1">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Section>

            {/* Section B — Structure */}
            {entry.structure.length === 0 ? (
              <Section title={isAr ? 'هيكل السورة' : 'Surah Structure'} icon={Layers}>
                <div className="text-center py-8 text-gray-400">
                  <Layers size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm mb-1">
                    {isAr
                      ? 'هيكل السورة التفصيلي يتطلب مراجعة علمية متخصصة.'
                      : 'Detailed surah structure requires specialist scholarly input.'}
                  </p>
                  <p className="text-xs text-gray-400 mb-3">
                    {isAr
                      ? `مفهرسة: ${indexedCount} من 114 سورة`
                      : `Indexed: ${indexedCount} of 114 surahs`}
                  </p>
                  <ReviewWarning isAr={isAr} />
                </div>
              </Section>
            ) : (
              <Section title={isAr ? 'هيكل السورة' : 'Surah Structure'} icon={Layers}>
                {entry.structure.map((section) => (
                  <div key={section.id} className="mb-4 border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold text-gray-800">
                        {isAr ? section.title.ar : section.title.en}
                      </span>
                      <span className="text-xs text-gray-400">
                        {surahNum}:{section.ayahRange.start}–{section.ayahRange.end}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      {isAr ? section.summary.ar : section.summary.en}
                    </p>
                  </div>
                ))}
                <ReviewWarning isAr={isAr} />
              </Section>
            )}

            {/* Section D — Rare Words */}
            <Section title={isAr ? 'المفردات النادرة' : 'Rare Words'} icon={BookOpen}>
              {rareWords.length === 0 ? (
                <div className="text-center py-6 text-gray-400">
                  <p className="text-sm">
                    {isAr
                      ? 'بيانات المفردات النادرة لهذه السورة قيد الإنشاء.'
                      : 'Rare word data for this surah is being built.'}
                  </p>
                  <ReviewWarning isAr={isAr} />
                </div>
              ) : (
                <div className="space-y-3">
                  {rareWords.map((w) => (
                    <div key={w.id} className="border rounded-xl p-4">
                      <div className="flex items-start gap-3 mb-2">
                        <div dir="rtl" className="text-xl font-bold text-gray-900">{w.arabic}</div>
                        <div className="text-xs text-gray-500 mt-1 italic">{w.transliteration}</div>
                        <span className="ml-auto text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-full px-2 py-0.5">
                          {w.rarityLevel}
                        </span>
                      </div>
                      <div className="text-sm text-gray-800 mb-1">
                        <strong>{isAr ? 'المعنى: ' : 'Meaning: '}</strong>
                        {isAr ? w.simpleMeaning.ar : w.simpleMeaning.en}
                      </div>
                      <div className="text-xs text-gray-600">
                        <strong>{isAr ? 'في السياق: ' : 'In context: '}</strong>
                        {isAr ? w.contextualMeaning.ar : w.contextualMeaning.en}
                      </div>
                      {w.reviewStatus === 'needs_review' && (
                        <div className="flex items-center gap-1 text-xs text-amber-600 mt-2">
                          <AlertTriangle size={11} />
                          <span>{isAr ? 'قيد المراجعة' : 'Pending review'}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          </div>

          {/* RIGHT column */}
          <div>
            {/* Section C — Stories */}
            {entry.storiesMentioned.length > 0 && (
              <Section title={isAr ? 'القصص في هذه السورة' : 'Stories in This Surah'} icon={BookOpen}>
                <div className="space-y-2">
                  {entry.storiesMentioned.map((s) => (
                    <Link
                      key={s.storyId}
                      to={`/stories/${s.storyId}`}
                      className="flex items-center justify-between gap-3 p-3 rounded-xl border hover:bg-gray-50 hover:border-primary-300 transition-colors"
                    >
                      <div>
                        <div className="text-sm font-medium text-gray-800" dir={isAr ? 'rtl' : 'ltr'}>
                          {storyTitle(s.storyId, isAr)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {s.ayahRange.display}
                          {s.coverage && (
                            <span className={clsx(
                              'ml-1.5 px-1.5 py-0.5 rounded text-[10px]',
                              s.coverage === 'complete' ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-500'
                            )}>
                              {s.coverage}
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRight size={14} className="text-gray-400 flex-shrink-0" />
                    </Link>
                  ))}
                </div>
                <ReviewWarning isAr={isAr} />
              </Section>
            )}

            {/* Section E — Memorizer Guide */}
            <Section title={isAr ? 'دليل الحافظ' : 'Memorizer Guide'} icon={RefreshCw}>
              {confusionPairs.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">
                    {isAr ? 'لا تخلط بين' : 'Do Not Confuse'}
                  </h3>
                  <div className="space-y-3">
                    {confusionPairs.map((pair) => (
                      <ConfusionPairCard key={pair.id} pair={pair} currentSurah={surahNum} />
                    ))}
                  </div>
                </div>
              )}
              {memLinks.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">
                    {isAr ? 'آيات مشابهة' : 'Similar Ayat'}
                  </h3>
                  <div className="space-y-3">
                    {memLinks.map((link) => (
                      <SimilarAyatCard key={link.id} link={link} currentSurah={surahNum} />
                    ))}
                  </div>
                </div>
              )}
              {storyRecurrences.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">
                    {isAr ? 'تكرار القصص' : 'Story Recurrences'}
                  </h3>
                  <div className="space-y-3">
                    {storyRecurrences.map((r) => (
                      <StoryRecurrenceCard key={r.storyId} recurrence={r} currentSurah={surahNum} />
                    ))}
                  </div>
                </div>
              )}
              {confusionPairs.length === 0 && memLinks.length === 0 && storyRecurrences.length === 0 && (
                <div className="text-center py-6 text-gray-400">
                  <RefreshCw size={28} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">
                    {isAr
                      ? 'بيانات دليل الحافظ لهذه السورة قيد الإنشاء.'
                      : 'Memorizer guide data for this surah is being built.'}
                  </p>
                </div>
              )}
              <ReviewWarning isAr={isAr} />
            </Section>
          </div>
        </div>

        {/* Named prev/next navigation */}
        <div className="flex items-stretch gap-2 mt-4">
          {prevEntry ? (
            <Link
              to={`/surah-atlas/${surahNum - 1}`}
              className="flex-1 flex items-center gap-2 p-3 bg-white border border-gray-200 rounded-xl hover:border-primary-400 hover:shadow-sm transition-all group"
            >
              <ArrowLeft size={16} className="text-gray-400 group-hover:text-primary-600 flex-shrink-0" />
              <div>
                <div className="text-xs text-gray-400">{isAr ? 'السورة السابقة' : 'Previous'}</div>
                <div className={clsx('text-sm font-semibold text-gray-700 group-hover:text-primary-700', isAr && 'font-arabic')}>
                  {surahNum - 1}. {isAr ? prevEntry.nameArabic : prevEntry.nameTransliteration}
                </div>
              </div>
            </Link>
          ) : <div className="flex-1" />}
          {nextEntry ? (
            <Link
              to={`/surah-atlas/${surahNum + 1}`}
              className="flex-1 flex items-center justify-end gap-2 p-3 bg-white border border-gray-200 rounded-xl hover:border-primary-400 hover:shadow-sm transition-all group text-right"
            >
              <div>
                <div className="text-xs text-gray-400">{isAr ? 'السورة التالية' : 'Next'}</div>
                <div className={clsx('text-sm font-semibold text-gray-700 group-hover:text-primary-700', isAr && 'font-arabic')}>
                  {surahNum + 1}. {isAr ? nextEntry.nameArabic : nextEntry.nameTransliteration}
                </div>
              </div>
              <ArrowRight size={16} className="text-gray-400 group-hover:text-primary-600 flex-shrink-0" />
            </Link>
          ) : <div className="flex-1" />}
        </div>
      </div>
    </div>
  );
}
