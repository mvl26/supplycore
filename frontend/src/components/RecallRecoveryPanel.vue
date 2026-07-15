<script setup>
import { ref, computed } from 'vue'
import { runDocMethod } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import FieldInput from './FieldInput.vue'
import Icon from './Icon.vue'

const props = defineProps({
  doc: Object,        // SC Recall Notice
  doctype: String,
})
const emit = defineEmits(['after'])
const toast = useToastStore()

const editing = ref(null)
const form = ref({})
const saving = ref(false)

const rows = computed(() => props.doc?.affected_items || [])

const summary = computed(() => {
  const r = rows.value
  return {
    total: r.length,
    pending: r.filter(x => !x.status || x.status === 'Pending').length,
    inProgress: r.filter(x => x.status === 'In Progress').length,
    recovered: r.filter(x => x.status === 'Recovered').length,
    destroyed: r.filter(x => x.status === 'Destroyed').length,
    closed: r.filter(x => x.status === 'Closed').length,
  }
})

const STATUS_COLOR = {
  Pending: 'bg-gray-100 text-gray-700',
  'In Progress': 'bg-amber-100 text-amber-800',
  Recovered: 'bg-green-100 text-green-800',
  Destroyed: 'bg-red-100 text-red-800',
  Closed: 'bg-blue-100 text-blue-800',
}

function openRecovery(row) {
  editing.value = row
  form.value = {
    recovered_qty: Number(row.recovered_qty || 0),
    destroyed_qty: Number(row.destroyed_qty || 0),
    status: row.status || 'In Progress',
    remarks: row.remarks || '',
  }
}

async function quickFullRecover(row) {
  await doQuickUpdate(row, {
    recovered_qty: Number(row.qty_issued || 0),
    destroyed_qty: 0,
    status: 'Recovered',
    remarks: 'Thu hồi toàn bộ (quick action)',
  }, 'Đã thu hồi toàn bộ')
}

async function quickFullDestroy(row) {
  await doQuickUpdate(row, {
    recovered_qty: 0,
    destroyed_qty: Number(row.qty_issued || 0),
    status: 'Destroyed',
    remarks: 'Huỷ toàn bộ (quick action)',
  }, 'Đã huỷ toàn bộ')
}

