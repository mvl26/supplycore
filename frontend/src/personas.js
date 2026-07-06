// Persona definitions — RBAC personas tightly mapped to xlsx
// `SupplyCore_Bang_hoi_Chan_dung_Phan_quyen_1.xlsx` (sheets 02/03/04) +
// HTML prototype `SupplyCore_UI_Prototype.html`.
//
// Persona ≠ Frappe role. Persona is a UI lens that picks WHICH curated nav
// + dashboard widgets a user sees. The backend `access` store (modules/
// features/doctypes) remains the source of truth for what's actually
// allowed. Persona nav items are filtered through access — if a persona's
// item points to a module/feature the user lacks, it is hidden.
//
// Why not add new SC-* Frappe roles? It would force a backend migration
// + reseed of every test user. The SC-* roles in spec map to existing
// Frappe roles via `ROLE_TO_PERSONA` below; admins extend the lookup as new
// Frappe roles are introduced.
//
// GĐ1 (2026-07): bỏ 2 persona bệnh viện (điều dưỡng khoa; QC tạm map vào
// 1 role dược đã xoá) — cả 2 Frappe role nguồn đã bị xoá khỏi backend, không
// còn cách nào resolve tới các persona này. GĐ2 sẽ định nghĩa lại role/persona
// theo mô hình phân phối.
//
// Admin (System Manager / SupplyCore Executive) gets the default flat view
// — full M0..M11 + every primary feature — which is also the fallback for
// any user whose roles don't match a named persona.

// Frappe role → persona id (first match wins, evaluated in order).
// SupplyCore Executive → admin (full view, never a curated persona).
export const ROLE_TO_PERSONA = [
  ['System Manager',        'admin'],
  ['SupplyCore Executive',  'admin'],
  ['SupplyCore Manager',    'lan'],
  ['SupplyCore Accountant', 'phong'],
  ['SupplyCore Storekeeper','tam'],
  ['Warehouse Officer',     'tam'],
]

