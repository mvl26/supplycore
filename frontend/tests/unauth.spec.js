// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true } }))
const store = { sc_server_url:'http://x', sc_api_key:'K', sc_api_secret:'S' }
vi.mock('@capacitor/preferences', () => ({ Preferences: {
  get: async ({ key }) => ({ value: store[key] ?? null }), set: async()=>{}, remove: async ({key})=>{delete store[key]} } }))

function mockFetch(status) {
  global.fetch = vi.fn(async () => ({ ok: status<400, status, json: async () => ({ message: 'x' }) }))
}

describe('native 401/403 handling', () => {
  beforeEach(() => { vi.resetModules() })

  it('403 KHÔNG bắn sc:unauth (không đăng xuất)', async () => {
    mockFetch(403)
    let unauth = false
    window.addEventListener('sc:unauth', () => (unauth = true))
    const api = await import('../src/api.js')
    await api.call('x').catch(() => {})
    await new Promise(r=>setTimeout(r,20))
    expect(unauth).toBe(false)
  })

  it('401 BẮN sc:unauth (đăng xuất)', async () => {
    mockFetch(401)
    let unauth = false
    window.addEventListener('sc:unauth', () => (unauth = true))
    const api = await import('../src/api.js')
    await api.call('x').catch(() => {})
    await new Promise(r=>setTimeout(r,20))
    expect(unauth).toBe(true)
  })
})
