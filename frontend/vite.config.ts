import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { compression } from 'vite-plugin-compression2'
import fs from 'fs'
import path from 'path'

/**
 * Vite Configuration - Optimized for FAANG-level Performance
 *
 * Key optimizations:
 * 1. Route-based code splitting with manual chunks
 * 2. Vendor chunking for better caching
 * 3. Tree shaking and minification
 * 4. Compression support
 *
 * HTTPS for Microphone Access:
 * - Run with HTTPS: HTTPS=true npm run dev
 * - This enables microphone access over LAN (required for getUserMedia)
 * - For localhost, HTTP works fine (browser exception)
 */
/**
 * Build-time API origin policy (VITE_API_URL is public: never a secret).
 *
 * - web build (default mode): '' (same origin, nginx proxies /api) or a
 *   public origin. A loopback address is refused, since it would only work on
 *   the developer's machine (override: ALLOW_LOCAL_API_URL=true).
 * - `--mode mobile` (Android/iOS release): the app has no same origin to fall
 *   back on, so VITE_API_URL is REQUIRED, must be https://, must not be a
 *   loopback address and must not be the placeholder from mobile.env.example.
 * - `--mode mobile-dev` (debug builds against a development backend, e.g.
 *   http://10.0.2.2:8000 from the Android emulator): required, any scheme.
 */
export const MOBILE_API_URL_PLACEHOLDER = 'https://REPLACE_WITH_PRODUCTION_API_HOST'
const LOOPBACK = /\/\/(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[::1\])(:|\/|$)/i

export function apiUrlProblem(mode: string, rawUrl: string | undefined): string | null {
  const url = (rawUrl ?? '').trim()
  if (mode === 'mobile') {
    if (!url) return 'VITE_API_URL is not set. Mobile release builds need the public HTTPS API origin (see frontend/mobile.env.example).'
    if (url.includes('REPLACE_WITH_PRODUCTION_API_HOST')) return 'VITE_API_URL is still the placeholder; set the real production API origin.'
    if (LOOPBACK.test(url)) return `VITE_API_URL=${url} is a loopback address; a phone cannot reach it.`
    if (!/^https:\/\/[^/\s]+/i.test(url)) return `VITE_API_URL=${url} must be an https:// origin for mobile release builds.`
    return null
  }
  if (mode === 'mobile-dev') {
    return url ? null : 'VITE_API_URL is not set. Mobile debug builds need the development API origin, e.g. http://10.0.2.2:8000 for the Android emulator.'
  }
  if (LOOPBACK.test(url) && process.env.ALLOW_LOCAL_API_URL !== 'true') {
    return `VITE_API_URL=${url} is a loopback address; production bundles must use '' (same origin) or a public origin`
  }
  return null
}

const enforceApiUrlPolicy = {
  name: 'tadabbur-api-url-policy',
  apply: 'build' as const,
  configResolved(config: { mode: string; env: Record<string, unknown> }) {
    const problem = apiUrlProblem(config.mode, config.env.VITE_API_URL as string | undefined)
    if (problem) throw new Error(problem)
  },
}

