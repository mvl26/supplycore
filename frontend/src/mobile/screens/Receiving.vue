<!-- frontend/src/mobile/screens/Receiving.vue
     Màn hình Tiếp nhận / Nhập kho — mobile (giao diện premium).

     LUỒNG:
       1. Danh sách phiếu SC Purchase Receipt ở trạng thái Draft (docstatus=0)
       2. Chọn phiếu → form chi tiết: danh sách vật tư (items[]), nhập SL nhận (qty),
          quét lô NCC (supplier_batch_no)
       3. Xác nhận: updateDoc (ghi qty + supplier_batch_no) → submitDoc (đăng tải tồn kho)

     Field schema (SC Purchase Receipt Item):
       item, item_name, qty (SL nhận), po_qty (SL đặt hàng - tham chiếu),
       uom, rate, warehouse, supplier_batch_no, batch_no, manufacturing_date, expiry_date
-->
<template>
  <MPullRefresh :refreshing="loading" @refresh="load">
    <MTopBar title="Tiếp nhận" sub="Phiếu nhập chờ xử lý" />

    <div class="m-page">

      <!-- ── DANH SÁCH PHIẾU NHẬP CHỜ ── -->
      <template v-if="!current">
        <!-- Đang tải -->
        <MSkeleton v-if="loading" :count="4" />

        <!-- Lỗi tải -->
        <MErrorState
          v-else-if="loadError"
          :message="loadError"
          @retry="load"
        />

        <!-- Rỗng -->
        <MEmpty
          v-else-if="rows.length === 0"
          icon="truck"
          title="Không có phiếu nhập chờ"
          sub="Tất cả phiếu đã được xử lý"
        />

        <!-- Danh sách -->
        <ul v-else class="m-list">
          <li
            v-for="r in rows"
            :key="r.name"
            class="m-card m-card--tap m-rise"
            @click="open(r.name)"
          >
            <div class="rc-card-header">
              <span class="m-card__title">{{ r.name }}</span>
              <Icon name="chevron-right" :size="16" class="m-card__chev" />
            </div>
            <div class="m-card__row">
              <span>NCC</span>
              <b>{{ r.supplier_name || r.supplier || '—' }}</b>
            </div>
            <div class="m-card__row">
              <span>Kho nhập</span>
              <b>{{ r.to_warehouse || '—' }}</b>
            </div>
            <div class="m-card__row">
              <span>Ngày</span>
              <b>{{ fmtDate(r.posting_date) }}</b>
            </div>
          </li>
        </ul>
      </template>

      <!-- ── CHI TIẾT PHIẾU NHẬP ── -->
      <template v-else>
        <!-- Hàng quay lại -->
        <div class="rc-back-row">
          <button class="m-btn m-btn--ghost m-btn--sm rc-back-btn" @click="backToList">
            <Icon name="arrow-left" :size="16" /> Danh sách
          </button>
          <span class="rc-detail-name">{{ current.name }}</span>
        </div>

        <!-- Meta phiếu -->
        <div class="m-card">
          <div class="m-card__row">
            <span>NCC</span>
            <b>{{ current.supplier_name || current.supplier || '—' }}</b>
          </div>
          <div class="m-card__row">
            <span>Kho nhập</span>
            <b>{{ current.to_warehouse || '—' }}</b>
          </div>
          <div v-if="current.purchase_order" class="m-card__row">
            <span>PO</span>
            <b class="rc-mono">{{ current.purchase_order }}</b>
          </div>
          <div v-if="current.qc_required" class="m-card__row">
            <span>QC</span>
            <MBadge status="Pending" label="Yêu cầu KCS" />
          </div>
        </div>

        <!-- Không có vật tư -->
        <MEmpty
          v-if="!current.items || current.items.length === 0"
          icon="package"
          title="Phiếu không có dòng vật tư"
        />

        <!-- Danh sách vật tư -->
        <ul v-else class="m-list">
          <li
            v-for="(it, i) in current.items"
            :key="it.name || i"
            class="m-card rc-item-card"
          >
            <!-- Tên vật tư -->
            <div class="m-card__title">{{ it.item_name || it.item }}</div>
            <div v-if="it.item_name" class="rc-item-code">{{ it.item }}</div>

            <!-- SL nhận — field thực: qty -->
            <label class="m-field">
              <span>
                SL nhận
                <span v-if="it.po_qty != null" class="rc-field-hint">(SL PO: {{ it.po_qty }})</span>
              </span>
              <input
                v-model.number="it.qty"
                type="number"
                inputmode="decimal"
                min="0"
                class="m-input rc-input-qty"
                placeholder="0"
              />
            </label>

            <!-- Quét lô NCC → supplier_batch_no -->
            <div class="rc-scan-row">
              <button class="m-btn m-btn--ghost m-btn--sm rc-scan-btn" @click="scanBatch(it)">
                <Icon name="scan" :size="16" /> Quét lô NCC
              </button>
              <span v-if="it.supplier_batch_no" class="m-badge m-badge--info rc-batch-val">
                {{ it.supplier_batch_no }}
              </span>
            </div>
          </li>
        </ul>

        <!-- Nút xác nhận -->
        <button
          class="m-btn m-btn--ok"
          :disabled="saving"
          @click="confirm"
        >
          <Icon name="check-circle" :size="18" />
          <span v-if="saving">Đang xử lý...</span>
          <span v-else>Xác nhận nhận hàng</span>
        </button>
      </template>

    </div>
  </MPullRefresh>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Icon from '../../components/Icon.vue'
