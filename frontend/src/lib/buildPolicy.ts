/**
 * Build-time policies used by vite.config.ts, kept free of Node APIs so the
 * unit tests (src/__tests__/viteConfigGuards.test.ts) type-check with the app.
 *
 * Nothing here ships in the app bundle: only vite.config.ts imports it.
 */

/**
 * Build-time API origin policy (VITE_API_URL is public: never a secret).
 *
 * - web build (default mode): '' (same origin, nginx proxies /api) or a
 *   public origin. A loopback address is refused, since it would only work on
 *   the developer's machine (override: ALLOW_LOCAL_API_URL=true).
 * - `--mode mobile` (Android/iOS release): the app has no same origin to fall
 *   back on, so VITE_API_URL is REQUIRED, must be https://, must not be a
 *   loopback, private-network (10/8, 172.16/12, 192.168/16), link-local
 *   (169.254/16), emulator or mDNS (*.local) host, must not be a bare IP
 *   address, and must not be the placeholder from mobile.env.example. A
 *   phone in the field can reach none of those.
 * - `--mode mobile-dev` (debug builds against a development backend, e.g.
 *   http://10.0.2.2:8000 from the Android emulator): required, any scheme.
 */
export const MOBILE_API_URL_PLACEHOLDER = 'https://REPLACE_WITH_PRODUCTION_API_HOST'
const LOOPBACK = /\/\/(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[::1\])(:|\/|$)/i

/** Hostname of an http(s) URL, lower-cased and without IPv6 brackets; null if unparsable. */
function hostOf(url: string): string | null {
  try {
    return new URL(url).hostname.toLowerCase().replace(/^\[|\]$/g, '')
  } catch {
    return null
  }
}

/**
 * Why a release app could not reach this host from a phone, or null when it
 * is a public DNS name. Release builds must name the API by a public domain
 * (TLS certificates are issued for names), so any IP literal is refused.
 */
export function unreachableHostReason(host: string): string | null {
  if (host === 'localhost' || host.endsWith('.localhost')) return 'a loopback address'
  if (host.endsWith('.local') || host.endsWith('.internal') || host.endsWith('.lan') || host.endsWith('.home.arpa')) {
    return 'a local-network (mDNS/intranet) name'
  }
  if (!host.includes('.') && !host.includes(':')) return 'a single-label intranet name'
  const v4 = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)
  if (v4) {
    const [a, b] = [Number(v4[1]), Number(v4[2])]
    if (a === 127 || a === 0) return 'a loopback address'
    if (a === 10 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168)) return 'a private-network address'
    if (a === 169 && b === 254) return 'a link-local address'
    if (a === 100 && b >= 64 && b <= 127) return 'a carrier-grade NAT address'
    return 'a bare IP address (use the public domain name)'
  }
  if (host.includes(':')) {
    if (host === '::1' || host === '::') return 'a loopback address'
    if (/^f[cd]/.test(host)) return 'a private-network (ULA) address'
    if (/^fe[89ab]/.test(host)) return 'a link-local address'
    return 'a bare IP address (use the public domain name)'
  }
  return null
}

export function apiUrlProblem(mode: string, rawUrl: string | undefined, allowLocal = false): string | null {
  const url = (rawUrl ?? '').trim()
  if (mode === 'mobile') {
    if (!url) return 'VITE_API_URL is not set. Mobile release builds need the public HTTPS API origin (see frontend/mobile.env.example).'
    if (url.includes('REPLACE_WITH_PRODUCTION_API_HOST')) return 'VITE_API_URL is still the placeholder; set the real production API origin.'
    if (LOOPBACK.test(url)) return `VITE_API_URL=${url} is a loopback address; a phone cannot reach it.`
    if (!/^https:\/\/[^/\s]+/i.test(url)) return `VITE_API_URL=${url} must be an https:// origin for mobile release builds.`
    const host = hostOf(url)
    if (!host) return `VITE_API_URL=${url} is not a valid URL.`
    const reason = unreachableHostReason(host)
    if (reason) return `VITE_API_URL=${url} is ${reason}; phones in the field cannot reach it. Mobile release builds need the public API domain (use --mode mobile-dev for emulator/LAN builds).`
    return null
  }
  if (mode === 'mobile-dev') {
    return url ? null : 'VITE_API_URL is not set. Mobile debug builds need the development API origin, e.g. http://10.0.2.2:8000 for the Android emulator.'
  }
  if (LOOPBACK.test(url) && !allowLocal) {
    return `VITE_API_URL=${url} is a loopback address; production bundles must use '' (same origin) or a public origin`
  }
  return null
}

/**
 * Service-worker matcher for canonical, non-personal API content (Qur'an
 * text, pages, juz, tafsir by verse, asbab, names, duas, vocabulary).
 *
 * Workbox serialises the matcher into sw.js with Function#toString, so it
 * cannot close over build-time values; the function is generated with the
 * API origin inlined as a literal. Only the app's own origin (web builds
 * proxy /api) or the configured VITE_API_URL origin is matched: a third-party
 * URL whose path merely looks like /api/v1/quran/... is never cached.
 */
const CANONICAL_API_PATHS: RegExp[] = [
  /^\/api\/v1\/quran\/(suras|verses|page|juz|tafseer|asbab|asma|allah-names|topics)(\/|$)/,
  /^\/api\/v1\/quran\/(metadata|tafsir\/sources)$/,
  /^\/api\/v1\/quran\/(tafsir\/verse|tafsir-comparison\/verse|tafsir\/compare)\//,
  /^\/api\/v1\/tafseer\/(editions$|surah\/|compare\/|\d+\/\d+$)/,
  /^\/api\/v1\/duas(\/|$)/,
  /^\/api\/v1\/vocabulary\/(verse|by-ref|lookup|sources)/,
  /^\/api\/v1\/quranic-calls\/(list|detail|by-surah|graph)/,
]

export function apiOriginOf(apiUrl: string | undefined): string {
  const raw = (apiUrl ?? '').trim()
  if (!raw) return ''
  try {
    return new URL(raw).origin
  } catch {
    return ''
  }
}

type SwMatchContext = { url: URL; request: Request; sameOrigin: boolean }

export function canonicalApiMatcher(apiUrl: string | undefined): (ctx: SwMatchContext) => boolean {
  const origin = JSON.stringify(apiOriginOf(apiUrl))
  const patterns = CANONICAL_API_PATHS.map((re) => re.toString()).join(', ')
  return new Function(
    'ctx',
    `const { url, request, sameOrigin } = ctx;
    return request.method === 'GET'
      && (sameOrigin || (${origin} !== '' && url.origin === ${origin}))
      && [${patterns}].some((re) => re.test(url.pathname));`,
  ) as (ctx: SwMatchContext) => boolean
}
