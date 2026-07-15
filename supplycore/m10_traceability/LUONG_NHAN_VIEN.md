# M10 — Truy xuất & Thu hồi: Luồng thao tác nhân viên

> Mô tả từng bước nhân viên Quản lý (SC-MANAGER), Thủ kho (SC-STOREKEEPER), QC (QC Officer), Kế toán (SC-ACCOUNTANT) xử lý 3 use case M10.

---

## Tổng quan

| UC | Vai trò chính | Mục tiêu |
|---|---|---|
| **UC-29** | Mọi role | Tra cứu vòng đời 1 lô (Batch Trace) — nhập → di chuyển → cấp phát → tồn hiện tại |
| **UC-30** | Manager | Lập Phiếu thu hồi (Recall), thông báo, theo dõi recovery, tạo return PR/write-off |
| **UC-31** | Manager + Auditor | Lập Investigation Report điều tra sự cố, audit trail, anomaly detection, lock user gian lận |

**Điểm truy cập:**
- UC-29 → sidebar **🔍 Truy xuất lô (M10)** → `/batch-trace`
- UC-30 → sidebar **M10 Truy xuất & Thu hồi** → list `SC Recall Notice`
- UC-31 → sidebar **M10** → list `SC Investigation Report`

---

## UC-29: Truy xuất lô (Batch Trace)

### Khi nào dùng
- NCC báo có lỗi 1 lô → muốn biết lô đó đã đi đâu.
- BN phản ứng phụ → cần trace lại lô đã dùng.
- Audit định kỳ → kiểm tra origin của lô.

### Các bước

**Bước 1. Vào trang Batch Trace**
- Sidebar → **🔍 Truy xuất lô (M10)**.

**Bước 2A. Tra cứu trực tiếp theo mã lô**
- Nhập `Mã lô (Batch No)` (VD: `DTRC-GLU5-202605-001`).
- Bấm **🔍 Tra cứu** hoặc Enter.

**Bước 2B. Hoặc tìm theo vật tư (nếu không nhớ mã lô)**
- Ô bên phải "Hoặc tìm theo VT" → nhập mã/tên vật tư → bấm **Tìm**.
- Hệ thống trả danh sách các lô của items khớp, sort theo `expiry_date DESC`.
- Click 1 lô trong danh sách → tự động tra cứu lô đó.

**Bước 3. Đọc kết quả — 5 section**

1. **Header (📦)**: Tên lô, item, manufacturer, supplier + supplier batch no, country, manufacturing_date, expiry_date.
   - Badge KCS (Pass/Fail/Pending).
   - Badge "🚫 ĐÃ KHOÁ" nếu `blocked = 1` + lý do khoá.
   - Pill expiry status: 🟢/🟡/🔴 + số ngày còn.

2. **Nguồn gốc (🏭)**: PR → PO → QI.
   - Click vào mã PR/PO/QI để mở DocView gốc.
   - Hiện status KCS.

3. **Tồn kho hiện tại (📍)**: Tổng SL + breakdown per warehouse.
   - Click warehouse → vào DocView SC Warehouse.

4. **Sổ cái tồn kho (📜)**: Bảng SLE chronological.
   - Cột: Ngày/Giờ, Kho, Vị trí, SL Δ (+xanh/-đỏ), Đơn giá, Chứng từ (link), Ghi chú.
   - Footer: Tổng nhập + Tổng xuất.

5. **Cấp phát BN (💉)**: Danh sách SC PD Item dùng lô.
   - Cột: Ngày, PD, BN, Khoa, SL, Đơn giá, BHYT trả, BN trả.
   - Click mã PD → DocView Patient Dispensing.

**Bước 4. Cảnh báo dữ liệu thiếu**
- Nếu lô có dữ liệu missing (thiếu NCC / số lô NCC / nhà SX / ngày SX / không liên kết PR / KCS pending):
  - Banner cam ⚠️ "Dữ liệu chưa đầy đủ" + danh sách field thiếu.
  - Cần liên hệ Storekeeper bổ sung trước khi recall hợp lệ.

### Lưu ý nhân viên
- Trace UI **read-only** — chỉ tra cứu, không sửa được dữ liệu lô từ đây.
- Để khoá/sửa lô → vào DocView `SC Batch`.

---

## UC-30: Phiếu thu hồi (Recall Notice)

### Tiền điều kiện
- Có lý do thu hồi rõ ràng (NCC thông báo, BYT yêu cầu, phát hiện hỏng nội bộ).
- Đã trace lô qua UC-29 để biết phạm vi ảnh hưởng.

