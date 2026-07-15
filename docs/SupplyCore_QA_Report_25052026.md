# 📋 BÁO CÁO KIỂM THỬ HỆ THỐNG SUPPLYCORE
**Phiên bản:** v0.2.0 · SupplyCore Executive
**Thực hiện bởi:** QA Agent (Claude)
**Ngày kiểm thử:** 25/05/2026
**URL hệ thống:** https://blockishly-unvowed-anglea.ngrok-free.dev/supplycore/

---

## 1. TỔNG QUAN HỆ THỐNG

SupplyCore là hệ thống quản lý cung ứng và kho dược phẩm/vật tư y tế cho bệnh viện, xây dựng trên nền tảng Frappe/ERPNext, gồm **11 module chính (M0–M11)**:

| Module | Tên | Mô tả |
|--------|-----|-------|
| M0 | Dữ liệu nền | Danh mục vật tư, NCC, kho, khoa |
| M1 | Hợp đồng | Quản lý hợp đồng framework/NCC |
| M2 | Kế hoạch & Mua | Yêu cầu mua, đơn mua hàng (PO) |
| M3 | Tiếp nhận | Phiếu nhập, kiểm tra QC |
| M4 | Quản lý kho | Kho, vị trí, sổ kho, lô hàng |
| M5 | Quản lý lô vật tư | FEFO, quản lý batch |
| M6 | Chuyển kho | Yêu cầu & phiếu chuyển kho |
| M7 | Cấp phát | Yêu cầu cấp phát, cấp phát BN |
| M8 | Kế toán | Hóa đơn mua, phiếu TT, bút toán GL |
| M9 | Kiểm kê | Phiếu kiểm kê, đối soát kho |
| M10 | Truy xuất & Thu hồi | Thu hồi, điều tra sự cố |
| M11 | Dashboard & Cảnh báo | Báo cáo điều hành, alert center |

---

## 2. CÁC USER ĐÃ TẠO VÀ PHÂN QUYỀN

Hệ thống hiện có **19 user** với **14 role**. Trong phiên kiểm thử đã tạo thêm 5 user mới:

| Email | Họ tên | Role | Mô tả vai trò |
|-------|--------|------|---------------|
| thuho.khodoc@hospital.vn | Nguyễn Thị Thu Hương | Storekeeper | Thủ kho Kho Khoa Dược |
| duocsi.tran@hospital.vn | Trần Minh Đức | Pharmacy Officer | Dược sĩ Khoa Dược |
| ketoan.le@hospital.vn | Lê Thị Hồng Như | Accountant | Kế toán viên |
| bacsi.nguyen@hospital.vn | Nguyễn Văn An | Department Requester | Bác sĩ yêu cầu vật tư |
| truongkhoa.pham@hospital.vn | Phạm Văn Minh | Manager | Trưởng khoa/Quản lý |

### Ma trận phân quyền theo role

| Tính năng | System Mgr | Manager | Storekeeper | Accountant | Pharmacy | Ward Staff | Requester |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Xem Dashboard | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tạo PO | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Nhập kho (PR) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Chuyển kho | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cấp phát | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Yêu cầu VT | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Kế toán | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Kiểm kê | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Thu hồi | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

---

## 3. KẾT QUẢ KIỂM THỬ THEO MODULE

### M3 – Tiếp nhận (Phiếu nhập kho)
- ✅ Form tạo phiếu nhập hoạt động đúng: Chọn NCC, kho đích, ngày nhập, vật tư, SL, đơn giá
- ✅ Workflow phê duyệt tồn tại: Sau khi lưu có nút "Gửi duyệt" trước khi Nhập chính thức
- ✅ Auto-fill UOM: Chọn vật tư → tự động điền đơn vị tính
- ✅ Chức năng "Lấy từ SC Purchase Order": Import từ PO đã có
- ⚠️ Phiếu mới chỉ có trạng thái Draft: Không có warning về SL tồn kho dự kiến khi nhập

