// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
vi.mock('@capacitor/preferences', () => ({ Preferences: { get: async()=>({value:null}), set: async()=>{}, remove: async()=>{} } }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))

const PR_DOC = { name:'SC-PR-1', doctype:'SC Purchase Receipt', docstatus:0, supplier:'NCC', to_warehouse:'Kho', items:[{item:'X',item_name:'VT X',qty:0,po_qty:10,supplier_batch_no:''}] }
const calls = { update: null, submit: null }
vi.mock('../src/api.js', () => ({
  call: vi.fn(async () => ({})),
  getList: vi.fn(async () => [{ name:'SC-PR-1', supplier:'NCC', to_warehouse:'Kho', posting_date:'2026-06-29' }]),
  getDoc: vi.fn(async () => JSON.parse(JSON.stringify(PR_DOC))),
  updateDoc: vi.fn(async (dt,name,fields) => { calls.update = { dt, name, fields }; return {} }),
  submitDoc: vi.fn(async (dt,name) => { calls.submit = { dt, name }; return {} }),
  runDocMethod: vi.fn(async () => ({})), count: vi.fn(async()=>0), getMeta: vi.fn(async()=>({fields:[]})),
}))

describe('luồng Tiếp nhận: nhập SL → xác nhận', () => {
  beforeEach(() => { setActivePinia(createPinia()); calls.update = null; calls.submit = null })
  it('updateDoc(items) + submitDoc được gọi đúng', async () => {
    const errs = []
    const Comp = (await import('../src/mobile/screens/Receiving.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true }, config:{ errorHandler:(e)=>errs.push(e) } } })
    await new Promise(r=>setTimeout(r,50))
    // mở phiếu
    await w.find('.m-card--tap').trigger('click')
    await new Promise(r=>setTimeout(r,60))
    // nhập SL nhận vào ô number
    const qtyInput = w.find('input[type=number]')
    expect(qtyInput.exists()).toBe(true)
    await qtyInput.setValue(7)
    // bấm xác nhận
    const btns = w.findAll('button')
    const confirmBtn = btns.find(b => /Xác nhận/i.test(b.text()))
    expect(confirmBtn).toBeTruthy()
    await confirmBtn.trigger('click')
    await new Promise(r=>setTimeout(r,60))
    console.log('UPDATE:', JSON.stringify(calls.update))
    console.log('SUBMIT:', JSON.stringify(calls.submit))
    console.log('ERRORS:', errs.map(e=>e.message).join(' | ')||'none')
    expect(errs.length).toBe(0)
    expect(calls.update?.dt).toBe('SC Purchase Receipt')
    expect(calls.update?.fields?.items?.[0]?.qty).toBe(7)   // SL nhận đúng field 'qty'
    expect(calls.submit?.name).toBe('SC-PR-1')
  })
})
