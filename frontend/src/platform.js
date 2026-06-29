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
