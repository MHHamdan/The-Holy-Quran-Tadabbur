/**
 * Daily reading reminder: one repeating local notification at a chosen time.
 *
 * Native apps only (Capacitor LocalNotifications). Nothing leaves the device:
 * no push service, no server. Tapping the notification opens /continue,
 * which resumes at the last verse read.
 */
import { isNativeApp } from './native';

const REMINDER_ID = 7301;
const KEY = 'tadabbur_reading_reminder_v1';

export interface ReminderSetting {
  enabled: boolean;
  hour: number;
  minute: number;
}

export const DEFAULT_REMINDER: ReminderSetting = { enabled: false, hour: 20, minute: 0 };

export const remindersSupported = isNativeApp;

export function loadReminder(): ReminderSetting {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULT_REMINDER, ...(JSON.parse(raw) as Partial<ReminderSetting>) } : DEFAULT_REMINDER;
  } catch {
    return DEFAULT_REMINDER;
  }
}

function save(setting: ReminderSetting) {
  try { localStorage.setItem(KEY, JSON.stringify(setting)); } catch { /* storage unavailable */ }
}

export type ReminderResult = 'scheduled' | 'cancelled' | 'denied' | 'unsupported' | 'failed';

/** Apply a setting: (re)schedule or cancel. Asks for notification permission when enabling. */
export async function applyReminder(
  setting: ReminderSetting,
  text: { title: string; body: string },
): Promise<ReminderResult> {
  if (!isNativeApp) return 'unsupported';
  try {
    const { LocalNotifications } = await import('@capacitor/local-notifications');
    await LocalNotifications.cancel({ notifications: [{ id: REMINDER_ID }] });
    if (!setting.enabled) {
      save(setting);
      return 'cancelled';
    }
    let perm = await LocalNotifications.checkPermissions();
    if (perm.display !== 'granted') perm = await LocalNotifications.requestPermissions();
    if (perm.display !== 'granted') {
      save({ ...setting, enabled: false });
      return 'denied';
    }
    await LocalNotifications.schedule({
      notifications: [{
        id: REMINDER_ID,
        title: text.title,
        body: text.body,
        schedule: { on: { hour: setting.hour, minute: setting.minute }, allowWhileIdle: true },
        extra: { route: '/continue' },
      }],
    });
    save(setting);
    return 'scheduled';
  } catch {
    return 'failed';
  }
}
