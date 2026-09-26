import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // @ → src/ so you can import '@/components/Foo.vue' anywhere
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    // Proxy all /api/* calls to the Django dev server.
    // This means in development you never have to hardcode
    // 'http://localhost:8000' in your Vue code — just use '/api/...'.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
