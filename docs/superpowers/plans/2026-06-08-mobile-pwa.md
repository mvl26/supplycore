# SupplyCore Mobile PWA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Biến SPA SupplyCore hiện tại thành PWA cài được trên iOS & Android (cài từ trình duyệt, chạy standalone, cache vỏ app — dữ liệu vẫn online).

**Architecture:** Thêm 3 mảnh vào pipeline build/serve sẵn có — (1) `vite-plugin-pwa` sinh `sw.js` + `manifest.webmanifest` + precache vỏ app; (2) bộ icon sinh từ logo mark Navy; (3) nhúng meta/manifest vào shell. Điểm khó scope service worker trên Frappe được giải bằng `page_renderer` hook phục vụ `/sw.js` ở gốc với header `Service-Worker-Allowed: /supplycore/`. Không sửa backend nghiệp vụ, không sửa nginx.

**Tech Stack:** Vue 3 + Vite, `vite-plugin-pwa` (Workbox), `sharp` (rasterize SVG→PNG), Frappe `page_renderer` hook (Python).

**Spec:** `docs/superpowers/specs/2026-06-08-mobile-pwa-design.md`

---

## File Structure

| File | Trách nhiệm | Create/Modify |
|---|---|---|
| `frontend/scripts/gen-icons.mjs` | Rasterize logo SVG → bộ PNG icon | Create |
| `frontend/public/icons/*.png` | Output icon (vite copy vào build) | Create (sinh ra) |
| `frontend/package.json` | Thêm devDep `sharp`, `vite-plugin-pwa`, script `icons` | Modify |
| `frontend/vite.config.js` | Cắm `vite-plugin-pwa` (manifest + workbox) | Modify |
| `frontend/src/pwa.js` | Đăng ký SW (`/sw.js`, scope `/supplycore/`) + update toast | Create |
| `frontend/src/main.js` | Gọi `registerPwa()` sau mount | Modify |
| `frontend/src/components/OfflineBanner.vue` | Banner khi mất mạng | Create |
| `frontend/src/components/AppShell.vue` | Gắn `<OfflineBanner/>` | Modify |
| `supplycore/pwa.py` | `page_renderer` class phục vụ `/sw.js` | Create |
| `supplycore/hooks.py` | Khai báo `page_renderer` | Modify |
| `supplycore/www/supplycore.html` | Thêm manifest link + meta iOS | Modify |

---

## Task 1: Sinh bộ icon từ logo mark

**Files:**
- Create: `frontend/scripts/gen-icons.mjs`
- Modify: `frontend/package.json`
- Output: `frontend/public/icons/icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, `apple-touch-icon.png`

- [ ] **Step 1: Cài `sharp`**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn add -D sharp
```
Expected: `sharp` xuất hiện trong `devDependencies`.

- [ ] **Step 2: Viết script sinh icon**

Create `frontend/scripts/gen-icons.mjs`:
```js
import sharp from 'sharp'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT = resolve(__dirname, '../public/icons')
mkdirSync(OUT, { recursive: true })

// Logo mark SupplyCore (đồng bộ với AppShell.vue): ô bo góc gradient Navy + dấu cộng trắng.
const mark = (size, { maskable = false } = {}) => {
  const pad = maskable ? Math.round(size * 0.12) : Math.round(size * 0.06)
  const inner = size - pad * 2
  const r = Math.round(inner * 0.22)
  const cx = size / 2
  const stroke = Math.max(2, Math.round(inner * 0.092))
  const arm = inner * 0.225
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <defs><linearGradient id="g" x1="0" y1="0" x2="${size}" y2="${size}" gradientUnits="userSpaceOnUse">
      <stop stop-color="#7FB4E0"/><stop offset="1" stop-color="#1F4E79"/></linearGradient></defs>
    ${maskable ? `<rect width="${size}" height="${size}" fill="#1F4E79"/>` : ''}
    <rect x="${pad}" y="${pad}" width="${inner}" height="${inner}" rx="${r}" fill="url(#g)"/>
    <path d="M${cx} ${cx - arm}V${cx + arm} M${cx - arm} ${cx}H${cx + arm}"
      stroke="#FFFFFF" stroke-width="${stroke}" stroke-linecap="round"/>
  </svg>`
}

