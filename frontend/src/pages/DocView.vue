<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDoc, submitDoc, cancelDoc, updateDoc, createDoc, call } from '../api'
import { DT } from '../modules'
import { FORM_SCHEMAS, QUICK_CREATE } from '../schemas'
import QuickCreateModal from '../components/QuickCreateModal.vue'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import ActionPanel from '../components/ActionPanel.vue'
import DocForm from '../components/DocForm.vue'
import RelatedDocs from '../components/RelatedDocs.vue'
import FefoPickGuide from '../components/FefoPickGuide.vue'
import WarehouseStockPanel from '../components/WarehouseStockPanel.vue'
import FetchUpstream from '../components/FetchUpstream.vue'
import RecallRecoveryPanel from '../components/RecallRecoveryPanel.vue'
import CountEntryPanel from '../components/CountEntryPanel.vue'
import IcsSummaryPanel from '../components/IcsSummaryPanel.vue'
import IrScopePanel from '../components/IrScopePanel.vue'
import RouteGuidePanel from '../components/RouteGuidePanel.vue'
import BarcodeDisplay from '../components/BarcodeDisplay.vue'
import FrameworkContractDetail from '../components/FrameworkContractDetail.vue'
import DetailViewGeneric from '../components/DetailViewGeneric.vue'
import { DETAIL_CONFIGS } from '../detail-configs'
import { useToastStore } from '../stores/toast'
import { fmtDate, fmtDateTime, fmtNumber } from '../utils'
import { statusLabel, isSubmittable } from '../modules'
import { fieldLabel } from '../i18n'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const doctype = computed(() => decodeURIComponent(route.params.dt))
const name = computed(() => decodeURIComponent(route.params.name))
const cfg = computed(() => DT[doctype.value])
const schema = computed(() => FORM_SCHEMAS[doctype.value])
const isNew = computed(() => name.value === 'new')

const doc = ref(null)
const loading = ref(false)
const saving = ref(false)
const editing = ref(false)
// L16: theo dõi thay đổi chưa lưu — chỉ hiện "Gửi duyệt" khi đã Lưu (sạch).
const dirty = ref(false)
watch(() => doc.value, () => { dirty.value = true })
async function markClean() { await nextTick(); dirty.value = false }
const batchItemName = ref('')   // tên vật tư của lô (fetch để in lên nhãn)
const docFormRef = ref(null)  // expose validate() từ DocForm để highlight field thiếu

const LINK_PENDING_KEY = 'sc-link-create-pending'
const LINK_RESULT_KEY  = 'sc-link-create-result'

// CR-03: state cho modal "Tạo nhanh" (không rời trang).
// target xác định nơi điền kết quả: top-level field hoặc dòng child.
const quickCreate = ref(null)  // { doctype, prefill, target: { childField?, rowIdx?, fieldName } }

async function load() {
  if (isNew.value) {
    // Init empty doc with defaults; childtable empty array
    doc.value = { doctype: doctype.value, docstatus: 0 }
    if (schema.value?.items) {
      doc.value[schema.value.items.field] = []
    }
    editing.value = true
    // Nếu đang trong vòng round-trip "+ Tạo mới Link" → prefill từ doc gốc
    try {
      const pending = JSON.parse(sessionStorage.getItem(LINK_PENDING_KEY) || 'null')
      if (pending && pending.newDoctype === doctype.value && pending.prefill) {
        doc.value = { ...doc.value, ...pending.prefill }
      }
    } catch (e) {}
    return
  }
  loading.value = true
  try {
    doc.value = await getDoc(doctype.value, name.value)
    // Lô: lấy tên vật tư (item_name) để in lên nhãn 50×30mm
    batchItemName.value = ''
    if (doctype.value === 'SC Batch' && doc.value?.item) {
      try {
        const r = await call('frappe.client.get_value', {
          doctype: 'SC Item', filters: { name: doc.value.item }, fieldname: 'item_name',
        })
        batchItemName.value = r?.item_name || ''
      } catch (e) {}
    }
    // Auto-edit khi draft → user khỏi phải bấm "Sửa"
    // Trừ khi đã duyệt 3-tier (approval_stage=Approved) → khoá sửa
    editing.value = doc.value.docstatus === 0
      && !isApprovalLocked(doc.value)
      && !!schema.value
    // Nếu vừa quay lại từ Tạo mới Link → patch field bằng record vừa tạo
    try {
      const result = JSON.parse(sessionStorage.getItem(LINK_RESULT_KEY) || 'null')
      if (result && result.returnPath && route.fullPath.startsWith(result.returnPath.split('?')[0])) {
        sessionStorage.removeItem(LINK_RESULT_KEY)
        doc.value = { ...doc.value, [result.field]: result.newName }
        editing.value = true
        toast.success(`Đã chọn ${result.field}: ${result.newName}`)
      }
    } catch (e) {}
    await markClean()
  } catch (e) {
    toast.error(`Không tải được: ${e.message}`)
    doc.value = null
  } finally {
    loading.value = false
  }
}

