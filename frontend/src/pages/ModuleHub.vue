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
const rows = ref([])
const counts = ref({})
const loading = ref(false)

async function loadCounts() {
  counts.value = {}
  for (const d of doctypes.value) {
    try { counts.value[d.dt] = await count(d.dt, {}) }
    catch { counts.value[d.dt] = '—' }
  }
}

async function loadRows() {
  if (!activeDt.value || !DT[activeDt.value]) return
  loading.value = true
  try {
    rows.value = await getList(activeDt.value, {
      fields: DT[activeDt.value].listFields,
      order_by: 'modified desc',
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
</script>

<template>
  <div v-if="!moduleInfo" class="sc-card p-10 text-center text-sc-text-muted">
    Module không tồn tại
  </div>
  <div v-else>
    <PageHeader :title="moduleInfo.name" :icon="moduleInfo.icon"
      :code="`${moduleInfo.code} · ${moduleInfo.group}`" />

    <!-- Doctype stats -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-5">
      <div v-for="d in doctypes" :key="d.dt"
        @click="activeDt = d.dt"
        class="sc-card p-4 cursor-pointer hover:shadow-sc-md transition"
        :class="activeDt === d.dt ? 'ring-2 ring-sc-royal' : ''">
        <div class="flex items-center justify-between">
          <span class="text-2xl">{{ d.icon }}</span>
          <span class="text-xs text-sc-text-muted">{{ d.dt }}</span>
        </div>
        <div class="mt-2 text-sm text-sc-text-muted">{{ d.label }}</div>
        <div class="text-2xl font-bold font-mono text-sc-navy mt-1">
          {{ counts[d.dt] ?? '—' }}
        </div>
      </div>
    </div>

    <!-- Recent rows of active doctype -->
    <div v-if="activeDt && DT[activeDt]" class="sc-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-sc-border">
        <h3 class="font-semibold text-sc-navy">
          {{ DT[activeDt].label }} — 10 gần đây
        </h3>
        <button @click="gotoList(activeDt)" class="text-sm text-sc-royal hover:underline">
          Xem tất cả →
        </button>
      </div>
      <DataTable :rows="rows" :columns="DT[activeDt].listColumns"
        :loading="loading" empty="Chưa có dữ liệu" @rowClick="openRow"
        class="!shadow-none !rounded-none !border-0" />
    </div>
  </div>
</template>