### Các bước

**Bước 1. Tạo Phiếu thu hồi mới**
- Sidebar **M10** → list `SC Recall Notice` → **+ Tạo mới**.
- Form 4 section:

  **Thông báo thu hồi:**
  - `recall_date` = hôm nay.
  - `recall_type`: Voluntary (tự nguyện) / Mandatory (bắt buộc — BYT/NCC ra lệnh) / Precautionary (phòng ngừa).
  - `severity`: Class I (Critical) — nguy hiểm tính mạng / Class II (High) — cao / Class III (Low) — thấp.
  - `item`: vật tư bị thu hồi.
  - `batch_no`: mã lô (filter theo item đã chọn).
  - `supplier`: NCC (auto fill từ batch).

  **Lý do:**
  - `recall_reason`: mô tả ngắn (bắt buộc).
  - `regulatory_reference`: VD "CV BYT số 1234/QLD-CL ngày 19/05/2026".

  **Tổng hợp thu hồi:** các field readonly sẽ tự fill sau khi populate.

  **Liên kết xử lý:** readonly — `return_pr`, `write_off_entry`, `clinical_notified_at`, `approved_by`.

- Bấm **💾 Lưu** (tạo Draft).

**Bước 2. Tự tìm items ảnh hưởng**
- Panel **⚡ Hành động khả dụng** → **🔍 Tự tìm items ảnh hưởng**.
- Hệ thống scan:
  - SLE per warehouse → các vị trí kho còn tồn lô.
  - SC PD Item → các BN đã dùng lô (location_type = `Patient`).
  - Thêm rows vào child table `affected_items` với:
    - `location_type` (Warehouse / Patient / Department)
    - `warehouse` / `department` / `patient`
    - `voucher_type/voucher_no/voucher_date` (PR/SLE/PD liên kết)
    - `qty_dispensed`, `recovered_qty = 0`, `destroyed_qty = 0`, `outstanding_qty = qty_dispensed`, `status = 'Pending'`
- Section "Vị trí ảnh hưởng" hiển thị danh sách read-only.

**Bước 3. Submit Recall → khoá lô**
- Bấm **📤 Submit**.
- Hệ thống:
  - Set `Batch.blocked = 1`, `block_reason = Recall <name>`.
  - Status Recall = `Issued`.
  - Mọi giao dịch xuất kho dùng lô này sẽ bị chặn.

**Bước 4. Thông báo các khoa + BS điều trị**
- Panel **⚡ Hành động khả dụng** sau submit:
  - **📧 Gửi phiếu cho khoa**: email cho head các department có affected items.
  - **👨‍⚕️ Báo BS điều trị**: email cho BS phụ trách các BN đã dùng lô.
  - Tự set `clinical_notified_at = now()`.

**Bước 5. Theo dõi & cập nhật recovery (panel mới)**
- Sau submit, panel **📦 Theo dõi thu hồi** hiển thị tự động:
  - **Progress bar** xanh+đỏ+xanh-dương+vàng theo trạng thái rows.
  - **5 chip summary**: Tổng / Chờ xử lý / Đang xử lý / Đã thu / Đã huỷ / Đã đóng.
  - **Table chi tiết** mỗi vị trí ảnh hưởng:
    - Cột "Hành động" có 3 nút per row:
      - **✏️ Cập nhật**: mở modal nhập chi tiết (recovered_qty, destroyed_qty, status, remarks).
      - **✓ Thu**: 1-click thu hồi toàn bộ row (recovered_qty = qty_dispensed).
      - **🗑 Huỷ**: 1-click đánh dấu huỷ toàn bộ row (destroyed_qty = qty_dispensed).
  - Quick action chạy ngay, không cần xác nhận → toast confirm khi xong.
- Hệ thống tự recompute `outstanding_qty`, `recall_resolution_pct` sau mỗi update.

**Bước 6. Tạo Return PR (trả NCC)**
- Khi đã thu hồi đủ về kho → panel actions → **📦 Tạo Return PR**.
- Hệ thống tạo SC Purchase Receipt với `is_return = 1`, liên kết qua `return_pr` của Recall.
- Tự navigate sang PR mới để Storekeeper điền thông tin trả hàng + supplier.

