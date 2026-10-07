import type { CapacitorConfig } from '@capacitor/cli';

/**
 * Capacitor shell for the Android and iOS apps.
 *
 * The app ships the built web assets (dist/) inside the package and talks to
 * the backend over HTTPS at the build-time VITE_API_URL (see
 * mobile.env.example). Nothing here may hold a secret: this file is compiled
 * into the native projects. There is deliberately no `server.url`, so the app
 * never loads remote code.
 *
 * WebView origins, which the backend must list in CORS_ORIGINS:
 *   Android  https://localhost
 *   iOS      capacitor://localhost
 */
// Debug builds against an http:// development backend (e.g. the Android
// emulator's http://10.0.2.2:8000) must opt in with CAP_ALLOW_HTTP_BACKEND=true
// at `cap sync` time (`npm run android:debug` does). Release syncs never set it,
// and the release network security config forbids cleartext traffic anyway.
const allowHttpBackend = process.env.CAP_ALLOW_HTTP_BACKEND === 'true';

const config: CapacitorConfig = {
  appId: 'com.mhamdan.tadabbur',
  appName: 'Tadabbur',
  webDir: 'dist',
  android: {
    // Release: never load http:// content into the https://localhost WebView.
    allowMixedContent: allowHttpBackend,
  },
  ios: {
    contentInset: 'never',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      launchAutoHide: true,
      backgroundColor: '#0284c7',
      showSpinner: false,
    },
    Keyboard: {
      // Resize the web view's body so inputs (Ask, Search) stay above the keyboard.
      resize: 'body',
      resizeOnFullScreen: true,
    },
    StatusBar: {
      overlaysWebView: false,
      style: 'DARK', // light text on the blue bar
      backgroundColor: '#0284c7',
    },
  },
};

export default config;
