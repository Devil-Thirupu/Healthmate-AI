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

// GitHub Pages SPA 404 redirect script
// When GH Pages returns 404, this stores the path and redirects to root
// index.html then reads sessionStorage.redirect and restores the route
const spa404Script = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>HealthMate AI</title>
  <script>
    var base = '/Healthmate-AI';
    var l = window.location;
    var path = l.pathname.slice(base.length) || '/';
    sessionStorage.redirect = l.origin + base + path + l.search + l.hash;
    l.replace(l.origin + base + '/?p=1');
  </script>
</head>
<body></body>
</html>`;

// https://vitejs.dev/config/
export default defineConfig({
  base: getBasePath(),
  plugins: [
    react(),
    {
      name: 'spa-404-fallback',
      closeBundle() {
        const distDir = path.resolve(__dirname, 'dist')
        const fallbackFile = path.join(distDir, '404.html')
        // Write proper SPA redirect 404 (not a copy of index.html)
        fs.writeFileSync(fallbackFile, spa404Script, 'utf8')
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
