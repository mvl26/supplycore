// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
vi.mock('@capacitor/preferences', () => ({ Preferences: { get: async()=>({value:null}), set: async()=>{}, remove: async()=>{} } }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))

let getListImpl = async () => []
vi.mock('../src/api.js', () => ({
  call: vi.fn(async () => []),
  getList: vi.fn((...a) => getListImpl(...a)),
  getDoc: vi.fn(async () => ({ name:'D', docstatus:0, approval_stage:'Manager Review' })),
  runDocMethod: vi.fn(async () => ({})), submitDoc: vi.fn(async()=>({})), updateDoc: vi.fn(async()=>({})), count: vi.fn(async()=>0), getMeta: vi.fn(async()=>({fields:[]})),
}))

describe('ApproveDocs xử lý quyền (403)', () => {
  beforeEach(() => setActivePinia(createPinia()))
  it('403 → hiện "không có quyền", KHÔNG bắn sc:unauth', async () => {
    let unauth = false
    window.addEventListener('sc:unauth', () => (unauth = true))
    getListImpl = async () => { const e = new Error('Không có quyền'); e.status = 403; throw e }
    const Comp = (await import('../src/mobile/screens/ApproveDocs.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true } } })
    await new Promise(r=>setTimeout(r,60))
    expect(w.text()).toContain('không có quyền')
    expect(unauth).toBe(false)   // 403 KHÔNG đăng xuất
  })
})
