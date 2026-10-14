/**
 * Spaced repetition for verse memorisation (SM-2 family, as used by Anki and
 * Quran Companion). Pure scheduling functions plus a localStorage store.
 *
 * A card is one verse ("surah:ayah"). Grades: again (forgot), hard, good,
 * easy. Intervals are whole days; a card is due when its due date is today or
 * earlier.
 */

export type Grade = 'again' | 'hard' | 'good' | 'easy';

export interface CardState {
  ease: number;      // 1.3 .. 3.0
  interval: number;  // days until the next review (0 = again today)
  reps: number;      // successful reviews in a row
  lapses: number;    // times forgotten
  due: string;       // YYYY-MM-DD
}

const STORAGE_KEY = 'tadabbur_srs_v1';
const LEGACY_KEY = 'tadabbur_flashcards_v1';
const MIN_EASE = 1.3;
const MAX_EASE = 3.0;

export function today(now = new Date()): string {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function addDays(day: string, n: number): string {
  const [y, m, d] = day.split('-').map(Number);
  return today(new Date(y, m - 1, d + n));
}

export function newCard(day = today()): CardState {
  return { ease: 2.5, interval: 0, reps: 0, lapses: 0, due: day };
}

const clampEase = (e: number) => Math.min(MAX_EASE, Math.max(MIN_EASE, Math.round(e * 100) / 100));

/** The next state after a review graded `grade` on `day`. */
export function review(card: CardState, grade: Grade, day = today()): CardState {
  if (grade === 'again') {
    return { ease: clampEase(card.ease - 0.2), interval: 0, reps: 0, lapses: card.lapses + 1, due: day };
  }
  const good = card.reps === 0 ? 1 : card.reps === 1 ? 3 : Math.round(card.interval * card.ease);
  let interval: number;
  let ease = card.ease;
  if (grade === 'hard') {
    interval = Math.max(1, Math.round(card.interval * 1.2));
    ease -= 0.15;
  } else if (grade === 'good') {
    interval = good;
  } else {
    // Always at least a day longer than "good"
    interval = card.reps === 0 ? 3 : Math.max(good + 1, Math.round(good * 1.3));
    ease += 0.15;
  }
  interval = Math.max(1, interval);
  return { ease: clampEase(ease), interval, reps: card.reps + 1, lapses: card.lapses, due: addDays(day, interval) };
}

/** Days until the next review for each grade, for labelling the buttons. */
export function previewIntervals(card: CardState): Record<Grade, number> {
  return {
    again: 0,
    hard: review(card, 'hard').interval,
    good: review(card, 'good').interval,
    easy: review(card, 'easy').interval,
  };
}

export const isDue = (card: CardState, day = today()) => card.due <= day;

export type Deck = Record<string, CardState>;

export const cardKey = (surah: number, ayah: number) => `${surah}:${ayah}`;

export function parseKey(key: string): { surah: number; ayah: number } {
  const [surah, ayah] = key.split(':').map(Number);
  return { surah, ayah };
}

/**
 * Load the deck. The first time, verses marked "mastered" in the old
 * flashcards are carried over as known cards due for review in a week, so no
 * progress is lost.
 */
export function loadDeck(): Deck {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Deck;
    const legacy = localStorage.getItem(LEGACY_KEY);
    if (legacy) {
      const { mastered = [] } = JSON.parse(legacy) as { mastered?: string[] };
      const day = today();
      const deck: Deck = Object.fromEntries(mastered.map((k) => [
        k, { ease: 2.5, interval: 7, reps: 2, lapses: 0, due: addDays(day, 7) },
      ]));
      saveDeck(deck);
      return deck;
    }
  } catch { /* storage unavailable */ }
  return {};
}

export function saveDeck(deck: Deck) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(deck)); } catch { /* storage unavailable */ }
}
