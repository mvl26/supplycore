<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import { useToastStore } from '../stores/toast'
import { fmtNumber, fmtShort } from '../utils'

const router = useRouter()
const toast = useToastStore()
const rows = ref([])
const loading = ref(false)

const search = ref('')
const filterType = ref('')
const sortKey = ref('name')
const sortDir = ref('asc')
const page = ref(1)
const pageSize = ref(20)

async function load() {
  loading.value = true
  try {
    rows.value = await call('supplycore.api.frontend.warehouse_summary')
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

onMounted(load)

const warehouseTypes = computed(() => {
  const set = new Set(rows.value.map(r => r.warehouse_type).filter(Boolean))
  return [...set].sort()
})

const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter(r => {
    if (filterType.value && r.warehouse_type !== filterType.value) return false
    if (q && !String(r.name).toLowerCase().includes(q)) return false
    return true
  })
})

const sortedRows = computed(() => {
  const arr = [...filteredRows.value]
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

const total = computed(() => sortedRows.value.length)
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sortedRows.value.slice(start, start + pageSize.value)
})

const totals = computed(() => ({
  qty: sortedRows.value.reduce((s, r) => s + (r.total_qty || 0), 0),
  value: sortedRows.value.reduce((s, r) => s + (r.total_value || 0), 0),
}))

function setSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'asc' }
  page.value = 1
}

function sortIcon(key) {
  if (sortKey.value !== key) return '⇅'
  return sortDir.value === 'asc' ? '▲' : '▼'
}

function clearFilters() {
  search.value = ''; filterType.value = ''
  page.value = 1
}

function openWarehouse(name) {
  router.push(`/doc/SC%20Warehouse/${encodeURIComponent(name)}`)
}
function openStockBalance(wh) {
  router.push(`/stock-balance?warehouse=${encodeURIComponent(wh)}`)
}
function newWarehouse() {
  router.push('/doc/SC%20Warehouse/new')
}
</script>

<template>
  <PageHeader title="Kho — Tồn kho hiện tại" icon="🏬"
    code="SC Warehouse" :subtitle="`${total.toLocaleString('vi-VN')} kho${search || filterType ? ' (đã lọc)' : ''}`">
    <template #actions>
      <button @click="load" class="sc-btn-secondary text-sm">↻</button>
      <button @click="newWarehouse" class="sc-btn-primary text-sm">+ Tạo kho</button>
    </template>
  </PageHeader>

  <!-- Toolbar -->
  <div class="sc-card p-3 mb-4 flex flex-wrap items-center gap-3">
    <div class="relative flex-1 min-w-[200px] max-w-md">
      <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted text-sm">🔍</span>
      <input v-model="search" @input="page = 1"
        placeholder="Tìm theo tên kho..."
        class="sc-input pl-8" />
    </div>
    <select v-model="filterType" @change="page = 1" class="sc-input max-w-[180px]">
      <option value="">— Tất cả loại kho —</option>
      <option v-for="t in warehouseTypes" :key="t" :value="t">{{ t }}</option>
    </select>
    <select v-model="sortKey" @change="page = 1" class="sc-input max-w-[180px]">
      <option value="name">🔤 Sắp xếp: Tên kho</option>
      <option value="total_qty">🔢 Sắp xếp: SL tồn</option>
      <option value="distinct_items">📦 Sắp xếp: Số items</option>
      <option value="total_value">💰 Sắp xếp: Giá trị</option>
    </select>
    <button @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
      class="sc-btn-secondary text-sm" :title="sortDir === 'asc' ? 'Tăng dần' : 'Giảm dần'">
      {{ sortDir === 'asc' ? '▲ Tăng' : '▼ Giảm' }}
    </button>
    <button v-if="search || filterType" @click="clearFilters"
      class="text-xs text-sc-text-muted hover:text-sc-danger underline">✕ Xoá lọc</button>
  </div>

  <div v-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải...</div>
  <div v-else-if="!total" class="sc-card p-10 text-center text-sc-text-muted">
    Không có kho khớp với bộ lọc
  </div>
  <div v-else class="sc-card overflow-hidden">
    <table class="sc-table">
      <thead>
        <tr>
          <th @click="setSort('name')" class="cursor-pointer select-none hover:bg-sc-bg">
            Tên kho <span class="text-xs text-sc-royal">{{ sortIcon('name') }}</span>
          </th>
          <th @click="setSort('warehouse_type')" class="cursor-pointer select-none hover:bg-sc-bg">
            Loại <span class="text-xs text-sc-royal">{{ sortIcon('warehouse_type') }}</span>
          </th>
          <th @click="setSort('total_qty')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
            Tổng SL tồn <span class="text-xs text-sc-royal">{{ sortIcon('total_qty') }}</span>
          </th>
          <th @click="setSort('distinct_items')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
            Số items <span class="text-xs text-sc-royal">{{ sortIcon('distinct_items') }}</span>
          </th>
          <th @click="setSort('total_value')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
            Giá trị tồn (VND) <span class="text-xs text-sc-royal">{{ sortIcon('total_value') }}</span>
          </th>
          <th class="w-32"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in pagedRows" :key="r.name" class="hover:bg-sc-bg">
          <td class="cursor-pointer font-medium text-sc-navy" @click="openWarehouse(r.name)">
            {{ r.name }}
          </td>
          <td>
            <span v-if="r.warehouse_type" class="sc-badge sc-badge-neutral">{{ r.warehouse_type }}</span>
          </td>
          <td class="text-right font-mono">{{ fmtNumber(r.total_qty) }}</td>
          <td class="text-right font-mono">{{ r.distinct_items || 0 }}</td>
          <td class="text-right font-mono font-semibold">{{ fmtShort(r.total_value) }}</td>
          <td>
            <button @click="openStockBalance(r.name)"
              class="text-xs text-sc-royal hover:underline">
              Chi tiết →
            </button>
          </td>
        </tr>
      </tbody>
      <tfoot class="bg-sc-bg font-semibold border-t-2 border-sc-border">
        <tr>
          <td colspan="2">Tổng cộng ({{ total }} kho)</td>
          <td class="text-right font-mono">{{ fmtNumber(totals.qty) }}</td>
          <td></td>
          <td class="text-right font-mono">{{ fmtShort(totals.value) }}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
    <Pagination :total="total" :page="page" :pageSize="pageSize"
      :loading="loading"
      @update:page="page = $event"
      @update:pageSize="(s) => { pageSize = s; page = 1 }" />
  </div>
</template>
