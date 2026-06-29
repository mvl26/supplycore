<template>
  <div class="m-state">
    <div class="m-state__icon"><Icon :name="icon" :size="26" /></div>
    <div class="m-state__title">{{ title }}</div>
    <div v-if="sub" class="m-state__sub">{{ sub }}</div>
    <slot />
  </div>
</template>

<script setup>
import Icon from '../../components/Icon.vue'
defineProps({
  icon: { type: String, default: 'inbox' },
  title: { type: String, default: 'Chưa có dữ liệu' },
  sub: { type: String, default: '' },
})
</script>
