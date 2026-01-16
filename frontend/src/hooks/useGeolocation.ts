/**
 * useGeolocation - Production-grade geolocation hook
 *
 * Features:
 * - Automatic permission handling
 * - High accuracy mode support
 * - Watching position changes
 * - Caching with localStorage
 * - Proper cleanup
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export interface GeolocationState {
  loading: boolean;
  error: GeolocationPositionError | Error | null;
  coords: {
    latitude: number;
    longitude: number;
    accuracy: number;
    altitude: number | null;
    altitudeAccuracy: number | null;
    heading: number | null;
    speed: number | null;
  } | null;
  timestamp: number | null;
}

export interface UseGeolocationOptions {
  /** Enable high accuracy mode (uses more battery) */
  enableHighAccuracy?: boolean;
  /** Maximum age of cached position in ms */
  maximumAge?: number;
  /** Timeout for position request in ms */
  timeout?: number;
  /** Watch position changes continuously */
  watch?: boolean;
  /** Cache key for localStorage */
  cacheKey?: string;
  /** Cache duration in ms (default: 5 minutes) */
  cacheDuration?: number;
}

const CACHE_KEY = 'tadabbur_geolocation_cache';
const DEFAULT_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface CachedPosition {
  coords: GeolocationState['coords'];
  timestamp: number;
  expiry: number;
}

function getCachedPosition(cacheKey: string): GeolocationState['coords'] | null {
  try {
    const cached = localStorage.getItem(cacheKey);
    if (!cached) return null;

    const parsed: CachedPosition = JSON.parse(cached);
    if (Date.now() > parsed.expiry) {
      localStorage.removeItem(cacheKey);
      return null;
    }

    return parsed.coords;
  } catch {
    return null;
  }
}

function setCachedPosition(
  cacheKey: string,
  coords: GeolocationState['coords'],
  duration: number
): void {
  try {
    const cached: CachedPosition = {
      coords,
      timestamp: Date.now(),
      expiry: Date.now() + duration,
    };
    localStorage.setItem(cacheKey, JSON.stringify(cached));
  } catch {
    // localStorage might be full or disabled
  }
}

export function useGeolocation(options: UseGeolocationOptions = {}): {
  state: GeolocationState;
  getCurrentPosition: () => void;
  clearWatch: () => void;
} {
  const {
    enableHighAccuracy = true,
    maximumAge = 0,
    timeout = 10000,
    watch = false,
    cacheKey = CACHE_KEY,
    cacheDuration = DEFAULT_CACHE_DURATION,
  } = options;

  const [state, setState] = useState<GeolocationState>(() => {
    // Try to get cached position on mount
    const cached = getCachedPosition(cacheKey);
    return {
      loading: false,
      error: null,
      coords: cached,
      timestamp: cached ? Date.now() : null,
    };
  });

  const watchIdRef = useRef<number | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleSuccess = useCallback(
    (position: GeolocationPosition) => {
      if (!mountedRef.current) return;

      const coords = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
      };

      setCachedPosition(cacheKey, coords, cacheDuration);

      setState({
        loading: false,
        error: null,
        coords,
        timestamp: position.timestamp,
      });
    },
    [cacheKey, cacheDuration]
  );

  const handleError = useCallback((error: GeolocationPositionError) => {
    if (!mountedRef.current) return;

    setState((prev) => ({
      ...prev,
      loading: false,
      error,
    }));
  }, []);

  const getCurrentPosition = useCallback(() => {
    if (!navigator.geolocation) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: new Error('Geolocation is not supported by your browser'),
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, {
      enableHighAccuracy,
      maximumAge,
      timeout,
    });
  }, [enableHighAccuracy, maximumAge, timeout, handleSuccess, handleError]);

  const clearWatch = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
  }, []);

  // Setup watching if enabled
  useEffect(() => {
    if (!watch || !navigator.geolocation) return;

    setState((prev) => ({ ...prev, loading: true }));

    watchIdRef.current = navigator.geolocation.watchPosition(
      handleSuccess,
      handleError,
      { enableHighAccuracy, maximumAge, timeout }
    );

    return clearWatch;
  }, [watch, enableHighAccuracy, maximumAge, timeout, handleSuccess, handleError, clearWatch]);

  return {
    state,
    getCurrentPosition,
    clearWatch,
  };
}
