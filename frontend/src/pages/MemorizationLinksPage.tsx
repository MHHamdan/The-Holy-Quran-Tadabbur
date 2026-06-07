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
import { RefreshCw, AlertTriangle, Search, BookOpen, Layers, type LucideIcon } from 'lucide-react';
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

type Tab = 'confusion' | 'similar' | 'phrases' | 'stories';

const TABS: { id: Tab; labelEn: string; labelAr: string; icon: LucideIcon }[] = [
  { id: 'confusion', labelEn: 'Confusion Pairs', labelAr: 'أزواج الخلط', icon: AlertTriangle },
  { id: 'similar', labelEn: 'Similar Ayat', labelAr: 'آيات مشابهة', icon: Layers },
  { id: 'phrases', labelEn: 'Repeated Phrases', labelAr: 'العبارات المتكررة', icon: RefreshCw },
  { id: 'stories', labelEn: 'Story Recurrences', labelAr: 'تكرار القصص', icon: BookOpen },
];

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
          p.confusionReason.en.toLowerCase().includes(q) ||
          p.confusionReason.ar.includes(search) ||
          p.keyDifference.en.toLowerCase().includes(q) ||
          p.keyDifference.ar.includes(search),
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
                {isAr ? 'ذكاء الحفظ' : 'Memorization Intelligence'}
              </h1>
              <p className="text-xs text-gray-500">
                {isAr ? 'روابط الحفظ · أزواج الخلط · العبارات المتكررة' : 'Links · Confusion Pairs · Repeated Phrases'}
              </p>
            </div>
          </div>

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
                  {r === 'all' ? (isAr ? 'الكل' : 'All') : r}
                </button>
              ))}
            </div>

            <p className="text-sm text-gray-500 mb-4">
              {isAr
                ? `${filteredConfusionPairs.length} زوج من الخلط`
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
                  <ConfusionPairCard key={pair.id} pair={pair} currentSurah={pair.ayahA.surah} />
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
