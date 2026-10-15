import { beforeEach, describe, expect, it, vi } from 'vitest';

const post = vi.fn();
const deleteSessions = vi.fn();
vi.mock('../lib/api', () => ({ api: { post }, therapyApi: { deleteSessions } }));
vi.mock('../lib/native', () => ({ isNativeApp: false }));
vi.mock('../lib/reminders', () => ({ applyReminder: vi.fn(async () => undefined), DEFAULT_REMINDER: {} }));

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

describe('eraseAllMyData: Tasmee sessions', () => {
  beforeEach(() => {
    post.mockReset();
    deleteSessions.mockReset();
    vi.stubGlobal('localStorage', makeStorage());
    vi.stubGlobal('window', {});
  });

  it('sends {sessions:[{id,token}]} from the Tasmee key, then clears local data', async () => {
    localStorage.setItem(TASMEE_KEY, JSON.stringify([
      { id: 's1', token: 't1', createdAt: 1 },
      { id: 's2', token: 't2', createdAt: 2 },
      { id: 'bad' }, // no token: cannot be deleted, skipped
    ]));
    localStorage.setItem('tadabbur_bookmarks', '[]');
    post.mockResolvedValue({ data: { deleted: 2 } });

    const { eraseAllMyData, TASMEE_SESSIONS_KEY } = await import('../lib/dataErasure');
    expect(TASMEE_SESSIONS_KEY).toBe(TASMEE_KEY);
    const result = await eraseAllMyData();

    expect(post).toHaveBeenCalledTimes(1);
    expect(post).toHaveBeenCalledWith('/tasmee/sessions/delete', {
      sessions: [{ id: 's1', token: 't1' }, { id: 's2', token: 't2' }],
    });
    expect(result).toEqual({ serverSessionsDeleted: 2, serverError: false });
    expect(localStorage.getItem(TASMEE_KEY)).toBeNull();
    expect(localStorage.getItem('tadabbur_bookmarks')).toBeNull();
  });

  it('sends nothing when the device has no Tasmee sessions', async () => {
    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();
    expect(post).not.toHaveBeenCalled();
    expect(result.serverError).toBe(false);
  });

  it('reports a server error and keeps the tokens so the user can retry', async () => {
    localStorage.setItem(TASMEE_KEY, JSON.stringify([{ id: 's1', token: 't1', createdAt: 1 }]));
    localStorage.setItem('tadabbur_journal', '[]');
    post.mockRejectedValue(new Error('network'));

    const { eraseAllMyData } = await import('../lib/dataErasure');
    const result = await eraseAllMyData();

    expect(result.serverError).toBe(true);
    expect(localStorage.getItem(TASMEE_KEY)).not.toBeNull();
    expect(localStorage.getItem('tadabbur_journal')).toBeNull();
  });
});
