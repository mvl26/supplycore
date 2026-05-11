<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MODULES, MODULE_DOCTYPES } from '../modules'
import { getList, count } from '../api'

const route = useRoute()
const router = useRouter()
const moduleId = computed(() => `m${route.params.n}`)
const moduleInfo = computed(() => MODULES.find(m => m.id === moduleId.value))
const doctypes = computed(() => MODULE_DOCTYPES[moduleId.value] || [])

const activeTab = ref(0)
const rows = ref([])
const total = ref(0)
const stats = ref({})
const loading = ref(false)
const error = ref(null)

// Per-doctype field config — chỉ trả các field phổ biến
const DT_FIELDS = {
  'Framework Contract':      ['name', 'supplier', 'valid_to', 'total_value', 'remaining_value', 'status'],
  'SC Material Request':     ['name', 'transaction_date', 'warehouse', 'status'],
  'SC Purchase Order':       ['name', 'transaction_date', 'supplier', 'total_value', 'status'],
  'SC Purchase Receipt':     ['name', 'posting_date', 'supplier', 'qc_status', 'is_return'],
  'SC Quality Inspection':   ['name', 'inspection_date', 'item', 'overall_status'],
  'SC Stock Entry':          ['name', 'posting_date', 'entry_type', 'from_warehouse', 'to_warehouse'],
  'SC Transfer Request':     ['name', 'request_date', 'from_warehouse', 'to_warehouse', 'status'],
  'SC Dispensing Request':   ['name', 'request_date', 'department', 'from_warehouse', 'status'],
  'SC Patient Dispensing':   ['name', 'dispensing_date', 'patient', 'patient_name', 'ward'],
  'SC Purchase Invoice':     ['name', 'invoice_date', 'supplier', 'grand_total', 'outstanding_amount', 'status'],
  'SC Payment Entry':        ['name', 'payment_date', 'supplier', 'amount', 'payment_method'],
  'SC GL Entry':             ['name', 'posting_date', 'account', 'debit', 'credit', 'voucher_no'],
  'SC Inventory Count Sheet':['name', 'posting_date', 'warehouse', 'count_type', 'status'],
  'SC Stock Reconciliation': ['name', 'posting_date', 'warehouse', 'total_difference_value', 'status'],
  'SC Batch':                ['name', 'item', 'expiry_date', 'qc_status', 'blocked', 'supplier'],
  'SC Warehouse':            ['name', 'warehouse_name', 'is_group', 'warehouse_type'],
  'SC Stock Ledger Entry':   ['name', 'posting_date', 'item', 'warehouse', 'qty_change', 'voucher_type', 'voucher_no'],
  'SC Recall Notice':        ['name', 'recall_date', 'item', 'batch_no', 'severity', 'status'],
  'SC Investigation Report': ['name', 'investigation_date', 'investigation_type', 'item', 'status'],
  'SC Alert':                ['name', 'alert_date', 'alert_type', 'severity', 'title', 'resolved'],
  'SC Alert Rule':           ['name', 'title', 'alert_type', 'severity', 'enabled', 'frequency'],
}