const render = (size, file, opts) =>
  sharp(Buffer.from(mark(size, opts))).png().toFile(resolve(OUT, file))

await Promise.all([
  render(192, 'icon-192.png'),
  render(512, 'icon-512.png'),
  render(512, 'icon-maskable-512.png', { maskable: true }),
  render(180, 'apple-touch-icon.png'),
])
console.log('icons → frontend/public/icons/')
```

- [ ] **Step 3: Thêm script vào package.json**

Trong `frontend/package.json` khối `"scripts"`, thêm:
```json
"icons": "node scripts/gen-icons.mjs",
```

- [ ] **Step 4: Chạy & verify kích thước**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn icons
node -e "const s=require('sharp');for(const f of ['icon-192','icon-512','icon-maskable-512','apple-touch-icon']){s('public/icons/'+f+'.png').metadata().then(m=>console.log(f,m.width+'x'+m.height))}"
```
Expected:
```
icon-192 192x192
icon-512 512x512
icon-maskable-512 512x512
apple-touch-icon 180x180
```

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add frontend/scripts/gen-icons.mjs frontend/package.json frontend/package-lock.json frontend/yarn.lock frontend/public/icons
git commit -m "feat(pwa): sinh bộ icon từ logo mark Navy"
```

---

## Task 2: Cắm `vite-plugin-pwa`

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: Cài plugin**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn add -D vite-plugin-pwa
```
Expected: `vite-plugin-pwa` trong `devDependencies`.

- [ ] **Step 2: Cấu hình plugin trong vite.config.js**

Trong `frontend/vite.config.js`: thêm import ở đầu file:
```js
import { VitePWA } from 'vite-plugin-pwa'
```
Trong mảng `plugins`, thêm sau `vue()`:
```js
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,          // tự đăng ký trong src/pwa.js (cần custom path + scope)
      filename: 'sw.js',
      manifestFilename: 'manifest.webmanifest',
      scope: '/supplycore/',
      manifest: {
        name: 'SupplyCore — Cung ứng Bệnh viện',
        short_name: 'SupplyCore',
        start_url: '/supplycore',
        scope: '/supplycore/',
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
        globPatterns: ['**/*.{js,css,png,svg,woff,woff2}'],
        navigateFallback: null,        // build này không có index.html (input = src/main.js)
        navigateFallbackDenylist: [/^\/api/, /^\/method/, /^\/app/],
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
```

- [ ] **Step 3: Build & verify SW + manifest sinh ra đúng chỗ**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn build
ls -la ../supplycore/public/frontend/sw.js ../supplycore/public/frontend/manifest.webmanifest
python3 -c "import json;m=json.load(open('../supplycore/public/frontend/manifest.webmanifest'));print('start_url=',m['start_url'],'scope=',m['scope'],'icons=',len(m['icons']))"
```
Expected: cả 2 file tồn tại; in ra `start_url= /supplycore scope= /supplycore/ icons= 3`.

- [ ] **Step 4: Verify precache có vỏ app**

Run:
```bash
grep -o 'index\.js\|index\.css' ../supplycore/public/frontend/sw.js | sort -u
```
Expected: thấy `index.css` và `index.js` (đã nằm trong precache manifest của SW).

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add frontend/package.json frontend/package-lock.json frontend/yarn.lock frontend/vite.config.js
git commit -m "feat(pwa): cắm vite-plugin-pwa — sinh manifest + service worker"
```

---

## Task 3: Backend — phục vụ `/sw.js` ở gốc qua `page_renderer`

**Files:**
- Create: `supplycore/pwa.py`
- Modify: `supplycore/hooks.py`

- [ ] **Step 1: Viết page renderer**