export default defineConfig(({ mode }) => ({
  plugins: [
    enforceApiUrlPolicy,
    react(),
    VitePWA({
      // "prompt": a new build is downloaded in the background and activated
      // only when the user accepts the in-app banner (AppUpdateBanner).
      registerType: 'prompt',
      // Native apps ship their assets inside the app package: no service
      // worker (it would only serve stale copies after an app update).
      disable: mode === 'mobile' || mode === 'mobile-dev',
      injectRegister: false,
      includeAssets: ['favicon.svg', 'icons/*.png'],
      manifest: false, // we manage manifest.json ourselves in /public
      workbox: {
        // App shell: hashed JS/CSS + index.html, precached and versioned per build.
        globPatterns: ['**/*.{js,css,html,ico,svg,woff2,png}'],
        cleanupOutdatedCaches: true,
        // SPA routes fall back to the cached shell offline; API, health and
        // backend docs must never be answered with index.html.
        navigateFallback: 'index.html',
        navigateFallbackDenylist: [/^\/api\//, /^\/health/, /^\/docs/, /^\/redoc/, /^\/openapi\.json/],
        runtimeCaching: [
          {
            // Canonical, non-personal content only: Qur'an text, pages, juz,
            // tafsir by verse, asbab, names, duas, vocabulary. Cached
            // aggressively for offline reading and refreshed in the background.
            // Everything else under /api (RAG answers, AI output, search,
            // per-user bookmarks/history/progress, stats, admin) is NOT
            // matched here and always goes to the network.
            // The matcher is serialised into sw.js, so the patterns are inline.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' && [
                /^\/api\/v1\/quran\/(suras|verses|page|juz|tafseer|asbab|asma|allah-names|topics)(\/|$)/,
                /^\/api\/v1\/quran\/(metadata|tafsir\/sources)$/,
                /^\/api\/v1\/quran\/(tafsir\/verse|tafsir-comparison\/verse|tafsir\/compare)\//,
                /^\/api\/v1\/tafseer\/(editions$|surah\/|compare\/|\d+\/\d+$)/,
                /^\/api\/v1\/duas(\/|$)/,
                /^\/api\/v1\/vocabulary\/(verse|by-ref|lookup|sources)/,
                /^\/api\/v1\/quranic-calls\/(list|detail|by-surah|graph)/,
              ].some((re) => re.test(url.pathname)),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-canonical-v2',
              expiration: { maxEntries: 3000, maxAgeSeconds: 30 * 24 * 3600 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            // Static JSON shipped with the frontend (atlas/graph data). Same
            // origin only; revalidated so a redeploy is picked up next visit.
            urlPattern: ({ url, sameOrigin }) =>
              sameOrigin && url.pathname.endsWith('.json') && !url.pathname.startsWith('/api/'),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'static-json-v2',
              expiration: { maxEntries: 200, maxAgeSeconds: 7 * 24 * 3600 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            // Google Fonts: the stylesheet changes rarely, font files never.
            urlPattern: ({ url }) => url.origin === 'https://fonts.googleapis.com',
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'google-fonts-css', expiration: { maxEntries: 10 } },
          },
          {
            urlPattern: ({ url }) => url.origin === 'https://fonts.gstatic.com',
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-files',
              expiration: { maxEntries: 40, maxAgeSeconds: 365 * 24 * 3600 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        // Keep SW disabled in dev so hot-reload is unaffected
        enabled: false,
      },
    }),
    // Build-time precompression: ship .gz (and .br) alongside every text asset so
    // nginx serves them with zero per-request CPU (gzip_static / brotli_static).
    // Heavy graph chunks (e.g. the 3.3 MB story-connection JSON→JS) drop ~6-8x
    // on the wire. Only compress files >1 KB where it actually pays off.
    // Not for the native apps: there is no nginx in the app package, and the
    // Android asset merger rejects x.js next to x.js.gz as duplicate resources.
    ...(mode === 'mobile' || mode === 'mobile-dev' ? [] : [compression({
      // gzip only — the stock nginx image serves .gz via gzip_static but has no
      // brotli module, so emitting .br would just leave dead files on disk.
      algorithm: 'gzip',
      include: /\.(js|mjs|css|html|json|svg|txt|xml|wasm)$/i,
      threshold: 1024,
      deleteOriginalAssets: false,
    })]),
  ],

  server: {
    // Ports are defined in scripts/ports.env and passed through by
    // scripts/start_all.sh. This machine runs several unrelated platforms, so
    // the defaults here match that block rather than Vite's usual 3000, which
    // other dev servers on the box take first.
    port: Number(process.env.TADABBUR_FRONTEND_PORT ?? 19300),
    host: '0.0.0.0',
    // Fail loudly instead of silently hopping to the next free port, which
    // would leave the backend's CORS list and the printed URL pointing nowhere.
    strictPort: true,
    // Tell the browser never to cache dev assets — ensures every page
    // load after 'make start' gets the latest code, not a stale copy.
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
    // Enable HTTPS if HTTPS=true environment variable is set
    // This is required for microphone access over LAN
    https: process.env.HTTPS === 'true' ? {
      key: fs.readFileSync(path.resolve(__dirname, 'certs/key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, 'certs/cert.pem')),
    } : undefined,
    proxy: {
      '/api': {
        target:
          process.env.CONTAINER_ENV === 'true'
            ? 'http://backend:8000'
            : `http://localhost:${process.env.TADABBUR_BACKEND_PORT ?? 19800}`,
        changeOrigin: true,
        ws: true,  // Enable WebSocket proxying
      },
    },
  },

  build: {
    // Enable source maps for production debugging
    sourcemap: false,

    // Minification settings - use esbuild (faster, included with Vite)
    minify: 'esbuild',

    // Chunk size warning limit (500KB)
    chunkSizeWarningLimit: 500,

    // Rollup options for code splitting
    rollupOptions: {
      output: {
        // Manual chunks for optimal loading
        manualChunks: {
          // Vendor chunks - cached separately
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['lucide-react', 'clsx'],
          'vendor-state': ['zustand', '@tanstack/react-query'],
          'vendor-network': ['axios'],
          'vendor-graph': ['cytoscape', 'react-cytoscapejs'],

          // Feature chunks - loaded on demand
          'feature-mushaf': [
            './src/pages/MushafPage.tsx',
          ],
          'feature-quran': [
            './src/pages/QuranPage.tsx',
          ],
          'feature-search': [
            './src/pages/SearchPage.tsx',
          ],
          'feature-themes': [
            './src/pages/ThemesPage.tsx',
            './src/pages/ThemeDetailPage.tsx',
          ],
          'feature-concepts': [
            './src/pages/ConceptsPage.tsx',
            './src/pages/ConceptDetailPage.tsx',
          ],
          'feature-stories': [
            './src/pages/StoryAtlasPage.tsx',
            './src/pages/StoryDetailPage.tsx',
          ],
          // Tools pages are each separately lazy-loaded in App.tsx router,
          // so omitting them from manualChunks lets Vite split them per-page.
          // Users only download the tool they visit, not all 9 tools together.
        },

        // Asset file naming for better caching
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`;
          }
          if (/woff2?|ttf|eot/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },

        // Chunk file naming
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },

    // Target modern browsers for smaller bundles
    target: 'es2020',
  },

  // Optimization settings
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'zustand',
      'axios',
      'clsx',
      'lucide-react',
    ],
  },

  // Enable CSS code splitting
  css: {
    devSourcemap: true,
  },
}))
