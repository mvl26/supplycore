<script setup>
import { ref, watch, computed } from 'vue'
import LinkAutocomplete from './LinkAutocomplete.vue'
import FormattedNumberInput from './FormattedNumberInput.vue'
import Icon from './Icon.vue'
import { call } from '../api'
import { QUICK_CREATE } from '../schemas'

// CR-03: bật "+ Tạo mới" cho mọi Link field có linkTo nằm trong registry
// quick-create (hoặc field tự khai báo canCreateNew).
const canQuickCreate = (f) => !!f.canCreateNew || !!QUICK_CREATE[f.linkTo]

const props = defineProps({
  modelValue: [String, Number, Boolean, Date],
  field:      { type: Object, required: true },  // { name, label, type, required, options, linkTo, hint, readonly, scope }
  size:       { type: String, default: 'normal' },
  showLabel:  { type: Boolean, default: true },
  readonly:   { type: Boolean, default: false },
  context:    { type: Object, default: () => ({}) },  // row trong child table hoặc doc trong form
  parentDoc:  { type: Object, default: () => ({}) },  // doc cha (header) — để scope theo field ở header (vd kho nguồn)
})
const emit = defineEmits(['update:modelValue', 'selected', 'createNew'])

// T14: cảnh báo (mềm) khi field Date có cờ warnPastDate và giá trị < hôm nay
const isPastDateWarn = computed(() => {
  if (!props.field.warnPastDate || props.field.type !== 'Date' || !props.modelValue) return false
  const v = new Date(String(props.modelValue) + 'T00:00:00')
  if (isNaN(v)) return false
  const t = new Date(); t.setHours(0, 0, 0, 0)
  return v < t
})