Create `supplycore/pwa.py`:
```python
"""PWA — phục vụ service worker ở gốc /sw.js với header Service-Worker-Allowed.

Vì app chạy ở /supplycore/* còn asset ở /assets/..., service worker phải nằm ở
đường dẫn ANCESTOR của /supplycore để kiểm soát được route app. /assets/.../sw.js
KHÔNG kiểm soát được /supplycore. Giải pháp: phục vụ sw.js ở gốc /sw.js, cho phép
scope /supplycore/ qua header Service-Worker-Allowed.
"""

import frappe
from werkzeug.wrappers import Response


class ServiceWorkerRenderer:
    def __init__(self, path, status_code=None):
        self.path = path
        self.status_code = status_code

    def can_render(self):
        return self.path == "sw.js"

    def render(self):
        sw_file = frappe.get_app_path("supplycore", "public", "frontend", "sw.js")
        try:
            with open(sw_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "// SupplyCore SW chưa build\n"
        resp = Response(content, mimetype="application/javascript")
        resp.headers["Service-Worker-Allowed"] = "/supplycore/"
        resp.headers["Cache-Control"] = "no-cache, max-age=0"
        return resp
```

- [ ] **Step 2: Khai báo hook**

Trong `supplycore/hooks.py`, thêm (gần khối `website_route_rules`, dòng ~71):
```python
page_renderer = ["supplycore.pwa.ServiceWorkerRenderer"]  # LƯU Ý: hook Frappe là page_renderer (SỐ ÍT)
```

- [ ] **Step 3: Reload hook & verify header**

`page_renderer` là Python hook → gunicorn (`--preload`) nạp lúc khởi động, nên phải **restart tiến trình web** mới có hiệu lực (không chỉ clear-cache).

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench
# Nếu chạy bằng supervisor/systemd:
bench restart
# Nếu chạy bằng `bench start`/`bench serve` ở terminal: Ctrl+C rồi chạy lại tiến trình đó.
bench --site supplycore clear-cache
curl -s -D - -o /dev/null -H "Host: supplycore" http://127.0.0.1:80/sw.js | grep -iE 'HTTP/|content-type|service-worker-allowed|cache-control'
```
Expected:
```
HTTP/1.1 200 OK
Content-Type: application/javascript
Service-Worker-Allowed: /supplycore/
Cache-Control: no-cache, max-age=0
```

- [ ] **Step 4: Verify nội dung là SW thật (không phải HTML shell)**

Run:
```bash
curl -s -H "Host: supplycore" http://127.0.0.1:80/sw.js | head -3
```
Expected: nội dung JavaScript (Workbox), KHÔNG phải `<!DOCTYPE html>`.

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/pwa.py supplycore/hooks.py
git commit -m "feat(pwa): page_renderer phục vụ /sw.js với Service-Worker-Allowed"
```

---

## Task 4: Nhúng manifest + meta iOS vào shell

**Files:**
- Modify: `supplycore/www/supplycore.html`

- [ ] **Step 1: Thêm các thẻ vào `<head>`**

Trong `supplycore/www/supplycore.html`, ngay sau dòng `<meta name="theme-color" content="#1F4E79" />`, thêm:
```html
  <link rel="manifest" href="/assets/supplycore/frontend/manifest.webmanifest" />
  <meta name="mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="SupplyCore" />
  <link rel="apple-touch-icon" href="/assets/supplycore/frontend/icons/apple-touch-icon.png" />
```

- [ ] **Step 2: Verify shell trả manifest link**

Run:
```bash
curl -s -H "Host: supplycore" http://127.0.0.1:80/supplycore | grep -iE 'rel="manifest"|apple-touch-icon|apple-mobile-web-app-capable'
```
Expected: thấy cả 3 dòng (manifest, apple-touch-icon, apple-mobile-web-app-capable).

- [ ] **Step 3: Verify manifest tải được**

Run:
```bash
curl -s -o /dev/null -w "manifest=%{http_code} ct=%{content_type}\n" -H "Host: supplycore" http://127.0.0.1:80/assets/supplycore/frontend/manifest.webmanifest
```
Expected: `manifest=200` (content_type có thể là application/manifest+json hoặc application/json — chấp nhận cả hai).

