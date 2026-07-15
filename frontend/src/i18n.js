// Dịch field-key (snake_case từ backend) sang nhãn tiếng Việt.
// Dùng cho phần xem chi tiết DocView khi không có schema label sẵn.

const FIELD_LABEL = {
  // Generic
  status: 'Trạng thái', docstatus: 'Trạng thái CT',
  name: 'Mã', doctype: 'Loại CT', idx: 'Thứ tự',
  owner: 'Người tạo', creation: 'Ngày tạo',
  modified: 'Cập nhật', modified_by: 'Người sửa',
  comment: 'Ghi chú', remark: 'Diễn giải', remarks: 'Diễn giải',
  // Item / Master
  item: 'Vật tư', item_code: 'Mã vật tư', item_name: 'Tên vật tư',
  item_group: 'Nhóm vật tư', uom: 'ĐVT', stock_uom: 'ĐVT tồn',
  is_stock_item: 'Có tồn kho', has_batch_no: 'Có lô',
  safety_stock: 'Tồn an toàn', reorder_level: 'Mức đặt hàng',
  description: 'Mô tả', disabled: 'Vô hiệu',
  // Warehouse
  warehouse: 'Kho', warehouse_name: 'Tên kho', warehouse_type: 'Loại kho',
  parent_warehouse: 'Kho cha', from_warehouse: 'Kho nguồn',
  to_warehouse: 'Kho đích', target_bin: 'Bin đích',
  bin_location: 'Vị trí (Bin)', is_group: 'Là nhóm',
  barcode: 'Barcode', bin_code: 'Mã vị trí', batch_id: 'Mã lô',
  // Supplier
  supplier: 'Nhà cung cấp', supplier_name: 'Tên NCC',
  supplier_batch_no: 'Số lô NCC', tax_id: 'MST',
  email_id: 'Email', mobile_no: 'Điện thoại',
  // Dates
  transaction_date: 'Ngày chứng từ', posting_date: 'Ngày hạch toán',
  schedule_date: 'Ngày cần', request_date: 'Ngày yêu cầu',
  inspection_date: 'Ngày kiểm',
  invoice_date: 'Ngày HĐ', payment_date: 'Ngày thanh toán',
  recall_date: 'Ngày thu hồi', investigation_date: 'Ngày điều tra',
  contract_date: 'Ngày ký HĐ', valid_from: 'Hiệu lực từ', valid_to: 'Hiệu lực đến',
  manufacturing_date: 'Ngày SX', expiry_date: 'Hạn dùng',
  alert_date: 'Thời điểm CB',
  // Money
  total_value: 'Tổng giá trị', remaining_value: 'Còn lại',
  grand_total: 'Tổng', total_amount: 'Tổng tiền',
  outstanding_amount: 'Còn nợ', amount: 'Số tiền',
  unit_price: 'Đơn giá', rate: 'Đơn giá', total_cost: 'Tổng chi phí',
  ceiling_price: 'Giá trần', payment_rate: 'Tỷ lệ TT', payment_terms: 'Điều khoản TT',
  payment_method: 'Phương thức TT', debit: 'Nợ', credit: 'Có',
  // Quantities
  qty: 'Số lượng', received_qty: 'SL đã nhận', billed_qty: 'SL đã HĐ',
  qty_change: 'Δ SL', balance_qty: 'Tồn',
  total_qty: 'Tổng SL', total_affected_qty: 'SL ảnh hưởng',
  recovered_qty: 'SL thu hồi', variance_qty: 'Δ SL',
  variance_value: 'Δ giá trị',
  total_difference_qty: 'Δ Tổng SL', total_difference_value: 'Δ Tổng GT',
  valuation_rate: 'Giá vốn',
  // Contract
  contract_number: 'Số HĐ',
  // PO/PR/MR
  purchase_order: 'Đơn mua', purchase_receipt: 'Phiếu tiếp nhận tạm',
  material_request: 'YC mua', request_type: 'Loại YC',
  is_return: 'Là trả hàng',
  // QC
  qc_required: 'Cần KCS', qc_status: 'KCS', overall_status: 'Kết quả',
  manual_inspection: 'Kiểm thủ công',
  // Batch
  batch: 'Lô', batch_no: 'Mã lô', blocked: 'Khoá',
  is_active: 'Hiệu lực',
  // Department
  department: 'Khoa phòng', department_name: 'Tên khoa',
  department_code: 'Mã khoa', department_type: 'Loại khoa',
  current_department: 'Khoa hiện tại',
  // Alert
  alert_type: 'Loại CB', title: 'Tiêu đề', severity: 'Mức độ',
  resolved: 'Đã xử lý', escalated: 'Đã đẩy lên',
  assigned_to: 'Phụ trách', frequency: 'Tần suất', enabled: 'Bật',
  reference_doctype: 'Loại CT tham chiếu', reference_name: 'Mã CT tham chiếu',
  channel_email: 'Kênh Email', channel_inapp: 'Kênh trong app', channel_sms: 'Kênh SMS',
  // Investigation
  investigation_type: 'Loại điều tra', variance_reason: 'Lý do chênh lệch',
  recall_type: 'Loại thu hồi', filter_user: 'Lọc theo người dùng',
  // Approval
  approval_stage: 'Bước duyệt', manager_approved_by: 'Manager duyệt',
  manager_approved_at: 'Manager duyệt lúc',
  executive_approved_by: 'GĐ duyệt', executive_approved_at: 'GĐ duyệt lúc',
  rejection_reason: 'Lý do từ chối',
  // Counting
  count_type: 'Loại kiểm', requires_investigation: 'Cần điều tra',
  voucher_type: 'Loại CT', voucher_no: 'Số CT',
  account: 'Tài khoản', account_code: 'Mã TK', account_name: 'Tên TK',
  account_type: 'Loại TK', entry_type: 'Loại bút toán',
  // Misc
  is_cancelled: 'Đã huỷ', must_be_whole_number: 'Số nguyên',
  parent_group: 'Nhóm cha', group_name: 'Tên nhóm',
  uom_name: 'Tên ĐVT', fefo_override: 'Bỏ qua FEFO',
  purpose: 'Mục đích',
  // Currency / contract refs
  currency: 'Tiền tệ', framework_contract: 'Hợp đồng khung',
  has_price_variance: 'Có chênh giá', sent_to_supplier_at: 'Gửi NCC lúc',
  // Misc
  items: 'Chi tiết', readings: 'Chỉ tiêu kiểm', tests: 'Phép thử',
  is_return: 'Là trả hàng', posting_date: 'Ngày hạch toán',
}

export function fieldLabel(key) {
  if (key == null) return ''
  if (FIELD_LABEL[key]) return FIELD_LABEL[key]
  return key.replace(/_/g, ' ')
}
