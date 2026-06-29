<script setup>
/**
 * ApproveDocs.vue — Màn hình Duyệt/ký phiếu (mobile)
 *
 * Các doctype và bộ lọc được suy ra trực tiếp từ điều kiện `when` trong actions.js:
 *
 * - Framework Contract:
 *     approve_as_manager: when(d) => d.approval_stage === 'Manager Review'  (không check docstatus)
 *     approve_as_executive: when(d) => d.approval_stage === 'Executive Review' (không check docstatus)
 *     reject_approval: when(d) => ['Manager Review','Executive Review'].includes(d.approval_stage)
 *   → Bộ lọc: approval_stage IN ('Manager Review','Executive Review')
 *     + docstatus=0 thêm vào để tránh liệt kê HĐ đã nộp nhưng approval_stage chưa reset.
 *     (NB: predicates FC không check docstatus — đây là safety filter chủ động, khác với PO.)
 *
 * - SC Purchase Order:
 *     approve_as_manager: when(d) => d.docstatus===0 && d.approval_stage==='Manager Review'
 *     approve_as_executive: when(d) => d.docstatus===0 && d.approval_stage==='Executive Review'
 *     reject: when(d) => d.docstatus===0 && ['Manager Review','Executive Review'].includes(d.approval_stage)
 *   → Bộ lọc: docstatus=0 AND approval_stage IN ('Manager Review','Executive Review')
 *
 * - SC Material Request:
 *     approve: when(d) => d.docstatus===1 && (d.status==='Pending' || !d.status)
 *     reject:  when(d) => d.docstatus===1 && (d.status==='Pending' || !d.status)
 *   → Bộ lọc: docstatus=1 AND status='Pending'
 *     (NB: !d.status edge-case không phủ; MR không có status=null trong thực tế.)
 *
 * Scan toàn bộ actions.js để kiểm tra variant:'success' có cổng pending khác:
 *   - SC Inventory Count Sheet: make_stock_reconciliation → tạo SR, không phải approval
 *   - SC Purchase Receipt: make_credit_note → luồng return, không phải approval
 *   - SC Alert: mark_resolved → ghi nhận cảnh báo, không phải approval
 *   - SC Stock Reconciliation: chỉ có reject (danger), không có approve (success)
 *   → 3 doctype trên là TOÀN BỘ doctype có approval workflow.
 *
 * Hành động không phải duyệt trong ActionPanel:
 *   Với mỗi trạng thái pending, ActionPanel chỉ render approve + reject (các hành động
 *   khác bị gated bởi docstatus/stage khác → không pass when predicate → không hiện).
 *   Ví dụ FC@ManagerReview → submit_for_review không hiện (cần Draft/Rejected);
 *   make_material_request không hiện (cần docstatus=1 Active).
 *
 * Lưu ý: FC/PO phê duyệt Manager → approval_stage chuyển sang 'Executive Review'
 *   → doc vẫn nằm trong filter, sẽ xuất hiện lại sau khi reload (chờ Executive duyệt).
 */

import { ref, computed } from 'vue'
import { getList, getDoc } from '../../api'
import { useToastStore } from '../../stores/toast'
import ActionPanel from '../../components/ActionPanel.vue'
import Icon from '../../components/Icon.vue'

const toast = useToastStore()

// ── Doctype config ──────────────────────────────────────────────────────────
const DOCTYPE_CONFIG = {
  'Framework Contract': {
    label: 'HĐ khung',
    filters: [
      ['docstatus', '=', 0],
      ['approval_stage', 'in', ['Manager Review', 'Executive Review']],
    ],
    fields: ['name', 'creation', 'approval_stage', 'supplier'],
  },
  'SC Purchase Order': {
    label: 'Đơn mua',
    filters: [
      ['docstatus', '=', 0],
      ['approval_stage', 'in', ['Manager Review', 'Executive Review']],
    ],
    fields: ['name', 'creation', 'approval_stage', 'supplier'],
  },
  'SC Material Request': {
    label: 'Yêu cầu mua',
    filters: [
      ['docstatus', '=', 1],
      ['status', '=', 'Pending'],
    ],
    fields: ['name', 'creation', 'status', 'department'],
  },
}

