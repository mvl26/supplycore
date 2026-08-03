<script setup>
import { ref, watch, computed } from 'vue'
import { call } from '../api'
import { fmtDate, fmtNumber } from '../utils'
import { qcBadge, qcLabel, expiryClass } from '../utils/status'
import Icon from './Icon.vue'
import Pagination from './Pagination.vue'

const props = defineProps({
  warehouse: String,
  item: { type: String, default: null },
  title: { type: String, default: 'Tồn kho tại kho' },
  // Picker mode: hiện ô tích + nút "Điền vào bảng chi tiết"
  selectable: { type: Boolean, default: false },
})
const emit = defineEmits(['fill'])

const rows = ref([])
const loading = ref(false)
const search = ref('')
const sortField = ref('')      // '' (mặc định) | received_date | expiry_date
const sortDir = ref('asc')
const page = ref(1)
const pageSize = ref(10)
const selected = ref(new Set())

const rowKey = (r) => `${r.item}|${r.batch || ''}|${r.bin_location || ''}`

async function load() {
  if (!props.warehouse) { rows.value = []; return }
  loading.value = true
  try {
    rows.value = await call('supplycore.api.frontend.warehouse_stock_for_item', {
      warehouse: props.warehouse, item: props.item || null,
    })
  } catch (e) {
    rows.value = []
  } finally {
    loading.value = false
  }
  selected.value = new Set()
  page.value = 1
}
watch(() => [props.warehouse, props.item], load, { immediate: true })

// — Filter —
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r =>
    (r.item || '').toLowerCase().includes(q) ||
    (r.item_name || '').toLowerCase().includes(q) ||
    (r.batch || '').toLowerCase().includes(q) ||
    (r.bin_location || '').toLowerCase().includes(q))
})

// — Sort (theo ngày nhập / hạn dùng) —
const sorted = computed(() => {
  if (!sortField.value) return filtered.value
  const f = sortField.value
  const dir = sortDir.value === 'desc' ? -1 : 1
  return [...filtered.value].sort((a, b) => {
    const av = a[f], bv = b[f]
    if (!av && !bv) return 0
    if (!av) return 1            // dòng thiếu ngày → xuống cuối
    if (!bv) return -1
    return av < bv ? -dir : av > bv ? dir : 0
  })
})

// — Paginate —
const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const pageRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sorted.value.slice(start, start + pageSize.value)
})
watch([filtered, pageSize, sortField, sortDir], () => {
  if (page.value > totalPages.value) page.value = totalPages.value
})

// — Selection —
const isSel = (r) => selected.value.has(rowKey(r))
function toggle(r) {
  if (r.blocked) return
  const s = new Set(selected.value)
  const k = rowKey(r)
  s.has(k) ? s.delete(k) : s.add(k)
  selected.value = s
}
const selectablePageRows = computed(() => pageRows.value.filter(r => !r.blocked))
const allPageSelected = computed(() =>
  selectablePageRows.value.length > 0 && selectablePageRows.value.every(r => isSel(r)))
function toggleAllPage() {
  const s = new Set(selected.value)
  if (allPageSelected.value) selectablePageRows.value.forEach(r => s.delete(rowKey(r)))
  else selectablePageRows.value.forEach(r => s.add(rowKey(r)))
  selected.value = s
}

function doFill() {
  const picked = rows.value.filter(r => selected.value.has(rowKey(r)))
  if (!picked.length) return
  emit('fill', picked)
  selected.value = new Set()
}

const isBelowSafety = (r) => r.safety_stock > 0 && r.qty < r.safety_stock
</script>

