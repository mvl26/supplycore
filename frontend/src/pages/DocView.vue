<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDoc, submitDoc, cancelDoc, updateDoc, createDoc, call } from '../api'
import { DT } from '../modules'
import { FORM_SCHEMAS } from '../schemas'
import PageHeader from '../components/PageHeader.vue'
import ActionPanel from '../components/ActionPanel.vue'
import DocForm from '../components/DocForm.vue'
import RelatedDocs from '../components/RelatedDocs.vue'
import FefoPickGuide from '../components/FefoPickGuide.vue'
import WarehouseStockPanel from '../components/WarehouseStockPanel.vue'
import { useToastStore } from '../stores/toast'
import { fmtDateTime, fmtNumber } from '../utils'
import { statusLabel } from '../modules'
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

const LINK_PENDING_KEY = 'sc-link-create-pending'
const LINK_RESULT_KEY  = 'sc-link-create-result'

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
    // Auto-edit khi draft → user khỏi phải bấm "Sửa"
    editing.value = doc.value.docstatus === 0 && !!schema.value
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
  } catch (e) {
    toast.error(`Không tải được: ${e.message}`)
    doc.value = null
  } finally {
    loading.value = false
  }
}

// Khi user bấm "+ Tạo mới" trên Link field → lưu state rồi navigate sang form new
async function onCreateNewLink(field) {
  if (!field?.linkTo) return
  const prefill = {}
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

watch(() => route.fullPath, load)
onMounted(load)

const statusBadge = computed(() => {
  if (!doc.value) return null
  const ds = doc.value.docstatus
  if (ds === 1) return { text: 'Đã gửi', cls: 'sc-badge-success' }
  if (ds === 2) return { text: 'Đã huỷ', cls: 'sc-badge-critical' }
  return { text: 'Nháp', cls: 'sc-badge-neutral' }
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
const POST_SUBMIT_NAV = {
  'SC Purchase Receipt': (d) => d?.docstatus === 1 && d.is_return === 0
    ? { path: '/putaway', query: { warehouse: d.warehouse || '' } } : null,
  'SC Stock Entry': (d) => d?.docstatus === 1 && d.to_warehouse
    ? { path: '/putaway', query: { warehouse: d.to_warehouse } } : null,
}

async function doSubmit() {
  if (!doc.value?.name) return
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
  if (/_date$/.test(key) && value) return new Date(value).toLocaleDateString('vi-VN')
  if (/_at$/.test(key) && value) return new Date(value).toLocaleString('vi-VN')
  if (STATUS_KEYS.has(key) && typeof value === 'string') return statusLabel(value)
  if (/value|amount|total|cost|rate/.test(key) && typeof value === 'number') {
    return fmtNumber(value)
  }
  if (value === 1) return '✓'
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
        <button @click="backToList" class="sc-btn-secondary text-sm">← Danh sách</button>
        <span v-if="statusBadge && !isNew" :class="['sc-badge', statusBadge.cls]">{{ statusBadge.text }}</span>

        <template v-if="isNew">
          <button @click="save" :disabled="saving" class="sc-btn-primary text-sm">
            {{ saving ? 'Đang lưu...' : '💾 Lưu' }}
          </button>
        </template>
        <template v-else-if="editing">
          <button @click="load" class="sc-btn-secondary text-sm">↺ Hoàn tác</button>
          <button @click="save" :disabled="saving" class="sc-btn-primary text-sm">
            {{ saving ? 'Đang lưu...' : '💾 Lưu' }}
          </button>
          <button v-if="doc.docstatus === 0" @click="doSubmit"
            :disabled="saving" class="bg-sc-success hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium text-sm">
            📤 Gửi duyệt
          </button>
        </template>
        <template v-else>
          <button v-if="doc.docstatus === 1" @click="doCancel"
            :disabled="saving" class="bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm">
            Hủy
          </button>
        </template>
      </template>
    </PageHeader>

    <!-- Action panel — hiển thị cả khi draft-editing để user gọi action (vd Gửi duyệt FC) -->
    <ActionPanel v-if="!isNew && doc?.name" :doctype="doctype" :doc="doc" @after="load" />

    <!-- Stock-aware widget chung -->
    <WarehouseStockPanel v-if="['SC Transfer Request', 'SC Stock Entry'].includes(doctype) && doc.from_warehouse"
      :warehouse="doc.from_warehouse"
      :title="isNew || editing ? 'Tồn kho nguồn (chọn lô khi điền items)' : 'Tồn kho nguồn'" />
    <template v-if="doctype === 'SC Patient Dispensing' && doc.items?.length">
      <FefoPickGuide v-for="(it, i) in doc.items.filter(it => it.item && it.warehouse && it.qty)"
        :key="`fefo-${i}`" :item="it.item" :warehouse="it.warehouse" :qtyNeeded="it.qty" />
    </template>

    <!-- New / Edit mode → DocForm -->
    <template v-if="isNew || editing">
      <DocForm v-model="doc" :doctype="doctype" @submit="save" @create-new="onCreateNewLink" />
      <div v-if="!schema" class="sc-card p-6 text-center">
        <p class="text-sc-text-muted">Form schema chưa được định nghĩa cho {{ doctype }}.</p>
      </div>
    </template>

    <!-- View mode (chỉ khi đã submit hoặc cancel — không phải draft) -->
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

    <!-- Related records (reverse lookups) — luôn hiển thị nếu doc tồn tại -->
    <RelatedDocs v-if="!isNew && doc?.name" :doctype="doctype" :name="doc.name" />
  </div>
</template>
