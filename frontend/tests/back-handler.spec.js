// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
vi.mock('@capacitor/preferences', () => ({ Preferences: { get: async()=>({value:null}), set: async()=>{}, remove: async()=>{} } }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))
vi.mock('../src/api.js', () => ({
  call: vi.fn(async () => ({})),
  getList: vi.fn(async () => [{ name:'SC-PR-1', supplier:'NCC', to_warehouse:'Kho', posting_date:'2026-06-29' }]),
  getDoc: vi.fn(async () => ({ name:'SC-PR-1', docstatus:0, is_return:0, purchase_order:'PO-X', items:[{item:'X',item_name:'VT',qty:0,po_qty:5}] })),
  updateDoc: vi.fn(async()=>({})), submitDoc: vi.fn(async()=>({})), count: vi.fn(async()=>0), getMeta: vi.fn(async()=>({fields:[]})),
}))

describe('nút Back đóng chi tiết thay vì thoát app', () => {
  beforeEach(() => setActivePinia(createPinia()))
  it('Receiving: mở chi tiết → handleBack() đóng chi tiết (về danh sách)', async () => {
    const { handleBack } = await import('../src/mobile/backHandler.js')
    const Comp = (await import('../src/mobile/screens/Receiving.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true } } })
    await new Promise(r=>setTimeout(r,50))
    await w.find('.m-card--tap').trigger('click')   // mở chi tiết
    await new Promise(r=>setTimeout(r,60))
    // đang ở chi tiết: có nút Xác nhận
    expect(w.findAll('button').some(b=>/Xác nhận/i.test(b.text()))).toBe(true)
    // mô phỏng nút Back cứng
    const handled = handleBack()
    await new Promise(r=>setTimeout(r,40))
    expect(handled).toBe(true)   // đã xử lý (KHÔNG thoát app)
    // đã về danh sách: không còn nút Xác nhận
    expect(w.findAll('button').some(b=>/Xác nhận/i.test(b.text()))).toBe(false)
    // handler đã pop: Back lần nữa không xử lý
    expect(handleBack()).toBe(false)
  })
})
