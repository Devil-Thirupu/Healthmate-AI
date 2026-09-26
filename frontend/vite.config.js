import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/Healthmate-AI/',
  plugins: [
    react(),
    {
      name: 'spa-404-fallback',
      closeBundle() {
        const distDir = path.resolve(__dirname, 'dist')
        const indexFile = path.join(distDir, 'index.html')
        const fallbackFile = path.join(distDir, '404.html')
        if (fs.existsSync(indexFile)) {
          fs.copyFileSync(indexFile, fallbackFile)
        }
      }
    }
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
