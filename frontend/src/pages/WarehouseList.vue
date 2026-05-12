<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '../api'
import PageHeader from '../components/PageHeader.vue'
import { useToastStore } from '../stores/toast'
import { fmtNumber, fmtShort } from '../utils'

const router = useRouter()
const toast = useToastStore()
const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await call('supplycore.api.frontend.warehouse_summary')
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openWarehouse(name) {
  router.push(`/doc/SC%20Warehouse/${encodeURIComponent(name)}`)
}
function openStockBalance(wh) {
  router.push(`/stock-balance?warehouse=${encodeURIComponent(wh)}`)
}
function newWarehouse() {
  router.push('/doc/SC%20Warehouse/new')
}
</script>

<template>
  <PageHeader title="Kho — Tồn kho hiện tại" icon="🏬"
    code="SC Warehouse" :subtitle="`${rows.length} kho hoạt động`">
    <template #actions>
      <button @click="load" class="sc-btn-secondary text-sm">↻</button>
      <button @click="newWarehouse" class="sc-btn-primary text-sm">+ Tạo kho</button>
    </template>
  </PageHeader>

  <div v-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải...</div>
  <div v-else-if="!rows.length" class="sc-card p-10 text-center text-sc-text-muted">
    Chưa có kho hoạt động
  </div>
  <div v-else class="sc-card overflow-hidden">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Tên kho</th>
          <th>Loại</th>
          <th class="text-right">Tổng SL tồn</th>
          <th class="text-right">Số items</th>
          <th class="text-right">Giá trị tồn (VND)</th>
          <th class="w-32"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.name" class="hover:bg-sc-bg">
          <td class="cursor-pointer font-medium text-sc-navy" @click="openWarehouse(r.name)">
            {{ r.name }}
          </td>
          <td>
            <span v-if="r.warehouse_type" class="sc-badge sc-badge-neutral">{{ r.warehouse_type }}</span>
          </td>
          <td class="text-right font-mono">{{ fmtNumber(r.total_qty) }}</td>
          <td class="text-right font-mono">{{ r.distinct_items || 0 }}</td>
          <td class="text-right font-mono font-semibold">{{ fmtShort(r.total_value) }}</td>
          <td>
            <button @click="openStockBalance(r.name)"
              class="text-xs text-sc-royal hover:underline">
              Chi tiết →
            </button>
          </td>
        </tr>
      </tbody>
      <tfoot class="bg-sc-bg font-semibold border-t-2 border-sc-border">
        <tr>
          <td colspan="2">Tổng cộng</td>
          <td class="text-right font-mono">{{ fmtNumber(rows.reduce((s, r) => s + (r.total_qty || 0), 0)) }}</td>
          <td></td>
          <td class="text-right font-mono">{{ fmtShort(rows.reduce((s, r) => s + (r.total_value || 0), 0)) }}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>
