<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from '../api'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import { useToastStore } from '../stores/toast'
import { fmtNumber, fmtVND, fmtDate } from '../utils'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const batchInput = ref(route.query.batch || '')
const itemInput = ref('')
const trace = ref(null)
const batchList = ref([])
const loading = ref(false)
const searchingItem = ref(false)

const API_PREFIX = 'supplycore.m10_traceability.api.trace.'

async function lookup() {
  if (!batchInput.value.trim()) {
    toast.warning('Nhập mã lô để tra cứu')
    return
  }
  loading.value = true
  trace.value = null
  try {
    trace.value = await call(API_PREFIX + 'get_batch_trace',
      { batch_no: batchInput.value.trim() })
    if (trace.value && trace.value.exists === false) {
      toast.warning(`Không tìm thấy lô ${batchInput.value}`)
    }
    router.replace({ query: { batch: batchInput.value.trim() } }).catch(() => {})
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function searchByItem() {
  if (!itemInput.value.trim()) return
  searchingItem.value = true
  batchList.value = []
  try {
    batchList.value = await call(API_PREFIX + 'list_batches_for_item',
      { item_code_or_name: itemInput.value.trim(), limit: 30 })
    if (!batchList.value.length) toast.info('Không tìm thấy lô khớp tên/mã VT')
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    searchingItem.value = false
  }
}

function selectBatch(b) {
  batchInput.value = b
  lookup()
}

function goToDoc(dt, name) {
  if (!name) return
  router.push(`/doc/${encodeURIComponent(dt)}/${encodeURIComponent(name)}`)
}

// Auto-load nếu URL có batch param
if (route.query.batch) lookup()

const qcBadge = (s) => ({
  Accepted: 'sc-badge-success', Rejected: 'sc-badge-critical',
  Pending: 'sc-badge-warning', Conditional: 'sc-badge-warning',
}[s] || 'sc-badge-neutral')

const qcLabel = (s) => ({
  Accepted: 'Đạt', Rejected: 'Không đạt',
  Pending: 'Chờ KCS', Conditional: 'Có điều kiện',
}[s] || s)

const expiryStatus = computed(() => {
  if (!trace.value?.header?.expiry_date) return null
  const exp = new Date(trace.value.header.expiry_date)
  const days = (exp - new Date()) / (1000 * 60 * 60 * 24)
  if (days < 0) return { cls: 'text-red-700 bg-red-100', label: 'ĐÃ HẾT HẠN' }
  if (days < 30) return { cls: 'text-red-700 bg-red-50', label: `Còn ${Math.floor(days)} ngày` }
  if (days < 90) return { cls: 'text-amber-700 bg-amber-50', label: `Còn ${Math.floor(days)} ngày` }
  return { cls: 'text-green-700 bg-green-50', label: `Còn ${Math.floor(days)} ngày` }
})

function totalConsumption(movements) {
  return movements.filter(m => !m.is_cancelled)
    .reduce((s, m) => m.qty_change < 0 ? s + Math.abs(m.qty_change) : s, 0)
}
function totalReceived(movements) {
  return movements.filter(m => !m.is_cancelled)
    .reduce((s, m) => m.qty_change > 0 ? s + m.qty_change : s, 0)
}

function voucherLink(vt, vn) {
  goToDoc(vt, vn)
}

const missingLabel = {
  supplier: 'NCC chưa khai',
  supplier_batch_no: 'Số lô NCC chưa khai',
  manufacturer: 'Nhà sản xuất chưa khai',
  manufacturing_date: 'Ngày SX chưa khai',
  purchase_receipt_origin: 'Không liên kết PR gốc',
  qc_inspection_pending: 'KCS chưa kết luận',
}
</script>

<template>
  <PageHeader title="Truy xuất lô — UC-29" icon="file-search" code="M10"
    subtitle="Tra cứu vòng đời 1 lô vật tư: nguồn gốc → di chuyển → cấp phát → tồn hiện tại" />

  <!-- Lookup form -->
  <div class="sc-card p-4 mb-4">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Mã lô (Batch No)</label>
        <div class="flex gap-2">
          <input v-model="batchInput" @keyup.enter="lookup"
            class="sc-input font-mono" placeholder="VD: GLU500-202503-001" />
          <button @click="lookup" :disabled="loading"
            class="sc-btn-primary text-sm disabled:opacity-50">
            <template v-if="loading">...</template>
            <template v-else><Icon name="search" :size="14" /> Tra cứu</template>
          </button>
        </div>
      </div>
      <div>
        <label class="text-xs text-sc-text-muted block mb-1">Hoặc tìm theo VT</label>
        <div class="flex gap-2">
          <input v-model="itemInput" @keyup.enter="searchByItem"
            class="sc-input" placeholder="Mã/tên vật tư..." />
          <button @click="searchByItem" :disabled="searchingItem"
            class="sc-btn-secondary text-sm disabled:opacity-50">
            {{ searchingItem ? '...' : 'Tìm' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Batch list result -->
    <div v-if="batchList.length" class="mt-4 border-t pt-3">
      <div class="text-xs text-sc-text-muted mb-2">Tìm thấy {{ batchList.length }} lô:</div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-64 overflow-y-auto">
        <button v-for="b in batchList" :key="b.name"
          @click="selectBatch(b.name)"
          class="text-left p-2 border rounded hover:bg-sc-bg hover:border-sc-royal transition">
          <div class="font-mono text-xs font-semibold text-sc-navy">{{ b.name }}</div>
          <div class="text-xs text-sc-text-muted">{{ b.item_name }} · HD: {{ fmtDate(b.expiry_date) || '—' }}</div>
          <div class="flex gap-1 mt-1">
            <span :class="['sc-badge', qcBadge(b.qc_status)]">{{ qcLabel(b.qc_status) }}</span>
            <span v-if="b.blocked" class="sc-badge sc-badge-critical">Khoá</span>
          </div>
        </button>
      </div>
    </div>
  </div>

  <!-- No data -->
  <div v-if="!trace" class="sc-card p-10 text-center text-sc-text-muted">
    Nhập mã lô và bấm <strong><Icon name="search" :size="14" /> Tra cứu</strong> để xem timeline.
  </div>

  <!-- Not found -->
  <div v-else-if="trace.exists === false" class="sc-card p-10 text-center text-sc-danger">
    <Icon name="x-circle" :size="16" /> Không tìm thấy lô <strong class="font-mono">{{ trace.batch_no }}</strong>
  </div>

  <!-- Trace timeline -->
  <div v-else class="space-y-4">
    <!-- Data quality warning -->
    <div v-if="!trace.data_quality.complete"
      class="sc-card p-3 bg-amber-50 border-amber-200">
      <div class="flex items-start gap-2">
        <span class="text-amber-700 text-lg"><Icon name="alert-triangle" :size="18" /></span>
        <div class="text-sm text-amber-900 flex-1">
          <strong>Dữ liệu chưa đầy đủ</strong> — các trường còn thiếu:
          <ul class="mt-1 list-disc list-inside text-xs">
            <li v-for="m in trace.data_quality.missing" :key="m">{{ missingLabel[m] || m }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Section 1: Header -->
    <div class="sc-card p-5">
      <h3 class="font-semibold text-sc-navy text-lg mb-3 flex items-center gap-2">
        <span class="text-2xl"><Icon name="package" :size="20" /></span>
        <span>Lô <span class="font-mono">{{ trace.header.name }}</span></span>
        <span v-if="trace.header.blocked" class="sc-badge sc-badge-critical"><Icon name="ban" :size="14" /> ĐÃ KHOÁ</span>
        <span :class="['sc-badge', qcBadge(trace.header.qc_status)]">
          KCS: {{ qcLabel(trace.header.qc_status) }}
        </span>
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div>
          <div class="text-xs text-sc-text-muted">Vật tư</div>
          <div class="cursor-pointer text-sc-royal hover:underline" @click="goToDoc('SC Item', trace.header.item)">
            <span class="font-mono text-xs">{{ trace.header.item }}</span>
          </div>
          <div class="text-xs">{{ trace.header.item_name }}</div>
        </div>
        <div>
          <div class="text-xs text-sc-text-muted">Nhà sản xuất</div>
          <div>{{ trace.header.manufacturer || '—' }}</div>
        </div>
        <div>
          <div class="text-xs text-sc-text-muted">NCC</div>
          <div>{{ trace.header.supplier || '—' }}</div>
          <div v-if="trace.header.supplier_batch_no" class="text-xs font-mono">
            Lô NCC: {{ trace.header.supplier_batch_no }}
          </div>
        </div>
        <div>
          <div class="text-xs text-sc-text-muted">Xuất xứ</div>
          <div>{{ trace.header.country_of_origin || '—' }}</div>
        </div>
        <div>
          <div class="text-xs text-sc-text-muted">Ngày SX</div>
          <div>{{ fmtDate(trace.header.manufacturing_date) || '—' }}</div>
        </div>
        <div>
          <div class="text-xs text-sc-text-muted">Hạn dùng</div>
          <div class="font-semibold">{{ fmtDate(trace.header.expiry_date) || '—' }}</div>
          <span v-if="expiryStatus"
            :class="['text-xs px-2 py-0.5 rounded-full inline-block mt-1', expiryStatus.cls]">
            {{ expiryStatus.label }}
          </span>
        </div>
        <div v-if="trace.header.block_reason" class="md:col-span-2">
          <div class="text-xs text-sc-text-muted">Lý do khoá</div>
          <div class="text-red-700">{{ trace.header.block_reason }}</div>
        </div>
      </div>
    </div>

    <!-- Section 2: Origin -->
    <div class="sc-card p-5">
      <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
        <span class="text-xl"><Icon name="building-2" :size="18" /></span> Nguồn gốc (PR → PO → QI)
      </h3>
      <div v-if="!trace.origin" class="text-sc-text-muted text-sm">
        <Icon name="alert-triangle" :size="14" /> Không tìm thấy PR gốc — có thể là lô nhập từ kho khác hoặc data import
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="border-l-4 border-sc-royal pl-3">
          <div class="text-xs text-sc-text-muted">Phiếu nhập (PR)</div>
          <div class="cursor-pointer text-sc-royal hover:underline font-mono text-sm"
            @click="goToDoc('SC Purchase Receipt', trace.origin.purchase_receipt)">
            {{ trace.origin.purchase_receipt }}
          </div>
          <div class="text-xs mt-1"><Icon name="calendar" :size="14" /> {{ fmtDate(trace.origin.received_date) }}</div>
          <div class="text-xs"><Icon name="building" :size="14" /> {{ trace.origin.supplier }}</div>
        </div>
        <div v-if="trace.origin.purchase_order" class="border-l-4 border-amber-500 pl-3">
          <div class="text-xs text-sc-text-muted">Đơn mua (PO)</div>
          <div class="cursor-pointer text-sc-royal hover:underline font-mono text-sm"
            @click="goToDoc('SC Purchase Order', trace.origin.purchase_order)">
            {{ trace.origin.purchase_order }}
          </div>
        </div>
        <div v-if="trace.origin.qc_inspection" class="border-l-4 border-green-500 pl-3">
          <div class="text-xs text-sc-text-muted">Phiếu KCS</div>
          <div class="cursor-pointer text-sc-royal hover:underline font-mono text-sm"
            @click="goToDoc('SC Quality Inspection', trace.origin.qc_inspection)">
            {{ trace.origin.qc_inspection }}
          </div>
          <div class="text-xs mt-1"><Icon name="calendar" :size="14" /> {{ fmtDate(trace.origin.qc_date) }}</div>
          <span :class="['sc-badge', qcBadge(trace.origin.qc_result)]">
            {{ qcLabel(trace.origin.qc_result) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Section 3: Current Stock -->
    <div class="sc-card p-5">
      <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
        <span class="text-xl"><Icon name="map-pin" :size="18" /></span> Tồn kho hiện tại
        <span class="ml-auto font-mono text-lg font-bold text-sc-success">
          {{ fmtNumber(trace.current_stock.total_qty) }}
        </span>
      </h3>
      <div v-if="!trace.current_stock.by_warehouse.length" class="text-sc-text-muted text-sm">
        Không còn tồn kho ở bất kỳ kho nào (đã xuất hết / huỷ).
      </div>
      <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div v-for="(w, idx) in trace.current_stock.by_warehouse" :key="idx"
          class="border rounded p-2 hover:bg-sc-bg cursor-pointer"
          @click="goToDoc('SC Warehouse', w.warehouse)">
          <div class="text-xs text-sc-text-muted">{{ w.warehouse }}</div>
          <div class="font-mono font-semibold text-right">{{ fmtNumber(w.qty) }}</div>
        </div>
      </div>
    </div>

    <!-- Section 4: Movements -->
    <div class="sc-card overflow-hidden">
      <div class="p-5 pb-3">
        <h3 class="font-semibold text-sc-navy flex items-center gap-2">
          <span class="text-xl"><Icon name="clipboard-list" :size="18" /></span> Sổ cái tồn kho ({{ trace.movements.length }} bút toán)
          <span class="ml-auto text-xs text-sc-text-muted">
            Nhập: <span class="text-sc-success font-mono">+{{ fmtNumber(totalReceived(trace.movements)) }}</span>
            · Xuất: <span class="text-sc-danger font-mono">-{{ fmtNumber(totalConsumption(trace.movements)) }}</span>
          </span>
        </h3>
      </div>
      <div v-if="!trace.movements.length" class="p-5 text-center text-sc-text-muted">
        Chưa có giao dịch nào trên lô này.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th>Ngày/Giờ</th><th>Kho</th><th>Vị trí</th>
              <th class="text-right">SL Δ</th>
              <th class="text-right">Đơn giá</th>
              <th>Chứng từ</th><th>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in trace.movements" :key="idx"
              :class="m.is_cancelled ? 'opacity-50 line-through' : ''">
              <td class="text-xs">
                {{ fmtDate(m.posting_date) }}
                <div class="text-sc-text-muted">{{ m.posting_time }}</div>
              </td>
              <td>{{ m.warehouse }}</td>
              <td class="text-xs font-mono">{{ m.bin_location || '—' }}</td>
              <td class="text-right font-mono font-semibold"
                :class="m.qty_change > 0 ? 'text-sc-success' : 'text-sc-danger'">
                {{ m.qty_change > 0 ? '+' : '' }}{{ fmtNumber(m.qty_change) }}
              </td>
              <td class="text-right font-mono">{{ fmtVND(m.valuation_rate) }}</td>
              <td class="text-xs">
                <span class="text-sc-royal hover:underline cursor-pointer font-mono"
                  @click="voucherLink(m.voucher_type, m.voucher_no)">
                  {{ m.voucher_no }}
                </span>
                <div class="text-sc-text-muted">{{ m.voucher_type?.replace('SC ', '') }}</div>
              </td>
              <td class="text-xs text-sc-text-muted">{{ m.remarks || '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>
