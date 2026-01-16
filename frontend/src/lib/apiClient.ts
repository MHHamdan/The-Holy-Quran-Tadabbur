/**
 * API Client - Production-grade HTTP client with caching and retry
 *
 * Features:
 * - Request/response interceptors
 * - Automatic retry with exponential backoff
 * - In-memory caching with TTL
 * - Request deduplication
 * - Type-safe error handling
 * - Request cancellation
 */

import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios';

// ============================================
// Types
// ============================================

export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  cacheTTL?: number;
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly isNetworkError: boolean;
  public readonly isTimeout: boolean;
  public readonly originalError: AxiosError | Error;

  constructor(
    message: string,
    status: number,
    code: string,
    originalError: AxiosError | Error
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.originalError = originalError;
    this.isNetworkError = code === 'NETWORK_ERROR';
    this.isTimeout = code === 'TIMEOUT';
  }
}

// ============================================
// In-Memory Cache
// ============================================

class RequestCache {
  private cache = new Map<string, CacheEntry<unknown>>();
  private pendingRequests = new Map<string, Promise<unknown>>();

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() > entry.timestamp + entry.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  set<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  // Request deduplication
  getPending<T>(key: string): Promise<T> | null {
    return this.pendingRequests.get(key) as Promise<T> | null;
  }

  setPending<T>(key: string, promise: Promise<T>): void {
    this.pendingRequests.set(key, promise);
    promise.finally(() => this.pendingRequests.delete(key));
  }
}

// ============================================
// API Client Factory
// ============================================

export function createApiClient(config: ApiClientConfig = {}): {
  client: AxiosInstance;
  cache: RequestCache;
  cachedGet: <T>(url: string, config?: AxiosRequestConfig & { cacheTTL?: number }) => Promise<T>;
  clearCache: () => void;
} {
  const {
    baseURL = '',
    timeout = 30000,
    retries = 3,
    retryDelay = 1000,
    cacheTTL = 5 * 60 * 1000, // 5 minutes default
  } = config;

  const cache = new RequestCache();

  // Create axios instance
  const client = axios.create({
    baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor for logging
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add timestamp for performance tracking
      config.headers.set('X-Request-Time', Date.now().toString());
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & {
        _retryCount?: number;
      };

      if (!originalRequest) {
        throw createApiError(error);
      }

      // Initialize retry count
      originalRequest._retryCount = originalRequest._retryCount ?? 0;

      // Check if we should retry
      const shouldRetry =
        originalRequest._retryCount < retries &&
        (!error.response || error.response.status >= 500) &&
        originalRequest.method?.toLowerCase() === 'get';

      if (shouldRetry) {
        originalRequest._retryCount++;

        // Exponential backoff
        const delay = retryDelay * Math.pow(2, originalRequest._retryCount - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));

        return client(originalRequest);
      }

      throw createApiError(error);
    }
  );

  // Create API error from axios error
  function createApiError(error: AxiosError): ApiError {
    if (error.code === 'ECONNABORTED') {
      return new ApiError(
        'Request timed out. Please try again.',
        0,
        'TIMEOUT',
        error
      );
    }

    if (!error.response) {
      return new ApiError(
        'Network error. Please check your connection.',
        0,
        'NETWORK_ERROR',
        error
      );
    }

    const status = error.response.status;
    const data = error.response.data as { message?: string; error?: string };
    const message =
      data?.message ||
      data?.error ||
      getDefaultErrorMessage(status);

    return new ApiError(message, status, `HTTP_${status}`, error);
  }

  function getDefaultErrorMessage(status: number): string {
    switch (status) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please log in again.';
      case 403:
        return 'Access forbidden.';
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      case 502:
        return 'Bad gateway. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return 'An unexpected error occurred.';
    }
  }

  // Cached GET request
  async function cachedGet<T>(
    url: string,
    requestConfig?: AxiosRequestConfig & { cacheTTL?: number }
  ): Promise<T> {
    const ttl = requestConfig?.cacheTTL ?? cacheTTL;
    const cacheKey = `${url}:${JSON.stringify(requestConfig?.params || {})}`;

    // Check cache first
    const cached = cache.get<T>(cacheKey);
    if (cached !== null) {
      return cached;
    }

    // Check for pending request (deduplication)
    const pending = cache.getPending<T>(cacheKey);
    if (pending) {
      return pending;
    }

    // Make new request
    const promise = client.get<T>(url, requestConfig).then((response) => {
      cache.set(cacheKey, response.data, ttl);
      return response.data;
    });

    cache.setPending(cacheKey, promise);
    return promise;
  }

  return {
    client,
    cache,
    cachedGet,
    clearCache: () => cache.clear(),
  };
}

// ============================================
// Default API Client Instance
// ============================================

export const { client: apiClient, cachedGet, clearCache } = createApiClient({
  timeout: 30000,
  retries: 3,
  cacheTTL: 5 * 60 * 1000,
});

// ============================================
// Utility Functions
// ============================================

/**
 * Check if error is a specific API error type
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

/**
 * Wrap async function with error handling
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  errorMessage = 'Operation failed'
): Promise<{ data: T | null; error: ApiError | null }> {
  try {
    const data = await fn();
    return { data, error: null };
  } catch (error) {
    if (isApiError(error)) {
      return { data: null, error };
    }
    return {
      data: null,
      error: new ApiError(
        errorMessage,
        0,
        'UNKNOWN',
        error instanceof Error ? error : new Error(String(error))
      ),
    };
  }
}
