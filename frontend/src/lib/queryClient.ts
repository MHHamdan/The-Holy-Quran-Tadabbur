/**
 * React Query Configuration - FAANG-level Caching Strategy
 *
 * Key features:
 * 1. Optimized stale times for different data types
 * 2. Background refetching for fresh data
 * 3. Retry logic with exponential backoff
 * 4. Window focus refetching for real-time updates
 */

import { QueryClient } from '@tanstack/react-query';

// =============================================================================
// Query Client Configuration
// =============================================================================

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data is considered fresh for 5 minutes
      staleTime: 5 * 60 * 1000,

      // Cache data for 30 minutes
      gcTime: 30 * 60 * 1000,

      // Retry failed requests 3 times with exponential backoff
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch on window focus for fresh data
      refetchOnWindowFocus: false,

      // Don't refetch on reconnect by default
      refetchOnReconnect: true,

      // Keep previous data while fetching new data
      placeholderData: (previousData: unknown) => previousData,
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
});

// =============================================================================
// Query Keys Factory - Centralized key management
// =============================================================================

export const queryKeys = {
  // Quran queries
  quran: {
    all: ['quran'] as const,
    page: (pageNo: number) => ['quran', 'page', pageNo] as const,
    /** Page verses with translations of the meanings (Quran reader page mode). */
    pageWithTranslations: (pageNo: number, translations: string) =>
      ['quran', 'page', pageNo, translations] as const,
    sura: (suraNo: number) => ['quran', 'sura', suraNo] as const,
    /** Surah verses with translations of the meanings (Quran reader). */
    suraWithTranslations: (suraNo: number, translations: string) =>
      ['quran', 'sura', suraNo, translations] as const,
    metadata: () => ['quran', 'metadata'] as const,
    verse: (suraNo: number, ayaNo: number) => ['quran', 'verse', suraNo, ayaNo] as const,
    audio: (suraNo: number, ayaNo: number, reciter: string) =>
      ['quran', 'audio', suraNo, ayaNo, reciter] as const,
  },

  // Tafsir queries
  tafsir: {
    all: ['tafsir'] as const,
    verse: (suraNo: number, ayaNo: number, edition: string) =>
      ['tafsir', 'verse', suraNo, ayaNo, edition] as const,
    editions: () => ['tafsir', 'editions'] as const,
  },

  // AI/LLM queries
  ai: {
    all: ['ai'] as const,
    summary: (verseId: number, edition: string) => ['ai', 'summary', verseId, edition] as const,
    explanation: (word: string, verseId: number) => ['ai', 'explanation', word, verseId] as const,
    answer: (question: string, verseId: number) => ['ai', 'answer', question, verseId] as const,
  },

  // Stories queries
  stories: {
    all: ['stories'] as const,
    list: () => ['stories', 'list'] as const,
    detail: (storyId: string) => ['stories', 'detail', storyId] as const,
    atlas: () => ['stories', 'atlas'] as const,
    cluster: (clusterId: string) => ['stories', 'cluster', clusterId] as const,
  },

  // Concepts queries
  concepts: {
    all: ['concepts'] as const,
    list: () => ['concepts', 'list'] as const,
    detail: (conceptId: string) => ['concepts', 'detail', conceptId] as const,
  },

  // Themes queries
  themes: {
    all: ['themes'] as const,
    list: () => ['themes', 'list'] as const,
    detail: (themeId: string) => ['themes', 'detail', themeId] as const,
  },

  // Search queries
  search: {
    all: ['search'] as const,
    results: (query: string) => ['search', 'results', query] as const,
  },
} as const;

// =============================================================================
// Stale Time Configurations for Different Data Types
// =============================================================================

// =============================================================================
// Offline: persist canonical Qur'an queries to IndexedDB
// =============================================================================
//
// Only canonical, non-personal reader data is persisted: surah and page verse
// lists (Tanzil text + any translations of the meanings already shown) and the
// surah metadata. Data is stored exactly as the API returned it, nothing is
// transformed. Entries expire after 30 days. Works in browsers and in the
// Capacitor WebView, where no service worker caches the API.

const PERSIST_DB = 'tadabbur-query-cache';
const PERSIST_STORE = 'queries';
const PERSIST_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;

