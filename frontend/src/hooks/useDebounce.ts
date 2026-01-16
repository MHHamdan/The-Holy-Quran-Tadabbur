/**
 * useDebounce & useThrottle - Production-grade timing hooks
 *
 * Features:
 * - Type-safe
 * - Automatic cleanup
 * - Leading/trailing edge options
 * - Cancel capability
 */

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * useDebounce - Debounce a value
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * useDebouncedCallback - Debounce a callback function
 */
export function useDebouncedCallback<Args extends unknown[]>(
  callback: (...args: Args) => void,
  delay: number,
  options: { leading?: boolean; trailing?: boolean } = {}
): {
  (...args: Args): void;
  cancel: () => void;
  flush: () => void;
} {
  const { leading = false, trailing = true } = options;

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const callbackRef = useRef(callback);
  const lastArgsRef = useRef<Args | null>(null);
  const hasLeadingRef = useRef(false);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    hasLeadingRef.current = false;
    lastArgsRef.current = null;
  }, []);

  const flush = useCallback(() => {
    if (timeoutRef.current && lastArgsRef.current) {
      callbackRef.current(...lastArgsRef.current);
      cancel();
    }
  }, [cancel]);

  const debouncedCallback = useCallback(
    (...args: Args) => {
      lastArgsRef.current = args;

      // Leading edge call
      if (leading && !hasLeadingRef.current) {
        hasLeadingRef.current = true;
        callbackRef.current(...args);
      }

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        // Trailing edge call
        if (trailing && lastArgsRef.current) {
          callbackRef.current(...lastArgsRef.current);
        }
        hasLeadingRef.current = false;
        timeoutRef.current = null;
        lastArgsRef.current = null;
      }, delay);
    },
    [delay, leading, trailing]
  );

  return Object.assign(debouncedCallback, { cancel, flush });
}

/**
 * useThrottle - Throttle a value
 */
export function useThrottle<T>(value: T, interval: number): T {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastExecutedRef = useRef(Date.now());
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const now = Date.now();
    const elapsed = now - lastExecutedRef.current;

    if (elapsed >= interval) {
      setThrottledValue(value);
      lastExecutedRef.current = now;
    } else {
      // Schedule update for remaining time
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        setThrottledValue(value);
        lastExecutedRef.current = Date.now();
      }, interval - elapsed);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, interval]);

  return throttledValue;
}

/**
 * useThrottledCallback - Throttle a callback function
 */
export function useThrottledCallback<Args extends unknown[]>(
  callback: (...args: Args) => void,
  interval: number
): (...args: Args) => void {
  const lastExecutedRef = useRef(0);
  const callbackRef = useRef(callback);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastArgsRef = useRef<Args | null>(null);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return useCallback(
    (...args: Args) => {
      const now = Date.now();
      const elapsed = now - lastExecutedRef.current;
      lastArgsRef.current = args;

      if (elapsed >= interval) {
        callbackRef.current(...args);
        lastExecutedRef.current = now;
      } else if (!timeoutRef.current) {
        timeoutRef.current = setTimeout(() => {
          if (lastArgsRef.current) {
            callbackRef.current(...lastArgsRef.current);
            lastExecutedRef.current = Date.now();
          }
          timeoutRef.current = null;
        }, interval - elapsed);
      }
    },
    [interval]
  );
}
