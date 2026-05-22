<script setup>
import Icon from '../components/Icon.vue'
</script>

<template>
  <div class="sc-card p-10 text-center">
    <div class="text-6xl mb-3"><Icon name="search" :size="64" /></div>
    <h2 class="text-xl font-bold text-sc-navy mb-1">Không tìm thấy trang</h2>
    <p class="text-sc-text-muted mb-4">URL bạn truy cập không tồn tại trong SupplyCore.</p>
    <router-link to="/" class="sc-btn-primary inline-block">Về Dashboard</router-link>
  </div>
</template>
