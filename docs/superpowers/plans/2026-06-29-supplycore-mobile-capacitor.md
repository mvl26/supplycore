# SupplyCore Mobile (Capacitor) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Đóng gói app Vue hiện tại thành app native (Capacitor) dùng chung dữ liệu Frappe, với server URL cấu hình được + token auth + 4 luồng mobile (tra cứu tồn/lô, duyệt phiếu, tiếp nhận, dashboard), web app giữ nguyên.

**Architecture:** Một codebase Vue. Native nhận diện qua `Capacitor.isNativePlatform()`: dùng base URL cấu hình + header `Authorization: token key:secret` (bỏ CSRF), bật CapacitorHttp để bỏ qua CORS; web giữ nguyên same-origin + session/CSRF. Backend thêm đúng 1 endpoint `mobile_login` vend api_key/secret. Mobile có shell riêng (bottom-tab, 4 màn hình) tái dùng stores/api/actions.

**Tech Stack:** Vue 3, Pinia, Vite, Frappe (Python), Capacitor 6 (`@capacitor/core`, `/cli`, `/android`, `/preferences`), `@capacitor-mlkit/barcode-scanning`.

## Global Constraints

- **Web không regress**: nhánh web trong `api.js` giữ nguyên `baseURL=''` (same-origin), `credentials:'include'`, CSRF như hiện tại. Mọi thay đổi `api.js` phải có nhánh `if (isNative())` riêng.
- **Chỉ thêm 1 backend surface mới**: `supplycore/api/mobile.py::mobile_login`. Không sửa REST/`actions.js`.
- **v1 online-only**: không offline/đồng bộ; không push notification (poll/in-app alerts).
- **DocType prefix `SC `** (có dấu cách), tiền VND precision=0 — hiển thị theo convention sẵn có.
- **Tiếng Việt** cho mọi UI text, không emoji (dùng `Icon.vue`/`icons.js`).
- Token lưu qua `@capacitor/preferences` key: `sc_server_url`, `sc_api_key`, `sc_api_secret`.

---

### Task 1: Backend endpoint `mobile_login`

**Files:**
- Create: `supplycore/api/mobile.py`
- Test: `supplycore/api/test_mobile.py`

**Interfaces:**
- Produces: `supplycore.api.mobile.mobile_login(usr, pwd) -> dict` trả `{ "api_key": str, "api_secret": str, "user": str, "full_name": str, "roles": [str] }`. Whitelisted `allow_guest=True`.

- [ ] **Step 1: Write the failing test**

```python
# supplycore/api/test_mobile.py
import frappe
import unittest
from supplycore.api.mobile import mobile_login


class TestMobileLogin(unittest.TestCase):
    def setUp(self):
        self.email = "mobiletest@example.com"
        if not frappe.db.exists("User", self.email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": self.email,
                "first_name": "Mobile",
                "send_welcome_email": 0,
                "new_password": "Secret#12345",
            }).insert(ignore_permissions=True)
        frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_valid_login_returns_token(self):
        res = mobile_login(self.email, "Secret#12345")
        self.assertEqual(res["user"], self.email)
        self.assertTrue(res["api_key"])
        self.assertTrue(res["api_secret"])
        self.assertIn("roles", res)

    def test_invalid_password_raises(self):
        with self.assertRaises(frappe.AuthenticationError):
            mobile_login(self.email, "wrong-password")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/hoangvietyeuem/frappe-bench && bench --site supplycore run-tests --app supplycore --module supplycore.api.test_mobile`
Expected: FAIL — `ModuleNotFoundError`/`ImportError: cannot import name 'mobile_login'`.

- [ ] **Step 3: Write minimal implementation**

```python
# supplycore/api/mobile.py
"""Mobile (Capacitor) API — token vending cho app native.

Chỉ surface mới so với web. App native gọi mobile_login để đổi
username/password lấy cặp api_key:api_secret, sau đó dùng header
Authorization: token key:secret cho mọi request (bỏ qua CSRF/CORS).
"""
import frappe
from frappe import _
from frappe.utils.password import update_password  # noqa: F401 (kept for parity)


@frappe.whitelist(allow_guest=True)
def mobile_login(usr, pwd):
    # Xác thực credentials bằng login manager của Frappe.
    login_manager = frappe.auth.LoginManager()
    login_manager.authenticate(user=usr, pwd=pwd)  # raise AuthenticationError nếu sai
    user = login_manager.user

    api_secret = _ensure_api_credentials(user)
    user_doc = frappe.get_doc("User", user)
    return {
        "user": user,
        "full_name": user_doc.full_name or user,
        "roles": [r.role for r in user_doc.get("roles", [])],
        "api_key": user_doc.api_key,
        "api_secret": api_secret,
    }


def _ensure_api_credentials(user):
    """Trả về api_secret. Sinh mới key+secret nếu user chưa có api_key.
    Frappe chỉ cho đọc secret rõ ngay sau khi generate; nếu user đã có key
    từ trước, ta tạo lại secret mới để đảm bảo vend được giá trị rõ."""
    user_doc = frappe.get_doc("User", user)
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)
    api_secret = frappe.generate_hash(length=15)
    user_doc.api_secret = api_secret
    user_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return api_secret
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/hoangvietyeuem/frappe-bench && bench --site supplycore run-tests --app supplycore --module supplycore.api.test_mobile`
Expected: PASS (2 tests).

- [ ] **Step 5: Verify endpoint reachable via REST**

Run: `cd /home/hoangvietyeuem/frappe-bench && bench --site supplycore execute "supplycore.api.mobile.mobile_login" --kwargs "{'usr':'Administrator','pwd':'<admin-pwd>'}"`
Expected: in ra dict có `api_key`, `api_secret`. (Nếu không biết mật khẩu admin, bỏ qua step này — test ở Step 4 đã đủ.)

- [ ] **Step 6: Commit**

```bash
git add supplycore/api/mobile.py supplycore/api/test_mobile.py
git commit -m "feat(mobile): endpoint mobile_login vend api_key/secret cho app native"
```