// Khi user bấm "+ Tạo mới" trên Link field → lưu state rồi navigate sang form new
// payload có thể là { field, search } (từ LinkAutocomplete khi không có kết quả)
async function onCreateNewLink(payload) {
  const field = payload?.field || payload
  const searchText = payload?.search || ''
  if (!field?.linkTo) return

  // CR-03: nếu doctype hỗ trợ quick-create → mở MODAL ngay (không rời trang).
  const qc = QUICK_CREATE[field.linkTo]
  if (qc) {
    const prefill = {}
    if (searchText && qc.prefillField) prefill[qc.prefillField] = searchText
    quickCreate.value = {
      doctype: field.linkTo,
      prefill,
      target: (payload && payload.childField != null)
        ? { childField: payload.childField, rowIdx: payload.rowIdx, fieldName: field.name }
        : { fieldName: field.name },
    }
    return
  }

  // Fallback (doctype chưa hỗ trợ quick-create, vd SC Batch): điều hướng + prefill cũ.
  const prefill = {}
  // UX-004: pre-fill tên/mã từ text user đã gõ trong dropdown search.
  // Map per-doctype field name chính (vd Item Group dùng group_name).
  const NAME_FIELD = {
    'SC Item Group': 'group_name', 'SC UOM': 'uom_name', 'SC Supplier': 'supplier_name',
    'SC Warehouse': 'warehouse_name', 'SC Department': 'department_name',
    'SC Item': 'item_name', 'SC Patient': 'patient_name',
    'SC GL Account': 'account_name',
  }
  if (searchText && NAME_FIELD[field.linkTo]) {
    prefill[NAME_FIELD[field.linkTo]] = searchText
  }
  // QI → SC Batch: prefill item, supplier (fetch từ PR nếu chưa có trên doc)
  if (doctype.value === 'SC Quality Inspection' && field.name === 'batch') {
    if (doc.value?.item) prefill.item = doc.value.item
    let supplier = doc.value?.supplier
    if (!supplier && doc.value?.purchase_receipt) {
      try {
        const res = await call('frappe.client.get_value', {
          doctype: 'SC Purchase Receipt',
          filters: { name: doc.value.purchase_receipt },
          fieldname: 'supplier',
        })
        supplier = res?.supplier
      } catch (e) {}
    }
    if (supplier) prefill.supplier = supplier
  }
  // PR rows / Stock Entry rows có thể mở rộng sau
  sessionStorage.setItem(LINK_PENDING_KEY, JSON.stringify({
    returnPath: route.fullPath,
    field: field.name,
    newDoctype: field.linkTo,
    prefill,
  }))
  router.push(`/doc/${encodeURIComponent(field.linkTo)}/new`)
}

// CR-03: bản ghi vừa tạo nhanh → tự điền vào đúng trường (top-level hoặc dòng
// child) + tự điền các cột phụ fetchFrom (vd item_name, supplier_name) ngay từ
// doc vừa tạo (đã có đủ field), không cần round-trip thêm.
function onQuickCreated({ name, doc: created }) {
  const qc = quickCreate.value
  quickCreate.value = null
  if (!qc || !name || !doc.value) return
  const t = qc.target
  if (t.childField != null) {
    // Child: cột nào có fetchFrom.source === field vừa set → lấy target_field từ doc mới
    const cols = schema.value?.items?.columns || []
    const companions = {}
    for (const c of cols) {
      if (c.fetchFrom && c.fetchFrom.source === t.fieldName) {
        const v = created?.[c.fetchFrom.target_field]
        if (v != null) companions[c.name] = v
      }
    }
    const arr = Array.isArray(doc.value[t.childField]) ? [...doc.value[t.childField]] : []
    if (arr[t.rowIdx]) {
      arr[t.rowIdx] = { ...arr[t.rowIdx], [t.fieldName]: name, ...companions }
      doc.value = { ...doc.value, [t.childField]: arr }
    }
  } else {
    // Top-level: field vừa set tự khai fetchFrom → set doc[target_field]
    const companions = {}
    const f = findHeaderField(t.fieldName)
    if (f?.fetchFrom) {
      const v = created?.[f.fetchFrom.target_field]
      if (v != null) companions[f.fetchFrom.target_field] = v
    }
    doc.value = { ...doc.value, [t.fieldName]: name, ...companions }
  }
}

