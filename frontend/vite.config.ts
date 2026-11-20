import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// The dev and preview servers proxy the Django backend so the API, uploaded
// files and the admin are same-origin (required to cache downloads for offline use). The Host
// header is passed through, so file URLs the API returns point back here.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backend = env.BACKEND_URL || 'http://127.0.0.1:8000'
  const proxy = {
    '/api': { target: backend },
    '/media': { target: backend },
    // Django admin (content editing) and its assets/uploads, on the same origin.
    '/admin': { target: backend },
    '/static': { target: backend },
    '/ckeditor5': { target: backend },
  }
  return {
    plugins: [
      react(),
      VitePWA({
        strategies: 'injectManifest',
        srcDir: 'src',
        filename: 'sw.ts',
        registerType: 'prompt',
        injectRegister: false,
        manifest: {
          id: '/',
          name: 'Learning Roadmap',
          short_name: 'Roadmap',
          description: 'Plan, study and track your learning roadmaps — online or offline.',
          start_url: '/?source=pwa',
          scope: '/',
          display: 'standalone',
          display_override: ['standalone', 'minimal-ui'],
          orientation: 'any',
          theme_color: '#12243b',
          background_color: '#12243b',
          categories: ['education', 'productivity'],
          icons: [
            { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
            { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
            {
              src: '/icons/icon-maskable-512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
            { src: '/icons/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
          ],
          shortcuts: [
            { name: 'Roadmaps', url: '/roadmaps' },
            { name: 'Progress', url: '/progress' },
            { name: 'Library', url: '/library' },
          ],
        },
        injectManifest: {
          // App shell, PDF.js worker, fonts and image decoders. Character maps
          // (only needed by some CJK PDFs) are cached on first use instead.
          globPatterns: ['**/*.{js,mjs,css,html,svg,png,ico,webmanifest,wasm,pfb,ttf}'],
          globIgnores: ['pdfjs/cmaps/**', 'pdfjs/wasm/quickjs*', 'pdfjs/wasm/*_fallback.js'],
          maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        },
        devOptions: { enabled: env.PWA_DEV === '1', type: 'module' },
      }),
    ],
    // Listen on all interfaces (0.0.0.0) so other devices on the network can connect.
    server: { host: true, port: 8083, strictPort: true, proxy },
    preview: { host: true, port: 8083, strictPort: true, proxy },
  }
})
