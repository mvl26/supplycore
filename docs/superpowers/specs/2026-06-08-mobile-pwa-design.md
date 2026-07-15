# SupplyCore Mobile — PWA (Progressive Web App)

- **Ngày:** 2026-06-08
- **Trạng thái:** Design — chờ duyệt
- **Phạm vi:** Biến SPA SupplyCore hiện tại thành app cài được trên iOS & Android, không viết lại app.

---

## 1. Mục tiêu & phạm vi

Đóng gói **toàn bộ** SPA Vue hiện tại (cả 16 màn hình) thành một **PWA** mà người dùng cài thẳng từ trình duyệt lên màn hình chính, chạy full-screen như app native, trên **cả iOS lẫn Android**.

**Mức offline = Mức 1** (đã chốt): cài được + cache *vỏ app* (HTML/JS/CSS/icon) để mở tức thì và mở được cả khi mất mạng; **dữ liệu vẫn lấy/ghi online** qua REST. Không đồng bộ dữ liệu offline.

### Non-goals (KHÔNG làm ở v1)
- Không Capacitor / không build native / không lên App Store / Google Play.
- Không cache dữ liệu API để đọc offline (đó là Mức 2), không sync 2 chiều (Mức 3).
- Không web push notification (iOS hạn chế; để sau).
- Không sửa backend nghiệp vụ, không đổi màn hình, không đổi RBAC/persona.

### Tiêu chí thành công
1. Chrome Android: hiện lời mời "Cài đặt", cài xong có icon SupplyCore, mở full-screen (không thanh địa chỉ).
2. iOS Safari: "Thêm vào màn hình chính" → icon đúng, mở standalone, status bar đúng màu.
3. Mở app khi **tắt mạng** vẫn lên giao diện (vỏ từ cache), hiển thị trạng thái "cần kết nối" khi gọi dữ liệu.
4. Lighthouse → mục **PWA: Installable** đạt.
5. Đăng nhập + điều hướng + gọi API hoạt động y như bản web khi có mạng.

---

## 2. Kiến trúc

Thêm **3 mảnh** vào pipeline build/serve hiện có; mọi thứ khác giữ nguyên.

```
Điện thoại                              Frappe server (không đổi backend)
┌──────────────────────────┐           ┌─────────────────────────────────┐
│ Icon "SupplyCore"        │  HTTPS    │ /supplycore        → vỏ HTML     │
│  └ mở standalone         │ ────────▶ │ /assets/supplycore/frontend/ → JS/CSS │
│ manifest.webmanifest     │           │ /sw.js             → service worker│
│ Service Worker           │  vỏ: cache│ /supplycore/manifest.webmanifest │
│  └ precache vỏ app       │  data: net│ /api/...           → dữ liệu (cần mạng)│
└──────────────────────────┘           └─────────────────────────────────┘
```

**Mảnh 1 — Build PWA:** thêm `vite-plugin-pwa` (Workbox) vào `frontend/vite.config.js`. Sinh `sw.js` + `manifest.webmanifest` + precache manifest của các asset đã build (index.js, index.css, chunks, icon).

**Mảnh 2 — Icon & splash:** sinh bộ icon từ logo mark có sẵn (SVG inline trong `AppShell.vue`: ô bo góc gradient Navy `#7FB4E0→#1F4E79` + dấu cộng trắng). Kích thước: `192`, `512`, `512 maskable`, `apple-touch-icon 180`. Màu nền splash = Navy `#1F4E79`.

**Mảnh 3 — Nhúng vào shell** `supplycore/www/supplycore.html`: thẻ `<link rel=manifest>`, dải meta iOS, `theme-color`, `apple-touch-icon`, và đăng ký service worker.

---

## 3. Thiết kế chi tiết

### 3.1. Service Worker scope — điểm mấu chốt trên Frappe

**Vấn đề:** App chạy ở route `/supplycore/*`, nhưng asset (gồm cả `sw.js` nếu để mặc định) nằm ở `/assets/supplycore/frontend/`. SW chỉ kiểm soát được các URL **cùng hoặc sâu hơn đường dẫn của chính nó**. SW ở `/assets/.../sw.js` → scope `/assets/.../` → **không** kiểm soát `/supplycore` ⇒ app không bao giờ được SW phục vụ.

**Giải pháp:** phục vụ `sw.js` ở **gốc** `/sw.js` qua **`page_renderer` hook** của Frappe (hook tên SỐ ÍT — `frappe.get_hooks("page_renderer")`, xác nhận tại `frappe/website/path_resolver.py`), rồi đăng ký với scope `/supplycore/`.

- Tạo `supplycore/pwa.py` với class `ServiceWorkerRenderer` (`can_render()` khớp path `"sw.js"`, `render()` đọc file đã build `public/frontend/sw.js`) và khai báo `page_renderer = ["supplycore.pwa.ServiceWorkerRenderer"]` trong `hooks.py`. Trả về `werkzeug.Response` với:
  - `Content-Type: application/javascript`
  - `Service-Worker-Allowed: /supplycore/`
  - `Cache-Control: no-cache, max-age=0` (để bản SW mới luôn được kiểm tra)
