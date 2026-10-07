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
import { queryClient } from './lib/queryClient'
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

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
