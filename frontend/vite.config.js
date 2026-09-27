import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Determine base path:
// Priority: VITE_BASE_PATH env var -> GitHub Pages default -> root '/'
const getBasePath = () => {
  if (process.env.VITE_BASE_PATH) {
    return process.env.VITE_BASE_PATH;
  }
  if (process.env.GITHUB_PAGES === 'true') {
    return '/Healthmate-AI/';
  }
  return '/';
};

// https://vitejs.dev/config/
export default defineConfig({
  base: getBasePath(),
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
