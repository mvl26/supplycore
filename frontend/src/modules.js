// 11 modules + DocType registry với column/field schema riêng

export const MODULES = [
  { id: 'm1',  code: 'M1',  name: 'Hợp đồng',            icon: '📑', route: '/m1',  group: 'Strategic' },
  { id: 'm2',  code: 'M2',  name: 'Kế hoạch & Mua',       icon: '🛒', route: '/m2',  group: 'Strategic' },
  { id: 'm3',  code: 'M3',  name: 'Tiếp nhận',            icon: '📦', route: '/m3',  group: 'Operations' },
  { id: 'm4',  code: 'M4',  name: 'Quản lý kho',          icon: '🏬', route: '/m4',  group: 'Operations' },
  { id: 'm5',  code: 'M5',  name: 'FEFO',                 icon: '⏱️', route: '/m5',  group: 'Operations' },
  { id: 'm6',  code: 'M6',  name: 'Chuyển kho',           icon: '🔁', route: '/m6',  group: 'Operations' },
  { id: 'm7',  code: 'M7',  name: 'Cấp phát',             icon: '💉', route: '/m7',  group: 'Operations' },
  { id: 'm8',  code: 'M8',  name: 'Kế toán',              icon: '💰', route: '/m8',  group: 'Finance' },
  { id: 'm9',  code: 'M9',  name: 'Kiểm kê',              icon: '📋', route: '/m9',  group: 'Quality' },
  { id: 'm10', code: 'M10', name: 'Truy xuất & Recall',   icon: '🔍', route: '/m10', group: 'Quality' },
  { id: 'm11', code: 'M11', name: 'Dashboard & Alert',    icon: '📊', route: '/m11', group: 'Insights' },
]

// Status → badge class mapping
const STATUS_BADGE = {
  Draft: 'sc-badge-neutral', Pending: 'sc-badge-warning',
  Submitted: 'sc-badge-info', Approved: 'sc-badge-success',
  Rejected: 'sc-badge-critical', Cancelled: 'sc-badge-neutral',
  Active: 'sc-badge-success', Expired: 'sc-badge-warning',
  Terminated: 'sc-badge-critical',
  Issued: 'sc-badge-info', 'In Progress': 'sc-badge-warning',
  Completed: 'sc-badge-success', Resolved: 'sc-badge-success',
  Investigating: 'sc-badge-warning', Closed: 'sc-badge-neutral',
  Paid: 'sc-badge-success', Unpaid: 'sc-badge-warning',
  Accepted: 'sc-badge-success',
  Critical: 'sc-badge-critical', Warning: 'sc-badge-warning', Info: 'sc-badge-info',
  Pending: 'sc-badge-warning', 'Sent to Supplier': 'sc-badge-info',
  'Partially Received': 'sc-badge-warning',
  'Material Receipt': 'sc-badge-success', 'Material Issue': 'sc-badge-warning',
  'Material Transfer': 'sc-badge-info',
}

