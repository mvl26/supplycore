<script setup>
import { computed } from 'vue'
import { statusLabel } from '../modules'
import Icon from './Icon.vue'
import { fmtDate, fmtDateTime, fmtVND, fmtNumber } from '../utils'

const props = defineProps({
  rows:    { type: Array, default: () => [] },
  columns: { type: Array, required: true }, // [{key, label, type, format, width, align, sortable}]
  loading: Boolean,
  empty:   { type: String, default: 'Chưa có dữ liệu' },
  rowKey:  { type: String, default: 'name' },
  rowClickable: { type: Boolean, default: true },
  sortKey: { type: String, default: '' },     // current sort column key
  sortDir: { type: String, default: 'desc' }, // 'asc' | 'desc'
  // Chọn dòng — opt-in, mặc định tắt để không đổi hành vi list view khác.
  selectable:    { type: Boolean, default: false },
  selectedKeys:  { type: Array, default: () => [] },
  rowSelectable: { type: Function, default: null }, // (row)=>bool; null = mọi dòng chọn được
})

const emit = defineEmits(['rowClick', 'sort', 'update:selectedKeys'])

// --- Selection helpers (chỉ hoạt động khi selectable) ---
function isRowSelectable(r) {
  return props.selectable && (!props.rowSelectable || props.rowSelectable(r))
}
const selectableRows = computed(() => props.rows.filter(isRowSelectable))
const allSelected = computed(() =>
  selectableRows.value.length > 0 &&
  selectableRows.value.every(r => props.selectedKeys.includes(r[props.rowKey])))
function toggleRow(r) {
  const k = r[props.rowKey]
  const set = new Set(props.selectedKeys)
  set.has(k) ? set.delete(k) : set.add(k)
  emit('update:selectedKeys', [...set])
}
function toggleAll() {
  emit('update:selectedKeys',
    allSelected.value ? [] : selectableRows.value.map(r => r[props.rowKey]))
}

// Rút gọn mã kỹ thuật: "SC-DN-2026-04161" -> "DN-04161" (bỏ tiền tố SC- và năm
// lặp lại cả bảng). Giữ nguyên nếu không khớp khuôn naming-series.
function shortenCode(v) {
  if (!v) return ''
  const m = String(v).match(/^(?:SC-)?([A-Za-z]+)-(\d{4})-(\w+)$/)
  return m ? `${m[1]}-${m[3]}` : String(v)
}

// Nội dung hiển thị của cell thường:
//  - cột có displayKey (hiện TÊN): tên nghiệp vụ; nếu trống -> rút gọn mã làm dự phòng.
//  - cột type='code': mã rút gọn.
//  - còn lại: format thường.
function cellText(r, c) {
  if (c.type === 'code') return shortenCode(r[c.key])
  if (c.displayKey) return r[c.displayKey] || shortenCode(r[c.key])
  return fmt(r[c.displayKey || c.key], c)
}
// Tooltip = mã đầy đủ (để xem/copy) cho cột mã hoặc cột tên có mã nền.
function cellTitle(r, c) {
  if (c.type === 'code') return r[c.key] || ''
  if (c.displayKey) return r[c.key] || ''
  return ''
}

function fmt(value, col) {
  if (value == null) return ''
  if (col.format) return col.format(value)
  if (col.type === 'date' && value) return fmtDate(value)
  if (col.type === 'datetime' && value) return fmtDateTime(value)
  if (col.type === 'currency') return fmtVND(value)
  if (col.type === 'int') return fmtNumber(value)
  return value
}

// Badge (M11): render span thật thay vì v-html.
function badgeCls(value, col) {
  return (col.badgeMap || {})[value] || 'sc-badge-neutral'
}
// QA-BUG-M3-01: truyền col.key để statusLabel pick field-aware label
// (vd qc_status='Pending' → 'Chờ QC' thay vì 'Chờ duyệt')
function badgeText(value, col) {
  return statusLabel(value, col.key) || '—'
}

function onHeaderKey(c, e) {
  e.preventDefault()
  onHeaderClick(c)
}

