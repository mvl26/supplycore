# SupplyCore QA Report v2 — Kiểm thử Toàn diện
**Hệ thống:** SupplyCore v0.2.0 — Quản lý Cung ứng Bệnh viện
**Người kiểm thử:** buihoangviet (SupplyCore Executive)
**Ngày kiểm thử:** 25/05/2026
**Phiên bản báo cáo:** v2.0 (Lần kiểm thử 2 — Toàn diện)
**URL hệ thống:** https://blockishly-unvowed-anglea.ngrok-free.dev/supplycore/

---

## MỤC LỤC

1. [Tổng quan hệ thống](#1-tong-quan)
2. [Người dùng & Phân quyền đã tạo](#2-users)
3. [Kết quả kiểm thử theo Module](#3-modules)
4. [Danh sách Bug (Tổng hợp 2 vòng)](#4-bugs)
5. [Điểm mù & Rủi ro nghiệp vụ](#5-blindspots)
6. [Đánh giá & Điểm số](#6-score)
7. [Hướng tối ưu & Khuyến nghị](#7-recommendations)

---

## 1. Tổng quan hệ thống {#1-tong-quan}

| Thông tin | Giá trị |
|---|---|
| Tên hệ thống | SupplyCore v0.2.0 |
| Phân loại | Phần mềm quản lý cung ứng – kho – tài chính bệnh viện |
| Số module | 12 module chính (M0–M11) + 6 chức năng phụ |
| Tổng số kho | 17 kho (68 bin locations) |
| Tổng vật tư | 160+ SLE (Stock Location Entry) |
| Tổng hợp đồng | 39 hợp đồng khung |
| Tổng lô hàng | 57 lô (batch) |
| Tổng nhân viên hệ thống | 20+ user |
| Số cảnh báo mở | 9 (7 critical) |
| Tổng nợ NCC | 55.165.000 VND |
| Chi phí vật tư tháng 5/2026 | 102.328.600 VND |

---

## 2. Người dùng & Phân quyền đã tạo {#2-users}

Đã tạo 5 user mới với các role điển hình trong bệnh viện:

| STT | Email | Họ tên | Vai trò | Mô tả |
|---|---|---|---|---|
| 1 | thuho.khodoc@hospital.vn | Nguyễn Thị Thu Hương | Storekeeper | Thủ kho dược |
| 2 | duocsi.tran@hospital.vn | Trần Minh Đức | Pharmacy Officer | Dược sĩ cấp phát |
| 3 | ketoan.le@hospital.vn | Lê Thị Hồng Như | Accountant | Kế toán kho |
| 4 | bacsi.nguyen@hospital.vn | Nguyễn Văn An | Department Requester | Bác sĩ yêu cầu vật tư |
| 5 | truongkhoa.pham@hospital.vn | Phạm Văn Minh | Manager | Trưởng khoa |

**Phát hiện:** Hệ thống có sẵn 14 role – đủ bao phủ hầu hết vị trí trong bệnh viện.

---

## 3. Kết quả kiểm thử theo Module {#3-modules}

### M0 — Dữ liệu nền (Master Data)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách vật tư | ✅ Hoạt động | 160+ items |
| Tạo mới vật tư | ✅ Hoạt động | Đã tạo TEST-ITEM-001 |
| Validate form rỗng | ✅ Highlight đúng | Các trường bắt buộc highlight đỏ |
| Danh sách NCC | ✅ Hoạt động | |
| Tạo NCC rỗng | ✅ Validate | Form validate đúng |
| Auto-fill "Mức tái đặt" | ⚠️ Bug | Auto-set = 0, không cảnh báo |
| MST validation | ⚠️ Bug | Không validate định dạng MST VN |

### M1 — Hợp đồng (Contract Management)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách hợp đồng | ✅ Hoạt động | 39 hợp đồng |
| Xem chi tiết | ✅ Hoạt động | SC-FC-2026-04476 |
| Tạo hợp đồng mới | ✅ Form mở được | |
| Trạng thái hợp đồng hết hạn | ⚠️ Bug | Vẫn hiển thị "Hiệu lực" dù remaining=0 |
| Trường tiếng Anh | ⚠️ Bug | used_value, committed_value chưa dịch |
| Trường giá trị HĐ | ⚠️ Bug | Phải là read-only, tự tính |

### M2 — Kế hoạch & Mua sắm (Purchase Planning)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách MR | ✅ Hoạt động | |
| Tạo MR mới | ✅ Hoạt động | SC-MR-2026-04617 đã tạo |
| Lưu MR | ✅ Thành công | |
| Gửi duyệt | 🔴 CRITICAL BUG | Trang đóng băng ~90 giây |
| Unit price auto-fill | ⚠️ Bug | Tự điền = 0 cho items có HĐ khung |

### M3 — Tiếp nhận (Goods Receipt)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách PR | ✅ Hoạt động | 27 PRs |
| Tạo PR mới | ✅ Hoạt động | SC-PR-2026-04616 |
| Form QC mới | ✅ Form mở được | |
| Trạng thái PR | ⚠️ Bug | Hiện "Chờ duyệt" trước khi gửi |
| QC không cần PR | ⚠️ Bug | Tạo QC độc lập không cần link PR |
| QC checklist | ⚠️ Bug | Template không bắt buộc |

### M4 — Quản lý kho (Warehouse Management)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách kho | ✅ Hoạt động | 17 kho |
| Bin locations | ✅ Hoạt động | 68 bins |
| SLE | ✅ Hoạt động | 160+ |
| Bin naming | ⚠️ Bug | Tên bin là hash code (TEST-BIN-04AC0L) |

### M5 — Quản lý lô vật tư (Batch Management)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách lô | ✅ Hoạt động | 57 lô |
| Xem chi tiết lô | ✅ Hoạt động | |
| Test data trong production | 🔴 CRITICAL | Lô "asdasd" trong hệ thống |
| Batch ID với "/" | ⚠️ Bug | lo/19/05/2026 — URL encoding lỗi |
| NSX/SX date | ⚠️ Bug | Không bắt buộc |

### Bản đồ kho (Warehouse Map)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Hiển thị sơ đồ | ✅ Hoạt động | Sơ đồ 2D bệnh viện |
| Click vào kho | ✅ Hoạt động | Kho Dược — 2 bins |
| Bin layout | ✅ Hiển thị | |

### M6 — Chuyển kho (Warehouse Transfer)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách Transfer | ✅ Hoạt động | |
| Tạo phiếu chuyển | ✅ Form mở được | |
| Validate nguồn = đích | 🔴 CRITICAL | Cho phép chọn trùng kho nguồn & đích |
| Hiển thị tồn kho âm | ⚠️ Bug | Nguồn hiện "Kho trống" dù có âm |

### M7 — Cấp phát (Dispensing)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách PD | ✅ Hoạt động | 13 records |
| Xem chi tiết | ✅ Hoạt động | SC-PD-2026-04542 |
| Cột "Khoa" trống | ⚠️ Bug | Nhiều record không có khoa |
| Test data bệnh nhân | ⚠️ Bug | "Nguyễn Văn UAT-DOC" trong tên |
| Field không dịch | ⚠️ Bug | "dispensing_request" tiếng Anh |
| Vượt trần BHYT | ⚠️ Bug | Cột "Vượt trần" trống |

### Xếp hàng lên kệ (Putaway)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách putaway | ✅ Hoạt động | 68 items pending |
| Items KCS pending | ⚠️ Bug | Items chưa QC hiện trong putaway |
| Items không có lô | ⚠️ Bug | Items không có batch number |

### M8 — Kế toán (Accounting)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| GL Entry list | ✅ Hoạt động | 60 entries |
| Cột "bucket" | ⚠️ Bug | Tiêu đề cột tiếng Anh |
| Tên tài khoản | ⚠️ Bug | GL Entry list không hiện tên TK |
| Báo cáo tồn kho — giá trị | ✅ Hoạt động | 61 rows |
| Vật tư giá 0 | 🔴 CRITICAL | Items với đơn giá = 0 |
| Báo cáo Aging | ✅ Hoạt động | 55.165.000 VND outstanding |
| Chi phí vật tư kỳ | ✅ Hoạt động | 102.328.600 VND |
| SUBTOTAL không dịch | ⚠️ Bug | Column header tiếng Anh |
| Cảnh báo chưa khóa sổ | ✅ Hiển thị | Pi=1, PE=0, PD=1 draft |
| Mã loại chứng từ | ⚠️ Bug | Pi/PE/PD không giải thích cho user |
| Quyết toán BHYT | ✅ Hoạt động | 933.4k tổng, 627.6k BHYT |
| "NoBHYT" code | ⚠️ Bug | Không dịch sang tiếng Việt |
| Record không có Khoa | ⚠️ Bug | Nhiều dòng blank Khoa |

### M9 — Kiểm kê (Inventory Count)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách ICS | ✅ Hoạt động | 8 phiếu |
| Tạo ICS mới | ✅ Form mở được | |
| Summary fields | ⚠️ Bug | Tổng items, sai lệch — cho phép sửa |

### M10 — Truy xuất & Thu hồi (Recall)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Danh sách Recall | ✅ Hoạt động | |
| Chi tiết SC-RCL-2026-04367 | ✅ Hoạt động | 100% resolution tracking |
| Batch trace | ✅ Hoạt động | DTRC-GLU5-202711-001 |
| Missing manufacturer | ⚠️ Bug | NSX info trống trong trace |

### M11 — Dashboard & Cảnh báo (Monitoring)

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Alert list | ✅ Hoạt động | 9 open, 7 critical |
| Alert Rules | ✅ Hoạt động | |
| [TEST] UAT Alert | 🔴 CRITICAL | Test alert trong production |
| 15+ UAT Alert Rules | 🔴 CRITICAL | Test rules trong production |
| Alert types tiếng Anh | ⚠️ Bug | qc_pending, low_stock... |

### Tồn kho

| Chức năng | Kết quả | Ghi chú |
|---|---|---|
| Stock balance list | ✅ Hoạt động | |
| Tồn kho âm | 🔴 CRITICAL | VTTH-GLOVE-S = -655, DTRC-GLU5 = -228k |

---

## 4. Danh sách Bug Toàn bộ {#4-bugs}

### 🔴 CRITICAL (Ảnh hưởng dữ liệu / Nghiệp vụ / Bảo mật)

| Mã bug | Module | Mô tả | Tái hiện |
|---|---|---|---|
| BUG-M2-02 | M2 Kế hoạch | "Gửi duyệt" button làm trang đóng băng ~90 giây | Tạo MR → click "Gửi duyệt" |
| BUG-M6-01 | M6 Chuyển kho | Cho phép chọn cùng kho làm nguồn VÀ đích | Tạo Transfer → chọn Kho A → Kho A |
| BUG-STOCK-01 | Tồn kho | Tồn kho âm: VTTH-GLOVE-S = -655, DTRC-GLU5 = -228k | Xem Tồn kho |
| BUG-M8-PRICE | M8 Kế toán | Items với đơn giá = 0 xuất hiện trong báo cáo tài chính | Báo cáo Tồn kho — giá trị |
| BUG-M11-03 | M11 Cảnh báo | 15+ "UAT Alert" test rules tồn tại trong môi trường production | Danh sách Alert Rules |
| BUG-M5-01 | M5 Lô hàng | Lô test "asdasd" tồn tại trong production | Danh sách lô |

### 🟠 HIGH (Logic nghiệp vụ / Tuân thủ)

| Mã bug | Module | Mô tả | Tác động |
|---|---|---|---|
| BUG-M1-02 | M1 Hợp đồng | HĐ đã dùng hết (remaining=0) vẫn hiển thị "Hiệu lực" | Cho phép tạo MR sai HĐ |
| BUG-M1-04 | M1 Hợp đồng | Trường tổng giá trị HĐ cho phép sửa (phải là read-only tự tính) | Sai tổng giá trị HĐ |
| BUG-M2-01 | M2 Kế hoạch | Unit price tự điền = 0 cho items có HĐ khung | MR tạo ra với giá = 0 |
| BUG-M3-01 | M3 Tiếp nhận | PR trạng thái "Chờ duyệt" trước khi thực sự gửi duyệt | Sai workflow, gây nhầm lẫn |
| BUG-M3-02 | M3 Tiếp nhận | QC có thể tạo không cần link với PR | Bypass quy trình kiểm nhận |
| BUG-M6-02 | M6 Chuyển kho | Kho nguồn hiện "Kho trống" dù có tồn kho âm | Không phát hiện âm kho |
| BUG-M7-05 | M7 Cấp phát | Cột "Vượt trần" BHYT trống, không có validation | Vi phạm quy định BHYT |
| BUG-M9-01 | M9 Kiểm kê | Summary fields (tổng items, sai lệch) cho phép chỉnh sửa | Làm sai kết quả kiểm kê |
| BUG-M11-01 | M11 Cảnh báo | Alert "[TEST] UAT Alert" trong danh sách production | Nhiễu cảnh báo thực |

### 🟡 MEDIUM (UX / Tích hợp / Hiệu năng)

| Mã bug | Module | Mô tả |
|---|---|---|
| BUG-M0-01 | M0 Dữ liệu nền | "Mức tái đặt" auto-set = 0 không cảnh báo |
| BUG-M0-02 | M0 Dữ liệu nền | MST không validate định dạng Việt Nam |
| BUG-M1-03 | M1 Hợp đồng | Trường used_value, committed_value không dịch tiếng Việt |
| BUG-M3-03 | M3 Tiếp nhận | QC Checklist Template không bắt buộc |
| BUG-M5-02 | M5 Lô hàng | "/" trong batch ID gây lỗi URL encoding |
| BUG-M5-03 | M5 Lô hàng | URL routing lỗi với "/" trong tên lô |
| BUG-M5-04 | M5 Lô hàng | NSX (nhà sản xuất) và ngày SX không bắt buộc |
| BUG-M7-01 | M7 Cấp phát | Cột "Khoa" trống cho nhiều records |
| BUG-M7-03 | M7 Cấp phát | Cấp phát từ khoa không có kho riêng được cho phép |
| BUG-M8-02 | M8 Kế toán | Column "SUBTOTAL" không dịch tiếng Việt |
| BUG-M8-05 | M8 Kế toán | Nhiều dòng Quyết toán BHYT không có "Khoa" |
| BUG-M8-06 | M8 Kế toán | "NoBHYT" code không dịch (nên là "Không có BHYT") |
| BUG-PUTAWAY-01 | Putaway | Items KCS-Pending xuất hiện trong danh sách putaway |
| BUG-PUTAWAY-02 | Putaway | Items không có batch number trong putaway |

### 🔵 LOW (Giao diện / Cosmetic / Dịch thuật)

| Mã bug | Module | Mô tả |
|---|---|---|
| BUG-BIN-01 | M4/Bản đồ kho | Tên bin là hash code (TEST-BIN-04AC0L) thay vì tên có ý nghĩa |
| BUG-M7-02 | M7 Cấp phát | Tên bệnh nhân test "Nguyễn Văn UAT-DOC" trong production |
| BUG-M7-04 | M7 Cấp phát | Field "dispensing_request" không dịch tiếng Việt |
| BUG-M8-01 | M8 Kế toán | GL Entry list không hiện tên tài khoản, chỉ có mã |
| BUG-M8-03 | M8 Kế toán | Cảnh báo chưa khóa sổ dùng mã kỹ thuật Pi/PE/PD |
| BUG-M11-02 | M11 Cảnh báo | Alert types tiếng Anh: qc_pending, low_stock, expiry_warning |

---

## 5. Điểm mù & Rủi ro nghiệp vụ {#5-blindspots}

### 5.1 Rủi ro Tài chính
- **Tồn kho âm không được chặn**: Hệ thống cho phép tồn kho xuống âm mà không có cơ chế ngăn chặn hoặc cảnh báo ngay tại điểm xuất kho. Với DTRC-GLU5 = -228.000 đơn vị và VTTH-GLOVE-S = -655, đây là lỗ hổng nghiêm trọng.
- **Items giá = 0**: Vật tư có đơn giá = 0 ảnh hưởng đến toàn bộ báo cáo tài chính, valuation tồn kho, và quyết toán BHYT.
- **Hợp đồng hết hạn vẫn "Hiệu lực"**: Nguy cơ tạo đơn mua sai hợp đồng.

### 5.2 Rủi ro Quy trình
- **Gửi duyệt MR đóng băng 90 giây**: Toàn bộ quy trình mua sắm bị nghẽn tại đây. Nếu server timeout, MR có thể ở trạng thái không xác định.
- **QC bypass**: Tạo QC không cần PR link có nghĩa là có thể nhập kho mà không qua quy trình tiếp nhận chính thống.
- **Transfer kho nguồn = đích**: Có thể tạo bút toán ảo làm sai lệch số liệu kho.

### 5.3 Rủi ro Tuân thủ BHYT
- **Không validate vượt trần BHYT**: Hệ thống không kiểm tra ceiling khi cấp phát cho bệnh nhân BHYT — vi phạm quy định thanh toán BHYT.
- **NoBHYT records trong BHYT report**: Dữ liệu lộn xộn giữa bệnh nhân BHYT và không BHYT.

### 5.4 Rủi ro Dữ liệu
- **Test data trong production**: 15+ UAT Alert Rules, lô "asdasd", tên "Nguyễn Văn UAT-DOC" — hệ thống chưa được dọn sạch trước khi đưa vào sản xuất.
- **Batch ID với "/" ký tự đặc biệt**: Gây lỗi URL routing, không thể truy cập chi tiết lô.
- **Không có audit trail rõ ràng**: Không thấy log ai đã sửa/xóa dữ liệu.

### 5.5 Điểm mù về Bảo mật
- **Phân quyền theo chức năng**: Cần kiểm tra xem Department Requester có thể tạo MR không? Storekeeper có thể approve không?
- **Không có 2FA**: Với dữ liệu nhạy cảm (BHYT, tài chính), không thấy cơ chế xác thực 2 bước.
- **Session management**: Ngrok URL public — cần xem xét cơ chế bảo vệ.

---

## 6. Đánh giá & Điểm số {#6-score}

| Hạng mục | Điểm | Nhận xét |
|---|---|---|
| Tính đầy đủ chức năng | 7/10 | Đủ module, nhưng một số chức năng chưa hoàn thiện |
| Độ ổn định | 5/10 | Freeze M2, URL bug M5, âm kho nghiêm trọng |
| Trải nghiệm người dùng (UX) | 6/10 | Giao diện tương đối tốt nhưng nhiều field tiếng Anh |
| Tuân thủ nghiệp vụ | 5/10 | BHYT ceiling không validate, QC có thể bypass |
| Chất lượng dữ liệu | 4/10 | Test data trong production, tồn kho âm, giá = 0 |
| Bảo mật & Phân quyền | 6/10 | Có RBAC nhưng chưa kiểm tra đầy đủ |
| **Tổng hợp** | **5.5/10** | **Cần cải thiện đáng kể trước khi go-live chính thức** |

---

## 7. Hướng tối ưu & Khuyến nghị {#7-recommendations}

### Ưu tiên 1 — Phải sửa ngay (P0)

1. **Fix freeze M2 "Gửi duyệt"**: Kiểm tra API endpoint /submit, thêm timeout handling, loading state, và error feedback. Có thể do synchronous call hoặc deadlock DB.
2. **Chặn tồn kho âm**: Thêm validation ở tầng backend — không cho phép PD/chuyển kho nếu tồn kho không đủ. Hiển thị cảnh báo real-time ở form cấp phát.
3. **Xóa toàn bộ test data production**: Script SQL để purge tất cả records có "[TEST]", "UAT", "asdasd" trong production.
4. **Fix transfer nguồn = đích**: Thêm validation: `if (source_warehouse == dest_warehouse) { block + show error }`
5. **Items giá = 0**: Bắt buộc nhập đơn giá khi tạo item; cảnh báo trong báo cáo tài chính.

### Ưu tiên 2 — Sửa trước go-live (P1)

6. **BHYT ceiling validation**: Khi cấp phát, tính tổng chi phí và so với trần BHYT. Block nếu vượt, hoặc yêu cầu approval.
7. **Fix trạng thái workflow**: PR không được "Chờ duyệt" trước khi gửi. MR unit price phải lấy từ HĐ khung, không điền = 0.
8. **Bắt buộc link QC với PR**: Kiểm soát để không tạo QC độc lập.
9. **Batch ID không được chứa "/"**: Validate batch ID, thay bằng "-" hoặc UUID.
10. **Summary fields trong ICS phải read-only**: Tính toán tự động từ chi tiết kiểm kê.

### Ưu tiên 3 — Cải thiện UX (P2)

11. **Dịch toàn bộ field tiếng Anh**: used_value, committed_value, bucket, SUBTOTAL, NoBHYT, dispensing_request, qc_pending, low_stock.
12. **Tên bin location có ý nghĩa**: Thay hash code bằng tên theo vị trí (A1-01, A1-02...).
13. **GL Entry hiển thị tên tài khoản**: Thêm cột "Tên TK" bên cạnh mã TK.
14. **Mô tả rõ mã chứng từ**: Giải thích Pi=Purchase Invoice, PE=Purchase Error, PD=Patient Dispensing trong giao diện.

### Ưu tiên 4 — Tối ưu dài hạn (P3)

15. **Real-time stock validation**: Hiển thị số tồn kho hiện tại ngay trong form cấp phát/chuyển kho.
16. **Audit trail đầy đủ**: Log mọi thao tác thay đổi dữ liệu (ai, khi nào, thay đổi gì).
17. **Dashboard cảnh báo thông minh hơn**: Phân nhóm cảnh báo theo khoa, ưu tiên, loại — hiện tại 9 alerts không đủ context.
18. **Khóa sổ tự động**: Nhắc nhở kế toán khóa sổ kỳ theo lịch; cảnh báo khi sắp đến hạn.
19. **API performance**: Xem xét lazy loading, pagination API để tránh freeze khi dataset lớn.
20. **Test environment riêng biệt**: Đảm bảo không có cross-contamination giữa UAT và production.

---

## PHỤ LỤC — Dữ liệu kiểm thử

### Dữ liệu tạo mới trong quá trình test

| Loại | ID | Mô tả |
|---|---|---|
| Item | TEST-ITEM-001 | Vật tư test — cần xóa sau testing |
| MR | SC-MR-2026-04617 | Yêu cầu mua VTTH-GLOVE-S 200 đơn vị |

### Danh sách URL đã kiểm thử

```
/supplycore/dashboard
/supplycore/users
/supplycore/m0 (Master Data)
/supplycore/m1 (Contracts)
/supplycore/m2 (Purchase Planning)
/supplycore/m3 (Goods Receipt)
/supplycore/m4 (Warehouse Mgmt)
/supplycore/m5 (Batch Mgmt)
/supplycore/warehouse-map
/supplycore/m6 (Transfer)
/supplycore/m7 (Dispensing)
/supplycore/list/SC Patient Dispensing
/supplycore/putaway
/supplycore/m8 (Accounting)
/supplycore/list/SC GL Entry
/supplycore/m9 (Inventory Count)
/supplycore/doc/SC Inventory Count Sheet/new
/supplycore/m10 (Recall & Trace)
/supplycore/m11 (Dashboard & Alerts)
/supplycore/list/SC Alert Rule
/supplycore/financial-reports (all 4 tabs)
/supplycore/stock-balance
/supplycore/batch-trace
/supplycore/alerts
```

---

*Báo cáo được tạo tự động bởi Claude (Anthropic) — SupplyCore QA Session 25/05/2026*
*Tổng số bug: 38 | Critical: 6 | High: 9 | Medium: 14 | Low: 9*
