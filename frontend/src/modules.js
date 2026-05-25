// 11 modules + DocType registry với column/field schema riêng

export const MODULES = [
  { id: 'm0',  code: 'M0',  name: 'Dữ liệu nền',          icon: 'database',         route: '/m0',  group: 'Thiết lập' },
  { id: 'm1',  code: 'M1',  name: 'Hợp đồng',             icon: 'file-text',        route: '/m1',  group: 'Chiến lược' },
  { id: 'm2',  code: 'M2',  name: 'Kế hoạch & Mua',       icon: 'shopping-cart',    route: '/m2',  group: 'Chiến lược' },
  { id: 'm3',  code: 'M3',  name: 'Tiếp nhận',            icon: 'truck',            route: '/m3',  group: 'Vận hành' },
  { id: 'm4',  code: 'M4',  name: 'Quản lý kho',          icon: 'warehouse',        route: '/m4',  group: 'Vận hành' },
  { id: 'm5',  code: 'M5',  name: 'Quản lý lô vật tư',    icon: 'layers',           route: '/m5',  group: 'Vận hành' },
  { id: 'm6',  code: 'M6',  name: 'Chuyển kho',           icon: 'arrow-left-right', route: '/m6',  group: 'Vận hành' },
  { id: 'm7',  code: 'M7',  name: 'Cấp phát',             icon: 'syringe',          route: '/m7',  group: 'Vận hành' },
  { id: 'm8',  code: 'M8',  name: 'Kế toán',              icon: 'wallet',           route: '/m8',  group: 'Tài chính' },
  { id: 'm9',  code: 'M9',  name: 'Kiểm kê',              icon: 'clipboard-check',  route: '/m9',  group: 'Chất lượng' },
  { id: 'm10', code: 'M10', name: 'Truy xuất & Thu hồi',  icon: 'file-search',      route: '/m10', group: 'Chất lượng' },
  { id: 'm11', code: 'M11', name: 'Dashboard & Cảnh báo', icon: 'bar-chart',        route: '/m11', group: 'Báo cáo' },
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
  'Partially Received': 'sc-badge-warning', Received: 'sc-badge-success',
  'Material Receipt': 'sc-badge-success', 'Material Issue': 'sc-badge-warning',
  'Material Transfer': 'sc-badge-info',
  Pass: 'sc-badge-success', Fail: 'sc-badge-critical', 'Partial Pass': 'sc-badge-warning',
  Conditional: 'sc-badge-warning',
  Open: 'sc-badge-warning', 'On Hold': 'sc-badge-warning',
  High: 'sc-badge-critical', Medium: 'sc-badge-warning', Low: 'sc-badge-info',
}

