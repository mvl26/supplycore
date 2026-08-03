<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../api'
import { statusLabel } from '../modules'
import KpiCard from '../components/KpiCard.vue'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import Icon from '../components/Icon.vue'
import { useAuthStore } from '../stores/auth'
import { useAccessStore } from '../stores/access'
import { useToastStore } from '../stores/toast'
import { fmtVND, fmtShort, fmtVNDShort } from '../utils'
import { PERSONA_WIDGETS, PERSONA_QUICK_ACTIONS } from '../personas'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement,
  CategoryScale, LinearScale, Filler,
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement,
  CategoryScale, LinearScale, Filler)

const router = useRouter()
const toast = useToastStore()
const auth = useAuthStore()
const access = useAccessStore()
const loading = ref(true)
const dashboard = ref(null)
const trend = ref([])
const period = ref('this_month')
const warehouse = ref('')
const department = ref('')
const roleView = ref('')   // '' = follow active persona; non-empty = manual override
const lastRefresh = ref(null)
const whOptions = ref([])
const deptOptions = ref([])
const pdfOpen = ref(false)
const pdfData = ref(null)

// Persona drives default widget set + quick actions. Manual roleView override
// (the dropdown) still wins if set — used for ad-hoc comparison views.
const persona = computed(() => access.activePersona)
const quickActions = computed(() => PERSONA_QUICK_ACTIONS[persona.value?.id] || [])

// Legacy Frappe-role → widget map kept for the manual override dropdown.
const ROLE_WIDGETS = {
  'SupplyCore Executive': ['stock_value','monthly_cost','ap_outstanding','pending_pos',
                            'expiring_soon','low_stock_items','contract_expiring_30d','po_overdue_count'],
  'SupplyCore Manager': ['stock_value','monthly_cost','pending_pos',
                         'expiring_soon','low_stock_items','contract_expiring_30d','po_overdue_count'],
  'SupplyCore Accountant': ['monthly_cost','ap_outstanding','pending_pos'],
  'SupplyCore Storekeeper': ['stock_value','expiring_soon','low_stock_items'],
}

const visibleKpiKeys = computed(() => {
  // Manual dropdown override wins.
  if (roleView.value) return new Set(ROLE_WIDGETS[roleView.value] || [])
  // Default: persona's widget set. null = show all (admin/lan).
  const w = PERSONA_WIDGETS[persona.value?.id]
  return w === null || w === undefined ? null : new Set(w)
})

function showKpi(key) {
  if (!visibleKpiKeys.value) return true
  return visibleKpiKeys.value.has(key)
}

async function load(force = 0) {
  loading.value = true
  try {
    dashboard.value = await call('supplycore.api.kpi.get_executive_dashboard', {
      period: period.value,
      warehouse: warehouse.value || null,
      department: department.value || null,
      force_refresh: force,
    })
    trend.value = await call('supplycore.api.kpi.get_monthly_cost_trend', { months: 12 })
    lastRefresh.value = new Date().toLocaleTimeString('vi-VN')
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  const [whs, depts] = await Promise.all([
    getList('SC Warehouse', { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 200 }).catch(() => []),
    getList('SC Department', { fields: ['name'], filters: { disabled: 0 }, limit: 100 }).catch(() => []),
  ])
  whOptions.value = whs
  deptOptions.value = depts
  // Default behaviour: follow active persona — leave roleView empty.
}

async function exportPdfData() {
  try {
    pdfData.value = await call('supplycore.api.kpi.get_dashboard_snapshot_pdf_data', {
      period: period.value, warehouse: warehouse.value || null,
    })
    pdfOpen.value = true
  } catch (e) {
    toast.error(`Lỗi xuất PDF: ${e.message}`)
  }
}

function printSnapshot() {
  window.print()
}

onMounted(async () => {
  await loadOptions()
  load(1)
})

// Màu chart đọc từ token CSS var (main.css :root) — không hardcode hex.
const cssVar = (name, fallback) =>
  (getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback)

const chartData = computed(() => {
  const royal = cssVar('--sc-royal', '#2E75B6')
  const navy = cssVar('--sc-navy', '#1F4E79')
  return {
    labels: trend.value.map(r => r.month),
    datasets: [{
      label: 'Chi phí mua (VND)',
      data: trend.value.map(r => r.cost),
      borderColor: royal,
      backgroundColor: royal + '1A', // ~10% alpha
      fill: true, tension: 0.3,
      pointRadius: 4, pointBackgroundColor: navy,
    }],
  }
})

const chartOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: {
    callbacks: { label: (ctx) => fmtVND(ctx.parsed.y) },
  }},
  scales: { y: { beginAtZero: true, ticks: { callback: (v) => fmtShort(v) } } },
}