function onHeaderClick(c) {
  if (!c.sortable) return
  let dir = 'asc'
  if (props.sortKey === c.key) dir = props.sortDir === 'asc' ? 'desc' : 'asc'
  emit('sort', { key: c.key, dir })
}
</script>

<template>
  <div class="sc-card overflow-hidden">
    <!-- Loading skeleton -->
    <div v-if="loading" class="p-4 space-y-2.5">
      <div v-for="n in 6" :key="n" class="sc-skeleton h-9 w-full" :style="{ opacity: 1 - n * 0.12 }" />
    </div>

    <!-- Empty -->
    <div v-else-if="!rows.length" class="py-16 flex flex-col items-center gap-3 text-sc-text-muted">
      <div class="h-12 w-12 rounded-xl bg-sc-bg-soft flex items-center justify-center">
        <Icon name="inbox" :size="24" class="text-sc-text-muted/70" />
      </div>
      <span class="text-sm">{{ empty }}</span>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="sc-table">
        <thead>
          <tr>
            <th v-if="selectable" class="w-10 text-center">
              <input type="checkbox" :checked="allSelected" :disabled="!selectableRows.length"
                @change="toggleAll" @click.stop
                aria-label="Chọn tất cả dòng nháp"
                class="w-4 h-4 cursor-pointer accent-sc-royal align-middle disabled:opacity-40" />
            </th>
            <th v-for="c in columns" :key="c.key"
              :style="c.width ? { width: c.width } : {}"
              :class="[
                c.align === 'right' ? 'text-right' : '',
                c.sortable ? 'cursor-pointer select-none hover:text-sc-navy transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sc-royal/40 rounded' : '',
              ]"
              :tabindex="c.sortable ? 0 : undefined"
              :role="c.sortable ? 'button' : undefined"
              :aria-sort="sortKey === c.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined"
              @click="onHeaderClick(c)"
              @keydown.enter="c.sortable && onHeaderKey(c, $event)"
              @keydown.space="c.sortable && onHeaderKey(c, $event)">
              <span class="inline-flex items-center gap-1"
                :class="c.align === 'right' ? 'flex-row-reverse' : ''">
                {{ c.label }}
                <template v-if="c.sortable">
                  <Icon v-if="sortKey === c.key"
                    :name="sortDir === 'asc' ? 'chevron-up' : 'chevron-down'"
                    :size="13" class="text-sc-royal" />
                  <Icon v-else name="chevrons-up-down" :size="13" class="text-sc-border-strong" />
                </template>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r[rowKey]"
            :class="rowClickable ? 'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-sc-royal/40' : ''"
            :tabindex="rowClickable ? 0 : undefined"
            @click="rowClickable && emit('rowClick', r)"
            @keydown.enter="rowClickable && emit('rowClick', r)">
            <td v-if="selectable" class="text-center" @click.stop>
              <input type="checkbox" :checked="selectedKeys.includes(r[rowKey])"
                :disabled="!isRowSelectable(r)" @change="toggleRow(r)"
                :aria-label="`Chọn ${r[rowKey]}`"
                :title="isRowSelectable(r) ? '' : 'Chỉ chọn được phiếu nháp'"
                class="w-4 h-4 cursor-pointer accent-sc-royal align-middle disabled:opacity-30 disabled:cursor-not-allowed" />
            </td>
            <td v-for="c in columns" :key="c.key"
              :class="[c.align === 'right' ? 'text-right' : '',
                       (c.mono || c.type === 'code') ? 'font-mono text-xs' : '']">
              <template v-if="c.type === 'badge'">
                <span class="sc-badge" :class="badgeCls(r[c.key], c)">{{ badgeText(r[c.key], c) }}</span>
              </template>
              <template v-else-if="c.type === 'check'">
                <Icon v-if="r[c.key]" name="check" :size="16" class="text-sc-success" />
                <span v-else class="text-sc-border-strong">—</span>
              </template>
              <template v-else>
                <span :title="cellTitle(r, c)">{{ cellText(r, c) }}</span>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
