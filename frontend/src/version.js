// SupplyCore frontend version + changelog (FEAT-005)
// Cập nhật theo SemVer Major.Minor.Patch mỗi release.

export const APP_VERSION = '0.2.0'
export const BUILD_DATE  = '2026-05-25'

export const RELEASE_NOTES = [
  {
    version: '0.2.0',
    date: '2026-05-25',
    title: 'Khắc phục Bug Report v0.1.0',
    items: [
      { type: 'fix',  text: 'BUG-001: SC Item Group / SC Warehouse / SC GL Account hỗ trợ nested-set (lft/rgt)' },
      { type: 'fix',  text: 'BUG-002: Hiển thị đầy đủ "Loại NCC" + các field thiếu trên form Supplier' },
      { type: 'fix',  text: 'BUG-003: Ẩn nút "Gửi duyệt" cho doctype không submittable (SC UOM, SC Item, ...)' },
      { type: 'ux',   text: 'UX-001: Thông báo lỗi tiếng Việt + mã SC-Exxx thân thiện' },
      { type: 'ux',   text: 'UX-002: Toast không còn che user header' },
      { type: 'ux',   text: 'UX-003: Tooltip + confirm dialog cho Gửi duyệt' },
      { type: 'ux',   text: 'UX-004: "+ Tạo mới" inline trong dropdown khi không có kết quả' },
      { type: 'ux',   text: 'UX-005: Highlight border đỏ + auto-scroll đến field thiếu' },
      { type: 'feat', text: 'FEAT-001: Hoàn thiện Import/Export Excel + CSV với template' },
      { type: 'feat', text: 'FEAT-003: Audit Trail global + báo cáo theo user/DocType/thời gian' },
      { type: 'feat', text: 'FEAT-004: Scheduler cảnh báo lô hết hạn + email notification' },
      { type: 'feat', text: 'FEAT-005: Trang Changelog + footer click hiển thị version dialog' },
      { type: 'perf', text: 'PERF-001: Thêm DB index cho item_code/batch_no/warehouse/posting_date' },
    ],
  },
  {
    version: '0.1.0',
    date: '2026-05-22',
    title: 'UAT v0.1 — bản đầu',
    items: [
      { type: 'feat', text: '14 màn hình UI: Dashboard, MR, PO, PR, QI, SE, PD, FC, Putaway, Recall, ...' },
      { type: 'feat', text: 'FEFO pick guide + WMS warehouse panel + bin assignment' },
      { type: 'feat', text: 'UC-30..34: Recall + Investigation + Executive Dashboard + Alerts' },
      { type: 'feat', text: 'RBAC matrix 7 role: System Manager → SupplyCore Manager/Purchaser/Storekeeper/Ward Staff/Accountant/Pharmacy Officer/QC Officer' },
    ],
  },
]

export const TYPE_LABEL = {
  fix:  { label: 'Fix',    cls: 'bg-red-100 text-red-700' },
  feat: { label: 'Feature',cls: 'bg-blue-100 text-blue-700' },
  ux:   { label: 'UX',     cls: 'bg-purple-100 text-purple-700' },
  perf: { label: 'Perf',   cls: 'bg-amber-100 text-amber-700' },
  docs: { label: 'Docs',   cls: 'bg-gray-100 text-gray-700' },
}
