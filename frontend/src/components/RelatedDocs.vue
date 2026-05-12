<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '../api'
import { fmtDate, fmtNumber, fmtShort } from '../utils'

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
  purchase_orders:      { title: 'Đơn mua hàng (PO)', icon: '🛒', dt: 'SC Purchase Order' },
  material_requests:    { title: 'Yêu cầu mua (MR)',  icon: '📝', dt: 'SC Material Request' },
  purchase_receipts:    { title: 'Phiếu nhập (PR)',   icon: '📦', dt: 'SC Purchase Receipt' },
  quality_inspections:  { title: 'Kiểm tra QC (QI)',  icon: '🔬', dt: 'SC Quality Inspection' },
  batches:              { title: 'Lô đã nhập',         icon: '🏷️', dt: 'SC Batch' },
  purchase_invoices:    { title: 'Hóa đơn mua (PI)',  icon: '🧾', dt: 'SC Purchase Invoice' },
  stock_balance:        { title: 'Tồn kho hiện tại',  icon: '📊', dt: null },
  recent_movements:     { title: 'Sổ kho gần đây',    icon: '📈', dt: 'SC Stock Ledger Entry' },
  movements:            { title: 'Lịch sử SLE',       icon: '📈', dt: 'SC Stock Ledger Entry' },
  recalls:              { title: 'Recall liên quan',  icon: '🚨', dt: 'SC Recall Notice' },
  dispensings:          { title: 'Lịch sử cấp phát',  icon: '💉', dt: 'SC Patient Dispensing' },
  patient_dispensings:  { title: 'Cấp phát BN từ DR', icon: '💉', dt: 'SC Patient Dispensing' },
  framework_contracts:  { title: 'HĐ khung',           icon: '📑', dt: 'Framework Contract' },
  affected_items:       { title: 'Items bị ảnh hưởng',icon: '⚠️', dt: null },
}

function openDoc(dt, recName) {
  if (!dt || !recName) return
  router.push(`/doc/${encodeURIComponent(dt)}/${encodeURIComponent(recName)}`)
}

function fmt(value, key) {
  if (value == null || value === '') return '—'
  if (/_date$/.test(key)) return fmtDate(value)
  if (/total|value|amount|qty|cost|balance|pays/.test(key) && typeof value === 'number') {
    return fmtShort(value)
  }
  if (value === 1) return '✓'
  if (value === 0) return ''
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
          <span class="text-lg">{{ SECTION_LABELS[key]?.icon || '🔗' }}</span>
          <h3 class="font-semibold text-sc-navy">
            {{ SECTION_LABELS[key]?.title || key }}
            <span class="text-xs font-normal text-sc-text-muted ml-1">({{ rows.length }})</span>
          </h3>
        </div>
        <div class="overflow-x-auto">
          <table class="sc-table text-sm">
            <thead>
              <tr>
                <th v-for="c in columnsFor(rows)" :key="c">{{ c.replace(/_/g, ' ') }}</th>
                <th v-if="SECTION_LABELS[key]?.dt" class="w-12"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, idx) in rows" :key="idx"
                :class="SECTION_LABELS[key]?.dt && r.name ? 'cursor-pointer hover:bg-sc-bg' : ''"
                @click="r.name && openDoc(SECTION_LABELS[key]?.dt, r.name)">
                <td v-for="c in columnsFor(rows)" :key="c"
                  :class="[typeof r[c] === 'number' ? 'font-mono text-right' : '',
                            c === 'name' ? 'font-mono text-xs' : '']">
                  {{ fmt(r[c], c) }}
                </td>
                <td v-if="SECTION_LABELS[key]?.dt && r.name" class="text-right">
                  <span class="text-xs text-sc-royal">→</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
