import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Book, MessageCircle, Home, Globe, BookOpen, Wrench, Network, Search, Link2, Compass, BookOpenCheck, Mic, Activity, Sparkles, Heart, Layers, RefreshCw, Users, Bookmark, Star, Flame, CalendarCheck, HandHeart } from 'lucide-react';
import { useBookmarksStore } from '../../stores/bookmarksStore';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';
import { FeedbackButton } from '../feedback/FeedbackButton';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { language, toggleLanguage, direction } = useLanguageStore();
  const { bookmarks } = useBookmarksStore();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'nav_home', icon: Home },
    { path: '/mushaf', label: 'nav_mushaf', icon: BookOpenCheck },
    { path: '/bookmarks', label: 'nav_bookmarks', icon: Bookmark },
    { path: '/challenge', label: 'nav_challenge', icon: Flame },
    { path: '/reading-plan', label: 'nav_reading_plan', icon: CalendarCheck },
    { path: '/duas', label: 'nav_duas', icon: HandHeart },
    { path: '/stories', label: 'nav_stories', icon: Book },
    { path: '/surah-atlas', label: 'nav_surah_atlas', icon: Layers },
    { path: '/prophets', label: 'nav_prophets', icon: Users },
    { path: '/memorization', label: 'nav_memorization', icon: RefreshCw },
    { path: '/concepts', label: 'nav_concepts', icon: Network },
    { path: '/themes', label: 'nav_themes', icon: Compass },
    { path: '/miracles', label: 'nav_miracles', icon: Sparkles },
    { path: '/asma-allah', label: 'nav_asma_allah', icon: Star },
    { path: '/similarity', label: 'nav_similarity', icon: Link2 },
    { path: '/search', label: 'nav_search', icon: Search },
    { path: '/ask', label: 'nav_ask', icon: MessageCircle },
    { path: '/tasmee', label: 'nav_tasmee', icon: Mic },
    { path: '/therapy', label: 'nav_therapy', icon: Heart },
    { path: '/sources', label: 'nav_sources', icon: BookOpen },
    { path: '/tools', label: 'nav_tools', icon: Wrench },
    { path: '/status', label: 'nav_status', icon: Activity },
  ];

  const LangToggle = () => (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white transition-colors flex-shrink-0"
      title={language === 'en' ? 'Switch to Arabic / تدبر القرآن' : 'Switch to English / Taddabur Al-Quran'}
    >
      <Globe className="w-4 h-4" />
      <span className={clsx('font-semibold text-sm whitespace-nowrap', language === 'en' ? 'font-arabic' : '')}>
        {language === 'en' ? 'تدبر القرآن' : 'Taddabur Al-Quran'}
      </span>
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50" dir={direction}>
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-3">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 flex-shrink-0">
              <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
                <Book className="w-5 h-5 text-white" />
              </div>
              <h1 className={clsx('text-lg font-bold text-gray-900 hidden sm:block', language === 'ar' && 'font-arabic')}>
                {t('app_title', language)}
              </h1>
            </Link>

            {/* Desktop Navigation — icons only on md, icons+text on xl */}
            <nav className="hidden md:flex items-center gap-0.5 flex-1 overflow-x-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={clsx(
                      'relative flex items-center gap-1.5 px-2.5 py-2 rounded-lg transition-colors flex-shrink-0',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    )}
                    title={t(item.label, language)}
                  >
                    <Icon className="w-4 h-4" />
                    <span className={clsx('font-medium text-sm hidden xl:inline', language === 'ar' && 'font-arabic')}>{t(item.label, language)}</span>
                    {item.path === '/bookmarks' && bookmarks.length > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-amber-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                        {bookmarks.length > 9 ? '9+' : bookmarks.length}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Language Toggle — always visible on desktop */}
            <div className="hidden md:flex flex-shrink-0">
              <LangToggle />
            </div>

            {/* Mobile: language toggle always in top-right */}
            <div className="md:hidden ms-auto">
              <LangToggle />
            </div>
          </div>
        </div>

        {/* Mobile Navigation row — icons + short labels */}
        <div className="md:hidden border-t border-gray-100 overflow-x-auto">
          <div className="flex py-1 px-2 gap-1 min-w-max">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg flex-shrink-0',
                    isActive ? 'text-primary-600 bg-primary-50' : 'text-gray-500'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span className={clsx('text-xs whitespace-nowrap', language === 'ar' && 'font-arabic')}>{t(item.label, language)}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">{children}</main>

      {/* Floating feedback button — available on every page */}
      <FeedbackButton />

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className={clsx('text-center text-sm text-gray-500', language === 'ar' && 'font-arabic')}>
            {t('footer_disclaimer', language)}
          </p>
        </div>
      </footer>
    </div>
  );
}
