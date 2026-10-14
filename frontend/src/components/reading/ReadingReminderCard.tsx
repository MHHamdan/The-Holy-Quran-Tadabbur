/**
 * Daily reading reminder toggle and time picker (native apps).
 */
import { useState } from 'react';
import clsx from 'clsx';
import { Bell, BellOff } from 'lucide-react';
import {
  applyReminder,
  loadReminder,
  remindersSupported,
  type ReminderResult,
  type ReminderSetting,
} from '../../lib/reminders';
import type { Language } from '../../i18n/translations';

const pad = (n: number) => n.toString().padStart(2, '0');

export function ReadingReminderCard({ language }: { language: Language }) {
  const ar = language === 'ar';
  const [setting, setSetting] = useState<ReminderSetting>(loadReminder);
  const [status, setStatus] = useState<ReminderResult | null>(null);
  const [busy, setBusy] = useState(false);

  const text = {
    title: ar ? 'وِردك اليومي' : 'Your daily reading',
    body: ar ? 'حان وقت وِردك من القرآن الكريم. تابع من حيث توقفت.' : 'Time for your Quran reading. Continue where you left off.',
  };

  async function update(next: ReminderSetting) {
    setBusy(true);
    const result = await applyReminder(next, text);
    setStatus(result);
    setSetting(result === 'denied' ? { ...next, enabled: false } : next);
    setBusy(false);
  }

  const messages: Partial<Record<ReminderResult, { ar: string; en: string; tone: string }>> = {
    scheduled: {
      ar: `سيصلك التذكير كل يوم الساعة ${pad(setting.hour)}:${pad(setting.minute)}`,
      en: `You'll be reminded every day at ${pad(setting.hour)}:${pad(setting.minute)}`,
      tone: 'text-emerald-700',
    },
    cancelled: { ar: 'تم إيقاف التذكير', en: 'Reminder turned off', tone: 'text-gray-500' },
    denied: {
      ar: 'الإشعارات غير مسموح بها. فعّلها من إعدادات الجهاز.',
      en: 'Notifications are not allowed. Enable them in your device settings.',
      tone: 'text-amber-700',
    },
    failed: { ar: 'تعذّر ضبط التذكير', en: 'Could not set the reminder', tone: 'text-red-700' },
  };
  const message = status ? messages[status] : undefined;

  return (
    <div className={clsx('rounded-2xl border border-gray-200 bg-white p-5 mb-6', ar && 'font-arabic')}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
          {setting.enabled ? <Bell className="w-5 h-5" /> : <BellOff className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-gray-900">{ar ? 'تذكير يومي بالقراءة' : 'Daily reading reminder'}</h2>
          {remindersSupported ? (
            <>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={setting.enabled}
                    disabled={busy}
                    onChange={(e) => update({ ...setting, enabled: e.target.checked })}
                    className="w-5 h-5 accent-primary-600"
                  />
                  <span className="text-sm">{ar ? 'تفعيل' : 'On'}</span>
                </label>
                <input
                  type="time"
                  value={`${pad(setting.hour)}:${pad(setting.minute)}`}
                  disabled={busy}
                  dir="ltr"
                  aria-label={ar ? 'وقت التذكير' : 'Reminder time'}
                  onChange={(e) => {
                    const [h, m] = e.target.value.split(':').map(Number);
                    if (Number.isFinite(h) && Number.isFinite(m)) {
                      const next = { ...setting, hour: h, minute: m };
                      if (next.enabled) void update(next);
                      else setSetting(next);
                    }
                  }}
                  className="input py-1 px-2 w-28 text-sm"
                />
              </div>
              {message && (
                <p role="status" className={clsx('mt-2 text-xs', message.tone)}>
                  {ar ? message.ar : message.en}
                </p>
              )}
            </>
          ) : (
            <p className="mt-1 text-sm text-gray-500">
              {ar
                ? 'متاح في تطبيق أندرويد و iOS: إشعار يومي في الوقت الذي تختاره، يفتح آخر موضع قرأته.'
                : 'Available in the Android and iOS apps: a daily notification at the time you choose that opens where you left off.'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
