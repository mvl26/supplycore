<script setup>
import { computed } from 'vue'

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
  <div class="flex flex-wrap items-center justify-between gap-3 px-3 py-2 border-t border-sc-border bg-sc-bg text-sm">
    <div class="flex items-center gap-2 text-sc-text-muted flex-wrap">
      <select :value="pageSize" @change="onPageSizeChange"
        class="sc-input py-1 px-2 text-sm" :disabled="loading"
        title="Số bản ghi mỗi trang">
        <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
      </select>
      <span>mục / trang</span>
      <span class="text-sc-border">·</span>
      <span>Đang xem</span>
      <span class="font-mono">{{ fromIdx.toLocaleString('vi-VN') }}–{{ toIdx.toLocaleString('vi-VN') }}</span>
      <span>trên tổng</span>
      <span class="font-mono font-semibold text-sc-navy">{{ total.toLocaleString('vi-VN') }}</span>
      <span>bản ghi</span>
    </div>

    <div class="flex items-center gap-1">
      <button @click="go(1)" :disabled="loading || currentPage <= 1"
        class="sc-pg-btn" title="Trang đầu">«</button>
      <button @click="go(currentPage - 1)" :disabled="loading || currentPage <= 1"
        class="sc-pg-btn">‹</button>

      <template v-for="(p, idx) in pageList" :key="p">
        <span v-if="idx > 0 && p - pageList[idx - 1] > 1" class="px-1 text-sc-text-muted">…</span>
        <button @click="go(p)" :disabled="loading"
          class="sc-pg-btn"
          :class="p === currentPage ? 'sc-pg-btn-active' : ''">
          {{ p }}
        </button>
      </template>

      <button @click="go(currentPage + 1)" :disabled="loading || currentPage >= totalPages"
        class="sc-pg-btn">›</button>
      <button @click="go(totalPages)" :disabled="loading || currentPage >= totalPages"
        class="sc-pg-btn" title="Trang cuối">»</button>
    </div>
  </div>
</template>

<style scoped>
.sc-pg-btn {
  min-width: 32px;
  padding: 4px 8px;
  border: 1px solid var(--sc-border, #e5e7eb);
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.2;
  color: var(--sc-text, #111827);
  transition: background 120ms, border-color 120ms;
}
.sc-pg-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}
.sc-pg-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.sc-pg-btn-active {
  background: #1F4E79;
  color: #fff;
  border-color: #1F4E79;
}
.sc-pg-btn-active:hover { background: #2E75B6; border-color: #2E75B6; }
</style>
