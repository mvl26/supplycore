<script setup>
import { ref, computed, watch } from 'vue'
import { FORM_SCHEMAS } from '../schemas'
import FormField from './FormField.vue'
import ChildTable from './ChildTable.vue'
import { today } from '../utils'
import { call } from '../api'

const props = defineProps({
  modelValue: { type: Object, required: true },
  doctype:    { type: String, required: true },
  readonly:   { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'submit'])

const schema = computed(() => FORM_SCHEMAS[props.doctype])
const doc = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

// Apply defaults nếu doc.name không có (new)
watch(schema, (s) => {
  if (!s || doc.value.name) return
  const next = { ...doc.value }
  for (const sec of s.sections || []) {
    for (const f of sec.fields) {
      if (next[f.name] == null && f.default !== undefined) {
        next[f.name] = f.default === 'today' ? today() : f.default
      }
    }
  }
  if (Object.keys(next).length !== Object.keys(doc.value).length) {
    emit('update:modelValue', next)
  }
}, { immediate: true })

function updateField(name, value) {
  emit('update:modelValue', { ...doc.value, [name]: value })
}

async function handleLinkSelected(field, linked) {
  if (!field.fetchFrom || !linked?.name) return
  try {
    const d = await call('frappe.client.get_value', {
      doctype: field.fetchFrom.target_doctype,
      filters: { name: linked.name },
      fieldname: field.fetchFrom.target_field,
    })
    const v = d?.[field.fetchFrom.target_field]
    if (v != null) emit('update:modelValue', { ...doc.value, [field.fetchFrom.target_field]: v })
  } catch (e) {}
}

function isVisible(field) {
  if (!field.dependOn) return true
  return !!doc.value[field.dependOn]
}
</script>

<template>
  <div v-if="!schema" class="sc-card p-6 text-center text-sc-text-muted">
    Chưa có form schema cho {{ doctype }}
  </div>
  <form v-else @submit.prevent="emit('submit')">
    <div v-for="(section, si) in schema.sections" :key="si"
      class="sc-card p-5 mb-4">
      <h3 class="font-semibold text-sc-navy mb-4">{{ section.title }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <template v-for="f in section.fields" :key="f.name">
          <div v-if="isVisible(f)"
            :class="['Small Text','Long Text','Text'].includes(f.type) ? 'md:col-span-2' : ''">
            <FormField :model-value="doc[f.name]"
              :field="f" :readonly="readonly"
              @update:model-value="v => updateField(f.name, v)"
              @selected="linked => handleLinkSelected(f, linked)" />
          </div>
        </template>
      </div>
    </div>

    <div v-if="schema.items" class="sc-card p-5 mb-4">
      <ChildTable :model-value="doc[schema.items.field] || []"
        :schema="schema.items" :readonly="readonly"
        @update:model-value="v => updateField(schema.items.field, v)" />
    </div>
  </form>
</template>
