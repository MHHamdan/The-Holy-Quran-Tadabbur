/**
 * Native (Capacitor) integration. Everything here is a no-op in the browser.
 */
import { Capacitor } from '@capacitor/core';

export const isNativeApp = Capacitor.isNativePlatform();

/**
 * Status bar, splash screen and the Android back button. Plugins are loaded
 * lazily so the web bundle does not pay for them.
 */
export async function initNativeShell(navigateBack: () => void): Promise<void> {
  if (!isNativeApp) return;

  const [{ StatusBar, Style }, { SplashScreen }, { App }] = await Promise.all([
    import('@capacitor/status-bar'),
    import('@capacitor/splash-screen'),
    import('@capacitor/app'),
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

  await SplashScreen.hide();
}