async function loadTab() {
  if (!doctypes.value[activeTab.value]) return
  loading.value = true; error.value = null
  const dt = doctypes.value[activeTab.value].dt
  try {
    rows.value = await getList(dt, {
      fields: DT_FIELDS[dt] || ['name'],
      order_by: 'modified desc',
      limit: 30,
    })
    total.value = await count(dt, {}).catch(() => rows.value.length)
  } catch (e) {
    error.value = e.message
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  stats.value = {}
  for (const d of doctypes.value) {
    try {
      stats.value[d.dt] = await count(d.dt, {})
    } catch (e) {
      stats.value[d.dt] = '—'
    }
  }
}

watch(activeTab, loadTab)
watch(moduleId, () => {
  activeTab.value = 0
  loadStats()
  loadTab()
})

onMounted(() => { loadStats(); loadTab() })

function deskUrl(dt, name) {
  const slug = dt.toLowerCase().replace(/ /g, '-')
  return name ? `/app/${slug}/${name}` : `/app/${slug}`
}

function fmt(v, f) {
  if (v == null) return '—'
  if (f === 'date' && v) return new Date(v).toLocaleDateString('vi-VN')
  if (f === 'datetime' && v) return new Date(v).toLocaleString('vi-VN')
  if (f === 'currency') return new Intl.NumberFormat('vi-VN').format(Number(v) || 0)
  if (typeof v === 'boolean') return v ? '✓' : ''
  if (v === 1) return '✓'
  if (v === 0) return ''
  return v
}

function fieldKind(field) {
  if (/date$/.test(field) && !/_date$/.test(field) === false) return 'date'
  if (/total_value|outstanding|amount|debit|credit|grand_total|remaining/.test(field)) return 'currency'
  return ''
}
</script>

<template>
  <div v-if="!moduleInfo">
    <div class="sc-card p-10 text-center text-sc-text-muted">
      Module không tồn tại
    </div>
  </div>
  <div v-else>
    <!-- Header -->
    <div class="sc-card p-5 mb-4 flex items-center gap-4">
      <div class="w-14 h-14 rounded-lg bg-sc-navy text-white text-2xl flex items-center justify-center">
        {{ moduleInfo.icon }}
      </div>
      <div class="flex-1">
        <div class="text-xs font-mono text-sc-text-muted">{{ moduleInfo.code }} · {{ moduleInfo.group }}</div>
        <h2 class="text-xl font-bold text-sc-navy">{{ moduleInfo.name }}</h2>
      </div>
      <a :href="`/app/${moduleInfo.code.toLowerCase()}-dashboard`" class="sc-btn-secondary text-sm">
        Workspace →
      </a>
    </div>

    <!-- Stats per doctype -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
      <div v-for="d in doctypes" :key="d.dt"
        class="sc-card p-4 cursor-pointer hover:shadow-sc-md transition"
        @click="activeTab = doctypes.indexOf(d)"
        :class="{ 'ring-2 ring-sc-royal': doctypes[activeTab] === d }">
        <div class="text-xs text-sc-text-muted">{{ d.label }}</div>
        <div class="text-2xl font-bold font-mono text-sc-navy mt-1">
          {{ stats[d.dt] ?? '—' }}
        </div>
      </div>
    </div>

    <!-- Tabs (visual only — clicked via stat cards above too) -->
    <div class="flex gap-1 mb-3 border-b border-sc-border">
      <button v-for="(d, i) in doctypes" :key="d.dt"
        @click="activeTab = i"
        class="px-4 py-2 text-sm font-medium border-b-2 transition"
        :class="activeTab === i ? 'border-sc-royal text-sc-royal' : 'border-transparent text-sc-text-muted hover:text-sc-text'">
        {{ d.label }}
      </button>
    </div>

    <!-- Data table -->
    <div class="sc-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-3 border-b border-sc-border">
        <div class="text-sm font-medium text-sc-navy">
          {{ doctypes[activeTab]?.label }} — gần đây
        </div>
        <a :href="deskUrl(doctypes[activeTab]?.dt)"
           class="text-xs text-sc-royal hover:underline">
          Mở danh sách đầy đủ →
        </a>
      </div>
      <div v-if="loading" class="p-10 text-center text-sc-text-muted text-sm">Đang tải...</div>
      <div v-else-if="error" class="p-5 text-sc-danger text-sm">{{ error }}</div>
      <div v-else-if="rows.length === 0" class="p-10 text-center text-sc-text-muted text-sm">
        Chưa có dữ liệu
      </div>
      <div v-else class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th v-for="f in DT_FIELDS[doctypes[activeTab]?.dt] || ['name']" :key="f">
                {{ f.replace(/_/g, ' ') }}
              </th>
              <th class="w-16"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.name">
              <td v-for="f in DT_FIELDS[doctypes[activeTab]?.dt] || ['name']" :key="f"
                :class="f === 'name' ? 'font-mono text-xs' : ''">
                {{ fmt(r[f], fieldKind(f)) }}
              </td>
              <td>
                <a :href="deskUrl(doctypes[activeTab].dt, r.name)"
                   class="text-sc-royal hover:underline text-xs">Xem →</a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
