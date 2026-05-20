# M8 — Kế toán: Luồng thao tác nhân viên

> Mô tả từng bước nhân viên Kế toán (SC-ACCOUNTANT), Quản lý (SC-MANAGER), Lãnh đạo (SC-EXECUTIVE) thao tác trên SPA SupplyCore để xử lý UC-24/25/26.

---

## Tổng quan

| UC | Vai trò chính | Mục tiêu |
|---|---|---|
| **UC-24** | Kế toán | Tạo Hoá đơn mua (PI) từ Phiếu nhập (PR) + 3-way match |
| **UC-25** | Kế toán + Manager/Executive | Tạo Phiếu thanh toán (PE), duyệt theo ngưỡng tiền |
| **UC-26** | Kế toán | Xem 4 báo cáo tài chính (Tồn kho — Công nợ — Chi phí kỳ — BHYT) |

**Điểm truy cập:** sidebar trái → **"Báo cáo TC (M8)"** hoặc vào danh sách `M8 Kế toán` từ ModuleHub.

---

## UC-24: Tạo Hoá đơn mua (PI) + 3-way match

### Tiền điều kiện
- PR (Phiếu nhập) đã submit, qc_status ≠ `Rejected`.
- Có PO gốc liên kết với PR.

### Các bước

**Bước 1. Vào PR đã submit**
- Sidebar **M3 Tiếp nhận** → list `SC Purchase Receipt` → click PR muốn lập hoá đơn.

**Bước 2. Tạo PI từ PR**
- Trong DocView PR, panel "⚡ Hành động khả dụng" → bấm **🧾 Tạo Hoá đơn mua (PI)**.
- Hệ thống tự tạo PI nháp với:
  - `supplier`, `purchase_order`, `purchase_receipt` ← từ PR
  - `supplier_invoice_no` = `AUTO-<PR-NAME>` (sửa lại)
  - `invoice_date` = hôm nay, `due_date` = +30 ngày
  - `vat_rate` = 10% (mặc định VN)
  - Items copy 1-1 từ PR
- Tự động navigate sang PI vừa tạo.

**Bước 3. Sửa số hoá đơn NCC + nhập số tiền chính xác**
- Sửa `supplier_invoice_no` đúng theo hoá đơn giấy/PDF NCC gửi.
- Kiểm tra `qty/rate/amount` từng dòng. Nếu lệch PR/PO → hệ thống sẽ flag 3-way mismatch khi submit.
- Bấm **💾 Lưu**.

**Bước 4. Submit PI → kích hoạt 3-way match**
- Bấm **📤 Submit**.
- Hệ thống chạy 3-way match:
  - So `PI.total ↔ PO.total ↔ PR.total` (tolerance ±1%).
  - **Match** (lệch ≤1%): `three_way_match_status = 'Match'`, `payment_hold = 0`.
  - **Mismatch** (lệch >1%): `three_way_match_status = 'Mismatch'`, `payment_hold = 1` tự bật. Cần nhập `mismatch_explanation` trước khi submit. PI bị "khoá thanh toán" cho đến khi Manager duyệt giải trình.
- Sau submit: GL post `Dr 152 Hàng tồn + Dr 1331 VAT đầu vào / Cr 331 Phải trả NCC`.

**Bước 5. Theo dõi danh sách PI**
- Vào **`/list/SC Purchase Invoice`** → cột "3-way" hiển thị badge (Match/Mismatch), cột "Khoá TT" hiển thị check icon nếu `payment_hold = 1`.
- Filter theo `payment_hold = 1` để xem PI cần xử lý mismatch.

### Lưu ý nhân viên
- ❌ Không tạo PI từ PR đã `qc_status = Rejected` — hệ thống chặn.
- ❌ Không tạo trùng PI cho cùng PR — hệ thống chặn (`SC-E007 PI_DUPLICATE`).
- ⚠️ Kiểm tra trùng `(supplier, supplier_invoice_no)` — hệ thống chặn nếu trùng (chống nhập trùng hoá đơn NCC).

---

## UC-25: Tạo Phiếu thanh toán (PE)

### Tiền điều kiện
- ≥1 PI submitted, `outstanding_amount > 0`, `payment_hold = 0`.

### Các bước

**Bước 1. Tạo PE mới**
- Sidebar **M8 Kế toán** → list `SC Payment Entry` → bấm **+ Tạo mới**.
- Nhập:
  - `payment_date` = hôm nay (mặc định).
  - `supplier` = chọn từ dropdown.
  - `payment_method` = `Bank Transfer` / `Cash` / `Cheque`.
- Bấm **💾 Lưu** (tạo draft).

**Bước 2. Auto-load các PI chưa thanh toán**
- Panel **⚡ Hành động khả dụng** → bấm **📋 Auto-load PI chưa thanh toán**.
- Nhập:
  - `supplier`: chọn NCC (cùng NCC trong PE).
  - `limit`: số PI tối đa (mặc định 50).
- Hệ thống trả danh sách PI outstanding (đã loại bỏ `payment_hold = 1`), sort theo `due_date ASC` (PI sắp đến hạn nhất ở trên).
- Result Viewer hiển thị table PI với cột: name, supplier_invoice_no, invoice_date, due_date, grand_total, paid_amount, outstanding_amount, three_way_match_status.

**Bước 3. Chọn PI cần thanh toán + nhập references**
- Trong PE form, child table "Tham chiếu" → thêm row cho từng PI muốn thanh toán:
  - `purchase_invoice` = mã PI.
  - `allocated_amount` = số tiền phân bổ (≤ outstanding_amount).
- Tổng `allocated_amount` các row = `PE.amount`.
- Nhập `partial_reason` nếu thanh toán một phần (`allocated_amount < outstanding_amount`).

