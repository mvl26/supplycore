<script setup>
import { ref, computed } from 'vue'
import { dataIo, downloadFile, fileToBase64 } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import Icon from './Icon.vue'

const props = defineProps({
  doctype:  { type: String, required: true },
  // Cột listColumns hiện trên màn hình [{key,label}] — dùng làm preset chọn cột
  listColumns: { type: Array, default: () => [] },
  // Filter Frappe đang áp dụng trên list (buildFilters output)
  filters:  { type: Array, default: () => [] },
  orderBy:  { type: String, default: 'modified desc' },
  // Quyền
  canImport: { type: Boolean, default: true },
})
const emit = defineEmits(['imported'])
const toast = useToastStore()

// ===== EXPORT =====
const exportOpen = ref(false)
const exportBusy = ref(false)
const allColumns = ref([])          // [{fieldname,label,in_list_view,fieldtype}]
const selectedCols = ref(new Set()) // fieldname đã chọn
const exportFileType = ref('csv')
const exportScope = ref('filtered') // 'filtered' = theo filter hiện tại; 'all' = toàn bộ
const exportLimit = ref(10000)

async function openExport() {
  exportOpen.value = true
  if (!allColumns.value.length) {
    try {
      const r = await dataIo.getListColumns(props.doctype)
      allColumns.value = r.columns || []
      // Mặc định chọn: các cột đang hiển thị trên list + name
      const listKeys = new Set(['name', ...props.listColumns.map(c => c.key)])
      selectedCols.value = new Set(
        allColumns.value.filter(c => listKeys.has(c.fieldname)).map(c => c.fieldname)
      )
      if (selectedCols.value.size === 0) {
        // fallback: chọn các cột in_list_view
        allColumns.value.filter(c => c.in_list_view).forEach(c => selectedCols.value.add(c.fieldname))
      }
      selectedCols.value.add('name')
    } catch (e) {
      toast.error(`Không tải được danh sách cột: ${e.message}`)
    }
  }
}

function toggleCol(fn) {
  if (fn === 'name') return  // name luôn bắt buộc
  const s = new Set(selectedCols.value)
  if (s.has(fn)) s.delete(fn); else s.add(fn)
  selectedCols.value = s
}
function selectAllCols() {
  selectedCols.value = new Set(allColumns.value.map(c => c.fieldname))
}
function selectListCols() {
  const listKeys = new Set(['name', ...props.listColumns.map(c => c.key)])
  selectedCols.value = new Set(
    allColumns.value.filter(c => listKeys.has(c.fieldname)).map(c => c.fieldname)
  )
}
function clearCols() {
  selectedCols.value = new Set(['name'])
}

const selectedCount = computed(() => selectedCols.value.size)

async function doExport() {
  if (selectedCols.value.size === 0) {
    toast.warning('Chọn ít nhất 1 cột')
    return
  }
  exportBusy.value = true
  try {
    // Giữ thứ tự cột theo allColumns
    const cols = allColumns.value
      .filter(c => selectedCols.value.has(c.fieldname))
      .map(c => c.fieldname)
    const file = await dataIo.exportList(props.doctype, {
      columns: cols,
      filters: exportScope.value === 'filtered' ? props.filters : [],
      file_type: exportFileType.value,
      limit: exportLimit.value,
      order_by: props.orderBy,
    })
    downloadFile(file)
    toast.success(`Đã xuất ${file.row_count} dòng → ${file.filename}`)
    exportOpen.value = false
  } catch (e) {
    toast.error(`Xuất lỗi: ${e.message}`)
  } finally {
    exportBusy.value = false
  }
}

// ===== IMPORT =====
const importOpen = ref(false)
const importFile = ref(null)
const importFileType = ref('csv')
const updateExisting = ref(false)
const importBusy = ref(false)
const dryResult = ref(null)
const commitDone = ref(null)
const tplBusy = ref(false)
const tplFileType = ref('csv')

function openImport() {
  importOpen.value = true
  importFile.value = null
  dryResult.value = null
  commitDone.value = null
}

