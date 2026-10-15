/**
 * A verse (or short range) rendered from the canonical text served by the API.
 *
 * Use this wherever a page wants to show "the related verse" instead of typing
 * Qur'an text into code. The Arabic is text_uthmani from quran_verses (Tanzil,
 * verbatim); in the English UI the QuranEnc Saheeh International translation is
 * shown with its edition attribution; the Tanzil attribution follows.
 */
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { quranApi, type Verse } from '../../lib/api';
import type { Language } from '../../i18n/translations';
import { QuranTextAttribution } from './QuranTextAttribution';
import { VerseTranslations, useTranslationEditions } from './VerseTranslations';

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';
const toArabicDigits = (n: number) => String(n).replace(/\d/g, (d) => AR_DIGITS[Number(d)]);

/** "2:255" or "75:17-18" -> {sura, start, end}; null when malformed. */
export function parseAyahRef(ref: string): { sura: number; start: number; end: number } | null {
  const m = /^(\d{1,3}):(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?$/.exec(ref.trim());
  if (!m) return null;
  const sura = Number(m[1]);
  const start = Number(m[2]);
  const end = m[3] ? Number(m[3]) : start;
  if (sura < 1 || sura > 114 || start < 1 || end < start) return null;
  return { sura, start, end };
}

/** Fetch verses for a reference; translations only in the English UI. */
export function useLiveVerses(sura: number, start: number, end: number, language: Language, enabled = true) {
  const translations = language === 'en' ? ['english_saheeh'] : [];
  return useQuery({
    queryKey: ['live-verse', sura, start, end, translations.join(',')],
    queryFn: async (): Promise<Verse[]> => {
      if (end > start) {
        return (await quranApi.getVerseRange(sura, start, end, translations)).data;
      }
      return [(await quranApi.getVerse(sura, start, translations)).data];
    },
    staleTime: Infinity,
    gcTime: 24 * 60 * 60 * 1000,
    retry: 1,
    enabled: enabled && sura > 0,
  });
}

interface LiveVerseProps {
  /** "s:a" or "s:a-b". */
  reference: string;
  language: Language;
  /** Show the translation in the English UI (default true). */
  showTranslation?: boolean;
  /** Show the Tanzil attribution line (default true). */
  showAttribution?: boolean;
  className?: string;
}

export function LiveVerse({
  reference,
  language,
  showTranslation = true,
  showAttribution = true,
  className,
}: LiveVerseProps) {
  const parsed = parseAyahRef(reference);
  const { data, isLoading, isError } = useLiveVerses(
    parsed?.sura ?? 0, parsed?.start ?? 0, parsed?.end ?? 0, language,
  );
  const { data: editions } = useTranslationEditions();
  const ar = language === 'ar';

  if (!parsed) return null;
  if (isLoading) {
    return <div className={clsx('h-10 rounded-lg bg-gray-100 animate-pulse', className)} aria-busy="true" />;
  }
  if (isError || !data?.length) {
    return (
      <p className={clsx('text-xs text-gray-500', ar && 'font-arabic', className)} dir={ar ? 'rtl' : 'ltr'}>
        {ar ? 'تعذّر تحميل نص الآية. ' : 'Could not load the verse text. '}
        <bdi dir="ltr">{reference}</bdi>
      </p>
    );
  }

  return (
    <div className={clsx('space-y-2', className)}>
      <p dir="rtl" lang="ar" className="font-mushaf text-lg leading-loose text-gray-900">
        {data.map((v) => (
          <span key={v.id}>
            {v.text_uthmani}
            <span className="text-primary-600 text-base mx-1" aria-hidden="true">
              ﴿{toArabicDigits(v.aya_no)}﴾
            </span>{' '}
          </span>
        ))}
      </p>
      {showTranslation && language === 'en' && (
        <div className="-mx-5">
          {data.map((v) => (
            <VerseTranslations
              key={v.id}
              translations={v.translations ?? []}
              editions={editions}
              language={language}
            />
          ))}
        </div>
      )}
      {showAttribution && <QuranTextAttribution language={language} />}
    </div>
  );
}
