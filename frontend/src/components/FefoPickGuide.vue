<script setup>
import { ref, watch } from 'vue'
import { call } from '../api'
import { fmtDate, fmtNumber } from '../utils'

const props = defineProps({
  item: String,
  warehouse: String,
  qtyNeeded: { type: [Number, String], default: 1 },
  autoLoad: { type: Boolean, default: true },
})

const guide = ref(null)
const loading = ref(false)

async function load() {
  if (!props.item || !props.warehouse || !props.qtyNeeded) {
    guide.value = null
    return
  }
  loading.value = true
  try {
    guide.value = await call('supplycore.api.frontend.fefo_pick_guide', {
      item: props.item, warehouse: props.warehouse, qty_needed: props.qtyNeeded,
    })
  } catch (e) {
    guide.value = { error: e.message }
  } finally {
    loading.value = false
  }
}

watch(() => [props.item, props.warehouse, props.qtyNeeded], () => {
  if (props.autoLoad) load()
}, { immediate: true })

defineExpose({ reload: load })

function urgencyClass(days) {
  if (days == null) return ''
  if (days < 30) return 'bg-red-50 border-l-4 border-sc-danger'
  if (days < 90) return 'bg-amber-50 border-l-4 border-sc-warning'
  return ''
}
</script>

<template>
  <div v-if="loading" class="sc-card p-4 text-sm text-sc-text-muted">Đang tính FEFO...</div>
  <div v-else-if="!item || !warehouse" class="sc-card p-4 text-sm text-sc-text-muted">
    Chọn item + kho để xem hướng dẫn FEFO
  </div>
  <div v-else-if="guide?.error" class="sc-card p-4 border-l-4 border-sc-danger text-sm text-sc-danger">
    {{ guide.error }}
  </div>
  <div v-else-if="guide" class="sc-card overflow-hidden mb-4">
    <div class="flex items-center justify-between px-4 py-3 border-b border-sc-border bg-sc-bg">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        🧭 Hướng dẫn lấy hàng (FEFO)
      </h3>
      <span class="text-sm font-mono"
        :class="guide.is_sufficient ? 'text-sc-success font-semibold' : 'text-sc-danger font-semibold'">
        {{ guide.summary }}
      </span>
    </div>

    <div v-if="!guide.picks.length" class="p-6 text-center text-sc-text-muted text-sm">
      Không có lô nào khả dụng (đã hết, blocked, hoặc chưa Accept QC)
    </div>
    <div v-else>
      <div v-for="(p, idx) in guide.picks" :key="idx"
        class="px-4 py-3 border-b border-sc-border last:border-0"
        :class="urgencyClass(p.days_left)">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-sc-navy text-white text-sm font-bold flex items-center justify-center flex-shrink-0">
            {{ idx + 1 }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-3 flex-wrap">
              <span class="font-mono text-xs px-2 py-0.5 bg-sc-royal text-white rounded">
                {{ p.batch }}
              </span>
              <span class="text-sm">📍 <span class="font-medium">{{ p.bin_location }}</span></span>
              <span class="text-sm">📦 Lấy <span class="font-bold font-mono">{{ fmtNumber(p.pick_qty) }}</span> /
                tồn {{ fmtNumber(p.available) }}</span>
              <span v-if="p.days_left != null" class="text-xs"
                :class="p.days_left < 30 ? 'text-sc-danger font-semibold' :
                          p.days_left < 90 ? 'text-sc-warning' : 'text-sc-text-muted'">
                HD {{ fmtDate(p.expiry_date) }} (còn {{ p.days_left }}d)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!guide.is_sufficient && guide.shortage > 0"
      class="bg-red-50 border-t border-red-200 px-4 py-2 text-sm text-sc-danger">
      ⚠ <b>Thiếu {{ fmtNumber(guide.shortage) }} đơn vị</b> — không có đủ tồn kho khả dụng tại {{ warehouse }}
    </div>
  </div>
</template>
