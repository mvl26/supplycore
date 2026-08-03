<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  // Response từ warehouse_map API (get_site_map / get_warehouse_map / get_route)
  mapData: { type: Object, default: null },
  // Kích thước ô (px)
  cellSize: { type: Number, default: 84 },
  // Cho click ô
  clickable: { type: Boolean, default: true },
})
const emit = defineEmits(['cellClick'])

const isSite = computed(() => props.mapData?.scope === 'site')
const rows = computed(() => Math.max(1, props.mapData?.rows || 1))
const cols = computed(() => Math.max(1, props.mapData?.cols || 1))

// Map "row-col" → cell
const cellAt = computed(() => {
  const m = {}
  for (const c of props.mapData?.cells || []) {
    m[`${c.row}-${c.col}`] = c
  }
  return m
})

// Set ô thuộc đường đi (path)
const pathSet = computed(() => {
  const s = new Set()
  for (const [r, c] of props.mapData?.path || []) s.add(`${r}-${c}`)
  return s
})

const entranceKey = computed(() => {
  const e = props.mapData?.entrance
  return e ? `${e.row}-${e.col}` : null
})

// Lưới đầy đủ gồm cả row 0 (entrance cho warehouse scope)
const gridRows = computed(() => {
  const minRow = isSite.value ? 1 : 0  // warehouse: entrance ở row 0
  const out = []
  for (let r = minRow; r <= rows.value; r++) out.push(r)
  return out
})
const gridCols = computed(() => {
  const out = []
  for (let c = 1; c <= cols.value; c++) out.push(c)
  return out
})

// Màu ô site theo loại kho
const SITE_TYPE = {
  Main:       { bg: 'var(--sc-navy)', fg: '#fff', icon: 'building-2', label: 'Kho tổng' },
  Sub:        { bg: 'var(--sc-royal)', fg: '#fff', icon: 'package', label: 'Kho con' },
  Department: { bg: 'var(--sc-royal-light)', fg: '#fff', icon: 'heart-pulse', label: 'Kho khoa' },
  Quarantine: { bg: '#C55A11', fg: '#fff', icon: 'alert-triangle', label: 'Cách ly' },
  Transit:    { bg: '#7F7F7F', fg: '#fff', icon: 'arrow-left-right', label: 'Trung chuyển' },
}
// Màu ô bin theo trạng thái
const BIN_STATUS = {
  Empty:    { bg: '#E2EFDA', fg: '#155724', label: 'Trống' },
  'In Use': { bg: '#FFF2CC', fg: '#856404', label: 'Đang dùng' },
  Full:     { bg: '#FCE4D6', fg: '#721C24', label: 'Đầy' },
}

function cellStyle(cell) {
  if (!cell) return { background: '#F8F8F8', border: '1px dashed #ddd' }
  if (isSite.value) {
    const t = SITE_TYPE[cell.type] || { bg: '#BFBFBF', fg: '#fff' }
    return { background: t.bg, color: t.fg }
  }
  if (cell.is_quarantine) return { background: '#FCE9D6', color: '#7D4707' }
  const s = BIN_STATUS[cell.status] || BIN_STATUS.Empty
  return { background: s.bg, color: s.fg }
}

function cellTitle(cell) {
  if (!cell) return ''
  if (isSite.value) {
    return `${cell.warehouse}\n${cell.type} · ${cell.block || ''}`
  }
  return `${cell.bin_code}\nTrạng thái: ${cell.status} · ${cell.occupancy_pct}%`
}

function onClick(cell) {
  if (props.clickable && cell) emit('cellClick', cell)
}

// Legend
const legend = computed(() => {
  if (isSite.value) return Object.entries(SITE_TYPE).map(([k, v]) => ({ ...v, key: k }))
  return [
    ...Object.entries(BIN_STATUS).map(([k, v]) => ({ ...v, bg: v.bg, key: k })),
    { key: 'Q', bg: '#FCE9D6', label: 'Cách ly QC' },
  ]
})
</script>