- SW ở `/sw.js` (gốc) → được phép scope tới `/supplycore/`. Đăng ký:
  `navigator.serviceWorker.register('/sw.js', { scope: '/supplycore/' })`
- Tương tự, `manifest.webmanifest` phục vụ ở `/supplycore/manifest.webmanifest` qua www-controller (hoặc link tuyệt đối tới bản trong `/assets/...` — nội dung manifest mới là thứ quyết định scope, không phải vị trí file). Chọn **link tuyệt đối tới `/assets/supplycore/frontend/manifest.webmanifest`** cho đơn giản (manifest không bị ràng buộc scope như SW).

> Cách này **không cần sửa nginx** (tránh phụ thuộc sudo) — chỉ dùng cơ chế www route sẵn có của Frappe.

### 3.2. Cấu hình `vite-plugin-pwa`

Chế độ `generateSW` (Workbox tự sinh). Cấu hình chính trong `vite.config.js`:

- `registerType: 'autoUpdate'` — SW mới tự cài, kèm cơ chế nhắc reload (xem 3.5).
- `manifest`: xem 3.3.
- `workbox`:
  - `globPatterns: ['**/*.{js,css,png,svg,woff2}']` — precache vỏ app đã build.
  - `navigateFallback: '/supplycore'` — điều hướng SPA khi offline trả về vỏ shell.
  - `navigateFallbackAllowlist: [/^\/supplycore/]` — chỉ fallback cho route app.
  - `runtimeCaching`: API (`/api/`, `/method/`) → **NetworkOnly** (Mức 1 không cache dữ liệu).
  - Precache thêm vỏ shell: thêm `/supplycore` vào `additionalManifestEntries` (revision theo version build) để navigateFallback có nội dung khi offline.
- `scope: '/supplycore/'`, `base` giữ nguyên `/assets/supplycore/frontend/`.
- Output `sw.js` + `manifest.webmanifest` vào `public/frontend/` (cùng outDir hiện tại) để www-controller đọc lại.

### 3.3. Web App Manifest

```json
{
  "name": "SupplyCore — Cung ứng Bệnh viện",
  "short_name": "SupplyCore",
  "start_url": "/supplycore",
  "scope": "/supplycore/",
  "display": "standalone",
  "background_color": "#1F4E79",
  "theme_color": "#1F4E79",
  "lang": "vi",
  "icons": [
    { "src": "/assets/supplycore/frontend/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/assets/supplycore/frontend/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/assets/supplycore/frontend/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

`start_url`/`scope` là **đường dẫn tương đối gốc** ⇒ không phụ thuộc domain (chạy đúng dù qua ngrok ngẫu nhiên hay domain thật).

### 3.4. Icon & meta iOS (trong `supplycore/www/supplycore.html`)

Thêm vào `<head>`:
```html
<link rel="manifest" href="/assets/supplycore/frontend/manifest.webmanifest">
<meta name="theme-color" content="#1F4E79">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="SupplyCore">
<link rel="apple-touch-icon" href="/assets/supplycore/frontend/icons/apple-touch-icon.png">
```
Đăng ký SW: đặt trong `main.js` (sau khi app mount) thay vì inline shell, để dùng được API `virtual:pwa-register` nếu cần, nhưng **ép path `/sw.js` + scope `/supplycore/`**.

Sinh icon: script `frontend/scripts/gen-icons.mjs` dùng `sharp` render SVG mark → PNG các kích thước, ghi vào `frontend/public/frontend/icons/` (hoặc thư mục public của Vite để copy vào build). Maskable thêm padding an toàn ~10%.

### 3.5. Cập nhật phiên bản

Frappe đã cache-bust asset bằng `?v=timestamp`. Với SW `autoUpdate`:
- Khi có bản build mới, SW mới precache asset mới, `skipWaiting` + `clientsClaim`.
- App lắng nghe sự kiện cập nhật (`virtual:pwa-register` callback) → hiện toast "Có bản mới — tải lại" (dùng store toast sẵn có) thay vì reload đột ngột giữa thao tác.

### 3.6. Offline (Mức 1) — hành vi cụ thể

- **Mở app offline:** SW phục vụ vỏ từ precache → UI hiện lên.
- **Gọi dữ liệu khi offline:** API NetworkOnly → fetch lỗi → `api.js` đã có lớp dịch lỗi; thêm nhận diện lỗi mạng → hiện banner "Mất kết nối — dữ liệu cần mạng" (component nhỏ, dùng `navigator.onLine` + sự kiện `online/offline`).
- **CSRF:** vỏ shell chứa CSRF token do Frappe render. Bản cache có thể mang token cũ; chấp nhận ở Mức 1 vì mọi thao tác ghi đều cần mạng và `api.js` tự lấy lại CSRF khi có mạng. (Ghi chú rủi ro, không xử lý thêm ở v1.)

### 3.7. HTTPS để test (đã chốt: ngrok ngẫu nhiên)

PWA chỉ cài được qua HTTPS. Test bằng `ngrok http 80 --host-header=supplycore` (đã dựng ở phiên trước: symlink + nginx phục vụ `/assets`). Vì `start_url`/`scope` là path tương đối nên URL ngrok đổi vẫn chạy. Mở `https://<ngrok>/supplycore` trên điện thoại → cài.

