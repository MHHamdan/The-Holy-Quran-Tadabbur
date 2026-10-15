import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { BookOpenCheck, FileX, Home, Search } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';

/** Catch-all route: unknown paths and stale deep links. */
export function NotFoundPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const btn = clsx(
    'inline-flex min-h-11 items-center gap-2 rounded-lg px-4 text-sm font-medium transition-colors',
    isAr && 'font-arabic',
  );
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center px-4 py-12 text-center" dir={isAr ? 'rtl' : 'ltr'}>
      <FileX className="mb-4 h-12 w-12 text-gray-500" aria-hidden="true" />
      <h1 className={clsx('text-2xl font-bold text-gray-900', isAr && 'font-arabic')}>{t('not_found_title', language)}</h1>
      <p className={clsx('mt-2 text-gray-600', isAr && 'font-arabic')}>{t('not_found_body', language)}</p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link to="/" className={clsx(btn, 'bg-primary-600 text-white hover:bg-primary-700')}>
          <Home className="h-4 w-4" aria-hidden="true" />
          {t('not_found_home', language)}
        </Link>
        <Link to="/mushaf" className={clsx(btn, 'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50')}>
          <BookOpenCheck className="h-4 w-4" aria-hidden="true" />
          {t('not_found_read', language)}
        </Link>
        <Link to="/search" className={clsx(btn, 'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50')}>
          <Search className="h-4 w-4" aria-hidden="true" />
          {t('not_found_search', language)}
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
