<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { confirmPickLine, submitDoc, getList } from '../api'
import { fmtNumber } from '../utils'
import Icon from './Icon.vue'
import FefoPickGuide from './FefoPickGuide.vue'
import { useToastStore } from '../stores/toast'

// Màn soạn hàng cho Phiếu giao hàng (nháp, picking_required): nhân viên kho quét
// lô + vị trí (bin) + SL cho từng dòng → server validate đúng lô/SL/tồn/hạn mới
// đánh dấu đã quét; đủ tất cả mới cho Submit (xuất kho). Máy PDA quét = gõ text
// vào ô đang focus + Enter → dùng được ngay trên trình duyệt PDA.
const props = defineProps({
  doc: { type: Object, required: true },
  readonly: { type: Boolean, default: false },   // true = phiếu đã submit → chỉ hiện danh sách đã lấy
})
const emit = defineEmits(['after'])
const toast = useToastStore()

const lines = computed(() => props.doc.items || [])
const confirmedCount = computed(() => lines.value.filter(l => l.scan_confirmed).length)
const total = computed(() => lines.value.length)
const allConfirmed = computed(() => total.value > 0 && confirmedCount.value === total.value)
const firstUnconfirmed = computed(() => lines.value.find(l => !l.scan_confirmed) || null)

// State ô quét theo từng dòng (key = row name)
const scan = reactive({})
function inp(row) {
  if (!scan[row.name]) scan[row.name] = { batch: row.batch || '', bin: '', qty: row.qty }
  return scan[row.name]
}
const openGuide = reactive({})   // toggle bảng FEFO gợi ý theo dòng
const busy = ref('')

// DN Item chỉ lưu MÃ vật tư + MÃ lô → nạp thêm TÊN vật tư (SC Item) và
// SỐ LÔ NCC (SC Batch.supplier_batch_no) để hiển thị cho nhân viên kho dễ đối chiếu.
const itemNames = reactive({})
const supBatches = reactive({})
async function loadMeta() {
  const rows = props.doc.items || []
  const itemCodes = [...new Set(rows.map(r => r.item).filter(Boolean))]
  const batchCodes = [...new Set(rows.map(r => r.batch).filter(Boolean))]
  if (itemCodes.length) {
    try {
      const its = await getList('SC Item', { filters: [['name', 'in', itemCodes]], fields: ['name', 'item_name'], limit: 999 })
      for (const it of its) itemNames[it.name] = it.item_name
    } catch (e) {}
  }
  if (batchCodes.length) {
    try {
      const bs = await getList('SC Batch', { filters: [['name', 'in', batchCodes]], fields: ['name', 'supplier_batch_no'], limit: 999 })
      for (const b of bs) supBatches[b.name] = b.supplier_batch_no
    } catch (e) {}
  }
}
watch(() => (props.doc.items || []).map(r => `${r.item}|${r.batch || ''}`).join(','),
  loadMeta, { immediate: true })
const itemLabel = (code) => itemNames[code] || code
const supBatchOf = (batch) => supBatches[batch] || ''

async function doConfirm(row) {
  const s = inp(row)
  if (!s.batch || !String(s.batch).trim()) { toast.error('Quét hoặc nhập số lô trước khi xác nhận'); return }
  if (!(Number(s.qty) > 0)) { toast.error('Số lượng phải lớn hơn 0'); return }
  busy.value = row.name
  try {
    const r = await confirmPickLine(
      props.doc.name, row.name,
      String(s.batch).trim(),
      s.bin ? String(s.bin).trim() : null,
      s.qty,
    )
    toast.success(r.all_confirmed
      ? 'Đã quét đủ tất cả — bấm "Xuất kho & giao" để hoàn tất'
      : `Đã xác nhận. Còn ${r.remaining_unconfirmed} dòng chưa quét`)
    emit('after')   // confirm_pick_line đã lưu phiếu → reload để lấy trạng thái mới
  } catch (e) {
    toast.error(e.message)
  } finally {
    busy.value = ''
  }
}

