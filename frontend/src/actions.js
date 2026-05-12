// Per-DocType custom actions (whitelisted methods từ Python backend)
// Method names verified từ doctype.py thực tế (UC-01..34)

export const ACTIONS = {
  // === M1 Framework Contract — UC-01..04 ===
  'Framework Contract': [
    { method: 'submit_for_review', label: 'Gửi duyệt',          icon: '📤', variant: 'primary',
      when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage || d.approval_stage === 'Rejected') },
    { method: 'approve_as_manager', label: 'Manager duyệt',     icon: '✓',  variant: 'success',
      when: (d) => d.approval_stage === 'Manager Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'approve_as_executive', label: 'Executive duyệt', icon: '✓✓', variant: 'success',
      when: (d) => d.approval_stage === 'Executive Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'reject_approval',   label: 'Từ chối',            icon: '✕',  variant: 'danger',
      when: (d) => ['Manager Review', 'Executive Review'].includes(d.approval_stage),
      args: [{ key: 'reason', label: 'Lý do từ chối', type: 'textarea', required: true }] },
    { method: 'request_renewal',   label: 'Gia hạn HĐ',         icon: '🔄', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Active',
      args: [
        { key: 'new_valid_to', label: 'Hết hạn mới', type: 'date', required: true },
        { key: 'reason', label: 'Lý do', type: 'textarea', required: true },
      ]},
  ],

  // === M2 Purchase Order — UC-08 ===
  'SC Purchase Order': [
    { method: 'submit_for_review',   label: 'Gửi duyệt',         icon: '📤', variant: 'primary',
      when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage) },
    { method: 'approve_as_manager',  label: 'Manager duyệt',     icon: '✓',  variant: 'success',
      when: (d) => d.approval_stage === 'Manager Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'approve_as_executive', label: 'Executive duyệt',  icon: '✓✓', variant: 'success',
      when: (d) => d.approval_stage === 'Executive Review',
      args: [{ key: 'comment', label: 'Ghi chú', type: 'textarea' }] },
    { method: 'reject',              label: 'Từ chối',           icon: '✕',  variant: 'danger',
      when: (d) => ['Manager Review', 'Executive Review'].includes(d.approval_stage),
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
  ],

  // === M2 Material Request — UC-07 ===
  'SC Material Request': [
    { method: 'approve', label: 'Duyệt MR',  icon: '✓', variant: 'success',
      when: (d) => d.docstatus === 1 && (d.status === 'Pending' || !d.status) },
    { method: 'reject',  label: 'Từ chối',   icon: '✕', variant: 'danger',
      when: (d) => d.docstatus === 1 && (d.status === 'Pending' || !d.status),
      args: [{ key: 'reason', label: 'Lý do từ chối', type: 'textarea', required: true }] },
    { method: 'get_po_suggestion', label: 'Gợi ý PO', icon: '💡', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' },
  ],

  // === M3 Purchase Receipt — UC-11, UC-26 ===
  'SC Purchase Receipt': [
    { method: 'make_debit_note',     label: 'Tạo Debit Note',          icon: '📝', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.debit_note },
    { method: 'make_credit_note',    label: 'Tạo Credit Note',         icon: '💰', variant: 'success',
      when: (d) => d.is_return === 1 && d.docstatus === 1 },
    { method: 'send_return_notification', label: 'Gửi NCC',            icon: '📧', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.notification_sent_at },
    { method: 'link_replacement',    label: 'Liên kết PR đổi hàng',   icon: '🔗', variant: 'secondary',
      when: (d) => d.is_return === 1 && d.docstatus === 1,
      args: [{ key: 'replacement_pr_name', label: 'Mã PR đổi hàng', type: 'text', required: true }] },
  ],

  // === M9 Stock Reconciliation — UC-19, UC-28 ===
  'SC Stock Reconciliation': [
    { method: 'reject', label: 'Manager từ chối', icon: '✕', variant: 'danger',
      when: (d) => d.docstatus === 0 && d.status !== 'Rejected',
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
    { method: 'get_reconciliation_minutes_data', label: 'Xem biên bản đối soát',
      icon: '📄', variant: 'secondary',
      when: (d) => d.docstatus === 1 },
  ],

  // === M10 Recall Notice — UC-30 ===
  'SC Recall Notice': [
    { method: 'populate_affected_items', label: 'Tự tìm items ảnh hưởng', icon: '🔍', variant: 'primary',
      when: (d) => d.docstatus === 0 },
    { method: 'notify_departments',  label: 'Gửi phiếu cho khoa',  icon: '📧', variant: 'primary',
      when: (d) => d.docstatus === 1 },
    { method: 'notify_clinical_staff', label: 'Báo BS điều trị',   icon: '👨‍⚕️', variant: 'warning',
      when: (d) => d.docstatus === 1 && !d.clinical_notified_at },
    { method: 'create_return_to_supplier', label: 'Tạo Return PR', icon: '📦', variant: 'primary',
      when: (d) => d.docstatus === 1 && !d.return_pr },
    { method: 'create_write_off',    label: 'Tạo Phiếu hủy',       icon: '🗑️', variant: 'danger',
      when: (d) => d.docstatus === 1 && !d.write_off_entry },
    { method: 'audit_dispensings_in_period', label: 'Audit cấp phát', icon: '📋', variant: 'secondary',
      when: () => true,
      args: [
        { key: 'start_date', label: 'Từ ngày', type: 'date' },
        { key: 'end_date',   label: 'Đến ngày', type: 'date' },
      ]},
  ],

  // === M10 Investigation Report — UC-31 ===
  'SC Investigation Report': [
    { method: 'run_audit_trail',     label: 'Chạy Audit Trail',     icon: '🔍', variant: 'primary',
      when: () => true },
    { method: 'compare_stock',       label: 'So sánh tồn kho',      icon: '⚖️', variant: 'primary',
      when: (d) => d.docstatus === 0 },
    { method: 'detect_anomalies',    label: 'Phát hiện bất thường', icon: '⚠️', variant: 'warning',
      when: (d) => d.docstatus === 0,
      args: [{ key: 'large_qty_threshold', label: 'Ngưỡng số lượng lớn', type: 'number', default: 1000 }] },
    { method: 'lock_user',           label: 'Khóa user (Fraud)',    icon: '🔒', variant: 'danger',
      when: () => true,
      args: [
        { key: 'user', label: 'Email user cần khóa', type: 'text', required: true },
        { key: 'reason', label: 'Lý do', type: 'textarea', required: true },
      ]},
    { method: 'create_system_error_adjustment', label: 'Tạo SR điều chỉnh',
      icon: '🔧', variant: 'primary',
      when: (d) => d.docstatus === 0 && d.variance_qty !== 0,
      args: [
        { key: 'actual_qty', label: 'SL thực tế', type: 'number', required: true },
        { key: 'valuation_rate', label: 'Đơn giá', type: 'number' },
      ]},
  ],

  // === M11 Alert — UC-34 ===
  'SC Alert': [
    { method: 'mark_resolved', label: 'Đánh dấu xử lý', icon: '✓', variant: 'success',
      when: (d) => !d.resolved,
      args: [
        { key: 'action', label: 'Hành động', type: 'select',
          options: ['Acknowledged', 'Acted Upon', 'Dismissed', 'Escalated'],
          default: 'Acted Upon', required: true },
        { key: 'remarks', label: 'Ghi chú', type: 'textarea' },
      ]},
    { method: 'snooze_alert', label: 'Snooze', icon: '💤', variant: 'secondary',
      when: (d) => !d.resolved,
      args: [
        { key: 'hours',  label: 'Số giờ', type: 'number', required: true, default: 4 },
        { key: 'reason', label: 'Lý do',  type: 'textarea' },
      ]},
    { method: 'assign_alert', label: 'Phân công', icon: '👤', variant: 'secondary',
      when: (d) => !d.resolved,
      args: [
        { key: 'user', label: 'Email user', type: 'text', required: true },
        { key: 'note', label: 'Ghi chú',    type: 'textarea' },
      ]},
  ],

  // === M11 Alert Rule — UC-33 ===
  'SC Alert Rule': [
    { method: 'test_alert_rule', label: 'Test gửi cảnh báo', icon: '🧪', variant: 'primary',
      when: () => true },
  ],
}