async function doQuickUpdate(row, payload, successMsg) {
  saving.value = true
  try {
    await runDocMethod(props.doctype, props.doc.name, 'update_recovery', {
      row_name: row.name, ...payload,
    })
    toast.success(`${successMsg} · ${row.voucher_no || row.warehouse || row.name}`)
    emit('after')
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

async function saveRecovery() {
  if (!editing.value) return
  const row = editing.value
  const qtyDis = Number(row.qty_issued || 0)
  const totalAct = Number(form.value.recovered_qty || 0) + Number(form.value.destroyed_qty || 0)
  if (totalAct > qtyDis + 0.0001) {
    toast.error(`Tổng thu hồi + huỷ (${totalAct}) > SL phát (${qtyDis})`)
    return
  }
  saving.value = true
  try {
    await runDocMethod(props.doctype, props.doc.name, 'update_recovery', {
      row_name: row.name,
      recovered_qty: form.value.recovered_qty,
      destroyed_qty: form.value.destroyed_qty,
      status: form.value.status,
      remarks: form.value.remarks,
    })
    toast.success(`Đã cập nhật ${row.voucher_no || row.warehouse || row.name}`)
    editing.value = null
    emit('after')
  } catch (e) {
    toast.error(e.message)
  } finally {
    saving.value = false
  }
}

function pct(part, whole) {
  if (!whole) return 0
  return Math.round((part / whole) * 100)
}
</script>

<template>
  <div v-if="doc?.docstatus === 1 && rows.length"
    class="sc-card p-5 mb-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="package" :size="18" /> Theo dõi thu hồi
        <span class="text-xs text-sc-text-muted ml-2">
          (UC-30 step 6 — cập nhật từng vị trí ảnh hưởng)
        </span>
      </h3>
      <div class="text-sm">
        Tiến độ: <strong class="text-sc-success font-mono">{{ doc.recall_resolution_pct || 0 }}%</strong>
      </div>
    </div>

    <!-- Status summary chips -->
    <div class="flex flex-wrap gap-2 mb-3 text-xs">
      <span class="px-2 py-1 rounded bg-gray-100">
        Tổng: <strong>{{ summary.total }}</strong>
      </span>
      <span class="px-2 py-1 rounded" :class="STATUS_COLOR.Pending">
        Chờ xử lý: <strong>{{ summary.pending }}</strong>
      </span>
      <span class="px-2 py-1 rounded" :class="STATUS_COLOR['In Progress']">
        Đang xử lý: <strong>{{ summary.inProgress }}</strong>
      </span>
      <span class="px-2 py-1 rounded" :class="STATUS_COLOR.Recovered">
        Đã thu: <strong>{{ summary.recovered }}</strong>
      </span>
      <span class="px-2 py-1 rounded" :class="STATUS_COLOR.Destroyed">
        Đã huỷ: <strong>{{ summary.destroyed }}</strong>
      </span>
      <span class="px-2 py-1 rounded" :class="STATUS_COLOR.Closed">
        Đã đóng: <strong>{{ summary.closed }}</strong>
      </span>
    </div>

    <!-- Recovery progress bar -->
    <div class="mb-4">
      <div class="h-3 bg-gray-200 rounded-full overflow-hidden flex">
        <div class="bg-green-500" :style="{ width: pct(summary.recovered, summary.total) + '%' }"></div>
        <div class="bg-red-400" :style="{ width: pct(summary.destroyed, summary.total) + '%' }"></div>
        <div class="bg-blue-400" :style="{ width: pct(summary.closed, summary.total) + '%' }"></div>
        <div class="bg-amber-400" :style="{ width: pct(summary.inProgress, summary.total) + '%' }"></div>
      </div>
    </div>

    <!-- Affected items table với quick action per row -->
    <div class="overflow-x-auto">
      <table class="sc-table text-xs">
        <thead>
          <tr>
            <th>Vị trí</th>
            <th>Chứng từ</th>
            <th class="text-right">SL phát</th>
            <th class="text-right">Đã thu</th>
            <th class="text-right">Đã huỷ</th>
            <th class="text-right">Còn</th>
            <th>Trạng thái</th>
            <th class="w-48 text-center">Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.name"
            :class="r.status === 'Recovered' || r.status === 'Destroyed' || r.status === 'Closed' ? 'opacity-60' : ''">
            <td>
              <div class="font-medium">{{ r.warehouse || r.department || '—' }}</div>
              <div class="text-xs text-sc-text-muted">{{ r.location_type }}</div>
            </td>
            <td>
              <div class="font-mono text-xs">{{ r.voucher_no }}</div>
              <div class="text-xs text-sc-text-muted">{{ r.voucher_type?.replace('SC ', '') }}</div>
            </td>
            <td class="text-right font-mono font-semibold">{{ r.qty_issued }}</td>
            <td class="text-right font-mono text-green-700">{{ r.recovered_qty || 0 }}</td>
            <td class="text-right font-mono text-red-700">{{ r.destroyed_qty || 0 }}</td>
            <td class="text-right font-mono"
              :class="r.outstanding_qty > 0 ? 'text-amber-700 font-bold' : 'text-sc-text-muted'">
              {{ r.outstanding_qty }}
            </td>
            <td>
              <span class="px-2 py-0.5 rounded text-xs"
                :class="STATUS_COLOR[r.status] || STATUS_COLOR.Pending">
                {{ r.status || 'Pending' }}
              </span>
            </td>
            <td class="text-center">
              <div class="flex gap-1 justify-center">
                <button @click="openRecovery(r)"
                  class="text-xs px-2 py-1 rounded bg-sc-royal text-white hover:bg-sc-navy"
                  title="Cập nhật chi tiết"><Icon name="edit" :size="14" /> Cập nhật</button>
                <button v-if="r.outstanding_qty > 0" @click="quickFullRecover(r)"
                  class="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700"
                  title="Thu hồi toàn bộ"><Icon name="check" :size="14" /> Thu</button>
                <button v-if="r.outstanding_qty > 0" @click="quickFullDestroy(r)"
                  class="text-xs px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700"
                  title="Huỷ toàn bộ"><Icon name="trash" :size="14" /> Huỷ</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="!!editing"
      :title="editing ? `Cập nhật thu hồi · ${editing.voucher_no || editing.name}` : ''"
      size="md" @close="editing = null">
      <div v-if="editing" class="space-y-3">
        <div class="bg-sc-bg p-3 rounded text-sm">
          <div class="flex justify-between">
            <span class="text-sc-text-muted">SL phát:</span>
            <strong class="font-mono">{{ editing.qty_issued }}</strong>
          </div>
          <div class="flex justify-between mt-1">
            <span class="text-sc-text-muted">Vị trí:</span>
            <span>{{ editing.warehouse || editing.department || '—' }} ({{ editing.location_type }})</span>
          </div>
        </div>
        <FieldInput v-model="form.recovered_qty" label="Đã thu hồi" type="number" required />
        <FieldInput v-model="form.destroyed_qty" label="Đã huỷ" type="number" required />
        <FieldInput v-model="form.status" label="Trạng thái" type="select"
          :options="['Pending', 'In Progress', 'Recovered', 'Destroyed', 'Closed']" />
        <FieldInput v-model="form.remarks" label="Ghi chú" type="textarea" />
      </div>
      <template #footer>
        <button @click="editing = null" class="sc-btn-secondary text-sm">Hủy</button>
        <button @click="saveRecovery" :disabled="saving" class="sc-btn-primary text-sm">
          {{ saving ? 'Đang lưu...' : 'Lưu cập nhật' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
