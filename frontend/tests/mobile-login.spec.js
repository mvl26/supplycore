// frontend/tests/mobile-login.spec.js
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('mobileLoginApi', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    delete global.fetch
  })

  it('POSTs to <serverUrl>/api/method/supplycore.api.mobile.mobile_login', async () => {
    const mockMessage = { user: 'admin@example.com', full_name: 'Admin', roles: [], api_key: 'K', api_secret: 'S' }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: mockMessage }),
    })
    const { mobileLoginApi } = await import('../src/api.js')
    const result = await mobileLoginApi('https://bv-abc.example.com', 'admin', 'secret')
    expect(global.fetch).toHaveBeenCalledTimes(1)
    const [url, opts] = global.fetch.mock.calls[0]
    expect(url).toBe('https://bv-abc.example.com/api/method/supplycore.api.mobile.mobile_login')
    expect(opts.method).toBe('POST')
    expect(result).toEqual(mockMessage)
  })

  it('strips trailing slash on serverUrl', async () => {
    const mockMessage = { user: 'u', full_name: 'U', roles: [], api_key: 'K', api_secret: 'S' }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: mockMessage }),
    })
    const { mobileLoginApi } = await import('../src/api.js')
    await mobileLoginApi('https://bv-abc.example.com/', 'u', 'p')
    const [url] = global.fetch.mock.calls[0]
    expect(url).toBe('https://bv-abc.example.com/api/method/supplycore.api.mobile.mobile_login')
  })

  it('returns the unwrapped .message object', async () => {
    const mockMessage = { user: 'u2', full_name: 'U2', roles: ['Manager'], api_key: 'K2', api_secret: 'S2' }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: mockMessage }),
    })
    const { mobileLoginApi } = await import('../src/api.js')
    const result = await mobileLoginApi('https://example.com', 'u2', 'p2')
    expect(result).toEqual(mockMessage)
  })

  it('rejects with parsed error message on 401 AuthenticationError', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ exc_type: 'AuthenticationError', exception: 'AuthenticationError: Bad credentials' }),
    })
    const { mobileLoginApi } = await import('../src/api.js')
    await expect(mobileLoginApi('https://x.com', 'u', 'p')).rejects.toThrow('Bad credentials')
  })
})
