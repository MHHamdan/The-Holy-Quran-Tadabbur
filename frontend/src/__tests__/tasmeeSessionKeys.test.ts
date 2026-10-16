import { beforeEach, describe, expect, it, vi } from 'vitest';

// Every Tasmee session key from the server's 90-day window must stay on the
// device, or "Delete my data" could not reach that row. The list used to be
// capped at 200, dropping the oldest keys.
const post = vi.fn();
vi.mock('../lib/api', () => ({ api: { post } }));
vi.mock('../lib/config', () => ({ wsUrl: (p: string) => p }));

const saved = new Map<string, string>();
beforeEach(() => {
  saved.clear();
  post.mockReset();
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => saved.get(k) ?? null,
    setItem: (k: string, v: string) => { saved.set(k, String(v)); },
    removeItem: (k: string) => { saved.delete(k); },
  });
});

describe('Tasmee session keys', () => {
  it('keeps all 250 recent sessions and deletes them all in batches of 200', async () => {
    const mod = await import('../hooks/useTasmeeWebSocket');
    for (let i = 0; i < 250; i++) mod.rememberTasmeeSession(`s${i}`, `t${i}`);
    expect(mod.listTasmeeSessions()).toHaveLength(250);

    post.mockImplementation(async (_url: string, body: { sessions: unknown[] }) => ({
      data: { deleted: body.sessions.length },
    }));
    expect(await mod.deleteRememberedTasmeeSessions()).toBe(250);
    expect(post).toHaveBeenCalledTimes(2);
    expect(post.mock.calls[0][1].sessions).toHaveLength(200);
    expect(post.mock.calls[1][1].sessions).toHaveLength(50);
    expect(post.mock.calls[0][1].sessions[0]).toEqual({ id: 's0', token: 't0' });
    expect(mod.listTasmeeSessions()).toHaveLength(0);
  });

  it('still prunes keys older than 90 days', async () => {
    const mod = await import('../hooks/useTasmeeWebSocket');
    const old = Date.now() - 91 * 86_400_000;
    saved.set(mod.TASMEE_SESSIONS_STORAGE_KEY, JSON.stringify([{ id: 'old', token: 'x', createdAt: old }]));
    mod.rememberTasmeeSession('new', 'y');
    expect(mod.listTasmeeSessions().map((r) => r.id)).toEqual(['new']);
  });
});