// Persona definitions. Each nav item:
//   { to, icon, label, requireModule?, requireFeature?, requireDoctype? }
// Gated against access store at render time. Groups: { group: 'Tên nhóm' }.
export const PERSONAS = {
  // === Admin / fallback — current flat layout. Sidebar uses MODULES + primaryNav directly. ===
  admin: {
    id: 'admin',
    name: 'Quản trị Hệ thống',
    title: 'Toàn quyền — xem mọi module',
    role: 'SC-ADMIN',
    avatar: 'A',
    color: '#1F4E79',
    scope: 'Toàn hệ thống — không lọc dữ liệu',
    twofa: 'Bắt buộc',
    goal: 'Cấu hình hệ thống, người dùng, vai trò, thiết lập DocType',
    // Admin uses default flat sidebar (primaryNav + module groups). No `nav` here.
    flat: true,
    home: '/dashboard',
  },

  // === SC-MANAGER · Lan — Trưởng phòng VTTBYT ===
  lan: {
    id: 'lan',
    name: 'Trưởng phòng Vật tư',
    title: 'Quản lý Kho & Cung ứng',
    role: 'SC-MANAGER',
    avatar: 'L',
    color: '#1F4E79',
    scope: 'Toàn bộ kho & khoa (xem tất cả)',
    twofa: 'Bắt buộc',
    goal: 'Kiểm soát chuỗi cung ứng, đảm bảo đủ vật tư & ngân sách hợp lý',
    home: '/dashboard',
    nav: [
      { group: 'Tổng quan' },
      { to: '/dashboard',         icon: 'layout-dashboard', label: 'Dashboard KPI' },
      { to: '/alerts',            icon: 'bell',             label: 'Trung tâm Cảnh báo',  requireFeature: 'alerts' },
      { group: 'Phê duyệt' },
      { to: '/list/SC Purchase Order',  icon: 'clipboard-check', label: 'Phê duyệt PO',          requireDoctype: 'SC Purchase Order' },
      { to: '/list/SC Payment Entry',   icon: 'wallet',          label: 'Phê duyệt Thanh toán',  requireDoctype: 'SC Payment Entry' },
      { to: '/list/Framework Contract', icon: 'file-text',       label: 'Phê duyệt Hợp đồng',    requireDoctype: 'Framework Contract' },
      { group: 'Cung ứng' },
      { to: '/m1',  icon: 'file-text',     label: 'M1 · Hợp đồng',         requireModule: 'm1' },
      { to: '/m2',  icon: 'shopping-cart', label: 'M2 · Kế hoạch & Mua',   requireModule: 'm2' },
      { to: '/list/SC Supplier', icon: 'building-2', label: 'Nhà cung cấp', requireDoctype: 'SC Supplier' },
      { group: 'Vận hành' },
      { to: '/m3',  icon: 'truck',     label: 'M3 · Tiếp nhận',       requireModule: 'm3' },
      { to: '/m4',  icon: 'warehouse', label: 'M4 · Quản lý kho',     requireModule: 'm4' },
      { group: 'Báo cáo & Kiểm soát' },
      { to: '/financial-reports', icon: 'wallet',     label: 'Báo cáo tài chính', requireFeature: 'financial_reports' },
      { to: '/stock-balance',     icon: 'package',    label: 'Tồn kho',           requireFeature: 'stock_balance' },
      { to: '/batch-trace',       icon: 'file-search', label: 'Truy xuất lô',      requireFeature: 'batch_trace' },
      { to: '/users',             icon: 'users',      label: 'Người dùng & Quyền', requireFeature: 'users' },
    ],
  },

  // === SC-MANAGER (Procurement focus) · Hùng — NV Mua sắm ===
  // Hùng shares the SupplyCore Manager Frappe role with Lan. Auto-detection
  // defaults to Lan; admins preview Hùng via the persona switcher.
  hung: {
    id: 'hung',
    name: 'NV Mua sắm',
    title: 'Quản lý NCC, Hợp đồng, PO',
    role: 'SC-MANAGER',
    avatar: 'H',
    color: '#2E75B6',
    scope: 'Dữ liệu NCC, PO, hợp đồng toàn hệ thống',
    twofa: 'Bắt buộc',
    goal: 'Tạo & theo dõi đơn hàng đúng hạn, quản lý nhà cung cấp',
    home: '/dashboard',
    nav: [
      { group: 'Tổng quan' },
      { to: '/dashboard', icon: 'shopping-cart', label: 'Bảng điều khiển Mua sắm' },
      { to: '/alerts',    icon: 'bell',          label: 'Cảnh báo cung ứng', requireFeature: 'alerts' },
      { group: 'Nhà cung cấp' },
      { to: '/list/SC Supplier',         icon: 'building-2', label: 'Danh sách NCC',          requireDoctype: 'SC Supplier' },
      { to: '/list/Framework Contract',  icon: 'file-text',  label: 'Hợp đồng Khung',         requireDoctype: 'Framework Contract' },
      { group: 'Mua sắm' },
      { to: '/list/SC Material Request', icon: 'clipboard-plus', label: 'Yêu cầu mua',            requireDoctype: 'SC Material Request' },
      { to: '/list/SC Purchase Order',   icon: 'clipboard-list', label: 'Đơn đặt hàng (PO)',      requireDoctype: 'SC Purchase Order' },
      { to: '/m2',                       icon: 'shopping-cart',  label: 'M2 · Kế hoạch & Mua',    requireModule: 'm2' },
      { group: 'Theo dõi' },
      { to: '/m3',                       icon: 'truck',        label: 'M3 · Tiếp nhận hàng',    requireModule: 'm3' },
      { to: '/list/SC Purchase Receipt', icon: 'package-check', label: 'Phiếu nhập (PR)',        requireDoctype: 'SC Purchase Receipt' },
    ],
  },

  // === SC-STOREKEEPER · Tâm — Thủ kho ===
  tam: {
    id: 'tam',
    name: 'Thủ kho',
    title: 'Vận hành Kho — FEFO, Bin, PDA',
    role: 'SC-STOREKEEPER',
    avatar: 'T',
    color: '#375623',
    scope: 'Chỉ các kho được gán cho user',
    twofa: 'Tùy chọn (Email OTP cho PDA)',
    goal: 'Nhập–xuất chính xác, không thất thoát, FEFO đúng',
    home: '/dashboard',
    nav: [
      { group: 'Tổng quan' },
      { to: '/dashboard',     icon: 'layout-dashboard', label: 'Bảng điều khiển Kho' },
      { to: '/alerts',        icon: 'bell',             label: 'Cảnh báo lô & tồn',   requireFeature: 'alerts' },
      { group: 'Nhập kho' },
      { to: '/m3',                       icon: 'truck',         label: 'M3 · Tiếp nhận hàng',    requireModule: 'm3' },
      { to: '/list/SC Purchase Receipt', icon: 'package-check', label: 'Phiếu nhập (GRN)',       requireDoctype: 'SC Purchase Receipt' },
      { to: '/putaway',                  icon: 'package-plus',  label: 'Xếp hàng lên kệ',        requireFeature: 'putaway' },
      { group: 'Quản lý kho' },
      { to: '/m4',                icon: 'warehouse',  label: 'M4 · Quản lý kho',     requireModule: 'm4' },
      { to: '/warehouse-map',     icon: 'map',        label: 'Bản đồ kho',           requireFeature: 'warehouse_map' },
      { to: '/m5',                icon: 'layers',     label: 'M5 · Lô vật tư (FEFO)', requireModule: 'm5' },
      { to: '/stock-balance',     icon: 'package',    label: 'Tồn kho',              requireFeature: 'stock_balance' },
      { group: 'Chuyển kho' },
      { to: '/m6',                icon: 'arrow-left-right', label: 'M6 · Chuyển kho', requireModule: 'm6' },
      { group: 'Kiểm kê' },
      { to: '/m9',                icon: 'clipboard-check', label: 'M9 · Kiểm kê',     requireModule: 'm9' },
    ],
  },

  // === SC-ACCOUNTANT · Phong — Kế toán thanh toán ===
  phong: {
    id: 'phong',
    name: 'Kế toán',
    title: 'Hóa đơn · 3-way Match · Thanh toán',
    role: 'SC-ACCOUNTANT',
    avatar: 'P',
    color: '#7030A0',
    scope: 'Dữ liệu hóa đơn, thanh toán (không sửa kho)',
    twofa: 'Khuyến nghị (TOTP / Email OTP)',
    goal: 'Thanh toán đúng, đối chiếu khớp 3 bên, minh bạch',
    home: '/dashboard',
    nav: [
      { group: 'Tổng quan' },
      { to: '/dashboard',          icon: 'layout-dashboard', label: 'Bảng điều khiển Kế toán' },
      { to: '/alerts',             icon: 'bell',             label: 'Cảnh báo thanh toán', requireFeature: 'alerts' },
      { group: 'Thanh toán' },
      { to: '/m8',                          icon: 'wallet',     label: 'M8 · Kế toán',         requireModule: 'm8' },
      { to: '/list/SC Purchase Invoice',    icon: 'receipt',    label: 'Hóa đơn NCC',          requireDoctype: 'SC Purchase Invoice' },
      { to: '/list/SC Payment Entry',       icon: 'credit-card', label: 'Phiếu thanh toán',     requireDoctype: 'SC Payment Entry' },
      { to: '/list/SC GL Entry',            icon: 'book',       label: 'Bút toán GL',          requireDoctype: 'SC GL Entry' },
      { group: 'Báo cáo' },
      { to: '/financial-reports', icon: 'wallet', label: 'Báo cáo tài chính', requireFeature: 'financial_reports' },
    ],
  },
}

