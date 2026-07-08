# Phân tích & xử lý báo cáo lỗi SupplyCore (16/06/2026)

> Nguồn: `docs/bug/` — file 1 (tóm tắt L01–L22), file 3 (tester bổ sung T01–T19).
> Phân loại bởi: rà soát mã nguồn trực tiếp (không đoán theo ảnh).
> Ngày phân tích: 24/06/2026 · Site: `supplycore`.

## Nguyên tắc phân loại

- **BUG (sửa + test)** = phần mềm cho qua dữ liệu sai / chạy ngược ý đồ thiết kế hoặc ngược
  requirement → có thể kiểm chứng bằng cách tái hiện thao tác sai.
- **NGHIỆP VỤ / CẢI TIẾN (ghi lại + giải thích)** = thay đổi *cái phần mềm nên làm* (tính năng mới,
  sở thích UX, đơn giản hóa thiết kế, đổi quy trình). Không phải lỗi kỹ thuật.
- **KHÔNG PHẢI LỖI (giải thích)** = báo cáo mô tả sai thực trạng; mã nguồn đã đúng.

---

## A. ĐÃ SỬA (bug thật) — chi tiết ở `FIXES_16062026.md`

| ID | Khu vực | Bản chất | Bằng chứng (mã) |
|----|---------|----------|-----------------|
| L12 | Tạo PO ràng buộc HĐ khung | PO không bắt NCC trùng HĐK & không lọc item trong HĐK | `sc_purchase_order.py:_validate_against_framework_contract` chỉ kiểm tiền |
| L13 | Tạo PO — ngày giao | Không chặn ngày giao < ngày tạo PO | `validate()` thiếu kiểm `schedule_date` |
| L14 | Tạo PO — SL vượt HĐK | Chỉ kiểm tổng TIỀN, không kiểm SL/dòng vs `remaining_qty` HĐK | cùng hàm trên |
| T12 | Tạo PO — SL ≤ 0 | Không chặn SL = 0 hoặc âm (lưu im lặng) | `sc_purchase_order_item.py` rỗng, parent không kiểm `qty>0` |
| L17 | QC — kết quả ↔ hành động | Cho cặp mâu thuẫn (Đạt+Trả NCC, Không đạt+Chấp nhận) | `sc_quality_inspection.py` không cross-validate |
| L19 | QC — người kiểm | `inspected_by` default user nhưng KHÔNG khóa (đổi được) | `sc_quality_inspection.json` thiếu `read_only` |
| L20 / T06 | QC — sửa được phiếu nhập | `purchase_receipt/item/batch/received_qty` không read-only | `sc_quality_inspection.json` |
| L21 / T09 | Tồn kho | `stock_balance()` cộng cả lô Pending/Rejected/blocked | `api/frontend.py:241` thiếu filter (các hàm khác đã filter đúng) |
| T17 | BHYT > 100% | `bhyt_payment_rate` (Percent) không chặn > 100 | `SC Patient` field default 80, không max |

## B. NGHIỆP VỤ / CẢI TIẾN — KHÔNG sửa, ghi nhận & giải thích

