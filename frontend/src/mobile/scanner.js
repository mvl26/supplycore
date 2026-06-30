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
let _cancel = null

async function runScan() {
  if (!isNative()) return null
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
    if (s && s.supported === false) { const e = new Error('Thiết bị không hỗ trợ quét mã.'); e.code = 'unsupported'; throw e }
  } catch (e) { if (e.code) throw e }

  document.documentElement.classList.add('sc-scanning')
  scanning.value = true

  return await new Promise((resolve, reject) => {
    let hit = null, err = null
    const cleanup = async () => {
      try { if (hit) await hit.remove() } catch (e) {}
      try { if (err) await err.remove() } catch (e) {}
      try { await BarcodeScanner.stopScan() } catch (e) {}
      document.documentElement.classList.remove('sc-scanning')
      scanning.value = false
      _cancel = null
    }
    _cancel = async () => { await cleanup(); resolve(null) }

    ;(async () => {
      try {
        hit = await BarcodeScanner.addListener('barcodesScanned', async (ev) => {
          const code = ev && ev.barcodes && ev.barcodes[0] && ev.barcodes[0].rawValue
          if (code) { await cleanup(); resolve(code) }
        })
        err = await BarcodeScanner.addListener('scanError', async (ev) => {
          await cleanup(); reject(new Error((ev && ev.message) || 'Lỗi khi quét mã'))
        })
        await BarcodeScanner.startScan()
      } catch (e) {
        await cleanup(); reject(e)
      }
    })()
  })
}

function cancel() { if (_cancel) _cancel() }

export function useScannerStore() { return { scanning, runScan, cancel } }
