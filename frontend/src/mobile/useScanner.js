// frontend/src/mobile/useScanner.js
// Barcode scanner helper cho Capacitor native.
// Trên web (isNative() = false) → scan() luôn trả null, an toàn.
// Chỉ dynamic-import plugin khi thật sự chạy native để tránh lỗi build web.

import { isNative } from '../platform'

export function useScanner() {
  /**
   * Quét một mã vạch / QR.
   * @returns {Promise<string|null>} rawValue của barcode đầu tiên, hoặc null.
   */
  async function scan() {
    if (!isNative()) return null

    // Dynamic import — chỉ resolve khi Capacitor native; tree-shaken khỏi web bundle.
    const { BarcodeScanner } = await import(/* @vite-ignore */ '@capacitor-mlkit/barcode-scanning')

    const perm = await BarcodeScanner.requestPermissions()
    if (perm.camera !== 'granted' && perm.camera !== 'limited') return null

    const { barcodes } = await BarcodeScanner.scan()
    return barcodes?.[0]?.rawValue || null
  }

  return { scan }
}
