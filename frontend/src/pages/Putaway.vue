<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { call, getList } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import Icon from '../components/Icon.vue'
import { useToastStore } from '../stores/toast'
import { fmtDate, fmtNumber } from '../utils'
import { qcBadge, qcLabel, expiryClass } from '../utils/status'

const router = useRouter()
const route = useRoute()
const toast = useToastStore()

const warehouses = ref([])
const filterWh = ref('')
const items = ref([])
const bins = ref([])
const loading = ref(false)
const saving = ref(false)
const searchText = ref('')
const sortKey = ref('posting_date')
const sortDir = ref('desc')
const page = ref(1)
const pageSize = ref(20)

// Map: sle_name → bin_location
const assignments = ref({})

async function loadWarehouses() {
  warehouses.value = await getList('SC Warehouse', {
    fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 100,
  })
}

async function loadBins() {
  // Luôn load tất cả bins (kèm warehouse) để mỗi row có thể chọn vị trí
  // thuộc đúng kho của row đó, kể cả khi filterWh để trống.
  bins.value = await call('supplycore.api.frontend.bins_for_warehouse', {})
}

const binsByWh = computed(() => {
  const m = {}
  for (const b of bins.value) {
    if (!m[b.warehouse]) m[b.warehouse] = []
    m[b.warehouse].push(b)
  }
  return m
})

async function loadPending() {
  loading.value = true
  try {
    items.value = await call('supplycore.api.frontend.pending_putaway', {
      warehouse: filterWh.value || null, limit: 100,
    })
    // Reset assignments
    assignments.value = {}
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

watch(filterWh, () => {
  loadPending()
})

onMounted(async () => {
  await Promise.all([loadWarehouses(), loadBins()])
  // Auto-select warehouse từ query param (vd: PR submit → ?warehouse=Kho X)
  const qWh = route.query.warehouse
  if (qWh && warehouses.value.some(w => w.name === qWh)) {
    filterWh.value = qWh
  }
  await loadPending()
})

const selectedCount = computed(() =>
  Object.values(assignments.value).filter(v => v).length)

const filteredItems = computed(() => {
  const q = searchText.value.trim().toLowerCase()
  if (!q) return items.value
  return items.value.filter(r =>
    String(r.voucher_no || '').toLowerCase().includes(q) ||
    String(r.item || '').toLowerCase().includes(q) ||
    String(r.item_name || '').toLowerCase().includes(q) ||
    String(r.batch || '').toLowerCase().includes(q))
})

const sortedItems = computed(() => {
  const arr = [...filteredItems.value]
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

const totalItems = computed(() => sortedItems.value.length)
const pagedItems = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sortedItems.value.slice(start, start + pageSize.value)
})

function setSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'asc' }
  page.value = 1
}
function sortIcon(key) {
  if (sortKey.value !== key) return 'chevrons-up-down'
  return sortDir.value === 'asc' ? 'chevron-up' : 'chevron-down'
}

