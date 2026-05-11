// Per-DocType custom actions (whitelisted methods from UC flow specs)
// Each action: { method, label, icon, variant, requireSubmitted, args: [{key, label, type, ...}] }

export const ACTIONS = {
  'Framework Contract': [
    { method: 'submit_for_review',   label: 'Gửi duyệt Manager',       icon: '📤', variant: 'primary',   when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage) },
    { method: 'manager_approve',     label: 'Manager duyệt',           icon: '✓',  variant: 'success',   when: (d) => d.approval_stage === 'Manager Review' },
    { method: 'executive_approve',   label: 'Executive duyệt',         icon: '✓✓', variant: 'success',   when: (d) => d.approval_stage === 'Executive Review' },
    { method: 'reject',              label: 'Từ chối',                 icon: '✕',  variant: 'danger',    when: (d) => ['Manager Review', 'Executive Review'].includes(d.approval_stage),
      args: [{ key: 'reason', label: 'Lý do từ chối', type: 'textarea', required: true }] },
  ],
  'SC Purchase Order': [
    { method: 'submit_for_review',   label: 'Gửi duyệt',               icon: '📤', variant: 'primary',   when: (d) => d.docstatus === 0 && (d.approval_stage === 'Draft' || !d.approval_stage) },
    { method: 'manager_approve',     label: 'Manager duyệt',           icon: '✓',  variant: 'success',   when: (d) => d.approval_stage === 'Manager Review' },
    { method: 'send_to_supplier',    label: 'Gửi NCC qua email',       icon: '📧', variant: 'primary',   when: (d) => d.docstatus === 1 && d.status === 'Approved' },
  ],
  'SC Material Request': [
    { method: 'approve',             label: 'Duyệt',                   icon: '✓',  variant: 'success',   when: (d) => d.docstatus === 1 && d.status === 'Pending' },
    { method: 'reject',              label: 'Từ chối',                 icon: '✕',  variant: 'danger',    when: (d) => d.docstatus === 1 && d.status === 'Pending',
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
  ],
  'SC Purchase Receipt': [
    { method: 'make_debit_note',     label: 'Tạo Debit Note',          icon: '📝', variant: 'primary',   when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.debit_note },
    { method: 'make_credit_note',    label: 'Tạo Credit Note (refund)', icon: '💰', variant: 'success',  when: (d) => d.is_return === 1 && d.docstatus === 1 },
    { method: 'send_return_notification', label: 'Gửi NCC thông báo trả', icon: '📧', variant: 'primary', when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.notification_sent_at },
  ],
  'SC Stock Reconciliation': [
    { method: 'reject',              label: 'Manager từ chối',         icon: '✕',  variant: 'danger',    when: (d) => d.docstatus === 0 && d.status !== 'Rejected',
      args: [{ key: 'reason', label: 'Lý do', type: 'textarea', required: true }] },
    { method: 'get_reconciliation_minutes_data', label: 'Xem biên bản đối soát', icon: '📄', variant: 'secondary', when: (d) => d.docstatus === 1 },
  ],
  'SC Recall Notice': [
    { method: 'populate_affected_items', label: 'Tự tìm items ảnh hưởng', icon: '🔍', variant: 'primary', when: (d) => d.docstatus === 0 },
    { method: 'notify_departments',  label: 'Gửi phiếu cho khoa',      icon: '📧', variant: 'primary',   when: (d) => d.docstatus === 1 },
    { method: 'notify_clinical_staff', label: 'Báo BS điều trị',       icon: '👨‍⚕️', variant: 'warning',  when: (d) => d.docstatus === 1 && !d.clinical_notified_at },
    { method: 'create_return_to_supplier', label: 'Tạo Return PR',     icon: '📦', variant: 'primary',   when: (d) => d.docstatus === 1 && !d.return_pr },
    { method: 'create_write_off',    label: 'Tạo Phiếu hủy',           icon: '🗑️', variant: 'danger',    when: (d) => d.docstatus === 1 && !d.write_off_entry },
    { method: 'audit_dispensings_in_period', label: 'Audit cấp phát giai đoạn', icon: '📋', variant: 'secondary', when: (d) => true },
  ],
  'SC Investigation Report': [
    { method: 'run_audit_trail',     label: 'Chạy Audit Trail',        icon: '🔍', variant: 'primary',   when: (d) => true },
    { method: 'compare_stock',       label: 'So sánh tồn kho',         icon: '⚖️', variant: 'primary',   when: (d) => d.docstatus === 0 },
    { method: 'detect_anomalies',    label: 'Phát hiện bất thường',    icon: '⚠️', variant: 'warning',   when: (d) => d.docstatus === 0,
      args: [{ key: 'large_qty_threshold', label: 'Ngưỡng số lượng lớn', type: 'number', default: 1000 }] },
    { method: 'lock_user',           label: 'Khóa user (Fraud)',       icon: '🔒', variant: 'danger',    when: (d) => true,
      args: [
        { key: 'user', label: 'Email user cần khóa', type: 'text', required: true },
        { key: 'reason', label: 'Lý do', type: 'textarea', required: true },
      ]},
    { method: 'create_system_error_adjustment', label: 'Tạo SR điều chỉnh', icon: '🔧', variant: 'primary', when: (d) => d.docstatus === 0 && d.variance_qty != 0,
      args: [
        { key: 'actual_qty', label: 'SL thực tế', type: 'number', required: true },
        { key: 'valuation_rate', label: 'Đơn giá', type: 'number' },
      ]},
  ],
  'SC Alert': [
    { method: 'mark_resolved',       label: 'Đánh dấu xử lý',          icon: '✓',  variant: 'success',   when: (d) => !d.resolved,
      args: [
        { key: 'action', label: 'Hành động', type: 'select', options: ['Acknowledged','Acted Upon','Dismissed','Escalated'], default: 'Acted Upon', required: true },
        { key: 'remarks', label: 'Ghi chú', type: 'textarea' },
      ]},
    { method: 'snooze_alert',        label: 'Snooze',                  icon: '💤', variant: 'secondary', when: (d) => !d.resolved,
      args: [
        { key: 'hours', label: 'Số giờ', type: 'number', required: true, default: 4 },
        { key: 'reason', label: 'Lý do', type: 'textarea' },
      ]},
    { method: 'assign_alert',        label: 'Phân công',               icon: '👤', variant: 'secondary', when: (d) => !d.resolved,
      args: [
        { key: 'user', label: 'Email user', type: 'text', required: true },
        { key: 'note', label: 'Ghi chú', type: 'textarea' },
      ]},
  ],
  'SC Alert Rule': [
    { method: 'test_alert_rule',     label: 'Test gửi',                icon: '🧪', variant: 'primary',   when: (d) => true },
  ],
}
