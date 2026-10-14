/**
 * "Delete my data": erase everything Tadabbur keeps for this person.
 *
 * There are no accounts, so the device holds the only keys. In order:
 *  1. server copies of guidance sessions / saved reflections (by the session
 *     ids this device created)
 *  2. offline recitation files
 *  3. the scheduled reading reminder
 *  4. every tadabbur* entry in local storage (bookmarks, journal, progress,
 *     settings, flashcards, search history...)
 */
import { therapyApi } from './api';
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
      .filter((k) => k.startsWith('tadabbur'))
      .forEach((k) => localStorage.removeItem(k));
  } catch { /* storage unavailable */ }

  return { serverSessionsDeleted, serverError };
}