async function saveAll() {
  const pairs = Object.entries(assignments.value)
    .filter(([k, v]) => v)
    .map(([sle_name, bin_location]) => ({ sle_name, bin_location }))
  if (!pairs.length) {
    toast.warning('Chưa chọn bin nào')
    return
  }
  saving.value = true
  try {
    const result = await call('supplycore.api.frontend.assign_bin',
      { assignments: pairs })
    toast.success(`Đã xếp ${result.updated} dòng lên kệ`)
    await loadPending()
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <PageHeader title="Phiếu xếp hàng lên kệ" icon="package"
    code="Gán vị trí"
    :subtitle="`${items.length} dòng chờ xếp${filterWh ? ` tại ${filterWh}` : ''}`">
    <template #actions>
      <button @click="loadPending" class="sc-btn-secondary text-sm">
        <Icon name="rotate-cw" :size="14" /> Tải lại
      </button>
      <button @click="saveAll" :disabled="saving || selectedCount === 0"
        class="sc-btn-primary text-sm disabled:opacity-50">
        <Icon name="save" :size="14" /> Lưu {{ selectedCount }} dòng
      </button>
    </template>
  </PageHeader>

  <div class="sc-card p-4 mb-4 flex flex-wrap items-end gap-3">
    <div class="flex-1 min-w-[180px] max-w-md">
      <label class="text-xs text-sc-text-muted block mb-1">Lọc theo kho</label>
      <select v-model="filterWh" class="sc-input">
        <option value="">— Tất cả kho —</option>
        <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
      </select>
    </div>
    <div class="flex-1 min-w-[200px] max-w-sm">
      <label class="text-xs text-sc-text-muted block mb-1">Tìm trong DS</label>
      <div class="relative">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted">
          <Icon name="search" :size="14" />
        </span>
        <input v-model="searchText" @input="page = 1"
          class="sc-input pl-8" placeholder="Mã chứng từ / VT / lô..." />
      </div>
    </div>
    <div>
      <label class="text-xs text-sc-text-muted block mb-1">Sắp xếp</label>
      <div class="flex gap-1">
        <select v-model="sortKey" @change="page = 1" class="sc-input">
          <option value="posting_date">Ngày</option>
          <option value="voucher_no">Chứng từ</option>
          <option value="item">Mã VT</option>
          <option value="expiry_date">Hạn dùng</option>
          <option value="qty">SL</option>
        </select>
        <button @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
          class="sc-btn-secondary text-sm">
          <Icon :name="sortDir === 'asc' ? 'chevron-up' : 'chevron-down'" :size="14" />
        </button>
      </div>
    </div>
  </div>

  <div v-if="loading" class="sc-card p-4 space-y-2.5"><div v-for="n in 6" :key="n" class="sc-skeleton h-9 w-full" :style="{ opacity: 1 - n * 0.12 }" /></div>
  <div v-else-if="!items.length" class="sc-card p-10 text-center text-sc-text-muted">
    <Icon name="check" :size="16" /> Không có hàng chờ xếp lên kệ
    <div class="text-xs mt-1">(Hàng vừa nhận qua PR/SE chưa được gán vị trí)</div>
  </div>
  <div v-else class="sc-card overflow-x-auto">
    <table class="sc-table">
      <thead>
        <tr>
          <th @click="setSort('voucher_no')" class="cursor-pointer select-none hover:bg-sc-bg">
            Chứng từ <span class="text-xs text-sc-royal"><Icon :name="sortIcon('voucher_no')" :size="12" /></span>
          </th>
          <th @click="setSort('posting_date')" class="cursor-pointer select-none hover:bg-sc-bg">
            Ngày <span class="text-xs text-sc-royal"><Icon :name="sortIcon('posting_date')" :size="12" /></span>
          </th>
          <th @click="setSort('item')" class="cursor-pointer select-none hover:bg-sc-bg">
            Mã VT <span class="text-xs text-sc-royal"><Icon :name="sortIcon('item')" :size="12" /></span>
          </th>
          <th @click="setSort('item_name')" class="cursor-pointer select-none hover:bg-sc-bg">
            Tên SP <span class="text-xs text-sc-royal"><Icon :name="sortIcon('item_name')" :size="12" /></span>
          </th>
          <th @click="setSort('warehouse')" class="cursor-pointer select-none hover:bg-sc-bg">
            Kho <span class="text-xs text-sc-royal"><Icon :name="sortIcon('warehouse')" :size="12" /></span>
          </th>
          <th @click="setSort('batch')" class="cursor-pointer select-none hover:bg-sc-bg">
            Lô <span class="text-xs text-sc-royal"><Icon :name="sortIcon('batch')" :size="12" /></span>
          </th>
          <th @click="setSort('expiry_date')" class="cursor-pointer select-none hover:bg-sc-bg">
            HD <span class="text-xs text-sc-royal"><Icon :name="sortIcon('expiry_date')" :size="12" /></span>
          </th>
          <th>KCS</th>
          <th @click="setSort('qty')" class="text-right cursor-pointer select-none hover:bg-sc-bg">
            SL <span class="text-xs text-sc-royal"><Icon :name="sortIcon('qty')" :size="12" /></span>
          </th>
          <th class="w-48"><Icon name="map-pin" :size="14" /> Chọn vị trí</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in pagedItems" :key="r.sle_name">
          <td>
            <span class="font-mono text-xs text-sc-royal">{{ r.voucher_no }}</span>
            <div class="text-xs text-sc-text-muted">{{ r.voucher_type.replace('SC ', '') }}</div>
          </td>
          <td class="text-xs">{{ fmtDate(r.posting_date) }}</td>
          <td class="font-mono text-xs">{{ r.item }}</td>
          <td class="text-sm">{{ r.item_name || '—' }}</td>
          <td class="text-xs">{{ r.warehouse }}</td>
          <td class="font-mono text-xs">{{ r.batch || '—' }}</td>
          <td class="text-xs"><span class="px-1.5 py-0.5 rounded" :class="expiryClass(r.expiry_date)">{{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}</span></td>
          <td>
            <span v-if="r.qc_status" :class="['sc-badge', qcBadge(r.qc_status)]">
              {{ qcLabel(r.qc_status) }}
            </span>
          </td>
          <td class="text-right font-mono font-semibold">{{ fmtNumber(r.qty) }}</td>
          <td>
            <select v-if="(binsByWh[r.warehouse] || []).length"
              v-model="assignments[r.sle_name]" class="sc-input py-1 text-xs">
              <option value="">— Chọn vị trí —</option>
              <option v-for="b in binsByWh[r.warehouse] || []"
                :key="b.name" :value="b.name">
                {{ b.bin_code || b.name }}
              </option>
            </select>
            <span v-else class="text-xs text-sc-text-muted italic">
              Kho chưa khai vị trí
            </span>
          </td>
        </tr>
      </tbody>
    </table>
    <Pagination :total="totalItems" :page="page" :pageSize="pageSize"
      :loading="loading"
      @update:page="page = $event"
      @update:pageSize="(s) => { pageSize = s; page = 1 }" />
  </div>
</template>
