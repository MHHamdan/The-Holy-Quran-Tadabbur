/**
 * EmptyState - Production-grade empty state components
 *
 * Features:
 * - Customizable icons and messages
 * - Action buttons
 * - Accessible
 * - Multiple variants
 */

import clsx from 'clsx';
import { memo, type ReactNode } from 'react';
import { useLanguageStore } from '../../stores/languageStore';

type Bi = { ar: string; en: string };

/** Pick the string for the current UI language. */
function useBi(): (b: Bi) => string {
  const language = useLanguageStore((s) => s.language);
  return (b: Bi) => (language === 'ar' ? b.ar : b.en);
}
import {
  Search,
  FileX,
  WifiOff,
  AlertCircle,
  Inbox,
  type LucideIcon,
} from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'default' | 'compact' | 'centered';
  className?: string;
  children?: ReactNode;
}

export const EmptyState = memo(function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  secondaryAction,
  variant = 'default',
  className,
  children,
}: EmptyStateProps) {
  const isCompact = variant === 'compact';
  const isCentered = variant === 'centered';

  return (
    <div
      className={clsx(
        'flex flex-col items-center text-center',
        isCompact ? 'py-6' : 'py-12',
        isCentered && 'min-h-[300px] justify-center',
        className
      )}
      role="status"
      aria-label={title}
    >
      <div
        className={clsx(
          'rounded-full bg-gray-100 mb-4',
          isCompact ? 'p-3' : 'p-4'
        )}
      >
        <Icon
          className={clsx(
            'text-gray-500',
            isCompact ? 'w-6 h-6' : 'w-10 h-10'
          )}
          aria-hidden="true"
        />
      </div>

      <h3
        className={clsx(
          'font-semibold text-gray-900',
          isCompact ? 'text-base mb-1' : 'text-lg mb-2'
        )}
      >
        {title}
      </h3>

      {description && (
        <p
          className={clsx(
            'text-gray-600 max-w-sm',
            isCompact ? 'text-sm mb-3' : 'text-base mb-4'
          )}
        >
          {description}
        </p>
      )}

      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {action && (
            <button
              type="button"
              onClick={action.onClick}
              className="inline-flex min-h-11 items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="inline-flex min-h-11 items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}

      {children}
    </div>
  );
});

// Pre-built empty state variants
export const NoSearchResults = memo(function NoSearchResults({
  query,
  onClear,
  className,
}: {
  query?: string;
  onClear?: () => void;
  className?: string;
}) {
  const bi = useBi();
  return (
    <EmptyState
      icon={Search}
      title={bi({ ar: 'لا توجد نتائج', en: 'No results found' })}
      description={
        query
          ? bi({ ar: `لا توجد نتائج لـ «${query}». جرّب كلمات أخرى.`, en: `No results found for "${query}". Try adjusting your search terms.` })
          : bi({ ar: 'جرّب البحث عن شيء آخر.', en: 'Try searching for something else.' })
      }
      action={onClear ? { label: bi({ ar: 'مسح البحث', en: 'Clear search' }), onClick: onClear } : undefined}
      className={className}
    />
  );
});

export const NoData = memo(function NoData({
  title,
  description,
  onRefresh,
  className,
}: {
  title?: string;
  description?: string;
  onRefresh?: () => void;
  className?: string;
}) {
  const bi = useBi();
  return (
    <EmptyState
      icon={FileX}
      title={title || bi({ ar: 'لا توجد بيانات', en: 'No data available' })}
      description={description || bi({ ar: 'لا توجد بيانات لعرضها الآن.', en: 'There is no data to display at this time.' })}
      action={onRefresh ? { label: bi({ ar: 'تحديث', en: 'Refresh' }), onClick: onRefresh } : undefined}
      className={className}
    />
  );
});

export const OfflineState = memo(function OfflineState({
  onRetry,
  className,
}: {
  onRetry?: () => void;
  className?: string;
}) {
  const bi = useBi();
  return (
    <EmptyState
      icon={WifiOff}
      title={bi({ ar: 'أنت غير متصل', en: "You're offline" })}
      description={bi({ ar: 'تحقّق من اتصالك بالإنترنت ثم أعد المحاولة.', en: 'Please check your internet connection and try again.' })}
      action={onRetry ? { label: bi({ ar: 'إعادة المحاولة', en: 'Try again' }), onClick: onRetry } : undefined}
      className={className}
    />
  );
});

export const ErrorState = memo(function ErrorState({
  title,
  description,
  onRetry,
  className,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  const bi = useBi();
  return (
    <EmptyState
      icon={AlertCircle}
      title={title || bi({ ar: 'حدث خطأ', en: 'Something went wrong' })}
      description={description || bi({ ar: 'حدث خطأ. أعد المحاولة.', en: 'An error occurred. Please try again.' })}
      action={onRetry ? { label: bi({ ar: 'إعادة المحاولة', en: 'Try again' }), onClick: onRetry } : undefined}
      className={className}
    />
  );
});

// Location permission denied state
export const LocationDenied = memo(function LocationDenied({
  onManualEntry,
  className,
}: {
  onManualEntry?: () => void;
  className?: string;
}) {
  const bi = useBi();
  return (
    <EmptyState
      icon={AlertCircle}
      title={bi({ ar: 'لم يُسمح بالوصول إلى الموقع', en: 'Location access denied' })}
      description={bi({
        ar: 'فعّل إذن الموقع من إعدادات المتصفح أو الجهاز، أو أدخل مدينتك يدوياً.',
        en: 'Please enable location permissions in your browser settings, or enter your location manually.',
      })}
      action={
        onManualEntry
          ? { label: bi({ ar: 'أدخل الموقع يدوياً', en: 'Enter location manually' }), onClick: onManualEntry }
          : undefined
      }
      className={className}
    />
  );
});
