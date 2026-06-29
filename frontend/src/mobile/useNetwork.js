// Trạng thái mạng phản ứng (reactive). Dùng @capacitor/network trên native,
// navigator.onLine + sự kiện online/offline trên web. Trả ref `online`.
import { ref, onMounted, onUnmounted } from 'vue'
import { isNative } from '../platform'

export function useNetwork() {
  const online = ref(true)
  let remove = null

  onMounted(async () => {
    if (isNative()) {
      try {
        const { Network } = await import('@capacitor/network')
        const s = await Network.getStatus()
        online.value = s.connected
        const h = await Network.addListener('networkStatusChange', (st) => { online.value = st.connected })
        remove = () => h.remove()
      } catch (e) { online.value = true }
    } else {
      online.value = navigator.onLine
      const on = () => (online.value = true), off = () => (online.value = false)
      window.addEventListener('online', on); window.addEventListener('offline', off)
      remove = () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
    }
  })
  onUnmounted(() => { if (remove) remove() })

  return { online }
}
