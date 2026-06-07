/**
 * Surah Atlas Page
 *
 * A comprehensive grid view of all 114 surahs with summaries, structure,
 * stories, themes, and memorization data.
 *
 * Safety: All entries are marked needs_review until scholarly validation.
 * Review warnings are always shown.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, Map, BookOpen, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';
import { SurahAtlasCard } from '../components/atlas/SurahAtlasCard';
import type { SurahAtlasFilter, SurahAtlasSortKey } from '../types/surahAtlas';

// ---------------------------------------------------------------------------
// Filter configuration
// ---------------------------------------------------------------------------

const REVELATION_FILTERS = [
  { id: 'all', labelEn: 'All', labelAr: 'الكل' },
  { id: 'makki', labelEn: 'Makki', labelAr: 'مكية' },
  { id: 'madani', labelEn: 'Madani', labelAr: 'مدنية' },
  { id: 'mixed', labelEn: 'Mixed', labelAr: 'مختلطة' },
];

const SORT_OPTIONS: { id: SurahAtlasSortKey; labelEn: string; labelAr: string }[] = [
  { id: 'quranOrder', labelEn: 'Quran Order', labelAr: 'الترتيب القرآني' },
  { id: 'ayahCount', labelEn: 'Ayah Count', labelAr: 'عدد الآيات' },
  { id: 'storyCount', labelEn: 'Story Count', labelAr: 'عدد القصص' },
];

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function SurahAtlasPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  const [filter, setFilter] = useState<SurahAtlasFilter>({
    revelationType: 'all',
    sortBy: 'quranOrder',
    searchQuery: '',
  });
  const filtered = useMemo(() => {
    let data = [...SURAH_ATLAS_DATA];

    // Search
    if (filter.searchQuery) {
      const q = filter.searchQuery.toLowerCase();
      data = data.filter(
        (s) =>
          s.nameTransliteration.toLowerCase().includes(q) ||
          s.nameEnglishMeaning.toLowerCase().includes(q) ||
          s.nameArabic.includes(filter.searchQuery ?? '') ||
          s.keyConcepts.some((c) => c.toLowerCase().includes(q)) ||
          (s.keyConceptsAr ?? []).some((c) => c.includes(filter.searchQuery ?? '')) ||
          s.prophetsMentioned.some((p) => p.toLowerCase().includes(q)) ||
          s.summary.short.ar.includes(filter.searchQuery ?? '') ||
          s.summary.short.en.toLowerCase().includes(q),
      );
    }

    // Revelation type filter
    if (filter.revelationType && filter.revelationType !== 'all') {
      data = data.filter((s) => s.revelationType === filter.revelationType);
    }

    // Sort
    if (filter.sortBy === 'ayahCount') {
      data.sort((a, b) => b.ayahCount - a.ayahCount);
    } else if (filter.sortBy === 'storyCount') {
      data.sort((a, b) => (b.storiesMentioned?.length ?? 0) - (a.storiesMentioned?.length ?? 0));
    } else {
      data.sort((a, b) => a.surahNumber - b.surahNumber);
    }

    return data;
  }, [filter]);

  return (
    <div className={clsx('min-h-screen bg-gray-50', isAr ? 'font-arabic' : '')}>
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
                <Map size={18} className="text-white" />
              </div>
              <div>
                <h1 className={clsx('text-xl font-bold text-gray-900', isAr && 'text-right')}>
                  {isAr ? 'أطلس السور' : 'Surah Atlas'}
                </h1>
                <p className="text-xs text-gray-500">
                  {isAr ? '114 سورة · جميعها قيد المراجعة' : '114 Surahs · All Pending Scholarly Review'}
                </p>
              </div>
            </div>

            <Link
              to="/tools/surah-memory-atlas"
              className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1"
            >
              {isAr ? 'دليل الحفظ' : 'Memory Guide'}
              <BookOpen size={12} />
            </Link>
          </div>

          {/* Search */}
          <div className="relative mb-3">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder={isAr ? 'ابحث عن سورة، نبي، أو موضوع...' : 'Search surah, prophet, or topic...'}
              className="w-full pl-9 pr-4 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-400 bg-white"
              value={filter.searchQuery ?? ''}
              onChange={(e) => setFilter((f) => ({ ...f, searchQuery: e.target.value }))}
              dir={isAr ? 'rtl' : 'ltr'}
            />
          </div>

          {/* Filter row */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Revelation type chips */}
            {REVELATION_FILTERS.map((rf) => (
              <button
                key={rf.id}
                onClick={() => setFilter((f) => ({ ...f, revelationType: rf.id as SurahAtlasFilter['revelationType'] }))}
                className={clsx(
                  'text-xs px-3 py-1.5 rounded-full border font-medium transition-colors',
                  filter.revelationType === rf.id
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-primary-300',
                )}
              >
                {isAr ? rf.labelAr : rf.labelEn}
              </button>
            ))}

            <div className="flex-1" />

            {/* Sort */}
            <select
              className="text-xs border rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-400"
              value={filter.sortBy ?? 'quranOrder'}
              onChange={(e) => setFilter((f) => ({ ...f, sortBy: e.target.value as SurahAtlasSortKey }))}
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.id} value={o.id}>
                  {isAr ? o.labelAr : o.labelEn}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Review banner */}
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 text-sm text-amber-800">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
          <div dir={isAr ? 'rtl' : 'ltr'}>
            <strong>{isAr ? 'تنبيه: ' : 'Note: '}</strong>
            {isAr
              ? 'جميع بيانات هذا الأطلس قيد المراجعة العلمية. الملخصات نصوص تربوية مؤقتة ولا ينبغي اعتبارها تفسيراً موثوقاً.'
              : 'All atlas data is pending scholarly review. Summaries are pedagogical placeholders and should not be taken as authoritative tafsir.'}
          </div>
        </div>

        {/* Results count */}
        <p className="text-sm text-gray-500 mb-4">
          {isAr
            ? `${filtered.length} سورة`
            : `${filtered.length} ${filtered.length === 1 ? 'surah' : 'surahs'}`}
        </p>

        {/* Grid */}
        {filtered.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Map size={40} className="mx-auto mb-3 opacity-30" />
            <p>{isAr ? 'لا توجد نتائج' : 'No results found'}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((entry) => (
              <SurahAtlasCard key={entry.surahNumber} entry={entry} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
