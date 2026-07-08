<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import Icon from '../components/Icon.vue'
import { useToastStore } from '../stores/toast'
import { fmtNumber, fmtVNDShort, fmtDate, fmtVND } from '../utils'

const router = useRouter()
const toast = useToastStore()

// === Tabs ===
const TABS = [
  { id: 'inventory', label: 'Tồn kho — giá trị', api: 'inventory_value_report' },
  { id: 'ap_aging',  label: 'Công nợ NCC (Aging)', api: 'ap_aging_report' },
  { id: 'ar_aging',  label: 'Công nợ phải thu (Aging)', api: 'ar_aging_by_customer' },
  { id: 'period',    label: 'Chi phí vật tư kỳ',  api: 'period_cost_report' },
]
const active = ref('inventory')

// === Common filters ===
const today = new Date().toISOString().slice(0, 10)
const firstDayMonth = `${today.slice(0, 7)}-01`
const filters = ref({
  warehouse: '',
  item_group: '',
  supplier: '',
  customer: '',
  as_of_date: today,
  from_date: firstDayMonth,
  to_date: today,
})

// Suggestions
const whSuggestions = ref([])
const supSuggestions = ref([])
const custSuggestions = ref([])

const loading = ref(false)
const data = ref(null)

// Drill-down
const drillOpen = ref(false)
const drillData = ref(null)

const API_PREFIX = 'supplycore.m8_accounting.api.financial_reports.'

async function loadSuggestions() {
  const [whs, sups, custs] = await Promise.all([
    getList('SC Warehouse', { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 200 }).catch(() => []),
    getList('SC Supplier', { fields: ['name', 'supplier_name'], filters: { disabled: 0 }, limit: 300 }).catch(() => []),
    getList('SC Customer', { fields: ['name', 'customer_name'], limit: 300 }).catch(() => []),
  ])
  whSuggestions.value = whs
  supSuggestions.value = sups
  custSuggestions.value = custs
}

async function runReport() {
  const tab = TABS.find(t => t.id === active.value)
  if (!tab) return
  loading.value = true
  data.value = null
  try {
    const args = {}
    if (active.value === 'inventory') {
      if (filters.value.warehouse) args.warehouse = filters.value.warehouse
      if (filters.value.item_group) args.item_group = filters.value.item_group
      if (filters.value.as_of_date) args.as_of_date = filters.value.as_of_date
    } else if (active.value === 'ap_aging') {
      if (filters.value.supplier) args.supplier = filters.value.supplier
      if (filters.value.as_of_date) args.as_of_date = filters.value.as_of_date
    } else if (active.value === 'ar_aging') {
      if (filters.value.customer) args.customer = filters.value.customer
      if (filters.value.as_of_date) args.as_of_date = filters.value.as_of_date
    } else if (active.value === 'period') {
      args.from_date = filters.value.from_date
      args.to_date = filters.value.to_date
      if (filters.value.item_group) args.item_group = filters.value.item_group
      if (filters.value.warehouse) args.warehouse = filters.value.warehouse
    }
    data.value = await call(API_PREFIX + tab.api, args)
  } catch (e) {
    toast.error(`Lỗi báo cáo: ${e.message}`)
  } finally {
    loading.value = false
  }
}

function setTab(id) {
  active.value = id
  data.value = null
}

// === Drill-down vào voucher ===
async function drillVoucher(vt, vn) {
  if (!vn) return
  try {
    drillData.value = await call(API_PREFIX + 'get_voucher_details',
      { voucher_type: vt, voucher_no: vn })
    drillOpen.value = true
  } catch (e) {
    toast.error(`Drill-down lỗi: ${e.message}`)
  }
}

function goToDoc(dt, name) {
  router.push(`/doc/${encodeURIComponent(dt)}/${encodeURIComponent(name)}`)
}

