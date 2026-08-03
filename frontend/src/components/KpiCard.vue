<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  label:    String,
  value:    [Number, String],
  unit:     String,
  icon:     String,
  trend:    String,
  trendDir: { type: String, default: 'neutral' },  // up / down / neutral
  variant:  { type: String, default: 'default' },  // default / critical / warning / success
  href:     String,
})

const ACCENT = {
  default:  { tile: 'bg-sc-royal-50 text-sc-royal',   bar: 'bg-sc-royal-light' },
  critical: { tile: 'bg-sc-danger-50 text-sc-danger',       bar: 'bg-sc-danger' },
  warning:  { tile: 'bg-sc-warning-50 text-sc-warning',    bar: 'bg-sc-warning' },
  success:  { tile: 'bg-sc-success-50 text-sc-success',  bar: 'bg-sc-success' },
}
const a = computed(() => ACCENT[props.variant] || ACCENT.default)
</script>

<template>
  <component :is="href ? 'a' : 'div'" :href="href"
    class="sc-card group relative overflow-hidden p-4 block transition-all duration-200 ease-sc
           hover:shadow-sc-md hover:border-sc-border-strong hover:-translate-y-[2px]">
    <!-- accent edge -->
    <span class="absolute left-0 inset-y-0 w-[3px]" :class="a.bar" />

    <div class="flex items-start justify-between gap-3">
      <div class="text-[12.5px] font-medium text-sc-text-muted leading-snug pt-0.5">{{ label }}</div>
      <div v-if="icon"
        class="h-9 w-9 rounded-lg flex items-center justify-center flex-shrink-0
               transition-transform duration-200 ease-sc group-hover:scale-110"
        :class="a.tile">
        <Icon :name="icon" :size="18" />
      </div>
    </div>

    <div class="mt-2.5 flex items-baseline gap-1.5">
      <div class="text-kpi font-bold font-mono text-sc-navy leading-none tracking-tight">{{ value }}</div>
      <div v-if="unit" class="text-xs font-medium text-sc-text-muted">{{ unit }}</div>
    </div>

    <div v-if="trend" class="mt-2 inline-flex items-center gap-1 text-xs font-medium"
      :class="trendDir === 'up' ? 'text-sc-success' : trendDir === 'down' ? 'text-sc-danger' : 'text-sc-text-muted'">
      <Icon v-if="trendDir === 'up'" name="trending-up" :size="14" />
      <Icon v-else-if="trendDir === 'down'" name="trending-down" :size="14" />
      {{ trend }}
    </div>
  </component>
</template>
