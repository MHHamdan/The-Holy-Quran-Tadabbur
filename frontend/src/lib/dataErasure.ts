/**
 * "Delete my data": erase everything Tadabbur keeps for this person.
 *
 * There are no accounts, so the device holds the only keys. In order:
 *  1. server copies of guidance sessions and saved reflections (/ask and
 *     /chat), by the {id, token} keys in lib/therapySessions — every session
 *     the server may still hold, not only the 50 shown in the journal
 *  2. server Tasmeeʿ sessions (recognised words and mistakes) this device
 *     created — deleteRememberedTasmeeSessions() from useTasmeeWebSocket, which
 *     owns the id/token list
 *  3. this device's recent searches held in server memory (DELETE /quran/history)
 *  4. this device's AI-assistant conversation (DELETE /rag/sessions/{id};
 *     it would otherwise expire after 24 hours)
 *  5. offline recitation files (offlineAudio.clearAll)
 *  6. the offline Qur'an copy, i.e. the persisted query cache
 *     (queryClient.clearPersistedQueries)
 *  7. the scheduled reading reminder
 *  8. every app entry in local and session storage
 *
 * Server deletes (1-4) must run before the storage sweep (8): the sweep would
 * otherwise erase the only record of the ids and tokens they need.
 *
 * A server delete that fails (offline, server down) is not forgotten: its keys
 * go into a small pending-erasure record written after the sweep, and
 * retryPendingErasure() sends them again on the next launch or when the
 * device comes back online. The result says which parts are still pending.
 */
import { api } from './api';
import { isNativeApp } from './native';
import { applyReminder, DEFAULT_REMINDER } from './reminders';
import { clearAll as clearOfflineAudio } from './offlineAudio';
import { clearPersistedQueries } from './queryClient';
import {
  deleteRememberedTasmeeSessions,
  TASMEE_SESSIONS_STORAGE_KEY,
} from '../hooks/useTasmeeWebSocket';
import {
  deleteTherapySessions,
  rememberedTherapySessions,
  TherapyDeleteError,
  type TherapySessionKey,
} from './therapySessions';

export const PENDING_ERASURE_KEY = 'tadabbur-erasure-pending';
const SEARCH_HISTORY_KEY = 'tadabbur-search-history';
const ASK_SESSION_KEY = 'tadabbur_ask_session';
/** Non-personal settings stored outside the tadabbur* prefix. */
const OTHER_PREFIXES = ['zakat_', 'prayer_settings', 'hijri-calendar-position', 'islamic-books-filters'];

export type ErasurePart = 'guidance' | 'tasmee' | 'search' | 'assistant';

interface PendingErasure {
  therapy: TherapySessionKey[];
  tasmee: boolean;
  search: string[];
  ask: string[];
  since: number;
}

export interface ErasureResult {
  serverSessionsDeleted: number;
  /** True when any server part could not be deleted yet. */
  serverError: boolean;
  /** The server parts still to delete; they are retried automatically. */
  pending: ErasurePart[];
}

function readJson<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function searchSessionId(): string | null {
  const v = readJson<{ state?: { sessionId?: string } }>(SEARCH_HISTORY_KEY);
  return typeof v?.state?.sessionId === 'string' ? v.state.sessionId : null;
}

function askSessionId(): string | null {
  const v = readJson<{ sessionId?: string }>(ASK_SESSION_KEY);
  return typeof v?.sessionId === 'string' ? v.sessionId : null;
}

function readPending(): PendingErasure | null {
  const p = readJson<Partial<PendingErasure>>(PENDING_ERASURE_KEY);
  if (!p) return null;
  return {
    therapy: Array.isArray(p.therapy) ? p.therapy : [],
    tasmee: p.tasmee === true,
    search: Array.isArray(p.search) ? p.search : [],
    ask: Array.isArray(p.ask) ? p.ask : [],
    since: typeof p.since === 'number' ? p.since : Date.now(),
  };
}

function writePending(p: PendingErasure): void {
  try {
    if (p.therapy.length || p.tasmee || p.search.length || p.ask.length) {
      localStorage.setItem(PENDING_ERASURE_KEY, JSON.stringify(p));
    } else {
      localStorage.removeItem(PENDING_ERASURE_KEY);
    }
  } catch { /* storage unavailable */ }
}

function isNotFound(err: unknown): boolean {
  return (err as { response?: { status?: number } })?.response?.status === 404;
}