**Bước 7. Tạo Phiếu huỷ (write-off)**
- Nếu lô không trả được NCC → panel actions → **🗑️ Tạo Phiếu huỷ**.
- Hệ thống tạo SC Stock Entry kiểu Material Issue, expense_account = tài khoản chi phí huỷ, liên kết qua `write_off_entry`.

**Bước 8. Audit lịch sử cấp phát**
- Panel actions → **📋 Audit cấp phát**.
- Nhập `start_date / end_date` → hệ thống trả danh sách tất cả PD trong kỳ dùng lô này.
- Result Modal hiển thị bảng (tự động render).

**Bước 9. Đóng Recall**
- Khi `recall_resolution_pct = 100%`:
  - Manual update status = `Closed` (sửa field `resolution` + `resolution_date`).
  - Hoặc để hệ thống auto-close nếu mọi row status ∈ `{Recovered, Destroyed, Closed}`.

### Lưu ý nhân viên
- 🔒 Submit Recall **không thể undo** — lô bị block ngay. Tạo Recall mới khác nếu muốn reset.
- ⚠️ Quick "Thu" / "Huỷ" thao tác trực tiếp, không có confirm — dùng cẩn thận.
- ❌ Recall đã Issued thì không sửa được item/batch — chỉ update recovery.

---

## UC-31: Investigation Report

### Khi nào dùng
- Phát hiện chênh lệch tồn kho lớn (SR `requires_investigation = 1`).
- Nghi ngờ gian lận / fraud.
- Sự cố hệ thống / mất dữ liệu.
- Audit định kỳ sâu (ABC analysis, top items).

### Các bước

**Bước 1. Tạo IR mới**
- Sidebar **M10** → list `SC Investigation Report` → **+ Tạo mới**.

**Bước 2. Điền thông tin điều tra**
- Section "Điều tra":
  - `investigation_date` = ngày bắt đầu (mặc định hôm nay).
  - `investigation_type`:
    - `Stock Loss` — thất thoát kho.
    - `Discrepancy` — sai lệch số liệu (mặc định).
    - `Fraud` — gian lận.
    - `System Error` — lỗi hệ thống.
    - `Other`.
- Section "Phạm vi (cần ≥1)":
  - **Bắt buộc ít nhất 1** trong: `item` / `warehouse` / `batch` — nếu không, banner cam ⚠️ "Cần xác định phạm vi điều tra" hiện.
  - `period_start` + `period_end` (bắt buộc) — khoảng thời gian audit.
  - `filter_user` (optional) — lọc theo user nghi ngờ.
- Section "Mô tả":
  - `description` — mô tả phát hiện ban đầu.
- Bấm **💾 Lưu** → tạo Draft.

**Bước 3. Chạy Audit Trail**
- Panel **⚡ Hành động khả dụng** → **🔍 Chạy Audit Trail**.
- Hệ thống query Version log + audit log của Frappe trong scope đã set, trả danh sách entries.
- **Result Modal hiển thị**:
  - Tổng entries / Suspicious count / Unique users.
  - Table chi tiết: thời gian, user, action, doctype + docname.
- Đóng modal — hệ thống không lưu vào IR (chỉ xem).

**Bước 4. So sánh tồn kho lý thuyết vs thực tế**
- Section "Kết quả so sánh tồn kho" sẽ fill sau khi chạy action.
- Nhập `actual_qty` (SL thực tế từ đếm tay) vào form.
- Panel actions → **⚖️ So sánh tồn kho**.
- Hệ thống compute:
  - `theoretical_qty` = sum SLE trong scope.
  - `variance_qty = actual_qty - theoretical_qty`.
  - `variance_value = variance_qty × avg valuation_rate`.
- Panel **⚖️ Kết quả so sánh tồn kho** hiện 4 cards: SL lý thuyết / SL thực tế / Δ SL / Δ Giá trị.
  - Đỏ nếu thiếu hụt, xanh dương nếu thừa, xanh lá nếu match.

**Bước 5. Phát hiện bất thường (7 heuristics)**
- Panel actions → **⚠️ Phát hiện bất thường**.
- Nhập `large_qty_threshold` (mặc định 1000) — ngưỡng SL "lớn bất thường".
- Hệ thống chạy 7 heuristics:
  1. After-hours activity (giờ ngoài giờ làm).
  2. Same-user multiple cancellations.
  3. Large qty single transaction.
  4. Negative stock movements.
  5. Cancelled-then-recreated patterns.
  6. Bulk modifications by 1 user.
  7. Balance mismatch replay.
