/**
 * Ayah Memorization Flashcards
 *
 * Shows the verse number and surah context; user tries to recall the ayah text,
 * then reveals it. Uses localStorage to persist "mastered" ayah IDs so progress
 * survives sessions.
 *
 * Safety: Actual Quran text is fetched from the existing QuranPage/API flow via
 * the verse reference — we DO NOT embed text strings here. Instead, we display
 * a deep-link to the Mushaf for text display, and show transliteration hints
 * only from the already-indexed vocabulary data where available.
 *
 * Flashcard data: surah-level metadata from SURAH_ATLAS_DATA (ayahCount).
 * No Quran text is stored or generated in this file.
 */

import { useState, useCallback, useMemo } from 'react';
import { Layers, ChevronLeft, ChevronRight, Eye, CheckCircle, RotateCcw, Link as LinkIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_NAMES } from '../data/surahNames';
import { SURAH_ATLAS_DATA } from '../data/surahAtlas';

// ---------------------------------------------------------------------------
// Persistence helpers
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'tadabbur_flashcards_v1';

interface FlashcardStore {
  mastered: string[];   // "surah:ayah" strings
}

function loadStore(): FlashcardStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as FlashcardStore;
  } catch {}
  return { mastered: [] };
}

function saveStore(store: FlashcardStore) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(store)); } catch {}
}

function makeKey(surah: number, ayah: number) { return `${surah}:${ayah}`; }

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getAyahCount(surahNum: number): number {
  return SURAH_ATLAS_DATA.find(s => s.surahNumber === surahNum)?.ayahCount ?? 7;
}

// ---------------------------------------------------------------------------
// AyahCard component
// ---------------------------------------------------------------------------