function findHeaderField(fieldName) {
  for (const sec of (schema.value?.sections || [])) {
    for (const f of (sec.fields || [])) {
      if (f.name === fieldName) return f
    }
  }
  return null
}

watch(() => route.fullPath, load)
onMounted(load)

// Merge data từ FetchUpstream → đè header field + replace items
function onUpstreamMerge({ header, items, source }) {
  if (!doc.value) return
  const next = { ...doc.value, ...(header || {}) }
  // Child table: nếu schema có items field → set; nếu form chưa có items array → init
  const itemsField = schema.value?.items?.field || 'items'
  if (Array.isArray(items) && items.length) {
    const existing = Array.isArray(next[itemsField]) ? next[itemsField] : []
    // Nếu user đã thêm vài dòng → append; nếu rỗng → thay
    if (existing.filter(r => r && Object.keys(r).length > 1).length === 0) {
      next[itemsField] = items
    } else {
      next[itemsField] = [...existing, ...items]
    }
  }
  // Lưu meta source để hiển thị badge
  if (source?.name) {
    next._upstream_source = `${source.doctype} ${source.name}`
  }
  doc.value = next
}

// WarehouseStockPanel (TR / SE): điền các dòng tồn kho đã tích → bảng chi tiết
async function onStockFill(picked) {
  if (!doc.value || !Array.isArray(picked) || !picked.length) return
  const itemsField = schema.value?.items?.field || 'items'
  // TR dùng requested_qty, SE dùng qty
  const qtyField = doctype.value === 'SC Transfer Request' ? 'requested_qty' : 'qty'
  const items = Array.isArray(doc.value[itemsField]) ? [...doc.value[itemsField]] : []
  const seen = new Set(items.map(r => `${r.item}|${r.batch || ''}`))

  // ĐVT theo vật tư — ưu tiên uom panel trả về; thiếu thì tra SC Item.uom
  const uomMap = {}
  const needUom = [...new Set(picked.filter(r => !r.uom && r.item).map(r => r.item))]
  await Promise.all(needUom.map(async (it) => {
    try {
      const d = await call('frappe.client.get_value', {
        doctype: 'SC Item', filters: { name: it }, fieldname: 'uom',
      })
      uomMap[it] = d?.uom || null
    } catch (e) { uomMap[it] = null }
  }))

  let added = 0
  for (const r of picked) {
    const k = `${r.item}|${r.batch || ''}`
    if (seen.has(k)) continue   // bỏ qua dòng item+lô đã có
    seen.add(k)
    const row = {
      item: r.item,
      uom: r.uom || uomMap[r.item] || null,   // ĐVT theo vật tư
      batch: r.batch || null,
    }
    row[qtyField] = r.qty
    items.push(row)
    added++
  }
  doc.value = { ...doc.value, [itemsField]: items }
  if (added) toast.success(`Đã điền ${added} dòng vào bảng chi tiết`)
  else toast.warning('Các dòng đã chọn đã có trong bảng chi tiết')
}

const statusBadge = computed(() => {
  if (!doc.value) return null
  const ds = doc.value.docstatus
  if (ds === 1) return { text: 'Đã gửi', cls: 'sc-badge-success' }
  if (ds === 2) return { text: 'Đã huỷ', cls: 'sc-badge-critical' }
  return { text: 'Nháp', cls: 'sc-badge-neutral' }
})

// Tài liệu đã qua 3-tier (stage=Approved) thì khoá sửa — chỉ submit hoặc reject
function isApprovalLocked(d) {
  if (!d) return false
  if (d.approval_stage === 'Approved' && (d.docstatus ?? 0) === 0) return true
  return false
}
const approvalLocked = computed(() => isApprovalLocked(doc.value))

