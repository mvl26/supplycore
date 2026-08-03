<script setup>
import { ref } from 'vue'
import Modal from './Modal.vue'

const state = ref({ open: false, title: '', message: '', confirmText: 'Xác nhận', cancelText: 'Hủy', variant: 'primary', input: null })
const inputVal = ref('')
const inputErr = ref('')
let resolver = null

// opts.input = { label, placeholder, required } → hiện ô nhập; confirm() resolve
// bằng CHUỖI đã nhập (thay vì true). Không có input → giữ nguyên true/false.
function ask(opts) {
  state.value = { ...state.value, input: null, ...opts, open: true }
  inputVal.value = ''
  inputErr.value = ''
  return new Promise((resolve) => { resolver = resolve })
}

function confirm() {
  if (state.value.input) {
    const v = (inputVal.value || '').trim()
    if (state.value.input.required && !v) { inputErr.value = 'Vui lòng nhập nội dung'; return }
    state.value.open = false; resolver?.(v || true)
    return
  }
  state.value.open = false; resolver?.(true)
}
function cancel() { state.value.open = false; resolver?.(false) }

defineExpose({ ask })
</script>

<template>
  <Modal :open="state.open" :title="state.title" size="sm" @close="cancel">
    <p class="text-sm text-sc-text">{{ state.message }}</p>
    <div v-if="state.input" class="mt-3">
      <label v-if="state.input.label" class="sc-label">{{ state.input.label }}
        <span v-if="state.input.required" class="text-sc-danger">*</span></label>
      <textarea v-model="inputVal" rows="3" class="sc-input"
        :placeholder="state.input.placeholder || ''" @keyup.enter.ctrl="confirm"></textarea>
      <div v-if="inputErr" class="text-xs text-sc-danger mt-1">{{ inputErr }}</div>
    </div>
    <template #footer>
      <button @click="cancel" class="sc-btn-secondary text-sm">{{ state.cancelText }}</button>
      <button @click="confirm"
        :class="state.variant === 'danger' ? 'bg-sc-danger hover:brightness-110 text-white px-4 py-2 rounded-md font-medium' : 'sc-btn-primary text-sm'">
        {{ state.confirmText }}
      </button>
    </template>
  </Modal>
</template>
