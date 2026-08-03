// 3 khối phân hệ cho sidebar nội bộ — MUA HÀNG / BÁN HÀNG / DÙNG CHUNG.
// Mỗi mục theo THỨ TỰ NGHIỆP VỤ (đầu -> cuối quy trình). Gating: `dt` (requireDoctype,
// perm read) | `feat` (requireFeature) | `always`. Khối chỉ hiện khi có >=1 mục hiện.
// Màu accent chọn để AN TOÀN MÙ MÀU (xanh dương ↔ hổ phách ↔ slate) — luôn kèm emoji + chữ.

// Vai quản lý luôn thấy mọi khối.
const MGMT = ['System Manager', 'SupplyCore Manager', 'SupplyCore Executive']

export const NAV_BLOCKS = [
  {
    id: 'mua',
    label: 'MUA HÀNG',
    icon: 'shopping-cart',
    // Khối chỉ hiện cho các vai này (ngoài item-gate theo quyền). [] = mọi vai.
    roles: [...MGMT, 'SupplyCore Purchaser', 'SupplyCore Accountant', 'SupplyCore Storekeeper', 'QC Officer', 'Warehouse Officer'],
    // accent trên nền tối (sidebar) + base cho page-header sáng
    accent: '#7FB4E0', accentBase: '#2E75B6',
    tint: 'rgba(127,180,224,0.30)', tintSoft: 'rgba(127,180,224,0.07)',
    items: [
      { label: 'HĐ khung mua (NCC)', icon: 'file-text',      to: '/list/Framework Contract',   dt: 'Framework Contract' },
      { label: 'Kế hoạch mua',        icon: 'calendar',        to: '/list/Procurement Plan',     dt: 'Procurement Plan' },
      { label: 'Yêu cầu mua (MR)',    icon: 'clipboard-list',  to: '/list/SC Material Request',  dt: 'SC Material Request' },
      { label: 'Đơn mua hàng (NCC)',  icon: 'shopping-cart',   to: '/list/SC Purchase Order',    dt: 'SC Purchase Order' },
      { label: 'Tiếp nhận & QC',      icon: 'truck',           to: '/list/SC Purchase Receipt',  dt: 'SC Purchase Receipt' },
      { label: 'Hoá đơn mua',         icon: 'receipt',         to: '/list/SC Purchase Invoice',  dt: 'SC Purchase Invoice' },
      { label: 'Thanh toán NCC',      icon: 'credit-card',     to: '/list/SC Payment Entry',     dt: 'SC Payment Entry' },
      { label: 'Công nợ phải trả',    icon: 'wallet',          to: '/financial-reports',         feat: 'financial_reports' },
    ],
  },
  {
    id: 'ban',
    label: 'BÁN HÀNG',
    icon: 'banknote',
    // Q2: Quản lý kiêm bán hàng — không có role bán riêng. Kế toán thấy (công nợ phải thu).
    roles: [...MGMT, 'SupplyCore Accountant'],
    accent: '#F0B45E', accentBase: '#C77A1F',
    tint: 'rgba(240,180,94,0.30)', tintSoft: 'rgba(240,180,94,0.08)',
    items: [
      { label: 'HĐ khung bán (KH)',   icon: 'file-text',       to: '/list/SC Sales Framework Contract', dt: 'SC Sales Framework Contract' },
      { label: 'Đơn gọi hàng (KH)',   icon: 'clipboard-list',  to: '/list/SC Sales Order',       dt: 'SC Sales Order' },
      { label: 'Phiếu giao hàng',     icon: 'truck',           to: '/list/SC Delivery Note',     dt: 'SC Delivery Note' },
      { label: 'Nghiệm thu',          icon: 'clipboard-check', to: '/list/SC Acceptance Record', dt: 'SC Acceptance Record' },
      { label: 'Hoá đơn bán',         icon: 'receipt',         to: '/list/SC Sales Invoice',     dt: 'SC Sales Invoice' },
      { label: 'Thu tiền (Phiếu thu)',icon: 'banknote',        to: '/list/SC Sales Receipt',     dt: 'SC Sales Receipt' },
      { label: 'Công nợ phải thu',    icon: 'wallet',          to: '/financial-reports',         feat: 'financial_reports' },
      { label: 'Khách hàng',          icon: 'user',            to: '/list/SC Customer',          dt: 'SC Customer' },
    ],
  },
  {
    id: 'chung',
    label: 'DÙNG CHUNG',
    icon: 'settings',
    accent: '#A9B7C6', accentBase: '#64748B',
    tint: 'rgba(169,183,198,0.26)', tintSoft: 'rgba(169,183,198,0.06)',
    items: [
      // Danh mục
      { label: 'Vật tư',              icon: 'package',         to: '/list/SC Item',              dt: 'SC Item' },
      { label: 'Nhà cung cấp',        icon: 'building',        to: '/list/SC Supplier',          dt: 'SC Supplier' },
      { label: 'Kho',                 icon: 'warehouse',       to: '/list/SC Warehouse',         dt: 'SC Warehouse' },
      { label: 'Đơn vị tính',         icon: 'ruler',           to: '/list/SC UOM',               dt: 'SC UOM' },
      // Kho vận
      { label: 'Tồn kho',             icon: 'box',             to: '/stock-balance',             feat: 'stock_balance' },
      { label: 'Lô vật tư',           icon: 'layers',          to: '/list/SC Batch',             dt: 'SC Batch' },
      { label: 'Nhập / Xuất kho',     icon: 'package-check',   to: '/list/SC Stock Entry',       dt: 'SC Stock Entry' },
      { label: 'Chuyển kho',          icon: 'arrow-left-right',to: '/list/SC Transfer Request',  dt: 'SC Transfer Request' },
      { label: 'Xếp hàng lên kệ',     icon: 'package-plus',    to: '/putaway',                   feat: 'putaway' },
      { label: 'Bản đồ kho',          icon: 'map',             to: '/warehouse-map',             feat: 'warehouse_map' },
      // Kiểm soát
      { label: 'Kiểm kê',             icon: 'clipboard-check', to: '/list/SC Inventory Count Sheet', dt: 'SC Inventory Count Sheet' },
      { label: 'Truy xuất & Thu hồi', icon: 'file-search',     to: '/batch-trace',               feat: 'batch_trace' },
      // Hệ thống
      { label: 'Cảnh báo',            icon: 'siren',           to: '/alerts',                    feat: 'alerts' },
      { label: 'Báo cáo tài chính',   icon: 'bar-chart',       to: '/financial-reports',         feat: 'financial_reports' },
      { label: 'Người dùng & Quyền',  icon: 'users',           to: '/users',                     feat: 'users' },
      { label: 'Cài đặt',             icon: 'settings',        to: '/doc/SupplyCore Settings/SupplyCore Settings', feat: 'users' },
    ],
  },
]
