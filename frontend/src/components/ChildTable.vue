<script setup>
import { computed } from 'vue'
import FormField from './FormField.vue'
import { call } from '../api'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  schema: { type: Object, required: true },  // { field, label, columns }
  readonly: Boolean,
})
const emit = defineEmits(['update:modelValue'])

const rows = computed(() => props.modelValue || [])

function newRow() {
  const r = {}
  for (const c of props.schema.columns) {
    if (c.default !== undefined) r[c.name] = c.default
  }
  emit('update:modelValue', [...rows.value, r])
}

function removeRow(idx) {
  const arr = [...rows.value]
  arr.splice(idx, 1)
  emit('update:modelValue', arr)
}

function applyBulk(action) {
  if (!rows.value.length) return
  const set = action.set || {}
  const arr = rows.value.map(r => ({ ...r, ...set }))
  emit('update:modelValue', arr)
}

const variantClass = (v) => ({
  success: 'bg-sc-success hover:bg-green-700 text-white',
  danger:  'bg-sc-danger hover:bg-red-700 text-white',
  primary: 'sc-btn-primary',
}[v] || 'sc-btn-secondary')

function updateCell(idx, name, value) {
  const arr = rows.value.map((r, i) => i === idx ? { ...r, [name]: value } : r)
  emit('update:modelValue', arr)
  // Trigger row-level auto-fetch nếu schema khai báo autoFetch.on chứa field này
  const af = props.schema.autoFetch
  if (af && af.api && af.on?.includes(name)) {
    const row = arr[idx]
    if (af.on.every(k => row[k])) runAutoFetch(idx, row, af)
  }
}

async function runAutoFetch(idx, row, af) {
  const params = {}
  for (const k of af.on) params[k] = row[k]
  try {
    const res = await call(af.api, params)
    if (!res || typeof res !== 'object') return
    const updates = {}
    for (const [k, v] of Object.entries(res)) {
      // Bỏ qua key không phải column hợp lệ
      if (!props.schema.columns.some(c => c.name === k)) continue
      if (v != null && v !== '') updates[k] = v
    }
    if (Object.keys(updates).length) {
      const arr2 = rows.value.map((r, i) => i === idx ? { ...r, ...updates } : r)
      emit('update:modelValue', arr2)
    }
  } catch (e) {}
}

// Auto-fetch related field after Link change
async function handleLinkSelected(idx, col, linkedDoc) {
  // Some cols have fetchFrom: when source field set, fetch target_field from target_doctype
  const updates = {}
  for (const otherCol of props.schema.columns) {
    if (otherCol.fetchFrom && otherCol.fetchFrom.source === col.name && linkedDoc?.name) {
      try {
        const d = await call('frappe.client.get_value', {
          doctype: otherCol.fetchFrom.target_doctype,
          filters: { name: linkedDoc.name },
          fieldname: otherCol.fetchFrom.target_field,
        })
        const v = d?.[otherCol.fetchFrom.target_field]
        if (v != null) updates[otherCol.name] = v
      } catch (e) {}
    }
  }
  if (Object.keys(updates).length) {
    const arr = rows.value.map((r, i) => i === idx ? { ...r, ...updates } : r)
    emit('update:modelValue', arr)
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-2 gap-2 flex-wrap">
      <h4 class="font-medium text-sc-navy text-sm">{{ schema.label }} ({{ rows.length }})</h4>
      <div v-if="!readonly" class="flex items-center gap-2 flex-wrap">
        <button v-for="(act, i) in (schema.bulkActions || [])" :key="i"
          @click="applyBulk(act)" type="button"
          :disabled="!rows.length"
          :class="['text-xs px-3 py-1 rounded-md font-medium disabled:opacity-40', variantClass(act.variant)]">
          {{ act.label }}
        </button>
        <button @click="newRow" type="button" class="sc-btn-secondary text-xs">
          + Thêm dòng
        </button>
      </div>
    </div>

    <div v-if="rows.length === 0" class="border border-dashed border-sc-border rounded-md p-6 text-center text-sm text-sc-text-muted">
      Chưa có dòng nào — click "+ Thêm dòng" để bắt đầu
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-sc-bg text-sc-text-muted text-xs uppercase">
            <th class="px-2 py-1.5 text-left w-8">#</th>
            <th v-for="c in schema.columns" :key="c.name"
              :style="c.width ? { width: c.width } : {}"
              class="px-2 py-1.5 text-left">
              {{ c.label }}
              <span v-if="c.required" class="text-sc-danger">*</span>
            </th>
            <th v-if="!readonly" class="w-10"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in rows" :key="idx" class="border-b border-sc-border">
            <td class="px-2 py-1 text-sc-text-muted text-xs align-top pt-3">{{ idx + 1 }}</td>
            <td v-for="c in schema.columns" :key="c.name" class="px-2 py-1 align-top">
              <FormField :model-value="r[c.name]"
                :field="c" size="sm" :show-label="false"
                @update:model-value="v => updateCell(idx, c.name, v)"
                @selected="(linked) => handleLinkSelected(idx, c, linked)" />
            </td>
            <td v-if="!readonly" class="px-2 py-1 align-top">
              <button @click="removeRow(idx)" type="button"
                class="text-sc-danger hover:bg-red-50 px-1.5 py-1 rounded text-sm">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
