/**
 * Attribution line under a displayed tafsir excerpt: title, author and the
 * source id it was retrieved from (CLAUDE.md: every displayed tafsir entry
 * shows source_id, author and title). Each name is wrapped with its own
 * direction so Arabic and English never share a single `dir`.
 */
import clsx from 'clsx';

export interface TafsirEditionMeta {
  id: string;
  name_ar?: string;
  name_en?: string;
  author_ar?: string;
  author_en?: string;
  language?: string;
}

const PROVIDERS: Record<string, string> = {
  quran_com: 'Quran.com',
  quran_tafseer: 'quran-tafseer.com',
};

export function TafsirSourceFooter({
  edition,
  provider,
  language,
  className,
}: {
  edition: TafsirEditionMeta;
  provider?: string;
  language: 'ar' | 'en';
  className?: string;
}) {
  const ar = language === 'ar';
  const title = (ar ? edition.name_ar : edition.name_en) || edition.name_ar || edition.name_en || edition.id;
  const author = (ar ? edition.author_ar : edition.author_en) || edition.author_ar || edition.author_en;
  const titleIsArabic = /[؀-ۿ]/.test(title);
  const authorIsArabic = !!author && /[؀-ۿ]/.test(author);
  const via = provider ? PROVIDERS[provider] ?? provider : null;

  return (
    <p
      className={clsx('mt-3 pt-2 border-t border-gray-200 text-xs text-gray-500', ar && 'font-arabic', className)}
      dir={ar ? 'rtl' : 'ltr'}
      lang={language}
      data-testid="tafsir-attribution"
    >
      <span dir={titleIsArabic ? 'rtl' : 'ltr'} lang={titleIsArabic ? 'ar' : 'en'} className="font-medium text-gray-600">
        {title}
      </span>
      {author && (
        <>
          {' — '}
          <span dir={authorIsArabic ? 'rtl' : 'ltr'} lang={authorIsArabic ? 'ar' : 'en'}>{author}</span>
        </>
      )}
      {' · '}
      {ar ? 'المصدر: ' : 'source: '}
      <span dir="ltr" lang="en"><code>{edition.id}</code>{via ? ` (via ${via})` : ''}</span>
    </p>
  );
}

export default TafsirSourceFooter;
