<script setup>
defineProps({
  label:    String,
  value:    [Number, String],
  unit:     String,
  icon:     String,
  trend:    String,
  trendDir: { type: String, default: 'neutral' },  // up/down/neutral
  variant:  { type: String, default: 'default' },  // default/critical/warning/success
  href:     String,
})

const variantBorder = {
  default:  'border-sc-border',
  critical: 'border-sc-critical',
  warning:  'border-sc-warning',
  success:  'border-sc-success',
}
</script>

<template>
  <component :is="href ? 'a' : 'div'" :href="href"
    class="sc-card border-l-4 p-4 block hover:shadow-sc-md transition"
    :class="variantBorder[variant]">
    <div class="flex items-start justify-between">
      <div class="text-sm text-sc-text-muted">{{ label }}</div>
      <div v-if="icon" class="text-xl opacity-70">{{ icon }}</div>
    </div>
    <div class="mt-2 flex items-baseline gap-1.5">
      <div class="text-kpi font-bold font-mono text-sc-navy leading-none">{{ value }}</div>
      <div v-if="unit" class="text-sm text-sc-text-muted">{{ unit }}</div>
    </div>
    <div v-if="trend" class="mt-2 text-xs"
      :class="trendDir === 'up' ? 'text-sc-success' : trendDir === 'down' ? 'text-sc-danger' : 'text-sc-text-muted'">
      <span v-if="trendDir === 'up'">▲</span>
      <span v-else-if="trendDir === 'down'">▼</span>
      {{ trend }}
    </div>
  </component>
</template>
