<script setup>
import { statusLabel } from '../modules'
import Icon from './Icon.vue'
import { fmtDate, fmtDateTime } from '../utils'

const props = defineProps({
  rows:    { type: Array, default: () => [] },
  columns: { type: Array, required: true }, // [{key, label, type, format, width, align, sortable}]
  loading: Boolean,
  empty:   { type: String, default: 'Chưa có dữ liệu' },
  rowKey:  { type: String, default: 'name' },
  rowClickable: { type: Boolean, default: true },
  sortKey: { type: String, default: '' },     // current sort column key
  sortDir: { type: String, default: 'desc' }, // 'asc' | 'desc'
})

const emit = defineEmits(['rowClick', 'sort'])

function fmt(value, col) {
  if (value == null) return ''
  if (col.format) return col.format(value)
  if (col.type === 'date' && value) return fmtDate(value)
  if (col.type === 'datetime' && value) return fmtDateTime(value)
  if (col.type === 'currency') return (Number(value) || 0).toLocaleString('vi-VN') + ' ₫'
  if (col.type === 'int') return Number(value).toLocaleString('vi-VN')
  if (col.type === 'badge') {
    const map = col.badgeMap || {}
    const cls = map[value] || 'sc-badge-neutral'
    // QA-BUG-M3-01: truyền col.key để statusLabel pick field-aware label
    // (vd qc_status='Pending' → 'Chờ QC' thay vì 'Chờ duyệt')
    const text = statusLabel(value, col.key) || '—'
    return { __html: `<span class="sc-badge ${cls}">${text}</span>` }
  }
  return value
}

function onHeaderClick(c) {
  if (!c.sortable) return
  let dir = 'asc'
  if (props.sortKey === c.key) dir = props.sortDir === 'asc' ? 'desc' : 'asc'
  emit('sort', { key: c.key, dir })
}
</script>

<template>
  <div class="sc-card overflow-hidden">
    <!-- Loading skeleton -->
    <div v-if="loading" class="p-4 space-y-2.5">
      <div v-for="n in 6" :key="n" class="sc-skeleton h-9 w-full" :style="{ opacity: 1 - n * 0.12 }" />
    </div>

    <!-- Empty -->
    <div v-else-if="!rows.length" class="py-16 flex flex-col items-center gap-3 text-sc-text-muted">
      <div class="h-12 w-12 rounded-xl bg-sc-bg-soft flex items-center justify-center">
        <Icon name="inbox" :size="24" class="text-sc-text-muted/70" />
      </div>
      <span class="text-sm">{{ empty }}</span>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="sc-table">
        <thead>
          <tr>
            <th v-for="c in columns" :key="c.key"
              :style="c.width ? { width: c.width } : {}"
              :class="[
                c.align === 'right' ? 'text-right' : '',
                c.sortable ? 'cursor-pointer select-none hover:text-sc-navy transition-colors' : '',
              ]"
              @click="onHeaderClick(c)">
              <span class="inline-flex items-center gap-1"
                :class="c.align === 'right' ? 'flex-row-reverse' : ''">
                {{ c.label }}
                <template v-if="c.sortable">
                  <Icon v-if="sortKey === c.key"
                    :name="sortDir === 'asc' ? 'chevron-up' : 'chevron-down'"
                    :size="13" class="text-sc-royal" />
                  <Icon v-else name="chevrons-up-down" :size="13" class="text-sc-border-strong" />
                </template>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r[rowKey]"
            :class="rowClickable ? 'cursor-pointer' : ''"
            @click="rowClickable && emit('rowClick', r)">
            <td v-for="c in columns" :key="c.key"
              :class="[c.align === 'right' ? 'text-right' : '', c.mono ? 'font-mono text-xs' : '']">
              <template v-if="c.type === 'badge'">
                <span v-html="fmt(r[c.key], c).__html"></span>
              </template>
              <template v-else-if="c.type === 'check'">
                <Icon v-if="r[c.key]" name="check" :size="16" class="text-sc-success" />
                <span v-else class="text-sc-border-strong">—</span>
              </template>
              <template v-else>
                {{ fmt(r[c.key], c) }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
