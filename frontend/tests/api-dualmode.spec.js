// frontend/tests/api-dualmode.spec.js
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('api dual-mode resolveUrl (web)', () => {
  beforeEach(() => vi.resetModules())

  it('web: resolveUrl giữ path tương đối', async () => {
    const api = await import('../src/api.js')
    expect(await api.resolveUrl('/api/method/x')).toBe('/api/method/x')
  })
})

describe('api dual-mode resolveUrl (native)', () => {
  beforeEach(() => vi.resetModules())

  it('native: prefix server URL đã cấu hình', async () => {
    vi.doMock('../src/platform.js', () => ({
      isNative: () => true,
      getServerUrl: async () => 'https://bv-abc.example.com',
      getToken: async () => ({ key: 'K', secret: 'S' }),
    }))
    const api = await import('../src/api.js')
    expect(await api.resolveUrl('/api/method/x'))
      .toBe('https://bv-abc.example.com/api/method/x')
  })
})
