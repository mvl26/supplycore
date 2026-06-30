<!-- frontend/src/mobile/screens/Receiving.vue
     Màn hình Tiếp nhận / Nhập kho — mobile (giao diện premium).

     LUỒNG:
       1. Danh sách phiếu SC Purchase Receipt ở trạng thái Draft (docstatus=0)
       2. Chọn phiếu → form chi tiết: danh sách vật tư (items[]), nhập SL nhận (qty),
          nhập Hạn dùng (expiry_date, bắt buộc), Ngày sản xuất (manufacturing_date, tuỳ chọn),
          quét lô NCC (supplier_batch_no)
       3. Xác nhận: validate client-side → updateDoc (ghi qty + expiry_date + ...) → submitDoc

     Field schema (SC Purchase Receipt Item):
       item, item_name, qty (SL nhận), po_qty (SL đặt hàng - tham chiếu),
       uom, rate, warehouse, supplier_batch_no, batch_no, manufacturing_date, expiry_date
-->
<template>
  <MPullRefresh :refreshing="current ? opening : loading" @refresh="onRefresh">
    <MTopBar title="Tiếp nhận" sub="Phiếu nhập chờ xử lý" />

    <div class="m-page">

      <!-- ── DANH SÁCH PHIẾU NHẬP CHỜ ── -->
      <template v-if="!current">
        <!-- Đang tải danh sách -->
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

        <!-- Danh sách — giữ hiển thị khi đang mở phiếu (opening=true) -->
        <template v-else>
          <!-- Banner nhỏ khi đang tải chi tiết phiếu: không ẩn list -->
          <div v-if="opening" class="rc-opening-bar">
            <span class="rc-opening-dot"></span>Đang tải phiếu...
          </div>
          <ul class="m-list">
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
          <div v-if="current.is_return" class="m-card__row">
            <span>Loại</span>
            <MBadge status="Warning" label="Hàng trả NCC" />
          </div>

          <!-- Phiếu KHÔNG có PO → backend bắt buộc 'Lý do không có PO' trước submit -->
          <label v-if="!current.purchase_order && !current.is_return" class="m-field" style="margin-top:8px">
            <span>
              Lý do không có PO <span class="rc-required">*</span>
              <span v-if="!String(current.no_po_reason || '').trim()" class="rc-inline-error">— bắt buộc</span>
            </span>
            <textarea
              v-model="current.no_po_reason"
              rows="2"
              class="m-input"
              :class="{ 'rc-input-error': !String(current.no_po_reason || '').trim() }"
              placeholder="VD: mua khẩn cấp / hàng mẫu thử…"
            ></textarea>
          </label>
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

            <!-- Hạn dùng — bắt buộc với dòng qty > 0, trừ hàng trả -->
            <label class="m-field">
              <span>
                Hạn dùng
                <span v-if="!current.is_return" class="rc-required">*</span>
                <span
                  v-if="Number(it.qty) > 0 && !it.expiry_date && !current.is_return"
                  class="rc-inline-error"
                >
                  — bắt buộc
                </span>
              </span>
              <input
                v-model="it.expiry_date"
                type="date"
                class="m-input"
                :class="{ 'rc-input-error': Number(it.qty) > 0 && !it.expiry_date && !current.is_return }"
              />
            </label>

            <!-- Ngày sản xuất — tuỳ chọn -->
            <label class="m-field">
              <span>Ngày sản xuất</span>
              <input
                v-model="it.manufacturing_date"
                type="date"
                class="m-input"
              />
            </label>

            <!-- Quét lô NCC → supplier_batch_no -->
            <div class="rc-scan-row">
              <button class="m-btn m-btn--ghost m-btn--sm rc-scan-btn" :disabled="scanning" @click="scanBatch(it)">
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
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { pushBack, popBack } from '../backHandler'
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
import { useScannerStore } from '../scanner'
import { useToastStore } from '../../stores/toast'
import { fmtDate } from '../../utils'

const DT = 'SC Purchase Receipt'

const rows      = ref([])
const current   = ref(null)
const loading   = ref(false)   // tải/làm mới danh sách
const opening   = ref(false)   // mở chi tiết phiếu (riêng — không ẩn list)
const saving    = ref(false)
const loadError = ref(null)

const { scan, scanning } = useScanner()
const toast    = useToastStore()

// Chốt thứ tự request danh sách (latest-wins)
let loadSeq = 0

// Theo dõi tên phiếu đang mở: bỏ kết quả cũ nếu người dùng đổi phiếu
let openingName = null

// ─── Pull-to-refresh ──────────────────────────────────────────────────────────

async function onRefresh() {
  if (current.value) {
    // Đang ở detail: làm mới chính phiếu đang xem, không tải lại list
    opening.value = true
    try {
      const doc = await getDoc(DT, current.value.name)
      current.value = doc
    } catch (e) {
      toast.error(`Lỗi làm mới: ${e.message}`)
    } finally {
      opening.value = false
    }
    return
  }
  await load()
}

