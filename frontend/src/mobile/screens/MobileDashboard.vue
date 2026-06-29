<!-- frontend/src/mobile/screens/MobileDashboard.vue -->
<template>
  <div class="m-page">
    <!-- Header -->
    <div class="m-head">
      <div>
        <div class="m-hi">Xin chào,</div>
        <div class="m-name">{{ auth.user.full_name || auth.user.name }}</div>
      </div>
      <button class="m-btn-link" @click="handleLogout">
        <Icon name="log-out" :size="15" />
        Đăng xuất
      </button>
    </div>

    <!-- KPI cards -->
    <div v-if="kpiLoaded || kpiLoading" class="m-kpis">
      <div v-if="kpiLoading" class="m-kpi-loading">
        <div class="sc-skeleton m-skel" />
        <div class="sc-skeleton m-skel" />
        <div class="sc-skeleton m-skel" />
      </div>
      <template v-else-if="kpiLoaded">
        <div class="m-kpi">
          <span class="m-kpi-val">{{ kpis.expiring_soon ?? 0 }}</span>
          <label class="m-kpi-lbl">Sắp hết hạn</label>
        </div>
        <div class="m-kpi">
          <span class="m-kpi-val">{{ kpis.low_stock_items ?? 0 }}</span>
          <label class="m-kpi-lbl">Tồn thấp</label>
        </div>
        <div class="m-kpi">
          <span class="m-kpi-val">{{ kpis.pending_pos ?? 0 }}</span>
          <label class="m-kpi-lbl">PO chờ</label>
        </div>
        <div class="m-kpi">
          <span class="m-kpi-val">{{ openAlertsTotal ?? 0 }}</span>
          <label class="m-kpi-lbl">Cảnh báo mở</label>
        </div>
      </template>
    </div>

    <!-- Alerts section -->
    <div class="m-section-head">
      <h2 class="m-h2">
        <Icon name="bell" :size="16" class="m-icon-navy" />
        Cảnh báo
      </h2>
      <button class="m-btn-link" :disabled="alertsLoading" @click="load">
        <Icon name="refresh-cw" :size="13" :class="{ 'm-spin': alertsLoading }" />
        Làm mới
      </button>
    </div>

    <p v-if="alertsLoading" class="m-muted">Đang tải...</p>

    <template v-else>
      <p v-if="!alerts.length" class="m-muted">Không có cảnh báo.</p>
      <ul v-else class="m-list">
        <li v-for="a in alerts" :key="a.name" class="m-card">
          <div class="m-card-top">
            <span class="m-card-title">{{ a.title }}</span>
            <span class="sc-badge" :class="badgeClass(a.severity)">
              {{ severityLabel(a.severity) }}
            </span>
          </div>
          <p v-if="a.message" class="m-card-msg">{{ a.message }}</p>
          <div v-if="a.alert_date" class="m-card-date">{{ fmtDate(a.alert_date) }}</div>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { useToastStore } from '../../stores/toast'
import { STATUS_LABEL } from '../../modules'
import { fmtDate } from '../../utils'
import Icon from '../../components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()
const toast = useToastStore()

const kpis = ref({})
const openAlertsTotal = ref(0)
const kpiLoading = ref(false)
const kpiLoaded = ref(false)

const alerts = ref([])
const alertsLoading = ref(false)

// Inline severity → badge-variant mapping (mirrors modules.js STATUS_BADGE)
const SEVERITY_BADGE = {
  Critical: 'sc-badge-critical',
  High:     'sc-badge-critical',
  Warning:  'sc-badge-warning',
  Medium:   'sc-badge-warning',
  Info:     'sc-badge-info',
  Low:      'sc-badge-info',
}

function badgeClass(severity) {
  return SEVERITY_BADGE[severity] || 'sc-badge-neutral'
}

function severityLabel(severity) {
  return STATUS_LABEL[severity] || severity || ''
}

async function loadKpis() {
  kpiLoading.value = true
  try {
    const data = await call('supplycore.api.kpi.get_executive_dashboard', { period: 'this_month' })
    if (data) {
      kpis.value = data.kpis || {}
      openAlertsTotal.value = data.open_alerts_total ?? 0
      kpiLoaded.value = true
    }
  } catch (e) {
    // Permission gap expected for lower-privilege personas — silently hide KPI cards
    kpiLoaded.value = false
  } finally {
    kpiLoading.value = false
  }
}

async function loadAlerts() {
  alertsLoading.value = true
  try {
    const rows = await getList('SC Alert', {
      fields: ['name', 'alert_date', 'alert_type', 'severity', 'title', 'message'],
      filters: [['resolved', '=', 0]],
      order_by: 'alert_date desc',
      limit: 50,
    })
    alerts.value = Array.isArray(rows) ? rows : []
  } catch (e) {
    toast.error(e.message || 'Không thể tải danh sách cảnh báo.')
    alerts.value = []
  } finally {
    alertsLoading.value = false
  }
}

async function load() {
  // Independent calls — failure of one does not blank the other
  await Promise.allSettled([loadKpis(), loadAlerts()])
}

async function handleLogout() {
  await auth.mobileLogout()
  router.replace('/m/setup')
}

onMounted(load)
</script>

<style scoped>
.m-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Header */
.m-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.m-hi {
  font-size: 12px;
  color: #9ca3af;
}
.m-name {
  font-size: 16px;
  font-weight: 700;
  color: #1F4E79;
}
.m-btn-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #2E75B6;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 0;
}
.m-btn-link:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* KPI */
.m-kpis {
  display: flex;
  gap: 8px;
}
.m-kpi {
  flex: 1;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 6px;
  text-align: center;
  background: #fff;
}
.m-kpi-val {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #1F4E79;
  line-height: 1.2;
}
.m-kpi-lbl {
  display: block;
  font-size: 10px;
  color: #6b7280;
  margin-top: 2px;
  line-height: 1.3;
}
.m-kpi-loading {
  display: flex;
  gap: 8px;
  flex: 1;
}
.m-skel {
  flex: 1;
  height: 68px;
  border-radius: 10px;
}

/* Section header */
.m-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.m-h2 {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #1F4E79;
  margin: 0;
}
.m-icon-navy {
  color: #1F4E79;
}

/* Alert list */
.m-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.m-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}
.m-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.m-card-title {
  font-weight: 600;
  color: #1F4E79;
  font-size: 13px;
  flex: 1;
}
.m-card-msg {
  margin: 6px 0 0;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.5;
}
.m-card-date {
  margin-top: 6px;
  font-size: 11px;
  color: #9ca3af;
}

/* Muted / empty */
.m-muted {
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
  padding: 16px 0;
}

/* Spinner */
@keyframes m-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.m-spin {
  animation: m-spin 0.7s linear infinite;
}
</style>
