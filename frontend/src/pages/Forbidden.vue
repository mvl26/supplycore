<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAccessStore } from '../stores/access'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const access = useAccessStore()

const reason = computed(() => route.query.r || 'Bạn không có phận sự để truy cập khu vực này')
const target = computed(() => route.query.from || '')
</script>

<template>
  <div class="sc-card p-10 text-center max-w-lg mx-auto mt-10">
    <div class="text-6xl mb-3">🛡</div>
    <h2 class="text-xl font-bold text-sc-navy mb-2">403 — Không có quyền</h2>
    <p class="text-sm text-sc-text-muted mb-4">{{ reason }}</p>
    <p v-if="target" class="text-xs text-sc-text-muted mb-4 font-mono">
      Đường dẫn: {{ target }}
    </p>

    <div class="text-xs text-left bg-sc-bg rounded-lg p-3 mb-4 border border-sc-border">
      <div class="font-semibold mb-1">Role hiện tại:</div>
      <div class="flex flex-wrap gap-1">
        <span v-for="r in access.roles.filter(x => x.startsWith('SupplyCore') || ['QC Officer','Pharmacy Officer','Warehouse Officer','BHYT Officer','Department Requester','System Manager'].includes(x))"
          :key="r"
          class="px-1.5 py-0.5 rounded bg-sc-royal/10 text-sc-royal font-medium">
          {{ r }}
        </span>
        <span v-if="!access.roles.length" class="text-sc-text-muted">— chưa load —</span>
      </div>
      <div class="mt-2 text-sc-text-muted">
        Liên hệ <b>SupplyCore Manager</b> để xin thêm role nếu cần.
      </div>
    </div>

    <div class="flex justify-center gap-2">
      <button @click="router.back()" class="sc-btn-secondary text-sm">← Quay lại</button>
      <router-link to="/dashboard" class="sc-btn-primary text-sm">🏠 Về Dashboard</router-link>
    </div>
  </div>
</template>
