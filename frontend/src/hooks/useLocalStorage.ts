/**
 * useLocalStorage - Production-grade localStorage hook
 *
 * Features:
 * - Type-safe with JSON serialization
 * - Cross-tab synchronization
 * - Automatic cleanup
 * - Error handling
 * - SSR safe
 */

import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';

type SetValue<T> = T | ((prevValue: T) => T);

function getStorageValue<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') {
    return defaultValue;
  }

  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item) as T;
  } catch (error) {
    console.warn(`Error reading localStorage key "${key}":`, error);
    return defaultValue;
  }
}

function setStorageValue<T>(key: string, value: T): void {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    if (value === undefined) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(value));
    }
    // Dispatch storage event for cross-tab sync
    window.dispatchEvent(new StorageEvent('storage', { key, newValue: JSON.stringify(value) }));
  } catch (error) {
    console.warn(`Error setting localStorage key "${key}":`, error);
  }
}

/**
 * Simple useLocalStorage hook
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (value: SetValue<T>) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T>(() =>
    getStorageValue(key, defaultValue)
  );

  const setValue = useCallback(
    (value: SetValue<T>) => {
      setStoredValue((prev) => {
        const newValue = value instanceof Function ? value(prev) : value;
        setStorageValue(key, newValue);
        return newValue;
      });
    },
    [key]
  );

  const removeValue = useCallback(() => {
    setStoredValue(defaultValue);
    try {
      localStorage.removeItem(key);
    } catch {
      // Ignore errors
    }
  }, [key, defaultValue]);

  // Sync with other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(JSON.parse(e.newValue));
        } catch {
          // Ignore parse errors
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key]);

  return [storedValue, setValue, removeValue];
}

/**
 * useLocalStorageSync - Uses useSyncExternalStore for better React 18 support
 */
export function useLocalStorageSync<T>(
  key: string,
  defaultValue: T
): [T, (value: SetValue<T>) => void] {
  const subscribe = useCallback(
    (callback: () => void) => {
      const handleStorage = (e: StorageEvent) => {
        if (e.key === key) {
          callback();
        }
      };
      window.addEventListener('storage', handleStorage);
      return () => window.removeEventListener('storage', handleStorage);
    },
    [key]
  );

  const getSnapshot = useCallback(() => {
    return localStorage.getItem(key);
  }, [key]);

  const getServerSnapshot = useCallback(() => {
    return JSON.stringify(defaultValue);
  }, [defaultValue]);

  const serializedValue = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );

  const value: T = serializedValue ? JSON.parse(serializedValue) : defaultValue;

  const setValue = useCallback(
    (newValue: SetValue<T>) => {
      const valueToStore = newValue instanceof Function ? newValue(value) : newValue;
      setStorageValue(key, valueToStore);
    },
    [key, value]
  );

  return [value, setValue];
}
