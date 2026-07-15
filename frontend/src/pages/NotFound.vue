<script setup>
import { useRoute } from 'vue-router'
import Icon from '../components/Icon.vue'

const route = useRoute()

// T01: gợi ý liên kết đúng. Alias ngữ nghĩa + đích phổ biến.
const SUGGEST = [
  { to: '/', label: 'Tổng quan', icon: 'layout-dashboard' },
  { to: '/inventory', label: 'Tồn kho', icon: 'package' },
  { to: '/contracts', label: 'Hợp đồng khung', icon: 'file-text' },
  { to: '/material-requests', label: 'Yêu cầu mua', icon: 'clipboard-list' },
  { to: '/purchase-orders', label: 'Đơn mua', icon: 'shopping-cart' },
  { to: '/receipts', label: 'Phiếu nhập', icon: 'truck' },
  { to: '/suppliers', label: 'Nhà cung cấp', icon: 'building-2' },
  { to: '/items', label: 'Vật tư', icon: 'pill' },
]
</script>

<template>
  <div class="sc-card p-10 text-center max-w-2xl mx-auto">
    <div class="text-6xl mb-3"><Icon name="search" :size="64" /></div>
    <h2 class="text-xl font-bold text-sc-navy mb-1">Không tìm thấy trang</h2>
    <p class="text-sc-text-muted mb-1">
      URL <code class="font-mono text-sc-danger">{{ route.fullPath }}</code> không tồn tại trong SupplyCore.
    </p>
    <p class="text-sm text-sc-text-muted mb-5">Có thể bạn muốn tới một trong các mục dưới đây:</p>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <router-link v-for="s in SUGGEST" :key="s.to" :to="s.to"
        class="sc-card p-3 hover:border-sc-royal hover:shadow transition flex flex-col items-center gap-2 text-sm">
        <Icon :name="s.icon" :size="22" class="text-sc-royal" />
        <span class="font-medium text-sc-navy">{{ s.label }}</span>
      </router-link>
    </div>

    <router-link to="/" class="sc-btn-primary inline-block">Về Tổng quan</router-link>
  </div>
</template>
