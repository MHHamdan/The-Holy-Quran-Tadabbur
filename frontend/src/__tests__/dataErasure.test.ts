import { beforeEach, describe, expect, it, vi } from 'vitest';

const post = vi.fn();
const del = vi.fn();
vi.mock('../lib/api', () => ({ api: { post, delete: del } }));
vi.mock('../lib/native', () => ({ isNativeApp: false }));
vi.mock('../lib/reminders', () => ({ applyReminder: vi.fn(async () => undefined), DEFAULT_REMINDER: {} }));
vi.mock('../lib/config', () => ({ wsUrl: (p: string) => p }));
// Order log: every erasure step records itself so the test can check that the
// server deletes run before the localStorage sweep.
const calls: string[] = [];
const clearAll = vi.fn(async () => { calls.push('offlineAudio'); });
const clearPersistedQueries = vi.fn(async () => { calls.push('persistedQueries'); });
vi.mock('../lib/offlineAudio', () => ({ clearAll }));
vi.mock('../lib/queryClient', () => ({ clearPersistedQueries }));

class MemoryStorage {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? this.m.get(k)! : null; }
  setItem(k: string, v: string) { this.m.set(k, String(v)); }
  removeItem(k: string) { this.m.delete(k); }
  clear() { this.m.clear(); }
  key(i: number) { return [...this.m.keys()][i] ?? null; }
  get length() { return this.m.size; }
}

// Object.keys(localStorage) must list the stored keys, as in a browser.
function makeStorage(): Storage {
  const store = new MemoryStorage();
  return new Proxy(store, {
    ownKeys: () => [...(store as unknown as { m: Map<string, string> }).m.keys()],
    getOwnPropertyDescriptor: (_t, k) =>
      typeof k === 'string' && store.getItem(k) !== null
        ? { enumerable: true, configurable: true, value: store.getItem(k) }
        : undefined,
    get: (t, k) => {
      const v = Reflect.get(t, k, t);
      return typeof v === 'function' ? v.bind(t) : v;
    },
  }) as unknown as Storage;
}

// Same key and row shape that useTasmeeWebSocket.rememberTasmeeSession writes.
const TASMEE_KEY = 'tadabbur-tasmee-sessions';
const THERAPY_KEY = 'tadabbur_therapy_sessions';
const PENDING_KEY = 'tadabbur-erasure-pending';
const SEARCH_SID = 'sess_11111111-2222-4333-8444-555555555555';

const therapyPosts = () => post.mock.calls.filter(([url]) => url === '/therapy/sessions/delete');
const tasmeePosts = () => post.mock.calls.filter(([url]) => url === '/tasmee/sessions/delete');

function okPost(deleted = 1) {
  return async (url: string, body: { sessions: unknown[] }) => {
    calls.push(`${url === '/therapy/sessions/delete' ? 'therapy' : 'tasmee'}:${
      localStorage.getItem(url === '/therapy/sessions/delete' ? THERAPY_KEY : TASMEE_KEY) ? 'present' : 'gone'}`);
    return { data: { deleted: Math.min(deleted, body.sessions.length) } };
  };
}

beforeEach(() => {
  vi.resetModules();
  post.mockReset();
  del.mockReset();
  del.mockResolvedValue({ data: {} });
  clearAll.mockClear();
  clearPersistedQueries.mockClear();
  calls.length = 0;
  vi.stubGlobal('localStorage', makeStorage());
  vi.stubGlobal('sessionStorage', makeStorage());
  vi.stubGlobal('window', {});
});

