/**
 * Spiritual-guidance session keys and the calls that need them.
 *
 * The server issues each guidance session (/therapy/ask, and the first turn of
 * a /therapy/chat conversation) an id plus a secret client_token, returned
 * once. The token is the only proof of ownership: reading or saving a
 * reflection, insights, a follow-up chat turn and deletion all require it.
 * This device keeps {id, token} for every session it created, pruned by age
 * (the server forgets sessions after 180 days), never by count, so "Delete my
 * data" can always reach every row the server still holds.
 *
 * Sessions created before tokens existed have only an id (from the old
 * tadabbur_reflections list); the server lets their owner delete them by id.
 */
import { api } from './api';
import type {
  ChatRequest,
  ChatResponse,
  InsightsResponse,
  ReflectionsResponse,
} from '../types/therapy';

export const THERAPY_SESSIONS_KEY = 'tadabbur_therapy_sessions';
const LEGACY_REFLECTIONS_KEY = 'tadabbur_reflections';
/** Server retention is 180 days; keep keys a little longer than that. */
export const THERAPY_KEY_MAX_AGE_MS = 200 * 24 * 60 * 60 * 1000;
/** Server-side cap on sessions per request. */
const BATCH = 200;

export interface TherapySessionKey {
  id: string;
  token?: string;
  createdAt: number;
}

export interface SessionCredential {
  id: string;
  token: string;
}

function readStored(): TherapySessionKey[] {
  try {
    const raw = JSON.parse(localStorage.getItem(THERAPY_SESSIONS_KEY) ?? '[]') as unknown;
    if (!Array.isArray(raw)) return [];
    return raw.filter((k): k is TherapySessionKey =>
      !!k && typeof (k as TherapySessionKey).id === 'string'
      && typeof (k as TherapySessionKey).createdAt === 'number');
  } catch {
    return [];
  }
}

function readLegacyIds(): TherapySessionKey[] {
  try {
    const entries = JSON.parse(localStorage.getItem(LEGACY_REFLECTIONS_KEY) ?? '[]') as
      { session_id?: string; timestamp?: number }[];
    if (!Array.isArray(entries)) return [];
    return entries
      .filter((e) => typeof e?.session_id === 'string' && !!e.session_id)
      .map((e) => ({ id: e.session_id as string, createdAt: typeof e.timestamp === 'number' ? e.timestamp : Date.now() }));
  } catch {
    return [];
  }
}

function write(keys: TherapySessionKey[]): void {
  try {
    localStorage.setItem(THERAPY_SESSIONS_KEY, JSON.stringify(keys));
  } catch { /* storage unavailable */ }
}

/**
 * Every session key this device holds, newest first: the stored keys plus any
 * id only the old reflections list knows, minus entries older than the
 * server's retention.
 */
export function rememberedTherapySessions(now = Date.now()): TherapySessionKey[] {
  const byId = new Map<string, TherapySessionKey>();
  for (const k of [...readLegacyIds(), ...readStored()]) {
    const prev = byId.get(k.id);
    byId.set(k.id, { ...prev, ...k, token: k.token ?? prev?.token });
  }
  return [...byId.values()]
    .filter((k) => now - k.createdAt < THERAPY_KEY_MAX_AGE_MS)
    .sort((a, b) => b.createdAt - a.createdAt);
}

export function rememberTherapySession(id: string, token?: string | null): void {
  if (!id) return;
  const keys = rememberedTherapySessions().filter((k) => k.id !== id);
  const prev = readStored().find((k) => k.id === id);
  write([{ id, token: token ?? prev?.token, createdAt: prev?.createdAt ?? Date.now() }, ...keys]);
}

export function forgetTherapySessions(ids: string[]): void {
  const drop = new Set(ids);
  write(rememberedTherapySessions().filter((k) => !drop.has(k.id)));
}

/** {id, token} for these ids (or all), newest first; sessions without a token are skipped. */
export function credentialsFor(ids?: string[]): SessionCredential[] {
  const want = ids ? new Set(ids) : null;
  return rememberedTherapySessions()
    .filter((k) => !!k.token && (!want || want.has(k.id)))
    .map((k) => ({ id: k.id, token: k.token as string }));
}

/** The token issued with this session, if this device has it. */
export function tokenFor(id: string): string | undefined {
  return rememberedTherapySessions().find((k) => k.id === id)?.token;
}

// ---------------------------------------------------------------------------
// API calls that carry the token
// ---------------------------------------------------------------------------

export async function saveReflection(sessionId: string, reflection: string): Promise<void> {
  const token = tokenFor(sessionId);
  if (!token) throw new Error('no session token');
  await api.post('/therapy/reflect', { session_id: sessionId, token, reflection });
}

export async function fetchReflections(ids?: string[]): Promise<ReflectionsResponse> {
  const sessions = credentialsFor(ids).slice(0, BATCH);
  if (sessions.length === 0) return { ok: true, reflections: [] };
  return (await api.post<ReflectionsResponse>('/therapy/reflections', { sessions })).data;
}

export async function fetchInsights(ids: string[] | undefined, language: string): Promise<InsightsResponse | null> {
  const sessions = credentialsFor(ids).slice(0, BATCH);
  if (sessions.length === 0) return null;
  return (await api.post<InsightsResponse>('/therapy/insights', { sessions, language })).data;
}

export type ChatTurnRequest = ChatRequest & { session_token?: string };
export type ChatTurnResponse = ChatResponse & { client_token?: string | null };

/** One chat turn. A response carrying client_token started a new session; it is remembered here. */
export async function chatTurn(body: ChatTurnRequest): Promise<ChatTurnResponse> {
  const data = (await api.post<ChatTurnResponse>('/therapy/chat', body)).data;
  if (data.client_token) rememberTherapySession(data.session_id, data.client_token);
  return data;
}

/**
 * Delete these sessions on the server, 200 per request. Resolves with the
 * number deleted; rejects with the keys that could not be sent (so a caller
 * can keep them for a retry).
 */
export async function deleteTherapySessions(keys: TherapySessionKey[]): Promise<number> {
  let deleted = 0;
  const failed: TherapySessionKey[] = [];
  for (let i = 0; i < keys.length; i += BATCH) {
    const batch = keys.slice(i, i + BATCH);
    try {
      const sessions = batch.map((k) => (k.token ? { id: k.id, token: k.token } : { id: k.id }));
      deleted += (await api.post<{ deleted: number }>('/therapy/sessions/delete', { sessions })).data.deleted;
    } catch {
      failed.push(...batch);
    }
  }
  if (failed.length > 0) throw new TherapyDeleteError(failed, deleted);
  return deleted;
}

export class TherapyDeleteError extends Error {
  constructor(public readonly remaining: TherapySessionKey[], public readonly deleted: number) {
    super('therapy session delete failed');
  }
}
