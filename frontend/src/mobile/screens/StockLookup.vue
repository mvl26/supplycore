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
       expiry_date (FEFO asc), qc_status, blocked, available (boolean: Accepted+không khoá)
-->
<template>
  <MPullRefresh :refreshing="refreshing" @refresh="onPullRefresh">
    <MTopBar title="Tra cứu" sub="Tồn kho &amp; lô vật tư" />

    <div class="m-page">
      <!-- Thanh tìm kiếm premium -->
      <div class="sl-search-bar">
        <div class="sl-search-wrap">
          <Icon name="search" :size="18" class="sl-search-icon" />
          <input
            v-model="q"
            class="sl-search-input"
            placeholder="Tên hoặc mã vật tư / lô"
            aria-label="Tìm vật tư hoặc lô"
            type="search"
            autocomplete="off"
            inputmode="search"
            @keyup.enter="onSearch"
          />
        </div>
        <button
          class="sl-icon-btn"
          :disabled="loading || scanning"
          aria-label="Quét mã"
          @click="onScan"
        >
          <Icon name="scan" :size="20" />
        </button>
      </div>

      <!-- Skeleton khi đang tải -->
      <MSkeleton v-if="loading" :count="5" />

      <!-- Không có quyền tra cứu SC Item -->
      <MEmpty
        v-else-if="noPermission"
        icon="lock"
        title="Bạn không có quyền tra cứu"
        sub="Hãy liên hệ quản trị viên để được cấp quyền đọc vật tư."
      />

      <!-- Lỗi -->
      <MErrorState
        v-else-if="mode === 'error'"
        :title="errorTitle"
        :message="errorMsg"
        @retry="onRetry"
      />

      <!-- Danh sách vật tư (bước chọn) -->
      <template v-else-if="mode === 'items'">
        <p class="m-muted" style="margin-bottom:-4px">Chọn vật tư để xem tồn kho:</p>
        <ul v-if="items.length" class="m-list">
          <li
            v-for="item in items"
            :key="item.name"
            class="m-card m-card--tap m-rise"
            @click="onSelectItem(item)"
          >
            <div class="m-card__title">{{ item.item_name || item.name }}</div>
            <div class="sl-code">{{ item.name }}</div>
          </li>
        </ul>
        <MEmpty
          v-else
          icon="search"
          title="Không tìm thấy vật tư / lô"
          sub="Thử nhập mã lô hoặc tên đầy đủ"
        />
      </template>

      <!-- Kết quả tồn kho / lô -->
      <template v-else-if="mode === 'stock'">
        <div class="sl-back-row">
          <button class="m-btn m-btn--ghost m-btn--sm sl-back-btn" @click="onBack">
            <Icon name="arrow-left" :size="16" />Quay lại
          </button>
          <span class="sl-selected-name">{{ selectedItem?.item_name || selectedItem?.name || '' }}</span>
        </div>

        <MEmpty
          v-if="stockRows.length === 0"
          icon="package"
          title="Không có tồn kho"
          sub="Vật tư chưa có số lượng trong kho"
        />
        <template v-else>
          <!-- Tóm tắt khả dụng: chỉ hiện khi có lô không khả dụng -->
          <div v-if="availQty < totalQty" class="sl-avail-summary">
            Khả dụng: <strong>{{ fmtQty(availQty) }}</strong>
            &nbsp;/&nbsp;Tổng: {{ fmtQty(totalQty) }}
          </div>
          <ul class="m-list">
            <li
              v-for="(r, i) in stockRows"
              :key="i"
              class="m-card m-rise sl-stock-card"
              :class="{
                'sl-card--expired':           isExpired(r.expiry_date),
                'sl-card--expiring-critical': isExpiringSoonCritical(r.expiry_date) && !isExpired(r.expiry_date),
                'sl-card--expiring':          isExpiringSoon(r.expiry_date) && !isExpiringSoonCritical(r.expiry_date) && !isExpired(r.expiry_date),
              }"
              :style="{ animationDelay: `${i * 40}ms` }"
            >
              <div class="m-card__title">
                {{ r.item_name || r.item }}
                <span v-if="r.item_name" class="sl-code-inline">{{ r.item }}</span>
              </div>
              <div class="m-card__row">
                <span>Kho</span>
                <b>{{ r.warehouse }}</b>
              </div>
              <div class="m-card__row">
                <span>Lô</span>
                <b class="sl-mono">{{ r.batch || '—' }}</b>
              </div>
              <div class="m-card__row">
                <span>Tồn</span>
                <b class="sl-qty">{{ fmtQty(r.qty) }}</b>
              </div>
              <div class="m-card__row">
                <span>HSD</span>
                <b :class="{
                  'sl-text-danger': isExpired(r.expiry_date) || isExpiringSoonCritical(r.expiry_date),
                  'sl-text-warn':   isExpiringSoon(r.expiry_date) && !isExpiringSoonCritical(r.expiry_date) && !isExpired(r.expiry_date),
                }">{{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}</b>
              </div>
              <div class="m-card__row" style="margin-top:4px">
                <span>KCS</span>
                <span class="sl-badges">
                  <MBadge :status="r.qc_status" domain="qc" />
                  <MBadge v-if="r.blocked" status="Rejected" label="Khoá" />
                </span>
              </div>
            </li>
          </ul>
        </template>
      </template>

      <!-- Màn hình khởi đầu -->
      <MEmpty
        v-else
        icon="search"
        title="Tra cứu tồn kho"
        sub="Nhập tên hoặc mã vật tư, hoặc quét barcode lô"
      />
    </div>
  </MPullRefresh>
