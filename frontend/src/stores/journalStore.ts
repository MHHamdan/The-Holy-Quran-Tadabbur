/**
 * journalStore — personal Quran verse reflection journal.
 *
 * Persisted to localStorage only. No auth, no backend, no cloud.
 * Each entry links to a specific surah:ayah reference.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type JournalCategory =
  | 'reflection'
  | 'question'
  | 'memorized'
  | 'gratitude'
  | 'supplication'
  | 'study_note';

export interface JournalEntry {
  id: string;
  surah: number;
  ayah: number;
  surahNameEn: string;
  surahNameAr: string;
  category: JournalCategory;
  note: string;
  createdAt: string; // ISO date string
  updatedAt: string; // ISO date string
}

interface JournalState {
  entries: JournalEntry[];
  addEntry: (entry: Omit<JournalEntry, 'id' | 'createdAt' | 'updatedAt'>) => void;
  updateEntry: (id: string, patch: Partial<Pick<JournalEntry, 'note' | 'category'>>) => void;
  deleteEntry: (id: string) => void;
}

export const CATEGORY_META: Record<JournalCategory, { labelEn: string; labelAr: string; emoji: string; color: string }> = {
  reflection:   { labelEn: 'Reflection',   labelAr: 'تأمل',       emoji: '🌙', color: 'violet' },
  question:     { labelEn: 'Question',     labelAr: 'سؤال',       emoji: '❓', color: 'blue'   },
  memorized:    { labelEn: 'Memorized',    labelAr: 'محفوظ',      emoji: '⭐', color: 'amber'  },
  gratitude:    { labelEn: 'Gratitude',    labelAr: 'شكر',        emoji: '🤲', color: 'emerald'},
  supplication: { labelEn: 'Supplication', labelAr: 'دعاء',       emoji: '💚', color: 'green'  },
  study_note:   { labelEn: 'Study Note',   labelAr: 'ملاحظة دراسة', emoji: '📝', color: 'gray'  },
};

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export const useJournalStore = create<JournalState>()(
  persist(
    (set) => ({
      entries: [],

      addEntry: (entry) => set(state => ({
        entries: [
          {
            ...entry,
            id: newId(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
          ...state.entries,
        ],
      })),

      updateEntry: (id, patch) => set(state => ({
        entries: state.entries.map(e =>
          e.id === id ? { ...e, ...patch, updatedAt: new Date().toISOString() } : e
        ),
      })),

      deleteEntry: (id) => set(state => ({
        entries: state.entries.filter(e => e.id !== id),
      })),
    }),
    {
      name: 'tadabbur_journal_v1',
    }
  )
);