// === Lịch sử sửa (Version diffs) ===
const editLog = ref([])
const editLogLoading = ref(false)
const editLogExpanded = ref(false)          // section thu gọn mặc định
const expandedVersions = ref(new Set())     // các log entry đang mở chi tiết
const editLogLoaded = ref(false)

async function loadEditLog() {
  if (isNew.value || !doc.value?.name) return
  editLogLoading.value = true
  try {
    editLog.value = await call('supplycore.api.frontend.get_doc_versions', {
      doctype: doctype.value, name: doc.value.name, limit: 50,
    }) || []
    editLogLoaded.value = true
  } catch (e) { editLog.value = [] }
  finally { editLogLoading.value = false }
}
// Reset khi đổi doc — chỉ tải log khi user mở section (lazy)
watch(() => doc.value?.name, () => {
  editLog.value = []
  editLogLoaded.value = false
  editLogExpanded.value = false
  expandedVersions.value = new Set()
})

function toggleEditLog() {
  editLogExpanded.value = !editLogExpanded.value
  if (editLogExpanded.value && !editLogLoaded.value) loadEditLog()
}
function toggleVersion(name) {
  const s = new Set(expandedVersions.value)
  s.has(name) ? s.delete(name) : s.add(name)
  expandedVersions.value = s
}

function fmtVal(v) {
  if (v == null) return '—'
  if (typeof v === 'object') return JSON.stringify(v).slice(0, 60)
  return String(v).slice(0, 80)
}

// Tên field thân thiện (child table notation giữ nguyên dạng rút gọn)
function fieldDisplay(f) {
  if (!f) return ''
  if (f.startsWith('+ ') || f.startsWith('- ')) return f
  if (f.includes('[')) {
    // vd "items[0].qty" → "Chi tiết #1 · qty"
    const m = f.match(/^(\w+)\[(\d+)\]\.(.+)$/)
    if (m) return `${fieldLabel(m[1])} #${Number(m[2]) + 1} · ${fieldLabel(m[3])}`
    return f
  }
  return fieldLabel(f)
}

// Tóm tắt 1 dòng cho mỗi version
function changeSummary(v) {
  const labels = (v.changed || []).map(c => fieldDisplay(c.field))
  const shown = labels.slice(0, 3).join(', ')
  const more = labels.length > 3 ? ` +${labels.length - 3}` : ''
  return `${labels.length} thay đổi — ${shown}${more}`
}
function fmtLogTime(s) {
  try { return fmtDateTime(s) } catch (e) { return s }
}

// === Barcode quét được (SC Batch / Bin Location) ===
const barcodeInfo = computed(() => {
  const d = doc.value
  if (!d || isNew.value) return null
  if (doctype.value === 'SC Batch') {
    const v = d.barcode || d.batch_id
    if (!v) return null
    // Nhãn lô: mã vạch (kèm mã barcode) + tên vật tư + HSD
    return {
      value: v,
      title: batchItemName.value || d.item || '',
      subtitle: d.expiry_date ? `HSD: ${d.expiry_date}` : '',
    }
  }
  if (doctype.value === 'Bin Location') {
    const v = d.barcode || d.bin_code
    if (!v) return null
    return { value: v, title: `Vị trí: ${d.bin_code || d.name}`,
             subtitle: [d.warehouse, d.zone].filter(Boolean).join(' · ') }
  }
  return null
})

function validateRequired() {
  const s = schema.value
  if (!s) return null
  const missing = []
  for (const sec of s.sections || []) {
    for (const f of sec.fields) {
      if (!f.required) continue
      const v = doc.value?.[f.name]
      if (v === undefined || v === null || v === '') missing.push(f.label || f.name)
    }
  }
  if (s.items) {
    const rows = doc.value?.[s.items.field] || []
    rows.forEach((row, i) => {
      for (const c of s.items.columns || []) {
        if (!c.required) continue
        const v = row?.[c.name]
        if (v === undefined || v === null || v === '') missing.push(`${s.items.label} dòng ${i + 1}: ${c.label || c.name}`)
      }
    })
    if (!rows.length && s.items.requiredRows) missing.push(`${s.items.label} cần ≥1 dòng`)
  }
  return missing.length ? missing : null
}

