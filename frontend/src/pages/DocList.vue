<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getList, count } from '../api'
import { DT } from '../modules'
import PageHeader from '../components/PageHeader.vue'
import DataTable from '../components/DataTable.vue'
import FieldInput from '../components/FieldInput.vue'
import { useToastStore } from '../stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const doctype = computed(() => decodeURIComponent(route.params.dt))
const cfg = computed(() => DT[doctype.value])

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const search = ref('')
const limit = ref(50)

async function load() {
  if (!cfg.value) return
  loading.value = true
  try {
    const filters = []
    if (search.value) {
      // Use or_filters via Frappe API
      filters.push(['name', 'like', `%${search.value}%`])
    }
    rows.value = await getList(doctype.value, {
      fields: cfg.value.listFields,
      filters,
      order_by: 'modified desc',
      limit: limit.value,
    })
    total.value = await count(doctype.value, {}).catch(() => rows.value.length)
  } catch (e) {
    toast.error(`Lỗi tải: ${e.message}`)
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(doctype, load)
onMounted(load)

function openRow(r) {
  router.push(`/doc/${encodeURIComponent(doctype.value)}/${encodeURIComponent(r.name)}`)
}

function newDoc() {
  router.push(`/doc/${encodeURIComponent(doctype.value)}/new`)
}
</script>

<template>
  <div v-if="!cfg" class="sc-card p-10 text-center text-sc-text-muted">
    DocType không tồn tại
  </div>
  <div v-else>
    <PageHeader :title="cfg.label" :icon="cfg.icon" :code="doctype" :subtitle="`${total} bản ghi`">
      <template #actions>
        <button @click="load" class="sc-btn-secondary text-sm">↻</button>
        <button @click="newDoc" class="sc-btn-primary text-sm">+ Tạo mới</button>
      </template>
    </PageHeader>

    <div class="sc-card p-3 mb-4 flex items-center gap-3">
      <FieldInput v-model="search" placeholder="Tìm theo mã/tên..." class="flex-1 max-w-sm"
        prefix="🔍" @keyup.enter="load" />
      <select v-model.number="limit" @change="load" class="sc-input max-w-[100px]">
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
        <option :value="200">200</option>
      </select>
    </div>

    <DataTable :rows="rows" :columns="cfg.listColumns" :loading="loading"
      empty="Chưa có bản ghi nào" @rowClick="openRow" />
  </div>
</template>
