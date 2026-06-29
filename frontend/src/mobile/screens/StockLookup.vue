<!-- frontend/src/mobile/screens/StockLookup.vue
     Màn hình tra cứu tồn kho / lô — mobile.

     LUỒNG TÌM KIẾM (một hành vi duy nhất, có thể dự đoán):
       1. Người dùng nhập text → nhấn Enter / nút tìm
       2. Tra SC Item với or_filters name/item_name LIKE %q%
       3. Nếu có kết quả → hiện danh sách vật tư để chọn
          Nếu không có kết quả → thử stock_balance({ batch: q }) trực tiếp (quét lô)
       4. Chọn vật tư → gọi stock_balance({ item }) → hiện thẻ lô FEFO
       5. Barcode scan → giống bước 2–4 (try item code trước, fallback sang batch)

     API thực:
       call('supplycore.api.frontend.stock_balance', { item?, warehouse?, batch? })
       getList('SC Item', { fields, or_filters, limit })

     Fields trả về từ stock_balance:
       item, item_name, warehouse, batch, qty, value,
       expiry_date (FEFO asc), qc_status, blocked, available
-->
<template>
  <div class="sl-page">
    <!-- Thanh tìm kiếm -->
    <div class="sl-search">
      <input
        v-model="q"
        class="sl-input"
        placeholder="Tên hoặc mã vật tư / lô"
        type="search"
        autocomplete="off"
        @keyup.enter="doSearch"
      />
      <button class="sl-btn-icon" :disabled="loading" @click="doSearch" title="Tìm">
        <Icon name="search" :size="20" />
      </button>
      <button class="sl-btn-icon" :disabled="loading" @click="onScan" title="Quét mã">
        <Icon name="scan" :size="20" />
      </button>
    </div>

    <!-- Trạng thái loading -->
    <p v-if="loading" class="sl-muted">Đang tải...</p>

    <!-- Danh sách vật tư (bước chọn) -->
    <template v-else-if="mode === 'items'">
      <p class="sl-hint">Chọn vật tư để xem tồn kho:</p>
      <ul class="sl-list">
        <li
          v-for="item in items"
          :key="item.name"
          class="sl-item-card"
          @click="selectItem(item)"
        >
          <div class="sl-item-code">{{ item.name }}</div>
          <div class="sl-item-name">{{ item.item_name || '' }}</div>
        </li>
      </ul>
      <p v-if="items.length === 0 && searched" class="sl-muted">Không tìm thấy vật tư.</p>
    </template>

    <!-- Kết quả tồn kho / lô -->
    <template v-else-if="mode === 'stock'">
      <div class="sl-back-row">
        <button class="sl-back-btn" @click="backToItems">
          <Icon name="arrow-left" :size="16" /> Quay lại
        </button>
        <span class="sl-selected-name">{{ selectedItem?.item_name || selectedItem?.name || '' }}</span>
      </div>

      <div v-if="stockRows.length === 0" class="sl-muted">Không có tồn kho.</div>
      <ul v-else class="sl-list">
        <li
          v-for="(r, i) in stockRows"
          :key="i"
          class="sl-stock-card"
          :class="{
            'sl-expired': isExpired(r.expiry_date),
            'sl-expiring': isExpiringSoon(r.expiry_date) && !isExpired(r.expiry_date),
          }"
        >
          <!-- Tên vật tư (hữu ích khi tìm theo lô — nhiều vật tư) -->
          <div class="sl-card-title">
            {{ r.item_name || r.item }}
            <span v-if="r.item_name" class="sl-card-code">{{ r.item }}</span>
          </div>
          <div class="sl-card-row">
            <span class="sl-label">Kho</span>
            <span class="sl-val">{{ r.warehouse }}</span>
          </div>
          <div class="sl-card-row">
            <span class="sl-label">Lô</span>
            <span class="sl-val sl-mono">{{ r.batch || '—' }}</span>
          </div>
          <div class="sl-card-row">
            <span class="sl-label">Tồn</span>
            <span class="sl-val sl-mono sl-qty">{{ fmtQty(r.qty) }}</span>
          </div>
          <div class="sl-card-row">
            <span class="sl-label">HSD</span>
            <span
              class="sl-val"
              :class="{
                'sl-text-danger': isExpired(r.expiry_date),
                'sl-text-warn': isExpiringSoon(r.expiry_date) && !isExpired(r.expiry_date),
              }"
            >
              {{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}
            </span>
          </div>
          <div class="sl-card-row">
            <span class="sl-label">KCS</span>
            <span class="sl-badge" :class="qcBadgeClass(r)">
              {{ qcLabel(r) }}
            </span>
          </div>
        </li>
      </ul>
    </template>

    <!-- Màn hình khởi đầu -->
    <p v-else class="sl-muted">Nhập tên / mã vật tư hoặc quét mã để tra cứu.</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Icon from '../../components/Icon.vue'
import { call, getList } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'

const toast = useToastStore()
const { scan } = useScanner()

const q         = ref('')
const loading   = ref(false)
const searched  = ref(false)
// mode: 'idle' | 'items' | 'stock'
const mode      = ref('idle')
const items     = ref([])          // kết quả getList SC Item
const stockRows = ref([])          // kết quả stock_balance
const selectedItem = ref(null)     // { name, item_name }

// ─── Helpers hiển thị ────────────────────────────────────────────────────────

function fmtQty(v) {
  if (v == null) return '0'
  return Number(v).toLocaleString('vi-VN')
}

function fmtDate(d) {
  if (!d) return '—'
  // d có thể là 'YYYY-MM-DD'
  const [y, m, day] = String(d).split('-')
  return `${day}/${m}/${y}`
}

function isExpired(d)  { return d && new Date(d) < new Date() }
function isExpiringSoon(d) {
  if (!d) return false
  const days = (new Date(d) - new Date()) / 86400000
  return days >= 0 && days < 30
}

function qcLabel(r) {
  if (r.blocked) return 'Khoá'
  return { Accepted: 'Đạt', Rejected: 'Không đạt', Pending: 'Chờ QC', Conditional: 'Có điều kiện' }[r.qc_status] || (r.qc_status || '—')
}

function qcBadgeClass(r) {
  if (r.blocked) return 'sl-badge--danger'
  switch (r.qc_status) {
    case 'Accepted':    return 'sl-badge--success'
    case 'Rejected':    return 'sl-badge--danger'
    case 'Conditional': return 'sl-badge--warn'
    default:            return 'sl-badge--neutral'   // Pending / null
  }
}

// ─── Tìm kiếm vật tư ─────────────────────────────────────────────────────────

async function doSearch() {
  const text = q.value.trim()
  if (!text) return
  loading.value = true
  searched.value = true
  mode.value = 'idle'
  items.value = []
  stockRows.value = []
  selectedItem.value = null

  try {
    // Tìm SC Item theo name (mã) HOẶC item_name (tên)
    const found = await getList('SC Item', {
      fields: ['name', 'item_name'],
      or_filters: [
        ['name',      'like', `%${text}%`],
        ['item_name', 'like', `%${text}%`],
      ],
      limit: 20,
    })

    if (found && found.length > 0) {
      if (found.length === 1) {
        // Tự động chọn luôn nếu chỉ có 1 kết quả
        await loadStock(found[0])
      } else {
        items.value = found
        mode.value = 'items'
      }
    } else {
      // Không tìm được vật tư → thử tìm theo mã lô (barcode/batch)
      await loadStockByBatch(text)
    }
  } catch (e) {
    toast.error(`Lỗi tìm kiếm: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function selectItem(item) {
  loading.value = true
  try {
    await loadStock(item)
  } finally {
    loading.value = false
  }
}

async function loadStock(item) {
  selectedItem.value = item
  const rows = await call('supplycore.api.frontend.stock_balance', {
    item: item.name,
    warehouse: null,
    batch: null,
  })
  stockRows.value = rows || []
  mode.value = 'stock'
}

async function loadStockByBatch(batchCode) {
  const rows = await call('supplycore.api.frontend.stock_balance', {
    item: null,
    warehouse: null,
    batch: batchCode,
  })
  if (rows && rows.length > 0) {
    selectedItem.value = { name: batchCode, item_name: `Lô: ${batchCode}` }
    stockRows.value = rows
    mode.value = 'stock'
  } else {
    items.value = []
    mode.value = 'items'   // hiện "Không tìm thấy"
    searched.value = true
  }
}

function backToItems() {
  if (items.value.length > 0) {
    mode.value = 'items'
  } else {
    mode.value = 'idle'
  }
  stockRows.value = []
  selectedItem.value = null
}

// ─── Barcode scan ─────────────────────────────────────────────────────────────

async function onScan() {
  const code = await scan()
  if (!code) {
    toast.warning('Không quét được mã. Kiểm tra quyền camera hoặc dùng trên thiết bị thật.')
    return
  }
  q.value = code
  await doSearch()
}
</script>

<style scoped>
.sl-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 16px;
}

/* ── Thanh tìm kiếm ── */
.sl-search {
  display: flex;
  gap: 8px;
  align-items: center;
}
.sl-input {
  flex: 1;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 15px;
  outline: none;
  color: #111827;
}
.sl-input:focus {
  border-color: #1F4E79;
  box-shadow: 0 0 0 2px rgba(31,78,121,.15);
}
.sl-btn-icon {
  flex-shrink: 0;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  padding: 0 12px;
  height: 42px;
  color: #1F4E79;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.sl-btn-icon:disabled { opacity: .45; cursor: not-allowed; }
.sl-btn-icon:active { background: #f3f4f6; }

/* ── Trạng thái / hint ── */
.sl-muted { color: #9ca3af; font-size: 13px; text-align: center; }
.sl-hint  { font-size: 12px; color: #6b7280; margin-bottom: 2px; }

/* ── Danh sách vật tư ── */
.sl-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }

.sl-item-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  cursor: pointer;
  background: #fff;
}
.sl-item-card:active { background: #f0f4f8; }
.sl-item-code { font-size: 12px; color: #6b7280; font-family: monospace; }
.sl-item-name { font-weight: 600; color: #1F4E79; font-size: 14px; margin-top: 2px; }

/* ── Hàng quay lại ── */
.sl-back-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sl-back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #2E75B6;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.sl-selected-name {
  font-weight: 600;
  color: #1F4E79;
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Thẻ lô tồn kho ── */
.sl-stock-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sl-stock-card.sl-expired  { border-left: 4px solid #ef4444; background: #fff5f5; }
.sl-stock-card.sl-expiring { border-left: 4px solid #f59e0b; background: #fffbeb; }

.sl-card-title {
  font-weight: 600;
  color: #1F4E79;
  font-size: 14px;
  margin-bottom: 6px;
}
.sl-card-code {
  font-family: monospace;
  font-size: 11px;
  color: #6b7280;
  margin-left: 6px;
}
.sl-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 1px 0;
}
.sl-label { color: #6b7280; }
.sl-val   { font-weight: 500; color: #111827; }
.sl-mono  { font-family: monospace; }
.sl-qty   { color: #1F4E79; font-weight: 700; }

.sl-text-danger { color: #dc2626; font-weight: 600; }
.sl-text-warn   { color: #d97706; font-weight: 600; }

/* ── Badge KCS ── */
.sl-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .01em;
}
.sl-badge--success { background: #dcfce7; color: #166534; }
.sl-badge--danger  { background: #fee2e2; color: #991b1b; }
.sl-badge--warn    { background: #fef9c3; color: #854d0e; }
.sl-badge--neutral { background: #f3f4f6; color: #374151; }
</style>