// === Export CSV ===
function exportCsv() {
  if (!data.value) return
  let rows = data.value.rows || data.value.by_item_group || []
  // AR aging: bucket là object lồng nhau — làm phẳng trước khi xuất CSV.
  if (active.value === 'ar_aging') {
    rows = rows.map(r => ({
      customer: r.customer, customer_name: r.customer_name,
      credit_limit: r.credit_limit,
      bucket_0_30: r.buckets?.['0_30'], bucket_31_60: r.buckets?.['31_60'],
      bucket_61_90: r.buckets?.['61_90'], bucket_over_90: r.buckets?.over_90,
      total_outstanding: r.total_outstanding, over_limit: r.over_limit,
    }))
  }
  if (!rows.length) {
    toast.warning('Không có dữ liệu để xuất')
    return
  }
  const keys = Object.keys(rows[0])
  const csv = [
    keys.join(','),
    ...rows.map(r => keys.map(k => {
      const v = r[k]
      if (v == null) return ''
      const s = String(v).replace(/"/g, '""')
      return /[",\n]/.test(s) ? `"${s}"` : s
    }).join(',')),
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `bao-cao-${active.value}-${today}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

// === Computed views ===
const apBuckets = computed(() => {
  if (active.value !== 'ap_aging' || !data.value) return null
  const b = data.value.buckets || {}
  const labels = {
    current: 'Chưa đến hạn',
    '0_30':  '0–30 ngày',
    '31_60': '31–60 ngày',
    '61_90': '61–90 ngày',
    over_90: '> 90 ngày',
  }
  return Object.entries(b).map(([k, v]) => ({
    key: k, label: labels[k] || k, amount: v,
  }))
})

const bucketCls = {
  current: 'bg-green-50 border-green-200',
  '0_30':  'bg-blue-50 border-blue-200',
  '31_60': 'bg-amber-50 border-amber-200',
  '61_90': 'bg-orange-50 border-orange-200',
  over_90: 'bg-red-50 border-red-200',
}

const bucketLabels = {
  '0_30':  '0–30 ngày',
  '31_60': '31–60 ngày',
  '61_90': '61–90 ngày',
  over_90: '> 90 ngày',
}

// AR aging (BRU-AR-001): tổng bucket toàn hệ thống (mọi khách) — hiển thị
// dạng "tile" tương tự AP, cộng dồn từ rows theo khách.
const arBuckets = computed(() => {
  if (active.value !== 'ar_aging' || !data.value) return null
  const totals = { '0_30': 0, '31_60': 0, '61_90': 0, over_90: 0 }
  for (const r of (data.value.rows || [])) {
    for (const k of Object.keys(totals)) totals[k] += r.buckets?.[k] || 0
  }
  return Object.entries(totals).map(([k, v]) => ({ key: k, label: bucketLabels[k] || k, amount: v }))
})

onMounted(loadSuggestions)
</script>

<template>
  <PageHeader title="Báo cáo tài chính M8" icon="bar-chart"
    code="UC-26" subtitle="4 báo cáo nghiệp vụ + drill-down chứng từ">
    <template #actions>
      <button @click="runReport" :disabled="loading"
        class="sc-btn-primary text-sm disabled:opacity-50">
        <Icon v-if="!loading" name="play" :size="14" />
        {{ loading ? 'Đang tải...' : 'Chạy báo cáo' }}
      </button>
      <button @click="exportCsv" :disabled="!data"
        class="sc-btn-secondary text-sm disabled:opacity-50">
        <Icon name="download" :size="14" /> Xuất CSV
      </button>
    </template>
  </PageHeader>

  <!-- Tabs -->
  <div class="sc-card mb-4 overflow-hidden">
    <div class="flex flex-wrap">
      <button v-for="t in TABS" :key="t.id"
        @click="setTab(t.id)"
        class="px-4 py-3 text-sm font-medium border-b-2 transition"
        :class="active === t.id
          ? 'border-sc-royal text-sc-navy bg-sc-bg'
          : 'border-transparent text-sc-text-muted hover:text-sc-navy hover:bg-sc-bg'">
        {{ t.label }}
      </button>
    </div>
  </div>

  <!-- Filters per tab -->
  <div class="sc-card p-4 mb-4">
    <div v-if="active === 'inventory'" class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Kho</label>
        <select v-model="filters.warehouse" class="sc-input">
          <option value="">— Tất cả —</option>
          <option v-for="w in whSuggestions" :key="w.name" :value="w.name">{{ w.name }}</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Nhóm vật tư</label>
        <input v-model="filters.item_group" class="sc-input" placeholder="Mã nhóm VT" />
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Tại ngày</label>
        <input v-model="filters.as_of_date" type="date" class="sc-input" />
      </div>
    </div>
    <div v-else-if="active === 'ap_aging'" class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Nhà cung cấp</label>
        <select v-model="filters.supplier" class="sc-input">
          <option value="">— Tất cả —</option>
          <option v-for="s in supSuggestions" :key="s.name" :value="s.name">
            {{ s.name }} · {{ s.supplier_name }}
          </option>
        </select>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Tại ngày</label>
        <input v-model="filters.as_of_date" type="date" class="sc-input" />
      </div>
    </div>
    <div v-else-if="active === 'ar_aging'" class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Khách hàng</label>
        <select v-model="filters.customer" class="sc-input">
          <option value="">— Tất cả —</option>
          <option v-for="c in custSuggestions" :key="c.name" :value="c.name">
            {{ c.name }} · {{ c.customer_name }}
          </option>
        </select>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Tại ngày</label>
        <input v-model="filters.as_of_date" type="date" class="sc-input" />
      </div>
    </div>
    <div v-else-if="active === 'period'" class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Từ ngày <span class="text-red-500">*</span></label>
        <input v-model="filters.from_date" type="date" class="sc-input" />
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Đến ngày <span class="text-red-500">*</span></label>
        <input v-model="filters.to_date" type="date" class="sc-input" />
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Nhóm vật tư</label>
        <input v-model="filters.item_group" class="sc-input" placeholder="Mã nhóm" />
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Kho</label>
        <select v-model="filters.warehouse" class="sc-input">
          <option value="">— Tất cả —</option>
          <option v-for="w in whSuggestions" :key="w.name" :value="w.name">{{ w.name }}</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Period finalization warning -->
  <div v-if="data && (data.period_finalized === false)"
    class="sc-card p-3 mb-4 bg-amber-50 border-amber-200">
    <div class="flex items-start gap-2">
      <span class="text-amber-700"><Icon name="alert-triangle" :size="18" /></span>
      <div class="text-sm text-amber-900 flex-1">
        <strong>Kỳ chưa khóa sổ</strong>
        — vẫn còn chứng từ <em>Draft</em> trong kỳ. Số liệu có thể thay đổi:
        <span v-if="data.pending_drafts">
          PI nháp = <strong>{{ data.pending_drafts.purchase_invoice || 0 }}</strong>,
          PE nháp = <strong>{{ data.pending_drafts.payment_entry || 0 }}</strong>
        </span>
      </div>
    </div>
  </div>

  <!-- Results -->
  <div v-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải dữ liệu báo cáo...</div>
  <div v-else-if="!data" class="sc-card p-10 text-center text-sc-text-muted">
    Bấm <strong>Chạy báo cáo</strong> để xem kết quả
  </div>

  <!-- TAB 1: Inventory Value -->
  <div v-else-if="active === 'inventory'" class="space-y-4">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div class="sc-card p-4">
        <div class="text-xs text-sc-text-muted">Số dòng</div>
        <div class="text-2xl font-bold text-sc-navy mt-1">{{ data.rows.length.toLocaleString('vi-VN') }}</div>
      </div>
      <div class="sc-card p-4">
        <div class="text-xs text-sc-text-muted">Tổng SL</div>
        <div class="text-2xl font-bold font-mono text-sc-navy mt-1">{{ fmtNumber(data.total_qty) }}</div>
      </div>
      <div class="sc-card p-4">
        <div class="text-xs text-sc-text-muted">Giá trị tồn (VND)</div>
        <div class="text-2xl font-bold font-mono text-sc-success mt-1">{{ fmtVNDShort(data.total_value) }}</div>
      </div>
    </div>
    <div class="sc-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th>Mã VT</th><th>Tên</th><th>Nhóm</th><th>Kho</th><th>Lô</th>
              <th class="text-right">SL</th><th class="text-right">Đơn giá BQ</th>
              <th class="text-right">Giá trị</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, idx) in data.rows" :key="idx"
              class="hover:bg-sc-bg cursor-pointer"
              @click="goToDoc('SC Item', r.item)">
              <td class="font-mono text-xs">{{ r.item }}</td>
              <td>{{ r.item_name }}</td>
              <td>{{ r.item_group }}</td>
              <td>{{ r.warehouse }}</td>
              <td class="font-mono text-xs">{{ r.batch || '—' }}</td>
              <td class="text-right font-mono">{{ fmtNumber(r.qty) }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.avg_rate) }}</td>
              <td class="text-right font-mono font-semibold" :title="fmtVND(r.value)">{{ fmtVND(r.value) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 2: AP Aging -->
  <div v-else-if="active === 'ap_aging'" class="space-y-4">
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3" v-if="apBuckets">
      <div v-for="b in apBuckets" :key="b.key"
        :class="['sc-card p-3 border-2', bucketCls[b.key] || '']">
        <div class="text-xs text-sc-text-muted">{{ b.label }}</div>
        <div class="text-lg font-bold font-mono mt-1">{{ fmtVNDShort(b.amount) }}</div>
      </div>
    </div>
    <div class="sc-card p-3 text-sm">
      Tổng công nợ outstanding: <strong class="font-mono text-sc-danger">{{ fmtVND(data.total_outstanding) }}</strong>
      tại ngày {{ fmtDate(data.as_of_date) }}
    </div>
    <div class="sc-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th>PI</th><th>NCC</th><th>Số HD NCC</th>
              <th>Ngày HD</th><th>Ngày đến hạn</th>
              <th class="text-right">Tổng</th>
              <th class="text-right">Đã trả</th>
              <th class="text-right">Còn lại</th>
              <th>Bucket</th>
              <th class="text-right">Quá hạn (ngày)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in data.rows" :key="r.name"
              class="hover:bg-sc-bg cursor-pointer">
              <td class="font-mono text-xs" @click.stop="drillVoucher('SC Purchase Invoice', r.name)">
                <span class="text-sc-royal hover:underline">{{ r.name }}</span>
              </td>
              <td>{{ r.supplier_name }}</td>
              <td class="font-mono text-xs">{{ r.supplier_invoice_no }}</td>
              <td>{{ fmtDate(r.invoice_date) }}</td>
              <td>{{ fmtDate(r.due_date) }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.grand_total) }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.paid_amount) }}</td>
              <td class="text-right font-mono font-semibold text-sc-danger">{{ fmtVND(r.outstanding_amount) }}</td>
              <td>
                <span class="text-xs px-2 py-0.5 rounded"
                  :class="bucketCls[r.bucket] || ''">{{ r.bucket }}</span>
              </td>
              <td class="text-right font-mono"
                :class="r.days_overdue > 60 ? 'text-sc-danger font-bold' : ''">
                {{ r.days_overdue > 0 ? r.days_overdue : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB: AR Aging (công nợ phải thu — BRU-AR-001) -->
  <div v-else-if="active === 'ar_aging'" class="space-y-4">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3" v-if="arBuckets">
      <div v-for="b in arBuckets" :key="b.key"
        :class="['sc-card p-3 border-2', bucketCls[b.key] || '']">
        <div class="text-xs text-sc-text-muted">{{ b.label }}</div>
        <div class="text-lg font-bold font-mono mt-1">{{ fmtVNDShort(b.amount) }}</div>
      </div>
    </div>
    <div class="sc-card p-3 text-sm">
      Tổng phải thu: <strong class="font-mono text-sc-danger">{{ fmtVND(data.total_outstanding) }}</strong>
      tại ngày {{ fmtDate(data.as_of_date) }}
    </div>
    <div class="sc-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th>Khách hàng</th>
              <th class="text-right">Hạn mức nợ</th>
              <th class="text-right">0–30 ngày</th>
              <th class="text-right">31–60 ngày</th>
              <th class="text-right">61–90 ngày</th>
              <th class="text-right">&gt; 90 ngày</th>
              <th class="text-right">Tổng còn lại</th>
              <th>Cảnh báo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in data.rows" :key="r.customer"
              class="hover:bg-sc-bg cursor-pointer"
              @click="goToDoc('SC Customer', r.customer)"
              :class="r.over_limit ? 'bg-red-50' : ''">
              <td>
                <span class="text-sc-royal hover:underline">{{ r.customer_name }}</span>
                <span class="block text-xs text-sc-text-muted font-mono">{{ r.customer }}</span>
              </td>
              <td class="text-right font-mono">{{ r.credit_limit ? fmtVND(r.credit_limit) : '—' }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.buckets['0_30']) }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.buckets['31_60']) }}</td>
              <td class="text-right font-mono">{{ fmtVND(r.buckets['61_90']) }}</td>
              <td class="text-right font-mono" :class="r.buckets.over_90 > 0 ? 'text-sc-danger font-bold' : ''">
                {{ fmtVND(r.buckets.over_90) }}
              </td>
              <td class="text-right font-mono font-semibold text-sc-danger">{{ fmtVND(r.total_outstanding) }}</td>
              <td>
                <span v-if="r.over_limit" class="sc-badge sc-badge-critical text-xs">
                  <Icon name="alert-triangle" :size="12" /> Vượt hạn mức
                </span>
                <span v-else class="text-xs text-sc-text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 3: Period Cost -->
  <div v-else-if="active === 'period'" class="space-y-4">
    <div class="sc-card p-4">
      <div class="text-xs text-sc-text-muted">Chi phí vật tư kỳ {{ fmtDate(data.from_date) }} → {{ fmtDate(data.to_date) }}</div>
      <div class="text-3xl font-bold font-mono text-sc-navy mt-2">{{ fmtVND(data.total_cost) }}</div>
    </div>
    <div class="sc-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th>Nhóm vật tư</th>
              <th class="text-right">Số PI</th>
              <th class="text-right">Tổng SL</th>
              <th class="text-right">Subtotal</th>
              <th class="text-right">% tổng</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, idx) in data.by_item_group" :key="idx" class="hover:bg-sc-bg">
              <td class="font-medium">{{ r.item_group }}</td>
              <td class="text-right font-mono">{{ r.pi_count }}</td>
              <td class="text-right font-mono">{{ fmtNumber(r.total_qty) }}</td>
              <td class="text-right font-mono font-semibold">{{ fmtVND(r.subtotal) }}</td>
              <td class="text-right font-mono">
                {{ data.total_cost > 0 ? ((r.subtotal / data.total_cost) * 100).toFixed(1) : '0' }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Drill-down modal -->
  <Modal :open="drillOpen" :title="drillData ? `Chứng từ: ${drillData.doctype} · ${drillData.name}` : ''"
    size="lg" @close="drillOpen = false">
    <div v-if="drillData" class="space-y-3 text-sm">
      <div v-if="drillData.exists === false" class="text-sc-danger">
        Chứng từ không tồn tại.
      </div>
      <template v-else>
        <div class="bg-sc-bg p-3 rounded">
          <div class="font-semibold mb-2">Header</div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <template v-for="(v, k) in drillData.header" :key="k">
              <div v-if="v != null && v !== ''" class="contents">
                <span class="text-sc-text-muted">{{ k }}:</span>
                <span class="font-mono break-all">{{ v }}</span>
              </div>
            </template>
          </div>
        </div>
        <div v-for="t in drillData.items" :key="t.table">
          <div class="font-semibold mb-1">{{ t.options }} ({{ t.rows.length }} dòng)</div>
          <div v-if="t.rows.length" class="overflow-x-auto bg-white border rounded">
            <table class="text-xs">
              <thead class="bg-sc-bg">
                <tr>
                  <th v-for="k in Object.keys(t.rows[0])" :key="k"
                    class="px-2 py-1 text-left whitespace-nowrap">{{ k }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in t.rows.slice(0, 50)" :key="i" class="border-t">
                  <td v-for="k in Object.keys(row)" :key="k"
                    class="px-2 py-1 whitespace-nowrap">{{ row[k] }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="t.rows.length > 50" class="text-xs text-sc-text-muted p-2">
              + {{ t.rows.length - 50 }} dòng khác (rút gọn)
            </div>
          </div>
        </div>
        <button @click="goToDoc(drillData.doctype, drillData.name); drillOpen = false"
          class="sc-btn-primary text-sm">Mở chứng từ <Icon name="arrow-right" :size="14" /></button>
      </template>
    </div>
  </Modal>
</template>
