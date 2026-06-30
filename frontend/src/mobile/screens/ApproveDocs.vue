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
import MTopBar from '../ui/MTopBar.vue'
import MBadge from '../ui/MBadge.vue'
import MSkeleton from '../ui/MSkeleton.vue'
import MEmpty from '../ui/MEmpty.vue'
import MErrorState from '../ui/MErrorState.vue'
import MPullRefresh from '../ui/MPullRefresh.vue'
import { tapLight, notifySuccess } from '../native'

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
const hasError      = ref(false)
const noPermission  = ref(false)   // user thiếu quyền đọc loại phiếu đang chọn (403)

// Detail view
const activeDoc     = ref(null)
const detailLoading = ref(false)

// ── Computed ─────────────────────────────────────────────────────────────────
const activeConfig = computed(() => DOCTYPE_CONFIG[activeDoctype.value])

// ── Methods ──────────────────────────────────────────────────────────────────
async function loadList() {
  loading.value = true
  hasError.value = false
  noPermission.value = false
  rows.value = []
  try {
    const cfg = activeConfig.value
    rows.value = await getList(activeDoctype.value, {
      filters: cfg.filters,
      fields: cfg.fields,
      order_by: 'creation desc',
      limit: 50,
    })
  } catch (e) {
    // 403 = không có quyền đọc loại phiếu này (vd Storekeeper ↔ HĐ khung) →
    // hiện thông báo nhẹ nhàng, KHÔNG báo lỗi đỏ, KHÔNG retry vô ích.
    if (e.status === 403) {
      noPermission.value = true
    } else {
      hasError.value = true
      toast.error(e.message ?? 'Lỗi tải danh sách')
    }
  } finally {
    loading.value = false
  }
}

function selectDoctype(dt) {
  if (dt === activeDoctype.value && !activeDoc.value) return
  tapLight()
  activeDoctype.value = dt
  activeDoc.value = null
  loadList()
}

async function openDoc(name) {
  tapLight()
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
  notifySuccess()
  activeDoc.value = null
  await loadList()
}

// Init
loadList()
</script>

<template>
  <MPullRefresh :refreshing="loading" @refresh="loadList">

    <MTopBar title="Duyệt phiếu" sub="Phiếu chờ phê duyệt" />

    <div class="m-page">

      <!-- Chip selector doctype -->
      <div class="m-chips">
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

        <!-- Loading skeleton -->
        <MSkeleton v-if="loading" :count="4" />

        <!-- Không có quyền đọc loại phiếu này -->
        <MEmpty
          v-else-if="noPermission"
          icon="lock"
          title="Bạn không có quyền duyệt loại phiếu này"
          sub="Hãy chọn loại phiếu khác hoặc liên hệ quản trị viên."
        />

        <!-- Error state -->
        <MErrorState v-else-if="hasError" @retry="loadList" />

        <!-- List -->
        <ul v-else-if="rows.length" class="m-list">
          <li
            v-for="r in rows"
            :key="r.name"
            class="m-card m-card--tap m-rise"
            @click="openDoc(r.name)"
          >
            <div class="m-card__title">{{ r.name }}</div>
            <div class="m-card__row">
              <span>Ngày tạo</span>
              <b>{{ r.creation?.slice(0, 10) }}</b>
            </div>
            <div v-if="r.supplier" class="m-card__row">
              <span>Nhà cung cấp</span>
              <b>{{ r.supplier }}</b>
            </div>
            <div v-if="r.department" class="m-card__row">
              <span>Khoa/Phòng</span>
              <b>{{ r.department }}</b>
            </div>
            <div class="m-card__row" style="margin-top:4px">
              <MBadge :status="r.approval_stage || r.status" />
              <Icon name="chevron-right" :size="16" class="m-card__chev" />
            </div>
          </li>
        </ul>

        <!-- Empty -->
        <MEmpty
          v-else
          icon="clipboard-check"
          title="Không có phiếu chờ duyệt"
          sub="Tất cả phiếu đã được xử lý."
        />

      </template>

      <!-- ── DETAIL VIEW ───────────────────────────────────────────────── -->
      <template v-else>

        <!-- Back button -->
        <button class="m-btn m-btn--ghost m-btn--sm" style="align-self:flex-start" @click="back">
          <Icon name="arrow-left" :size="16" />
          Quay lại
        </button>

        <!-- Doc summary card -->
        <div class="m-card">
          <div class="m-card__title" style="font-size:16px;margin-bottom:8px">{{ activeDoc.name }}</div>
          <div v-if="activeDoc.creation" class="m-card__row">
            <span>Ngày tạo</span>
            <b>{{ activeDoc.creation?.slice(0, 10) }}</b>
          </div>
          <div v-if="activeDoc.supplier" class="m-card__row">
            <span>Nhà cung cấp</span>
            <b>{{ activeDoc.supplier }}</b>
          </div>
          <div v-if="activeDoc.department" class="m-card__row">
            <span>Khoa/Phòng</span>
            <b>{{ activeDoc.department }}</b>
          </div>
          <div v-if="activeDoc.approval_stage || activeDoc.status" class="m-card__row" style="margin-top:4px">
            <span>Trạng thái</span>
            <MBadge :status="activeDoc.approval_stage || activeDoc.status" />
          </div>
        </div>

        <!-- Loading indicator while fetching full doc -->
        <MSkeleton v-if="detailLoading" :count="2" />

        <!-- ActionPanel handles all approve/reject logic, arg prompts, and method calls -->
        <div v-else class="m-card" style="padding:0;overflow:hidden">
          <ActionPanel
            :doctype="activeDoctype"
            :doc="activeDoc"
            @after="onAfter"
          />
        </div>

      </template>

    </div>
  </MPullRefresh>
</template>