<template>
  <div v-if="!warehouse" class="sc-card p-4 text-sm text-sc-text-muted">
    Chọn kho để xem tồn
  </div>
  <div v-else class="sc-card overflow-hidden mb-4">
    <!-- Header + nút xác nhận -->
    <div class="flex items-center justify-between gap-3 px-4 py-3 border-b border-sc-border
      bg-sc-bg-soft/60 flex-wrap">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="package" :size="18" /> {{ title }}
        <span class="font-mono text-sm text-sc-text-muted">{{ warehouse }}</span>
      </h3>
      <div class="flex items-center gap-2.5">
        <span class="text-xs text-sc-text-muted">{{ filtered.length }} dòng tồn</span>
        <button v-if="selectable" @click="doFill" :disabled="!selected.size"
          class="sc-btn-primary text-xs">
          <Icon name="check" :size="14" />
          Điền {{ selected.size }} dòng vào chi tiết
        </button>
      </div>
    </div>

    <!-- Toolbar: filter + sắp xếp -->
    <div class="px-4 py-2.5 border-b border-sc-border flex items-center gap-3 flex-wrap">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-sc-text-muted">
          <Icon name="search" :size="15" />
        </span>
        <input v-model="search" placeholder="Lọc mã VT / tên / lô / vị trí..."
          class="sc-input pl-8 py-1.5 text-sm" />
      </div>
      <div class="flex items-center gap-1.5">
        <span class="text-xs text-sc-text-muted whitespace-nowrap">Sắp xếp:</span>
        <select v-model="sortField" class="sc-input py-1.5 text-sm w-auto">
          <option value="">Mặc định (HSD gần nhất)</option>
          <option value="received_date">Ngày nhập</option>
          <option value="expiry_date">Hạn dùng</option>
        </select>
        <button v-if="sortField" type="button"
          @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
          class="sc-icon-btn h-8 w-8"
          :title="sortDir === 'asc' ? 'Tăng dần' : 'Giảm dần'">
          <Icon :name="sortDir === 'asc' ? 'arrow-up' : 'arrow-down'" :size="15" />
        </button>
      </div>
    </div>

    <div v-if="loading" class="p-6 text-center text-sc-text-muted text-sm">Đang tải...</div>
    <div v-else-if="!filtered.length" class="p-6 text-center text-sc-text-muted text-sm">
      {{ rows.length ? 'Không có dòng khớp bộ lọc' : `Kho trống${item ? ` cho vật tư ${item}` : ''}` }}
    </div>

    <template v-else>
      <div class="overflow-x-auto">
        <table class="sc-table text-sm">
          <thead>
            <tr>
              <th v-if="selectable" class="w-10 text-center">
                <input type="checkbox" :checked="allPageSelected" @change="toggleAllPage"
                  class="w-4 h-4 align-middle accent-sc-royal cursor-pointer"
                  title="Chọn tất cả dòng trên trang" />
              </th>
              <th>Mã VT</th>
              <th>Tên</th>
              <th>Lô hệ thống</th>
              <th>Lô NCC</th>
              <th>Vị trí</th>
              <th>KCS</th>
              <th>Ngày nhập</th>
              <th>HD</th>
              <th class="text-right">SL tồn</th>
              <th class="text-right">Tồn an toàn</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in pageRows" :key="rowKey(r)"
              :class="[
                isBelowSafety(r) ? 'bg-sc-warning-50' : '',
                selectable && !r.blocked ? 'cursor-pointer' : '',
                selectable && isSel(r) ? '!bg-sc-royal-50' : '',
              ]"
              @click="selectable && toggle(r)">
              <td v-if="selectable" class="text-center">
                <input type="checkbox" :checked="isSel(r)" :disabled="r.blocked"
                  @click.stop="toggle(r)"
                  class="w-4 h-4 align-middle accent-sc-royal cursor-pointer disabled:opacity-40" />
              </td>
              <td class="font-mono text-xs">{{ r.item }}</td>
              <td>{{ r.item_name || '—' }}</td>
              <td class="font-mono text-xs">{{ r.batch || '—' }}</td>
              <td class="font-mono text-xs">{{ r.supplier_batch_no || '—' }}</td>
              <td>
                <span v-if="r.bin_location" class="font-mono text-xs px-2 py-0.5 bg-sc-bg-soft rounded">
                  {{ r.bin_location }}
                </span>
                <span v-else class="text-xs text-sc-text-muted italic">chưa xếp</span>
              </td>
              <td>
                <span v-if="r.qc_status" :class="['sc-badge', qcBadge(r.qc_status)]">
                  {{ qcLabel(r.qc_status) }}
                </span>
                <span v-if="r.blocked" class="sc-badge sc-badge-critical ml-1">Khoá</span>
              </td>
              <td class="text-xs">{{ r.received_date ? fmtDate(r.received_date) : '—' }}</td>
              <td class="text-xs"><span class="px-1.5 py-0.5 rounded" :class="expiryClass(r.expiry_date)">{{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}</span></td>
              <td class="text-right font-mono font-semibold"
                :class="{ 'text-sc-warning': isBelowSafety(r) }">
                {{ fmtNumber(r.qty) }}
              </td>
              <td class="text-right font-mono text-xs text-sc-text-muted">
                {{ r.safety_stock ? fmtNumber(r.safety_stock) : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <Pagination :total="filtered.length" :page="page" :page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        @update:page="page = $event" @update:page-size="pageSize = $event" />
    </template>
  </div>
</template>
