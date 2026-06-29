<template>
  <div class="m-state">
    <div class="m-state__icon" style="background:var(--m-crit-bg);color:var(--m-crit)"><Icon name="alert-triangle" :size="26" /></div>
    <div class="m-state__title">{{ title }}</div>
    <div v-if="message" class="m-state__sub">{{ message }}</div>
    <button class="m-btn m-btn--ghost m-btn--sm" style="margin-top:6px" @click="$emit('retry')">
      <Icon name="rotate-cw" :size="16" /> Thử lại
    </button>
  </div>
</template>

<script setup>
import Icon from '../../components/Icon.vue'
defineProps({
  title: { type: String, default: 'Không tải được dữ liệu' },
  message: { type: String, default: '' },
})
defineEmits(['retry'])
</script>
