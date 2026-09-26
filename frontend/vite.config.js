import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  // ── Vitest configuration ───────────────────────────────────────────────────
  // Adding 'test' here tells Vitest how to run our component tests.
  test: {
    // 'jsdom' simulates a browser DOM environment in Node.js.
    // Without this, document/window/etc. don't exist and Vue can't mount.
    environment: 'jsdom',

    // Makes test globals (describe, it, expect, vi) available without
    // needing to import them in every test file.
    globals: true,

    // setupFiles runs before every test file — good for global mocks.
    setupFiles: ['./src/tests/setup.js'],
  }
})
