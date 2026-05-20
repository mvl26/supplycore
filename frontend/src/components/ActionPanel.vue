<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ACTIONS } from '../actions'
import { runDocMethod, call } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import FieldInput from './FieldInput.vue'

const router = useRouter()

const props = defineProps({
  doctype: String,
  doc: Object,
})
const emit = defineEmits(['after'])

const toast = useToastStore()
const running = ref(false)
const selected = ref(null)
const args = ref({})
const result = ref(null)
const resultLabel = ref('')
const showResult = ref(false)

// Action method nào trả về data nhiều → cần show kết quả cho user
const RESULT_ACTIONS = new Set([
  'get_reconciliation_minutes_data',
  'get_investigation_minutes_data',
  'get_count_sheet_print_data',
  'run_audit_trail',
  'compare_stock',
  'detect_anomalies',
  'audit_dispensings_in_period',
  'verify_audit_integrity',
])

const visible = computed(() => {
  const list = ACTIONS[props.doctype] || []
  return list.filter(a => !a.when || a.when(props.doc || {}))
})

function openAction(a) {
  if (a.args && a.args.length) {
    selected.value = a
    args.value = {}
    a.args.forEach(f => { args.value[f.key] = f.default ?? '' })
  } else {
    runAction(a, {})
  }
}

async function runAction(a, argsObj) {
  running.value = true
  result.value = null
  try {
    let r
    if (a.apiMethod) {
      // Module-level whitelisted function — supplycore.<module>.<func>
      // apiNameArg = key để inject doc name vào payload; null/''/undefined → bỏ qua
      const argKey = a.apiNameArg === undefined ? 'name' : a.apiNameArg
      const payload = { ...argsObj }
      if (argKey && props.doc?.name) payload[argKey] = props.doc.name
      const msg2 = await call(a.apiMethod, payload)
      r = { message: msg2 }
    } else {
      r = await runDocMethod(props.doctype, props.doc.name, a.method, argsObj)
    }
    const msg = r?.message ?? r
    result.value = typeof msg === 'object' ? msg : { result: msg }
    toast.success(`Đã thực hiện: ${a.label}`)
    selected.value = null
    emit('after', a, result.value)

    // Show result modal cho method trả về data
    const methodKey = a.method || (a.apiMethod || '').split('.').pop()
    if (RESULT_ACTIONS.has(methodKey) && result.value && typeof result.value === 'object') {
      resultLabel.value = a.label
      showResult.value = true
    }

    // Auto-navigate nếu action có navigateOnSuccess
    if (a.navigateOnSuccess && result.value) {
      const nav = a.navigateOnSuccess
      if (nav.type === 'doc' && nav.from && result.value[nav.from]) {
        setTimeout(() => {
          router.push(`/doc/${encodeURIComponent(nav.dt)}/${encodeURIComponent(result.value[nav.from])}`)
        }, 600)
      }
    }
    // Auto-navigate cho các method có URL field trả về
    else if (result.value?.url) {
      const url = result.value.url
      const m = url.match(/\/supplycore\/(doc|list)\/([^/]+)(?:\/(.+))?/)
      if (m) {
        setTimeout(() => {
          router.push(`/${m[1]}/${m[2]}${m[3] ? '/' + m[3] : ''}`)
        }, 600)
      }
    }
  } catch (e) {
    toast.error(e.message)
  } finally {
    running.value = false
  }
}

function confirmModal() {
  if (!selected.value) return
  // Validate required
  for (const f of selected.value.args || []) {
    if (f.required && (args.value[f.key] === '' || args.value[f.key] == null)) {
      toast.warning(`Vui lòng nhập ${f.label}`)
      return
    }
  }
  runAction(selected.value, args.value)
}

const btnClass = {
  primary:   'sc-btn-primary',
  secondary: 'sc-btn-secondary',
  success:   'bg-sc-success hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium',
  warning:   'bg-sc-warning hover:bg-amber-600 text-white px-4 py-2 rounded-md font-medium',
  danger:    'bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium',
}
</script>

