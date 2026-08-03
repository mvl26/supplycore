<script setup>
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import FormField from './FormField.vue'
import Icon from './Icon.vue'
import Modal from './Modal.vue'
import LineItemDetailDrawer from './LineItemDetailDrawer.vue'
import DocPreviewDrawer from './DocPreviewDrawer.vue'
import { call, voucherIo, downloadFile, fileToBase64, VOUCHER_IO_DOCTYPES } from '../api'
import { useToastStore } from '../stores/toast'
import { fmtVND } from '../utils'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  schema: { type: Object, required: true },  // { field, label, columns }
  readonly: Boolean,
  parentDoc: { type: Object, default: () => ({}) },  // doc cha — để kế thừa giá trị header
  doctype: { type: String, default: '' },            // doctype cha — để Import/Export lưới (CR-02)
  lockCols: Boolean,   // khoá các cột đánh dấu `lockable` (vd đơn bán theo HĐ khung)
})

// Cột read-only động: cột tĩnh (col.readonly) HOẶC cột lockable khi đang khoá
function colReadonly(c) {
  return props.readonly || !!c.readonly || (!!c.lockable && props.lockCols)
}
const emit = defineEmits(['update:modelValue', 'createNew'])
const toast = useToastStore()

const rows = computed(() => props.modelValue || [])

// CR-02: chỉ bật Tải mẫu/Import/Export khi doctype được hỗ trợ
const ioEnabled = computed(() => !props.readonly && VOUCHER_IO_DOCTYPES.includes(props.doctype))

// Tổng cộng cột Currency có compute (vd FC: total_amount)
const totals = computed(() => {
  const out = {}
  for (const col of props.schema.columns || []) {
    if (col.type !== 'Currency') continue
    out[col.name] = rows.value.reduce((s, r) => s + Number(r[col.name] || 0), 0)
  }
  return out
})

const grandTotal = computed(() => {
  // Ưu tiên cột có compute (vd total_amount); fallback: cột Currency cuối cùng
  const cols = props.schema.columns || []
  const computed_col = cols.find(c => c.type === 'Currency' && c.compute)
  if (computed_col) return totals.value[computed_col.name] || 0
  return null
})

function newRow() {
  const r = {}
  for (const c of props.schema.columns) {
    if (c.default !== undefined) r[c.name] = c.default
    // L09/T13: kế thừa giá trị header khi thêm dòng (vd Ngày cần dòng = Ngày cần chung), vẫn cho sửa
    if (c.inheritFrom && props.parentDoc && props.parentDoc[c.inheritFrom] != null && props.parentDoc[c.inheritFrom] !== '') {
      r[c.name] = props.parentDoc[c.inheritFrom]
    }
  }
  emit('update:modelValue', [...rows.value, r])
}

function removeRow(idx) {
  const arr = [...rows.value]
  arr.splice(idx, 1)
  emit('update:modelValue', arr)
}

function applyBulk(action) {
  if (!rows.value.length) return
  const set = action.set || {}
  const arr = rows.value.map(r => ({ ...r, ...set }))
  emit('update:modelValue', arr)
}

const variantClass = (v) => ({
  success: 'bg-sc-success hover:brightness-110 text-white',
  danger:  'bg-sc-danger hover:brightness-110 text-white',
  primary: 'sc-btn-primary',
}[v] || 'sc-btn-secondary')

function updateCell(idx, name, value) {
  const arr = rows.value.map((r, i) => i === idx ? { ...r, [name]: value } : r)
  // Compute fields trên cùng dòng: col.compute = {from: [a, b], op: 'mul'}
  const row = arr[idx]
  for (const col of props.schema.columns) {
    if (!col.compute) continue
    const { from, op } = col.compute
    if (!from?.includes(name)) continue
    const vals = from.map(k => Number(row[k] || 0))
    let v = 0
    if (op === 'mul') v = vals.reduce((a, b) => a * b, 1)
    else if (op === 'add') v = vals.reduce((a, b) => a + b, 0)
    else if (op === 'sub') v = vals[0] - vals.slice(1).reduce((a, b) => a + b, 0)
    row[col.name] = v
  }
  emit('update:modelValue', arr)
  // Trigger row-level auto-fetch nếu schema khai báo autoFetch.on chứa field này
  const af = props.schema.autoFetch
  if (af && af.api && af.on?.includes(name)) {
    if (af.on.every(k => row[k])) runAutoFetch(idx, row, af)
  }
}

