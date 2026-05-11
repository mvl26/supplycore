<script setup>
import { ref, computed, onMounted } from 'vue'
import { getList, call } from '../api'

const alerts = ref([])
const loading = ref(true)
const error = ref(null)
const filter = ref('open')  // open / resolved / all
const severityFilter = ref('all')

async function load() {
  loading.value = true; error.value = null
  try {
    const filters = []
    if (filter.value === 'open') filters.push(['resolved', '=', 0])
    else if (filter.value === 'resolved') filters.push(['resolved', '=', 1])
    if (severityFilter.value !== 'all') filters.push(['severity', '=', severityFilter.value])
    alerts.value = await getList('SC Alert', {
      fields: ['name', 'alert_date', 'alert_type', 'severity', 'title', 'message',
                'reference_doctype', 'reference_name', 'resolved', 'snooze_until',
                'snooze_reason', 'assigned_to', 'escalated'],
      filters,
      order_by: 'alert_date desc',
      limit: 50,
    })
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

const sevBadge = (s) => ({
  Critical: 'sc-badge-critical', Warning: 'sc-badge-warning', Info: 'sc-badge-info',
}[s] || 'sc-badge-neutral')

const counts = computed(() => {
  const c = { all: alerts.value.length, Critical: 0, Warning: 0, Info: 0 }
  alerts.value.forEach(a => { if (c[a.severity] !== undefined) c[a.severity]++ })
  return c
})

const selected = ref(null)
const actionType = ref(null)  // resolve | snooze | assign
const actionInput = ref({ remarks: '', hours: 4, reason: '', user: '' })

function openAction(alert, type) {
  selected.value = alert
  actionType.value = type
  actionInput.value = { remarks: '', hours: 4, reason: '', user: '' }
}

async function performAction() {
  if (!selected.value || !actionType.value) return
  try {
    const doctype = 'SC Alert'
    const name = selected.value.name
    if (actionType.value === 'resolve') {
      await call('frappe.client.set_value', { doctype, name,
        fieldname: 'resolved', value: 0 })  // ensure not double-resolved on retry
      await call('frappe.desk.form.utils.add_comment', {
        reference_doctype: doctype, reference_name: name,
        content: actionInput.value.remarks || 'Resolved via Alert Center',
      }).catch(() => {})
      // Call doc method
      await callDocMethod(doctype, name, 'mark_resolved', {
        action: 'Acted Upon', remarks: actionInput.value.remarks,
      })
    } else if (actionType.value === 'snooze') {
      await callDocMethod(doctype, name, 'snooze_alert', {
        hours: actionInput.value.hours, reason: actionInput.value.reason,
      })
    } else if (actionType.value === 'assign') {
      await callDocMethod(doctype, name, 'assign_alert', {
        user: actionInput.value.user, note: actionInput.value.remarks,
      })
    }
    closeAction()
    await load()
  } catch (e) {
    alert(`Lỗi: ${e.message}`)
  }
}

async function callDocMethod(doctype, name, method, args = {}) {
  return call('frappe.client.run_doc_method', {
    method, docs: JSON.stringify({ doctype, name, ...args }),
  }).catch(async () => {
    // Fallback to direct doc.method endpoint
    const url = `/api/method/run_doc_method?dt=${encodeURIComponent(doctype)}&dn=${encodeURIComponent(name)}&method=${method}&args=${encodeURIComponent(JSON.stringify(args))}`
    const r = await fetch(url, { credentials: 'include' })
    if (!r.ok) throw new Error(`${method} failed`)
    return r.json()
  })
}

function closeAction() {
  selected.value = null
  actionType.value = null
}

function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('vi-VN')
}
</script>

<template>
  <div>
    <!-- Filters -->
    <div class="sc-card p-4 mb-4 flex flex-wrap items-center gap-3">
      <div class="flex gap-1">
        <button v-for="f in ['open', 'resolved', 'all']" :key="f"
          @click="filter = f; load()"
          class="px-3 py-1.5 rounded-md text-sm font-medium transition"
          :class="filter === f ? 'bg-sc-navy text-white' : 'bg-sc-bg text-sc-text hover:bg-sc-border'">
          {{ {open: 'Đang mở', resolved: 'Đã xử lý', all: 'Tất cả'}[f] }}
          <span class="ml-1.5 text-xs opacity-70">({{ counts.all }})</span>
        </button>
      </div>

      <div class="border-l border-sc-border pl-3 flex gap-1">
        <button v-for="s in ['all', 'Critical', 'Warning', 'Info']" :key="s"
          @click="severityFilter = s; load()"
          class="px-3 py-1.5 rounded-md text-sm transition"
          :class="severityFilter === s ? 'bg-sc-royal text-white' : 'bg-white border border-sc-border hover:bg-sc-bg'">
          {{ s === 'all' ? 'Tất cả mức' : s }}
        </button>
      </div>

      <button @click="load" class="ml-auto sc-btn-secondary text-sm">↻</button>
    </div>

    <!-- List -->
    <div v-if="loading" class="text-center py-20 text-sc-text-muted">Đang tải...</div>
    <div v-else-if="error" class="sc-card p-5 border-l-4 border-sc-danger">
      <div class="text-sc-danger font-medium">Lỗi: {{ error }}</div>
    </div>
    <div v-else-if="alerts.length === 0" class="sc-card p-10 text-center text-sc-text-muted">
      ✓ Không có cảnh báo nào
    </div>
    <div v-else class="space-y-3">
      <div v-for="a in alerts" :key="a.name" class="sc-card p-4 hover:shadow-sc-md transition">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0 mt-1">
            <span :class="['sc-badge', sevBadge(a.severity)]">{{ a.severity }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h4 class="font-semibold text-sc-navy">{{ a.title }}</h4>
              <span v-if="a.escalated" class="sc-badge sc-badge-critical">↑ ESCALATED</span>
              <span v-if="a.resolved" class="sc-badge sc-badge-success">✓ Resolved</span>
              <span v-if="a.snooze_until && !a.resolved" class="sc-badge sc-badge-neutral">
                💤 Snoozed → {{ fmtDate(a.snooze_until) }}
              </span>
              <span v-if="a.assigned_to" class="sc-badge sc-badge-info">
                👤 {{ a.assigned_to }}
              </span>
            </div>
            <p class="text-sm text-sc-text-muted mt-1">{{ a.message }}</p>
            <div class="flex items-center gap-3 mt-2 text-xs text-sc-text-muted">
              <span>📅 {{ fmtDate(a.alert_date) }}</span>
              <span v-if="a.reference_doctype">
                🔗 <a :href="`/app/${a.reference_doctype.toLowerCase().replace(/ /g,'-')}/${a.reference_name}`"
                       class="text-sc-royal hover:underline">
                  {{ a.reference_doctype }} {{ a.reference_name }}
                </a>
              </span>
            </div>
          </div>
          <div v-if="!a.resolved" class="flex gap-2">
            <button @click="openAction(a, 'resolve')" class="sc-btn-primary text-xs">✓ Resolve</button>
            <button @click="openAction(a, 'snooze')" class="sc-btn-secondary text-xs">💤 Snooze</button>
            <button @click="openAction(a, 'assign')" class="sc-btn-secondary text-xs">👤 Assign</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Modal -->
    <div v-if="selected && actionType" class="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-sc-lg p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-sc-navy mb-1">
          {{ {resolve: 'Đánh dấu đã xử lý', snooze: 'Tạm ẩn cảnh báo', assign: 'Phân công xử lý'}[actionType] }}
        </h3>
        <p class="text-sm text-sc-text-muted mb-4">{{ selected.title }}</p>

        <template v-if="actionType === 'resolve'">
          <label class="text-sm font-medium block mb-1">Ghi chú hành động</label>
          <textarea v-model="actionInput.remarks" rows="3" class="sc-input"
            placeholder="VD: Đã liên hệ NCC, đã refill stock..."></textarea>
        </template>

        <template v-else-if="actionType === 'snooze'">
          <label class="text-sm font-medium block mb-1">Số giờ tạm ẩn</label>
          <input v-model.number="actionInput.hours" type="number" min="1" class="sc-input mb-3" />
          <label class="text-sm font-medium block mb-1">Lý do</label>
          <textarea v-model="actionInput.reason" rows="2" class="sc-input"
            placeholder="VD: Đang chờ NCC xác nhận"></textarea>
        </template>

        <template v-else-if="actionType === 'assign'">
          <label class="text-sm font-medium block mb-1">Email user</label>
          <input v-model="actionInput.user" type="text" class="sc-input mb-3"
            placeholder="user@example.com" />
          <label class="text-sm font-medium block mb-1">Ghi chú (optional)</label>
          <textarea v-model="actionInput.remarks" rows="2" class="sc-input"></textarea>
        </template>

        <div class="flex justify-end gap-2 mt-5">
          <button @click="closeAction" class="sc-btn-secondary text-sm">Hủy</button>
          <button @click="performAction" class="sc-btn-primary text-sm">Xác nhận</button>
        </div>
      </div>
    </div>
  </div>
</template>
