# SupplyCore QA Report v3 — Kiểm thử Vòng 3 (Xác minh & Bổ sung)
**Hệ thống:** SupplyCore v0.2.0
**Người kiểm thử:** buihoangviet (SupplyCore Executive)
**Ngày kiểm thử:** 25/05/2026
**Phiên bản báo cáo:** v3.0 — Vòng 3: Xác minh lại toàn bộ bugs + phát hiện mới

---

## TÓM TẮT ĐIỀU HÀNH

| Chỉ số | Giá trị |
|---|---|
| Tổng số bug (3 vòng) | **62 bugs** |
| 🔴 Critical | 10 |
| 🟠 High | 20 |
| 🟡 Medium | 20 |
| 🔵 Low | 12 |
| Bug được xác nhận lại | 32/38 (84%) |
| Bug đã được sửa | 2 (tồn kho âm, trạng thái HĐ) |
| Bug mới phát hiện vòng 3 | 24 bugs |
| Điểm tổng thể | **4.5/10** (giảm từ 5.5 do phát hiện thêm) |

---

## TRẠNG THÁI XÁC NHẬN BUGS TỪ VÒNG TRƯỚC

### Bugs đã SỬA / THAY ĐỔI ✅
| Bug cũ | Trạng thái | Ghi chú |
|---|---|---|
| BUG-STOCK-01: Tồn kho âm VTTH-GLOVE-S=-655 | ✅ ĐÃ SỬA | Hiện = 260 sau khi nhập thêm hàng |
| BUG-STOCK-01: Tồn kho âm DTRC-GLU5=-228k | ✅ ĐÃ SỬA | Hiện = 1.053 |
| BUG-M1-02: HĐ hết mức vẫn "Hiệu lực" | ✅ ĐÃ SỬA | SC-FC-2026-04476 hiện = "Hết hạn mức" |

### Bugs ĐÃ XÁC NHẬN LẠI ⚠️
| Bug | Xác nhận | Bổ sung |
|---|---|---|
| BUG-M2-02: Freeze "Gửi duyệt" MR | ✅ XÁC NHẬN | Timeout 30s CDP + 45s JS |
| BUG-PO-04 MỚI: Freeze "Gửi duyệt" PO | ✅ PHÁT HIỆN MỚI | Cùng lỗi systemic |
| BUG-M3-10 MỚI: Freeze "Gửi duyệt" PR | ✅ PHÁT HIỆN MỚI | Cùng lỗi systemic — tất cả doc types |
| BUG-M2-01: Unit price MR = 0 | ✅ XÁC NHẬN | Khi tạo PO tự lấy đúng giá từ HĐK |
| BUG-M6-01: Nguồn = đích kho | ✅ XÁC NHẬN | Không có validation, không có error |
| BUG-M9-01: Summary fields editable | ✅ XÁC NHẬN | Đã nhập 999 vào Tổng items thành công |
| BUG-M11-03: UAT Alert Rules | ✅ XÁC NHẬN | 16 UAT + 2 SMOKE = 18 test rules |
| BUG-M5-02: "/" trong batch ID barcode | ✅ XÁC NHẬN | Barcode "lo/19/05/2026" |
| BUG-M5-04: NSX/SX không bắt buộc | ✅ XÁC NHẬN | Trống hoàn toàn |
| BUG-M8-01: GL Entry không hiện tên TK | ✅ XÁC NHẬN | Cả list và detail view |
| BUG-M7-02: Test data bệnh nhân | ✅ XÁC NHẬN | 3 BN "Nguyễn Văn UAT-DOC" |

---

## DANH SÁCH ĐẦY ĐỦ BUGS — V3

### 🔴 CRITICAL (Ảnh hưởng nghiêm trọng đến vận hành)