describe('eraseAllMyData: Tasmee sessions', () => {
  it('sends {sessions:[{id,token}]} from the Tasmee key, then clears local data', async () => {
    localStorage.setItem(TASMEE_KEY, JSON.stringify([
      { id: 's1', token: 't1', createdAt: 1 },
      { id: 's2', token: 't2', createdAt: 2 },
      { id: 'bad' }, // no token: cannot be deleted, skipped
    ]));
    localStorage.setItem('tadabbur_bookmarks', '[]');
    post.mockResolvedValue({ data: { deleted: 2 } });

    const { TASMEE_SESSIONS_STORAGE_KEY } = await import('../hooks/useTasmeeWebSocket');
    expect(TASMEE_SESSIONS_STORAGE_KEY).toBe(TASMEE_KEY);
    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(post).toHaveBeenCalledTimes(1);
    expect(tasmeePosts()).toHaveLength(1);
    expect(post).toHaveBeenCalledWith('/tasmee/sessions/delete', {
      sessions: [{ id: 's1', token: 't1' }, { id: 's2', token: 't2' }],
    });
    expect(result).toEqual({ serverSessionsDeleted: 2, serverError: false, pending: [] });
    expect(localStorage.getItem(TASMEE_KEY)).toBeNull();
    expect(localStorage.getItem('tadabbur_bookmarks')).toBeNull();
    expect(clearAll).toHaveBeenCalledTimes(1);
    expect(clearPersistedQueries).toHaveBeenCalledTimes(1);
  });

  it('sends nothing when the device has no server sessions', async () => {
    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();
    expect(post).not.toHaveBeenCalled();
    expect(del).not.toHaveBeenCalled();
    expect(result.serverError).toBe(false);
    expect(localStorage.getItem(PENDING_KEY)).toBeNull();
  });

  it('reports a server error and keeps the tokens so the user can retry', async () => {
    localStorage.setItem(TASMEE_KEY, JSON.stringify([{ id: 's1', token: 't1', createdAt: 1 }]));
    localStorage.setItem('tadabbur_journal', '[]');
    post.mockRejectedValue(new Error('network'));

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(result.serverError).toBe(true);
    expect(result.pending).toEqual(['tasmee']);
    expect(localStorage.getItem(TASMEE_KEY)).not.toBeNull();
    expect(localStorage.getItem('tadabbur_journal')).toBeNull();
  });

  it('deletes server rows before clearing offline data and local storage', async () => {
    localStorage.setItem(THERAPY_KEY, JSON.stringify([{ id: 'g1', token: 'tok-g1', createdAt: Date.now() }]));
    localStorage.setItem(TASMEE_KEY, JSON.stringify([{ id: 's1', token: 't1', createdAt: 1 }]));
    post.mockImplementation(okPost());

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(calls).toEqual(['therapy:present', 'tasmee:present', 'offlineAudio', 'persistedQueries']);
    expect(therapyPosts()[0][1]).toEqual({ sessions: [{ id: 'g1', token: 'tok-g1' }] });
    expect(result).toEqual({ serverSessionsDeleted: 2, serverError: false, pending: [] });
    expect(localStorage.getItem(THERAPY_KEY)).toBeNull();
  });

  it('still clears offline data when a local cleanup step throws', async () => {
    clearAll.mockImplementationOnce(async () => { throw new Error('cache'); });
    localStorage.setItem('tadabbur_bookmarks', '[]');
    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();
    expect(clearPersistedQueries).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('tadabbur_bookmarks')).toBeNull();
    expect(result.serverError).toBe(false);
  });
});