// Status / option enum → Vietnamese label mapping. Backend stores English keys;
// frontend displays Vietnamese. Used by DataTable badge column và DocView status.
export const STATUS_LABEL = {
  // Docstatus / workflow
  Draft: 'Nháp', Pending: 'Chờ duyệt', Submitted: 'Đã gửi',
  Approved: 'Đã duyệt', Rejected: 'Từ chối', Cancelled: 'Đã huỷ',
  Active: 'Hiệu lực', Expired: 'Hết hạn', Terminated: 'Kết thúc',
  Issued: 'Đã phát hành', 'In Progress': 'Đang xử lý',
  Completed: 'Hoàn tất', Resolved: 'Đã xử lý',
  Investigating: 'Đang điều tra', Closed: 'Đã đóng',
  Paid: 'Đã thanh toán', Unpaid: 'Chưa thanh toán',
  // QC outcomes
  Accepted: 'Đạt', Pass: 'Đạt', Fail: 'Không đạt',
  'Partial Pass': 'Đạt một phần', Conditional: 'Có điều kiện',
  // Severity
  Critical: 'Nghiêm trọng', High: 'Cao', Medium: 'Trung bình',
  Low: 'Thấp', Warning: 'Cảnh báo', Info: 'Thông tin',
  // PO flow
  'Sent to Supplier': 'Đã gửi NCC',
  'Partially Received': 'Nhận một phần', Received: 'Đã nhận',
  // Stock Entry types
  'Material Receipt': 'Nhập kho', 'Material Issue': 'Xuất kho',
  'Material Transfer': 'Chuyển kho', Manufacture: 'Sản xuất', Repack: 'Đóng gói lại',
  // MR request types
  Purchase: 'Mua', 'Material Transfer Request': 'Yêu cầu chuyển kho',
  // Alert action results
  Open: 'Đang mở', Acknowledged: 'Đã ghi nhận', 'Acted Upon': 'Đã xử lý',
  Dismissed: 'Bỏ qua', Escalated: 'Đã đẩy lên',
  // Warehouse types
  Main: 'Kho chính', Department: 'Kho khoa', Quarantine: 'Cách ly',
  Damaged: 'Hỏng', Sample: 'Mẫu',
  // Recall severity
  'Class I (Critical)': 'Mức I (Nghiêm trọng)',
  'Class II (High)': 'Mức II (Cao)',
  'Class III (Low)': 'Mức III (Thấp)',
  Voluntary: 'Tự nguyện', Mandatory: 'Bắt buộc', Precautionary: 'Phòng ngừa',
  // Count types
  Full: 'Toàn bộ', Cycle: 'Định kỳ', Adhoc: 'Đột xuất',
  // Investigation types
  'Stock Loss': 'Mất hàng', Discrepancy: 'Chênh lệch',
  Fraud: 'Gian lận', 'System Error': 'Lỗi hệ thống',
  // Payment methods
  'Bank Transfer': 'Chuyển khoản', Cash: 'Tiền mặt', Cheque: 'Séc',
  // Variance reason
  'Counting Error': 'Lỗi đếm', Damage: 'Hư hỏng',
  Theft: 'Mất cắp', Expiry: 'Hết hạn',
  // Alert frequency
  Realtime: 'Thời gian thực', Hourly: 'Theo giờ',
  Daily: 'Hàng ngày', Weekly: 'Hàng tuần',
  // Days of week
  Mon: 'T2', Tue: 'T3', Wed: 'T4', Thu: 'T5',
  Fri: 'T6', Sat: 'T7', Sun: 'CN',
  // Department types
  Clinical: 'Lâm sàng', Surgical: 'Ngoại khoa', Lab: 'Xét nghiệm',
  Pharmacy: 'Nhà thuốc', Admin: 'Hành chính', Other: 'Khác',
}

// Doctypes có docstatus / submittable workflow.
// "Gửi duyệt" button chỉ hiển thị cho các doctype trong set này (BUG-003).
export const SUBMITTABLE_DOCTYPES = new Set([
  'Framework Contract', 'Release Order', 'Procurement Plan',
  'SC Material Request', 'SC Purchase Order', 'SC Purchase Receipt',
  'SC Quality Inspection', 'SC Stock Entry',
  'SC Transfer Request', 'SC Dispensing Request', 'SC Patient Dispensing',
  'SC Inventory Count Sheet', 'SC Stock Reconciliation',
  'SC Recall Notice', 'SC Investigation Report',
  'SC Purchase Invoice', 'SC Payment Entry',
])

export function isSubmittable(doctype) {
  return SUBMITTABLE_DOCTYPES.has(doctype)
}

export function statusLabel(value) {
  if (value == null || value === '') return ''
  return STATUS_LABEL[value] ?? value
}

