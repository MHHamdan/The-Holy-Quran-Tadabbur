import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface BookmarkedVerse {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  text_uthmani: string;
  bookmarked_at: string;
  note?: string;
}

interface BookmarksState {
  bookmarks: BookmarkedVerse[];
  addBookmark: (verse: Omit<BookmarkedVerse, 'bookmarked_at'>) => void;
  removeBookmark: (verseId: number) => void;
  isBookmarked: (verseId: number) => boolean;
  updateNote: (verseId: number, note: string) => void;
  clearAll: () => void;
}

export const useBookmarksStore = create<BookmarksState>()(
  persist(
    (set, get) => ({
      bookmarks: [],

      addBookmark: (verse) => {
        if (get().isBookmarked(verse.id)) return;
        set((state) => ({
          bookmarks: [
            { ...verse, bookmarked_at: new Date().toISOString() },
            ...state.bookmarks,
          ],
        }));
      },

      removeBookmark: (verseId) => {
        set((state) => ({
          bookmarks: state.bookmarks.filter((b) => b.id !== verseId),
        }));
      },

      isBookmarked: (verseId) => {
        return get().bookmarks.some((b) => b.id === verseId);
      },

      updateNote: (verseId, note) => {
        set((state) => ({
          bookmarks: state.bookmarks.map((b) =>
            b.id === verseId ? { ...b, note } : b
          ),
        }));
      },

      clearAll: () => set({ bookmarks: [] }),
    }),
    { name: 'tadabbur-bookmarks' }
  )
);
