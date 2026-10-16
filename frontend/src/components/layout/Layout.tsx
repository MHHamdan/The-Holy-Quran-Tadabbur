import { ReactNode, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Book, Globe, Search } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import { FeedbackButton } from '../feedback/FeedbackButton';
import { activeTabFor, isReaderRoute, TABS } from './navConfig';
import { BottomNav, tabTarget } from './BottomNav';
import { MoreSheet } from './MoreSheet';

interface LayoutProps {
  children: ReactNode;
}

/** Routes that fill the viewport (chat composer): no global footer. */
const NO_FOOTER_ROUTES = ['/ask'];

export function Layout({ children }: LayoutProps) {
  const { language, toggleLanguage, direction } = useLanguageStore();
  const location = useLocation();
  const [moreOpen, setMoreOpen] = useState(false);
  const isAr = language === 'ar';
  const active = activeTabFor(location.pathname);
  // Same predicate FeedbackButton uses to decide whether the FAB renders.
  const fabShown = !isReaderRoute(location.pathname);

  // Close the More sheet whenever the route changes.
  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  const LangToggle = () => (
    <button
      type="button"
      onClick={toggleLanguage}
      // The accessible name starts with the visible label (WCAG 2.5.3).
      aria-label={`${language === 'en' ? 'العربية' : 'English'} — ${t('lang_switch_aria', language)}`}
      className="flex min-h-11 items-center gap-2 rounded-lg bg-primary-700 px-3 py-2.5 text-white transition-colors hover:bg-primary-800 flex-shrink-0"
    >
      <Globe className="h-4 w-4" aria-hidden="true" />
      <span
        lang={language === 'en' ? 'ar' : 'en'}
        className={clsx('whitespace-nowrap text-sm font-semibold', language === 'en' && 'font-arabic')}
      >
        {language === 'en' ? 'العربية' : 'English'}
      </span>
    </button>
  );

  const showFooter = !NO_FOOTER_ROUTES.includes(location.pathname);

  return (
    <div className="app-shell flex min-h-screen flex-col bg-gray-50 bottom-nav-clearance" dir={direction}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:start-2 focus:top-2 focus:z-[70] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-primary-800 focus:shadow-lg"
      >
        {t('skip_to_content', language)}
      </a>

      {/* Header: logo, primary sections (md+), search and language */}
      <header className="app-header app-header-inset sticky top-0 z-50 bg-white shadow-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-4 sm:px-6 md:h-16 lg:px-8">
          <Link
            to="/"
            aria-label={t('header_home', language)}
            className="tap flex flex-shrink-0 items-center gap-2 rounded-lg"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-700" aria-hidden="true">
              <Book className="h-5 w-5 text-white" />
            </span>
            <span className={clsx('hidden text-lg font-bold text-gray-900 lg:block', isAr && 'font-arabic')}>
              {t('app_title', language)}
            </span>
          </Link>

          <nav aria-label={t('nav_primary_label', language)} className="hidden flex-1 items-center justify-center gap-1 md:flex">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = active === tab.id;
              const target = tabTarget(tab.id, tab.to, active);
              const cls = clsx(
                'flex min-h-11 items-center gap-1.5 rounded-lg px-3 text-sm font-medium transition-colors',
                isActive || (tab.to === null && moreOpen) ? 'bg-primary-50 text-primary-800' : 'text-gray-700 hover:bg-gray-100',
                isAr && 'font-arabic',
              );
              return target ? (
                <Link key={tab.id} to={target} aria-current={isActive ? 'page' : undefined} className={cls}>
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {t(tab.labelKey, language)}
                </Link>
              ) : (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setMoreOpen(true)}
                  aria-haspopup="dialog"
                  aria-expanded={moreOpen}
                  aria-current={isActive ? 'page' : undefined}
                  className={cls}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {t(tab.labelKey, language)}
                </button>
              );
            })}
          </nav>

          <div className="ms-auto flex items-center gap-1 md:ms-0">
            <Link
              to="/search"
              aria-label={t('header_search', language)}
              aria-current={location.pathname === '/search' ? 'page' : undefined}
              className="tap rounded-lg text-gray-700 hover:bg-gray-100"
            >
              <Search className="h-5 w-5" aria-hidden="true" />
            </Link>
            <LangToggle />
          </div>
        </div>
      </header>

      {/* pb-20 clears the floating feedback button (44px, 1rem above the tab
          bar) so the last controls on a page, e.g. a duʿā's Share action, can be
          scrolled out from under it. Only where the FAB renders: reader routes
          (/ask, /mushaf, /quran, /tasmee) have no FAB, and /ask is a fixed-height
          chat that extra padding would make scroll. */}
      <main id="main" tabIndex={-1} className={clsx('flex-1 min-w-0 focus:outline-none', fabShown && 'pb-20')}>
        {children}
      </main>

      <FeedbackButton />

      {showFooter && (
        <footer className="mt-auto border-t border-gray-100 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <p className={clsx('text-center text-sm text-gray-600', isAr && 'font-arabic')}>
              {t('footer_disclaimer', language)}
            </p>
            <p className={clsx('mt-1 text-center text-xs text-gray-600', isAr && 'font-arabic')}>
              <a href="https://tanzil.net" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary-700">
                {t('footer_quran_text_credit', language)} (<bdi dir="ltr">tanzil.net, CC BY 3.0</bdi>)
              </a>
            </p>
            <nav
              aria-label={t('more_section_app', language)}
              className={clsx('mt-2 flex flex-wrap justify-center gap-x-4 text-sm text-gray-600', isAr && 'font-arabic')}
            >
              <Link to="/about" className="inline-flex min-h-11 items-center underline hover:text-primary-700">
                {t('footer_about', language)}
              </Link>
              <Link to="/privacy" className="inline-flex min-h-11 items-center underline hover:text-primary-700">
                {t('footer_privacy', language)}
              </Link>
              <Link to="/sources" className="inline-flex min-h-11 items-center underline hover:text-primary-700">
                {t('footer_sources', language)}
              </Link>
              <Link to="/licenses" className="inline-flex min-h-11 items-center underline hover:text-primary-700">
                {t('footer_licenses', language)}
              </Link>
            </nav>
          </div>
        </footer>
      )}

      <BottomNav language={language} active={active} moreOpen={moreOpen} onMore={() => setMoreOpen(true)} />
      <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} />
    </div>
  );
}
