<script setup>
import { ref, watch, computed } from 'vue'
import LinkAutocomplete from './LinkAutocomplete.vue'
import Icon from './Icon.vue'
import { call } from '../api'

const props = defineProps({
  modelValue: [String, Number, Boolean, Date],
  field:      { type: Object, required: true },  // { name, label, type, required, options, linkTo, hint, readonly, scope }
  size:       { type: String, default: 'normal' },
  showLabel:  { type: Boolean, default: true },
  readonly:   { type: Boolean, default: false },
  context:    { type: Object, default: () => ({}) },  // row trong child table hoặc doc trong form
})
const emit = defineEmits(['update:modelValue', 'selected', 'createNew'])

// === Scope resolver: filter dropdown theo item của row/doc ===
// field.scope = { itemField: 'item' } → SC Batch: [['item','=',ctx.item]]; SC UOM: [['name','in',[uoms...]]]
const extraFilters = ref([])
async function resolveScope() {
  const scope = props.field.scope
  if (!scope?.itemField) { extraFilters.value = []; return }
  const itemVal = props.context?.[scope.itemField]
  if (!itemVal) { extraFilters.value = []; return }
  if (props.field.linkTo === 'SC Batch') {
    extraFilters.value = [['item', '=', itemVal]]
  } else if (props.field.linkTo === 'SC UOM') {
    try {
      const uoms = await call('supplycore.api.frontend.item_eligible_uoms', { item: itemVal })
      extraFilters.value = (uoms && uoms.length) ? [['name', 'in', uoms]] : []
    } catch (e) { extraFilters.value = [] }
  } else if (props.field.linkTo === 'Framework Contract') {
    // Chỉ gợi ý HĐ khung (Active) thực sự có chứa vật tư của dòng này.
    // Item không thuộc HĐ khung nào → dropdown rỗng (sentinel không khớp).
    try {
      const fcs = await call('supplycore.api.frontend.framework_contracts_for_item', { item: itemVal })
      extraFilters.value = [['name', 'in', (fcs && fcs.length) ? fcs : ['__no_fc__']]]
    } catch (e) { extraFilters.value = [] }
  } else {
    extraFilters.value = []
  }
}
watch(() => [props.field.scope, props.context?.[props.field.scope?.itemField]],
  resolveScope, { immediate: true })

function update(v) {
  if (props.readonly || props.field.readonly) return
  if (props.field.type === 'Int' || props.field.type === 'Float' || props.field.type === 'Currency' || props.field.type === 'Percent') {
    emit('update:modelValue', v === '' || v == null ? null : Number(v))
  } else if (props.field.type === 'Check') {
    emit('update:modelValue', v ? 1 : 0)
  } else {
    emit('update:modelValue', v)
  }
}

const isReadonly = () => props.readonly || !!props.field.readonly
const inputClass = props.size === 'sm' ? 'sc-input py-1.5 text-sm' : 'sc-input'

// Attach upload state
const uploading = ref(false)
const uploadErr = ref('')

function getCsrf() {
  return window.sc_csrf
    || document.querySelector('meta[name="csrf-token"]')?.content
    || ''
}

async function handleAttach(e) {
  if (isReadonly()) return
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  uploadErr.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('is_private', '0')
    fd.append('folder', 'Home/Attachments')
    const r = await fetch('/api/method/upload_file', {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': getCsrf(), Accept: 'application/json' },
      body: fd,
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || `HTTP ${r.status}`)
    const url = d.message?.file_url
    if (!url) throw new Error('Không nhận được file_url')
    emit('update:modelValue', url)
  } catch (err) {
    uploadErr.value = err.message || String(err)
  } finally {
    uploading.value = false
    if (e.target) e.target.value = ''
  }
}

function clearAttach() {
  if (isReadonly()) return
  emit('update:modelValue', null)
}
</script>

