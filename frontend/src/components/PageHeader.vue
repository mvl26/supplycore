<script setup>
import Icon from './Icon.vue'

defineProps({
  title:    String,
  subtitle: String,
  icon:     String,
  code:     String,
})
</script>

<template>
  <div class="sc-rise flex flex-col sm:flex-row sm:flex-wrap sm:items-start gap-3 sm:gap-4 mb-6 pb-5 border-b border-sc-border">
    <div class="flex items-start gap-3 sm:gap-4 flex-1 min-w-0">
      <div v-if="icon"
        class="h-11 w-11 sm:h-12 sm:w-12 rounded-xl bg-gradient-to-br from-sc-royal to-sc-navy
               text-white flex items-center justify-center shadow-sc-md flex-shrink-0">
        <Icon :name="icon" :size="24" :stroke-width="1.7" />
      </div>

      <div class="flex-1 min-w-0">
        <div v-if="code" class="mb-1">
          <span class="font-mono text-[10.5px] font-bold tracking-wide uppercase
            text-sc-royal bg-sc-royal-50 rounded px-1.5 py-0.5">{{ code }}</span>
        </div>
        <h1 class="text-lg sm:text-xl md:text-2xl font-bold text-sc-navy leading-tight truncate">{{ title }}</h1>
        <p v-if="subtitle" class="text-[13px] text-sc-text-muted mt-1">{{ subtitle }}</p>
      </div>
    </div>

    <div class="flex items-center gap-2 flex-wrap sc-no-print">
      <slot name="actions" />
    </div>
  </div>
</template>
