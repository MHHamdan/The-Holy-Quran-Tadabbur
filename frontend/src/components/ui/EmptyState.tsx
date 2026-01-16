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
            'text-gray-400',
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
            'text-gray-500 max-w-sm',
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
              onClick={action.onClick}
              className="inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="inline-flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
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
  return (
    <EmptyState
      icon={Search}
      title="No results found"
      description={
        query
          ? `No results found for "${query}". Try adjusting your search terms.`
          : 'Try searching for something else.'
      }
      action={onClear ? { label: 'Clear search', onClick: onClear } : undefined}
      className={className}
    />
  );
});

export const NoData = memo(function NoData({
  title = 'No data available',
  description,
  onRefresh,
  className,
}: {
  title?: string;
  description?: string;
  onRefresh?: () => void;
  className?: string;
}) {
  return (
    <EmptyState
      icon={FileX}
      title={title}
      description={description || 'There is no data to display at this time.'}
      action={onRefresh ? { label: 'Refresh', onClick: onRefresh } : undefined}
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
  return (
    <EmptyState
      icon={WifiOff}
      title="You're offline"
      description="Please check your internet connection and try again."
      action={onRetry ? { label: 'Try again', onClick: onRetry } : undefined}
      className={className}
    />
  );
});

export const ErrorState = memo(function ErrorState({
  title = 'Something went wrong',
  description,
  onRetry,
  className,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <EmptyState
      icon={AlertCircle}
      title={title}
      description={description || 'An error occurred. Please try again.'}
      action={onRetry ? { label: 'Try again', onClick: onRetry } : undefined}
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
  return (
    <EmptyState
      icon={AlertCircle}
      title="Location access denied"
      description="Please enable location permissions in your browser settings, or enter your location manually."
      action={
        onManualEntry
          ? { label: 'Enter location manually', onClick: onManualEntry }
          : undefined
      }
      className={className}
    />
  );
});