<template>
  <div v-if="visible.length" class="sc-card p-5 mb-4">
    <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
      ⚡ Hành động khả dụng
    </h3>
    <div class="flex flex-wrap gap-2">
      <button v-for="a in visible" :key="a.method || a.apiMethod"
        @click="openAction(a)" :disabled="running"
        :class="[btnClass[a.variant] || 'sc-btn-secondary', 'text-sm disabled:opacity-50']">
        <span class="mr-1">{{ a.icon }}</span> {{ a.label }}
      </button>
    </div>
  </div>

  <Modal :open="!!selected" :title="selected ? selected.label : ''" size="md"
    @close="selected = null">
    <div class="space-y-3">
      <FieldInput v-for="f in selected?.args || []" :key="f.key"
        v-model="args[f.key]"
        :label="f.label" :type="f.type || 'text'"
        :options="f.options" :required="f.required" :hint="f.hint" />
    </div>
    <template #footer>
      <button @click="selected = null" class="sc-btn-secondary text-sm">Hủy</button>
      <button @click="confirmModal" :disabled="running"
        :class="[btnClass[selected?.variant] || 'sc-btn-primary', 'text-sm']">
        {{ running ? 'Đang chạy...' : 'Xác nhận' }}
      </button>
    </template>
  </Modal>

  <!-- Result viewer modal — hiển thị kết quả structured của action data-rich -->
  <Modal :open="showResult" :title="`Kết quả: ${resultLabel}`" size="lg"
    @close="showResult = false">
    <div v-if="result" class="space-y-3 text-sm">
      <!-- Anomalies / findings array -->
      <div v-if="result.anomalies && Array.isArray(result.anomalies)">
        <div class="font-semibold mb-2">⚠️ Bất thường phát hiện ({{ result.anomalies.length }})</div>
        <div v-if="!result.anomalies.length" class="text-sc-text-muted italic">
          Không có bất thường nào.
        </div>
        <div v-else class="space-y-2">
          <div v-for="(a, i) in result.anomalies" :key="i"
            class="border-l-4 border-amber-500 bg-amber-50 p-2 rounded">
            <div class="font-medium text-amber-900">{{ a.type || a.kind || 'Anomaly' }}</div>
            <div class="text-xs text-amber-800 mt-1">
              <template v-for="(v, k) in a" :key="k">
                <div v-if="k !== 'type' && k !== 'kind'"><strong>{{ k }}:</strong> {{ v }}</div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Audit trail entries -->
      <div v-else-if="result.entries && Array.isArray(result.entries)">
        <div class="font-semibold mb-2">📋 Audit Trail — {{ result.entries.length }} entries</div>
        <div class="bg-sc-bg p-2 rounded text-xs grid grid-cols-3 gap-2 mb-2">
          <div>Tổng: <strong>{{ result.total_entries ?? result.entries.length }}</strong></div>
          <div>Suspicious: <strong>{{ result.suspicious_count ?? 0 }}</strong></div>
          <div>Users: <strong>{{ result.unique_users ?? '—' }}</strong></div>
        </div>
        <div class="max-h-96 overflow-y-auto">
          <table class="text-xs w-full">
            <thead class="bg-sc-bg sticky top-0">
              <tr>
                <th class="p-1 text-left">Thời gian</th>
                <th class="p-1 text-left">User</th>
                <th class="p-1 text-left">Action</th>
                <th class="p-1 text-left">Doc</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(e, i) in result.entries.slice(0, 200)" :key="i" class="border-t">
                <td class="p-1 font-mono">{{ e.timestamp || e.creation }}</td>
                <td class="p-1">{{ e.user || e.owner }}</td>
                <td class="p-1">{{ e.action || e.event }}</td>
                <td class="p-1 font-mono">{{ e.doctype }} {{ e.docname || e.name }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Stock comparison -->
      <div v-else-if="result.theoretical_qty != null || result.variance_qty != null">
        <div class="font-semibold mb-2">⚖️ So sánh tồn kho</div>
        <div class="grid grid-cols-2 gap-3">
          <div class="border rounded p-2">
            <div class="text-xs text-sc-text-muted">SL lý thuyết</div>
            <div class="text-lg font-mono font-bold">{{ result.theoretical_qty }}</div>
          </div>
          <div class="border rounded p-2">
            <div class="text-xs text-sc-text-muted">SL thực tế</div>
            <div class="text-lg font-mono font-bold">{{ result.actual_qty }}</div>
          </div>
          <div class="border rounded p-2" :class="result.variance_qty != 0 ? 'border-red-300 bg-red-50' : ''">
            <div class="text-xs text-sc-text-muted">Chênh lệch SL</div>
            <div class="text-lg font-mono font-bold"
              :class="result.variance_qty != 0 ? 'text-red-700' : ''">
              {{ result.variance_qty > 0 ? '+' : '' }}{{ result.variance_qty }}
            </div>
          </div>
          <div class="border rounded p-2" :class="result.variance_value != 0 ? 'border-red-300 bg-red-50' : ''">
            <div class="text-xs text-sc-text-muted">Chênh lệch giá trị</div>
            <div class="text-lg font-mono font-bold"
              :class="result.variance_value != 0 ? 'text-red-700' : ''">
              {{ Number(result.variance_value || 0).toLocaleString('vi-VN') }} VND
            </div>
          </div>
        </div>
      </div>

      <!-- Minutes data (biên bản) -->
      <div v-else-if="result.title || result.header_title">
        <div class="font-semibold text-base mb-2">{{ result.title || result.header_title }}</div>
        <div v-if="result.summary" class="bg-sc-bg p-3 rounded mb-3">
          <div class="grid grid-cols-2 gap-2 text-xs">
            <template v-for="(v, k) in result.summary" :key="k">
              <div class="text-sc-text-muted">{{ k }}:</div>
              <div class="font-mono">{{ v }}</div>
            </template>
          </div>
        </div>
        <div v-if="result.rows || result.items" class="overflow-x-auto">
          <table class="text-xs w-full">
            <thead class="bg-sc-bg">
              <tr>
                <th v-for="k in Object.keys((result.rows || result.items)[0] || {})" :key="k"
                  class="p-1 text-left">{{ k }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in (result.rows || result.items).slice(0, 100)" :key="i" class="border-t">
                <td v-for="k in Object.keys(row)" :key="k"
                  class="p-1 whitespace-nowrap">{{ row[k] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recovery / Dispensing audit summary -->
      <div v-else-if="result.audited != null || result.notified != null || result.recipients != null">
        <div class="font-semibold mb-2">📊 Tổng hợp</div>
        <div class="grid grid-cols-2 gap-2">
          <div v-for="(v, k) in result" :key="k" class="border rounded p-2">
            <div class="text-xs text-sc-text-muted">{{ k }}</div>
            <div class="font-mono">{{ Array.isArray(v) ? v.length + ' items' : (typeof v === 'object' ? JSON.stringify(v).slice(0, 80) : v) }}</div>
          </div>
        </div>
      </div>

      <!-- Generic fallback: pretty JSON -->
      <details v-else>
        <summary class="cursor-pointer text-sc-text-muted text-xs">Xem raw JSON</summary>
        <pre class="text-xs bg-gray-50 p-2 rounded overflow-x-auto mt-2">{{ JSON.stringify(result, null, 2) }}</pre>
      </details>
    </div>
    <template #footer>
      <button @click="showResult = false" class="sc-btn-primary text-sm">Đóng</button>
    </template>
  </Modal>
</template>
