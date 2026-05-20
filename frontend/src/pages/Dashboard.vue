<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../api'
import { statusLabel } from '../modules'
import KpiCard from '../components/KpiCard.vue'
import PageHeader from '../components/PageHeader.vue'
import Modal from '../components/Modal.vue'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
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
const loading = ref(true)
const dashboard = ref(null)
const trend = ref([])
const period = ref('this_month')
const warehouse = ref('')
const department = ref('')
const roleView = ref('')   // '' = full executive view
const lastRefresh = ref(null)
const whOptions = ref([])
const deptOptions = ref([])
const pdfOpen = ref(false)
const pdfData = ref(null)

// Role mapping → widget allow-list (matches backend ROLE_WIDGETS)
const ROLE_WIDGETS = {
  'SupplyCore Executive': ['stock_value','monthly_cost','ap_outstanding','pending_pos',
                            'expiring_soon','low_stock_items','contract_expiring_30d','po_overdue_count'],
  'SupplyCore Manager': ['stock_value','monthly_cost','pending_pos',
                         'expiring_soon','low_stock_items','contract_expiring_30d','po_overdue_count'],
  'SupplyCore Accountant': ['monthly_cost','ap_outstanding','pending_pos'],
  'SupplyCore Storekeeper': ['stock_value','expiring_soon','low_stock_items'],
  'Pharmacy Officer': ['monthly_cost','expiring_soon'],
}

const visibleKpiKeys = computed(() => {
  if (!roleView.value) return null  // null = show all
  return new Set(ROLE_WIDGETS[roleView.value] || [])
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
  // Auto-detect role view based on user roles
  const userRoles = auth.user?.roles || []
  for (const r of ['SupplyCore Executive','SupplyCore Manager','SupplyCore Accountant',
                    'SupplyCore Storekeeper','Pharmacy Officer']) {
    if (userRoles.includes(r)) { roleView.value = ''; break }
  }
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

const fmtVND = (v) => new Intl.NumberFormat('vi-VN', {
  style: 'currency', currency: 'VND', maximumFractionDigits: 0,
}).format(Number(v) || 0)

const fmtShort = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + ' tỷ'
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + ' tr'
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'k'
  return n.toLocaleString('vi-VN')
}

const chartData = computed(() => ({
  labels: trend.value.map(r => r.month),
  datasets: [{
    label: 'Chi phí mua (VND)',
    data: trend.value.map(r => r.cost),
    borderColor: '#2E75B6',
    backgroundColor: 'rgba(46, 117, 182, 0.1)',
    fill: true, tension: 0.3,
    pointRadius: 4, pointBackgroundColor: '#1F4E79',
  }],
}))

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
</script>

<template>
  <PageHeader title="Dashboard điều hành" icon="📊" code="SCR-01"
    :subtitle="lastRefresh ? `Cập nhật ${lastRefresh}${dashboard?.cached ? ' (đã cache 5 phút)' : ''}` : 'Đang tải...'">
    <template #actions>
      <select v-model="roleView" @change="load(1)"
        class="sc-input max-w-[200px] text-sm" title="Lọc widget theo vai trò">
        <option value="">📊 View đầy đủ (Executive)</option>
        <option value="SupplyCore Manager">👔 Manager</option>
        <option value="SupplyCore Accountant">🧮 Kế toán</option>
        <option value="SupplyCore Storekeeper">📦 Thủ kho</option>
        <option value="Pharmacy Officer">💊 Dược viên</option>
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
      <button @click="load(1)" class="sc-btn-secondary text-sm" title="Tải lại (bỏ cache)">↻</button>
      <button @click="exportPdfData" class="sc-btn-secondary text-sm">📄 Snapshot PDF</button>
    </template>
  </PageHeader>

  <div v-if="loading && !dashboard" class="text-center py-20 text-sc-text-muted">Đang tải...</div>
  <template v-else-if="dashboard">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
      <KpiCard v-if="showKpi('stock_value')" label="Tổng giá trị tồn kho"
        :value="fmtShort(dashboard.kpis.stock_value)" unit="VND" icon="📦"
        @click="gotoDrill('stock_value')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('monthly_cost')" label="Chi phí mua kỳ này"
        :value="fmtShort(dashboard.kpis.monthly_cost)" unit="VND" icon="💸"
        @click="gotoDrill('monthly_cost')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('ap_outstanding')" label="Công nợ NCC"
        :value="fmtShort(dashboard.kpis.ap_outstanding)" unit="VND" icon="🧾" variant="warning"
        @click="gotoDrill('ap_outstanding')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('pending_pos')" label="PO đang chờ"
        :value="dashboard.kpis.pending_pos" unit="đơn" icon="📨"
        @click="gotoDrill('pending_pos')" class="cursor-pointer" />

      <KpiCard v-if="showKpi('expiring_soon')" label="Lô sắp hết hạn (30 ngày)"
        :value="dashboard.kpis.expiring_soon" unit="lô" icon="⏰" variant="warning"
        @click="gotoDrill('expiring_soon')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('low_stock_items')" label="Vật tư dưới tồn an toàn"
        :value="dashboard.kpis.low_stock_items" unit="vật tư" icon="📉" variant="warning"
        @click="gotoDrill('low_stock_items')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('contract_expiring_30d')" label="HĐ sắp hết hạn"
        :value="dashboard.kpis.contract_expiring_30d" unit="HĐ" icon="📑"
        :variant="dashboard.kpis.contract_expiring_30d > 0 ? 'critical' : 'default'"
        @click="gotoDrill('contract_expiring_30d')" class="cursor-pointer" />
      <KpiCard v-if="showKpi('po_overdue_count')" label="PO quá hạn giao"
        :value="dashboard.kpis.po_overdue_count" unit="đơn" icon="⚠️"
        :variant="dashboard.kpis.po_overdue_count > 0 ? 'critical' : 'default'"
        @click="gotoDrill('po_overdue_count')" class="cursor-pointer" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
      <div class="lg:col-span-2 sc-card p-5">
        <h3 class="font-semibold text-sc-navy mb-3">Xu hướng chi phí 12 tháng</h3>
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
        <div v-if="dashboard.open_alerts_total === 0" class="text-sm text-sc-text-muted text-center py-10">
          ✓ Không có cảnh báo
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
        <router-link to="/m4" class="text-xs text-sc-royal hover:underline">Xem kho →</router-link>
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
            <td class="text-right font-mono">{{ fmtShort(item.cost) }}</td>
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
              <td class="p-1 text-right font-mono">{{ fmtShort(t.cost) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <template #footer>
      <button @click="pdfOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
      <button @click="printSnapshot" class="sc-btn-primary text-sm">🖨️ In / Xuất PDF</button>
    </template>
  </Modal>
</template>