- [ ] **Step 4: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/www/supplycore.html
git commit -m "feat(pwa): nhúng manifest + meta iOS vào shell"
```

---

## Task 5: Đăng ký service worker + toast cập nhật

**Files:**
- Create: `frontend/src/pwa.js`
- Modify: `frontend/src/main.js`

- [ ] **Step 1: Viết module đăng ký SW**

Create `frontend/src/pwa.js`:
```js
// Đăng ký service worker ở /sw.js với scope /supplycore/ (xem supplycore/pwa.py).
// injectRegister:null trong vite-plugin-pwa nên ta tự đăng ký để ép path + scope.
import { useToastStore } from './stores/toast'

export function registerPwa() {
  if (!('serviceWorker' in navigator)) return
  // SW chỉ chạy trên HTTPS hoặc localhost.
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') return

  window.addEventListener('load', async () => {
    try {
      const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/supplycore/' })
      reg.addEventListener('updatefound', () => {
        const sw = reg.installing
        if (!sw) return
        sw.addEventListener('statechange', () => {
          // Có bản mới và đang có controller cũ → mời tải lại.
          if (sw.state === 'installed' && navigator.serviceWorker.controller) {
            useToastStore().push('Có bản cập nhật mới — chạm để tải lại', 'info', 0)
            window.__sc_sw_waiting = reg.waiting || sw
          }
        })
      })
    } catch (e) {
      console.warn('[pwa] đăng ký SW thất bại:', e)
    }
  })

  // Khi SW mới nắm quyền điều khiển → reload để dùng asset mới.
  let reloaded = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloaded) return
    reloaded = true
    location.reload()
  })
}
```

- [ ] **Step 2: Gọi trong main.js**

Trong `frontend/src/main.js`: thêm import sau dòng `import './assets/main.css'`:
```js
import { registerPwa } from './pwa'
```
Và thêm sau dòng `app.mount('#app')`:
```js
registerPwa()
```

- [ ] **Step 3: Build (không lỗi)**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn build
grep -c "registerPwa\|serviceWorker" ../supplycore/public/frontend/index.js
```
Expected: build thành công; số đếm ≥ 1 (mã đăng ký đã vào bundle).

- [ ] **Step 4: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add frontend/src/pwa.js frontend/src/main.js
git commit -m "feat(pwa): đăng ký service worker + toast cập nhật"
```

---

## Task 6: Banner mất kết nối

**Files:**
- Create: `frontend/src/components/OfflineBanner.vue`
- Modify: `frontend/src/components/AppShell.vue`

- [ ] **Step 1: Viết component**

Create `frontend/src/components/OfflineBanner.vue`:
```vue
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const online = ref(navigator.onLine)
const set = () => { online.value = navigator.onLine }

onMounted(() => {
  window.addEventListener('online', set)
  window.addEventListener('offline', set)
})
onUnmounted(() => {
  window.removeEventListener('online', set)
  window.removeEventListener('offline', set)
})
</script>

<template>
  <div v-if="!online"
    class="fixed top-0 inset-x-0 z-[100] bg-amber-500 text-white text-[13px] font-medium text-center py-1.5 px-3 shadow">
    Mất kết nối mạng — dữ liệu cần kết nối để cập nhật
  </div>
</template>
```

- [ ] **Step 2: Gắn vào AppShell**

Trong `frontend/src/components/AppShell.vue`:
- Trong khối `<script setup>` (cùng nơi import component khác), thêm:
```js
import OfflineBanner from './OfflineBanner.vue'
```
- Trong `<template>`, đặt ngay sau thẻ mở `<template>` (phần tử đầu tiên, trước layout chính):
```html
  <OfflineBanner />
```
> Nếu AppShell dùng Options API (không `setup`), đăng ký vào `components: { OfflineBanner, ... }` và đặt `<OfflineBanner />` đầu template. Kiểm tra đầu file để chọn đúng kiểu.

- [ ] **Step 3: Build & verify import**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend
yarn build
grep -c "Mất kết nối mạng" ../supplycore/public/frontend/index.js
```
Expected: build OK; số đếm ≥ 1.

