<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'
import { fmtNumber, fmtDate, fmtDateTime } from '../utils'

const props = defineProps({
  doc: { type: Object, required: true },
})

const items = computed(() => Array.isArray(props.doc.items) ? props.doc.items : [])

const totals = computed(() => {
  const t = { contract_qty: 0, ordered_qty: 0, remaining_qty: 0, total_amount: 0 }
  for (const r of items.value) {
    t.contract_qty += Number(r.contract_qty) || 0
    t.ordered_qty += Number(r.ordered_qty) || 0
    t.remaining_qty += Number(r.remaining_qty) || (Number(r.contract_qty) || 0) - (Number(r.ordered_qty) || 0)
    t.total_amount += Number(r.total_amount) || (Number(r.contract_qty) || 0) * (Number(r.unit_price) || 0)
  }
  return t
})

// Validity timeline — % của tổng thời lượng HĐ đã trôi
const validity = computed(() => {
  const from = props.doc.valid_from ? new Date(props.doc.valid_from) : null
  const to = props.doc.valid_to ? new Date(props.doc.valid_to) : null
  if (!from || !to) return null
  const now = new Date()
  const total = to - from
  const elapsed = now - from
  const pct = total > 0 ? Math.max(0, Math.min(100, (elapsed / total) * 100)) : 0
  const daysTotal = Math.round(total / 86400000)
  const daysRemain = Math.round((to - now) / 86400000)
  const expired = daysRemain < 0
  const expiringSoon = daysRemain >= 0 && daysRemain <= 30
  return { pct, daysTotal, daysRemain, expired, expiringSoon, from, to }
})

// Tổng giá trị / sử dụng / còn lại
const value = computed(() => {
  const total = Number(props.doc.total_value) || 0
  const used = Number(props.doc.used_value) || 0
  const committed = Number(props.doc.committed_value) || 0
  const remaining = Number(props.doc.remaining_value) || (total - used - committed)
  return {
    total, used, committed, remaining,
    usedPct: total > 0 ? (used / total) * 100 : 0,
    committedPct: total > 0 ? (committed / total) * 100 : 0,
    remainingPct: total > 0 ? Math.max(0, (remaining / total) * 100) : 0,
  }
})

