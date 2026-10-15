/**
 * Memorization Links Page
 *
 * Helps memorizers navigate:
 * - Confusion pairs (easily mixed ayat)
 * - Similar ayat across surahs
 * - Repeated phrases
 * - Story recurrence maps
 * - Prophet story appearances across surahs
 *
 * Safety: All data is auto-generated and marked needs_review.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, AlertTriangle, Search, BookOpen, Layers, Mic, ArrowRight, type LucideIcon } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import {
  CONFUSION_PAIRS,
  MEMORIZATION_LINKS,
  REPEATED_PHRASES,
  STORY_RECURRENCES,
} from '../data/quranMemorizationLinks';
import { ConfusionPairCard, SimilarAyatCard } from '../components/quran/SimilarAyatCard';
import { RepeatedPhraseCard, StoryRecurrenceCard } from '../components/quran/MemorizerHintCard';
import { useLiveVerses } from '../components/quran/LiveVerse';
import { QuranTextAttribution } from '../components/quran/QuranTextAttribution';
import type { ConfusionPair } from '../types/quranMemorization';

type Tab = 'confusion' | 'similar' | 'phrases' | 'stories';

const TABS: { id: Tab; labelEn: string; labelAr: string; icon: LucideIcon }[] = [
  { id: 'confusion', labelEn: 'Confusion Pairs', labelAr: 'مواضع الالتباس', icon: AlertTriangle },
  { id: 'similar', labelEn: 'Similar Ayat', labelAr: 'آيات مشابهة', icon: Layers },
  { id: 'phrases', labelEn: 'Repeated Phrases', labelAr: 'العبارات المتكررة', icon: RefreshCw },
  { id: 'stories', labelEn: 'Story Recurrences', labelAr: 'تكرار القصص', icon: BookOpen },
];

// ─── Unreviewed confusion pairs: references + a diff computed from the text ──

const RISK_LABELS: Record<'high' | 'medium' | 'low', { ar: string; en: string }> = {
  high: { ar: 'خطر عالٍ', en: 'High risk' },
  medium: { ar: 'متوسط', en: 'Medium' },
  low: { ar: 'منخفض', en: 'Low' },
};

/** Letters only, for comparing words across the two passages. */
function wordKey(word: string): string {
  return word
    .replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, '')
    .replace(/[ٱأإآ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه');
}

function PassageWithDiff({ words, otherKeys }: { words: string[]; otherKeys: Set<string> }) {
  return (
    <p dir="rtl" lang="ar" className="font-mushaf text-lg leading-loose text-gray-900">
      {words.map((w, i) => {
        const k = wordKey(w);
        const differs = k.length > 0 && !otherKeys.has(k);
        return (
          <span key={i}>
            {differs ? <mark className="bg-amber-100 text-gray-900 rounded px-0.5">{w}</mark> : w}{' '}
          </span>
        );
      })}
    </p>
  );
}

function UnreviewedPairCard({ pair, language }: { pair: ConfusionPair; language: 'ar' | 'en' }) {
  const isAr = language === 'ar';
  // Fetched on request: the tab lists ~130 pairs.
  const [open, setOpen] = useState(false);
  const a = useLiveVerses(pair.ayahA.surah, pair.ayahA.ayah, pair.ayahA.rangeEnd ?? pair.ayahA.ayah, 'ar', open);
  const b = useLiveVerses(pair.ayahB.surah, pair.ayahB.ayah, pair.ayahB.rangeEnd ?? pair.ayahB.ayah, 'ar', open);
  const wordsA = (a.data ?? []).flatMap(v => v.text_uthmani.split(/\s+/));
  const wordsB = (b.data ?? []).flatMap(v => v.text_uthmani.split(/\s+/));
  const keysA = new Set(wordsA.map(wordKey));
  const keysB = new Set(wordsB.map(wordKey));
  const risk = RISK_LABELS[pair.riskLevel];

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-4 space-y-3" dir={isAr ? 'rtl' : 'ltr'}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={clsx('text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700', isAr && 'font-arabic')}>
          {isAr ? risk.ar : risk.en}
        </span>
        <span className={clsx('text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700', isAr && 'font-arabic')}>
          {isAr ? 'غير مُراجَع' : 'Unreviewed'}
        </span>
        <span className="text-sm text-gray-700">
          <bdi dir="ltr">{pair.ayahA.display}</bdi> · <bdi dir="ltr">{pair.ayahB.display}</bdi>
        </span>
      </div>
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className={clsx('text-xs text-primary-700 hover:underline', isAr && 'font-arabic')}
        >
          {isAr ? 'قارن النصين' : 'Compare the two texts'}
        </button>
      ) : a.isLoading || b.isLoading ? (
        <div className="h-16 rounded-lg bg-gray-100 animate-pulse" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {[{ ref: pair.ayahA, words: wordsA, other: keysB }, { ref: pair.ayahB, words: wordsB, other: keysA }].map(p => (
            <div key={p.ref.display} className="rounded-lg bg-gray-50 p-3">
              <Link to={`/quran/${p.ref.surah}?aya=${p.ref.ayah}`} className="text-xs text-primary-700 hover:underline">
                <bdi dir="ltr">{p.ref.display}</bdi>
              </Link>
              <PassageWithDiff words={p.words} otherKeys={p.other} />
            </div>
          ))}
        </div>
      )}
      {open && <p className={clsx('text-[11px] text-gray-500', isAr && 'font-arabic')}>
        {isAr
          ? 'الكلمات المظللة لا ترد في المقطع الآخر (مقارنة آلية للنص). شرح الفرق ونصيحة الحفظ يظهران بعد المراجعة العلمية.'
          : 'Highlighted words do not occur in the other passage (an automatic text comparison). The explanation and memorisation tip appear after scholarly review.'}
      </p>}
      {open && <QuranTextAttribution language={language} />}
    </article>
  );
}

