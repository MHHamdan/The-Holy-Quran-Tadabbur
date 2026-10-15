/**
 * VerseOfDayCard — Homepage "Verse of the Day" widget.
 *
 * Design: deterministic (day-of-year % curated pool), so the same user sees
 * the same verse all day without needing an account.
 *
 * Content policy: the pool holds references only. The Arabic is the canonical
 * text_uthmani from the API, followed by the Tanzil attribution. In English the
 * QuranEnc Saheeh International translation is fetched with the verse and
 * credited with its edition and version; in Arabic no second line is shown
 * (the pool used to repeat a hand-typed, partly different copy of the verse
 * there as a "translation").
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, ExternalLink, RefreshCw, Volume2, Share2, Bookmark, BookmarkCheck } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { useBookmarksStore } from '../../stores/bookmarksStore';
import { quranApi, type Verse } from '../../lib/api';
import { QuranTextAttribution } from '../quran/QuranTextAttribution';
import { useTranslationEditions } from '../quran/VerseTranslations';

// ---------------------------------------------------------------------------
// Curated pool: references only (surah, ayah)
// ---------------------------------------------------------------------------
type VerseRef = readonly [surah: number, ayah: number];

const POOL: readonly VerseRef[] = [
  [1, 1], [2, 152], [2, 255], [2, 286], [3, 139], [3, 173], [3, 185], [4, 36], [6, 17], [7, 23],
  [9, 51], [10, 62], [11, 6], [13, 28], [14, 7], [16, 97], [17, 23], [18, 10], [20, 46], [20, 114],
  [21, 87], [23, 1], [24, 35], [25, 63], [27, 40], [28, 24], [29, 45], [29, 69], [31, 34], [33, 21],
  [33, 56], [36, 82], [39, 10], [39, 53], [40, 60], [41, 30], [42, 10], [49, 10], [49, 13], [51, 56],
  [55, 13], [57, 21], [58, 11], [59, 18], [59, 22], [65, 3], [67, 2], [68, 4], [76, 9], [89, 27],
  [93, 5], [94, 5], [94, 6], [108, 1], [112, 1],
];

/** Left-to-right isolate, so "2:255" keeps its order inside Arabic text. */
const isolateLtr = (s: string) => `⁦${s}⁩`;

const ENGLISH_EDITION = 'english_saheeh';

function getDayIndex(): number {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = +now - +start;
  const oneDay = 1000 * 60 * 60 * 24;
  const dayOfYear = Math.floor(diff / oneDay);
  return dayOfYear % POOL.length;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  compact?: boolean;
}

