// frontend/src/mobile/useScanner.js
// Helper quét mã — uỷ quyền cho scanner singleton (startScan + overlay).
// Trên web (isNative()=false) scan() trả null an toàn. Giữ API cũ { scan }.
// Bổ sung: export scanning + cancel để screens có thể disable nút khi đang quét.
import { useScannerStore } from './scanner'

export function useScanner() {
  const { runScan, scanning, cancel } = useScannerStore()
  return { scan: runScan, scanning, cancel }
}
