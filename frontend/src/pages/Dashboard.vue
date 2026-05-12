<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '../api'
import { statusLabel } from '../modules'
import KpiCard from '../components/KpiCard.vue'
import PageHeader from '../components/PageHeader.vue'
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
const loading = ref(true)
const dashboard = ref(null)
const trend = ref([])
const period = ref('this_month')
const lastRefresh = ref(null)

async function load(force = 0) {
  loading.value = true
  try {
    dashboard.value = await call('supplycore.api.kpi.get_executive_dashboard', {
      period: period.value, force_refresh: force,
    })
    trend.value = await call('supplycore.api.kpi.get_monthly_cost_trend', { months: 12 })
    lastRefresh.value = new Date().toLocaleTimeString('vi-VN')
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))

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
      <select v-model="period" @change="load(1)" class="sc-input max-w-[160px] text-sm">
        <option value="today">Hôm nay</option>
        <option value="this_week">Tuần này</option>
        <option value="this_month">Tháng này</option>
        <option value="this_quarter">Quý này</option>
        <option value="this_year">Năm nay</option>
      </select>
      <button @click="load(1)" class="sc-btn-secondary text-sm">↻ Tải lại</button>
    </template>
  </PageHeader>

  <div v-if="loading && !dashboard" class="text-center py-20 text-sc-text-muted">Đang tải...</div>
  <template v-else-if="dashboard">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
      <KpiCard label="Tổng giá trị tồn kho"
        :value="fmtShort(dashboard.kpis.stock_value)" unit="VND" icon="📦"
        @click="gotoDrill('stock_value')" class="cursor-pointer" />
      <KpiCard label="Chi phí mua kỳ này"
        :value="fmtShort(dashboard.kpis.monthly_cost)" unit="VND" icon="💸"
        @click="gotoDrill('monthly_cost')" class="cursor-pointer" />
      <KpiCard label="Công nợ NCC"
        :value="fmtShort(dashboard.kpis.ap_outstanding)" unit="VND" icon="🧾" variant="warning"
        @click="gotoDrill('ap_outstanding')" class="cursor-pointer" />
      <KpiCard label="PO đang chờ"
        :value="dashboard.kpis.pending_pos" unit="đơn" icon="📨"
        @click="gotoDrill('pending_pos')" class="cursor-pointer" />

      <KpiCard label="Lô sắp hết hạn (30 ngày)"
        :value="dashboard.kpis.expiring_soon" unit="lô" icon="⏰" variant="warning"
        @click="gotoDrill('expiring_soon')" class="cursor-pointer" />
      <KpiCard label="Vật tư dưới tồn an toàn"
        :value="dashboard.kpis.low_stock_items" unit="vật tư" icon="📉" variant="warning"
        @click="gotoDrill('low_stock_items')" class="cursor-pointer" />
      <KpiCard label="HĐ sắp hết hạn"
        :value="dashboard.kpis.contract_expiring_30d" unit="HĐ" icon="📑"
        :variant="dashboard.kpis.contract_expiring_30d > 0 ? 'critical' : 'default'"
        @click="gotoDrill('contract_expiring_30d')" class="cursor-pointer" />
      <KpiCard label="PO quá hạn giao"
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
</template>