const doctypeKeys = Object.keys(DOCTYPE_CONFIG)

// ── State ───────────────────────────────────────────────────────────────────
const activeDoctype = ref(doctypeKeys[0])
const rows          = ref([])
const loading       = ref(false)

// Detail view
const activeDoc     = ref(null)
const detailLoading = ref(false)

// ── Computed ─────────────────────────────────────────────────────────────────
const activeConfig = computed(() => DOCTYPE_CONFIG[activeDoctype.value])

// ── Methods ──────────────────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  rows.value = []
  try {
    const cfg = activeConfig.value
    rows.value = await getList(activeDoctype.value, {
      filters: cfg.filters,
      fields: cfg.fields,
      order_by: 'creation desc',
      limit_page_length: 50,
    })
  } catch (e) {
    toast.error(e.message ?? 'Lỗi tải danh sách')
  } finally {
    loading.value = false
  }
}

function selectDoctype(dt) {
  if (dt === activeDoctype.value && !activeDoc.value) return
  activeDoctype.value = dt
  activeDoc.value = null
  loadList()
}

async function openDoc(name) {
  detailLoading.value = true
  activeDoc.value = { name }   // placeholder so detail view renders immediately
  try {
    activeDoc.value = await getDoc(activeDoctype.value, name)
  } catch (e) {
    toast.error(e.message ?? 'Lỗi tải chi tiết')
    activeDoc.value = null
  } finally {
    detailLoading.value = false
  }
}

function back() {
  activeDoc.value = null
}

async function onAfter() {
  // Phiếu vừa được duyệt/từ chối → trở về danh sách và reload
  activeDoc.value = null
  await loadList()
}

// Init
loadList()
</script>

<template>
  <div class="m-approve">

    <!-- Doctype chip selector -->
    <div class="m-approve__tabs">
      <button
        v-for="dt in doctypeKeys"
        :key="dt"
        :class="['m-chip', dt === activeDoctype ? 'm-chip--on' : '']"
        @click="selectDoctype(dt)"
      >
        {{ DOCTYPE_CONFIG[dt].label }}
      </button>
    </div>

    <!-- ── LIST VIEW ─────────────────────────────────────────────────── -->
    <template v-if="!activeDoc">
      <div v-if="loading" class="m-state">
        <Icon name="loader" :size="18" class="m-spin" />
        Đang tải...
      </div>

      <ul v-else-if="rows.length" class="m-list">
        <li
          v-for="r in rows"
          :key="r.name"
          class="m-card"
          @click="openDoc(r.name)"
        >
          <div class="m-card__title">
            <Icon name="file-text" :size="14" />
            {{ r.name }}
          </div>
          <div class="m-card__row">
            <span>Ngày tạo</span>
            <b>{{ r.creation?.slice(0, 10) }}</b>
          </div>
          <div v-if="r.approval_stage" class="m-card__row">
            <span>Giai đoạn</span>
            <span class="m-badge">{{ r.approval_stage }}</span>
          </div>
          <div v-if="r.status" class="m-card__row">
            <span>Trạng thái</span>
            <span class="m-badge">{{ r.status }}</span>
          </div>
          <div v-if="r.supplier" class="m-card__row">
            <span>Nhà cung cấp</span>
            <b>{{ r.supplier }}</b>
          </div>
          <div v-if="r.department" class="m-card__row">
            <span>Khoa/Phòng</span>
            <b>{{ r.department }}</b>
          </div>
          <div class="m-card__arrow">
            <Icon name="chevron-right" :size="16" />
          </div>
        </li>
      </ul>

      <div v-else class="m-state m-state--empty">
        <Icon name="inbox" :size="32" />
        <p>Không có phiếu chờ duyệt.</p>
      </div>
    </template>

    <!-- ── DETAIL VIEW ───────────────────────────────────────────────── -->
    <template v-else>
      <button class="m-back" @click="back">
        <Icon name="arrow-left" :size="16" />
        Quay lại
      </button>

      <!-- Key fields summary -->
      <div class="m-card m-detail">
        <div class="m-detail__name">{{ activeDoc.name }}</div>
        <div v-if="activeDoc.creation" class="m-card__row">
          <span>Ngày tạo</span>
          <b>{{ activeDoc.creation?.slice(0, 10) }}</b>
        </div>
        <div v-if="activeDoc.approval_stage" class="m-card__row">
          <span>Giai đoạn</span>
          <span class="m-badge">{{ activeDoc.approval_stage }}</span>
        </div>
        <div v-if="activeDoc.status" class="m-card__row">
          <span>Trạng thái</span>
          <span class="m-badge">{{ activeDoc.status }}</span>
        </div>
        <div v-if="activeDoc.supplier" class="m-card__row">
          <span>Nhà cung cấp</span>
          <b>{{ activeDoc.supplier }}</b>
        </div>
        <div v-if="activeDoc.department" class="m-card__row">
          <span>Khoa/Phòng</span>
          <b>{{ activeDoc.department }}</b>
        </div>
      </div>

      <!-- Loading indicator while fetching full doc -->
      <div v-if="detailLoading" class="m-state">
        <Icon name="loader" :size="18" class="m-spin" />
        Đang tải chi tiết...
      </div>

      <!-- ActionPanel handles all approve/reject logic, arg prompts, and method calls -->
      <div v-else class="m-action-wrap">
        <ActionPanel
          :doctype="activeDoctype"
          :doc="activeDoc"
          @after="onAfter"
        />
      </div>
    </template>

  </div>