async function downloadTemplate(withData) {
  tplBusy.value = true
  try {
    const file = await dataIo.getListTemplate(props.doctype, {
      file_type: tplFileType.value,
      with_data: withData,
      limit: 50,
    })
    downloadFile(file)
    toast.success(withData
      ? `Đã tải template + ${file.row_count} dòng dữ liệu`
      : `Đã tải template trống (${file.columns.length} cột)`)
  } catch (e) {
    toast.error(`Tải template lỗi: ${e.message}`)
  } finally {
    tplBusy.value = false
  }
}

function onFileChosen(ev) {
  const f = ev.target.files?.[0]
  if (!f) { importFile.value = null; return }
  importFile.value = f
  importFileType.value = f.name.toLowerCase().endsWith('.xlsx') ? 'xlsx' : 'csv'
  dryResult.value = null
  commitDone.value = null
}

async function runDryRun() {
  if (!importFile.value) return
  importBusy.value = true
  dryResult.value = null
  commitDone.value = null
  try {
    const content_b64 = await fileToBase64(importFile.value)
    dryResult.value = await dataIo.importData(props.doctype, {
      content_b64,
      file_type: importFileType.value,
      update_existing: updateExisting.value,
      dry_run: true,
      two_row_header: true,   // format 3-dòng
    })
    const s = dryResult.value.summary
    if ((dryResult.value.errors || []).length) {
      toast.warning(`${dryResult.value.errors.length} lỗi cần sửa`)
    } else {
      toast.success(`Sẵn sàng: ${s.would_create} tạo · ${s.would_update} cập nhật`)
    }
  } catch (e) {
    toast.error(`Kiểm tra lỗi: ${e.message}`)
  } finally {
    importBusy.value = false
  }
}

async function runCommit() {
  if (!importFile.value || !dryResult.value) return
  importBusy.value = true
  try {
    const content_b64 = await fileToBase64(importFile.value)
    commitDone.value = await dataIo.importData(props.doctype, {
      content_b64,
      file_type: importFileType.value,
      update_existing: updateExisting.value,
      dry_run: false,
      two_row_header: true,
    })
    const s = commitDone.value.summary
    toast.success(`Tạo ${s.created} · Cập nhật ${s.updated} · Bỏ qua ${s.skipped} · Lỗi ${s.failed}`)
    emit('imported')
  } catch (e) {
    toast.error(`Nhập lỗi: ${e.message}`)
  } finally {
    importBusy.value = false
  }
}

const result = computed(() => commitDone.value || dryResult.value)

const actionBadge = (a) => ({
  create:'sc-badge-success', created:'sc-badge-success',
  update:'sc-badge-info', updated:'sc-badge-info',
  skip:'sc-badge-neutral', skipped:'sc-badge-neutral',
  error:'sc-badge-critical', failed:'sc-badge-critical',
}[a] || 'sc-badge-neutral')
const actionLabel = (a) => ({
  create:'Sẽ tạo', created:'Đã tạo', update:'Sẽ cập nhật', updated:'Đã cập nhật',
  skip:'Bỏ qua', skipped:'Đã bỏ qua', error:'Lỗi', failed:'Lỗi',
}[a] || a)
</script>