export default function MemorizationLinksPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const [activeTab, setActiveTab] = useState<Tab>('confusion');
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const filteredConfusionPairs = useMemo(() => {
    let pairs = [...CONFUSION_PAIRS];
    if (riskFilter !== 'all') pairs = pairs.filter((p) => p.riskLevel === riskFilter);
    if (search) {
      const q = search.toLowerCase();
      pairs = pairs.filter(
        (p) =>
          p.ayahA.display.includes(search) ||
          p.ayahB.display.includes(search) ||
          p.ayahA.display.includes(q) ||
          p.ayahB.display.includes(q) ||
          (p.reviewStatus !== 'needs_review' && (
            p.confusionReason.en.toLowerCase().includes(q) ||
            p.confusionReason.ar.includes(search) ||
            p.keyDifference.en.toLowerCase().includes(q) ||
            p.keyDifference.ar.includes(search))),
      );
    }
    const riskOrder = { high: 0, medium: 1, low: 2 };
    pairs.sort((a, b) => riskOrder[a.riskLevel] - riskOrder[b.riskLevel]);
    return pairs;
  }, [riskFilter, search]);

  const filteredLinks = useMemo(() => {
    let links = [...MEMORIZATION_LINKS];
    if (search) {
      const q = search.toLowerCase();
      links = links.filter(
        (l) =>
          l.sourceAyah.display.includes(search) ||
          l.targetAyah.display.includes(search) ||
          l.similarityReason.en.toLowerCase().includes(q) ||
          l.similarityReason.ar.includes(search),
      );
    }
    return links;
  }, [search]);

  const filteredPhrases = useMemo(() => {
    let phrases = [...REPEATED_PHRASES];
    if (search) {
      const q = search.toLowerCase();
      phrases = phrases.filter(
        (p) =>
          p.phraseArabic.includes(search) ||
          (p.transliteration ?? '').toLowerCase().includes(q) ||
          p.meaningEn.toLowerCase().includes(q) ||
          p.meaningAr.includes(search),
      );
    }
    return phrases;
  }, [search]);

  const filteredStories = useMemo(() => {
    let stories = [...STORY_RECURRENCES];
    if (search) {
      const q = search.toLowerCase();
      stories = stories.filter(
        (r) =>
          r.storyId.includes(q) ||
          r.titleEn.toLowerCase().includes(q) ||
          r.titleAr.includes(search),
      );
    }
    return stories;
  }, [search]);

  return (
    <div className={clsx('min-h-screen bg-gray-50', isAr ? 'font-arabic' : '')}>
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
              <RefreshCw size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {isAr ? 'مساعد الحفظ' : 'Memorization Helper'}
              </h1>
              <p className="text-xs text-gray-500">
                {isAr ? 'روابط الحفظ · مواضع الالتباس · العبارات المتكررة' : 'Links · Confusion Pairs · Repeated Phrases'}
              </p>
            </div>
          </div>

          {/* Tasmee practice banner */}
          <Link
            to="/tasmee"
            className="flex items-center justify-between gap-3 mb-3 px-4 py-3 bg-primary-50 border border-primary-200 rounded-xl hover:bg-primary-100 transition-colors"
            dir={isAr ? 'rtl' : 'ltr'}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Mic size={15} className="text-white" />
              </div>
              <div>
                <p className={clsx('text-sm font-semibold text-primary-800', isAr && 'font-arabic')}>
                  {isAr ? 'التسميع — تدرّب بصوتك' : 'Tasmeeʿ — Practice with your voice'}
                </p>
                <p className={clsx('text-xs text-primary-600', isAr && 'font-arabic')}>
                  {isAr ? 'تلاوة مع التصحيح الفوري وكشف الأخطاء' : 'Recite with real-time feedback and mistake detection'}
                </p>
              </div>
            </div>
            <ArrowRight size={16} className={clsx('text-primary-500 flex-shrink-0', isAr && 'rotate-180')} />
          </Link>

          {/* Search */}
          <div className="relative mb-3">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={isAr ? 'ابحث عن آية أو موضوع...' : 'Search ayah or topic...'}
              className="w-full pl-9 pr-4 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              dir={isAr ? 'rtl' : 'ltr'}
            />
          </div>

          {/* Tabs */}
          <div className="flex gap-1 overflow-x-auto">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg font-medium whitespace-nowrap transition-colors',
                    activeTab === tab.id
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100',
                  )}
                >
                  <Icon size={12} />
                  {isAr ? tab.labelAr : tab.labelEn}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Review banner */}
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-sm text-amber-800">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
          <div dir={isAr ? 'rtl' : 'ltr'}>
            <strong>{isAr ? 'تنبيه: ' : 'Note: '}</strong>
            {isAr
              ? 'جميع بيانات ذكاء الحفظ مولّدة تلقائياً وقيد المراجعة العلمية. لا ينبغي استخدامها دون مراجعة متخصص.'
              : 'All memorization intelligence data is auto-generated and pending scholarly review. Do not use without specialist verification.'}
          </div>
        </div>

        {/* Confusion Pairs Tab */}
        {activeTab === 'confusion' && (
          <div>
            {/* Risk filter */}
            <div className="flex gap-2 mb-4">
              {(['all', 'high', 'medium', 'low'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRiskFilter(r)}
                  className={clsx(
                    'text-xs px-3 py-1.5 rounded-full border font-medium transition-colors',
                    riskFilter === r
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300',
                  )}
                >
                  {r === 'all' ? (isAr ? 'الكل' : 'All') : (isAr ? RISK_LABELS[r].ar : RISK_LABELS[r].en)}
                </button>
              ))}
            </div>

            <p className="text-sm text-gray-500 mb-4">
              {isAr
                ? `${filteredConfusionPairs.length} موضع التباس`
                : `${filteredConfusionPairs.length} confusion ${filteredConfusionPairs.length === 1 ? 'pair' : 'pairs'}`}
            </p>

            {filteredConfusionPairs.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <AlertTriangle size={32} className="mx-auto mb-2 opacity-30" />
                <p>{isAr ? 'لا توجد نتائج' : 'No results found'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredConfusionPairs.map((pair) => (
                  pair.reviewStatus === 'needs_review'
                    ? <UnreviewedPairCard key={pair.id} pair={pair} language={language} />
                    : <ConfusionPairCard key={pair.id} pair={pair} currentSurah={pair.ayahA.surah} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Similar Ayat Tab */}
        {activeTab === 'similar' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              {isAr
                ? `${filteredLinks.length} رابط مشابهة`
                : `${filteredLinks.length} similarity ${filteredLinks.length === 1 ? 'link' : 'links'}`}
            </p>

            {filteredLinks.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Layers size={32} className="mx-auto mb-2 opacity-30" />
                <p>{isAr ? 'لا توجد نتائج' : 'No results found'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredLinks.map((link) => (
                  <SimilarAyatCard key={link.id} link={link} currentSurah={link.sourceSurah} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Repeated Phrases Tab */}
        {activeTab === 'phrases' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              {isAr
                ? `${filteredPhrases.length} عبارة متكررة`
                : `${filteredPhrases.length} repeated ${filteredPhrases.length === 1 ? 'phrase' : 'phrases'}`}
            </p>

            {filteredPhrases.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <RefreshCw size={32} className="mx-auto mb-2 opacity-30" />
                <p>{isAr ? 'لا توجد نتائج' : 'No results found'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredPhrases.map((phrase) => (
                  <RepeatedPhraseCard key={phrase.id} phrase={phrase} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Story Recurrences Tab */}
        {activeTab === 'stories' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              {isAr
                ? `${filteredStories.length} قصة`
                : `${filteredStories.length} ${filteredStories.length === 1 ? 'story' : 'stories'}`}
            </p>

            {filteredStories.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <BookOpen size={32} className="mx-auto mb-2 opacity-30" />
                <p>{isAr ? 'لا توجد نتائج' : 'No results found'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredStories.map((story) => (
                  <StoryRecurrenceCard key={story.storyId} recurrence={story} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