</template>

<style scoped>
.m-approve {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 2px;
}

/* ── Chips ── */
.m-approve__tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}
.m-approve__tabs::-webkit-scrollbar { display: none; }

.m-chip {
  white-space: nowrap;
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.m-chip--on {
  background: #1F4E79;
  color: #fff;
  border-color: #1F4E79;
}

/* ── List ── */
.m-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Card ── */
.m-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
  cursor: pointer;
  position: relative;
  transition: box-shadow 0.15s;
}
.m-card:active {
  box-shadow: 0 0 0 2px #2E75B633;
}
.m-card__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #1F4E79;
  margin-bottom: 6px;
  font-size: 14px;
}
.m-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #4b5563;
  padding: 3px 0;
}
.m-card__arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}

/* ── Badge ── */
.m-badge {
  background: #EFF6FF;
  color: #1F4E79;
  border: 1px solid #BFDBFE;
  border-radius: 4px;
  padding: 1px 7px;
  font-size: 12px;
  font-weight: 500;
}

/* ── State (loading / empty) ── */
.m-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-size: 13px;
  padding: 16px 0;
}
.m-state--empty {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 10px;
  color: #9ca3af;
}
.m-state--empty p {
  margin: 0;
  font-size: 14px;
}

/* Spin animation for loader icon */
@keyframes spin { to { transform: rotate(360deg); } }
.m-spin { animation: spin 1s linear infinite; }

/* ── Detail view ── */
.m-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1F4E79;
  font-size: 14px;
  font-weight: 500;
  background: none;
  border: none;
  padding: 4px 0;
  cursor: pointer;
}
.m-detail {
  cursor: default;
}
.m-detail__name {
  font-weight: 700;
  font-size: 15px;
  color: #1F4E79;
  margin-bottom: 8px;
  word-break: break-all;
}

/* ── ActionPanel wrapper ── */
.m-action-wrap {
  /* Constrain ActionPanel to mobile width; it may use Tailwind flex-wrap */
  overflow-x: hidden;
}
</style>
