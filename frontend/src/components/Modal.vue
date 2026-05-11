<script setup>
defineProps({
  open: Boolean,
  title: String,
  size: { type: String, default: 'md' }, // sm/md/lg/xl
})
const emit = defineEmits(['close'])

const sizeClass = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-4xl' }
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
        @click.self="emit('close')">
        <div class="bg-white rounded-xl shadow-2xl w-full mx-auto" :class="sizeClass[size]">
          <div class="flex items-center justify-between px-5 py-4 border-b border-sc-border">
            <h3 class="font-semibold text-sc-navy">{{ title }}</h3>
            <button @click="emit('close')" class="text-sc-text-muted hover:text-sc-text">✕</button>
          </div>
          <div class="p-5"><slot /></div>
          <div v-if="$slots.footer" class="px-5 py-3 border-t border-sc-border flex justify-end gap-2">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