### M7 – Cấp phát
- ✅ Validation bắt buộc hoạt động: Không cho lưu khi thiếu Mã VT, UOM, SL YC
- ✅ Hỗ trợ Patient-Specific dispensing: Liên kết bệnh nhân vào yêu cầu cấp phát
- ✅ Trường SL DUYỆT độc lập với SL YC: Cho phép thủ kho điều chỉnh SL thực cấp
- ⚠️ Không có giới hạn SL cấp phát theo tồn kho: Có thể yêu cầu và duyệt vượt tồn

### M4 – Quản lý kho
- ✅ Danh sách kho đầy đủ: 17 kho với phân loại Main/Department
- ✅ Quản lý vị trí lưu trữ (Bin Location): 68 vị trí
- ✅ Sổ kho SLE: 160 bút toán tồn kho
- ⚠️ Nhiều vật tư chưa có vị trí lưu trữ: Hiển thị "chưa xếp" ở nhiều dòng

### M6 – Chuyển kho
- ✅ Bản đồ kho trực quan: Hiển thị sơ đồ tuyến đường chuyển kho
- ✅ Workflow approval: Yêu cầu manager approve khi configured
- ✅ Hiển thị tồn kho nguồn real-time khi tạo yêu cầu chuyển
- ✅ Nhiều trạng thái: Draft → Đã duyệt → In Transit → Đã nhận

### M8 – Kế toán
- ✅ 3-way matching: Invoice ↔ PO ↔ PR
- ✅ Payment Entry: Liên kết thanh toán NCC
- ✅ GL Entry: Bút toán kế toán tự động
- ⚠️ Hóa đơn tổng = 0: Có hóa đơn SC-PI-2026-04374 với tổng = 0, trạng thái Not Applicable

### M9 – Kiểm kê
- ✅ Phiếu kiểm kê và đối soát: Hỗ trợ quy trình kiểm kê đầy đủ
- ✅ Nhiều trạng thái: Draft → Counted → Reconciled

### M10 – Truy xuất & Thu hồi
- ✅ Theo dõi thu hồi theo UC-30: Progress tracking chi tiết
- ✅ Liên kết ngược về PR, PO, cấp phát BN
- ✅ Gửi phiếu cho khoa: Thông báo khoa phòng bị ảnh hưởng

---

## 4. BUG ĐÃ PHÁT HIỆN

### 🔴 NGHIÊM TRỌNG (Critical)

#### BUG-001: Tồn kho âm không bị chặn
- **Module:** M5, M6, M7 (Tất cả nghiệp vụ xuất kho)
- **Mô tả:** Hệ thống cho phép SL tồn kho xuống âm. Phát hiện cụ thể:
  - DTRC-GLU5 tại Kho Khoa Dược: tồn -228.0k (giá trị âm)
  - VTTH-GLOVE-S: tồn -655 trong khi safety stock = 120
- **Tác động:** Hàng thực tế không có nhưng hệ thống vẫn cho phép xuất → nguy cơ thiếu vật tư y tế nghiêm trọng
- **Root cause nghi ngờ:** Chuyển kho và cấp phát không kiểm tra SL tồn tại thời điểm thực hiện
- **Hướng xử lý:** Implement hard-stop validation trước khi submit bất kỳ transaction giảm tồn; hiển thị warning real-time khi SL sắp về 0

#### BUG-002: Vật tư KCS Pending xuất hiện trong tồn kho khả dụng
- **Module:** M3, M5, M6
- **Mô tả:** Vật tư nhập vào với trạng thái KCS = "Pending" (chưa kiểm tra chất lượng) vẫn tính vào tồn kho chung và có thể được cấp phát/chuyển kho
- **Tác động:** Vi phạm quy trình kiểm soát chất lượng, rủi ro cấp phát hàng chưa qua kiểm tra cho bệnh nhân
- **Hướng xử lý:** Tách biệt "Available Qty" (đã qua QC) và "Quarantine Qty" (đang QC); chỉ dùng Available Qty cho xuất kho

