<script setup>
import { ref } from 'vue'
import Modal from './Modal.vue'

const state = ref({ open: false, title: '', message: '', confirmText: 'Xác nhận', cancelText: 'Hủy', variant: 'primary' })
let resolver = null

function ask(opts) {
  state.value = { ...state.value, ...opts, open: true }
  return new Promise((resolve) => { resolver = resolve })
}

function confirm() { state.value.open = false; resolver?.(true) }
function cancel()  { state.value.open = false; resolver?.(false) }

defineExpose({ ask })
</script>

<template>
  <Modal :open="state.open" :title="state.title" size="sm" @close="cancel">
    <p class="text-sm text-sc-text">{{ state.message }}</p>
    <template #footer>
      <button @click="cancel" class="sc-btn-secondary text-sm">{{ state.cancelText }}</button>
      <button @click="confirm"
        :class="state.variant === 'danger' ? 'bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium' : 'sc-btn-primary text-sm'">
        {{ state.confirmText }}
      </button>
    </template>
  </Modal>
</template>
