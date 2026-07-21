<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getList, count, deleteDoc, VOUCHER_IO_DOCTYPES as VIO_LIST } from '../api'
import { DT, isSubmittable } from '../modules'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import DataTable from '../components/DataTable.vue'
import FieldInput from '../components/FieldInput.vue'
import Pagination from '../components/Pagination.vue'
import ListImportExport from '../components/ListImportExport.vue'
import VoucherIO from '../components/VoucherIO.vue'
import Confirm from '../components/Confirm.vue'

// Doctype hỗ trợ xuất/nhập Excel 2 sheet (phiếu cha-con) — khớp voucher_io.CONFIGS
const VOUCHER_IO_DOCTYPES = new Set(VIO_LIST)
import { useAccessStore } from '../stores/access'
import { useToastStore } from '../stores/toast'

const access = useAccessStore()

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const doctype = computed(() => decodeURIComponent(route.params.dt))
const cfg = computed(() => DT[doctype.value])

// Columns sortable mặc định (server-side qua order_by SQL), TRỪ cột không có nghĩa
// sắp xếp: badge (trạng thái), check (boolean), code (mã rút gọn hiển thị).
const NO_SORT_TYPES = new Set(['badge', 'check', 'code'])
const columns = computed(() => {
  if (!cfg.value) return []
  return cfg.value.listColumns.map(c => ({
    ...c,
    sortable: c.sortable !== false && !NO_SORT_TYPES.has(c.type),
  }))
})

// === State ===
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const loadError = ref(null)
const search = ref('')
const page = ref(1)
const pageSize = ref(20)
const sortKey = ref('')
const sortDir = ref('desc')
const showFilters = ref(false)
const columnFilters = ref({})  // { fieldName: 'value' }

// === Xóa phiếu nháp hàng loạt (chỉ doctype submittable + có quyền delete) ===
const confirmRef = ref(null)
const selectedKeys = ref([])
const deleting = ref(false)
const bulkDeletable = computed(() =>
  !!cfg.value && isSubmittable(doctype.value) && access.canDoctype(doctype.value, 'delete'))
const rowIsDraft = (r) => (r.docstatus ?? 0) === 0
// Đảm bảo docstatus có trong data để gate checkbox từng dòng.
const fetchFields = computed(() => {
  const f = [...(cfg.value?.listFields || [])]
  if (!f.includes('docstatus')) f.push('docstatus')
  return f
})

const PAGE_SIZES = [10, 20, 50, 100]

// Trường ngày mặc định cho mỗi DocType (fallback 'modified')
const DATE_FIELD_BY_DT = {
  'SC Material Request': 'transaction_date',
  'SC Purchase Order': 'transaction_date',
  'SC Purchase Receipt': 'posting_date',
  'SC Stock Entry': 'posting_date',
  'SC Quality Inspection': 'inspection_date',
  'SC Alert': 'alert_date',
  'SC Framework Contract': 'valid_from',
  'SC Delivery Request': 'posting_date',
  'SC Physical Count': 'count_date',
  'SC Inventory Count Sheet': 'count_date',
  'SC Stock Reconciliation': 'posting_date',
  'SC Recall': 'recall_date',
}
const dateField = computed(() =>
  DATE_FIELD_BY_DT[doctype.value] || 'modified')

const sortOptions = computed(() => {
  const df = dateField.value
  return [
    { value: `${df}|desc`, label: `Mới nhất (${df === 'modified' ? 'cập nhật' : 'ngày'})` },
    { value: `${df}|asc`,  label: `Cũ nhất` },
    { value: 'name|asc',   label: 'Mã/Tên A → Z' },
    { value: 'name|desc',  label: 'Mã/Tên Z → A' },
    { value: 'creation|desc', label: 'Tạo mới nhất' },
    { value: 'creation|asc',  label: 'Tạo cũ nhất' },
  ]
})

const currentSortVal = computed({
  get: () => sortKey.value ? `${sortKey.value}|${sortDir.value}` : '',
  set: (v) => {
    const [k, d] = (v || '').split('|')
    sortKey.value = k || ''
    sortDir.value = d === 'asc' ? 'asc' : 'desc'
    page.value = 1
    loadAndSync()
  },
})

// === Build filters ===
function isDateCol(key) {
  const c = columns.value.find(c => c.key === key)
  return c && (c.type === 'date' || c.type === 'datetime')
}

