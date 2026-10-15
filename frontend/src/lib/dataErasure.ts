/**
 * "Delete my data": erase everything Tadabbur keeps for this person.
 *
 * There are no accounts, so the device holds the only keys. In order:
 *  1. server copies of guidance sessions / saved reflections (by the session
 *     ids this device created)
 *  1b. server Tasmeeʿ sessions (recognised words and mistakes) this device
 *     created, listed in localStorage under TASMEE_SESSIONS_KEY by useTasmeeWebSocket
 *  2. offline recitation files
 *  3. the scheduled reading reminder
 *  4. every tadabbur* entry in local storage (bookmarks, journal, progress,
 *     settings, flashcards, search history...)
 */
import { api, therapyApi } from './api';
import { isNativeApp } from './native';
import { applyReminder, DEFAULT_REMINDER } from './reminders';

function guidanceSessionIds(): string[] {
  try {
    const entries = JSON.parse(localStorage.getItem('tadabbur_reflections') ?? '[]') as { session_id?: string }[];
    return entries.map((e) => e.session_id).filter((id): id is string => !!id);
  } catch {
    return [];
  }
}

/** localStorage key where useTasmeeWebSocket (rememberTasmeeSession) records
 *  the Tasmeeʿ sessions this device created: a JSON array of
 *  { id, token, createdAt }. Must stay identical to TASMEE_SESSIONS_STORAGE_KEY
 *  in hooks/useTasmeeWebSocket.ts. */
export const TASMEE_SESSIONS_KEY = 'tadabbur-tasmee-sessions';

export interface StoredTasmeeSession { id: string; token: string }

export function tasmeeSessions(): StoredTasmeeSession[] {
  try {
    const raw = JSON.parse(localStorage.getItem(TASMEE_SESSIONS_KEY) ?? '[]') as unknown;
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((r): r is { id: string; token: string } =>
        !!r && typeof r === 'object' && typeof (r as { id?: unknown }).id === 'string'
        && typeof (r as { token?: unknown }).token === 'string')
      .map(({ id, token }) => ({ id, token }));
  } catch {
    return [];
  }
}

/** POST /tasmee/sessions/delete with { sessions: [{ id, token }] } in batches
 *  of 200 (the server's limit), then forget the list locally. Throws if any
 *  batch fails, leaving the list in place so the user can retry. */
export async function deleteTasmeeSessions(): Promise<number> {
  const rows = tasmeeSessions();
  let deleted = 0;
  for (let i = 0; i < rows.length; i += 200) {
    const res = await api.post<{ deleted: number }>('/tasmee/sessions/delete', { sessions: rows.slice(i, i + 200) });
    deleted += res.data?.deleted ?? 0;
  }
  try { localStorage.removeItem(TASMEE_SESSIONS_KEY); } catch { /* storage unavailable */ }
  return deleted;
}

export interface ErasureResult {
  serverSessionsDeleted: number;
  serverError: boolean;
}

export async function eraseAllMyData(): Promise<ErasureResult> {
  let serverSessionsDeleted = 0;
  let serverError = false;
  const ids = guidanceSessionIds();
  for (let i = 0; i < ids.length; i += 200) {
    try {
      serverSessionsDeleted += (await therapyApi.deleteSessions(ids.slice(i, i + 200))).deleted;
    } catch {
      serverError = true;
    }
  }

  // Must run before the localStorage sweep below, which would otherwise erase
  // the only record of the tokens needed to delete these server rows.
  let keepTasmeeTokens = false;
  try {
    serverSessionsDeleted += await deleteTasmeeSessions();
  } catch {
    serverError = true;
    keepTasmeeTokens = true; // keep the tokens so "Delete my data" can be retried
  }

  try {
    if (isNativeApp) {
      const { Filesystem, Directory } = await import('@capacitor/filesystem');
      await Filesystem.rmdir({ path: 'audio', directory: Directory.Data, recursive: true }).catch(() => undefined);
    } else if ('caches' in window) {
      await caches.delete('tadabbur-audio-v1');
    }
  } catch { /* nothing saved */ }

  await applyReminder({ ...DEFAULT_REMINDER, enabled: false }, { title: '', body: '' }).catch(() => undefined);

  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith('tadabbur') || k.startsWith('zakat_'))
      .filter((k) => !(keepTasmeeTokens && k === TASMEE_SESSIONS_KEY))
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* storage unavailable */ }

  return { serverSessionsDeleted, serverError };
}
