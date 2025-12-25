import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
    // Add middleware to log requests
    middlewareMode: false,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  // Add resolve alias for debugging
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})