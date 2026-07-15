import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// Build vào supplycore/public/frontend/ để Frappe serve qua /assets/supplycore/frontend/
export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,          // tự đăng ký trong src/pwa.js (cần custom path + scope)
      filename: 'sw.js',
      manifestFilename: 'manifest.webmanifest',
      scope: '/supplycore',
      manifest: {
        name: 'SupplyCore — Cung ứng Bệnh viện',
        short_name: 'SupplyCore',
        start_url: '/supplycore',
        scope: '/supplycore',
        display: 'standalone',
        background_color: '#1F4E79',
        theme_color: '#1F4E79',
        lang: 'vi',
        icons: [
          { src: '/assets/supplycore/frontend/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/assets/supplycore/frontend/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/assets/supplycore/frontend/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // SW phục vụ ở gốc /sw.js → importScripts("./workbox-*.js") sẽ phân giải về
        // /workbox-*.js (404). Gộp runtime vào sw.js để bỏ hẳn file rời + importScripts.
        inlineWorkboxRuntime: true,
        globPatterns: ['**/*.{js,css,png,svg,woff,woff2}'],
        // SW phục vụ ở gốc /sw.js nhưng asset ở /assets/supplycore/frontend/. Workbox
        // phân giải precache URL tương đối theo vị trí SW (/) → /index.js (404). Ép các
        // entry globbed (js/css/icon/chunk) thành tuyệt đối dưới base. Riêng
        // manifest.webmanifest do plugin thêm SAU transform nên không vào đây — nó được
        // phục vụ ở gốc /manifest.webmanifest qua page_renderer (supplycore/pwa.py).
        manifestTransforms: [
          async (entries) => ({
            manifest: entries.map((e) =>
              e.url.startsWith('/') || e.url.startsWith('http')
                ? e
                : { ...e, url: '/assets/supplycore/frontend/' + e.url }
            ),
          }),
        ],
        navigateFallback: null,        // build này không có index.html (input = src/main.js)
        runtimeCaching: [
          {
            urlPattern: ({ request, url }) => request.mode === 'navigate' && url.pathname.startsWith('/supplycore'),
            handler: 'NetworkFirst',
            options: { cacheName: 'sc-shell', networkTimeoutSeconds: 3 },
          },
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api') || url.pathname.startsWith('/method'),
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/method': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../supplycore/public/frontend',
    emptyOutDir: true,
    rollupOptions: {
      input: 'src/main.js',
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: (info) => info.name === 'main.css' || info.name?.endsWith('.css')
          ? 'index.css'
          : 'assets/[name]-[hash][extname]',
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'chart': ['chart.js', 'vue-chartjs'],
        },
      },
    },
  },
  base: '/assets/supplycore/frontend/',
})