</template>

<script setup>
import { ref, computed } from 'vue'
import Icon from '../../components/Icon.vue'
import MTopBar from '../ui/MTopBar.vue'
import MBadge from '../ui/MBadge.vue'
import MSkeleton from '../ui/MSkeleton.vue'
import MEmpty from '../ui/MEmpty.vue'
import MErrorState from '../ui/MErrorState.vue'
import MPullRefresh from '../ui/MPullRefresh.vue'
import { call, getList } from '../../api'
import { useScanner } from '../useScanner'
import { useToastStore } from '../../stores/toast'
import { tapLight, notifyError } from '../native'

const toast = useToastStore()
const { scan, scanning } = useScanner()

const q            = ref('')
const loading      = ref(false)
const refreshing   = ref(false)
// mode: 'idle' | 'items' | 'stock' | 'error'
const mode         = ref('idle')
const items        = ref([])          // kết quả getList SC Item
const stockRows    = ref([])          // kết quả stock_balance
const selectedItem = ref(null)        // { name, item_name[, _isBatch: true] }
const errorTitle   = ref('')
const errorMsg     = ref('')
const lastQuery    = ref('')          // để pull-to-refresh chạy lại khi ở mode items/error
const noPermission = ref(false)       // getList SC Item trả 403

// Token tăng dần — chỉ áp kết quả của lần gọi mới nhất, bỏ qua kết quả cũ (race condition)
let reqId = 0

// ─── Computed tóm tắt tồn khả dụng ──────────────────────────────────────────

const totalQty = computed(() =>
  stockRows.value.reduce((s, r) => s + Number(r.qty || 0), 0)
)
const availQty = computed(() =>
  stockRows.value.filter(r => r.available).reduce((s, r) => s + Number(r.qty || 0), 0)
)

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

// Parse YYYY-MM-DD theo múi giờ địa phương — tránh new Date('YYYY-MM-DD') parse UTC
// và lệch ngày biên tại GMT+7 (trước 07:00 sáng ngày hết hạn bị tô đỏ nhầm)
function parseLocalDate(d) {
  if (!d) return null
  const [y, m, day] = String(d).split('-').map(Number)
  return new Date(y, m - 1, day)
}

function todayMidnight() {
  const t = new Date()
  t.setHours(0, 0, 0, 0)
  return t
}

function isExpired(d) {
  if (!d) return false
  return parseLocalDate(d) < todayMidnight()
}

