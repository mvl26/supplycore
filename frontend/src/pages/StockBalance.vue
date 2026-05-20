<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import { useToastStore } from '../stores/toast'
import { fmtNumber, fmtShort, fmtVND, fmtDate } from '../utils'

const router = useRouter()
const toast = useToastStore()
const loading = ref(false)
const rows = ref([])

const filters = ref({ item: '', warehouse: '', batch: '' })
const itemSuggestions = ref([])
const whSuggestions = ref([])

const sortKey = ref('item')
const sortDir = ref('asc')
const page = ref(1)
const pageSize = ref(20)

async function load() {
  loading.value = true
  page.value = 1
  try {
    rows.value = await call('supplycore.api.frontend.stock_balance', {
      item: filters.value.item || null,
      warehouse: filters.value.warehouse || null,
      batch: filters.value.batch || null,
    })
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Load filter suggestions
  itemSuggestions.value = await getList('SC Item',
    { fields: ['name', 'item_name'], filters: { is_stock_item: 1, disabled: 0 }, limit: 200 })
    .catch(() => [])
  whSuggestions.value = await getList('SC Warehouse',
    { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 100 })
    .catch(() => [])
  load()
})

const totals = computed(() => {
  const totalQty = rows.value.reduce((s, r) => s + (r.qty || 0), 0)
  const totalValue = rows.value.reduce((s, r) => s + (r.value || 0), 0)
  const distinctItems = new Set(rows.value.map(r => r.item)).size
  const distinctBatches = new Set(rows.value.map(r => r.batch).filter(Boolean)).size
  return { totalQty, totalValue, distinctItems, distinctBatches }
})

const sortedRows = computed(() => {
  const arr = [...rows.value]
  const k = sortKey.value, d = sortDir.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const va = a[k], vb = b[k]
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * d
    return String(va).localeCompare(String(vb), 'vi') * d
  })
  return arr
})

const totalRows = computed(() => sortedRows.value.length)
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

function setSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'asc' }
  page.value = 1
}
function sortIcon(key) {
  if (sortKey.value !== key) return '⇅'
  return sortDir.value === 'asc' ? '▲' : '▼'
}

function openBatch(b) {
  if (b) router.push(`/doc/SC%20Batch/${encodeURIComponent(b)}`)
}
function openItem(i) {
  if (i) router.push(`/doc/SC%20Item/${encodeURIComponent(i)}`)
}

const isExpiringSoon = (date) => {
  if (!date) return false
  const days = (new Date(date) - new Date()) / (1000 * 60 * 60 * 24)
  return days < 30 && days >= 0
}
const isExpired = (date) => date && new Date(date) < new Date()
const qcLabel = (s) => ({
  Accepted: 'Đạt', Rejected: 'Không đạt', Conditional: 'Có điều kiện',
}[s] || s)
</script>