function AyahCard({
  surah,
  ayah,
  totalAyahs,
  isMastered,
  isRtl,
  onMaster,
  onUnmaster,
}: {
  surah: number;
  ayah: number;
  totalAyahs: number;
  isMastered: boolean;
  isRtl: boolean;
  onMaster: () => void;
  onUnmaster: () => void;
}) {
  const [revealed, setRevealed] = useState(false);
  const surahName = SURAH_NAMES[surah - 1];

  // Reset reveal state when ayah changes
  const cardKey = `${surah}-${ayah}`;

  return (
    <div key={cardKey} className="space-y-4">
      {/* Card front */}
      <div className={clsx(
        'rounded-2xl border p-6 text-center min-h-[200px] flex flex-col items-center justify-center gap-3',
        isMastered ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-gray-100'
      )}>
        {/* Surah + ayah reference */}
        <div>
          <p className={clsx('text-3xl font-bold text-gray-800', isRtl && 'font-arabic')}>
            {isRtl ? surahName?.ar : surahName?.en} — {isRtl ? 'آية' : 'Ayah'} {ayah}
          </p>
          <p className="text-sm text-gray-400 mt-1 font-arabic" dir="rtl">
            سورة {surahName?.ar} ({surah}:{ayah})
          </p>
        </div>

        {!revealed ? (
          <div className="flex flex-col items-center gap-2">
            <p className={clsx('text-sm text-gray-400 italic', isRtl && 'font-arabic')}>
              {isRtl ? 'تذكّر الآية من الذاكرة…' : 'Recall the verse from memory…'}
            </p>
            <button
              onClick={() => setRevealed(true)}
              className={clsx(
                'flex items-center gap-2 px-5 py-2 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 transition-colors',
                isRtl && 'flex-row-reverse'
              )}
            >
              <Eye className="w-4 h-4" />
              {isRtl ? 'أظهر الآية' : 'Reveal'}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            {/* Link to Mushaf for actual text */}
            <Link
              to={`/quran/${surah}?ayah=${ayah}`}
              className={clsx(
                'inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors',
                isRtl && 'flex-row-reverse font-arabic'
              )}
            >
              <LinkIcon className="w-3.5 h-3.5" />
              {isRtl ? `افتح ${surahName?.ar} ${surah}:${ayah} في المصحف` : `Open ${surahName?.en} ${surah}:${ayah} in Mushaf`}
            </Link>

            {/* Progress bar hint */}
            <p className={clsx('text-xs text-gray-400', isRtl && 'font-arabic')}>
              {isRtl
                ? `الآية ${ayah} من ${totalAyahs}`
                : `Verse ${ayah} of ${totalAyahs}`}
            </p>

            {/* Master / Not yet buttons */}
            <div className={clsx('flex gap-3', isRtl && 'flex-row-reverse')}>
              {!isMastered ? (
                <button
                  onClick={onMaster}
                  className={clsx(
                    'flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors',
                    isRtl && 'flex-row-reverse font-arabic'
                  )}
                >
                  <CheckCircle className="w-4 h-4" />
                  {isRtl ? 'حفظت' : 'I know it!'}
                </button>
              ) : (
                <button
                  onClick={onUnmaster}
                  className={clsx(
                    'flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-300 transition-colors',
                    isRtl && 'flex-row-reverse font-arabic'
                  )}
                >
                  <RotateCcw className="w-4 h-4" />
                  {isRtl ? 'أعد' : 'Re-study'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function FlashcardsPage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [selectedSurah, setSelectedSurah] = useState(1);
  const [currentAyah, setCurrentAyah] = useState(1);
  const [store, setStore] = useState<FlashcardStore>(loadStore);

  const totalAyahs = useMemo(() => getAyahCount(selectedSurah), [selectedSurah]);

  const masteredInSurah = useMemo(() => {
    let count = 0;
    for (let i = 1; i <= totalAyahs; i++) {
      if (store.mastered.includes(makeKey(selectedSurah, i))) count++;
    }
    return count;
  }, [store, selectedSurah, totalAyahs]);

  const updateStore = useCallback((newStore: FlashcardStore) => {
    setStore(newStore);
    saveStore(newStore);
  }, []);

  function masterCurrent() {
    const key = makeKey(selectedSurah, currentAyah);
    if (!store.mastered.includes(key)) {
      updateStore({ mastered: [...store.mastered, key] });
    }
  }

  function unmasterCurrent() {
    const key = makeKey(selectedSurah, currentAyah);
    updateStore({ mastered: store.mastered.filter(k => k !== key) });
  }

  function prev() {
    if (currentAyah > 1) setCurrentAyah(a => a - 1);
  }

  function next() {
    if (currentAyah < totalAyahs) setCurrentAyah(a => a + 1);
  }

  function changeSurah(n: number) {
    setSelectedSurah(n);
    setCurrentAyah(1);
  }

  const isMastered = store.mastered.includes(makeKey(selectedSurah, currentAyah));
  const pct = totalAyahs > 0 ? Math.round((masteredInSurah / totalAyahs) * 100) : 0;

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={clsx('flex items-center gap-3 mb-6', isRtl && 'flex-row-reverse')}>
        <Layers className="w-7 h-7 text-emerald-500" />
        <div>
          <h1 className={clsx('text-2xl font-bold text-gray-900', isRtl && 'font-arabic')}>
            {isRtl ? 'بطاقات الحفظ' : 'Memorization Flashcards'}
          </h1>
          <p className={clsx('text-xs text-gray-400 mt-0.5', isRtl && 'font-arabic')}>
            {isRtl
              ? 'مارس استرجاع الآيات من الذاكرة — تقدمك يُحفظ تلقائياً'
              : 'Practice active recall — progress saved locally'}
          </p>
        </div>
      </div>

      {/* Surah selector */}
      <div className="mb-4">
        <label className={clsx('block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'اختر السورة' : 'Select Surah'}
        </label>
        <div className="relative">
          <select
            value={selectedSurah}
            onChange={e => changeSurah(Number(e.target.value))}
            className={clsx(
              'w-full appearance-none rounded-xl border border-gray-200 bg-white px-4 py-3 pr-9 text-sm font-semibold text-gray-800 focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100',
              isRtl && 'font-arabic text-right pr-4 pl-9'
            )}
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            {SURAH_NAMES.map((sn, i) => (
              <option key={i + 1} value={i + 1}>
                {i + 1}. {isRtl ? sn.ar : sn.en}
              </option>
            ))}
          </select>
          <ChevronRight className={clsx('pointer-events-none absolute top-1/2 -translate-y-1/2 rotate-90 w-4 h-4 text-gray-400', isRtl ? 'left-3' : 'right-3')} />
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-5">
        <div className={clsx('flex justify-between text-xs text-gray-400 mb-1', isRtl && 'flex-row-reverse')}>
          <span className={isRtl ? 'font-arabic' : ''}>
            {isRtl ? `${masteredInSurah} من ${totalAyahs} آية محفوظة` : `${masteredInSurah} / ${totalAyahs} mastered`}
          </span>
          <span className="font-bold">{pct}%</span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-400 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Flashcard */}
      <AyahCard
        key={`${selectedSurah}-${currentAyah}`}
        surah={selectedSurah}
        ayah={currentAyah}
        totalAyahs={totalAyahs}
        isMastered={isMastered}
        isRtl={isRtl}
        onMaster={masterCurrent}
        onUnmaster={unmasterCurrent}
      />

      {/* Navigation */}
      <div className={clsx('flex items-center justify-between mt-4', isRtl && 'flex-row-reverse')}>
        <button
          onClick={prev}
          disabled={currentAyah <= 1}
          className={clsx(
            'flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors',
            currentAyah <= 1
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
          )}
        >
          <ChevronLeft className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          {isRtl ? 'السابق' : 'Prev'}
        </button>

        {/* Ayah dots (show up to 20) */}
        <div className="flex gap-1 flex-wrap justify-center max-w-[200px]">
          {Array.from({ length: Math.min(totalAyahs, 20) }, (_, i) => {
            const ayahNum = i + 1;
            const km = store.mastered.includes(makeKey(selectedSurah, ayahNum));
            return (
              <button
                key={ayahNum}
                onClick={() => setCurrentAyah(ayahNum)}
                title={`Ayah ${ayahNum}`}
                className={clsx(
                  'w-2.5 h-2.5 rounded-full transition-colors',
                  ayahNum === currentAyah
                    ? 'bg-violet-600 ring-2 ring-violet-200'
                    : km ? 'bg-emerald-400' : 'bg-gray-200 hover:bg-gray-300'
                )}
              />
            );
          })}
          {totalAyahs > 20 && (
            <span className="text-[10px] text-gray-400 self-center">+{totalAyahs - 20}</span>
          )}
        </div>

        <button
          onClick={next}
          disabled={currentAyah >= totalAyahs}
          className={clsx(
            'flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-colors',
            currentAyah >= totalAyahs
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
          )}
        >
          {isRtl ? 'التالي' : 'Next'}
          <ChevronRight className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
        </button>
      </div>

      {/* All-surahs summary */}
      <div className="mt-8 p-4 bg-gray-50 rounded-2xl border border-gray-100">
        <p className={clsx('text-xs font-bold text-gray-700 mb-2', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'التقدم الكلي' : 'Overall Progress'}
        </p>
        <p className={clsx('text-sm text-gray-500', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? `${store.mastered.length} آية محفوظة من القرآن الكريم`
            : `${store.mastered.length} ayahs marked mastered across the Quran`}
        </p>
        {store.mastered.length > 0 && (
          <button
            onClick={() => {
              if (confirm(isRtl ? 'إعادة تعيين كل التقدم؟' : 'Reset all progress?')) {
                updateStore({ mastered: [] });
              }
            }}
            className={clsx('mt-2 text-xs text-red-400 hover:text-red-600', isRtl && 'font-arabic')}
          >
            {isRtl ? 'إعادة تعيين الكل' : 'Reset all'}
          </button>
        )}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-6', isRtl && 'font-arabic')}>
        {isRtl
          ? 'لا يُخزَّن نص القرآن هنا — اضغط "افتح في المصحف" لعرض الآية'
          : 'Quran text is not stored here — tap "Open in Mushaf" to view the verse'}
      </p>
    </div>
  );
}
