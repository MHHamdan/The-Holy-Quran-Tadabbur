/**
 * Where the backend API lives.
 *
 * - Web (same origin): leave VITE_API_URL empty; requests go to /api/... on the
 *   page's own origin (nginx or the Vite dev proxy forwards them).
 * - Mobile apps / separately hosted API: set VITE_API_URL to the public HTTPS
 *   origin, e.g. https://api.example.org. Production builds refuse a localhost
 *   value (see vite.config.ts).
 *
 * Only public values belong here: never put a secret in a VITE_* variable.
 */
export const API_ORIGIN: string = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

/** Absolute (or same-origin relative) URL for an API path such as "/api/v1/quran/metadata". */
export function apiUrl(path: string): string {
  return `${API_ORIGIN}${path.startsWith('/') ? path : `/${path}`}`;
}

/** WebSocket URL for an API path, matching the API's scheme (https → wss). */
export function wsUrl(path: string): string {
  const origin = API_ORIGIN || window.location.origin;
  return `${origin.replace(/^http/, 'ws')}${path.startsWith('/') ? path : `/${path}`}`;
}

/**
 * Public web address used in shared links (e.g. https://tadabbur.example.org).
 * In the browser it defaults to the page's own origin. Inside the Android/iOS
 * apps the origin is https://localhost or capacitor://localhost, which is
 * useless to the person receiving a link, so shares carry no link there unless
 * VITE_PUBLIC_WEB_URL is set at build time.
 */
const CONFIGURED_WEB_ORIGIN = (import.meta.env.VITE_PUBLIC_WEB_URL || '').replace(/\/+$/, '');

export function publicWebUrl(path: string, isNative: boolean): string | null {
  const origin = CONFIGURED_WEB_ORIGIN || (isNative ? '' : window.location.origin);
  return origin ? `${origin}${path.startsWith('/') ? path : `/${path}`}` : null;
}
