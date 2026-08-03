<script setup>
// CR-03 · Modal "Tạo nhanh" dùng chung — tạo bản ghi tham chiếu ngay trên form
// hiện tại (không rời trang) rồi tự chọn vào droplist đang đứng.
import { ref, reactive, computed } from 'vue'
import Modal from './Modal.vue'
import FormField from './FormField.vue'
import { QUICK_CREATE } from '../schemas'
import { createDoc } from '../api'
import { useToastStore } from '../stores/toast'

const props = defineProps({
  doctype: { type: String, required: true },
  prefill: { type: Object, default: () => ({}) },  // vd { supplier_name: 'ABC' } từ text đã gõ
})
const emit = defineEmits(['created', 'close'])
const toast = useToastStore()

const cfg = computed(() => QUICK_CREATE[props.doctype] || { title: `Tạo nhanh ${props.doctype}`, fields: [] })

const form = reactive({})
for (const f of cfg.value.fields) {
  form[f.name] = props.prefill[f.name] ?? f.default ?? ''
}

const busy = ref(false)
const errors = reactive({})

async function save() {
  // Required → hiện lỗi INLINE dưới từng field (không chỉ toast).
  Object.keys(errors).forEach(k => delete errors[k])
  for (const f of cfg.value.fields) {
    if (f.required && !String(form[f.name] ?? '').trim()) {
      errors[f.name] = `Vui lòng nhập: ${f.label}`
    }
  }
  if (Object.keys(errors).length) return
  busy.value = true
  try {
    const payload = {}
    for (const f of cfg.value.fields) {
      if (form[f.name] !== '' && form[f.name] != null) payload[f.name] = form[f.name]
    }
    const doc = await createDoc(props.doctype, payload)
    toast.success(`Đã tạo ${doc.name}`)
    emit('created', { name: doc.name, doc })
  } catch (e) {
    toast.error(`Tạo thất bại: ${e.message || e}`)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Modal :open="true" :title="cfg.title" @close="emit('close')">
    <div class="space-y-3">
      <div v-for="f in cfg.fields" :key="f.name" :class="{ 'sc-field-invalid': errors[f.name] }">
        <FormField :field="f" :model-value="form[f.name]"
          @update:model-value="v => { form[f.name] = v; if (errors[f.name]) delete errors[f.name] }" />
        <div v-if="errors[f.name]" class="text-xs text-sc-danger mt-1">{{ errors[f.name] }}</div>
      </div>
      <div class="flex justify-end gap-2 pt-2 border-t border-sc-border mt-2">
        <button type="button" class="sc-btn-secondary text-sm" :disabled="busy"
          @click="emit('close')">Huỷ</button>
        <button type="button" class="sc-btn-primary text-sm" :disabled="busy" @click="save">
          {{ busy ? 'Đang lưu…' : 'Tạo & chọn' }}
        </button>
      </div>
    </div>
  </Modal>
</template>
