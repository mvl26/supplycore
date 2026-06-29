// Lớp trừu tượng Capacitor. An toàn trên web (Capacitor không tồn tại):
// isNative()=false, mọi getter trả null. Trên native dùng @capacitor/preferences.

let _cap = null
let _prefs = null          // proxy plugin Capacitor Preferences (chỉ tham chiếu, KHÔNG await)
let _prefsReady = false

// window.Capacitor được native bridge tiêm vào trước khi bundle chạy.
// typeof window guard để import an toàn ở môi trường node (vitest/SSR).
_cap = (typeof window !== 'undefined' && window.Capacitor) ? window.Capacitor : null

export function isNative() {
  return !!(_cap && _cap.isNativePlatform && _cap.isNativePlatform())
}

// QUAN TRỌNG: trả về boolean "sẵn sàng", TUYỆT ĐỐI không trả/await proxy plugin.
// Proxy plugin Capacitor bẫy mọi truy cập thuộc tính kể cả `.then` → nếu nó là
// giá trị resolve của một promise (vd `return _prefs` trong async rồi `await`),
// JS sẽ gọi `_prefs.then(...)` và Capacitor throw "Preferences.then() is not
// implemented on web" → vỡ guard router → màn trắng. Chỉ await KẾT QUẢ method.
async function ensurePrefs() {
  if (_prefsReady) return true
  if (!isNative()) return false
  const mod = await import('@capacitor/preferences')
  _prefs = mod.Preferences
  _prefsReady = true
  return true
}

const K_URL = 'sc_server_url'
const K_KEY = 'sc_api_key'
const K_SECRET = 'sc_api_secret'

export async function getServerUrl() {
  if (!(await ensurePrefs())) return null
  const { value } = await _prefs.get({ key: K_URL })
  return value || null
}
export async function setServerUrl(url) {
  if (!(await ensurePrefs())) return
  await _prefs.set({ key: K_URL, value: String(url).replace(/\/+$/, '') })
}
export async function getToken() {
  if (!(await ensurePrefs())) return null
  const k = (await _prefs.get({ key: K_KEY })).value
  const s = (await _prefs.get({ key: K_SECRET })).value
  return (k && s) ? { key: k, secret: s } : null
}
export async function setToken(key, secret) {
  if (!(await ensurePrefs())) return
  await _prefs.set({ key: K_KEY, value: key })
  await _prefs.set({ key: K_SECRET, value: secret })
}
export async function clearToken() {
  if (!(await ensurePrefs())) return
  await _prefs.remove({ key: K_KEY })
  await _prefs.remove({ key: K_SECRET })
}
