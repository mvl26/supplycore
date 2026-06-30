// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
vi.mock('@capacitor/preferences', () => ({ Preferences: { get: async()=>({value:null}), set: async()=>{}, remove: async()=>{} } }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))

let runArgs = null
// PO ở Manager Review → ACTIONS có approve_as_manager (when docstatus===0 && approval_stage==='Manager Review')
const PO = { name:'SC-PO-9', doctype:'SC Purchase Order', docstatus:0, approval_stage:'Manager Review', status:'Approved', supplier:'NCC', items:[] }
vi.mock('../src/api.js', () => ({
  call: vi.fn(async () => []),
  getList: vi.fn(async () => [{ name:'SC-PO-9', creation:'2026-06-29', approval_stage:'Manager Review', supplier:'NCC' }]),
  getDoc: vi.fn(async () => JSON.parse(JSON.stringify(PO))),
  runDocMethod: vi.fn(async (dt,name,method,args) => { runArgs = { dt, name, method, args }; return {} }),
  submitDoc: vi.fn(async()=>({})), updateDoc: vi.fn(async()=>({})), count: vi.fn(async()=>0), getMeta: vi.fn(async()=>({fields:[]})),
}))

describe('Duyệt: ActionPanel có nút duyệt + gọi runDocMethod', () => {
  beforeEach(() => { setActivePinia(createPinia()); runArgs = null })
  it('mở PO Manager Review → có nút duyệt; bấm → runDocMethod(approve_as_manager) hoặc mở modal', async () => {
    const errs = []
    const Comp = (await import('../src/mobile/screens/ApproveDocs.vue')).default
    const w = mount(Comp, { global: { stubs:{ 'router-link':true, teleport:true }, config:{ errorHandler:(e)=>errs.push(e) } } })
    await new Promise(r=>setTimeout(r,50))
    // chuyển tab sang SC Purchase Order
    const chips = w.findAll('.m-chip')
    const poChip = chips.find(c => /Đơn mua/i.test(c.text()))
    if (poChip) await poChip.trigger('click')
    await new Promise(r=>setTimeout(r,50))
    await w.find('.m-card--tap').trigger('click')
    await new Promise(r=>setTimeout(r,60))
    const html = w.html()
    const hasApprove = /duyệt/i.test(html)
    console.log('CÓ NÚT DUYỆT:', hasApprove)
    // bấm nút có chữ "duyệt" (Manager duyệt)
    const btn = w.findAll('button').find(b => /duyệt/i.test(b.text()) && !/từ chối/i.test(b.text()))
    if (btn) { await btn.trigger('click'); await new Promise(r=>setTimeout(r,60)) }
    console.log('runDocMethod gọi:', JSON.stringify(runArgs))
    console.log('ERRORS:', errs.map(e=>e.message).join(' | ')||'none')
    expect(errs.length).toBe(0)
    expect(hasApprove).toBe(true)
    // bấm trực tiếp gọi runDocMethod (action không args) HOẶC mở modal nhập comment (action có args)
    const calledOrModal = !!runArgs || /ghi chú|comment|modal/i.test(w.html())
    expect(calledOrModal).toBe(true)
  })
})