const severityColor = (sev) => ({
  Critical: 'sc-badge-critical', Warning: 'sc-badge-warning', Info: 'sc-badge-info',
}[sev] || 'sc-badge-neutral')

// Internal navigation routes for drill-down
const drillTo = {
  stock_value: '/list/SC Stock Ledger Entry',
  monthly_cost: '/list/SC Purchase Invoice',
  ap_outstanding: '/list/SC Purchase Invoice',
  pending_pos: '/list/SC Purchase Order',
  expiring_soon: '/list/SC Batch',
  low_stock_items: '/m4',
  contract_expiring_30d: '/list/Framework Contract',
  po_overdue_count: '/list/SC Purchase Order',
}

function gotoDrill(key) { router.push(drillTo[key] || '/') }

// FEAT-002: Export CSV cho widget "Top vật tư tiêu thụ" + "Xu hướng chi phí"
function exportCsv(filename, rows, columns) {
  const header = columns.map(c => `"${c.label}"`).join(',')
  const body = rows.map(r => columns.map(c => {
    const v = r[c.key]
    if (v == null) return ''
    const s = String(v).replace(/"/g, '""')
    return /[",\n]/.test(s) ? `"${s}"` : s
  }).join(',')).join('\n')
  const blob = new Blob(['﻿' + header + '\n' + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function exportTopItems() {
  exportCsv(`top_items_${new Date().toISOString().slice(0,10)}.csv`,
    dashboard.value?.top_items || [],
    [
      { key: 'item_code', label: 'Mã VT' },
      { key: 'item_name', label: 'Tên VT' },
      { key: 'qty_used', label: 'Số lượng' },
      { key: 'cost',     label: 'Chi phí (VND)' },
    ])
}

function exportTrend() {
  exportCsv(`cost_trend_${new Date().toISOString().slice(0,10)}.csv`,
    trend.value || [],
    [
      { key: 'month', label: 'Tháng' },
      { key: 'cost',  label: 'Chi phí (VND)' },
    ])
}
</script>

<template>
  <PageHeader :title="persona?.id !== 'admin' ? `Dashboard — ${persona.name}` : 'Dashboard điều hành'"
    icon="bar-chart" code="SCR-01"
    :subtitle="lastRefresh ? `${persona.scope} · Cập nhật ${lastRefresh}${dashboard?.cached ? ' (đã cache 5 phút)' : ''}` : 'Đang tải...'">
    <template #actions>
      <select v-model="roleView" @change="load(1)"
        class="sc-input max-w-[220px] text-sm" title="Lọc widget theo vai trò">
        <option value="">Theo chân dung ({{ persona.role }})</option>
        <option value="SupplyCore Executive">View đầy đủ (Executive)</option>
        <option value="SupplyCore Manager">Vai trò Quản lý</option>
        <option value="SupplyCore Accountant">Vai trò Kế toán</option>
        <option value="SupplyCore Storekeeper">Vai trò Thủ kho</option>
      </select>
      <select v-model="warehouse" @change="load(1)"
        class="sc-input max-w-[160px] text-sm" title="Lọc theo kho">
        <option value="">— Tất cả kho —</option>
        <option v-for="w in whOptions" :key="w.name" :value="w.name">{{ w.name }}</option>
      </select>
      <select v-model="department" @change="load(1)"
        class="sc-input max-w-[160px] text-sm" title="Lọc theo khoa phòng">
        <option value="">— Tất cả khoa —</option>
        <option v-for="d in deptOptions" :key="d.name" :value="d.name">{{ d.name }}</option>
      </select>
      <select v-model="period" @change="load(1)" class="sc-input max-w-[140px] text-sm">
        <option value="today">Hôm nay</option>
        <option value="this_week">Tuần này</option>
        <option value="this_month">Tháng này</option>
        <option value="this_quarter">Quý này</option>
        <option value="this_year">Năm nay</option>
      </select>
      <button @click="load(1)" class="sc-btn-secondary text-sm" title="Tải lại (bỏ cache)">
        <Icon name="rotate-cw" :size="15" />
      </button>
      <button @click="exportPdfData" class="sc-btn-secondary text-sm">
        <Icon name="download" :size="15" /> Snapshot PDF
      </button>
    </template>
  </PageHeader>

  <div v-if="loading && !dashboard" class="sc-card p-4 space-y-2.5"><div v-for="n in 6" :key="n" class="sc-skeleton h-9 w-full" :style="{ opacity: 1 - n * 0.12 }" /></div>
  <template v-else-if="dashboard">
    <!-- Persona quick actions (hidden for admin / empty list) -->
    <div v-if="quickActions.length" class="flex flex-wrap gap-2 mb-4">
      <button v-for="(qa, idx) in quickActions" :key="idx"
        @click="router.push(qa.to)"
        class="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-semibold
               border transition-all duration-150 shadow-sc-xs hover:shadow-sc"
        :class="{
          'bg-sc-navy text-white border-sc-navy hover:bg-sc-navy-deep': qa.variant === 'primary',
          'bg-sc-success text-white border-sc-success/40 hover:brightness-110': qa.variant === 'success',
          'bg-sc-warning text-white border-sc-warning/40 hover:brightness-110': qa.variant === 'warning',
          'bg-sc-danger text-white border-sc-danger/40 hover:brightness-110': qa.variant === 'danger',
          'bg-sc-surface text-sc-navy border-sc-border hover:bg-sc-royal-50':
            !qa.variant || qa.variant === 'ghost',
        }">
        <Icon :name="qa.icon" :size="15" />
        {{ qa.label }}
      </button>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5 sc-stagger">
      <KpiCard v-if="showKpi('stock_value')" label="Tổng giá trị tồn kho"
        :value="fmtVNDShort(dashboard.kpis.stock_value)" :title="fmtVND(dashboard.kpis.stock_value)" icon="package"
        @click="gotoDrill('stock_value')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('monthly_cost')" label="Chi phí mua kỳ này"
        :value="fmtVNDShort(dashboard.kpis.monthly_cost)" :title="fmtVND(dashboard.kpis.monthly_cost)" icon="banknote"
        @click="gotoDrill('monthly_cost')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('ap_outstanding')" label="Công nợ NCC"
        :value="fmtVNDShort(dashboard.kpis.ap_outstanding)" :title="fmtVND(dashboard.kpis.ap_outstanding)" icon="receipt" variant="warning"
        @click="gotoDrill('ap_outstanding')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('pending_pos')" label="PO đang chờ"
        :value="dashboard.kpis.pending_pos" unit="đơn" icon="inbox"
        @click="gotoDrill('pending_pos')" class="cursor-pointer" />

      <KpiCard v-if="showKpi('expiring_soon')" label="Lô sắp hết hạn (30 ngày)"
        :value="dashboard.kpis.expiring_soon" unit="lô" icon="alarm-clock" variant="warning"
        @click="gotoDrill('expiring_soon')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('low_stock_items')" label="Vật tư dưới tồn an toàn"
        :value="dashboard.kpis.low_stock_items" unit="vật tư" icon="trending-down" variant="warning"
        @click="gotoDrill('low_stock_items')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('contract_expiring_30d')" label="HĐ sắp hết hạn"
        :value="dashboard.kpis.contract_expiring_30d" unit="HĐ" icon="file-text"
        :variant="dashboard.kpis.contract_expiring_30d > 0 ? 'critical' : 'default'"
        @click="gotoDrill('contract_expiring_30d')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('po_overdue_count')" label="PO quá hạn giao"
        :value="dashboard.kpis.po_overdue_count" unit="đơn" icon="alert-triangle"
        :variant="dashboard.kpis.po_overdue_count > 0 ? 'critical' : 'default'"
        @click="gotoDrill('po_overdue_count')" class="cursor-pointer" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
      <div class="lg:col-span-2 sc-card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-sc-navy">Xu hướng chi phí 12 tháng</h3>
          <button v-if="trend.length" @click="exportTrend"
            class="text-xs text-sc-royal hover:underline inline-flex items-center gap-1" title="Xuất dữ liệu chart sang CSV">
            <Icon name="download" :size="13" /> CSV
          </button>
        </div>
        <div class="h-72">
          <Line v-if="trend.length" :data="chartData" :options="chartOptions" />
          <div v-else class="text-center py-20 text-sc-text-muted">Chưa có dữ liệu</div>
        </div>
      </div>

      <div class="sc-card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-sc-navy">Cảnh báo đang mở</h3>
          <router-link to="/alerts" class="text-xs text-sc-royal hover:underline">Tất cả →</router-link>
        </div>
        <div v-if="dashboard.open_alerts_total === 0"
          class="flex flex-col items-center gap-2 text-sm text-sc-text-muted text-center py-10">
          <span class="h-10 w-10 rounded-full bg-sc-success-50 text-sc-success flex items-center justify-center">
            <Icon name="check" :size="20" />
          </span>
          Không có cảnh báo đang mở
        </div>
        <div v-else>
          <div class="text-4xl font-bold text-sc-navy mb-3">{{ dashboard.open_alerts_total }}</div>
          <div class="space-y-2">
            <div v-for="(c, sev) in dashboard.open_alerts" :key="sev"
              class="flex items-center justify-between text-sm">
              <span :class="['sc-badge', severityColor(sev)]">{{ statusLabel(sev) }}</span>
              <span class="font-mono">{{ c }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="sc-card p-5">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-sc-navy">Top 10 vật tư tiêu thụ</h3>
        <div class="flex items-center gap-3">
          <button v-if="dashboard.top_items.length" @click="exportTopItems"
            class="text-xs text-sc-royal hover:underline inline-flex items-center gap-1" title="Xuất bảng sang CSV">
            <Icon name="download" :size="13" /> CSV
          </button>
          <router-link to="/m4" class="text-xs text-sc-royal hover:underline">Xem kho →</router-link>
        </div>
      </div>
      <table v-if="dashboard.top_items.length" class="sc-table">
        <thead><tr>
          <th class="w-10">#</th><th>Mã VT</th><th>Tên</th>
          <th class="text-right">SL</th><th class="text-right">Chi phí (VND)</th>
        </tr></thead>
        <tbody>
          <tr v-for="(item, idx) in dashboard.top_items" :key="item.item_code"
            @click="router.push(`/doc/SC Item/${encodeURIComponent(item.item_code)}`)"
            class="cursor-pointer">
            <td class="text-sc-text-muted">{{ idx + 1 }}</td>
            <td class="font-mono text-xs">{{ item.item_code }}</td>
            <td>{{ item.item_name }}</td>
            <td class="text-right font-mono">{{ fmtShort(item.qty_used) }}</td>
            <td class="text-right font-mono" :title="fmtVND(item.cost)">{{ fmtVND(item.cost) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="text-center py-10 text-sc-text-muted">Chưa có dữ liệu</div>
    </div>
  </template>

  <!-- PDF snapshot dialog (window.print() để export PDF qua trình duyệt) -->
  <Modal :open="pdfOpen" :title="pdfData ? pdfData.title : 'Snapshot Dashboard'" size="lg"
    @close="pdfOpen = false">
    <div v-if="pdfData" class="space-y-4 text-sm print:p-6">
      <div class="text-xs text-sc-text-muted border-b pb-2 print:text-sm">
        Tạo lúc: {{ pdfData.generated_at }} · Bởi: {{ pdfData.generated_by }} ·
        Kỳ: <strong>{{ pdfData.period.label }}</strong> ({{ pdfData.period.from }} → {{ pdfData.period.to }})
        <span v-if="pdfData.filters.warehouse"> · Kho: {{ pdfData.filters.warehouse }}</span>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div v-for="(v, k) in pdfData.kpis" :key="k" class="border rounded p-3">
          <div class="text-xs text-sc-text-muted">{{ k }}</div>
          <div class="text-lg font-bold font-mono">{{ fmtShort(v) }}</div>
        </div>
      </div>
      <div v-if="pdfData.top_items?.length">
        <div class="font-semibold mb-1">Top vật tư tiêu thụ</div>
        <table class="text-xs w-full">
          <thead class="bg-sc-bg">
            <tr><th class="p-1 text-left">Mã</th><th class="p-1 text-left">Tên</th>
                <th class="p-1 text-right">SL</th><th class="p-1 text-right">Chi phí</th></tr>
          </thead>
          <tbody>
            <tr v-for="t in pdfData.top_items" :key="t.item_code" class="border-t">
              <td class="p-1 font-mono">{{ t.item_code }}</td>
              <td class="p-1">{{ t.item_name }}</td>
              <td class="p-1 text-right font-mono">{{ fmtShort(t.qty_used) }}</td>
              <td class="p-1 text-right font-mono" :title="fmtVND(t.cost)">{{ fmtVND(t.cost) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <template #footer>
      <button @click="pdfOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
      <button @click="printSnapshot" class="sc-btn-primary text-sm">
        <Icon name="printer" :size="15" /> In / Xuất PDF
      </button>
    </template>
  </Modal>
</template>
