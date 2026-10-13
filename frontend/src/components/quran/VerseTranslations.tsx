/**
 * Translations of the meanings under a verse.
 *
 * QuranEnc's republication terms require each translation to appear verbatim,
 * with its publisher, version and footnotes. So every block names its edition
 * and version, links to QuranEnc.com, and shows the footnotes on request. The
 * block is labelled as a translation of the meanings, never as Qur'an text.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { quranApi, type Translation, type TranslationEdition } from '../../lib/api';
import type { Language } from '../../i18n/translations';

/** Edition languages written right to left. */
const RTL_LANGUAGES = new Set(['ar', 'ur', 'fa', 'ps', 'ug', 'ku', 'sd', 'dv', 'he']);

export const isRtlLanguage = (code: string) => RTL_LANGUAGES.has(code);

/** Display names for edition languages (ISO 639 codes from QuranEnc). */
export const LANGUAGE_NAMES: Record<string, { en: string; ar: string }> = {
  en: { en: 'English', ar: 'الإنجليزية' },
  ur: { en: 'Urdu', ar: 'الأردية' },
  id: { en: 'Indonesian', ar: 'الإندونيسية' },
  tr: { en: 'Turkish', ar: 'التركية' },
  fr: { en: 'French', ar: 'الفرنسية' },
  es: { en: 'Spanish', ar: 'الإسبانية' },
  de: { en: 'German', ar: 'الألمانية' },
  fa: { en: 'Persian', ar: 'الفارسية' },
  hi: { en: 'Hindi', ar: 'الهندية' },
  zh: { en: 'Chinese', ar: 'الصينية' },
  pt: { en: 'Portuguese', ar: 'البرتغالية' },
  nl: { en: 'Dutch', ar: 'الهولندية' },
  bs: { en: 'Bosnian', ar: 'البوسنية' },
  sw: { en: 'Swahili', ar: 'السواحلية' },
  ha: { en: 'Hausa', ar: 'الهوسا' },
  so: { en: 'Somali', ar: 'الصومالية' },
  ta: { en: 'Tamil', ar: 'التاميلية' },
  ml: { en: 'Malayalam', ar: 'المليبارية' },
  uz: { en: 'Uzbek', ar: 'الأوزبكية' },
  ja: { en: 'Japanese', ar: 'اليابانية' },
};

export const languageName = (code: string, ui: Language) =>
  LANGUAGE_NAMES[code]?.[ui] ?? code;

/** Edition catalogue; it changes only when the seeder runs, so cache it for the session. */
export function useTranslationEditions() {
  return useQuery({
    queryKey: ['translation-editions'],
    queryFn: () => quranApi.getTranslationEditions().then((r) => r.data),
    staleTime: Infinity,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

interface VerseTranslationsProps {
  translations: Translation[];
  editions: TranslationEdition[] | undefined;
  language: Language;
}

export function VerseTranslations({ translations, editions, language }: VerseTranslationsProps) {
  if (translations.length === 0) return null;
  return (
    <div className="mx-5 mb-3 space-y-2">
      {translations.map((t) => (
        <TranslationBlock
          key={t.translator}
          translation={t}
          edition={editions?.find((e) => e.key === t.translator)}
          language={language}
        />
      ))}
    </div>
  );
}

function TranslationBlock({
  translation,
  edition,
  language,
}: {
  translation: Translation;
  edition: TranslationEdition | undefined;
  language: Language;
}) {
  const [showNotes, setShowNotes] = useState(false);
  const rtl = isRtlLanguage(translation.language);
  const uiAr = language === 'ar';
  const version = translation.edition_version ?? edition?.version;

  return (
    <div className="reader-translation px-4 py-3 bg-gray-50 rounded-xl border-s-4 border-primary-200">
      <p
        dir={rtl ? 'rtl' : 'ltr'}
        lang={translation.language}
        className={clsx('text-sm text-gray-700 leading-relaxed', rtl && 'font-arabic text-base')}
      >
        {translation.text}
      </p>

      {showNotes && translation.footnotes && (
        <p
          dir={rtl ? 'rtl' : 'ltr'}
          lang={translation.language}
          className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500 leading-relaxed whitespace-pre-line"
        >
          {translation.footnotes}
        </p>
      )}

      <div
        dir={uiAr ? 'rtl' : 'ltr'}
        className={clsx(
          'mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-gray-400',
          uiAr && 'font-arabic',
        )}
      >
        <span>{uiAr ? 'ترجمة معاني' : 'Translation of the meanings'}</span>
        <span dir="ltr">
          {edition?.title ?? translation.translator}
          {version ? ` · v${version}` : ''}
        </span>
        {edition && (
          <a
            href={edition.source_url}
            target="_blank"
            rel="noopener noreferrer"
            dir="ltr"
            className="underline hover:text-primary-600"
          >
            QuranEnc.com
          </a>
        )}
        {translation.footnotes && (
          <button
            type="button"
            onClick={() => setShowNotes((v) => !v)}
            aria-expanded={showNotes}
            className="underline hover:text-primary-600"
          >
            {showNotes
              ? uiAr ? 'إخفاء الحواشي' : 'Hide footnotes'
              : uiAr ? 'الحواشي' : 'Footnotes'}
          </button>
        )}
      </div>
    </div>
  );
}
