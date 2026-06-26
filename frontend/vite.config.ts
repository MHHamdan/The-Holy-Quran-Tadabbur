import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
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
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: false, // we manage manifest.json ourselves in /public
      workbox: {
        // Cache JS/CSS/HTML with stale-while-revalidate for fast offline loads
        globPatterns: ['**/*.{js,css,html,ico,svg,woff2}'],
        runtimeCaching: [
          {
            // Quran text + tafseer API — cache for 24 h, serve stale offline
            urlPattern: /\/api\/v1\/(quran|tafseer|asbab|vocabulary|duas|dhikr)/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-quran-cache',
              expiration: { maxEntries: 500, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Static JSON data served by the frontend (generated atlas files, etc.)
            urlPattern: /\.json$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'json-data-cache',
              expiration: { maxEntries: 200, maxAgeSeconds: 604800 }, // 7 days
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
  ],

  server: {
    port: 3000,
    host: '0.0.0.0',
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
        target: process.env.CONTAINER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8002',
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
})
