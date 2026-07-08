<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  open: Boolean,
  title: String,
  size: { type: String, default: 'md' }, // sm/md/lg/xl
})
const emit = defineEmits(['close'])

// Đóng modal bằng phím Esc (finding từ probe CR-03)
function onKey(e) { if (e.key === 'Escape' && props.open) emit('close') }
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

const sizeClass = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-4xl' }
</script>

<template>
  <Teleport to="body">
    <Transition name="sc-modal">
      <div v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4
               bg-sc-navy-900/55 backdrop-blur-[3px]"
        @click.self="emit('close')">
        <div class="sc-modal-panel bg-sc-surface rounded-2xl shadow-sc-xl w-full mx-auto
          border border-sc-border overflow-hidden" :class="sizeClass[size]">
          <div class="flex items-center justify-between px-5 py-4 border-b border-sc-border">
            <h3 class="font-bold text-[15px] text-sc-navy">{{ title }}</h3>
            <button @click="emit('close')" class="sc-icon-btn -mr-1.5" aria-label="Đóng">
              <Icon name="x" :size="18" />
            </button>
          </div>
          <div class="p-5 max-h-[72vh] overflow-y-auto"><slot /></div>
          <div v-if="$slots.footer"
            class="px-5 py-3.5 border-t border-sc-border bg-sc-bg-soft/60 flex justify-end gap-2">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sc-modal-enter-active { transition: opacity .2s ease; }
.sc-modal-leave-active { transition: opacity .14s ease; }
.sc-modal-enter-from, .sc-modal-leave-to { opacity: 0; }
.sc-modal-enter-active .sc-modal-panel {
  transition: transform .26s cubic-bezier(0.22, 1, 0.36, 1), opacity .26s ease;
}
.sc-modal-enter-from .sc-modal-panel { transform: translateY(16px) scale(0.96); opacity: 0; }
</style>
