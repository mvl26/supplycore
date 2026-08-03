// Detail-view configs — per-doctype renderer description.
// Driven by DetailViewGeneric.vue. Each config follows FC pattern:
// hero + tiles + sections + optional approval timeline + items table.
//
// Field accessor `(d) => ...` runs against the loaded doc.

import { fmtDate, fmtDateTime, fmtVND } from './utils'

const today = () => new Date()
const daysBetween = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000)

// ---------- Shared status resolvers -----------------------------------------

function approvalStatus(d, opts = {}) {
  const ds = d.docstatus
  if (ds === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
  if (ds === 1) {
    if (opts.submittedLabel) return { label: opts.submittedLabel, cls: 'sc-badge-success', icon: 'check-circle-2' }
    return { label: 'Đã duyệt', cls: 'sc-badge-success', icon: 'check-circle-2' }
  }
  const stage = d.approval_stage
  if (stage === 'Approved') return { label: 'Đã duyệt — chờ kích hoạt', cls: 'sc-badge-info', icon: 'check' }
  if (stage === 'Executive Review') return { label: 'Chờ Lãnh đạo', cls: 'sc-badge-warning', icon: 'clock' }
  if (stage === 'Manager Review') return { label: 'Chờ Quản lý', cls: 'sc-badge-warning', icon: 'clock' }
  if (stage === 'Rejected') return { label: 'Đã từ chối', cls: 'sc-badge-critical', icon: 'x-circle' }
  return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
}

function statusByField(d, map) {
  const v = d.status || ''
  return map[v] || { label: v || '—', cls: 'sc-badge-neutral', icon: 'circle' }
}

// ---------- Configs ---------------------------------------------------------

export const DETAIL_CONFIGS = {

  // ===== M1: Release Order (Lệnh gọi hàng) ==================================
  'Release Order': {
    icon: 'clipboard-list',
    accentLabel: 'Lệnh gọi hàng',
    title: (d) => d.supplier_name || d.supplier || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.release_date ? `Lệnh ${fmtDate(d.release_date)}` : null },
      { icon: 'truck', text: (d) => d.required_by ? `Cần giao ${fmtDate(d.required_by)}` : null },
      { icon: 'file-text', text: (d) => d.framework_contract ? `HĐK ${d.framework_contract}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Draft': { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Approved': { label: 'Đã duyệt', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Converted': { label: 'Đã tạo PO', cls: 'sc-badge-info', icon: 'shopping-cart' },
        'Cancelled': { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng giá trị', value: (d) => d.total_amount, fmt: 'moneyShort',
        sublabel: (d) => d.total_amount ? fmtVND(d.total_amount) : null },
      { icon: 'list', label: 'Số dòng vật tư', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL gọi',
        value: (d) => (d.items || []).reduce((s, r) => s + (Number(r.qty) || 0), 0), fmt: 'number' },
      { icon: 'file-text', label: 'HĐK còn lại lúc tạo', value: (d) => d.remaining_value_at_release, fmt: 'moneyShort' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Hợp đồng khung', value: (d) => d.framework_contract,
          link: (d) => d.framework_contract ? `/doc/Framework Contract/${d.framework_contract}` : null },
        { label: 'Nhà cung cấp', value: (d) => d.supplier_name || d.supplier },
        { label: 'Purchase Order tạo từ RO', value: (d) => d.purchase_order,
          link: (d) => d.purchase_order ? `/doc/SC Purchase Order/${d.purchase_order}` : null },
        { label: 'Ghi chú', value: (d) => d.remarks, pre: true },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Danh mục vật tư cần gọi',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item_code', mono: true, anchor: 'navy' },
        { label: 'Tên vật tư', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL gọi', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Còn HĐK', accessor: 'available_qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'unit_price', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, 'qty', null, null, 'amount'],
    },
  },

  // ===== M2: Procurement Plan (Kế hoạch mua sắm) ============================
  'Procurement Plan': {
    icon: 'calendar',
    accentLabel: 'Kế hoạch mua sắm',
    title: (d) => d.warehouse || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.plan_date ? `Lập ${fmtDate(d.plan_date)}` : null },
      { icon: 'tag', text: (d) => d.period_type ? `Kỳ ${d.period_type}` : null },
      { icon: 'warehouse', text: (d) => d.warehouse ? `Kho ${d.warehouse}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Draft': { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Approved': { label: 'Đã duyệt', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Generated': { label: 'Đã tạo MR', cls: 'sc-badge-info', icon: 'file-text' },
        'Cancelled': { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng ước tính', value: (d) => d.total_estimated_cost, fmt: 'moneyShort',
        sublabel: (d) => d.total_estimated_cost ? fmtVND(d.total_estimated_cost) : null },
      { icon: 'list', label: 'Số dòng vật tư', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL dự kiến',
        value: (d) => (d.items || []).reduce((s, r) => s + (Number(r.planned_qty) || 0), 0), fmt: 'number' },
      { icon: 'shield-alert', label: 'Ngân sách',
        value: (d) => Number(d.budget) > 0 ? fmtVND(d.budget) : '—',
        accent: (d) => Number(d.budget) > 0 && Number(d.total_estimated_cost) > Number(d.budget) ? 'amber' : 'default',
        sublabel: (d) => Number(d.budget) > 0 && Number(d.total_estimated_cost) > Number(d.budget)
          ? (d.budget_acknowledged ? 'Vượt — đã xác nhận' : 'Vượt ngân sách') : null },
    ],
    sections: [
      { title: 'Phạm vi & tham số', icon: 'crosshair', fields: [
        { label: 'Kho', value: (d) => d.warehouse },
        { label: 'Từ ngày', value: (d) => d.from_date ? fmtDate(d.from_date) : '—' },
        { label: 'Đến ngày', value: (d) => d.to_date ? fmtDate(d.to_date) : '—' },
        { label: 'Ngày cần hàng', value: (d) => d.required_by ? fmtDate(d.required_by) : '—' },
        { label: 'Tháng lịch sử tính', value: (d) => d.consumption_lookback_months },
        { label: 'Hệ số safety stock', value: (d) => d.safety_stock_factor != null ? `${d.safety_stock_factor}%` : '—' },
        { label: 'Material Request đã tạo', value: (d) => d.material_request,
          link: (d) => d.material_request ? `/doc/SC Material Request/${d.material_request}` : null },
        { label: 'Ghi chú', value: (d) => d.remarks, pre: true },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Danh mục vật tư cần mua',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item_code', mono: true, anchor: 'navy' },
        { label: 'Tên vật tư', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'Tồn', accessor: 'current_stock', align: 'right', fmt: 'number' },
        { label: 'TT/tháng', accessor: 'avg_monthly_consumption', align: 'right', fmt: 'number' },
        { label: 'SL mua', accessor: 'planned_qty', align: 'right', fmt: 'number', anchor: 'navy' },
        { label: 'Đơn giá', accessor: 'estimated_unit_cost', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'estimated_amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, null, null, 'planned_qty', null, 'estimated_amount'],
    },
  },

  // ===== Financial: PO ======================================================
  'SC Purchase Order': {
    icon: 'shopping-cart',
    accentLabel: 'Đơn đặt hàng',
    title: (d) => d.supplier_name || d.supplier || '—',
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.transaction_date ? `Ngày PO ${fmtDate(d.transaction_date)}` : null },
      { icon: 'truck', text: (d) => d.schedule_date ? `Hẹn giao ${fmtDate(d.schedule_date)}` : null },
      { icon: 'warehouse', text: (d) => d.to_warehouse ? `Kho nhận ${d.to_warehouse}` : null },
      { icon: 'file-text', text: (d) => d.framework_contract ? `HĐ ${d.framework_contract}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      if (d.docstatus === 1) {
        return statusByField(d, {
          'To Receive': { label: 'Đã gửi NCC — chờ nhận', cls: 'sc-badge-info', icon: 'send' },
          'Partially Received': { label: 'Nhận một phần', cls: 'sc-badge-warning', icon: 'package' },
          'Received': { label: 'Đã nhận đủ', cls: 'sc-badge-success', icon: 'check-circle-2' },
          'Closed': { label: 'Đóng', cls: 'sc-badge-neutral', icon: 'check' },
        })
      }
      return approvalStatus(d)
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng giá trị', value: (d) => d.grand_total, fmt: 'moneyShort',
        sublabel: (d) => d.grand_total ? fmtVND(d.grand_total) : null },
      { icon: 'list', label: 'Số dòng vật tư', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL đặt', value: (d) => d.total_qty, fmt: 'number' },
      { icon: 'package-check', label: 'Đã nhận',
        value: (d) => (d.items || []).reduce((s, r) => s + (Number(r.received_qty) || 0), 0),
        fmt: 'number',
        sublabel: (d) => {
          const total = Number(d.total_qty) || 0
          const got = (d.items || []).reduce((s, r) => s + (Number(r.received_qty) || 0), 0)
          return total > 0 ? `${((got / total) * 100).toFixed(1)}% tổng SL` : null
        },
        accent: (d) => {
          const total = Number(d.total_qty) || 0
          const got = (d.items || []).reduce((s, r) => s + (Number(r.received_qty) || 0), 0)
          return total > 0 && got >= total ? 'emerald' : 'default'
        },
      },
    ],
    sections: [
      { title: 'Điều khoản & tham chiếu', icon: 'file-signature', fields: [
        { label: 'Thanh toán', value: (d) => d.payment_terms },
        { label: 'Giao hàng', value: (d) => d.delivery_terms, pre: true },
        { label: 'HĐ khung', value: (d) => d.framework_contract,
          link: (d) => d.framework_contract ? `/doc/Framework Contract/${d.framework_contract}` : null },
        { label: 'Release Order', value: (d) => d.release_order },
        { label: 'Material Request', value: (d) => d.material_request,
          link: (d) => d.material_request ? `/doc/SC Material Request/${d.material_request}` : null },
        { label: 'Lệch giá', value: (d) => d.has_price_variance ? 'Có — kiểm tra dòng có cảnh báo' : '—' },
      ]},
    ],
    approval: (d) => [
      { title: 'Quản lý duyệt', by: d.manager_approved_by, at: d.manager_approved_at,
        done: !!d.manager_approved_at },
      { title: 'Lãnh đạo duyệt', by: d.executive_approved_by, at: d.executive_approved_at,
        done: !!d.executive_approved_at },
      { title: 'Gửi NCC', by: null, at: d.sent_to_supplier_at, done: !!d.sent_to_supplier_at },
      { title: 'NCC xác nhận', by: null, at: null, done: !!d.supplier_confirmation_received },
    ],
    items: {
      field: 'items',
      label: 'Danh mục vật tư',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên vật tư', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL đặt', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Đã nhận', accessor: 'received_qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'rate', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, 'qty', 'received_qty', null, 'amount'],
    },
  },

  // ===== Financial: PR ======================================================
  'SC Purchase Receipt': {
    icon: 'package-check',
    accentLabel: 'Phiếu tiếp nhận tạm',
    title: (d) => d.supplier_name || d.supplier || '—',
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.posting_date ? `Nhập ${fmtDate(d.posting_date)}` : null },
      { icon: 'warehouse', text: (d) => d.to_warehouse ? `Kho ${d.to_warehouse}` : null },
      { icon: 'file-text', text: (d) => d.purchase_order ? `PO ${d.purchase_order}` : null },
      { icon: 'undo-2', text: (d) => d.is_return ? 'Phiếu trả NCC' : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      if (d.docstatus === 0) return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
      if (d.is_return) return { label: 'Trả NCC', cls: 'sc-badge-info', icon: 'undo-2' }
      // GĐ MVL — lifecycle 2 bước theo receipt_status.
      if (d.receipt_status === 'Đã nhập kho') return { label: 'Đã nhập kho', cls: 'sc-badge-success', icon: 'check-circle-2' }
      if (d.receipt_status === 'Chờ xử lý') return { label: 'Chờ xử lý (QC không đạt)', cls: 'sc-badge-critical', icon: 'shield-x' }
      // Đã tiếp nhận — phân theo QC (rollup 'Pass'/'Fail'/'Partial Pass').
      if (d.qc_required && (!d.qc_status || d.qc_status === 'Pending')) return { label: 'Đã tiếp nhận · Chờ QC', cls: 'sc-badge-warning', icon: 'shield-alert' }
      if (d.qc_status === 'Fail' || d.qc_status === 'Rejected') return { label: 'QC không đạt', cls: 'sc-badge-critical', icon: 'shield-x' }
      if (d.qc_status === 'Partial Pass') return { label: 'QC đạt một phần', cls: 'sc-badge-warning', icon: 'shield-alert' }
      // Đã tiếp nhận + QC đạt → chờ bấm "Xác nhận nhập kho".
      return { label: 'Chờ nhập kho', cls: 'sc-badge-info', icon: 'package-plus' }
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng giá trị', value: (d) => d.total_value, fmt: 'moneyShort' },
      { icon: 'boxes', label: 'Tổng SL', value: (d) => d.total_qty, fmt: 'number' },
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'alert-triangle', label: 'Over-receipt',
        value: (d) => d.has_over_receipt ? 'Có' : '—',
        sublabel: (d) => d.has_over_receipt
          ? (d.over_receipt_acknowledged ? 'Manager đã xác nhận' : 'Chưa xác nhận')
          : null,
        accent: (d) => d.has_over_receipt && !d.over_receipt_acknowledged ? 'amber' : 'default' },
    ],
    sections: [
      { title: 'Tham chiếu & chứng từ', icon: 'link', fields: [
        { label: 'PO tham chiếu', value: (d) => d.purchase_order,
          link: (d) => d.purchase_order ? `/doc/SC Purchase Order/${d.purchase_order}` : null },
        { label: 'Lý do không PO', value: (d) => d.no_po_reason, pre: true },
        { label: 'Bản scan giao hàng', value: (d) => d.delivery_note_attachment ? 'Đã đính kèm' : '—' },
        { label: 'Đã nhập chính thức', value: (d) => d.officially_received_at ? fmtDateTime(d.officially_received_at) : '—' },
      ]},
      { title: 'Phiếu trả NCC (nếu có)', icon: 'undo-2', fields: [
        { label: 'Trả phiếu', value: (d) => d.return_against },
        { label: 'Lý do trả', value: (d) => d.return_reason, pre: true },
        { label: 'Trạng thái', value: (d) => d.return_status },
        { label: 'Debit Note', value: (d) => d.debit_note,
          link: (d) => d.debit_note ? `/doc/SC Purchase Invoice/${d.debit_note}` : null },
        { label: 'PR đổi hàng', value: (d) => d.replacement_pr,
          link: (d) => d.replacement_pr ? `/doc/SC Purchase Receipt/${d.replacement_pr}` : null },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Vật tư nhập kho',
      icon: 'package-plus',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên vật tư', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Lô', accessor: 'batch_no', mono: true },
        { label: 'HSD', accessor: 'expiry_date', fmt: 'date', align: 'center' },
        { label: 'Đơn giá', accessor: 'rate', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, 'qty', null, null, null, 'amount'],
    },
  },

  // ===== Financial: PI ======================================================
  'SC Purchase Invoice': {
    icon: 'receipt',
    accentLabel: 'Hoá đơn mua hàng',
    title: (d) => d.supplier_name || d.supplier || '—',
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.invoice_date ? `Ngày HĐ ${fmtDate(d.invoice_date)}` : null },
      { icon: 'clock', text: (d) => {
        if (!d.due_date) return null
        const days = daysBetween(today(), d.due_date)
        if (d.outstanding_amount > 0 && days < 0) return `Quá hạn ${Math.abs(days)} ngày`
        return d.outstanding_amount > 0 ? `Đến hạn còn ${days} ngày` : `Đến hạn ${fmtDate(d.due_date)}`
      } },
      { icon: 'hash', text: (d) => d.supplier_invoice_no ? `Số HĐ NCC ${d.supplier_invoice_no}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      if (d.docstatus === 0) return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
      const out = Number(d.outstanding_amount) || 0
      if (out <= 0) return { label: 'Đã thanh toán', cls: 'sc-badge-success', icon: 'check-circle-2' }
      if (d.payment_hold) return { label: 'Tạm hold', cls: 'sc-badge-warning', icon: 'pause-circle' }
      if (d.due_date && new Date(d.due_date) < today()) return { label: 'Quá hạn', cls: 'sc-badge-critical', icon: 'alert-circle' }
      return { label: 'Chờ thanh toán', cls: 'sc-badge-info', icon: 'hourglass' }
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng cộng', value: (d) => d.grand_total, fmt: 'moneyShort' },
      { icon: 'check', label: 'Đã trả', value: (d) => d.paid_amount, fmt: 'moneyShort',
        sublabel: (d) => {
          const g = Number(d.grand_total) || 0, p = Number(d.paid_amount) || 0
          return g > 0 ? `${((p / g) * 100).toFixed(1)}% tổng` : null
        } },
      { icon: 'hourglass', label: 'Còn phải trả', value: (d) => d.outstanding_amount, fmt: 'moneyShort',
        accent: (d) => Number(d.outstanding_amount) > 0 ? 'amber' : 'emerald' },
      { icon: 'scale', label: '3-way match',
        value: (d) => d.three_way_match_status || '—',
        sublabel: (d) => d.match_variance_amount ? `Lệch ${fmtVND(d.match_variance_amount)}` : null,
        accent: (d) => d.three_way_match_status === 'Mismatch' ? 'critical' :
                       d.three_way_match_status === 'Match' ? 'emerald' : 'default' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Purchase Order', value: (d) => d.purchase_order,
          link: (d) => d.purchase_order ? `/doc/SC Purchase Order/${d.purchase_order}` : null },
        { label: 'Purchase Receipt', value: (d) => d.purchase_receipt,
          link: (d) => d.purchase_receipt ? `/doc/SC Purchase Receipt/${d.purchase_receipt}` : null },
        { label: 'Loại', value: (d) => d.is_debit_note ? 'Debit Note' : d.is_credit_note ? 'Credit Note' : 'HĐ thường' },
        { label: 'Giải trình lệch', value: (d) => d.mismatch_explanation, pre: true },
      ]},
      { title: 'Thanh toán', icon: 'credit-card', fields: [
        { label: 'Điều khoản', value: (d) => d.payment_terms },
        { label: 'Cấp duyệt', value: (d) => d.approval_required_by },
        { label: 'Đã duyệt', value: (d) => d.approved_by },
        { label: 'Lúc', value: (d) => d.approved_at ? fmtDateTime(d.approved_at) : '—' },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Chi tiết hoá đơn',
      icon: 'list',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'rate', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, 'qty', null, 'amount'],
    },
  },

  // ===== Operational: MR ====================================================
  'SC Material Request': {
    icon: 'clipboard-plus',
    accentLabel: 'Yêu cầu vật tư',
    title: (d) => d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.transaction_date ? `Yêu cầu ${fmtDate(d.transaction_date)}` : null },
      { icon: 'clock', text: (d) => d.schedule_date ? `Cần ${fmtDate(d.schedule_date)}` : null },
      { icon: 'warehouse', text: (d) => d.warehouse ? `Kho đích ${d.warehouse}` : null },
      { icon: 'user', text: (d) => d.requested_by ? `Bởi ${d.requested_by}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Pending': { label: 'Chờ duyệt', cls: 'sc-badge-warning', icon: 'clock' },
        'Approved': { label: 'Đã duyệt', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Ordered': { label: 'Đã chuyển PO', cls: 'sc-badge-info', icon: 'shopping-cart' },
        'Received': { label: 'Đã hoàn tất', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Stopped': { label: 'Dừng', cls: 'sc-badge-neutral', icon: 'pause-circle' },
        'Rejected': { label: 'Đã từ chối', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL', value: (d) => d.total_qty, fmt: 'number' },
      { icon: 'wallet', label: 'Ước tính giá trị', value: (d) => d.total_estimated_cost, fmt: 'moneyShort' },
      { icon: 'tag', label: 'Loại', value: (d) => d.request_type || '—' },
    ],
    sections: [
      { title: 'Bối cảnh', icon: 'info', fields: [
        // L10: người yêu cầu hiển thị Tên (account), không để trống
        { label: 'Người yêu cầu', value: (d) => {
          const acc = d.requested_by || d.owner || '—'
          return d.requested_by_name ? `${d.requested_by_name} (${acc})` : acc
        } },
        { label: 'Khách hàng yêu cầu', value: (d) => d.customer || '—',
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Kho đích', value: (d) => d.warehouse },
        { label: 'Procurement Plan', value: (d) => d.procurement_plan,
          link: (d) => d.procurement_plan ? `/doc/Procurement Plan/${d.procurement_plan}` : null },
        { label: 'Lý do', value: (d) => d.reason, pre: true },
        { label: 'Lý do từ chối', value: (d) => d.rejection_reason, pre: true },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Dòng yêu cầu',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL YC', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'HĐ khung', accessor: 'framework_contract', mono: true },
        { label: 'Đơn giá ƯT', accessor: 'estimated_unit_cost', align: 'right', fmt: 'money' },
        { label: 'Cần lúc', accessor: 'schedule_date', fmt: 'date', align: 'center' },
      ],
      totals: [null, null, null, 'qty', null, null, null],
    },
  },

  // ===== Operational: SE ====================================================
  'SC Stock Entry': {
    icon: 'arrow-right-left',
    accentLabel: 'Giao dịch kho',
    title: (d) => d.entry_type || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.posting_date ? `Posting ${fmtDate(d.posting_date)}` : null },
      { icon: 'warehouse', text: (d) => {
        if (d.entry_type === 'Material Transfer') return `${d.from_warehouse || '?'} → ${d.to_warehouse || '?'}`
        if (d.entry_type === 'Material Receipt') return `Nhận về ${d.to_warehouse || '?'}`
        if (d.entry_type === 'Material Issue') return `Xuất từ ${d.from_warehouse || '?'}`
        return null
      } },
      { icon: 'link', text: (d) => d.transfer_request ? `TR ${d.transfer_request}` : null },
      { icon: 'alert-circle', text: (d) => d.recall_notice ? `Recall ${d.recall_notice}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      if (d.docstatus === 1) return { label: 'Đã hạch toán kho', cls: 'sc-badge-success', icon: 'check-circle-2' }
      return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
    },
    tiles: [
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL', value: (d) => d.total_qty, fmt: 'number' },
      { icon: 'wallet', label: 'Tổng giá trị', value: (d) => d.total_value, fmt: 'moneyShort' },
      { icon: 'shield-alert', label: 'FEFO Override',
        value: (d) => (d.items || []).filter(r => r.fefo_override).length,
        fmt: 'number',
        sublabel: (d) => (d.items || []).filter(r => r.fefo_override).length ? 'Có dòng override' : null,
        accent: (d) => (d.items || []).filter(r => r.fefo_override).length ? 'amber' : 'default' },
    ],
    sections: [
      { title: 'Lộ trình', icon: 'route', fields: [
        { label: 'Loại GD', value: (d) => d.entry_type },
        { label: 'Kho nguồn', value: (d) => d.from_warehouse || '—' },
        { label: 'Kho đích', value: (d) => d.to_warehouse || '—' },
        { label: 'Mục đích', value: (d) => d.purpose },
        { label: 'PDA Session', value: (d) => d.pda_session_id },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Dòng giao dịch',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Lô', accessor: 'batch', mono: true },
        { label: 'Đơn giá', accessor: 'valuation_rate', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, null, 'qty', null, null, 'amount'],
    },
  },

  // ===== Operational: TR ====================================================
  'SC Transfer Request': {
    icon: 'arrow-right-left',
    accentLabel: 'Yêu cầu chuyển kho',
    title: (d) => `${d.from_warehouse || '?'} → ${d.to_warehouse || '?'}`,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.request_date ? `Yêu cầu ${fmtDate(d.request_date)}` : null },
      { icon: 'clock', text: (d) => d.required_by ? `Cần ${fmtDate(d.required_by)}` : null },
      { icon: 'user', text: (d) => d.requested_by ? `Bởi ${d.requested_by}` : null },
      { icon: 'building-2', text: (d) => d.requested_for_department ? `Khoa ${d.requested_for_department}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Pending': { label: 'Chờ duyệt', cls: 'sc-badge-warning', icon: 'clock' },
        'Approved': { label: 'Đã duyệt', cls: 'sc-badge-info', icon: 'check' },
        'Transferred': { label: 'Đã chuyển kho', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Rejected': { label: 'Đã từ chối', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL yêu cầu', value: (d) => d.total_qty, fmt: 'number' },
      { icon: 'check', label: 'Đã chuyển',
        value: (d) => (d.items || []).reduce((s, r) => s + (Number(r.transferred_qty) || 0), 0),
        fmt: 'number',
        sublabel: (d) => {
          const t = Number(d.total_qty) || 0
          const got = (d.items || []).reduce((s, r) => s + (Number(r.transferred_qty) || 0), 0)
          return t > 0 ? `${((got / t) * 100).toFixed(1)}%` : null
        },
        accent: (d) => {
          const t = Number(d.total_qty) || 0
          const got = (d.items || []).reduce((s, r) => s + (Number(r.transferred_qty) || 0), 0)
          return t > 0 && got >= t ? 'emerald' : 'default'
        } },
      { icon: 'shield-check', label: 'Cần Manager',
        value: (d) => d.requires_manager_approval ? 'Có' : '—',
        accent: (d) => d.requires_manager_approval ? 'amber' : 'default' },
    ],
    sections: [
      { title: 'Routing', icon: 'route', fields: [
        { label: 'Loại', value: (d) => d.transfer_type },
        { label: 'Kho nguồn', value: (d) => d.from_warehouse },
        { label: 'Kho đích', value: (d) => d.to_warehouse },
        { label: 'Khoa', value: (d) => d.requested_for_department },
        { label: 'Stock Entry', value: (d) => d.stock_entry,
          link: (d) => d.stock_entry ? `/doc/SC Stock Entry/${d.stock_entry}` : null },
      ]},
    ],
    approval: (d) => d.approved_by || d.approved_at ? [
      { title: 'Duyệt chuyển kho', by: d.approved_by, at: d.approved_at, done: !!d.approved_at },
      { title: 'Tạo Stock Entry', by: null, at: null, done: !!d.stock_entry, comment: d.stock_entry ? d.stock_entry : null },
    ] : [],
    items: {
      field: 'items',
      label: 'Vật tư chuyển',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL YC', accessor: 'requested_qty', align: 'right', fmt: 'number' },
        { label: 'Duyệt', accessor: 'approved_qty', align: 'right', fmt: 'number' },
        { label: 'Đã chuyển', accessor: 'transferred_qty', align: 'right', fmt: 'number', anchor: 'navy' },
        { label: 'Lô', accessor: 'batch', mono: true },
      ],
      totals: [null, null, null, 'requested_qty', 'approved_qty', 'transferred_qty', null],
    },
  },

  // ===== M10: Recall Notice =================================================
  'SC Recall Notice': {
    icon: 'alert-octagon',
    accentLabel: 'Thông báo thu hồi',
    title: (d) => d.batch_no ? `Lô ${d.batch_no}` : d.item ? `VT ${d.item}` : d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.recall_date ? `Thu hồi ${fmtDate(d.recall_date)}` : null },
      { icon: 'package', text: (d) => d.batch_no ? `Lô ${d.batch_no}` : null },
      { icon: 'building-2', text: (d) => d.supplier ? `NCC ${d.supplier}` : null },
      { icon: 'gavel', text: (d) => d.regulatory_reference ? d.regulatory_reference : null },
    ],
    status: (d) => {
      const sev = d.severity || ''
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      // Backend enum = 'Class I (Critical)' / 'Class II (High)' / 'Class III (Low)'
      // → khớp theo tiền tố Class I/II/III để không phụ thuộc hậu tố.
      const sevMap = {
        'Class I': { label: 'Class I — nguy cấp', cls: 'sc-badge-critical', icon: 'alert-octagon' },
        'Class II': { label: 'Class II', cls: 'sc-badge-warning', icon: 'alert-triangle' },
        'Class III': { label: 'Class III', cls: 'sc-badge-info', icon: 'info' },
      }
      const sevKey = sev.startsWith('Class III') ? 'Class III'
        : sev.startsWith('Class II') ? 'Class II'
        : sev.startsWith('Class I') ? 'Class I' : null
      if (sevKey) return sevMap[sevKey]
      return statusByField(d, {
        'Open': { label: 'Đang thu hồi', cls: 'sc-badge-warning', icon: 'alert-triangle' },
        'In Progress': { label: 'Đang xử lý', cls: 'sc-badge-info', icon: 'loader' },
        'Closed': { label: 'Đã đóng', cls: 'sc-badge-success', icon: 'check-circle-2' },
      })
    },
    tiles: [
      { icon: 'package', label: 'SL ảnh hưởng', value: (d) => d.total_affected_qty, fmt: 'number' },
      { icon: 'undo-2', label: 'Đã thu hồi', value: (d) => d.recovered_qty, fmt: 'number',
        sublabel: (d) => d.recall_resolution_pct ? `${d.recall_resolution_pct.toFixed(1)}% giải quyết` : null,
        accent: 'emerald' },
      { icon: 'trash-2', label: 'Đã huỷ', value: (d) => d.destroyed_qty, fmt: 'number' },
      { icon: 'hourglass', label: 'Còn ngoài', value: (d) => d.outstanding_qty, fmt: 'number',
        accent: (d) => Number(d.outstanding_qty) > 0 ? 'amber' : 'emerald' },
    ],
    sections: [
      { title: 'Nguyên nhân & xử lý', icon: 'shield-alert', fields: [
        { label: 'Loại thu hồi', value: (d) => d.recall_type },
        { label: 'Mức độ', value: (d) => d.severity },
        { label: 'Lý do', value: (d) => d.recall_reason, pre: true },
        { label: 'Pháp lý', value: (d) => d.regulatory_reference },
        { label: 'Phương án', value: (d) => d.resolution },
        { label: 'Ngày xử lý', value: (d) => d.resolution_date ? fmtDate(d.resolution_date) : '—' },
      ]},
      { title: 'Tham chiếu & thông báo', icon: 'send', fields: [
        { label: 'PR trả NCC', value: (d) => d.return_pr,
          link: (d) => d.return_pr ? `/doc/SC Purchase Receipt/${d.return_pr}` : null },
        { label: 'Phiếu huỷ', value: (d) => d.write_off_entry,
          link: (d) => d.write_off_entry ? `/doc/SC Stock Entry/${d.write_off_entry}` : null },
        { label: 'Báo BS điều trị', value: (d) => d.clinical_notified_at ? fmtDateTime(d.clinical_notified_at) : '—' },
        { label: 'Người duyệt', value: (d) => d.approved_by },
        { label: 'Duyệt lúc', value: (d) => d.approved_at ? fmtDateTime(d.approved_at) : '—' },
      ]},
    ],
    items: {
      field: 'affected_items',
      label: 'Vị trí ảnh hưởng',
      icon: 'map-pin',
      columns: [
        { label: 'Loại', accessor: 'location_type', align: 'center' },
        { label: 'Kho/Khoa', accessor: (r) => r.warehouse || r.department || '—', mono: true },
        { label: 'Chứng từ', accessor: 'voucher_no', mono: true, anchor: 'navy' },
        { label: 'Ngày', accessor: 'voucher_date', fmt: 'date', align: 'center' },
        { label: 'SL xuất', accessor: 'qty_issued', align: 'right', fmt: 'number' },
        { label: 'Đã thu', accessor: 'recovered_qty', align: 'right', fmt: 'number' },
        { label: 'Đã huỷ', accessor: 'destroyed_qty', align: 'right', fmt: 'number' },
        { label: 'Còn', accessor: 'outstanding_qty', align: 'right', fmt: 'number', anchor: 'navy' },
        { label: 'Trạng thái', accessor: 'status' },
      ],
      totals: [null, null, null, null, null, 'qty_issued', 'recovered_qty', 'destroyed_qty', 'outstanding_qty', null],
    },
  },

  // ===== M10: Investigation Report ==========================================
  'SC Investigation Report': {
    icon: 'search',
    accentLabel: 'Báo cáo điều tra',
    title: (d) => d.investigation_type || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.investigation_date ? `Mở ${fmtDate(d.investigation_date)}` : null },
      { icon: 'package', text: (d) => d.item ? `VT ${d.item}` : null },
      { icon: 'warehouse', text: (d) => d.warehouse ? `Kho ${d.warehouse}` : null },
      { icon: 'package', text: (d) => d.batch ? `Lô ${d.batch}` : null },
      { icon: 'user', text: (d) => d.triggered_by ? `Mở bởi ${d.triggered_by}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Open': { label: 'Đang điều tra', cls: 'sc-badge-warning', icon: 'search' },
        'Pending Review': { label: 'Chờ duyệt', cls: 'sc-badge-info', icon: 'hourglass' },
        'Closed': { label: 'Đã đóng', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Rejected': { label: 'Bác bỏ', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'trending-down', label: 'Δ qty', value: (d) => d.variance_qty, fmt: 'number',
        accent: (d) => Number(d.variance_qty) < 0 ? 'critical' :
                       Number(d.variance_qty) > 0 ? 'amber' : 'default' },
      { icon: 'wallet', label: 'Δ giá trị', value: (d) => d.variance_value, fmt: 'moneyShort' },
      { icon: 'alert-triangle', label: 'Bất thường', value: (d) => d.anomalies_detected, fmt: 'number',
        accent: (d) => Number(d.anomalies_detected) > 0 ? 'critical' : 'default' },
      { icon: 'list', label: 'Findings', value: (d) => (d.findings || []).length, fmt: 'number' },
    ],
    sections: [
      { title: 'Scope điều tra', icon: 'scan-search', fields: [
        { label: 'Loại sự cố', value: (d) => d.investigation_type },
        { label: 'Vật tư', value: (d) => d.item,
          link: (d) => d.item ? `/doc/SC Item/${d.item}` : null },
        { label: 'Kho', value: (d) => d.warehouse },
        { label: 'Lô', value: (d) => d.batch },
        { label: 'Từ ngày', value: (d) => d.period_start ? fmtDate(d.period_start) : '—' },
        { label: 'Đến ngày', value: (d) => d.period_end ? fmtDate(d.period_end) : '—' },
        { label: 'Filter user', value: (d) => d.filter_user },
        { label: 'Mô tả', value: (d) => d.description, pre: true },
      ]},
      { title: 'Kết luận & khắc phục', icon: 'gavel', fields: [
        { label: 'Khuyến nghị', value: (d) => d.recommendation, pre: true },
        { label: 'Kết luận', value: (d) => d.conclusion, pre: true },
        { label: 'Người duyệt', value: (d) => d.approved_by },
        { label: 'Duyệt lúc', value: (d) => d.approved_at ? fmtDateTime(d.approved_at) : '—' },
        { label: 'Phiếu điều chỉnh', value: (d) => d.system_error_adjustment,
          link: (d) => d.system_error_adjustment ? `/doc/SC Stock Reconciliation/${d.system_error_adjustment}` : null },
      ]},
    ],
    items: {
      field: 'findings',
      label: 'Findings — bất thường phát hiện',
      icon: 'alert-circle',
      columns: [
        { label: 'Loại', accessor: 'finding_type' },
        { label: 'Mức độ', accessor: 'severity', align: 'center' },
        { label: 'Chứng từ', accessor: 'voucher_no', mono: true, anchor: 'navy' },
        { label: 'Ngày', accessor: 'voucher_date', fmt: 'date', align: 'center' },
        { label: 'Người nghi vấn', accessor: 'user_suspected', mono: true },
        { label: 'Δ qty', accessor: 'qty_change', align: 'right', fmt: 'number' },
        { label: 'Hành động', accessor: 'action_taken' },
      ],
    },
  },

  // ===== M10: Inventory Count Sheet =========================================
  'SC Inventory Count Sheet': {
    icon: 'clipboard-check',
    accentLabel: 'Phiếu kiểm kê',
    title: (d) => d.warehouse || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.count_date ? `Đếm ${fmtDate(d.count_date)}` : null },
      { icon: 'user', text: (d) => d.counted_by ? `Thủ kho ${d.counted_by}` : null },
      { icon: 'tag', text: (d) => d.count_scope ? `Phạm vi ${d.count_scope}` : null },
      { icon: 'package', text: (d) => d.item_group ? `Nhóm ${d.item_group}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Planned': { label: 'Đã lên kế hoạch', cls: 'sc-badge-info', icon: 'clipboard-list' },
        'In Progress': { label: 'Đang đếm', cls: 'sc-badge-warning', icon: 'loader' },
        'Counted': { label: 'Đếm xong', cls: 'sc-badge-info', icon: 'check' },
        'Reconciled': { label: 'Đã điều chỉnh kho', cls: 'sc-badge-success', icon: 'check-circle-2' },
      })
    },
    tiles: [
      { icon: 'list', label: 'Tổng items', value: (d) => d.total_items, fmt: 'number' },
      { icon: 'alert-triangle', label: 'Lệch', value: (d) => d.mismatched_items, fmt: 'number',
        sublabel: (d) => {
          const t = Number(d.total_items) || 0
          return t > 0 ? `${((Number(d.mismatched_items || 0) / t) * 100).toFixed(1)}% items` : null
        },
        accent: (d) => Number(d.mismatched_items) > 0 ? 'amber' : 'emerald' },
      { icon: 'trending-down', label: 'Δ qty', value: (d) => d.total_variance_qty, fmt: 'number',
        accent: (d) => Number(d.total_variance_qty) < 0 ? 'critical' :
                       Number(d.total_variance_qty) > 0 ? 'amber' : 'default' },
      { icon: 'wallet', label: 'Δ giá trị', value: (d) => d.total_variance_value, fmt: 'moneyShort' },
    ],
    sections: [
      { title: 'Phạm vi kiểm kê', icon: 'crosshair', fields: [
        { label: 'Kho', value: (d) => d.warehouse },
        { label: 'Phạm vi', value: (d) => d.count_scope },
        { label: 'Nhóm vật tư', value: (d) => d.item_group },
        { label: 'Zone bin', value: (d) => d.bin_zone },
        { label: 'Ngưỡng đếm lại', value: (d) => d.recount_threshold_pct ? `${d.recount_threshold_pct}%` : '—' },
      ]},
      { title: 'Quá trình & điều chỉnh', icon: 'shield-check', fields: [
        { label: 'Lập kế hoạch', value: (d) => d.planned_by },
        { label: 'Thủ kho đếm', value: (d) => d.counted_by },
        { label: 'Manager chứng kiến', value: (d) => d.manager_witness },
        { label: 'SR đã tạo', value: (d) => d.stock_reconciliation,
          link: (d) => d.stock_reconciliation ? `/doc/SC Stock Reconciliation/${d.stock_reconciliation}` : null },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Dòng kiểm kê',
      icon: 'list-checks',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'Tên', accessor: 'item_name', max: true },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'Lô', accessor: 'batch', mono: true },
        { label: 'Bin', accessor: 'bin_location', mono: true },
        { label: 'Hệ thống', accessor: 'system_qty', align: 'right', fmt: 'number' },
        { label: 'Thực', accessor: 'actual_qty', align: 'right', fmt: 'number' },
        { label: 'Δ', accessor: 'difference', align: 'right', fmt: 'number', anchor: 'navy' },
        { label: '%', accessor: 'variance_pct', align: 'right', fmt: 'pct' },
      ],
      totals: [null, null, null, null, null, 'system_qty', 'actual_qty', 'difference', null],
    },
  },

  // ===== M7 Sales: Customer =================================================
  'SC Customer': {
    icon: 'building-2',
    accentLabel: 'Khách hàng',
    title: (d) => d.customer_name || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'hash', text: (d) => d.tax_code ? `MST ${d.tax_code}` : null },
      { icon: 'user', text: (d) => d.portal_user ? `Portal ${d.portal_user}` : 'Chưa có tài khoản Portal' },
    ],
    status: (d) => statusByField(d, {
      'Hoạt động': { label: 'Hoạt động', cls: 'sc-badge-success', icon: 'check-circle-2' },
      'Tạm ngưng': { label: 'Tạm ngưng', cls: 'sc-badge-neutral', icon: 'pause-circle' },
    }),
    tiles: [
      { icon: 'wallet', label: 'Hạn mức nợ', value: (d) => d.credit_limit, fmt: 'moneyShort' },
      { icon: 'file-text', label: 'Điều khoản TT', value: (d) => d.payment_terms || '—' },
      { icon: 'user-check', label: 'Tài khoản Portal',
        value: (d) => d.portal_user ? 'Đã gán' : 'Chưa gán',
        accent: (d) => d.portal_user ? 'emerald' : 'amber' },
    ],
    sections: [
      { title: 'Thông tin khách hàng', icon: 'info', fields: [
        { label: 'Mã số thuế', value: (d) => d.tax_code },
        { label: 'Tài khoản Portal', value: (d) => d.portal_user || 'Chưa gán — không thể kích hoạt (BRU-CUS-001)' },
        { label: 'Điều khoản TT', value: (d) => d.payment_terms },
        { label: 'Địa chỉ hoá đơn', value: (d) => d.billing_address, pre: true },
        { label: 'Địa chỉ giao hàng', value: (d) => d.shipping_address, pre: true },
      ]},
    ],
  },

  // ===== M7 Sales: Sales Framework Contract =================================
  'SC Sales Framework Contract': {
    icon: 'file-text',
    accentLabel: 'HĐ khung bán hàng',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'hash', text: (d) => d.contract_number ? `Số ${d.contract_number}` : null },
      { icon: 'calendar', text: (d) => d.valid_from ? `Từ ${fmtDate(d.valid_from)}` : null },
      { icon: 'calendar', text: (d) => d.valid_to ? `Đến ${fmtDate(d.valid_to)}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Nháp': { label: 'Nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Chờ duyệt': { label: 'Chờ duyệt', cls: 'sc-badge-warning', icon: 'clock' },
        'Hiệu lực': { label: 'Hiệu lực', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Hết hạn': { label: 'Hết hạn', cls: 'sc-badge-critical', icon: 'alert-circle' },
        'Thanh lý': { label: 'Thanh lý', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng giá trị', value: (d) => d.total_value, fmt: 'moneyShort' },
      { icon: 'trending-up', label: 'Đã bán', value: (d) => d.used_value, fmt: 'moneyShort' },
      { icon: 'clock', label: 'Đang gọi', value: (d) => d.committed_value, fmt: 'moneyShort' },
      { icon: 'piggy-bank', label: 'Còn lại', value: (d) => d.remaining_value, fmt: 'moneyShort' },
    ],
    sections: [
      { title: 'Thông tin hợp đồng', icon: 'file-text', fields: [
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Số hợp đồng', value: (d) => d.contract_number || '—' },
        { label: 'Ngày ký', value: (d) => d.contract_date ? fmtDate(d.contract_date) : '—' },
        { label: 'Hiệu lực từ', value: (d) => d.valid_from ? fmtDate(d.valid_from) : '—' },
        { label: 'Hết hạn', value: (d) => d.valid_to ? fmtDate(d.valid_to) : '—' },
        { label: 'Người duyệt', value: (d) => d.approved_by || '—' },
      ]},
      { title: 'Điều khoản', icon: 'scroll-text', fields: [
        { label: 'Điều khoản thanh toán', value: (d) => d.payment_terms || '—' },
        { label: 'Điều khoản giao hàng', value: (d) => d.delivery_terms || '—' },
      ]},
      { title: 'Hồ sơ & Ghi chú', icon: 'paperclip', fields: [
        { label: 'File hợp đồng', value: (d) => d.attachment ? 'Đã đính kèm' : '—',
          link: (d) => d.attachment || null },
        { label: 'Ghi chú', value: (d) => d.remarks || '—' },
        { label: 'Ngày thanh lý', value: (d) => d.termination_date ? fmtDate(d.termination_date) : '—' },
        { label: 'Lý do thanh lý', value: (d) => d.termination_reason || '—' },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Danh mục vật tư',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL HĐ', accessor: 'contract_qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'unit_price', align: 'right', fmt: 'money' },
        { label: 'Đã bán', accessor: 'sold_qty', align: 'right', fmt: 'number' },
        { label: 'Còn lại', accessor: 'remaining_qty', align: 'right', fmt: 'number', anchor: 'navy' },
      ],
      totals: [null, null, 'contract_qty', null, 'sold_qty', 'remaining_qty'],
    },
  },

  // ===== M7 Sales: Sales Order (FIX green-badge-on-reject) ==================
  'SC Sales Order': {
    icon: 'clipboard-list',
    accentLabel: 'Đơn bán hàng',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.order_date ? `Đặt ${fmtDate(d.order_date)}` : null },
      { icon: 'file-text', text: (d) => d.framework_contract ? `HĐ ${d.framework_contract}` : null },
    ],
    // Trạng thái lấy theo field `status` (VN) — KHÔNG suy từ docstatus, vì
    // approve/reject xảy ra ở docstatus=1 (SO bị từ chối vẫn docstatus=1).
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Chờ duyệt': { label: 'Chờ duyệt', cls: 'sc-badge-warning', icon: 'clock' },
        'Đã duyệt': { label: 'Đã duyệt', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Đang xử lý': { label: 'Đang xử lý', cls: 'sc-badge-info', icon: 'loader' },
        'Đã bàn giao': { label: 'Đã bàn giao', cls: 'sc-badge-info', icon: 'truck' },
        'Hoàn tất': { label: 'Hoàn tất', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Từ chối': { label: 'Từ chối', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng tiền', value: (d) => d.total_amount, fmt: 'moneyShort' },
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'shield-alert', label: 'Khoá tín dụng',
        value: (d) => d.credit_hold ? 'Có' : '—',
        accent: (d) => d.credit_hold ? 'critical' : 'default' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'HĐ khung', value: (d) => d.framework_contract_display || d.framework_contract,
          link: (d) => d.framework_contract ? `/doc/SC Sales Framework Contract/${d.framework_contract}` : null },
        { label: 'Người duyệt', value: (d) => d.approval_by },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Chi tiết đơn hàng',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'unit_price', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, null, 'qty', null, 'amount'],
    },
  },

  // ===== M7 Sales: Delivery Note ============================================
  'SC Delivery Note': {
    icon: 'truck',
    accentLabel: 'Phiếu giao hàng',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.delivery_date ? `Giao ${fmtDate(d.delivery_date)}` : null },
      { icon: 'file-text', text: (d) => d.sales_order ? `SO ${d.sales_order}` : null },
      { icon: 'warehouse', text: (d) => d.from_warehouse ? `Kho ${d.from_warehouse}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Nháp': { label: 'Nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Đã giao': { label: 'Đã giao', cls: 'sc-badge-info', icon: 'truck' },
        'Đã nghiệm thu': { label: 'Đã nghiệm thu', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Đã xuất HĐ': { label: 'Đã xuất HĐ', cls: 'sc-badge-success', icon: 'receipt' },
      })
    },
    tiles: [
      { icon: 'list', label: 'Số dòng', value: (d) => (d.items || []).length, fmt: 'number' },
      { icon: 'boxes', label: 'Tổng SL giao',
        value: (d) => (d.items || []).reduce((s, r) => s + (Number(r.qty) || 0), 0), fmt: 'number' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Sales Order', value: (d) => d.sales_order,
          link: (d) => d.sales_order ? `/doc/SC Sales Order/${d.sales_order}` : null },
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Kho xuất', value: (d) => d.from_warehouse },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Vật tư giao',
      icon: 'package',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'UOM', accessor: 'uom', align: 'center', anchor: 'muted' },
        { label: 'SL giao', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Lô', accessor: 'batch', mono: true },
        { label: 'Kho', accessor: 'warehouse', mono: true },
      ],
      totals: [null, null, 'qty', null, null],
    },
  },

  // ===== M7 Sales: Acceptance Record ========================================
  'SC Acceptance Record': {
    icon: 'check-circle',
    accentLabel: 'Biên bản nghiệm thu',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.acceptance_date ? `Nghiệm thu ${fmtDate(d.acceptance_date)}` : null },
      { icon: 'file-text', text: (d) => d.delivery_note ? `DN ${d.delivery_note}` : null },
      { icon: 'user', text: (d) => d.accepted_by ? `Người nhận ${d.accepted_by}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Nháp': { label: 'Nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Đã nghiệm thu': { label: 'Đã nghiệm thu', cls: 'sc-badge-success', icon: 'check-circle-2' },
      })
    },
    tiles: [
      { icon: 'file-text', label: 'DN tham chiếu', value: (d) => d.delivery_note || '—' },
      { icon: 'user', label: 'Người nhận', value: (d) => d.accepted_by || '—' },
    ],
    sections: [
      { title: 'Thông tin nghiệm thu', icon: 'info', fields: [
        { label: 'Delivery Note', value: (d) => d.delivery_note,
          link: (d) => d.delivery_note ? `/doc/SC Delivery Note/${d.delivery_note}` : null },
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Người nhận hàng', value: (d) => d.accepted_by },
        { label: 'Ghi chú', value: (d) => d.note, pre: true },
      ]},
    ],
  },

  // ===== M7/M8: Sales Invoice ===============================================
  'SC Sales Invoice': {
    icon: 'receipt',
    accentLabel: 'Hoá đơn bán hàng',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.invoice_date ? `Ngày HĐ ${fmtDate(d.invoice_date)}` : null },
      { icon: 'file-text', text: (d) => d.delivery_note ? `DN ${d.delivery_note}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      return statusByField(d, {
        'Nháp': { label: 'Nháp', cls: 'sc-badge-neutral', icon: 'file' },
        'Đã phát hành': { label: 'Đã phát hành', cls: 'sc-badge-info', icon: 'send' },
        'Đã thu một phần': { label: 'Đã thu một phần', cls: 'sc-badge-warning', icon: 'hourglass' },
        'Đã thu đủ': { label: 'Đã thu đủ', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Hủy': { label: 'Hủy', cls: 'sc-badge-critical', icon: 'x-circle' },
      })
    },
    tiles: [
      { icon: 'wallet', label: 'Tổng cộng', value: (d) => d.grand_total, fmt: 'moneyShort' },
      { icon: 'check', label: 'Đã thu',
        value: (d) => (Number(d.grand_total) || 0) - (Number(d.outstanding_amount) || 0), fmt: 'moneyShort',
        sublabel: (d) => {
          const g = Number(d.grand_total) || 0
          const p = g - (Number(d.outstanding_amount) || 0)
          return g > 0 ? `${((p / g) * 100).toFixed(1)}% tổng` : null
        } },
      { icon: 'hourglass', label: 'Còn phải thu', value: (d) => d.outstanding_amount, fmt: 'moneyShort',
        accent: (d) => Number(d.outstanding_amount) > 0 ? 'amber' : 'emerald' },
      { icon: 'percent', label: 'Thuế suất',
        value: (d) => d.tax_rate != null ? `${d.tax_rate}%` : '—' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Delivery Note', value: (d) => d.delivery_note,
          link: (d) => d.delivery_note ? `/doc/SC Delivery Note/${d.delivery_note}` : null },
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Tiền thuế', value: (d) => d.tax_amount != null ? fmtVND(d.tax_amount) : '—' },
      ]},
    ],
    items: {
      field: 'items',
      label: 'Chi tiết hoá đơn',
      icon: 'list',
      columns: [
        { label: 'Mã VT', accessor: 'item', mono: true, anchor: 'navy' },
        { label: 'SL', accessor: 'qty', align: 'right', fmt: 'number' },
        { label: 'Đơn giá', accessor: 'unit_price', align: 'right', fmt: 'money' },
        { label: 'Thành tiền', accessor: 'amount', align: 'right', fmt: 'money', anchor: 'navy' },
      ],
      totals: [null, 'qty', null, 'amount'],
    },
  },

  // ===== M7/M8: Sales Receipt (no status field → dùng docstatus) ============
  'SC Sales Receipt': {
    icon: 'credit-card',
    accentLabel: 'Phiếu thu tiền',
    title: (d) => d.customer_name || d.customer || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.receipt_date ? `Thu ${fmtDate(d.receipt_date)}` : null },
      { icon: 'file-text', text: (d) => d.sales_invoice ? `SI ${d.sales_invoice}` : null },
      { icon: 'credit-card', text: (d) => d.mode || null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      if (d.docstatus === 1) return { label: 'Đã thu', cls: 'sc-badge-success', icon: 'check-circle-2' }
      return { label: 'Bản nháp', cls: 'sc-badge-neutral', icon: 'file' }
    },
    tiles: [
      { icon: 'wallet', label: 'Số tiền thu', value: (d) => d.amount, fmt: 'moneyShort' },
      { icon: 'credit-card', label: 'Hình thức', value: (d) => d.mode || '—' },
    ],
    sections: [
      { title: 'Tham chiếu', icon: 'link', fields: [
        { label: 'Hoá đơn bán', value: (d) => d.sales_invoice,
          link: (d) => d.sales_invoice ? `/doc/SC Sales Invoice/${d.sales_invoice}` : null },
        { label: 'Khách hàng', value: (d) => d.customer_name || d.customer,
          link: (d) => d.customer ? `/doc/SC Customer/${d.customer}` : null },
        { label: 'Ngày thu', value: (d) => d.receipt_date ? fmtDate(d.receipt_date) : '—' },
      ]},
    ],
  },

  // ===== M3: Quality Inspection (overall_status resolver + readings) ========
  'SC Quality Inspection': {
    icon: 'flask-conical',
    accentLabel: 'Kiểm tra chất lượng',
    title: (d) => d.item_name || d.item || d.name,
    subtitleMono: (d) => d.name,
    meta: [
      { icon: 'calendar', text: (d) => d.inspection_date ? `Kiểm ${fmtDate(d.inspection_date)}` : null },
      { icon: 'package-check', text: (d) => d.purchase_receipt ? `PR ${d.purchase_receipt}` : null },
      { icon: 'building-2', text: (d) => d.supplier ? `NCC ${d.supplier}` : null },
      { icon: 'layers', text: (d) => d.batch ? `Lô ${d.batch}` : null },
    ],
    status: (d) => {
      if (d.docstatus === 2) return { label: 'Đã huỷ', cls: 'sc-badge-neutral', icon: 'x-circle' }
      const map = {
        'Pending': { label: 'Chờ kiểm', cls: 'sc-badge-warning', icon: 'clock' },
        'Accepted': { label: 'Đạt', cls: 'sc-badge-success', icon: 'check-circle-2' },
        'Rejected': { label: 'Không đạt', cls: 'sc-badge-critical', icon: 'x-circle' },
        'Conditional': { label: 'Đạt có điều kiện', cls: 'sc-badge-warning', icon: 'alert-triangle' },
        'On Hold': { label: 'Tạm giữ', cls: 'sc-badge-neutral', icon: 'pause-circle' },
      }
      return map[d.overall_status] || { label: d.overall_status || '—', cls: 'sc-badge-neutral', icon: 'circle' }
    },
    tiles: [
      { icon: 'boxes', label: 'SL nhận', value: (d) => d.received_qty, fmt: 'number' },
      { icon: 'list', label: 'Số tiêu chí', value: (d) => (d.readings || []).length, fmt: 'number' },
      { icon: 'x-octagon', label: 'Tiêu chí không đạt',
        value: (d) => (d.readings || []).filter(r => r.status === 'Rejected').length, fmt: 'number',
        accent: (d) => (d.readings || []).filter(r => r.status === 'Rejected').length ? 'critical' : 'default' },
    ],
    sections: [
      { title: 'Thông tin kiểm', icon: 'info', fields: [
        { label: 'Phiếu nhập', value: (d) => d.purchase_receipt,
          link: (d) => d.purchase_receipt ? `/doc/SC Purchase Receipt/${d.purchase_receipt}` : null },
        { label: 'Vật tư', value: (d) => d.item,
          link: (d) => d.item ? `/doc/SC Item/${d.item}` : null },
        { label: 'Lô', value: (d) => d.batch },
        { label: 'Người kiểm', value: (d) => d.inspected_by },
        { label: 'Hành động', value: (d) => d.action_taken },
        { label: 'Lý do không đạt', value: (d) => d.failure_reason, pre: true },
        { label: 'Ghi chú KCS', value: (d) => d.remarks, pre: true },
      ]},
    ],
    items: {
      field: 'readings',
      label: 'Tiêu chí kiểm tra',
      icon: 'list-checks',
      columns: [
        { label: 'Tiêu chí', accessor: 'specification', max: true },
        { label: 'Giá trị đo', accessor: 'value' },
        { label: 'Kết quả', accessor: 'status', align: 'center' },
        { label: 'Tới hạn', accessor: 'is_critical', align: 'center', fmt: 'check' },
        { label: 'Ghi chú', accessor: 'remarks' },
      ],
    },
  },
}
