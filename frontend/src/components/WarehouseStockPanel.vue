<script setup>
import { ref, watch } from 'vue'
import { call } from '../api'
import { fmtDate, fmtNumber } from '../utils'

const props = defineProps({
  warehouse: String,
  item: { type: String, default: null },
  title: { type: String, default: 'Tồn kho tại kho' },
})

const rows = ref([])
const loading = ref(false)

async function load() {
  if (!props.warehouse) { rows.value = []; return }
  loading.value = true
  try {
    rows.value = await call('supplycore.api.frontend.warehouse_stock_for_item', {
      warehouse: props.warehouse, item: props.item || null,
    })
  } catch (e) {
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => [props.warehouse, props.item], load, { immediate: true })

const totalQty = (r) => r.qty || 0
const isBelowSafety = (r) => r.safety_stock > 0 && r.qty < r.safety_stock
</script>

<template>
  <div v-if="!warehouse" class="sc-card p-4 text-sm text-sc-text-muted">
    Chọn kho để xem tồn
  </div>
  <div v-else class="sc-card overflow-hidden mb-4">
    <div class="flex items-center justify-between px-4 py-3 border-b border-sc-border bg-sc-bg">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        📦 {{ title }} <span class="font-mono text-sm text-sc-text-muted">{{ warehouse }}</span>
      </h3>
      <span class="text-xs text-sc-text-muted">{{ rows.length }} dòng</span>
    </div>
    <div v-if="loading" class="p-6 text-center text-sc-text-muted text-sm">Đang tải...</div>
    <div v-else-if="!rows.length" class="p-6 text-center text-sc-text-muted text-sm">
      Kho trống{{ item ? ` cho vật tư ${item}` : '' }}
    </div>
    <div v-else class="overflow-x-auto">
      <table class="sc-table text-sm">
        <thead>
          <tr>
            <th>Mã VT</th>
            <th>Tên</th>
            <th>Lô</th>
            <th>Vị trí</th>
            <th>KCS</th>
            <th>HD</th>
            <th class="text-right">SL tồn</th>
            <th class="text-right">Tồn an toàn</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, idx) in rows" :key="idx"
            :class="{ 'bg-amber-50': isBelowSafety(r) }">
            <td class="font-mono text-xs">{{ r.item }}</td>
            <td>{{ r.item_name || '—' }}</td>
            <td class="font-mono text-xs">{{ r.batch || '—' }}</td>
            <td>
              <span v-if="r.bin_location" class="font-mono text-xs px-2 py-0.5 bg-sc-bg rounded">
                {{ r.bin_location }}
              </span>
              <span v-else class="text-xs text-sc-text-muted italic">chưa xếp</span>
            </td>
            <td>
              <span v-if="r.qc_status" :class="['sc-badge',
                r.qc_status === 'Accepted' ? 'sc-badge-success' :
                r.qc_status === 'Rejected' ? 'sc-badge-critical' : 'sc-badge-warning']">
                {{ r.qc_status === 'Accepted' ? 'Đạt' : r.qc_status === 'Rejected' ? 'Không đạt' : r.qc_status }}
              </span>
              <span v-if="r.blocked" class="sc-badge sc-badge-critical ml-1">Khoá</span>
            </td>
            <td class="text-xs">{{ r.expiry_date ? fmtDate(r.expiry_date) : '—' }}</td>
            <td class="text-right font-mono font-semibold"
              :class="{ 'text-sc-warning': isBelowSafety(r) }">
              {{ fmtNumber(r.qty) }}
            </td>
            <td class="text-right font-mono text-xs text-sc-text-muted">
              {{ r.safety_stock ? fmtNumber(r.safety_stock) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
