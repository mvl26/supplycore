<script setup>
import Icon from './Icon.vue'
import { useToastStore } from '../stores/toast'
const toast = useToastStore()

const ICON = { success: 'check-circle', warning: 'alert-triangle', error: 'x-circle', info: 'info' }
const STYLE = {
  success: 'bg-emerald-50 text-sc-success ring-emerald-200',
  warning: 'bg-amber-50 text-sc-warning ring-amber-200',
  error:   'bg-red-50 text-sc-danger ring-red-200',
  info:    'bg-sky-50 text-sc-info ring-sky-200',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-[72px] right-4 z-[60] space-y-2.5 max-w-sm w-[calc(100vw-2rem)] sm:w-auto">
      <TransitionGroup name="sc-toast">
        <div v-for="t in toast.toasts" :key="t.id"
          class="flex items-start gap-3 rounded-xl px-3.5 py-3 text-[13px] font-medium
                 shadow-sc-lg ring-1 ring-inset"
          :class="STYLE[t.variant] || STYLE.info">
          <Icon :name="ICON[t.variant] || ICON.info" :size="18" class="mt-px flex-shrink-0" />
          <div class="flex-1 leading-snug">{{ t.msg }}</div>
          <button @click="toast.dismiss(t.id)"
            class="opacity-50 hover:opacity-100 transition-opacity flex-shrink-0 -mr-0.5"
            aria-label="Đóng">
            <Icon name="x" :size="15" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.sc-toast-enter-active { transition: all .3s cubic-bezier(0.22, 1, 0.36, 1); }
.sc-toast-leave-active { transition: all .2s ease; position: absolute; }
.sc-toast-enter-from { opacity: 0; transform: translateX(28px) scale(0.95); }
.sc-toast-leave-to { opacity: 0; transform: translateX(28px); }
.sc-toast-move { transition: transform .25s ease; }
</style>
