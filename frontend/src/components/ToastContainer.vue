<script setup>
import { useToastStore } from '../stores/toast'
const toast = useToastStore()

const icon = { success: '✓', warning: '⚠️', error: '✕', info: 'ℹ' }
const cls = {
  success: 'bg-green-50 text-green-800 border-green-200',
  warning: 'bg-amber-50 text-amber-800 border-amber-200',
  error: 'bg-red-50 text-red-800 border-red-200',
  info: 'bg-sky-50 text-sky-800 border-sky-200',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[60] space-y-2 max-w-sm">
      <TransitionGroup name="slide">
        <div v-for="t in toast.toasts" :key="t.id"
          class="border rounded-lg shadow-lg px-4 py-3 flex items-start gap-2 text-sm"
          :class="cls[t.variant] || cls.info">
          <span class="font-bold mt-0.5">{{ icon[t.variant] || icon.info }}</span>
          <div class="flex-1">{{ t.msg }}</div>
          <button @click="toast.dismiss(t.id)" class="opacity-50 hover:opacity-100">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all .2s; }
.slide-enter-from { opacity: 0; transform: translateX(20px); }
.slide-leave-to { opacity: 0; transform: translateX(20px); }
</style>
