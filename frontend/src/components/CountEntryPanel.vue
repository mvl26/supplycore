<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { updateDoc, call } from '../api'
import { useToastStore } from '../stores/toast'
import { fmtNumber } from '../utils'
import Icon from './Icon.vue'

const props = defineProps({
  doc: Object,        // SC Inventory Count Sheet
  doctype: String,
})
const emit = defineEmits(['after'])
const toast = useToastStore()

const search = ref('')
const filter = ref('all')   // all | pending | mismatch | recount
const saving = ref(false)
const focusedIdx = ref(-1)

const items = computed(() => props.doc?.items || [])
const threshold = computed(() => Number(props.doc?.recount_threshold_pct || 5))
const hideSys = computed(() => Number(props.doc?.hide_system_qty) === 1)

const stats = computed(() => {
  const total = items.value.length
  let counted = 0, mismatch = 0, recount = 0
  for (const r of items.value) {
    const a = Number(r.actual_qty ?? 0)
    const s = Number(r.system_qty ?? 0)
    if (Number(r.is_counted) === 1) counted++
    if (Number(r.is_counted) === 1 && a !== s) mismatch++
    if (r.needs_recount) recount++
  }
  return { total, counted, mismatch, recount, remaining: total - counted }
})

const progressPct = computed(() => {
  if (!stats.value.total) return 0
  return Math.round((stats.value.counted / stats.value.total) * 100)
})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  let arr = items.value
  if (q) arr = arr.filter(r =>
    String(r.item || '').toLowerCase().includes(q) ||
    String(r.item_name || '').toLowerCase().includes(q) ||
    String(r.batch || '').toLowerCase().includes(q) ||
    String(r.bin_location || '').toLowerCase().includes(q))
  if (filter.value === 'pending') arr = arr.filter(r => Number(r.is_counted) !== 1)
  else if (filter.value === 'mismatch') arr = arr.filter(r => {
    const a = Number(r.actual_qty), s = Number(r.system_qty || 0)
    return Number(r.is_counted) === 1 && a !== s
  })
  else if (filter.value === 'recount') arr = arr.filter(r => r.needs_recount)
  return arr
})

// Variance calculation per row
function variancePct(row) {
  const s = Number(row.system_qty || 0)
  const a = Number(row.actual_qty || 0)
  if (s === 0) return a === 0 ? 0 : 100
  return ((a - s) / s) * 100
}

function rowCls(row) {
  if (Number(row.is_counted) !== 1) return ''
  const v = variancePct(row)
  if (Math.abs(v) > threshold.value) return 'bg-sc-danger-50'
  if (Math.abs(v) > 0) return 'bg-sc-warning-50'
  return 'bg-sc-success-50'
}

async function saveRow(row, key, val) {
  if (props.doc.docstatus !== 0) {
    toast.warning('Phiếu đã submit — không sửa được')
    return
  }
  saving.value = true
  try {
    // Batch update các field tính toán cùng lúc
    const s = Number(row.system_qty || 0)
    const a = key === 'actual_qty' ? Number(val || 0) : Number(row.actual_qty || 0)
    const updates = { [key]: val }
    if (key === 'actual_qty') {
      updates.is_counted = 1
      updates.difference = a - s
      updates.variance_pct = s !== 0 ? ((a - s) / s) * 100 : (a !== 0 ? 100 : 0)
      updates.needs_recount = Math.abs(updates.variance_pct) > threshold.value ? 1 : 0
      updates.variance_value = (a - s) * Number(row.valuation_rate || 0)
    }
    await call('frappe.client.set_value', {
      doctype: 'SC ICS Item',
      name: row.name,
      fieldname: updates,
    })
    Object.assign(row, updates)
  } catch (e) {
    toast.error(`Lỗi lưu: ${e.message}`)
  } finally {
    saving.value = false
  }
}

let saveTimer = null
function onCountInput(row, val) {
  // Debounce save: chờ 500ms sau khi gõ xong
  clearTimeout(saveTimer)
  row.actual_qty = val
  saveTimer = setTimeout(() => saveRow(row, 'actual_qty', val == null || val === '' ? null : Number(val)), 500)
}

function onRecountInput(row, val) {
  clearTimeout(saveTimer)
  row.recount_actual_qty = val
  saveTimer = setTimeout(() => saveRow(row, 'recount_actual_qty', val == null || val === '' ? null : Number(val)), 500)
}