// Status / approval pill
const statusMeta = computed(() => {
  const ds = props.doc.docstatus
  const status = props.doc.status
  const stage = props.doc.approval_stage
  if (ds === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
  if (ds === 1) {
    if (status === 'Exhausted') return { label: 'Đã hết hạn mức', cls: 'sc-badge-neutral', icon: 'check-circle-2' }
    if (validity.value?.expired) return { label: 'Hết hạn', cls: 'sc-badge-critical', icon: 'alert-circle' }
    if (validity.value?.expiringSoon) return { label: 'Sắp hết hạn', cls: 'sc-badge-warning', icon: 'alert-triangle' }
    return { label: 'Đang hiệu lực', cls: 'sc-badge-success', icon: 'check-circle-2' }
  }
  if (stage === 'Approved') return { label: 'Đã duyệt — chờ kích hoạt', cls: 'sc-badge-info', icon: 'check' }
  if (stage === 'Executive Review') return { label: 'Chờ Lãnh đạo', cls: 'sc-badge-warning', icon: 'clock' }
  if (stage === 'Manager Review') return { label: 'Chờ Quản lý', cls: 'sc-badge-warning', icon: 'clock' }
  if (stage === 'Rejected') return { label: 'Đã từ chối', cls: 'sc-badge-critical', icon: 'x-circle' }
  return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
})

// Approval timeline — 3 mốc: Manager, Executive, Activate
const approvalSteps = computed(() => {
  const d = props.doc
  return [
    {
      key: 'manager',
      title: 'Quản lý duyệt',
      by: d.manager_approved_by, at: d.manager_approved_at, comment: d.manager_comment,
      done: !!d.manager_approved_at,
    },
    {
      key: 'executive',
      title: 'Lãnh đạo duyệt',
      by: d.executive_approved_by, at: d.executive_approved_at, comment: d.executive_comment,
      done: !!d.executive_approved_at,
    },
    {
      key: 'activate',
      title: 'Kích hoạt hợp đồng',
      by: d.modified_by, at: d.docstatus === 1 ? d.modified : null,
      done: d.docstatus === 1,
    },
  ]
})

function fmtMoney(v) {
  return fmtNumber(v)
}

function fmtMoneyShort(v) {
  const n = Number(v) || 0
  if (n >= 1e9) return (n / 1e9).toFixed(2).replace(/\.00$/, '') + ' tỷ'
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + ' tr'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'k'
  return fmtNumber(n)
}

const hasApprovalData = computed(() => approvalSteps.value.some(s => s.done || s.by))
</script>

<template>
  <div class="space-y-4">
    <!-- ============================================================ -->
    <!-- HERO PANEL — supplier identity + validity timeline             -->
    <!-- ============================================================ -->
    <div class="sc-card overflow-hidden">
      <div class="relative px-6 pt-6 pb-5
                  bg-gradient-to-br from-[#F8FAFD] via-white to-[#EEF4FB]
                  border-b border-sc-border">
        <!-- Decorative chevron rail -->
        <div class="absolute right-0 top-0 bottom-0 w-1.5 bg-gradient-to-b
                    from-sc-navy via-sc-royal to-sc-royal-light opacity-90"></div>

        <div class="grid grid-cols-1 lg:grid-cols-[1fr,auto] gap-4 lg:gap-8 items-start">
          <!-- Supplier identity -->
          <div class="min-w-0">
            <div class="flex items-center gap-3 mb-2 text-xs">
              <span class="inline-flex items-center gap-1 text-sc-text-muted uppercase tracking-wider">
                <Icon name="file-text" :size="12" /> Hợp đồng khung
              </span>
              <span class="text-sc-border">·</span>
              <span class="font-mono text-sc-navy">{{ doc.contract_number || doc.name }}</span>
            </div>
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-sc-navy
                          flex items-center justify-center text-white shadow-sc-sm">
                <Icon name="building-2" :size="22" />
              </div>
              <div class="min-w-0 flex-1">
                <h1 class="text-xl font-semibold text-sc-navy leading-tight truncate">
                  {{ doc.supplier_name || doc.supplier || '—' }}
                </h1>
                <div class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-sc-text-muted">
                  <span v-if="doc.supplier" class="font-mono text-xs">{{ doc.supplier }}</span>
                  <span v-if="doc.contract_date" class="inline-flex items-center gap-1.5">
                    <Icon name="calendar" :size="13" /> Ký {{ fmtDate(doc.contract_date) }}
                  </span>
                  <span v-if="doc.payment_terms" class="inline-flex items-center gap-1.5">
                    <Icon name="credit-card" :size="13" /> {{ doc.payment_terms }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Status pill -->
          <div class="flex flex-col items-start lg:items-end gap-2 pl-16 lg:pl-0">
            <span :class="['sc-badge', statusMeta.cls, 'gap-1.5']">
              <Icon :name="statusMeta.icon" :size="13" />
              {{ statusMeta.label }}
            </span>
            <div v-if="validity" class="text-xs text-sc-text-muted">
              <template v-if="validity.expired">
                Đã quá hạn {{ Math.abs(validity.daysRemain) }} ngày
              </template>
              <template v-else>
                Còn <span class="font-semibold text-sc-navy">{{ validity.daysRemain }}</span> ngày
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Validity timeline strip -->
      <div v-if="validity" class="px-6 py-5">
        <div class="flex items-baseline justify-between text-xs mb-2">
          <div class="font-mono text-sc-text">{{ fmtDate(doc.valid_from) }}</div>
          <div class="text-sc-text-muted">
            {{ Math.round(validity.pct) }}% thời lượng · tổng {{ validity.daysTotal }} ngày
          </div>
          <div class="font-mono text-sc-text">{{ fmtDate(doc.valid_to) }}</div>
        </div>
        <div class="relative h-2 rounded-full bg-sc-border/70 overflow-hidden">
          <div class="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
            :class="validity.expired ? 'bg-sc-critical'
                   : validity.expiringSoon ? 'bg-sc-warning'
                   : 'bg-gradient-to-r from-sc-royal to-sc-royal-light'"
            :style="{ width: validity.pct + '%' }"></div>
          <!-- Today marker -->
          <div v-if="!validity.expired && validity.pct < 100"
            class="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-sc-navy rounded"
            :style="{ left: validity.pct + '%' }"
            title="Hôm nay"></div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- VALUE TILES — financial commitment breakdown                   -->
    <!-- ============================================================ -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div class="sc-card p-4">
        <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-sc-text-muted mb-2">
          <Icon name="wallet" :size="13" />
          <span>Tổng giá trị</span>
        </div>
        <div class="font-mono text-xl font-semibold text-sc-navy leading-none">
          {{ fmtMoneyShort(value.total) }}
        </div>
        <div class="text-xs text-sc-text-muted mt-1 font-mono">{{ fmtMoney(value.total) }} đ</div>
      </div>

      <div class="sc-card p-4">
        <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-sc-text-muted mb-2">
          <Icon name="shopping-cart" :size="13" />
          <span>Đã sử dụng (PO)</span>
        </div>
        <div class="font-mono text-xl font-semibold text-sc-text leading-none">
          {{ fmtMoneyShort(value.used) }}
        </div>
        <div class="text-xs text-sc-text-muted mt-1">{{ value.usedPct.toFixed(1) }}% tổng giá trị</div>
      </div>

      <div class="sc-card p-4">
        <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-sc-text-muted mb-2">
          <Icon name="hourglass" :size="13" />
          <span>Đang gọi (RO)</span>
        </div>
        <div class="font-mono text-xl font-semibold text-sc-text leading-none">
          {{ fmtMoneyShort(value.committed) }}
        </div>
        <div class="text-xs text-sc-text-muted mt-1">{{ value.committedPct.toFixed(1) }}% chưa convert PO</div>
      </div>

      <div class="sc-card p-4 ring-1 ring-emerald-200/70 bg-emerald-50/30">
        <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-emerald-800/80 mb-2">
          <Icon name="check-circle-2" :size="13" />
          <span>Còn lại khả dụng</span>
        </div>
        <div class="font-mono text-xl font-semibold text-emerald-700 leading-none">
          {{ fmtMoneyShort(value.remaining) }}
        </div>
        <div class="text-xs text-emerald-700/70 mt-1">{{ value.remainingPct.toFixed(1) }}% còn dùng</div>
      </div>
    </div>

    <!-- Spend bar — visual breakdown of used / committed / remaining -->
    <div v-if="value.total > 0" class="sc-card p-4">
      <div class="flex items-baseline justify-between mb-2">
        <h3 class="font-semibold text-sc-navy text-sm flex items-center gap-2">
          <Icon name="bar-chart-3" :size="15" /> Phân bổ giá trị hợp đồng
        </h3>
        <span class="text-xs text-sc-text-muted font-mono">{{ fmtMoney(value.total) }} đ</span>
      </div>
      <div class="flex h-3 rounded-full overflow-hidden bg-sc-border/60">
        <div class="bg-sc-navy transition-all" :style="{ width: value.usedPct + '%' }"
          :title="`Đã sử dụng ${value.usedPct.toFixed(1)}%`"></div>
        <div class="bg-sc-royal-light transition-all" :style="{ width: value.committedPct + '%' }"
          :title="`Đang gọi ${value.committedPct.toFixed(1)}%`"></div>
        <div class="bg-emerald-400 transition-all" :style="{ width: value.remainingPct + '%' }"
          :title="`Còn lại ${value.remainingPct.toFixed(1)}%`"></div>
      </div>
      <div class="flex flex-wrap gap-x-5 gap-y-1 mt-2 text-xs">
        <span class="inline-flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-sm bg-sc-navy"></span>
          <span class="text-sc-text-muted">Đã sử dụng</span>
        </span>
        <span class="inline-flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-sm bg-sc-royal-light"></span>
          <span class="text-sc-text-muted">Đang gọi</span>
        </span>
        <span class="inline-flex items-center gap-1.5">
          <span class="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-400"></span>
          <span class="text-sc-text-muted">Còn lại</span>
        </span>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- DETAILS — terms (left) + approval timeline (right)             -->
    <!-- ============================================================ -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <div class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy text-sm mb-3 flex items-center gap-2">
          <Icon name="file-signature" :size="15" /> Điều khoản hợp đồng
        </h3>
        <dl class="space-y-3 text-sm">
          <div class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">Thanh toán</dt>
            <dd class="text-sc-text font-medium">{{ doc.payment_terms || '—' }}</dd>
          </div>
          <div class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">Giao hàng</dt>
            <dd class="text-sc-text whitespace-pre-line">{{ doc.delivery_terms || '—' }}</dd>
          </div>
          <div class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">Tệp đính kèm</dt>
            <dd>
              <a v-if="doc.attachment" :href="doc.attachment" target="_blank"
                class="inline-flex items-center gap-1.5 text-sc-royal hover:text-sc-navy hover:underline">
                <Icon name="paperclip" :size="14" /> Mở PDF
              </a>
              <span v-else class="text-sc-text-muted">—</span>
            </dd>
          </div>
          <div class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">Người tạo</dt>
            <dd class="text-sc-text">{{ doc.owner || '—' }}</dd>
          </div>
          <div v-if="doc.remarks" class="flex gap-3">
            <dt class="w-32 text-sc-text-muted flex-shrink-0">Ghi chú</dt>
            <dd class="text-sc-text whitespace-pre-line">{{ doc.remarks }}</dd>
          </div>
        </dl>
      </div>

      <div class="sc-card p-5">
        <h3 class="font-semibold text-sc-navy text-sm mb-4 flex items-center gap-2">
          <Icon name="badge-check" :size="15" /> Quy trình phê duyệt
        </h3>
        <ol v-if="hasApprovalData || doc.docstatus !== 0" class="relative space-y-4">
          <li v-for="(s, i) in approvalSteps" :key="s.key" class="relative pl-8">
            <!-- Connector line -->
            <span v-if="i < approvalSteps.length - 1"
              class="absolute left-[10px] top-6 bottom-[-1rem] w-px"
              :class="s.done ? 'bg-emerald-300' : 'bg-sc-border'"></span>
            <!-- Step marker -->
            <span class="absolute left-0 top-0.5 inline-flex items-center justify-center
                         w-5 h-5 rounded-full ring-2 ring-white"
              :class="s.done ? 'bg-emerald-500 text-white' : 'bg-sc-border text-sc-text-muted'">
              <Icon v-if="s.done" name="check" :size="12" />
              <span v-else class="w-1.5 h-1.5 rounded-full bg-white"></span>
            </span>
            <div class="text-sm font-medium" :class="s.done ? 'text-sc-text' : 'text-sc-text-muted'">
              {{ s.title }}
            </div>
            <div v-if="s.done" class="mt-0.5 text-xs text-sc-text-muted">
              <span class="font-medium text-sc-text">{{ s.by || '—' }}</span>
              <span v-if="s.at"> · {{ fmtDateTime(s.at) }}</span>
            </div>
            <div v-if="s.comment" class="mt-1.5 text-xs text-sc-text bg-sc-bg rounded-md px-2.5 py-1.5 border-l-2 border-sc-royal">
              <Icon name="message-square" :size="11" class="inline mr-1" />{{ s.comment }}
            </div>
          </li>
        </ol>
        <div v-else class="text-sm text-sc-text-muted py-3">
          Chưa có hoạt động phê duyệt.
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- ITEMS TABLE — with totals footer                               -->
    <!-- ============================================================ -->
    <div class="sc-card overflow-hidden">
      <div class="flex items-baseline justify-between px-5 pt-5 pb-3">
        <h3 class="font-semibold text-sc-navy text-sm flex items-center gap-2">
          <Icon name="package" :size="15" /> Danh mục vật tư
          <span class="text-sc-text-muted font-normal">({{ items.length }} dòng)</span>
        </h3>
        <div v-if="items.length" class="text-xs text-sc-text-muted">
          Đã đặt
          <span class="font-mono font-semibold text-sc-navy">
            {{ totals.contract_qty > 0 ? ((totals.ordered_qty / totals.contract_qty) * 100).toFixed(1) : 0 }}%
          </span>
          / hợp đồng
        </div>
      </div>

      <div v-if="!items.length" class="px-5 pb-5 text-sm text-sc-text-muted">
        Hợp đồng chưa có dòng vật tư nào.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="sc-table">
          <thead>
            <tr>
              <th class="w-10 text-center">#</th>
              <th>Mã VT</th>
              <th>Tên vật tư</th>
              <th class="text-center">UOM</th>
              <th class="text-right">SL HĐ</th>
              <th class="text-right">Đã đặt</th>
              <th class="text-right">Còn lại</th>
              <th class="text-right">Đơn giá</th>
              <th class="text-right">Thành tiền</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in items" :key="idx">
              <td class="text-center text-sc-text-muted font-mono">{{ idx + 1 }}</td>
              <td class="font-mono text-sc-navy">{{ row.item_code || '—' }}</td>
              <td class="max-w-[260px] truncate" :title="row.item_name">{{ row.item_name || '—' }}</td>
              <td class="text-center text-sc-text-muted">{{ row.uom || '—' }}</td>
              <td class="text-right font-mono">{{ fmtNumber(row.contract_qty) }}</td>
              <td class="text-right font-mono">{{ fmtNumber(row.ordered_qty || 0) }}</td>
              <td class="text-right font-mono"
                :class="(row.remaining_qty ?? (row.contract_qty - (row.ordered_qty || 0))) <= 0
                  ? 'text-sc-text-muted' : 'text-sc-navy font-semibold'">
                {{ fmtNumber(row.remaining_qty ?? ((row.contract_qty || 0) - (row.ordered_qty || 0))) }}
              </td>
              <td class="text-right font-mono">{{ fmtNumber(row.unit_price) }}</td>
              <td class="text-right font-mono font-semibold text-sc-navy">
                {{ fmtNumber(row.total_amount || (row.contract_qty || 0) * (row.unit_price || 0)) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-sc-bg border-t-2 border-sc-navy/20">
              <td colspan="4" class="font-semibold text-sc-navy py-2.5 pl-3">
                <span class="inline-flex items-center gap-2">
                  <Icon name="sigma" :size="14" />
                  TỔNG <span class="text-sc-text-muted font-normal">({{ items.length }} dòng)</span>
                </span>
              </td>
              <td class="text-right font-mono font-semibold text-sc-navy">{{ fmtNumber(totals.contract_qty) }}</td>
              <td class="text-right font-mono font-semibold text-sc-navy">{{ fmtNumber(totals.ordered_qty) }}</td>
              <td class="text-right font-mono font-semibold text-sc-navy">{{ fmtNumber(totals.remaining_qty) }}</td>
              <td></td>
              <td class="text-right font-mono font-semibold text-sc-navy">{{ fmtNumber(totals.total_amount) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>