- Panel **⚠️ Bất thường phát hiện** hiển thị danh sách card per anomaly + chi tiết JSON.

**Bước 6. Khoá user nghi ngờ (Fraud)**
- Nếu xác định user gian lận → panel actions → **🔒 Khoá user (Fraud)**.
- Nhập:
  - `user`: email user cần khoá.
  - `reason`: lý do.
- Hệ thống set User.enabled = 0 + log vào `suspended_users_log` của IR.
- Cần role `SupplyCore Manager` hoặc cao hơn.

**Bước 7. Tạo SR điều chỉnh tự động (nếu là System Error)**
- Panel actions → **🔧 Tạo SR điều chỉnh**.
- Nhập `actual_qty` (SL thực sau audit) + `valuation_rate` (đơn giá điều chỉnh).
- Hệ thống tạo SC Stock Reconciliation Draft với 1 dòng item = chênh lệch, link qua `system_error_adjustment`.
- Banner xanh "✓ SR điều chỉnh đã được tạo: SC-SR-..." hiện trong form, click link để mở SR.

**Bước 8. Kết luận + ký**
- Nhập:
  - `recommendation`: biện pháp khắc phục đề xuất.
  - `conclusion`: kết luận chính.
  - `remarks`: ghi chú.
- Manager submit IR → `approved_by` tự set.

### Lưu ý nhân viên
- ⚠️ Khoá user là hành động không thể undo trên UI — phải vào Frappe Desk để mở lại.
- 📋 IR thường chạy song song với SR `requires_investigation = 1` (M9 UC-28).
- 🔍 Audit Trail entries có thể >200 dòng — Result Modal chỉ hiện 200 đầu, xuống các trang khác qua Frappe Desk.

---

## Map vai trò ↔ hành động

| Vai trò | UC-29 Trace | UC-30 Tạo Recall | UC-30 Submit + Notify | UC-31 Tạo IR | UC-31 Submit + Lock user |
|---|---|---|---|---|---|
| Mọi role SC | ✓ | — | — | — | — |
| SC-STOREKEEPER | ✓ | đọc | — | đọc | — |
| SC-MANAGER | ✓ | ✓ | ✓ | ✓ | ✓ |
| SC-AUDITOR | ✓ | đọc | — | ✓ | đọc |
| QC Officer | ✓ | — | — | — | — |

---

## Quick reference button mapping

### Trang Batch Trace
| Button | Hành động |
|---|---|
| 🔍 Tra cứu | get_batch_trace(batch_no) |
| Tìm | list_batches_for_item(item_code_or_name) |

### DocView SC Recall Notice
| Khi nào hiện | Button | Method |
|---|---|---|
| Draft | 🔍 Tự tìm items ảnh hưởng | populate_affected_items |
| Submitted | 📧 Gửi phiếu cho khoa | notify_departments |
| Submitted, chưa notify clinical | 👨‍⚕️ Báo BS điều trị | notify_clinical_staff |
| Submitted, chưa return | 📦 Tạo Return PR | create_return_to_supplier |
| Submitted, chưa write-off | 🗑️ Tạo Phiếu huỷ | create_write_off |
| Bất kỳ | 📋 Audit cấp phát | audit_dispensings_in_period |
| Per row (panel) | ✏️ Cập nhật / ✓ Thu / 🗑 Huỷ | update_recovery |

### DocView SC Investigation Report
| Button | Method |
|---|---|
| 🔍 Chạy Audit Trail | run_audit_trail |
| ⚖️ So sánh tồn kho | compare_stock |
| ⚠️ Phát hiện bất thường | detect_anomalies |
| 🔒 Khoá user (Fraud) | lock_user |
| 🔧 Tạo SR điều chỉnh | create_system_error_adjustment |

---

## Error codes thường gặp

| Code | Ý nghĩa | Xử lý |
|---|---|---|
| `SC-E-INV-NO-SCOPE` | IR thiếu Vật tư/Kho/Batch | Nhập ít nhất 1 phạm vi |
| `SC-E-RCL-NOT-ISSUED` | update_recovery khi Recall chưa submit | Submit Recall trước |
| `SC-E-RCL-ROW-NOT-FOUND` | row_name không tồn tại trong affected_items | Reload form, dùng panel UI thay vì gọi API |
| `BATCH_RECALLED` | Cố xuất kho lô bị block | Lô đã recall — không xuất được |
| `SC-E-IR-LOCK-FORBIDDEN` | Role không đủ để lock user | Chuyển cho Manager |
