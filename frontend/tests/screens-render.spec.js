// @vitest-environment happy-dom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// --- mock Capacitor (native) ---
vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => true, getPlatform: () => 'android' } }))
const store = {}
vi.mock('@capacitor/preferences', () => ({ Preferences: {
  get: async ({ key }) => ({ value: store[key] ?? null }), set: async ({ key, value }) => { store[key]=value }, remove: async ({ key }) => { delete store[key] } } }))
vi.mock('@capacitor/status-bar', () => ({ StatusBar:{setStyle:vi.fn(),setBackgroundColor:vi.fn()}, Style:{Dark:'DARK'} }))
vi.mock('@capacitor/splash-screen', () => ({ SplashScreen:{hide:vi.fn()} }))
vi.mock('@capacitor/keyboard', () => ({ Keyboard:{setResizeMode:vi.fn(),setScroll:vi.fn()} }))
vi.mock('@capacitor/haptics', () => ({ Haptics:{impact:vi.fn(),notification:vi.fn()}, ImpactStyle:{Light:'L',Medium:'M'}, NotificationType:{Success:'S',Error:'E'} }))
vi.mock('@capacitor/network', () => ({ Network:{ getStatus: async()=>({connected:true}), addListener: async()=>({remove:vi.fn()}) } }))
vi.mock('@capacitor-mlkit/barcode-scanning', () => ({ BarcodeScanner:{ requestPermissions: async()=>({camera:'granted'}), scan: async()=>({barcodes:[]}) } }))

// --- mock vue-router ---
vi.mock('vue-router', () => ({ useRouter: () => ({ replace: vi.fn(), push: vi.fn() }), useRoute: () => ({ params:{}, query:{}, meta:{} }) }))

// --- mock api với dữ liệu mẫu ---
vi.mock('../src/api.js', () => ({
  call: vi.fn(async (m) => m.includes('kpi') ? { kpis:{expiring_soon:3,low_stock_items:5,pending_pos:7}, open_alerts_total:9 } : { item:'X', item_name:'VT', warehouse:'K', batch:'B', qty:10, expiry_date:'2027-01-01', qc_status:'Accepted', blocked:0 }),
  getList: vi.fn(async (dt) => dt==='SC Alert' ? [{name:'A1',title:'Cảnh báo',message:'msg',severity:'Critical',alert_date:'2026-06-29'}] : [{name:'D1',item:'X',item_name:'VT',warehouse:'K',supplier:'NCC',creation:'2026-06-29',approval_stage:'Manager Review',qty:5}]),
  getDoc: vi.fn(async () => ({ name:'D1', items:[{item:'X',item_name:'VT',qty:0,po_qty:5}] })),
  count: vi.fn(async () => 0), submitDoc: vi.fn(async()=>({})), updateDoc: vi.fn(async()=>({})), runDocMethod: vi.fn(async()=>({})),
}))

const screens = {
  StockLookup: () => import('../src/mobile/screens/StockLookup.vue'),
  ApproveDocs: () => import('../src/mobile/screens/ApproveDocs.vue'),
  Receiving: () => import('../src/mobile/screens/Receiving.vue'),
  MobileDashboard: () => import('../src/mobile/screens/MobileDashboard.vue'),
  ServerLogin: () => import('../src/mobile/ServerLogin.vue'),
}

describe('mobile screens render không lỗi', () => {
  beforeEach(() => setActivePinia(createPinia()))
  for (const [name, load] of Object.entries(screens)) {
    it(name + ' mount OK', async () => {
      const Comp = (await load()).default
      const w = shallowMount(Comp, { global: { stubs: { 'router-link': true } } })
      await new Promise(r=>setTimeout(r,30))
      expect(w.exists()).toBe(true)
    })
  }
})
