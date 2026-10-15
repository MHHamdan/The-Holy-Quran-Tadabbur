/**
 * Search History Store
 *
 * Manages user session and search history for personalization:
 * - Persistent session ID
 * - Local search history cache
 * - API integration for recording and retrieving
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { quranApi, SearchHistoryEntry, SearchSuggestion, VerseRecommendation } from '../lib/api';

// The session id is the only key to a reader's server-side search history,
// so it comes from the CSPRNG: "sess_" + a v4 UUID (the backend rejects
// anything else).
export const SESSION_ID_PATTERN = /^sess_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function uuidV4(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Older WebViews without randomUUID: same format from getRandomValues
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

export function generateSessionId(): string {
  return `sess_${uuidV4()}`;
}

interface SearchHistoryState {
  // Session
  sessionId: string;

  // Local cache of recent searches (for quick access)
  recentSearches: SearchHistoryEntry[];
  suggestions: SearchSuggestion[];
  recommendations: VerseRecommendation[];

  // Loading states
  isLoadingHistory: boolean;
  isLoadingSuggestions: boolean;
  isLoadingRecommendations: boolean;

  // Actions
  recordSearch: (query: string, queryType?: string, resultCount?: number, themes?: string[]) => Promise<void>;
  recordVerseClick: (suraNo: number, ayaNo: number, context?: string) => Promise<void>;
  loadHistory: (limit?: number, queryType?: string) => Promise<void>;
  loadSuggestions: (prefix?: string, limit?: number) => Promise<void>;
  loadRecommendations: (limit?: number) => Promise<void>;
  clearHistory: () => Promise<void>;
  resetSession: () => void;
}

export const useSearchHistoryStore = create<SearchHistoryState>()(
  persist(
    (set, get) => ({
      // Initialize with a new session ID
      sessionId: generateSessionId(),

      // Empty initial state
      recentSearches: [],
      suggestions: [],
      recommendations: [],

      // Loading states
      isLoadingHistory: false,
      isLoadingSuggestions: false,
      isLoadingRecommendations: false,

      // Record a search query
      recordSearch: async (query: string, queryType = 'text', resultCount = 0, themes?: string[]) => {
        const { sessionId } = get();
        try {
          await quranApi.recordSearch(sessionId, {
            query,
            query_type: queryType,
            result_count: resultCount,
            themes,
          });

          // Optimistically update local cache
          const newEntry: SearchHistoryEntry = {
            query,
            query_type: queryType,
            timestamp: new Date().toISOString(),
            result_count: resultCount,
            clicked_verses: [],
          };

          set((state) => ({
            recentSearches: [newEntry, ...state.recentSearches.slice(0, 19)],
          }));
        } catch (error) {
          console.error('Failed to record search:', error);
        }
      },

      // Record a verse click
      recordVerseClick: async (suraNo: number, ayaNo: number, context = 'search') => {
        const { sessionId } = get();
        try {
          await quranApi.recordVerseClick(sessionId, {
            sura_no: suraNo,
            aya_no: ayaNo,
            context,
          });
        } catch (error) {
          console.error('Failed to record verse click:', error);
        }
      },

      // Load search history from server
      loadHistory: async (limit = 20, queryType?: string) => {
        const { sessionId } = get();
        set({ isLoadingHistory: true });

        try {
          const response = await quranApi.getSearchHistory(sessionId, { limit, query_type: queryType });
          set({ recentSearches: response.data });
        } catch (error) {
          console.error('Failed to load search history:', error);
        } finally {
          set({ isLoadingHistory: false });
        }
      },

      // Load search suggestions
      loadSuggestions: async (prefix?: string, limit = 10) => {
        const { sessionId } = get();
        set({ isLoadingSuggestions: true });

        try {
          const response = await quranApi.getSearchSuggestions(sessionId, { prefix, limit });
          set({ suggestions: response.data });
        } catch (error) {
          console.error('Failed to load suggestions:', error);
        } finally {
          set({ isLoadingSuggestions: false });
        }
      },

      // Load personalized recommendations
      loadRecommendations: async (limit = 10) => {
        const { sessionId } = get();
        set({ isLoadingRecommendations: true });

        try {
          const response = await quranApi.getPersonalizedRecommendations(sessionId, limit);
          set({ recommendations: response.data });
        } catch (error) {
          console.error('Failed to load recommendations:', error);
        } finally {
          set({ isLoadingRecommendations: false });
        }
      },

      // Clear search history
      clearHistory: async () => {
        const { sessionId } = get();
        try {
          await quranApi.clearSearchHistory(sessionId);
          set({
            recentSearches: [],
            suggestions: [],
            recommendations: [],
          });
        } catch (error) {
          console.error('Failed to clear history:', error);
        }
      },

      // Reset session (for testing or privacy)
      resetSession: () => {
        set({
          sessionId: generateSessionId(),
          recentSearches: [],
          suggestions: [],
          recommendations: [],
        });
      },
    }),
    {
      name: 'tadabbur-search-history',
      // v1: ids from Math.random (v0) are replaced with CSPRNG ids
      version: 1,
      migrate: (persisted) => {
        const state = (persisted ?? {}) as { sessionId?: string };
        const sessionId = state.sessionId && SESSION_ID_PATTERN.test(state.sessionId)
          ? state.sessionId
          : generateSessionId();
        return { ...state, sessionId } as SearchHistoryState;
      },
      partialize: (state) => ({
        sessionId: state.sessionId,
        // Don't persist the cache, always fetch fresh
      }),
    }
  )
);
