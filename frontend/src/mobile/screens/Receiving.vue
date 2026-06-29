<!-- frontend/src/mobile/screens/Receiving.vue
     Màn hình Tiếp nhận / Nhập kho — mobile.

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
  <div class="rc-page">

    <!-- ── DANH SÁCH PHIẾU NHẬP CHỜ ── -->
    <template v-if="!current">
      <div class="rc-header">
        <span class="rc-title">Phiếu nhập chờ xử lý</span>
        <button class="rc-refresh-btn" :disabled="loading" @click="load" title="Tải lại">
          <Icon name="refresh" :size="18" />
        </button>
      </div>

      <p v-if="loading" class="rc-muted">Đang tải...</p>

      <p v-else-if="rows.length === 0" class="rc-muted">Không có phiếu nhập chờ.</p>

      <ul v-else class="rc-list">
        <li
          v-for="r in rows"
          :key="r.name"
          class="rc-card rc-card--clickable"
          @click="open(r.name)"
        >
          <div class="rc-card-title">{{ r.name }}</div>
          <div class="rc-card-row">
            <span class="rc-label">NCC</span>
            <span class="rc-val">{{ r.supplier_name || r.supplier || '—' }}</span>
          </div>
          <div class="rc-card-row">
            <span class="rc-label">Kho nhập</span>
            <span class="rc-val">{{ r.to_warehouse || '—' }}</span>
          </div>
          <div class="rc-card-row">
            <span class="rc-label">Ngày</span>
            <span class="rc-val">{{ fmtDate(r.posting_date) }}</span>
          </div>
        </li>
      </ul>
    </template>

    <!-- ── CHI TIẾT PHIẾU NHẬP ── -->
    <template v-else>
      <div class="rc-back-row">
        <button class="rc-back-btn" @click="backToList">
          <Icon name="arrow-left" :size="16" /> Danh sách
        </button>
        <span class="rc-detail-name">{{ current.name }}</span>
      </div>

      <div class="rc-detail-meta">
        <div class="rc-card-row">
          <span class="rc-label">NCC</span>
          <span class="rc-val">{{ current.supplier_name || current.supplier || '—' }}</span>
        </div>
        <div class="rc-card-row">
          <span class="rc-label">Kho nhập</span>
          <span class="rc-val">{{ current.to_warehouse || '—' }}</span>
        </div>
        <div v-if="current.purchase_order" class="rc-card-row">
          <span class="rc-label">PO</span>
          <span class="rc-val rc-mono">{{ current.purchase_order }}</span>
        </div>
        <div v-if="current.qc_required" class="rc-card-row">
          <span class="rc-label">QC</span>
          <span class="rc-badge rc-badge--warn">Yêu cầu KCS</span>
        </div>
      </div>

      <p v-if="!current.items || current.items.length === 0" class="rc-muted">
        Phiếu không có dòng vật tư.
      </p>

      <ul v-else class="rc-list">
        <li v-for="(it, i) in current.items" :key="i" class="rc-card rc-item-card">
          <!-- Tên vật tư -->
          <div class="rc-card-title">{{ it.item_name || it.item }}</div>
          <div v-if="it.item_name" class="rc-item-code">{{ it.item }}</div>

          <!-- SL nhận — field thực: qty -->
          <label class="rc-field">
            <span class="rc-field-label">
              SL nhận
              <span v-if="it.po_qty != null" class="rc-field-hint">(SL PO: {{ it.po_qty }})</span>
            </span>
            <input
              v-model.number="it.qty"
              type="number"
              inputmode="decimal"
              min="0"
              class="rc-input-qty"
              placeholder="0"
            />
          </label>

          <!-- Số lô NCC — supplier_batch_no -->
          <div class="rc-scan-row">
            <button class="rc-scan-btn" @click="scanBatch(it)">
              <Icon name="scan" :size="16" /> Quét lô NCC
            </button>
            <span v-if="it.supplier_batch_no" class="rc-batch-val rc-mono">
              {{ it.supplier_batch_no }}
            </span>
          </div>
        </li>
      </ul>

      <button
        class="rc-confirm-btn"
        :disabled="saving"
        @click="confirm"
      >
        <span v-if="saving">Đang xử lý...</span>
        <span v-else>Xác nhận nhận hàng</span>
      </button>
    </template>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Icon from '../../components/Icon.vue'
