<script setup>
defineProps({
  title:    String,
  subtitle: String,
  icon:     String,
  code:     String,
})
</script>

<template>
  <div class="flex items-center gap-3 mb-5">
    <div v-if="icon" class="w-12 h-12 rounded-lg bg-sc-navy text-white text-xl flex items-center justify-center flex-shrink-0">
      {{ icon }}
    </div>
    <div class="flex-1 min-w-0">
      <div v-if="code" class="text-xs font-mono text-sc-text-muted">{{ code }}</div>
      <h1 class="text-xl font-bold text-sc-navy">{{ title }}</h1>
      <div v-if="subtitle" class="text-sm text-sc-text-muted">{{ subtitle }}</div>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
