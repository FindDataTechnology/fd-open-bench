import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '3118'),
    proxy: {
      '/api': {
        target: process.env.API_URL || 'http://localhost:8999/api/v1',
        changeOrigin: true,
      },
    },
  },
})
