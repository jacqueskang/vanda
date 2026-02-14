import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  root: '.',
  build: {
    outDir: '../../dist/ui',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/chat': 'http://localhost:8088',
      '/agents': 'http://localhost:8088',
      '/health': 'http://localhost:8088',
    },
  },
})
