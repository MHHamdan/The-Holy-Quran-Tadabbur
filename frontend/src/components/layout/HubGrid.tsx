import { Link } from 'react-router-dom';
import clsx from 'clsx';
import type { Language } from '../../i18n/translations';
import type { NavLink } from './navConfig';

/** Grid of hub links (icon, title, optional one-line description). */
export function HubGrid({
  items,
  language,
  compact = false,
  onNavigate,
}: {
  items: NavLink[];
  language: Language;
  compact?: boolean;
  onNavigate?: () => void;
}) {
  const isAr = language === 'ar';
  return (
    <ul
      className={clsx(
        'grid gap-3',
        compact ? 'grid-cols-2 sm:grid-cols-3' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
      )}
    >
      {items.map((item) => {
        const Icon = item.icon;
        const desc = item.desc ? item.desc[language] : null;
        return (
          <li key={item.path}>
            <Link
              to={item.path}
              onClick={onNavigate}
              className={clsx(
                'group flex h-full items-start gap-3 rounded-xl border border-gray-200 bg-white transition-colors hover:border-primary-300 hover:bg-primary-50/40',
                compact ? 'min-h-12 p-3' : 'p-4',
              )}
            >
              <span className="shrink-0 rounded-lg bg-primary-50 p-2 text-primary-700" aria-hidden="true">
                <Icon className={compact ? 'h-4 w-4' : 'h-5 w-5'} />
              </span>
              <span className="min-w-0 flex-1">
                <span
                  className={clsx(
                    'block font-semibold text-gray-900 group-hover:text-primary-700',
                    compact ? 'text-sm' : 'text-base',
                    isAr && 'font-arabic',
                  )}
                >
                  {item.title[language]}
                </span>
                {desc && !compact && (
                  <span className={clsx('mt-0.5 block text-sm leading-relaxed text-gray-600', isAr && 'font-arabic')}>
                    {desc}
                  </span>
                )}
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
