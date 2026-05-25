<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '../api'
import { fmtDate, fmtNumber, fmtShort } from '../utils'
import { fieldLabel } from '../i18n'
import { statusLabel } from '../modules'
import Icon from './Icon.vue'

const props = defineProps({
  doctype: { type: String, required: true },
  name:    { type: String, required: true },
})

const router = useRouter()
const related = ref({})
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    related.value = await call('supplycore.api.frontend.related_docs',
      { doctype: props.doctype, name: props.name })
  } catch (e) {
    related.value = {}
  } finally {
    loading.value = false
  }
}

watch(() => [props.doctype, props.name], load)
onMounted(load)

const SECTION_LABELS = {
  purchase_orders:      { title: 'Đơn mua hàng (PO)', icon: 'shopping-cart', dt: 'SC Purchase Order' },
  material_requests:    { title: 'Yêu cầu mua (MR)',  icon: 'file-text', dt: 'SC Material Request' },
  purchase_receipts:    { title: 'Phiếu nhập (PR)',   icon: 'package', dt: 'SC Purchase Receipt' },
  quality_inspections:  { title: 'Kiểm tra QC (QI)',  icon: 'flask-conical', dt: 'SC Quality Inspection' },
  batches:              { title: 'Lô đã nhập',         icon: 'tag', dt: 'SC Batch' },
  purchase_invoices:    { title: 'Hóa đơn mua (PI)',  icon: 'receipt', dt: 'SC Purchase Invoice' },
  stock_balance:        { title: 'Tồn kho hiện tại',  icon: 'bar-chart', dt: null },
  recent_movements:     { title: 'Sổ kho gần đây',    icon: 'trending-up', dt: 'SC Stock Ledger Entry' },
  movements:            { title: 'Lịch sử SLE',       icon: 'trending-up', dt: 'SC Stock Ledger Entry' },
  recalls:              { title: 'Recall liên quan',  icon: 'siren', dt: 'SC Recall Notice' },
  dispensings:          { title: 'Lịch sử cấp phát',  icon: 'syringe', dt: 'SC Patient Dispensing' },
  patient_dispensings:  { title: 'Cấp phát BN từ DR', icon: 'syringe', dt: 'SC Patient Dispensing' },
  framework_contracts:  { title: 'HĐ khung',           icon: 'file-text', dt: 'Framework Contract' },
  affected_items:       { title: 'Vật tư bị ảnh hưởng', icon: 'alert-triangle', dt: null },
}

const STATUS_KEYS = new Set(['status', 'qc_status', 'overall_status', 'severity',
  'request_type', 'warehouse_type', 'entry_type', 'alert_type', 'bhyt_type'])

// Per-section item navigation override (vd stock_balance click → batch detail)
const NAV_OVERRIDE = {
  stock_balance: (row) => row.batch ? `/doc/SC Batch/${encodeURIComponent(row.batch)}` :
                          row.item ? `/doc/SC Item/${encodeURIComponent(row.item)}` : null,
}

function openDoc(dt, recName) {
  if (!dt || !recName) return
  router.push(`/doc/${encodeURIComponent(dt)}/${encodeURIComponent(recName)}`)
}

function rowClick(sectionKey, row) {
  const override = NAV_OVERRIDE[sectionKey]
  if (override) {
    const url = override(row)
    if (url) { router.push(url); return }
  }
  const dt = SECTION_LABELS[sectionKey]?.dt
  if (dt && row.name) openDoc(dt, row.name)
}

function fmt(value, key) {
  if (value == null || value === '') return '—'
  if (/_date$/.test(key)) return fmtDate(value)
  if (STATUS_KEYS.has(key) && typeof value === 'string') return statusLabel(value, key)
  if (/total|value|amount|qty|cost|balance|pays/.test(key) && typeof value === 'number') {
    return fmtShort(value)
  }
  if (value === 1) return 'Có'
  if (value === 0) return '—'
  return value
}

function columnsFor(rows) {
  if (!rows.length) return []
  const skip = new Set(['name', 'doctype', 'parent', 'idx', 'creation', 'modified',
                          'modified_by', 'owner', 'docstatus'])
  const keys = Object.keys(rows[0]).filter(k => !skip.has(k))
  return keys.slice(0, 6)
}
</script>

<template>
  <div v-if="loading" class="text-sm text-sc-text-muted px-5 py-3">Đang tải tham chiếu...</div>
  <div v-else>
    <div v-for="(rows, key) in related" :key="key">
      <div v-if="Array.isArray(rows) && rows.length" class="sc-card mb-4 overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-3 border-b border-sc-border">
          <Icon :name="SECTION_LABELS[key]?.icon || 'link'" :size="18" />
          <h3 class="font-semibold text-sc-navy">
            {{ SECTION_LABELS[key]?.title || key }}
            <span class="text-xs font-normal text-sc-text-muted ml-1">({{ rows.length }})</span>
          </h3>
        </div>
        <div class="overflow-x-auto">
          <table class="sc-table text-sm">
            <thead>
              <tr>
                <th v-for="c in columnsFor(rows)" :key="c">{{ fieldLabel(c) }}</th>
                <th v-if="SECTION_LABELS[key]?.dt" class="w-12"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, idx) in rows" :key="idx"
                :class="(NAV_OVERRIDE[key] || SECTION_LABELS[key]?.dt) ? 'cursor-pointer hover:bg-sc-bg' : ''"
                @click="rowClick(key, r)">
                <td v-for="c in columnsFor(rows)" :key="c"
                  :class="[typeof r[c] === 'number' ? 'font-mono text-right' : '',
                            c === 'name' ? 'font-mono text-xs' : '']">
                  {{ fmt(r[c], c) }}
                </td>
                <td v-if="SECTION_LABELS[key]?.dt && r.name" class="text-right">
                  <span class="text-sc-royal"><Icon name="arrow-right" :size="12" /></span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