function onKey(e, idx) {
  if (e.key === 'Enter' || (e.key === 'ArrowDown')) {
    e.preventDefault()
    const next = idx + 1
    if (next < filtered.value.length) {
      focusedIdx.value = next
      nextTick(() => {
        const el = document.querySelector(`#count-input-${filtered.value[next].name}`)
        if (el) el.focus()
      })
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const prev = idx - 1
    if (prev >= 0) {
      focusedIdx.value = prev
      nextTick(() => {
        const el = document.querySelector(`#count-input-${filtered.value[prev].name}`)
        if (el) el.focus()
      })
    }
  }
}

function reloadDoc() {
  emit('after')
}
</script>

<template>
  <div v-if="doc && doc.docstatus === 0 && items.length"
    class="sc-card p-5 mb-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="clipboard-list" :size="20" /> Bảng nhập đếm
        <span class="text-xs text-sc-text-muted ml-2">
          (Enter/↓ chuyển dòng · Tự lưu sau 500ms)
        </span>
      </h3>
      <div class="flex items-center gap-2 text-sm">
        <span v-if="saving" class="text-sc-warning text-xs inline-flex items-center gap-1"><Icon name="save" :size="14" /> Đang lưu...</span>
        <button @click="reloadDoc" class="sc-btn-secondary text-xs inline-flex items-center gap-1"><Icon name="rotate-cw" :size="14" /> Reload</button>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="mb-3">
      <div class="flex items-center justify-between text-xs mb-1">
        <span>
          Đã đếm <strong class="font-mono">{{ stats.counted }}/{{ stats.total }}</strong>
          ({{ progressPct }}%)
        </span>
        <span class="text-sc-text-muted">
          Lệch: <strong class="text-sc-warning">{{ stats.mismatch }}</strong>
          · Cần đếm lại: <strong class="text-sc-danger">{{ stats.recount }}</strong>
          · Còn: <strong>{{ stats.remaining }}</strong>
        </span>
      </div>
      <div class="h-2 bg-sc-border rounded-full overflow-hidden">
        <div class="h-full bg-sc-success transition-all"
          :style="{ width: progressPct + '%' }"></div>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <div class="relative flex-1 min-w-[200px] max-w-sm">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted"><Icon name="search" :size="15" /></span>
        <input v-model="search" class="sc-input pl-8 py-1 text-sm"
          placeholder="Tìm mã/tên/lô/vị trí..." />
      </div>
      <button v-for="f in [
          {k:'all',l:'Tất cả',c:stats.total},
          {k:'pending',l:'Chưa đếm',c:stats.remaining},
          {k:'mismatch',l:'Lệch',c:stats.mismatch},
          {k:'recount',l:'Đếm lại',c:stats.recount}]"
        :key="f.k" @click="filter = f.k"
        class="px-3 py-1.5 rounded-md text-xs font-medium transition"
        :class="filter === f.k ? 'bg-sc-navy text-white' : 'bg-sc-bg hover:bg-sc-border'">
        {{ f.l }} <span class="ml-1 font-mono">({{ f.c }})</span>
      </button>
    </div>

    <!-- Count entry table -->
    <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
      <table class="sc-table text-xs">
        <thead class="sticky top-0 bg-white z-10">
          <tr>
            <th class="w-10">#</th>
            <th>Mã VT</th>
            <th>Tên</th>
            <th>Lô</th>
            <th>Vị trí</th>
            <th v-if="!hideSys" class="text-right">SL HT</th>
            <th class="text-right">SL đếm</th>
            <th class="text-right">% lệch</th>
            <th>Cờ</th>
            <th class="text-right">SL đếm L2</th>
            <th class="text-right">SL đếm L3</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in filtered" :key="r.name"
            :class="rowCls(r)">
            <td class="text-sc-text-muted font-mono">{{ idx + 1 }}</td>
            <td class="font-mono">{{ r.item }}</td>
            <td>{{ r.item_name }}</td>
            <td class="font-mono">{{ r.batch || '—' }}</td>
            <td class="font-mono text-xs">{{ r.bin_location || '—' }}</td>
            <td v-if="!hideSys" class="text-right font-mono">{{ fmtNumber(r.system_qty) }}</td>
            <td class="text-right">
              <input :id="`count-input-${r.name}`"
                type="number" step="any" inputmode="decimal"
                :value="r.actual_qty"
                @input="e => onCountInput(r, e.target.value)"
                @keydown="e => onKey(e, idx)"
                class="w-24 text-right font-mono px-2 py-1 border rounded focus:border-sc-royal focus:outline-none focus:ring-2 focus:ring-sc-royal/30"
                placeholder="—" />
            </td>
            <td class="text-right font-mono"
              :class="Math.abs(variancePct(r)) > threshold ? 'text-sc-danger font-bold' : (Math.abs(variancePct(r)) > 0 ? 'text-sc-warning' : 'text-sc-text-muted')">
              {{ Number(r.is_counted) === 1 ? variancePct(r).toFixed(1) + '%' : '—' }}
            </td>
            <td>
              <span v-if="r.needs_recount" class="sc-badge sc-badge-warning text-xs">Đếm lại</span>
              <span v-else-if="Number(r.is_counted) === 1 && Number(r.actual_qty) === Number(r.system_qty || 0)"
                class="text-sc-success"><Icon name="check" :size="14" /></span>
            </td>
            <td class="text-right">
              <input v-if="r.needs_recount"
                type="number" step="any"
                :value="r.recount_actual_qty"
                @input="e => onRecountInput(r, e.target.value)"
                class="w-20 text-right font-mono px-1 py-0.5 border rounded text-xs"
                placeholder="—" />
              <span v-else class="text-sc-text-muted">—</span>
            </td>
            <td class="text-right">
              <span v-if="r.third_count_qty != null">{{ r.third_count_qty }}</span>
              <span v-else class="text-sc-text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!filtered.length" class="text-center py-6 text-sc-text-muted text-sm">
      Không có item nào khớp bộ lọc
    </div>

    <div class="mt-3 text-xs text-sc-text-muted">
      <Icon name="info" :size="14" /> Mẹo: Bấm <kbd class="px-1 py-0.5 bg-sc-bg-soft rounded">Enter</kbd> hoặc <kbd class="px-1 py-0.5 bg-sc-bg-soft rounded">↓</kbd> để chuyển ô tiếp theo · <kbd class="px-1 py-0.5 bg-sc-bg-soft rounded">↑</kbd> quay lại.
      Ngưỡng đếm lại: <strong>{{ threshold }}%</strong>. Item có |% lệch| > ngưỡng sẽ tự bật cờ "Đếm lại".
    </div>
  </div>
</template>
