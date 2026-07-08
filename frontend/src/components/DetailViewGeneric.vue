<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'
import { fmtNumber, fmtVND, fmtVNDShort, fmtDate, fmtDateTime } from '../utils'
import { DETAIL_CONFIGS } from '../detail-configs'

const props = defineProps({
  doctype: { type: String, required: true },
  doc: { type: Object, required: true },
})

const cfg = computed(() => DETAIL_CONFIGS[props.doctype] || null)

function call(fn, doc) {
  if (typeof fn === 'function') {
    try { return fn(doc) } catch (e) { return null }
  }
  return fn
}

function fmt(value, kind) {
  if (value == null || value === '') return '—'
  if (kind === 'money' || kind === 'number') {
    // Nếu value không phải số → trả raw (vd: '—' đã handle ở trên)
    if (typeof value === 'string' && isNaN(Number(value))) return value
    return kind === 'money' ? fmtVND(value) : fmtNumber(value)
  }
  if (kind === 'moneyShort') {
    const n = Number(value)
    if (!Number.isFinite(n)) return value
    return fmtVNDShort(n)
  }
  if (kind === 'pct') {
    const n = Number(value); if (!Number.isFinite(n)) return value
    return n.toFixed(1) + '%'
  }
  if (kind === 'date') return fmtDate(value)
  if (kind === 'datetime') return fmtDateTime(value)
  if (kind === 'check') return value ? 'Có' : '—'
  return value
}

const title = computed(() => call(cfg.value?.title, props.doc))
const subtitleMono = computed(() => call(cfg.value?.subtitleMono, props.doc))
const metaChips = computed(() => {
  const items = cfg.value?.meta || []
  return items.map(m => ({ icon: m.icon, text: call(m.text, props.doc) })).filter(m => m.text)
})
const status = computed(() => call(cfg.value?.status, props.doc) || null)
const tiles = computed(() => (cfg.value?.tiles || []).map(t => ({
  icon: t.icon,
  label: t.label,
  value: call(t.value, props.doc),
  fmt: t.fmt || 'number',
  sublabel: call(t.sublabel, props.doc),
  accent: (typeof t.accent === 'function' ? call(t.accent, props.doc) : t.accent) || 'default',
})))
const sections = computed(() => (cfg.value?.sections || []).map(s => ({
  title: s.title,
  icon: s.icon,
  fields: (s.fields || []).map(f => ({
    label: f.label,
    value: call(f.value, props.doc),
    link: call(f.link, props.doc),
    pre: f.pre,
  })),
})))
const approvalSteps = computed(() => {
  const arr = call(cfg.value?.approval, props.doc)
  return Array.isArray(arr) ? arr : []
})

const items = computed(() => {
  const itemsCfg = cfg.value?.items
  if (!itemsCfg) return null
  const rows = Array.isArray(props.doc[itemsCfg.field]) ? props.doc[itemsCfg.field] : []
  return { cfg: itemsCfg, rows }
})

const totalsRow = computed(() => {
  if (!items.value || !items.value.cfg.totals) return null
  const sums = {}
  for (const r of items.value.rows) {
    for (const col of items.value.cfg.totals) {
      if (!col) continue
      const n = Number(r[col]) || 0
      sums[col] = (sums[col] || 0) + n
    }
  }
  return sums
})

function cellValue(row, col) {
  if (typeof col.accessor === 'function') return col.accessor(row)
  return row[col.accessor]
}

const tileAccentClass = {
  default: 'text-sc-navy',
  emerald: 'text-emerald-700',
  amber:   'text-amber-700',
  royal:   'text-sc-royal',
  critical:'text-sc-critical',
}
const tileCardClass = {
  default: '',
  emerald: 'ring-1 ring-emerald-200/70 bg-emerald-50/30',
  amber:   'ring-1 ring-amber-200/70 bg-amber-50/30',
  royal:   '',
  critical:'ring-1 ring-red-200/70 bg-red-50/30',
}
</script>

