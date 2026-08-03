<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  total:      { type: Number, default: 0 },     // tổng số bản ghi (đã filter)
  page:       { type: Number, default: 1 },     // trang hiện tại (1-based)
  pageSize:   { type: Number, default: 20 },
  pageSizes:  { type: Array,  default: () => [10, 20, 50, 100] },
  loading:    { type: Boolean, default: false },
})
const emit = defineEmits(['update:page', 'update:pageSize'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const currentPage = computed(() => Math.min(Math.max(1, props.page), totalPages.value))

const fromIdx = computed(() =>
  props.total === 0 ? 0 : (currentPage.value - 1) * props.pageSize + 1)
const toIdx = computed(() =>
  Math.min(currentPage.value * props.pageSize, props.total))

// Build compact page-number list: 1 … (p-1) p (p+1) … last
const pageList = computed(() => {
  const tp = totalPages.value, cp = currentPage.value
  const out = new Set([1, tp, cp - 1, cp, cp + 1])
  return [...out].filter(p => p >= 1 && p <= tp).sort((a, b) => a - b)
})

function go(p) {
  const np = Math.min(Math.max(1, p), totalPages.value)
  if (np !== currentPage.value) emit('update:page', np)
}

function onPageSizeChange(e) {
  const sz = Number(e.target.value)
  emit('update:pageSize', sz)
  emit('update:page', 1)
}
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5
    border-t border-sc-border bg-sc-bg-soft/60 text-sm">
    <div class="flex items-center gap-2 text-sc-text-muted flex-wrap">
      <select :value="pageSize" @change="onPageSizeChange"
        class="sc-input py-1 px-2 text-sm w-auto" :disabled="loading"
        title="Số bản ghi mỗi trang">
        <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
      </select>
      <span>mục / trang</span>
      <span class="text-sc-border-strong">·</span>
      <span>Đang xem</span>
      <span class="font-mono text-sc-text font-medium">{{ fromIdx.toLocaleString('vi-VN') }}–{{ toIdx.toLocaleString('vi-VN') }}</span>
      <span>trên</span>
      <span class="font-mono font-bold text-sc-navy">{{ total.toLocaleString('vi-VN') }}</span>
      <span>bản ghi</span>
    </div>

    <div class="flex items-center gap-1">
      <button @click="go(1)" :disabled="loading || currentPage <= 1"
        class="sc-pg-btn" title="Trang đầu">
        <Icon name="chevron-left" :size="14" class="-mr-2" /><Icon name="chevron-left" :size="14" />
      </button>
      <button @click="go(currentPage - 1)" :disabled="loading || currentPage <= 1"
        class="sc-pg-btn" title="Trang trước">
        <Icon name="chevron-left" :size="15" />
      </button>

      <template v-for="(p, idx) in pageList" :key="p">
        <span v-if="idx > 0 && p - pageList[idx - 1] > 1" class="px-1 text-sc-text-muted">…</span>
        <button @click="go(p)" :disabled="loading"
          class="sc-pg-btn font-mono"
          :class="p === currentPage ? 'sc-pg-btn-active' : ''">
          {{ p }}
        </button>
      </template>

      <button @click="go(currentPage + 1)" :disabled="loading || currentPage >= totalPages"
        class="sc-pg-btn" title="Trang sau">
        <Icon name="chevron-right" :size="15" />
      </button>
      <button @click="go(totalPages)" :disabled="loading || currentPage >= totalPages"
        class="sc-pg-btn" title="Trang cuối">
        <Icon name="chevron-right" :size="14" class="-mr-2" /><Icon name="chevron-right" :size="14" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.sc-pg-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--sc-border);
  background: var(--sc-surface);
  border-radius: 7px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sc-text);
  transition: background 120ms, border-color 120ms, color 120ms;
}
.sc-pg-btn:hover:not(:disabled) {
  background: var(--sc-royal-50);
  border-color: var(--sc-royal);
  color: var(--sc-royal);
}
.sc-pg-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.35);
  border-color: var(--sc-royal);
}
.sc-pg-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.sc-pg-btn-active,
.sc-pg-btn-active:hover {
  background: var(--sc-navy, #1F4E79);
  color: #fff;
  border-color: var(--sc-navy, #1F4E79);
}
</style>
