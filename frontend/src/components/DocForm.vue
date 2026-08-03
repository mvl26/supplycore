<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { FORM_SCHEMAS } from '../schemas'
import FormField from './FormField.vue'
import ChildTable from './ChildTable.vue'
import Icon from './Icon.vue'
import { today } from '../utils'
import { call } from '../api'
import { useToastStore } from '../stores/toast'

const props = defineProps({
  modelValue: { type: Object, required: true },
  doctype:    { type: String, required: true },
  readonly:   { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'submit', 'createNew'])

const schema = computed(() => FORM_SCHEMAS[props.doctype])
const doc = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const toast = useToastStore()

// UX-005: track field nào bị lỗi để highlight border đỏ.
// touched = user đã nhấn Lưu một lần (sau đó mọi validation lỗi đều show).
const touched = ref(false)
const invalidFields = ref(new Set())

function isFieldInvalid(field) {
  if (!touched.value) return false
  if (!field.required) return false
  const v = doc.value[field.name]
  return v == null || v === '' || (Array.isArray(v) && v.length === 0)
}

// UX-005: validate() — gọi từ ngoài (DocView.save) để check field bắt buộc
// + highlight + auto-scroll. Trả về true nếu OK, false nếu còn thiếu.
function validate() {
  touched.value = true
  invalidFields.value = new Set()
  if (schema.value) {
    for (const sec of schema.value.sections || []) {
      for (const f of sec.fields) {
        const v = doc.value[f.name]
        if (f.required && (v == null || v === '')) {
          invalidFields.value.add(f.name)
        }
      }
    }
  }
  if (invalidFields.value.size > 0) {
    const first = invalidFields.value.values().next().value
    toast.error(`Vui lòng điền các trường bắt buộc (${invalidFields.value.size} trường thiếu)`)
    nextTick(() => {
      const el = document.querySelector(`[data-field="${first}"]`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        const input = el.querySelector('input, select, textarea')
        if (input) input.focus()
      }
    })
    return false
  }
  return true
}

function validateAndSubmit() {
  if (!validate()) return
  emit('submit')
}

defineExpose({ validate })

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

// L04: addYears cho date yyyy-mm-dd
function addYears(ymd, n) {
  if (!ymd) return ymd
  const [y, m, d] = String(ymd).split('-').map(Number)
  if (!y) return ymd
  const dt = new Date(Date.UTC(y, (m || 1) - 1, d || 1))
  dt.setUTCFullYear(dt.getUTCFullYear() + n)
  return dt.toISOString().slice(0, 10)
}

// Schema-driven derive: field nguồn khai báo `derive: [{target, op}]`
// op: 'copy' | 'plus1year'. Áp khi field nguồn đổi (vẫn cho user sửa target sau đó).
function applyDerives(next, name, value) {
  for (const sec of (schema.value?.sections || [])) {
    for (const f of sec.fields) {
      if (f.name !== name || !f.derive || !value) continue
      for (const d of f.derive) {
        if (d.op === 'copy') next[d.target] = value
        else if (d.op === 'plus1year') next[d.target] = addYears(value, 1)
      }
    }
  }
}

function updateField(name, value) {
  const next = { ...doc.value, [name]: value }
  applyDerives(next, name, value)
  // Bảng con → cộng dồn vào field header (vd Σ Số tiền phân bổ → Số tiền phiếu
  // thanh toán). Cấu hình: schema.items.sumInto = { column, target }
  const si = schema.value?.items
  if (si && name === si.field && si.sumInto && Array.isArray(value)) {
    next[si.sumInto.target] = value.reduce((s, r) => s + Number(r[si.sumInto.column] || 0), 0)
  }
  emit('update:modelValue', next)
}

// Khoá chi tiết theo HĐ khung (đơn bán): local ref (KHÔNG lưu DB, KHÔNG suy từ
// việc framework_contract có giá trị — vì "Đặt lại" phải mở khoá mà VẪN giữ HĐ
// khung để bộ lọc vật tư còn hiệu lực). Chọn HĐ khung → true; Đặt lại → false.
const fcLocked = ref(false)
onMounted(() => { if (doc.value?.framework_contract) fcLocked.value = true })
function resetFcLock() { fcLocked.value = false }
// Xoá HĐ khung → mở khoá luôn (tránh kẹt: khoá còn nhưng không còn nút Đặt lại).
// CHỈ mở khi rỗng — KHÔNG tự khoá lại khi có giá trị (Đặt lại phải giữ mở).
watch(() => doc.value?.framework_contract, (v) => { if (!v) fcLocked.value = false })

async function handleLinkSelected(field, linked) {
  if (!linked?.name) return
  const patch = {}
  // 1) Tự điền 1 field (vd Khách hàng lấy từ HĐ khung)
  if (field.fetchFrom) {
    try {
      const d = await call('frappe.client.get_value', {
        doctype: field.fetchFrom.target_doctype,
        filters: { name: linked.name },
        fieldname: field.fetchFrom.target_field,
      })
      const v = d?.[field.fetchFrom.target_field]
      if (v != null) patch[field.fetchFrom.target_field] = v
    } catch (e) {}
  }
  // 2) Nạp chi tiết vật tư từ HĐ khung → điền vào bảng & khoá lại
  if (field.loadItemsFrom) {
    const lf = field.loadItemsFrom
    try {
      const rows = await call(lf.api, { [lf.arg]: linked.name })
      const items = (rows || []).map(src => {
        const r = {}
        for (const [tgt, srcKey] of Object.entries(lf.map)) r[tgt] = src[srcKey]
        r.qty = r.qty ?? 0
        r.amount = Number(r.qty || 0) * Number(r.unit_price || 0)  // qty=0 → 0, cập nhật khi nhập SL
        return r
      })
      if (schema.value?.items?.field) patch[schema.value.items.field] = items
      fcLocked.value = true
    } catch (e) {
      toast.error(`Không nạp được vật tư từ HĐ khung: ${e.message}`)
    }
  }
  if (Object.keys(patch).length) {
    const next = { ...doc.value, ...patch }
    // sumInto: vừa nạp bảng con → cập nhật tổng ở header
    const si = schema.value?.items
    if (si?.sumInto && patch[si.field]) {
      next[si.sumInto.target] = patch[si.field].reduce((s, r) => s + Number(r[si.sumInto.column] || 0), 0)
    }
    emit('update:modelValue', next)
  }
}

function isVisible(field) {
  if (!field.dependOn) return true
  const dep = field.dependOn
  // Hỗ trợ biểu thức "eval:<expr>" (truy cập doc.*) bên cạnh tên field đơn.
  if (typeof dep === 'string' && dep.startsWith('eval:')) {
    try {
      // eslint-disable-next-line no-new-func
      return !!(new Function('doc', `return (${dep.slice(5)})`))(doc.value)
    } catch (e) {
      return true
    }
  }
  return !!doc.value[dep]
}

// Field bị khoá khi field nguồn (readonlyWhenSet) đã có giá trị — vd PO tạo từ
// HĐ khung: chọn framework_contract xong thì khoá luôn supplier + framework_contract.
function fieldReadonly(field) {
  if (props.readonly || field.readonly) return true
  if (field.readonlyWhenSet && doc.value[field.readonlyWhenSet]) return true
  return false
}
</script>

<template>
  <div v-if="!schema" class="sc-card p-6 text-center text-sc-text-muted">
    Chưa có form schema cho {{ doctype }}
  </div>
  <form v-else @submit.prevent="validateAndSubmit">
    <div v-for="(section, si) in schema.sections" :key="si"
      class="sc-card p-5 mb-4">
      <h3 class="font-semibold text-sc-navy mb-4">{{ section.title }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <template v-for="f in section.fields" :key="f.name">
          <div v-if="isVisible(f)"
            :data-field="f.name"
            :class="[
              ['Small Text','Long Text','Text'].includes(f.type) ? 'md:col-span-2' : '',
              isFieldInvalid(f) ? 'sc-field-invalid' : '',
            ]">
            <FormField :model-value="doc[f.name]"
              :field="f" :context="doc" :readonly="fieldReadonly(f)"
              @update:model-value="v => updateField(f.name, v)"
              @selected="linked => handleLinkSelected(f, linked)"
              @create-new="(payload) => emit('createNew', payload?.field ? payload : { field: f, ...(payload || {}) })" />
            <div v-if="isFieldInvalid(f)" class="text-xs text-sc-danger mt-1">
              Trường bắt buộc — vui lòng điền giá trị.
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="schema.items" class="sc-card p-5 mb-4">
      <!-- Đơn bán có HĐ khung: báo trạng thái khoá + nút Đặt lại để mở sửa -->
      <div v-if="doc.framework_contract" class="flex items-center justify-between mb-3 gap-2 flex-wrap">
        <span class="text-xs px-2 py-1 rounded"
          :class="fcLocked ? 'bg-sc-royal-50 text-sc-royal' : 'bg-sc-warning-50 text-sc-warning'">
          <template v-if="fcLocked">🔒 Chi tiết khoá theo HĐ khung — bấm "Đặt lại" để sửa</template>
          <template v-else>✏️ Đang cho sửa — ô Vật tư chỉ hiện hàng trong HĐ khung</template>
        </span>
        <button v-if="fcLocked && !readonly" @click="resetFcLock" type="button" class="sc-btn-secondary text-xs">
          <Icon name="unlock" :size="13" /> Đặt lại để sửa
        </button>
      </div>
      <ChildTable :model-value="doc[schema.items.field] || []"
        :schema="schema.items" :readonly="readonly" :parent-doc="doc" :doctype="doctype"
        :lock-cols="fcLocked"
        @update:model-value="v => updateField(schema.items.field, v)"
        @create-new="(p) => emit('createNew', p)" />
    </div>
  </form>
</template>
