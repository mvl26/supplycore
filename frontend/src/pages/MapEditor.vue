<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from '../api'
import { useToastStore } from '../stores/toast'
import PageHeader from '../components/PageHeader.vue'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'

const toast = useToastStore()
const loading = ref(false)
const saving = ref(false)

const config = ref({
  site_name: '', site_address: '',
  site_map_rows: 6, site_map_cols: 5,
  site_entrance_row: 5, site_entrance_col: 3,
  site_entrance_label: 'Cổng chính',
})

// state for warehouse placements (in-memory mutable copy)
// each item: { name, warehouse_type, site_row, site_col, site_block, department, dirty }
const warehouses = ref([])

// Mode chỉnh sửa: 'place' (mặc định click ô để add/edit) | 'entrance' (click để đặt cổng)
const mode = ref('place')

const cellModal = ref(null)  // { row, col, existing? }

const TYPE_META = {
  Main:       { color: '#1F4E79', label: 'Kho tổng',     icon: 'building-2' },
  Sub:        { color: '#2E75B6', label: 'Kho con',      icon: 'package' },
  Department: { color: '#5B9BD5', label: 'Kho khoa',     icon: 'heart-pulse' },
  Quarantine: { color: '#C55A11', label: 'Cách ly',      icon: 'alert-triangle' },
  Transit:    { color: '#7F7F7F', label: 'Trung chuyển', icon: 'arrow-left-right' },
}

const placedByCell = computed(() => {
  const m = {}
  for (const w of warehouses.value) {
    if (w.site_row && w.site_col) {
      m[`${w.site_row}-${w.site_col}`] = w
    }
  }
  return m
})

const unassigned = computed(() =>
  warehouses.value
    .filter(w => !w.site_row || !w.site_col)
    .sort((a, b) => a.name.localeCompare(b.name))
)

const stats = computed(() => {
  const total = warehouses.value.length
  const placed = total - unassigned.value.length
  return { total, placed, unassigned: unassigned.value.length }
})