#### BUG-003: Đơn giá = 0 trong Stock Entry
- **Module:** M4, M8
- **Mô tả:** Nhiều bút toán Stock Entry (chuyển kho) có đơn giá = 0, gây ra báo cáo tài chính sai lệch (giá trị tồn kho = 0 cho các mặt hàng đó)
- **Tác động:** Báo cáo tồn kho - giá trị không chính xác; có thể ảnh hưởng đến quyết toán BHYT
- **Root cause nghi ngờ:** Khi chuyển kho không kế thừa đơn giá từ lô gốc
- **Hướng xử lý:** Tự động kế thừa đơn giá bình quân (Moving Average) từ Stock Ledger Entry gốc khi tạo Stock Entry chuyển kho

---

### 🟠 CAO (High)

#### BUG-004: Thiếu thông tin nhà sản xuất trong dữ liệu lô
- **Module:** M5, M10
- **Mô tả:** Truy xuất lô DTRC-GLU5-202711-001 hiển thị cảnh báo "Nhà sản xuất chưa khai" → không đáp ứng yêu cầu truy xuất nguồn gốc theo quy định Bộ Y tế
- **Tác động:** Không thể truy xuất nguồn gốc đầy đủ khi có sự cố chất lượng; vi phạm Thông tư 22/2011/TT-BYT
- **Hướng xử lý:** Bắt buộc nhập thông tin nhà sản xuất khi tạo lô hoặc khi nhập kho

#### BUG-005: Số lô NCC không bắt buộc khi nhập kho
- **Module:** M3
- **Mô tả:** Form phiếu nhập không yêu cầu điền "Số lô NCC" (batch number của nhà cung cấp) và ngày hết hạn (HSD) mặc dù đây là thông tin truy xuất bắt buộc
- **Tác động:** Mất truy xuất ngược về NCC nếu có sự cố chất lượng
- **Hướng xử lý:** Bắt buộc nhập Số lô NCC và HSD khi "Yêu cầu QC" được check

#### BUG-006: Hóa đơn mua có giá trị 0
- **Module:** M8
- **Mô tả:** Hóa đơn SC-PI-2026-04374 và SC-PI-2026-04373 có Tổng = 0, trạng thái = "Not Applicable" cho 3-way match
- **Tác động:** Dữ liệu kế toán không sạch, báo cáo công nợ NCC có thể sai
- **Hướng xử lý:** Thêm validation không cho tạo hóa đơn với tổng = 0 trừ khi là credit note

---

### 🟡 TRUNG BÌNH (Medium)

#### BUG-007: Logic tính recall_resolution_pct chưa đúng
- **Module:** M10
- **Mô tả:** Thu hồi SC-RCL-2026-04367: SL ảnh hưởng = 100, SL thu hồi = 90, destroyed = 10 → recall_resolution_pct = 100% nhưng thực tế có 10 đơn vị bị destroyed chưa được giải trình rõ
- **Hướng xử lý:** Phân biệt "thu hồi về kho" với "xác nhận tiêu hủy tại chỗ"; cả hai đều tính vào resolved qty

#### BUG-008: Tên user bị cắt ngắn trong danh sách
- **Module:** Users & Quyền
- **Mô tả:** Họ tên đầy đủ như "Nguyễn Thị Thu Hương" chỉ hiển thị "Nguyễn" trong bảng danh sách user
- **Hướng xử lý:** Tăng độ rộng cột "Họ tên" hoặc hiển thị full_name thay vì first_name

#### BUG-009: SL duyệt trong Yêu cầu cấp phát không giới hạn bởi tồn kho
- **Module:** M7
- **Mô tả:** Thủ kho có thể điền SL DUYỆT tùy ý, không có real-time check với tồn kho khả dụng tại thời điểm duyệt
- **Hướng xử lý:** Thêm validator khi lưu SL DUYỆT > SL tồn; hiển thị tồn kho real-time bên cạnh ô nhập

---

### 🔵 THẤP (Low / UX)

#### BUG-010: Dashboard không tự động refresh
- **Module:** Dashboard
- **Hướng xử lý:** Thêm tùy chọn auto-refresh mỗi 5/10/15 phút

#### BUG-011: Không có search/filter nâng cao cho cảnh báo
- **Module:** M11 Alert Center
- **Mô tả:** Không filter được theo kho, loại cảnh báo, hoặc date range
- **Hướng xử lý:** Thêm advanced filter theo kho, người phụ trách, loại cảnh báo, khoảng ngày

