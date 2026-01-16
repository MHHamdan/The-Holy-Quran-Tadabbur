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

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
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
        />
      );
    }

    return this.props.children;
  }
}

// Default error fallback UI
interface ErrorFallbackProps {
  error: Error | null;
  onReset?: () => void;
}

export const ErrorFallback = memo(function ErrorFallback({
  error,
  onReset,
}: ErrorFallbackProps) {
  return (
    <div
      className="min-h-[200px] flex items-center justify-center p-6"
      role="alert"
      aria-live="assertive"
    >
      <div className="text-center max-w-md">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
          <AlertTriangle className="w-8 h-8 text-red-600" aria-hidden="true" />
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Something went wrong
        </h2>

        <p className="text-gray-600 mb-4">
          {error?.message || 'An unexpected error occurred. Please try again.'}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              Try Again
            </button>
          )}

          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            <Home className="w-4 h-4" aria-hidden="true" />
            Go Home
          </a>
        </div>

        {import.meta.env.DEV && error && (
          <details className="mt-4 text-left">
            <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
              Error details
            </summary>
            <pre className="mt-2 p-3 bg-gray-100 rounded text-xs text-red-600 overflow-auto max-h-40">
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
          className="shrink-0 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          Retry
        </button>
      )}
    </div>
  );
});
