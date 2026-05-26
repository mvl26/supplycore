// Per-DocType custom actions (whitelisted methods từ Python backend)
// Method names verified từ doctype.py thực tế (UC-01..34)

export const ACTIONS = {
  // === M1 Framework Contract — UC-01..04 ===
  'Framework Contract': [
    { method: 'submit_for_review', label: 'Gửi duyệt',          icon: 'upload', variant: 'primary',
      when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage || d.approval_stage === 'Rejected') },
    { method: 'approve_as_manager', label: 'Manager duyệt',     icon: 'check',  variant: 'success',
      when: (d) => d.approval_stage === 'Manager Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'approve_as_executive', label: 'Executive duyệt', icon: 'check-circle', variant: 'success',
      when: (d) => d.approval_stage === 'Executive Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'reject_approval',   label: 'Từ chối',            icon: 'x',  variant: 'danger',
      when: (d) => ['Manager Review', 'Executive Review'].includes(d.approval_stage),
      args: [{ key: 'reason', label: 'Lý do từ chối', type: 'textarea', required: true }] },
    { method: 'make_material_request', label: 'Tạo Yêu cầu mua hàng', icon: 'file-text', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Active',
      navigateOnSuccess: { type: 'doc', dt: 'SC Material Request', from: 'material_request' } },
    { method: 'request_renewal',   label: 'Gia hạn HĐ',         icon: 'rotate-cw', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.status === 'Active',
      args: [
        { key: 'new_valid_to', label: 'Hết hạn mới', type: 'date', required: true },
        { key: 'reason', label: 'Lý do', type: 'textarea', required: true },
      ]},
  ],

  // === M2 Purchase Order — UC-08 (workflow đơn giản hoá) ===
  'SC Purchase Order': [
    { method: 'make_purchase_receipt', label: 'Tạo Phiếu nhập (PR)', icon: 'package', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status !== 'Received' && d.status !== 'Cancelled',
      navigateOnSuccess: { type: 'doc', dt: 'SC Purchase Receipt', from: 'purchase_receipt' } },
    { method: 'submit_for_review',   label: 'Gửi duyệt (Optional)', icon: 'upload', variant: 'secondary',
      when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage) },
    { method: 'approve_as_manager',  label: 'Manager duyệt',     icon: 'check',  variant: 'success',
      when: (d) => d.docstatus === 0 && d.approval_stage === 'Manager Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'approve_as_executive', label: 'Executive duyệt',  icon: 'check-circle', variant: 'success',
      when: (d) => d.docstatus === 0 && d.approval_stage === 'Executive Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'reject',              label: 'Từ chối',           icon: 'x',  variant: 'danger',
      when: (d) => d.docstatus === 0 && ['Manager Review', 'Executive Review'].includes(d.approval_stage),
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
  ],

  // === M2 Material Request — UC-07 ===
  'SC Material Request': [
    { method: 'approve', label: 'Duyệt MR',  icon: 'check', variant: 'success',
      when: (d) => d.docstatus === 1 && (d.status === 'Pending' || !d.status) },
    { method: 'reject',  label: 'Từ chối',   icon: 'x', variant: 'danger',
      when: (d) => d.docstatus === 1 && (d.status === 'Pending' || !d.status),
      args: [{ key: 'reason', label: 'Lý do từ chối', type: 'textarea', required: true }] },
    { method: 'create_purchase_orders', label: 'Tạo Đơn mua (PO)', icon: 'shopping-cart', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' },
    { method: 'get_po_suggestion', label: 'Gợi ý PO', icon: 'star', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' },
  ],

  // === M3 Purchase Receipt — UC-09..14 ===
  // Lô được tự sinh bởi backend ở on_submit (xem _create_batches_if_needed).
  // QC nếu qc_required=1 cũng được tự tạo (_auto_create_qi). User không cần
  // bấm tay 3 nút "Tạo Phiếu KCS / Tạo Lô / Xem Lô đã tạo".
  //
  // Sau khi QC hoàn tất (qc_status='Accepted' hoặc không cần QC) → 2 hành
  // động chính: tạo Hoá đơn mua + Xếp hàng lên kệ.
  'SC Purchase Receipt': [
    // UC-24 step 1: Tạo Hoá đơn mua từ PR
    { apiMethod: 'supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice.make_invoice_from_pr',
      apiNameArg: 'pr_name',
      label: 'Tạo Hoá đơn mua (PI)', icon: 'receipt', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && (!d.qc_required || d.qc_status === 'Accepted'),
      navigateOnSuccess: { type: 'doc', dt: 'SC Purchase Invoice', from: 'result' } },
    // Xếp hàng lên kệ — chỉ hiện khi QC đã xong (hoặc không cần QC)
    { route: (d) => `/putaway?warehouse=${encodeURIComponent(d.to_warehouse || '')}`,
      label: 'Xếp hàng lên kệ', icon: 'package-plus', variant: 'success',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && (!d.qc_required || d.qc_status === 'Accepted') },
    { method: 'make_debit_note',     label: 'Tạo Debit Note',          icon: 'file-text', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.debit_note },
    { method: 'make_credit_note',    label: 'Tạo Credit Note',         icon: 'banknote', variant: 'success',
      when: (d) => d.is_return === 1 && d.docstatus === 1 },
    { method: 'send_return_notification', label: 'Gửi NCC',            icon: 'mail', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.notification_sent_at },
    { method: 'link_replacement',    label: 'Liên kết PR đổi hàng',   icon: 'link', variant: 'secondary',
      when: (d) => d.is_return === 1 && d.docstatus === 1,
      args: [{ key: 'replacement_pr_name', label: 'Mã PR đổi hàng', type: 'text', required: true }] },
  ],

  // === M8 Purchase Invoice — UC-24 (3-way match indicator) ===
  'SC Purchase Invoice': [
    // UC-24 step 6: nếu mismatch → field mismatch_explanation reqd; UI hiển thị
    // payment_hold; submit để post GL Dr152+Dr1331/Cr331 (via doc.submit).
    // Không cần button riêng — workflow theo docstatus chuẩn.
  ],

  // === M8 Payment Entry — UC-25 ===
  'SC Payment Entry': [
    // UC-25 step 2: Auto-load các PI outstanding của supplier để chọn references
    { apiMethod: 'supplycore.m8_accounting.doctype.sc_payment_entry.sc_payment_entry.auto_load_outstanding_invoices',
      apiNameArg: null,  // không inject doc.name
      label: 'Auto-load PI chưa thanh toán', icon: 'clipboard-list', variant: 'primary',
      when: (d) => d.docstatus === 0 && d.supplier,
      args: [
        { key: 'supplier', label: 'NCC', type: 'text', required: true },
        { key: 'limit', label: 'Số PI tối đa', type: 'number', default: 50 },
      ]},
  ],

  // === M6 Transfer Request — UC-18 ===
  'SC Transfer Request': [
    { method: 'make_stock_entry', label: 'Tạo phiếu chuyển kho', icon: 'truck', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' && !d.stock_entry,
      navigateOnSuccess: { type: 'doc', dt: 'SC Stock Entry', from: 'result' } },
    { method: 'get_transfer_slip_data', label: 'Xem phiếu chuyển', icon: 'file', variant: 'secondary',
      when: (d) => d.docstatus === 1 },
  ],

  // === M9 Inventory Count Sheet — UC-27 ===
  'SC Inventory Count Sheet': [
    { method: 'auto_load_items', label: 'Tự nạp items theo phạm vi', icon: 'clipboard-list', variant: 'primary',
      when: (d) => d.docstatus === 0 && (d.status === 'Draft' || !d.status) },
    { method: 'start_counting', label: 'Bắt đầu đếm', icon: 'play', variant: 'primary',
      when: (d) => d.docstatus === 0 && d.status === 'Draft' },
    { method: 'get_count_sheet_print_data', label: 'Xem dữ liệu in phiếu',
      icon: 'printer', variant: 'secondary',
      when: (d) => d.docstatus === 0,
      args: [{ key: 'hide_system_qty', label: 'Ẩn SL hệ thống (0/1)', type: 'number', default: 1 }] },
    { method: 'make_stock_reconciliation', label: 'Tạo SR đối soát',
      icon: 'settings', variant: 'success',
      when: (d) => d.docstatus === 1 && d.status === 'Counted' && !d.stock_reconciliation,
      navigateOnSuccess: { type: 'doc', dt: 'SC Stock Reconciliation', from: 'result' } },
  ],

  // === M9 Stock Reconciliation — UC-19, UC-28 ===
  'SC Stock Reconciliation': [
    { method: 'load_from_count_sheet', label: 'Tải từ phiếu kiểm', icon: 'download', variant: 'secondary',
      when: (d) => d.docstatus === 0 && d.count_sheet },
    { method: 'reject', label: 'Manager từ chối', icon: 'x', variant: 'danger',
      when: (d) => d.docstatus === 0 && d.status !== 'Rejected',
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
    { method: 'get_reconciliation_minutes_data', label: 'Xem biên bản đối soát',
      icon: 'file', variant: 'secondary',
      when: (d) => d.docstatus === 1 },
  ],

  // === M10 Recall Notice — UC-30 ===
  'SC Recall Notice': [
    { method: 'populate_affected_items', label: 'Tự tìm items ảnh hưởng', icon: 'search', variant: 'primary',
      when: (d) => d.docstatus === 0 },
    { method: 'notify_departments',  label: 'Gửi phiếu cho khoa',  icon: 'mail', variant: 'primary',
      when: (d) => d.docstatus === 1 },
    { method: 'notify_clinical_staff', label: 'Báo BS điều trị',   icon: 'user', variant: 'warning',
      when: (d) => d.docstatus === 1 && !d.clinical_notified_at },
    { method: 'create_return_to_supplier', label: 'Tạo Return PR', icon: 'package', variant: 'primary',
      when: (d) => d.docstatus === 1 && !d.return_pr },
    { method: 'create_write_off',    label: 'Tạo Phiếu hủy',       icon: 'trash', variant: 'danger',
      when: (d) => d.docstatus === 1 && !d.write_off_entry },
    { method: 'audit_dispensings_in_period', label: 'Audit cấp phát', icon: 'clipboard-list', variant: 'secondary',
      when: () => true,
      args: [
        { key: 'start_date', label: 'Từ ngày', type: 'date' },
        { key: 'end_date',   label: 'Đến ngày', type: 'date' },
      ]},
    // UC-30 step 6: cập nhật thu hồi 1 dòng affected_item
    { method: 'update_recovery', label: 'Cập nhật thu hồi (dòng)', icon: 'file-text', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.status !== 'Closed',
      args: [
        { key: 'row_name',      label: 'Tên row affected_item', type: 'text', required: true },
        { key: 'recovered_qty', label: 'SL đã thu hồi', type: 'number', default: 0 },
        { key: 'destroyed_qty', label: 'SL đã huỷ', type: 'number', default: 0 },
        { key: 'status',        label: 'Trạng thái', type: 'select',
          options: ['In Progress', 'Recovered', 'Destroyed', 'Closed'], default: 'In Progress' },
        { key: 'remarks',       label: 'Ghi chú', type: 'textarea' },
      ]},
  ],

  // === M10 Investigation Report — UC-31 ===
  'SC Investigation Report': [
    { method: 'run_audit_trail',     label: 'Chạy Audit Trail',     icon: 'search', variant: 'primary',
      when: () => true },
    { method: 'compare_stock',       label: 'So sánh tồn kho',      icon: 'git-compare', variant: 'primary',
      when: (d) => d.docstatus === 0 },
    { method: 'detect_anomalies',    label: 'Phát hiện bất thường', icon: 'alert-triangle', variant: 'warning',
      when: (d) => d.docstatus === 0,
      args: [{ key: 'large_qty_threshold', label: 'Ngưỡng số lượng lớn', type: 'number', default: 1000 }] },
    { method: 'lock_user',           label: 'Khóa user (Fraud)',    icon: 'lock', variant: 'danger',
      when: () => true,
      args: [
        { key: 'user', label: 'Email user cần khóa', type: 'text', required: true },
        { key: 'reason', label: 'Lý do', type: 'textarea', required: true },
      ]},
    { method: 'create_system_error_adjustment', label: 'Tạo SR điều chỉnh',
      icon: 'settings', variant: 'primary',
      when: (d) => d.docstatus === 0 && d.variance_qty !== 0,
      args: [
        { key: 'actual_qty', label: 'SL thực tế', type: 'number', required: true },
        { key: 'valuation_rate', label: 'Đơn giá', type: 'number' },
      ]},
  ],

  // === M11 Alert — UC-34 ===
  'SC Alert': [
    { method: 'mark_resolved', label: 'Đánh dấu xử lý', icon: 'check', variant: 'success',
      when: (d) => !d.resolved,
      args: [
        { key: 'action', label: 'Hành động', type: 'select',
          options: ['Acknowledged', 'Acted Upon', 'Dismissed', 'Escalated'],
          default: 'Acted Upon', required: true },
        { key: 'remarks', label: 'Ghi chú', type: 'textarea' },
      ]},
    { method: 'snooze_alert', label: 'Snooze', icon: 'alarm-clock', variant: 'secondary',
      when: (d) => !d.resolved,
      args: [
        { key: 'hours',  label: 'Số giờ', type: 'number', required: true, default: 4 },
        { key: 'reason', label: 'Lý do',  type: 'textarea' },
      ]},
    { method: 'assign_alert', label: 'Phân công', icon: 'user', variant: 'secondary',
      when: (d) => !d.resolved,
      args: [
        { key: 'user', label: 'Email user', type: 'text', required: true },
        { key: 'note', label: 'Ghi chú',    type: 'textarea' },
      ]},

    // === UC-34 step 4: Hành động nghiệp vụ theo loại alert ===
    // Low stock → tạo PO khẩn
    { method: 'action_create_purchase_order',
      label: 'Tạo PO khẩn', icon: 'shopping-cart', variant: 'primary',
      when: (d) => !d.resolved && d.alert_type === 'low_stock',
      navigateOnSuccess: { type: 'doc', dt: 'SC Purchase Order', from: 'po' } },
    // Low stock → tạo MR (chậm hơn)
    { method: 'action_create_material_request',
      label: 'Tạo Yêu cầu mua (MR)', icon: 'file-text', variant: 'secondary',
      when: (d) => !d.resolved && d.alert_type === 'low_stock',
      navigateOnSuccess: { type: 'doc', dt: 'SC Material Request', from: 'mr' } },
    // Expiring → ưu tiên cấp phát lô gần hết hạn
    { method: 'action_priority_dispense',
      label: 'Ưu tiên cấp phát', icon: 'zap', variant: 'warning',
      when: (d) => !d.resolved && (d.alert_type === 'expiring' || d.alert_type === 'expiring_soon'),
      args: [{ key: 'note', label: 'Ghi chú dispense', type: 'textarea' }] },
    // PO overdue / supplier issue → liên hệ NCC
    { method: 'action_contact_supplier',
      label: 'Liên hệ NCC', icon: 'mail', variant: 'primary',
      when: (d) => !d.resolved && ['po_overdue', 'supplier_quality', 'po_late'].includes(d.alert_type),
      args: [{ key: 'message', label: 'Nội dung email', type: 'textarea' }] },
    // Recall / batch fail → cách ly lô
    { method: 'action_quarantine_batch',
      label: 'Cách ly lô', icon: 'ban', variant: 'danger',
      when: (d) => !d.resolved &&
        ['batch_fail', 'recall_batch', 'qi_failed'].includes(d.alert_type) &&
        d.reference_doctype === 'SC Batch' },
    // AP outstanding → tạo phiếu thanh toán
    { method: 'action_create_payment',
      label: 'Tạo Phiếu thanh toán', icon: 'credit-card', variant: 'primary',
      when: (d) => !d.resolved && ['ap_overdue', 'payment_due'].includes(d.alert_type) &&
        d.reference_doctype === 'SC Purchase Invoice',
      navigateOnSuccess: { type: 'doc', dt: 'SC Payment Entry', from: 'pe' } },
  ],

  // === M11 Alert Rule — UC-33 ===
  'SC Alert Rule': [
    { method: 'test_alert_rule', label: 'Test gửi cảnh báo', icon: 'flask-conical', variant: 'primary',
      when: () => true },
  ],
}