export const PERSONA_LIST = ['admin', 'lan', 'hung', 'tam', 'phong']

// Resolve persona from a user's Frappe roles. Returns persona id ('admin' if no match).
export function resolvePersona(roles = []) {
  if (!roles || !roles.length) return 'admin'
  const set = new Set(roles)
  for (const [role, pid] of ROLE_TO_PERSONA) {
    if (set.has(role)) return pid
  }
  return 'admin'
}

export function getPersona(id) {
  return PERSONAS[id] || PERSONAS.admin
}

// KPI widget allow-list per persona — used by Dashboard.vue
// to filter the KPI grid. Admin/Lan see all; others see a focused subset.
export const PERSONA_WIDGETS = {
  admin: null,  // null = show all
  lan:   null,  // Manager sees everything
  hung:  ['pending_pos', 'po_overdue_count', 'contract_expiring_30d', 'monthly_cost'],
  tam:   ['stock_value', 'expiring_soon', 'low_stock_items'],
  phong: ['monthly_cost', 'ap_outstanding', 'pending_pos'],
}

// Quick-action chips shown above the KPI grid, persona-specific.
// Each: { to, icon, label, variant: 'primary' | 'ghost' | 'success' | 'warning' | 'danger' }
export const PERSONA_QUICK_ACTIONS = {
  admin: [],
  lan: [
    { to: '/list/SC Purchase Order',   icon: 'clipboard-check', label: 'Phê duyệt PO',         variant: 'primary' },
    { to: '/list/SC Payment Entry',    icon: 'wallet',          label: 'Phê duyệt Thanh toán', variant: 'success' },
    { to: '/alerts',                   icon: 'bell',            label: 'Cảnh báo',             variant: 'ghost' },
  ],
  hung: [
    { to: '/list/SC Purchase Order',   icon: 'clipboard-list',  label: 'Tạo PO',          variant: 'primary' },
    { to: '/list/Framework Contract',  icon: 'file-text',       label: 'Hợp đồng khung',  variant: 'ghost' },
    { to: '/list/SC Supplier',         icon: 'building-2',      label: 'Danh sách NCC',   variant: 'ghost' },
  ],
  tam: [
    { to: '/putaway',                  icon: 'package-plus',  label: 'Xếp hàng lên kệ',  variant: 'primary' },
    { to: '/list/SC Stock Entry',      icon: 'arrow-left-right', label: 'Xuất kho FEFO', variant: 'success' },
    { to: '/m9',                       icon: 'clipboard-check', label: 'Kiểm kê',         variant: 'ghost' },
    { to: '/warehouse-map',            icon: 'map',           label: 'Bản đồ kho',       variant: 'ghost' },
  ],
  phong: [
    { to: '/list/SC Purchase Invoice', icon: 'receipt',     label: 'Hóa đơn mới',     variant: 'primary' },
    { to: '/list/SC Payment Entry',    icon: 'credit-card', label: 'Phiếu thanh toán', variant: 'success' },
    { to: '/financial-reports',        icon: 'wallet',      label: 'Báo cáo tài chính', variant: 'ghost' },
  ],
}
