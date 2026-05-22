<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getList, count, runDocMethod } from '../api'
import { useToastStore } from '../stores/toast'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'
import FieldInput from '../components/FieldInput.vue'
import Pagination from '../components/Pagination.vue'

const router = useRouter()
const toast = useToastStore()

const alerts = ref([])
const loading = ref(true)
const filter = ref('open')
const severityFilter = ref('all')
const searchText = ref('')
const sortKey = ref('alert_date')
const sortDir = ref('desc')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const selected = ref(null)
const actionType = ref(null)
const actionInput = ref({ remarks: '', hours: 4, reason: '', user: '' })

function buildFilters() {
  const filters = []
  if (filter.value === 'open') filters.push(['resolved', '=', 0])
  else if (filter.value === 'resolved') filters.push(['resolved', '=', 1])
  if (severityFilter.value !== 'all') filters.push(['severity', '=', severityFilter.value])
  if (searchText.value) filters.push(['title', 'like', `%${searchText.value}%`])
  return filters
}

async function load() {
  loading.value = true
  try {
    const filters = buildFilters()
    const start = (page.value - 1) * pageSize.value
    const [data, cnt] = await Promise.all([
      getList('SC Alert', {
        fields: ['name', 'alert_date', 'alert_type', 'severity', 'title', 'message',
                 'reference_doctype', 'reference_name', 'resolved', 'snooze_until',
                 'snooze_reason', 'assigned_to', 'escalated'],
        filters,
        order_by: `${sortKey.value} ${sortDir.value}`,
        limit: pageSize.value,
        start,
      }),
      count('SC Alert', filters).catch(() => 0),
    ])
    alerts.value = data
    total.value = cnt
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Debounce search
let searchTimer = null
let searchInit = true
watch(searchText, () => {
  if (searchInit) { searchInit = false; return }
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; load() }, 300)
})

const counts = computed(() => ({ all: total.value }))

const sevCls = (s) => ({
  Critical: 'sc-badge-critical', Warning: 'sc-badge-warning', Info: 'sc-badge-info',
}[s] || 'sc-badge-neutral')

const sevLabel = (s) => ({
  Critical: 'Nghiêm trọng', Warning: 'Cảnh báo', Info: 'Thông tin',
}[s] || s)

const fmt = (d) => d ? new Date(d).toLocaleString('vi-VN') : ''

function openAction(a, type) {
  selected.value = a
  actionType.value = type
  actionInput.value = { remarks: '', hours: 4, reason: '', user: '' }
}
function closeAction() { selected.value = null; actionType.value = null }

async function performAction() {
  if (!selected.value || !actionType.value) return
  try {
    const dt = 'SC Alert'
    const nm = selected.value.name
    if (actionType.value === 'resolve') {
      await runDocMethod(dt, nm, 'mark_resolved', {
        action: 'Acted Upon', remarks: actionInput.value.remarks,
      })
      toast.success('Đã đánh dấu xử lý')
    } else if (actionType.value === 'snooze') {
      await runDocMethod(dt, nm, 'snooze_alert', {
        hours: actionInput.value.hours, reason: actionInput.value.reason,
      })
      toast.success(`Đã tạm ẩn ${actionInput.value.hours}h`)
    } else if (actionType.value === 'assign') {
      await runDocMethod(dt, nm, 'assign_alert', {
        user: actionInput.value.user, note: actionInput.value.remarks,
      })
      toast.success(`Đã giao cho ${actionInput.value.user}`)
    }
    closeAction()
    await load()
  } catch (e) {
    toast.error(e.message)
  }
}

function openRef(a) {
  if (a.reference_doctype && a.reference_name) {
    router.push(`/doc/${encodeURIComponent(a.reference_doctype)}/${encodeURIComponent(a.reference_name)}`)
  }
}
</script>