/** Query keys that may be persisted: ['quran', 'sura' | 'page' | 'metadata', ...]. */
export function isPersistableQueryKey(key: readonly unknown[]): boolean {
  return key[0] === 'quran' && (key[1] === 'sura' || key[1] === 'page' || key[1] === 'metadata');
}

interface PersistedQuery {
  id: string;
  queryKey: unknown[];
  data: unknown;
  updatedAt: number;
}

function openPersistDb(): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    try {
      if (typeof indexedDB === 'undefined') return resolve(null);
      const req = indexedDB.open(PERSIST_DB, 1);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(PERSIST_STORE)) {
          req.result.createObjectStore(PERSIST_STORE, { keyPath: 'id' });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
      req.onblocked = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

let dbPromise: Promise<IDBDatabase | null> | null = null;
const persistDb = () => (dbPromise ??= openPersistDb());

function withStore<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>): Promise<T | null> {
  return persistDb().then((db) => new Promise<T | null>((resolve) => {
    if (!db) return resolve(null);
    try {
      const req = run(db.transaction(PERSIST_STORE, mode).objectStore(PERSIST_STORE));
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    } catch {
      resolve(null);
    }
  }));
}

/** Load persisted queries (younger than 30 days) into the cache. */
export async function restorePersistedQueries(client: QueryClient = queryClient): Promise<number> {
  const rows = (await withStore<PersistedQuery[]>('readonly', (s) => s.getAll() as IDBRequest<PersistedQuery[]>)) ?? [];
  const now = Date.now();
  let restored = 0;
  for (const row of rows) {
    if (!row || !Array.isArray(row.queryKey) || now - row.updatedAt > PERSIST_MAX_AGE_MS) {
      if (row?.id) void withStore('readwrite', (s) => s.delete(row.id));
      continue;
    }
    if (client.getQueryData(row.queryKey) === undefined) {
      client.setQueryData(row.queryKey, row.data, { updatedAt: row.updatedAt });
      restored += 1;
    }
  }
  return restored;
}

/** Write every successful canonical query to IndexedDB. Returns an unsubscribe. */
export function startQueryPersistence(client: QueryClient = queryClient): () => void {
  return client.getQueryCache().subscribe((event) => {
    if (event.type !== 'updated' || event.action.type !== 'success') return;
    const { queryKey, state } = event.query;
    if (!isPersistableQueryKey(queryKey) || state.data === undefined) return;
    const row: PersistedQuery = {
      id: JSON.stringify(queryKey),
      queryKey: [...queryKey],
      data: state.data,
      updatedAt: state.dataUpdatedAt || Date.now(),
    };
    void withStore('readwrite', (s) => s.put(row));
  });
}

/** How many distinct surahs have their text stored on this device. */
export async function countPersistedSurahs(): Promise<number> {
  const ids = (await withStore<IDBValidKey[]>('readonly', (s) => s.getAllKeys())) ?? [];
  const surahs = new Set<unknown>();
  for (const id of ids) {
    try {
      const key = JSON.parse(String(id)) as unknown[];
      if (key[0] === 'quran' && key[1] === 'sura') surahs.add(key[2]);
    } catch { /* not a query key */ }
  }
  return surahs.size;
}

/** Remove the offline Qur'an copy from this device. */
export async function clearPersistedQueries(client: QueryClient = queryClient): Promise<void> {
  await withStore('readwrite', (s) => s.clear());
  client.removeQueries({ predicate: (q) => isPersistableQueryKey(q.queryKey) });
}

// Canonical text never changes: keep it in memory for the whole session so an
// offline reader does not lose a surah after the default 30-minute gc.
queryClient.setQueryDefaults(['quran', 'sura'], { gcTime: Infinity });
queryClient.setQueryDefaults(['quran', 'page'], { gcTime: Infinity });
queryClient.setQueryDefaults(['quran', 'metadata'], { gcTime: Infinity });

export const staleTimes = {
  // Quran text never changes - very long stale time
  quranText: 24 * 60 * 60 * 1000, // 24 hours

  // Tafsir data rarely changes
  tafsir: 60 * 60 * 1000, // 1 hour

  // AI responses can be cached for a while
  aiResponse: 30 * 60 * 1000, // 30 minutes

  // Audio URLs are stable
  audio: 24 * 60 * 60 * 1000, // 24 hours

  // Stories and concepts rarely change
  staticContent: 60 * 60 * 1000, // 1 hour

  // Search results should be fresh
  search: 5 * 60 * 1000, // 5 minutes
} as const;
