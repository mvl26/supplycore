# Spec GĐ3 — M12 Portal Khách hàng: Cô lập dữ liệu + API (RSK-01)

- **Ngày:** 2026-07-07 · **Nhánh:** `feat/mvl-distributor` (sau GĐ2)
- **Nguồn:** BA MVL v2 (#11 API M12, #13 Security, #04 BRU-CUS/SEC, #16 4 cột mốc) + `PHAN_TICH_HUONG_THIET_KE_MVL.md`.
- **Phạm vi GĐ3:** **backend cô lập dữ liệu + 7 API portal + theo dõi 4 cột mốc**, có bộ test cô lập (RSK-01) làm gate. UI Portal (trang khách) để **GĐ4**.

## 0. Quyết định kiến trúc UI (chốt)
App hiện là **1 SPA Vue** phục vụ mọi route `/supplycore/*`. Ranh giới bảo mật KHÔNG thể đặt ở client router (chỉ là UX). → GĐ3 xây **ranh giới ở backend**: permission_query_conditions + has_permission + doctype permissions + API role-gate. UI khách (trang `www/portal` riêng hoặc guard SPA) làm ở GĐ4, tiêu thụ các API GĐ3. Điều này khóa mô hình bảo mật trước, UI sau — đúng nguyên tắc "test cô lập trước" (RSK-01).

## 1. Mục tiêu (kiểm chứng được)
1. Role `SC Customer Portal` tồn tại; mỗi SC Customer "Hoạt động" bắt buộc có `portal_user` 1-1 (BRU-CUS-001/002); có API cấp tài khoản portal (tạo Website User + gán role + link 2 chiều).
2. **Cô lập dữ liệu tuyệt đối (RSK-01):** user role Portal chỉ đọc được SC Sales Order/Delivery Note/Sales Invoice/Sales Receipt/Sales Framework Contract thuộc CHÍNH khách của mình; không thấy của khách khác; không truy cập doctype/API nội bộ (NCC, kho, giá mua, PO...) → PermissionError/403 (BRU-SEC-001).
3. 7 API portal hoạt động, đều tự lọc theo khách đăng nhập.
4. Theo dõi đơn **4 cột mốc**: Đã đặt → Đã bàn giao/nghiệm thu → Đã cấp hóa đơn → Đã thu tiền.
5. Không hồi quy GĐ1/GĐ2; migrate/build/ping sạch.

## 2. Thành phần

### 2.1 Role + provisioning
- Tạo Role `SC Customer Portal` (desk_access=0 — chỉ website) qua patch v0_9 (idempotent) + thêm vào `install.py` DEFAULT_ROLES.
- SC Customer controller: BRU-CUS-001 — khi `status="Hoạt động"` mà chưa có `portal_user` → chặn kích hoạt. BRU-CUS-002 (1-1) đã có từ GĐ2.
- API `portal_provision(customer, email, [send_welcome])` (trong `api/portal.py`): tạo/lấy `User` type "Website User", gán role `SC Customer Portal`, set `SC Customer.portal_user = user`; chỉ role nội bộ (Manager/Purchaser) gọi được.

### 2.2 Cô lập dữ liệu (backend — lõi RSK-01)
- `utils/permissions.py`: hàm `portal_customer_query(user)` → nếu user KHÔNG có role Portal trả `""` (không giới hạn cho nội bộ); nếu CÓ role Portal trả SQL: ``customer in (select name from `tabSC Customer` where portal_user = %(user)s)`` (escape đúng). Một hàm per-doctype hoặc dùng chung (5 doctype đều có field `customer`).
- Đăng ký `permission_query_conditions` cho cả 5 doctype trong hooks.py.
- Đăng ký `has_permission` cho cả 5 doctype: `def portal_doc_permission(doc, user, permission_type)` → nếu user role Portal: chỉ cho phép nếu `doc.customer` thuộc user; và chỉ `read` (không write/create/cancel). Nội bộ: trả True (để mặc định role-permission xử lý).
- **Chặn nội bộ:** KHÔNG cấp bất kỳ permission nào cho role `SC Customer Portal` trong các doctype JSON nội bộ (Item, Supplier, Warehouse, PO, Batch...). Role Portal chỉ có `read` (qua has_permission) trên 5 doctype bán của chính khách.

### 2.3 7 API Portal (`api/portal.py`, đều @frappe.whitelist(), tự lọc theo `frappe.session.user`)
Helper `_current_customer()` → tìm SC Customer có portal_user==session.user; nếu không có → PermissionError (chặn nội bộ gọi API portal cũng OK vì họ không map customer). Mỗi API kiểm role Portal.
1. `portal.me` (thay `login` — auth dùng Frappe `/api/method/login` chuẩn): trả hồ sơ khách + credit_limit + công nợ hiện tại.
2. `portal.contracts`: danh sách SC Sales Framework Contract "Hiệu lực" của khách + items (giá HĐ).
3. `portal.catalog`: vật tư + bảng giá lấy TỪ HĐ khung còn hiệu lực của khách (chỉ mặt hàng thuộc HĐ — BRU-SFC-001).
4. `portal.order_place(contract, items)`: tạo SC Sales Order (status "Chờ duyệt") cho khách, giá cố định theo HĐ (BRU-SFC-002), qty ≤ remaining (BRU-SO-001). Trả order name.
5. `portal.order_track(order)`: trả **4 cột mốc** {placed, delivered_accepted, invoiced, paid} với timestamp/trạng thái, CHỈ nếu order thuộc khách.
6. `portal.order_history`: danh sách đơn của khách (phân trang).
7. `portal.document_download(doctype, name)`: chỉ cho tải chứng từ (SI/DN) thuộc khách (PDF/print) → chặn nếu không thuộc khách.

### 2.4 4 cột mốc (order_track)
Suy từ chuỗi: SO (Đã đặt khi tồn tại/duyệt) → DN nghiệm thu (Đã bàn giao/nghiệm thu) → SI phát hành (Đã cấp hóa đơn) → Receipt đủ (Đã thu tiền). Trả trạng thái mỗi mốc: done/current/pending + thời điểm.

## 3. Business Rules / Security phải test (TDD — RSK-01, viết TRƯỚC)
- **ISO-1**: portal user A không đọc được SO/DN/SI/Receipt/SFC của khách B (permission_query lọc → get_list rỗng; get_doc → PermissionError).
- **ISO-2**: portal user gọi API/đọc doctype nội bộ (SC Supplier, SC Purchase Order, SC Item write...) → PermissionError.
- **ISO-3**: `portal.order_track`/`document_download` với order/doc của khách khác → PermissionError.
- **ISO-4**: portal user chỉ `read`, không create/write/cancel trực tiếp SO của mình (chỉ qua order_place tạo Chờ duyệt).
- BRU-CUS-001: kích hoạt customer không portal_user → chặn.
- BRU-SFC-001/002 + BRU-SO-001 qua `order_place` (giá HĐ, item thuộc HĐ, qty ≤ remaining).

## 4. Ngoài phạm vi GĐ3 (→ GĐ4)
UI trang khách (www/portal hoặc SPA guard + 4-milestone tracker UI), email welcome, dashboard công nợ khách, rebrand.

## 5. Định nghĩa Done
Role + provisioning + cô lập 5 doctype (permission_query + has_permission) + 7 API + 4 cột mốc; bộ test cô lập ISO-1..4 + BRU pass; nội bộ không bị ảnh hưởng (get_list nội bộ vẫn thấy hết); migrate/build/ping sạch; không hồi quy.
