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
