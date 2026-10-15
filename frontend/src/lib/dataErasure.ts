/**
 * "Delete my data": erase everything Tadabbur keeps for this person.
 *
 * There are no accounts, so the device holds the only keys. In order:
 *  1. server copies of guidance sessions / saved reflections (by the session
 *     ids this device created)
 *  2. server Tasmeeʿ sessions (recognised words and mistakes) this device
 *     created — deleteRememberedTasmeeSessions() from useTasmeeWebSocket, which
 *     owns the id/token list
 *  3. offline recitation files (offlineAudio.clearAll)
 *  4. the offline Qur'an copy, i.e. the persisted query cache
 *     (queryClient.clearPersistedQueries)
 *  5. the scheduled reading reminder
 *  6. every tadabbur* entry in local storage (bookmarks, journal, progress,
 *     settings, flashcards, search history...)
 *
 * Server deletes (1, 2) must run before the localStorage sweep (6): the sweep
 * would otherwise erase the only record of the ids and tokens they need.
 */
import { therapyApi } from './api';
import { isNativeApp } from './native';
import { applyReminder, DEFAULT_REMINDER } from './reminders';
import { clearAll as clearOfflineAudio } from './offlineAudio';
import { clearPersistedQueries } from './queryClient';
import {
  deleteRememberedTasmeeSessions,
  TASMEE_SESSIONS_STORAGE_KEY,
} from '../hooks/useTasmeeWebSocket';

function guidanceSessionIds(): string[] {
  try {
    const entries = JSON.parse(localStorage.getItem('tadabbur_reflections') ?? '[]') as { session_id?: string }[];
    return entries.map((e) => e.session_id).filter((id): id is string => !!id);
  } catch {
    return [];
  }
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

  let keepTasmeeTokens = false;
  try {
    serverSessionsDeleted += await deleteRememberedTasmeeSessions();
  } catch {
    serverError = true;
    keepTasmeeTokens = true; // keep the tokens so "Delete my data" can be retried
  }

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
      .filter((k) => k.startsWith('tadabbur') || k.startsWith('zakat_'))
      .filter((k) => !(keepTasmeeTokens && k === TASMEE_SESSIONS_STORAGE_KEY))
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* storage unavailable */ }

  return { serverSessionsDeleted, serverError };
}
