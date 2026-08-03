<script setup>
import { computed, ref } from 'vue'
import { runDocMethod } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import Icon from './Icon.vue'
import { fmtNumber } from '../utils'

const props = defineProps({
  doc: Object,        // SC Inventory Count Sheet
  doctype: String,
})
const toast = useToastStore()
const printOpen = ref(false)
const printData = ref(null)

const items = computed(() => props.doc?.items || [])

const stats = computed(() => {
  const r = items.value
  let counted = 0, mismatch = 0, recount = 0, recounted2 = 0, recounted3 = 0
  let totalSysQty = 0, totalActualQty = 0, totalVarianceQty = 0, totalVarianceValue = 0
  for (const x of r) {
    const s = Number(x.system_qty || 0)
    const a = Number(x.actual_qty || 0)
    const isCounted = Number(x.is_counted) === 1
    if (isCounted) counted++
    if (isCounted && a !== s) {
      mismatch++
      totalVarianceQty += (a - s)
      totalVarianceValue += (a - s) * Number(x.valuation_rate || 0)
    }
    if (x.needs_recount) recount++
    if (x.recount_actual_qty != null && x.recount_actual_qty !== '') recounted2++
    if (x.third_count_qty != null && x.third_count_qty !== '') recounted3++
    totalSysQty += s
    totalActualQty += a
  }
  return { total: r.length, counted, mismatch, recount, recounted2, recounted3,
           totalSysQty, totalActualQty, totalVarianceQty, totalVarianceValue }
})

const isReady = computed(() => {
  // Sẵn sàng make SR: tất cả items đã đếm + items cần đếm lại đã có recount
  if (stats.value.total === 0) return false
  if (stats.value.counted < stats.value.total) return false
  if (stats.value.recount > stats.value.recounted2) return false
  return true
})

async function openPrintSheet() {
  try {
    const r = await runDocMethod(props.doctype, props.doc.name,
      'get_count_sheet_print_data', { hide_system_qty: 1 })
    printData.value = r?.message ?? r
    printOpen.value = true
  } catch (e) {
    toast.error(`Lỗi: ${e.message}`)
  }
}

