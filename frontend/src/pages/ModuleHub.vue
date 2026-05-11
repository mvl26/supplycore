<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MODULES, MODULE_DOCTYPES, DT } from '../modules'
import { getList, count } from '../api'
import PageHeader from '../components/PageHeader.vue'
import DataTable from '../components/DataTable.vue'

const route = useRoute()
const router = useRouter()
const moduleId = computed(() => `m${route.params.n}`)
const moduleInfo = computed(() => MODULES.find(m => m.id === moduleId.value))
const doctypes = computed(() => MODULE_DOCTYPES[moduleId.value] || [])

const activeDt = ref(null)
const activeMeta = computed(() => doctypes.value.find(d => d.dt === activeDt.value))
const rows = ref([])
const counts = ref({})
const loading = ref(false)

async function loadCounts() {
  counts.value = {}
  // Unique doctypes (cùng dt có thể xuất hiện 2 lần qua extraModules)
  const seen = new Set()
  for (const d of doctypes.value) {
    if (seen.has(d.dt)) continue
    seen.add(d.dt)
    try { counts.value[d.dt] = await count(d.dt, d.defaultFilters ? Object.fromEntries(d.defaultFilters.map(f => [f[0], f[2]])) : {}) }
    catch { counts.value[d.dt] = '—' }
  }
}

async function loadRows() {
  if (!activeDt.value || !DT[activeDt.value]) return
  loading.value = true
  try {
    const meta = activeMeta.value || {}
    rows.value = await getList(activeDt.value, {
      fields: DT[activeDt.value].listFields,
      filters: meta.defaultFilters || [],
      order_by: meta.defaultOrderBy || 'modified desc',
      limit: 10,
    })
  } catch (e) {
    rows.value = []
  } finally {
    loading.value = false
  }
}

function init() {
  activeDt.value = doctypes.value[0]?.dt || null
  loadCounts()
  loadRows()
}

watch(moduleId, init)
watch(activeDt, loadRows)
onMounted(init)

function openRow(r) {
  router.push(`/doc/${encodeURIComponent(activeDt.value)}/${encodeURIComponent(r.name)}`)
}
function gotoList(dt) {
  router.push(`/list/${encodeURIComponent(dt)}`)
}
function newDoc(dt) {
  router.push(`/doc/${encodeURIComponent(dt)}/new`)
}
</script>

<template>
  <div v-if="!moduleInfo" class="sc-card p-10 text-center text-sc-text-muted">
    Module không tồn tại
  </div>
  <div v-else>
    <PageHeader :title="moduleInfo.name" :icon="moduleInfo.icon"
      :code="`${moduleInfo.code} · ${moduleInfo.group}`" />

    <!-- Doctype stats với + Tạo mới button -->
    <div v-if="doctypes.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
      <div v-for="d in doctypes" :key="`${d.dt}-${d.label}`"
        class="sc-card overflow-hidden"
        :class="activeDt === d.dt ? 'ring-2 ring-sc-royal' : ''">
        <div @click="activeDt = d.dt" class="p-4 cursor-pointer hover:bg-sc-bg transition">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ d.icon }}</span>
              <div>
                <div class="text-sm font-medium text-sc-text">{{ d.label }}</div>
                <div class="text-xs text-sc-text-muted font-mono">{{ d.dt }}</div>
              </div>
            </div>
            <span class="text-2xl font-bold font-mono text-sc-navy">
              {{ counts[d.dt] ?? '—' }}
            </span>
          </div>
        </div>
        <div class="border-t border-sc-border flex">
          <button @click="newDoc(d.dt)"
            class="flex-1 px-3 py-2 text-xs font-medium text-sc-royal hover:bg-sc-bg transition border-r border-sc-border">
            + Tạo mới
          </button>
          <button @click="gotoList(d.dt)"
            class="flex-1 px-3 py-2 text-xs font-medium text-sc-text-muted hover:bg-sc-bg transition">
            Xem danh sách →
          </button>
        </div>
      </div>
    </div>

    <div v-else class="sc-card p-10 text-center text-sc-text-muted">
      Module này chưa có doctype hoạt động
    </div>

    <!-- Recent rows of active doctype -->
    <div v-if="activeDt && DT[activeDt]" class="sc-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-sc-border">
        <h3 class="font-semibold text-sc-navy">
          {{ activeMeta?.label || DT[activeDt].label }} — 10 gần đây
          <span v-if="activeMeta?.defaultFilters" class="text-xs text-sc-text-muted font-normal ml-2">
            ({{ activeMeta.defaultFilters.map(f => `${f[0]}=${f[2]}`).join(', ') }})
          </span>
        </h3>
        <div class="flex gap-2">
          <button @click="newDoc(activeDt)" class="sc-btn-primary text-xs">+ Tạo mới</button>
          <button @click="gotoList(activeDt)" class="sc-btn-secondary text-xs">Danh sách đầy đủ →</button>
        </div>
      </div>
      <DataTable :rows="rows" :columns="DT[activeDt].listColumns"
        :loading="loading" empty="Chưa có dữ liệu" @rowClick="openRow"
        class="!shadow-none !rounded-none !border-0" />
    </div>
  </div>
</template>