import MTopBar from '../ui/MTopBar.vue'
import MBadge from '../ui/MBadge.vue'
import MSkeleton from '../ui/MSkeleton.vue'
import MEmpty from '../ui/MEmpty.vue'
import MErrorState from '../ui/MErrorState.vue'
import MPullRefresh from '../ui/MPullRefresh.vue'
import { tapLight, notifySuccess, notifyError } from '../native'
import { getList, getDoc, updateDoc, submitDoc } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'

const DT = 'SC Purchase Receipt'

const rows      = ref([])
const current   = ref(null)
const loading   = ref(false)
const saving    = ref(false)
const loadError = ref(null)

const { scan } = useScanner()
const toast    = useToastStore()

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtDate(d) {
  if (!d) return '—'
  const parts = String(d).split('-')
  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`
  return d
}

// ─── Tải danh sách phiếu Draft ───────────────────────────────────────────────

async function load() {
  loading.value = true
  loadError.value = null
  try {
    rows.value = await getList(DT, {
      filters: [['docstatus', '=', 0]],
      fields: ['name', 'supplier', 'supplier_name', 'to_warehouse', 'posting_date'],
      order_by: 'creation desc',
      limit: 50,
    })
  } catch (e) {
    loadError.value = e.message
    toast.error(`Lỗi tải danh sách: ${e.message}`)
  } finally {
    loading.value = false
  }
}

// ─── Mở chi tiết phiếu ───────────────────────────────────────────────────────

async function open(name) {
  tapLight()
  loading.value = true
  try {
    current.value = await getDoc(DT, name)
  } catch (e) {
    toast.error(`Lỗi tải phiếu: ${e.message}`)
  } finally {
    loading.value = false
  }
}

function backToList() {
  current.value = null
}

// ─── Quét lô NCC → ghi vào supplier_batch_no ─────────────────────────────────

async function scanBatch(it) {
  tapLight()
  try {
    const code = await scan()
    if (code) it.supplier_batch_no = code   // null = huỷ, im lặng
  } catch (e) {
    notifyError()
    toast.error(e.message || 'Không mở được camera quét mã.')
  }
}

// ─── Xác nhận nhận hàng: update → submit ──────────────────────────────────────

async function confirm() {
  if (saving.value) return
  if (current.value.items && current.value.items.every(it => !Number(it.qty))) {
    toast.warning('Vui lòng nhập số lượng nhận cho ít nhất một dòng.')
    return
  }
  saving.value = true
  try {
    // Ghi toàn bộ mảng items (giữ tất cả field, chỉ qty + supplier_batch_no được chỉnh)
    await updateDoc(DT, current.value.name, { items: current.value.items })
    await submitDoc(DT, current.value.name)
    notifySuccess()
    toast.success('Đã xác nhận nhận hàng và cập nhật tồn kho.')
    current.value = null
    await load()
  } catch (e) {
    // Giữ ở detail view để người dùng có thể sửa và thử lại
    notifyError()
    toast.error(`Lỗi xác nhận: ${e.message}`)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
/* ── Header card (mã phiếu + chevron) ── */
.rc-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

/* ── Quay lại ── */
.rc-back-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rc-back-btn {
  flex-shrink: 0;
}
.rc-detail-name {
  font-weight: 650;
  color: var(--m-navy);
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Card vật tư ── */
.rc-item-card { gap: 10px; }
.rc-item-code {
  font-size: 11px;
  color: var(--m-ink-3);
  font-family: monospace;
  margin-top: -6px;
}

/* ── Field hint SL PO ── */
.rc-field-hint {
  font-size: 11px;
  color: var(--m-ink-3);
  margin-left: 4px;
}

/* ── Input SL nhận — fontsizen lớn cho dễ gõ mobile ── */
.rc-input-qty {
  font-size: 20px;
  font-weight: 650;
  color: var(--m-navy);
  text-align: right;
}

/* ── Hàng quét lô ── */
.rc-scan-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.rc-scan-btn {
  flex-shrink: 0;
}
.rc-batch-val {
  font-family: monospace;
  letter-spacing: .02em;
}

/* ── Mono (PO ref) ── */
.rc-mono { font-family: monospace; }
</style>
