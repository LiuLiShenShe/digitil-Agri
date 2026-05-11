import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/scene/',
  build: {
    outDir: 'dist/scene'
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    allowedHosts: 'all',
    proxy: {
      '/sceneApi': {
        target: 'http://127.0.0.1:9010',
        changeOrigin: true,
        ws: true,
      },
      '/scene-assets': {
        target: 'http://127.0.0.1:9010',
        changeOrigin: true,
      }
    }
  }
})
