/**
 * LoadingSpinner - Production-grade loading indicators
 *
 * Features:
 * - Multiple sizes and variants
 * - Accessible with proper ARIA
 * - Screen reader announcements
 */

import clsx from 'clsx';
import { memo } from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'white' | 'gray';
  className?: string;
  label?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

const colorClasses = {
  primary: 'text-primary-600',
  white: 'text-white',
  gray: 'text-gray-400',
};

export const LoadingSpinner = memo(function LoadingSpinner({
  size = 'md',
  variant = 'primary',
  className,
  label = 'Loading',
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label}
      className={clsx('inline-flex items-center justify-center', className)}
    >
      <Loader2
        className={clsx(
          'animate-spin',
          sizeClasses[size],
          colorClasses[variant]
        )}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
});

// Full page loading overlay
interface LoadingOverlayProps {
  message?: string;
  className?: string;
}

export const LoadingOverlay = memo(function LoadingOverlay({
  message = 'Loading...',
  className,
}: LoadingOverlayProps) {
  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm',
        className
      )}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="xl" />
        <p className="text-gray-600 font-medium">{message}</p>
      </div>
    </div>
  );
});

// Inline loading state
interface LoadingInlineProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingInline = memo(function LoadingInline({
  message,
  size = 'md',
  className,
}: LoadingInlineProps) {
  return (
    <div
      className={clsx('flex items-center justify-center gap-3 py-8', className)}
      role="status"
      aria-live="polite"
    >
      <LoadingSpinner size={size} />
      {message && <span className="text-gray-500">{message}</span>}
    </div>
  );
});

// Button loading state helper
interface ButtonLoadingProps {
  loading: boolean;
  children: React.ReactNode;
  loadingText?: string;
}

export const ButtonContent = memo(function ButtonContent({
  loading,
  children,
  loadingText,
}: ButtonLoadingProps) {
  if (loading) {
    return (
      <>
        <LoadingSpinner size="sm" variant="white" className="mr-2" />
        {loadingText || children}
      </>
    );
  }
  return <>{children}</>;
});
