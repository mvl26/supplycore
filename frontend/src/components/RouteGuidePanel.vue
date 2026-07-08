<script setup>
import { ref, watch, computed } from 'vue'
import { warehouseMap } from '../api'
import MapView from './MapView.vue'
import Icon from './Icon.vue'
import { useToastStore } from '../stores/toast'

const props = defineProps({
  doctype: { type: String, required: true },
  doc:     { type: Object, required: true },
})
const toast = useToastStore()

const open = ref(true)
const loading = ref(false)
const mapData = ref(null)
const caption = ref('')

// Panel chỉ hiện cho doctype có ngữ cảnh đường đi
const RELEVANT = ['SC Stock Entry', 'Bin Location', 'SC Transfer Request']
const relevant = computed(() => RELEVANT.includes(props.doctype))

async function buildMap() {
  if (!relevant.value || !props.doc) return
  loading.value = true
  mapData.value = null
  try {
    if (props.doctype === 'SC Stock Entry' || props.doctype === 'SC Transfer Request') {
      const from = props.doc.from_warehouse
      const to = props.doc.to_warehouse
      if (from && to) {
        // Chuyển kho — tuyến từ kho nguồn tới kho đích
        mapData.value = await warehouseMap.route(from, to)
        caption.value = `Tuyến chuyển kho: ${from} → ${to}`
      } else if (to) {
        // Nhập kho — chỉ đường tới kho đích
        mapData.value = await warehouseMap.site(to)
        caption.value = `Chỉ đường tới kho nhận: ${to}`
      } else if (from) {
        // Xuất kho (Material Issue) — sơ đồ kho nguồn để biết chỗ lấy hàng
        mapData.value = await warehouseMap.warehouse(from)
        caption.value = `Sơ đồ kho lấy hàng: ${from}`
      }
    } else if (props.doctype === 'Bin Location') {
      if (props.doc.warehouse && props.doc.name) {
        mapData.value = await warehouseMap.warehouse(props.doc.warehouse, props.doc.name)
        caption.value = `Vị trí ô ${props.doc.bin_code || props.doc.name} trong ${props.doc.warehouse}`
      }
    }
  } catch (e) {
    toast.error(`Lỗi tải bản đồ: ${e.message}`)
  } finally {
    loading.value = false
  }
}

watch(() => [props.doctype, props.doc?.name, props.doc?.from_warehouse,
              props.doc?.to_warehouse, props.doc?.warehouse],
  buildMap, { immediate: true })

const hasMap = computed(() => mapData.value && (mapData.value.cells || []).length > 0)
</script>

<template>
  <div v-if="relevant && hasMap" class="sc-card mb-4 overflow-hidden">
    <header class="px-5 py-3 border-b border-sc-border bg-sc-bg flex items-center justify-between cursor-pointer"
      @click="open = !open">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="map" :size="20" /> Bản đồ chỉ đường
        <span class="text-xs font-normal text-sc-text-muted">{{ caption }}</span>
      </h3>
      <span class="text-sc-text-muted"><Icon :name="open ? 'chevron-up' : 'chevron-down'" :size="16" /></span>
    </header>
    <div v-show="open" class="p-4">
      <div v-if="loading" class="text-center py-8 text-sc-text-muted text-sm">Đang tải bản đồ...</div>
      <MapView v-else :map-data="mapData" :cell-size="80" :clickable="false" />
    </div>
  </div>
</template>
