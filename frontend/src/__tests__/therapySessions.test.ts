import { beforeEach, describe, expect, it, vi } from 'vitest';

const post = vi.fn();
vi.mock('../lib/api', () => ({ api: { post } }));

class MemoryStorage {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? this.m.get(k)! : null; }
  setItem(k: string, v: string) { this.m.set(k, String(v)); }
  removeItem(k: string) { this.m.delete(k); }
  clear() { this.m.clear(); }
}

const KEY = 'tadabbur_therapy_sessions';
const DAY = 24 * 60 * 60 * 1000;

beforeEach(() => {
  vi.resetModules();
  post.mockReset();
  vi.stubGlobal('localStorage', new MemoryStorage());
});

describe('therapy session keys', () => {
  it('keeps every key regardless of count and prunes only by age', async () => {
    const now = Date.now();
    const keys = Array.from({ length: 120 }, (_, i) => ({ id: `g${i}`, token: `t${i}`, createdAt: now - i * 1000 }));
    keys.push({ id: 'old', token: 'x', createdAt: now - 201 * DAY });
    localStorage.setItem(KEY, JSON.stringify(keys));
    const { rememberedTherapySessions } = await import('../lib/therapySessions');
    const got = rememberedTherapySessions(now);
    expect(got).toHaveLength(120);
    expect(got.map((k) => k.id)).not.toContain('old');
  });

  it('merges ids only the old reflections list knows (no token) and keeps tokens', async () => {
    localStorage.setItem(KEY, JSON.stringify([{ id: 'a', token: 'ta', createdAt: Date.now() }]));
    localStorage.setItem('tadabbur_reflections', JSON.stringify([
      { session_id: 'a', timestamp: Date.now() - 10 },
      { session_id: 'legacy', timestamp: Date.now() - 20 },
    ]));
    const { rememberedTherapySessions, credentialsFor } = await import('../lib/therapySessions');
    expect(rememberedTherapySessions().map((k) => [k.id, k.token])).toEqual([['a', 'ta'], ['legacy', undefined]]);
    expect(credentialsFor()).toEqual([{ id: 'a', token: 'ta' }]);
  });

  it('chatTurn stores the key of a new conversation and sends the token on follow-ups', async () => {
    post.mockResolvedValueOnce({ data: { session_id: 'c1', client_token: 'tok-c1', answer: '' } });
    const { chatTurn, tokenFor } = await import('../lib/therapySessions');
    await chatTurn({ message: 'I feel anxious today', language: 'en' });
    expect(tokenFor('c1')).toBe('tok-c1');

    post.mockResolvedValueOnce({ data: { session_id: 'c1', client_token: null, answer: '' } });
    await chatTurn({ message: 'and more', language: 'en', session_id: 'c1', session_token: 'tok-c1' });
    expect(post).toHaveBeenLastCalledWith('/therapy/chat', expect.objectContaining({ session_id: 'c1', session_token: 'tok-c1' }));
    expect(JSON.parse(localStorage.getItem(KEY)!)).toHaveLength(1);
  });

  it('saveReflection and fetchReflections send the token', async () => {
    localStorage.setItem(KEY, JSON.stringify([{ id: 'a', token: 'ta', createdAt: Date.now() }]));
    post.mockResolvedValue({ data: { ok: true, reflections: [] } });
    const { saveReflection, fetchReflections } = await import('../lib/therapySessions');
    await saveReflection('a', 'note');
    expect(post).toHaveBeenCalledWith('/therapy/reflect', { session_id: 'a', token: 'ta', reflection: 'note' });
    await fetchReflections(['a', 'unknown']);
    expect(post).toHaveBeenLastCalledWith('/therapy/reflections', { sessions: [{ id: 'a', token: 'ta' }] });
    await expect(saveReflection('unknown', 'note')).rejects.toThrow();
  });
});
