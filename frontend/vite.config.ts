import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite Configuration - Optimized for FAANG-level Performance
 *
 * Key optimizations:
 * 1. Route-based code splitting with manual chunks
 * 2. Vendor chunking for better caching
 * 3. Tree shaking and minification
 * 4. Compression support
 */
export default defineConfig({
  plugins: [react()],

  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
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
            './src/pages/StoriesPage.tsx',
            './src/pages/StoryDetailPage.tsx',
            './src/pages/StoryAtlasPage.tsx',
            './src/pages/StoryAtlasDetailPage.tsx',
          ],
          'feature-tools': [
            './src/pages/ToolsPage.tsx',
            './src/pages/tools/ZakatCalculatorPage.tsx',
            './src/pages/tools/MosqueFinderPage.tsx',
            './src/pages/tools/IslamicVideosPage.tsx',
            './src/pages/tools/IslamicNewsPage.tsx',
            './src/pages/tools/IslamicBooksPage.tsx',
            './src/pages/tools/HajjUmrahGuidePage.tsx',
            './src/pages/tools/IslamicWebSearchPage.tsx',
            './src/pages/tools/PrayerTimesPage.tsx',
            './src/pages/tools/HijriCalendarPage.tsx',
          ],
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