<template>
  <div :class="field.type === 'Check' ? '' : 'flex flex-col'">
    <label v-if="showLabel && field.type !== 'Check'"
      class="text-xs font-medium text-sc-text-muted mb-1">
      {{ field.label }}
      <span v-if="field.required" class="text-sc-danger">*</span>
    </label>

    <!-- Link → autocomplete -->
    <LinkAutocomplete v-if="field.type === 'Link'"
      :model-value="modelValue" :link-to="field.linkTo" :required="field.required"
      :size="size" :allow-create="!!field.canCreateNew" :readonly="isReadonly()"
      :extra-filters="extraFilters"
      @update:model-value="update" @selected="(r) => emit('selected', r)"
      @create-new="emit('createNew', field)" />

    <!-- Select -->
    <select v-else-if="field.type === 'Select'"
      :value="modelValue ?? ''" :required="field.required" :disabled="isReadonly()"
      @change="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'opacity-70 cursor-not-allowed']">
      <option value="">— Chọn —</option>
      <option v-for="o in field.options" :key="o.value ?? o" :value="o.value ?? o">
        {{ o.label ?? o }}
      </option>
    </select>

    <!-- Text areas -->
    <textarea v-else-if="field.type === 'Small Text' || field.type === 'Long Text' || field.type === 'Text'"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      :rows="field.type === 'Long Text' ? 5 : 3"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <!-- Check -->
    <label v-else-if="field.type === 'Check'" class="flex items-center gap-2 cursor-pointer py-1.5">
      <input type="checkbox" :checked="!!modelValue" :disabled="isReadonly()"
        @change="e => update(e.target.checked)"
        class="w-4 h-4 text-sc-royal rounded" />
      <span class="text-sm">{{ field.label }}{{ field.required ? ' *' : '' }}</span>
    </label>

    <!-- Date -->
    <input v-else-if="field.type === 'Date'" type="date"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <!-- Datetime -->
    <input v-else-if="field.type === 'Datetime'" type="datetime-local"
      :value="modelValue ? new Date(modelValue).toISOString().slice(0, 16) : ''"
      :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <!-- Time -->
    <input v-else-if="field.type === 'Time'" type="time"
      :value="modelValue ?? ''" :required="field.required" step="1" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <!-- Number-like -->
    <input v-else-if="['Int','Float','Currency','Percent'].includes(field.type)" type="number"
      :step="field.type === 'Int' ? '1' : '0.01'"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <!-- Attach: file upload via /api/method/upload_file -->
    <div v-else-if="field.type === 'Attach'" class="flex items-center gap-2 flex-wrap">
      <template v-if="modelValue">
        <a :href="modelValue" target="_blank" rel="noopener"
          class="text-sc-royal underline text-sm truncate max-w-[260px] inline-flex items-center gap-1"
          :title="modelValue"><Icon name="paperclip" :size="14" /> {{ modelValue.split('/').pop() }}</a>
        <button v-if="!isReadonly()" type="button" @click="clearAttach"
          class="text-xs text-sc-danger hover:underline">Gỡ tệp</button>
      </template>
      <template v-else>
        <label v-if="!isReadonly()"
          :class="['sc-btn-secondary cursor-pointer inline-flex items-center gap-1',
                   size === 'sm' ? 'text-xs py-1 px-2' : 'text-sm']">
          <Icon :name="uploading ? 'clock' : 'paperclip'" :size="14" />
          {{ uploading ? 'Đang tải...' : 'Chọn tệp' }}
          <input type="file" class="hidden"
            :accept="field.accept || '.pdf,.doc,.docx,.png,.jpg,.jpeg'"
            :disabled="uploading" @change="handleAttach" />
        </label>
        <span v-else class="text-sm text-sc-text-muted italic">— chưa đính kèm —</span>
      </template>
      <span v-if="uploadErr" class="text-xs text-sc-danger">{{ uploadErr }}</span>
    </div>

    <!-- Default: text/data -->
    <input v-else type="text"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-gray-50']" />

    <div v-if="field.hint" class="text-xs text-sc-text-muted mt-1">{{ field.hint }}</div>
  </div>
</template>