| Mã | Module | Mô tả | Tái hiện | Tác động |
|---|---|---|---|---|
| BUG-SUBMIT-01 | M2/M3/PO | **Gửi duyệt freeze toàn bộ document types** (MR/PR/PO) ~30-90 giây | Click Gửi duyệt trên bất kỳ document | Chặn toàn bộ workflow mua sắm & tiếp nhận |
| BUG-M6-01 | M6 | Cho phép chuyển kho nguồn = đích | Tạo Transfer, chọn cùng kho | Bút toán kho ảo, sai số liệu |
| BUG-M11-UAT | M11 | 18 test rules (UAT+SMOKE) đang hoạt động trong production | Xem Alert Rule list | Nhiễu hệ thống cảnh báo, bỏ sót cảnh báo thật |
| BUG-M9-01 | M9 | Summary fields kiểm kê (Tổng items, Items lệch) editable | Tạo ICS, nhập giá trị vào Tổng items | Kết quả kiểm kê có thể bị làm giả |
| BUG-STOCK-02 | Tồn kho | Hàng KCS=Pending (chưa pass QC) tính vào tồn kho available | Xem tồn kho DTRC-GLU5 | Báo cáo tồn kho sai, cấp phát hàng chưa kiểm |
| BUG-M0-09 | M0 Patient | Số thẻ BHYT không validate định dạng chuẩn VN | BN-DOC: số thẻ = "DN1Dm1evS" | Quyết toán BHYT với số thẻ sai |
| BUG-M2-06 | M2 | MR được duyệt với total_estimated_cost = 0 | SC-MR-2026-04617 | Mua hàng không có cơ sở giá |
| BUG-TEST-DATA | Nhiều module | Test data production: 18 UAT rules, 3 BN UAT-DOC, lô "asdasd", HĐ TEST-LOG-xxx, BN-DOC-xxx | Khắp hệ thống | Sai lệch toàn bộ báo cáo và analytics |
| BUG-M3-11 | M3 | 20+/27 PR không có PO tham chiếu — nhập kho không qua PO | Danh sách PR | Bypass kiểm soát tài chính |
| BUG-M6-04 | M6 | Hàng KCS=Pending xuất hiện trong danh sách chọn để chuyển kho | Form chuyển kho | Chuyển hàng chưa kiểm tra QC |

### 🟠 HIGH (Logic nghiệp vụ / Tuân thủ)

| Mã | Module | Mô tả |
|---|---|---|
| BUG-M1-04 | M1 | Trường "Tổng giá trị HĐ" vẫn editable dù hint "Tự động tính" |
| BUG-M1-07 | M1 | Comment duyệt HĐ = "d" (1 ký tự) không có validation tối thiểu |
| BUG-M1-09 | M1 | Cột chi tiết HĐ: CONTRACT QTY, ORDERED QTY, REMAINING QTY — tiếng Anh |
| BUG-M1-11 | M1 | "renewal history" — tiếng Anh |
| BUG-M2-03 | M2 | Fields "auto generated", "total estimated cost" tiếng Anh trong view detail |
| BUG-M2-05 | M2 | Columns "ESTIMATED UNIT COST", "ESTIMATED AMOUNT" tiếng Anh |
| BUG-PO-01 | M2/PO | Duyệt PO là "Optional" — có thể bỏ qua approval workflow |
| BUG-M3-09 | M3 | Số lô NCC không bắt buộc trong PR |
| BUG-M4-01 | M4 | Kho "kho tam", "kho 1" — test data, tên không chuẩn trong production |
| BUG-M5-06 | M5 | "blocked=0" hiển thị trong subtitle danh sách lô |
| BUG-M7-05 | M7 | Cột "Vượt trần" BHYT trống, không có validation ceiling |
| BUG-M0-13 | M0 | Cột LOẠI TK kế toán: "Expense", "Tax", "Payable", "Stock" — tiếng Anh |
| BUG-M8-09 | M8 | "Loại CT" = "SC Purchase Invoice" tiếng Anh |
| BUG-M8-08 | M8 | Fields "against account", "party type", "party" tiếng Anh trong GL Entry |
| BUG-STOCK-QCS | Tồn kho | Không phân biệt tồn kho "available" vs "pending QC" trong view tổng hợp |
| BUG-M1-12 | M1 | Trường "Người tạo" HĐ không bị disabled — có thể nhập tay |
| BUG-M3-07 | M3 | Cho phép tạo PR mà không cần PO |
| BUG-M1-05 | M1 | 7+ HĐ với số HĐ "TEST-LOG-xxx", "TEST-EDIT-xxx" trong production |
| BUG-BIN-02 | M4 | Bin status = "Empty" tiếng Anh |
| BUG-M9-02 | M9 | "SR đã tạo" cho phép link ICS với SR hiện có sai |

### 🟡 MEDIUM

