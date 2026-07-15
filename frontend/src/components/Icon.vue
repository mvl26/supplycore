<script setup>
import { computed } from 'vue'
import { ICONS } from '../icons'

// Monoline stroke icon. Inherits color via currentColor — set text-* on the
// parent. Falls back to a neutral dot if the name is unknown.
const props = defineProps({
  name:        { type: String, required: true },
  size:        { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 1.75 },
})

const inner = computed(() => ICONS[props.name] || ICONS.dot)
</script>

<template>
  <svg
    :width="size" :height="size" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" :stroke-width="strokeWidth"
    stroke-linecap="round" stroke-linejoin="round"
    class="sc-icon" aria-hidden="true" v-html="inner" />
</template>

<style scoped>
.sc-icon { flex-shrink: 0; display: inline-block; vertical-align: middle; }
</style>
