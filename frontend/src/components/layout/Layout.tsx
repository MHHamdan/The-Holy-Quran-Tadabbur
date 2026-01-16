import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Book, MessageCircle, Home, Globe, BookOpen, Wrench, Map, Network, Search, Link2, Compass, BookOpenCheck } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import { t } from '../../i18n/translations';
import clsx from 'clsx';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { language, toggleLanguage, direction } = useLanguageStore();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'nav_home', icon: Home },
    { path: '/mushaf', label: 'nav_mushaf', icon: BookOpenCheck },
    { path: '/stories', label: 'nav_stories', icon: Book },
    { path: '/story-atlas', label: 'nav_atlas', icon: Map },
    { path: '/concepts', label: 'nav_concepts', icon: Network },
    { path: '/themes', label: 'nav_themes', icon: Compass },
    { path: '/similarity', label: 'nav_similarity', icon: Link2 },
    { path: '/search', label: 'nav_search', icon: Search },
    { path: '/ask', label: 'nav_ask', icon: MessageCircle },
    { path: '/sources', label: 'nav_sources', icon: BookOpen },
    { path: '/tools', label: 'nav_tools', icon: Wrench },
  ];

  return (
    <div className="min-h-screen bg-gray-50" dir={direction}>
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Book className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {t('app_title', language)}
                </h1>
              </div>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{t(item.label, language)}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 hover:border-primary-500 transition-colors"
            >
              <Globe className="w-5 h-5 text-gray-600" />
              <span className="font-medium text-sm">
                {language === 'en' ? 'العربية' : 'English'}
              </span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-gray-100">
          <div className="flex justify-around py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={clsx(
                    'flex flex-col items-center gap-1 px-4 py-2',
                    isActive ? 'text-primary-600' : 'text-gray-500'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-xs">{t(item.label, language)}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            {t('footer_disclaimer', language)}
          </p>
        </div>
      </footer>
    </div>
  );
}
