<template>
  <div aria-hidden="true">
    <!-- variant="kpi": lưới 3 cột KPI (khớp .m-kpis) -->
    <template v-if="variant === 'kpi'">
      <div class="m-kpis">
        <div v-for="i in 3" :key="i" class="m-sk m-sk-kpi" />
      </div>
    </template>

    <!-- variant="line": danh sách dòng ngắn -->
    <template v-else-if="variant === 'line'">
      <div class="m-list">
        <div v-for="i in count" :key="i" class="m-sk m-sk-line" />
      </div>
    </template>

    <!-- variant="card" (mặc định): danh sách card cao 92px -->
    <template v-else>
      <div class="m-list">
        <div v-for="i in count" :key="i" class="m-sk m-sk-card" />
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  count:   { type: Number, default: 4 },
  // 'card' → danh sách card | 'kpi' → lưới 3 cột KPI | 'line' → dòng ngắn
  variant: { type: String, default: 'card' },
})
</script>