// === Scope resolver: filter dropdown theo item của row/doc ===
// field.scope = { itemField: 'item' } → SC Batch: [['item','=',ctx.item]]; SC UOM: [['name','in',[uoms...]]]
const extraFilters = ref([])
async function resolveScope() {
  const scope = props.field.scope
  if (!scope) { extraFilters.value = []; return }
  // Lọc HĐ khung bán theo khách đã chọn ở header (yêu cầu #5 — chiều ngược).
  // Chưa chọn khách → không lọc (hiện tất cả), mirror cách scope kho tự thoát.
  if (scope.customerField) {
    const cust = props.context?.[scope.customerField] ?? props.parentDoc?.[scope.customerField]
    extraFilters.value = cust ? [['customer', '=', cust]] : []
    return
  }
  // Lọc ô chọn Vật tư ở dòng chi tiết chỉ trong HĐ khung của đơn (yêu cầu #5).
  // Chưa chọn HĐ khung → không lọc; HĐ khung không có vật tư → dropdown rỗng.
  if (props.field.linkTo === 'SC Item' && scope.salesFcField) {
    const fc = props.parentDoc?.[scope.salesFcField] ?? props.context?.[scope.salesFcField]
    if (!fc) { extraFilters.value = []; return }
    try {
      const items = await call('supplycore.api.sales.sales_framework_items', { framework_contract: fc })
      const codes = (items || []).map(r => r.item).filter(Boolean)
      extraFilters.value = [['name', 'in', codes.length ? codes : ['__no_fc_item__']]]
    } catch (e) { extraFilters.value = [] }
    return
  }
  // SC Item giới hạn theo KHO: chỉ hiện vật tư có tồn (>0) trong kho nguồn của phiếu.
  // warehouseFromParent=true → kho ở header (doc cha); ngược lại kho ở chính dòng (context).
  // Chưa chọn kho → không giới hạn (hiện toàn bộ); kho không có tồn → dropdown rỗng.
  if (props.field.linkTo === 'SC Item' && scope.warehouseField) {
    const src = scope.warehouseFromParent ? props.parentDoc : props.context
    const wh = src?.[scope.warehouseField]
    if (!wh) { extraFilters.value = []; return }
    try {
      const items = await call('supplycore.api.frontend.items_in_warehouse', { warehouse: wh })
      extraFilters.value = [['name', 'in', (items && items.length) ? items : ['__none__']]]
    } catch (e) { extraFilters.value = [] }
    return
  }
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
watch(() => {
  const s = props.field.scope
  return [
    s,
    s?.itemField ? props.context?.[s.itemField] : null,
    s?.warehouseField
      ? (s.warehouseFromParent ? props.parentDoc?.[s.warehouseField] : props.context?.[s.warehouseField])
      : null,
    s?.customerField ? (props.context?.[s.customerField] ?? props.parentDoc?.[s.customerField]) : null,
    s?.salesFcField ? (props.parentDoc?.[s.salesFcField] ?? props.context?.[s.salesFcField]) : null,
  ]
}, resolveScope, { immediate: true })

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

async function uploadOne(file) {
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
  return { url, name: d.message?.file_name || file.name }
}

async function handleAttach(e) {
  if (isReadonly()) return
  const file = e.target.files?.[0]
  if (!file) return
  uploading.value = true
  uploadErr.value = ''
  try {
    const { url } = await uploadOne(file)
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

// L05: đính kèm NHIỀU tệp — lưu JSON array [{url, name}] vào 1 field Long Text.
const attachList = computed(() => {
  const v = props.modelValue
  if (!v) return []
  try {
    const a = JSON.parse(v)
    return Array.isArray(a) ? a : []
  } catch (e) {
    return typeof v === 'string' && v ? [{ url: v, name: v.split('/').pop() }] : []
  }
})
async function handleAttachMultiple(e) {
  if (isReadonly()) return
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  uploading.value = true
  uploadErr.value = ''
  try {
    const cur = [...attachList.value]
    for (const f of files) cur.push(await uploadOne(f))
    emit('update:modelValue', JSON.stringify(cur))
  } catch (err) {
    uploadErr.value = err.message || String(err)
  } finally {
    uploading.value = false
    if (e.target) e.target.value = ''
  }
}
function removeAttachAt(idx) {
  if (isReadonly()) return
  const cur = attachList.value.filter((_, i) => i !== idx)
  emit('update:modelValue', cur.length ? JSON.stringify(cur) : null)
}
</script>

<template>
  <div :class="field.type === 'Check' ? '' : 'flex flex-col'">
    <label v-if="showLabel && field.type !== 'Check'" class="sc-label">
      {{ field.label }}
      <span v-if="field.required" class="text-sc-danger">*</span>
    </label>

    <!-- Link → autocomplete -->
    <LinkAutocomplete v-if="field.type === 'Link'"
      :model-value="modelValue" :link-to="field.linkTo" :required="field.required"
      :size="size" :allow-create="canQuickCreate(field)" :readonly="isReadonly()"
      :extra-filters="extraFilters"
      @update:model-value="update" @selected="(r) => emit('selected', r)"
      @create-new="(payload) => emit('createNew', { field, ...(payload || {}) })" />

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
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

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
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

    <!-- Datetime -->
    <input v-else-if="field.type === 'Datetime'" type="datetime-local"
      :value="modelValue ? new Date(modelValue).toISOString().slice(0, 16) : ''"
      :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

    <!-- Time -->
    <input v-else-if="field.type === 'Time'" type="time"
      :value="modelValue ?? ''" :required="field.required" step="1" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

    <!-- Number-like — ngăn cách hàng nghìn kiểu VN (1.000.000) -->
    <FormattedNumberInput v-else-if="['Int','Float','Currency','Percent'].includes(field.type)"
      :model-value="modelValue" :allow-decimal="field.type !== 'Int'"
      :readonly="isReadonly()" @update:model-value="update"
      :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

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

    <!-- AttachMultiple: 1 hoặc nhiều tệp (L05) -->
    <div v-else-if="field.type === 'AttachMultiple'" class="space-y-1">
      <div v-for="(a, i) in attachList" :key="i" class="flex items-center gap-2">
        <a :href="a.url" target="_blank" rel="noopener"
          class="text-sc-royal underline text-sm truncate max-w-[280px] inline-flex items-center gap-1"
          :title="a.name"><Icon name="paperclip" :size="14" /> {{ a.name }}</a>
        <button v-if="!isReadonly()" type="button" @click="removeAttachAt(i)"
          class="text-xs text-sc-danger hover:underline">Gỡ</button>
      </div>
      <label v-if="!isReadonly()"
        :class="['sc-btn-secondary cursor-pointer inline-flex items-center gap-1',
                 size === 'sm' ? 'text-xs py-1 px-2' : 'text-sm']">
        <Icon :name="uploading ? 'clock' : 'paperclip'" :size="14" />
        {{ uploading ? 'Đang tải...' : (attachList.length ? 'Thêm tệp' : 'Chọn tệp (1 hoặc nhiều)') }}
        <input type="file" multiple class="hidden"
          :accept="field.accept || '.pdf,.doc,.docx,.png,.jpg,.jpeg'"
          :disabled="uploading" @change="handleAttachMultiple" />
      </label>
      <span v-else-if="!attachList.length" class="text-sm text-sc-text-muted italic">— chưa đính kèm —</span>
      <span v-if="uploadErr" class="text-xs text-sc-danger block">{{ uploadErr }}</span>
    </div>

    <!-- Password (masked) -->
    <input v-else-if="field.type === 'Password'" type="password"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      autocomplete="new-password"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

    <!-- Default: text/data -->
    <input v-else type="text"
      :value="modelValue ?? ''" :required="field.required" :readonly="isReadonly()"
      @input="e => update(e.target.value)" :class="[inputClass, isReadonly() && 'bg-sc-bg-soft']" />

    <div v-if="field.hint" class="text-xs text-sc-text-muted mt-1">{{ field.hint }}</div>
    <div v-if="isPastDateWarn" class="text-xs text-sc-warning mt-1 flex items-center gap-1"><Icon name="alert-triangle" :size="12" /> Ngày đã ở quá khứ (trước hôm nay)</div>
  </div>
</template>