<template>
  <span class="inline-flex gap-2">
    <button @click="openExport" class="sc-btn-secondary text-sm" title="Xuất danh sách ra file">
      <Icon name="upload" :size="14" /> Xuất
    </button>
    <button v-if="canImport" @click="openImport" class="sc-btn-secondary text-sm" title="Nhập dữ liệu từ file">
      <Icon name="download" :size="14" /> Nhập
    </button>
  </span>

  <!-- ===== EXPORT MODAL ===== -->
  <Modal :open="exportOpen" title="Xuất danh sách" size="lg" @close="exportOpen = false">
    <div class="space-y-4 text-sm">
      <div class="bg-blue-50 border border-blue-200 rounded p-2 text-xs text-blue-800">
        File xuất ra có <b>3 phần</b>: dòng 1 = tên cột hiển thị · dòng 2 = mã trường (fieldname) ·
        dòng 3 trở đi = dữ liệu. Giữ nguyên 2 dòng đầu để nhập lại được.
      </div>

      <!-- Scope + format -->
      <div class="flex flex-wrap gap-4">
        <div>
          <label class="text-xs text-sc-text-muted block mb-1">Phạm vi</label>
          <select v-model="exportScope" class="sc-input text-sm">
            <option value="filtered">Theo bộ lọc hiện tại</option>
            <option value="all">Toàn bộ (bỏ lọc)</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-sc-text-muted block mb-1">Định dạng</label>
          <select v-model="exportFileType" class="sc-input text-sm">
            <option value="csv">CSV (.csv)</option>
            <option value="xlsx">Excel (.xlsx)</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-sc-text-muted block mb-1">Giới hạn dòng</label>
          <input v-model.number="exportLimit" type="number" class="sc-input text-sm w-28" />
        </div>
      </div>

      <!-- Column picker -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="text-xs font-medium text-sc-text-muted">
            Chọn cột xuất ({{ selectedCount }}/{{ allColumns.length }})
          </label>
          <div class="flex gap-1 text-xs">
            <button @click="selectListCols" class="text-sc-royal hover:underline">Cột đang xem</button>
            <span class="text-sc-border">·</span>
            <button @click="selectAllCols" class="text-sc-royal hover:underline">Tất cả</button>
            <span class="text-sc-border">·</span>
            <button @click="clearCols" class="text-sc-royal hover:underline">Bỏ chọn</button>
          </div>
        </div>
        <div class="border border-sc-border rounded max-h-64 overflow-y-auto p-2 grid grid-cols-2 md:grid-cols-3 gap-1">
          <label v-for="c in allColumns" :key="c.fieldname"
            class="flex items-center gap-1.5 text-xs px-1 py-0.5 rounded hover:bg-sc-bg cursor-pointer"
            :class="c.fieldname === 'name' ? 'opacity-70' : ''">
            <input type="checkbox" :checked="selectedCols.has(c.fieldname)"
              :disabled="c.fieldname === 'name'"
              @change="toggleCol(c.fieldname)" />
            <span class="truncate" :title="`${c.label} (${c.fieldname})`">
              {{ c.label }}
              <span class="text-sc-text-muted">· {{ c.fieldname }}</span>
            </span>
          </label>
        </div>
      </div>
    </div>
    <template #footer>
      <button @click="exportOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
      <button @click="doExport" :disabled="exportBusy || selectedCount === 0"
        class="sc-btn-primary text-sm">
        <Icon v-if="!exportBusy" name="download" :size="14" />
        {{ exportBusy ? 'Đang xuất...' : `Tải file (${selectedCount} cột)` }}
      </button>
    </template>
  </Modal>

  <!-- ===== IMPORT MODAL ===== -->
  <Modal :open="importOpen" title="Nhập dữ liệu từ file" size="lg" @close="importOpen = false">
    <div class="space-y-4 text-sm">
      <div class="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-800">
        File nhập phải đúng <b>format 3 phần</b>: dòng 1 = tên hiển thị (chỉ để đọc) ·
        <b>dòng 2 = fieldname</b> (bắt buộc, hệ thống dùng dòng này) · dòng 3+ = dữ liệu.
        Tải template bên dưới để có sẵn đúng cấu trúc.
      </div>

      <!-- BƯỚC 1: Tải template -->
      <div class="border border-sc-border rounded p-3 bg-sc-bg">
        <div class="text-xs font-semibold text-sc-navy mb-2">① Tải template (đúng format 3 dòng)</div>
        <div class="flex flex-wrap items-center gap-2">
          <select v-model="tplFileType" class="sc-input text-sm py-1">
            <option value="csv">CSV (.csv)</option>
            <option value="xlsx">Excel (.xlsx)</option>
          </select>
          <button @click="downloadTemplate(false)" :disabled="tplBusy"
            class="sc-btn-secondary text-sm">
            <Icon name="download" :size="14" /> Template trống
          </button>
          <button @click="downloadTemplate(true)" :disabled="tplBusy"
            class="sc-btn-secondary text-sm">
            <Icon name="download" :size="14" /> Template + dữ liệu hiện có (≤50 dòng)
          </button>
        </div>
        <p class="text-xs text-sc-text-muted mt-1.5">
          Template trống: chỉ 2 dòng header để điền mới. Template + dữ liệu: kèm bản ghi
          hiện có để sửa rồi nhập lại (bật "Cập nhật" bên dưới).
        </p>
      </div>

      <!-- BƯỚC 2: Chọn file -->
      <div>
        <label class="text-xs font-semibold text-sc-navy block mb-1">② Chọn file đã điền (.csv / .xlsx)</label>
        <input type="file" accept=".csv,.xlsx" @change="onFileChosen" class="block w-full text-sm" />
        <div v-if="importFile" class="text-xs text-sc-text-muted mt-1">
          {{ importFile.name }} · {{ (importFile.size/1024).toFixed(1) }} KB
        </div>
      </div>

      <label class="flex items-center gap-2 text-sm">
        <input type="checkbox" v-model="updateExisting" />
        Cập nhật bản ghi đã tồn tại (khớp theo cột <code>name</code>)
      </label>

      <div>
        <div class="text-xs font-semibold text-sc-navy mb-1">③ Kiểm tra & nhập</div>
        <div class="flex gap-2">
          <button @click="runDryRun" :disabled="!importFile || importBusy"
            class="sc-btn-secondary text-sm">
            <Icon v-if="!(importBusy && !commitDone)" name="search" :size="14" />
            {{ importBusy && !commitDone ? 'Đang kiểm tra...' : 'Kiểm tra (dry-run)' }}
          </button>
          <button @click="runCommit"
            :disabled="!dryResult || importBusy || (dryResult?.errors?.length)"
            class="sc-btn-primary text-sm">
            <Icon name="check" :size="14" /> Nhập vào hệ thống
          </button>
        </div>
      </div>

      <!-- Result -->
      <div v-if="result" class="border border-sc-border rounded overflow-hidden">
        <div class="bg-sc-bg px-3 py-2 flex flex-wrap gap-2 text-xs">
          <span v-for="(v,k) in result.summary" :key="k"
            class="px-2 py-0.5 bg-white border border-sc-border rounded">
            <b class="font-mono">{{ v }}</b>
            <span class="text-sc-text-muted ml-1">{{ {
              total:'Tổng', created:'Đã tạo', updated:'Đã cập nhật',
              skipped:'Bỏ qua', failed:'Lỗi',
              would_create:'Sẽ tạo', would_update:'Sẽ cập nhật',
            }[k] || k }}</span>
          </span>
        </div>
        <div v-if="result.errors?.length" class="bg-red-50 px-3 py-2 border-t border-red-200">
          <div class="text-xs font-semibold text-red-700 mb-1">{{ result.errors.length }} lỗi:</div>
          <ul class="text-xs text-red-700 list-disc list-inside max-h-32 overflow-y-auto">
            <li v-for="(e,i) in result.errors" :key="i">{{ e }}</li>
          </ul>
        </div>
        <div v-if="result.unmapped_headers?.length"
          class="bg-yellow-50 px-3 py-1.5 border-t border-yellow-200 text-xs text-yellow-800">
          Cột không khớp (bỏ qua):
          <code v-for="h in result.unmapped_headers" :key="h" class="mx-1">{{ h }}</code>
        </div>
        <div class="max-h-56 overflow-y-auto">
          <table class="w-full text-xs">
            <thead class="bg-sc-bg sticky top-0">
              <tr>
                <th class="px-2 py-1 text-left">Dòng</th>
                <th class="px-2 py-1 text-left">Kết quả</th>
                <th class="px-2 py-1 text-left">Mã</th>
                <th class="px-2 py-1 text-left">Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in result.preview" :key="row.line" class="border-t border-sc-border">
                <td class="px-2 py-1 font-mono">{{ row.line }}</td>
                <td class="px-2 py-1">
                  <span class="sc-badge text-xs" :class="actionBadge(row.action)">
                    {{ actionLabel(row.action) }}
                  </span>
                </td>
                <td class="px-2 py-1 font-mono">{{ row.name || '—' }}</td>
                <td class="px-2 py-1">
                  <span v-if="row.error" class="text-red-600">{{ row.error }}</span>
                  <span v-else-if="row.reason" class="text-sc-text-muted">{{ row.reason }}</span>
                  <span v-else-if="row.fields_count" class="text-sc-text-muted">{{ row.fields_count }} trường</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <template #footer>
      <button @click="importOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
    </template>
  </Modal>
</template>
