<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { warehouseMap } from '../api'
import PageHeader from '../components/PageHeader.vue'
import MapView from '../components/MapView.vue'
import Icon from '../components/Icon.vue'
import { useToastStore } from '../stores/toast'

const router = useRouter()
const toast = useToastStore()

const tab = ref('site')          // 'site' | 'warehouse'
const loading = ref(false)
const siteMap = ref(null)
const whMap = ref(null)
const mappedWarehouses = ref([])
const selectedWh = ref('')

async function loadSite(targetWh = null) {
  loading.value = true
  try {
    siteMap.value = await warehouseMap.site(targetWh)
  } catch (e) {
    toast.error(`Lỗi tải bản đồ khuôn viên: ${e.message}`)
  } finally {
    loading.value = false
  }
}

async function loadWarehouse(wh) {
  if (!wh) { whMap.value = null; return }
  loading.value = true
  try {
    whMap.value = await warehouseMap.warehouse(wh)
  } catch (e) {
    toast.error(`Lỗi tải sơ đồ kho: ${e.message}`)
  } finally {
    loading.value = false
  }
}

function onSiteCellClick(cell) {
  if (!cell?.warehouse) return
  // Click 1 kho trên bản đồ khuôn viên → mở sơ đồ bin của kho đó
  selectedWh.value = cell.warehouse
  tab.value = 'warehouse'
  loadWarehouse(cell.warehouse)
}

function onBinCellClick(cell) {
  if (cell?.bin) router.push(`/doc/Bin Location/${encodeURIComponent(cell.bin)}`)
}

function highlightWarehouse(wh) {
  loadSite(wh)
}

onMounted(async () => {
  await loadSite()
  try {
    mappedWarehouses.value = await warehouseMap.listMapped()
  } catch (e) { mappedWarehouses.value = [] }
})
</script>

<template>
  <PageHeader title="Bản đồ kho" icon="map" code="Warehouse Map"
    subtitle="Bản đồ khuôn viên kho phân phối + sơ đồ vị trí lưu trữ trong từng kho">
  </PageHeader>

  <!-- Tabs -->
  <div class="sc-card mb-4 overflow-hidden">
    <div class="flex">
      <button @click="tab = 'site'"
        class="px-5 py-3 text-sm font-medium border-b-2 transition"
        :class="tab === 'site' ? 'border-sc-royal text-sc-navy bg-sc-bg' : 'border-transparent text-sc-text-muted hover:bg-sc-bg'">
        <Icon name="map" :size="16" /> Bản đồ khuôn viên
      </button>
      <button @click="tab = 'warehouse'"
        class="px-5 py-3 text-sm font-medium border-b-2 transition"
        :class="tab === 'warehouse' ? 'border-sc-royal text-sc-navy bg-sc-bg' : 'border-transparent text-sc-text-muted hover:bg-sc-bg'">
        <Icon name="warehouse" :size="16" /> Sơ đồ trong kho
      </button>
    </div>
  </div>

  <!-- TAB SITE -->
  <div v-if="tab === 'site'" class="space-y-4">
    <div class="sc-card p-3 flex flex-wrap items-center gap-3">
      <label class="text-sm text-sc-text-muted">Chỉ đường tới kho:</label>
      <select :value="siteMap?.target_warehouse || ''"
        @change="highlightWarehouse($event.target.value || null)"
        class="sc-input max-w-xs text-sm">
        <option value="">— Không chỉ đường —</option>
        <option v-for="w in mappedWarehouses" :key="w.name" :value="w.name">
          {{ w.name }}
        </option>
      </select>
      <span class="text-xs text-sc-text-muted">
        Bấm 1 kho trên bản đồ để xem sơ đồ bin bên trong.
      </span>
    </div>

    <div class="sc-card p-4">
      <div v-if="loading" class="text-center py-10 text-sc-text-muted">Đang tải...</div>
      <MapView v-else :map-data="siteMap" :cell-size="96" @cell-click="onSiteCellClick" />
    </div>
  </div>

  <!-- TAB WAREHOUSE -->
  <div v-else class="space-y-4">
    <div class="sc-card p-3 flex flex-wrap items-center gap-3">
      <label class="text-sm text-sc-text-muted">Chọn kho:</label>
      <select v-model="selectedWh" @change="loadWarehouse(selectedWh)"
        class="sc-input max-w-xs text-sm">
        <option value="">— Chọn kho —</option>
        <option v-for="w in mappedWarehouses" :key="w.name" :value="w.name">
          {{ w.name }} ({{ w.map_rows }}×{{ w.map_cols }} ô)
        </option>
      </select>
      <span v-if="whMap" class="text-xs text-sc-text-muted">
        Bấm 1 ô bin để mở chi tiết vị trí lưu trữ.
      </span>
    </div>

    <div class="sc-card p-4">
      <div v-if="loading" class="text-center py-10 text-sc-text-muted">Đang tải...</div>
      <div v-else-if="!whMap" class="text-center py-10 text-sc-text-muted">
        Chọn 1 kho để xem sơ đồ vị trí lưu trữ bên trong.
      </div>
      <MapView v-else :map-data="whMap" :cell-size="96" @cell-click="onBinCellClick" />
    </div>
  </div>
</template>
