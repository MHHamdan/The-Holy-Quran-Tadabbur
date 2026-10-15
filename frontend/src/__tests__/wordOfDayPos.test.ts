import { describe, expect, it } from 'vitest';
import { POS_AR } from '../components/home/WordOfDayCard';
import { WORD_OF_DAY_VOCAB } from '../data/wordOfDayVocab';

describe('Word of the day part-of-speech labels', () => {
  it('every part of speech has an Arabic label (no English tag in the Arabic UI)', () => {
    const missing = [...new Set(WORD_OF_DAY_VOCAB.map((w) => w.partOfSpeech))].filter((p) => !POS_AR[p]);
    expect(missing).toEqual([]);
  });
});