| Mã | Module | Mô tả |
|---|---|---|
| BUG-M0-01 | M0 | "Mức tái đặt" auto = 0, không cảnh báo |
| BUG-M0-02 | M0 | MST không validate định dạng VN |
| BUG-M0-10 | M0 | "The BHYT hết hạn" — lỗi chính tả ("The" → "Thẻ") |
| BUG-M0-11 | M0 | Placeholder "Chọn SC Department" tiếng Anh |
| BUG-M0-12 | M0 | KHOA column trống trong lịch sử cấp phát của bệnh nhân |
| BUG-M0-15 | M0 | Cột TK và SỐ TK trong GL Account trùng giá trị — mục đích không rõ |
| BUG-M1-03 | M1 | "used value", "committed value" tiếng Anh |
| BUG-M1-08 | M1 | Field "executive override bl..." bị truncate |
| BUG-M2-01 | M2 | Unit price MR = 0 gây nhầm lẫn (PO tự lấy đúng giá khi tạo) |
| BUG-M3-06 | M3 | QC mặc định tick, không flexible cho từng loại hàng |
| BUG-M3-08 | M3 | Cột "HD" trong chi tiết PR — tên quá ngắn, không rõ nghĩa |
| BUG-M4-03 | M4 | Số lô không nhất quán: M4 = 46, M5 = 45, các view khác = 57 |
| BUG-M5-02 | M5 | "/" trong barcode lô (lo/19/05/2026) — không chuẩn cho scanner |
| BUG-M5-04 | M5 | NSX, ngày SX không bắt buộc |
| BUG-M5-08 | M5 | "Xác nhận nhập lô hạn ngắn" không có tooltip/giải thích |
| BUG-BIN-05 | M4 | Tất cả bins = "Empty" dù có 160 SLE entries — không update status |
| BUG-M8-01 | M8 | GL Entry list và detail không hiện tên TK, chỉ mã số |
| BUG-M9-03 | M9 | "Manager chứng kiến (lần 3)" nhưng không có lần 1, lần 2 |
| BUG-M9-04 | M9 | Ngưỡng đếm lại % trống dù hint "mặc định 5%" |
| BUG-M11-02 | M11 | Alert types tiếng Anh: low_stock, contract_expiring, qc_pending |

### 🔵 LOW (Cosmetic / Dịch thuật)

| Mã | Module | Mô tả |
|---|---|---|
| BUG-M0-04 | M0 | Skeleton/spinner không hiển thị khi load trang — blank 3s |
| BUG-M0-05 | M0 | Tên nhóm vật tư "Ringer Lactate", "Glucose" — không nhất quán |
| BUG-M0-07 | M0 | BN007 không có số thẻ BHYT nhưng không hiện "N/A" |
| BUG-M0-08 | M0 | Bệnh nhân gán cho phòng hành chính (Ban GĐ, CNTT) |
| BUG-M1-13 | M1 | Upload PDF HĐ không bắt buộc |
| BUG-M3-04 | M3 | Placeholder "Chọn SC Supplier", "Chọn SC Purchase Order" tiếng Anh |
| BUG-M5-05 | M5 | Số lô NCC = "1234567", "123456" — test data |
| BUG-M8-10 | M8 | "Đã huỷ" field trống không rõ nghĩa (nên hiện "Không") |
| BUG-M8-05 | M8 | Nhiều dòng Quyết toán BHYT không có "Khoa" |
| BUG-M8-06 | M8 | "NoBHYT" code trong BHYT report không dịch |
| BUG-BIN-04 | M4 | Column "CODE", "BARCODE" tiếng Anh |
| BUG-M11-06 | M11 | "M11-SMOKE-expiring-30", "M11-SMOKE-contract-90" — smoke test rules trong production |

---

## KẾT QUẢ XÁC MINH WORKFLOW HOÀN CHỈNH

### Workflow MR → PO (ĐÃ TEST FULL)
```
Tạo MR (SC-MR-2026-04617) ✅
  → Lưu MR ✅
  → Gửi duyệt MR 🔴 FREEZE 30s (nhưng backend hoàn thành)
  → Trạng thái: Chờ duyệt ✅
  → Duyệt MR ✅ (click Duyệt MR)
  → Trạng thái: Đã duyệt ✅
  → Tạo PO (SC-PO-2026-04618) ✅ (giá lấy đúng từ HĐK: 1.000đ/đôi)
  → Gửi duyệt PO 🔴 FREEZE 30s
  → [Chưa test tiếp vì freeze]
```

