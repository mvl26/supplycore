<!-- frontend/src/mobile/screens/MobileDashboard.vue -->
<template>
  <MPullRefresh :refreshing="refreshing" @refresh="onPullRefresh">
    <MTopBar title="Bảng tin" :sub="auth.user.full_name">
      <template #right>
        <button class="m-btn m-btn--ghost m-btn--sm" @click="logout">Đăng xuất</button>
      </template>
    </MTopBar>

    <div class="m-page">
      <!-- KPI cards: chỉ hiển thị khi đang tải hoặc đã tải thành công; lỗi → ẩn hoàn toàn -->
      <div v-if="kpiLoading || kpiLoaded" class="m-kpis">
        <template v-if="kpiLoading">
          <div class="m-sk m-sk-kpi" />
          <div class="m-sk m-sk-kpi" />
          <div class="m-sk m-sk-kpi" />
        </template>
        <template v-else>
          <div class="m-kpi">
            <span class="m-kpi__val">{{ kpis.expiring_soon ?? 0 }}</span>
            <span class="m-kpi__lbl">Sắp hết hạn</span>
          </div>
          <div class="m-kpi">
            <span class="m-kpi__val">{{ kpis.low_stock_items ?? 0 }}</span>
            <span class="m-kpi__lbl">Tồn thấp</span>
          </div>
          <div class="m-kpi">
            <span class="m-kpi__val">{{ kpis.pending_pos ?? 0 }}</span>
            <span class="m-kpi__lbl">PO chờ</span>
          </div>
        </template>
      </div>

      <!-- Tiêu đề phần Cảnh báo -->
      <div class="m-section-head">
        <h2 class="m-section-title">
          <Icon name="bell" :size="16" />
          Cảnh báo
        </h2>
        <button
          class="m-btn m-btn--ghost m-btn--sm"
          :disabled="alertsLoading"
          @click="onRefreshAlerts"
        >
          <Icon name="rotate-cw" :size="13" :class="{ 'm-ptr__spin': alertsLoading }" />
          Làm mới
        </button>
      </div>

      <!-- Trạng thái đang tải -->
      <MSkeleton v-if="alertsLoading" :count="3" />

      <!-- Trạng thái lỗi -->
      <MErrorState
        v-else-if="alertsError"
        title="Không tải được cảnh báo"
        @retry="loadAlerts"
      />

      <!-- Danh sách rỗng -->
      <MEmpty
        v-else-if="!alerts.length"
        icon="check-circle"
        title="Không có cảnh báo"
        sub="Hệ thống đang hoạt động bình thường"
      />

      <!-- Danh sách cảnh báo -->
      <ul v-else class="m-list">
        <li
          v-for="(a, i) in alerts"
          :key="a.name"
          class="m-card m-rise"
          :style="{ animationDelay: i * 28 + 'ms' }"
        >
          <div class="m-card__row">
            <span class="m-card__title">{{ a.title }}</span>
            <MBadge :status="a.severity" />
          </div>
          <p v-if="a.message" class="m-alert-msg">{{ a.message }}</p>
          <div v-if="a.alert_date" class="m-alert-date">{{ fmtDate(a.alert_date) }}</div>
        </li>
      </ul>
    </div>
  </MPullRefresh>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { fmtDate } from '../../utils'
import Icon from '../../components/Icon.vue'
import MTopBar from '../ui/MTopBar.vue'
import MBadge from '../ui/MBadge.vue'
import MSkeleton from '../ui/MSkeleton.vue'
import MEmpty from '../ui/MEmpty.vue'
import MErrorState from '../ui/MErrorState.vue'
import MPullRefresh from '../ui/MPullRefresh.vue'
import { tapLight } from '../native'

const auth = useAuthStore()
const router = useRouter()

const kpis = ref({})
const kpiLoading = ref(false)
const kpiLoaded = ref(false)

const alerts = ref([])
const alertsLoading = ref(false)
const alertsError = ref(false)

const refreshing = ref(false)

async function loadKpis() {
  kpiLoading.value = true
  try {
    const data = await call('supplycore.api.kpi.get_executive_dashboard', { period: 'this_month' })
    if (data) {
      kpis.value = data.kpis || {}
      kpiLoaded.value = true
    }
  } catch {
    // Thiếu quyền hoặc lỗi mạng — ẩn KPI, không toast
    kpiLoaded.value = false
  } finally {
    kpiLoading.value = false
  }
}

async function loadAlerts() {
  alertsLoading.value = true
  alertsError.value = false
  try {
    const rows = await getList('SC Alert', {
      fields: ['name', 'alert_date', 'alert_type', 'severity', 'title', 'message'],
      filters: [['resolved', '=', 0]],
      order_by: 'alert_date desc',
      limit: 50,
    })
    alerts.value = Array.isArray(rows) ? rows : []
  } catch {
    alertsError.value = true
    alerts.value = []
  } finally {
    alertsLoading.value = false
  }
}

// KPI và alerts fetch độc lập — một lỗi không làm trắng cái kia
async function loadAll() {
  await Promise.allSettled([loadKpis(), loadAlerts()])
}

async function onPullRefresh() {
  refreshing.value = true
  await loadAll()
  refreshing.value = false
}

async function onRefreshAlerts() {
  tapLight()
  await loadAlerts()
}

async function logout() {
  tapLight()
  await auth.mobileLogout()
  router.replace('/m/setup')
}

onMounted(loadAll)
</script>

<style scoped>
/* KPI skeleton dạng lưới 3 cột */
.m-sk-kpi {
  height: 80px;
  border-radius: var(--m-r, 14px);
}

/* Section header: tiêu đề + nút Làm mới */
.m-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.m-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 650;
  color: var(--m-navy, #1F4E79);
  margin: 0;
}

/* Nội dung card cảnh báo */
.m-alert-msg {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--m-ink-2, #475569);
  line-height: 1.5;
}
.m-alert-date {
  margin-top: 6px;
  font-size: 11px;
  color: var(--m-ink-3, #94A3B8);
}
</style>