describe('eraseAllMyData: guidance sessions', () => {
  it('deletes chat sessions and sessions beyond the 50-entry journal cap', async () => {
    const now = Date.now();
    // 60 sessions with tokens (journal shows only 50), one of them a chat session
    const keys = Array.from({ length: 60 }, (_, i) => ({ id: `g${i}`, token: `tok-${i}`, createdAt: now - i * 1000 }));
    localStorage.setItem(THERAPY_KEY, JSON.stringify(keys));
    // A legacy entry known only to the old reflections list (no token)
    localStorage.setItem('tadabbur_reflections', JSON.stringify([{ session_id: 'legacy-1', timestamp: now - 5000 }]));
    post.mockImplementation(async (_url: string, body: { sessions: unknown[] }) => ({ data: { deleted: body.sessions.length } }));

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    const sent = therapyPosts().flatMap(([, body]) => (body as { sessions: { id: string; token?: string }[] }).sessions);
    expect(sent).toHaveLength(61);
    expect(sent).toContainEqual({ id: 'g59', token: 'tok-59' });
    expect(sent).toContainEqual({ id: 'legacy-1' });
    expect(result.serverSessionsDeleted).toBe(61);
    expect(result.pending).toEqual([]);
  });

  it('keeps the guidance keys when the delete fails or the device is offline, and names them', async () => {
    localStorage.setItem(THERAPY_KEY, JSON.stringify([{ id: 'g1', token: 'tok-g1', createdAt: Date.now() }]));
    localStorage.setItem('tadabbur_reflections', JSON.stringify([{ session_id: 'g1', reflection: 'private', timestamp: Date.now() }]));
    post.mockRejectedValue(new Error('offline'));

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(result.serverError).toBe(true);
    expect(result.pending).toEqual(['guidance']);
    // Local content is gone, only the key to the server row survives
    expect(localStorage.getItem('tadabbur_reflections')).toBeNull();
    expect(localStorage.getItem(THERAPY_KEY)).toBeNull();
    const pending = JSON.parse(localStorage.getItem(PENDING_KEY)!);
    expect(pending.therapy).toEqual([expect.objectContaining({ id: 'g1', token: 'tok-g1' })]);
    expect(JSON.stringify(pending)).not.toContain('private');
  });

  it('retries the pending deletes later and clears the record when they succeed', async () => {
    localStorage.setItem(THERAPY_KEY, JSON.stringify([{ id: 'g1', token: 'tok-g1', createdAt: Date.now() }]));
    post.mockRejectedValue(new Error('offline'));
    const mod = await import('../lib/dataErasure');
    await mod.eraseAllMyData();
    expect(mod.pendingErasureParts()).toEqual(['guidance']);

    post.mockReset();
    post.mockResolvedValue({ data: { deleted: 1 } });
    const retry = await mod.retryPendingErasure();

    expect(therapyPosts()[0][1]).toEqual({ sessions: [{ id: 'g1', token: 'tok-g1' }] });
    expect(retry).toEqual({ serverSessionsDeleted: 1, serverError: false, pending: [] });
    expect(localStorage.getItem(PENDING_KEY)).toBeNull();
    expect(await mod.retryPendingErasure()).toBeNull();
  });

  it('keeps only the failed batch when one of several batches fails', async () => {
    const now = Date.now();
    const keys = Array.from({ length: 250 }, (_, i) => ({ id: `g${i}`, token: `tok-${i}`, createdAt: now - i }));
    localStorage.setItem(THERAPY_KEY, JSON.stringify(keys));
    post
      .mockResolvedValueOnce({ data: { deleted: 200 } })
      .mockRejectedValueOnce(new Error('500'));

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(result.serverSessionsDeleted).toBe(200);
    expect(JSON.parse(localStorage.getItem(PENDING_KEY)!).therapy).toHaveLength(50);
  });
});

describe('eraseAllMyData: search history and assistant conversation', () => {
  it('clears this device\'s server search history and Ask conversation', async () => {
    localStorage.setItem('tadabbur-search-history', JSON.stringify({ state: { sessionId: SEARCH_SID }, version: 1 }));
    localStorage.setItem('tadabbur_ask_session', JSON.stringify({ sessionId: 'ask-123' }));
    localStorage.setItem('prayer_settings', '{}');
    sessionStorage.setItem('anything', '1');

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(del).toHaveBeenCalledWith('/quran/history', { params: { session_id: SEARCH_SID } });
    expect(del).toHaveBeenCalledWith('/rag/sessions/ask-123');
    expect(result.pending).toEqual([]);
    expect(localStorage.getItem('tadabbur-search-history')).toBeNull();
    expect(localStorage.getItem('prayer_settings')).toBeNull();
    expect(sessionStorage.getItem('anything')).toBeNull();
  });

  it('treats an expired Ask conversation (404) as deleted, and queues a failed search delete', async () => {
    localStorage.setItem('tadabbur-search-history', JSON.stringify({ state: { sessionId: SEARCH_SID }, version: 1 }));
    localStorage.setItem('tadabbur_ask_session', JSON.stringify({ sessionId: 'ask-123' }));
    del.mockImplementation(async (url: string) => {
      if (url.startsWith('/rag/')) throw Object.assign(new Error('nf'), { response: { status: 404 } });
      throw new Error('offline');
    });

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(result.pending).toEqual(['search']);
    expect(JSON.parse(localStorage.getItem(PENDING_KEY)!).search).toEqual([SEARCH_SID]);
  });
});
