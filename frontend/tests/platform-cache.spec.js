import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true } }))
const store = { sc_api_key:'K0', sc_api_secret:'S0' }
const getSpy = vi.fn(async ({ key }) => ({ value: key in store ? store[key] : null }))
vi.mock('@capacitor/preferences', () => ({ Preferences: {
  get: (...a) => getSpy(...a),
  set: async ({ key, value }) => { store[key] = value },
  remove: async ({ key }) => { delete store[key] },
}}))

describe('platform Preferences cache', () => {
  beforeEach(() => { vi.resetModules(); getSpy.mockClear() })

  it('getToken cache: lần 2 KHÔNG đọc lại Preferences', async () => {
    const p = await import('../src/platform.js')
    const t1 = await p.getToken()
    const calls1 = getSpy.mock.calls.length   // 2 (key + secret)
    const t2 = await p.getToken()
    expect(t2).toEqual(t1)
    expect(getSpy.mock.calls.length).toBe(calls1)   // không gọi thêm
  })

  it('setToken cập nhật cache; clearToken xoá cache', async () => {
    const p = await import('../src/platform.js')
    await p.setToken('K9', 'S9')
    expect(await p.getToken()).toEqual({ key:'K9', secret:'S9' })
    await p.clearToken()
    expect(await p.getToken()).toBe(null)
  })
})