<template>
  <div v-if="cfg" class="space-y-4">
    <!-- HERO ===================================================== -->
    <div class="sc-card overflow-hidden">
      <div class="relative px-6 py-5 bg-gradient-to-br from-[#F8FAFD] via-white to-[#EEF4FB]">
        <div class="absolute right-0 top-0 bottom-0 w-1.5
                    bg-gradient-to-b from-sc-navy via-sc-royal to-sc-royal-light opacity-90"></div>

        <div class="grid grid-cols-1 lg:grid-cols-[1fr,auto] gap-4 lg:gap-8 items-start">
          <div class="min-w-0">
            <div class="flex items-center gap-3 mb-2 text-xs">
              <span class="inline-flex items-center gap-1 text-sc-text-muted uppercase tracking-wider">
                <Icon v-if="cfg.icon" :name="cfg.icon" :size="12" /> {{ cfg.accentLabel || doctype }}
              </span>
              <span v-if="subtitleMono" class="text-sc-border">·</span>
              <span v-if="subtitleMono" class="font-mono text-sc-navy">{{ subtitleMono }}</span>
            </div>
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-sc-navy
                          flex items-center justify-center text-white shadow-sc-sm">
                <Icon :name="cfg.icon || 'file'" :size="22" />
              </div>
              <div class="min-w-0 flex-1">
                <h1 class="text-xl font-semibold text-sc-navy leading-tight truncate" :title="title">
                  {{ title || '—' }}
                </h1>
                <div v-if="metaChips.length" class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-sc-text-muted">
                  <span v-for="(m, i) in metaChips" :key="i" class="inline-flex items-center gap-1.5">
                    <Icon v-if="m.icon" :name="m.icon" :size="13" /> {{ m.text }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="status" class="flex flex-col items-start lg:items-end gap-2 pl-16 lg:pl-0">
            <span :class="['sc-badge', status.cls, 'gap-1.5']">
              <Icon v-if="status.icon" :name="status.icon" :size="13" />
              {{ status.label }}
            </span>
            <div v-if="status.sublabel" class="text-xs text-sc-text-muted">{{ status.sublabel }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TILES ==================================================== -->
    <div v-if="tiles.length" class="grid grid-cols-2 gap-3"
      :class="tiles.length >= 4 ? 'lg:grid-cols-4' : tiles.length === 3 ? 'lg:grid-cols-3' : 'lg:grid-cols-2'">
      <div v-for="(t, i) in tiles" :key="i" :class="['sc-card p-4', tileCardClass[t.accent]]">
        <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-sc-text-muted mb-2">
          <Icon v-if="t.icon" :name="t.icon" :size="13" />
          <span>{{ t.label }}</span>
        </div>
        <div :class="['font-mono text-xl font-semibold leading-none', tileAccentClass[t.accent]]">
          {{ fmt(t.value, t.fmt) }}
        </div>
        <div v-if="t.sublabel" class="text-xs text-sc-text-muted mt-1">{{ t.sublabel }}</div>
      </div>
    </div>

    <!-- SECTIONS (left/right grid) =============================== -->
    <div v-if="sections.length" class="grid grid-cols-1 gap-3"
      :class="(sections.length + (approvalSteps.length ? 1 : 0)) >= 2 ? 'lg:grid-cols-2' : ''">
      <div v-for="(s, i) in sections" :key="i" class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy text-sm mb-3 flex items-center gap-2">
          <Icon v-if="s.icon" :name="s.icon" :size="15" /> {{ s.title }}
        </h3>
        <dl class="space-y-2.5 text-sm">
          <div v-for="(f, j) in s.fields" :key="j" class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">{{ f.label }}</dt>
            <dd v-if="f.link" class="min-w-0 flex-1">
              <router-link :to="f.link" class="text-sc-royal hover:text-sc-navy hover:underline break-all">
                {{ f.value || '—' }}
              </router-link>
            </dd>
            <dd v-else-if="f.pre" class="text-sc-text whitespace-pre-line min-w-0 flex-1">{{ f.value || '—' }}</dd>
            <dd v-else class="text-sc-text font-medium break-all min-w-0 flex-1">{{ f.value || '—' }}</dd>
          </div>
        </dl>
      </div>

      <!-- APPROVAL TIMELINE ==================================== -->
      <div v-if="approvalSteps.length" class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy text-sm mb-4 flex items-center gap-2">
          <Icon name="badge-check" :size="15" /> Quy trình phê duyệt
        </h3>
        <ol class="relative space-y-4">
          <li v-for="(s, i) in approvalSteps" :key="i" class="relative pl-8">
            <span v-if="i < approvalSteps.length - 1"
              class="absolute left-[10px] top-6 bottom-[-1rem] w-px"
              :class="s.done ? 'bg-emerald-300' : 'bg-sc-border'"></span>
            <span class="absolute left-0 top-0.5 inline-flex items-center justify-center
                         w-5 h-5 rounded-full ring-2 ring-white"
              :class="s.done ? 'bg-emerald-500 text-white' : 'bg-sc-border text-sc-text-muted'">
              <Icon v-if="s.done" name="check" :size="12" />
              <span v-else class="w-1.5 h-1.5 rounded-full bg-white"></span>
            </span>
            <div class="text-sm font-medium" :class="s.done ? 'text-sc-text' : 'text-sc-text-muted'">
              {{ s.title }}
            </div>
            <div v-if="s.done && (s.by || s.at)" class="mt-0.5 text-xs text-sc-text-muted">
              <span v-if="s.by" class="font-medium text-sc-text">{{ s.by }}</span>
              <span v-if="s.at"> · {{ fmtDateTime(s.at) }}</span>
            </div>
            <div v-if="s.comment" class="mt-1.5 text-xs text-sc-text bg-sc-bg rounded-md
                                          px-2.5 py-1.5 border-l-2 border-sc-royal">
              <Icon name="message-square" :size="11" class="inline mr-1" />{{ s.comment }}
            </div>
          </li>
        </ol>
      </div>
    </div>

    <!-- ITEMS TABLE ============================================ -->
    <div v-if="items && items.cfg" class="sc-card overflow-hidden">
      <div class="flex items-baseline justify-between px-5 pt-5 pb-3">
        <h3 class="font-semibold text-sc-navy text-sm flex items-center gap-2">
          <Icon :name="items.cfg.icon || 'package'" :size="15" />
          {{ items.cfg.label || 'Chi tiết' }}
          <span class="text-sc-text-muted font-normal">({{ items.rows.length }} dòng)</span>
        </h3>
      </div>

      <div v-if="!items.rows.length" class="px-5 pb-5 text-sm text-sc-text-muted">
        Chưa có dòng nào.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th class="w-10 text-center">#</th>
              <th v-for="(col, i) in items.cfg.columns" :key="i"
                :class="[col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : '',
                         col.width ? '' : '']"
                :style="col.width ? `width:${col.width}` : ''">
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in items.rows" :key="idx">
              <td class="text-center text-sc-text-muted font-mono">{{ idx + 1 }}</td>
              <td v-for="(col, i) in items.cfg.columns" :key="i"
                :class="[
                  col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : '',
                  col.mono || col.fmt === 'number' || col.fmt === 'money' ? 'font-mono' : '',
                  col.anchor === 'navy' ? 'text-sc-navy font-semibold' :
                    col.anchor === 'muted' ? 'text-sc-text-muted' : '',
                  col.max ? 'max-w-[260px] truncate' : '',
                ]"
                :title="col.max ? cellValue(row, col) : ''">
                {{ fmt(cellValue(row, col), col.fmt) }}
              </td>
            </tr>
          </tbody>
          <tfoot v-if="items.cfg.totals">
            <tr class="bg-sc-bg border-t-2 border-sc-navy/20">
              <td colspan="1" class="px-4 py-2.5"></td>
              <td v-for="(col, i) in items.cfg.columns" :key="i"
                class="px-4 py-2.5 font-semibold text-sc-navy"
                :class="[col.align === 'right' ? 'text-right font-mono' : '',
                         col.align === 'center' ? 'text-center' : '']">
                <template v-if="i === 0">
                  <span class="inline-flex items-center gap-2">
                    <Icon name="sigma" :size="14" />
                    TỔNG <span class="text-sc-text-muted font-normal">({{ items.rows.length }} dòng)</span>
                  </span>
                </template>
                <template v-else-if="items.cfg.totals[i] && totalsRow">
                  {{ fmt(totalsRow[items.cfg.totals[i]], col.fmt) }}
                </template>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>