// ─── Tải danh sách phiếu Draft ───────────────────────────────────────────────

async function load() {
  const tok = ++loadSeq
  loading.value = true
  loadError.value = null
  try {
    const result = await getList(DT, {
      filters: [['docstatus', '=', 0]],
      fields: ['name', 'supplier', 'supplier_name', 'to_warehouse', 'posting_date'],
      order_by: 'creation desc',
      limit: 50,
    })
    if (tok !== loadSeq) return   // bị request mới hơn thay thế
    rows.value = result
  } catch (e) {
    if (tok !== loadSeq) return
    loadError.value = e.message
    toast.error(`Lỗi tải danh sách: ${e.message}`)
  } finally {
    if (tok === loadSeq) loading.value = false
  }
}

// ─── Mở chi tiết phiếu ───────────────────────────────────────────────────────

async function open(name) {
  tapLight()
  // Đặt cờ trước khi await để không ẩn danh sách (không dùng loading)
  opening.value = true
  openingName = name
  try {
    const doc = await getDoc(DT, name)
    if (openingName !== name) return   // người dùng đã bấm phiếu khác
    current.value = doc
  } catch (e) {
    if (openingName === name) toast.error(`Lỗi tải phiếu: ${e.message}`)
  } finally {
    if (openingName === name) opening.value = false
  }
}

function backToList() {
  current.value = null
  openingName = null
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

// ─── Xác nhận nhận hàng: validate → update → submit ──────────────────────────

async function confirm() {
  if (saving.value) return

  const items = current.value.items || []
  const isReturn = !!current.value.is_return

  // Chuẩn hoá qty: '' hoặc NaN → 0
  items.forEach(it => {
    const n = Number(it.qty)
    it.qty = isNaN(n) ? 0 : n
  })

  // Kiểm tra ít nhất một dòng có qty > 0
  if (items.every(it => it.qty <= 0)) {
    toast.warning('Vui lòng nhập số lượng nhận cho ít nhất một dòng.')
    return
  }

  // Validate expiry_date — bắt buộc với mọi dòng qty > 0, không phải hàng trả
  if (!isReturn) {
    const missingExpiry = items
      .filter(it => it.qty > 0 && !it.expiry_date)
      .map(it => it.item_name || it.item)
    if (missingExpiry.length) {
      toast.warning(
        `Thiếu Hạn dùng cho ${missingExpiry.length > 1 ? 'các dòng' : 'dòng'}: ${missingExpiry.join(', ')}`
      )
      return
    }
  }

  // Phiếu không có PO → backend bắt buộc no_po_reason trước submit
  if (!current.value.purchase_order && !isReturn
      && !String(current.value.no_po_reason || '').trim()) {
    toast.warning("Phiếu không có PO — vui lòng nhập 'Lý do không có PO'.")
    return
  }

  saving.value = true
  try {
    // Ghi items (qty + expiry_date + supplier_batch_no + manufacturing_date)
    // + no_po_reason (nếu phiếu không có PO) rồi submit. Dùng save_doc + submit_doc
    // (đã deploy) để không phụ thuộc backend reload.
    await updateDoc(DT, current.value.name, {
      items: current.value.items,
      no_po_reason: current.value.no_po_reason || '',
    })
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

// ─── Vòng đời ─────────────────────────────────────────────────────────────────

onMounted(load)

// Nút Back cứng Android: khi đang xem chi tiết phiếu → đóng chi tiết (giữ dữ
// liệu đang nhập) thay vì thoát app. Đăng ký handler khi current mở.
watch(current, (v) => {
  if (v) pushBack(backToList)
  else popBack(backToList)
})

// Huỷ scanner + gỡ back handler khi rời màn.
onUnmounted(() => {
  useScannerStore().cancel()
  popBack(backToList)
})
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

/* ── Input SL nhận — fontsize lớn cho dễ gõ mobile ── */
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

/* ── Dấu * bắt buộc ── */
.rc-required {
  color: var(--m-danger, #dc2626);
  margin-left: 2px;
}

/* ── Cảnh báo inline thiếu hạn dùng ── */
.rc-inline-error {
  color: var(--m-danger, #dc2626);
  font-size: 11px;
  margin-left: 4px;
}

/* ── Input viền đỏ khi lỗi ── */
.rc-input-error {
  border-color: var(--m-danger, #dc2626) !important;
}

/* ── Banner đang mở phiếu (hiển thị ở đỉnh list, không ẩn list) ── */
.rc-opening-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--m-ink-2);
  background: var(--m-surface-2, #f3f4f6);
  border-radius: 8px;
  margin-bottom: 8px;
}

/* ── Chấm nhảy animation (thay spinner icon) ── */
.rc-opening-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--m-royal, #2E75B6);
  animation: rc-dot-pulse 1s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes rc-dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .4; transform: scale(.7); }
}
</style>
