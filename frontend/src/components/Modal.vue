<script setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  open: Boolean,
  title: String,
  size: { type: String, default: 'md' }, // sm/md/lg/xl
})
const emit = defineEmits(['close'])

const panelRef = ref(null)
let lastFocused = null

function focusables() {
  if (!panelRef.value) return []
  return [...panelRef.value.querySelectorAll(
    'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])'
  )].filter(el => el.offsetParent !== null)
}

// Esc đóng + Tab bị GIỮ trong modal (focus-trap) — a11y.
function onKey(e) {
  if (!props.open) return
  if (e.key === 'Escape') { emit('close'); return }
  if (e.key === 'Tab') {
    const f = focusables()
    if (!f.length) { e.preventDefault(); panelRef.value?.focus(); return }
    const first = f[0], last = f[f.length - 1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

// Mở: nhớ focus trước đó rồi focus vào modal. Đóng: trả focus về chỗ cũ.
watch(() => props.open, async (o) => {
  if (o) {
    lastFocused = document.activeElement
    await nextTick()
    ;(focusables()[0] || panelRef.value)?.focus()
  } else if (lastFocused) {
    lastFocused.focus?.()
    lastFocused = null
  }
})

const sizeClass = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-4xl' }
</script>

<template>
  <Teleport to="body">
    <Transition name="sc-modal">
      <div v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4
               bg-sc-navy-900/55 backdrop-blur-[3px]"
        @click.self="emit('close')">
        <div ref="panelRef" tabindex="-1" role="dialog" aria-modal="true" :aria-label="title"
          class="sc-modal-panel bg-sc-surface rounded-2xl shadow-sc-xl w-full mx-auto
          border border-sc-border overflow-hidden focus:outline-none" :class="sizeClass[size]">
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
