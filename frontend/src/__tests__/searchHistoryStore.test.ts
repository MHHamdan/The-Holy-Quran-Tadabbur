import { describe, expect, it, vi } from 'vitest';

// /privacy says the app keeps no list of searches on the device or the
// server: recording a search must not call the history endpoints and must not
// put the query into persisted storage.
const recordSearch = vi.fn();
const recordVerseClick = vi.fn();
vi.mock('../lib/api', () => ({ quranApi: { recordSearch, recordVerseClick } }));

const saved = new Map<string, string>();
vi.stubGlobal('localStorage', {
  getItem: (k: string) => saved.get(k) ?? null,
  setItem: (k: string, v: string) => { saved.set(k, String(v)); },
  removeItem: (k: string) => { saved.delete(k); },
  clear: () => saved.clear(),
  key: () => null,
  length: 0,
});

describe('searchHistoryStore', () => {
  it('records searches in memory only', async () => {
    const { useSearchHistoryStore } = await import('../stores/searchHistoryStore');
    await useSearchHistoryStore.getState().recordSearch('patience', 'text', 12);
    await useSearchHistoryStore.getState().recordVerseClick(2, 153);

    expect(recordSearch).not.toHaveBeenCalled();
    expect(recordVerseClick).not.toHaveBeenCalled();
    expect(useSearchHistoryStore.getState().recentSearches[0].query).toBe('patience');

    const persisted = saved.get('tadabbur-search-history') ?? '';
    expect(persisted).not.toContain('patience');
    // The session id stays persisted so "Delete my data" can still clear a
    // server copy recorded by earlier builds.
    expect(persisted).toMatch(/sess_[0-9a-f-]{36}/);
  });
});