---

### Task 2: Frontend platform module (Capacitor wrapper + config store)

**Files:**
- Create: `frontend/src/platform.js`
- Test: `frontend/tests/platform.spec.js`

**Interfaces:**
- Produces:
  - `isNative(): boolean`
  - `getServerUrl(): Promise<string|null>` / `setServerUrl(url): Promise<void>`
  - `getToken(): Promise<{key:string, secret:string}|null>` / `setToken(key, secret): Promise<void>` / `clearToken(): Promise<void>`
  - Trên web (không có Capacitor) mọi getter trả `null` và `isNative()` trả `false`.

- [ ] **Step 1: Write the failing test**

```javascript
// frontend/tests/platform.spec.js
import { describe, it, expect, beforeEach, vi } from 'vitest'

// Giả lập KHÔNG có Capacitor (môi trường web): module phải chạy an toàn.
describe('platform (web fallback)', () => {
  beforeEach(() => { vi.resetModules() })

  it('isNative() trả false khi không có Capacitor', async () => {
    const p = await import('../src/platform.js')
    expect(p.isNative()).toBe(false)
  })

  it('getServerUrl()/getToken() trả null trên web', async () => {
    const p = await import('../src/platform.js')
    expect(await p.getServerUrl()).toBe(null)
    expect(await p.getToken()).toBe(null)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/platform.spec.js`
Expected: FAIL — `Cannot find module '../src/platform.js'`.

- [ ] **Step 3: Write minimal implementation**

```javascript
// frontend/src/platform.js
// Lớp trừu tượng Capacitor. An toàn trên web (Capacitor không tồn tại):
// isNative()=false, mọi getter trả null. Trên native dùng @capacitor/preferences.

let _cap = null
let _prefs = null
try {
  // Các import này chỉ resolve khi đã cài Capacitor (Task 4). Dùng require động
  // qua import() được Vite tree-shake; bọc try để web build không vỡ nếu thiếu.
  // eslint-disable-next-line
  _cap = (typeof window !== 'undefined' && window.Capacitor) ? window.Capacitor : null
} catch (e) { _cap = null }

export function isNative() {
  return !!(_cap && _cap.isNativePlatform && _cap.isNativePlatform())
}

async function prefs() {
  if (_prefs) return _prefs
  if (!isNative()) return null
  const mod = await import('@capacitor/preferences')
  _prefs = mod.Preferences
  return _prefs
}

const K_URL = 'sc_server_url'
const K_KEY = 'sc_api_key'
const K_SECRET = 'sc_api_secret'

export async function getServerUrl() {
  const p = await prefs(); if (!p) return null
  const { value } = await p.get({ key: K_URL }); return value || null
}
export async function setServerUrl(url) {
  const p = await prefs(); if (!p) return
  await p.set({ key: K_URL, value: String(url).replace(/\/+$/, '') })
}
export async function getToken() {
  const p = await prefs(); if (!p) return null
  const k = (await p.get({ key: K_KEY })).value
  const s = (await p.get({ key: K_SECRET })).value
  return (k && s) ? { key: k, secret: s } : null
}
export async function setToken(key, secret) {
  const p = await prefs(); if (!p) return
  await p.set({ key: K_KEY, value: key })
  await p.set({ key: K_SECRET, value: secret })
}
export async function clearToken() {
  const p = await prefs(); if (!p) return
  await p.remove({ key: K_KEY }); await p.remove({ key: K_SECRET })
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/platform.spec.js`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/platform.js frontend/tests/platform.spec.js
git commit -m "feat(mobile): platform.js wrapper Capacitor + config/token store (web-safe)"
```

---

### Task 3: `api.js` dual-mode (base URL + token header)

**Files:**
- Modify: `frontend/src/api.js` (hàm `request` quanh dòng 12-37; thêm helper trên đầu file)
- Test: `frontend/tests/api-dualmode.spec.js`

**Interfaces:**
- Consumes: `isNative`, `getServerUrl`, `getToken` từ `platform.js`.
- Produces: `request(path, options)` không đổi chữ ký; nội bộ prefix base URL + header token khi native. Thêm export `resolveUrl(path): Promise<string>` để test.

- [ ] **Step 1: Write the failing test**

```javascript
// frontend/tests/api-dualmode.spec.js
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('api dual-mode resolveUrl (web)', () => {
  beforeEach(() => vi.resetModules())

  it('web: resolveUrl giữ path tương đối', async () => {
    const api = await import('../src/api.js')
    expect(await api.resolveUrl('/api/method/x')).toBe('/api/method/x')
  })
})