async function runAutoFetch(idx, row, af) {
  const params = {}
  for (const k of af.on) params[k] = row[k]
  try {
    const res = await call(af.api, params)
    if (!res || typeof res !== 'object') return
    const updates = {}
    for (const [k, v] of Object.entries(res)) {
      // Bỏ qua key không phải column hợp lệ
      if (!props.schema.columns.some(c => c.name === k)) continue
      if (v != null && v !== '') updates[k] = v
    }
    if (Object.keys(updates).length) {
      const arr2 = rows.value.map((r, i) => i === idx ? { ...r, ...updates } : r)
      emit('update:modelValue', arr2)
    }
  } catch (e) {}
}

// ---- Row detail drawer (Yêu cầu 1) --------------------------------------
const drawerIdx = ref(null)
// Groups cho drawer: dùng schema.detail.groups nếu có; nếu không → 1 section từ columns
// (giữ drawer DÙNG CHUNG cho mọi bảng con, kể cả chưa khai detail).
const drawerGroups = computed(() =>
  props.schema.detail?.groups || [{ title: 'Chi tiết dòng', fields: props.schema.columns || [] }]
)
// Cột định danh vật tư (đặt icon mapping cạnh) — schema.itemField hoặc cột Link 'SC Item' đầu.
const itemField = computed(() =>
  props.schema.itemField || (props.schema.columns.find(c => c.linkTo === 'SC Item')?.name) || null
)
const hasTrace = (r) => !!(r && r.supplier_item_name)

function openDrawer(idx) { drawerIdx.value = idx }
function closeDrawer() { drawerIdx.value = null }
function applyDrawer(newRow) {
  if (drawerIdx.value == null) return
  const arr = rows.value.map((r, i) => i === drawerIdx.value ? { ...r, ...newRow } : r)
  emit('update:modelValue', arr)
}
function navigateDrawer(dir) {
  const next = (drawerIdx.value ?? 0) + dir
  if (next >= 0 && next < rows.value.length) drawerIdx.value = next
}
// Click dòng mở drawer — TRỪ khi click trực tiếp vào input/dropdown/nút.
function onRowClick(idx, e) {
  if (e.target.closest('input, select, textarea, button, a, [role="button"], .sc-input, .link-autocomplete')) return
  openDrawer(idx)
}

// ---- Cuộn ngang + ghim cột (Yêu cầu 3) ----------------------------------
const scrollEl = ref(null)
const atStart = ref(true)
const atEnd = ref(true)
function onScroll() {
  const el = scrollEl.value
  if (!el) return
  atStart.value = el.scrollLeft <= 1
  atEnd.value = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1
}
watch(rows, () => nextTick(onScroll))
onMounted(() => nextTick(onScroll))

// Auto-fetch related field after Link change
async function handleLinkSelected(idx, col, linkedDoc) {
  // Some cols have fetchFrom: when source field set, fetch target_field from target_doctype
  const updates = {}
  for (const otherCol of props.schema.columns) {
    if (otherCol.fetchFrom && otherCol.fetchFrom.source === col.name && linkedDoc?.name) {
      try {
        const d = await call('frappe.client.get_value', {
          doctype: otherCol.fetchFrom.target_doctype,
          filters: { name: linkedDoc.name },
          fieldname: otherCol.fetchFrom.target_field,
        })
        const v = d?.[otherCol.fetchFrom.target_field]
        if (v != null) updates[otherCol.name] = v
      } catch (e) {}
    }
  }
  if (Object.keys(updates).length) {
    const arr = rows.value.map((r, i) => i === idx ? { ...r, ...updates } : r)
    emit('update:modelValue', arr)
  }
}

// ===== CR-02: Tải mẫu / Import / Export ngay tại lưới =====
const ioBusy = ref(false)
const importOpen = ref(false)
const importFile = ref(null)
const importFileType = ref('xlsx')
const parseResult = ref(null)
const loadMode = ref('append')   // 'append' | 'replace'