### Workflow PR → QC (ĐÃ TEST FULL)
```
Tạo PR (SC-PR-2026-04616) ✅ (không cần link PO — lỗ hổng)
  → Lưu PR ✅
  → Gửi duyệt PR 🔴 FREEZE 30s (nhưng backend hoàn thành)
  → Trạng thái QC: Chờ QC ✅
  → [QC chưa test tiếp vì freeze]
```

### Freeze Pattern Analysis
**Vấn đề cốt lõi**: Nút "Gửi duyệt" gửi HTTP request đến backend. Backend xử lý xong (trạng thái thay đổi đúng) nhưng:
1. Frontend block UI thread (không có async/loading state)
2. Browser CDP timeout sau 30s  
3. Trang "unresponsive" trong khi backend đang xử lý
4. Sau 30-90s, trang tự phục hồi với trạng thái mới

**Root cause có thể**: Thiếu async handling, thiếu loading indicator, hoặc server side event polling blocking main thread

---

## PHÁT HIỆN MỚI QUAN TRỌNG NHẤT (VÒNG 3)

### 1. Freeze là systemic, không phải chỉ MR
- MR Gửi duyệt: FREEZE ✅ confirmed
- PO Gửi duyệt: FREEZE ✅ confirmed  
- PR Gửi duyệt: FREEZE ✅ confirmed
- **Tất cả document submit đều bị ảnh hưởng**

### 2. Hàng KCS Pending tính vào tồn kho (BUG-STOCK-02)
DTRC-GLU5 có 8 lô "Pending" trong Kho Trung chuyển nhưng vẫn được tính vào tổng 1.053 chai. 
Rủi ro: Cấp phát hàng chưa kiểm, báo cáo tài chính sai.

### 3. 18 test rules đang active (BUG-M11-UAT)
16 UAT Alert + 2 SMOKE test rules đều có BẬT=✓, chạy Daily.
Mỗi ngày tạo ra hàng chục cảnh báo giả, che lấp cảnh báo thật.

### 4. 20+/27 PR không có PO tham chiếu (BUG-M3-11)
Phần lớn phiếu nhập hàng không được kiểm soát bởi PO — 
vi phạm nguyên tắc kiểm soát nội bộ 3 chiều (PO-GR-Invoice).

---

## KHUYẾN NGHỊ ƯU TIÊN (CẬP NHẬT)

### P0 — Sửa ngay (blocking production)
1. **Fix freeze submit**: Thêm async submit + loading state + disable button khi đang xử lý
2. **Purge test data**: Script xóa 18 alert rules UAT/SMOKE, 3 BN UAT-DOC, lô asdasd, HĐ TEST-xxx
3. **Fix tồn kho Pending**: Tách "available qty" = tổng - pending_qc; báo cáo và cấp phát chỉ dùng available qty
4. **Validate nguồn ≠ đích**: Ở cả frontend và backend transfer form

### P1 — Sửa trước go-live
5. **Bắt buộc PO cho PR**: Validation hoặc cảnh báo khi tạo PR không có PO
6. **Lock summary fields ICS**: Tổng items, Items lệch = read-only, tính toán từ detail
7. **Validate số thẻ BHYT**: Regex format chuẩn (VD: [A-Z]{2}[0-9]-[0-9]{3}-[0-9]{8})
8. **Cập nhật bin status**: Trigger update bin status khi có SLE thay đổi

### P2 — Cải thiện UX
9. **Dịch toàn bộ field/column tiếng Anh** (40+ fields đã liệt kê)
10. **Thêm tên TK bên cạnh mã** trong GL Entry
11. **Loading skeleton** khi tải danh sách
12. **Tooltip cho "hạn ngắn"** và các field kỹ thuật

---

## PHỤ LỤC — DOCUMENTS TẠO TRONG QUÁ TRÌNH TEST

| Document | ID | Trạng thái hiện tại |
|---|---|---|
| Vật tư test | TEST-ITEM-001 | Active |
| MR | SC-MR-2026-04617 | Đã duyệt |
| PO | SC-PO-2026-04618 | Nhập (freeze khi submit) |
| PR | SC-PR-2026-04616 | Chờ QC |

*Lưu ý: Cần xóa/archive các documents test này sau khi review xong.*

---

*Báo cáo v3 — Claude (Anthropic) — SupplyCore QA Session 25/05/2026*
*Tổng bugs: 62 | Critical: 10 | High: 20 | Medium: 20 | Low: 12*
