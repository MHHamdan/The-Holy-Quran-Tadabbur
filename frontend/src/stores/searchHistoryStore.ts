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

// Generate a unique session ID
function generateSessionId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return `sess_${timestamp}_${random}`;
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
      partialize: (state) => ({
        sessionId: state.sessionId,
        // Don't persist the cache, always fetch fresh
      }),
    }
  )
);