// ===== Chọn từ danh sách (picker) — vd chọn hóa đơn công nợ NCC để thanh toán =====
// Cấu hình qua schema.picker: { api, filterField, filterArg, rowKey, columns[],
//   map{targetCol: sourceKey}, previewDoctype, previewKey, buttonLabel, title, emptyHint }
const pickerCfg = computed(() => props.schema.picker || null)
const pickerReady = computed(() =>
  !props.readonly && !!pickerCfg.value && !!props.parentDoc?.[pickerCfg.value.filterField])
const pickerOpen = ref(false)
const pickerLoading = ref(false)
const pickerRows = ref([])
const pickerSel = ref(new Set())
const pickerPreview = ref({ open: false, name: '' })

// key đã có trong lưới (theo cột đích được map từ rowKey) → chặn chọn trùng
const pickerTargetCol = computed(() => {
  const cfg = pickerCfg.value; if (!cfg) return null
  return Object.keys(cfg.map).find(tc => cfg.map[tc] === cfg.rowKey) || null
})
const pickerExisting = computed(() => {
  const tc = pickerTargetCol.value
  if (!tc) return new Set()
  return new Set((rows.value || []).map(r => r[tc]).filter(Boolean))
})

async function openPicker() {
  const cfg = pickerCfg.value
  if (!cfg) return
  if (!pickerReady.value) { toast.error(cfg.emptyHint || 'Chưa đủ điều kiện để nạp danh sách'); return }
  pickerOpen.value = true
  pickerLoading.value = true
  pickerRows.value = []
  pickerSel.value = new Set()
  try {
    const arg = cfg.filterArg || cfg.filterField
    const res = await call(cfg.api, { [arg]: props.parentDoc[cfg.filterField] })
    pickerRows.value = Array.isArray(res) ? res : (res?.message || [])
    if (!pickerRows.value.length) toast.push(cfg.emptyResult || 'Không có hóa đơn còn nợ cho NCC này', 'info')
  } catch (e) {
    toast.error(`Nạp danh sách lỗi: ${e.message}`)
  } finally {
    pickerLoading.value = false
  }
}

function togglePick(row) {
  const k = row[pickerCfg.value.rowKey]
  if (pickerExisting.value.has(k)) return   // đã có trong lưới → khóa
  const s = new Set(pickerSel.value)
  s.has(k) ? s.delete(k) : s.add(k)
  pickerSel.value = s
}

function addPicked() {
  const cfg = pickerCfg.value; if (!cfg) return
  const added = []
  for (const src of pickerRows.value) {
    if (!pickerSel.value.has(src[cfg.rowKey])) continue
    if (pickerExisting.value.has(src[cfg.rowKey])) continue
    const nr = baseRow()
    for (const [targetCol, srcKey] of Object.entries(cfg.map)) nr[targetCol] = src[srcKey]
    added.push(nr)
  }
  if (added.length) emit('update:modelValue', [...rows.value, ...added])
  toast.success(`Đã thêm ${added.length} dòng`)
  pickerOpen.value = false
}

function openPickerPreview(row) {
  pickerPreview.value = { open: true, name: row[pickerCfg.value.previewKey || pickerCfg.value.rowKey] }
}

// Dòng cơ sở: default + kế thừa header (giống newRow) để dòng nhập đồng nhất
function baseRow() {
  const r = {}
  for (const c of props.schema.columns) {
    if (c.default !== undefined) r[c.name] = c.default
    if (c.inheritFrom && props.parentDoc?.[c.inheritFrom] != null && props.parentDoc[c.inheritFrom] !== '')
      r[c.name] = props.parentDoc[c.inheritFrom]
  }
  return r
}

// Tính cột compute (vd Thành tiền = SL × Đơn giá) cho 1 dòng
function computeRow(r) {
  const row = { ...r }
  for (const col of props.schema.columns) {
    if (!col.compute) continue
    const { from, op } = col.compute
    const vals = (from || []).map(k => Number(row[k] || 0))
    if (op === 'mul') row[col.name] = vals.reduce((a, b) => a * b, 1)
    else if (op === 'add') row[col.name] = vals.reduce((a, b) => a + b, 0)
    else if (op === 'sub') row[col.name] = vals[0] - vals.slice(1).reduce((a, b) => a + b, 0)
  }
  return row
}