// DocType schema — fields cho List + Form + actions
export const DT = {
  // === M0 Master Data ===
  'SC Item': {
    module: 'm0', label: 'Vật tư', icon: 'pill',
    listColumns: [
      { key: 'name', label: 'Mã VT', mono: true },
      { key: 'item_name', label: 'Tên' },
      { key: 'item_group', label: 'Nhóm' },
      { key: 'uom', label: 'ĐVT' },
      { key: 'is_stock_item', label: 'Tồn kho', type: 'check' },
      { key: 'has_batch_no', label: 'Có lô', type: 'check' },
      { key: 'safety_stock', label: 'Tồn an toàn', type: 'int', align: 'right' },
      { key: 'disabled', label: 'Vô hiệu', type: 'check' },
    ],
    listFields: ['name', 'item_code', 'item_name', 'item_group', 'uom',
                  'is_stock_item', 'has_batch_no', 'safety_stock', 'reorder_level', 'disabled'],
  },
  'SC Item Group': {
    module: 'm0', label: 'Nhóm vật tư', icon: 'folder',
    listColumns: [
      { key: 'name', label: 'Tên nhóm' },
      { key: 'parent_group', label: 'Nhóm cha' },
      { key: 'is_group', label: 'Là nhóm', type: 'check' },
    ],
    listFields: ['name', 'group_name', 'parent_group', 'is_group'],
  },
  'SC UOM': {
    module: 'm0', label: 'Đơn vị tính', icon: 'ruler',
    listColumns: [
      { key: 'name', label: 'Mã ĐVT' },
      { key: 'uom_name', label: 'Tên ĐVT' },
      { key: 'must_be_whole_number', label: 'Số nguyên', type: 'check' },
    ],
    listFields: ['name', 'uom_name', 'must_be_whole_number'],
  },
  'SC Supplier': {
    module: 'm0', label: 'Nhà cung cấp', icon: 'building-2',
    listColumns: [
      { key: 'name', label: 'Mã NCC', mono: true },
      { key: 'supplier_name', label: 'Tên NCC' },
      { key: 'tax_id', label: 'MST', mono: true },
      { key: 'email_id', label: 'Email' },
      { key: 'mobile_no', label: 'Điện thoại' },
      { key: 'disabled', label: 'Vô hiệu', type: 'check' },
    ],
    listFields: ['name', 'supplier_name', 'tax_id', 'email_id', 'mobile_no', 'disabled'],
  },
  'SC Warehouse': {
    module: 'm0', label: 'Kho', icon: 'warehouse',
    listColumns: [
      { key: 'name', label: 'Tên kho' },
      { key: 'warehouse_type', label: 'Loại' },
      { key: 'parent_warehouse', label: 'Kho cha' },
      { key: 'is_group', label: 'Nhóm', type: 'check' },
      { key: 'disabled', label: 'Vô hiệu', type: 'check' },
    ],
    listFields: ['name', 'warehouse_name', 'warehouse_type', 'parent_warehouse',
                  'is_group', 'disabled'],
  },
  'Bin Location': {
    module: 'm0', extraModules: ['m4'], label: 'Vị trí lưu trữ', icon: 'map-pin',
    listColumns: [
      { key: 'name', label: 'Mã vị trí', mono: true },
      { key: 'warehouse', label: 'Kho' },
      { key: 'bin_code', label: 'Code', mono: true },
      { key: 'barcode', label: 'Barcode', mono: true },
      { key: 'zone', label: 'Khu' },
      { key: 'aisle', label: 'Hàng' },
      { key: 'rack', label: 'Kệ' },
      { key: 'shelf', label: 'Tầng' },
      { key: 'level', label: 'Mức' },
      { key: 'status', label: 'Trạng thái' },
      { key: 'is_quarantine', label: 'Cách ly', type: 'check' },
      { key: 'enabled', label: 'Hiệu lực', type: 'check' },
    ],
    listFields: ['name', 'warehouse', 'bin_code', 'barcode', 'zone', 'aisle', 'rack',
                  'shelf', 'level', 'status', 'occupancy_pct',
                  'is_quarantine', 'temperature_controlled', 'enabled'],
    defaultOrderBy: 'warehouse asc, bin_code asc',
  },
  'SC Department': {
    module: 'm0', label: 'Khoa phòng', icon: 'building',
    listColumns: [
      { key: 'name', label: 'Tên khoa' },
      { key: 'department_code', label: 'Mã', mono: true },
      { key: 'department_type', label: 'Loại' },
      { key: 'disabled', label: 'Vô hiệu', type: 'check' },
    ],
    listFields: ['name', 'department_name', 'department_code', 'department_type', 'disabled'],
  },
  'SC Patient': {
    module: 'm0', label: 'Bệnh nhân', icon: 'heart-pulse',
    listColumns: [
      { key: 'name', label: 'Mã BN', mono: true },
      { key: 'patient_name', label: 'Họ tên' },
      { key: 'gender', label: 'Giới' },
      { key: 'bhyt_card_no', label: 'Thẻ BHYT', mono: true },
      { key: 'bhyt_type', label: 'Loại BHYT' },
      { key: 'current_department', label: 'Khoa' },
    ],
    listFields: ['name', 'patient_name', 'gender', 'dob', 'bhyt_card_no',
                  'bhyt_type', 'bhyt_payment_rate', 'current_department', 'disabled'],
  },
  'SC BHYT Code Config': {
    module: 'm0', label: 'Mã BHYT', icon: 'tag',
    listColumns: [
      { key: 'name', label: 'Mã', mono: true },
      { key: 'bhyt_code', label: 'BHYT Code' },
      { key: 'bhyt_name', label: 'Tên BHYT' },
      { key: 'bhyt_group', label: 'Nhóm' },
      { key: 'payment_rate', label: 'Tỷ lệ %', type: 'int', align: 'right' },
      { key: 'ceiling_price', label: 'Giá trần', type: 'currency', align: 'right' },
      { key: 'is_active', label: 'Hiệu lực', type: 'check' },
    ],
    listFields: ['name', 'bhyt_code', 'bhyt_name', 'bhyt_group', 'payment_rate',
                  'ceiling_price', 'item', 'item_group', 'is_active'],
  },
  'SC GL Account': {
    module: 'm0', label: 'TK kế toán', icon: 'book',
    listColumns: [
      { key: 'name', label: 'TK', mono: true },
      { key: 'account_code', label: 'Số TK' },
      { key: 'account_name', label: 'Tên' },
      { key: 'account_type', label: 'Loại' },
      { key: 'is_group', label: 'Nhóm', type: 'check' },
    ],
    listFields: ['name', 'account_code', 'account_name', 'account_type', 'is_group', 'disabled'],
  },

  // === M1 ===
  'Framework Contract': {
    module: 'm1', label: 'Hợp đồng khung', icon: 'file-text',
    listColumns: [
      { key: 'name', label: 'Mã HĐ', mono: true },
      { key: 'contract_number', label: 'Số HĐ' },
      { key: 'supplier_name', label: 'NCC' },
      { key: 'valid_from', label: 'Từ', type: 'date' },
      { key: 'valid_to', label: 'Đến', type: 'date' },
      { key: 'total_value', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'remaining_value', label: 'Còn lại', type: 'currency', align: 'right' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    // Gộp 2 cột Từ/Đến thành 1 dải filter (period overlap) trong panel "Lọc cột"
    dateRangePairs: [
      { start: 'valid_from', end: 'valid_to', label: 'Hiệu lực HĐ' },
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
    module: 'm2', label: 'Yêu cầu mua', icon: 'shopping-cart',
    listColumns: [
      { key: 'name', label: 'Mã MR', mono: true },
      { key: 'transaction_date', label: 'Ngày', type: 'date' },
      { key: 'request_type', label: 'Loại' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'schedule_date', label: 'Ngày cần', type: 'date' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'transaction_date', 'request_type', 'warehouse', 'schedule_date', 'status', 'docstatus'],
  },
  'SC Purchase Order': {
    module: 'm2', label: 'Đơn mua hàng', icon: 'clipboard-list',
    listColumns: [
      { key: 'name', label: 'Mã PO', mono: true },
      { key: 'transaction_date', label: 'Ngày', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'schedule_date', label: 'Ngày giao', type: 'date' },
      { key: 'grand_total', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'transaction_date', 'supplier', 'schedule_date', 'grand_total', 'status', 'docstatus'],
    actions: ['submit', 'cancel', 'send_to_supplier'],
  },

  // === M3 ===
  'SC Purchase Receipt': {
    module: 'm3', label: 'Phiếu nhập', icon: 'package-check',
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
    module: 'm3', label: 'Kiểm tra QC', icon: 'flask-conical',
    listColumns: [
      { key: 'name', label: 'Mã QI', mono: true },
      { key: 'inspection_date', label: 'Ngày', type: 'date' },
      { key: 'purchase_receipt', label: 'PR', mono: true },
      { key: 'item', label: 'Vật tư' },
      { key: 'supplier', label: 'NCC' },
      { key: 'overall_status', label: 'Kết quả', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'inspection_date', 'purchase_receipt', 'item', 'supplier', 'overall_status', 'docstatus'],
  },

  // === M4 ===
  'SC Warehouse': {
    module: 'm4', label: 'Kho', icon: 'warehouse',
    listColumns: [
      { key: 'name', label: 'Tên kho' },
      { key: 'warehouse_type', label: 'Loại' },
      { key: 'is_group', label: 'Nhóm', type: 'check' },
      { key: 'disabled', label: 'Vô hiệu', type: 'check' },
    ],
    listFields: ['name', 'warehouse_name', 'warehouse_type', 'is_group', 'disabled'],
  },
  'SC Stock Ledger Entry': {
    module: 'm4', label: 'Sổ kho (SLE)', icon: 'list',
    listColumns: [
      { key: 'name', label: 'SLE', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'item', label: 'Vật tư' },
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
    module: 'm4', label: 'Lô', icon: 'layers',
    listColumns: [
      { key: 'name', label: 'Mã lô', mono: true },
      { key: 'barcode', label: 'Barcode', mono: true },
      { key: 'item', label: 'Vật tư' },
      { key: 'supplier_batch_no', label: 'Số lô NCC' },
      { key: 'manufacturing_date', label: 'SX', type: 'date' },
      { key: 'expiry_date', label: 'HD', type: 'date' },
      { key: 'qc_status', label: 'QC', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'blocked', label: 'Khoá', type: 'check' },
    ],
    dateRangePairs: [
      { start: 'manufacturing_date', end: 'expiry_date', label: 'Vòng đời lô (SX → HD)' },
    ],
    listFields: ['name', 'barcode', 'item', 'supplier_batch_no', 'manufacturing_date', 'expiry_date',
                  'qc_status', 'blocked', 'supplier'],
  },

  // === M6 ===
  'SC Transfer Request': {
    module: 'm6', label: 'Yêu cầu chuyển kho', icon: 'arrow-left-right',
    listColumns: [
      { key: 'name', label: 'Mã TR', mono: true },
      { key: 'request_date', label: 'Ngày', type: 'date' },
      { key: 'from_warehouse', label: 'Từ' },
      { key: 'to_warehouse', label: 'Đến' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'request_date', 'from_warehouse', 'to_warehouse', 'status', 'docstatus'],
  },
  'SC Stock Entry': {
    module: 'm6', label: 'Phiếu chuyển kho', icon: 'arrow-left-right',
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
    module: 'm7', label: 'Yêu cầu cấp phát', icon: 'clipboard-plus',
    listColumns: [
      { key: 'name', label: 'Mã DR', mono: true },
      { key: 'request_date', label: 'Ngày', type: 'date' },
      { key: 'department', label: 'Khoa' },
      { key: 'from_warehouse', label: 'Kho' },
      { key: 'purpose', label: 'Mục đích' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'request_date', 'department', 'from_warehouse', 'purpose', 'status', 'docstatus'],
  },
  'SC Patient Dispensing': {
    module: 'm7', label: 'Cấp phát BN', icon: 'syringe',
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
                  'total_cost', 'patient_pays', 'docstatus'],
  },

  // === M8 ===
  'SC Purchase Invoice': {
    module: 'm8', label: 'Hóa đơn mua', icon: 'receipt',
    listColumns: [
      { key: 'name', label: 'Mã PI', mono: true },
      { key: 'invoice_date', label: 'Ngày HD', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'purchase_receipt', label: 'PR', mono: true },
      { key: 'grand_total', label: 'Tổng', type: 'currency', align: 'right' },
      { key: 'outstanding_amount', label: 'Còn lại', type: 'currency', align: 'right' },
      { key: 'three_way_match_status', label: '3-way', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'payment_hold', label: 'Khoá TT', type: 'check' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'invoice_date', 'supplier', 'purchase_receipt', 'grand_total',
                  'outstanding_amount', 'three_way_match_status', 'payment_hold',
                  'status', 'docstatus'],
  },
  'SC Payment Entry': {
    module: 'm8', label: 'Phiếu thanh toán', icon: 'credit-card',
    listColumns: [
      { key: 'name', label: 'Mã PE', mono: true },
      { key: 'payment_date', label: 'Ngày', type: 'date' },
      { key: 'supplier', label: 'NCC' },
      { key: 'amount', label: 'Số tiền', type: 'currency', align: 'right' },
      { key: 'payment_method', label: 'Phương thức' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'payment_date', 'supplier', 'amount', 'payment_method', 'status', 'docstatus'],
  },
  'SC GL Entry': {
    module: 'm8', label: 'Bút toán GL', icon: 'book',
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
    module: 'm9', label: 'Phiếu kiểm kê', icon: 'clipboard-list',
    listColumns: [
      { key: 'name', label: 'ICS', mono: true },
      { key: 'count_date', label: 'Ngày', type: 'date' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'count_scope', label: 'Phạm vi' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'count_date', 'warehouse', 'count_scope', 'status', 'docstatus'],
  },
  'SC Stock Reconciliation': {
    module: 'm9', label: 'Đối soát kho', icon: 'git-compare',
    listColumns: [
      { key: 'name', label: 'SR', mono: true },
      { key: 'posting_date', label: 'Ngày', type: 'date' },
      { key: 'warehouse', label: 'Kho' },
      { key: 'total_difference_qty', label: 'Δ Qty', type: 'int', align: 'right' },
      { key: 'total_difference_value', label: 'Δ Giá trị', type: 'currency', align: 'right' },
      { key: 'requires_investigation', label: 'Điều tra', type: 'check' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'posting_date', 'warehouse', 'total_difference_qty',
                  'total_difference_value', 'requires_investigation', 'status', 'docstatus'],
  },

  // === M10 ===
  'SC Recall Notice': {
    module: 'm10', label: 'Thu hồi', icon: 'siren',
    listColumns: [
      { key: 'name', label: 'RCL', mono: true },
      { key: 'recall_date', label: 'Ngày', type: 'date' },
      { key: 'item', label: 'Vật tư' },
      { key: 'batch_no', label: 'Lô', mono: true },
      { key: 'severity', label: 'Mức độ', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'recall_date', 'item', 'batch_no', 'severity', 'status',
                  'total_affected_qty', 'recovered_qty', 'docstatus'],
  },
  'SC Investigation Report': {
    module: 'm10', label: 'Điều tra', icon: 'file-search',
    listColumns: [
      { key: 'name', label: 'INV', mono: true },
      { key: 'investigation_date', label: 'Ngày', type: 'date' },
      { key: 'investigation_type', label: 'Loại' },
      { key: 'item', label: 'Vật tư' },
      { key: 'variance_qty', label: 'Δ Qty', type: 'int', align: 'right' },
      { key: 'status', label: 'Trạng thái', type: 'badge', badgeMap: STATUS_BADGE },
    ],
    listFields: ['name', 'investigation_date', 'investigation_type', 'item',
                  'variance_qty', 'variance_value', 'status', 'docstatus'],
  },

  // === M11 ===
  'SC Alert': {
    module: 'm11', label: 'Cảnh báo', icon: 'bell',
    listColumns: [
      { key: 'alert_date', label: 'Thời điểm', type: 'datetime' },
      { key: 'severity', label: 'Mức', type: 'badge', badgeMap: STATUS_BADGE },
      { key: 'alert_type', label: 'Loại' },
      { key: 'title', label: 'Tiêu đề' },
      { key: 'resolved', label: 'Xử lý', type: 'check' },
      { key: 'escalated', label: 'Đẩy lên', type: 'check' },
    ],
    listFields: ['name', 'alert_date', 'severity', 'alert_type', 'title',
                  'resolved', 'escalated', 'assigned_to', 'reference_doctype', 'reference_name'],
  },
  'SC Alert Rule': {
    module: 'm11', label: 'Cấu hình rule', icon: 'sliders',
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

// DocType list per module — 1 doctype có thể ở nhiều module qua extraModules
export const MODULE_DOCTYPES = (() => {
  const m = {}
  Object.entries(DT).forEach(([dt, cfg]) => {
    const mods = [cfg.module, ...(cfg.extraModules || [])]
    for (const mod of mods) {
      m[mod] = m[mod] || []
      m[mod].push({ dt, label: cfg.label, icon: cfg.icon })
    }
  })
  // M5 Quản lý lô vật tư: SC Batch sắp xếp theo HSD (FEFO) làm view chính
  if (!m['m5']) m['m5'] = []
  m['m5'].push(
    { dt: 'SC Batch', label: 'Danh sách lô vật tư', icon: 'clock',
      defaultOrderBy: 'expiry_date asc',
      defaultFilters: [['blocked', '=', 0]] },
  )
  return m
})()