async function save() {
  // UX-005: gọi DocForm.validate() để highlight border đỏ + scroll
  if (docFormRef.value?.validate && !docFormRef.value.validate()) return
  const missing = validateRequired()
  if (missing) {
    toast.error(`Thiếu trường bắt buộc: ${missing.join(', ')}`)
    return
  }
  saving.value = true
  try {
    if (isNew.value) {
      const payload = { ...doc.value, doctype: doctype.value }
      const created = await createDoc(doctype.value, payload)
      toast.success(`Đã tạo ${created.name}`)
      // Nếu đang round-trip "+ Tạo mới Link" → quay lại form gốc, patch field
      let pending = null
      try { pending = JSON.parse(sessionStorage.getItem(LINK_PENDING_KEY) || 'null') } catch (e) {}
      if (pending && pending.newDoctype === doctype.value) {
        sessionStorage.removeItem(LINK_PENDING_KEY)
        sessionStorage.setItem(LINK_RESULT_KEY, JSON.stringify({
          returnPath: pending.returnPath,
          field: pending.field,
          newName: created.name,
        }))
        router.replace(pending.returnPath)
        return
      }
      router.replace(`/doc/${encodeURIComponent(doctype.value)}/${encodeURIComponent(created.name)}`)
    } else {
      // Send only the changed payload; Frappe handles partial update
      await updateDoc(doctype.value, name.value, doc.value)
      toast.success('Đã lưu')
      await load()  // load() sẽ tự bật editing nếu vẫn là draft
    }
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

// Sau submit thì điều hướng tới trang phù hợp với UC
// PR: KHÔNG auto-nav — phải QC xong, user tự bấm "Xếp hàng lên kệ" ở ActionPanel.
const POST_SUBMIT_NAV = {
  'SC Stock Entry': (d) => d?.docstatus === 1 && d.to_warehouse
    ? { path: '/putaway', query: { warehouse: d.to_warehouse } } : null,
}

async function doSubmit() {
  if (!doc.value?.name) return
  if (!confirm('Gửi bản ghi này vào quy trình duyệt? Sau khi gửi, bản ghi sẽ KHÔNG sửa được trừ khi Huỷ duyệt.')) return
  saving.value = true
  try {
    await submitDoc(doctype.value, name.value)
    toast.success('Đã gửi duyệt')
    await load()
    const navFn = POST_SUBMIT_NAV[doctype.value]
    const nav = navFn?.(doc.value)
    if (nav) {
      toast.success('Chuyển sang xếp hàng lên kệ...')
      router.push(nav)
    }
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

async function doCancel() {
  if (!confirm('Hủy bản ghi này?')) return
  saving.value = true
  try {
    await cancelDoc(doctype.value, name.value)
    toast.success('Đã hủy')
    await load()
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

function backToList() {
  router.push(`/list/${encodeURIComponent(doctype.value)}`)
}

// Group fields for display (read-only mode)
const fieldGroups = computed(() => {
  if (!doc.value) return { main: [], items: [] }
  const main = [], items = []
  const skip = new Set(['doctype', 'docstatus', 'owner', 'creation', 'modified', 'modified_by',
    'idx', 'parent', 'parentfield', 'parenttype', '_user_tags', '_comments', '_assign', '_liked_by', 'name'])
  for (const [k, v] of Object.entries(doc.value)) {
    if (skip.has(k)) continue
    if (Array.isArray(v)) items.push({ key: k, value: v })
    else main.push({ key: k, value: v })
  }
  return { main, items }
})

const STATUS_KEYS = new Set([
  'status', 'qc_status', 'overall_status', 'severity', 'request_type',
  'warehouse_type', 'department_type', 'count_type', 'recall_type',
  'investigation_type', 'variance_reason', 'payment_method',
  'bhyt_type', 'entry_type', 'alert_type', 'approval_stage',
])

function displayField(value, key) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 100)
  if (/_date$/.test(key) && value) return fmtDate(value)
  if (/_at$/.test(key) && value) return fmtDateTime(value)
  if (STATUS_KEYS.has(key) && typeof value === 'string') return statusLabel(value, key)
  if (/value|amount|total|cost|rate/.test(key) && typeof value === 'number') {
    return fmtNumber(value)
  }
  if (value === 1) return 'Có'
  if (value === 0) return ''
  return value
}
</script>

<template>
  <div v-if="!cfg" class="sc-card p-10 text-center text-sc-text-muted">
    DocType {{ doctype }} không hỗ trợ
  </div>
  <div v-else-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải...</div>
  <div v-else-if="!doc" class="sc-card p-10 text-center text-sc-text-muted">
    Không tìm thấy {{ doctype }} {{ name }}
  </div>
  <div v-else>
    <PageHeader
      :title="isNew ? `Tạo ${cfg.label}` : `${cfg.label} ${doc.name || ''}`"
      :icon="cfg.icon" :code="doctype"
      :subtitle="isNew ? 'Bản ghi mới — điền form và lưu' :
        `Cập nhật: ${doc.modified ? fmtDateTime(doc.modified) : ''}`">
      <template #actions>
        <button @click="backToList" class="sc-btn-secondary text-sm"><Icon name="chevron-left" :size="14" /> Danh sách</button>
        <span v-if="statusBadge && !isNew" :class="['sc-badge', statusBadge.cls]">{{ statusBadge.text }}</span>

        <template v-if="isNew">
          <button @click="save" :disabled="saving" class="sc-btn-primary text-sm">
            <template v-if="saving">Đang lưu...</template>
            <template v-else><Icon name="save" :size="14" /> Lưu</template>
          </button>
        </template>
        <template v-else-if="editing">
          <button @click="load" class="sc-btn-secondary text-sm"><Icon name="refresh-ccw" :size="14" /> Hoàn tác</button>
          <button @click="save" :disabled="saving" class="sc-btn-primary text-sm">
            <template v-if="saving">Đang lưu...</template>
            <template v-else><Icon name="save" :size="14" /> Lưu</template>
          </button>
          <button v-if="doc.docstatus === 0 && isSubmittable(doctype) && !dirty" @click="doSubmit"
            :disabled="saving" class="bg-sc-success hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm"
            title="Gửi bản ghi vào quy trình duyệt. Sau khi gửi sẽ không sửa được trừ khi Huỷ duyệt.">
            <Icon name="upload" :size="14" /> Gửi duyệt
          </button>
          <span v-else-if="doc.docstatus === 0 && isSubmittable(doctype) && dirty"
            class="text-xs text-sc-text-muted self-center italic">Lưu để hiện nút Gửi duyệt</span>
        </template>
        <template v-else>
          <!-- Đã duyệt 3-tier nhưng chưa Submit → cho Submit kích hoạt -->
          <button v-if="approvalLocked" @click="doSubmit"
            :disabled="saving" class="bg-sc-success hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm">
            <template v-if="saving">Đang gửi...</template>
            <template v-else><Icon name="upload" :size="14" /> Submit kích hoạt</template>
          </button>
          <button v-if="doc.docstatus === 1" @click="doCancel"
            :disabled="saving" class="bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm">
            Hủy
          </button>
        </template>
      </template>
    </PageHeader>

    <!-- Action panel — hiển thị cả khi draft-editing để user gọi action (vd Gửi duyệt FC) -->
    <ActionPanel v-if="!isNew && doc?.name" :doctype="doctype" :doc="doc" @after="load" />

    <!-- Mã vạch quét được — SC Batch / Bin Location -->
    <BarcodeDisplay v-if="barcodeInfo" :value="barcodeInfo.value"
      :title="barcodeInfo.title" :subtitle="barcodeInfo.subtitle" />

    <!-- M10 Recall Notice: panel theo dõi thu hồi với inline edit per row -->
    <RecallRecoveryPanel v-if="doctype === 'SC Recall Notice' && !isNew && doc?.name"
      :doctype="doctype" :doc="doc" @after="load" />

    <!-- M9 ICS: tổng quan kiểm kê + phiếu đếm in -->
    <IcsSummaryPanel v-if="doctype === 'SC Inventory Count Sheet' && !isNew && doc?.name"
      :doctype="doctype" :doc="doc" />

    <!-- M9 ICS: bảng nhập đếm nhanh (chỉ hiện khi draft) -->
    <CountEntryPanel v-if="doctype === 'SC Inventory Count Sheet' && !isNew && doc?.name && doc.docstatus === 0"
      :doctype="doctype" :doc="doc" @after="load" />

    <!-- M10 Investigation Report: scope hint + variance display -->
    <IrScopePanel v-if="doctype === 'SC Investigation Report' && !isNew && doc?.name"
      :doc="doc" />

    <!-- Bản đồ chỉ đường: Chuyển kho / Cấp phát / Vị trí lưu trữ -->
    <RouteGuidePanel v-if="!isNew && doc?.name" :doctype="doctype" :doc="doc" />

    <!-- Banner: HĐ đã duyệt 3-tier → khoá sửa -->
    <div v-if="approvalLocked"
      class="sc-card border-l-4 border-sc-success bg-green-50 px-4 py-3 mb-4 text-sm">
      <div class="font-semibold text-sc-navy"><Icon name="lock" :size="16" /> Hợp đồng đã được duyệt — đã khoá sửa</div>
      <div class="text-sc-text-muted mt-1">
        HĐ đã qua đủ 3-tier (Kế toán → Quản lý → Lãnh đạo). Bấm <b>Submit</b> để kích hoạt,
        hoặc <b>Reject</b> để gửi lại Kế toán điều chỉnh.
      </div>
    </div>

    <!-- Stock-aware widget chung -->
    <WarehouseStockPanel v-if="['SC Transfer Request', 'SC Stock Entry'].includes(doctype) && doc.from_warehouse"
      :warehouse="doc.from_warehouse"
      :selectable="isNew || editing"
      :title="isNew || editing ? 'Chọn tồn kho nguồn — tích để điền vào bảng chi tiết' : 'Tồn kho nguồn'"
      @fill="onStockFill" />
    <template v-if="doctype === 'SC Patient Dispensing' && doc.items?.length">
      <FefoPickGuide v-for="(it, i) in doc.items.filter(it => it.item && it.warehouse && it.qty)"
        :key="`fefo-${i}`" :item="it.item" :warehouse="it.warehouse" :qtyNeeded="it.qty" />
    </template>

    <!-- New / Edit mode → DocForm -->
    <template v-if="isNew || editing">
      <!-- Fetch upstream — chỉ hiện ở form New để pull data từ doc cha -->
      <FetchUpstream v-if="isNew" :target-doctype="doctype" @merge="onUpstreamMerge" />
      <DocForm ref="docFormRef" v-model="doc" :doctype="doctype" @submit="save" @create-new="onCreateNewLink" />
      <div v-if="!schema" class="sc-card p-6 text-center">
        <p class="text-sc-text-muted">Form schema chưa được định nghĩa cho {{ doctype }}.</p>
      </div>
    </template>

    <!-- CR-03: modal Tạo nhanh bản ghi tham chiếu (NCC, Vật tư, Kho, BN, Khoa…) -->
    <QuickCreateModal v-if="quickCreate"
      :doctype="quickCreate.doctype" :prefill="quickCreate.prefill"
      @created="onQuickCreated" @close="quickCreate = null" />

    <!-- View mode (chỉ khi đã submit hoặc cancel — không phải draft) -->
    <template v-else>

      <!-- Framework Contract: bố cục riêng — hero + timeline + value tiles + items totals -->
      <FrameworkContractDetail v-if="doctype === 'Framework Contract'" :doc="doc" class="mb-4" />

      <!-- 11 doctype khác: config-driven generic detail view -->
      <DetailViewGeneric v-else-if="DETAIL_CONFIGS[doctype]"
        :doctype="doctype" :doc="doc" class="mb-4" />

      <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div class="sc-card p-5">
          <h3 class="font-semibold text-sc-navy mb-3">Thông tin chính</h3>
          <dl class="space-y-2 text-sm">
            <div v-for="f in fieldGroups.main.slice(0, 12)" :key="f.key"
              class="grid grid-cols-[140px_1fr] gap-2">
              <dt class="text-sc-text-muted truncate">{{ fieldLabel(f.key) }}</dt>
              <dd class="text-sc-text font-medium break-all">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </dl>
        </div>
        <div v-if="fieldGroups.main.length > 12" class="sc-card p-5">
          <h3 class="font-semibold text-sc-navy mb-3">Chi tiết khác</h3>
          <dl class="space-y-2 text-sm">
            <div v-for="f in fieldGroups.main.slice(12)" :key="f.key"
              class="grid grid-cols-[140px_1fr] gap-2">
              <dt class="text-sc-text-muted truncate">{{ fieldLabel(f.key) }}</dt>
              <dd class="text-sc-text font-medium break-all">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div v-for="child in fieldGroups.items" :key="child.key" class="sc-card p-5 mb-4">
        <h3 class="font-semibold text-sc-navy mb-3">{{ fieldLabel(child.key) }} ({{ child.value.length }})</h3>
        <div v-if="child.value.length === 0" class="text-sm text-sc-text-muted">Chưa có dòng nào</div>
        <div v-else class="overflow-x-auto">
          <table class="sc-table">
            <thead>
              <tr>
                <th class="w-8">#</th>
                <th v-for="k in Object.keys(child.value[0] || {}).filter(k => !['doctype','parent','parentfield','parenttype','idx','owner','creation','modified','modified_by','docstatus','name'].includes(k)).slice(0, 8)" :key="k">
                  {{ fieldLabel(k) }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in child.value" :key="idx">
                <td class="text-sc-text-muted">{{ idx + 1 }}</td>
                <td v-for="k in Object.keys(row).filter(k => !['doctype','parent','parentfield','parenttype','idx','owner','creation','modified','modified_by','docstatus','name'].includes(k)).slice(0, 8)" :key="k"
                  :class="typeof row[k] === 'number' ? 'font-mono text-right' : ''">
                  {{ displayField(row[k], k) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      </template>
    </template>

    <!-- Lịch sử sửa (Version diffs) — thu gọn mặc định, mỗi log 1 dòng -->
    <div v-if="!isNew && doc?.name" class="sc-card mb-4">
      <button type="button" @click="toggleEditLog"
        class="w-full flex items-center justify-between px-5 py-3 hover:bg-sc-bg">
        <h3 class="font-semibold text-sc-navy">
          <span class="inline-block w-4"><Icon :name="editLogExpanded ? 'chevron-down' : 'chevron-right'" :size="14" /></span>
          <Icon name="history" :size="16" /> Lịch sử sửa<span v-if="editLogLoaded"> ({{ editLog.length }})</span>
        </h3>
        <span class="text-xs text-sc-text-muted">
          {{ editLogExpanded ? 'Bấm để thu gọn' : 'Bấm để xem' }}
        </span>
      </button>

      <div v-if="editLogExpanded" class="px-5 pb-4">
        <div v-if="editLogLoading" class="text-sm text-sc-text-muted py-2">Đang tải...</div>
        <div v-else-if="!editLog.length" class="text-sm text-sc-text-muted py-2">
          Chưa có lần sửa nào được ghi log.
        </div>
        <div v-else class="divide-y divide-sc-border">
          <div v-for="v in editLog" :key="v.name">
            <!-- Dòng tóm tắt — click mở/đóng chi tiết -->
            <button type="button" @click="toggleVersion(v.name)"
              class="w-full flex items-start gap-2 py-2 text-left hover:bg-sc-bg">
              <span class="text-sc-text-muted text-xs mt-0.5 w-3">
                <Icon :name="expandedVersions.has(v.name) ? 'chevron-down' : 'chevron-right'" :size="12" />
              </span>
              <span class="flex-1 min-w-0">
                <span class="text-sm text-sc-text">{{ changeSummary(v) }}</span>
                <span class="block text-xs text-sc-text-muted">
                  {{ v.owner }} · {{ fmtLogTime(v.creation) }}
                </span>
              </span>
            </button>
            <!-- Chi tiết field-level — chỉ khi mở -->
            <table v-if="expandedVersions.has(v.name)"
              class="w-full text-xs mb-2 ml-5">
              <tbody>
                <tr v-for="(c, i) in v.changed" :key="i" class="border-b border-sc-border">
                  <td class="py-1 pr-2 text-sc-text-muted align-top" style="width: 32%">
                    {{ fieldDisplay(c.field) }}
                  </td>
                  <td class="py-1 pr-2 text-sc-danger line-through align-top" style="width: 30%">
                    {{ fmtVal(c.old) }}
                  </td>
                  <td class="py-1 text-sc-success font-medium align-top">
                    <Icon name="arrow-right" :size="14" /> {{ fmtVal(c.new) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Related records (reverse lookups) — luôn hiển thị nếu doc tồn tại -->
    <RelatedDocs v-if="!isNew && doc?.name" :doctype="doctype" :name="doc.name" />
  </div>
</template>