**Bước 4. Submit PE → duyệt theo ngưỡng**
- Bấm **📤 Submit**.
- Hệ thống xác định cấp duyệt theo Settings `po_approval_threshold` (mặc định 50tr):
  - **< 50tr**: cần role `SupplyCore Manager` để submit.
  - **≥ 50tr**: cần role `SupplyCore Executive` để submit.
- Nếu sai role → bị reject `SC-E-PE-INSUFFICIENT-AUTH`.
- Cảnh báo nếu bank balance không đủ (warning, không block).
- Sau submit: GL post `Dr 331 Phải trả / Cr 1121 Tiền gửi NH`. Đồng thời update `PI.paid_amount += allocated_amount`, `PI.outstanding_amount` tự giảm.

**Bước 5. Theo dõi trạng thái**
- Vào list `SC Payment Entry` → cột `status`. PE hoàn tất khi `docstatus = 1`.
- Vào list `SC Purchase Invoice` → cột `outstanding_amount` đã giảm. Khi `outstanding_amount = 0`, `status = 'Paid'`.

### Lưu ý nhân viên
- ❌ Không submit PE thanh toán PI có `payment_hold = 1` — hệ thống chặn (`SC-E-PE-INVOICE-HELD`).
- ⚠️ Bank balance warning chỉ là cảnh báo — vẫn submit được, nhưng phải có lý do.

---

## UC-26: Báo cáo tài chính

### Truy cập
Sidebar → **📊 Báo cáo TC (M8)** → `/financial-reports`.

### Cấu trúc trang
4 tab: **📦 Tồn kho — giá trị | ⏰ Công nợ NCC | 💰 Chi phí vật tư kỳ | 🏥 Quyết toán BHYT**.

Mỗi tab có:
- Khu filter trên cùng (riêng cho tab).
- Nút **▶ Chạy báo cáo** + **📥 Xuất CSV** trên header.
- Banner cảnh báo "⚠️ Kỳ chưa khoá sổ" nếu còn chứng từ Draft trong kỳ → số có thể thay đổi.

### Tab 1 — Tồn kho giá trị

**Bước 1.** Chọn:
- `warehouse`: kho cần xem (để trống = tất cả).
- `item_group`: lọc theo nhóm vật tư (mã).
- `as_of_date`: tại ngày nào (mặc định hôm nay).

**Bước 2.** Bấm **▶ Chạy báo cáo**.

**Bước 3.** Xem 3 KPI cards (Số dòng / Tổng SL / Giá trị tồn) + table chi tiết per (item, warehouse, batch).

**Bước 4.** Click vào dòng item → drill-down vào DocView SC Item.

### Tab 2 — Công nợ NCC (Aging)

**Bước 1.** Chọn `supplier` (để trống = tất cả) + `as_of_date`.

**Bước 2.** Bấm **▶ Chạy báo cáo**.

**Bước 3.** Xem 5 bucket aging:
- 🟢 Chưa đến hạn
- 🔵 0–30 ngày
- 🟡 31–60 ngày
- 🟠 61–90 ngày
- 🔴 > 90 ngày

**Bước 4.** Trong table, click vào PI → mở drill-down modal hiển thị header + items + linked vouchers. Bấm "Mở chứng từ →" để vào DocView PI gốc.

### Tab 3 — Chi phí vật tư kỳ

**Bước 1.** Chọn `from_date` + `to_date` (bắt buộc) + `item_group`/`warehouse` (tuỳ chọn).

**Bước 2.** Bấm **▶ Chạy báo cáo**.

**Bước 3.** Xem tổng chi phí kỳ + breakdown theo nhóm vật tư (số PI, tổng SL, subtotal, % tổng).

### Tab 4 — Quyết toán BHYT

**Bước 1.** Chọn `from_date` + `to_date` (bắt buộc) + `department`/`bhyt_group` (tuỳ chọn).

**Bước 2.** Bấm **▶ Chạy báo cáo**.

**Bước 3.** Xem 4 KPI: Tổng CP / BHYT chi trả / BN tự trả / Vượt trần.

**Bước 4.** Table chi tiết per (bhyt_group, ward) — số PD, số BN, tổng SL/CP.

### Xuất CSV
Mọi tab đều có nút **📥 Xuất CSV** xuống file UTF-8 BOM, mở Excel không lỗi font.

### Cảnh báo
- "⚠️ Kỳ chưa khoá sổ" hiện banner nếu còn PI Draft / PE Draft / PD Draft trong kỳ. Số liệu chỉ ổn định sau khi đóng kỳ.

---

## Map vai trò ↔ tính năng

| Vai trò | Tạo PI | Submit PI <50tr | Submit PE ≥50tr | Báo cáo |
|---|---|---|---|---|
| SC-ACCOUNTANT | ✓ | ✓ | — | ✓ |
| SC-MANAGER | ✓ | ✓ | — | ✓ |
| SC-EXECUTIVE | — | — | ✓ | ✓ |
| SC-AUDITOR | đọc | — | — | ✓ |

---

## Error codes thường gặp

| Code | Ý nghĩa | Xử lý |
|---|---|---|
| SC-E007 PI_DUPLICATE | PI đã tồn tại cho PR | Mở PI cũ, không tạo mới |
| SC-E007 QC_REJECTED | PR bị QC từ chối | Tạo PR đổi hàng trước |
| SC-E009 THREE_WAY_MISMATCH | Lệch PO/PR/PI >1% | Nhập `mismatch_explanation`, Manager duyệt |
| SC-E-PE-INVOICE-HELD | PI bị `payment_hold` | Manager review mismatch, set hold=0 |
| SC-E-PE-INSUFFICIENT-AUTH | Role không đủ duyệt ngưỡng | Chuyển PE cho Executive |