// Cặp date columns merge thành 1 filter dải ngày (period overlap)
const dateRangePairs = computed(() => cfg.value?.dateRangePairs || [])
const pairedColKeys = computed(() => {
  const s = new Set()
  for (const p of dateRangePairs.value) { s.add(p.start); s.add(p.end) }
  return s
})
const pairKey = (p) => `__range__${p.start}__${p.end}`

function hasFilterValue(v) {
  if (v == null || v === '') return false
  if (typeof v === 'object') return !!(v.from || v.to)
  return true
}

// Các field text để ô tìm kiếm quét: mã (name) + mọi cột hiện TÊN (displayKey)
// + cột tên/số hợp đồng trực tiếp. Chỉ lấy field có trong listFields (query được).
// L3: gõ tên KH hay mã đầy đủ đều ra kết quả.
const searchFields = computed(() => {
  const lf = new Set(cfg.value?.listFields || [])
  const out = new Set(['name'])
  for (const c of (cfg.value?.listColumns || [])) {
    if (c.displayKey && lf.has(c.displayKey)) out.add(c.displayKey)
    if (/_name$/.test(c.key) && lf.has(c.key)) out.add(c.key)
    if (c.key === 'contract_number' && lf.has(c.key)) out.add(c.key)
  }
  return [...out]
})

// Tìm kiếm dạng OR trên các field text (tách khỏi buildFilters vì filters là AND).
function buildSearchOr() {
  if (!search.value) return []
  const q = `%${search.value}%`
  return searchFields.value.map(f => [f, 'like', q])
}

function buildFilters() {
  const filters = []
  for (const [k, v] of Object.entries(columnFilters.value)) {
    if (!hasFilterValue(v)) continue
    // Pair: __range__startField__endField → overlap với period [v.from, v.to]
    if (k.startsWith('__range__')) {
      const [, , startF, endF] = k.split('__')
      if (!startF || !endF) continue
      // Overlap: start <= picked.to AND end >= picked.from
      if (v.to)   filters.push([startF, '<=', v.to])
      if (v.from) filters.push([endF,   '>=', v.from])
      continue
    }
    const col = columns.value.find(c => c.key === k)
    if (typeof v === 'object') {
      // Date range cho 1 cột đơn: {from, to}
      if (v.from) filters.push([k, '>=', v.from])
      if (v.to)   filters.push([k, '<=', v.to])
    } else if (col && col.type === 'check') {
      filters.push([k, '=', Number(v)])
    } else {
      filters.push([k, 'like', `%${v}%`])
    }
  }
  return filters
}

// Đếm số filter cột đang active
function activeFilterCount() {
  return Object.values(columnFilters.value).filter(hasFilterValue).length
}

// Init filter slot khi mở "Lọc cột" lần đầu — đảm bảo date col có object {from, to}
function ensureFilterSlot(key) {
  if (columnFilters.value[key] !== undefined) return
  columnFilters.value[key] = isDateCol(key) ? { from: '', to: '' } : ''
}

function buildOrderBy() {
  if (sortKey.value) return `${sortKey.value} ${sortDir.value}`
  return cfg.value?.defaultOrderBy || 'modified desc'
}

