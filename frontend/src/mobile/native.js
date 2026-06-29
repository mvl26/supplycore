// Tích hợp native Capacitor: StatusBar, SplashScreen, Keyboard, Haptics.
// Mọi thứ no-op an toàn trên web (isNative()=false) — import động để web bundle
// không cần các plugin này lúc chạy.
import { isNative } from '../platform'

// Khởi tạo trải nghiệm native khi app mount. Gọi 1 lần ở main.js (đã gate isNative).
export async function initNative() {
  if (!isNative()) return
  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar')
    await StatusBar.setStyle({ style: Style.Dark })          // chữ trắng trên nền navy
    await StatusBar.setBackgroundColor({ color: '#1F4E79' }) // Android
  } catch (e) { /* iOS có thể không hỗ trợ setBackgroundColor */ }
  try {
    const { Keyboard } = await import('@capacitor/keyboard')
    await Keyboard.setResizeMode({ mode: 'native' })
    await Keyboard.setScroll({ isDisabled: false })
  } catch (e) { /* optional */ }
  try {
    const { SplashScreen } = await import('@capacitor/splash-screen')
    await SplashScreen.hide()
  } catch (e) { /* optional */ }
}

// ---- Haptics: phản hồi rung tinh tế. No-op nếu không native. ----
async function _haptics() {
  if (!isNative()) return null
  try { return await import('@capacitor/haptics') } catch (e) { return null }
}
export async function tapLight() {
  const h = await _haptics(); if (h) try { await h.Haptics.impact({ style: h.ImpactStyle.Light }) } catch (e) {}
}
export async function tapMedium() {
  const h = await _haptics(); if (h) try { await h.Haptics.impact({ style: h.ImpactStyle.Medium }) } catch (e) {}
}
export async function notifySuccess() {
  const h = await _haptics(); if (h) try { await h.Haptics.notification({ type: h.NotificationType.Success }) } catch (e) {}
}
export async function notifyError() {
  const h = await _haptics(); if (h) try { await h.Haptics.notification({ type: h.NotificationType.Error }) } catch (e) {}
}
