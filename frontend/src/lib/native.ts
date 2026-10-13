/**
 * Native (Capacitor) integration. Every export degrades to a web equivalent
 * (or a no-op) in the browser. Plugins are loaded lazily so the web bundle
 * does not pay for them.
 */
import { Capacitor } from '@capacitor/core';
import { publicWebUrl } from './config';

export const isNativeApp = Capacitor.isNativePlatform();

/** Custom URL scheme for deep links: tadabbur://quran/2?aya=255 opens /quran/2?aya=255. */
export const APP_URL_SCHEME = 'tadabbur';

/**
 * Turn a deep link or notification route into an in-app path, or null.
 * Only paths inside the app are accepted; anything else is ignored.
 */
export function inAppPath(url: string): string | null {
  let path: string;
  if (url.startsWith('/')) {
    path = url;
  } else {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === `${APP_URL_SCHEME}:`) {
        // tadabbur://quran/2 parses with host "quran" and pathname "/2"
        path = `/${parsed.host}${parsed.pathname === '/' ? '' : parsed.pathname}${parsed.search}`;
      } else if (parsed.protocol === 'https:' && publicWebUrl('/', false)?.startsWith(parsed.origin)) {
        path = `${parsed.pathname}${parsed.search}`;
      } else {
        return null;
      }
    } catch {
      return null;
    }
  }
  return /^\/[A-Za-z0-9\-_/]*(\?[A-Za-z0-9=&\-_.,%]*)?$/.test(path) && !path.startsWith('//') ? path : null;
}

/**
 * Status bar, splash screen, Android back button, deep links and taps on
 * local notifications.
 */
export async function initNativeShell(
  navigateBack: () => void,
  navigateTo: (path: string) => void,
): Promise<void> {
  if (!isNativeApp) return;

  const [{ StatusBar, Style }, { SplashScreen }, { App }, { LocalNotifications }] = await Promise.all([
    import('@capacitor/status-bar'),
    import('@capacitor/splash-screen'),
    import('@capacitor/app'),
    import('@capacitor/local-notifications'),
  ]);

  try {
    await StatusBar.setStyle({ style: Style.Dark });
    if (Capacitor.getPlatform() === 'android') {
      await StatusBar.setBackgroundColor({ color: '#0284c7' });
    }
  } catch { /* status bar styling is cosmetic */ }

  // Android hardware back: go back in the SPA history; leave the app at the root.
  App.addListener('backButton', ({ canGoBack }) => {
    if (canGoBack) navigateBack();
    else App.exitApp();
  });

  App.addListener('appUrlOpen', ({ url }) => {
    const path = inAppPath(url);
    if (path) navigateTo(path);
  });

  LocalNotifications.addListener('localNotificationActionPerformed', ({ notification }) => {
    const route = (notification.extra as { route?: string } | undefined)?.route;
    const path = route ? inAppPath(route) : null;
    if (path) navigateTo(path);
  });

  await SplashScreen.hide();
}

/** A light tap, e.g. on each dhikr count. Native haptics in the apps, vibration on the web. */
export async function hapticTap(strong = false): Promise<void> {
  if (isNativeApp) {
    try {
      const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
      await Haptics.impact({ style: strong ? ImpactStyle.Heavy : ImpactStyle.Light });
    } catch { /* haptics are optional */ }
    return;
  }
  try { navigator.vibrate?.(strong ? 40 : 12); } catch { /* vibration is optional */ }
}

export type ShareOutcome = 'shared' | 'copied' | 'failed';

/**
 * Share text (and a link when one exists) through the system share sheet:
 * the native sheet in the apps, the Web Share API in browsers that have it,
 * otherwise the clipboard.
 */
export async function shareContent(opts: { title: string; text: string; path?: string }): Promise<ShareOutcome> {
  const url = opts.path ? publicWebUrl(opts.path, isNativeApp) ?? undefined : undefined;
  if (isNativeApp) {
    try {
      const { Share } = await import('@capacitor/share');
      await Share.share({ title: opts.title, text: opts.text, url, dialogTitle: opts.title });
      return 'shared';
    } catch {
      return 'failed'; // includes the user dismissing the sheet
    }
  }
  if (navigator.share) {
    try {
      await navigator.share({ title: opts.title, text: opts.text, url });
      return 'shared';
    } catch {
      return 'failed';
    }
  }
  try {
    await navigator.clipboard.writeText(url ? `${opts.text}\n${url}` : opts.text);
    return 'copied';
  } catch {
    return 'failed';
  }
}