<template>
  <PageHeader title="Trung tâm cảnh báo" icon="bell" code="SCR-13"
    :subtitle="`${counts.all} cảnh báo trong bộ lọc hiện tại`">
    <template #actions>
      <button @click="load" class="sc-btn-secondary text-sm"><Icon name="rotate-cw" :size="14" /> Tải lại</button>
    </template>
  </PageHeader>

  <div class="sc-card p-3 mb-4 flex flex-wrap items-center gap-2">
    <div class="flex gap-1">
      <button v-for="f in ['open', 'resolved', 'all']" :key="f"
        @click="filter = f; page = 1; load()"
        class="px-3 py-1.5 rounded-md text-sm font-medium transition"
        :class="filter === f ? 'bg-sc-navy text-white' : 'bg-sc-bg hover:bg-sc-border'">
        {{ {open: 'Đang mở', resolved: 'Đã xử lý', all: 'Tất cả'}[f] }}
      </button>
    </div>
    <div class="border-l border-sc-border pl-2 ml-1 flex gap-1">
      <button v-for="s in ['all', 'Critical', 'Warning', 'Info']" :key="s"
        @click="severityFilter = s; page = 1; load()"
        class="px-3 py-1.5 rounded-md text-sm transition"
        :class="severityFilter === s ? 'bg-sc-royal text-white' : 'bg-white border border-sc-border hover:bg-sc-bg'">
        {{ s === 'all' ? 'Tất cả mức' : sevLabel(s) }}
      </button>
    </div>
    <div class="border-l border-sc-border pl-2 ml-1 flex items-center gap-2 flex-1 min-w-[200px]">
      <div class="relative flex-1 max-w-sm">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted text-sm"><Icon name="search" :size="14" /></span>
        <input v-model="searchText" placeholder="Tìm theo tiêu đề..."
          class="sc-input pl-8 py-1.5 text-sm" />
      </div>
      <select v-model="sortKey" @change="page = 1; load()" class="sc-input py-1.5 text-sm max-w-[160px]">
        <option value="alert_date">Ngày cảnh báo</option>
        <option value="severity">Mức độ</option>
        <option value="title">Tiêu đề</option>
        <option value="modified">Cập nhật</option>
      </select>
      <button @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'; load()"
        class="sc-btn-secondary text-xs">
        <Icon :name="sortDir === 'asc' ? 'arrow-up' : 'arrow-down'" :size="14" />
      </button>
    </div>
  </div>

  <div v-if="loading" class="text-center py-20 text-sc-text-muted">Đang tải...</div>
  <div v-else-if="alerts.length === 0" class="sc-card p-10 text-center text-sc-text-muted">
    <Icon name="check" :size="16" /> Không có cảnh báo
  </div>
  <div v-else>
  <div class="space-y-3">
    <div v-for="a in alerts" :key="a.name" class="sc-card p-4 hover:shadow-sc-md transition">
      <div class="flex items-start gap-3">
        <div class="flex-shrink-0 mt-1">
          <span :class="['sc-badge', sevCls(a.severity)]">{{ sevLabel(a.severity) }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h4 class="font-semibold text-sc-navy">{{ a.title }}</h4>
            <span v-if="a.escalated" class="sc-badge sc-badge-critical"><Icon name="arrow-up" :size="14" /> ĐÃ ĐẨY LÊN</span>
            <span v-if="a.resolved" class="sc-badge sc-badge-success"><Icon name="check" :size="14" /> Đã xử lý</span>
            <span v-if="a.snooze_until && !a.resolved" class="sc-badge sc-badge-neutral">
              <Icon name="alarm-clock" :size="14" /> Tạm ẩn <Icon name="arrow-right" :size="14" /> {{ fmt(a.snooze_until) }}
            </span>
            <span v-if="a.assigned_to" class="sc-badge sc-badge-info"><Icon name="user" :size="14" /> {{ a.assigned_to }}</span>
          </div>
          <p class="text-sm text-sc-text-muted mt-1">{{ a.message }}</p>
          <div class="flex items-center gap-3 mt-2 text-xs text-sc-text-muted">
            <span><Icon name="calendar" :size="14" /> {{ fmt(a.alert_date) }}</span>
            <button v-if="a.reference_doctype" @click="openRef(a)"
              class="text-sc-royal hover:underline">
              <Icon name="link" :size="14" /> {{ a.reference_doctype }} {{ a.reference_name }}
            </button>
          </div>
        </div>
        <div v-if="!a.resolved" class="flex gap-2 flex-wrap">
          <button @click="openAction(a, 'resolve')" class="sc-btn-primary text-xs"><Icon name="check" :size="14" /> Xử lý</button>
          <button @click="openAction(a, 'snooze')" class="sc-btn-secondary text-xs"><Icon name="alarm-clock" :size="14" /> Tạm ẩn</button>
          <button @click="openAction(a, 'assign')" class="sc-btn-secondary text-xs"><Icon name="user" :size="14" /> Phân công</button>
        </div>
      </div>
    </div>
  </div>
  <div class="sc-card mt-3 overflow-hidden">
    <Pagination :total="total" :page="page" :pageSize="pageSize"
      :loading="loading"
      @update:page="(p) => { page = p; load() }"
      @update:pageSize="(s) => { pageSize = s; page = 1; load() }" />
  </div>
  </div>

  <Modal :open="!!selected && !!actionType"
    :title="selected ? `${{resolve:'Đánh dấu đã xử lý',snooze:'Tạm ẩn',assign:'Phân công'}[actionType]} — ${selected.title}` : ''"
    size="md" @close="closeAction">
    <template v-if="actionType === 'resolve'">
      <FieldInput v-model="actionInput.remarks" label="Ghi chú hành động" type="textarea"
        placeholder="VD: Đã liên hệ NCC, refill stock..." />
    </template>
    <template v-else-if="actionType === 'snooze'">
      <FieldInput v-model="actionInput.hours" label="Số giờ" type="number" required />
      <div class="h-3"></div>
      <FieldInput v-model="actionInput.reason" label="Lý do" type="textarea"
        placeholder="VD: Đang chờ NCC xác nhận" />
    </template>
    <template v-else-if="actionType === 'assign'">
      <FieldInput v-model="actionInput.user" label="Email người phụ trách" required
        placeholder="email@bệnhviện.vn" />
      <div class="h-3"></div>
      <FieldInput v-model="actionInput.remarks" label="Ghi chú (tuỳ chọn)" type="textarea" />
    </template>
    <template #footer>
      <button @click="closeAction" class="sc-btn-secondary text-sm">Hủy</button>
      <button @click="performAction" class="sc-btn-primary text-sm">Xác nhận</button>
    </template>
  </Modal>
</template>