function downloadCsv() {
  const rows = items.value
  if (!rows.length) return
  const keys = ['item', 'item_name', 'batch', 'bin_location', 'uom', 'system_qty', 'actual_qty', 'difference', 'variance_pct']
  const csv = [
    keys.join(','),
    ...rows.map(r => keys.map(k => {
      const v = r[k]
      if (v == null) return ''
      const s = String(v).replace(/"/g, '""')
      return /[",\n]/.test(s) ? `"${s}"` : s
    }).join(','))
  ].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.doc.name}-count-sheet.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

function printNow() {
  window.print()
}
</script>

<template>
  <div v-if="doc && items.length" class="sc-card p-5 mb-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2">
        <Icon name="bar-chart" :size="18" /> Tổng quan kiểm kê
      </h3>
      <div class="flex gap-2">
        <button @click="openPrintSheet" class="sc-btn-secondary text-sm" title="Xem dữ liệu phiếu (ẩn SL hệ thống)">
          <Icon name="printer" :size="14" /> Phiếu đếm
        </button>
        <button @click="downloadCsv" class="sc-btn-secondary text-sm" title="Xuất CSV">
          <Icon name="download" :size="14" /> CSV
        </button>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
      <div class="border border-sc-border rounded p-3">
        <div class="text-xs text-sc-text-muted">Tổng items</div>
        <div class="text-2xl font-bold font-mono">{{ stats.total }}</div>
      </div>
      <div class="border border-sc-border rounded p-3"
        :class="stats.counted === stats.total ? 'border-sc-success/40 bg-sc-success-50' : 'border-sc-warning/40 bg-sc-warning-50'">
        <div class="text-xs text-sc-text-muted">Đã đếm</div>
        <div class="text-2xl font-bold font-mono"
          :class="stats.counted === stats.total ? 'text-sc-success' : 'text-sc-warning'">
          {{ stats.counted }} / {{ stats.total }}
        </div>
      </div>
      <div class="border border-sc-border rounded p-3"
        :class="stats.mismatch > 0 ? 'border-sc-danger/40 bg-sc-danger-50' : 'border-sc-success/40 bg-sc-success-50'">
        <div class="text-xs text-sc-text-muted">Items lệch</div>
        <div class="text-2xl font-bold font-mono"
          :class="stats.mismatch > 0 ? 'text-sc-danger' : 'text-sc-success'">
          {{ stats.mismatch }}
        </div>
      </div>
      <div class="border border-sc-border rounded p-3"
        :class="stats.recount > 0 ? 'border-sc-warning/40 bg-sc-warning-50' : ''">
        <div class="text-xs text-sc-text-muted">Cần đếm lại</div>
        <div class="text-2xl font-bold font-mono"
          :class="stats.recount > 0 ? 'text-sc-warning' : ''">
          {{ stats.recount }}
        </div>
        <div v-if="stats.recount > 0" class="text-xs">
          Đã L2: <strong>{{ stats.recounted2 }}</strong> · L3: <strong>{{ stats.recounted3 }}</strong>
        </div>
      </div>
      <div class="border border-sc-border rounded p-3"
        :class="stats.totalVarianceValue < 0 ? 'border-sc-danger/40 bg-sc-danger-50' : (stats.totalVarianceValue > 0 ? 'border-sc-info/40 bg-sc-info-50' : '')">
        <div class="text-xs text-sc-text-muted">Tổng lệch giá trị</div>
        <div class="text-xl font-bold font-mono"
          :class="stats.totalVarianceValue < 0 ? 'text-sc-danger' : (stats.totalVarianceValue > 0 ? 'text-sc-info' : '')">
          {{ stats.totalVarianceValue >= 0 ? '+' : '' }}{{ fmtNumber(stats.totalVarianceValue) }}
        </div>
        <div class="text-xs">VND</div>
      </div>
    </div>

    <!-- Workflow hint -->
    <div v-if="doc.docstatus === 0" class="mt-4 text-sm">
      <div v-if="stats.counted === 0"
        class="bg-sc-info-50 border-l-4 border-sc-info/40 p-3 rounded">
        <Icon name="info" :size="16" /> <strong>Bước 1:</strong> Bấm <em>"Tự nạp items"</em> để load danh sách vật tư trong phạm vi, rồi nhập SL đếm vào bảng dưới.
      </div>
      <div v-else-if="!isReady"
        class="bg-sc-warning-50 border-l-4 border-sc-warning/40 p-3 rounded">
        <Icon name="clock" :size="16" /> <strong>Đang đếm:</strong>
        <span v-if="stats.counted < stats.total">
          Còn <strong>{{ stats.total - stats.counted }}</strong> items chưa đếm.
        </span>
        <span v-if="stats.recount > stats.recounted2">
          Còn <strong>{{ stats.recount - stats.recounted2 }}</strong> items cần đếm lại lần 2.
        </span>
      </div>
      <div v-else class="bg-sc-success-50 border-l-4 border-sc-success/40 p-3 rounded">
        <Icon name="check" :size="16" /> <strong>Đã đếm xong</strong> — Submit phiếu rồi bấm <em>"Tạo SR đối soát"</em> để tạo phiếu điều chỉnh kho.
      </div>
    </div>
    <div v-else-if="doc.docstatus === 1 && doc.status === 'Counted' && !doc.stock_reconciliation"
      class="mt-4 bg-sc-success-50 border-l-4 border-sc-success/40 p-3 rounded text-sm">
      <Icon name="check" :size="16" /> <strong>Phiếu đã submit</strong> — Bấm <em>"Tạo SR đối soát"</em> để điều chỉnh tồn kho theo kết quả đếm.
    </div>
    <div v-else-if="doc.stock_reconciliation"
      class="mt-4 bg-sc-info-50 border-l-4 border-sc-info/40 p-3 rounded text-sm">
      <Icon name="settings" :size="16" /> SR đối soát đã tạo:
      <router-link :to="`/doc/SC Stock Reconciliation/${encodeURIComponent(doc.stock_reconciliation)}`"
        class="text-sc-royal hover:underline font-mono">{{ doc.stock_reconciliation }}</router-link>
    </div>

    <!-- Print modal — hiển thị dạng phiếu để counter staff in/copy -->
    <Modal :open="printOpen" title="Phiếu đếm kiểm kê (ẩn SL hệ thống)" size="lg"
      @close="printOpen = false">
      <div v-if="printData" class="space-y-3 text-sm print:p-6">
        <div class="text-center font-semibold text-base mb-3">
          PHIẾU KIỂM KÊ KHO
          <div class="text-xs text-sc-text-muted font-normal">
            {{ doc.name }} · {{ doc.warehouse }} · {{ doc.count_date }}
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>Người đếm: {{ doc.counted_by || '___________' }}</div>
          <div>Ngày: {{ doc.count_date }}</div>
        </div>
        <table class="text-xs w-full border-collapse">
          <thead>
            <tr class="bg-sc-bg">
              <th class="border p-1">#</th>
              <th class="border p-1 text-left">Mã VT</th>
              <th class="border p-1 text-left">Tên</th>
              <th class="border p-1 text-left">Lô</th>
              <th class="border p-1 text-left">Vị trí</th>
              <th class="border p-1 text-left">ĐVT</th>
              <th class="border p-1 text-center">SL đếm</th>
              <th class="border p-1 text-center">Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in (printData.rows || items)" :key="i">
              <td class="border p-1 text-center">{{ i + 1 }}</td>
              <td class="border p-1 font-mono">{{ r.item }}</td>
              <td class="border p-1">{{ r.item_name }}</td>
              <td class="border p-1 font-mono">{{ r.batch || '' }}</td>
              <td class="border p-1 font-mono">{{ r.bin_location || '' }}</td>
              <td class="border p-1">{{ r.uom }}</td>
              <td class="border p-1 text-center" style="width: 80px;">_______</td>
              <td class="border p-1" style="width: 100px;"></td>
            </tr>
          </tbody>
        </table>
        <div class="grid grid-cols-2 gap-8 mt-6 text-xs">
          <div>
            <div class="font-semibold">Người đếm</div>
            <div class="border-t mt-12 pt-1 text-center">(Ký và ghi rõ họ tên)</div>
          </div>
          <div>
            <div class="font-semibold">Quản lý chứng kiến</div>
            <div class="border-t mt-12 pt-1 text-center">(Ký và ghi rõ họ tên)</div>
          </div>
        </div>
      </div>
      <template #footer>
        <button @click="printOpen = false" class="sc-btn-secondary text-sm">Đóng</button>
        <button @click="printNow" class="sc-btn-primary text-sm"><Icon name="printer" :size="14" /> In</button>
      </template>
    </Modal>
  </div>
</template>
