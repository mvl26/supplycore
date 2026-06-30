// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
vi.mock('@capacitor/preferences', () => ({ Preferences: { get: async()=>({value:null}), set: async()=>{}, remove: async()=>{} } }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))

const PR_DOC = { name:'SC-PR-1', doctype:'SC Purchase Receipt', docstatus:0, is_return:0, supplier:'NCC', to_warehouse:'Kho', items:[{item:'X',item_name:'VT X',qty:0,po_qty:10,supplier_batch_no:'',expiry_date:'',manufacturing_date:''}] }
const calls = { update:null, submit:null }
vi.mock('../src/api.js', () => ({
  call: vi.fn(async () => ({})),
  getList: vi.fn(async () => [{ name:'SC-PR-1', supplier:'NCC', to_warehouse:'Kho', posting_date:'2026-06-29' }]),
  getDoc: vi.fn(async () => JSON.parse(JSON.stringify(PR_DOC))),
  updateDoc: vi.fn(async (dt,name,fields) => { calls.update = { dt, name, fields }; return {} }),
  submitDoc: vi.fn(async (dt,name) => { calls.submit = { dt, name }; return {} }),
  count: vi.fn(async()=>0), getMeta: vi.fn(async()=>({fields:[]})),
}))

describe('luồng Tiếp nhận: nhập SL + Hạn dùng → xác nhận', () => {
  beforeEach(() => { setActivePinia(createPinia()); calls.update=null; calls.submit=null })

  it('CHẶN khi thiếu Hạn dùng (qty>0, expiry trống)', async () => {
    const Comp = (await import('../src/mobile/screens/Receiving.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true } } })
    await new Promise(r=>setTimeout(r,50))
    await w.find('.m-card--tap').trigger('click')
    await new Promise(r=>setTimeout(r,60))
    await w.find('input[type=number]').setValue(7)
    await w.findAll('button').find(b => /Xác nhận/i.test(b.text())).trigger('click')
    await new Promise(r=>setTimeout(r,60))
    expect(calls.update).toBe(null)   // chặn — không gọi backend
  })

  it('updateDoc(qty+expiry) + submitDoc khi đủ Hạn dùng', async () => {
    const errs = []
    const Comp = (await import('../src/mobile/screens/Receiving.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true }, config:{ errorHandler:(e)=>errs.push(e) } } })
    await new Promise(r=>setTimeout(r,50))
    await w.find('.m-card--tap').trigger('click')
    await new Promise(r=>setTimeout(r,60))
    await w.find('input[type=number]').setValue(7)
    await w.find('input[type=date]').setValue('2027-01-15')
    await w.findAll('button').find(b => /Xác nhận/i.test(b.text())).trigger('click')
    await new Promise(r=>setTimeout(r,60))
    console.log('UPDATE:', JSON.stringify(calls.update))
    expect(errs.length).toBe(0)
    expect(calls.update?.fields?.items?.[0]?.qty).toBe(7)
    expect(calls.update?.fields?.items?.[0]?.expiry_date).toBe('2027-01-15')
    expect(calls.submit?.name).toBe('SC-PR-1')
  })
})
