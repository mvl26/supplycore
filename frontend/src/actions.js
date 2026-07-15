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

  // === M1 Release Order — UC-05 (Lệnh gọi hàng → PO) ===
  'Release Order': [
    { method: 'make_purchase_order', label: 'Tạo đơn mua (PO)', icon: 'shopping-cart', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' && !d.purchase_order,
      navigateOnSuccess: { type: 'doc', dt: 'SC Purchase Order', from: 'result' } },
  ],

  // === M2 Procurement Plan — UC-06 (Kế hoạch mua → MR) ===
  'Procurement Plan': [
    { method: 'auto_load_items', label: 'Tự nạp theo tiêu thụ', icon: 'clipboard-list', variant: 'primary',
      when: (d) => d.docstatus === 0 && d.warehouse,
      args: [{ key: 'item_filter', label: 'Lọc theo nhóm VT (tuỳ chọn)', type: 'link',
               linkTo: 'SC Item Group', placeholder: '— Tất cả nhóm (để trống) —' }] },
    { method: 'auto_load_reorder_items', label: 'Tự nạp theo tồn tối thiểu', icon: 'download', variant: 'secondary',
      when: (d) => d.docstatus === 0 && d.warehouse },
    { method: 'make_material_request', label: 'Tạo Yêu cầu mua (MR)', icon: 'file-text', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Approved' && !d.material_request,
      navigateOnSuccess: { type: 'doc', dt: 'SC Material Request', from: 'result' } },
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
  // Sau khi QC hoàn tất (qc_status='Pass' hoặc không cần QC) → 2 hành
  // động chính: tạo Hoá đơn mua + Xếp hàng lên kệ.
  'SC Purchase Receipt': [
    // GĐ MVL — Bước 2: Xác nhận nhập kho (ghi sổ kho tại ngày xác nhận). Chỉ hiện
    // khi đã tiếp nhận + QC Pass (hoặc không cần QC) + chưa nhập kho. Role thủ kho/
    // quản lý mới bấm được (backend chặn 403). Ghi sổ ở NGÀY xác nhận (mặc định hôm nay).
    { method: 'confirm_warehouse_in',
      label: 'Xác nhận nhập kho', icon: 'package-check', variant: 'success',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && d.receipt_status === 'Đã tiếp nhận'
        && (!d.qc_required || d.qc_status === 'Pass' || d.qc_status === 'Partial Pass'),
      args: [{ key: 'warehouse_in_date', label: 'Ngày nhập kho (để trống = hôm nay)', type: 'date' }] },
    // QC có dòng Từ chối -> điều hướng sang phiếu Trả NCC (nháp, tự tạo).
    { method: 'find_return_pr',
      label: 'Xem phiếu trả NCC', icon: 'undo-2', variant: 'warning',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && (d.qc_status === 'Fail' || d.qc_status === 'Partial Pass') },
    // UC-24 step 1: Tạo Hoá đơn mua từ PR
    { apiMethod: 'supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice.make_invoice_from_pr',
      apiNameArg: 'pr_name',
      label: 'Tạo Hoá đơn mua (PI)', icon: 'receipt', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && (!d.qc_required || d.qc_status === 'Pass' || d.qc_status === 'Partial Pass'),
      navigateOnSuccess: { type: 'doc', dt: 'SC Purchase Invoice', from: 'result' } },
    // In phiếu — backend tự chọn mẫu: "Phiếu nhập kho" khi Đã nhập kho, ngược lại
    // "Phiếu tiếp nhận tạm" (ghi rõ chưa nhập kho). Mở bản in HTML ở tab mới.
    // In phiếu — mở printview (tab mới): mẫu "Phiếu nhập kho (TT99)" khi đã nhập kho
    // (in vật tư + lô + hạn), ngược lại "Phiếu tiếp nhận tạm".
    { printFormat: (d) => d.receipt_status === 'Đã nhập kho'
        ? 'PR - Phiếu nhập kho (TT99)' : 'PR - Phiếu tiếp nhận tạm',
      label: 'In phiếu (tiếp nhận / nhập kho)', icon: 'printer', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.is_return === 0 },
    // In phiếu TRẢ NCC — chỉ các dòng hàng trả lại (lô QC không đạt).
    { printFormat: () => 'PR - Phiếu trả NCC',
      label: 'In phiếu trả NCC', icon: 'printer', variant: 'secondary',
      when: (d) => d.docstatus === 1 && d.is_return === 1 },
    // Xếp hàng lên kệ — chỉ hiện khi QC đã xong (hoặc không cần QC)
    { route: (d) => `/putaway?warehouse=${encodeURIComponent(d.to_warehouse || '')}`,
      label: 'Xếp hàng lên kệ', icon: 'package-plus', variant: 'success',
      when: (d) => d.docstatus === 1 && d.is_return === 0
        && (!d.qc_required || d.qc_status === 'Pass') },
    { method: 'make_debit_note',     label: 'Tạo Debit Note',          icon: 'file-text', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.debit_note },
    { method: 'make_credit_note',    label: 'Tạo Credit Note',         icon: 'banknote', variant: 'success',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.credit_note },
    { method: 'send_return_notification', label: 'Gửi NCC',            icon: 'mail', variant: 'primary',
      when: (d) => d.is_return === 1 && d.docstatus === 1 && !d.notification_sent_at },
    { method: 'link_replacement',    label: 'Liên kết PR đổi hàng',   icon: 'link', variant: 'secondary',
      when: (d) => d.is_return === 1 && d.docstatus === 1,
      args: [{ key: 'replacement_pr_name', label: 'PR đổi hàng', type: 'link',
               linkTo: 'SC Purchase Receipt', required: true, placeholder: '— Chọn phiếu nhập đổi hàng —' }] },
  ],

  // === M7 Sales — O2C (SO duyệt → DN → nghiệm thu → SI → thu tiền) ===
  'SC Customer': [
    // GĐ MVL — cấp tài khoản Portal cho khách (role SC Customer Portal). Chỉ
    // hiện khi chưa có portal_user. Nhập email → tạo Website User + link + gửi
    // email đặt mật khẩu để khách đăng nhập gọi hàng.
    { apiMethod: 'supplycore.api.portal.portal_provision',
      apiNameArg: 'customer',
      label: 'Cấp tài khoản Portal', icon: 'user-plus', variant: 'primary',
      when: (d) => d.docstatus !== 2 && !d.portal_user,
      args: [
        { key: 'email', label: 'Email đăng nhập của khách', type: 'text', required: true },
        { key: 'send_invite', label: 'Gửi email đặt mật khẩu (1/0)', type: 'number', default: 1 },
      ] },
  ],
  'SC Sales Order': [
    { method: 'approve', label: 'Duyệt', icon: 'check', variant: 'success',
      when: (d) => d.docstatus === 1 && d.status === 'Chờ duyệt' },
    { method: 'reject',  label: 'Từ chối', icon: 'x', variant: 'danger',
      when: (d) => d.docstatus === 1 && d.status === 'Chờ duyệt' },
    // GĐ MVL b5 — bán tự động: sau khi duyệt, nhân viên bấm tạo phiếu giao.
    { apiMethod: 'supplycore.api.sales.make_delivery',
      apiNameArg: 'sales_order',
      label: 'Tạo phiếu giao', icon: 'truck', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Đã duyệt',
      args: [
        { key: 'from_warehouse', label: 'Kho xuất (để trống = kho mặc định)', type: 'link',
          linkTo: 'SC Warehouse', placeholder: '— Chọn kho (để trống = kho mặc định) —' },
        { key: 'delivery_date', label: 'Ngày giao', type: 'date' },
      ],
      navigateOnSuccess: { type: 'doc', dt: 'SC Delivery Note', from: 'name' } },
  ],
  'SC Delivery Note': [
    // Lập biên bản nghiệm thu (create+submit qua sales API) — param: delivery_note
    { apiMethod: 'supplycore.api.sales.delivery_accept',
      apiNameArg: 'delivery_note',
      label: 'Lập nghiệm thu', icon: 'clipboard-check', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Đã giao',
      args: [
        { key: 'accepted_by', label: 'Người nhận hàng', type: 'text' },
        { key: 'note', label: 'Ghi chú', type: 'textarea' },
      ],
      navigateOnSuccess: { type: 'doc', dt: 'SC Acceptance Record', from: 'result' } },
    // Xuất hóa đơn bán từ DN đã nghiệm thu — param: delivery_note
    { apiMethod: 'supplycore.api.sales.sales_invoice_create',
      apiNameArg: 'delivery_note',
      label: 'Xuất hóa đơn', icon: 'receipt', variant: 'primary',
      when: (d) => d.docstatus === 1 && d.status === 'Đã nghiệm thu',
      args: [
        { key: 'tax_rate', label: 'Thuế suất (%)', type: 'number', default: 0 },
      ],
      navigateOnSuccess: { type: 'doc', dt: 'SC Sales Invoice', from: 'name' } },
  ],
  'SC Sales Invoice': [
    // Thu tiền (create+submit SC Sales Receipt) — param: sales_invoice
    { apiMethod: 'supplycore.api.sales.receipt_collect',
      apiNameArg: 'sales_invoice',
      label: 'Thu tiền', icon: 'banknote', variant: 'success',
      when: (d) => d.docstatus === 1 && Number(d.outstanding_amount) > 0,
      args: [
        { key: 'amount', label: 'Số tiền thu', type: 'number', required: true },
        { key: 'mode', label: 'Hình thức', type: 'select',
          options: ['Chuyển khoản', 'Tiền mặt'], default: 'Chuyển khoản' },
      ],
      navigateOnSuccess: { type: 'doc', dt: 'SC Sales Receipt', from: 'name' } },
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
        { key: 'supplier', label: 'NCC', type: 'link', linkTo: 'SC Supplier', required: true,
          placeholder: '— Chọn nhà cung cấp —' },
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
        { key: 'user', label: 'User cần khóa', type: 'link', linkTo: 'User', required: true,
          placeholder: '— Chọn user —' },
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
        { key: 'user', label: 'User', type: 'link', linkTo: 'User', required: true,
          placeholder: '— Chọn user —' },
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
