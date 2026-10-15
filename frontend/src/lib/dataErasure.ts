/**
 * "Delete my data": erase everything Tadabbur keeps for this person.
 *
 * There are no accounts, so the device holds the only keys. In order:
 *  1. server copies of guidance sessions / saved reflections (by the session
 *     ids this device created)
 *  1b. server Tasmeeʿ sessions (recognised words and mistakes) this device
 *     created, listed in localStorage under TASMEE_SESSIONS_KEY by TasmeePage
 *  2. offline recitation files
 *  3. the scheduled reading reminder
 *  4. every tadabbur* entry in local storage (bookmarks, journal, progress,
 *     settings, flashcards, search history...)
 */
import { therapyApi } from './api';
import { apiUrl } from './config';
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

/** localStorage key where TasmeePage records the sessions this device created:
 *  a JSON array of { id, token? } (or plain id strings). */
export const TASMEE_SESSIONS_KEY = 'tadabbur_tasmee_sessions';

interface StoredTasmeeSession { id: string; token?: string }

export function tasmeeSessions(): StoredTasmeeSession[] {
  try {
    const raw = JSON.parse(localStorage.getItem(TASMEE_SESSIONS_KEY) ?? '[]') as unknown;
    if (!Array.isArray(raw)) return [];
    return raw
      .map((e): StoredTasmeeSession | null => {
        if (typeof e === 'string' || typeof e === 'number') return { id: String(e) };
        if (e && typeof e === 'object' && 'id' in e) {
          const o = e as { id: unknown; token?: unknown };
          return { id: String(o.id), token: typeof o.token === 'string' ? o.token : undefined };
        }
        return null;
      })
      .filter((e): e is StoredTasmeeSession => !!e && !!e.id);
  } catch {
    return [];
  }
}

async function deleteTasmeeSessions(sessions: StoredTasmeeSession[]): Promise<number> {
  const res = await fetch(apiUrl('/api/v1/tasmee/sessions/delete'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_ids: sessions.map((s) => s.id),
      client_tokens: sessions.map((s) => s.token ?? null),
    }),
  });
  if (!res.ok) throw new Error(`tasmee delete failed: ${res.status}`);
  const data = (await res.json().catch(() => ({}))) as { deleted?: number };
  return data.deleted ?? 0;
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

  const tasmee = tasmeeSessions();
  for (let i = 0; i < tasmee.length; i += 200) {
    try {
      serverSessionsDeleted += await deleteTasmeeSessions(tasmee.slice(i, i + 200));
    } catch {
      serverError = true;
    }
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
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* storage unavailable */ }

  return { serverSessionsDeleted, serverError };
}