---

## 4. Đơn vị công việc (để lập plan)

1. **Icon pipeline** — `gen-icons.mjs` + bộ PNG (độc lập, test bằng mắt).
2. **Vite PWA config** — thêm plugin, manifest, workbox (phụ thuộc #1 cho đường dẫn icon).
3. **www-controller** `sw.js.py` + header `Service-Worker-Allowed` (độc lập backend).
4. **Shell injection** — meta + manifest link trong `supplycore/www/supplycore.html`.
5. **SW registration + update toast** — trong `main.js` (phụ thuộc #2, #3).
6. **Offline banner** — component + lắng nghe `online/offline` (độc lập UI).
7. **Build & verify** — `yarn build` → bench, kiểm Lighthouse + cài thử Android/iOS qua ngrok.

Mỗi đơn vị có ranh giới rõ: input/output xác định, test được riêng.

---

## 5. Rủi ro & lưu ý

- **iOS cài thủ công**: Safari không có nút "Cài" tự động — người dùng phải "Thêm vào màn hình chính". Cần hướng dẫn ngắn (1 ảnh) cho người dùng iOS.
- **SW scope sai** = lỗi hay gặp nhất → đã xử lý bằng `/sw.js` gốc + scope `/supplycore/` + header allowed. Phải verify bằng `chrome://inspect` / Application tab.
- **Precache vỏ động (CSRF)**: như 3.6, chấp nhận ở v1.
- **`sw.js` qua www-controller** phải đọc đúng file build mỗi lần deploy; controller đọc động từ `public/frontend/sw.js` nên tự cập nhật theo build.
- **Đăng xuất/đa site**: scope giới hạn `/supplycore/` nên SW không đụng các route Frappe khác (`/app`, site khác).

---

## 6. Kiểm thử

- Lighthouse (Chrome DevTools) → PWA Installable pass, không lỗi manifest/SW.
- Application tab: Manifest hợp lệ, Service Worker `activated`, scope = `/supplycore/`, precache có index.js/css.
- Android Chrome: cài → mở standalone → tắt mạng mở lại → UI lên + banner offline.
- iOS Safari: Thêm vào màn hình chính → icon/tên/status bar đúng → mở standalone.
- Hồi quy: đăng nhập + 2–3 màn hình chính khi có mạng vẫn chạy như web.

---

## 7. Ghi chú triển khai — gotcha Frappe + PWA (đã gặp & xử lý)

Năm điểm non-obvious phát hiện khi implement (bắt qua review), ghi lại để khỏi vấp lại:

1. **Hook là `page_renderer` (SỐ ÍT).** Frappe đọc `frappe.get_hooks("page_renderer")` (`frappe/website/path_resolver.py`). `page_renderers` (số nhiều) chỉ là tên thư mục module → khai báo số nhiều sẽ bị bỏ qua âm thầm, `/sw.js` trả 404.
2. **Node 18 thiếu `globalThis.crypto`** cho workbox-build (qua worker threads). Script build mang cờ `NODE_OPTIONS=--experimental-global-webcrypto` (scope riêng app, không đụng Node của bench). KHÔNG nâng Node cả bench (socketio pin v18.20.8).
3. **Precache URL phải tuyệt đối.** SW phục vụ ở `/sw.js` (gốc) ⇒ Workbox phân giải URL tương đối theo gốc (`index.js` → `/index.js` 404). Dùng `manifestTransforms` ép entry globbed thành `/assets/supplycore/frontend/...`.
4. **`manifest.webmanifest` & runtime Workbox không vào manifestTransforms.** vite-plugin-pwa thêm manifest vào precache *sau* transform; runtime nạp qua `importScripts("./workbox-*.js")`. Cả hai phân giải về gốc → 404 → install fail. Xử lý: (a) `inlineWorkboxRuntime: true` (gộp runtime vào sw.js, bỏ importScripts); (b) page_renderer phục vụ thêm `/manifest.webmanifest` ở gốc.
5. **Scope phải đồng nhất, không lệch dấu `/`.** Vì URL canonical là `/supplycore` (không dấu `/`; `/supplycore/` bị nginx 301 về `/supplycore`), căn TẤT CẢ về `/supplycore`: manifest `start_url`+`scope`, VitePWA `scope`, `register()` scope, header `Service-Worker-Allowed`. `start_url` phải nằm trong `scope` (so khớp prefix).

**Reload sau deploy:** `page_renderer`/`pwa.py`/shell template được gunicorn `--preload` nạp lúc khởi động → đổi backend phải **restart web** (`sudo supervisorctl restart frappe-bench-frappe-web` hoặc `sudo bench restart`) + `bench --site supplycore clear-cache`. Build output `public/frontend/` bị gitignore → mỗi deploy phải `cd frontend && yarn build` lại.
