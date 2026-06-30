// frontend/src/mobile/useScanner.js
// Helper quét mã — uỷ quyền cho scanner singleton (startScan + overlay).
// Trên web (isNative()=false) scan() trả null an toàn. Giữ API cũ { scan }.
import { useScannerStore } from './scanner'

export function useScanner() {
  const { runScan } = useScannerStore()
  return { scan: runScan }
}