const submitting = ref(false)
async function doSubmit() {
  submitting.value = true
  try {
    await submitDoc('SC Delivery Note', props.doc.name)
    toast.success('Đã xuất kho & giao hàng — tồn kho đã trừ')
    emit('after')
  } catch (e) {
    toast.error(e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="sc-card mb-4 overflow-hidden">
    <!-- Header + tiến độ -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-sc-border bg-sc-bg gap-3 flex-wrap">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon :name="readonly ? 'clipboard-check' : 'scan'" :size="18" />
        {{ readonly ? 'Đã lấy hàng — lô · vị trí · số lượng' : 'Soạn hàng — quét xác nhận' }}
        <span class="text-xs font-normal text-sc-text-muted">Kho xuất: {{ doc.from_warehouse }}</span>
      </h3>
      <span class="text-sm font-mono px-2 py-0.5 rounded"
        :class="(readonly || allConfirmed) ? 'bg-sc-success-50 text-sc-success font-semibold' : 'bg-sc-warning-50 text-sc-warning'">
        {{ readonly ? total + ' dòng' : confirmedCount + '/' + total + ' dòng đã quét' }}
      </span>
    </div>

    <div class="p-3 space-y-2">
      <div v-for="row in lines" :key="row.name"
        class="border rounded-lg p-3"
        :class="row.scan_confirmed ? 'border-sc-success/50 bg-sc-success-50/40' : 'border-sc-border'">
        <!-- Dòng đã xác nhận -->
        <div v-if="row.scan_confirmed" class="flex items-center gap-x-3 gap-y-1 flex-wrap text-sm">
          <Icon name="check-circle" :size="18" class="text-sc-success" />
          <span class="font-medium">{{ itemLabel(row.item) }}</span>
          <span class="font-mono text-xs text-sc-text-muted">{{ row.item }}</span>
          <span class="font-mono text-xs px-2 py-0.5 bg-sc-royal text-white rounded">Lô {{ row.batch }}</span>
          <span v-if="supBatchOf(row.batch)" class="text-xs text-sc-text-muted">Lô NCC: <b>{{ supBatchOf(row.batch) }}</b></span>
          <span v-if="row.bin_location" class="inline-flex items-center gap-1 text-sc-text-muted">
            <Icon name="map-pin" :size="14" /> {{ row.bin_location }}</span>
          <span class="inline-flex items-center gap-1"><Icon name="package" :size="14" /> SL {{ fmtNumber(row.qty) }}</span>
          <span class="text-xs text-sc-success ml-auto">{{ readonly ? 'Đã lấy' : 'Đã xác nhận' }}</span>
        </div>

        <!-- Dòng chưa xác nhận: ô quét -->
        <div v-else>
          <div class="flex items-center justify-between gap-2 mb-2 flex-wrap">
            <div class="text-sm">
              <span class="font-medium">{{ itemLabel(row.item) }}</span>
              <span class="text-sc-text-muted font-mono text-xs ml-1">{{ row.item }}</span>
              <span class="text-sc-text-muted">· cần {{ fmtNumber(row.qty) }} {{ row.uom }}</span>
              <span v-if="row.batch" class="block text-xs text-sc-text-muted mt-0.5">
                Lô gợi ý: <b class="font-mono">{{ row.batch }}</b>
                <template v-if="supBatchOf(row.batch)"> · Lô NCC: <b>{{ supBatchOf(row.batch) }}</b></template>
              </span>
            </div>
            <button type="button" class="text-xs text-sc-royal inline-flex items-center gap-1"
              @click="openGuide[row.name] = !openGuide[row.name]">
              <Icon name="map" :size="13" /> {{ openGuide[row.name] ? 'Ẩn' : 'Gợi ý FEFO' }}
            </button>
          </div>

          <FefoPickGuide v-if="openGuide[row.name]" class="mb-2"
            :item="row.item" :warehouse="row.warehouse || doc.from_warehouse" :qty-needed="row.qty" />

          <div class="grid grid-cols-1 sm:grid-cols-[1fr_1fr_90px_auto] gap-2 items-end">
            <div>
              <label class="text-xs text-sc-text-muted">Quét/nhập LÔ</label>
              <input v-model="inp(row).batch" type="text"
                :autofocus="firstUnconfirmed && row.name === firstUnconfirmed.name"
                placeholder="Quét mã lô…" class="sc-input py-2"
                @keyup.enter="doConfirm(row)" />
            </div>
            <div>
              <label class="text-xs text-sc-text-muted">Quét VỊ TRÍ (bin) — tùy chọn</label>
              <input v-model="inp(row).bin" type="text"
                placeholder="Quét mã vị trí…" class="sc-input py-2"
                @keyup.enter="doConfirm(row)" />
            </div>
            <div>
              <label class="text-xs text-sc-text-muted">SL lấy</label>
              <input v-model.number="inp(row).qty" type="number" min="0" step="any"
                class="sc-input py-2" @keyup.enter="doConfirm(row)" />
            </div>
            <button type="button" class="sc-btn-primary py-2 whitespace-nowrap"
              :disabled="busy === row.name" @click="doConfirm(row)">
              <Icon name="check" :size="15" /> {{ busy === row.name ? 'Đang…' : 'Xác nhận' }}
            </button>
          </div>
          <p class="text-[11px] text-sc-text-muted mt-1">
            Có thể quét <b>lô khác</b> lô gợi ý — hệ thống sẽ kiểm tra đúng vật tư, còn hạn, đủ tồn.
          </p>
        </div>
      </div>
    </div>

    <!-- Submit (chỉ khi đang soạn — phiếu đã submit thì ẩn) -->
    <div v-if="!readonly" class="px-4 py-3 border-t border-sc-border bg-sc-bg flex items-center justify-between gap-3 flex-wrap">
      <span class="text-sm" :class="allConfirmed ? 'text-sc-success' : 'text-sc-text-muted'">
        <template v-if="allConfirmed">✓ Đã quét đủ — sẵn sàng xuất kho</template>
        <template v-else>Còn {{ total - confirmedCount }} dòng chưa quét — quét đủ mới xuất được</template>
      </span>
      <button type="button" class="bg-sc-success hover:brightness-110 text-white px-4 py-2 rounded-md font-medium text-sm disabled:opacity-40"
        :disabled="!allConfirmed || submitting" @click="doSubmit">
        <Icon name="truck" :size="15" /> {{ submitting ? 'Đang xuất…' : 'Xuất kho & giao (Submit)' }}
      </button>
    </div>
  </div>
</template>
