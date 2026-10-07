/**
 * Service-worker update prompt and offline notice.
 *
 * The service worker is registered with registerType "prompt": a new build is
 * downloaded in the background but only activated when the user chooses to
 * reload, so an update never swaps code under an in-progress recitation or
 * question. Without this, old lazy chunks could disappear mid-session.
 *
 * The native apps (Capacitor) ship their assets inside the app package and
 * have no service worker: they mount NativeConnectivityBanner instead, which
 * only shows the offline notice.
 */
import { useEffect, useState } from 'react';
import { useRegisterSW } from 'virtual:pwa-register/react';
import { RefreshCw, WifiOff, X } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';

const UPDATE_CHECK_INTERVAL_MS = 60 * 60 * 1000;

function useOnline(): boolean {
  const [online, setOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine));
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);
  return online;
}

/** Web/PWA: update prompt + offline notice. */
export function AppUpdateBanner() {
  const online = useOnline();
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, registration) {
      // Long-lived tabs and installed apps otherwise only check on navigation.
      if (registration) setInterval(() => { registration.update().catch(() => undefined); }, UPDATE_CHECK_INTERVAL_MS);
    },
  });
  return (
    <Banners
      online={online}
      needRefresh={needRefresh}
      onReload={() => updateServiceWorker(true)}
      onDismiss={() => setNeedRefresh(false)}
    />
  );
}

/** Android/iOS: offline notice only (no service worker in the native apps). */
export function NativeConnectivityBanner() {
  const online = useOnline();
  return <Banners online={online} needRefresh={false} onReload={() => undefined} onDismiss={() => undefined} />;
}

function Banners({ online, needRefresh, onReload, onDismiss }: {
  online: boolean;
  needRefresh: boolean;
  onReload: () => void;
  onDismiss: () => void;
}) {
  const { language } = useLanguageStore();
  const isAr = language === 'ar';

  if (!needRefresh && online) return null;

  return (
    <div
      className="fixed inset-x-0 bottom-20 sm:bottom-4 z-50 flex flex-col items-center gap-2 px-4 pointer-events-none"
      dir={isAr ? 'rtl' : 'ltr'}
    >
      {!online && (
        <div role="status" className="pointer-events-auto flex items-center gap-2 rounded-xl bg-gray-900/90 text-white text-sm px-4 py-2 shadow-lg max-w-md">
          <WifiOff className="w-4 h-4 flex-shrink-0" />
          <span>
            {isAr
              ? 'أنت غير متصل. الصفحات المحفوظة من القرآن والتفسير متاحة، أما ميزات الذكاء الاصطناعي فتحتاج إلى اتصال.'
              : 'You are offline. Saved Qur\'an and tafsir pages still work; AI features need a connection.'}
          </span>
        </div>
      )}
      {needRefresh && (
        <div role="alert" className="pointer-events-auto flex items-center gap-3 rounded-xl bg-white border border-primary-200 text-gray-800 text-sm px-4 py-3 shadow-lg max-w-md">
          <RefreshCw className="w-4 h-4 text-primary-600 flex-shrink-0" />
          <span className="flex-1">{isAr ? 'يتوفر إصدار جديد من التطبيق.' : 'A new version of the app is available.'}</span>
          <button
            onClick={onReload}
            className="rounded-lg bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 text-xs font-medium"
          >
            {isAr ? 'تحديث' : 'Reload'}
          </button>
          <button
            onClick={onDismiss}
            aria-label={isAr ? 'لاحقاً' : 'Later'}
            className="p-1 rounded text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