export function VerseOfDayCard({ compact = false }: Props) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [idx, setIdx] = useState(getDayIndex);
  const [verse, setVerse] = useState<Verse | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef<string | null>(null);
  const { addBookmark, removeBookmark, isBookmarked } = useBookmarksStore();
  const { data: editions } = useTranslationEditions();

  const ref = POOL[idx];
  const refLabel = `${ref[0]}:${ref[1]}`;
  const suraName = verse ? (isRtl ? verse.sura_name_ar : verse.sura_name_en) : '';

  // Bookmark by the verse's real id (it used to be surah*1000+ayah, which
  // marked a different verse: 2:255 -> id 2255 = 19:5).
  const bookmarked = verse ? isBookmarked(verse.id) : false;

  const toggleBookmark = useCallback(() => {
    if (!verse) return;
    if (bookmarked) {
      removeBookmark(verse.id);
    } else {
      addBookmark({
        id: verse.id,
        sura_no: verse.sura_no,
        sura_name_ar: verse.sura_name_ar,
        sura_name_en: verse.sura_name_en,
        aya_no: verse.aya_no,
        text_uthmani: verse.text_uthmani,
      });
    }
  }, [bookmarked, verse, addBookmark, removeBookmark]);

  const shareVerse = useCallback(async () => {
    if (!verse) return;
    const verseRef = `${isRtl ? verse.sura_name_ar : verse.sura_name_en} (${isolateLtr(refLabel)})`;
    const text = `${verse.text_uthmani}\n— ${verseRef}\n${isRtl ? 'نص القرآن: مشروع تنزيل tanzil.net' : "Qur'an text: Tanzil Project, tanzil.net"}`;
    if (navigator.share) {
      try { await navigator.share({ title: verseRef, text }); } catch { /* cancelled */ }
    } else {
      navigator.clipboard.writeText(text).catch(console.error);
    }
  }, [verse, isRtl, refLabel]);

  useEffect(() => {
    const key = `${idx}:${language}`;
    if (fetchedRef.current === key) return;
    fetchedRef.current = key;
    setLoading(true);
    setVerse(null);
    quranApi
      .getVerse(ref[0], ref[1], language === 'en' ? [ENGLISH_EDITION] : [])
      .then(res => setVerse(res.data))
      .catch(() => setVerse(null))
      .finally(() => setLoading(false));
  }, [idx, ref, language]);

  const rotate = () => setIdx(i => (i + 1) % POOL.length);

  const translation = !isRtl ? verse?.translations?.find(t => t.translator === ENGLISH_EDITION) : undefined;
  const edition = editions?.find(e => e.key === ENGLISH_EDITION);
  const editionVersion = translation?.edition_version ?? edition?.version;

  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-2xl border border-emerald-200',
        'bg-gradient-to-br from-emerald-50 via-teal-50 to-sky-50',
        compact ? 'p-4' : 'p-5 md:p-6',
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Decorative orb */}
      <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-emerald-100/60 blur-2xl pointer-events-none" />

      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-3', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <p className={clsx('text-xs font-semibold text-emerald-700 uppercase tracking-wide', isRtl && 'font-arabic')}>
              {isRtl ? 'آية اليوم' : 'Verse of the Day'}
            </p>
            <p className={clsx('text-[10px] text-gray-400', isRtl && 'font-arabic')}>
              {suraName && <>{suraName} · </>}
              <bdi dir="ltr">{refLabel}</bdi>
            </p>
          </div>
        </div>
        <button
          onClick={rotate}
          className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-white/60 transition-colors"
          title={isRtl ? 'آية أخرى' : 'Another verse'}
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Arabic text */}
      <div className="min-h-[3rem] mb-3">
        {loading ? (
          <div className="h-8 bg-emerald-100 rounded-lg animate-pulse w-3/4 ms-auto" />
        ) : verse ? (
          <p
            dir="rtl"
            lang="ar"
            className={clsx(
              'font-arabic text-right leading-loose text-gray-900',
              compact ? 'text-lg' : 'text-xl md:text-2xl',
            )}
          >
            {verse.text_uthmani}
          </p>
        ) : null}
        {verse && <QuranTextAttribution language={language} className="mt-1" />}
      </div>

      {/* Divider */}
      <div className="border-t border-emerald-100 mb-3" />

      {/* Translation of the meanings (English UI only), credited to its edition */}
      {translation && (
        <>
          <p dir="ltr" lang="en" className="text-sm text-gray-600 leading-relaxed mb-1 text-left">
            {translation.text}
          </p>
          <p dir="ltr" className="text-[11px] text-emerald-600 font-medium mb-1 text-left">
            — {verse?.sura_name_en} <bdi>{refLabel}</bdi>
          </p>
          <p dir="ltr" className="text-[10px] text-gray-400 mb-4 text-left">
            Translation of the meanings: {edition?.title ?? 'Saheeh International'}
            {editionVersion ? ` v${editionVersion}` : ''},{' '}
            <a href="https://quranenc.com" target="_blank" rel="noopener noreferrer" className="underline">QuranEnc.com</a>
          </p>
        </>
      )}
      {isRtl && verse && (
        <p className="text-[11px] text-emerald-600 font-medium mb-4 font-arabic text-right">
          — {verse.sura_name_ar} <bdi dir="ltr">{refLabel}</bdi>
        </p>
      )}

      {/* CTA */}
      <div className={clsx('flex items-center gap-2 flex-wrap', isRtl && 'flex-row-reverse')}>
        <Link
          to={`/quran/${ref[0]}`}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-emerald-600 text-white hover:bg-emerald-700 transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <ExternalLink className="w-3 h-3" />
          {isRtl ? 'اقرأ في المصحف' : 'Read in Mushaf'}
        </Link>
        <Link
          to={`/ask`}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-white/70 text-emerald-700 border border-emerald-200 hover:bg-white transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <Volume2 className="w-3 h-3" />
          {isRtl ? 'تدبر هذه الآية' : 'Reflect on this verse'}
        </Link>
        {verse && (
          <>
            <button
              onClick={toggleBookmark}
              className={clsx(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                bookmarked
                  ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                  : 'bg-white/70 text-gray-600 border border-gray-200 hover:bg-white',
                isRtl && 'font-arabic',
              )}
              title={isRtl ? (bookmarked ? 'إزالة الإشارة' : 'حفظ الآية') : (bookmarked ? 'Remove bookmark' : 'Bookmark')}
            >
              {bookmarked ? <BookmarkCheck className="w-3 h-3" /> : <Bookmark className="w-3 h-3" />}
              {isRtl ? (bookmarked ? 'محفوظة' : 'حفظ') : (bookmarked ? 'Saved' : 'Save')}
            </button>
            <button
              onClick={shareVerse}
              className={clsx(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
                'bg-white/70 text-gray-600 border border-gray-200 hover:bg-white transition-colors',
                isRtl && 'font-arabic',
              )}
              title={isRtl ? 'مشاركة' : 'Share'}
            >
              <Share2 className="w-3 h-3" />
              {isRtl ? 'مشاركة' : 'Share'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
