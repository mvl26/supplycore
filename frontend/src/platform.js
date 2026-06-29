// Lớp trừu tượng Capacitor — dùng API CHÍNH THỨC của Capacitor.
//
// LÝ DO không tự đọc window.Capacitor: bundled @capacitor/core tự quản lý
// window.Capacitor và GHI ĐÈ mọi giá trị bên ngoài; tự cache `window.Capacitor`
// lúc module-load còn dính race (bridge native tiêm chưa xong) → isNative() sai
// → app chạy chế độ web → API gọi same-origin → 404 → dashboard trống + getDoc
// null ("cannot read property of null"). Capacitor.isNativePlatform() là nguồn
// sự thật, đúng cả trên native, web lẫn node (vitest trả false).
import { Capacitor } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'

export function isNative() {
  return Capacitor.isNativePlatform()
}

const K_URL = 'sc_server_url'
const K_KEY = 'sc_api_key'
const K_SECRET = 'sc_api_secret'

// CHỈ await KẾT QUẢ method (Preferences.get/set trả promise thật); KHÔNG bao giờ
// await/return chính object Preferences (proxy Capacitor bẫy `.then` → throw).
export async function getServerUrl() {
  if (!isNative()) return null
  const { value } = await Preferences.get({ key: K_URL })
  return value || null
}
export async function setServerUrl(url) {
  if (!isNative()) return
  await Preferences.set({ key: K_URL, value: String(url).replace(/\/+$/, '') })
}
export async function getToken() {
  if (!isNative()) return null
  const k = (await Preferences.get({ key: K_KEY })).value
  const s = (await Preferences.get({ key: K_SECRET })).value
  return (k && s) ? { key: k, secret: s } : null
}
export async function setToken(key, secret) {
  if (!isNative()) return
  await Preferences.set({ key: K_KEY, value: key })
  await Preferences.set({ key: K_SECRET, value: secret })
}
export async function clearToken() {
  if (!isNative()) return
  await Preferences.remove({ key: K_KEY })
  await Preferences.remove({ key: K_SECRET })
}
