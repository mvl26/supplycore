<script setup>
import { computed, ref } from 'vue'
import FormField from './FormField.vue'
import Icon from './Icon.vue'
import Modal from './Modal.vue'
import { call, voucherIo, downloadFile, fileToBase64, VOUCHER_IO_DOCTYPES } from '../api'
import { useToastStore } from '../stores/toast'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  schema: { type: Object, required: true },  // { field, label, columns }
  readonly: Boolean,
  parentDoc: { type: Object, default: () => ({}) },  // doc cha — để kế thừa giá trị header
  doctype: { type: String, default: '' },            // doctype cha — để Import/Export lưới (CR-02)
})
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

function fmtCurrency(v) {
  if (v == null) return ''
  return Math.round(Number(v) || 0).toLocaleString('vi-VN') + ' ₫'
}

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
  success: 'bg-sc-success hover:bg-green-700 text-white',
  danger:  'bg-sc-danger hover:bg-red-700 text-white',
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
        <button @click="newRow" type="button" class="sc-btn-secondary text-xs">
          + Thêm dòng
        </button>
      </div>
    </div>

    <div v-if="rows.length === 0" class="border border-dashed border-sc-border rounded-md p-6 text-center text-sm text-sc-text-muted">
      Chưa có dòng nào — click "+ Thêm dòng" để bắt đầu
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-sc-bg text-sc-text-muted text-xs uppercase">
            <th class="px-2 py-1.5 text-left w-8">#</th>
            <th v-for="c in schema.columns" :key="c.name"
              :style="c.width ? { width: c.width } : {}"
              class="px-2 py-1.5 text-left">
              {{ c.label }}
              <span v-if="c.required" class="text-sc-danger">*</span>
            </th>
            <th v-if="!readonly" class="w-10"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in rows" :key="idx" class="border-b border-sc-border">
            <td class="px-2 py-1 text-sc-text-muted text-xs align-top pt-3">{{ idx + 1 }}</td>
            <td v-for="c in schema.columns" :key="c.name" class="px-2 py-1 align-top">
              <FormField :model-value="r[c.name]"
                :field="c" :context="r" :parent-doc="parentDoc" size="sm" :show-label="false"
                @update:model-value="v => updateCell(idx, c.name, v)"
                @selected="(linked) => handleLinkSelected(idx, c, linked)"
                @create-new="(p) => emit('createNew', { ...(p || {}), field: c, childField: schema.field, rowIdx: idx })" />
            </td>
            <td v-if="!readonly" class="px-2 py-1 align-top">
              <button @click="removeRow(idx)" type="button"
                class="text-sc-danger hover:bg-red-50 px-1.5 py-1 rounded text-sm"><Icon name="x" :size="14" /></button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="grandTotal != null && rows.length">
          <tr class="bg-sc-bg font-semibold">
            <td class="px-2 py-2 text-sc-text-muted text-xs"></td>
            <td v-for="c in schema.columns" :key="c.name" class="px-2 py-2 text-sm">
              <span v-if="c.compute && c.type === 'Currency'" class="font-mono">
                Tổng: {{ fmtCurrency(totals[c.name]) }}
              </span>
            </td>
            <td v-if="!readonly"></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- CR-02: modal Import danh mục vào lưới (chưa lưu DB) -->
    <Modal :open="importOpen" :title="`Nhập danh mục: ${schema.label}`" size="lg" @close="importOpen = false">
      <div class="space-y-4 text-sm">
        <div class="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-800">
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
          <div v-if="parseResult.error_count" class="bg-red-50 px-3 py-2 border-t border-red-200 max-h-40 overflow-y-auto">
            <ul class="text-xs text-red-700 list-disc list-inside">
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
  </div>
</template>