<template>
  <PageHeader title="Tồn kho hiện tại" icon="📊" code="Tồn kho"
    :subtitle="`${rows.length} bản ghi · ${totals.distinctItems} vật tư · ${totals.distinctBatches} lô`">
    <template #actions>
      <button @click="load" class="sc-btn-secondary text-sm">↻ Tải lại</button>
    </template>
  </PageHeader>

  <!-- Filters -->
  <div class="sc-card p-4 mb-4">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Vật tư</label>
        <select v-model="filters.item" @change="load" class="sc-input">
          <option value="">— Tất cả vật tư —</option>
          <option v-for="i in itemSuggestions" :key="i.name" :value="i.name">
            {{ i.name }} {{ i.item_name ? `· ${i.item_name}` : '' }}
          </option>
        </select>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Kho</label>
        <select v-model="filters.warehouse" @change="load" class="sc-input">
          <option value="">— Tất cả kho —</option>
          <option v-for="w in whSuggestions" :key="w.name" :value="w.name">{{ w.name }}</option>
        </select>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Lô</label>
        <input v-model="filters.batch" @keyup.enter="load"
          class="sc-input" placeholder="Nhập mã lô (Enter để tìm)" />
      </div>
    </div>
  </div>

  <!-- KPI summary -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
    <div class="sc-card p-4">
      <div class="text-xs text-sc-text-muted">Tổng số lượng tồn</div>
      <div class="text-2xl font-bold font-mono text-sc-navy mt-1">{{ fmtNumber(totals.totalQty) }}</div>
    </div>
    <div class="sc-card p-4">
      <div class="text-xs text-sc-text-muted">Tổng giá trị</div>
      <div class="text-2xl font-bold font-mono text-sc-navy mt-1">{{ fmtShort(totals.totalValue) }} VND</div>
    </div>
    <div class="sc-card p-4">
      <div class="text-xs text-sc-text-muted">Số vật tư</div>
      <div class="text-2xl font-bold font-mono text-sc-navy mt-1">{{ totals.distinctItems }}</div>
    </div>
    <div class="sc-card p-4">
      <div class="text-xs text-sc-text-muted">Số lô</div>
      <div class="text-2xl font-bold font-mono text-sc-navy mt-1">{{ totals.distinctBatches }}</div>
    </div>
  </div>

  <!-- Data table -->
  <div class="sc-card overflow-hidden">
    <div v-if="loading" class="p-10 text-center text-sc-text-muted">Đang tải...</div>
    <div v-else-if="!rows.length" class="p-10 text-center text-sc-text-muted">
      Không có tồn kho khớp với bộ lọc
    </div>
    <div v-else class="overflow-x-auto">
      <table class="sc-table">
        <thead>
          <tr>
            <th @click="setSort('item')" class="cursor-pointer select-none hover:bg-sc-bg">
              Mã VT <span class="text-xs text-sc-royal">{{ sortIcon('item') }}</span>
            </th>
            <th @click="setSort('item_name')" class="cursor-pointer select-none hover:bg-sc-bg">
              Tên <span class="text-xs text-sc-royal">{{ sortIcon('item_name') }}</span>
            </th>
            <th @click="setSort('warehouse')" class="cursor-pointer select-none hover:bg-sc-bg">
              Kho <span class="text-xs text-sc-royal">{{ sortIcon('warehouse') }}</span>
            </th>
            <th @click="setSort('batch')" class="cursor-pointer select-none hover:bg-sc-bg">
              Lô <span class="text-xs text-sc-royal">{{ sortIcon('batch') }}</span>
            </th>
            <th @click="setSort('qc_status')" class="cursor-pointer select-none hover:bg-sc-bg">
              KCS <span class="text-xs text-sc-royal">{{ sortIcon('qc_status') }}</span>
            </th>
            <th @click="setSort('expiry_date')" class="cursor-pointer select-none hover:bg-sc-bg">
              HD <span class="text-xs text-sc-royal">{{ sortIcon('expiry_date') }}</span>
            </th>
            <th @click="setSort('qty')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
              SL tồn <span class="text-xs text-sc-royal">{{ sortIcon('qty') }}</span>
            </th>
            <th @click="setSort('value')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
              Giá trị (VND) <span class="text-xs text-sc-royal">{{ sortIcon('value') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in pagedRows" :key="idx"
            class="cursor-pointer"
            :class="{ 'bg-red-50': isExpired(r.expiry_date), 'bg-amber-50': isExpiringSoon(r.expiry_date) && !isExpired(r.expiry_date) }">
            <td class="font-mono text-xs" @click="openItem(r.item)">{{ r.item }}</td>
            <td>{{ r.item_name || '—' }}</td>
            <td>{{ r.warehouse }}</td>
            <td class="font-mono text-xs" @click="openBatch(r.batch)">{{ r.batch || '—' }}</td>
            <td>
              <span v-if="r.qc_status" :class="['sc-badge', r.qc_status === 'Accepted' ? 'sc-badge-success' : r.qc_status === 'Rejected' ? 'sc-badge-critical' : 'sc-badge-warning']">
                {{ qcLabel(r.qc_status) }}
              </span>
              <span v-if="r.blocked" class="sc-badge sc-badge-critical ml-1">Khoá</span>
            </td>
            <td>
              <span :class="{ 'text-sc-danger font-semibold': isExpired(r.expiry_date),
                              'text-sc-warning font-medium': isExpiringSoon(r.expiry_date) && !isExpired(r.expiry_date) }">
                {{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}
              </span>
            </td>
            <td class="text-right font-mono font-semibold">{{ fmtNumber(r.qty) }}</td>
            <td class="text-right font-mono">{{ fmtShort(r.value) }}</td>
          </tr>
        </tbody>
      </table>
      <Pagination :total="totalRows" :page="page" :pageSize="pageSize"
        :loading="loading"
        @update:page="page = $event"
        @update:pageSize="(s) => { pageSize = s; page = 1 }" />
    </div>
  </div>
</template>
