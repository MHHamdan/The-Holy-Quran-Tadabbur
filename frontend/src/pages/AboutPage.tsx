import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { Info } from 'lucide-react';
import { useLanguageStore } from '../stores/languageStore';
import { t } from '../i18n/translations';
import { useFeedbackDialog } from '../components/feedback/feedbackStore';

/** "What is Tadabbur": what the app is, what its AI does and does not do. */
export function AboutPage() {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';
  const openFeedback = useFeedbackDialog((s) => s.openDialog);
  const h2 = clsx('mb-2 text-lg font-semibold text-gray-900', isAr && 'font-arabic');
  const p = clsx('leading-relaxed text-gray-700', isAr && 'font-arabic');
  const link = 'inline-block py-2 text-primary-700 underline hover:text-primary-800';

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6" dir={isAr ? 'rtl' : 'ltr'}>
      <div className="mb-6 flex items-center gap-3">
        <Info className="h-7 w-7 text-primary-700" aria-hidden="true" />
        <h1 className={clsx('text-2xl font-bold text-gray-900', isAr && 'font-arabic')}>{t('about_title', language)}</h1>
      </div>

      <section className="mb-7">
        <h2 className={h2}>{t('about_what_title', language)}</h2>
        <p className={p}>{t('about_what_body', language)}</p>
      </section>

      <section className="mb-7">
        <h2 className={h2}>{t('about_ai_title', language)}</h2>
        <p className={p}>{t('about_ai_body', language)}</p>
        <p className={clsx(p, 'mt-2')}>{t('about_ai_mistakes', language)}</p>
      </section>

      <section className="mb-7">
        <h2 className={h2}>{t('about_sources_title', language)}</h2>
        <ul className={clsx('flex flex-wrap gap-x-5', isAr && 'font-arabic')}>
          <li><Link to="/sources" className={link}>{t('about_link_sources', language)}</Link></li>
          <li><Link to="/privacy" className={link}>{t('about_link_privacy', language)}</Link></li>
          <li><Link to="/licenses" className={link}>{t('about_link_licenses', language)}</Link></li>
        </ul>
      </section>

      <section>
        <h2 className={h2}>{t('about_feedback_title', language)}</h2>
        <p className={p}>{t('about_feedback_body', language)}</p>
        <button
          type="button"
          onClick={openFeedback}
          className={clsx('mt-3 inline-flex min-h-11 items-center rounded-lg bg-amber-700 px-4 text-sm font-medium text-white hover:bg-amber-800', isAr && 'font-arabic')}
        >
          {t('more_report_issue', language)}
        </button>
      </section>
    </div>
  );
}

export default AboutPage;
