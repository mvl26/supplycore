<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call, getList } from '../api'
import PageHeader from '../components/PageHeader.vue'
import { useToastStore } from '../stores/toast'
import { fmtDate, fmtNumber } from '../utils'

const router = useRouter()
const toast = useToastStore()

const warehouses = ref([])
const filterWh = ref('')
const items = ref([])
const bins = ref([])
const loading = ref(false)
const saving = ref(false)

// Map: sle_name → bin_location
const assignments = ref({})

async function loadWarehouses() {
  warehouses.value = await getList('SC Warehouse', {
    fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 100,
  })
}

async function loadBins() {
  if (!filterWh.value) { bins.value = []; return }
  bins.value = await call('supplycore.api.frontend.bins_for_warehouse',
    { warehouse: filterWh.value })
}

async function loadPending() {
  loading.value = true
  try {
    items.value = await call('supplycore.api.frontend.pending_putaway', {
      warehouse: filterWh.value || null, limit: 100,
    })
    // Reset assignments
    assignments.value = {}
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  } finally {
    loading.value = false
  }
}

watch(filterWh, () => {
  loadBins()
  loadPending()
})

onMounted(async () => {
  await loadWarehouses()
  if (warehouses.value.length) filterWh.value = warehouses.value[0].name
})

const selectedCount = computed(() =>
  Object.values(assignments.value).filter(v => v).length)

async function saveAll() {
  const pairs = Object.entries(assignments.value)
    .filter(([k, v]) => v)
    .map(([sle_name, bin_location]) => ({ sle_name, bin_location }))
  if (!pairs.length) {
    toast.warning('Chưa chọn bin nào')
    return
  }
  saving.value = true
  try {
    const result = await call('supplycore.api.frontend.assign_bin',
      { assignments: pairs })
    toast.success(`✓ Đã xếp ${result.updated} dòng lên kệ`)
    await loadPending()
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <PageHeader title="Phiếu xếp hàng lên kệ (Putaway)" icon="📦"
    code="Bin Assignment"
    :subtitle="`${items.length} dòng chờ xếp${filterWh ? ` tại ${filterWh}` : ''}`">
    <template #actions>
      <button @click="loadPending" class="sc-btn-secondary text-sm">↻ Refresh</button>
      <button @click="saveAll" :disabled="saving || selectedCount === 0"
        class="sc-btn-primary text-sm disabled:opacity-50">
        💾 Lưu {{ selectedCount }} dòng
      </button>
    </template>
  </PageHeader>

  <div class="sc-card p-4 mb-4">
    <label class="text-xs text-sc-text-muted block mb-1">Lọc theo kho</label>
    <select v-model="filterWh" class="sc-input max-w-md">
      <option value="">— Tất cả kho —</option>
      <option v-for="w in warehouses" :key="w.name" :value="w.name">{{ w.name }}</option>
    </select>
  </div>

  <div v-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải...</div>
  <div v-else-if="!items.length" class="sc-card p-10 text-center text-sc-text-muted">
    ✓ Không có hàng chờ xếp lên kệ
    <div class="text-xs mt-1">(Hàng vừa nhận qua PR/SE chưa có bin_location)</div>
  </div>
  <div v-else class="sc-card overflow-hidden">
    <table class="sc-table">
      <thead>
        <tr>
          <th>Chứng từ</th>
          <th>Ngày</th>
          <th>Item</th>
          <th>Tên SP</th>
          <th>Kho</th>
          <th>Lô</th>
          <th>HD</th>
          <th>QC</th>
          <th class="text-right">SL</th>
          <th class="w-48">📍 Chọn Bin</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in items" :key="r.sle_name">
          <td>
            <span class="font-mono text-xs text-sc-royal">{{ r.voucher_no }}</span>
            <div class="text-xs text-sc-text-muted">{{ r.voucher_type.replace('SC ', '') }}</div>
          </td>
          <td class="text-xs">{{ fmtDate(r.posting_date) }}</td>
          <td class="font-mono text-xs">{{ r.item }}</td>
          <td class="text-sm">{{ r.item_name || '—' }}</td>
          <td class="text-xs">{{ r.warehouse }}</td>
          <td class="font-mono text-xs">{{ r.batch || '—' }}</td>
          <td class="text-xs">{{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}</td>
          <td>
            <span v-if="r.qc_status" :class="['sc-badge',
              r.qc_status === 'Accepted' ? 'sc-badge-success' : 'sc-badge-warning']">
              {{ r.qc_status }}
            </span>
          </td>
          <td class="text-right font-mono font-semibold">{{ fmtNumber(r.qty) }}</td>
          <td>
            <select v-model="assignments[r.sle_name]" class="sc-input py-1 text-xs">
              <option value="">— Chọn bin —</option>
              <option v-for="b in bins.filter(b => b.name && (!r.warehouse || true))"
                :key="b.name" :value="b.name">
                {{ b.name }} {{ b.bin_code && b.bin_code !== b.name ? `(${b.bin_code})` : '' }}
              </option>
            </select>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
