<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { call, uploadFile } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const toast = useToastStore()

const file = ref(null)
const fileName = ref('')
const busy = ref(false)
const result = ref(null)
const errorMsg = ref('')
const method = ref('vision')  // 'vision' (Claude API) | 'ocr' (tesseract offline)

function onPick(e) {
  const f = e.target.files && e.target.files[0]
  file.value = f || null
  fileName.value = f ? f.name : ''
  result.value = null
  errorMsg.value = ''
}

async function runImport() {
  if (!file.value) { toast.error('Chọn file PDF phiếu HIS trước'); return }
  busy.value = true
  result.value = null
  errorMsg.value = ''
  try {
    const up = await uploadFile(file.value, { isPrivate: true })
    const r = await call('supplycore.api.his_import.import_transfer_slip',
      { file_url: up.file_url, backend: method.value })
    result.value = r
    if (r.status === 'submitted') {
      toast.success(`Đã ghi nhận & submit phiếu ${r.his_slip_no} (${r.lines_ok} dòng)`)
    } else if (r.status === 'draft_review') {
      toast.success(`Đã quét & tạo phiếu nháp ${r.his_slip_no} — kiểm tra rồi submit`)
    } else {
      toast.warning(`Tạo phiếu nháp — ${r.lines_error} dòng cần sửa`)
    }
  } catch (e) {
    errorMsg.value = e.message || String(e)
    toast.error(errorMsg.value)
  } finally {
    busy.value = false
  }
}

function openTR() {
  if (result.value?.transfer_request) {
    router.push(`/doc/SC Transfer Request/${encodeURIComponent(result.value.transfer_request)}`)
  }
}
</script>

<template>
  <div>
    <PageHeader title="Nhập phiếu chuyển kho HIS" icon="file-text"
      code="M6 · UC-18B" subtitle="Đọc tự động phiếu xuất điều chuyển HIS (PDF) bằng AI" />

    <div class="sc-card p-5 mb-5 max-w-2xl">
      <p class="text-[13px] text-sc-text-soft mb-4">
        Chọn file PDF phiếu "PHIẾU XUẤT ĐIỀU CHUYỂN" từ HIS. Hệ thống đọc nội dung,
        đối chiếu vật tư (theo Mã HIS) và kho, rồi:
        khớp 100% → tạo &amp; ghi nhận phiếu chuyển kho tự động;
        có dòng lỗi → tạo phiếu nháp để sửa tay.
      </p>

      <div class="mb-4">
        <div class="text-[12px] font-semibold text-sc-text mb-1.5">Phương thức đọc</div>
        <div class="flex flex-col gap-1.5">
          <label class="flex items-start gap-2 cursor-pointer text-[13px]">
            <input type="radio" value="vision" v-model="method" class="mt-0.5" />
            <span><span class="font-medium">AI (Vision)</span> — chính xác cao, khớp 100% tự ghi nhận &amp; submit. <span class="text-sc-text-muted">Cần cấu hình API key.</span></span>
          </label>
          <label class="flex items-start gap-2 cursor-pointer text-[13px]">
            <input type="radio" value="ocr" v-model="method" class="mt-0.5" />
            <span><span class="font-medium">Quét OCR (offline)</span> — không cần API key. Luôn tạo phiếu nháp điền sẵn để <span class="font-medium text-amber-700">bạn đối chiếu PDF rồi submit tay</span>.</span>
          </label>
        </div>
      </div>

      <label class="flex items-center gap-3 cursor-pointer">
        <span class="sc-btn-secondary text-sm inline-flex items-center gap-2">
          <Icon name="upload" :size="16" /> Chọn PDF
        </span>
        <span class="text-[13px] text-sc-text-muted truncate">{{ fileName || 'Chưa chọn file' }}</span>
        <input type="file" accept="application/pdf,.pdf" class="hidden" @change="onPick" />
      </label>

      <div class="mt-4">
        <button class="sc-btn-primary text-sm inline-flex items-center gap-2"
          :disabled="!file || busy" @click="runImport">
          <Icon :name="busy ? 'rotate-cw' : 'zap'" :size="16" :class="busy ? 'animate-spin' : ''" />
          {{ busy ? 'Đang đọc & nhập…' : 'Nhập tự động' }}
        </button>
      </div>

      <div v-if="errorMsg" class="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-[13px] whitespace-pre-line">
        {{ errorMsg }}
      </div>
    </div>

    <!-- Report -->
    <div v-if="result" class="sc-card p-5 max-w-3xl">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
          <span class="sc-badge"
            :class="result.status === 'submitted' ? 'sc-badge-success'
              : (result.status === 'draft_review' ? 'sc-badge-info' : 'sc-badge-warning')">
            {{ result.status === 'submitted' ? 'Đã ghi nhận (submitted)'
              : (result.status === 'draft_review' ? 'Phiếu nháp (đã quét — cần đối chiếu)'
              : 'Phiếu nháp (cần sửa)') }}
          </span>
          <span class="font-mono text-[12px] text-sc-text-muted">{{ result.his_slip_no }}</span>
        </div>
        <button class="sc-btn-secondary text-xs inline-flex items-center gap-1.5" @click="openTR">
          Mở phiếu <Icon name="arrow-right" :size="14" />
        </button>
      </div>

      <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="text-center p-3 rounded-lg bg-sc-bg-soft">
          <div class="text-2xl font-bold font-mono text-sc-navy">{{ result.lines_total }}</div>
          <div class="text-[11px] text-sc-text-muted">Tổng dòng</div>
        </div>
        <div class="text-center p-3 rounded-lg bg-green-50">
          <div class="text-2xl font-bold font-mono text-green-700">{{ result.lines_ok }}</div>
          <div class="text-[11px] text-sc-text-muted">Khớp OK</div>
        </div>
        <div class="text-center p-3 rounded-lg bg-amber-50">
          <div class="text-2xl font-bold font-mono text-amber-700">{{ result.lines_error }}</div>
          <div class="text-[11px] text-sc-text-muted">Cần sửa</div>
        </div>
      </div>

      <div v-if="result.unmapped_warehouses?.length" class="mb-3 text-[13px]">
        <span class="font-semibold text-sc-text">Kho chưa ánh xạ:</span>
        <span class="text-amber-700"> {{ result.unmapped_warehouses.join(', ') }}</span>
        <span class="text-sc-text-muted"> — thêm tại DocType "SC HIS Warehouse Map"</span>
      </div>
      <div v-if="result.unmapped_items?.length" class="mb-3 text-[13px]">
        <span class="font-semibold text-sc-text">Mã HIS chưa có vật tư:</span>
        <span class="text-amber-700"> {{ result.unmapped_items.join(', ') }}</span>
        <span class="text-sc-text-muted"> — điền "Mã HIS" trên SC Item tương ứng</span>
      </div>

      <div v-if="result.errors?.length" class="mt-3">
        <div class="text-[12px] font-semibold text-sc-text mb-2">Dòng cần sửa</div>
        <table class="sc-table w-full text-[12.5px]">
          <thead>
            <tr><th>TT</th><th>Mã HIS</th><th>Tên VT</th><th>Trạng thái</th><th>Ghi chú</th></tr>
          </thead>
          <tbody>
            <tr v-for="er in result.errors" :key="er.tt">
              <td>{{ er.tt }}</td>
              <td class="font-mono">{{ er.his_code }}</td>
              <td>{{ er.name }}</td>
              <td><span class="sc-badge sc-badge-warning">{{ er.status }}</span></td>
              <td class="text-sc-text-soft">{{ er.note }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
