import { defineConfig } from 'vitest/config'

// Unit tests only: plain Node, none of the app's Vite plugins (PWA, CSP,
// licences). Components are rendered with react-dom/server, so no DOM is needed.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  },
  esbuild: { jsx: 'automatic' },
})