// === Load ===
async function load() {
  if (!cfg.value) return
  loading.value = true
  loadError.value = null
  selectedKeys.value = []   // đổi trang/lọc/doctype → bỏ chọn cũ
  try {
    const filters = buildFilters()
    const orFilters = buildSearchOr()
    const start = (page.value - 1) * pageSize.value
    const [data, cnt] = await Promise.all([
      getList(doctype.value, {
        fields: fetchFields.value,
        filters,
        or_filters: orFilters,
        order_by: buildOrderBy(),
        limit: pageSize.value,
        start,
      }),
      count(doctype.value, filters, orFilters).catch(() => 0),
    ])
    rows.value = data
    total.value = cnt
    // Nếu page hiện tại lớn hơn tổng số trang (do filter đổi) → quay về trang cuối hợp lệ
    const maxPage = Math.max(1, Math.ceil(cnt / pageSize.value))
    if (page.value > maxPage) {
      page.value = maxPage
      const startFix = (page.value - 1) * pageSize.value
      rows.value = await getList(doctype.value, {
        fields: fetchFields.value,
        filters,
        or_filters: orFilters,
        order_by: buildOrderBy(),
        limit: pageSize.value,
        start: startFix,
      })
    }
  } catch (e) {
    loadError.value = e.message || String(e)
    toast.error(`Lỗi tải: ${loadError.value}`)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// === URL sync (giữ trạng thái khi reload) ===
function syncToRoute() {
  const q = { ...route.query }
  q.page = page.value > 1 ? String(page.value) : undefined
  q.size = pageSize.value !== 20 ? String(pageSize.value) : undefined
  q.q = search.value || undefined
  q.sort = currentSortVal.value || undefined
  // Chỉ persist filter có giá trị
  const cleanFlt = {}
  for (const [k, v] of Object.entries(columnFilters.value)) {
    if (hasFilterValue(v)) cleanFlt[k] = v
  }
  q.flt = Object.keys(cleanFlt).length ? JSON.stringify(cleanFlt) : undefined
  // Loại bỏ key undefined
  Object.keys(q).forEach(k => q[k] === undefined && delete q[k])
  router.replace({ query: q }).catch(() => {})
}

function loadAndSync() {
  syncToRoute()
  load()
}

function loadFromRoute() {
  const q = route.query
  page.value = Number(q.page) || 1
  pageSize.value = PAGE_SIZES.includes(Number(q.size)) ? Number(q.size) : 20
  search.value = q.q || ''
  if (q.sort) {
    const [k, d] = String(q.sort).split('|')
    sortKey.value = k || ''
    sortDir.value = d === 'asc' ? 'asc' : 'desc'
  } else {
    sortKey.value = ''
    sortDir.value = 'desc'
  }
  try {
    columnFilters.value = q.flt ? JSON.parse(q.flt) : {}
  } catch (e) { columnFilters.value = {} }
  showFilters.value = activeFilterCount() > 0
}

// === Watchers ===
let suppressWatch = false
watch(doctype, () => {
  suppressWatch = true
  loadFromRoute()
  load()
  // Cho phép watcher chạy lại ở next tick
  setTimeout(() => { suppressWatch = false }, 0)
})

// Debounce search (FieldInput chỉ emit update:modelValue → watch ref)
let searchTimer = null
watch(search, () => {
  if (suppressWatch) return
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadAndSync()
  }, 300)
})

// Debounce column filter inputs
let filterTimer = null
function onFilterInput() {
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    page.value = 1
    loadAndSync()
  }, 300)
}

// === Sort qua click column header ===
function onSort({ key, dir }) {
  sortKey.value = key
  sortDir.value = dir
  page.value = 1
  loadAndSync()
}

// === Pagination handlers ===
function onPageChange(p) { page.value = p; loadAndSync() }
function onPageSizeChange(s) { pageSize.value = s; page.value = 1; loadAndSync() }

// === Filter row toggle ===
function toggleFilters() {
  showFilters.value = !showFilters.value
  if (!showFilters.value) {
    columnFilters.value = {}
    page.value = 1
    loadAndSync()
  }
}

function clearAll() {
  search.value = ''
  columnFilters.value = {}
  sortKey.value = ''
  sortDir.value = 'desc'
  page.value = 1
  loadAndSync()
}

// === Navigation ===
function openRow(r) {
  router.push(`/doc/${encodeURIComponent(doctype.value)}/${encodeURIComponent(r.name)}`)
}
function newDoc() {
  router.push(`/doc/${encodeURIComponent(doctype.value)}/new`)
}

// Xóa hàng loạt các phiếu nháp đã chọn. Backend guard vẫn chặn nếu lọt phiếu ≠ nháp.
async function doBulkDelete() {
  const keys = [...selectedKeys.value]
  if (!keys.length) return
  if (!await confirmRef.value.ask({
    title: 'Xóa phiếu nháp',
    message: `Xóa vĩnh viễn ${keys.length} phiếu nháp đã chọn? Không thể hoàn tác.`,
    confirmText: `Xóa ${keys.length} phiếu`, variant: 'danger',
  })) return
  deleting.value = true
  let ok = 0; const fails = []
  try {
    for (const k of keys) {
      try { await deleteDoc(doctype.value, k); ok++ }
      catch (e) { fails.push(k) }
    }
  } finally {
    deleting.value = false
  }
  if (ok) toast.success(`Đã xóa ${ok} phiếu`)
  if (fails.length) toast.error(`${fails.length} phiếu không xóa được (đã gửi/đã hủy hoặc thiếu quyền)`)
  await load()
}

onMounted(() => {
  suppressWatch = true
  loadFromRoute()
  load()
  setTimeout(() => { suppressWatch = false }, 0)
})
</script>