// DocType schema — fields cho List + Form + actions
export const DT = {
  // === M1 ===
  'Framework Contract': {
    module: 'm1', label: 'Hợp đồng khung', icon: '📑',
    listColumns: [
      { key: 'name', label: 'Mã HĐ', mono: true },
      { key: 'contract_number', label: 'Số HĐ' },
      { key: 'supplier_name', label: 'NCC' },
      { key: 'valid_from', label: 'Từ', type: 'date' },
      { key: 'valid_to', label: 'Đến', type: 'date' },
      { key: 'total_value', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'remaining_value', label: 'Còn lại', type: 'currency', align: 'right' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'contract_number', 'supplier_name', 'valid_from', 'valid_to',
                  'total_value', 'remaining_value', 'status', 'docstatus'],
    formSections: [
      { title: 'Thông tin chung', fields: [
        ['supplier', 'Link', { required: true, link_to: 'SC Supplier' }],
        ['contract_number', 'Data', { required: true }],
        ['contract_date', 'Date', { required: true }],
        ['valid_from', 'Date', { required: true }],
        ['valid_to', 'Date', { required: true }],
      ]},
      { title: 'Giá trị', fields: [
        ['total_value', 'Currency', { required: true }],
        ['remaining_value', 'Currency', { readonly: true }],
        ['payment_terms', 'Data'],
      ]},
    ],
    actions: ['submit_for_review', 'manager_approve', 'executive_approve', 'reject'],
  },

  // === M2 ===
  'SC Material Request': {
    module: 'm2', label: 'Yêu cầu mua', icon: '🛒',
    listColumns: [
      { key: 'name', label: 'Mã MR', mono: true },
      { key: 'transaction_date', label: 'Ngày', type: 'date' },
      { key: 'request_type', label: 'Loại' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'schedule_date', label: 'Ngày cần', type: 'date' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'transaction_date', 'request_type', 'warehouse', 'schedule_date', 'status', 'docstatus'],
  },
  'SC Purchase Order': {
    module: 'm2', label: 'Đơn mua hàng', icon: '🛒',
    listColumns: [
      { key: 'name', label: 'Mã PO', mono: true },
      { key: 'transaction_date', label: 'Ngày', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'schedule_date', label: 'Ngày giao', type: 'date' },
      { key: 'total_value', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'transaction_date', 'supplier', 'schedule_date', 'total_value', 'status', 'docstatus'],
    actions: ['submit', 'cancel', 'send_to_supplier'],
  },

  // === M3 ===
  'SC Purchase Receipt': {
    module: 'm3', label: 'Phiếu nhập', icon: '📦',
    listColumns: [
      { key: 'name', label: 'Mã PR', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'purchase_order', label: 'PO', mono: true },
      { key: 'is_return', label: 'Trả', type: 'check' },
      { key: 'qc_status', label: 'QC', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'posting_date', 'supplier', 'purchase_order', 'is_return', 'qc_status', 'docstatus'],
    actions: ['submit', 'cancel', 'make_debit_note', 'make_credit_note'],
  },
  'SC Quality Inspection': {
    module: 'm3', label: 'Kiểm tra QC', icon: '🔬',
    listColumns: [
      { key: 'name', label: 'Mã QI', mono: true },
      { key: 'inspection_date', label: 'Ngày', type: 'date' },
      { key: 'purchase_receipt', label: 'PR', mono: true },
      { key: 'item', label: 'Item' },
      { key: 'overall_status', label: 'Kết quả', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'inspection_date', 'purchase_receipt', 'item', 'overall_status', 'docstatus'],
  },

  // === M4 ===
  'SC Warehouse': {
    module: 'm4', label: 'Kho', icon: '🏬',
    listColumns: [
      { key: 'name', label: 'Tên kho' },
      { key: 'warehouse_type', label: 'Loại' },
      { key: 'is_group', label: 'Nhóm', type: 'check' },
      { key: 'disabled', label: 'Disabled', type: 'check' },
    ],
    listFields: ['name', 'warehouse_name', 'warehouse_type', 'is_group', 'disabled'],
  },
  'SC Stock Ledger Entry': {
    module: 'm4', label: 'Sổ kho (SLE)', icon: '📊',
    listColumns: [
      { key: 'name', label: 'SLE', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'item', label: 'Item' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'batch', label: 'Lô', mono: true },
      { key: 'qty_change', label: 'Δ Qty', type: 'int', align: 'right' },
      { key: 'balance_qty', label: 'Tồn', type: 'int', align: 'right' },
      { key: 'voucher_type', label: 'CT' },
      { key: 'voucher_no', label: 'Số CT', mono: true },
    ],
    listFields: ['name', 'posting_date', 'item', 'warehouse', 'batch', 'qty_change',
                  'balance_qty', 'voucher_type', 'voucher_no', 'is_cancelled'],
  },
  'SC Batch': {
    module: 'm4', label: 'Lô', icon: '🏷️',
    listColumns: [
      { key: 'name', label: 'Mã lô', mono: true },
      { key: 'item', label: 'Item' },
      { key: 'supplier_batch_no', label: 'Số lô NCC' },
      { key: 'manufacturing_date', label: 'SX', type: 'date' },
      { key: 'expiry_date', label: 'HD', type: 'date' },
      { key: 'qc_status', label: 'QC', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'blocked', label: 'Blocked', type: 'check' },
    ],
    listFields: ['name', 'item', 'supplier_batch_no', 'manufacturing_date', 'expiry_date',
                  'qc_status', 'blocked', 'supplier'],
  },

  // === M6 ===
  'SC Transfer Request': {
    module: 'm6', label: 'Yêu cầu chuyển kho', icon: '🔁',
    listColumns: [
      { key: 'name', label: 'Mã TR', mono: true },
      { key: 'request_date', label: 'Ngày', type: 'date' },
      { key: 'from_warehouse', label: 'Từ' },
      { key: 'to_warehouse', label: 'Đến' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'request_date', 'from_warehouse', 'to_warehouse', 'status', 'docstatus'],
  },
  'SC Stock Entry': {
    module: 'm6', label: 'Phiếu chuyển kho', icon: '🔁',
    listColumns: [
      { key: 'name', label: 'Mã SE', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'entry_type', label: 'Loại', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'from_warehouse', label: 'Từ' },
      { key: 'to_warehouse', label: 'Đến' },
      { key: 'total_qty', label: 'Tổng SL', type: 'int', align: 'right' },
    ],
    listFields: ['name', 'posting_date', 'entry_type', 'from_warehouse', 'to_warehouse',
                  'total_qty', 'total_value', 'docstatus'],
  },

  // === M7 ===
  'SC Dispensing Request': {
    module: 'm7', label: 'Yêu cầu cấp phát', icon: '💊',
    listColumns: [
      { key: 'name', label: 'Mã DR', mono: true },
      { key: 'request_date', label: 'Ngày', type: 'date' },
      { key: 'department', label: 'Khoa' },
      { key: 'from_warehouse', label: 'Kho' },
      { key: 'priority', label: 'Ưu tiên' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'request_date', 'department', 'from_warehouse', 'priority', 'status', 'docstatus'],
  },
  'SC Patient Dispensing': {
    module: 'm7', label: 'Cấp phát BN', icon: '💉',
    listColumns: [
      { key: 'name', label: 'Mã PD', mono: true },
      { key: 'dispensing_date', label: 'Ngày', type: 'date' },
      { key: 'patient', label: 'BN', mono: true },
      { key: 'patient_name', label: 'Tên BN' },
      { key: 'ward', label: 'Khoa' },
      { key: 'total_cost', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'patient_pays', label: 'BN trả', type: 'currency', align: 'right' },
    ],
    listFields: ['name', 'dispensing_date', 'patient', 'patient_name', 'ward',
                  'total_cost', 'patient_pays', 'bhyt_amount', 'docstatus'],
  },

  // === M8 ===
  'SC Purchase Invoice': {
    module: 'm8', label: 'Hóa đơn mua', icon: '🧾',
    listColumns: [
      { key: 'name', label: 'Mã PI', mono: true },
      { key: 'invoice_date', label: 'Ngày HD', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'purchase_receipt', label: 'PR', mono: true },
      { key: 'grand_total', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'outstanding_amount', label: 'Còn lại', type: 'currency', align: 'right' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'invoice_date', 'supplier', 'purchase_receipt', 'grand_total',
                  'outstanding_amount', 'status', 'docstatus'],
  },
  'SC Payment Entry': {
    module: 'm8', label: 'Phiếu thanh toán', icon: '💳',
    listColumns: [
      { key: 'name', label: 'Mã PE', mono: true },
      { key: 'payment_date', label: 'Ngày', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'amount', label: 'Số tiền', type: 'currency', align: 'right' },
      { key: 'payment_method', label: 'Phương thức' },
    ],
    listFields: ['name', 'payment_date', 'supplier', 'amount', 'payment_method', 'docstatus'],
  },
  'SC GL Entry': {
    module: 'm8', label: 'Bút toán GL', icon: '💰',
    listColumns: [
      { key: 'name', label: 'GL', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'account', label: 'TK' },
      { key: 'debit', label: 'Nợ', type: 'currency', align: 'right' },
      { key: 'credit', label: 'Có', type: 'currency', align: 'right' },
      { key: 'voucher_no', label: 'Chứng từ', mono: true },
    ],
    listFields: ['name', 'posting_date', 'account', 'debit', 'credit', 'voucher_no', 'voucher_type'],
  },

  // === M9 ===
  'SC Inventory Count Sheet': {
    module: 'm9', label: 'Phiếu kiểm kê', icon: '📋',
    listColumns: [
      { key: 'name', label: 'ICS', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'count_type', label: 'Loại' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'posting_date', 'warehouse', 'count_type', 'status', 'docstatus'],
  },
  'SC Stock Reconciliation': {
    module: 'm9', label: 'Đối soát kho', icon: '🔍',
    listColumns: [
      { key: 'name', label: 'SR', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'total_difference_qty', label: 'Δ Qty', type: 'int', align: 'right' },
      { key: 'total_difference_value', label: 'Δ Giá trị', type: 'currency', align: 'right' },
      { key: 'requires_investigation', label: 'Điều tra', type: 'check' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'posting_date', 'warehouse', 'total_difference_qty',
                  'total_difference_value', 'requires_investigation', 'status', 'docstatus'],
  },

  // === M10 ===
  'SC Recall Notice': {
    module: 'm10', label: 'Thu hồi', icon: '🚨',
    listColumns: [
      { key: 'name', label: 'RCL', mono: true },
      { key: 'recall_date', label: 'Ngày', type: 'date' },
      { key: 'item', label: 'Item' },
      { key: 'batch_no', label: 'Lô', mono: true },
      { key: 'severity', label: 'Mức độ', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'recall_date', 'item', 'batch_no', 'severity', 'status',
                  'total_affected_qty', 'recovered_qty', 'docstatus'],
  },
  'SC Investigation Report': {
    module: 'm10', label: 'Điều tra', icon: '🔎',
    listColumns: [
      { key: 'name', label: 'INV', mono: true },
      { key: 'investigation_date', label: 'Ngày', type: 'date' },
      { key: 'investigation_type', label: 'Loại' },
      { key: 'item', label: 'Item' },
      { key: 'variance_qty', label: 'Δ Qty', type: 'int', align: 'right' },
      { key: 'status', label: 'Status', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'investigation_date', 'investigation_type', 'item',
                  'variance_qty', 'variance_value', 'status', 'docstatus'],
  },

  // === M11 ===
  'SC Alert': {
    module: 'm11', label: 'Cảnh báo', icon: '🔔',
    listColumns: [
      { key: 'alert_date', label: 'Thời điểm', type: 'datetime' },
      { key: 'severity', label: 'Mức', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'alert_type', label: 'Loại' },
      { key: 'title', label: 'Tiêu đề' },
      { key: 'resolved', label: 'Xử lý', type: 'check' },
      { key: 'escalated', label: 'Escalate', type: 'check' },
    ],
    listFields: ['name', 'alert_date', 'severity', 'alert_type', 'title',
                  'resolved', 'escalated', 'assigned_to', 'reference_doctype', 'reference_name'],
  },
  'SC Alert Rule': {
    module: 'm11', label: 'Cấu hình rule', icon: '⚙️',
    listColumns: [
      { key: 'name', label: 'AR', mono: true },
      { key: 'title', label: 'Tiêu đề' },
      { key: 'alert_type', label: 'Loại' },
      { key: 'severity', label: 'Mức', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'frequency', label: 'Tần suất' },
      { key: 'enabled', label: 'Bật', type: 'check' },
    ],
    listFields: ['name', 'title', 'alert_type', 'severity', 'frequency', 'enabled',
                  'channel_email', 'channel_inapp', 'channel_sms'],
  },
}

// DocType list per module
export const MODULE_DOCTYPES = (() => {
  const m = {}
  Object.entries(DT).forEach(([dt, cfg]) => {
    m[cfg.module] = m[cfg.module] || []
    m[cfg.module].push({ dt, label: cfg.label, icon: cfg.icon })
  })
  return m
})()
