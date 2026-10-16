/**
 * Tadabbur Application Entry Point
 *
 * Performance optimizations:
 * 1. React Query for server state management
 * 2. Strict mode for development warnings
 * 3. Optimized provider hierarchy
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient, restorePersistedQueries, startQueryPersistence } from './lib/queryClient'
import App from './App'
import './styles/globals.css'

// After a deploy, a tab still running the previous build may request lazy
// chunks that no longer exist. Reload to pick up the new build instead of
// leaving the route broken — at most once per 30 s, so a chunk that is
// genuinely missing cannot cause a reload loop.
window.addEventListener('vite:preloadError', (event) => {
  const KEY = 'tadabbur-chunk-reload-at'
  try {
    const last = Number(sessionStorage.getItem(KEY) || 0)
    if (Date.now() - last < 30_000) return
    sessionStorage.setItem(KEY, String(Date.now()))
  } catch { return /* storage unavailable: cannot guard against loops, so do not reload */ }
  event.preventDefault()
  window.location.reload()
})

const root = ReactDOM.createRoot(document.getElementById('root')!)

// Restore the offline Qur'an cache (IndexedDB) before the first render, so a
// reader opened without a connection finds its text; never wait more than 1.5 s.
void Promise.race([
  restorePersistedQueries().catch(() => 0),
  new Promise((resolve) => setTimeout(resolve, 1500)),
]).finally(() => {
  startQueryPersistence()
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>,
  )
  // "Delete my data" server deletes that failed (offline, server down) are
  // retried on every launch and whenever the device comes back online — not
  // only when /privacy or /therapy is opened. Loaded lazily, off the first paint.
  void import('./lib/dataErasure')
    .then(({ startPendingErasureRetry }) => startPendingErasureRetry())
    .catch(() => { /* chunk unavailable: the Privacy and Guidance pages retry too */ })
})
