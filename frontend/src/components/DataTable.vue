<script setup>
import { statusLabel } from '../modules'

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
  if (col.type === 'date' && value) return new Date(value).toLocaleDateString('vi-VN')
  if (col.type === 'datetime' && value) return new Date(value).toLocaleString('vi-VN')
  if (col.type === 'currency') return new Intl.NumberFormat('vi-VN').format(Number(value) || 0)
  if (col.type === 'int') return Number(value).toLocaleString('vi-VN')
  if (col.type === 'check') return value ? '✓' : ''
  if (col.type === 'badge') {
    const map = col.badgeMap || {}
    const cls = map[value] || 'sc-badge-neutral'
    const text = statusLabel(value) || '—'
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
    <div v-if="loading" class="p-10 text-center text-sc-text-muted text-sm">Đang tải...</div>
    <div v-else-if="!rows.length" class="p-10 text-center text-sc-text-muted text-sm">{{ empty }}</div>
    <div v-else class="overflow-x-auto">
      <table class="sc-table">
        <thead>
          <tr>
            <th v-for="c in columns" :key="c.key"
              :style="c.width ? { width: c.width } : {}"
              :class="[
                c.align === 'right' ? 'text-right' : '',
                c.sortable ? 'cursor-pointer select-none hover:bg-sc-bg' : '',
              ]"
              @click="onHeaderClick(c)">
              <span class="inline-flex items-center gap-1">
                {{ c.label }}
                <template v-if="c.sortable">
                  <span v-if="sortKey === c.key" class="text-sc-royal text-xs">
                    {{ sortDir === 'asc' ? '▲' : '▼' }}
                  </span>
                  <span v-else class="text-sc-border text-xs">⇅</span>
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
