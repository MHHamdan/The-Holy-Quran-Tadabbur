import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { t, type Language } from '../../i18n/translations';
import { TABS, type TabId } from './navConfig';

/** Where a tab goes. The Read tab resumes reading; tapped again while already
 *  reading it opens the surah index instead. */
export function tabTarget(id: TabId, to: string | null, active: TabId | null): string | null {
  if (id === 'read' && active === 'read') return '/quran';
  return to;
}

/** Five-tab bar fixed to the bottom of the screen on phones (hidden from md up). */
export function BottomNav({
  language,
  active,
  moreOpen,
  onMore,
}: {
  language: Language;
  active: TabId | null;
  moreOpen: boolean;
  onMore: () => void;
}) {
  const isAr = language === 'ar';
  const itemClass = (isActive: boolean) =>
    clsx(
      'flex min-h-14 w-full flex-col items-center justify-center gap-0.5 px-1 text-xs font-medium transition-colors',
      isActive ? 'text-primary-700' : 'text-gray-600 hover:text-gray-900',
      isAr && 'font-arabic',
    );

  return (
    <nav
      aria-label={t('nav_primary_label', language)}
      className="fixed inset-x-0 bottom-0 z-50 border-t border-gray-200 bg-white safe-area-bottom md:hidden"
    >
      <ul className="mx-auto grid max-w-lg grid-cols-5">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = active === tab.id;
          const label = t(tab.labelKey, language);
          const target = tabTarget(tab.id, tab.to, active);
          return (
            <li key={tab.id}>
              {target ? (
                <Link to={target} aria-current={isActive ? 'page' : undefined} className={itemClass(isActive)}>
                  <Icon className={clsx('h-5 w-5', isActive && 'stroke-[2.5]')} aria-hidden="true" />
                  <span>{label}</span>
                </Link>
              ) : (
                <button
                  type="button"
                  onClick={onMore}
                  aria-haspopup="dialog"
                  aria-expanded={moreOpen}
                  aria-current={isActive ? 'page' : undefined}
                  className={itemClass(isActive || moreOpen)}
                >
                  <Icon className={clsx('h-5 w-5', (isActive || moreOpen) && 'stroke-[2.5]')} aria-hidden="true" />
                  <span>{label}</span>
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
