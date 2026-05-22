<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { fetchUpstream } from '../api'
import { useToastStore } from '../stores/toast'
import Icon from './Icon.vue'

const props = defineProps({
  targetDoctype: { type: String, required: true },
  // Khi true → ẩn component (doc đã có name)
  hidden: { type: Boolean, default: false },
})
const emit = defineEmits(['merge'])

const toast = useToastStore()
const sources = ref([])
const selectedSource = ref('')
const candidates = ref([])
const search = ref('')
const loading = ref(false)
const fetching = ref(false)
const open = ref(false)

const activeSource = computed(() =>
  sources.value.find(s => s.source_doctype === selectedSource.value))

async function loadSources() {
  try {
    sources.value = await fetchUpstream.sourcesFor(props.targetDoctype)
    if (sources.value.length && !selectedSource.value) {
      selectedSource.value = sources.value[0].source_doctype
    }
  } catch (e) {
    sources.value = []
  }
}

async function loadCandidates() {
  if (!selectedSource.value) return
  loading.value = true
  try {
    candidates.value = await fetchUpstream.listCandidates(
      selectedSource.value, props.targetDoctype, search.value, 20)
  } catch (e) {
    candidates.value = []
    toast.error(`Không tải được: ${e.message}`)
  } finally {
    loading.value = false
  }
}

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadCandidates, 300)
})
watch(selectedSource, loadCandidates)
watch(open, (v) => { if (v) loadCandidates() })

onMounted(loadSources)

async function applyFetch(srcName) {
  fetching.value = true
  try {
    const data = await fetchUpstream.fetch(selectedSource.value, srcName, props.targetDoctype)
    const nItems = (data.items || []).length
    const nHdr = Object.keys(data.header || {}).length
    emit('merge', data)
    toast.success(`Đã lấy ${nItems} dòng + ${nHdr} field từ ${data.source.label} ${data.source.name}`)
    open.value = false
  } catch (e) {
    toast.error(`Fetch lỗi: ${e.message}`)
  } finally {
    fetching.value = false
  }
}

function formatVal(v, key) {
  if (v == null || v === '') return '—'
  if (key.includes('date') || key.includes('_at') || key.includes('_to')) {
    try { return new Date(v).toLocaleDateString('vi-VN') } catch { return v }
  }
  if (key.includes('total') || key.includes('value') || key.includes('amount')) {
    if (typeof v === 'number') return v.toLocaleString('vi-VN')
  }
  return String(v).slice(0, 40)
}
</script>

<template>
  <div v-if="!hidden && sources.length" class="mb-3">
    <!-- Trigger button -->
    <button v-if="!open" @click="open = true" type="button"
      class="sc-btn-secondary text-sm flex items-center gap-2">
      <Icon name="download" :size="15" /> Lấy từ {{ sources.map(s => s.label).join(' / ') }}
    </button>

    <!-- Inline picker -->
    <div v-else class="sc-card border-2 border-sc-royal/30 bg-sc-royal/5 overflow-hidden">
      <header class="px-4 py-2.5 border-b border-sc-border bg-white flex items-center justify-between gap-3">
        <div class="text-sm font-semibold text-sc-navy flex items-center gap-2">
          <Icon name="download" :size="16" /> Lấy dữ liệu từ doc upstream
        </div>
        <button @click="open = false" type="button" class="text-sc-text-muted hover:text-sc-text"><Icon name="x" :size="16" /></button>
      </header>

      <div class="p-4 space-y-3">
        <!-- Source selector -->
        <div class="flex flex-wrap items-center gap-2">
          <label class="text-xs text-sc-text-muted">Loại nguồn:</label>
          <button v-for="s in sources" :key="s.source_doctype" type="button"
            @click="selectedSource = s.source_doctype"
            :class="['px-3 py-1 rounded-md text-sm border transition',
              selectedSource === s.source_doctype
                ? 'bg-sc-royal text-white border-sc-royal'
                : 'bg-white border-sc-border text-sc-text hover:bg-sc-bg']">
            {{ s.label }}
          </button>
        </div>
        <p v-if="activeSource" class="text-xs text-sc-text-muted italic flex items-center gap-1">
          <Icon name="info" :size="13" /> {{ activeSource.description }}
        </p>

        <!-- Search -->
        <input v-model="search" type="text"
          :placeholder="`Tìm ${activeSource?.label || ''}...`"
          class="sc-input w-full text-sm" />

        <!-- Candidates -->
        <div v-if="loading" class="text-sm text-sc-text-muted py-3 text-center">Đang tải…</div>
        <div v-else-if="!candidates.length" class="text-sm text-sc-text-muted py-3 text-center">
          Không có bản ghi nào phù hợp
        </div>
        <div v-else class="border border-sc-border rounded-md max-h-72 overflow-y-auto bg-white">
          <button v-for="c in candidates" :key="c.name" type="button"
            @click="applyFetch(c.name)"
            :disabled="fetching"
            class="w-full text-left px-3 py-2 hover:bg-sc-royal/10 border-b border-sc-border last:border-b-0 transition disabled:opacity-50">
            <div class="font-mono text-xs text-sc-royal font-semibold">{{ c.name }}</div>
            <div class="text-xs text-sc-text-muted flex flex-wrap gap-x-3 mt-0.5">
              <span v-for="k in Object.keys(c).filter(k => !['name','modified'].includes(k))" :key="k">
                <span class="text-sc-text-muted">{{ k }}:</span>
                <b class="text-sc-text ml-0.5">{{ formatVal(c[k], k) }}</b>
              </span>
            </div>
          </button>
        </div>
        <div v-if="fetching" class="text-xs text-sc-royal font-medium">Đang fetch...</div>
      </div>
    </div>
  </div>
</template>