async function downloadGridTemplate(ft) {
  ioBusy.value = true
  try {
    const file = await voucherIo.childTemplate(props.doctype, { file_type: ft })
    downloadFile(file)
    toast.success('Đã tải file mẫu danh mục vật tư')
  } catch (e) {
    toast.error(`Tải mẫu lỗi: ${e.message}`)
  } finally {
    ioBusy.value = false
  }
}

function exportGrid() {
  const cols = props.schema.columns || []
  const esc = (v) => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s
  }
  const lines = [
    cols.map(c => esc(c.label)).join(','),   // dòng 1 = nhãn
    cols.map(c => esc(c.name)).join(','),     // dòng 2 = fieldname
    ...rows.value.map(r => cols.map(c => esc(r[c.name])).join(',')),
  ]
  const text = '﻿' + lines.join('\n')
  const b64 = btoa(unescape(encodeURIComponent(text)))
  downloadFile({ filename: `${(props.doctype || 'items').replace(/\s+/g, '_')}_luoi.csv`,
                 content_b64: b64, content_type: 'text/csv; charset=utf-8' })
  toast.success(`Đã xuất ${rows.value.length} dòng`)
}

function openImport() {
  importOpen.value = true
  importFile.value = null
  parseResult.value = null
}
function onImportFile(ev) {
  const f = ev.target.files?.[0]
  if (!f) { importFile.value = null; return }
  importFile.value = f
  importFileType.value = f.name.toLowerCase().endsWith('.csv') ? 'csv' : 'xlsx'
  parseResult.value = null
}
async function runParse() {
  if (!importFile.value) return
  ioBusy.value = true
  parseResult.value = null
  try {
    const content_b64 = await fileToBase64(importFile.value)
    parseResult.value = await voucherIo.parseChild(props.doctype, { content_b64, file_type: importFileType.value })
    const r = parseResult.value
    if (r.error_count) toast.warning(`${r.ok_count} dòng hợp lệ · ${r.error_count} dòng lỗi`)
    else toast.success(`${r.ok_count} dòng hợp lệ, sẵn sàng nạp`)
  } catch (e) {
    toast.error(`Đọc file lỗi: ${e.message}`)
  } finally {
    ioBusy.value = false
  }
}
function loadIntoGrid() {
  const ok = parseResult.value?.rows_ok || []
  if (!ok.length) return
  const newRows = ok.map(o => computeRow({ ...baseRow(), ...o }))
  const merged = loadMode.value === 'replace' ? newRows : [...rows.value, ...newRows]
  emit('update:modelValue', merged)
  toast.success(`Đã nạp ${newRows.length} dòng vào lưới${loadMode.value === 'replace' ? ' (thay thế)' : ''}`)
  importOpen.value = false
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-2 gap-2 flex-wrap">
      <h4 class="font-medium text-sc-navy text-sm">{{ schema.label }} ({{ rows.length }})</h4>
      <div v-if="!readonly" class="flex items-center gap-2 flex-wrap">
        <button v-for="(act, i) in (schema.bulkActions || [])" :key="i"
          @click="applyBulk(act)" type="button"
          :disabled="!rows.length"
          :class="['text-xs px-3 py-1 rounded-md font-medium disabled:opacity-40', variantClass(act.variant)]">
          {{ act.label }}
        </button>
        <template v-if="ioEnabled">
          <button @click="downloadGridTemplate('xlsx')" :disabled="ioBusy" type="button"
            class="sc-btn-secondary text-xs" title="Tải file mẫu danh mục vật tư">
            <Icon name="download" :size="13" /> Tải mẫu
          </button>
          <button @click="openImport" :disabled="ioBusy" type="button"
            class="sc-btn-secondary text-xs" title="Nhập danh mục từ Excel/CSV">
            <Icon name="download" :size="13" /> Import
          </button>
          <button @click="exportGrid" :disabled="!rows.length" type="button"
            class="sc-btn-secondary text-xs" title="Xuất danh mục đang có ra CSV">
            <Icon name="upload" :size="13" /> Export
          </button>
        </template>
        <button v-if="pickerCfg" @click="openPicker" type="button"
          class="sc-btn-secondary text-xs" :disabled="!pickerReady"
          :title="pickerReady ? '' : (pickerCfg.emptyHint || '')">
          <Icon name="clipboard-list" :size="13" /> {{ pickerCfg.buttonLabel || 'Chọn từ danh sách' }}
        </button>
        <button v-if="!lockCols" @click="newRow" type="button" class="sc-btn-secondary text-xs">
          + Thêm dòng
        </button>
      </div>
    </div>

    <div v-if="rows.length === 0" class="border border-dashed border-sc-border rounded-md p-6 text-center text-sm text-sc-text-muted">
      Chưa có dòng nào — click "+ Thêm dòng" để bắt đầu
    </div>

    <div v-else ref="scrollEl" @scroll="onScroll" class="overflow-x-auto">
      <table class="w-full text-sm min-w-[720px]">
        <thead>
          <tr class="bg-sc-bg text-sc-text-muted text-xs uppercase">
            <th class="sticky left-0 z-[3] bg-sc-bg px-2 py-1.5 text-left w-10"
              :class="{ 'sc-sticky-shadow-r': !atStart && !itemField }"></th>
            <th v-for="c in schema.columns" :key="c.name"
              :style="c.width ? { width: c.width } : {}"
              class="px-2 py-1.5 text-left"
              :class="[c.name === itemField ? 'sticky left-10 z-[3] bg-sc-bg' : '',
                       c.name === itemField && !atStart ? 'sc-sticky-shadow-r' : '']">
              {{ c.label }}
              <span v-if="c.required" class="text-sc-danger">*</span>
            </th>
            <th v-if="!readonly" class="sticky right-0 z-[3] bg-sc-bg w-10"
              :class="{ 'sc-sticky-shadow-l': !atEnd }"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in rows" :key="idx"
            class="border-b border-sc-border hover:bg-sc-royal-50/25 cursor-pointer transition-colors"
            @click="onRowClick(idx, $event)">
            <td class="sticky left-0 z-[2] bg-sc-surface px-2 py-1 align-top pt-2.5 w-10"
              :class="{ 'sc-sticky-shadow-r': !atStart && !itemField }"
              @click.stop="openDrawer(idx)" title="Xem chi tiết dòng">
              <div class="flex items-center gap-0.5 text-sc-text-muted text-xs cursor-pointer hover:text-sc-royal">
                <Icon name="chevron-right" :size="12" class="opacity-60" />{{ idx + 1 }}
              </div>
            </td>
            <td v-for="c in schema.columns" :key="c.name" class="px-2 py-1 align-top relative"
              :class="[c.name === itemField ? 'sticky left-10 z-[2] bg-sc-surface' : '',
                       c.name === itemField && !atStart ? 'sc-sticky-shadow-r' : '']">
              <FormField :model-value="r[c.name]"
                :field="c" :context="r" :parent-doc="parentDoc" size="sm" :show-label="false"
                :readonly="colReadonly(c)"
                @update:model-value="v => updateCell(idx, c.name, v)"
                @selected="(linked) => handleLinkSelected(idx, c, linked)"
                @create-new="(p) => emit('createNew', { ...(p || {}), field: c, childField: schema.field, rowIdx: idx })" />
              <!-- Yêu cầu 2.3: dòng có mapping NCC → icon nhỏ cạnh mã vật tư -->
              <span v-if="c.name === itemField && hasTrace(r)"
                class="absolute top-1 right-1 text-sc-royal" :title="`Tên hàng theo NCC: ${r.supplier_item_name}`">
                <Icon name="truck" :size="12" />
              </span>
            </td>
            <td v-if="!readonly" class="sticky right-0 z-[2] bg-sc-surface px-2 py-1 align-top w-10"
              :class="{ 'sc-sticky-shadow-l': !atEnd }">
              <button @click.stop="removeRow(idx)" type="button"
                class="text-sc-danger hover:bg-sc-danger-50 px-1.5 py-1 rounded text-sm"
                title="Bỏ dòng này (không bán mặt hàng này)"><Icon name="x" :size="14" /></button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="grandTotal != null && rows.length">
          <tr class="bg-sc-bg font-semibold">
            <td class="sticky left-0 z-[3] bg-sc-bg px-2 py-2 text-sc-text-muted text-xs w-10"
              :class="{ 'sc-sticky-shadow-r': !atStart && !itemField }"></td>
            <td v-for="c in schema.columns" :key="c.name" class="px-2 py-2 text-sm"
              :class="[c.compute && c.type === 'Currency' ? 'text-right' : '',
                       c.name === itemField ? 'sticky left-10 z-[3] bg-sc-bg' : '',
                       c.name === itemField && !atStart ? 'sc-sticky-shadow-r' : '']">
              <span v-if="c.compute && c.type === 'Currency'" class="font-mono">
                Tổng: {{ fmtVND(totals[c.name]) }}
              </span>
            </td>
            <td v-if="!readonly" class="sticky right-0 z-[3] bg-sc-bg w-10"
              :class="{ 'sc-sticky-shadow-l': !atEnd }"></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Drawer chi tiết dòng (dùng chung) -->
    <LineItemDetailDrawer
      :open="drawerIdx !== null"
      :row="drawerIdx !== null ? (rows[drawerIdx] || {}) : {}"
      :groups="drawerGroups"
      :parent-doc="parentDoc"
      :index="drawerIdx || 0" :total="rows.length"
      :title="schema.label || 'Chi tiết dòng'"
      @apply="applyDrawer" @close="closeDrawer" @navigate="navigateDrawer" />

    <!-- CR-02: modal Import danh mục vào lưới (chưa lưu DB) -->
    <Modal :open="importOpen" :title="`Nhập danh mục: ${schema.label}`" size="lg" @close="importOpen = false">
      <div class="space-y-4 text-sm">
        <div class="bg-sc-warning-50 border border-sc-warning/40 rounded p-2 text-xs text-sc-warning">
          Tải mẫu → điền → chọn file (.xlsx/.csv) → kiểm tra → <b>nạp vào lưới</b>. Dữ liệu chỉ
          nạp vào form đang soạn (<b>chưa lưu</b>); vẫn sửa tay được. Dòng lỗi sẽ <b>không</b> được nạp.
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button @click="downloadGridTemplate('xlsx')" :disabled="ioBusy" type="button" class="sc-btn-secondary text-xs">
            <Icon name="download" :size="13" /> Mẫu .xlsx
          </button>
          <button @click="downloadGridTemplate('csv')" :disabled="ioBusy" type="button" class="sc-btn-secondary text-xs">
            <Icon name="download" :size="13" /> Mẫu .csv
          </button>
          <input type="file" accept=".xlsx,.csv" @change="onImportFile" class="text-xs" />
          <button @click="runParse" :disabled="!importFile || ioBusy" type="button" class="sc-btn-secondary text-xs">
            <Icon name="search" :size="13" /> {{ ioBusy ? 'Đang đọc...' : 'Kiểm tra' }}
          </button>
        </div>

        <div v-if="parseResult" class="border border-sc-border rounded overflow-hidden">
          <div class="bg-sc-bg px-3 py-2 flex flex-wrap gap-3 text-xs">
            <span><b class="font-mono">{{ parseResult.total }}</b> tổng dòng</span>
            <span class="text-sc-success"><b class="font-mono">{{ parseResult.ok_count }}</b> hợp lệ</span>
            <span class="text-sc-danger"><b class="font-mono">{{ parseResult.error_count }}</b> lỗi</span>
          </div>
          <div v-if="parseResult.error_count" class="bg-sc-danger-50 px-3 py-2 border-t border-sc-danger/40 max-h-40 overflow-y-auto">
            <ul class="text-xs text-sc-danger list-disc list-inside">
              <li v-for="(e, i) in parseResult.rows_error" :key="i">
                Dòng {{ e.line }}<span v-if="e.item"> ({{ e.item }})</span>: {{ e.errors.join('; ') }}
              </li>
            </ul>
          </div>
          <div class="px-3 py-2 border-t border-sc-border flex items-center gap-3 text-xs">
            <label class="flex items-center gap-1"><input type="radio" value="append" v-model="loadMode" /> Thêm vào lưới</label>
            <label class="flex items-center gap-1"><input type="radio" value="replace" v-model="loadMode" /> Thay thế lưới</label>
          </div>
        </div>
      </div>
      <template #footer>
        <button @click="importOpen = false" type="button" class="sc-btn-secondary text-sm">Đóng</button>
        <button @click="loadIntoGrid" :disabled="!parseResult || !parseResult.ok_count" type="button" class="sc-btn-primary text-sm">
          <Icon name="check" :size="14" /> Nạp {{ parseResult?.ok_count || 0 }} dòng vào lưới
        </button>
      </template>
    </Modal>

    <!-- Picker: chọn dòng từ danh sách (vd hóa đơn công nợ NCC) + xem trước -->
    <Modal v-if="pickerCfg" :open="pickerOpen" :title="pickerCfg.title || 'Chọn dòng'" size="xl"
      @close="pickerOpen = false">
      <div v-if="pickerLoading" class="p-6 text-center text-sm text-sc-text-muted">Đang nạp danh sách…</div>
      <div v-else-if="!pickerRows.length" class="p-6 text-center text-sm text-sc-text-muted">
        Không có dòng nào để chọn.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-sc-bg text-sc-text-muted text-xs uppercase">
            <tr>
              <th class="px-2 py-1.5 w-8"></th>
              <th v-for="col in pickerCfg.columns" :key="col.key"
                class="px-2 py-1.5" :class="col.money ? 'text-right' : 'text-left'">{{ col.label }}</th>
              <th class="px-2 py-1.5 w-8 text-center">Xem</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in pickerRows" :key="row[pickerCfg.rowKey]"
              class="border-b border-sc-border hover:bg-sc-royal-50/25 cursor-pointer"
              :class="{ 'opacity-50': pickerExisting.has(row[pickerCfg.rowKey]) }"
              @click="togglePick(row)">
              <td class="px-2 py-1.5 text-center" @click.stop>
                <input type="checkbox" class="w-4 h-4"
                  :checked="pickerSel.has(row[pickerCfg.rowKey]) || pickerExisting.has(row[pickerCfg.rowKey])"
                  :disabled="pickerExisting.has(row[pickerCfg.rowKey])"
                  @change="togglePick(row)" />
              </td>
              <td v-for="col in pickerCfg.columns" :key="col.key" class="px-2 py-1.5"
                :class="col.money ? 'text-right tabular-nums font-mono' : ''">
                {{ col.money ? fmtVND(row[col.key]) : (row[col.key] ?? '—') }}
              </td>
              <td class="px-2 py-1.5 text-center" @click.stop>
                <button type="button" @click="openPickerPreview(row)"
                  class="text-sc-royal hover:bg-sc-royal-50 rounded p-1" title="Xem trước phiếu">
                  <Icon name="eye" :size="15" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p class="text-xs text-sc-text-muted mt-2">Dòng mờ = đã có trong lưới.</p>
      </div>
      <template #footer>
        <span class="text-xs text-sc-text-muted mr-auto self-center">Đã chọn {{ pickerSel.size }}</span>
        <button @click="pickerOpen = false" type="button" class="sc-btn-secondary text-sm">Hủy</button>
        <button @click="addPicked" :disabled="!pickerSel.size" type="button" class="sc-btn-primary text-sm">
          <Icon name="check" :size="14" /> Thêm {{ pickerSel.size || '' }} dòng
        </button>
      </template>
    </Modal>

    <DocPreviewDrawer v-if="pickerCfg" :open="pickerPreview.open"
      :doctype="pickerCfg.previewDoctype || ''" :name="pickerPreview.name"
      @close="pickerPreview.open = false" />
  </div>
</template>

<style scoped>
/* Bóng đổ mép cột ghim (Yêu cầu 3) — báo còn nội dung khuất khi cuộn ngang */
.sc-sticky-shadow-r { box-shadow: 8px 0 10px -7px rgba(16, 42, 69, 0.22); }
.sc-sticky-shadow-l { box-shadow: -8px 0 10px -7px rgba(16, 42, 69, 0.22); }
</style>