describe('api dual-mode resolveUrl (native)', () => {
  beforeEach(() => vi.resetModules())

  it('native: prefix server URL đã cấu hình', async () => {
    vi.doMock('../src/platform.js', () => ({
      isNative: () => true,
      getServerUrl: async () => 'https://bv-abc.example.com',
      getToken: async () => ({ key: 'K', secret: 'S' }),
    }))
    const api = await import('../src/api.js')
    expect(await api.resolveUrl('/api/method/x'))
      .toBe('https://bv-abc.example.com/api/method/x')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run tests/api-dualmode.spec.js`
Expected: FAIL — `api.resolveUrl is not a function`.

- [ ] **Step 3: Write minimal implementation**

Thêm import + helper ở đầu `api.js` (sau dòng `const getCsrf = ...` block, trước `async function request`):

```javascript
import { isNative, getServerUrl, getToken } from './platform'

// Native: prefix base URL đã cấu hình. Web: giữ path tương đối (same-origin).
export async function resolveUrl(path) {
  if (!isNative()) return path
  const base = await getServerUrl()
  if (!base) return path
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`
}

async function authHeaders() {
  if (!isNative()) return {} // web dùng CSRF như cũ
  const t = await getToken()
  return t ? { Authorization: `token ${t.key}:${t.secret}` } : {}
}
```

Sửa thân `request` để dùng chúng:

```javascript
async function request(path, options = {}) {
  const isForm = options.body instanceof FormData
  const headers = {
    'Accept': 'application/json',
    // Web: gửi CSRF. Native: không cần CSRF (token auth) — vẫn vô hại nếu rỗng.
    'X-Frappe-CSRF-Token': isNative() ? '' : (_csrf || getCsrf() || ''),
    ...(await authHeaders()),
    ...(options.headers || {}),
  }
  if (!isForm) headers['Content-Type'] = 'application/json'
  const url = await resolveUrl(path)
  const res = await fetch(url, {
    // Native dùng token (không cookie); web giữ 'include' để gửi session cookie.
    credentials: isNative() ? 'omit' : 'include',
    ...options,
    headers,
  })
  let body = null
  try { body = await res.json() } catch (e) { /* ignore */ }
  if (!res.ok) {
    const msg = parseFrappeError(body) || `HTTP ${res.status}`
    const err = new Error(msg)
    err.status = res.status
    err.body = body
    throw err
  }
  return body
}
```

(Lưu ý: nếu còn chỗ thứ 2 dùng `fetch` trực tiếp — quanh dòng 225 cũ — áp dụng cùng pattern `resolveUrl` + `authHeaders`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run tests/api-dualmode.spec.js`
Expected: PASS (2 tests).

- [ ] **Step 5: Verify web không regress**

Run: `cd frontend && npx vitest run`
Expected: toàn bộ test cũ PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api.js frontend/tests/api-dualmode.spec.js
git commit -m "feat(mobile): api.js dual-mode base URL + token header (web giữ same-origin/CSRF)"
```

---

### Task 4: Cài Capacitor + cấu hình + scaffold Android

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/capacitor.config.ts`
- Create (tự sinh): `frontend/android/` (qua `npx cap add android`)

**Interfaces:**
- Produces: thư mục `android/` build được; `window.Capacitor` tồn tại khi chạy native; CapacitorHttp bật.

- [ ] **Step 1: Cài dependencies**

Run:
```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/preferences @capacitor-mlkit/barcode-scanning
```
Expected: cài xong, `package.json` có các package trên.

- [ ] **Step 2: Tạo capacitor.config.ts**

```typescript
// frontend/capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'vn.com.miyano.supplycore',
  appName: 'SupplyCore',
  // webDir trỏ tới build SPA của Vite. Xác nhận output thực tế ở vite.config.js
  // (hiện build vào ../supplycore/public/frontend); copy ra dist trước khi sync.
  webDir: 'dist',
  server: { androidScheme: 'https' },
  plugins: {
    CapacitorHttp: { enabled: true }, // bỏ qua CORS browser cho request native
  },
}

export default config
```

- [ ] **Step 3: Build web + sync Android**

Run:
```bash
cd frontend
npm run build -- --outDir dist
npx cap add android
npx cap sync android
```
Expected: `android/` được tạo, `cap sync` báo `✔ Sync finished`.

- [ ] **Step 4: Verify Capacitor có mặt**

Run: `cd frontend && node -e "console.log(require('@capacitor/core/package.json').version)"`
Expected: in version (vd `6.x.x`).

- [ ] **Step 5: Cập nhật .gitignore**

Thêm vào `frontend/.gitignore` (tạo nếu chưa có) — KHÔNG commit build artifact native nặng nhưng GIỮ config:
```
android/app/build/
android/.gradle/
android/local.properties
dist/
```

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/capacitor.config.ts frontend/.gitignore frontend/android
git commit -m "build(mobile): cài Capacitor + scaffold Android + bật CapacitorHttp"
```

---

### Task 5: Mobile shell + entry routing (native → bottom-tab)

**Files:**
- Create: `frontend/src/mobile/MobileShell.vue`
- Create: `frontend/src/mobile/mobileRoutes.js`
- Modify: `frontend/src/router.js` (thêm nhánh native), `frontend/src/main.js` (gắn `window.Capacitor` nếu cần)

**Interfaces:**
- Consumes: `isNative()` từ `platform.js`.
- Produces: route `/m/*` cho mobile; `MobileShell` render `<router-view>` + bottom-tab 4 mục (Tra cứu, Duyệt, Tiếp nhận, Dashboard). Khi `isNative()` và chưa cấu hình/đăng nhập → điều hướng tới `/m/setup`.

- [ ] **Step 1: Tạo mobileRoutes.js (4 màn hình + setup, dùng lazy import)**

```javascript
// frontend/src/mobile/mobileRoutes.js
export const mobileRoutes = [
  { path: '/m/setup', name: 'mSetup', component: () => import('./ServerLogin.vue'), meta: { public: true, mobile: true, layout: 'mobile-blank' } },
  {
    path: '/m', component: () => import('./MobileShell.vue'), meta: { mobile: true },
    children: [
      { path: '', redirect: '/m/lookup' },
      { path: 'lookup', name: 'mLookup', component: () => import('./screens/StockLookup.vue'), meta: { mobile: true, title: 'Tra cứu' } },
      { path: 'approve', name: 'mApprove', component: () => import('./screens/ApproveDocs.vue'), meta: { mobile: true, title: 'Duyệt phiếu' } },
      { path: 'receiving', name: 'mReceiving', component: () => import('./screens/Receiving.vue'), meta: { mobile: true, title: 'Tiếp nhận' } },
      { path: 'dashboard', name: 'mDashboard', component: () => import('./screens/MobileDashboard.vue'), meta: { mobile: true, title: 'Bảng tin' } },
    ],
  },
]
```

- [ ] **Step 2: Tạo MobileShell.vue (bottom-tab)**

```vue
<!-- frontend/src/mobile/MobileShell.vue -->
<template>
  <div class="m-shell">
    <main class="m-content"><router-view /></main>
    <nav class="m-tabbar">
      <router-link v-for="t in tabs" :key="t.to" :to="t.to" class="m-tab" active-class="m-tab--active">
        <Icon :name="t.icon" :size="22" />
        <span>{{ t.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import Icon from '../components/Icon.vue'
const tabs = [
  { to: '/m/lookup', icon: 'layers', label: 'Tra cứu' },
  { to: '/m/approve', icon: 'clipboard-check', label: 'Duyệt' },
  { to: '/m/receiving', icon: 'truck', label: 'Tiếp nhận' },
  { to: '/m/dashboard', icon: 'bar-chart', label: 'Bảng tin' },
]
</script>

<style scoped>
.m-shell { display: flex; flex-direction: column; height: 100vh; }
.m-content { flex: 1; overflow-y: auto; padding: 12px; padding-bottom: 72px; }
.m-tabbar { position: fixed; bottom: 0; left: 0; right: 0; height: 60px;
  display: flex; border-top: 1px solid #e5e7eb; background: #fff; }
.m-tab { flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 2px; font-size: 11px; color: #6b7280; text-decoration: none; }
.m-tab--active { color: #1F4E79; }
</style>
```

> Xác minh `components/Icon.vue` tồn tại + các icon `layers/clipboard-check/truck/bar-chart` có trong `icons.js` (đã thấy dùng trong `modules.js`). Nếu thiếu icon nào, thêm vào `icons.js`.

- [ ] **Step 3: Gắn mobileRoutes + guard vào router.js**

Trong `frontend/src/router.js`: import và spread routes, thêm guard đẩy native vào `/m`:

```javascript
import { mobileRoutes } from './mobile/mobileRoutes'
import { isNative } from './platform'
import { getServerUrl, getToken } from './platform'
// ... trong mảng routes: thêm ...mobileRoutes vào TRƯỚC route catch-all 404.

// Sau khi tạo router, thêm guard (bổ sung, không thay guard sẵn có):
router.beforeEach(async (to) => {
  if (!isNative()) {
    // Trên native bundle, nếu lỡ vào route web → ép sang mobile.
    return true
  }
  if (to.meta.mobile) {
    if (to.name === 'mSetup') return true
    const ok = (await getServerUrl()) && (await getToken())
    return ok ? true : { name: 'mSetup' }
  }
  // Native mà route không phải mobile → chuyển vào shell mobile.
  return { path: '/m' }
})
```

- [ ] **Step 4: Run web test suite (đảm bảo không vỡ web)**

Run: `cd frontend && npx vitest run`
Expected: PASS toàn bộ (mobile routes lazy — không ảnh hưởng web).

- [ ] **Step 5: Build kiểm tra biên dịch**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build thành công, không lỗi import.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/mobile/MobileShell.vue frontend/src/mobile/mobileRoutes.js frontend/src/router.js
git commit -m "feat(mobile): shell bottom-tab + routing native /m/*"
```

---

### Task 6: Màn hình cấu hình server + đăng nhập (`ServerLogin.vue`)

**Files:**
- Create: `frontend/src/mobile/ServerLogin.vue`
- Modify: `frontend/src/stores/auth.js` (thêm action `mobileLogin`)
- Modify: `frontend/src/api.js` (thêm `mobileLoginApi`)

**Interfaces:**
- Consumes: `setServerUrl`, `setToken` từ `platform.js`; `call`/`request` từ `api.js`.
- Produces:
  - `api.js`: `mobileLoginApi(serverUrl, usr, pwd) -> { api_key, api_secret, user, full_name, roles }`
  - `auth.js`: action `mobileLogin(serverUrl, usr, pwd) -> boolean` (lưu config+token, set `this.user`).

- [ ] **Step 1: Thêm `mobileLoginApi` vào api.js**

```javascript
// Gọi endpoint vend token. Phải gọi TRƯỚC khi có token → tự dựng URL tuyệt đối.
export async function mobileLoginApi(serverUrl, usr, pwd) {
  const base = String(serverUrl).replace(/\/+$/, '')
  const res = await fetch(`${base}/api/method/supplycore.api.mobile.mobile_login`, {
    method: 'POST',
    credentials: 'omit',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify({ usr, pwd }),
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new Error(parseFrappeError(body) || `HTTP ${res.status}`)
  return body.message // Frappe bọc kết quả whitelisted trong .message
}
```

- [ ] **Step 2: Thêm action `mobileLogin` vào auth.js**

```javascript
// trong actions: {} của useAuthStore
import { setServerUrl, setToken } from '../platform'
import { mobileLoginApi } from '../api'
// ...
async mobileLogin(serverUrl, usr, pwd) {
  this.loginError = null
  this.loginLoading = true
  try {
    const r = await mobileLoginApi(serverUrl, usr, pwd)
    await setServerUrl(serverUrl)
    await setToken(r.api_key, r.api_secret)
    this.user = { name: r.user, full_name: r.full_name, email: r.user,
      is_guest: false, roles: r.roles || [] }
    this.booted = true
    await useAccessStore().load(true)
    return true
  } catch (e) {
    this.loginError = e.message || 'Đăng nhập thất bại'
    return false
  } finally {
    this.loginLoading = false
  }
},
```

- [ ] **Step 3: Tạo ServerLogin.vue**

```vue
<!-- frontend/src/mobile/ServerLogin.vue -->
<template>
  <div class="m-login">
    <h1 class="m-login__title">SupplyCore</h1>
    <label class="m-field">
      <span>Địa chỉ máy chủ</span>
      <input v-model="serverUrl" type="url" inputmode="url" placeholder="https://bv-abc.example.com" />
    </label>
    <label class="m-field">
      <span>Tài khoản</span>
      <input v-model="usr" type="text" autocapitalize="none" autocomplete="username" />
    </label>
    <label class="m-field">
      <span>Mật khẩu</span>
      <input v-model="pwd" type="password" autocomplete="current-password" />
    </label>
    <p v-if="auth.loginError" class="m-error">{{ auth.loginError }}</p>
    <button class="m-btn" :disabled="auth.loginLoading || !valid" @click="submit">
      {{ auth.loginLoading ? 'Đang đăng nhập…' : 'Đăng nhập' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const serverUrl = ref('')
const usr = ref('')
const pwd = ref('')
const valid = computed(() => /^https?:\/\/.+/.test(serverUrl.value) && usr.value && pwd.value)

async function submit() {
  const ok = await auth.mobileLogin(serverUrl.value.trim(), usr.value.trim(), pwd.value)
  if (ok) router.replace('/m/lookup')
}
</script>

<style scoped>
.m-login { padding: 24px 18px; display: flex; flex-direction: column; gap: 16px; max-width: 420px; margin: 0 auto; }
.m-login__title { color: #1F4E79; font-size: 26px; font-weight: 700; text-align: center; margin-top: 32px; }
.m-field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: #374151; }
.m-field input { border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; font-size: 16px; }
.m-btn { background: #1F4E79; color: #fff; border: none; border-radius: 8px; padding: 14px; font-size: 16px; font-weight: 600; }
.m-btn:disabled { opacity: .5; }
.m-error { color: #b91c1c; font-size: 13px; }
</style>
```

- [ ] **Step 4: Run web tests**

Run: `cd frontend && npx vitest run`
Expected: PASS (auth.js thay đổi không phá test web; nếu có test auth, cập nhật mock cho `mobileLoginApi`).

- [ ] **Step 5: Build kiểm tra**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build OK.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/mobile/ServerLogin.vue frontend/src/stores/auth.js frontend/src/api.js
git commit -m "feat(mobile): màn hình cấu hình server + đăng nhập token"
```

---

### Task 7: Màn hình Tra cứu tồn/lô + quét barcode (`StockLookup.vue`)

**Files:**
- Create: `frontend/src/mobile/screens/StockLookup.vue`
- Create: `frontend/src/mobile/useScanner.js`

**Interfaces:**
- Consumes: `getList`/`call` từ `api.js`.
- Produces: `useScanner()` trả `{ scan(): Promise<string|null> }` dùng `@capacitor-mlkit/barcode-scanning` (trả null nếu không native/không quyền).

- [ ] **Step 1: Tạo useScanner.js**

```javascript
// frontend/src/mobile/useScanner.js
import { isNative } from '../platform'

export function useScanner() {
  async function scan() {
    if (!isNative()) return null
    const { BarcodeScanner } = await import('@capacitor-mlkit/barcode-scanning')
    const perm = await BarcodeScanner.requestPermissions()
    if (perm.camera !== 'granted' && perm.camera !== 'limited') return null
    const { barcodes } = await BarcodeScanner.scan()
    return barcodes?.[0]?.rawValue || null
  }
  return { scan }
}
```

- [ ] **Step 2: Tạo StockLookup.vue**

```vue
<!-- frontend/src/mobile/screens/StockLookup.vue -->
<template>
  <div class="m-page">
    <div class="m-searchbar">
      <input v-model="q" placeholder="Tên / mã vật tư" @keyup.enter="search" />
      <button class="m-icon-btn" @click="onScan" title="Quét mã"><Icon name="search" :size="20" /></button>
    </div>
    <p v-if="loading" class="m-muted">Đang tải…</p>
    <ul class="m-list">
      <li v-for="r in rows" :key="r.item_code + r.warehouse + r.batch_no" class="m-card">
        <div class="m-card__title">{{ r.item_name || r.item_code }}</div>
        <div class="m-card__row"><span>Kho</span><b>{{ r.warehouse }}</b></div>
        <div class="m-card__row"><span>Lô</span><b>{{ r.batch_no || '—' }}</b></div>
        <div class="m-card__row"><span>Tồn</span><b>{{ r.qty }}</b></div>
        <div class="m-card__row"><span>HSD</span><b>{{ r.expiry_date || '—' }}</b></div>
      </li>
    </ul>
    <p v-if="!loading && !rows.length && searched" class="m-muted">Không có kết quả.</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Icon from '../../components/Icon.vue'
import { getList } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'

const q = ref(''); const rows = ref([]); const loading = ref(false); const searched = ref(false)
const { scan } = useScanner()
const toast = useToastStore()

async function search() {
  loading.value = true; searched.value = true
  try {
    // Tra theo lô tồn kho. Doctype SC Stock Ledger Entry / batch balance —
    // dùng getList với filter item_name like. XÁC MINH tên doctype + field
    // thực tế trong schemas.js trước khi chốt (vd 'SC Batch' / 'SC Stock Ledger Entry').
    rows.value = await getList('SC Batch', {
      filters: q.value ? [['item_name', 'like', `%${q.value}%`]] : [],
      fields: ['item_code', 'item_name', 'warehouse', 'batch_no', 'qty', 'expiry_date'],
      limit_page_length: 50,
      order_by: 'expiry_date asc', // FEFO
    })
  } catch (e) { toast.push(e.message, 'error') }
  finally { loading.value = false }
}

async function onScan() {
  const code = await scan()
  if (code) { q.value = code; search() }
  else toast.push('Không quét được mã (kiểm tra quyền camera).', 'warning')
}
</script>

<style scoped>
.m-page { display: flex; flex-direction: column; gap: 12px; }
.m-searchbar { display: flex; gap: 8px; }
.m-searchbar input { flex: 1; border: 1px solid #d1d5db; border-radius: 8px; padding: 10px; font-size: 16px; }
.m-icon-btn { border: 1px solid #d1d5db; border-radius: 8px; background: #fff; padding: 0 12px; }
.m-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.m-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; }
.m-card__title { font-weight: 600; color: #1F4E79; margin-bottom: 6px; }
.m-card__row { display: flex; justify-content: space-between; font-size: 13px; color: #4b5563; padding: 2px 0; }
.m-muted { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
```

> **XÁC MINH trước khi code**: tên doctype + field tồn kho/lô thật. Mở `frontend/src/schemas.js` và `frontend/src/pages/StockBalance.vue` / `BatchTrace.vue` để lấy doctype + field đúng (vd có thể là `SC Stock Ledger Entry` với `actual_qty`, hoặc một report method `call('supplycore.api.stock.balance', ...)`). Sửa filter/fields/order_by cho khớp; giữ `order_by` theo HSD để đúng FEFO.

- [ ] **Step 3: Build kiểm tra biên dịch**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/mobile/screens/StockLookup.vue frontend/src/mobile/useScanner.js
git commit -m "feat(mobile): màn tra cứu tồn/lô + quét barcode (FEFO)"
```

---

### Task 8: Màn hình Duyệt/ký phiếu (`ApproveDocs.vue`)

**Files:**
- Create: `frontend/src/mobile/screens/ApproveDocs.vue`

**Interfaces:**
- Consumes: `getList`, `submitDoc`, `runDocMethod` từ `api.js`; `ACTIONS` từ `actions.js`.
- Produces: danh sách phiếu `docstatus=0` của các doctype duyệt được; nút Duyệt (submit) / mở chi tiết.

- [ ] **Step 1: Xác minh action duyệt thực tế**

Mở `frontend/src/actions.js` đọc `ACTIONS` để biết doctype nào có hành động "Duyệt"/submit và method gọi (vd `submitDoc(dt,name)` hay `runDocMethod(dt,name,'approve')`). Liệt kê doctype mục tiêu (PO/chuyển kho/cấp phát/thanh toán) + cách submit đúng. Dùng kết quả này ở Step 2.

- [ ] **Step 2: Tạo ApproveDocs.vue**

```vue
<!-- frontend/src/mobile/screens/ApproveDocs.vue -->
<template>
  <div class="m-page">
    <div class="m-tabs">
      <button v-for="d in doctypes" :key="d.dt"
        :class="['m-chip', d.dt === active ? 'm-chip--on' : '']" @click="select(d.dt)">
        {{ d.label }}
      </button>
    </div>
    <p v-if="loading" class="m-muted">Đang tải…</p>
    <ul class="m-list">
      <li v-for="r in rows" :key="r.name" class="m-card">
        <div class="m-card__title">{{ r.name }}</div>
        <div class="m-card__row"><span>Ngày</span><b>{{ r.creation?.slice(0,10) }}</b></div>
        <div class="m-actions">
          <button class="m-btn m-btn--ok" :disabled="busy===r.name" @click="approve(r)">Duyệt</button>
        </div>
      </li>
    </ul>
    <p v-if="!loading && !rows.length" class="m-muted">Không có phiếu chờ duyệt.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getList, submitDoc } from '../../api'
import { useToastStore } from '../../stores/toast'

// XÁC MINH danh sách doctype + nhãn theo actions.js/personas.
const doctypes = [
  { dt: 'SC Purchase Order', label: 'Đặt mua' },
  { dt: 'SC Transfer Request', label: 'Chuyển kho' },
  { dt: 'SC Patient Dispensing', label: 'Cấp phát' },
]
const active = ref(doctypes[0].dt)
const rows = ref([]); const loading = ref(false); const busy = ref(null)
const toast = useToastStore()

async function load() {
  loading.value = true
  try {
    rows.value = await getList(active.value, {
      filters: [['docstatus', '=', 0]],
      fields: ['name', 'creation'],
      order_by: 'creation desc', limit_page_length: 50,
    })
  } catch (e) { toast.push(e.message, 'error') }
  finally { loading.value = false }
}
function select(dt) { active.value = dt; load() }

async function approve(r) {
  busy.value = r.name
  try {
    await submitDoc(active.value, r.name) // submit = duyệt; đổi sang runDocMethod nếu actions.js yêu cầu
    toast.push(`Đã duyệt ${r.name}`, 'success')
    rows.value = rows.value.filter(x => x.name !== r.name)
  } catch (e) { toast.push(e.message, 'error') }
  finally { busy.value = null }
}
onMounted(load)
</script>

<style scoped>
.m-page { display: flex; flex-direction: column; gap: 12px; }
.m-tabs { display: flex; gap: 8px; overflow-x: auto; }
.m-chip { white-space: nowrap; border: 1px solid #d1d5db; background: #fff; border-radius: 999px; padding: 6px 12px; font-size: 13px; }
.m-chip--on { background: #1F4E79; color: #fff; border-color: #1F4E79; }
.m-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.m-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; }
.m-card__title { font-weight: 600; color: #1F4E79; }
.m-card__row { display: flex; justify-content: space-between; font-size: 13px; color: #4b5563; padding: 2px 0; }
.m-actions { margin-top: 8px; display: flex; gap: 8px; }
.m-btn--ok { background: #16a34a; color: #fff; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; }
.m-muted { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
```

- [ ] **Step 3: Build kiểm tra**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/mobile/screens/ApproveDocs.vue
git commit -m "feat(mobile): màn duyệt/ký phiếu chờ"
```

---

### Task 9: Màn hình Tiếp nhận/nhập kho (`Receiving.vue`)

**Files:**
- Create: `frontend/src/mobile/screens/Receiving.vue`

**Interfaces:**
- Consumes: `getList`, `getDoc`, `runDocMethod`/`updateDoc`/`submitDoc` từ `api.js`; `useScanner` từ Task 7.
- Produces: danh sách phiếu nhận chờ (vd `SC Purchase Receipt` draft) → quét mã/nhập số lượng thực nhận → xác nhận.

- [ ] **Step 1: Xác minh luồng tiếp nhận thật**

Mở `frontend/src/pages/` (vd Putaway/receipt) + `actions.js` + `schemas.js` để xác định: doctype nhận hàng (vd `SC Purchase Receipt`), child item field (vd `items`), field số lượng thực nhận (vd `received_qty`/`qty`), và cách submit. Ghi lại tên chính xác trước khi code Step 2.

- [ ] **Step 2: Tạo Receiving.vue**

```vue
<!-- frontend/src/mobile/screens/Receiving.vue -->
<template>
  <div class="m-page">
    <h2 class="m-h2">Phiếu nhận chờ xử lý</h2>
    <p v-if="loading" class="m-muted">Đang tải…</p>
    <ul v-if="!current" class="m-list">
      <li v-for="r in rows" :key="r.name" class="m-card" @click="open(r.name)">
        <div class="m-card__title">{{ r.name }}</div>
        <div class="m-card__row"><span>NCC</span><b>{{ r.supplier || '—' }}</b></div>
      </li>
    </ul>
    <p v-if="!loading && !rows.length && !current" class="m-muted">Không có phiếu nhận chờ.</p>

    <div v-if="current" class="m-detail">
      <button class="m-link" @click="current=null">← Danh sách</button>
      <h3 class="m-card__title">{{ current.name }}</h3>
      <div v-for="(it, i) in current.items" :key="i" class="m-card">
        <div class="m-card__title">{{ it.item_name || it.item_code }}</div>
        <label class="m-field"><span>SL thực nhận</span>
          <input v-model.number="it.received_qty" type="number" inputmode="decimal" />
        </label>
        <button class="m-icon-btn" @click="scanTo(it)"><Icon name="search" :size="18" /> Quét lô</button>
        <div v-if="it._batch" class="m-card__row"><span>Lô quét</span><b>{{ it._batch }}</b></div>
      </div>
      <button class="m-btn m-btn--ok" :disabled="saving" @click="confirm">Xác nhận nhận</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Icon from '../../components/Icon.vue'
import { getList, getDoc, updateDoc, submitDoc } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'

const DT = 'SC Purchase Receipt' // XÁC MINH ở Step 1
const rows = ref([]); const current = ref(null)
const loading = ref(false); const saving = ref(false)
const { scan } = useScanner(); const toast = useToastStore()

async function load() {
  loading.value = true
  try {
    rows.value = await getList(DT, {
      filters: [['docstatus', '=', 0]],
      fields: ['name', 'supplier'], order_by: 'creation desc', limit_page_length: 50,
    })
  } catch (e) { toast.push(e.message, 'error') } finally { loading.value = false }
}
async function open(name) {
  try { current.value = await getDoc(DT, name) }
  catch (e) { toast.push(e.message, 'error') }
}
async function scanTo(it) {
  const code = await scan()
  if (code) it._batch = code
  else toast.push('Không quét được mã.', 'warning')
}
async function confirm() {
  saving.value = true
  try {
    await updateDoc(DT, current.value.name, { items: current.value.items })
    await submitDoc(DT, current.value.name)
    toast.push('Đã xác nhận nhận hàng.', 'success')
    current.value = null; await load()
  } catch (e) { toast.push(e.message, 'error') } finally { saving.value = false }
}
onMounted(load)
</script>

<style scoped>
.m-page { display: flex; flex-direction: column; gap: 12px; }
.m-h2 { font-size: 16px; font-weight: 600; color: #1F4E79; }
.m-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.m-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; }
.m-card__title { font-weight: 600; color: #1F4E79; }
.m-card__row { display: flex; justify-content: space-between; font-size: 13px; color: #4b5563; padding: 2px 0; }
.m-field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; margin: 8px 0; }
.m-field input { border: 1px solid #d1d5db; border-radius: 8px; padding: 10px; font-size: 16px; }
.m-icon-btn { border: 1px solid #d1d5db; border-radius: 8px; background: #fff; padding: 8px 12px; font-size: 13px; display: inline-flex; gap: 6px; align-items: center; }
.m-btn--ok { background: #16a34a; color: #fff; border: none; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: 600; }
.m-link { background: none; border: none; color: #2E75B6; font-size: 14px; padding: 0; }
.m-muted { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
```

- [ ] **Step 3: Build kiểm tra**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/mobile/screens/Receiving.vue
git commit -m "feat(mobile): màn tiếp nhận/nhập kho + quét lô"
```

---

### Task 10: Màn hình Dashboard & Cảnh báo (`MobileDashboard.vue`)

**Files:**
- Create: `frontend/src/mobile/screens/MobileDashboard.vue`

**Interfaces:**
- Consumes: `call`/`getList`/`count` từ `api.js`; logout từ `auth.js`.
- Produces: thẻ tóm tắt (số phiếu chờ, sắp hết hạn, tồn thấp) + danh sách cảnh báo, có nút làm mới (poll thủ công) và đăng xuất.

- [ ] **Step 1: Xác minh nguồn dữ liệu cảnh báo**

Mở `frontend/src/pages/Dashboard.vue` + `AlertCenter.vue` để tái dùng đúng method/endpoint cảnh báo (vd `call('supplycore.api.dashboard.summary')` hoặc getList `SC Alert`). Ghi lại tên + shape trả về dùng ở Step 2.

- [ ] **Step 2: Tạo MobileDashboard.vue**

```vue
<!-- frontend/src/mobile/screens/MobileDashboard.vue -->
<template>
  <div class="m-page">
    <div class="m-head">
      <div><div class="m-hi">Xin chào</div><b>{{ auth.user.full_name }}</b></div>
      <button class="m-link" @click="logout">Đăng xuất</button>
    </div>
    <div class="m-kpis">
      <div class="m-kpi"><span>{{ kpi.pending }}</span><label>Chờ duyệt</label></div>
      <div class="m-kpi"><span>{{ kpi.expiring }}</span><label>Sắp hết hạn</label></div>
      <div class="m-kpi"><span>{{ kpi.lowstock }}</span><label>Tồn thấp</label></div>
    </div>
    <div class="m-head"><h2 class="m-h2">Cảnh báo</h2><button class="m-link" @click="load">Làm mới</button></div>
    <p v-if="loading" class="m-muted">Đang tải…</p>
    <ul class="m-list">
      <li v-for="(a, i) in alerts" :key="i" class="m-card">
        <div class="m-card__title">{{ a.title }}</div>
        <div class="m-card__row"><span>{{ a.message }}</span></div>
      </li>
    </ul>
    <p v-if="!loading && !alerts.length" class="m-muted">Không có cảnh báo.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getList, count } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { clearToken } from '../../platform'
import { useToastStore } from '../../stores/toast'

const auth = useAuthStore(); const router = useRouter(); const toast = useToastStore()
const kpi = ref({ pending: 0, expiring: 0, lowstock: 0 })
const alerts = ref([]); const loading = ref(false)

async function load() {
  loading.value = true
  try {
    // XÁC MINH method/doctype thật ở Step 1. Tạm dùng count + getList SC Alert.
    kpi.value.pending = await count('SC Purchase Order', { docstatus: 0 })
    alerts.value = await getList('SC Alert', {
      fields: ['title', 'message'], filters: [['status', '=', 'Open']],
      order_by: 'creation desc', limit_page_length: 50,
    })
  } catch (e) { toast.push(e.message, 'error') } finally { loading.value = false }
}
async function logout() {
  await clearToken(); auth.user = { name: 'Guest', is_guest: true, roles: [] }
  auth.booted = false; router.replace('/m/setup')
}
onMounted(load)
</script>

<style scoped>
.m-page { display: flex; flex-direction: column; gap: 14px; }
.m-head { display: flex; justify-content: space-between; align-items: center; }
.m-hi { font-size: 12px; color: #9ca3af; }
.m-h2 { font-size: 16px; font-weight: 600; color: #1F4E79; }
.m-kpis { display: flex; gap: 10px; }
.m-kpi { flex: 1; border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; text-align: center; }
.m-kpi span { display: block; font-size: 24px; font-weight: 700; color: #1F4E79; }
.m-kpi label { font-size: 11px; color: #6b7280; }
.m-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.m-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; }
.m-card__title { font-weight: 600; color: #1F4E79; }
.m-card__row { display: flex; justify-content: space-between; font-size: 13px; color: #4b5563; padding: 2px 0; }
.m-link { background: none; border: none; color: #2E75B6; font-size: 13px; }
.m-muted { color: #9ca3af; font-size: 13px; text-align: center; }
</style>
```

- [ ] **Step 3: Build kiểm tra**

Run: `cd frontend && npm run build -- --outDir dist`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/mobile/screens/MobileDashboard.vue
git commit -m "feat(mobile): màn dashboard + cảnh báo (poll/làm mới) + đăng xuất"
```

---

### Task 11: Tích hợp end-to-end trên thiết bị Android

**Files:**
- Modify: `frontend/android/app/src/main/AndroidManifest.xml` (quyền camera)

**Interfaces:**
- Consumes: toàn bộ tasks trước.

- [ ] **Step 1: Thêm quyền camera vào AndroidManifest.xml**

Thêm trong `<manifest>`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.INTERNET" />
```

- [ ] **Step 2: Build + sync + mở Android Studio**

Run:
```bash
cd frontend
npm run build -- --outDir dist
npx cap sync android
npx cap open android
```
Expected: Android Studio mở project; Gradle sync OK.

- [ ] **Step 3: Chạy trên thiết bị/emulator + nhập server thật**

Chạy app (▶ trong Android Studio). Trên màn `ServerLogin`: nhập URL server SupplyCore thật (HTTPS hoặc IP LAN), tài khoản hợp lệ.
Expected: đăng nhập thành công → vào tab Tra cứu.

- [ ] **Step 4: Verify 4 luồng với dữ liệu thật**

Kiểm thủ công, đối chiếu với web (cùng dữ liệu):
- Tra cứu: tìm 1 vật tư có thật → hiện tồn/lô/HSD. Quét 1 barcode → ra kết quả.
- Duyệt: thấy phiếu draft thật → Duyệt → kiểm tra trên web đã submitted.
- Tiếp nhận: mở 1 phiếu nhận → nhập SL → xác nhận → kiểm tra web.
- Dashboard: KPI + cảnh báo khớp web; nút Làm mới hoạt động.
Expected: cả 4 luồng đúng; KHÔNG lỗi CORS/CSRF trong logcat.

- [ ] **Step 5: Verify web KHÔNG regress**

Mở `/supplycore` trên trình duyệt desktop, đăng nhập + thao tác vài module.
Expected: hoạt động y như trước (same-origin + CSRF).

- [ ] **Step 6: Commit**

```bash
git add frontend/android/app/src/main/AndroidManifest.xml
git commit -m "feat(mobile): quyền camera + xác minh E2E 4 luồng trên Android"
```

---

## Self-Review

**Spec coverage:**
- §2 Kiến trúc 1 codebase + native detect → Task 2,3,4,5. ✓
- §3 Server URL cấu hình + token auth + dual-mode + CapacitorHttp + backend `mobile_login` → Task 1,2,3,4,6. ✓
- §4 bốn luồng v1 → Task 7,8,9,10. ✓
- §5 ngoài phạm vi (push/offline) → không có task (đúng chủ đích). ✓
- §6 cấu trúc thư mục → khớp các Task. ✓
- §7 phụ thuộc/build (Capacitor, barcode plugin, Android) → Task 4,11. ✓
- §8 tiêu chí thành công → Task 11 Step 4-5. ✓
- §9 rủi ro (CORS, vend secret, base URL không phá web, barcode permission) → Task 1,3,7,11. ✓

**Placeholder scan:** Các "XÁC MINH …" là *bước hành động bắt buộc đọc code thật* (schemas.js/actions.js/pages) trước khi điền doctype/field — không phải code placeholder; mỗi cái nêu rõ file cần đọc + cái cần lấy. Doctype/field minh hoạ (`SC Batch`, `SC Purchase Receipt`, `SC Alert`...) phải được xác nhận/sửa ở step tương ứng.

**Type consistency:** `isNative/getServerUrl/getToken/setToken/clearToken/setServerUrl` (platform.js) dùng nhất quán ở api.js/auth.js/screens. `mobileLoginApi`→`auth.mobileLogin`→`ServerLogin`. `resolveUrl`/`authHeaders` chỉ trong api.js. `useScanner().scan()` dùng ở Task 7 & 9. ✓
