// Scanner barcode/QR dùng @capacitor-mlkit/barcode-scanning ở chế độ startScan()
// (scanner NHÚNG SẴN, hiện camera xuyên WebView) — KHÔNG dùng scan() vì scan()
// cần Google Barcode Scanner Module (tải bất đồng bộ qua Play Services) → nhiều
// máy chưa có module → "không hiện camera".
//
// Cơ chế: bật class `sc-scanning` trên <html> để nền app trong suốt (camera native
// nằm SAU WebView lộ ra), ScanOverlay (teleport body) vẽ khung + nút Huỷ ở trên.
import { ref } from 'vue'
import { isNative } from '../platform'

const scanning = ref(false)
// _busy: khoá đồng bộ, set ngay trước await đầu tiên để chặn TOCTOU double-tap
let _busy = false
let _cancel = null

async function runScan() {
  if (!isNative()) return null
  // Guard: chặn double-tap hoặc gọi đồng thời khi đang quét
  // (scanning.value chỉ true sau nhiều await → dùng _busy khoá ngay đồng bộ)
  if (scanning.value || _busy) return null
  _busy = true

  let _statusBar = null

  try {
    const { BarcodeScanner } = await import('@capacitor-mlkit/barcode-scanning')

    // Quyền camera
    let perm = await BarcodeScanner.checkPermissions().catch(() => ({ camera: 'prompt' }))
    if (perm.camera !== 'granted' && perm.camera !== 'limited') {
      perm = await BarcodeScanner.requestPermissions()
    }
    if (perm.camera !== 'granted' && perm.camera !== 'limited') {
      const e = new Error('Chưa cấp quyền camera. Vào Cài đặt > Ứng dụng > SupplyCore để bật Camera.')
      e.code = 'no-permission'
      throw e
    }

    // Thiết bị có hỗ trợ không
    try {
      const s = await BarcodeScanner.isSupported()
      if (s && s.supported === false) {
        const e = new Error('Thiết bị không hỗ trợ quét mã.')
        e.code = 'unsupported'
        throw e
      }
    } catch (e) { if (e.code) throw e }

    // StatusBar: trong suốt khi quét, tránh dải màu đè lên camera
    try {
      const { StatusBar } = await import('@capacitor/status-bar')
      _statusBar = StatusBar
      await StatusBar.setOverlaysWebView({ overlay: true })
    } catch { /* thiết bị không hỗ trợ hoặc chạy web */ }

    document.documentElement.classList.add('sc-scanning')
    scanning.value = true

    return await new Promise((resolve, reject) => {
      let done = false
      let cancelled = false
      let backBtn = null
      let appState = null

      const cleanup = async () => {
        if (done) return
        done = true
        // Gỡ UI ngay trước khi await stopScan để overlay/ẩn-app không kéo dài nếu stopScan chậm
        document.documentElement.classList.remove('sc-scanning')
        scanning.value = false
        _cancel = null
        // Gỡ toàn bộ listeners BarcodeScanner một lần
        try { await BarcodeScanner.removeAllListeners() } catch {}
        // Gỡ App listeners
        try { if (backBtn) { await backBtn.remove(); backBtn = null } } catch {}
        try { if (appState) { await appState.remove(); appState = null } } catch {}
        // Dừng camera
        try { await BarcodeScanner.stopScan() } catch {}
        // Khôi phục StatusBar
        try {
          if (_statusBar) await _statusBar.setOverlaysWebView({ overlay: false })
        } catch {}
      }

      // _cancel gán đồng bộ → nút Huỷ phản hồi ngay kể cả trước startScan
      _cancel = async () => {
        cancelled = true
        await cleanup()
        resolve(null)
      }

      ;(async () => {
        try {
          await BarcodeScanner.addListener('barcodesScanned', async (ev) => {
            if (done) return
            const code = ev && ev.barcodes && ev.barcodes[0] && ev.barcodes[0].rawValue
            if (code) { await cleanup(); resolve(code) }
          })
          await BarcodeScanner.addListener('scanError', async (ev) => {
            if (done) return
            await cleanup()
            reject(new Error((ev && ev.message) || 'Lỗi khi quét mã'))
          })

          // Lắng nghe nút back cứng Android + app vào nền
          try {
            const { App } = await import('@capacitor/app')
            backBtn = await App.addListener('backButton', async () => {
              if (!done) { await cleanup(); resolve(null) }
            })
            appState = await App.addListener('appStateChange', async ({ isActive }) => {
              if (!isActive && !done) { await cleanup(); resolve(null) }
            })
          } catch { /* @capacitor/app không khả dụng */ }

          await BarcodeScanner.startScan()

          // Xử lý race: cancel chạy trong khoảng addListener→startScan
          // → cleanup() đã chạy nhưng stopScan lúc đó camera chưa bật
          // → camera vừa bật ngay sau startScan(), phải stopScan lại
          if (cancelled) {
            try { await BarcodeScanner.stopScan() } catch {}
          }
        } catch (e) {
          if (!done) { await cleanup(); reject(e) }
        }
      })()
    })
  } finally {
    _busy = false
  }
}

function cancel() { if (_cancel) _cancel() }

export function useScannerStore() { return { scanning, runScan, cancel } }
