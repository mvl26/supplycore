<script setup>
import { ref, onMounted, computed } from 'vue'
import { call } from '../api'
import KpiCard from '../components/KpiCard.vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement,
  CategoryScale, LinearScale, Filler,
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement,
  CategoryScale, LinearScale, Filler)

const loading = ref(true)
const error = ref(null)
const dashboard = ref(null)
const trend = ref([])

const period = ref('this_month')
const warehouse = ref(null)
const lastRefresh = ref(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    dashboard.value = await call('supplycore.api.kpi.get_executive_dashboard', {
      period: period.value,
      warehouse: warehouse.value || null,
      force_refresh: 1,
    })
    trend.value = await call('supplycore.api.kpi.get_monthly_cost_trend', { months: 12 })
    lastRefresh.value = new Date().toLocaleTimeString('vi-VN')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

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
    fill: true,
    tension: 0.3,
    pointRadius: 4,
    pointBackgroundColor: '#1F4E79',
  }],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => fmtVND(ctx.parsed.y),
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: (v) => fmtShort(v) },
    },
  },
}

const severityColor = (sev) => ({
  Critical: 'sc-badge-critical',
  Warning:  'sc-badge-warning',
  Info:     'sc-badge-info',
}[sev] || 'sc-badge-neutral')
</script>

<template>
  <div>
    <!-- Filters -->
    <div class="flex items-center gap-3 mb-5">
      <label class="text-sm text-sc-text-muted">Kỳ:</label>
      <select v-model="period" @change="load" class="sc-input max-w-[180px]">
        <option value="today">Hôm nay</option>
        <option value="this_week">Tuần này</option>
        <option value="this_month">Tháng này</option>
        <option value="this_quarter">Quý này</option>
        <option value="this_year">Năm nay</option>
      </select>
      <button @click="load" class="sc-btn-secondary text-sm">↻ Refresh</button>
      <span v-if="dashboard?.cached" class="text-xs text-sc-text-muted">
        Cập nhật lúc {{ lastRefresh }} (cached)
      </span>
      <span v-else-if="lastRefresh" class="text-xs text-sc-text-muted">
        Cập nhật lúc {{ lastRefresh }}
      </span>
    </div>

    <div v-if="loading" class="text-center py-20 text-sc-text-muted">Đang tải...</div>
    <div v-else-if="error" class="sc-card p-6 border-l-4 border-sc-danger">
      <div class="font-medium text-sc-danger">Lỗi tải dashboard</div>
      <div class="text-sm text-sc-text-muted mt-1">{{ error }}</div>
    </div>
    <template v-else-if="dashboard">
      <!-- KPI Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        <KpiCard label="Tổng giá trị tồn kho"
          :value="fmtShort(dashboard.kpis.stock_value)" unit="VND"
          icon="📦" :href="dashboard.drill_down.stock_value" />
        <KpiCard label="Chi phí mua kỳ này"
          :value="fmtShort(dashboard.kpis.monthly_cost)" unit="VND"
          icon="💸" :href="dashboard.drill_down.monthly_cost" />
        <KpiCard label="Công nợ NCC"
          :value="fmtShort(dashboard.kpis.ap_outstanding)" unit="VND"
          icon="🧾" variant="warning"
          :href="dashboard.drill_down.ap_outstanding" />
        <KpiCard label="PO chờ"
          :value="dashboard.kpis.pending_pos" unit="đơn"
          icon="📨" :href="dashboard.drill_down.pending_pos" />

        <KpiCard label="Lô sắp hết hạn (30 ngày)"
          :value="dashboard.kpis.expiring_soon" unit="lô"
          icon="⏰" variant="warning"
          :href="dashboard.drill_down.expiring_soon" />
        <KpiCard label="Items dưới safety stock"
          :value="dashboard.kpis.low_stock_items" unit="items"
          icon="📉" variant="warning"
          :href="dashboard.drill_down.low_stock_items" />
        <KpiCard label="HĐ sắp hết hạn (30 ngày)"
          :value="dashboard.kpis.contract_expiring_30d" unit="HĐ"
          icon="📑" :variant="dashboard.kpis.contract_expiring_30d > 0 ? 'critical' : 'default'"
          :href="dashboard.drill_down.contract_expiring_30d" />
        <KpiCard label="PO quá hạn giao"
          :value="dashboard.kpis.po_overdue_count" unit="đơn"
          icon="⚠️" :variant="dashboard.kpis.po_overdue_count > 0 ? 'critical' : 'default'"
          :href="dashboard.drill_down.po_overdue_count" />
      </div>

      <!-- 2-column: Chart + Alerts -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
        <div class="lg:col-span-2 sc-card p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sc-navy">Xu hướng chi phí 12 tháng</h3>
            <a href="/app/sc-purchase-invoice" class="text-xs text-sc-royal hover:underline">
              Chi tiết →
            </a>
          </div>
          <div class="h-72">
            <Line v-if="trend.length" :data="chartData" :options="chartOptions" />
            <div v-else class="text-center py-20 text-sc-text-muted">Chưa có dữ liệu</div>
          </div>
        </div>

        <div class="sc-card p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sc-navy">Cảnh báo đang mở</h3>
            <router-link to="/alerts" class="text-xs text-sc-royal hover:underline">
              Tất cả →
            </router-link>
          </div>
          <div v-if="dashboard.open_alerts_total === 0" class="text-sm text-sc-text-muted text-center py-10">
            ✓ Không có cảnh báo
          </div>
          <div v-else>
            <div class="text-3xl font-bold text-sc-navy mb-3">{{ dashboard.open_alerts_total }}</div>
            <div class="space-y-2">
              <div v-for="(count, sev) in dashboard.open_alerts" :key="sev"
                class="flex items-center justify-between text-sm">
                <span :class="['sc-badge', severityColor(sev)]">{{ sev }}</span>
                <span class="font-mono text-sc-text">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top items -->
      <div class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy mb-3">Top 10 vật tư tiêu thụ</h3>
        <table v-if="dashboard.top_items.length" class="sc-table">
          <thead>
            <tr>
              <th class="w-10">#</th>
              <th>Mã VT</th>
              <th>Tên</th>
              <th class="text-right">SL tiêu thụ</th>
              <th class="text-right">Chi phí (VND)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in dashboard.top_items" :key="item.item_code">
              <td class="text-sc-text-muted">{{ idx + 1 }}</td>
              <td class="font-mono text-xs">{{ item.item_code }}</td>
              <td>{{ item.item_name }}</td>
              <td class="text-right font-mono">{{ fmtShort(item.qty_used) }}</td>
              <td class="text-right font-mono">{{ fmtShort(item.cost) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-10 text-sc-text-muted">
          Chưa có dữ liệu tiêu thụ trong kỳ
        </div>
      </div>
    </template>
  </div>
</template>
