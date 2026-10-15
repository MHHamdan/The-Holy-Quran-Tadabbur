/**
 * ErrorBoundary - Production-grade error boundary component
 *
 * Features:
 * - Catches JavaScript errors anywhere in child component tree
 * - Logs error information
 * - Displays a fallback UI
 * - Recovery options
 * - Error reporting hook
 */

import { Component, type ErrorInfo, type ReactNode, memo } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { t, type Language } from '../../i18n/translations';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  /** 'panel': a one-line "not available" notice for a part of a page. */
  variant?: 'page' | 'panel';
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
  resetKeys?: unknown[];
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Log error
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler
    this.props.onError?.(error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // Reset error state if resetKeys changed
    if (this.state.hasError && this.props.resetKeys) {
      const hasChanged = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      );
      if (hasChanged) {
        this.resetErrorBoundary();
      }
    }
  }

  resetErrorBoundary = (): void => {
    this.props.onReset?.();
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onReset={this.resetErrorBoundary}
          variant={this.props.variant}
        />
      );
    }

    return this.props.children;
  }
}

// Default error fallback UI. Localized from the language store; the raw
// error text is shown only in development builds (it is meaningless to
// readers and was shown in English inside the Arabic UI).
interface ErrorFallbackProps {
  error: Error | null;
  onReset?: () => void;
  variant?: 'page' | 'panel';
  /** Overrides the language store (tests, previews). */
  language?: Language;
  /** Overrides import.meta.env.DEV (tests). */
  showDetails?: boolean;
}

export const ErrorFallback = memo(function ErrorFallback({
  error,
  onReset,
  variant = 'page',
  language: languageProp,
  showDetails = import.meta.env.DEV,
}: ErrorFallbackProps) {
  const storeLanguage = useLanguageStore((s) => s.language);
  const language = languageProp ?? storeLanguage;
  const isAr = language === 'ar';

  if (variant === 'panel') {
    return (
      <div
        role="alert"
        dir={isAr ? 'rtl' : 'ltr'}
        className={clsx('flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700', isAr && 'font-arabic')}
      >
        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
        <span className="flex-1">{t('panel_unavailable', language)}</span>
        {onReset && (
          <button type="button" onClick={onReset} className="min-h-11 rounded-lg px-3 text-primary-700 underline">
            {t('err_boundary_retry', language)}
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className="min-h-[200px] flex items-center justify-center p-6"
      role="alert"
      aria-live="assertive"
      dir={isAr ? 'rtl' : 'ltr'}
      lang={language}
    >
      <div className="text-center max-w-md">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
          <AlertTriangle className="w-8 h-8 text-red-600" aria-hidden="true" />
        </div>

        <h2 className={clsx('text-xl font-semibold text-gray-900 mb-2', isAr && 'font-arabic')}>
          {t('err_boundary_title', language)}
        </h2>

        <p className={clsx('text-gray-600 mb-4', isAr && 'font-arabic')}>
          {t('err_boundary_body', language)}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              className={clsx('inline-flex min-h-11 items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors', isAr && 'font-arabic')}
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              {t('err_boundary_retry', language)}
            </button>
          )}

          <a
            href="/"
            className={clsx('inline-flex min-h-11 items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors', isAr && 'font-arabic')}
          >
            <Home className="w-4 h-4" aria-hidden="true" />
            {t('err_boundary_home', language)}
          </a>
        </div>

        {showDetails && error && (
          <details className="mt-4 text-start">
            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
              {t('err_boundary_details', language)}
            </summary>
            <pre dir="ltr" className="mt-2 p-3 bg-gray-100 rounded text-xs text-red-700 overflow-auto max-h-40 text-left">
              {error.message}
              {'\n'}
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
});

// Inline error display for non-critical errors
interface InlineErrorProps {
  error: Error | string | null;
  onRetry?: () => void;
  className?: string;
}

export const InlineError = memo(function InlineError({
  error,
  onRetry,
  className,
}: InlineErrorProps) {
  const language = useLanguageStore((s) => s.language);
  if (!error) return null;

  const message = typeof error === 'string' ? error : error.message;

  return (
    <div
      className={`flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg ${className || ''}`}
      role="alert"
    >
      <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" aria-hidden="true" />
      <p className="flex-1 text-sm text-red-800">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="shrink-0 min-h-11 px-3 text-sm bg-red-700 text-white rounded hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          {t('err_boundary_retry', language)}
        </button>
      )}
    </div>
  );
});
