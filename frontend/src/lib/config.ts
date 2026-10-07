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