async function load() {
  loading.value = true
  try {
    const d = await call('supplycore.api.warehouse_map.get_editable_site_map')
    config.value = { ...config.value, ...d.config }
    warehouses.value = (d.warehouses || []).map(w => ({ ...w }))
  } catch (e) {
    toast.error(`Không tải được: ${e.message}`)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function onCellClick(row, col) {
  if (mode.value === 'entrance') {
    config.value.site_entrance_row = row
    config.value.site_entrance_col = col
    mode.value = 'place'
    toast.success(`Đã đặt cổng tại ô (${row}, ${col})`)
    return
  }
  const existing = placedByCell.value[`${row}-${col}`]
  cellModal.value = { row, col, existing }
}

function placePicked(whName, type) {
  if (!whName) return
  const w = warehouses.value.find(x => x.name === whName)
  if (!w) return
  w.site_row = cellModal.value.row
  w.site_col = cellModal.value.col
  if (type) w.warehouse_type = type
  cellModal.value = null
}

function editTypeInModal(type) {
  if (!cellModal.value?.existing) return
  cellModal.value.existing.warehouse_type = type
}

function removeFromCell() {
  const w = cellModal.value?.existing
  if (!w) return
  w.site_row = null
  w.site_col = null
  cellModal.value = null
}

async function save() {
  saving.value = true
  try {
    // Build payload — only send placed (with coords) + recently-cleared
    const payload = warehouses.value
      .filter(w => w.site_row && w.site_col)
      .map(w => ({
        name: w.name,
        site_row: w.site_row,
        site_col: w.site_col,
        warehouse_type: w.warehouse_type,
        site_block: w.site_block || '',
      }))
    // Cleared ones: anything that has no coords now (might have had before)
    // Backend just upserts, no need to send if no change. To handle removals,
    // we send clear=true cho doc đã placed trước nhưng giờ trống.
    const cleared = warehouses.value
      .filter(w => !w.site_row || !w.site_col)
      .map(w => ({ name: w.name, clear: true }))

    const r = await call('supplycore.api.warehouse_map.save_site_layout', {
      config: config.value,
      warehouses: [...payload, ...cleared],
    })
    toast.success(`Đã lưu — ${r.total} kho cập nhật${r.errors?.length ? `, ${r.errors.length} lỗi` : ''}`)
    if (r.errors?.length) {
      console.warn('Map save errors:', r.errors)
    }
    await load()
  } catch (e) {
    toast.error(`Lưu thất bại: ${e.message}`)
  } finally {
    saving.value = false
  }
}

function isEntrance(row, col) {
  return Number(config.value.site_entrance_row) === row
      && Number(config.value.site_entrance_col) === col
}

function gridRows() {
  return Array.from({ length: Math.max(1, Number(config.value.site_map_rows) || 6) }, (_, i) => i + 1)
}
function gridCols() {
  return Array.from({ length: Math.max(1, Number(config.value.site_map_cols) || 5) }, (_, i) => i + 1)
}
</script>

<template>
  <PageHeader title="Bản đồ khuôn viên" icon="map"
    subtitle="Tùy chỉnh sơ đồ kho theo bệnh viện — đặt cổng, sắp xếp kho lên lưới, lưu cấu hình">
    <template #actions>
      <button @click="load" :disabled="loading" class="sc-btn-secondary text-sm">
        <Icon name="refresh-ccw" :size="14" /> Tải lại
      </button>
      <button @click="save" :disabled="saving || loading" class="sc-btn-primary text-sm">
        <template v-if="saving">Đang lưu...</template>
        <template v-else><Icon name="save" :size="14" /> Lưu cấu hình</template>
      </button>
    </template>
  </PageHeader>

  <div v-if="loading" class="sc-card p-10 text-center text-sc-text-muted">Đang tải...</div>

  <div v-else class="space-y-4">
    <!-- =================== CONFIG PANEL =================== -->
    <div class="sc-card p-5">
      <h3 class="font-semibold text-sc-navy text-sm mb-4 flex items-center gap-2">
        <Icon name="building-2" :size="15" /> Thông tin bệnh viện
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
        <label class="flex flex-col gap-1">
          <span class="text-xs uppercase tracking-wider text-sc-text-muted">Tên bệnh viện</span>
          <input v-model="config.site_name"
            class="border border-sc-border rounded-md px-3 py-1.5" placeholder="VD: BV Bạch Mai" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-xs uppercase tracking-wider text-sc-text-muted">Địa chỉ</span>
          <input v-model="config.site_address"
            class="border border-sc-border rounded-md px-3 py-1.5" placeholder="VD: Đống Đa, Hà Nội" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-xs uppercase tracking-wider text-sc-text-muted">Nhãn cổng</span>
          <input v-model="config.site_entrance_label"
            class="border border-sc-border rounded-md px-3 py-1.5" placeholder="Cổng chính" />
        </label>
        <div class="flex gap-2">
          <label class="flex-1 flex flex-col gap-1">
            <span class="text-xs uppercase tracking-wider text-sc-text-muted">Hàng</span>
            <input type="number" v-model.number="config.site_map_rows" min="1" max="40"
              class="border border-sc-border rounded-md px-3 py-1.5 font-mono" />
          </label>
          <label class="flex-1 flex flex-col gap-1">
            <span class="text-xs uppercase tracking-wider text-sc-text-muted">Cột</span>
            <input type="number" v-model.number="config.site_map_cols" min="1" max="40"
              class="border border-sc-border rounded-md px-3 py-1.5 font-mono" />
          </label>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3 mt-4 text-xs">
        <button @click="mode = mode === 'entrance' ? 'place' : 'entrance'"
          :class="[mode === 'entrance' ? 'bg-sc-navy text-white' : 'sc-btn-secondary',
                   'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium']">
          <Icon name="log-out" :size="13" />
          {{ mode === 'entrance' ? 'Click ô để đặt cổng — Esc / click lại để hủy' : 'Đặt vị trí cổng' }}
        </button>
        <span class="text-sc-text-muted">
          Cổng hiện tại: <b class="font-mono text-sc-navy">({{ config.site_entrance_row }}, {{ config.site_entrance_col }})</b>
        </span>
        <span class="text-sc-text-muted">·</span>
        <span class="text-sc-text-muted">
          Kho đã đặt: <b class="text-sc-navy">{{ stats.placed }}</b> / {{ stats.total }} ·
          chưa đặt: <b :class="stats.unassigned > 0 ? 'text-amber-700' : 'text-sc-text-muted'">{{ stats.unassigned }}</b>
        </span>
      </div>
    </div>

    <!-- =================== MAP GRID + UNASSIGNED =================== -->
    <div class="grid grid-cols-1 lg:grid-cols-[1fr,280px] gap-4">
      <!-- Grid -->
      <div class="sc-card p-5">
        <div class="flex items-baseline justify-between mb-3">
          <h3 class="font-semibold text-sc-navy text-sm flex items-center gap-2">
            <Icon name="grid-3x3" :size="15" /> Lưới bản đồ
          </h3>
          <div class="flex flex-wrap gap-3 text-xs">
            <span v-for="(t, k) in TYPE_META" :key="k" class="inline-flex items-center gap-1.5">
              <span class="inline-block w-3 h-3 rounded-sm" :style="{ background: t.color }"></span>
              {{ t.label }}
            </span>
          </div>
        </div>
        <div class="overflow-auto bg-sc-bg rounded-lg p-3">
          <div class="inline-grid gap-1.5"
            :style="{ gridTemplateColumns: `repeat(${config.site_map_cols || 5}, 96px)` }">
            <template v-for="r in gridRows()" :key="`row-${r}`">
              <div v-for="c in gridCols()" :key="`${r}-${c}`"
                @click="onCellClick(r, c)"
                :class="['relative rounded-md flex flex-col items-center justify-center text-center cursor-pointer transition-all',
                  isEntrance(r, c) ? 'ring-2 ring-sc-navy ring-offset-1 bg-sc-navy text-white' :
                  placedByCell[`${r}-${c}`] ? 'shadow-sc-sm hover:shadow-sc-md hover:-translate-y-px' :
                  'border-2 border-dashed border-sc-border bg-white hover:border-sc-royal hover:bg-sc-royal-50/60',
                  mode === 'entrance' ? 'cursor-crosshair' : '',
                ]"
                :style="placedByCell[`${r}-${c}`] && !isEntrance(r, c) ? {
                  background: TYPE_META[placedByCell[`${r}-${c}`].warehouse_type]?.color || '#94a3b8',
                  color: 'white',
                } : {}"
                style="height: 90px"
                :title="`(${r}, ${c})`">

                <!-- Entrance -->
                <template v-if="isEntrance(r, c)">
                  <Icon name="log-out" :size="20" />
                  <span class="text-[10px] mt-1 leading-tight">{{ config.site_entrance_label }}</span>
                </template>

                <!-- Placed warehouse -->
                <template v-else-if="placedByCell[`${r}-${c}`]">
                  <Icon :name="TYPE_META[placedByCell[`${r}-${c}`].warehouse_type]?.icon || 'map-pin'" :size="18" />
                  <span class="text-[10px] font-medium leading-tight mt-0.5 px-1 truncate w-full">
                    {{ placedByCell[`${r}-${c}`].name.replace('Kho ', '') }}
                  </span>
                </template>

                <!-- Empty -->
                <template v-else>
                  <span class="text-sc-text-muted/40 text-xs font-mono">{{ r }}·{{ c }}</span>
                </template>
              </div>
            </template>
          </div>
        </div>
        <p class="text-xs text-sc-text-muted mt-3">
          Click ô trống để thêm kho · click ô có kho để đổi loại / gỡ khỏi bản đồ ·
          chế độ "Đặt cổng" để chuyển vị trí cổng chính.
        </p>
      </div>

      <!-- Unassigned list -->
      <div class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy text-sm mb-3 flex items-center gap-2">
          <Icon name="package-x" :size="15" /> Kho chưa đặt
          <span class="text-sc-text-muted font-normal">({{ unassigned.length }})</span>
        </h3>
        <div v-if="!unassigned.length" class="text-sm text-sc-text-muted py-3">
          Tất cả kho đã được đặt lên bản đồ.
        </div>
        <ul v-else class="space-y-1.5 max-h-[480px] overflow-y-auto">
          <li v-for="w in unassigned" :key="w.name"
            class="px-2.5 py-2 rounded-md bg-sc-bg flex items-start gap-2 text-sm">
            <span class="inline-block w-2.5 h-2.5 rounded-sm mt-1 flex-shrink-0"
              :style="{ background: TYPE_META[w.warehouse_type]?.color || '#94a3b8' }"></span>
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{{ w.name }}</div>
              <div class="text-[11px] text-sc-text-muted">
                {{ TYPE_META[w.warehouse_type]?.label || w.warehouse_type || '—' }}
                <span v-if="w.department"> · {{ w.department }}</span>
              </div>
            </div>
          </li>
        </ul>
        <p class="text-xs text-sc-text-muted mt-3">
          Để đặt kho từ danh sách: click vào ô trống trên lưới rồi chọn kho trong popup.
        </p>
      </div>
    </div>
  </div>

  <!-- =================== CELL MODAL =================== -->
  <Modal :open="!!cellModal" :title="cellModal?.existing
      ? `Sửa ô (${cellModal.row}, ${cellModal.col}) — ${cellModal.existing.name}`
      : `Đặt kho vào ô (${cellModal?.row}, ${cellModal?.col})`"
    size="md" @close="cellModal = null">

    <!-- EDIT existing -->
    <div v-if="cellModal?.existing" class="space-y-4 text-sm">
      <div>
        <div class="text-xs uppercase tracking-wider text-sc-text-muted mb-1.5">Loại kho</div>
        <div class="flex flex-wrap gap-2">
          <button v-for="(t, k) in TYPE_META" :key="k"
            @click="editTypeInModal(k)"
            :class="['inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border-2 transition',
              cellModal.existing.warehouse_type === k ? 'border-sc-navy text-white' : 'border-transparent bg-sc-bg hover:bg-sc-border']"
            :style="cellModal.existing.warehouse_type === k ? { background: t.color } : {}">
            <Icon :name="t.icon" :size="13" /> {{ t.label }}
          </button>
        </div>
      </div>
      <div v-if="cellModal.existing.department">
        <div class="text-xs uppercase tracking-wider text-sc-text-muted">Khoa</div>
        <div class="text-sc-text">{{ cellModal.existing.department }}</div>
      </div>
    </div>

    <!-- PLACE new (pick from unassigned) -->
    <div v-else class="space-y-3 text-sm">
      <div class="text-sc-text-muted">Chọn kho chưa đặt để đưa vào ô này:</div>
      <div v-if="!unassigned.length" class="text-sm text-amber-700 bg-amber-50 p-3 rounded-md">
        Tất cả kho đã được đặt. Để tạo kho mới, dùng trang
        <router-link to="/list/SC Warehouse" class="underline">Danh sách kho</router-link>
        rồi quay lại đây.
      </div>
      <div v-else class="max-h-[360px] overflow-y-auto divide-y divide-sc-border border border-sc-border rounded-md">
        <button v-for="w in unassigned" :key="w.name"
          @click="placePicked(w.name)"
          class="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-sc-royal-50/60 text-left">
          <span class="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
            :style="{ background: TYPE_META[w.warehouse_type]?.color || '#94a3b8' }"></span>
          <span class="flex-1 min-w-0">
            <span class="block font-medium truncate">{{ w.name }}</span>
            <span class="block text-[11px] text-sc-text-muted">
              {{ TYPE_META[w.warehouse_type]?.label || '—' }}
            </span>
          </span>
          <Icon name="arrow-right" :size="14" class="text-sc-royal" />
        </button>
      </div>
    </div>

    <template #footer>
      <button v-if="cellModal?.existing" @click="removeFromCell"
        class="bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium">
        <Icon name="trash-2" :size="14" class="inline mr-1" />Gỡ khỏi bản đồ
      </button>
      <button @click="cellModal = null" class="sc-btn-secondary text-sm">
        {{ cellModal?.existing ? 'Xong' : 'Đóng' }}
      </button>
    </template>
  </Modal>
</template>
