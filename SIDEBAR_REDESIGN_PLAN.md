# PLAN — Thiết kế lại Sidebar SPA nội bộ (3 khối phân hệ) · ✅ ĐÃ TRIỂN KHAI

> Chốt: Q1 = tách từng bước nghiệp vụ · Q2 = Manager kiêm bán hàng (không role mới) · Q3 = cam/hổ phách.
> Đã build + reload + verify: manager thấy cả 3 khối; purchaser chỉ Mua+Chung (ẩn Bán); accountant cả AP+AR.
> File: `frontend/src/nav-blocks.js` (mới), `components/AppShell.vue` (refactor), `api/access.py` (+Procurement Plan).
> 103/103 Python + 12/12 UI xanh.


## 0. Audit hiện trạng
- **Component:** `frontend/src/components/AppShell.vue` — sidebar dark navy, 2 layout:
  (a) *persona-curated* (theo vai, `personas.js`), (b) *admin/fallback* (full module `MODULES`).
- **Menu hiện tại:** 11 module hub M0–M11 (`modules.js`), nhóm theo `group`
  (Thiết lập/Chiến lược/Kinh doanh/Vận hành/Tài chính/Chất lượng/Báo cáo). **Chỉ 1 màu accent
  xanh dương** cho mọi mục active — chưa phân màu theo phân hệ.
- **Phân quyền:** `stores/access.js` fetch `api/access.menu` → `modules/features/doctypes` theo role.
  `personas.js`: 5 persona (admin, `lan` TP Vật tư, `hung` NV Mua sắm, `tam` Thủ kho, `phong` Kế toán).
  **⚠️ CHƯA có persona/role "Nhân viên Bán hàng"** — mảng bán hàng (M7) hiện chỉ là 1 hub, chưa có vai riêng.
- **Role hiện có:** SupplyCore Manager, Purchaser, Storekeeper, Accountant, Executive, Auditor,
  Warehouse Officer, QC Officer (+ SC Customer Portal, Khách hàng cho cổng — KHÔNG đụng).
- **Cổng khách hàng** (`www/portal`) tách biệt hoàn toàn — redesign này KHÔNG chạm.

## 1. Cấu trúc 3 khối đề xuất (thứ tự nghiệp vụ đầu→cuối)

### 🛒 MUA HÀNG — accent XANH DƯƠNG
1. HĐ khung mua (NCC) — `Framework Contract`
2. Kế hoạch mua — `Procurement Plan` / `Demand Forecast`
3. Yêu cầu mua (MR) — `SC Material Request`
4. **Đơn mua hàng (NCC)** — `SC Purchase Order`
5. Tiếp nhận & QC — `SC Purchase Receipt` + `SC Quality Inspection`
6. **Hoá đơn mua** — `SC Purchase Invoice`
7. Thanh toán NCC — `SC Payment Entry`
8. **Công nợ phải trả** — báo cáo AP
9. Báo cáo mua hàng

### 💰 BÁN HÀNG — accent CAM/HỔ PHÁCH (đề xuất, xem Q3)
1. HĐ khung bán (KH) — `SC Sales Framework Contract`
2. **Đơn gọi hàng (KH)** — `SC Sales Order`
3. Phiếu giao hàng — `SC Delivery Note`
4. Nghiệm thu — `SC Acceptance Record`
5. **Hoá đơn bán** — `SC Sales Invoice`
6. Phiếu thu (thu tiền) — `SC Sales Receipt`
7. **Công nợ phải thu** — báo cáo AR (aging)
8. Khách hàng — `SC Customer`
9. Báo cáo bán hàng

### ⚙️ DÙNG CHUNG — accent XÁM/SLATE
- **Danh mục:** Vật tư `SC Item` · Nhà cung cấp `SC Supplier` · Kho `SC Warehouse` · ĐVT `SC UOM` · Nhóm VT
- **Kho vận:** Tồn kho · Lô vật tư `SC Batch` (M5) · Nhập/Xuất kho `SC Stock Entry` · Chuyển kho `SC Transfer Request` (M6) · Xếp hàng lên kệ · Bản đồ kho
- **Kiểm soát:** Kiểm kê (M9) · Truy xuất & Thu hồi (M10)
- **Hệ thống:** Dashboard & Cảnh báo (M11) · Báo cáo tài chính · Người dùng & Quyền · Cài đặt

## 2. Hệ màu nhận diện (accessible — KHÔNG chỉ dựa màu)
Mỗi khối = **emoji + label chữ (header nhóm) + màu accent + accent bar trái mục active + màu icon**.
Bộ 3 màu chọn để **an toàn mù màu** (xanh dương ↔ cam ↔ xám phân biệt tốt cả deuteranopia/protanopia):

