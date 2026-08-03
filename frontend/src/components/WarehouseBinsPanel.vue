<script setup>
// Quản lý vị trí lưu trữ (Bin Location) NGAY trên màn Kho: xem danh sách vị trí
// của kho + tạo vị trí mới (đã điền sẵn kho qua ?prefill=).
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getList } from '../api'
import Icon from './Icon.vue'

const props = defineProps({ doc: { type: Object, required: true } })
const router = useRouter()
const bins = ref([])
const loading = ref(false)

async function load() {
  if (!props.doc?.name) return
  loading.value = true
  try {
    bins.value = await getList('Bin Location', {
      filters: [['warehouse', '=', props.doc.name]],
      fields: ['name', 'bin_code', 'barcode', 'status', 'occupancy_pct', 'is_quarantine', 'enabled'],
      order_by: 'bin_code asc', limit: 200,
    })
  } catch (e) {
    bins.value = []
  } finally {
    loading.value = false
  }
}
watch(() => props.doc?.name, load, { immediate: true })

function addBin() {
  const pf = encodeURIComponent(JSON.stringify({ warehouse: props.doc.name }))
  router.push(`/doc/${encodeURIComponent('Bin Location')}/new?prefill=${pf}`)
}
function openBin(name) {
  router.push(`/doc/${encodeURIComponent('Bin Location')}/${encodeURIComponent(name)}`)
}
function viewAll() {
  router.push(`/list/${encodeURIComponent('Bin Location')}`)
}

const statusLabel = (s) => ({ Empty: 'Trống', 'In Use': 'Đang dùng', Full: 'Đầy' }[s] || s || '—')
const statusCls = (s) => ({
  Empty: 'bg-sc-bg text-sc-text-muted', 'In Use': 'bg-sc-royal-50 text-sc-royal', Full: 'bg-sc-warning-50 text-sc-warning',
}[s] || 'bg-sc-bg text-sc-text-muted')

defineExpose({ reload: load })
</script>

<template>
  <div class="sc-card mb-4 overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-sc-border bg-sc-bg gap-2 flex-wrap">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="map-pin" :size="18" /> Vị trí lưu trữ trong kho
        <span class="text-xs font-normal text-sc-text-muted">{{ bins.length }} vị trí</span>
      </h3>
      <div class="flex items-center gap-2">
        <button @click="viewAll" type="button" class="sc-btn-secondary text-xs">Xem tất cả</button>
        <button @click="addBin" type="button" class="sc-btn-primary text-xs">
          <Icon name="plus" :size="13" /> Thêm vị trí
        </button>
      </div>
    </div>
    <div v-if="loading" class="p-4 text-sm text-sc-text-muted">Đang tải…</div>
    <div v-else-if="!bins.length" class="p-6 text-center text-sm text-sc-text-muted">
      Kho này chưa có vị trí nào. Bấm <b>Thêm vị trí</b> để tạo (đã điền sẵn kho).
    </div>
    <div v-else class="divide-y divide-sc-border max-h-[420px] overflow-y-auto">
      <button v-for="b in bins" :key="b.name" type="button" @click="openBin(b.name)"
        class="w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-sc-royal-50/30 text-left">
        <span class="font-mono font-medium">{{ b.bin_code || b.name }}</span>
        <span v-if="b.is_quarantine" class="text-xs px-1.5 py-0.5 rounded bg-sc-warning-50 text-sc-warning">Cách ly</span>
        <span v-if="!b.enabled" class="text-xs text-sc-text-muted">(vô hiệu)</span>
        <span class="text-xs px-2 py-0.5 rounded ml-auto" :class="statusCls(b.status)">{{ statusLabel(b.status) }}</span>
        <span class="text-xs text-sc-text-muted w-12 text-right">{{ Math.round(b.occupancy_pct || 0) }}%</span>
        <Icon name="chevron-right" :size="14" class="text-sc-text-muted" />
      </button>
    </div>
  </div>
</template>
