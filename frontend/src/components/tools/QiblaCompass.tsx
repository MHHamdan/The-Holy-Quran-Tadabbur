/**
 * Live Qibla compass: the dial turns with the device so the Kaaba marker
 * points toward the Qibla. Falls back to the static bearing when the device
 * has no compass (most desktops).
 */
import { useEffect, useRef } from 'react';
import clsx from 'clsx';
import { Compass } from 'lucide-react';
import { angleDiff, useDeviceHeading } from '../../lib/qibla';
import { hapticTap } from '../../lib/native';

const ALIGNED_DEGREES = 5;

const toArabicNumerals = (s: string) => s.replace(/\d/g, (d) => '٠١٢٣٤٥٦٧٨٩'[Number(d)]);

export function QiblaCompass({ bearing, isArabic }: { bearing: number; isArabic: boolean }) {
  const { heading, status, start } = useDeviceHeading();
  const live = status === 'active' && heading !== null;
  const offset = live ? angleDiff(bearing, heading) : null;
  const aligned = offset !== null && Math.abs(offset) <= ALIGNED_DEGREES;

  // One haptic tick each time the phone comes into line with the Qibla.
  const wasAligned = useRef(false);
  useEffect(() => {
    if (aligned && !wasAligned.current) void hapticTap(true);
    wasAligned.current = aligned;
  }, [aligned]);

  const dialRotation = live ? -heading : 0;
  const t = (ar: string, en: string) => (isArabic ? ar : en);

  return (
    <section
      aria-label={t('اتجاه القبلة', 'Qibla Direction')}
      className={clsx(
        'mb-6 p-4 rounded-xl border transition-colors',
        aligned ? 'bg-emerald-100 border-emerald-400' : 'bg-emerald-50 border-emerald-200',
      )}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-emerald-100 rounded-lg" aria-hidden="true">
          <Compass className="w-6 h-6 text-emerald-600" />
        </div>
        <div className="flex-1">
          <p className={clsx('font-semibold text-emerald-900', isArabic && 'font-arabic')}>
            {t('اتجاه القبلة', 'Qibla Direction')}
          </p>
          <p className="text-sm text-emerald-700" dir={isArabic ? 'rtl' : 'ltr'}>
            {isArabic
              ? `${toArabicNumerals(bearing.toFixed(1))}° من الشمال`
              : `${bearing.toFixed(1)}° from North`}
          </p>
        </div>
      </div>

      <div className="relative mx-auto w-56 h-56" role="img"
        aria-label={live
          ? t(`القبلة على بعد ${Math.round(Math.abs(offset ?? 0))} درجة`, `Qibla is ${Math.round(Math.abs(offset ?? 0))}° away`)
          : t(`القبلة ${Math.round(bearing)} درجة من الشمال`, `Qibla is ${Math.round(bearing)}° from north`)}
      >
        {/* Dial: rotates against the device heading so N stays north */}
        <div
          className="absolute inset-0 rounded-full border-4 border-emerald-200 bg-white shadow-inner transition-transform duration-150"
          style={{ transform: `rotate(${dialRotation}deg)` }}
        >
          {(['N', 'E', 'S', 'W'] as const).map((c, i) => (
            <span
              key={c}
              className={clsx('absolute left-1/2 top-1/2 text-xs font-bold', c === 'N' ? 'text-red-600' : 'text-gray-500')}
              style={{ transform: `translate(-50%, -50%) rotate(${i * 90}deg) translateY(-96px) rotate(${-i * 90}deg)` }}
            >
              {isArabic ? { N: 'ش', E: 'ق', S: 'ج', W: 'غ' }[c] : c}
            </span>
          ))}
          {/* Qibla marker at the bearing */}
          <div
            className="absolute left-1/2 top-1/2"
            style={{ transform: `translate(-50%, -50%) rotate(${bearing}deg)` }}
          >
            <div className="flex flex-col items-center" style={{ transform: 'translateY(-70px)' }}>
              <span className="text-2xl leading-none" aria-hidden="true">🕋</span>
            </div>
            <div className="mx-auto w-1 h-16 bg-emerald-600 rounded-full" style={{ transform: 'translateY(-46px)' }} />
          </div>
        </div>
        {/* Fixed pointer: the top of the phone */}
        <div className="absolute left-1/2 -top-2 -translate-x-1/2 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[14px] border-t-gray-800" aria-hidden="true" />
      </div>

      <p role="status" className={clsx('mt-4 text-center text-sm', isArabic && 'font-arabic',
        aligned ? 'text-emerald-800 font-semibold' : 'text-emerald-700')}>
        {live
          ? aligned
            ? t('أنت متجه نحو القبلة', 'You are facing the Qibla')
            : t('أدر الهاتف حتى تصبح الكعبة أعلى الشاشة', 'Turn until the Kaaba is at the top')
          : status === 'needs-permission'
            ? null
            : status === 'denied'
              ? t('لم يُسمح بالوصول إلى البوصلة. البوصلة تعرض الاتجاه من الشمال.', 'Compass access was not allowed. Showing the bearing from north.')
              : t('ضع الهاتف أفقيًا. إن لم تتحرك البوصلة فجهازك لا يدعمها؛ استخدم الدرجة من الشمال.',
                  'Hold the phone flat. If the dial does not move, your device has no compass: use the bearing from north.')}
      </p>
      {status === 'needs-permission' && (
        <div className="mt-3 text-center">
          <button
            type="button"
            onClick={() => void start()}
            className={clsx('px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700', isArabic && 'font-arabic')}
          >
            {t('تشغيل البوصلة', 'Start compass')}
          </button>
        </div>
      )}
    </section>
  );
}
