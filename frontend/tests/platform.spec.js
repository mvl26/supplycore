import { describe, it, expect, beforeEach, vi } from 'vitest'

// Giả lập KHÔNG có Capacitor (môi trường web): module phải chạy an toàn.
describe('platform (web fallback)', () => {
  beforeEach(() => { vi.resetModules() })

  it('isNative() trả false khi không có Capacitor', async () => {
    const p = await import('../src/platform.js')
    expect(p.isNative()).toBe(false)
  })

  it('getServerUrl()/getToken() trả null trên web', async () => {
    const p = await import('../src/platform.js')
    expect(await p.getServerUrl()).toBe(null)
    expect(await p.getToken()).toBe(null)
  })
})
