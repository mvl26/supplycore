// Form schemas — fields cho create/edit từng doctype
// Field type: Data | Text | Small Text | Long Text | Int | Float | Currency
//            Percent | Date | Datetime | Time | Check | Select | Link
//
// Item schemas dùng cho child table

export const FORM_SCHEMAS = {
  // ============================================================
  // M1 Contract
  // ============================================================
  'Framework Contract': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'supplier', label: 'Nhà cung cấp', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'contract_number', label: 'Số HĐ', type: 'Data', required: true },
        { name: 'contract_date', label: 'Ngày ký', type: 'Date', required: true },
        { name: 'valid_from', label: 'Hiệu lực từ', type: 'Date', required: true },
        { name: 'valid_to', label: 'Hết hạn', type: 'Date', required: true },
      ]},
      { title: 'Giá trị', fields: [
        { name: 'total_value', label: 'Tổng giá trị (VND)', type: 'Currency', required: true },
        { name: 'payment_terms', label: 'Điều khoản thanh toán', type: 'Data' },
        { name: 'delivery_terms', label: 'Điều khoản giao hàng', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Danh mục vật tư',
      columns: [
        { name: 'item_code', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '30%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '15%',
          fetchFrom: { source: 'item_code', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'contract_qty', label: 'SL HĐ', type: 'Float', required: true, width: '20%' },
        { name: 'unit_price', label: 'Đơn giá', type: 'Currency', required: true, width: '20%' },
      ],
    },
  },

  // ============================================================
  // M2 Planning
  // ============================================================
  'SC Material Request': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'request_type', label: 'Loại', type: 'Select', required: true,
          options: ['Purchase', 'Material Transfer', 'Material Issue'], default: 'Purchase' },
        { name: 'transaction_date', label: 'Ngày tạo', type: 'Date', required: true, default: 'today' },
        { name: 'schedule_date', label: 'Ngày cần', type: 'Date', required: true },
        { name: 'warehouse', label: 'Kho nhận', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '28%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '14%',
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '18%' },
        { name: 'schedule_date', label: 'Ngày cần', type: 'Date', width: '20%' },
      ],
    },
  },

  'SC Purchase Order': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'transaction_date', label: 'Ngày PO', type: 'Date', required: true, default: 'today' },
        { name: 'schedule_date', label: 'Ngày giao DK', type: 'Date', required: true },
        { name: 'framework_contract', label: 'HĐ khung', type: 'Link', linkTo: 'Framework Contract' },
        { name: 'delivery_terms', label: 'Điều khoản giao', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', required: true, width: '20%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true, width: '15%' },
        { name: 'schedule_date', label: 'Ngày giao', type: 'Date', width: '15%' },
      ],
    },
  },

  // ============================================================
  // M3 Receiving
  // ============================================================
  'SC Purchase Receipt': {
    sections: [
      { title: 'Thông tin nhập kho', fields: [
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'purchase_order', label: 'PO tham chiếu', type: 'Link', linkTo: 'SC Purchase Order' },
        { name: 'posting_date', label: 'Ngày nhập', type: 'Date', required: true, default: 'today' },
        { name: 'to_warehouse', label: 'Kho đích', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'is_return', label: 'Phiếu trả NCC', type: 'Check' },
        { name: 'return_reason', label: 'Lý do trả', type: 'Small Text', dependOn: 'is_return' },
        { name: 'qc_required', label: 'Yêu cầu QC', type: 'Check', default: 1 },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '20%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL nhận', type: 'Float', required: true, width: '12%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', width: '15%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '15%' },
        { name: 'supplier_batch_no', label: 'Số lô NCC', type: 'Data', width: '13%' },
        { name: 'expiry_date', label: 'HD', type: 'Date', width: '15%' },
      ],
    },
  },

  // ============================================================
  // M4 WMS
  // ============================================================
  'SC Batch': {
    sections: [
      { title: 'Thông tin lô', fields: [
        { name: 'batch_id', label: 'Mã lô', type: 'Data', required: true },
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true },
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier' },
        { name: 'supplier_batch_no', label: 'Số lô NCC', type: 'Data' },
        { name: 'manufacturing_date', label: 'Ngày SX', type: 'Date' },
        { name: 'expiry_date', label: 'Hạn dùng', type: 'Date', required: true },
        { name: 'manufacturer', label: 'NSX', type: 'Data' },
        { name: 'country_of_origin', label: 'Xuất xứ', type: 'Data' },
      ]},
      { title: 'Trạng thái', fields: [
        { name: 'qc_status', label: 'QC', type: 'Select', options: ['Pending', 'Accepted', 'Rejected'], default: 'Pending' },
        { name: 'short_expiry_ack', label: 'Xác nhận nhập lô hạn ngắn', type: 'Check' },
      ]},
    ],
  },

  // ============================================================
  // M6 Transfer
  // ============================================================
  'SC Transfer Request': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'request_date', label: 'Ngày yêu cầu', type: 'Date', required: true, default: 'today' },
        { name: 'from_warehouse', label: 'Kho nguồn', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'to_warehouse', label: 'Kho đích', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'reason', label: 'Lý do', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '30%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '15%' },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '20%' },
        { name: 'batch', label: 'Lô (nếu chỉ định)', type: 'Link', linkTo: 'SC Batch', width: '30%' },
      ],
    },
  },

  'SC Stock Entry': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'entry_type', label: 'Loại GT', type: 'Select', required: true,
          options: ['Material Receipt', 'Material Issue', 'Material Transfer', 'Manufacture', 'Repack'],
          default: 'Material Transfer' },
        { name: 'posting_date', label: 'Ngày', type: 'Date', required: true, default: 'today' },
        { name: 'from_warehouse', label: 'Kho nguồn', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'to_warehouse', label: 'Kho đích', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'purpose', label: 'Mục đích', type: 'Data' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '22%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%' },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'valuation_rate', label: 'Đơn giá', type: 'Currency', width: '18%' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '20%' },
        { name: 'fefo_override', label: 'FEFO override', type: 'Check', width: '15%' },
      ],
    },
  },

  // ============================================================
  // M7 Dispensing
  // ============================================================
  'SC Dispensing Request': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'request_date', label: 'Ngày YC', type: 'Date', required: true, default: 'today' },
        { name: 'department', label: 'Khoa yêu cầu', type: 'Link', linkTo: 'SC Department', required: true },
        { name: 'from_warehouse', label: 'Kho cấp', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'priority', label: 'Ưu tiên', type: 'Select',
          options: ['Normal', 'Urgent', 'Emergency'], default: 'Normal' },
        { name: 'reason', label: 'Lý do', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '32%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '15%' },
        { name: 'requested_qty', label: 'SL YC', type: 'Float', required: true, width: '18%' },
        { name: 'approved_qty', label: 'SL duyệt', type: 'Float', width: '18%' },
        { name: 'remarks', label: 'Ghi chú', type: 'Data', width: '17%' },
      ],
    },
  },

  'SC Patient Dispensing': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'dispensing_date', label: 'Ngày cấp', type: 'Date', required: true, default: 'today' },
        { name: 'patient', label: 'Bệnh nhân', type: 'Link', linkTo: 'SC Patient', required: true },
        { name: 'ward', label: 'Khoa', type: 'Link', linkTo: 'SC Department' },
        { name: 'dispensing_request', label: 'DR liên quan', type: 'Link', linkTo: 'SC Dispensing Request' },
        { name: 'bhyt_card_no', label: 'Số thẻ BHYT', type: 'Data',
          fetchFrom: { source: 'patient', target_doctype: 'SC Patient', target_field: 'bhyt_card_no' } },
        { name: 'bhyt_payment_rate', label: 'Tỷ lệ BHYT (%)', type: 'Percent', default: 80 },
      ]},
    ],
    items: {
      field: 'items', label: 'Items dùng',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '28%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%' },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '12%' },
        { name: 'unit_cost', label: 'Đơn giá', type: 'Currency', required: true, width: '18%' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '15%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '15%' },
      ],
    },
  },

  // ============================================================
  // M8 Accounting
  // ============================================================
  'SC Purchase Invoice': {
    sections: [
      { title: 'Thông tin HD', fields: [
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'invoice_date', label: 'Ngày HD', type: 'Date', required: true, default: 'today' },
        { name: 'due_date', label: 'Hạn thanh toán', type: 'Date' },
        { name: 'purchase_receipt', label: 'PR tham chiếu', type: 'Link', linkTo: 'SC Purchase Receipt' },
        { name: 'supplier_invoice_no', label: 'Số HD NCC', type: 'Data' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%' },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', required: true, width: '18%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '15%' },
        { name: 'purchase_receipt_item', label: 'PR Item ref', type: 'Data', width: '15%' },
      ],
    },
  },

  'SC Payment Entry': {
    sections: [
      { title: 'Thông tin thanh toán', fields: [
        { name: 'payment_date', label: 'Ngày thanh toán', type: 'Date', required: true, default: 'today' },
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'amount', label: 'Số tiền', type: 'Currency', required: true },
        { name: 'payment_method', label: 'Phương thức', type: 'Select',
          options: ['Bank Transfer', 'Cash', 'Cheque'], default: 'Bank Transfer' },
        { name: 'bank_account', label: 'Tài khoản ngân hàng', type: 'Data' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'references', label: 'Hóa đơn thanh toán',
      columns: [
        { name: 'purchase_invoice', label: 'PI', type: 'Link', linkTo: 'SC Purchase Invoice', required: true, width: '50%' },
        { name: 'allocated_amount', label: 'Số tiền phân bổ', type: 'Currency', required: true, width: '50%' },
      ],
    },
  },

  // ============================================================
  // M9 Stocktake
  // ============================================================
  'SC Inventory Count Sheet': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'posting_date', label: 'Ngày kiểm', type: 'Date', required: true, default: 'today' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'count_type', label: 'Loại kiểm', type: 'Select',
          options: ['Full', 'Cycle', 'Adhoc'], default: 'Cycle' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '18%' },
        { name: 'system_qty', label: 'SL hệ thống', type: 'Float', width: '15%' },
        { name: 'counted_qty', label: 'SL đếm', type: 'Float', required: true, width: '15%' },
        { name: 'valuation_rate', label: 'Đơn giá', type: 'Currency', width: '17%' },
      ],
    },
  },

  'SC Stock Reconciliation': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'posting_date', label: 'Ngày đối soát', type: 'Date', required: true, default: 'today' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'count_sheet', label: 'Phiếu kiểm kê nguồn', type: 'Link', linkTo: 'SC Inventory Count Sheet' },
        { name: 'expense_account', label: 'TK chi phí điều chỉnh', type: 'Link', linkTo: 'SC GL Account' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
      { title: 'Điều tra', fields: [
        { name: 'investigation_notes', label: 'Ghi chú điều tra', type: 'Small Text',
          hint: 'Bắt buộc khi |Δ giá trị| > Settings.large_variance_threshold' },
      ]},
    ],
    items: {
      field: 'items', label: 'Items điều chỉnh',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '20%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '15%' },
        { name: 'system_qty', label: 'SL hệ thống', type: 'Float', width: '14%' },
        { name: 'actual_qty', label: 'SL thực tế', type: 'Float', required: true, width: '14%' },
        { name: 'valuation_rate', label: 'Đơn giá', type: 'Currency', width: '12%' },
        { name: 'reason', label: 'Lý do', type: 'Select',
          options: ['Counting Error', 'Damage', 'Theft', 'Expiry', 'Other'], width: '15%' },
      ],
    },
  },

  // ============================================================
  // M10 Traceability
  // ============================================================
  'SC Recall Notice': {
    sections: [
      { title: 'Thông báo thu hồi', fields: [
        { name: 'recall_date', label: 'Ngày thu hồi', type: 'Date', required: true, default: 'today' },
        { name: 'recall_type', label: 'Loại', type: 'Select',
          options: ['Voluntary', 'Mandatory', 'Precautionary'], default: 'Voluntary' },
        { name: 'severity', label: 'Mức độ', type: 'Select',
          options: ['Class I (Critical)', 'Class II (High)', 'Class III (Low)'], default: 'Class II (High)' },
        { name: 'item', label: 'Vật tư', type: 'Link', linkTo: 'SC Item', required: true },
        { name: 'batch_no', label: 'Lô', type: 'Link', linkTo: 'SC Batch', required: true },
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier' },
      ]},
      { title: 'Lý do', fields: [
        { name: 'recall_reason', label: 'Lý do thu hồi', type: 'Small Text', required: true },
        { name: 'regulatory_reference', label: 'Tham chiếu pháp lý', type: 'Data',
          hint: 'VD: CV BYT số ..., TT ...' },
      ]},
    ],
  },

  'SC Investigation Report': {
    sections: [
      { title: 'Điều tra', fields: [
        { name: 'investigation_date', label: 'Ngày bắt đầu', type: 'Date', required: true, default: 'today' },
        { name: 'investigation_type', label: 'Loại sự cố', type: 'Select',
          options: ['Stock Loss', 'Discrepancy', 'Fraud', 'System Error', 'Other'], default: 'Discrepancy' },
      ]},
      { title: 'Phạm vi', fields: [
        { name: 'item', label: 'Vật tư', type: 'Link', linkTo: 'SC Item' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'batch', label: 'Batch', type: 'Link', linkTo: 'SC Batch' },
        { name: 'period_start', label: 'Từ ngày', type: 'Date', required: true },
        { name: 'period_end', label: 'Đến ngày', type: 'Date', required: true, default: 'today' },
        { name: 'filter_user', label: 'Filter user', type: 'Link', linkTo: 'User' },
      ]},
      { title: 'Mô tả & Kết luận', fields: [
        { name: 'description', label: 'Mô tả phát hiện', type: 'Small Text' },
        { name: 'actual_qty', label: 'SL thực tế (manual count)', type: 'Float' },
        { name: 'recommendation', label: 'Biện pháp khắc phục', type: 'Long Text' },
        { name: 'conclusion', label: 'Kết luận', type: 'Long Text' },
      ]},
    ],
  },

  // ============================================================
  // M11 Alerts
  // ============================================================
  'SC Alert Rule': {
    sections: [
      { title: 'Quy tắc', fields: [
        { name: 'title', label: 'Tiêu đề', type: 'Data', required: true },
        { name: 'alert_type', label: 'Loại cảnh báo', type: 'Select', required: true,
          options: ['low_stock', 'expiring_batch', 'contract_expiring', 'fc_remaining_low',
                     'overdue_payment', 'qc_pending', 'recall_outstanding'] },
        { name: 'severity', label: 'Mức độ', type: 'Select',
          options: ['Critical', 'Warning', 'Info'], default: 'Warning' },
        { name: 'enabled', label: 'Bật', type: 'Check', default: 1 },
      ]},
      { title: 'Tần suất', fields: [
        { name: 'frequency', label: 'Tần suất', type: 'Select',
          options: ['Daily', 'Hourly', 'Realtime', 'Weekly'], default: 'Daily' },
        { name: 'scheduled_time', label: 'Giờ chạy', type: 'Time', default: '08:00:00' },
        { name: 'day_of_week', label: 'Thứ', type: 'Select',
          options: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], default: 'Mon' },
      ]},
      { title: 'Ngưỡng', fields: [
        { name: 'threshold_value', label: 'Giá trị ngưỡng', type: 'Float', default: 30 },
        { name: 'threshold_operator', label: 'Phép so sánh', type: 'Select',
          options: ['<', '<=', '=', '>=', '>'], default: '<=' },
        { name: 'threshold_unit', label: 'Đơn vị', type: 'Select',
          options: ['days', 'percent', 'VND', 'qty'], default: 'days' },
      ]},
      { title: 'Kênh', fields: [
        { name: 'channel_email', label: 'Email', type: 'Check', default: 1 },
        { name: 'channel_inapp', label: 'In-app', type: 'Check', default: 1 },
        { name: 'channel_sms', label: 'SMS', type: 'Check', default: 0 },
        { name: 'sms_phones', label: 'Số điện thoại SMS (phẩy)', type: 'Small Text', dependOn: 'channel_sms' },
      ]},
      { title: 'Người nhận', fields: [
        { name: 'recipient_roles', label: 'Roles (phẩy)', type: 'Small Text' },
        { name: 'extra_emails', label: 'Email bổ sung (phẩy)', type: 'Small Text' },
      ]},
    ],
  },
}
