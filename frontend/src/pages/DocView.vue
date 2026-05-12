<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDoc, submitDoc, cancelDoc, updateDoc, createDoc } from '../api'
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

async function load() {
  if (isNew.value) {
    // Init empty doc with defaults; childtable empty array
    doc.value = { doctype: doctype.value, docstatus: 0 }
    if (schema.value?.items) {
      doc.value[schema.value.items.field] = []
    }
    editing.value = true
    return
  }
  loading.value = true
  try {
    doc.value = await getDoc(doctype.value, name.value)
    editing.value = false
  } catch (e) {
    toast.error(`Không tải được: ${e.message}`)
    doc.value = null
  } finally {
    loading.value = false
  }
}

watch(() => route.fullPath, load)
onMounted(load)

const statusBadge = computed(() => {
  if (!doc.value) return null
  const ds = doc.value.docstatus
  if (ds === 1) return { text: 'Submitted', cls: 'sc-badge-success' }
  if (ds === 2) return { text: 'Cancelled', cls: 'sc-badge-critical' }
  return { text: 'Draft', cls: 'sc-badge-neutral' }
})

async function save() {
  saving.value = true
  try {
    if (isNew.value) {
      const payload = { ...doc.value, doctype: doctype.value }
      const created = await createDoc(doctype.value, payload)
      toast.success(`Đã tạo ${created.name}`)
      router.replace(`/doc/${encodeURIComponent(doctype.value)}/${encodeURIComponent(created.name)}`)
    } else {
      // Send only the changed payload; Frappe handles partial update
      await updateDoc(doctype.value, name.value, doc.value)
      toast.success('Đã lưu')
      editing.value = false
      await load()
    }
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

async function doSubmit() {
  if (!doc.value?.name) return
  saving.value = true
  try {
    await submitDoc(doctype.value, name.value)
    toast.success('Đã submit')
    await load()
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

function displayField(value, key) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 100)
  if (/_date$/.test(key) && value) return new Date(value).toLocaleDateString('vi-VN')
  if (/_at$/.test(key) && value) return new Date(value).toLocaleString('vi-VN')
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
          <button @click="editing = false; load()" class="sc-btn-secondary text-sm">Hủy</button>
          <button @click="save" :disabled="saving" class="sc-btn-primary text-sm">
            {{ saving ? 'Đang lưu...' : '💾 Lưu' }}
          </button>
        </template>
        <template v-else>
          <button v-if="doc.docstatus === 0 && schema"
            @click="editing = true" class="sc-btn-secondary text-sm">✎ Sửa</button>
          <button v-if="doc.docstatus === 0" @click="doSubmit"
            :disabled="saving" class="sc-btn-primary text-sm">Submit</button>
          <button v-if="doc.docstatus === 1" @click="doCancel"
            :disabled="saving" class="bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm">
            Hủy
          </button>
        </template>
      </template>
    </PageHeader>

    <!-- New / Edit mode → DocForm -->
    <template v-if="isNew || editing">
      <DocForm v-model="doc" :doctype="doctype" @submit="save" />
      <div v-if="!schema" class="sc-card p-6 text-center">
        <p class="text-sc-text-muted">Form schema chưa được định nghĩa cho {{ doctype }}.</p>
      </div>
      <!-- TR/SE form: hiển thị tồn kho nguồn để chọn lô -->
      <WarehouseStockPanel v-if="['SC Transfer Request', 'SC Stock Entry'].includes(doctype) && doc.from_warehouse"
        :warehouse="doc.from_warehouse"
        title="Tồn kho nguồn (chọn lô khi điền items)" />
    </template>

    <!-- View mode -->
    <template v-else>
      <ActionPanel :doctype="doctype" :doc="doc" @after="load" />

      <!-- Stock-aware view: TR/SE → tồn kho nguồn; PD → FEFO guide -->
      <WarehouseStockPanel v-if="['SC Transfer Request', 'SC Stock Entry'].includes(doctype) && doc.from_warehouse"
        :warehouse="doc.from_warehouse"
        title="Tồn kho nguồn" />
      <template v-if="doctype === 'SC Patient Dispensing' && doc.items?.length">
        <FefoPickGuide v-for="(it, i) in doc.items.filter(it => it.item && it.warehouse && it.qty)"
          :key="`fefo-${i}`" :item="it.item" :warehouse="it.warehouse" :qtyNeeded="it.qty" />
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div class="sc-card p-5">
          <h3 class="font-semibold text-sc-navy mb-3">Thông tin chính</h3>
          <dl class="space-y-2 text-sm">
            <div v-for="f in fieldGroups.main.slice(0, 12)" :key="f.key"
              class="grid grid-cols-[140px_1fr] gap-2">
              <dt class="text-sc-text-muted truncate">{{ f.key.replace(/_/g, ' ') }}</dt>
              <dd class="text-sc-text font-medium break-all">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </dl>
        </div>
        <div v-if="fieldGroups.main.length > 12" class="sc-card p-5">
          <h3 class="font-semibold text-sc-navy mb-3">Chi tiết khác</h3>
          <dl class="space-y-2 text-sm">
            <div v-for="f in fieldGroups.main.slice(12)" :key="f.key"
              class="grid grid-cols-[140px_1fr] gap-2">
              <dt class="text-sc-text-muted truncate">{{ f.key.replace(/_/g, ' ') }}</dt>
              <dd class="text-sc-text font-medium break-all">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Related records (reverse lookups) -->
      <RelatedDocs v-if="!isNew && doc?.name" :doctype="doctype" :name="doc.name" />

      <div v-for="child in fieldGroups.items" :key="child.key" class="sc-card p-5 mb-4">
        <h3 class="font-semibold text-sc-navy mb-3">{{ child.key.replace(/_/g, ' ') }} ({{ child.value.length }})</h3>
        <div v-if="child.value.length === 0" class="text-sm text-sc-text-muted">Chưa có item</div>
        <div v-else class="overflow-x-auto">
          <table class="sc-table">
            <thead>
              <tr>
                <th class="w-8">#</th>
                <th v-for="k in Object.keys(child.value[0] || {}).filter(k => !['doctype','parent','parentfield','parenttype','idx','owner','creation','modified','modified_by','docstatus','name'].includes(k)).slice(0, 8)" :key="k">
                  {{ k.replace(/_/g, ' ') }}
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
  </div>
</template>
