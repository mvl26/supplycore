<script setup>
import { ref, computed } from 'vue'
import { voucherIo, downloadFile, fileToBase64 } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import Icon from './Icon.vue'

const props = defineProps({
  doctype: { type: String, required: true },
  label: { type: String, default: 'phiếu' },        // tên loại phiếu (tiêu đề modal)
  filters: { type: Array, default: () => [] },
  orderBy: { type: String, default: 'modified desc' },
  canImport: { type: Boolean, default: true },
})
const emit = defineEmits(['imported'])
const toast = useToastStore()

// ===== EXPORT =====
const exportOpen = ref(false)
const exportBusy = ref(false)
const exportScope = ref('filtered')
const exportLimit = ref(10000)

async function doExport() {
  exportBusy.value = true
  try {
    const file = await voucherIo.export(props.doctype, {
      filters: exportScope.value === 'filtered' ? props.filters : [],
      limit: exportLimit.value,
      order_by: props.orderBy,
    })
    downloadFile(file)
    toast.success(`Đã xuất ${file.contract_count} phiếu · ${file.item_count} dòng vật tư → ${file.filename}`)
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
const allowCreate = ref(true)
const importBusy = ref(false)
const tplBusy = ref(false)
const dryResult = ref(null)
const commitDone = ref(null)

function openImport() {
  importOpen.value = true
  importFile.value = null
  dryResult.value = null
  commitDone.value = null
}

async function downloadTemplate(withData) {
  tplBusy.value = true
  try {
    const file = await voucherIo.template(props.doctype, { with_data: withData, limit: 50 })
    downloadFile(file)
    toast.success(withData
      ? `Đã tải template + ${file.contract_count} phiếu hiện có`
      : 'Đã tải template trống (sheet Phiếu + Vật tư + Hướng dẫn)')
  } catch (e) {
    toast.error(`Tải template lỗi: ${e.message}`)
  } finally {
    tplBusy.value = false
  }
}

function onFileChosen(ev) {
  const f = ev.target.files?.[0]
  if (!f) { importFile.value = null; return }
  if (!f.name.toLowerCase().endsWith('.xlsx')) toast.warning('Chỉ nhận file Excel .xlsx (2 sheet)')
  importFile.value = f
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
    dryResult.value = await voucherIo.import(props.doctype, {
      content_b64, dry_run: true, allow_create: allowCreate.value,
    })
    const s = dryResult.value.summary
    if ((dryResult.value.errors || []).length) {
      toast.warning(`${dryResult.value.errors.length} lỗi cần sửa`)
    } else {
      toast.success(`Sẵn sàng: ${s.would_create} tạo · ${s.would_update} cập nhật · ${s.skipped} bỏ qua`)
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
    commitDone.value = await voucherIo.import(props.doctype, {
      content_b64, dry_run: false, allow_create: allowCreate.value,
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
  create: 'sc-badge-success', created: 'sc-badge-success',
  update: 'sc-badge-info', updated: 'sc-badge-info',
  skipped: 'sc-badge-neutral', error: 'sc-badge-critical', failed: 'sc-badge-critical',
}[a] || 'sc-badge-neutral')
const actionLabel = (a) => ({
  create: 'Sẽ tạo', created: 'Đã tạo', update: 'Sẽ cập nhật', updated: 'Đã cập nhật',
  skipped: 'Bỏ qua', error: 'Lỗi', failed: 'Lỗi',
}[a] || a)
</script>

<template>
  <span class="inline-flex gap-2">
    <button @click="exportOpen = true" class="sc-btn-secondary text-sm" title="Xuất phiếu + danh mục vật tư ra Excel">
      <Icon name="upload" :size="14" /> Xuất
    </button>
    <button v-if="canImport" @click="openImport" class="sc-btn-secondary text-sm" title="Nhập phiếu + danh mục vật tư từ Excel">
      <Icon name="download" :size="14" /> Nhập
    </button>
  </span>

  <!-- ===== EXPORT MODAL ===== -->
  <Modal :open="exportOpen" :title="`Xuất ${label} (Excel 2 sheet)`" size="md" @close="exportOpen = false">
    <div class="space-y-4 text-sm">
      <div class="bg-blue-50 border border-blue-200 rounded p-2 text-xs text-blue-800">
        File Excel có <b>2 sheet</b>: <b>Phiếu</b> (mỗi phiếu 1 dòng) và <b>Vật tư</b>
        (mỗi item 1 dòng), nối nhau bằng cột <b>Mã phiếu</b>. Giữ nguyên 2 dòng đầu mỗi sheet để nhập lại được.
      </div>
      <div class="flex flex-wrap gap-4">
        <div>
          <label class="text-xs text-sc-text-muted block mb-1">Phạm vi</label>
          <select v-model="exportScope" class="sc-input text-sm">
            <option value="filtered">Theo bộ lọc hiện tại</option>
            <option value="all">Toàn bộ (bỏ lọc)</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-sc-text-muted block mb-1">Giới hạn số phiếu</label>
          <input v-model.number="exportLimit" type="number" class="sc-input text-sm w-32" />
        </div>
      </div>
    </div>
    <template #footer>
      <button @click="exportOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
      <button @click="doExport" :disabled="exportBusy" class="sc-btn-primary text-sm">
        <Icon v-if="!exportBusy" name="download" :size="14" />
        {{ exportBusy ? 'Đang xuất...' : 'Tải file Excel' }}
      </button>
    </template>
  </Modal>

  <!-- ===== IMPORT MODAL ===== -->
  <Modal :open="importOpen" :title="`Nhập ${label} từ Excel`" size="lg" @close="importOpen = false">
    <div class="space-y-4 text-sm">
      <div class="bg-amber-50 border border-amber-200 rounded p-2 text-xs text-amber-800">
        File <b>.xlsx</b> cấu trúc <b>2 sheet</b> (Phiếu + Vật tư), nối bằng <b>Mã phiếu</b>.
        Phiếu nhập vào <b>luôn lưu ở dạng Nháp (Draft)</b>. Phiếu đã có sẽ <b>cập nhật + thay
        toàn bộ danh mục vật tư</b> (chỉ khi đang Draft); phiếu đã duyệt/ghi sổ sẽ bị bỏ qua.
      </div>

      <div class="border border-sc-border rounded p-3 bg-sc-bg">
        <div class="text-xs font-semibold text-sc-navy mb-2">① Tải template (kèm sheet Hướng dẫn)</div>
        <div class="flex flex-wrap items-center gap-2">
          <button @click="downloadTemplate(false)" :disabled="tplBusy" class="sc-btn-secondary text-sm">
            <Icon name="download" :size="14" /> Template trống
          </button>
          <button @click="downloadTemplate(true)" :disabled="tplBusy" class="sc-btn-secondary text-sm">
            <Icon name="download" :size="14" /> Template + dữ liệu hiện có (≤50 phiếu)
          </button>
        </div>
      </div>

      <div>
        <label class="text-xs font-semibold text-sc-navy block mb-1">② Chọn file đã điền (.xlsx)</label>
        <input type="file" accept=".xlsx" @change="onFileChosen" class="block w-full text-sm" />
        <div v-if="importFile" class="text-xs text-sc-text-muted mt-1">
          {{ importFile.name }} · {{ (importFile.size / 1024).toFixed(1) }} KB
        </div>
      </div>

      <label class="flex items-center gap-2 text-sm">
        <input type="checkbox" v-model="allowCreate" />
        Tạo mới phiếu chưa có trong hệ thống (phiếu mới luôn ở Draft)
      </label>

      <div>
        <div class="text-xs font-semibold text-sc-navy mb-1">③ Kiểm tra & nhập</div>
        <div class="flex gap-2">
          <button @click="runDryRun" :disabled="!importFile || importBusy" class="sc-btn-secondary text-sm">
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

      <div v-if="result" class="border border-sc-border rounded overflow-hidden">
        <div class="bg-sc-bg px-3 py-2 flex flex-wrap gap-2 text-xs">
          <span v-for="(v, k) in result.summary" :key="k"
            class="px-2 py-0.5 bg-white border border-sc-border rounded">
            <b class="font-mono">{{ v }}</b>
            <span class="text-sc-text-muted ml-1">{{ {
              total: 'Tổng phiếu', created: 'Đã tạo', updated: 'Đã cập nhật',
              skipped: 'Bỏ qua', failed: 'Lỗi', would_create: 'Sẽ tạo', would_update: 'Sẽ cập nhật',
            }[k] || k }}</span>
          </span>
        </div>
        <div v-if="result.errors?.length" class="bg-red-50 px-3 py-2 border-t border-red-200">
          <div class="text-xs font-semibold text-red-700 mb-1">{{ result.errors.length }} lỗi:</div>
          <ul class="text-xs text-red-700 list-disc list-inside max-h-32 overflow-y-auto">
            <li v-for="(e, i) in result.errors" :key="i">{{ e }}</li>
          </ul>
        </div>
        <div class="max-h-56 overflow-y-auto">
          <table class="w-full text-xs">
            <thead class="bg-sc-bg sticky top-0">
              <tr>
                <th class="px-2 py-1 text-left">Mã phiếu</th>
                <th class="px-2 py-1 text-left">Kết quả</th>
                <th class="px-2 py-1 text-right">Số VT</th>
                <th class="px-2 py-1 text-left">Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in result.preview" :key="i" class="border-t border-sc-border">
                <td class="px-2 py-1 font-mono">{{ row.name || row.key || '—' }}</td>
                <td class="px-2 py-1">
                  <span class="sc-badge text-xs" :class="actionBadge(row.action)">{{ actionLabel(row.action) }}</span>
                </td>
                <td class="px-2 py-1 text-right font-mono">{{ row.item_count ?? '—' }}</td>
                <td class="px-2 py-1">
                  <span v-if="row.error" class="text-red-600">{{ row.error }}</span>
                  <span v-else-if="row.reason" class="text-sc-text-muted">{{ row.reason }}</span>
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