/** Send every server delete in `work`; returns what is still pending. */
async function runServerDeletes(work: PendingErasure): Promise<{ deleted: number; left: PendingErasure }> {
  let deleted = 0;
  const left: PendingErasure = { therapy: [], tasmee: false, search: [], ask: [], since: work.since };

  if (work.therapy.length) {
    try {
      deleted += await deleteTherapySessions(work.therapy);
    } catch (err) {
      if (err instanceof TherapyDeleteError) {
        deleted += err.deleted;
        left.therapy = err.remaining;
      } else {
        left.therapy = work.therapy;
      }
    }
  }

  if (work.tasmee) {
    try {
      deleted += await deleteRememberedTasmeeSessions();
    } catch {
      left.tasmee = true; // the Tasmeeʿ key list is kept for the retry
    }
  }

  for (const sid of work.search) {
    try {
      await api.delete('/quran/history', { params: { session_id: sid } });
    } catch (err) {
      if (!isNotFound(err)) left.search.push(sid);
    }
  }

  for (const sid of work.ask) {
    try {
      await api.delete(`/rag/sessions/${encodeURIComponent(sid)}`);
    } catch (err) {
      if (!isNotFound(err)) left.ask.push(sid); // 404: already expired
    }
  }

  return { deleted, left };
}

function pendingParts(p: PendingErasure): ErasurePart[] {
  const parts: ErasurePart[] = [];
  if (p.therapy.length) parts.push('guidance');
  if (p.tasmee) parts.push('tasmee');
  if (p.search.length) parts.push('search');
  if (p.ask.length) parts.push('assistant');
  return parts;
}

export async function eraseAllMyData(): Promise<ErasureResult> {
  const earlier = readPending();
  const therapyKeys = new Map<string, TherapySessionKey>();
  for (const k of [...(earlier?.therapy ?? []), ...rememberedTherapySessions()]) therapyKeys.set(k.id, k);
  const search = searchSessionId();
  const ask = askSessionId();

  const work: PendingErasure = {
    therapy: [...therapyKeys.values()],
    tasmee: true,
    search: [...new Set([...(earlier?.search ?? []), ...(search ? [search] : [])])],
    ask: [...new Set([...(earlier?.ask ?? []), ...(ask ? [ask] : [])])],
    since: earlier?.since ?? Date.now(),
  };
  const { deleted, left } = await runServerDeletes(work);

  try {
    await clearOfflineAudio();
  } catch { /* nothing saved */ }

  // Native builds also kept recitations under Data/audio before offlineAudio
  // moved them; remove that directory too (no-op when it does not exist).
  if (isNativeApp) {
    try {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      await Filesystem.rmdir({ path: 'audio', directory: Directory.Data, recursive: true }).catch(() => undefined);
    } catch { /* plugin unavailable */ }
  }

  try {
    await clearPersistedQueries();
  } catch { /* IndexedDB unavailable */ }

  await applyReminder({ ...DEFAULT_REMINDER, enabled: false }, { title: '', body: '' }).catch(() => undefined);

  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith('tadabbur') || OTHER_PREFIXES.some((p) => k.startsWith(p)))
      .filter((k) => !(left.tasmee && k === TASMEE_SESSIONS_STORAGE_KEY))
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* storage unavailable */ }
  try {
    sessionStorage.clear();
  } catch { /* storage unavailable */ }

  // Written after the sweep: the only copy of the keys still to delete.
  writePending(left);

  const pending = pendingParts(left);
  return { serverSessionsDeleted: deleted, serverError: pending.length > 0, pending };
}

/**
 * Retry server deletes left over from an earlier "Delete my data". Returns
 * null when nothing is pending.
 */
export async function retryPendingErasure(): Promise<ErasureResult | null> {
  const pendingBefore = readPending();
  if (!pendingBefore) return null;
  const { deleted, left } = await runServerDeletes(pendingBefore);
  writePending(left);
  const pending = pendingParts(left);
  return { serverSessionsDeleted: deleted, serverError: pending.length > 0, pending };
}

export function hasPendingErasure(): boolean {
  return readPending() !== null;
}

/** The server parts a previous "Delete my data" has not deleted yet. */
export function pendingErasureParts(): ErasurePart[] {
  const p = readPending();
  return p ? pendingParts(p) : [];
}

let retryWired = false;
let retrying: Promise<unknown> | null = null;

function retryNow(): void {
  if (retrying || !hasPendingErasure()) return;
  retrying = retryPendingErasure().catch(() => null).finally(() => { retrying = null; });
}

/**
 * Retry pending server deletes now and whenever the device comes back
 * online. Safe to call more than once (call it at app start).
 */
export function startPendingErasureRetry(): void {
  retryNow();
  if (retryWired || typeof window === 'undefined' || typeof window.addEventListener !== 'function') return;
  retryWired = true;
  window.addEventListener('online', retryNow);
}