- [ ] **Step 4: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add frontend/src/components/OfflineBanner.vue frontend/src/components/AppShell.vue
git commit -m "feat(pwa): banner cảnh báo mất kết nối"
```

---

## Task 7: Build tổng + verify cài đặt thật

**Files:** không sửa code — chỉ build & kiểm thử.

- [ ] **Step 1: Build frontend + bench**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore/frontend && yarn build
cd /home/hoangvietyeuem/frappe-bench && bench --site supplycore clear-cache
```
Expected: build không lỗi; `sw.js`, `manifest.webmanifest`, `icons/*` có trong `supplycore/public/frontend/`.

- [ ] **Step 2: Verify bộ ba qua HTTP (local)**

Run:
```bash
H="Host: supplycore"
curl -s -o /dev/null -w "shell=%{http_code}\n" -H "$H" http://127.0.0.1:80/supplycore
curl -s -o /dev/null -w "sw=%{http_code}\n" -H "$H" http://127.0.0.1:80/sw.js
curl -s -o /dev/null -w "manifest=%{http_code}\n" -H "$H" http://127.0.0.1:80/assets/supplycore/frontend/manifest.webmanifest
curl -s -o /dev/null -w "icon=%{http_code}\n" -H "$H" http://127.0.0.1:80/assets/supplycore/frontend/icons/icon-192.png
```
Expected: tất cả `=200`.

- [ ] **Step 3: Mở tunnel HTTPS**

Run (ở terminal của bạn — ngrok không chạy được trong sandbox):
```bash
ngrok http 80 --host-header=supplycore
```
Lấy URL `https://<ngrok>` từ output.

- [ ] **Step 4: Lighthouse PWA audit**

Trên Chrome desktop, mở `https://<ngrok>/supplycore` → DevTools → Lighthouse → category "Progressive Web App" → Analyze.
Expected: mục **Installable** đạt (manifest hợp lệ, SW đăng ký, HTTPS). Tab Application → Service Workers: `activated`, Scope = `/supplycore/`.

- [ ] **Step 5: Cài thử trên điện thoại**

- **Android Chrome:** mở `https://<ngrok>/supplycore` → hiện lời mời cài / menu ⋮ → "Cài đặt ứng dụng" → icon SupplyCore lên màn hình chính → mở standalone. Bật chế độ máy bay → mở lại app → UI vẫn lên + banner "Mất kết nối".
- **iOS Safari:** mở `https://<ngrok>/supplycore` → nút Share → "Thêm vào Màn hình chính" → icon/tên đúng → mở standalone (không thanh địa chỉ), status bar đúng.

- [ ] **Step 6: Hồi quy có mạng**

Đăng nhập + mở 2–3 màn hình (Dashboard, StockBalance, một DocList) qua app đã cài → hoạt động như bản web.

- [ ] **Step 7: Commit tài liệu kết quả (tuỳ chọn)**

Nếu cần ghi lại kết quả test, thêm ghi chú vào cuối spec và:
```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add docs/superpowers/specs/2026-06-08-mobile-pwa-design.md
git commit -m "docs(pwa): ghi kết quả kiểm thử cài đặt"
```

---

## Ghi chú thực thi

- **TDD-style cho PWA:** domain này không hợp unit test thuần — mỗi task có bước verify cụ thể (kiểm file build, header qua curl, Lighthouse) đóng vai trò "test". Giữ commit nhỏ sau mỗi task.
- **HTTPS bắt buộc:** SW không chạy trên HTTP (trừ localhost). Mọi kiểm thử cài đặt phải qua ngrok HTTPS.
- **Thứ tự phụ thuộc:** Task 1 → 2 (icon path), Task 2 → 3 (cần sw.js đã build để renderer đọc), Task 2 → 5. Task 4, 6 độc lập. Task 7 sau cùng.
- **Rollback:** gỡ `page_renderer` khỏi hooks.py + xoá thẻ manifest/meta trong shell + gỡ plugin PWA khỏi vite.config → về web thường. Không đụng dữ liệu/RBAC.
