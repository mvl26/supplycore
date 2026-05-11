<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDoc, runDocMethod, submitDoc, cancelDoc, updateDoc, createDoc } from '../api'
import { DT } from '../modules'
import PageHeader from '../components/PageHeader.vue'
import ActionPanel from '../components/ActionPanel.vue'
import { useToastStore } from '../stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const doctype = computed(() => decodeURIComponent(route.params.dt))
const name = computed(() => decodeURIComponent(route.params.name))
const cfg = computed(() => DT[doctype.value])
const isNew = computed(() => name.value === 'new')

const doc = ref(null)
const loading = ref(false)
const saving = ref(false)

async function load() {
  if (isNew.value) {
    doc.value = { doctype: doctype.value, docstatus: 0 }
    return
  }
  loading.value = true
  try {
    doc.value = await getDoc(doctype.value, name.value)
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

async function doAction(action) {
  if (!doc.value) return
  saving.value = true
  try {
    if (action === 'submit') {
      await submitDoc(doctype.value, name.value)
      toast.success('Đã submit')
    } else if (action === 'cancel') {
      await cancelDoc(doctype.value, name.value)
      toast.success('Đã hủy')
    } else {
      await runDocMethod(doctype.value, name.value, action)
      toast.success(`Đã chạy ${action}`)
    }
    await load()
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

// Hiển thị field values — group theo schema
function displayField(value, key) {
  if (value == null || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 100)
  if (/_date$/.test(key) && value) return new Date(value).toLocaleDateString('vi-VN')
  if (/_at$/.test(key) && value) return new Date(value).toLocaleString('vi-VN')
  if (/value|amount|total|cost|rate/.test(key) && typeof value === 'number') {
    return new Intl.NumberFormat('vi-VN').format(value)
  }
  return value
}

// Group fields into Main / Items (Table) / Other
const fieldGroups = computed(() => {
  if (!doc.value) return { main: [], items: [], other: [] }
  const main = [], items = [], other = []
  const skip = new Set(['doctype', 'docstatus', 'owner', 'creation', 'modified', 'modified_by',
    'idx', 'parent', 'parentfield', 'parenttype', '_user_tags', '_comments', '_assign', '_liked_by',
    'name'])
  for (const [k, v] of Object.entries(doc.value)) {
    if (skip.has(k)) continue
    if (Array.isArray(v)) items.push({ key: k, value: v })
    else main.push({ key: k, value: v })
  }
  return { main, items, other }
})

function backToList() {
  router.push(`/list/${encodeURIComponent(doctype.value)}`)
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
      :subtitle="isNew ? 'Bản ghi mới' : `Cập nhật: ${doc.modified ? new Date(doc.modified).toLocaleString('vi-VN') : ''}`">
      <template #actions>
        <button @click="backToList" class="sc-btn-secondary text-sm">← Danh sách</button>
        <span v-if="statusBadge" :class="['sc-badge', statusBadge.cls]">{{ statusBadge.text }}</span>
        <button v-if="!isNew && doc.docstatus === 0" @click="doAction('submit')"
          :disabled="saving" class="sc-btn-primary text-sm">Submit</button>
        <button v-if="!isNew && doc.docstatus === 1" @click="doAction('cancel')"
          :disabled="saving" class="bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium text-sm">
          Cancel
        </button>
      </template>
    </PageHeader>

    <div v-if="isNew" class="sc-card p-6 text-center">
      <p class="text-sc-text-muted mb-3">
        Tạo nhanh từ giao diện SupplyCore chưa hỗ trợ đầy đủ field cho {{ cfg.label }}.<br/>
        Vui lòng dùng API hoặc seed script.
      </p>
      <button @click="backToList" class="sc-btn-secondary">← Quay lại</button>
    </div>

    <!-- Custom action panel -->
    <ActionPanel v-if="!isNew && doc" :doctype="doctype" :doc="doc" @after="load" />

    <!-- Main fields -->
    <div v-if="!isNew" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy mb-3">Thông tin chính</h3>
        <dl class="space-y-2 text-sm">
          <template v-for="f in fieldGroups.main.slice(0, 12)" :key="f.key">
            <div class="grid grid-cols-2 gap-2">
              <dt class="text-sc-text-muted">{{ f.key.replace(/_/g, ' ') }}</dt>
              <dd class="text-sc-text font-medium">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </template>
        </dl>
      </div>
      <div v-if="fieldGroups.main.length > 12" class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy mb-3">Chi tiết khác</h3>
        <dl class="space-y-2 text-sm">
          <template v-for="f in fieldGroups.main.slice(12)" :key="f.key">
            <div class="grid grid-cols-2 gap-2">
              <dt class="text-sc-text-muted">{{ f.key.replace(/_/g, ' ') }}</dt>
              <dd class="text-sc-text font-medium">{{ displayField(f.value, f.key) }}</dd>
            </div>
          </template>
        </dl>
      </div>
    </div>

    <!-- Child tables -->
    <div v-if="!isNew" v-for="(child, i) in fieldGroups.items" :key="child.key" class="sc-card p-5 mb-4">
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
  </div>
</template>