#### BUG-012: Cùng một cảnh báo xuất hiện trùng lặp
- **Module:** M11
- **Mô tả:** "Framework Contract SC-FC-2026-04053 sắp hết hạn" xuất hiện 2 lần với cùng timestamp
- **Hướng xử lý:** Thêm deduplication logic; sử dụng unique constraint (alert_type + reference_doc + date)

#### BUG-013: Dropdown role trong tạo user dễ nhầm lẫn
- **Module:** User Management
- **Hướng xử lý:** Highlight rõ checkbox đang được chọn; tên role trong tooltip phải khớp với tên trong danh sách

---

## 5. BLINDSPOT VÀ ĐIỂM YẾU CHƯA ĐƯỢC BẢO PHỦ

### 5.1 Bảo mật & Phân quyền

| # | Blindspot | Mức độ rủi ro | Mô tả |
|---|-----------|:---:|-------|
| S1 | Không có Row-level security theo kho | 🔴 | Storekeeper của Kho Khoa Dược vẫn có thể xem/tạo phiếu nhập cho Kho ICU |
| S2 | Không có 4-eyes principle cho giao dịch lớn | 🟠 | Không có cơ chế yêu cầu 2 người xác nhận cho xuất kho giá trị lớn |
| S3 | Audit log chưa rõ ràng | 🟠 | Không có dedicated audit log page; lịch sử chỉnh sửa chỉ ở từng document |
| S4 | Không lock sau khi submit | 🟡 | Document sau khi Nhập vẫn có thể sửa bởi user có quyền cao |
| S5 | Thiếu password policy | 🟡 | Khi tạo user không hiển thị policy yêu cầu độ phức tạp mật khẩu |

### 5.2 Nghiệp vụ Bệnh viện

| # | Blindspot | Mức độ rủi ro | Mô tả |
|---|-----------|:---:|-------|
| B1 | Không có kiểm soát Cold Chain | 🔴 | Không có trường ghi nhận nhiệt độ bảo quản khi nhập/xuất vật tư sinh phẩm/vaccine |
| B2 | Thiếu quản lý thuốc gây nghiện/hướng thần | 🔴 | Không có category đặc biệt hay workflow riêng cho narcotics; vi phạm quy định Bộ Y tế |
| B3 | Không tích hợp với HIS/EMR | 🟠 | Cấp phát BN nhập tên thủ công; rủi ro sai tên, sai MRN |
| B4 | Thiếu quản lý hạn dùng sau khi mở (In-use expiry) | 🟠 | Một số thuốc/reagent có hạn dùng khác sau khi mở; hệ thống chỉ track HD gốc |
| B5 | Không có cảnh báo tương tác thuốc | 🟡 | Khi cấp phát BN không cảnh báo DDI (drug-drug interaction) |
| B6 | Thiếu quản lý vật tư một lần dùng vs tái sử dụng | 🟡 | Không phân biệt disposable (single-use) vs reusable items |

### 5.3 Luồng quy trình (Process Flow)

| # | Blindspot | Mô tả |
|---|-----------|-------|
| P1 | Không có cơ chế "Emergency request" | Khi khoa cần gấp ngoài giờ, không có fast-track workflow |
| P2 | Không có substitution logic | Khi vật tư hết tồn, hệ thống không gợi ý vật tư thay thế tương đương |
| P3 | Thiếu Par Level automation | Hệ thống có safety stock nhưng không tự động tạo Purchase Request khi xuống dưới ngưỡng |
| P4 | Không có trả hàng từ khoa về kho | Không có workflow "return to pharmacy" khi thuốc không dùng hết |
| P5 | Kiểm kê chỉ hỗ trợ "All Items" | Không hỗ trợ cycle counting (kiểm kê xoay vòng theo ABC) |

---

## 6. ĐỀ XUẤT TỐI ƯU

### 6.1 Ưu tiên cao nhất (Sprint tới)

