<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows:    { type: Array, default: () => [] },
  columns: { type: Array, required: true }, // [{key, label, type, format, width, align}]
  loading: Boolean,
  empty:   { type: String, default: 'Chưa có dữ liệu' },
  rowKey:  { type: String, default: 'name' },
  rowClickable: { type: Boolean, default: true },
})

const emit = defineEmits(['rowClick'])

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
    return { __html: `<span class="sc-badge ${cls}">${value || '—'}</span>` }
  }
  return value
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
              :class="c.align === 'right' ? 'text-right' : ''">
              {{ c.label }}
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