<template>
  <div v-if="!mapData" class="text-center py-8 text-sc-text-muted text-sm">
    Chưa có dữ liệu bản đồ
  </div>
  <div v-else>
    <!-- Header -->
    <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
      <div class="text-sm">
        <span class="font-semibold text-sc-navy inline-flex items-center gap-1">
          <Icon :name="isSite ? 'map' : 'warehouse'" :size="16" />
          {{ isSite ? mapData.site_name : mapData.warehouse }}
        </span>
        <span v-if="isSite && mapData.site_address" class="text-sc-text-muted ml-1">
          · {{ mapData.site_address }}
        </span>
        <span v-if="!isSite && mapData.block" class="text-sc-text-muted ml-1">
          · {{ mapData.block }}
        </span>
      </div>
      <!-- Legend -->
      <div class="flex flex-wrap gap-2 text-xs">
        <span v-for="l in legend" :key="l.key" class="inline-flex items-center gap-1">
          <span class="inline-block w-3 h-3 rounded-sm" :style="{ background: l.bg }"></span>
          {{ l.label }}
        </span>
      </div>
    </div>

    <!-- Grid -->
    <div class="overflow-auto border border-sc-border rounded-lg bg-sc-bg-soft p-3">
      <div class="inline-grid gap-1"
        :style="{ gridTemplateColumns: `repeat(${cols}, ${cellSize}px)` }">
        <template v-for="r in gridRows" :key="`row-${r}`">
          <div v-for="c in gridCols" :key="`${r}-${c}`"
            class="relative rounded-md flex flex-col items-center justify-center text-center transition"
            :style="{
              height: cellSize + 'px',
              ...cellStyle(cellAt[`${r}-${c}`]),
              cursor: (clickable && cellAt[`${r}-${c}`]) ? 'pointer' : 'default',
            }"
            :class="[
              cellAt[`${r}-${c}`]?.is_target ? 'ring-4 ring-sc-royal ring-offset-1 sc-map-pulse z-10' : '',
              pathSet.has(`${r}-${c}`) && !cellAt[`${r}-${c}`]?.is_target ? 'sc-map-path' : '',
            ]"
            :title="cellTitle(cellAt[`${r}-${c}`])"
            @click="onClick(cellAt[`${r}-${c}`])">

            <!-- Entrance marker -->
            <template v-if="`${r}-${c}` === entranceKey">
              <div class="absolute inset-0 flex flex-col items-center justify-center
                          bg-sc-navy text-white rounded-md">
                <Icon name="log-out" :size="18" />
                <span class="text-[10px] leading-tight">{{ mapData.entrance_label }}</span>
              </div>
            </template>

            <!-- Site cell -->
            <template v-else-if="isSite && cellAt[`${r}-${c}`]">
              <Icon :name="(SITE_TYPE[cellAt[`${r}-${c}`].type] || {}).icon || 'map-pin'" :size="18" />
              <span class="text-[10px] leading-tight font-medium px-1 mt-0.5">
                {{ cellAt[`${r}-${c}`].warehouse.replace('Kho ', '') }}
              </span>
              <span v-if="cellAt[`${r}-${c}`].is_target"
                class="text-[9px] bg-white/25 rounded px-1 mt-0.5">ĐÍCH</span>
            </template>

            <!-- Bin cell -->
            <template v-else-if="!isSite && cellAt[`${r}-${c}`]">
              <span class="text-[11px] font-mono font-semibold leading-tight">
                {{ cellAt[`${r}-${c}`].bin_code }}
              </span>
              <span class="text-[10px] leading-tight">
                {{ cellAt[`${r}-${c}`].occupancy_pct }}%
              </span>
              <span v-if="cellAt[`${r}-${c}`].is_target"
                class="text-[9px] bg-sc-royal text-white rounded px-1 mt-0.5">ĐÍCH</span>
            </template>

            <!-- Path step dot (ô trống thuộc đường đi) -->
            <template v-else-if="pathSet.has(`${r}-${c}`)">
              <span class="text-sc-royal"><Icon name="dot" :size="18" /></span>
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- Route info -->
    <div v-if="mapData.path && mapData.path.length"
      class="mt-2 text-xs text-sc-text-muted flex items-center gap-2">
      <span class="text-sc-royal"><Icon name="arrow-right" :size="14" /></span>
      Tuyến chỉ đường: <b>{{ mapData.path.length }}</b> bước —
      từ <b>{{ mapData.route_from || mapData.entrance_label }}</b>
      tới <b>{{ mapData.target_warehouse || mapData.target_bin || 'đích' }}</b>
    </div>
  </div>
</template>

<style scoped>
.sc-map-path {
  outline: 3px solid rgba(46, 117, 182, 0.55);
  outline-offset: -3px;
}
@keyframes sc-map-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(46, 117, 182, 0.6); }
  50%      { box-shadow: 0 0 0 8px rgba(46, 117, 182, 0); }
}
.sc-map-pulse { animation: sc-map-pulse 1.6s ease-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .sc-map-pulse { animation: none; }
}
</style>