| ID | Khu vực | Vì sao KHÔNG coi là bug | Khuyến nghị |
|----|---------|------------------------|-------------|
| L02 | Bin Location 'Trống' | **Đúng thiết kế.** `status` (Empty/In Use/Full) là **read-only, tự tính** từ `current_qty` vs `capacity` (`bin_location.py:48-56`). "Không nhập được" là cố ý — trạng thái phản ánh tồn thực, không cho nhập tay. | Giữ nguyên; có thể thêm tooltip giải thích. |
| L03 / T05 | Hiển thị mã vs tên | Quyết định UX, không phải lỗi. Dropdown hiện đã hiện tên ở dòng phụ (`LinkAutocomplete.vue:subLabel`). Đổi "Tên (mã)" là thay đổi sản phẩm. | Cải tiến UX đợt sau: ưu tiên Tên, mã làm phụ. |
| L04 | HĐK — mặc định ngày | Yêu cầu thêm hành vi mặc định (ngày hiệu lực = ngày ký, hết hạn +1 năm). Tính năng tiện ích, không phải lỗi. | Cải tiến: set default khi tạo, vẫn cho sửa. |
| L05 | HĐK — đính kèm nhiều tệp | Giới hạn của kiểu field `Attach` (Frappe lưu 1 URL). Cần đổi sang Table/Attach-multiple — tính năng mới. | Cải tiến: dùng child table "Tài liệu đính kèm". |
| L06 / T11 | Import Excel danh mục | Tính năng mới. (Đã có `api/fc_io.py` đang phát triển + nút Xuất/Nhập trên list.) | Hoàn thiện & tài liệu hóa luồng Import. |
| L07 / T03 | Định dạng tiền | UX. `fmtVND` đã có (đầy đủ, phân tách ngàn, ₫); `fmtShort` rút gọn 'k/tr' dùng ở thẻ KPI. | Chuẩn hóa: bảng/biểu mẫu dùng `fmtVND`; chỉ KPI dùng `fmtShort` + tooltip. |
| L08 | Duyệt HĐK — bắt nội dung dài | Hiện có rule `SC-E026 APPROVAL_COMMENT_TOO_SHORT` bắt comment dài. Chủ đầu tư muốn **bỏ** ràng buộc → đổi quy tắc nghiệp vụ, không phải lỗi. | Quyết định nghiệp vụ: hạ ngưỡng/bỏ rule nếu chốt. |
| L09 / T13 | YC mua — ngày cần dòng | Tiện ích mặc định (UX). Luồng FC→MR đã default `schedule_date`; thêm dòng tay ở UI chưa auto-fill. | Cải tiến frontend: thêm dòng → điền ngày cần chung, vẫn sửa được. |
| L10 | Duyệt YC mua — Bối cảnh | UX/hiển thị (tên người yêu cầu, khoa). Không phải lỗi logic. | Cải tiến hiển thị panel duyệt. |
| L11 | Tìm HĐK đa tiêu chí | Cải tiến tìm kiếm (tên NCC/mã/tên VT). | Mở rộng filter tìm kiếm. |
| L16 | Gộp nút Lưu/Gửi duyệt | Quy trình/UX. Hiện theo chuẩn Frappe Save→Submit. | Cải tiến UX: ẩn "Gửi duyệt" tới khi đã Lưu. |
| L18 | Thiếu bước Duyệt QC | Thiết kế quy trình. QC hiện submit là chốt ngay (không có state Duyệt riêng). Thêm là **đổi quy trình**. | Quyết định nghiệp vụ: có cần state "Chờ duyệt QC"? |
| L22 | Bỏ kho cha/con | **Ngược requirement gốc** (Phase 1: "kho 3 tầng" bắt buộc). Hiện đang dùng thật: 19 kho, 14 có kho cha, 1 nhóm. Bỏ = tái thiết kế lớn (NestedSet, FEFO, báo cáo theo tầng). | **Cần chốt với chủ đầu tư**: đây là đổi phạm vi, không phải lỗi. Nếu chốt bỏ → kế hoạch migration riêng. |
| T01 | Route theo tên | Cải tiến điều hướng (alias `/contracts`…). Route hiện theo mã module. | Thêm alias + 404 gợi ý. |
| T04 | Định dạng ngày form | UX. Form dùng `<input type=date>` (hiển thị theo locale trình duyệt, **lưu ISO yyyy-mm-dd** nên KHÔNG sai dữ liệu); list hiển thị d/m/yyyy. Không gây hỏng dữ liệu. | Cải tiến: date-picker địa phương hóa dd/mm/yyyy. |
| T07 | QC checklist bắt buộc | Cải tiến quy trình (bắt chọn checklist trước khi kết luận). | Cân nhắc thêm `reqd`/validate nếu chốt. |
| T14 | YC mua — ngày cần quá khứ | Header MR đã có rule `SC-E-DATE` (`schedule_date ≥ transaction_date`). Cảnh báo "< hôm nay" là cải tiến thêm. | Cải tiến: cảnh báo mềm khi ngày cần < hôm nay. |
| T15 (ngoài QC) | Khóa người thực hiện ở M6/M9 | `requested_by`, `planned_by`, `counted_by`, `manager_witness` để chọn tự do — là **lựa chọn thiết kế** (đôi khi nhập hộ). Khóa cứng = đổi nghiệp vụ. Riêng QC `inspected_by` đã khóa (mục L19). | Quyết định nghiệp vụ: default = user đăng nhập, chỉ quản lý sửa. |

## C. KHÔNG PHẢI LỖI — báo cáo mô tả sai thực trạng

| ID | Kết luận sau khi đọc mã |
|----|--------------------------|
| T02 | **Dropdown đã tải phía server, `limit:20`** (`LinkAutocomplete.vue:doSearch`) — KHÔNG tải toàn bộ danh mục. "Renderer frozen" (nếu có) nằm ở chỗ khác, cần hồ sơ riêng. |
| T08 | **Nhãn đã Việt hóa** qua registry `modules.js` (DT label). Tên tiếng Anh chỉ là tên kỹ thuật trong DB, frontend luôn hiện nhãn Việt. |
| T16 | **Điểm tích cực** — `SC-E024 SAME_WAREHOUSE` đã có (`sc_transfer_request.py:66`). Dùng làm khuôn mẫu mã lỗi cho các fix khác. |
| T18 | **'Kho xuất' đã có** — `sc_pd_item.warehouse` (Kho cấp) + kiểm tồn `sc_patient_dispensing.py:36-49` (chặn khi không đủ tồn). Không thiếu. |
| T19 | **Điểm tích cực** — Kiểm kê có đếm mù + ngưỡng đếm lại. Giữ nguyên. |
| T10 | Mã chứng từ nhảy số là **đặc tính naming Frappe** (huỷ/rollback để lại lỗ hổng số). Không phải lỗi; môi trường test càng dễ thấy. |

## D. CẦN LÀM RÕ / KHÔNG TÁI HIỆN ĐƯỢC

| ID | Phân tích |
|----|-----------|
| L15 | Báo "Chưa có hạn dùng dù đã nhập". **Mã backend đúng**: chỉ throw `SC-E-PR-MISSING-EXPIRY` khi dòng KHÔNG có `batch_no` VÀ KHÔNG có `expiry_date` (`sc_purchase_receipt.py:67-82`). Field `expiry_date` nằm ở section "Lô" (không ở cột list-view). Triệu chứng "nhập rồi vẫn báo thiếu" ⇒ nhiều khả năng lỗi **binding ngày ở frontend** (liên quan T04: chuỗi ngày không parse → lưu rỗng), không phải backend. Dữ liệu test đã bị wipe nên không tái hiện trực tiếp. **Khuyến nghị**: kiểm tra binding field `expiry_date` trong grid PR ở frontend + chuẩn hóa định dạng ngày (T04) rồi mới kết luận. KHÔNG sửa backend mù. |
| L01 | Race condition trang Người dùng & Quyền — **đã xác minh** thứ tự load (`router.js` + `Users.vue:onMounted`). Đã sửa (xem mục A/FIXES). |