// Cảnh báo gấp: hết hạn trong 30 ngày (ngưỡng nghiệp vụ mức cao)
function isExpiringSoonCritical(d) {
  if (!d) return false
  const ms = parseLocalDate(d) - todayMidnight()
  return ms >= 0 && ms <= 30 * 86400000
}

// Sắp hết hạn: trong 90 ngày (ngưỡng nghiệp vụ mức cảnh báo, bao gồm ≤30)
function isExpiringSoon(d) {
  if (!d) return false
  const ms = parseLocalDate(d) - todayMidnight()
  return ms >= 0 && ms <= 90 * 86400000
}

// ─── Core search logic ────────────────────────────────────────────────────────

async function doSearch(text, { showLoading = true } = {}) {
  // Chặn tái nhập: Enter nhiều lần nhanh khi đang hiện skeleton
  if (showLoading && loading.value) return

  const myId = ++reqId   // token của lần gọi này; nếu không khớp khi await xong thì bỏ kết quả

  if (showLoading) loading.value = true
  mode.value = 'idle'
  items.value = []
  stockRows.value = []
  selectedItem.value = null
  errorTitle.value = ''
  errorMsg.value = ''
  noPermission.value = false
  lastQuery.value = text

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
    if (myId !== reqId) return   // kết quả cũ bị thay thế bởi lần gọi mới hơn

    if (found && found.length > 0) {
      if (found.length === 1) {
        // Tự động chọn luôn nếu chỉ có 1 kết quả
        selectedItem.value = found[0]
        const rows = await call('supplycore.api.frontend.stock_balance', {
          item: found[0].name,
          warehouse: null,
          batch: null,
        })
        if (myId !== reqId) return
        stockRows.value = rows || []
        mode.value = 'stock'
      } else {
        items.value = found
        mode.value = 'items'
      }
    } else {
      // Không tìm được vật tư → thử tìm theo mã lô (barcode/batch)
      const rows = await call('supplycore.api.frontend.stock_balance', {
        item: null,
        warehouse: null,
        batch: text,
      })
      if (myId !== reqId) return
      if (rows && rows.length > 0) {
        selectedItem.value = { name: text, item_name: `Lô: ${text}`, _isBatch: true }
        stockRows.value = rows
        mode.value = 'stock'
      } else {
        items.value = []
        mode.value = 'items'   // hiện "Không tìm thấy"
      }
    }
  } catch (e) {
    if (myId !== reqId) return
    // 403: thiếu quyền đọc SC Item — hiện thông báo nhẹ, không hiện retry vô ích
    if (e.status === 403) {
      noPermission.value = true
    } else {
      errorTitle.value = 'Lỗi tìm kiếm'
      errorMsg.value = e.message || ''
      mode.value = 'error'
      toast.error(`Lỗi tìm kiếm: ${e.message}`)
    }
  } finally {
    if (showLoading && myId === reqId) loading.value = false
  }
}

// ─── Tìm kiếm từ UI ──────────────────────────────────────────────────────────

function onSearch() {
  const text = q.value.trim()
  if (!text || loading.value) return
  tapLight()
  doSearch(text)
}

async function onSelectItem(item) {
  tapLight()
  loading.value = true
  try {
    await loadStock(item)
  } catch (e) {
    errorTitle.value = 'Lỗi tải tồn kho'
    errorMsg.value = e.message || ''
    mode.value = 'error'
    toast.error(`Lỗi tải tồn kho: ${e.message}`)
  } finally {
    loading.value = false
  }
}

// Tải tồn kho theo vật tư — dùng cho onSelectItem và onPullRefresh (không concurrent với doSearch)
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

function onBack() {
  tapLight()
  if (items.value.length > 0) {
    mode.value = 'items'
  } else {
    mode.value = 'idle'
  }
  stockRows.value = []
  selectedItem.value = null
}

function onRetry() {
  tapLight()
  const text = lastQuery.value || q.value.trim()
  if (text) doSearch(text)
}

// ─── Pull-to-refresh ──────────────────────────────────────────────────────────