<template>
  <div v-if="!cfg" class="sc-card p-10 text-center text-sc-text-muted">
    DocType không tồn tại
  </div>
  <div v-else>
    <PageHeader :title="cfg.label" :icon="cfg.icon" :code="doctype"
      :subtitle="`${total.toLocaleString('vi-VN')} bản ghi${search || activeFilterCount() ? ' (đã lọc)' : ''}`">
      <template #actions>
        <button @click="load" class="sc-btn-secondary text-sm" title="Tải lại"><Icon name="rotate-cw" :size="14" /></button>
        <VoucherIO v-if="VOUCHER_IO_DOCTYPES.has(doctype)"
          :doctype="doctype" :label="cfg.label"
          :filters="buildFilters()" :order-by="buildOrderBy()"
          :can-import="access.canDoctype(doctype, 'create')"
          @imported="load" />
        <ListImportExport v-else :doctype="doctype" :list-columns="columns"
          :filters="buildFilters()" :order-by="buildOrderBy()"
          :can-import="access.canDoctype(doctype, 'create')"
          @imported="load" />
        <button v-if="access.canDoctype(doctype, 'create')"
          @click="newDoc" class="sc-btn-primary text-sm"><Icon name="plus" :size="14" /> Tạo mới</button>
      </template>
    </PageHeader>

    <!-- Toolbar: search + sort + filter toggle + page size -->
    <div class="sc-card p-3 mb-4 flex flex-wrap items-center gap-3">
      <FieldInput v-model="search" placeholder="Tìm theo mã/tên..."
        prefix-icon="search"
        class="flex-1 min-w-[200px] max-w-md"
        @keyup.enter="loadAndSync" />

      <div class="flex items-center gap-1 text-sm">
        <label class="text-sc-text-muted">Sắp xếp:</label>
        <select v-model="currentSortVal" class="sc-input py-1 px-2 text-sm">
          <option value="">— Mặc định —</option>
          <option v-for="o in sortOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </div>

      <button @click="toggleFilters" class="sc-btn-secondary text-sm"
        :class="showFilters ? '!bg-sc-navy !text-white' : ''"
        title="Bật/tắt bộ lọc theo cột">
        <Icon name="filter" :size="14" /> Lọc cột
        <span v-if="activeFilterCount()" class="ml-1 text-xs">
          ({{ activeFilterCount() }})
        </span>
      </button>

      <button v-if="search || activeFilterCount() || sortKey"
        @click="clearAll" class="text-xs text-sc-text-muted hover:text-sc-danger underline">
        <Icon name="x" :size="14" /> Xoá lọc
      </button>
    </div>

    <!-- Column filter row -->
    <div v-if="showFilters" class="sc-card p-3 mb-4">
      <div class="text-xs text-sc-text-muted mb-2">
        Lọc theo cột — cặp ngày Từ/Đến gộp thành 1 dải lọc khoảng giữa:
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        <!-- Pair date range: 2 picker, filter overlap với khoảng giữa -->
        <div v-for="p in dateRangePairs" :key="pairKey(p)" class="flex flex-col col-span-2">
          <label class="text-xs text-sc-text-muted mb-0.5">
            {{ p.label }} <span class="italic">(dải lọc giữa)</span>
          </label>
          <div class="flex items-center gap-1">
            <input type="date"
              :value="(columnFilters[pairKey(p)] && columnFilters[pairKey(p)].from) || ''"
              @change="e => {
                const k = pairKey(p);
                const cur = typeof columnFilters[k] === 'object' ? columnFilters[k] : {};
                columnFilters[k] = { from: e.target.value, to: cur.to || '' };
                onFilterInput();
              }"
              class="sc-input py-1 text-xs flex-1" title="Từ ngày" />
            <span class="text-sc-text-muted text-xs"><Icon name="arrow-right" :size="14" /></span>
            <input type="date"
              :value="(columnFilters[pairKey(p)] && columnFilters[pairKey(p)].to) || ''"
              @change="e => {
                const k = pairKey(p);
                const cur = typeof columnFilters[k] === 'object' ? columnFilters[k] : {};
                columnFilters[k] = { from: cur.from || '', to: e.target.value };
                onFilterInput();
              }"
              class="sc-input py-1 text-xs flex-1" title="Đến ngày" />
          </div>
        </div>

        <template v-for="c in columns" :key="c.key">
          <div v-if="!pairedColKeys.has(c.key)" class="flex flex-col">
            <label class="text-xs text-sc-text-muted mb-0.5">{{ c.label }}</label>
            <!-- Cột date/datetime đơn lẻ: 2 input chọn ngày (từ / đến) -->
            <template v-if="c.type === 'date' || c.type === 'datetime'">
              <div class="flex items-center gap-1">
                <input type="date"
                  :value="(columnFilters[c.key] && columnFilters[c.key].from) || ''"
                  @change="e => {
                    const cur = typeof columnFilters[c.key] === 'object' ? columnFilters[c.key] : {};
                    columnFilters[c.key] = { from: e.target.value, to: cur.to || '' };
                    onFilterInput();
                  }"
                  class="sc-input py-1 text-xs flex-1" title="Từ ngày" />
                <span class="text-sc-text-muted text-xs"><Icon name="arrow-right" :size="14" /></span>
                <input type="date"
                  :value="(columnFilters[c.key] && columnFilters[c.key].to) || ''"
                  @change="e => {
                    const cur = typeof columnFilters[c.key] === 'object' ? columnFilters[c.key] : {};
                    columnFilters[c.key] = { from: cur.from || '', to: e.target.value };
                    onFilterInput();
                  }"
                  class="sc-input py-1 text-xs flex-1" title="Đến ngày" />
              </div>
            </template>
            <!-- Cột check (boolean): dropdown 3 trạng thái -->
            <template v-else-if="c.type === 'check'">
              <select
                :value="columnFilters[c.key] ?? ''"
                @change="e => { columnFilters[c.key] = e.target.value; onFilterInput() }"
                class="sc-input py-1 text-sm">
                <option value="">— Tất cả —</option>
                <option value="1">Có</option>
                <option value="0">Không</option>
              </select>
            </template>
            <!-- Còn lại: text contains -->
            <template v-else>
              <input v-model="columnFilters[c.key]" @input="onFilterInput"
                class="sc-input py-1 text-sm" :placeholder="`Lọc ${c.label.toLowerCase()}...`" />
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- Lỗi tải (khác với "không có dữ liệu") -->
    <div v-if="loadError && !loading" class="sc-card p-8 text-center">
      <Icon name="alert-triangle" :size="36" class="mx-auto text-sc-danger mb-3" />
      <div class="font-semibold text-sc-text mb-1">Lỗi tải dữ liệu</div>
      <div class="text-sm text-sc-text-muted mb-4 break-all">{{ loadError }}</div>
      <button class="sc-btn-secondary text-sm mx-auto" @click="load">
        <Icon name="refresh-cw" :size="15" /> Thử lại
      </button>
    </div>

    <template v-else>
      <!-- Thanh xóa hàng loạt — chỉ hiện khi có phiếu nháp được chọn -->
      <div v-if="bulkDeletable && selectedKeys.length"
        class="sc-card px-4 py-2.5 mb-2 flex items-center gap-3 border-sc-danger/40 bg-sc-danger/5">
        <span class="text-sm font-medium text-sc-text">Đã chọn {{ selectedKeys.length }} phiếu nháp</span>
        <button @click="doBulkDelete" :disabled="deleting"
          class="bg-sc-danger hover:brightness-110 text-white px-3 py-1.5 rounded-md font-medium text-sm disabled:opacity-60">
          <Icon name="trash-2" :size="14" />
          {{ deleting ? 'Đang xóa...' : `Xóa ${selectedKeys.length} phiếu` }}
        </button>
        <button @click="selectedKeys = []" class="sc-btn-secondary text-sm">Bỏ chọn</button>
      </div>

      <DataTable :rows="rows" :columns="columns" :loading="loading"
        empty="Chưa có bản ghi nào"
        :sortKey="sortKey" :sortDir="sortDir"
        :selectable="bulkDeletable"
        :selectedKeys="selectedKeys"
        :rowSelectable="rowIsDraft"
        @update:selectedKeys="selectedKeys = $event"
        @rowClick="openRow" @sort="onSort" />
    </template>

    <div v-if="!loadError" class="mt-1">
      <Pagination :total="total" :page="page" :pageSize="pageSize"
        :pageSizes="PAGE_SIZES" :loading="loading"
        @update:page="onPageChange" @update:pageSize="onPageSizeChange" />
    </div>

    <Confirm ref="confirmRef" />
  </div>
</template>