| Khối | Accent (nền tối sidebar) | Dùng cho | Ghi chú a11y |
|---|---|---|---|
| 🛒 Mua hàng | Xanh dương `#7FB4E0` (base `#2E75B6`) | header nhóm, icon, bar, page header | + emoji 🛒 + chữ "MUA HÀNG" |
| 💰 Bán hàng | Hổ phách `#F0B45E` (base `#C77A1F`) | — | + emoji 💰 + chữ "BÁN HÀNG" |
| ⚙️ Dùng chung | Slate `#94A3B8` (base `#64748B`) | — | + emoji ⚙️ + chữ "DÙNG CHUNG" |

- **Page header** (topbar) khi vào trang sâu: hiện **chip phân hệ** (emoji + tên khối + màu) để luôn biết đang ở đâu.
- **Header nhóm KHÔNG click** (label), mục con click được.
- Icon: dùng bộ icon sẵn có (`components/Icon.vue`, lucide) — không chế icon mới.

## 3. Đặt tên phân biệt (chống nhầm 2 phân hệ)
| Mua hàng | Bán hàng |
|---|---|
| Đơn mua hàng (NCC) | Đơn gọi hàng (KH) |
| Hoá đơn mua | Hoá đơn bán |
| Công nợ phải trả | Công nợ phải thu |
| HĐ khung mua (NCC) | HĐ khung bán (KH) |
| Thanh toán NCC | Thu tiền (Phiếu thu) |

(App hiện chưa bật song ngữ file translation cho các nhãn này — sửa trực tiếp nhãn tiếng Việt trong `modules.js`/`personas.js`; nếu có `translations/` sẽ cập nhật kèm.)

## 4. Phân quyền theo vai (khối hiện theo role)
| Vai / Role | Thấy khối |
|---|---|
| NV Mua sắm (Purchaser) | 🛒 Mua hàng + ⚙️ Dùng chung |
| **NV Bán hàng** (role MỚI — xem Q2) | 💰 Bán hàng + ⚙️ Dùng chung |
| Thủ kho (Storekeeper) | ⚙️ Dùng chung (kho) + phần Tiếp nhận (Mua) |
| Kế toán (Accountant) | Kế toán Mua (AP) + Bán (AR) + Dùng chung |
| Quản lý / Admin (Manager/Executive) | Cả 3 khối |
| Portal khách hàng | KHÔNG đụng (cổng riêng) |

Gating tái dùng `access.js` (`canModule/canFeature/canDoctype`) — mỗi mục có `requireDoctype/requireFeature`.

## 5. Hành vi
- Nhóm **collapse/expand**, nhớ trạng thái `localStorage`; mặc định **mở nhóm chứa trang đang mở**.
- Mục active: accent bar + nền tint + màu icon theo khối.
- **Mobile:** sidebar → drawer (đã có sẵn cơ chế `sidebarOpen`).

## 6. Kế hoạch code (sau khi duyệt)
1. `modules.js`: thêm metadata `block` (mua/ban/chung) + `order` (thứ tự flow) + map route/doctype cho từng mục.
2. `AppShell.vue`: render 3 khối (header emoji+label+màu), accent bar/icon theo màu khối, collapse-per-group + nhớ localStorage, page-header chip phân hệ.
3. `personas.js`: cập nhật nav các persona theo 3 khối + thêm persona Bán hàng (nếu chốt Q2).
4. `api/access.py` + role: nếu thêm role "SupplyCore Sales" → map module/feature bán hàng.
5. CSS: 3 biến accent, tint active theo khối, đảm bảo tương phản trên nền navy + focus keyboard + reduced-motion.
6. Build + kiểm thử (desktop/mobile, từng role) + không phá 12 UI test cổng KH.

## 7. Cần bạn chốt trước khi code
- **Q1 — Độ chi tiết menu:** (A) tách từng bước nghiệp vụ thành mục riêng như mục 1 (khớp ví dụ của bạn),
  hay (B) giữ hub M0–M11 nhưng gom vào 3 khối + đổi màu (ít thay đổi hơn)?
- **Q2 — Vai Bán hàng:** thêm role/persona "NV Bán hàng" riêng, hay để Quản lý/Manager đảm nhiệm bán hàng?
- **Q3 — Màu khối Bán hàng:** Cam/hổ phách (an toàn mù màu nhất cạnh xanh dương) hay Xanh lá (như gợi ý)?
