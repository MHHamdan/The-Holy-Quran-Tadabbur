/**
 * useAsync - Production-grade async state management hook
 *
 * Features:
 * - Type-safe state transitions
 * - Automatic cleanup on unmount
 * - Request deduplication
 * - Retry with exponential backoff
 * - Stale-while-revalidate pattern support
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export type AsyncState<T> =
  | { status: 'idle'; data: null; error: null }
  | { status: 'pending'; data: T | null; error: null }
  | { status: 'success'; data: T; error: null }
  | { status: 'error'; data: T | null; error: Error };

export interface UseAsyncOptions<T> {
  /** Initial data (useful for SSR or cached data) */
  initialData?: T;
  /** Callback on successful execution */
  onSuccess?: (data: T) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Number of retry attempts (default: 0) */
  retryCount?: number;
  /** Base delay for exponential backoff in ms (default: 1000) */
  retryDelay?: number;
  /** Keep previous data while refetching */
  keepPreviousData?: boolean;
}

export interface UseAsyncReturn<T, Args extends unknown[]> {
  /** Current async state */
  state: AsyncState<T>;
  /** Execute the async function */
  execute: (...args: Args) => Promise<T | undefined>;
  /** Reset to idle state */
  reset: () => void;
  /** Convenience getters */
  isIdle: boolean;
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
  data: T | null;
  error: Error | null;
}

export function useAsync<T, Args extends unknown[] = []>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: UseAsyncOptions<T> = {}
): UseAsyncReturn<T, Args> {
  const {
    initialData,
    onSuccess,
    onError,
    retryCount = 0,
    retryDelay = 1000,
    keepPreviousData = false,
  } = options;

  const [state, setState] = useState<AsyncState<T>>(() =>
    initialData
      ? { status: 'success', data: initialData, error: null }
      : { status: 'idle', data: null, error: null }
  );

  // Track mounted state to prevent state updates after unmount
  const mountedRef = useRef(true);
  // Track current request to handle race conditions
  const requestIdRef = useRef(0);
  // Store callbacks in refs to avoid dependency issues
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [onSuccess, onError]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args: Args): Promise<T | undefined> => {
      const requestId = ++requestIdRef.current;

      setState((prev) => ({
        status: 'pending',
        data: keepPreviousData ? prev.data : null,
        error: null,
      }));

      let lastError: Error | null = null;
      let attempts = 0;
      const maxAttempts = retryCount + 1;

      while (attempts < maxAttempts) {
        try {
          const result = await asyncFunction(...args);

          // Only update if this is still the latest request and component is mounted
          if (requestId === requestIdRef.current && mountedRef.current) {
            setState({ status: 'success', data: result, error: null });
            onSuccessRef.current?.(result);
          }

          return result;
        } catch (err) {
          lastError = err instanceof Error ? err : new Error(String(err));
          attempts++;

          // If we have more attempts, wait with exponential backoff
          if (attempts < maxAttempts) {
            await new Promise((resolve) =>
              setTimeout(resolve, retryDelay * Math.pow(2, attempts - 1))
            );
          }
        }
      }

      // All attempts failed
      if (requestId === requestIdRef.current && mountedRef.current) {
        setState((prev) => ({
          status: 'error',
          data: keepPreviousData ? prev.data : null,
          error: lastError!,
        }));
        onErrorRef.current?.(lastError!);
      }

      return undefined;
    },
    [asyncFunction, keepPreviousData, retryCount, retryDelay]
  );

  const reset = useCallback(() => {
    requestIdRef.current++;
    setState({ status: 'idle', data: null, error: null });
  }, []);

  return {
    state,
    execute,
    reset,
    isIdle: state.status === 'idle',
    isPending: state.status === 'pending',
    isSuccess: state.status === 'success',
    isError: state.status === 'error',
    data: state.data,
    error: state.error,
  };
}

/**
 * useAsyncCallback - Like useAsync but for callbacks that don't auto-execute
 */
export function useAsyncCallback<T, Args extends unknown[]>(
  asyncFunction: (...args: Args) => Promise<T>,
  deps: React.DependencyList = []
): UseAsyncReturn<T, Args> {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const stableAsyncFunction = useCallback(asyncFunction, deps);
  return useAsync(stableAsyncFunction);
}
