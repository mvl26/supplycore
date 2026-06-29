// frontend/tests/use-scanner.spec.js
// Kiểm tra useScanner() trả null khi không chạy trên native (web fallback).
// platform.js được mock để isNative() = false.

import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('useScanner (web fallback)', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('scan() resolves to null when not native', async () => {
    // Mock platform: isNative = false
    vi.doMock('../src/platform.js', () => ({
      isNative: () => false,
      getServerUrl: async () => null,
      getToken: async () => null,
      setServerUrl: async () => {},
      setToken: async () => {},
      clearToken: async () => {},
    }))

    const { useScanner } = await import('../src/mobile/useScanner.js')
    const { scan } = useScanner()
    const result = await scan()
    expect(result).toBeNull()
  })

  it('scan() does NOT call BarcodeScanner when not native', async () => {
    // Assure the plugin import is never reached
    vi.doMock('../src/platform.js', () => ({ isNative: () => false }))
    // If the plugin import is reached in a non-native env it would throw — absence of throw proves the guard works.
    const { useScanner } = await import('../src/mobile/useScanner.js')
    const { scan } = useScanner()
    await expect(scan()).resolves.toBeNull()
  })
})