async function onPullRefresh() {
  refreshing.value = true
  try {
    if (mode.value === 'stock' && selectedItem.value) {
      // Đang xem tồn kho → làm mới đúng view, không doSearch lại (tránh nhảy về items list)
      const s = selectedItem.value
      if (s._isBatch) {
        // Lô được tìm trực tiếp qua mã lô
        const rows = await call('supplycore.api.frontend.stock_balance', {
          item: null, warehouse: null, batch: s.name,
        })
        stockRows.value = rows || []
      } else {
        await loadStock(s)
      }
    } else {
      const text = lastQuery.value || q.value.trim()
      if (!text) return
      await doSearch(text, { showLoading: false })
    }
  } catch (e) {
    toast.error(`Lỗi làm mới: ${e.message}`)
  } finally {
    refreshing.value = false
  }
}

// ─── Barcode scan ─────────────────────────────────────────────────────────────

async function onScan() {
  tapLight()
  try {
    const code = await scan()
    if (!code) return            // người dùng bấm Huỷ — không báo lỗi
    q.value = code
    await doSearch(code)
  } catch (e) {
    notifyError()
    toast.error(e.message || 'Không mở được camera quét mã.')
  }
}
</script>

<style scoped>
/* ── Thanh tìm kiếm premium ── */
.sl-search-bar {
  display: flex;
  gap: 10px;
  align-items: center;
}

.sl-search-wrap {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.sl-search-icon {
  position: absolute;
  left: 14px;
  color: var(--m-ink-3);
  pointer-events: none;
  z-index: 1;
}

.sl-search-input {
  width: 100%;
  border: 1px solid var(--m-line);
  border-radius: 12px;
  padding: 13px 14px 13px 42px;
  font-size: 16px;
  background: var(--m-card);
  color: var(--m-ink);
  outline: none;
  transition: border-color .12s, box-shadow .12s;
  -webkit-appearance: none;
}

.sl-search-input:focus {
  border-color: var(--m-royal);
  box-shadow: 0 0 0 3px rgba(46, 117, 182, .14);
}

/* ── Nút quét icon ── */
.sl-icon-btn {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border: 1px solid var(--m-line);
  border-radius: 12px;
  background: var(--m-card);
  color: var(--m-navy);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
  transition: background .1s, transform .1s;
}

.sl-icon-btn:active  { background: var(--m-tint); transform: scale(.95); }
.sl-icon-btn:disabled { opacity: .45; cursor: not-allowed; }

/* ── Mã vật tư (dòng phụ trong item list) ── */
.sl-code {
  font-size: 12px;
  color: var(--m-ink-3);
  font-family: 'JetBrains Mono', monospace;
  margin-top: 2px;
}

/* ── Nút quay lại + tên vật tư đã chọn ── */
.sl-back-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sl-back-btn {
  flex-shrink: 0;
}

.sl-selected-name {
  font-weight: 650;
  color: var(--m-navy);
  font-size: 14px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Tóm tắt khả dụng ── */
.sl-avail-summary {
  font-size: 13px;
  color: var(--m-ink-2);
  padding: 6px 2px 2px;
}

.sl-avail-summary strong {
  color: var(--m-ok);
  font-weight: 650;
}

/* ── Thẻ tồn kho / lô ── */
.sl-stock-card {
  border-left: 3px solid transparent;
  transition: border-left-color .15s;
}

.sl-card--expired           { border-left-color: var(--m-crit); background: var(--m-crit-bg); }
.sl-card--expiring-critical { border-left-color: var(--m-crit); background: var(--m-warn-bg); }
.sl-card--expiring          { border-left-color: var(--m-warn); background: var(--m-warn-bg); }

.sl-code-inline {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--m-ink-3);
  margin-left: 6px;
  font-weight: 400;
}

.sl-mono { font-family: 'JetBrains Mono', monospace; }

.sl-qty {
  color: var(--m-navy);
  font-weight: 750;
  font-size: 15px;
}

.sl-text-danger { color: var(--m-crit); font-weight: 650; }
.sl-text-warn   { color: var(--m-warn); font-weight: 650; }

/* ── Nhóm badge KCS ── */
.sl-badges {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}
</style>