import { getList, getDoc, updateDoc, submitDoc } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'

const DT = 'SC Purchase Receipt'

const rows    = ref([])
const current = ref(null)
const loading = ref(false)
const saving  = ref(false)

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
  try {
    rows.value = await getList(DT, {
      filters: [['docstatus', '=', 0]],
      fields: ['name', 'supplier', 'supplier_name', 'to_warehouse', 'posting_date'],
      order_by: 'creation desc',
      limit: 50,
    })
  } catch (e) {
    toast.error(`Lỗi tải danh sách: ${e.message}`)
  } finally {
    loading.value = false
  }
}

// ─── Mở chi tiết phiếu ───────────────────────────────────────────────────────

async function open(name) {
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
  const code = await scan()
  if (code) {
    it.supplier_batch_no = code
  } else {
    toast.warning('Không quét được mã. Kiểm tra quyền camera hoặc dùng trên thiết bị thật.')
  }
}

// ─── Xác nhận nhận hàng: update → submit ──────────────────────────────────────

async function confirm() {
  if (saving.value) return
  saving.value = true
  try {
    // Ghi toàn bộ mảng items (giữ tất cả field, chỉ qty + supplier_batch_no được chỉnh)
    await updateDoc(DT, current.value.name, { items: current.value.items })
    await submitDoc(DT, current.value.name)
    toast.success('Đã xác nhận nhận hàng và cập nhật tồn kho.')
    current.value = null
    await load()
  } catch (e) {
    // Giữ ở detail view để người dùng có thể sửa và thử lại
    toast.error(`Lỗi xác nhận: ${e.message}`)
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.rc-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 20px;
}

/* ── Header danh sách ── */
.rc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rc-title {
  font-size: 16px;
  font-weight: 600;
  color: #1F4E79;
}
.rc-refresh-btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 6px 10px;
  color: #1F4E79;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.rc-refresh-btn:disabled { opacity: .45; cursor: not-allowed; }
.rc-refresh-btn:active { background: #f3f4f6; }

/* ── Trạng thái muted ── */
.rc-muted { color: #9ca3af; font-size: 13px; text-align: center; margin: 16px 0; }

/* ── Danh sách ── */
.rc-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }

/* ── Thẻ chung ── */
.rc-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rc-card--clickable { cursor: pointer; }
.rc-card--clickable:active { background: #f0f4f8; }

.rc-card-title {
  font-weight: 600;
  color: #1F4E79;
  font-size: 14px;
  margin-bottom: 4px;
}
.rc-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.rc-label { color: #6b7280; }
.rc-val   { font-weight: 500; color: #111827; }
.rc-mono  { font-family: monospace; }

/* ── Badge ── */
.rc-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}
.rc-badge--warn { background: #fef9c3; color: #854d0e; }

/* ── Quay lại ── */
.rc-back-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rc-back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #2E75B6;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.rc-detail-name {
  font-weight: 600;
  color: #1F4E79;
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Meta phiếu ── */
.rc-detail-meta {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 14px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ── Card vật tư ── */
.rc-item-card { gap: 8px; }
.rc-item-code { font-size: 11px; color: #6b7280; font-family: monospace; margin-top: -4px; }

/* ── Field SL nhận ── */
.rc-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rc-field-label {
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}
.rc-field-hint {
  font-size: 11px;
  color: #9ca3af;
}
.rc-input-qty {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 18px;
  font-weight: 600;
  color: #1F4E79;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}
.rc-input-qty:focus {
  border-color: #1F4E79;
  box-shadow: 0 0 0 2px rgba(31,78,121,.15);
}

/* ── Quét lô ── */
.rc-scan-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.rc-scan-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 8px 12px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  flex-shrink: 0;
}
.rc-scan-btn:active { background: #f3f4f6; }
.rc-batch-val {
  font-size: 13px;
  color: #1F4E79;
  font-weight: 600;
}

/* ── Nút xác nhận ── */
.rc-confirm-btn {
  background: #1F4E79;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
  width: 100%;
}
.rc-confirm-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}
.rc-confirm-btn:not(:disabled):active { background: #163d61; }
</style>
