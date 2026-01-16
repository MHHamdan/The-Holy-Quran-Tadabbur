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
    sura: (suraNo: number) => ['quran', 'sura', suraNo] as const,
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
