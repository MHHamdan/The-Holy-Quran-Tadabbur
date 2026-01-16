/**
 * React Query Hooks for Quran Data
 *
 * FAANG-level optimizations:
 * 1. Automatic caching and deduplication
 * 2. Background refetching
 * 3. Optimistic updates
 * 4. Prefetching for adjacent pages
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
import { quranApi, api, Verse } from '../lib/api';
import { queryKeys, staleTimes } from '../lib/queryClient';

// =============================================================================
// Types
// =============================================================================

interface TafsirResponse {
  text: string;
  audio_url?: string;
  source: string;
}

interface AudioResponse {
  audio_url: string;
  reciter: string;
}

interface AIResponse {
  ok: boolean;
  result: string | null;
  error: string | null;
}

// =============================================================================
// Quran Page Verses Hook
// =============================================================================

export function usePageVerses(pageNo: number) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.quran.page(pageNo),
    queryFn: async () => {
      const response = await quranApi.getPageVerses(pageNo);
      return response.data as Verse[];
    },
    staleTime: staleTimes.quranText,
    enabled: pageNo >= 1 && pageNo <= 604,
  });

  // Prefetch adjacent pages for smooth navigation
  useEffect(() => {
    if (pageNo > 1) {
      queryClient.prefetchQuery({
        queryKey: queryKeys.quran.page(pageNo - 1),
        queryFn: () => quranApi.getPageVerses(pageNo - 1).then(r => r.data),
        staleTime: staleTimes.quranText,
      });
    }
    if (pageNo < 604) {
      queryClient.prefetchQuery({
        queryKey: queryKeys.quran.page(pageNo + 1),
        queryFn: () => quranApi.getPageVerses(pageNo + 1).then(r => r.data),
        staleTime: staleTimes.quranText,
      });
    }
  }, [pageNo, queryClient]);

  return query;
}

// =============================================================================
// Tafsir Hook
// =============================================================================

export function useTafsir(
  suraNo: number,
  ayaNo: number,
  edition: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: queryKeys.tafsir.verse(suraNo, ayaNo, edition),
    queryFn: async (): Promise<TafsirResponse> => {
      const response = await api.get(`/tafseer/external/verse/${suraNo}/${ayaNo}`, {
        params: { edition }
      });
      return {
        text: response.data.text || '',
        audio_url: response.data.audio_url,
        source: response.data.source || '',
      };
    },
    staleTime: staleTimes.tafsir,
    enabled: enabled && suraNo > 0 && ayaNo > 0,
  });
}

// =============================================================================
// Audio URL Hook
// =============================================================================

export function useVerseAudio(
  suraNo: number,
  ayaNo: number,
  reciter: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: queryKeys.quran.audio(suraNo, ayaNo, reciter),
    queryFn: async (): Promise<AudioResponse> => {
      const response = await api.get(`/quran/audio/verse/${suraNo}/${ayaNo}`, {
        params: { reciter }
      });
      return {
        audio_url: response.data.audio_url,
        reciter,
      };
    },
    staleTime: staleTimes.audio,
    enabled: enabled && suraNo > 0 && ayaNo > 0,
  });
}

// =============================================================================
// AI Summary Hook
// =============================================================================

export function useAISummary(
  tafsirText: string,
  verseText: string,
  language: string,
  enabled: boolean = false
) {
  return useQuery({
    queryKey: ['ai', 'summary', tafsirText.slice(0, 50), language],
    queryFn: async (): Promise<AIResponse> => {
      const response = await api.post('/tafseer/llm/summarize', {
        tafsir_text: tafsirText,
        verse_text: verseText,
        language,
      });
      return response.data;
    },
    staleTime: staleTimes.aiResponse,
    enabled: enabled && tafsirText.length > 0,
    retry: 1,
  });
}

// =============================================================================
// AI Word Explanation Hook
// =============================================================================

export function useWordExplanation(
  word: string,
  verseText: string,
  context: string,
  language: string,
  enabled: boolean = false
) {
  return useQuery({
    queryKey: ['ai', 'explain', word, verseText.slice(0, 30), language],
    queryFn: async (): Promise<AIResponse> => {
      const response = await api.post('/tafseer/llm/explain-word', {
        word: word.trim(),
        verse_text: verseText,
        context,
        language,
      });
      return response.data;
    },
    staleTime: staleTimes.aiResponse,
    enabled: enabled && word.trim().length > 0,
    retry: 1,
  });
}

// =============================================================================
// AI Q&A Hook
// =============================================================================

export function useAIAnswer(
  question: string,
  verseText: string,
  tafsirText: string,
  language: string,
  enabled: boolean = false
) {
  return useQuery({
    queryKey: ['ai', 'answer', question, verseText.slice(0, 30), language],
    queryFn: async (): Promise<AIResponse> => {
      const response = await api.post('/tafseer/llm/answer', {
        question: question.trim(),
        verse_text: verseText,
        tafsir_text: tafsirText,
        language,
      });
      return response.data;
    },
    staleTime: staleTimes.aiResponse,
    enabled: enabled && question.trim().length > 0,
    retry: 1,
  });
}

// =============================================================================
// Prefetch Utilities
// =============================================================================

export function usePrefetchTafsir() {
  const queryClient = useQueryClient();

  return useCallback(
    (suraNo: number, ayaNo: number, edition: string) => {
      queryClient.prefetchQuery({
        queryKey: queryKeys.tafsir.verse(suraNo, ayaNo, edition),
        queryFn: () =>
          api.get(`/tafseer/external/verse/${suraNo}/${ayaNo}`, {
            params: { edition }
          }).then(r => ({
            text: r.data.text || '',
            audio_url: r.data.audio_url,
            source: r.data.source || '',
          })),
        staleTime: staleTimes.tafsir,
      });
    },
    [queryClient]
  );
}

export function usePrefetchAudio() {
  const queryClient = useQueryClient();

  return useCallback(
    (suraNo: number, ayaNo: number, reciter: string) => {
      queryClient.prefetchQuery({
        queryKey: queryKeys.quran.audio(suraNo, ayaNo, reciter),
        queryFn: () =>
          api.get(`/quran/audio/verse/${suraNo}/${ayaNo}`, {
            params: { reciter }
          }).then(r => ({
            audio_url: r.data.audio_url,
            reciter,
          })),
        staleTime: staleTimes.audio,
      });
    },
    [queryClient]
  );
}