1. **FIX BUG-001: Hard-stop tồn kho âm**
   - Thêm before_save validator: nếu projected_qty < 0 → raise ValidationError
   - Dùng frappe.db.get_value để kiểm tra stock_qty tại thời điểm submit

2. **FIX BUG-002: Tách available_qty và quarantine_qty**
   - Thêm trường qty_in_qc vào SC Batch và SC Stock Ledger Entry
   - Chỉ allow xuất kho từ (qty - qty_in_qc)

3. **IMPLEMENT Row-Level Security (S1)**
   - Map mỗi user Storekeeper → danh sách warehouse được phép
   - Dùng Frappe Permission Query Conditions

### 6.2 Tối ưu kiến trúc

**Bảo mật:**
- Implement JWT session timeout
- Thêm 2FA cho tài khoản Manager trở lên
- Log tất cả thao tác sensitive vào audit_log table riêng
- Implement field-level encryption cho thông tin bệnh nhân

**Performance:**
- Trang Tồn kho hiện tải toàn bộ 61 records; cần virtual scrolling / pagination
- Dashboard nên cache API với Redis, TTL 5 phút
- Lazy load module khi user chưa có quyền

**UX/UI:**
- Thêm breadcrumb navigation trên tất cả trang chi tiết
- Mobile responsive: sidebar menu chưa collapse trên màn hình < 1024px
- Thêm keyboard shortcut (Ctrl+S = Lưu, Ctrl+Enter = Submit)
- Toast notification nên có duration dài hơn (5s) và có nút undo
- Số liệu âm trong báo cáo nên highlight đỏ tự động

**Tích hợp:**
- Expose REST API cho HIS integration (Patient sync, auto dispensing record)
- Webhook khi tồn kho xuống dưới safety stock → gửi Zalo/Email alert
- Export báo cáo sang Excel (không chỉ CSV) với format template sẵn
- Tích hợp barcode/QR scanner để scan lô khi nhập/xuất

### 6.3 Compliance & Regulatory

- Thêm module "Báo cáo Bộ Y tế": tổng hợp xuất nhập tồn theo quy định
- Quản lý thuốc gây nghiện: workflow riêng với dual sign-off
- Nhật ký kiểm soát lạnh (Cold Chain Log): ghi nhiệt độ mỗi 4h
- Digital signature cho phiếu xuất/nhập quan trọng
- FIFO/FEFO enforcement: bắt buộc chọn lô theo FEFO khi cấp phát

---

## 7. TÓM TẮT SỐ LIỆU KIỂM THỬ

| Hạng mục | Số lượng |
|----------|----------|
| Module đã kiểm thử | 11/11 (100%) |
| User tạo mới | 5 |
| Transaction đã tạo | 2 (Phiếu nhập + Yêu cầu cấp phát) |
| Bug nghiêm trọng 🔴 | 3 |
| Bug cao 🟠 | 3 |
| Bug trung bình 🟡 | 3 |
| Bug thấp 🔵 | 4 |
| **Tổng bug** | **13** |
| Blindspot bảo mật | 5 |
| Blindspot nghiệp vụ | 6 |
| Blindspot process | 5 |

---

## 8. ĐÁNH GIÁ TỔNG THỂ

| Tiêu chí | Điểm | Nhận xét |
|----------|:----:|---------|
| Độ bao phủ chức năng | 7/10 | Đầy đủ luồng chính, thiếu cold chain & narcotics |
| UX/UI | 7/10 | Dashboard đẹp, bản đồ kho sáng tạo; form nhập đôi chỗ chưa intuitive |
| Bảo mật | 5/10 | Thiếu row-level security và audit log tập trung |
| Chất lượng dữ liệu | 5/10 | Tồn kho âm, đơn giá 0, trùng cảnh báo |
| Compliance | 4/10 | Thiếu nhiều yêu cầu pháp lý bệnh viện VN |
| Performance | 7/10 | UI loading chấp nhận được |
| **Điểm tổng** | **5.8/10** | Cần sửa bug nghiêm trọng và bổ sung compliance trước go-live |

---

*Báo cáo được tạo tự động bởi QA Agent — SupplyCore Testing Session 25/05/2026*
