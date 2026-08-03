// Form schemas — fields cho create/edit từng doctype
// Field type: Data | Text | Small Text | Long Text | Int | Float | Currency
//            Percent | Date | Datetime | Time | Check | Select | Link
//
// Item schemas dùng cho child table

export const FORM_SCHEMAS = {
  // ============================================================
  // M0 Master Data
  // ============================================================
  'SC Item': {
    sections: [
      { title: 'Thông tin vật tư', fields: [
        { name: 'item_code', label: 'Mã VT', type: 'Data', required: true },
        { name: 'item_name', label: 'Tên VT', type: 'Data', required: true },
        { name: 'item_group', label: 'Nhóm vật tư', type: 'Link', linkTo: 'SC Item Group' },
        { name: 'uom', label: 'Đơn vị tồn kho', type: 'Link', linkTo: 'SC UOM', required: true },
      ]},
      { title: 'Cấu hình', fields: [
        { name: 'is_stock_item', label: 'Quản lý tồn kho', type: 'Check', default: 1 },
        { name: 'has_batch_no', label: 'Có quản lý lô', type: 'Check' },
        { name: 'safety_stock', label: 'Tồn kho an toàn', type: 'Float' },
        { name: 'reorder_level', label: 'Mức tái đặt', type: 'Float' },
        { name: 'disabled', label: 'Vô hiệu hoá', type: 'Check' },
      ]},
      { title: 'Đơn vị kép (BR-BH-03)', fields: [
        { name: 'buy_uom', label: 'Đơn vị mua (mặc định)', type: 'Link', linkTo: 'SC UOM',
          hint: 'Đơn vị dùng khi mua — vd Hộp/Thùng' },
        { name: 'use_uom', label: 'Đơn vị sử dụng (mặc định)', type: 'Link', linkTo: 'SC UOM' },
      ]},
    ],
    items: {
      field: 'uom_conversions',
      label: 'Quy đổi đơn vị kép — 1 đơn vị = ? đơn vị tồn kho (vd 1 Hộp = 50 Cái, 1 Thùng = 100 Cái)',
      columns: [
        { name: 'uom', label: 'Đơn vị', type: 'Link', linkTo: 'SC UOM', required: true, width: '50%' },
        { name: 'conversion_factor', label: '= ? đơn vị tồn kho', type: 'Float', required: true, width: '50%' },
      ],
    },
  },
  'SC Item Group': {
    sections: [
      { title: 'Nhóm vật tư', fields: [
        { name: 'group_name', label: 'Tên nhóm', type: 'Data', required: true },
        { name: 'parent_group', label: 'Nhóm cha', type: 'Link', linkTo: 'SC Item Group' },
        { name: 'is_group', label: 'Là nhóm chứa nhóm con', type: 'Check' },
        { name: 'description', label: 'Mô tả', type: 'Small Text' },
      ]},
    ],
  },
  'SC UOM': {
    sections: [
      { title: 'Đơn vị tính', fields: [
        { name: 'uom_name', label: 'Tên UOM', type: 'Data', required: true },
        { name: 'must_be_whole_number', label: 'Bắt buộc số nguyên', type: 'Check', default: 1 },
      ]},
    ],
  },
  'SC Supplier': {
    sections: [
      { title: 'Thông tin NCC', fields: [
        { name: 'supplier_name', label: 'Tên NCC', type: 'Data', required: true },
        { name: 'tax_id', label: 'Mã số thuế', type: 'Data', required: true },
        { name: 'supplier_type', label: 'Loại NCC', type: 'Select', required: true,
          options: [
            { value: 'Nhà sản xuất', label: 'Nhà sản xuất' },
            { value: 'Nhà phân phối', label: 'Nhà phân phối' },
            { value: 'Đại lý', label: 'Đại lý' },
            { value: 'Khác', label: 'Khác' },
          ], default: 'Nhà phân phối' },
        { name: 'default_item_group', label: 'Nhóm vật tư chính', type: 'Link', linkTo: 'SC Item Group' },
      ]},
      { title: 'Liên hệ', fields: [
        { name: 'email_id', label: 'Email', type: 'Data', required: true },
        { name: 'mobile_no', label: 'Điện thoại', type: 'Data', required: true },
        { name: 'address', label: 'Địa chỉ', type: 'Small Text', required: true },
        { name: 'province', label: 'Tỉnh/Thành phố', type: 'Data',
          hint: 'VD: Hà Nội, TP.HCM, Đà Nẵng' },
      ]},
      { title: 'Thanh toán', fields: [
        { name: 'payment_terms', label: 'Điều khoản thanh toán', type: 'Select',
          options: [
            { value: 'Net 30', label: 'Net 30 (trả sau 30 ngày)' },
            { value: 'Net 60', label: 'Net 60 (trả sau 60 ngày)' },
            { value: 'Net 90', label: 'Net 90 (trả sau 90 ngày)' },
            { value: 'COD', label: 'COD (trả ngay)' },
            { value: '50/50', label: '50/50 (đặt cọc 50%)' },
            { value: 'Khác', label: 'Khác' },
          ] },
        { name: 'credit_limit', label: 'Hạn mức tín dụng (VND)', type: 'Currency' },
        { name: 'bank_name', label: 'Ngân hàng', type: 'Data',
          hint: 'VD: Vietcombank, BIDV, Techcombank' },
        { name: 'bank_account_no', label: 'Số tài khoản', type: 'Data' },
      ]},
      { title: 'Giấy tờ pháp lý', fields: [
        { name: 'gpkd_no', label: 'Số GPKD', type: 'Data', hint: 'Giấy phép kinh doanh' },
        { name: 'gpp_certificate_no', label: 'Số GPP/GDP', type: 'Data' },
        { name: 'gpp_expiry', label: 'Hết hạn GPP', type: 'Date' },
        { name: 'iso_certificate_no', label: 'Số ISO', type: 'Data' },
      ]},
      { title: 'Đánh giá & Trạng thái', fields: [
        { name: 'rating', label: 'Điểm trung bình (0-5)', type: 'Float', readonly: true },
        { name: 'disabled', label: 'Vô hiệu hoá', type: 'Check' },
        { name: 'blacklist_flag', label: 'Blacklist (chặn tạo PO mới)', type: 'Check' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
  },
  'SC Warehouse': {
    sections: [
      { title: 'Kho', fields: [
        { name: 'warehouse_name', label: 'Tên kho', type: 'Data', required: true },
        { name: 'warehouse_type', label: 'Loại kho', type: 'Select',
          options: [
            { value: 'Main', label: 'Kho chính' },
            { value: 'Sub', label: 'Kho phụ' },
            { value: 'Department', label: 'Kho khoa phòng' },
            { value: 'Quarantine', label: 'Kho cách ly' },
            { value: 'Transit', label: 'Kho trung chuyển' },
          ] },
        { name: 'parent_warehouse', label: 'Kho cha', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'is_group', label: 'Là nhóm', type: 'Check' },
        { name: 'disabled', label: 'Vô hiệu hoá', type: 'Check' },
      ]},
      { title: 'Thông tin liên hệ', fields: [
        { name: 'address', label: 'Địa chỉ', type: 'Small Text' },
        { name: 'phone', label: 'Điện thoại', type: 'Data' },
      ]},
    ],
  },
  'Bin Location': {
    sections: [
      { title: 'Vị trí lưu trữ', fields: [
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'bin_code', label: 'Mã vị trí (code)', type: 'Data', required: true,
          hint: 'VD: A-01-03-02 (Khu-Hàng-Kệ-Tầng)' },
        { name: 'description', label: 'Mô tả', type: 'Data' },
        { name: 'enabled', label: 'Hiệu lực', type: 'Check', default: 1 },
        { name: 'is_quarantine', label: 'Vị trí cách ly (Quarantine)', type: 'Check',
          hint: 'Hàng QC chưa duyệt' },
      ]},
      { title: 'Sơ đồ kho (tuỳ chọn)', fields: [
        { name: 'zone', label: 'Khu (Zone)', type: 'Data' },
        { name: 'aisle', label: 'Hàng (Aisle)', type: 'Data' },
        { name: 'rack', label: 'Kệ (Rack)', type: 'Data' },
        { name: 'shelf', label: 'Tầng (Shelf)', type: 'Data' },
        { name: 'level', label: 'Mức (Level)', type: 'Data' },
      ]},
      { title: 'Sức chứa & sử dụng', fields: [
        { name: 'capacity_qty', label: 'Sức chứa', type: 'Float' },
        { name: 'capacity_uom', label: 'ĐVT sức chứa', type: 'Link', linkTo: 'SC UOM' },
        { name: 'current_qty', label: 'Hiện đang chứa', type: 'Float', readonly: true,
          hint: 'Tự cập nhật từ Stock Ledger' },
        { name: 'occupancy_pct', label: 'Tỷ lệ đầy (%)', type: 'Percent', readonly: true },
        { name: 'status', label: 'Trạng thái', type: 'Select',
          options: [
            { value: 'Empty', label: 'Trống' },
            { value: 'In Use', label: 'Đang dùng' },
            { value: 'Full', label: 'Đầy' },
          ], default: 'Empty' },
      ]},
      { title: 'Điều kiện bảo quản', fields: [
        { name: 'temperature_controlled', label: 'Kiểm soát nhiệt độ', type: 'Check' },
        { name: 'min_temperature', label: 'Nhiệt độ tối thiểu (°C)', type: 'Float',
          dependOn: 'temperature_controlled' },
        { name: 'max_temperature', label: 'Nhiệt độ tối đa (°C)', type: 'Float',
          dependOn: 'temperature_controlled' },
      ]},
      { title: 'Khác', fields: [
        { name: 'barcode', label: 'Barcode', type: 'Data' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
  },
  'SC Department': {
    sections: [
      { title: 'Khoa phòng', fields: [
        { name: 'department_name', label: 'Tên khoa', type: 'Data', required: true },
        { name: 'department_code', label: 'Mã khoa', type: 'Data' },
        { name: 'department_type', label: 'Loại', type: 'Select',
          options: [
            { value: 'Clinical', label: 'Lâm sàng' },
            { value: 'Surgical', label: 'Phẫu thuật' },
            { value: 'Lab', label: 'Xét nghiệm' },
            { value: 'Pharmacy', label: 'Dược' },
            { value: 'Admin', label: 'Hành chính' },
            { value: 'Other', label: 'Khác' },
          ] },
        { name: 'disabled', label: 'Vô hiệu hoá', type: 'Check' },
      ]},
    ],
  },
  'SC GL Account': {
    sections: [
      { title: 'Tài khoản kế toán', fields: [
        { name: 'account_code', label: 'Số tài khoản (VAS)', type: 'Data', required: true,
          hint: 'VD: 152, 331, 642, 1121, 1331' },
        { name: 'account_name', label: 'Tên tài khoản', type: 'Data', required: true },
        { name: 'account_type', label: 'Loại TK', type: 'Select',
          options: [
            { value: 'Asset', label: 'Tài sản' },
            { value: 'Liability', label: 'Nợ phải trả' },
            { value: 'Equity', label: 'Vốn chủ sở hữu' },
            { value: 'Revenue', label: 'Doanh thu' },
            { value: 'Expense', label: 'Chi phí' },
          ] },
        { name: 'parent_account', label: 'TK cha', type: 'Link', linkTo: 'SC GL Account' },
        { name: 'is_group', label: 'Là nhóm', type: 'Check' },
        { name: 'disabled', label: 'Vô hiệu hoá', type: 'Check' },
      ]},
    ],
  },

  // ============================================================
  // M1 Contract
  // ============================================================
  'Framework Contract': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'supplier', label: 'Nhà cung cấp', type: 'Link', linkTo: 'SC Supplier', required: true },
        { name: 'contract_number', label: 'Tên / Số hợp đồng', type: 'Data', required: true,
          hint: 'Tên hoặc số hợp đồng (vd: HĐ-2026-NCC-A001)' },
        { name: 'contract_date', label: 'Ngày ký', type: 'Date', required: true,
          hint: 'Chọn ngày ký → tự điền Hiệu lực từ = ngày ký, Hết hạn = +1 năm (vẫn sửa được)',
          derive: [{ target: 'valid_from', op: 'copy' }, { target: 'valid_to', op: 'plus1year' }] },
        { name: 'valid_from', label: 'Hiệu lực từ', type: 'Date', required: true },
        { name: 'valid_to', label: 'Hết hạn', type: 'Date', required: true },
      ]},
      { title: 'Giá trị', fields: [
        { name: 'total_value', label: 'Tổng giá trị (VND)', type: 'Currency', readonly: true,
          hint: 'Tự động tính = Σ thành tiền các dòng vật tư bên dưới' },
        { name: 'payment_terms', label: 'Điều khoản thanh toán', type: 'Data' },
        { name: 'delivery_terms', label: 'Điều khoản giao hàng', type: 'Small Text' },
      ]},
      { title: 'Tệp đính kèm & người tạo', fields: [
        { name: 'attachments', label: 'Tài liệu hợp đồng (1 hoặc nhiều tệp)', type: 'AttachMultiple',
          hint: 'Có thể chọn nhiều tệp cùng lúc hoặc thêm dần (PDF/ảnh/Word)' },
        { name: 'owner', label: 'Người tạo', type: 'Data', readonly: true,
          hint: 'Tự động ghi user tạo HĐ — không sửa được' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Danh mục vật tư',
      itemField: 'item_code',
      columns: [
        { name: 'item_code', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          scope: { itemField: 'item_code' },
          fetchFrom: { source: 'item_code', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'contract_qty', label: 'SL HĐ', type: 'Float', required: true, width: '15%' },
        { name: 'unit_price', label: 'Đơn giá', type: 'Currency', required: true, width: '18%' },
        { name: 'total_amount', label: 'Thành tiền', type: 'Currency', readonly: true, width: '20%',
          compute: { from: ['contract_qty', 'unit_price'], op: 'mul' } },
      ],
      detail: { groups: [
        { title: 'Thông tin vật tư', icon: 'package', fields: [
          { name: 'item_code', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true },
          { name: 'item_name', label: 'Tên vật tư', type: 'Data', readonly: true },
          { name: 'uom', label: 'Đơn vị tính', type: 'Link', linkTo: 'SC UOM', required: true, scope: { itemField: 'item_code' } },
        ]},
        { title: 'Số lượng & giá', icon: 'banknote', fields: [
          { name: 'contract_qty', label: 'SL hợp đồng', type: 'Float', required: true },
          { name: 'unit_price', label: 'Đơn giá', type: 'Currency', required: true },
          { name: 'total_amount', label: 'Thành tiền', type: 'Currency', readonly: true, compute: { from: ['contract_qty', 'unit_price'], op: 'mul' } },
          { name: 'ordered_qty', label: 'SL đã đặt', type: 'Float', readonly: true },
          { name: 'remaining_qty', label: 'SL còn lại', type: 'Float', readonly: true },
        ]},
        { title: 'Truy vết NCC', icon: 'truck', fields: [
          { name: 'supplier_item_name', label: 'Tên hàng theo NCC', type: 'Data' },
          { name: 'supplier_item_code', label: 'Mã hàng theo NCC', type: 'Data' },
        ]},
        { title: 'Ghi chú dòng', icon: 'file-text', fields: [
          { name: 'remarks', label: 'Ghi chú dòng', type: 'Small Text' },
        ]},
      ]},
    },
  },

  'Release Order': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'framework_contract', label: 'Hợp đồng khung', type: 'Link', linkTo: 'Framework Contract', required: true,
          fetchFrom: { target_doctype: 'Framework Contract', target_field: 'supplier' },
          hint: 'Chọn HĐ khung Active — NCC tự điền theo hợp đồng. Để trống items để backend tự nạp vật tư còn hạn mức.' },
        { name: 'supplier', label: 'Nhà cung cấp', type: 'Link', linkTo: 'SC Supplier', readonly: true,
          hint: 'Tự lấy theo HĐ khung' },
        { name: 'release_date', label: 'Ngày lệnh', type: 'Date', required: true, default: 'today' },
        { name: 'required_by', label: 'Ngày cần giao', type: 'Date', required: true,
          hint: 'Không được trước ngày lệnh' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Danh mục vật tư cần gọi',
      columns: [
        { name: 'item_code', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          scope: { itemField: 'item_code' },
          fetchFrom: { source: 'item_code', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL gọi', type: 'Float', required: true, width: '15%' },
        { name: 'available_qty', label: 'Còn theo HĐK', type: 'Float', readonly: true, width: '15%' },
        { name: 'unit_price', label: 'Đơn giá HĐK', type: 'Currency', readonly: true, width: '18%',
          hint: 'Lấy theo hợp đồng khung — không sửa tay' },
        { name: 'amount', label: 'Thành tiền', type: 'Currency', readonly: true, width: '15%',
          compute: { from: ['qty', 'unit_price'], op: 'mul' } },
      ],
    },
  },

  // ============================================================
  // M2 Planning
  // ============================================================
  'Procurement Plan': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'plan_date', label: 'Ngày lập kế hoạch', type: 'Date', required: true, default: 'today' },
        { name: 'period_type', label: 'Kỳ kế hoạch', type: 'Select', required: true,
          options: [
            { value: 'Monthly', label: 'Hàng tháng' },
            { value: 'Quarterly', label: 'Hàng quý' },
            { value: 'Yearly', label: 'Hàng năm' },
            { value: 'Adhoc', label: 'Đột xuất' },
          ], default: 'Monthly' },
        { name: 'from_date', label: 'Từ ngày', type: 'Date', required: true },
        { name: 'to_date', label: 'Đến ngày', type: 'Date', required: true },
        { name: 'required_by', label: 'Ngày cần hàng', type: 'Date',
          hint: 'Sẽ truyền sang Material Request khi tạo' },
      ]},
      { title: 'Phạm vi & tham số tính', fields: [
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'consumption_lookback_months', label: 'Số tháng lịch sử tính bình quân', type: 'Int', default: 3,
          hint: 'Lấy bình quân tiêu thụ N tháng gần nhất' },
        { name: 'safety_stock_factor', label: 'Hệ số safety stock (%)', type: 'Percent', default: 20,
          hint: '% bổ sung trên nhu cầu cơ bản' },
      ]},
      { title: 'Ngân sách', fields: [
        { name: 'budget', label: 'Ngân sách dự kiến (VND)', type: 'Currency',
          hint: 'Để 0 nếu không kiểm soát ngân sách' },
        { name: 'total_estimated_cost', label: 'Tổng chi phí ước tính (VND)', type: 'Currency', readonly: true,
          hint: 'Tự tính = Σ thành tiền các dòng' },
        { name: 'budget_acknowledged', label: 'Xác nhận vượt ngân sách', type: 'Check',
          hint: 'Bắt buộc tick nếu tổng chi phí vượt ngân sách mới submit được' },
        { name: 'auto_create_mr', label: 'Tự tạo Material Request sau Submit', type: 'Check' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Danh mục vật tư cần mua',
      columns: [
        { name: 'item_code', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '18%' },
        { name: 'item_name', label: 'Tên', type: 'Data', readonly: true, width: '15%',
          fetchFrom: { source: 'item_code', target_doctype: 'SC Item', target_field: 'item_name' } },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', width: '8%',
          scope: { itemField: 'item_code' },
          fetchFrom: { source: 'item_code', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'current_stock', label: 'Tồn hiện tại', type: 'Float', readonly: true, width: '10%' },
        { name: 'avg_monthly_consumption', label: 'Tiêu thụ/tháng', type: 'Float', readonly: true, width: '10%' },
        { name: 'planned_qty', label: 'SL dự kiến mua', type: 'Float', required: true, width: '11%' },
        { name: 'estimated_unit_cost', label: 'Đơn giá ƯT', type: 'Currency', width: '13%' },
        { name: 'estimated_amount', label: 'Thành tiền', type: 'Currency', readonly: true, width: '13%',
          compute: { from: ['planned_qty', 'estimated_unit_cost'], op: 'mul' } },
      ],
    },
  },

  'SC Material Request': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'request_type', label: 'Loại', type: 'Select', required: true,
          options: [
            { value: 'Purchase', label: 'Mua hàng' },
            { value: 'Material Transfer', label: 'Chuyển kho' },
            { value: 'Material Issue', label: 'Xuất kho' },
          ], default: 'Purchase' },
        { name: 'transaction_date', label: 'Ngày tạo', type: 'Date', required: true, default: 'today' },
        { name: 'schedule_date', label: 'Ngày cần', type: 'Date', required: true, warnPastDate: true },
        { name: 'warehouse', label: 'Kho nhận', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'customer', label: 'Khách hàng yêu cầu', type: 'Link', linkTo: 'SC Customer' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '22%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '12%' },
        { name: 'framework_contract', label: 'HĐ khung', type: 'Link', linkTo: 'Framework Contract', width: '18%',
          scope: { itemField: 'item' } },
        { name: 'estimated_unit_cost', label: 'Đơn giá ƯT', type: 'Currency', width: '18%' },
        { name: 'schedule_date', label: 'Ngày cần', type: 'Date', width: '15%',
          inheritFrom: 'schedule_date', warnPastDate: true },
      ],
    },
  },

  'SC Purchase Order': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier', required: true,
          readonlyWhenSet: 'framework_contract',
          hint: 'Khi đã chọn HĐ khung, NCC bị khoá theo hợp đồng — bấm "Đặt lại" để chọn NCC khác' },
        { name: 'transaction_date', label: 'Ngày PO', type: 'Date', required: true, default: 'today' },
        { name: 'schedule_date', label: 'Ngày giao DK', type: 'Date', required: true },
        { name: 'framework_contract', label: 'HĐ khung', type: 'Link', linkTo: 'Framework Contract',
          readonlyWhenSet: 'framework_contract',
          fetchFrom: { target_doctype: 'Framework Contract', target_field: 'supplier' },
          hint: 'Chọn HĐ khung sẽ tự điền & khoá NCC. Bấm "Đặt lại" để chọn HĐ khung khác' },
        { name: 'delivery_terms', label: 'Điều khoản giao', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      itemField: 'item',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', required: true, width: '20%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true, width: '15%' },
        { name: 'schedule_date', label: 'Ngày giao', type: 'Date', width: '15%' },
      ],
      detail: { groups: [
        { title: 'Thông tin vật tư', icon: 'package', fields: [
          { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true },
          { name: 'item_name', label: 'Tên vật tư', type: 'Data', readonly: true },
          { name: 'uom', label: 'Đơn vị tính', type: 'Link', linkTo: 'SC UOM', required: true, scope: { itemField: 'item' } },
        ]},
        { title: 'Số lượng & giá', icon: 'banknote', fields: [
          { name: 'qty', label: 'SL đặt', type: 'Float', required: true },
          { name: 'rate', label: 'Đơn giá', type: 'Currency', required: true },
          { name: 'amount', label: 'Thành tiền', type: 'Currency', readonly: true, compute: { from: ['qty', 'rate'], op: 'mul' } },
          { name: 'received_qty', label: 'SL đã nhận', type: 'Float', readonly: true },
          { name: 'warehouse', label: 'Kho nhận', type: 'Link', linkTo: 'SC Warehouse' },
          { name: 'schedule_date', label: 'Ngày giao', type: 'Date' },
        ]},
        { title: 'Truy vết NCC', icon: 'truck', fields: [
          { name: 'supplier_item_name', label: 'Tên hàng theo NCC', type: 'Data' },
          { name: 'supplier_item_code', label: 'Mã hàng theo NCC', type: 'Data' },
        ]},
        { title: 'Ghi chú dòng', icon: 'file-text', fields: [
          { name: 'remarks', label: 'Ghi chú dòng', type: 'Small Text' },
        ]},
      ]},
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
        { name: 'no_po_reason', label: 'Lý do nhập không PO', type: 'Small Text',
          dependOn: 'eval:!doc.purchase_order && !doc.is_return',
          hint: 'Bắt buộc khi nhập kho không có PO tham chiếu' },
        { name: 'over_receipt_acknowledged', label: 'Manager xác nhận nhận vượt', type: 'Check',
          dependOn: 'eval:doc.has_over_receipt',
          hint: 'Bắt buộc xác nhận khi SL nhận vượt SL đặt trên PO' },
        { name: 'qc_required', label: 'Yêu cầu QC', type: 'Check', default: 1 },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '20%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL nhận', type: 'Float', required: true, width: '12%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', width: '15%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '15%' },
        { name: 'supplier_batch_no', label: 'Số lô NCC', type: 'Data', width: '13%' },
        { name: 'expiry_date', label: 'HD', type: 'Date', width: '15%', required: true },
        // Nhập lúc nhận hàng — sẽ in lên nhãn lô (model/xuất xứ/NSX)
        { name: 'manufacturing_date', label: 'Ngày SX', type: 'Date', width: '15%' },
        { name: 'manufacturer', label: 'NSX', type: 'Data', width: '13%' },
        { name: 'country_of_origin', label: 'Xuất xứ', type: 'Data', width: '13%' },
        { name: 'model', label: 'Model', type: 'Data', width: '13%' },
      ],
    },
  },

  // ============================================================
  // M3 Quality Inspection — sửa kết quả KCS
  // ============================================================
  'SC Quality Inspection': {
    sections: [
      { title: 'Thông tin kiểm', fields: [
        { name: 'inspection_date', label: 'Ngày kiểm', type: 'Date', required: true, default: 'today' },
        { name: 'purchase_receipt', label: 'Phiếu nhập', type: 'Link', linkTo: 'SC Purchase Receipt', required: true,
          readonly: true, hint: 'Phiếu QC tạo tự động từ phiếu nhập — không sửa',
          fetchFrom: { target_doctype: 'SC Purchase Receipt', target_field: 'supplier' } },
        { name: 'supplier', label: 'Nhà cung cấp', type: 'Link', linkTo: 'SC Supplier', readonly: true,
          hint: 'Tự fetch từ Phiếu nhập' },
        { name: 'item', label: 'Vật tư', type: 'Link', linkTo: 'SC Item', required: true, readonly: true,
          fetchFrom: { target_doctype: 'SC Item', target_field: 'item_name' } },
        { name: 'item_name', label: 'Tên vật tư', type: 'Data', readonly: true },
        { name: 'batch', label: 'Lô (hệ thống)', type: 'Link', linkTo: 'SC Batch', readonly: true,
          hint: 'Mã lô hệ thống tự sinh — lấy theo phiếu nhập' },
        { name: 'supplier_batch_no', label: 'Số lô NCC', type: 'Data', readonly: true,
          hint: 'Số lô in trên hàng của nhà cung cấp — phân biệt với lô hệ thống' },
        { name: 'received_qty', label: 'SL nhận', type: 'Float', readonly: true,
          hint: 'Lấy từ phiếu nhập — QC chỉ kết luận Đạt/Không đạt' },
        { name: 'inspected_by', label: 'Người kiểm', type: 'Link', linkTo: 'User', readonly: true,
          hint: 'Tự ghi nhận theo người kết luận QC' },
      ]},
      { title: 'Kết quả', fields: [
        { name: 'manual_inspection', label: 'Kiểm thủ công', type: 'Check' },
        // GĐ MVL — bỏ "Kết quả tổng" (trùng với Hành động). Kết luận QC chọn 1 nơi
        // duy nhất ở đây; hệ thống tự suy Đạt/Không đạt cho lô & phiếu nhập.
        { name: 'action_taken', label: 'Kết luận QC (Hành động)', type: 'Select', required: true,
          hint: 'Chấp nhận → hàng đạt; Trả NCC / Yêu cầu đổi hàng → hàng không đạt',
          options: [
            { value: 'Pending', label: 'Chờ xử lý' },
            { value: 'Accept', label: 'Chấp nhận (Đạt)' },
            { value: 'Conditional Accept', label: 'Chấp nhận có điều kiện' },
            { value: 'Return to Supplier', label: 'Trả NCC (Không đạt)' },
            { value: 'Request Replacement', label: 'Yêu cầu đổi hàng (Không đạt)' },
          ] },
        { name: 'remarks', label: 'Ghi chú KCS', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'readings', label: 'Tiêu chí kiểm tra',
      // Bỏ QC Checklist Template: hiện sẵn 5 tiêu chí QC nhập kho mẫu để KCS tick (thêm/bớt được).
      // Giữ ĐỒNG BỘ với backend sc_purchase_receipt.py::_DEFAULT_QI_CRITERIA.
      defaultRows: [
        { specification: 'Bao bì, nhãn mác nguyên vẹn, đầy đủ thông tin', status: '' },
        { specification: 'Số lô khớp chứng từ', status: '' },
        { specification: 'Hạn sử dụng còn đủ theo quy định', status: '' },
        { specification: 'Quy cách, số lượng đúng đặt hàng', status: '' },
        { specification: 'Cảm quan đạt (màu sắc, hình thức, không hư hỏng/biến chất)', status: '' },
      ],
      bulkActions: [
        { label: 'Accept tất cả', variant: 'success', set: { status: 'Accepted' } },
        { label: 'Reject tất cả', variant: 'danger',  set: { status: 'Rejected' } },
      ],
      columns: [
        { name: 'specification', label: 'Tiêu chí', type: 'Data', required: true, width: '30%' },
        { name: 'value', label: 'Giá trị đo', type: 'Data', width: '25%' },
        { name: 'status', label: 'Kết quả', type: 'Select',
          options: [
            { value: 'Pending', label: 'Chờ' },
            { value: 'Accepted', label: 'Đạt' },
            { value: 'Rejected', label: 'Không đạt' },
          ], required: true, width: '15%' },
        { name: 'is_critical', label: 'Tới hạn', type: 'Check', width: '10%' },
        { name: 'remarks', label: 'Ghi chú', type: 'Data', width: '20%' },
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
        { name: 'barcode', label: 'Barcode lô', type: 'Data',
          hint: 'Tự sinh = Mã lô khi lưu. Để trống nếu muốn dùng mã lô.' },
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true },
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier' },
        { name: 'supplier_batch_no', label: 'Số lô NCC', type: 'Data' },
        { name: 'manufacturing_date', label: 'Ngày SX', type: 'Date' },
        { name: 'expiry_date', label: 'Hạn dùng', type: 'Date', required: true },
        { name: 'manufacturer', label: 'NSX', type: 'Data' },
        { name: 'country_of_origin', label: 'Xuất xứ', type: 'Data' },
        { name: 'model', label: 'Model', type: 'Data' },
      ]},
      { title: 'Trạng thái', fields: [
        { name: 'qc_status', label: 'QC', type: 'Select',
          options: [
            { value: 'Pending', label: 'Chờ' },
            { value: 'Accepted', label: 'Đạt' },
            { value: 'Rejected', label: 'Không đạt' },
          ], default: 'Pending' },
        { name: 'expiry_warning_ack', label: 'Xác nhận nhập lô hạn ngắn', type: 'Check' },
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
        { name: 'required_by', label: 'Cần trước ngày', type: 'Date', required: true, default: 'today' },
        { name: 'transfer_type', label: 'Loại yêu cầu', type: 'Select', required: true,
          options: [
            { value: 'Routine', label: 'Thường quy' },
            { value: 'Urgent', label: 'Khẩn cấp' },
            { value: 'Replenishment', label: 'Bổ sung' },
            { value: 'Return to Main', label: 'Trả về kho chính' },
          ], default: 'Routine' },
        { name: 'requested_by', label: 'Người yêu cầu', type: 'Link', linkTo: 'User' },
      ]},
      { title: 'Kho', fields: [
        { name: 'from_warehouse', label: 'Kho nguồn', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'to_warehouse', label: 'Kho đích', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'requested_qty', label: 'SL yêu cầu', type: 'Float', required: true, width: '15%' },
        { name: 'approved_qty', label: 'SL duyệt', type: 'Float', width: '15%' },
        { name: 'batch', label: 'Lô (nếu chỉ định)', type: 'Link', linkTo: 'SC Batch', width: '23%',
          scope: { itemField: 'item' } },
      ],
    },
  },

  'SC Stock Entry': {
    sections: [
      { title: 'Thông tin', fields: [
        { name: 'entry_type', label: 'Loại GT', type: 'Select', required: true,
          options: [
            { value: 'Material Receipt', label: 'Nhập kho' },
            { value: 'Material Issue', label: 'Xuất kho' },
            { value: 'Material Transfer', label: 'Chuyển kho' },
            { value: 'Manufacture', label: 'Sản xuất' },
            { value: 'Repack', label: 'Đóng gói lại' },
          ],
          default: 'Material Transfer' },
        { name: 'posting_date', label: 'Ngày', type: 'Date', required: true, default: 'today' },
        { name: 'from_warehouse', label: 'Kho nguồn', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'to_warehouse', label: 'Kho đích', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'purpose', label: 'Mục đích', type: 'Data' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '22%',
          scope: { warehouseField: 'from_warehouse', warehouseFromParent: true } },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'valuation_rate', label: 'Đơn giá', type: 'Currency', width: '18%', readonly: true },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '20%',
          scope: { itemField: 'item' } },
        { name: 'fefo_override', label: 'Bỏ qua FEFO', type: 'Check', width: '15%' },
      ],
    },
  },

  // ============================================================
  // M7 Sales
  // ============================================================
  'SC Customer': {
    sections: [
      { title: 'Thông tin khách hàng', fields: [
        { name: 'customer_name', label: 'Tên khách hàng', type: 'Data', required: true },
        { name: 'tax_code', label: 'Mã số thuế', type: 'Data', required: true },
        { name: 'email', label: 'Tài khoản đăng nhập (email)', type: 'Data',
          hint: 'Email khách dùng để đăng nhập cổng — sẽ tạo tài khoản Portal khi lưu' },
        { name: 'portal_password', label: 'Mật khẩu Portal', type: 'Password',
          hint: 'Đặt mật khẩu đăng nhập cho khách (tối thiểu 6 ký tự). Cấp lại cho khách sau khi tạo. Không lưu lại trên hồ sơ.' },
        { name: 'phone', label: 'Điện thoại', type: 'Data' },
        { name: 'status', label: 'Trạng thái', type: 'Select', required: true,
          options: [
            { value: 'Tạm ngưng', label: 'Tạm ngưng' },
            { value: 'Hoạt động', label: 'Hoạt động' },
          ], default: 'Tạm ngưng',
          hint: 'Khách hàng mới mặc định Tạm ngưng — chỉ chuyển Hoạt động sau khi có tài khoản Portal' },
        { name: 'credit_limit', label: 'Hạn mức nợ (VND)', type: 'Currency' },
        { name: 'payment_terms', label: 'Điều khoản thanh toán', type: 'Data' },
        { name: 'portal_user', label: 'Tài khoản Portal (tự tạo)', type: 'Data', readonly: true,
          hint: 'Tự tạo từ tài khoản + mật khẩu ở trên khi lưu — không cần chọn thủ công' },
      ]},
      { title: 'Địa chỉ', fields: [
        { name: 'billing_address', label: 'Địa chỉ hoá đơn', type: 'Small Text' },
        { name: 'shipping_address', label: 'Địa chỉ giao hàng', type: 'Small Text' },
      ]},
    ],
  },
  'SC Sales Framework Contract': {
    sections: [
      { title: 'Thông tin HĐ khung', fields: [
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer', required: true },
        { name: 'contract_number', label: 'Số hợp đồng', type: 'Data', required: true },
        { name: 'contract_date', label: 'Ngày ký', type: 'Date', required: true, default: 'today' },
        { name: 'valid_from', label: 'Hiệu lực từ', type: 'Date', required: true, default: 'today' },
        { name: 'valid_to', label: 'Hiệu lực đến', type: 'Date', required: true },
      ]},
      { title: 'Điều khoản', fields: [
        { name: 'payment_terms', label: 'Điều khoản thanh toán', type: 'Data' },
        { name: 'delivery_terms', label: 'Điều khoản giao hàng', type: 'Small Text' },
      ]},
      { title: 'Hồ sơ & Ghi chú', fields: [
        { name: 'attachment', label: 'File hợp đồng (PDF)', type: 'Attach' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '22%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'contract_qty', label: 'SL hợp đồng', type: 'Float', required: true, width: '15%' },
        { name: 'unit_price', label: 'Đơn giá', type: 'Currency', required: true, width: '18%' },
        { name: 'sold_qty', label: 'Đã bán', type: 'Float', width: '15%' },
        { name: 'remaining_qty', label: 'Còn lại', type: 'Float', width: '15%' },
      ],
    },
  },
  'SC Sales Order': {
    sections: [
      { title: 'Thông tin đơn bán', fields: [
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer', required: true,
          readonlyWhenSet: 'framework_contract',
          hint: 'Chọn khách trước sẽ lọc HĐ khung theo khách này' },
        { name: 'framework_contract', label: 'HĐ khung', type: 'Link', linkTo: 'SC Sales Framework Contract',
          // Lọc HĐ khung theo khách đã chọn (yêu cầu #5, chiều ngược)
          scope: { customerField: 'customer' },
          // Chọn HĐ khung → tự điền khách + nạp chi tiết vật tư (khoá lại; sửa qua nút Đặt lại)
          fetchFrom: { target_doctype: 'SC Sales Framework Contract', target_field: 'customer' },
          loadItemsFrom: {
            api: 'supplycore.api.sales.sales_framework_items',
            arg: 'framework_contract',
            // qty nạp sẵn = SL còn lại của HĐ khung (sửa được); giá theo HĐ
            map: { item: 'item', uom: 'uom', unit_price: 'unit_price', qty: 'remaining_qty' },
          },
          hint: 'Chọn HĐ khung sẽ tự điền khách + nạp vật tư & khoá — giá theo HĐ khung (BRU-SFC-002). Sửa: bấm Đặt lại.' },
        { name: 'order_date', label: 'Ngày đặt', type: 'Date', required: true, default: 'today' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      sumInto: { column: 'amount', target: 'total_amount' },
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%',
          lockable: true, scope: { salesFcField: 'framework_contract' } },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          lockable: true, scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'unit_price', label: 'Đơn giá', type: 'Currency', width: '18%', readonly: true,
          hint: 'Lấy theo HĐ khung (SFC) — không sửa tay' },
        { name: 'amount', label: 'Thành tiền', type: 'Currency', width: '18%', readonly: true,
          compute: { from: ['qty', 'unit_price'], op: 'mul' } },
      ],
    },
  },
  'SC Delivery Note': {
    sections: [
      { title: 'Thông tin giao hàng', fields: [
        { name: 'sales_order', label: 'SO tham chiếu', type: 'Link', linkTo: 'SC Sales Order', required: true },
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer' },
        { name: 'from_warehouse', label: 'Kho xuất', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'delivery_date', label: 'Ngày giao', type: 'Date', required: true, default: 'today' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '22%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL giao', type: 'Float', required: true, width: '15%' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '18%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '18%' },
      ],
    },
  },
  'SC Acceptance Record': {
    sections: [
      { title: 'Thông tin nghiệm thu', fields: [
        { name: 'delivery_note', label: 'DN tham chiếu', type: 'Link', linkTo: 'SC Delivery Note', required: true },
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer' },
        { name: 'acceptance_date', label: 'Ngày nghiệm thu', type: 'Date', required: true, default: 'today' },
        { name: 'accepted_by', label: 'Người nhận hàng', type: 'Data', required: true },
        { name: 'note', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
  },

  'SC Sales Invoice': {
    sections: [
      { title: 'Thông tin HD bán hàng', fields: [
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer', required: true },
        { name: 'delivery_note', label: 'DN tham chiếu (đã nghiệm thu)', type: 'Link', linkTo: 'SC Delivery Note', required: true },
        { name: 'invoice_date', label: 'Ngày HD', type: 'Date', required: true, default: 'today' },
        { name: 'tax_rate', label: 'Thuế suất (%)', type: 'Percent' },
      ]},
    ],
    items: {
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '30%' },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '20%' },
        { name: 'unit_price', label: 'Đơn giá', type: 'Currency', required: true, width: '25%' },
        { name: 'amount', label: 'Thành tiền', type: 'Currency', width: '25%' },
      ],
    },
  },
  'SC Sales Receipt': {
    sections: [
      { title: 'Thông tin thu tiền', fields: [
        { name: 'customer', label: 'Khách hàng', type: 'Link', linkTo: 'SC Customer', required: true },
        { name: 'sales_invoice', label: 'SI tham chiếu', type: 'Link', linkTo: 'SC Sales Invoice', required: true },
        { name: 'receipt_date', label: 'Ngày thu', type: 'Date', required: true, default: 'today' },
        { name: 'amount', label: 'Số tiền', type: 'Currency', required: true },
        { name: 'mode', label: 'Hình thức thu', type: 'Select',
          options: [
            { value: 'Chuyển khoản', label: 'Chuyển khoản' },
            { value: 'Tiền mặt', label: 'Tiền mặt' },
          ], default: 'Chuyển khoản' },
      ]},
    ],
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
      field: 'items', label: 'Chi tiết',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '25%' },
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '12%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'qty', label: 'SL', type: 'Float', required: true, width: '15%' },
        { name: 'rate', label: 'Đơn giá', type: 'Currency', required: true, width: '18%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '15%' },
        { name: 'purchase_receipt_item', label: 'Tham chiếu dòng PR', type: 'Data', width: '15%' },
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
          options: [
            { value: 'Bank Transfer', label: 'Chuyển khoản' },
            { value: 'Cash', label: 'Tiền mặt' },
            { value: 'Cheque', label: 'Séc' },
          ], default: 'Bank Transfer' },
        { name: 'bank_account', label: 'Tài khoản ngân hàng', type: 'Data' },
        { name: 'remarks', label: 'Ghi chú', type: 'Small Text' },
      ]},
    ],
    items: {
      field: 'references', label: 'Hóa đơn thanh toán',
      // Tổng "Số tiền phân bổ" của các dòng → tự điền vào "Số tiền" ở header
      sumInto: { column: 'allocated_amount', target: 'amount' },
      columns: [
        { name: 'purchase_invoice', label: 'Hóa đơn mua', type: 'Link', linkTo: 'SC Purchase Invoice', required: true, width: '50%' },
        { name: 'allocated_amount', label: 'Số tiền phân bổ', type: 'Currency', required: true, width: '50%' },
      ],
      // Chọn hóa đơn công nợ NCC (đã lọc còn phải trả, bỏ phiếu bị giữ) + xem trước
      picker: {
        buttonLabel: 'Chọn hóa đơn công nợ',
        title: 'Hóa đơn NCC còn phải trả',
        api: 'supplycore.m8_accounting.doctype.sc_payment_entry.sc_payment_entry.auto_load_outstanding_invoices',
        filterField: 'supplier',
        filterArg: 'supplier',
        rowKey: 'name',
        previewDoctype: 'SC Purchase Invoice',
        previewKey: 'name',
        emptyHint: 'Chọn Nhà cung cấp ở trên trước để nạp danh sách hóa đơn còn nợ',
        columns: [
          { key: 'name', label: 'Hóa đơn' },
          { key: 'supplier_invoice_no', label: 'Số HĐ NCC' },
          { key: 'invoice_date', label: 'Ngày HĐ' },
          { key: 'due_date', label: 'Hạn TT' },
          { key: 'grand_total', label: 'Tổng tiền', money: true },
          { key: 'outstanding_amount', label: 'Còn phải trả', money: true },
        ],
        map: { purchase_invoice: 'name', allocated_amount: 'outstanding_amount' },
      },
    },
  },

  // ============================================================
  // M9 Stocktake
  // ============================================================
  'SC Inventory Count Sheet': {
    sections: [
      { title: 'Thông tin chung', fields: [
        { name: 'count_date', label: 'Ngày kiểm', type: 'Date', required: true, default: 'today' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', required: true },
        { name: 'planned_by', label: 'Người lập', type: 'Link', linkTo: 'User' },
        { name: 'counted_by', label: 'Người đếm', type: 'Link', linkTo: 'User' },
      ]},
      { title: 'Phạm vi đếm', fields: [
        { name: 'count_scope', label: 'Phạm vi', type: 'Select', required: true,
          options: [
            { value: 'All Items', label: 'Toàn bộ vật tư' },
            { value: 'By Item Group', label: 'Theo nhóm vật tư' },
            { value: 'By Zone', label: 'Theo khu vực kệ' },
          ], default: 'All Items' },
        { name: 'item_group', label: 'Nhóm vật tư', type: 'Link', linkTo: 'SC Item Group',
          dependOn: 'count_scope', hint: 'Bắt buộc khi phạm vi = Theo nhóm vật tư' },
        { name: 'bin_zone', label: 'Khu vực kệ', type: 'Data',
          hint: 'VD: A1, B2 — dùng khi phạm vi = Theo khu vực kệ' },
        { name: 'recount_threshold_pct', label: 'Ngưỡng đếm lại (%)', type: 'Percent',
          hint: 'Item nào lệch > ngưỡng → đếm lại lần 2 (mặc định 5%)' },
        { name: 'hide_system_qty', label: 'In phiếu ẩn SL hệ thống', type: 'Check',
          hint: 'Bật để đếm "mù" — không cho biết SL hệ thống' },
      ]},
      { title: 'Tổng hợp', fields: [
        { name: 'total_items', label: 'Tổng items', type: 'Int', readonly: true },
        { name: 'mismatched_items', label: 'Items lệch', type: 'Int', readonly: true },
        { name: 'total_variance_qty', label: 'Tổng SL lệch', type: 'Float', readonly: true },
        { name: 'total_variance_value', label: 'Tổng giá trị lệch (VND)', type: 'Currency', readonly: true },
        { name: 'manager_witness', label: 'Manager chứng kiến (lần 3)', type: 'Link', linkTo: 'User',
          hint: 'Bắt buộc khi có item cần đếm lần 3' },
        { name: 'status', label: 'Trạng thái', type: 'Data', readonly: true },
        { name: 'stock_reconciliation', label: 'SR đã tạo', type: 'Link', linkTo: 'SC Stock Reconciliation', readonly: true },
      ]},
    ],
    items: {
      field: 'items', label: 'Items kiểm kê',
      columns: [
        { name: 'item', label: 'Mã VT', type: 'Link', linkTo: 'SC Item', required: true, width: '18%' },
        { name: 'item_name', label: 'Tên', type: 'Data', readonly: true, width: '15%' },
        { name: 'uom', label: 'ĐVT', type: 'Link', linkTo: 'SC UOM', width: '7%',
          scope: { itemField: 'item' } },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '12%',
          scope: { itemField: 'item' } },
        { name: 'bin_location', label: 'Vị trí', type: 'Link', linkTo: 'Bin Location', width: '10%' },
        { name: 'system_qty', label: 'SL HT', type: 'Float', readonly: true, width: '8%' },
        { name: 'actual_qty', label: 'SL đếm', type: 'Float', required: true, width: '8%' },
        { name: 'variance_pct', label: '% lệch', type: 'Float', readonly: true, width: '7%' },
        { name: 'needs_recount', label: 'Đếm lại', type: 'Check', readonly: true, width: '5%' },
        { name: 'recount_actual_qty', label: 'SL đếm L2', type: 'Float', width: '8%',
          hint: 'Nhập khi cần đếm lại' },
        { name: 'third_count_qty', label: 'SL đếm L3', type: 'Float', width: '8%',
          hint: 'Cần manager chứng kiến' },
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
        { name: 'uom', label: 'UOM', type: 'Link', linkTo: 'SC UOM', required: true, width: '10%',
          scope: { itemField: 'item' },
          fetchFrom: { source: 'item', target_doctype: 'SC Item', target_field: 'uom' } },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch', width: '15%',
          scope: { itemField: 'item' } },
        { name: 'system_qty', label: 'SL hệ thống', type: 'Float', width: '14%' },
        { name: 'actual_qty', label: 'SL thực tế', type: 'Float', required: true, width: '14%' },
        { name: 'valuation_rate', label: 'Đơn giá', type: 'Currency', width: '12%' },
        { name: 'reason', label: 'Lý do', type: 'Select',
          options: [
            { value: 'Counting Error', label: 'Sai lệch kiểm đếm' },
            { value: 'Damage', label: 'Hư hỏng' },
            { value: 'Theft', label: 'Mất cắp' },
            { value: 'Expiry', label: 'Hết hạn' },
            { value: 'Other', label: 'Khác' },
          ], width: '15%' },
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
          options: [
            { value: 'Voluntary', label: 'Tự nguyện' },
            { value: 'Mandatory', label: 'Bắt buộc' },
            { value: 'Precautionary', label: 'Phòng ngừa' },
          ], default: 'Voluntary' },
        { name: 'severity', label: 'Mức độ', type: 'Select',
          options: [
            { value: 'Class I (Critical)', label: 'Loại I — Nguy hiểm' },
            { value: 'Class II (High)', label: 'Loại II — Cao' },
            { value: 'Class III (Low)', label: 'Loại III — Thấp' },
          ], default: 'Class II (High)' },
        { name: 'item', label: 'Vật tư', type: 'Link', linkTo: 'SC Item', required: true },
        { name: 'batch_no', label: 'Lô', type: 'Link', linkTo: 'SC Batch', required: true,
          scope: { itemField: 'item' } },
        { name: 'supplier', label: 'NCC', type: 'Link', linkTo: 'SC Supplier' },
      ]},
      { title: 'Lý do', fields: [
        { name: 'recall_reason', label: 'Lý do thu hồi', type: 'Small Text', required: true },
        { name: 'regulatory_reference', label: 'Tham chiếu pháp lý', type: 'Data',
          hint: 'VD: CV BYT số ..., TT ...' },
      ]},
      { title: 'Tổng hợp thu hồi', fields: [
        { name: 'total_affected_qty', label: 'Tổng SL ảnh hưởng', type: 'Float', readonly: true },
        { name: 'recovered_qty', label: 'Đã thu hồi', type: 'Float', readonly: true },
        { name: 'destroyed_qty', label: 'Đã huỷ', type: 'Float', readonly: true },
        { name: 'outstanding_qty', label: 'Còn lại', type: 'Float', readonly: true },
        { name: 'recall_resolution_pct', label: 'Tiến độ (%)', type: 'Percent', readonly: true },
        { name: 'status', label: 'Trạng thái', type: 'Data', readonly: true },
      ]},
      { title: 'Liên kết xử lý', fields: [
        { name: 'return_pr', label: 'Phiếu trả NCC', type: 'Link', linkTo: 'SC Purchase Receipt', readonly: true },
        { name: 'write_off_entry', label: 'Phiếu huỷ', type: 'Link', linkTo: 'SC Stock Entry', readonly: true },
        { name: 'clinical_notified_at', label: 'Thời điểm báo BS', type: 'Datetime', readonly: true },
        { name: 'approved_by', label: 'Người duyệt', type: 'Link', linkTo: 'User', readonly: true },
      ]},
    ],
    items: {
      field: 'affected_items', label: 'Vị trí ảnh hưởng (auto populate)',
      readonly: true,
      columns: [
        { name: 'location_type', label: 'Loại', type: 'Data', width: '10%' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse', width: '12%' },
        { name: 'department', label: 'Khoa', type: 'Link', linkTo: 'SC Department', width: '12%' },
        { name: 'voucher_type', label: 'Chứng từ', type: 'Data', width: '10%' },
        { name: 'voucher_no', label: 'Mã CT', type: 'Data', width: '12%' },
        { name: 'qty_issued', label: 'SL', type: 'Float', width: '8%' },
        { name: 'recovered_qty', label: 'Đã thu', type: 'Float', width: '8%' },
        { name: 'destroyed_qty', label: 'Đã huỷ', type: 'Float', width: '8%' },
        { name: 'outstanding_qty', label: 'Còn', type: 'Float', width: '8%' },
        { name: 'status', label: 'TT', type: 'Data', width: '12%' },
      ],
    },
  },

  'SC Investigation Report': {
    sections: [
      { title: 'Điều tra', fields: [
        { name: 'investigation_date', label: 'Ngày bắt đầu', type: 'Date', required: true, default: 'today' },
        { name: 'investigation_type', label: 'Loại sự cố', type: 'Select', required: true,
          options: [
            { value: 'Stock Loss', label: 'Thất thoát kho' },
            { value: 'Discrepancy', label: 'Sai lệch' },
            { value: 'Fraud', label: 'Gian lận' },
            { value: 'System Error', label: 'Lỗi hệ thống' },
            { value: 'Other', label: 'Khác' },
          ], default: 'Discrepancy' },
        { name: 'triggered_by', label: 'Trigger', type: 'Link', linkTo: 'User', readonly: true },
        { name: 'status', label: 'Trạng thái', type: 'Data', readonly: true },
      ]},
      { title: 'Phạm vi (cần ≥1)', fields: [
        { name: 'item', label: 'Vật tư', type: 'Link', linkTo: 'SC Item',
          hint: 'Cần ≥ 1 trong: Vật tư / Kho / Batch' },
        { name: 'warehouse', label: 'Kho', type: 'Link', linkTo: 'SC Warehouse' },
        { name: 'batch', label: 'Lô', type: 'Link', linkTo: 'SC Batch',
          scope: { itemField: 'item' } },
        { name: 'period_start', label: 'Từ ngày', type: 'Date', required: true },
        { name: 'period_end', label: 'Đến ngày', type: 'Date', required: true, default: 'today' },
        { name: 'filter_user', label: 'Lọc theo user', type: 'Link', linkTo: 'User',
          hint: 'Để trống = không lọc user' },
      ]},
      { title: 'Mô tả', fields: [
        { name: 'description', label: 'Mô tả phát hiện', type: 'Small Text' },
      ]},
      { title: 'Kết quả so sánh tồn kho (sau chạy "So sánh tồn kho")', fields: [
        { name: 'theoretical_qty', label: 'SL lý thuyết', type: 'Float', readonly: true },
        { name: 'actual_qty', label: 'SL thực tế (đếm tay)', type: 'Float',
          hint: 'Nhập manual count rồi chạy "So sánh tồn kho"' },
        { name: 'variance_qty', label: 'Chênh lệch SL', type: 'Float', readonly: true },
        { name: 'variance_value', label: 'Chênh lệch giá trị (VND)', type: 'Currency', readonly: true },
      ]},
      { title: 'Phát hiện (sau chạy Anomalies/Audit Trail)', fields: [
        { name: 'anomalies_detected', label: 'JSON anomalies', type: 'Long Text', readonly: true,
          hint: 'Tự điền bởi action "Phát hiện bất thường"' },
        { name: 'system_error_adjustment', label: 'SR điều chỉnh đã tạo', type: 'Link',
          linkTo: 'SC Stock Reconciliation', readonly: true },
      ]},
      { title: 'Kết luận & Khắc phục', fields: [
        { name: 'recommendation', label: 'Biện pháp khắc phục', type: 'Long Text' },
        { name: 'conclusion', label: 'Kết luận', type: 'Long Text' },
        { name: 'approved_by', label: 'Người duyệt', type: 'Link', linkTo: 'User', readonly: true },
        { name: 'remarks', label: 'Ghi chú thêm', type: 'Small Text' },
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
          options: [
            { value: 'Critical', label: 'Nghiêm trọng' },
            { value: 'Warning', label: 'Cảnh báo' },
            { value: 'Info', label: 'Thông tin' },
          ], default: 'Warning' },
        { name: 'enabled', label: 'Bật', type: 'Check', default: 1 },
      ]},
      { title: 'Tần suất', fields: [
        { name: 'frequency', label: 'Tần suất', type: 'Select',
          options: [
            { value: 'Daily', label: 'Hàng ngày' },
            { value: 'Hourly', label: 'Hàng giờ' },
            { value: 'Realtime', label: 'Thời gian thực' },
            { value: 'Weekly', label: 'Hàng tuần' },
          ], default: 'Daily' },
        { name: 'scheduled_time', label: 'Giờ chạy', type: 'Time', default: '08:00:00' },
        { name: 'day_of_week', label: 'Thứ', type: 'Select',
          options: [
            { value: 'Mon', label: 'Thứ 2' },
            { value: 'Tue', label: 'Thứ 3' },
            { value: 'Wed', label: 'Thứ 4' },
            { value: 'Thu', label: 'Thứ 5' },
            { value: 'Fri', label: 'Thứ 6' },
            { value: 'Sat', label: 'Thứ 7' },
            { value: 'Sun', label: 'Chủ nhật' },
          ], default: 'Mon' },
      ]},
      { title: 'Ngưỡng', fields: [
        { name: 'threshold_value', label: 'Giá trị ngưỡng', type: 'Float', default: 30 },
        { name: 'threshold_operator', label: 'Phép so sánh', type: 'Select',
          options: ['<', '<=', '=', '>=', '>'], default: '<=' },
        { name: 'threshold_unit', label: 'Đơn vị', type: 'Select',
          options: [
            { value: 'days', label: 'Ngày' },
            { value: 'percent', label: '%' },
            { value: 'VND', label: 'VNĐ' },
            { value: 'qty', label: 'Số lượng' },
          ], default: 'days' },
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

// ============================================================
// CR-03 · Quick-create — cấu hình "Tạo nhanh" trong droplist.
// Mọi Link field có linkTo nằm trong registry này sẽ tự hiện
// nút "➕ Tạo mới" + mở QuickCreateModal (không rời trang).
// Field tối thiểu = field bắt buộc của doctype (để insert thành công).
// ============================================================
export const QUICK_CREATE = {
  'SC Supplier': {
    title: 'Tạo nhanh Nhà cung cấp',
    prefillField: 'supplier_name',
    fields: [
      { name: 'supplier_name', label: 'Tên NCC', type: 'Data', required: true },
      { name: 'supplier_type', label: 'Loại NCC', type: 'Select', required: true, options: [
        { value: 'Nhà sản xuất', label: 'Nhà sản xuất' },
        { value: 'Nhà phân phối', label: 'Nhà phân phối' },
        { value: 'Đại lý', label: 'Đại lý' },
        { value: 'Khác', label: 'Khác' },
      ] },
      { name: 'tax_id', label: 'Mã số thuế', type: 'Data', required: true },
      { name: 'email_id', label: 'Email', type: 'Data', required: true },
      { name: 'mobile_no', label: 'Điện thoại', type: 'Data', required: true },
      { name: 'address', label: 'Địa chỉ', type: 'Small Text', required: true },
    ],
  },
  'SC Item': {
    title: 'Tạo nhanh Vật tư',
    prefillField: 'item_name',
    fields: [
      { name: 'item_code', label: 'Mã VT', type: 'Data', required: true },
      { name: 'item_name', label: 'Tên vật tư', type: 'Data', required: true },
      { name: 'uom', label: 'Đơn vị tồn (UOM)', type: 'Link', linkTo: 'SC UOM', required: true },
    ],
  },
  'SC Warehouse': {
    title: 'Tạo nhanh Kho',
    prefillField: 'warehouse_name',
    fields: [
      { name: 'warehouse_name', label: 'Tên kho', type: 'Data', required: true },
    ],
  },
  'SC Department': {
    title: 'Tạo nhanh Khoa/Phòng',
    prefillField: 'department_name',
    fields: [
      { name: 'department_name', label: 'Tên khoa/phòng', type: 'Data', required: true },
    ],
  },
  'SC Customer': {
    title: 'Tạo nhanh Khách hàng',
    prefillField: 'customer_name',
    fields: [
      { name: 'customer_name', label: 'Tên khách hàng', type: 'Data', required: true },
      { name: 'tax_code', label: 'Mã số thuế', type: 'Data', required: true },
      { name: 'credit_limit', label: 'Hạn mức nợ (VND)', type: 'Currency' },
      { name: 'billing_address', label: 'Địa chỉ hoá đơn', type: 'Small Text' },
    ],
  },
}
